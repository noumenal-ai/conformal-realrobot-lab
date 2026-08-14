from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SEALED_SHA256SUMS.json"
ALLOWED_LEAN = {
    line.strip()
    for line in (ROOT / "lean" / "ALLOW_EDIT.txt").read_text(encoding="utf-8").splitlines()
    if line.strip()
}


def ignored(relative: Path) -> bool:
    parts = relative.parts
    text = relative.as_posix()
    if not parts:
        return True
    if parts[0] in {"outputs", "work", ".venv"}:
        return True
    if "__pycache__" in parts or ".pytest_cache" in parts or any(p.endswith(".egg-info") for p in parts):
        return True
    if ".lake" in parts or relative.name == "lake-manifest.json":
        return True
    if text.startswith("lean/statistical/ZPM/") or text == "lean/statistical/ZPM.lean":
        return True
    if text.startswith("lean/causal/Causality/") or text == "lean/causal/Causality.lean":
        return True
    if text in ALLOWED_LEAN:
        return True
    if relative.name == MANIFEST.name:
        return True
    return False


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = []
    for relative, sha in expected.items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"Missing sealed file: {relative}")
        elif digest(path) != sha:
            failures.append(f"Modified sealed file: {relative}")
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and not ignored(path.relative_to(ROOT))
    }
    extras = sorted(actual.difference(expected))
    if extras:
        failures.append("Unapproved extra files: " + ", ".join(extras))
    if failures:
        raise SystemExit("\n".join(failures))
    print("Sealed scientific/experiment files verified")


if __name__ == "__main__":
    main()
