# Environment Variables

All environment variables used by Farmer Code services.

## Required Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | All agents | Claude API key |

## Service Ports

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHESTRATOR_PORT` | 8000 | Orchestrator service port |
| `AGENT_HUB_PORT` | 8001 | Agent Hub service port |
| `BARON_PORT` | 8002 | Baron agent port |
| `DUC_PORT` | 8003 | Duc agent port |
| `MARIE_PORT` | 8004 | Marie agent port |

## Service URLs

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_HUB_URL` | http://agent-hub:8001 | Agent Hub URL (for Orchestrator) |
| `ORCHESTRATOR_URL` | http://orchestrator:8000 | Orchestrator URL |
| `BARON_URL` | http://baron:8002 | Baron agent URL |
| `DUC_URL` | http://duc:8003 | Duc agent URL |
| `MARIE_URL` | http://marie:8004 | Marie agent URL |

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | sqlite:///./data/app.db | Database connection string |

## Agent Hub

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIDENCE_THRESHOLD` | 80 | Min confidence for auto-accept |
| `AUDIT_LOG_PATH` | ./logs/audit.jsonl | Audit log file path |
| `SESSION_TIMEOUT_MINUTES` | 60 | Session expiry time |

## Agents

| Variable | Default | Description |
|----------|---------|-------------|
| `BARON_MODEL` | claude-sonnet-4-20250514 | Claude model for Baron |
| `DUC_MODEL` | claude-sonnet-4-20250514 | Claude model for Duc |
| `MARIE_MODEL` | claude-sonnet-4-20250514 | Claude model for Marie |

## GitHub Integration

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | - | GitHub personal access token |
| `GITHUB_APP_ID` | - | GitHub App ID (if using App) |
| `GITHUB_PRIVATE_KEY` | - | GitHub App private key |

## Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_FORMAT` | json | Log format (json/text) |

## Example .env File

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional - GitHub
GITHUB_TOKEN=ghp_...

# Optional - Override ports
# ORCHESTRATOR_PORT=8000
# AGENT_HUB_PORT=8001

# Optional - Override models
# BARON_MODEL=claude-opus-4-20250514
```
