from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
KNOWN_GIT_PATHS = (
    Path(r"C:\Program Files\Git\cmd\git.exe"),
    Path(r"C:\Program Files\Git\bin\git.exe"),
    Path(r"C:\Program Files (x86)\Git\cmd\git.exe"),
)
RUNTIME_DIRNAME = "_runtime"
REVIEW_DIRNAME = "_review"
ALLOWED_RUNTIME_PUBLIC = {".gitkeep", "README.md"}
STATUS_RANK = {"ok": 0, "warning": 1, "error": 2}


def _check(label: str, status: str, detail: str) -> dict[str, str]:
    return {"label": label, "status": status, "detail": detail}


def _project_version(root: Path) -> str | None:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return None
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def _release_notes_path(root: Path, release_version: str) -> Path:
    return root / "docs" / "releases" / f"RELEASE_NOTES_v{release_version}.md"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _load_quick_start_doctor(root: Path) -> dict[str, Any]:
    path = root / REVIEW_DIRNAME / "quick_start_doctor.json"
    payload = _load_json(path)
    if payload is None:
        if path.exists():
            return {"status": "invalid", "path": str(path), "summary": {}}
        return {"status": "missing", "path": str(path), "summary": {}}
    return {
        "status": str(payload.get("status", "invalid")),
        "path": str(path),
        "summary": payload.get("summary", {}) if isinstance(payload.get("summary", {}), dict) else {},
    }


def _load_runtime_performance_baseline(root: Path) -> dict[str, Any]:
    path = root / REVIEW_DIRNAME / "runtime_performance_baseline.json"
    payload = _load_json(path)
    if payload is None:
        if path.exists():
            return {"status": "invalid", "path": str(path), "summary": {}}
        return {"status": "missing", "path": str(path), "summary": {}}
    return {
        "status": str(payload.get("status", "invalid")),
        "path": str(path),
        "summary": payload.get("summary", {}) if isinstance(payload.get("summary", {}), dict) else {},
    }


def _evaluate_checks(checks: list[dict[str, str]]) -> str:
    highest = max((STATUS_RANK.get(check["status"], 0) for check in checks), default=0)
    if highest >= STATUS_RANK["error"]:
        return "BLOCKED"
    if highest >= STATUS_RANK["warning"]:
        return "READY WITH WARNINGS"
    return "READY"


def run_preflight(
    root: Path = ROOT,
    *,
    release_version: str | None = None,
    git_available: bool | None = None,
    pytest_installed: bool | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    resolved_release_version = release_version or _project_version(root)
    runtime_dir = root / RUNTIME_DIRNAME

    effective_git_available = (
        git_available
        if git_available is not None
        else (shutil.which("git") is not None or any(path.exists() for path in KNOWN_GIT_PATHS))
    )
    checks.append(
        _check(
            "git_installed",
            "ok" if effective_git_available else "warning",
            "git is available on PATH." if effective_git_available else "git is not installed or not available on PATH.",
        )
    )
    checks.append(
        _check(
            "git_repository",
            "ok" if (root / ".git").exists() else "warning",
            "Git metadata exists." if (root / ".git").exists() else "No .git directory found in this workspace.",
        )
    )

    gitignore_text = (root / ".gitignore").read_text(encoding="utf-8") if (root / ".gitignore").exists() else ""
    dockerignore_text = (root / ".dockerignore").read_text(encoding="utf-8") if (root / ".dockerignore").exists() else ""
    checks.append(
        _check(
            "gitignore_runtime_block",
            "ok" if "_runtime/*" in gitignore_text else "error",
            "_runtime is ignored in .gitignore." if "_runtime/*" in gitignore_text else ".gitignore does not ignore _runtime/*.",
        )
    )
    checks.append(
        _check(
            "dockerignore_runtime_block",
            "ok" if "_runtime/" in dockerignore_text else "error",
            "_runtime is ignored in .dockerignore." if "_runtime/" in dockerignore_text else ".dockerignore does not ignore _runtime/.",
        )
    )

    runtime_entries = sorted(path for path in runtime_dir.iterdir()) if runtime_dir.exists() else []
    risky_runtime = [path for path in runtime_entries if path.name not in ALLOWED_RUNTIME_PUBLIC]
    checks.append(
        _check(
            "runtime_state_present",
            "warning" if risky_runtime else "ok",
            (
                "Runtime state exists locally and should not be uploaded: " + ", ".join(path.name for path in risky_runtime)
            )
            if risky_runtime
            else "_runtime contains only public-safe placeholder files.",
        )
    )

    env_candidates = sorted(path.name for path in root.glob(".env*") if path.name != ".env.production.example")
    checks.append(
        _check(
            "private_env_files",
            "warning" if env_candidates else "ok",
            "Private env-like files found: " + ", ".join(env_candidates) if env_candidates else "No extra private .env files detected.",
        )
    )

    effective_pytest_installed = pytest_installed if pytest_installed is not None else (importlib.util.find_spec("pytest") is not None)
    checks.append(
        _check(
            "pytest_installed",
            "ok" if effective_pytest_installed else "warning",
            "pytest is installed." if effective_pytest_installed else "pytest is not installed in the current interpreter.",
        )
    )

    if resolved_release_version:
        release_notes_path = _release_notes_path(root, resolved_release_version)
        checks.append(
            _check(
                "release_notes_target",
                "ok" if release_notes_path.exists() else "error",
                (
                    f"Release notes exist for v{resolved_release_version}."
                    if release_notes_path.exists()
                    else f"Release notes are missing for v{resolved_release_version}: {release_notes_path}"
                ),
            )
        )
    else:
        release_notes_catalog = sorted((root / "docs" / "releases").glob("RELEASE_NOTES_v*.md")) if (root / "docs" / "releases").exists() else []
        checks.append(
            _check(
                "release_notes_catalog",
                "ok" if release_notes_catalog else "warning",
                "Release notes catalog is present." if release_notes_catalog else "No release notes files were found under docs/releases/.",
            )
        )

    quick_start_doctor = _load_quick_start_doctor(root)
    doctor_status = str(quick_start_doctor.get("status", "missing"))
    doctor_summary = quick_start_doctor.get("summary", {}) if isinstance(quick_start_doctor.get("summary", {}), dict) else {}
    if doctor_status == "pass":
        checks.append(_check("quick_start_doctor_posture", "ok", f"Quick-start doctor passed ({doctor_summary.get('checks_total', 0)} checks)."))
    elif doctor_status == "warn":
        checks.append(_check("quick_start_doctor_posture", "warning", f"Quick-start doctor has advisories ({doctor_summary.get('advisory_failed_total', 0)} advisory failures)."))
    elif doctor_status == "fail":
        checks.append(_check("quick_start_doctor_posture", "error", f"Quick-start doctor failed ({doctor_summary.get('required_failed_total', 0)} required failures)."))
    elif doctor_status == "invalid":
        checks.append(_check("quick_start_doctor_posture", "warning", f"Quick-start doctor artifact is invalid: {quick_start_doctor.get('path')}."))
    else:
        checks.append(_check("quick_start_doctor_posture", "warning", f"Quick-start doctor artifact is missing: {quick_start_doctor.get('path')}."))

    performance_baseline = _load_runtime_performance_baseline(root)
    performance_status = str(performance_baseline.get("status", "missing"))
    performance_summary = performance_baseline.get("summary", {}) if isinstance(performance_baseline.get("summary", {}), dict) else {}
    detail = (
        f"slowest={performance_summary.get('slowest_metric', 'unknown')} "
        f"({float(performance_summary.get('slowest_elapsed_ms', 0.0) or 0.0):.3f} ms); "
        f"dashboard={float(performance_summary.get('dashboard_snapshot_elapsed_ms', 0.0) or 0.0):.3f} ms"
    )
    if performance_status == "ready":
        checks.append(_check("runtime_performance_guardrail", "ok", f"Runtime performance baseline is within budget: {detail}."))
    elif performance_status == "monitoring":
        checks.append(_check("runtime_performance_guardrail", "warning", f"Runtime performance baseline is above warning budget: {detail}."))
    elif performance_status in {"critical", "failed"}:
        checks.append(_check("runtime_performance_guardrail", "error", f"Runtime performance baseline is blocking: {detail}."))
    elif performance_status == "invalid":
        checks.append(_check("runtime_performance_guardrail", "warning", f"Runtime performance baseline artifact is invalid: {performance_baseline.get('path')}."))
    else:
        checks.append(_check("runtime_performance_guardrail", "warning", f"Runtime performance baseline artifact is missing: {performance_baseline.get('path')}."))

    result = {
        "status": _evaluate_checks(checks),
        "checks": checks,
        "root": str(root),
        "release_version": resolved_release_version,
        "quick_start_doctor": quick_start_doctor,
        "runtime_performance_baseline": performance_baseline,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run public release preflight checks for runtime hygiene, artifacts, and performance posture.")
    parser.add_argument("--release-version", default=None, help="Optional release version to require release notes for, for example 0.7.0.")
    parser.add_argument("--json", action="store_true", help="Print the full preflight result as JSON.")
    args = parser.parse_args()

    result = run_preflight(release_version=args.release_version)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("release_version"):
            print(f"Target release version: v{result['release_version']}")
        for check in result["checks"]:
            print(f"[{str(check['status']).upper()}] {check['label']}: {check['detail']}")
        print()
        print(f"Preflight result: {result['status']}")

    return 1 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
