# Quickstart: Services Architecture

**Feature**: 008-services-architecture
**Time to complete**: ~10 minutes

This guide validates the services architecture works end-to-end.

## Prerequisites

- Docker and Docker Compose installed
- Git repository cloned
- `.env` file configured (see below)

## Step 1: Configure Environment

Create `.env` file in repository root:

```bash
# Copy example
cp .env.example .env

# Required for agent services (Claude API)
ANTHROPIC_API_KEY=your-api-key

# Required for GitHub escalation (optional for local testing)
GITHUB_TOKEN=your-github-token
GITHUB_REPO=owner/repo
```

## Step 2: Start All Services

```bash
# Start all services in background
docker-compose up -d

# Verify all services are running
docker-compose ps

# Expected output:
# NAME            STATUS    PORTS
# orchestrator    running   0.0.0.0:8001->8000/tcp
# agent-hub       running   0.0.0.0:8002->8000/tcp
# baron           running   0.0.0.0:8010->8000/tcp
```

## Step 3: Verify Health Checks

```bash
# Check Orchestrator
curl http://localhost:8001/health
# Expected: {"status":"healthy","version":"1.0.0"}

# Check Agent Hub
curl http://localhost:8002/health
# Expected: {"status":"healthy","version":"1.0.0","connected_agents":["baron"]}

# Check Baron Agent
curl http://localhost:8010/health
# Expected: {"status":"healthy","version":"1.0.0","agent_name":"baron"}
```

## Step 4: End-to-End Workflow Test

### 4.1 Create a Workflow

```bash
# Start a specify workflow
curl -X POST http://localhost:8001/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "specify",
    "feature_description": "Add user authentication with OAuth2",
    "context": {"priority": "P1"}
  }'

# Expected response:
# {
#   "id": "abc123...",
#   "workflow_type": "specify",
#   "status": "in_progress",
#   "feature_id": "009-user-auth",
#   "created_at": "2026-01-05T10:00:00Z"
# }
```

### 4.2 Check Workflow Status

```bash
# Replace {workflow_id} with actual ID from previous response
curl http://localhost:8001/workflows/{workflow_id}

# When complete, status will be "waiting_approval" or "completed"
```

### 4.3 Test Agent-to-Agent Communication

```bash
# Ask architecture question through Agent Hub
curl -X POST http://localhost:8002/ask/architecture \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What authentication method should we use?",
    "context": "Building a REST API for web and mobile clients",
    "feature_id": "008-services-architecture"
  }'

# Expected response:
# {
#   "answer": "For a REST API serving web and mobile clients...",
#   "confidence": 85,
#   "status": "resolved",
#   "session_id": "def456..."
# }
```

### 4.4 Test Session Management

```bash
# Create a session
curl -X POST http://localhost:8002/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "@duc",
    "feature_id": "008-services-architecture"
  }'

# Use session for follow-up question
curl -X POST http://localhost:8002/ask/architecture \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How should we handle token refresh?",
    "feature_id": "008-services-architecture",
    "session_id": "{session_id_from_above}"
  }'

# Response will include context from previous question
```

## Step 5: Test Low Confidence Escalation

```bash
# Ask an ambiguous question to trigger low confidence
curl -X POST http://localhost:8002/ask/security \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Should we use encryption?",
    "feature_id": "008-services-architecture"
  }'

# If confidence < 80%, response includes escalation_id
# {
#   "answer": "Generally yes, but it depends on...",
#   "confidence": 65,
#   "status": "pending_human",
#   "escalation_id": "esc123..."
# }

# Check escalation status
curl http://localhost:8002/escalations/{escalation_id}

# Submit human response (simulating GitHub comment)
curl -X POST http://localhost:8002/escalations/{escalation_id} \
  -H "Content-Type: application/json" \
  -d '{
    "action": "confirm",
    "responder": "@johndoe"
  }'
```

## Step 6: Verify Audit Logs

```bash
# Logs are written to ./data/logs/qa/
ls -la ./data/logs/qa/

# View logs for feature
cat ./data/logs/qa/008-services-architecture.jsonl
```

## Step 7: Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean state)
docker-compose down -v
```

## Validation Checklist

- [ ] All three services start successfully
- [ ] Health endpoints return healthy status
- [ ] Workflow creation works
- [ ] Agent Hub routes to Baron
- [ ] Sessions preserve context
- [ ] Low confidence triggers escalation
- [ ] Audit logs are written

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs orchestrator
docker-compose logs agent-hub
docker-compose logs baron

# Rebuild images
docker-compose build --no-cache
```

### Agent timeout errors

```bash
# Check ANTHROPIC_API_KEY is set
docker-compose exec agent-hub env | grep ANTHROPIC

# Increase timeout in docker-compose.yml
# AGENT_TIMEOUT_SECONDS=600
```

### Session not found

```bash
# Sessions expire after 1 hour by default
# Check session status
curl http://localhost:8002/sessions/{session_id}
```

## Success Criteria Validation

| Criteria | Test | Expected |
|----------|------|----------|
| SC-001 | `docker-compose up` | Services start in < 60s |
| SC-002 | Workflow creation | Completes successfully |
| SC-003 | Agent communication | < 1s overhead |
| SC-005 | Low confidence | Escalation created < 5s |
| SC-006 | Session | Context preserved across 5 messages |
| SC-007 | Audit logs | 100% of invocations logged |
