"""Unit tests for GitHubClient and CLI parsing."""

import unittest
from unittest.mock import patch, MagicMock
from gh_dashboard.client import GitHubClient, GitHubAPIError
from gh_dashboard.cli import parse_repo_arg


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

    @patch("gh_dashboard.client.urllib.request.urlopen")
    def test_client_request_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"name": "test-repo", "stargazers_count": 42}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = GitHubClient(token="mock-token")
        data = client.get_repo("test-owner", "test-repo")
        self.assertEqual(data["name"], "test-repo")
        self.assertEqual(data["stargazers_count"], 42)


if __name__ == "__main__":
    unittest.main()

