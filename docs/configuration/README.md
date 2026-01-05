# Configuration Guide

How to configure Farmer Code for different environments.

## Contents

| Document | Description |
|----------|-------------|
| [Environment Variables](./environment-variables.md) | All env vars documented |

## Configuration Sources

Farmer Code reads configuration from:

1. **Environment Variables** (`.env` file)
2. **YAML Configuration** (`config/routing.yaml`)
3. **JSON State** (`.plans/{issue}/state.json`)

## Quick Setup

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit with your credentials:

```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=owner/repo
```

3. (Optional) Customize routing:

```bash
cp config/routing.yaml config/routing.local.yaml
# Edit routing.local.yaml
```

## Configuration by Module

### GitHub Integration

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | Personal access token |
| `GITHUB_REPO` | Yes | Repository (owner/repo) |

### Knowledge Router

| File | Purpose |
|------|---------|
| `config/routing.yaml` | Agent routing rules |

### Orchestrator

No additional configuration required. Uses GitHub credentials.

### Worktree Manager

No configuration required. Uses local git settings.

## Environment Files

### `.env` (Local Development)

```env
# GitHub
GITHUB_TOKEN=ghp_your_token
GITHUB_REPO=farmer1st/farmcode

# Claude (optional)
ANTHROPIC_API_KEY=sk-ant-your_key

# Debug
DEBUG=false
LOG_LEVEL=INFO
```

### `.env.example` (Template)

```env
# Copy this to .env and fill in values
GITHUB_TOKEN=
GITHUB_REPO=
ANTHROPIC_API_KEY=
```

## Security

- **Never commit `.env`** - It's in `.gitignore`
- **Use GitHub Secrets** for CI/CD
- **Rotate tokens** periodically
- **Minimum permissions** - Only grant what's needed

## Related Documentation

- [Getting Started](../getting-started/README.md)
- [Constitution - Security](../../.specify/memory/constitution.md)
