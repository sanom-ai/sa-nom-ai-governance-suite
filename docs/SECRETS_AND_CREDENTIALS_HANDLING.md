# Secrets And Credentials Handling

This guide defines the first public baseline for how SA-NOM should handle secrets and credentials in self-managed, private, and air-gapped environments.

## Why This Guide Exists

SA-NOM is designed for organizations that often deploy AI systems in private infrastructure where operational ownership stays with the operator.

That makes secrets handling part of the trust story. The goal is not to pretend that the public repository already delivers a fully automated enterprise secrets platform. The goal is to make the expected handling model explicit so operators, contributors, and evaluators can see where secrets belong, where they do not belong, and when human approval is still required.

## Core Principles

- keep secrets out of the repository
- keep secrets out of public examples and test fixtures
- separate configuration values from sensitive credential material
- keep runtime-generated credentials and artifacts out of source control
- make secret ownership, rotation posture, and override paths explicit
- assume that self-managed operators are responsible for their deployment boundary

## Secret Classes

SA-NOM deployments commonly need to distinguish between several classes of sensitive material.

### 1. Runtime Credentials

Examples:
- API keys
- service tokens
- bootstrap access profiles
- webhook signing secrets
- database or storage credentials

Handling expectation:
- inject at runtime or through deployment-specific secret stores
- never hard-code in public files
- never commit into `_runtime/`, examples, or markdown docs

### 2. Operator Configuration With Sensitive Fields

Examples:
- deployment manifests that reference secret names
- environment files that contain real credentials
- node or provider configuration with embedded tokens

Handling expectation:
- the public repo may document the shape of configuration
- real secret values must remain outside the repo
- sample files should use placeholders only

### 3. High-Sensitivity Recovery Material

Examples:
- emergency access tokens
- restore credentials
- signing keys
- encrypted backup unlock material

Handling expectation:
- keep under stricter human control
- require explicit documented custody
- do not treat as ordinary developer convenience data

## Where Secrets Must Not Live

Secrets must not be committed to:
- markdown docs
- example JSON files
- test fixtures meant for public review
- committed `.env` files
- `_runtime/` artifacts that are tracked by git
- screenshots, walkthroughs, or demo outputs intended for sharing

If a guide or example needs to show a credential location, use placeholders such as:
- `YOUR_API_KEY_HERE`
- `REPLACE_WITH_SECRET_NAME`
- `example-not-a-real-secret`

## Local Development Hygiene

Local development should make secret boundaries easier to respect, not easier to blur.

Recommended baseline:
- install dependencies locally, but keep real credentials outside committed files
- prefer local environment variables or local-only secret files excluded by `.gitignore`
- use public-safe placeholder values in sample commands and screenshots
- clear temporary runtime artifacts after local testing when they contain sensitive data

Contributor expectation:
- before opening a PR, check that no secret material, machine-local runtime state, or deployment credential files were staged accidentally

## Deployment And Self-Managed Operations

SA-NOM is often evaluated for private deployment, self-managed environments, and air-gapped operations.

That means deployment teams should treat secrets as operator-owned infrastructure inputs.

Expected posture:
- secret values are injected by the deployment environment, not published by the application repo
- secret storage, rotation, escrow, and recovery responsibility remain with the operator
- the public repo may document what categories of secrets are needed, but not the real values themselves
- emergency credentials, restore credentials, and signing material should remain under stricter custody than routine application settings

## Rotation And Review Posture

The public baseline should assume that secrets have lifecycle requirements even when automation is still environment-specific.

Minimum expectations:
- define who owns each credential class
- define when routine rotation is expected
- document which credentials require urgent rotation after suspected exposure
- keep revocation and replacement steps understandable to operators

## Incident And Exposure Response

If a secret is suspected to be exposed:
- revoke or rotate the affected credential as soon as practical
- determine whether the exposure touched only local development or a real deployment boundary
- replace affected artifacts or profiles rather than trusting the old material
- document the incident path according to the operator's governance process

The public repo should not imply that secret recovery is fully automated unless that automation actually exists.

## Human And AI Boundaries

SA-NOM is designed so AI can do routine governed work inside approved boundaries.

Secrets handling is different. AI may help with:
- documenting expected secret categories
- checking whether placeholders are still placeholders
- surfacing missing configuration references
- summarizing credential ownership and rotation posture

AI should not be treated as the autonomous owner of real secrets, emergency credentials, or high-risk rotation decisions unless an organization has explicitly built and approved that control path.

## Public Baseline And Commercial Boundary

This guide defines the public baseline only.

It does not claim that the AGPL repository already provides:
- a complete secrets manager
- automated escrow and recovery
- enterprise key management integration
- end-to-end production credential rotation tooling

Commercial or private deployment work may go further through tailored integrations, deployment controls, and operator-specific operating models.

## Practical Summary

The right public message is simple:

SA-NOM can be deployed in private and self-managed environments, but real secrets must stay outside the public repo, outside public examples, and inside operator-controlled handling paths.
