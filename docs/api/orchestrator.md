# Orchestrator API

Workflow state machine and phase execution.

**Port:** 8000

[**Open Full API Documentation →**](./orchestrator.html){target="_blank" .md-button .md-button--primary}

## Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflows` | POST | Create and start a new workflow |
| `/workflows/{id}` | GET | Get workflow by ID |
| `/workflows/{id}/advance` | POST | Advance workflow to next state |
| `/health` | GET | Health check |
