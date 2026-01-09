# Simplified Workflow Architecture (Draft)

**Status:** Draft for review - to be merged into r-and-d-architecture.md
**Version:** 0.4.0-draft

---

## 1. Core Principles

### 1.1 The Two Sources of Truth

| Source | What It Holds | Why |
|--------|---------------|-----|
| **Git** | The work (code, specs, test results) | Commits are immutable, auditable, the actual deliverable |
| **Kubernetes CRD** | The pointer (which phase, which commit) | Crash-recoverable, kubectl-editable, no external DB needed |

DynamoDB is **not** in the critical path. It receives fire-and-forget events for analytics and stores deployment records for rollback capability.

### 1.2 One Commit Per Phase

Each workflow phase produces exactly **one atomic commit**. This commit contains:
- The phase's primary artifact (spec.md, plan.md, code changes, etc.)
- A journal entry (`journal/{phase}.json`) with structured results

The orchestrator's job is simple: **poll Git for new commits, advance the phase index**.

---

## 2. The IssueWorkflow CRD

```yaml
apiVersion: farmercode.io/v1
kind: IssueWorkflow
metadata:
  name: issue-42
  namespace: farmercode          # CRD lives in infra namespace
spec:
  # === CONTEXT ===
  repo: "farmer1st/my-app"
  branch: "feature/42-avatars"
  issueNumber: 42

  # === COST CONTROL ===
  # Delete namespace N seconds after completion/failure
  ttlSecondsAfterFinished: 14400  # 4 hours

  # === PHASE TIMEOUT ===
  # Max time for any single phase (includes human escalation wait)
  phaseTimeoutSeconds: 28800      # 8 hours

  # === STATIC WORKFLOW MAP ===
  # Fixed SOP - agents cannot modify this
  phases:
    - name: SPECIFY
      agent: baron
    - name: PLAN
      agent: baron
    - name: TASKS
      agent: baron
    - name: TEST_DESIGN
      agent: marie
    - name: IMPLEMENT_BACKEND
      agent: dede
    - name: IMPLEMENT_FRONTEND
      agent: dali
    - name: IMPLEMENT_GITOPS
      agent: gus
    - name: VERIFY
      agent: marie
    - name: DOCS_QA
      agent: victor
    - name: REVIEW
      agent: general
    - name: RELEASE_DEV
      agent: gus
    - name: RELEASE_STAGING
      agent: gus
    - name: RELEASE_PROD
      agent: gus
    - name: RETRO
      agent: socrate

status:
  # === THE POINTER ===
  currentPhaseIndex: 4            # Currently on IMPLEMENT_BACKEND
  state: RUNNING                  # PENDING | RUNNING | COMPLETED | FAILED

  # === GIT WATERMARK ===
  lastCommitSha: "a1b2c3d4"       # Only look for commits AFTER this

  # === TIMESTAMPS ===
  startTime: "2026-01-09T10:00:00Z"
  phaseStartTime: "2026-01-09T14:30:00Z"  # When current phase began
  finishTime: null                # Set when COMPLETED or FAILED

  # === CURRENT PHASE TRACKING ===
  currentAttempt: 1               # Retry count for current phase
  lastResult: null                # Last journal result (success/failed/skipped)

  # === WORKFLOW NAMESPACE ===
  workflowNamespace: fc-issue-42  # Ephemeral namespace for this workflow
```

---

## 3. The Orchestrator Loop

The orchestrator is a stateless pod that runs a simple polling loop.

```python
class Orchestrator:
    POLL_INTERVAL = 5  # seconds

    async def run(self):
        """Main loop - poll Git, advance phases."""
        while True:
            try:
                await self.tick()
            except Exception as e:
                logger.error(f"Tick failed: {e}")
            await asyncio.sleep(self.POLL_INTERVAL)

    async def tick(self):
        """Single iteration of the orchestrator loop."""
        # 1. Read current state from CRD
        crd = await self.k8s.get_crd(self.issue_id)

        if crd.status.state in ("COMPLETED", "FAILED"):
            return  # Nothing to do

        phase = crd.spec.phases[crd.status.currentPhaseIndex]

        # 2. Check for timeout
        if self.is_phase_timed_out(crd):
            await self.fail_workflow(crd, f"Phase {phase.name} timed out")
            return

        # 3. Check Git for new commits
        new_commits = await self.git.get_commits_since(crd.status.lastCommitSha)

        if not new_commits:
            # No new commits - ensure agent is working
            await self.ensure_agent_triggered(crd, phase)
            return

        # 4. Found commit(s) - check journal for result
        latest_commit = new_commits[-1]
        journal = await self.read_journal(phase.name, latest_commit.sha)

        if journal is None:
            # Commit exists but no journal - agent still working (partial commit)
            logger.debug(f"Commit {latest_commit.sha[:8]} has no journal, waiting...")
            return

        # 5. Process journal result
        await self.process_phase_result(crd, phase, journal, latest_commit.sha)

    async def process_phase_result(self, crd, phase, journal, commit_sha):
        """Handle phase completion based on journal result."""

        # Log to DynamoDB (fire-and-forget)
        asyncio.create_task(self.log_phase_completed(crd, phase, journal))

        if journal.result == "success" or journal.result == "skipped":
            # Advance to next phase
            next_index = crd.status.currentPhaseIndex + 1

            if next_index >= len(crd.spec.phases):
                # Workflow complete
                await self.k8s.patch_crd_status(crd.name, {
                    "state": "COMPLETED",
                    "lastCommitSha": commit_sha,
                    "finishTime": datetime.utcnow().isoformat(),
                })
            else:
                # Move to next phase
                await self.k8s.patch_crd_status(crd.name, {
                    "currentPhaseIndex": next_index,
                    "lastCommitSha": commit_sha,
                    "phaseStartTime": datetime.utcnow().isoformat(),
                    "currentAttempt": 1,
                    "lastResult": journal.result,
                })

        elif journal.result == "failed":
            # Phase failed - mark workflow as failed
            await self.fail_workflow(crd, f"Phase {phase.name} failed: {journal.reason}")

    async def ensure_agent_triggered(self, crd, phase):
        """Trigger agent if not already working."""
        # Use A2A to send task to agent
        # Agent is responsible for idempotency (won't restart if already working)
        await self.a2a.send_task(
            agent=phase.agent,
            method="tasks/send",
            params={
                "message": {
                    "role": "user",
                    "parts": [{
                        "type": "text",
                        "text": json.dumps({
                            "phase": phase.name,
                            "issue_id": crd.metadata.name,
                            "repo": crd.spec.repo,
                            "branch": crd.spec.branch,
                            "context": await self.build_phase_context(crd, phase),
                        })
                    }]
                }
            }
        )

    async def fail_workflow(self, crd, reason: str):
        """Mark workflow as failed."""
        await self.k8s.patch_crd_status(crd.name, {
            "state": "FAILED",
            "finishTime": datetime.utcnow().isoformat(),
            "lastResult": "failed",
            "failureReason": reason,
        })
        # Log to DynamoDB
        asyncio.create_task(self.log_workflow_failed(crd, reason))
```

---

## 4. The Journal Protocol

Each phase commits a journal file with structured results. This is how the orchestrator knows the phase outcome.

### 4.1 Journal Location

```
specs/{issue-id}/
├── spec.md                    # SPECIFY artifact
├── plan.md                    # PLAN artifact
├── tasks.md                   # TASKS artifact
└── journal/
    ├── specify.json           # SPECIFY result
    ├── plan.json              # PLAN result
    ├── tasks.json             # TASKS result
    ├── test-design.json       # TEST_DESIGN result
    ├── implement-backend.json # IMPLEMENT_BACKEND result
    ├── implement-frontend.json
    ├── implement-gitops.json
    ├── verify.json            # VERIFY result (test pass/fail)
    ├── docs-qa.json
    ├── review.json            # REVIEW result (approved/rejected)
    ├── release-dev.json       # RELEASE_DEV result
    ├── release-staging.json
    ├── release-prod.json
    └── retro.json
```

### 4.2 Journal Schema

```json
{
  "$schema": "journal-entry",
  "phase": "VERIFY",
  "agent": "marie",
  "result": "success",           // "success" | "failed" | "skipped"
  "reason": null,                // Required if failed
  "timestamp": "2026-01-09T15:30:00Z",
  "duration_seconds": 342,
  "metrics": {
    // Phase-specific metrics
    "tests_run": 47,
    "tests_passed": 47,
    "coverage_percent": 87.3
  },
  "artifacts": [
    // Files created/modified by this phase
    "services/user-management/profile-service/tests/test_avatar.py",
    "apps/web/src/components/__tests__/Avatar.test.tsx"
  ],
  "escalations": [
    // Any human escalations during this phase
    {
      "question": "Should avatar upload have size limit?",
      "answer": "Yes, 5MB max",
      "responder": "@john",
      "wait_seconds": 1800
    }
  ]
}
```

### 4.3 Journal Examples by Phase

**SPECIFY:**
```json
{
  "phase": "SPECIFY",
  "agent": "baron",
  "result": "success",
  "metrics": {
    "requirements_count": 8,
    "acceptance_criteria_count": 12
  },
  "artifacts": ["specs/042-avatars/spec.md"]
}
```

**VERIFY:**
```json
{
  "phase": "VERIFY",
  "agent": "marie",
  "result": "success",
  "metrics": {
    "tests_run": 47,
    "tests_passed": 47,
    "tests_failed": 0,
    "coverage_percent": 87.3,
    "lint_errors": 0,
    "type_errors": 0
  },
  "artifacts": []
}
```

**VERIFY (failed):**
```json
{
  "phase": "VERIFY",
  "agent": "marie",
  "result": "failed",
  "reason": "3 tests failed in avatar upload suite",
  "metrics": {
    "tests_run": 47,
    "tests_passed": 44,
    "tests_failed": 3
  },
  "failed_tests": [
    "test_avatar_upload_large_file",
    "test_avatar_upload_invalid_format",
    "test_avatar_resize"
  ]
}
```

**RELEASE_DEV:**
```json
{
  "phase": "RELEASE_DEV",
  "agent": "gus",
  "result": "success",
  "metrics": {
    "services_deployed": 2,
    "deploy_pr_number": 156
  },
  "deployment": {
    "environment": "dev",
    "overlay_path": "infra/k8s/overlays/dev",
    "commit_sha": "abc123",
    "images": {
      "web": "sha-def456",
      "profile-service": "sha-ghi789"
    }
  }
}
```

**IMPLEMENT_BACKEND (skipped):**
```json
{
  "phase": "IMPLEMENT_BACKEND",
  "agent": "dede",
  "result": "skipped",
  "reason": "No backend tasks in tasks.md for this feature"
}
```

---

## 5. Agent Contract

Each agent must follow this contract for the orchestrator loop to work.

### 5.1 A2A Interface

Agents expose the standard A2A endpoint at `http://{agent}:8002/a2a`.

```python
@app.post("/a2a")
async def a2a_endpoint(request: JSONRPCRequest):
    if request.method == "tasks/send":
        return await handle_task(request.params)
    elif request.method == "tasks/get":
        return await get_task_status(request.params)
    # ... other A2A methods
```

### 5.2 Task Handling

When an agent receives a task:

```python
async def handle_task(params: dict) -> TaskResponse:
    task_data = json.loads(params["message"]["parts"][0]["text"])

    # 1. Check idempotency - am I already working on this phase?
    if self.is_already_working(task_data["issue_id"], task_data["phase"]):
        return TaskResponse(status="working", message="Already processing")

    # 2. Validate git state
    await self.git.fetch()
    # Agent works on the branch specified in task_data

    # 3. Execute phase work
    result = await self.execute_phase(task_data)

    # 4. Commit with journal
    journal = self.create_journal(task_data["phase"], result)
    await self.git.add_all()
    await self.git.commit(
        message=f"[{self.agent_name}] {task_data['phase'].lower()}: {result.summary}",
    )
    await self.git.push()

    return TaskResponse(status="completed", commit_sha=self.git.head())
```

### 5.3 Escalation Handling (Internal)

Escalations are handled **inside** the agent, transparent to the orchestrator.

```python
async def maybe_escalate(self, question: str, confidence: int) -> str:
    """Agent handles escalation internally."""
    if confidence >= 80:
        return None  # No escalation needed

    # Post to GitHub
    comment_id = await self.github.post_comment(
        issue=self.issue_number,
        body=f"/human: {question}\n\nConfidence: {confidence}%"
    )

    # Poll for response (agent waits, orchestrator doesn't know)
    response = await self.poll_for_human_response(
        comment_id=comment_id,
        timeout=timedelta(hours=4),  # Agent's internal timeout
    )

    # Record in journal
    self.escalations.append({
        "question": question,
        "answer": response.text,
        "responder": response.user,
        "wait_seconds": response.wait_time,
    })

    return response.text
```

From the orchestrator's perspective, the agent is just "working" for a longer time. If the agent times out (no human response), it commits a failed journal.

---

## 6. Operator Lifecycle Management

The Operator (Kopf) manages the full lifecycle: creation, monitoring, and cleanup.

```python
import kopf

@kopf.on.create('farmercode.io', 'v1', 'issueworkflows')
async def on_workflow_created(spec, name, namespace, **kwargs):
    """Create ephemeral namespace and deploy all pods."""
    workflow_ns = f"fc-{name}"

    # 1. Create namespace
    await k8s.create_namespace(workflow_ns)

    # 2. Create PVC for worktree
    await k8s.create_pvc(
        name="worktree",
        namespace=workflow_ns,
        size="10Gi",
    )

    # 3. Deploy orchestrator
    await k8s.deploy(
        name="orchestrator",
        namespace=workflow_ns,
        image="ghcr.io/farmer1st/orchestrator:latest",
        env={
            "ISSUE_ID": name,
            "CRD_NAME": name,
            "CRD_NAMESPACE": namespace,
        },
    )

    # 4. Deploy all agents
    for phase in spec["phases"]:
        agent = phase["agent"]
        if not await k8s.deployment_exists(agent, workflow_ns):
            await k8s.deploy(
                name=agent,
                namespace=workflow_ns,
                image=f"ghcr.io/farmer1st/{agent}:latest",
                env={
                    "ISSUE_ID": name,
                    "AGENT_NAME": agent,
                    "ESCALATION_ENABLED": "true",
                },
            )

    # 5. Update CRD status
    return {
        "status": {
            "state": "RUNNING",
            "workflowNamespace": workflow_ns,
            "startTime": datetime.utcnow().isoformat(),
            "currentPhaseIndex": 0,
        }
    }


@kopf.timer('farmercode.io', 'v1', 'issueworkflows', interval=300)  # Every 5 min
async def cleanup_finished_workflows(spec, status, name, **kwargs):
    """Delete namespace after TTL expires."""
    if status.get("state") not in ("COMPLETED", "FAILED"):
        return

    finish_time = datetime.fromisoformat(status["finishTime"])
    ttl = spec.get("ttlSecondsAfterFinished", 14400)

    if datetime.utcnow() > finish_time + timedelta(seconds=ttl):
        workflow_ns = status["workflowNamespace"]
        logger.info(f"TTL expired for {name}, deleting namespace {workflow_ns}")

        # Cascading delete - kills all pods, PVCs, etc.
        await k8s.delete_namespace(workflow_ns)

        # Optionally delete the CRD itself
        # await k8s.delete_crd(name)
```

---

## 7. Sequence Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              Simplified Workflow Sequence                                │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  GitHub          API Poller       Operator        K8s           Orchestrator    Agent   │
│    │                │                │             │                 │            │      │
│    │  Poll "READY"  │                │             │                 │            │      │
│    │<───────────────│                │             │                 │            │      │
│    │  Issue #42     │                │             │                 │            │      │
│    │───────────────>│                │             │                 │            │      │
│    │                │                │             │                 │            │      │
│    │                │  Create CRD    │             │                 │            │      │
│    │                │───────────────>│             │                 │            │      │
│    │                │                │  Watch      │                 │            │      │
│    │                │                │<────────────│                 │            │      │
│    │                │                │             │                 │            │      │
│    │                │                │  Create NS  │                 │            │      │
│    │                │                │────────────>│                 │            │      │
│    │                │                │  Deploy Pods│                 │            │      │
│    │                │                │────────────>│                 │            │      │
│    │                │                │             │                 │            │      │
│    │                │                │             │     ┌───────────────────────────┐  │
│    │                │                │             │     │ ORCHESTRATOR LOOP (5s)    │  │
│    │                │                │             │     ├───────────────────────────┤  │
│    │                │                │             │     │                           │  │
│    │                │                │             │  1. │ Read CRD Status           │  │
│    │                │                │             │<────│ (phaseIndex, lastCommit)  │  │
│    │                │                │             │     │                           │  │
│    │                │                │             │  2. │ Check Git for new commits │  │
│    │                │                │             │     │                           │  │
│    │                │                │             │     │ No commit found?          │  │
│    │                │                │             │  3. │──────────────────────────>│  │
│    │                │                │             │     │ A2A: tasks/send           │  │
│    │                │                │             │     │                           │  │
│    │                │                │             │     │         Agent works...    │  │
│    │                │                │             │     │         (may escalate     │  │
│    │                │                │             │     │          internally)      │  │
│    │                │                │             │     │                           │  │
│    │                │                │             │     │ Agent commits with journal│  │
│    │                │                │             │     │<──────────────────────────│  │
│    │                │                │             │     │                           │  │
│    │                │                │             │  4. │ Read journal/{phase}.json │  │
│    │                │                │             │     │                           │  │
│    │                │                │             │  5. │ Patch CRD: advance index  │  │
│    │                │                │             │────>│                           │  │
│    │                │                │             │     │                           │  │
│    │                │                │             │  6. │ Log to DynamoDB (async)   │  │
│    │                │                │             │     │                           │  │
│    │                │                │             │     │ Repeat for next phase...  │  │
│    │                │                │             │     └───────────────────────────┘  │
│    │                │                │             │                 │            │      │
│    │                │                │             │  Workflow COMPLETED           │      │
│    │                │                │             │                 │            │      │
│    │                │                │  TTL Timer  │                 │            │      │
│    │                │                │  (5 min)    │                 │            │      │
│    │                │                │<────────────│                 │            │      │
│    │                │                │             │                 │            │      │
│    │                │                │  Delete NS  │                 │            │      │
│    │                │                │────────────>│  (cascades)     │            │      │
│    │                │                │             │                 │            │      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Architecture Decision Records (ADRs)

### ADR-001: Git-Driven State Machine

**Decision:** Use Git commits as phase completion signals, CRD status as the pointer.

**Context:** Need to track workflow progress through multi-step SDLC phases.

**Rationale:**
- Git IS the source of truth for software development
- Commits are immutable, auditable, already versioned
- CRD status survives orchestrator crashes (Kubernetes guarantees)
- `kubectl edit` for manual intervention is intuitive for ops
- No external workflow engine to operate (Temporal requires complex cluster)

**Trade-offs:**
- Less flexible than Temporal for complex branching workflows
- Journal protocol adds convention that agents must follow

---

### ADR-002: Polling Over Webhooks

**Decision:** Use internal polling (GitHub API + Git) instead of webhooks.

**Context:** Need to trigger workflows and detect phase completion.

**Rationale:**
- **Zero ingress:** No public endpoints to secure
- **Simpler infrastructure:** No webhook receivers, tunnels, or runners
- **Acceptable latency:** 60s for issue detection, 5s for commit detection
- **Easier debugging:** Logs show poll results, no webhook delivery issues

**Trade-offs:**
- Higher API usage (mitigated by conditional requests / ETags)
- Slightly higher latency than webhooks

---

### ADR-003: CRD for Execution, DynamoDB for Analytics

**Decision:** Execution state in CRD, rich history in DynamoDB (fire-and-forget).

**Context:** Need to persist workflow state and collect data for learning.

**Rationale:**
- **Decoupled failure domains:** Workflow doesn't fail if DynamoDB is down
- **etcd is highly available:** CRD status is the "save game"
- **DynamoDB for queries:** Retro agent needs rich history, deployment records need querying for rollback

**Trade-offs:**
- DynamoDB data could be lost if fire-and-forget fails (acceptable for analytics)
- Deployment records in DynamoDB are critical for rollback (not fire-and-forget for those)

---

### ADR-004: One Commit Per Phase

**Decision:** Each phase produces exactly one atomic commit with a journal file.

**Context:** Orchestrator needs to know when a phase is complete and its result.

**Rationale:**
- **Clear completion signal:** Commit exists = phase attempted
- **Structured results:** Journal JSON tells success/fail/skip
- **Auditable:** Every phase result is in Git history
- **Simple orchestrator:** Just poll for commits, read journal

**Trade-offs:**
- Agents must follow the journal protocol strictly
- Large phases might naturally want multiple commits (mitigated by using git squash or single final commit)

---

### ADR-005: Namespace-per-Issue with TTL Cleanup

**Decision:** Ephemeral namespace `fc-{issue-id}` with automatic TTL deletion.

**Context:** Need isolation between concurrent features and cost control.

**Rationale:**
- **Simple DNS:** Agents call `http://baron:8002` (namespace-scoped)
- **Hard isolation:** No cross-feature interference
- **Guaranteed cleanup:** Namespace deletion cascades to all resources
- **Cost control:** TTL prevents zombie resources

**Trade-offs:**
- More namespaces to manage (mitigated by automation)
- Slight overhead per namespace (acceptable)

---

### ADR-006: Escalations Internal to Agents

**Decision:** Agents handle escalations internally (poll GitHub), orchestrator is unaware.

**Context:** Agents sometimes need human input during their work.

**Rationale:**
- **Simpler orchestrator:** Just waits for commit, doesn't track escalation state
- **Agent autonomy:** Agent decides when/how to escalate
- **Timeout handling:** Phase timeout covers escalation timeout
- **Journal records escalations:** Full audit trail in Git

**Trade-offs:**
- No central visibility into "waiting for human" state (mitigated by Slack notifications)
- Long-running phases might look "stuck" to observers

---

### ADR-007: No Feedback Loops in v1

**Decision:** Linear phase progression only. Failed phase = failed workflow.

**Context:** Original design had feedback triggers (e.g., review_changes → back to IMPLEMENT).

**Rationale:**
- **Simpler orchestrator:** Phase index only increments
- **Clearer failure mode:** Human intervenes to fix and restart
- **v2 option:** Add internal loops (REVIEW can A2A to IMPLEMENT before committing)

**Trade-offs:**
- More human intervention for recoverable failures
- Can be enhanced in v2 without architectural changes

---

## 9. What's NOT in This Model

These features are explicitly deferred or removed:

| Feature | Status | Rationale |
|---------|--------|-----------|
| Feedback loops (phase rewind) | Deferred to v2 | Keep orchestrator simple |
| Event sourcing in DynamoDB | Removed | CRD + Git is sufficient |
| Complex escalation tracking | Removed | Agent handles internally |
| Workflow-as-data (editable phases) | Removed | Static SOP is safer |
| Stop-and-go (pod termination on wait) | Deferred | Polling is simpler for v1 |

---

## 10. Migration Notes

To update `r-and-d-architecture.md`:

1. **Replace Section 3.8** (Orchestrator Implementation) with the simplified loop
2. **Add Section 3.x** for Journal Protocol
3. **Update Section 9** (Event Sourcing) - clarify DynamoDB is analytics-only
4. **Simplify Section 11** (Resilience) - remove event replay, add TTL cleanup
5. **Update ADRs** or create new ADR section
6. **Remove/simplify** feedback loop diagrams in Section 10
