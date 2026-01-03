# FarmCode Feature Breakdown

**Vision**: AI agent orchestration system for automated software development following the Farmer1st SDLC workflow.

**Bootstrap Strategy**: Build the minimum viable orchestrator (MVO) first, then use it to build the rest of itself!

---

## Phase 1: Minimum Viable Orchestrator (MVO)
**Goal**: Can orchestrate a single workflow phase end-to-end (Phase 1-2 of SDLC)

### Feature 1.1: GitHub Integration Core
**Priority**: P1 (Critical - Foundation)
**Description**: Backend service for GitHub operations using REST API polling (local-first design)

**Capabilities**:
- Create/read/update GitHub issues
- Post/read issue comments with polling (5-10 second intervals)
- Add/remove labels
- Basic PR operations (create, read)
- Incremental comment polling (since last check)

**Why first**: Everything depends on GitHub as source of truth. Without this, nothing else works. Uses polling to work locally without public endpoint.

**Acceptance**: Can create issue, post comment, poll for new comments, update labels via API

---

### Feature 1.2: Git Worktree Manager
**Priority**: P1 (Critical - Foundation)
**Description**: Service for managing git branches and worktrees

**Capabilities**:
- Create branches from main
- Create worktrees in sibling directories
- Create .plans folder structure
- Commit and push changes
- Remove worktrees
- Delete branches

**Why second**: Phase 1 requires worktree creation. This is the second foundation piece.

**Acceptance**: Can create branch "123-test-feature", create worktree, initialize .plans/123/, clean up

---

### Feature 1.3: Orchestrator State Machine (Phases 1-2 Only)
**Priority**: P1 (Critical - Core Logic)
**Description**: State machine that orchestrates SDLC Phase 1 (Issue Setup) and Phase 2 (Specs)

**Capabilities**:
- State: IDLE → PHASE_1 → PHASE_2 → GATE_1 → DONE
- Execute Phase 1: Create issue, branch, worktree, .plans structure
- Execute Phase 2: Dispatch @duc agent
- Poll for completion signal (✅ comment from agent)
- Wait for human approval ("approved" comment)
- Update GitHub labels for each state transition

**Why third**: This is the brain - ties GitHub + Git operations together into a workflow.

**Acceptance**: Given feature description, creates issue #X, worktree, dispatches agent, waits for completion, requests human approval, completes workflow

---

### Feature 1.4: Claude CLI Agent Spawner
**Priority**: P1 (Critical - Agent Execution)
**Description**: Service that spawns and manages Claude CLI agents

**Capabilities**:
- Spawn Claude CLI with custom prompt
- Pass context (issue number, worktree path, phase, role)
- Monitor agent process
- Capture agent output/logs
- Handle agent errors/timeouts

**Why fourth**: Without agents, we have no automation. This brings the AI to life.

**Acceptance**: Can spawn Claude CLI as @duc, pass issue context, agent reads issue and creates spec files

---

### Feature 1.5: Comment Monitor & Parser
**Priority**: P1 (Critical - Agent Communication)
**Description**: Service that monitors GitHub comments and parses agent signals

**Capabilities**:
- Poll GitHub issue comments (every 5-10 seconds)
- Parse completion signals (✅ @baron)
- Parse questions (❓ @agent or @human)
- Parse blocks (🚫)
- Detect human approval ("approved", "merge")
- Notify orchestrator of state changes

**Why fifth**: Agents communicate via comments. This closes the feedback loop.

**Acceptance**: Detects "✅ Specs complete. @baron" and notifies orchestrator that Phase 2 is complete

---

### Feature 1.6: CLI Interface (Temporary)
**Priority**: P1 (MVP - User Interface)
**Description**: Simple command-line interface to start workflows

**Capabilities**:
- `farmcode start "feature description"` - starts workflow
- `farmcode status <issue-number>` - shows current state
- `farmcode approve <issue-number>` - approves current gate
- `farmcode logs <issue-number>` - shows agent logs

**Why sixth**: Need some way to interact with the system. CLI is fastest to build.

**Acceptance**: Can start workflow, monitor progress, approve gates from terminal

---

## Phase 2: Visual Interface
**Goal**: Replace CLI with Electron app + Kanban board

### Feature 2.1: Electron App Shell
**Priority**: P2
**Description**: Desktop application wrapper with project selection

**Capabilities**:
- Startup: select project folder (local repo)
- Configure GitHub repo connection
- Store project preferences
- Launch orchestrator as background service

**Acceptance**: Opens app, selects project, connects to GitHub repo

---

### Feature 2.2: Kanban Board UI
**Priority**: P2
**Description**: Real-time visual board showing workflow progress

**Capabilities**:
- Columns: New → Specs → Plans → Tests → Implementation → Review → Done
- Cards: Issues with current phase, assigned agents, progress
- Real-time updates (via websocket or polling)
- Click card to see details (comments, files, agent logs)
- Approve gates from UI

**Acceptance**: Shows issues moving through workflow in real-time, can approve gates by clicking

---

### Feature 2.3: Agent Configuration UI
**Priority**: P2
**Description**: Interface to select and configure agents per task

**Capabilities**:
- Select which agent to assign (different @duc versions, etc.)
- Configure agent parameters (model, temperature, etc.)
- Save agent profiles per project

**Acceptance**: Can choose "Claude Opus for @duc" vs "Claude Sonnet for @duc"

---

## Phase 3: Complete Workflow
**Goal**: Support all 8 SDLC phases

### Feature 3.1: Orchestrator Phases 3-8
**Priority**: P3
**Description**: Complete state machine with all workflow phases

**Capabilities**:
- Phase 3: Parallel agent dispatch (@dede, @dali, @gus)
- Phase 4: Test plan (@marie)
- Phase 5: TDD implementation (parallel agents)
- Phase 6: PR creation
- Phase 7: Reviews (parallel reviewers)
- Phase 8: Merge & cleanup
- All 4 gates
- Handle review feedback loops

**Acceptance**: Can orchestrate full workflow from feature description to merged PR

---

### Feature 3.2: Agent Question Routing
**Priority**: P3
**Description**: Handle agent-to-agent and agent-to-human questions

**Capabilities**:
- Detect ❓ @agent in comments
- Dispatch target agent to answer
- Pause workflow on ❓ @human
- Resume after human response

**Acceptance**: @dede asks "❓ @duc Should we use GraphQL?", orchestrator dispatches @duc to answer

---

### Feature 3.3: Real-time Sync Engine (Webhooks)
**Priority**: P3
**Description**: Replace polling with webhooks for real-time updates (requires public endpoint or ngrok)

**Capabilities**:
- GitHub webhook receiver endpoint (HTTPS)
- Webhook signature validation
- Parse webhook events (issue_comment, issues, pull_request)
- WebSocket to UI clients for instant updates
- Push updates to Kanban board in real-time
- Tunneling support (ngrok/cloudflare) for local development

**Why deferred**: Polling works fine for MVP. Webhooks require publicly accessible endpoint, which doesn't work for local-first design without tunneling. This is an optimization for better UX.

**Acceptance**: Comment posted on GitHub appears in UI within 1 second via webhook instead of 10-second polling delay

---

## Phase 4: Bootstrap Ready
**Goal**: Use FarmCode to build FarmCode features!

### Feature 4.1: Plans Folder Templates
**Priority**: P4
**Description**: Templating system for .plans structure

**Capabilities**:
- Template for README.md
- Template for specs (backend/frontend/infra)
- Template for plans
- Template for reviews
- Customizable per project

**Acceptance**: Creates .plans/123/ with all templates populated

---

### Feature 4.2: Multi-Project Management
**Priority**: P4
**Description**: Manage multiple projects simultaneously

**Capabilities**:
- Switch between projects
- See all active workflows across projects
- Project-specific agent configurations

**Acceptance**: Can work on FarmCode AND another project simultaneously

---

## Phase 5: Production Ready
**Goal**: Deploy and scale

### Feature 5.1: Deployment Orchestration
**Priority**: P5
**Description**: Automated deployment to dev/staging/production

**Capabilities**:
- Deploy to dev on merge
- Promote to staging (with approval)
- Promote to production (with approval)
- Rollback capabilities
- Environment health checks

**Acceptance**: Merged PR auto-deploys to dev, can promote to staging/prod

---

### Feature 5.2: Analytics & Metrics
**Priority**: P5
**Description**: Track workflow performance

**Capabilities**:
- Cycle time per phase
- Agent success rate
- Approval gate wait times
- Code quality metrics
- Cost tracking (API usage)

**Acceptance**: Dashboard shows "Average cycle time: 2 hours", "Phase 5 bottleneck: 45min avg"

---

## Bootstrap Sequence

**Week 1-2: MVO (Features 1.1-1.6)**
- Can orchestrate Phase 1-2 via CLI
- Creates issue, worktree, spawns @duc, waits for specs, gets approval

**Week 3-4: Visual UI (Features 2.1-2.3)**
- Electron app with Kanban board
- Can see workflow in real-time
- Approve gates from UI

**Week 5: Complete Workflow (Feature 3.1)**
- All 8 phases working
- Can orchestrate full feature from description to merged PR

**Week 6+: Bootstrap!**
- Use FarmCode to build Features 3.2, 3.3, 4.1, 4.2, 5.1, 5.2
- FarmCode builds FarmCode!

---

## Recommended First Feature

**Start with: Feature 1.1 - GitHub Integration Core**

This is the foundation. Once we have solid GitHub operations, everything else builds on top.

Run: `/speckit.specify` with Feature 1.1 description to create the first spec!
