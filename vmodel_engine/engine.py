from __future__ import annotations

import json
from pathlib import Path

from vmodel_engine.agents import (
    AGENT_ROLES,
    arbitrate_agent_disputes,
    evaluate_quality_policy,
    perform_artifact_reviews,
    write_agent_governance_artifacts,
)
from vmodel_engine.artifacts import write_artifact_package
from vmodel_engine.gates import run_python_project_gates
from vmodel_engine.models import ArtifactPackage, WorkflowRun, utc_now_iso
from vmodel_engine.planning import create_implementation_tasks, create_traceability_matrix
from vmodel_engine.project_templates import generate_python_cli_project
from vmodel_engine.release import write_gate_report, write_release_evidence
from vmodel_engine.requirements import build_requirements
from vmodel_engine.tooling import inspect_tools
from vmodel_engine.work_items import LocalIssueTracker


SUPPORTED_PROJECT_TYPES = {"python-cli"}


def build_project(
    requirements_path: Path,
    output_dir: Path,
    project_name: str | None = None,
    project_type: str = "python-cli",
) -> WorkflowRun:
    if project_type not in SUPPORTED_PROJECT_TYPES:
        supported = ", ".join(sorted(SUPPORTED_PROJECT_TYPES))
        raise ValueError(f"unsupported project type '{project_type}'. Supported types: {supported}")

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = output_dir / "artifacts"
    generated_project_dir = output_dir / "generated-project"

    package = create_artifact_package(requirements_path, project_name)
    write_artifact_package(package, artifact_dir)
    artifact_reviews = perform_artifact_reviews(package)
    arbitration_records = arbitrate_agent_disputes(artifact_reviews)
    quality_policy_results = evaluate_quality_policy(package, artifact_reviews, arbitration_records)
    write_agent_governance_artifacts(
        AGENT_ROLES,
        artifact_reviews,
        arbitration_records,
        quality_policy_results,
        output_dir,
    )
    work_items = LocalIssueTracker(output_dir).create_items(package.implementation_tasks)
    generate_python_cli_project(package, generated_project_dir)
    gate_results = run_python_project_gates(generated_project_dir)
    tool_statuses = inspect_tools()
    status = (
        "ready_for_human_acceptance"
        if all(result.passed for result in gate_results) and all(result.passed for result in quality_policy_results)
        else "blocked_by_gates"
    )

    run = WorkflowRun(
        project_name=package.project_name,
        project_type=project_type,
        status=status,
        artifact_dir=str(artifact_dir),
        generated_project_dir=str(generated_project_dir),
        work_items=work_items,
        gate_results=gate_results,
        tool_statuses=tool_statuses,
        artifact_reviews=artifact_reviews,
        arbitration_records=arbitration_records,
        quality_policy_results=quality_policy_results,
        created_at=utc_now_iso(),
    )
    (output_dir / "workflow-run.json").write_text(json.dumps(run.to_dict(), indent=2) + "\n", encoding="utf-8")
    write_gate_report(gate_results, output_dir)
    write_release_evidence(run, output_dir)
    return run


def create_artifact_package(requirements_path: Path, project_name: str | None = None) -> ArtifactPackage:
    brief = requirements_path.read_text(encoding="utf-8").strip()
    needs, system_requirements, software_requirements = build_requirements(brief)
    tasks = create_implementation_tasks(software_requirements)
    traceability = create_traceability_matrix(software_requirements, system_requirements, tasks)
    return ArtifactPackage(
        project_name=project_name or requirements_path.stem.replace("_", " ").replace("-", " ").title(),
        created_at=utc_now_iso(),
        source_brief=brief,
        user_needs=needs,
        system_requirements=system_requirements,
        software_requirements=software_requirements,
        implementation_tasks=tasks,
        traceability=traceability,
    )
