"""Formatters for CLI terminal output and Markdown report generation.
Supports human-readable durations, GraphQL discussion analytics, and rate-limit reporting.
"""

import json
from typing import Any, Dict


def format_hours_readable(hours: float) -> str:
    """Format hour counts into friendly hour + day representations."""
    if hours <= 0:
        return "0.0 hrs"
    if hours >= 24.0:
        days = hours / 24.0
        return f"{hours:.1f} hrs ({days:.1f} days)"
    return f"{hours:.1f} hrs"


class TerminalFormatter:
    """Renders formatted ASCII/ANSI terminal tables and summaries."""

    @classmethod
    def render_dashboard(cls, data: Dict[str, Any], use_color: bool = True) -> str:
        """Render complete terminal dashboard view."""
        repo = data.get("repo", {})
        pr_metrics = data.get("pr_metrics", {})
        issue_metrics = data.get("issue_metrics", {})
        contributor_metrics = data.get("contributor_metrics", {})
        health = data.get("health", {})
        ci = data.get("ci_metrics", {})
        discussions = data.get("discussions_metrics", {})
        rate_limit = data.get("rate_limit_info", {})

        repo_name = repo.get("full_name", "Unknown Repository")
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        lang = repo.get("language") or "N/A"
        grade = health.get("health_grade", "N/A")
        score = health.get("health_score", 0)

        lines = []
        lines.append("=" * 76)
        lines.append(f"  GITHUB ENGINEERING DASHBOARD :: {repo_name}")
        lines.append("=" * 76)
        lines.append(f"  Stars: {stars:<6} | Forks: {forks:<6} | Language: {lang:<10} | Health: {score}/100 (Grade {grade})")
        lines.append("-" * 76)

        # Pull Request Velocity
        mttm_str = format_hours_readable(pr_metrics.get("avg_merge_time_hours", 0.0))
        lines.append("  [PULL REQUEST VELOCITY]")
        lines.append(f"    Evaluated:   {pr_metrics.get('total', 0):<6} | Merged: {pr_metrics.get('merged', 0):<6} | Open: {pr_metrics.get('open', 0):<6}")
        lines.append(f"    Merge Rate:  {pr_metrics.get('merge_rate_pct', 0)}%")
        lines.append(f"    Mean Time to Merge (MTTM): {mttm_str}")
        lines.append("-" * 76)

        # Issue Resolution
        mttr_str = format_hours_readable(issue_metrics.get("avg_resolution_time_hours", 0.0))
        lines.append("  [ISSUE RESOLUTION & VELOCITY]")
        lines.append(f"    Evaluated:   {issue_metrics.get('total', 0):<6} | Closed: {issue_metrics.get('closed', 0):<6} | Open: {issue_metrics.get('open', 0):<6}")
        if issue_metrics.get("total_open_backlog", 0) > issue_metrics.get("open", 0):
            lines.append(f"    Repository Open Backlog:   {issue_metrics.get('total_open_backlog')} total issues")
        lines.append(f"    Resolution Rate:           {issue_metrics.get('resolution_rate_pct', 0)}%")
        lines.append(f"    Mean Time to Resolution:   {mttr_str}")
        lines.append("-" * 76)

        # Contributor Distribution
        lines.append("  [CONTRIBUTOR METRICS]")
        lines.append(f"    Total Contributors: {contributor_metrics.get('total_contributors', 0)}")
        top_contribs = contributor_metrics.get("top_contributors", [])
        if top_contribs:
            lines.append("    Top Contributors:")
            for tc in top_contribs[:5]:
                lines.append(f"      • @{tc['login']:<18} : {tc['contributions']:<4} commits ({tc['share_pct']}%)")
        lines.append("-" * 76)

        # GitHub Discussions (GraphQL)
        total_disc = discussions.get("total_discussions", 0)
        lines.append("  [COMMUNITY DISCUSSIONS (GRAPHQL API v4)]")
        lines.append(f"    Total Discussions: {total_disc}")
        recent_disc = discussions.get("recent_discussions", [])
        if recent_disc:
            lines.append("    Recent Threads:")
            for d in recent_disc[:3]:
                answered = " [Answered]" if d.get("isAnswered") else ""
                lines.append(f"      • {d.get('title')[:55]}{answered}")
        lines.append("-" * 76)

        # CI / Workflow Health
        lines.append("  [CI / AUTOMATION HEALTH (GITHUB ACTIONS)]")
        lines.append(f"    Recent Runs Evaluated: {ci.get('total_runs', 0)} | Success Rate: {ci.get('success_rate_pct', 0)}%")

        # Rate Limit Footer
        rem = rate_limit.get("remaining")
        limit = rate_limit.get("limit")
        if rem is not None and limit is not None:
            lines.append("-" * 76)
            lines.append(f"  [API QUOTA] Remaining: {rem} / {limit} requests")
        lines.append("=" * 76)

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
        discussions = data.get("discussions_metrics", {})

        repo_name = repo.get("full_name", "Unknown Repository")
        mttm_str = format_hours_readable(pr_metrics.get("avg_merge_time_hours", 0.0))
        mttr_str = format_hours_readable(issue_metrics.get("avg_resolution_time_hours", 0.0))

        md = []
        md.append(f"# Engineering Health Report: {repo_name}\n")
        md.append(f"Generated via `gh-dashboard` (REST v3 & GraphQL v4) | Target: [{repo_name}](https://github.com/{repo_name})\n")

        # Snapshot
        md.append("## 1. Repository Snapshot\n")
        md.append("| Metric | Value |")
        md.append("|---|---|")
        md.append(f"| **Primary Language** | {repo.get('language') or 'N/A'} |")
        md.append(f"| **Stars** | {repo.get('stargazers_count', 0)} |")
        md.append(f"| **Forks** | {repo.get('forks_count', 0)} |")
        md.append(f"| **Health Score** | **{health.get('health_score', 0)} / 100** (Grade {health.get('health_grade', 'N/A')}) |")
        md.append(f"| **Discussions Count** | {discussions.get('total_discussions', 0)} |")
        md.append(f"| **CI Success Rate** | {ci.get('success_rate_pct', 0)}% |\n")

        # PRs
        md.append("## 2. Pull Request Velocity\n")
        md.append("| Metric | Result |")
        md.append("|---|---|")
        md.append(f"| Total PRs Evaluated | {pr_metrics.get('total', 0)} |")
        md.append(f"| Merged PRs | {pr_metrics.get('merged', 0)} |")
        md.append(f"| Open PRs | {pr_metrics.get('open', 0)} |")
        md.append(f"| Merge Rate | **{pr_metrics.get('merge_rate_pct', 0)}%** |")
        md.append(f"| Mean Time to Merge (MTTM) | {mttm_str} |\n")

        # Issues
        md.append("## 3. Issue Resolution & MTTR\n")
        md.append("| Metric | Result |")
        md.append("|---|---|")
        md.append(f"| Total Issues Evaluated | {issue_metrics.get('total', 0)} |")
        md.append(f"| Closed Issues | {issue_metrics.get('closed', 0)} |")
        md.append(f"| Open Issues | {issue_metrics.get('open', 0)} |")
        md.append(f"| Resolution Rate | **{issue_metrics.get('resolution_rate_pct', 0)}%** |")
        md.append(f"| Mean Time to Resolution (MTTR) | {mttr_str} |\n")

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
