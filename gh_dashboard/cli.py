"""Command Line Interface for GitHub Engineering Dashboard (gh-dashboard).
"""

import argparse
import json
import os
import sys
from typing import Optional

# Ensure package directory is on sys.path if executed directly
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from gh_dashboard import __version__
from gh_dashboard.analytics import EngineeringAnalytics
from gh_dashboard.client import GitHubAPIError, GitHubClient
from gh_dashboard.formatters import MarkdownFormatter, TerminalFormatter


def parse_repo_arg(repo_arg: str):
    """Parse 'owner/repo' or full GitHub URL into (owner, repo)."""
    clean = repo_arg.strip().rstrip("/")
    if "github.com/" in clean:
        clean = clean.split("github.com/")[-1]
    parts = clean.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid repository format '{repo_arg}'. Expected 'owner/repo'.")
    return parts[0], parts[1]


def run_audit(client: GitHubClient, owner: str, repo: str) -> dict:
    """Fetch all repository data and calculate metrics."""
    repo_data = client.get_repo(owner, repo)
    community = client.get_community_profile(owner, repo)
    prs = client.get_pull_requests(owner, repo, state="all", limit=100)
    issues = client.get_issues(owner, repo, state="all", limit=100)
    contributors = client.get_contributors(owner, repo, limit=100)
    workflow_runs = client.get_workflow_runs(owner, repo, limit=10)

    pr_metrics = EngineeringAnalytics.analyze_pull_requests(prs)
    issue_metrics = EngineeringAnalytics.analyze_issues(issues)
    contributor_metrics = EngineeringAnalytics.analyze_contributors(contributors)
    health = EngineeringAnalytics.calculate_health_score(repo_data, community)
    ci_metrics = EngineeringAnalytics.analyze_ci_runs(workflow_runs)

    return {
        "repo": repo_data,
        "pr_metrics": pr_metrics,
        "issue_metrics": issue_metrics,
        "contributor_metrics": contributor_metrics,
        "health": health,
        "ci_metrics": ci_metrics,
    }


def main(args: Optional[list] = None):
    parser = argparse.ArgumentParser(
        prog="gh-dashboard",
        description="GitHub Engineering Dashboard & Metrics CLI."
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--token", help="GitHub Personal Access Token (defaults to GITHUB_TOKEN or gh CLI)")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Run full engineering audit on a repository")
    audit_parser.add_argument("repo", help="Target repository in 'owner/repo' format")

    # Command: health
    health_parser = subparsers.add_parser("health", help="Check community health score only")
    health_parser.add_argument("repo", help="Target repository in 'owner/repo' format")

    # Command: export
    export_parser = subparsers.add_parser("export", help="Export metrics report to Markdown or JSON")
    export_parser.add_argument("repo", help="Target repository in 'owner/repo' format")
    export_parser.add_argument("-f", "--format", choices=["markdown", "json"], default="markdown", help="Export format")
    export_parser.add_argument("-o", "--out", help="Output file path (prints to stdout if omitted)")

    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        sys.exit(0)

    client = GitHubClient(token=parsed_args.token)

    try:
        owner, repo_name = parse_repo_arg(parsed_args.repo)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if parsed_args.command == "audit":
            print(f"Auditing repository {owner}/{repo_name} via GitHub API...")
            data = run_audit(client, owner, repo_name)
            output = TerminalFormatter.render_dashboard(data)
            print(output)

        elif parsed_args.command == "health":
            repo_data = client.get_repo(owner, repo_name)
            community = client.get_community_profile(owner, repo_name)
            health = EngineeringAnalytics.calculate_health_score(repo_data, community)
            print(f"\nRepository: {owner}/{repo_name}")
            print(f"Health Score: {health['health_score']} / 100 (Grade {health['health_grade']})")
            print("\nCheck Details:")
            for c in health["checks"]:
                status = "PASS" if c["status"] == "PASS" else "FAIL"
                print(f"  [{status}] {c['check']:<25} : {c['points']} pts")

        elif parsed_args.command == "export":
            data = run_audit(client, owner, repo_name)
            if parsed_args.format == "json":
                # Serialize to clean json
                content = json.dumps(data, indent=2, default=str)
            else:
                content = MarkdownFormatter.render_markdown(data)

            if parsed_args.out:
                with open(parsed_args.out, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Successfully exported {parsed_args.format} report to {parsed_args.out}")
            else:
                print(content)

    except GitHubAPIError as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
