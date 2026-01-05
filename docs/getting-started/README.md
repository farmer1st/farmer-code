# Getting Started

This guide will help you set up Farmer Code for development.

## Contents

| Document | Description |
|----------|-------------|
| [Quick Start](./quickstart.md) | 5-minute setup guide |
| [Development Workflow](./development-workflow.md) | How to contribute |

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** - Required for backend
- **uv** - Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Git** - Version control
- **GitHub Account** - With repository access
- **Claude CLI** - For AI agent operations (optional for testing)

## Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/farmer1st/farmer-code.git
cd farmer-code
```

### 2. Install Dependencies

```bash
# Install Python dependencies with uv
uv sync

# Verify installation
uv run python --version
uv run pytest --version
```

### 3. Configure Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# GitHub (required for GitHub integration)
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_REPO=farmer1st/farmer-code

# Claude (optional - for AI agent tests)
ANTHROPIC_API_KEY=sk-ant-your_key
```

### 4. Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific module tests
uv run pytest tests/unit/agent_hub/ -v
```

### 5. Run Linting

```bash
# Check code style
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Type checking
uv run mypy src/
```

## Project Structure

```
farmer-code/
├── src/                      # Source code
│   ├── github_integration/   # GitHub API wrapper
│   ├── worktree_manager/     # Git worktree management
│   ├── orchestrator/         # SDLC workflow state machine
│   └── agent_hub/            # Central agent coordination
├── tests/                    # Test suites
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── contract/             # Contract tests
│   └── e2e/                  # End-to-end tests
├── specs/                    # Feature specifications
│   └── [###-feature-name]/   # Per-feature specs
├── docs/                     # Documentation
├── config/                   # Configuration files
├── .specify/                 # SpecKit templates
└── .plans/                   # Active feature state
```

## Next Steps

1. **Read the Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)
2. **Explore the Architecture**: [docs/architecture/](../architecture/README.md)
3. **Understand the Modules**: [docs/modules/](../modules/README.md)
4. **Review User Journeys**: [docs/user-journeys/](../user-journeys/JOURNEYS.md)

## Common Commands

| Command | Description |
|---------|-------------|
| `uv sync` | Install/update dependencies |
| `uv run pytest` | Run all tests |
| `uv run ruff check .` | Run linter |
| `uv run mypy src/` | Run type checker |
| `uv run pytest -m journey` | Run journey tests only |

## Troubleshooting

### "Module not found" errors

Ensure you're using `uv run`:

```bash
# Wrong
python -m pytest

# Correct
uv run pytest
```

### GitHub API errors

Check your `.env` file has valid credentials:

```bash
# Test GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Test failures

Some tests require GitHub credentials. Set up `.env` properly or run unit tests only:

```bash
# Unit tests only (no external dependencies)
uv run pytest tests/unit/
```

## Getting Help

- Check [docs/](../) for documentation
- Review [user journeys](../user-journeys/JOURNEYS.md) for workflow understanding
- Open an issue on GitHub for bugs
