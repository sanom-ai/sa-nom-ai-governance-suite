# Public Upload Runbook

Use this runbook right before pushing the repository to a public Git host.

## 1. Run Preflight

PowerShell:

```powershell
C:\Python314\python.exe public_release_preflight.py
```

Interpretation:
- `READY`: safe to continue
- `READY WITH WARNINGS`: continue only after you understand each warning
- `BLOCKED`: fix the reported error before upload

If preflight reports that `git` is missing, install Git for Windows first or use a one-time web upload for the initial repository publish.

## 2. Review Local Runtime State

This workspace currently keeps local runtime files under `_runtime/`. They are ignored by git and Docker, but they still exist on disk.

Before upload, manually confirm that `_runtime/` contains no files you intend to publish.
Typical local-only files include:
- `generated_access_tokens.json`
- `owner_registration.json`
- `runtime_audit_log.jsonl`
- `runtime_session_store.json`
- `runtime_override_store.json`
- `trusted_registry_cache.json`

## 3. Create Or Attach A Git Repository

Recommended path: install Git for Windows so you can keep normal version history, tags, and future updates.

If this folder is not yet a git repository:

```powershell
git init
git branch -M main
```

If you already have a remote repository:

```powershell
git remote add origin <YOUR_GIT_REMOTE_URL>
```

If you need a one-time fallback before Git is installed, create an empty GitHub repository in the browser and upload the public-safe files manually, but only after reviewing the `_runtime/` warning from preflight.

## 4. Review What Will Be Uploaded

```powershell
git status --short
git add .
git status --short
```

Pause here and confirm that `_runtime/`, secrets, and review-only artifacts are not staged.

## 5. Create The First Public Commit

```powershell
git commit -m "Prepare public AGPL community baseline"
```

## 6. Tag The First Release

```powershell
git tag v0.1.0
```

## 7. Push

```powershell
git push -u origin main
git push origin v0.1.0
```

## 8. Publish Release Metadata

After push:
- use `RELEASE_NOTES_v0.1.0.md` as the first release description
- verify README rendering on the hosted repository
- verify issue templates and PR template appear correctly
- verify contact email and commercial links are visible

## Final Manual Gate

Do not upload until all of the following are true:
- `LICENSE`, `NOTICE`, `COMMERCIAL_LICENSE.md`, and `FEATURE_MATRIX.md` are final
- `_runtime/` contains no intended public artifacts beyond placeholders
- `python -m pytest _support/tests` has been run in an environment with pytest installed
- you are comfortable with the public commercial positioning and contact path

