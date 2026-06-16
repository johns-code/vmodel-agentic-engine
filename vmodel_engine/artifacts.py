from __future__ import annotations

import json
from pathlib import Path

from vmodel_engine.models import ArtifactPackage, Requirement


ARTIFACT_FILENAMES = {
    "user_needs": "01-user-needs.md",
    "system_requirements": "02-system-requirements.md",
    "software_requirements": "03-software-requirements.md",
    "architecture": "04-architecture-design.md",
    "detailed_design": "05-detailed-design-notes.md",
    "implementation_plan": "06-implementation-task-plan.md",
    "test_strategy": "07-test-strategy.md",
    "unit_test_plan": "08-unit-test-plan.md",
    "integration_test_plan": "09-integration-test-plan.md",
    "system_test_plan": "10-system-test-plan.md",
    "acceptance_test_plan": "11-acceptance-test-plan.md",
    "traceability": "12-requirements-traceability-matrix.md",
    "verification_report": "13-verification-report.md",
    "validation_report": "14-validation-report.md",
    "code_review_report": "15-code-review-report.md",
    "security_review_report": "16-security-review-report.md",
    "release_notes": "17-release-notes.md",
}


def write_artifact_package(package: ArtifactPackage, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = [
        _write(output_dir / "artifact-package.json", json.dumps(package.to_dict(), indent=2) + "\n"),
        _write(output_dir / ARTIFACT_FILENAMES["user_needs"], render_user_needs(package)),
        _write(output_dir / ARTIFACT_FILENAMES["system_requirements"], render_requirements("System Requirements Specification", package.system_requirements)),
        _write(output_dir / ARTIFACT_FILENAMES["software_requirements"], render_requirements("Software Requirements Specification", package.software_requirements)),
        _write(output_dir / ARTIFACT_FILENAMES["architecture"], render_architecture(package)),
        _write(output_dir / ARTIFACT_FILENAMES["detailed_design"], render_detailed_design(package)),
        _write(output_dir / ARTIFACT_FILENAMES["implementation_plan"], render_implementation_plan(package)),
        _write(output_dir / ARTIFACT_FILENAMES["test_strategy"], render_test_strategy(package)),
        _write(output_dir / ARTIFACT_FILENAMES["unit_test_plan"], render_test_plan(package, "Unit Test Plan", "UT")),
        _write(output_dir / ARTIFACT_FILENAMES["integration_test_plan"], render_test_plan(package, "Integration Test Plan", "IT")),
        _write(output_dir / ARTIFACT_FILENAMES["system_test_plan"], render_test_plan(package, "System Test Plan", "ST")),
        _write(output_dir / ARTIFACT_FILENAMES["acceptance_test_plan"], render_test_plan(package, "Acceptance Test Plan", "AT")),
        _write(output_dir / ARTIFACT_FILENAMES["traceability"], render_traceability(package)),
        _write(output_dir / ARTIFACT_FILENAMES["verification_report"], render_verification_report(package)),
        _write(output_dir / ARTIFACT_FILENAMES["validation_report"], render_validation_report(package)),
        _write(output_dir / ARTIFACT_FILENAMES["code_review_report"], render_review_report(package, "Code Review Report")),
        _write(output_dir / ARTIFACT_FILENAMES["security_review_report"], render_review_report(package, "Security Review Report")),
        _write(output_dir / ARTIFACT_FILENAMES["release_notes"], render_release_notes(package)),
    ]
    return written


def render_user_needs(package: ArtifactPackage) -> str:
    rows = "\n".join(f"| {need.id} | {need.statement} | {need.rationale} |" for need in package.user_needs)
    return _header(package, "User Needs Document") + "\n| ID | Need | Rationale |\n| --- | --- | --- |\n" + rows + "\n"


def render_requirements(title: str, requirements: list[Requirement]) -> str:
    rows = []
    for requirement in requirements:
        criteria = "<br>".join(requirement.acceptance_criteria)
        rows.append(f"| {requirement.id} | {requirement.parent_id} | {requirement.priority} | {requirement.statement} | {criteria} |")
    return f"# {title}\n\n| ID | Parent | Priority | Requirement | Acceptance Criteria |\n| --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n"


def render_architecture(package: ArtifactPackage) -> str:
    return _header(package, "Architecture/Design Document") + """
## Initial Architecture

The MVP is a deterministic artifact-generation pipeline with replaceable agent interfaces.

## Components

| Component | Responsibility |
| --- | --- |
| CLI intake | Accept requirements input and output location. |
| Requirements agent | Convert user brief statements into structured V-model requirements. |
| Planning agent | Produce implementation work items from software requirements. |
| Traceability agent | Link requirements to design placeholders, tasks, tests, and verification records. |
| Artifact writer | Emit Markdown and JSON artifacts for inspection and future CI use. |

## Integration Direction

Later releases should connect work items to GitHub Issues or Jira, create implementation branches and pull requests, and use CI results as release gates.
"""


def render_detailed_design(package: ArtifactPackage) -> str:
    lines = [_header(package, "Detailed Design Notes"), "## Requirement-Level Design Placeholders", ""]
    for link in package.traceability:
        lines.append(f"- `{link.design_refs[0]}`: Design detail for `{link.requirement_id}` is pending elaboration by the design agent.")
    return "\n".join(lines) + "\n"


def render_implementation_plan(package: ArtifactPackage) -> str:
    rows = "\n".join(
        f"| {task.id} | {task.title} | {', '.join(task.requirement_ids)} | {task.suggested_owner_role} | {task.status} |"
        for task in package.implementation_tasks
    )
    return _header(package, "Implementation Task Plan") + "\n| ID | Title | Requirements | Owner Role | Status |\n| --- | --- | --- | --- | --- |\n" + rows + "\n"


def render_test_strategy(package: ArtifactPackage) -> str:
    return _header(package, "Test Strategy") + """
## Strategy

Verification proceeds from implementation detail toward user acceptance:

| V-Model Level | Evidence |
| --- | --- |
| Unit verification | Unit tests linked to software requirements. |
| Integration verification | Interface and workflow tests linked to architecture decisions. |
| System verification | End-to-end tests proving system requirements. |
| User acceptance validation | Acceptance tests proving user needs. |

CI results are treated as authoritative gate evidence once tool integrations are enabled.
"""


def render_test_plan(package: ArtifactPackage, title: str, prefix: str) -> str:
    rows = []
    for index, requirement in enumerate(package.software_requirements, start=1):
        rows.append(f"| {prefix}-{index:003d} | {requirement.id} | Planned | Verify: {requirement.statement} |")
    return _header(package, title) + "\n| Test ID | Requirement | Status | Objective |\n| --- | --- | --- | --- |\n" + "\n".join(rows) + "\n"


def render_traceability(package: ArtifactPackage) -> str:
    rows = []
    for link in package.traceability:
        rows.append(
            f"| {link.user_need_id} | {link.requirement_id} | {', '.join(link.design_refs)} | "
            f"{', '.join(link.task_refs)} | {', '.join(link.test_refs)} | {', '.join(link.verification_refs)} | {link.status} |"
        )
    return _header(package, "Requirements Traceability Matrix") + "\n| User Need | Requirement | Design | Tasks | Tests | Verification | Status |\n| --- | --- | --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n"


def render_verification_report(package: ArtifactPackage) -> str:
    return _gate_report(package, "Verification Report", "Verification is pending implementation and CI execution.")


def render_validation_report(package: ArtifactPackage) -> str:
    return _gate_report(package, "Validation Report", "Validation is pending user acceptance review.")


def render_review_report(package: ArtifactPackage, title: str) -> str:
    return _gate_report(package, title, "Review is pending pull request and static analysis evidence.")


def render_release_notes(package: ArtifactPackage) -> str:
    return _header(package, "Release Notes") + """
## Status

Initial artifact package generated. No deployable software release has been approved yet.

## Human Approval Gate

Final release requires explicit human approval after verification, validation, code review, and security review are complete.
"""


def _gate_report(package: ArtifactPackage, title: str, note: str) -> str:
    return _header(package, title) + f"\n## Gate Status\n\nPending\n\n## Evidence\n\n{note}\n"


def _header(package: ArtifactPackage, title: str) -> str:
    return f"# {title}\n\nProject: {package.project_name}\n\nGenerated: {package.created_at}\n"


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path
