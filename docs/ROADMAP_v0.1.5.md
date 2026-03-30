# Roadmap - v0.1.5

This roadmap captures the next product step after `v0.1.4`.

## Theme

Turn SA-NOM from a demo-ready private AI operations platform into a pilot-ready product with clearer use-case packs, repeatable guided scenarios, and stronger operator workflows for real organizational trials.

## Milestone Goal

By the end of `v0.1.5`, a serious evaluator should be able to pick a role-based scenario, run it on the private Ollama lane, review the governed outputs, and understand what a paid pilot would look like without needing to invent the operating pattern from scratch.

## Product Priorities

### 1. Pilot-Ready Role Packs

Build the first public-safe role packs that feel like real operational starting points instead of only generic role infrastructure.

Target candidates:
- Legal review and escalation pack
- HR policy and exception-handling pack
- Compliance monitoring and reporting pack
- Executive summary or CFO reporting pack

Expected outcomes:
- each pack has a documented purpose, scope, and safe default behavior
- each pack has public-safe sample inputs and expected outputs
- each pack can be used in a guided demo or pilot discussion

### 2. Guided Operational Scenarios

Move beyond setup checks into repeatable scenario flows.

Target scenario types:
- request intake to governed answer
- escalation when confidence is below threshold
- evidence generation after a governed decision
- operator review of a blocked or override-required path

Expected outcomes:
- scenario docs are easy to run in sequence
- the scenario output looks like a small real workflow, not only a technical health check
- the walkthrough can be reused in customer demos and pilot proposals

### 3. Operator And Admin UX Improvements

Reduce the gap between a passing smoke path and a usable operator experience.

Target areas:
- clearer operator dashboards or status surfaces
- easier explanation of provider state, trusted-registry state, and readiness state
- better runtime summaries for humans reviewing AI activity
- cleaner admin guidance for startup, recovery, and go-live checks

Expected outcomes:
- operators can tell what the system is doing without reading multiple reports
- support and onboarding friction goes down
- customer demo quality improves because the runtime state is easier to explain

## Technical Priorities

- Strengthen scenario-level tests for role packs, governed responses, and evidence outputs.
- Add reusable fixtures for pilot-style flows so new use-case packs do not become brittle.
- Review whether the runtime should emit more operator-facing summaries or structured scenario artifacts.
- Continue hardening the Ollama-first private lane for repeatable pilot usage.

## Documentation And Demo Priorities

- Add scenario-specific runbooks for the first pilot-ready use cases.
- Add a one-page Thai demo checklist for faster live calls.
- Add a pilot proposal or pilot-outline template that maps directly to the commercial discovery path.
- Improve the bridge from README -> guided evaluation -> live scenario -> commercial next step.

## Commercial Priorities

- Define the first paid-pilot shape more explicitly.
- Clarify what the customer receives during a guided pilot versus a broader rollout engagement.
- Add example pilot success criteria and pilot closeout outputs.
- Make role-pack-based demo stories easier to price, scope, and repeat.

## Candidate Deliverables

- at least 2 public-safe pilot-ready role packs
- at least 2 guided operational scenarios
- improved operator-facing runtime summaries or dashboards for scenario review
- Thai demo checklist
- pilot proposal template
- scenario-aligned example artifacts and expected outputs

## Exit Criteria For v0.1.5

- a new evaluator can run at least one meaningful role-based scenario on the private Ollama lane
- at least one scenario produces governed output plus evidence that can be shown during a live demo or pilot conversation
- the commercial path includes a clear paid-pilot story, not only general discovery and pricing material
- product docs connect setup, scenario execution, and pilot next steps without major gaps
