"""Unit tests for GitHubClient, rate-limiting, and CLI utilities."""

import unittest
from unittest.mock import patch, MagicMock
from gh_dashboard.client import GitHubClient, GitHubAPIError, RateLimitExceededError
from gh_dashboard.cli import parse_repo_arg
from gh_dashboard.formatters import format_hours_readable


class TestGitHubClient(unittest.TestCase):

    def test_parse_repo_arg(self):
        owner, repo = parse_repo_arg("Hemz1416/Poke-dwonload")
        self.assertEqual(owner, "Hemz1416")
        self.assertEqual(repo, "Poke-dwonload")

        owner, repo = parse_repo_arg("https://github.com/torvalds/linux/")
        self.assertEqual(owner, "torvalds")
        self.assertEqual(repo, "linux")

        with self.assertRaises(ValueError):
            parse_repo_arg("invalid-repo-format")

    def test_format_hours_readable(self):
        self.assertEqual(format_hours_readable(0.0), "0.0 hrs")
        self.assertEqual(format_hours_readable(12.5), "12.5 hrs")
        self.assertEqual(format_hours_readable(48.0), "48.0 hrs (2.0 days)")

    @patch("gh_dashboard.client.urllib.request.urlopen")
    def test_client_request_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"name": "test-repo", "stargazers_count": 42}'
        mock_response.headers = {"X-RateLimit-Limit": "5000", "X-RateLimit-Remaining": "4990"}
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = GitHubClient(token="mock-token")
        data = client.get_repo("test-owner", "test-repo")
        self.assertEqual(data["name"], "test-repo")
        self.assertEqual(data["stargazers_count"], 42)
        self.assertEqual(client.last_rate_limit["remaining"], 4990)

    @patch("gh_dashboard.client.urllib.request.urlopen")
    def test_client_graphql_query(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"data": {"repository": {"discussions": {"totalCount": 5}}}}'
        mock_response.headers = {}
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = GitHubClient(token="mock-token")
        res = client.graphql("query { viewer { login } }")
        self.assertEqual(res["repository"]["discussions"]["totalCount"], 5)


if __name__ == "__main__":
    unittest.main()
