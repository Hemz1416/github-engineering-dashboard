"""GitHub API Client for Engineering Dashboard.
Uses standard library urllib with automatic gh CLI token discovery.
"""

import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    """Authenticated client for interacting with GitHub REST API v3."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or self._discover_token()
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "GitHub-Engineering-Dashboard/0.1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    @staticmethod
    def _discover_token() -> Optional[str]:
        """Discover GitHub token from environment variable or gh CLI."""
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

    def request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make an authenticated GET request to GitHub API."""
        url = endpoint if endpoint.startswith("http") else f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        if params:
            query_str = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query_str}"

        req = urllib.request.Request(url, headers=self.headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_msg)
                message = err_json.get("message", str(e))
            except Exception:
                message = err_msg or str(e)
            raise GitHubAPIError(f"GitHub API Error [{e.code}]: {message}", status_code=e.code)
        except urllib.error.URLError as e:
            raise GitHubAPIError(f"Network error communicating with GitHub API: {e.reason}")

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
        """Fetch pull requests for the repository."""
        params = {"state": state, "per_page": min(limit, 100)}
        data = self.request(f"repos/{owner}/{repo}/pulls", params=params)
        return data if isinstance(data, list) else []

    def get_issues(self, owner: str, repo: str, state: str = "all", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch issues (excluding PRs) for the repository."""
        params = {"state": state, "per_page": min(limit, 100)}
        data = self.request(f"repos/{owner}/{repo}/issues", params=params)
        if isinstance(data, list):
            # GitHub issues endpoint includes pull requests; filter them out
            return [item for item in data if "pull_request" not in item]
        return []

    def get_contributors(self, owner: str, repo: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch contributor stats."""
        params = {"per_page": min(limit, 100)}
        try:
            data = self.request(f"repos/{owner}/{repo}/contributors", params=params)
            return data if isinstance(data, list) else []
        except GitHubAPIError:
            return []

    def get_releases(self, owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent releases."""
        params = {"per_page": min(limit, 100)}
        try:
            data = self.request(f"repos/{owner}/{repo}/releases", params=params)
            return data if isinstance(data, list) else []
        except GitHubAPIError:
            return []

    def get_workflow_runs(self, owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent GitHub Actions CI workflow runs."""
        params = {"per_page": min(limit, 100)}
        try:
            data = self.request(f"repos/{owner}/{repo}/actions/runs", params=params)
            return data.get("workflow_runs", []) if isinstance(data, dict) else []
        except GitHubAPIError:
            return []

