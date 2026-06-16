from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from vmodel_engine.models import GateResult


def run_python_project_gates(project_dir: Path) -> list[GateResult]:
    return [
        _run("unit-tests", [sys.executable, "-m", "pytest"], project_dir),
        _run("security-smoke-scan", [sys.executable, "-m", "vmodel_engine.security_scan", str(project_dir)], Path.cwd()),
    ]


def _run(name: str, command: list[str], cwd: Path) -> GateResult:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    output = (completed.stdout + completed.stderr).strip()
    return GateResult(
        name=name,
        command=command,
        passed=completed.returncode == 0,
        exit_code=completed.returncode,
        output=output,
    )
