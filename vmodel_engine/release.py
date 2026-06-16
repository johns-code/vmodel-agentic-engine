from __future__ import annotations

import json
from pathlib import Path

from vmodel_engine.models import GateResult, WorkflowRun


def write_gate_report(gate_results: list[GateResult], output_dir: Path) -> Path:
    path = output_dir / "gate-results.json"
    path.write_text(json.dumps([result.__dict__ for result in gate_results], indent=2) + "\n", encoding="utf-8")
    return path


def write_release_evidence(run: WorkflowRun, output_dir: Path) -> list[Path]:
    release_dir = output_dir / "release-evidence"
    release_dir.mkdir(parents=True, exist_ok=True)
    manifest = release_dir / "manifest.json"
    summary = release_dir / "README.md"
    manifest.write_text(json.dumps(run.to_dict(), indent=2) + "\n", encoding="utf-8")
    summary.write_text(_summary(run), encoding="utf-8")
    tools = release_dir / "tool-inventory.md"
    tools.write_text(_tool_inventory(run), encoding="utf-8")
    return [manifest, summary, tools]


def _summary(run: WorkflowRun) -> str:
    gates = "\n".join(f"- {gate.name}: {'PASS' if gate.passed else 'FAIL'}" for gate in run.gate_results)
    policies = "\n".join(
        f"- {policy.name}: {'PASS' if policy.passed else 'FAIL'}" for policy in run.quality_policy_results
    )
    return f"""# Release Evidence

Project: {run.project_name}

Status: {run.status}

Generated project: `{run.generated_project_dir}`

Artifact directory: `{run.artifact_dir}`

## Gates

{gates}

## Agent Quality Policy

{policies}

## Reviews

- Artifact reviews: {len(run.artifact_reviews)}
- Arbitration records: {len(run.arbitration_records)}

## Approval

Human approval is required before final acceptance and release.
"""


def _tool_inventory(run: WorkflowRun) -> str:
    rows = "\n".join(
        f"| {tool.name} | {tool.purpose} | {'Yes' if tool.available else 'No'} | {tool.version_output} |"
        for tool in run.tool_statuses
    )
    return "# Tool Inventory\n\n| Tool | Purpose | Available | Version |\n| --- | --- | --- | --- |\n" + rows + "\n"
