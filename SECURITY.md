# Security Policy

## Supported Scope

The public repository includes runtime orchestration, dashboard surfaces, audit handling, and deployment helpers.
Treat any authentication, authorization, token, session, audit-integrity, or data-exposure issue as security-sensitive.

## Reporting a Vulnerability

Do not open public issues for suspected vulnerabilities.

Report security issues privately to:
- sanomaiarch@gmail.com

Include:
- affected file or endpoint
- reproduction steps
- expected vs actual behavior
- impact assessment
- any suggested mitigation

## Handling Expectations

The maintainers should:
- acknowledge a report quickly
- triage severity and impact
- coordinate a fix and release plan
- credit reporters when appropriate and approved

## Repository Hygiene Posture

The public repository follows a dependency-light security posture.

That means maintainers should prefer small, reviewable dependency changes, keep secrets out of tracked files, and treat authentication, authorization, token, session, audit-integrity, and data-exposure paths as security-sensitive even when the deployment model is self-managed.

See [docs/SECURITY_AND_DEPENDENCY_HYGIENE.md](docs/SECURITY_AND_DEPENDENCY_HYGIENE.md) for the broader hygiene baseline.


## Security Automation Baseline

The repository now includes a lightweight pull-request dependency review check as an early security automation layer. See [docs/SECURITY_AUTOMATION_BASELINE.md](docs/SECURITY_AUTOMATION_BASELINE.md) for the current scope and limits.

