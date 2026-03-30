# Issue Drafts - v0.1.1

Use these drafts to seed the first public issue batch.

## 1. Add packaging metadata for cleaner local setup

- Title: `Add packaging metadata for cleaner local setup`
- Labels: `enhancement`, `community`, `v0.1.1`
- Milestone: `v0.1.1`

```md
## Summary
Add lightweight packaging metadata so first-time evaluators have a cleaner local setup path.

## Problem
The repository is currently script-first and works, but the local setup path is less polished than it could be.

## Proposed Direction
Evaluate whether a minimal `pyproject.toml` or equivalent packaging metadata should be added without disrupting the current runtime model.

## Acceptance Criteria
- setup path is documented clearly
- packaging choice is minimal and justified
- existing runtime workflow still works
```

## 2. Document troubleshooting for startup validation failures

- Title: `Document troubleshooting for startup validation failures`
- Labels: `documentation`, `community`, `v0.1.1`
- Milestone: `v0.1.1`

```md
## Summary
Add troubleshooting guidance for common startup validation failures.

## Problem
New evaluators may hit startup validation errors without enough context to recover quickly.

## Proposed Direction
Document likely failure modes such as missing owner registration, invalid access profiles, and trusted-registry issues.

## Acceptance Criteria
- troubleshooting section added to docs
- at least the most common startup failures are covered
- recovery steps are short and concrete
```

## 3. Expand public-safe examples for onboarding

- Title: `Expand public-safe examples for onboarding`
- Labels: `documentation`, `enhancement`, `community`, `v0.1.1`
- Milestone: `v0.1.1`

```md
## Summary
Add more public-safe examples for evaluators and documentation.

## Problem
The current examples cover the baseline, but more examples would make evaluation and demos easier.

## Proposed Direction
Add example flows for owner registration, delegated access, and trusted registry refresh.

## Acceptance Criteria
- examples remain public-safe
- docs link to the new examples
- examples help evaluators complete a quick-start path faster
```

## 4. Run the full pytest suite in a clean environment

- Title: `Run the full pytest suite in a clean environment`
- Labels: `bug`, `community`, `v0.1.1`
- Milestone: `v0.1.1`

```md
## Summary
Run the full pytest suite in a clean environment with dev dependencies installed.

## Problem
The public release was validated with direct regression execution and compile checks, but full pytest still needs to be confirmed in a clean environment.

## Proposed Direction
Install `requirements-dev.txt`, run `python -m pytest _support/tests`, and capture any failures as follow-up issues.

## Acceptance Criteria
- pytest command is executed in a clean environment
- failures are documented if present
- docs reflect the tested path accurately
```

## 5. Add FAQ for AGPL, self-hosting, and commercial boundaries

- Title: `Add FAQ for AGPL, self-hosting, and commercial boundaries`
- Labels: `documentation`, `commercial`, `community`, `v0.1.1`
- Milestone: `v0.1.1`

```md
## Summary
Add an FAQ covering common licensing and adoption questions.

## Problem
Potential users and buyers may not immediately understand the AGPL obligations, the self-hosted model, or where the commercial layer begins.

## Proposed Direction
Add a concise FAQ to the public docs and link it from the README.

## Acceptance Criteria
- AGPL obligations explained simply
- self-hosting and commercial boundary explained clearly
- contact path remains easy to find
```

## 6. Review line-ending normalization and add .gitattributes if needed

- Title: `Review line-ending normalization and add .gitattributes if needed`
- Labels: `enhancement`, `community`, `v0.1.1`
- Milestone: `v0.1.1`

```md
## Summary
Review line-ending normalization and decide whether to add a `.gitattributes` policy.

## Problem
Git currently warns about LF/CRLF normalization for multiple files in the repository.

## Proposed Direction
Decide on a repository-wide line-ending policy and encode it explicitly if that improves contributor consistency.

## Acceptance Criteria
- line-ending policy documented or codified
- warning noise reduced for contributors
- no unintended content changes
```

## 7. Improve README with visuals or product flow snapshots

- Title: `Improve README with visuals or product flow snapshots`
- Labels: `documentation`, `enhancement`, `good first issue`, `v0.1.1`
- Milestone: `v0.1.1`

```md
## Summary
Add one or more visuals that help new visitors understand the product faster.

## Problem
The README is clearer now, but visuals could reduce evaluation friction further.

## Proposed Direction
Add screenshots, diagrams, or a short architecture overview for first-time visitors.

## Acceptance Criteria
- visuals are public-safe
- README remains fast to scan
- visuals improve first-time comprehension
```

## 8. Prepare a guided smoke-test path for first-time evaluators

- Title: `Prepare a guided smoke-test path for first-time evaluators`
- Labels: `enhancement`, `community`, `commercial`, `v0.1.1`
- Milestone: `v0.1.1`

```md
## Summary
Create a guided smoke-test path that helps evaluators confirm the core runtime quickly.

## Problem
A smoother evaluation path increases trust and helps both community adoption and commercial discovery.

## Proposed Direction
Document or script a short path that covers owner registration, delegated access setup, readiness checks, and a first successful runtime action.

## Acceptance Criteria
- evaluation flow is clear and short
- path stays aligned with the public-safe examples
- flow is reusable in commercial discovery calls
```

