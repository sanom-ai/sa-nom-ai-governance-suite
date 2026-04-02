# Release Notes - v0.6.2

## Release Focus

`v0.6.2` is the trigger-runtime follow-up release after the initial Global Harmony baseline in `v0.6.1`.

This release does not open a new product direction. It strengthens the execution layer behind PTAG so SA-NOM can move from trigger syntax toward governed runtime effects that are easier to audit, route, and extend.

The scope stays intentionally tight:

- canonical `WHEN ... THEN ...` trigger grammar for PTAG policy blocks
- runtime execution of trigger effects rather than trigger parsing alone
- stronger approval, policy-pack, tone-guidance, and evidence pathways tied to trigger actions

## Completed Scope

### Canonical PTAG Trigger Grammar

- established `WHEN ... THEN ...` as the canonical trigger form inside PTAG policy blocks
- kept the grammar case-insensitive and flexible enough for inline and multi-line conditions
- added validator signals for malformed trigger structure so policy authors get clearer feedback

### Runtime Effect Execution

- operationalized trigger evaluation so runtime decisions can materialize action plans from PTAG policies
- added first-class handling for `require_approval(...)`, `apply_policy_pack(...)`, `rewrite_tone(...)`, and `log_evidence(...)`
- attached trigger outcomes to machine-readable runtime metadata instead of leaving them as parser-only artifacts

### Auditability And Operator Visibility

- surfaced trigger branch, approval requirements, policy-pack effects, tone guidance, and evidence tags through runtime outputs
- improved audit evidence so trigger-driven behavior can be inspected later by operators and reviewers
- kept the human-gate boundary intact for actions that should pause rather than continue automatically

### Documentation And Test Contract

- updated PTAG framework and full-spec documentation to match the canonical trigger grammar
- added parser, validator, and runtime regression coverage around trigger behavior
- kept the release positioned as execution-depth improvement, not as a broad syntax migration release

## Why This Release Matters

`v0.6.2` matters because it turns PTAG triggers into something the governed runtime can actually act on.

That makes SA-NOM look less like a repository with promising governance syntax and more like a runtime that can evaluate context, decide what should happen next, and surface that decision in a controlled, auditable form.

The release is especially important for later enterprise work because it gives the repo one coherent trigger foundation that can support:

- human approval gates
- policy-pack activation
- tone or alignment guidance
- evidence and trace enrichment

## Verification

- `python -m compileall -q .`
- `python -m ruff check sa_nom_governance/core --select E,F,I --ignore E501`
- `python -m pytest _support/tests`

## Next Phase

After `v0.6.2`, the next step should continue through disciplined runtime strengthening rather than another syntax expansion.

That means the strongest follow-up is the `v0.7.0` platform-foundation line: cleaner runtime structure, stronger portability, deeper governed autonomy, better degraded-state visibility, and tighter operational discipline.

## Notes

- `v0.6.2` should be read as the runtime-effect executor release for the PTAG trigger line
- this release strengthens the policy-to-runtime bridge without over-claiming full orchestration maturity
- the goal of the release is depth and coherence, not a large feature spread
