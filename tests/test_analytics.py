"""Unit tests for EngineeringAnalytics engine."""

import unittest
from gh_dashboard.analytics import EngineeringAnalytics, parse_iso_datetime
from gh_dashboard.formatters import CsvFormatter


class TestEngineeringAnalytics(unittest.TestCase):

    def test_parse_iso_datetime(self):
        dt = parse_iso_datetime("2026-11-02T05:54:27Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 11)
        self.assertEqual(dt.day, 2)

        self.assertIsNone(parse_iso_datetime(None))
        self.assertIsNone(parse_iso_datetime("invalid-date"))

    def test_analyze_pull_requests_empty(self):
        metrics = EngineeringAnalytics.analyze_pull_requests([])
        self.assertEqual(metrics["total"], 0)
        self.assertEqual(metrics["merge_rate_pct"], 0.0)

    def test_analyze_pull_requests_calculation(self):
        prs = [
            {
                "state": "closed",
                "merged_at": "2026-11-02T10:00:00Z",
                "created_at": "2026-11-02T08:00:00Z",
                "closed_at": "2026-11-02T10:00:00Z",
            },
            {
                "state": "closed",
                "merged_at": None,
                "created_at": "2026-11-02T07:00:00Z",
                "closed_at": "2026-11-02T08:00:00Z",
            },
            {
                "state": "open",
                "merged_at": None,
                "created_at": "2026-11-02T09:00:00Z",
                "closed_at": None,
            }
        ]
        metrics = EngineeringAnalytics.analyze_pull_requests(prs)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["open"], 1)
        self.assertEqual(metrics["merged"], 1)
        self.assertEqual(metrics["closed_unmerged"], 1)
        self.assertEqual(metrics["merge_rate_pct"], 50.0)
        self.assertEqual(metrics["avg_merge_time_hours"], 2.0)
        self.assertEqual(metrics["avg_close_time_hours"], 1.0)

    def test_analyze_issues(self):
        issues = [
            {
                "state": "closed",
                "created_at": "2026-11-01T00:00:00Z",
                "closed_at": "2026-11-01T04:00:00Z",
            },
            {
                "state": "open",
                "created_at": "2026-11-01T02:00:00Z",
                "closed_at": None,
            }
        ]
        metrics = EngineeringAnalytics.analyze_issues(issues, total_backlog_hint=42)
        self.assertEqual(metrics["total"], 2)
        self.assertEqual(metrics["open"], 1)
        self.assertEqual(metrics["closed"], 1)
        self.assertEqual(metrics["total_open_backlog"], 42)
        self.assertEqual(metrics["resolution_rate_pct"], 50.0)
        self.assertEqual(metrics["avg_resolution_time_hours"], 4.0)

    def test_calculate_health_score(self):
        repo = {"description": "A great project"}
        community = {
            "files": {
                "readme": {"url": "readme.md"},
                "license": {"key": "mit"},
                "contributing": {"url": "contributing.md"},
            }
        }
        health = EngineeringAnalytics.calculate_health_score(repo, community)
        self.assertEqual(health["health_score"], 65)  # 10 (desc) + 20 (readme) + 20 (license) + 15 (contributing)
        self.assertEqual(health["health_grade"], "C")

    def test_analyze_contributors(self):
        contributors = [
            {"login": "alice", "contributions": 80},
            {"login": "bob", "contributions": 20},
        ]
        result = EngineeringAnalytics.analyze_contributors(contributors)
        self.assertEqual(result["total_contributors"], 2)
        self.assertEqual(result["total_contributions"], 100)
        self.assertEqual(result["top_contributors"][0]["login"], "alice")
        self.assertEqual(result["top_contributors"][0]["share_pct"], 80.0)

    def test_render_csv(self):
        sample_data = {
            "repo": {"full_name": "test/repo", "language": "Python", "stargazers_count": 10, "forks_count": 2},
            "pr_metrics": {"total": 5, "merged": 4, "open": 1, "merge_rate_pct": 80.0, "avg_merge_time_hours": 12.0},
            "issue_metrics": {"total": 3, "closed": 2, "open": 1, "total_open_backlog": 5, "resolution_rate_pct": 66.7, "avg_resolution_time_hours": 8.0},
            "contributor_metrics": {"total_contributors": 2},
            "health": {"health_score": 85, "health_grade": "A"},
            "ci_metrics": {"total_runs": 10, "success_rate_pct": 100.0},
            "discussions_metrics": {"total_discussions": 7},
        }
        csv_out = CsvFormatter.render_csv(sample_data)
        self.assertIn("metric,value", csv_out)
        self.assertIn("repository,test/repo", csv_out)
        self.assertIn("pr_merge_rate_pct,80.0", csv_out)
        self.assertIn("health_score,85", csv_out)


if __name__ == "__main__":
    unittest.main()

