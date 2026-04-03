# ISSUE DRAFTS v0.7.9

## Slice 1 - Runtime Entrypoint Hardening
- Add testable `argv` entrypoints to the smallest operational CLIs without changing normal runtime usage.
- Cover API bootstrap, private-server launch, runtime backup, audit reseal, trusted-registry refresh, provider probe, access-profile hash/rotation, and owner registration.
- Lock these paths with focused tests so pilot-critical operations stop relying on untested script glue.

## Slice 2 - Deployment And Recovery Validation
- Expand confidence around smoke, backup, restore, and recovery utilities used during private-first setup and runtime recovery.
- Make pilot recovery flows measurable instead of documentation-only.

## Slice 3 - Dashboard And API Confidence Expansion
- Push more coverage into dashboard server and API boundary paths that still lag behind the rest of the runtime.
- Keep Control Room, protected routes, and diagnostics trustworthy under guarded access patterns.

## Slice 4 - Pilot Confidence Scenarios
- Add realistic end-to-end confidence scenarios that exercise product behavior instead of only isolated units.
- Reduce the number of pilot stories that still depend on repo knowledge or manual operator stitching.
