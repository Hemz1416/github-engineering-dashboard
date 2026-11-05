"""Formatters for CLI terminal output and Markdown report generation.
"""

import json
from typing import Any, Dict


class TerminalFormatter:
    """Renders formatted ASCII/ANSI terminal tables and summaries."""

    HEADER_BLUE = "\033[94m"
    SUCCESS_GREEN = "\033[92m"
    WARNING_YELLOW = "\033[93m"
    DANGER_RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def render_dashboard(cls, data: Dict[str, Any], use_color: bool = True) -> str:
        """Render complete terminal dashboard view."""
        repo = data.get("repo", {})
        pr_metrics = data.get("pr_metrics", {})
        issue_metrics = data.get("issue_metrics", {})
        contributor_metrics = data.get("contributor_metrics", {})
        health = data.get("health", {})
        ci = data.get("ci_metrics", {})

        repo_name = repo.get("full_name", "Unknown Repository")
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        lang = repo.get("language") or "N/A"
        grade = health.get("health_grade", "N/A")
        score = health.get("health_score", 0)

        lines = []
        lines.append("=" * 72)
        lines.append(f"  GITHUB ENGINEERING DASHBOARD :: {repo_name}")
        lines.append("=" * 72)
        lines.append(f"  Stars: {stars:<6} | Forks: {forks:<6} | Language: {lang:<10} | Health: {score}/100 (Grade {grade})")
        lines.append("-" * 72)

        # Pull Request Velocity
        lines.append("  [PULL REQUEST VELOCITY]")
        lines.append(f"    Total Evaluated: {pr_metrics.get('total', 0):<6} | Merged: {pr_metrics.get('merged', 0):<6} | Open: {pr_metrics.get('open', 0):<6}")
        lines.append(f"    Merge Rate:      {pr_metrics.get('merge_rate_pct', 0)}%")
        lines.append(f"    Mean Time to Merge (MTTM): {pr_metrics.get('avg_merge_time_hours', 0)} hrs")
        lines.append("-" * 72)

        # Issue Resolution
        lines.append("  [ISSUE RESOLUTION & VELOCITY]")
        lines.append(f"    Total Evaluated: {issue_metrics.get('total', 0):<6} | Closed: {issue_metrics.get('closed', 0):<6} | Open: {issue_metrics.get('open', 0):<6}")
        lines.append(f"    Resolution Rate: {issue_metrics.get('resolution_rate_pct', 0)}%")
        lines.append(f"    Mean Time to Resolution (MTTR): {issue_metrics.get('avg_resolution_time_hours', 0)} hrs")
        lines.append("-" * 72)

        # Contributor Distribution
        lines.append("  [CONTRIBUTOR METRICS]")
        lines.append(f"    Total Contributors: {contributor_metrics.get('total_contributors', 0)}")
        top_contribs = contributor_metrics.get("top_contributors", [])
        if top_contribs:
            lines.append("    Top Contributors:")
            for tc in top_contribs[:5]:
                lines.append(f"      • @{tc['login']:<18} : {tc['contributions']:<4} commits ({tc['share_pct']}%)")
        lines.append("-" * 72)

        # CI Workflow Runs
        lines.append("  [CI / AUTOMATION HEALTH]")
        lines.append(f"    Total Recent Runs: {ci.get('total_runs', 0)} | Success Rate: {ci.get('success_rate_pct', 0)}%")
        lines.append("=" * 72)

        return "\n".join(lines)


class MarkdownFormatter:
    """Renders exportable GitHub-Flavored Markdown reports."""

    @classmethod
    def render_markdown(cls, data: Dict[str, Any]) -> str:
        """Render markdown report suitable for CI or repository docs."""
        repo = data.get("repo", {})
        pr_metrics = data.get("pr_metrics", {})
        issue_metrics = data.get("issue_metrics", {})
        contributor_metrics = data.get("contributor_metrics", {})
        health = data.get("health", {})
        ci = data.get("ci_metrics", {})

        repo_name = repo.get("full_name", "Unknown Repository")

        md = []
        md.append(f"# Engineering Health Report: {repo_name}\n")
        md.append(f"Generated via `gh-dashboard` | Target: [{repo_name}](https://github.com/{repo_name})\n")

        # Snapshot
        md.append("## 1. Repository Snapshot\n")
        md.append("| Metric | Value |")
        md.append("|---|---|")
        md.append(f"| **Primary Language** | {repo.get('language') or 'N/A'} |")
        md.append(f"| **Stars** | {repo.get('stargazers_count', 0)} |")
        md.append(f"| **Forks** | {repo.get('forks_count', 0)} |")
        md.append(f"| **Health Score** | **{health.get('health_score', 0)} / 100** (Grade {health.get('health_grade', 'N/A')}) |")
        md.append(f"| **CI Success Rate** | {ci.get('success_rate_pct', 0)}% |\n")

        # PRs
        md.append("## 2. Pull Request Velocity\n")
        md.append("| Metric | Result |")
        md.append("|---|---|")
        md.append(f"| Total PRs Analyzed | {pr_metrics.get('total', 0)} |")
        md.append(f"| Merged PRs | {pr_metrics.get('merged', 0)} |")
        md.append(f"| Open PRs | {pr_metrics.get('open', 0)} |")
        md.append(f"| Merge Rate | **{pr_metrics.get('merge_rate_pct', 0)}%** |")
        md.append(f"| Mean Time to Merge (MTTM) | {pr_metrics.get('avg_merge_time_hours', 0)} hours |\n")

        # Issues
        md.append("## 3. Issue Resolution & MTTR\n")
        md.append("| Metric | Result |")
        md.append("|---|---|")
        md.append(f"| Total Issues Analyzed | {issue_metrics.get('total', 0)} |")
        md.append(f"| Closed Issues | {issue_metrics.get('closed', 0)} |")
        md.append(f"| Open Issues | {issue_metrics.get('open', 0)} |")
        md.append(f"| Resolution Rate | **{issue_metrics.get('resolution_rate_pct', 0)}%** |")
        md.append(f"| Mean Time to Resolution (MTTR) | {issue_metrics.get('avg_resolution_time_hours', 0)} hours |\n")

        # Contributors
        md.append("## 4. Key Contributors\n")
        md.append("| Contributor | Commits | Contribution Share |")
        md.append("|---|---|---|")
        for tc in contributor_metrics.get("top_contributors", [])[:5]:
            md.append(f"| [@{tc['login']}](https://github.com/{tc['login']}) | {tc['contributions']} | {tc['share_pct']}% |")

        # Health Breakdown
        md.append("\n## 5. Standards & Health Audit\n")
        md.append("| Check | Points | Status |")
        md.append("|---|---|---|")
        for c in health.get("checks", []):
            icon = "✅" if c["status"] == "PASS" else "❌"
            md.append(f"| {c['check']} | {c['points']} | {icon} {c['status']} |")

        return "\n".join(md)
