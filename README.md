# GitHub Engineering Dashboard (`gh-dashboard`)

[![CI](https://github.com/Hemz1416/github-engineering-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/Hemz1416/github-engineering-dashboard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Clean](https://img.shields.io/badge/code%20style-pep8-green.svg)](https://www.python.org/dev/peps/pep-0008/)

**GitHub Engineering Dashboard** (`gh-dashboard`) is a lightweight, zero-third-party-dependency CLI tool and metrics engine for engineering leads, maintainers, and developers to analyze repository health, pull request velocity, issue resolution latency (MTTR), and contributor distribution via GitHub REST and GraphQL APIs.

---

## 🚀 Features

- **⚡ Pull Request Velocity:** Computes merge ratio, Mean Time to Merge (MTTM), and turnaround times.
- **🎯 Issue Tracking & MTTR:** Evaluates issue closure rates and Mean Time to Resolution.
- **👥 Contributor Insights:** Maps key contributor commit distribution and community engagement.
- **🛡️ Community Health Audit:** Grades repository documentation, licensing, security policies, and issue templates (0–100 scale).
- **🤖 CI/CD Workflow Health:** Tracks GitHub Actions run success rates and failure patterns.
- **📄 Multi-Format Export:** Generates rich ANSI terminal views, exportable GitHub-Flavored Markdown reports, and machine-readable JSON data.
- **🔒 Zero-Config Authentication:** Seamlessly integrates with the GitHub CLI (`gh auth token`) or standard `GITHUB_TOKEN` environment variables.

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
# or directly with python:
python -m gh_dashboard.cli audit tiangolo/fastapi
```

### 2. Check Repository Health & Compliance Score
```bash
gh-dashboard health pydantic/pydantic
```

### 3. Export Markdown Report for CI or Documentation
```bash
gh-dashboard export psf/requests --format markdown --out requests-audit.md
```

### 4. Export Machine-Readable JSON Metrics
```bash
gh-dashboard export octocat/Hello-World --format json --out metrics.json
```

---

## 🏗️ Architecture

```
gh_dashboard/
├── __init__.py      # Version and package exports
├── client.py        # Robust GitHub REST API client with automatic token resolution
├── analytics.py     # Pure mathematical & statistical metric calculations
├── formatters.py    # Terminal table rendering and Markdown report generation
└── cli.py           # Command-line interface with subcommands (audit, health, export)
```

---

## 🌐 GitHub Developer Program Integration

This application is built for the **GitHub Developer Program**:
- **API Versioning:** Uses official `X-GitHub-Api-Version: 2022-11-28`.
- **User-Agent:** Complies with GitHub API requirements (`GitHub-Engineering-Dashboard/0.1.0`).
- **Rate Limit Safeguards:** Handles HTTP 403 / 429 rate limits gracefully with descriptive feedback.
- **Support & Issues:** Submit inquiries or bug reports via GitHub Issues.

---

## 🧪 Testing

The test suite runs with standard library `unittest`:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📄 License

Licensed under the [MIT License](LICENSE). Copyright © 2026 Hemant Ram.

