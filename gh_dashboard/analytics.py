"""Engineering Metrics & Analytics Engine.
Calculates PR velocity, MTTR, contributor distribution, and repository health scores.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO-8601 datetime strings from GitHub API."""
    if not dt_str:
        return None
    try:
        # Python 3.7+ can parse ISO strings; replace Z with +00:00
        clean_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None


class EngineeringAnalytics:
    """Computes engineering metrics from raw GitHub API responses."""

    @staticmethod
    def analyze_pull_requests(prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute PR velocity, merge rates, and lead time metrics."""
        total = len(prs)
        if total == 0:
            return {
                "total": 0,
                "open": 0,
                "merged": 0,
                "closed_unmerged": 0,
                "merge_rate_pct": 0.0,
                "avg_merge_time_hours": 0.0,
                "avg_close_time_hours": 0.0,
            }

        open_count = 0
        merged_count = 0
        closed_unmerged_count = 0
        merge_durations_hours: List[float] = []
        close_durations_hours: List[float] = []

        for pr in prs:
            state = pr.get("state")
            merged_at = pr.get("merged_at")
            created_at = parse_iso_datetime(pr.get("created_at"))
            closed_at = parse_iso_datetime(pr.get("closed_at"))

            if state == "open":
                open_count += 1
            elif merged_at:
                merged_count += 1
                if created_at and closed_at:
                    duration = (closed_at - created_at).total_seconds() / 3600.0
                    merge_durations_hours.append(max(0.0, duration))
            else:
                closed_unmerged_count += 1
                if created_at and closed_at:
                    duration = (closed_at - created_at).total_seconds() / 3600.0
                    close_durations_hours.append(max(0.0, duration))

        decided = merged_count + closed_unmerged_count
        merge_rate = (merged_count / decided * 100.0) if decided > 0 else 0.0
        avg_merge_time = (sum(merge_durations_hours) / len(merge_durations_hours)) if merge_durations_hours else 0.0
        avg_close_time = (sum(close_durations_hours) / len(close_durations_hours)) if close_durations_hours else 0.0

        return {
            "total": total,
            "open": open_count,
            "merged": merged_count,
            "closed_unmerged": closed_unmerged_count,
            "merge_rate_pct": round(merge_rate, 1),
            "avg_merge_time_hours": round(avg_merge_time, 1),
            "avg_close_time_hours": round(avg_close_time, 1),
        }

    @staticmethod
    def analyze_issues(issues: List[Dict[str, Any]], total_backlog_hint: Optional[int] = None) -> Dict[str, Any]:
        """Compute issue resolution metrics, MTTR, and reconcile with repository backlog."""
        total = len(issues)
        if total == 0:
            return {
                "total": 0,
                "open": 0,
                "closed": 0,
                "total_open_backlog": total_backlog_hint or 0,
                "resolution_rate_pct": 0.0,
                "avg_resolution_time_hours": 0.0,
            }

        open_count = 0
        closed_count = 0
        resolution_durations_hours: List[float] = []

        for issue in issues:
            state = issue.get("state")
            created_at = parse_iso_datetime(issue.get("created_at"))
            closed_at = parse_iso_datetime(issue.get("closed_at"))

            if state == "open":
                open_count += 1
            else:
                closed_count += 1
                if created_at and closed_at:
                    duration = (closed_at - created_at).total_seconds() / 3600.0
                    resolution_durations_hours.append(max(0.0, duration))

        res_rate = (closed_count / total * 100.0) if total > 0 else 0.0
        avg_mttr = (sum(resolution_durations_hours) / len(resolution_durations_hours)) if resolution_durations_hours else 0.0

        return {
            "total": total,
            "open": open_count,
            "closed": closed_count,
            "total_open_backlog": total_backlog_hint if total_backlog_hint is not None else open_count,
            "resolution_rate_pct": round(res_rate, 1),
            "avg_resolution_time_hours": round(avg_mttr, 1),
        }

    @staticmethod
    def analyze_contributors(contributors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contributor distribution and identify key contributors."""
        total_contributors = len(contributors)
        total_contributions = sum(c.get("contributions", 0) for c in contributors)

        top_contributors = []
        for c in contributors[:10]:
            contribs = c.get("contributions", 0)
            pct = (contribs / total_contributions * 100.0) if total_contributions > 0 else 0.0
            top_contributors.append({
                "login": c.get("login", "unknown"),
                "contributions": contribs,
                "share_pct": round(pct, 1),
            })

        return {
            "total_contributors": total_contributors,
            "total_contributions": total_contributions,
            "top_contributors": top_contributors,
        }

    @staticmethod
    def calculate_health_score(repo: Dict[str, Any], community: Dict[str, Any]) -> Dict[str, Any]:
        """Compute an overall Repository Health Score (0-100) based on standards."""
        score = 0
        breakdown = []

        # 1. Description
        if repo.get("description"):
            score += 10
            breakdown.append({"check": "Description provided", "points": 10, "status": "PASS"})
        else:
            breakdown.append({"check": "Description provided", "points": 0, "status": "FAIL"})

        # 2. License
        if repo.get("license") or (community.get("files", {}).get("license")):
            score += 20
            breakdown.append({"check": "Open Source License", "points": 20, "status": "PASS"})
        else:
            breakdown.append({"check": "Open Source License", "points": 0, "status": "FAIL"})

        # 3. README
        if community.get("files", {}).get("readme"):
            score += 20
            breakdown.append({"check": "README Documentation", "points": 20, "status": "PASS"})
        else:
            breakdown.append({"check": "README Documentation", "points": 0, "status": "FAIL"})

        # 4. Code of Conduct
        if community.get("files", {}).get("code_of_conduct"):
            score += 10
            breakdown.append({"check": "Code of Conduct", "points": 10, "status": "PASS"})
        else:
            breakdown.append({"check": "Code of Conduct", "points": 0, "status": "FAIL"})

        # 5. Contributing Guidelines
        if community.get("files", {}).get("contributing"):
            score += 15
            breakdown.append({"check": "CONTRIBUTING.md Guide", "points": 15, "status": "PASS"})
        else:
            breakdown.append({"check": "CONTRIBUTING.md Guide", "points": 0, "status": "FAIL"})

        # 6. Issue Templates
        if community.get("files", {}).get("issue_template"):
            score += 10
            breakdown.append({"check": "Issue Templates", "points": 10, "status": "PASS"})
        else:
            breakdown.append({"check": "Issue Templates", "points": 0, "status": "FAIL"})

        # 7. Pull Request Template
        if community.get("files", {}).get("pull_request_template"):
            score += 10
            breakdown.append({"check": "PR Template", "points": 10, "status": "PASS"})
        else:
            breakdown.append({"check": "PR Template", "points": 0, "status": "FAIL"})

        # 8. Security Policy
        if community.get("files", {}).get("security"):
            score += 5
            breakdown.append({"check": "SECURITY.md Policy", "points": 5, "status": "PASS"})
        else:
            breakdown.append({"check": "SECURITY.md Policy", "points": 0, "status": "FAIL"})

        return {
            "health_score": min(100, score),
            "health_grade": "A" if score >= 85 else ("B" if score >= 70 else ("C" if score >= 50 else "D")),
            "checks": breakdown,
        }

    @staticmethod
    def analyze_ci_runs(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute CI workflow reliability statistics."""
        total = len(runs)
        if total == 0:
            return {"total_runs": 0, "success_rate_pct": 0.0, "recent_statuses": []}

        successes = sum(1 for r in runs if r.get("conclusion") == "success")
        rate = (successes / total * 100.0) if total > 0 else 0.0

        recent = []
        for r in runs[:5]:
            recent.append({
                "name": r.get("name", "workflow"),
                "status": r.get("status"),
                "conclusion": r.get("conclusion") or "in_progress",
                "created_at": r.get("created_at"),
            })

        return {
            "total_runs": total,
            "success_rate_pct": round(rate, 1),
            "recent_statuses": recent,
        }

