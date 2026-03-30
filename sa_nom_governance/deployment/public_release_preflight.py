from __future__ import annotations

from pathlib import Path
import importlib.util
import shutil

ROOT = Path(__file__).resolve().parents[2]
KNOWN_GIT_PATHS = (
    Path(r"C:\Program Files\Git\cmd\git.exe"),
    Path(r"C:\Program Files\Git\bin\git.exe"),
    Path(r"C:\Program Files (x86)\Git\cmd\git.exe"),
)
RUNTIME_DIR = ROOT / "_runtime"
ALLOWED_RUNTIME_PUBLIC = {".gitkeep", "README.md"}


def _check(label: str, status: str, detail: str) -> tuple[str, str, str]:
    return label, status, detail


def main() -> int:
    checks: list[tuple[str, str, str]] = []

    git_available = shutil.which("git") is not None or any(path.exists() for path in KNOWN_GIT_PATHS)
    checks.append(
        _check(
            "git_installed",
            "ok" if git_available else "warning",
            "git is available on PATH." if git_available else "git is not installed or not available on PATH.",
        )
    )
    checks.append(
        _check(
            "git_repository",
            "ok" if (ROOT / ".git").exists() else "warning",
            "Git metadata exists." if (ROOT / ".git").exists() else "No .git directory found in this workspace.",
        )
    )

    gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    dockerignore_text = (ROOT / ".dockerignore").read_text(encoding="utf-8") if (ROOT / ".dockerignore").exists() else ""

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

    runtime_entries = sorted(path for path in RUNTIME_DIR.iterdir()) if RUNTIME_DIR.exists() else []
    risky_runtime = [path for path in runtime_entries if path.name not in ALLOWED_RUNTIME_PUBLIC]
    if risky_runtime:
        checks.append(
            _check(
                "runtime_state_present",
                "warning",
                "Runtime state exists locally and should not be uploaded: " + ", ".join(path.name for path in risky_runtime),
            )
        )
    else:
        checks.append(_check("runtime_state_present", "ok", "_runtime contains only public-safe placeholder files."))

    env_candidates = sorted(path.name for path in ROOT.glob('.env*') if path.name != '.env.production.example')
    checks.append(
        _check(
            "private_env_files",
            "ok" if not env_candidates else "warning",
            "No extra private .env files detected." if not env_candidates else "Private env-like files found: " + ", ".join(env_candidates),
        )
    )

    pytest_installed = importlib.util.find_spec("pytest") is not None
    checks.append(
        _check(
            "pytest_installed",
            "ok" if pytest_installed else "warning",
            "pytest is installed." if pytest_installed else "pytest is not installed in the current interpreter.",
        )
    )

    release_notes = ROOT / "../../docs/releases/RELEASE_NOTES_v0.1.0.md"
    checks.append(
        _check(
            "release_notes_present",
            "ok" if release_notes.exists() else "warning",
            "Release notes file exists." if release_notes.exists() else "Release notes file is missing.",
        )
    )

    has_error = False
    has_warning = False
    for label, status, detail in checks:
        if status == "error":
            has_error = True
        if status == "warning":
            has_warning = True
        print(f"[{status.upper()}] {label}: {detail}")

    print()
    if has_error:
        print("Preflight result: BLOCKED")
        return 1
    if has_warning:
        print("Preflight result: READY WITH WARNINGS")
        return 0
    print("Preflight result: READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
