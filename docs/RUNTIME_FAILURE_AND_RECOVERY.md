# Runtime Failure And Recovery

This guide defines the first public baseline for how SA-NOM should be understood under failure conditions and during operational recovery.

## Why This Guide Exists

SA-NOM is designed for governed AI operations in private, self-managed, and air-gapped deployment scenarios.

That means technical evaluators will eventually ask a practical question: what happens when the runtime is unhealthy, a dependency is missing, generated state is stale, or critical startup gates fail?

This guide explains the intended recovery posture without pretending that every recovery path is already fully automated.

## Core Position

SA-NOM should be read as:
- explicit about startup and readiness gates
- recoverable through operator-led workflows
- honest about the boundary between documented posture and full runtime automation
- designed so recovery stays governed rather than improvised

The goal is not zero failure. The goal is understandable failure handling.

## Failure Modes That Matter Most

At the public baseline, the most important failure categories are:
- startup-readiness failures
- missing or stale `_runtime/` artifacts
- invalid owner registration or access profile state
- trusted-registry signing misconfiguration
- provider configuration and provider-probe failures
- environment or secret misconfiguration
- inconsistent local evaluation state after failed runs

These are the failures the repo should help operators reason about first.

## Readiness Before Service Start

SA-NOM already exposes a useful recovery concept: validate before serving traffic.

Primary readiness command:
- `python scripts/dashboard_server.py --check-only`

This matters because recovery should start with posture inspection, not guesswork.

The operator should be able to answer:
- what failed?
- is this a local setup problem or a deployment problem?
- is the state missing, stale, or inconsistent?
- should this be fixed by regeneration, configuration correction, or human approval?

## Operator-Led Recovery Order

The preferred recovery order is:
1. inspect readiness with `--check-only`
2. identify the failing component or missing artifact
3. regenerate or refresh only the affected state
4. re-run readiness validation
5. run targeted smoke checks where appropriate
6. start the runtime only after the gate is green again

This keeps recovery deliberate and auditable.

## Runtime State And Regeneration Boundaries

A key recovery concept in SA-NOM is that `_runtime/` is generated operational state, not source code.

That means:
- some failures should be resolved by regenerating affected runtime artifacts
- generated state should not be treated as manually curated business logic
- operators should distinguish between safe regeneration and sensitive recovery actions
- regenerated artifacts that include credential material must still follow the secrets-handling baseline

Examples of regeneration-led recovery:
- owner registration refresh for missing local evaluation state
- access-profile regeneration when the profile artifact is invalid or stale
- trusted-registry refresh when the signed manifest is out of date or misaligned

## Sensitive Recovery Areas

Not every recovery step should be treated as a routine restart.

Higher-scrutiny areas include:
- emergency access or recovery credentials
- bootstrap access profile regeneration tied to real deployment trust boundaries
- trusted-registry signing posture
- restore operations involving retained operational evidence
- situations where runtime recovery could overwrite or discard evidence that matters to audit or incident review

In these cases, human confirmation and documented custody matter more than speed alone.

## What AI Can And Cannot Do In Recovery

SA-NOM is designed so AI can do governed work inside approved boundaries.

For runtime recovery, AI may help with:
- summarizing readiness failures
- listing likely recovery steps from known runbooks
- identifying missing configuration references
- surfacing which artifacts look stale or absent
- preparing meeting-ready recovery status summaries through Human Ask

AI should not be treated as the autonomous owner of:
- emergency recovery decisions
- destructive reset choices in live environments
- evidence-discard or hold-release decisions
- trust-boundary changes around credentials, signing, or production access

## Local Evaluation Versus Live Deployment Recovery

The public repository should distinguish clearly between local evaluation cleanup and live deployment recovery.

Local evaluation may allow:
- safe regeneration of demo runtime state
- removal of failed local artifacts that do not need preservation
- quick repetition of readiness and smoke checks

Live or controlled deployments require more care:
- preserve evidence that matters to the operator's governance process
- confirm whether a recovery step changes trust posture or retained records
- avoid using local reset habits as if they were production-safe runbooks

## Recovery Documentation Expectations

A recovery-capable system should make at least these things clear:
- what artifacts are generated versus curated
- what can be safely regenerated
- what commands operators should run first
- what conditions require higher scrutiny or human approval
- where the public repo stops and deployment-specific operator responsibility begins

## Relationship To Existing Docs

This guide should be read with:
- [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [docs/SECRETS_AND_CREDENTIALS_HANDLING.md](SECRETS_AND_CREDENTIALS_HANDLING.md)
- [docs/SECURITY_AND_DEPENDENCY_HYGIENE.md](SECURITY_AND_DEPENDENCY_HYGIENE.md)

Deployment explains how to start well.
Troubleshooting explains common startup failures.
This guide explains the broader runtime recovery posture behind those steps.

## Public Baseline And Future Work

This guide defines a public baseline only.

It does not claim that the public repo already provides:
- full high-availability orchestration
- automatic failover and stateful recovery automation
- environment-wide backup and restore automation
- production incident management tooling by default

Future work may add deeper backup, restore, and operational validation guidance.

## Practical Summary

The right public message is:

SA-NOM should fail in understandable ways, guide operators toward readiness-first recovery, and keep higher-risk recovery actions under explicit human control.
