from __future__ import annotations

import argparse
import re
from pathlib import Path


SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]{8,}['\"]"),
]


def scan_path(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".toml", ".json", ".md", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path))
                break
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Minimal deterministic security smoke scan.")
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    findings = scan_path(args.root)
    if findings:
        print("Potential secrets found:")
        for finding in findings:
            print(finding)
        return 1
    print("No security smoke-scan findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
