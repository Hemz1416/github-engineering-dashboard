# GitHub Engineering Dashboard (`gh-dashboard`)

[![CI](https://github.com/Hemz1416/github-engineering-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/Hemz1416/github-engineering-dashboard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Clean](https://img.shields.io/badge/code%20style-pep8-green.svg)](https://www.python.org/dev/peps/pep-0008/)

**GitHub Engineering Dashboard** (`gh-dashboard`) is a zero-third-party-dependency CLI tool and engineering metrics engine for engineering leads, maintainers, and developers to analyze repository health, pull request velocity, issue resolution latency (MTTR), and contributor distribution via the **GitHub REST API v3** and **GraphQL API v4**.

---

## 🚀 Features

- **⚡ Pull Request Velocity:** Computes merge ratios, Mean Time to Merge (MTTM), and turnaround times.
- **🎯 Issue Tracking & Backlog Reconciliation:** Reconciles sample MTTR with repository-level open backlogs.
- **👥 Contributor Insights:** Maps key contributor commit distribution and community engagement.
- **🛡️ Community Health Audit:** Grades repository documentation, licensing, security policies, and issue templates (0–100 scale).
- **💬 Community Discussions (GraphQL API v4):** Queries repository discussions and answer resolution status.
- **🤖 CI/CD Workflow Health:** Tracks GitHub Actions run success rates and failure patterns.
- **📊 Rate Limit Monitoring:** Real-time tracking of REST and GraphQL quota consumption.
- **📄 Multi-Format Export:** Generates clean ANSI terminal tables, exportable Markdown reports, and machine-readable JSON data.
- **🔒 Zero-Config Authentication:** Seamlessly integrates with the GitHub CLI (`gh auth token`) or standard `GITHUB_TOKEN` environment variables.

---

## 🖥️ Illustrative Terminal Output (Sample Preview)

> *Note: The following output is illustrative sample data demonstrating metrics computation for an open-source repository (`tiangolo/fastapi`). Run `gh-dashboard audit <owner/repo>` to generate live metrics for any repository.*

```text
============================================================================
  GITHUB ENGINEERING DASHBOARD :: tiangolo/fastapi
============================================================================
  Stars: 78500  | Forks: 6400   | Language: Python     | Health: 85/100 (Grade A)
----------------------------------------------------------------------------
  [PULL REQUEST VELOCITY]
    Evaluated:   100    | Merged: 64     | Open: 22    
    Merge Rate:  82.1%
    Mean Time to Merge (MTTM): 36.4 hrs (1.5 days)
----------------------------------------------------------------------------
  [ISSUE RESOLUTION & VELOCITY]
    Evaluated:   100    | Closed: 78     | Open: 22    
    Repository Open Backlog:   240 total issues
    Resolution Rate:           78.0%
    Mean Time to Resolution:   48.2 hrs (2.0 days)
----------------------------------------------------------------------------
  [COMMUNITY DISCUSSIONS (GRAPHQL API v4)]
    Total Discussions: 1840
----------------------------------------------------------------------------
  [CI / AUTOMATION HEALTH (GITHUB ACTIONS)]
    Recent Runs Evaluated: 10 | Success Rate: 100.0%
----------------------------------------------------------------------------
  [API QUOTA] Remaining: 4965 / 5000 requests
============================================================================
```

---

## 📦 Installation

### From Source
```bash
git clone https://github.com/Hemz1416/github-engineering-dashboard.git
cd github-engineering-dashboard
pip install -e .
```

---

## 🛠️ Usage

### 1. Run a Full Engineering Audit
```bash
gh-dashboard audit tiangolo/fastapi
# or with python directly:
python -m gh_dashboard.cli audit tiangolo/fastapi
```

### 2. Inspect API Rate Limit Quotas
```bash
gh-dashboard rate-limit
```

### 3. Check Community Health & Standards Compliance
```bash
gh-dashboard health pydantic/pydantic
```

### 4. Export Markdown Report for CI or Documentation
```bash
gh-dashboard export psf/requests --format markdown --out requests-audit.md
```

### 5. Export Machine-Readable JSON Metrics
```bash
gh-dashboard export octocat/Hello-World --format json --out metrics.json
```

---

## 🏗️ Architecture

```
gh_dashboard/
├── __init__.py      # Version and package exports
├── client.py        # Robust REST v3 & GraphQL v4 API client with rate limit tracking
├── analytics.py     # Pure mathematical & statistical metric calculations
├── formatters.py    # Terminal table rendering and Markdown report generation
└── cli.py           # Command-line interface with subcommands (audit, health, rate-limit, export)
```

---

## 🌐 GitHub Developer Program Integration

This application is built for the **GitHub Developer Program**:
- **REST Endpoints Used:**
  - `GET /repos/{owner}/{repo}` (Repository metadata & backlog)
  - `GET /repos/{owner}/{repo}/community/profile` (Documentation standards)
  - `GET /repos/{owner}/{repo}/pulls` (PR velocity & merge metrics)
  - `GET /repos/{owner}/{repo}/issues` (Issue resolution latency & MTTR)
  - `GET /repos/{owner}/{repo}/contributors` (Contributor commit share)
  - `GET /repos/{owner}/{repo}/releases` (Release cadence)
  - `GET /repos/{owner}/{repo}/actions/runs` (CI workflow reliability)
  - `GET /rate_limit` (Quota tracking)
- **GraphQL Endpoints Used:**
  - `POST /graphql` (Repository discussion count and answered thread resolution)
- **API Versioning:** Uses official `X-GitHub-Api-Version: 2022-11-28`.
- **User-Agent:** Complies with GitHub API requirements (`GitHub-Engineering-Dashboard/0.1.0`).
- **Rate Limit Safeguards:** Tracks headers and handles HTTP 403/429 with `RateLimitExceededError`.
- **Support & Issues:** Community inquiries and bug reports are handled via GitHub Issues.

---

## 🧪 Testing

The test suite runs with standard library `unittest` across Python 3.9 through 3.13:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📄 License

Licensed under the [MIT License](LICENSE). Copyright © 2026 Hemant Ram.
