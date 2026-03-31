# Issue Drafts - v0.1.14

Use these draft issues to turn the `v0.1.14` roadmap into implementation work.

## 1. Add Structured Security Exception Issue Template

**Goal**
Create a GitHub issue template for accepted or deferred security findings.

**Scope ideas**
- capture finding summary
- capture affected package or workflow area
- capture why the issue is deferred
- capture owner and revisit point

**Success signal**
Accepted security exceptions are easier to record consistently and review later.

## 2. Add Deferred Security Follow-Up Issue Template

**Goal**
Create a lightweight template for follow-up work that should remain visible after merge.

**Scope ideas**
- capture linked PR or accepted exception
- capture mitigation status
- capture milestone or review checkpoint
- capture closure criteria

**Success signal**
Deferred security work becomes easier to track and revisit without heavy process.

## 3. Add Security Escalation Rules Guide

**Goal**
Document which findings require stronger human scrutiny and when merge should be blocked or escalated.

**Scope ideas**
- auth, token, session, audit, backup, recovery, and deployment trust-boundary triggers
- difference between low-impact tooling issues and trust-critical findings
- plain-language escalation guidance

**Success signal**
Reviewers can distinguish routine follow-up from findings that require stronger human decision-making.

## 4. Align Security Docs With AI-Assist And Human-Decision Boundary

**Goal**
Make security workflow docs more explicit that AI can assist with surfacing and summarizing findings, but humans decide exceptions and escalation.

**Scope ideas**
- update security workflow docs
- tighten contributor wording
- keep the repo's AI operating philosophy consistent across modules

**Success signal**
The AI-first but human-gated model reads clearly in the security workflow narrative.
