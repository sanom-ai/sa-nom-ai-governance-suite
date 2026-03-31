# Backup And Restore Validation

This guide defines the first public baseline for how SA-NOM should think about backup scope, restore expectations, and validation after a restore event.

## Why This Guide Exists

A governed system should not only explain how it starts. It should also explain how operators preserve critical state and how they validate that a restored environment is trustworthy again.

For SA-NOM, backup and restore posture matters because the platform deals with:
- generated runtime state
- access-profile artifacts
- trusted-registry material
- audit and evidence-related outputs
- retained operational records

This guide explains the public baseline without pretending that the repository already includes a full enterprise backup platform.

## Core Position

SA-NOM should be read as:
- explicit about which operational artifacts matter enough to back up
- careful about the difference between restorable state and reproducible state
- validation-oriented after restore, not satisfied by file presence alone
- governed in higher-risk recovery actions that may affect trust, retention, or audit posture

The goal is not backup theater. The goal is credible restore readiness.

## What Typically Needs Protection

At the public baseline, operators should think about at least these categories.

### 1. Runtime State

Examples:
- `_runtime/owner_registration.json`
- `_runtime/access_profiles.json`
- trusted registry manifests and related generated state
- runtime data that is not trivially reproducible from source alone

### 2. Credential-Adjacent Artifacts

Examples:
- generated access token outputs used during secure handoff
- environment-specific secret references
- restore credentials and emergency recovery material

These require stricter custody and should not be treated like ordinary application files.

### 3. Evidence And Audit Outputs

Examples:
- exported evidence bundles
- audit-related records needed for operator review
- release-readiness or probe reports archived with go-live records

### 4. Retained Operational Records

Examples:
- records subject to retention expectations
- artifacts under hold or needed for incident review
- records that should not be discarded just because the runtime is being restored

## Backup Scope Versus Reproducible State

Not everything needs to be backed up the same way.

Operators should distinguish between:
- source-controlled assets that can be restored from git
- generated runtime state that may need regeneration or preservation
- sensitive or retained artifacts that need controlled backup and restore handling

A useful rule of thumb is:
- if it is reproducible safely from source and approved configuration, backup urgency may be lower
- if it represents trust, registration, retention, or evidence posture, backup discipline should be higher

## Minimum Backup Posture

The public baseline should assume at least the following:
- identify which runtime artifacts are needed to resume trusted operation
- identify which evidence or retained records must survive restore events
- keep backup storage under operator control
- keep restore credentials and backup access material under stricter custody
- document what is included, how often it is captured, and who owns validation

## Restore Validation Matters More Than File Copy Alone

A restore is not complete just because files are back on disk.

Operators should validate that the restored environment is operationally and governably sound.

Minimum restore-validation questions:
- does `python scripts/dashboard_server.py --check-only` return a ready deployment profile?
- is owner registration present and consistent with expected identity?
- are access profiles structurally valid and still within acceptable trust posture?
- do trusted-registry artifacts still align with expected signing posture?
- do retained evidence and records still exist where expected?
- do smoke checks pass after restore?

## Recommended Restore Validation Order

1. restore the environment using operator-controlled backup material
2. confirm secret and credential references are reconnected correctly
3. run `python scripts/dashboard_server.py --check-only`
4. inspect owner registration, access profiles, and trusted-registry state
5. run the relevant smoke tests
6. verify evidence, retained records, and archived reports expected by the operator
7. only return the environment to service when readiness and trust posture are acceptable again

## High-Scrutiny Restore Areas

Some restore actions require more than a routine operator check.

Examples:
- restore operations that touch emergency access or recovery credentials
- restore paths that may overwrite newer evidence with older state
- restore decisions that affect legal hold, audit hold, or retained records
- trust-boundary changes around registry signing or production access profiles

These cases should remain under explicit human control and documented custody.

## AI And Human Boundaries In Restore Work

AI may help with:
- listing expected backup scope categories
- comparing restored artifact presence against expected state
- summarizing failed validation steps
- preparing Human Ask summaries for recovery meetings

AI should not autonomously decide to:
- discard retained records
- release holds
- replace trust-critical signing or access material without approved human control
- declare a restored environment trustworthy when validation evidence is incomplete

## Relationship To Existing Docs

This guide should be read with:
- [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [docs/RUNTIME_FAILURE_AND_RECOVERY.md](RUNTIME_FAILURE_AND_RECOVERY.md)
- [docs/SECRETS_AND_CREDENTIALS_HANDLING.md](SECRETS_AND_CREDENTIALS_HANDLING.md)
- [docs/SECURITY_AUDIT_CHECKLIST.md](SECURITY_AUDIT_CHECKLIST.md)

Deployment covers baseline setup.
Runtime failure and recovery explains broader operator-led recovery posture.
This guide focuses specifically on backup scope, restore discipline, and validation after restore.

## Public Baseline And Future Work

This guide defines a public baseline only.

It does not claim that the repository already provides:
- built-in scheduled backup orchestration
- automatic cross-site recovery
- point-in-time recovery tooling for every deployment mode
- enterprise restore attestation or backup compliance automation by default

Future work may add deeper restore exercises, operational evidence expectations, or deployment-specific backup guidance.

## Practical Summary

The right public message is:

SA-NOM should not only be backed up. It should be restored and then validated in a way that preserves trust, evidence posture, and operator control.
