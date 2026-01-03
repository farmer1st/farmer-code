# farmcode Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-02

## Active Technologies
- Python 3.11+ + subprocess (stdlib), pathlib (stdlib), Pydantic v2 (validation) (002-git-worktree-manager)
- N/A (operates on filesystem via git) (002-git-worktree-manager)

- Python 3.11+ + PyGithub (GitHub API client), python-dotenv (secrets), python-jose (JWT for GitHub App auth) (001-github-integration-core)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 002-git-worktree-manager: Added Python 3.11+ + subprocess (stdlib), pathlib (stdlib), Pydantic v2 (validation)

- 001-github-integration-core: Added Python 3.11+ + PyGithub (GitHub API client), python-dotenv (secrets), python-jose (JWT for GitHub App auth)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
