# ROADMAP v0.7.9 - Confidence Hardening

Status: In progress  
Line: v0.7.9-confidence-hardening

## Goal
Raise trust in SA-NOM as a serious private-first pilot product by hardening low-coverage runtime entrypoints, operational CLIs, deployment recovery paths, and release confidence checks.

## Slices

### 1. Runtime Entrypoint Hardening
- cover the smallest but riskiest runtime entry modules first
- make operational CLIs easier to test without changing their external behavior
- remove blind spots around API bootstrap, private-server launch, runtime backup, audit reseal, owner registration, and trusted-registry refresh

### 2. Deployment And Recovery Validation
- tighten smoke, backup, restore, and registration flows used during private setup and operational recovery
- make pilot-critical operational commands verifiable through repeatable tests

### 3. Dashboard And API Confidence Expansion
- add targeted coverage to dashboard server and API boundary flows that still sit below the rest of the codebase
- keep the command surface trustworthy under reload, guarded access, and diagnostics pressure

### 4. Pilot Confidence Scenarios
- lock more realistic end-to-end operator scenarios into tests and release gates
- reduce the number of pilot stories that still depend on repo knowledge instead of product behavior

## Slice 1 Definition of Done
- the main runtime and governance CLIs accept explicit argv-style invocation for testing without changing normal CLI usage
- low-coverage operational entrypoints are covered by focused tests
- runtime bootstrap, owner registration, trust refresh, audit reseal, backup, and provider probe paths are no longer effectively untested
- the first confidence-hardening slice improves coverage while also improving structure and maintainability
