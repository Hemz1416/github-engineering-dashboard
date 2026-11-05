from setuptools import setup, find_packages

setup(
    name="github-engineering-dashboard",
    version="0.1.0",
    author="Hemant Ram",
    description="A lightweight engineering metrics and repository analytics CLI powered by GitHub REST and GraphQL APIs.",
    long_description=open("README.md", encoding="utf-8").read() if open("README.md", encoding="utf-8") else "",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "gh-dashboard = gh_dashboard.cli:main",
        ],
    },
)

