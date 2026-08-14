from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = re.compile(r"(?m)^\s*-- BEGIN AUTOFORMALIZE_ONLY ([A-Za-z0-9_]+)\s*$")
END_TEMPLATE = r"(?m)^\s*-- END AUTOFORMALIZE_ONLY {name}\s*$"


def normalized_contract(text: str) -> str:
    output = []
    cursor = 0
    for match in BEGIN.finditer(text):
        name = match.group(1)
        end_re = re.compile(END_TEMPLATE.format(name=re.escape(name)))
        end_match = end_re.search(text, match.end())
        if end_match is None:
            raise ValueError(f"Missing END marker for {name}")
        output.append(text[cursor : match.end()])
        output.append("\n  __AUTOFORMALIZE_BODY__\n")
        output.append(text[end_match.start() : end_match.end()])
        cursor = end_match.end()
    output.append(text[cursor:])
    return "".join(output)


def contract_hash(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(normalized_contract(text).encode("utf-8")).hexdigest()


def marker_bodies(text: str) -> list[tuple[str, str]]:
    bodies = []
    for match in BEGIN.finditer(text):
        name = match.group(1)
        end_re = re.compile(END_TEMPLATE.format(name=re.escape(name)))
        end_match = end_re.search(text, match.end())
        if end_match is None:
            raise ValueError(f"Missing END marker for {name}")
        bodies.append((name, text[match.end() : end_match.start()]))
    return bodies


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "lean" / "contract_hashes.json").read_text(encoding="utf-8"))
    failures = []
    forbidden = re.compile(r"\b(sorry|admit|axiom|unsafe|native_decide)\b")
    for relative, expected in manifest.items():
        path = ROOT / relative
        actual = contract_hash(path)
        if actual != expected:
            failures.append(f"Locked Lean statement/import region changed: {relative}")
        if args.final:
            text = path.read_text(encoding="utf-8")
            if forbidden.search(text):
                failures.append(f"Forbidden Lean token in {relative}")
            for name, body in marker_bodies(text):
                if re.search(r"(?m)^\s*exact\s+_\s*$", body):
                    failures.append(f"Unfilled proof body {name} in {relative}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("Lean contract verified" + ("; proof bodies filled" if args.final else ""))


if __name__ == "__main__":
    main()
