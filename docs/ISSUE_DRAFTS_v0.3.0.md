# Issue Drafts - v0.3.0

Use these issue drafts to deliver the `v0.3.0` usability milestone.

## 1. Add Quick Start Path For Local/Private Runtime

**Goal**
Create a startup path that gets a user to a successful governed runtime run in 5-10 minutes.

**Scope ideas**
- reduce manual setup steps for local/private startup
- define a single recommended startup command path
- add a first-run validation flow that proves the runtime is alive
- clarify required environment prerequisites without forcing deep repo reading

**Success signal**
A new user can bring up SA-NOM quickly and verify a first successful run.

## 2. Add Baseline Operator Dashboard

**Goal**
Expose the runtime through a simple dashboard that surfaces workflow state, readiness, inbox, recovery, and proof information.

**Scope ideas**
- dashboard views for workflow backlog and current state
- readiness summary and operator action pressure
- human decision inbox visibility
- workflow proof bundle visibility and export actions

**Success signal**
An operator can understand the runtime posture without digging through implementation files.

## 3. Add Guided Demo And First-Run Flow

**Goal**
Make the local/private demo path easier to run and easier to trust.

**Scope ideas**
- step-by-step demo flow tied to real governed runtime surfaces
- first-run success criteria and visible confirmation points
- simple troubleshooting cues for common setup failures
- local/private validation path that can be repeated on a real machine

**Success signal**
A demo can be run consistently with less setup friction and less operator guesswork.

## 4. Tighten Operator UX Around Human-Required States

**Goal**
Improve the usability of human-required, blocked, and recovery states without weakening runtime governance.

**Scope ideas**
- clearer labels and summaries for human checkpoints
- safer default actions in the dashboard/operator layer
- visible mapping between UI actions and governed runtime outcomes
- simpler proof and handoff navigation for trust-sensitive steps

**Success signal**
Operators can understand what they must decide and what the AI can continue autonomously.

## 5. Close v0.3.0 With Usability Proof

**Goal**
Finish the milestone with proof that SA-NOM became easier to start, easier to observe, and easier to operate.

**Scope ideas**
- quick-start validation run on a local/private environment
- dashboard walkthrough proof for non-technical operator tasks
- first-run and demo closeout summary
- release notes that show the shift from execution-core maturity to usability maturity

**Success signal**
`v0.3.0` closes with visible usability gains, not only implementation claims.
