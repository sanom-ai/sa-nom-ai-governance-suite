# Open-Source Release Checklist

Use this checklist before making the repository public or cutting a public release tag.

## Code and Artifact Hygiene

- Confirm `_runtime/` contains no real organization state, generated secrets, or live evidence packs.
- Confirm examples in `examples/` are sanitized and safe for screenshots, demos, and onboarding.
- Rebuild `trusted_registry_manifest.json` if policy packs changed.
- Verify `.gitignore` and `.dockerignore` still block `_runtime/`, `.env`, generated tokens, and review artifacts.

## License and Public Metadata

- Confirm `LICENSE` contains the canonical AGPL-3.0 text.
- Review `NOTICE`, `TRADEMARKS.md`, `SECURITY.md`, and `COMMERCIAL_LICENSE.md` together before release.
- Confirm contact email and pricing links are current.
- Confirm any repo description or public website copy matches the open-core boundary in `FEATURE_MATRIX.md`.

## Technical Verification

- Run `python -m py_compile` on the touched Python files.
- Run `python -m pytest _support/tests`.
- Run `python dashboard_server.py --check-only`.
- Re-test the quick-start path from `README.md` and `DEPLOYMENT.md`.

## Commercial Readiness

- Confirm pricing tiers and engagement language are current.
- Prepare a short sales intake template covering organization size, environment type, and timeline.
- Prepare a current demo environment or screen recording for first commercial calls.
- Confirm which features remain community, which are quote-only, and which are service-led.

## Public Launch Readiness

- Prepare release notes for the first public tag.
- Enable issue tracking and define how community support will be handled.
- Confirm the public source location that AGPL users should be directed to.
- Review the repository once from a new-user perspective: install, run, understand the model, and find contact details in under ten minutes.

## Final Gate

- Cut the release only after legal, technical, and commercial checks all pass.
- If any item above is uncertain, pause the public launch and resolve it first.

