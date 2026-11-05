"""GitHub API Client for Engineering Dashboard.
Implements authenticated GitHub REST API v3 and GraphQL API v4 clients with zero third-party dependencies.
Features automatic gh CLI token discovery, rate-limit tracking, pagination, and robust error handling.
"""

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitExceededError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded."""
    def __init__(self, message: str, reset_timestamp: Optional[int] = None):
        super().__init__(message, status_code=403)
        self.reset_timestamp = reset_timestamp


class GitHubClient:
    """Authenticated client for interacting with GitHub REST API v3 and GraphQL API v4."""

    REST_BASE_URL = "https://api.github.com"
    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(self, token: Optional[str] = None):
        self.token = token or self._discover_token()
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "GitHub-Engineering-Dashboard/0.1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        self.last_rate_limit: Dict[str, Any] = {
            "limit": None,
            "remaining": None,
            "reset": None,
            "used": None,
        }

    @staticmethod
    def _discover_token() -> Optional[str]:
        """Discover GitHub token from environment variables or local gh CLI auth keyring."""
        env_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if env_token:
            return env_token.strip()
        try:
            res = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8"
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def _update_rate_limit_headers(self, headers: Any) -> None:
        """Extract and store rate limit metadata from response headers."""
        if not headers:
            return
        limit = headers.get("X-RateLimit-Limit")
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        used = headers.get("X-RateLimit-Used")

        if limit is not None:
            self.last_rate_limit["limit"] = int(limit)
        if remaining is not None:
            self.last_rate_limit["remaining"] = int(remaining)
        if reset is not None:
            self.last_rate_limit["reset"] = int(reset)
        if used is not None:
            self.last_rate_limit["used"] = int(used)

    def request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        data: Optional[bytes] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """Make an authenticated HTTP request to GitHub REST API."""
        url = endpoint if endpoint.startswith("http") else f"{self.REST_BASE_URL}/{endpoint.lstrip('/')}"
        if params and method == "GET":
            query_str = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query_str}"

        req_headers = dict(self.headers)
        if extra_headers:
            req_headers.update(extra_headers)

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                self._update_rate_limit_headers(resp.headers)
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            self._update_rate_limit_headers(e.headers)
            err_msg = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_msg)
                message = err_json.get("message", str(e))
            except Exception:
                message = err_msg or str(e)

            if e.code in (403, 429) and "rate limit" in message.lower():
                reset_ts = self.last_rate_limit.get("reset")
                raise RateLimitExceededError(
                    f"GitHub API Rate Limit Exceeded: {message}. Resets at timestamp {reset_ts}",
                    reset_timestamp=reset_ts
                )
            raise GitHubAPIError(f"GitHub API Error [{e.code}]: {message}", status_code=e.code)
        except urllib.error.URLError as e:
            raise GitHubAPIError(f"Network error communicating with GitHub API: {e.reason}")

    def paginate(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_items: int = 100) -> List[Dict[str, Any]]:
        """Paginate through list endpoints up to max_items."""
        items: List[Dict[str, Any]] = []
        page = 1
        per_page = min(max_items, 100)
        current_params = dict(params or {})
        current_params["per_page"] = per_page

        while len(items) < max_items:
            current_params["page"] = page
            data = self.request(endpoint, params=current_params)
            if not isinstance(data, list) or not data:
                break
            items.extend(data)
            if len(data) < per_page:
                break
            page += 1

        return items[:max_items]

    def graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL v4 query against GitHub's GraphQL API."""
        payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        res = self.request(self.GRAPHQL_URL, method="POST", data=payload, extra_headers=headers)
        if "errors" in res:
            err_details = "; ".join(e.get("message", str(e)) for e in res["errors"])
            raise GitHubAPIError(f"GraphQL Error: {err_details}")
        return res.get("data", {})

    def get_rate_limit(self) -> Dict[str, Any]:
        """Fetch current authenticated and unauthenticated rate limit quotas."""
        return self.request("rate_limit")

    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository general metadata."""
        return self.request(f"repos/{owner}/{repo}")

    def get_community_profile(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch community health metrics and standard files (README, License, CoC)."""
        try:
            return self.request(f"repos/{owner}/{repo}/community/profile")
        except GitHubAPIError:
            return {}

    def get_pull_requests(self, owner: str, repo: str, state: str = "all", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch pull requests for the repository with pagination support."""
        params = {"state": state}
        if limit <= 100:
            params["per_page"] = limit
            data = self.request(f"repos/{owner}/{repo}/pulls", params=params)
            return data if isinstance(data, list) else []
        return self.paginate(f"repos/{owner}/{repo}/pulls", params=params, max_items=limit)

    def get_issues(self, owner: str, repo: str, state: str = "all", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch issues (excluding PRs) with pagination support."""
        params = {"state": state}
        raw_items = self.paginate(f"repos/{owner}/{repo}/issues", params=params, max_items=limit)
        return [item for item in raw_items if "pull_request" not in item]

    def get_contributors(self, owner: str, repo: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch contributor stats."""
        try:
            return self.paginate(f"repos/{owner}/{repo}/contributors", max_items=limit)
        except GitHubAPIError:
            return []

    def get_releases(self, owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent releases."""
        try:
            data = self.request(f"repos/{owner}/{repo}/releases", params={"per_page": min(limit, 100)})
            return data if isinstance(data, list) else []
        except GitHubAPIError:
            return []

    def get_workflow_runs(self, owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent GitHub Actions CI workflow runs."""
        try:
            data = self.request(f"repos/{owner}/{repo}/actions/runs", params={"per_page": min(limit, 100)})
            return data.get("workflow_runs", []) if isinstance(data, dict) else []
        except GitHubAPIError:
            return []

    def get_discussions_summary(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository discussion metrics via GraphQL API v4.
        
        Properly differentiates between active discussions, disabled discussions,
        and GraphQL query/permission/network errors rather than silently reporting zero.
        """
        query = """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            hasDiscussionsEnabled
            discussions(first: 10, orderBy: {field: CREATED_AT, direction: DESC}) {
              totalCount
              nodes {
                id
                title
                createdAt
                isAnswered
                category {
                  name
                  isAnswerable
                }
              }
            }
          }
        }
        """
        try:
            data = self.graphql(query, variables={"owner": owner, "name": repo})
            repo_data = data.get("repository") or {}
            has_enabled = repo_data.get("hasDiscussionsEnabled", False)
            disc_data = repo_data.get("discussions", {})
            return {
                "status": "ok" if has_enabled else "disabled",
                "enabled": has_enabled,
                "total_discussions": disc_data.get("totalCount", 0) if has_enabled else 0,
                "recent_discussions": disc_data.get("nodes", []) if has_enabled else [],
            }
        except GitHubAPIError as e:
            return {
                "status": "error",
                "error": str(e),
                "enabled": None,
                "total_discussions": None,
                "recent_discussions": [],
            }
