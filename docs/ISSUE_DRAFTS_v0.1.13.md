# Issue Drafts - v0.1.13

Use these draft issues to turn the `v0.1.13` roadmap into implementation work.

## 1. Add Security Exception Workflow Guide

**Goal**
Document how maintainers should handle dependency or lightweight security findings that are not fixed immediately.

**Scope ideas**
- define what qualifies as a temporary exception
- define what still blocks merge
- require justification, owner, and review language for accepted exceptions

**Success signal**
Accepted-risk handling becomes more explicit and easier to audit in review conversations.

## 2. Add Follow-Up Visibility Workflow

**Goal**
Make deferred security work easier to track after merge.

**Scope ideas**
- issue-driven follow-up expectations
- linking accepted exceptions to follow-up work items
- documenting revisit timing or milestone ownership

**Success signal**
Security gaps that are tolerated temporarily remain visible and attributable.

## 3. Add Escalation Rules For Sensitive Findings

**Goal**
Clarify which findings deserve higher scrutiny or stronger maintainer response.

**Scope ideas**
- distinguish runtime-trust findings from lower-impact dev-tool findings
- point to auth, token, session, audit, deployment, and backup paths as escalation triggers
- document reviewer language for elevated findings

**Success signal**
Maintainers can explain why some findings require stronger action than others.

## 4. Align Docs Around Exception Handling

**Goal**
Keep security, contributor, and automation docs consistent once the exception workflow is introduced.

**Scope ideas**
- update `SECURITY.md`
- update `CONTRIBUTING.md`
- update `docs/SECURITY_AUTOMATION_BASELINE.md`
- add links from the docs index

**Success signal**
The repo's security workflow reads as a coherent system instead of scattered guidance.
