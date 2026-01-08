# Agent Hub API

Agent routing, sessions, and human escalations.

**Port:** 8001

[**Open Full API Documentation →**](./agent-hub.html){target="_blank" .md-button .md-button--primary}

## Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask/{topic}` | POST | Ask expert by topic |
| `/invoke/{agent}` | POST | Invoke a specific agent |
| `/sessions` | POST | Create session |
| `/sessions/{id}` | GET | Get session with messages |
| `/sessions/{id}` | DELETE | Close session |
| `/escalations/{id}` | GET | Get escalation status |
| `/escalations/{id}` | POST | Submit human response |
| `/health` | GET | Health check |
