# Configuration

Configuration options for Farmer Code services.

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (local) |
| `.env.example` | Template for `.env` |
| `docker-compose.yml` | Service definitions |
| `mkdocs.yml` | Documentation config |
| `pyproject.toml` | Python project config |

## Service Configuration

### Orchestrator

```yaml
# In docker-compose.yml
orchestrator:
  environment:
    - ORCHESTRATOR_PORT=8000
    - AGENT_HUB_URL=http://agent-hub:8001
    - DATABASE_URL=sqlite:///./data/orchestrator.db
```

### Agent Hub

```yaml
agent-hub:
  environment:
    - AGENT_HUB_PORT=8001
    - CONFIDENCE_THRESHOLD=80
    - DATABASE_URL=sqlite:///./data/agent_hub.db
    - AUDIT_LOG_PATH=/app/logs/audit.jsonl
```

### Agents

```yaml
baron:
  environment:
    - BARON_PORT=8002
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    - BARON_MODEL=claude-sonnet-4-20250514
```

## Database Configuration

SQLite is used for local development:

```
DATABASE_URL=sqlite:///./data/service.db
```

For production, use PostgreSQL:

```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

## Logging Configuration

Audit logs are written to JSONL files:

```
AUDIT_LOG_PATH=/app/logs/audit.jsonl
LOG_LEVEL=INFO
```

## See Also

- [Environment Variables](environment.md) - Complete list
- [Running Locally](../guides/running-locally.md) - Setup guide
