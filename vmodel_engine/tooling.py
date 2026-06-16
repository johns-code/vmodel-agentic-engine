from __future__ import annotations

import shutil
import subprocess

from vmodel_engine.models import ToolStatus


TOOL_CANDIDATES = [
    ("git", "source control, branches, and pull request workflows", "git", ["git", "--version"]),
    ("pytest", "Python unit and integration test execution", "pytest", ["pytest", "--version"]),
    ("semgrep", "static application security testing", "semgrep", ["semgrep", "--version"]),
    ("trivy", "dependency, filesystem, and container vulnerability scanning", "trivy", ["trivy", "--version"]),
    ("node", "JavaScript project support for Jest, Playwright, and frontend templates", "node", ["node", "--version"]),
    ("npm", "JavaScript package and script execution", "npm", ["npm", "--version"]),
]


def inspect_tools() -> list[ToolStatus]:
    statuses: list[ToolStatus] = []
    for name, purpose, command, version_command in TOOL_CANDIDATES:
        executable = shutil.which(command)
        available = executable is not None
        version_output = ""
        if available:
            resolved_command = [executable, *version_command[1:]]
            try:
                completed = subprocess.run(resolved_command, capture_output=True, text=True, check=False)
                lines = (completed.stdout + completed.stderr).strip().splitlines()
                version_output = lines[0] if lines else ""
            except OSError as exc:
                available = False
                version_output = str(exc)
        statuses.append(
            ToolStatus(
                name=name,
                purpose=purpose,
                command=command,
                available=available,
                version_output=version_output,
            )
        )
    return statuses


def render_tool_statuses(statuses: list[ToolStatus]) -> str:
    lines = ["Tool inventory:"]
    for status in statuses:
        marker = "available" if status.available else "missing"
        suffix = f" ({status.version_output})" if status.version_output else ""
        lines.append(f"  {marker}: {status.name} - {status.purpose}{suffix}")
    return "\n".join(lines)
