# Environment Variables

Complete list of environment variables used by FarmCode.

## Required Variables

### GitHub Integration

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token or app token | `ghp_xxxx...` |
| `GITHUB_REPO` | Target repository in owner/repo format | `farmer1st/farmcode` |

**Token Permissions Required**:
- `repo` - Full control of private repositories
- `workflow` - Update GitHub Action workflows (if using Actions)

### How to Create GitHub Token

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`
4. Copy token to `.env`

## Optional Variables

### Claude AI

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | None |

**Used by**: Knowledge Router for agent dispatch

### Debugging

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

**Log Levels**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## Variable Reference by Module

### github_integration

```env
GITHUB_TOKEN=ghp_xxxx    # Required
GITHUB_REPO=owner/repo   # Required
```

### knowledge_router

```env
ANTHROPIC_API_KEY=sk-ant-xxxx  # Optional (for agent dispatch)
```

### orchestrator

No additional environment variables. Uses GitHub credentials.

### worktree_manager

No environment variables. Uses local git configuration.

## Configuration Files

In addition to environment variables, some modules use configuration files:

| File | Module | Purpose |
|------|--------|---------|
| `config/routing.yaml` | knowledge_router | Agent routing rules |

## Example `.env` File

```env
# ===================
# Required
# ===================

# GitHub Access
GITHUB_TOKEN=ghp_your_personal_access_token_here
GITHUB_REPO=farmer1st/farmcode

# ===================
# Optional
# ===================

# Claude AI (for Knowledge Router agent dispatch)
ANTHROPIC_API_KEY=sk-ant-your_key_here

# Debugging
DEBUG=false
LOG_LEVEL=INFO
```

## Loading Environment Variables

FarmCode uses `python-dotenv` to load `.env`:

```python
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

token = os.getenv("GITHUB_TOKEN")
repo = os.getenv("GITHUB_REPO")
```

## CI/CD Configuration

For GitHub Actions, store secrets in repository settings:

1. Go to Repository > Settings > Secrets and variables > Actions
2. Add secrets:
   - `GITHUB_TOKEN` (or use `secrets.GITHUB_TOKEN`)
   - `ANTHROPIC_API_KEY`

Access in workflow:

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Troubleshooting

### "GITHUB_TOKEN not set"

```
Error: GITHUB_TOKEN environment variable not set
```

**Fix**: Ensure `.env` exists with valid token:

```bash
echo $GITHUB_TOKEN  # Should print token
# If empty, check .env file
```

### "Invalid token"

```
github.GithubException: 401 Bad credentials
```

**Fix**: Regenerate token and update `.env`

### "Repository not found"

```
github.GithubException: 404 Not Found
```

**Fix**: Check `GITHUB_REPO` format is `owner/repo`:

```bash
# Correct
GITHUB_REPO=farmer1st/farmcode

# Wrong
GITHUB_REPO=https://github.com/farmer1st/farmcode
```
