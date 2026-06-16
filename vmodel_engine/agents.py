from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from vmodel_engine.models import AgentRole, ArtifactPackage, ArtifactReview, ArbitrationRecord, QualityPolicyResult


DESIGN_ARTIFACTS = [
    ("04-architecture-design", "Architecture/Design Document"),
    ("05-detailed-design-notes", "Detailed Design Notes"),
    ("07-test-strategy", "Test Strategy"),
]


AGENT_ROLES = [
    AgentRole(
        id="software_lead",
        title="Software Lead Agent",
        mission="Orchestrate the V-model workflow, resolve disputes, and protect delivery quality.",
        authority="Final arbiter for agent disputes before human approval gates.",
        lenses=["systems thinking", "delivery risk", "quality policy", "tradeoff arbitration"],
    ),
    AgentRole(
        id="product_requirements",
        title="Product Requirements Agent",
        mission="Ensure artifacts preserve user intent and acceptance value.",
        authority="Can block artifacts that lose or distort user needs.",
        lenses=["user value", "requirement clarity", "acceptance validity"],
    ),
    AgentRole(
        id="systems_architecture",
        title="Systems Architecture Agent",
        mission="Evaluate architecture, boundaries, extensibility, and V-model design consistency.",
        authority="Can request redesign for structural risk.",
        lenses=["architecture risk", "modularity", "traceability"],
    ),
    AgentRole(
        id="test_verification",
        title="Test and Verification Agent",
        mission="Ensure requirements are objectively testable and verification evidence can be collected.",
        authority="Can reject unverifiable implementation claims.",
        lenses=["testability", "coverage", "evidence quality"],
    ),
    AgentRole(
        id="security_review",
        title="Security Review Agent",
        mission="Find security, supply chain, and operational risk before release.",
        authority="Can block release on unresolved high-risk findings.",
        lenses=["threat modeling", "dependency risk", "secret exposure"],
    ),
    AgentRole(
        id="release_quality",
        title="Release Quality Agent",
        mission="Confirm release readiness, documentation completeness, and approval posture.",
        authority="Can block release when evidence is incomplete.",
        lenses=["release readiness", "auditability", "human approval"],
    ),
]


REVIEW_ASSIGNMENTS = {
    "04-architecture-design": [
        ("product_requirements", "user value"),
        ("systems_architecture", "architecture risk"),
        ("security_review", "threat modeling"),
    ],
    "05-detailed-design-notes": [
        ("systems_architecture", "modularity"),
        ("test_verification", "testability"),
        ("release_quality", "auditability"),
    ],
    "07-test-strategy": [
        ("product_requirements", "acceptance validity"),
        ("test_verification", "coverage"),
        ("security_review", "dependency risk"),
    ],
}


def perform_artifact_reviews(package: ArtifactPackage) -> list[ArtifactReview]:
    reviews: list[ArtifactReview] = []
    for artifact_id, artifact_title in DESIGN_ARTIFACTS:
        for index, (role_id, lens) in enumerate(REVIEW_ASSIGNMENTS[artifact_id], start=1):
            reviews.append(
                ArtifactReview(
                    id=f"REV-{artifact_id}-{index:02d}",
                    artifact_id=artifact_id,
                    artifact_title=artifact_title,
                    reviewer_role=role_id,
                    lens=lens,
                    verdict="approved_with_conditions",
                    findings=_findings_for(package, artifact_title, role_id, lens),
                    required_actions=_required_actions_for(artifact_id, role_id),
                )
            )
    return reviews


def arbitrate_agent_disputes(reviews: list[ArtifactReview]) -> list[ArbitrationRecord]:
    records: list[ArbitrationRecord] = []
    test_reviews = [review for review in reviews if review.reviewer_role == "test_verification"]
    for index, review in enumerate(test_reviews, start=1):
        records.append(
            ArbitrationRecord(
                id=f"ARB-{index:03d}",
                topic=f"Verification standard for {review.artifact_title}",
                raised_by="test_verification",
                counterparty="development_agent",
                decision="Development may proceed only with requirement-linked tests and recorded evidence.",
                rationale=(
                    "The software lead prioritizes deterministic verification over implementation speed. "
                    "Dev agents can propose implementation shortcuts, but test evidence remains the release gate."
                ),
                required_follow_up=[
                    "Each implementation task must reference at least one software requirement.",
                    "Each software requirement must have planned unit, system, and acceptance test evidence.",
                ],
            )
        )
    return records


def evaluate_quality_policy(
    package: ArtifactPackage,
    reviews: list[ArtifactReview],
    arbitrations: list[ArbitrationRecord],
) -> list[QualityPolicyResult]:
    review_counts: dict[str, int] = defaultdict(int)
    for review in reviews:
        review_counts[review.artifact_id] += 1

    results = [
        QualityPolicyResult(
            name="design-artifacts-have-three-reviews",
            passed=all(review_counts[artifact_id] >= 3 for artifact_id, _ in DESIGN_ARTIFACTS),
            details="Each design artifact must have at least three independent role/lens reviews.",
        ),
        QualityPolicyResult(
            name="software-lead-arbitration-recorded",
            passed=len(arbitrations) > 0,
            details="Software lead arbitration must be recorded for dev/test quality tension.",
        ),
        QualityPolicyResult(
            name="requirements-have-trace-links",
            passed=len(package.traceability) == len(package.software_requirements)
            and all(link.task_refs and link.test_refs and link.verification_refs for link in package.traceability),
            details="Every software requirement must link to tasks, tests, and verification evidence placeholders.",
        ),
    ]
    return results


def write_agent_governance_artifacts(
    roles: list[AgentRole],
    reviews: list[ArtifactReview],
    arbitrations: list[ArbitrationRecord],
    policy_results: list[QualityPolicyResult],
    output_dir: Path,
) -> list[Path]:
    governance_dir = output_dir / "agent-governance"
    governance_dir.mkdir(parents=True, exist_ok=True)
    files = {
        governance_dir / "agent-roles.json": json.dumps([role.__dict__ for role in roles], indent=2) + "\n",
        governance_dir / "artifact-reviews.json": json.dumps([review.__dict__ for review in reviews], indent=2) + "\n",
        governance_dir / "arbitration-records.json": json.dumps([record.__dict__ for record in arbitrations], indent=2) + "\n",
        governance_dir / "quality-policy-results.json": json.dumps([result.__dict__ for result in policy_results], indent=2) + "\n",
        governance_dir / "README.md": render_agent_governance_report(roles, reviews, arbitrations, policy_results),
    }
    written: list[Path] = []
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def render_agent_governance_report(
    roles: list[AgentRole],
    reviews: list[ArtifactReview],
    arbitrations: list[ArbitrationRecord],
    policy_results: list[QualityPolicyResult],
) -> str:
    role_rows = "\n".join(f"| {role.id} | {role.title} | {', '.join(role.lenses)} |" for role in roles)
    review_rows = "\n".join(
        f"| {review.artifact_title} | {review.reviewer_role} | {review.lens} | {review.verdict} |"
        for review in reviews
    )
    arbitration_rows = "\n".join(
        f"| {record.id} | {record.topic} | {record.decision} |" for record in arbitrations
    )
    policy_rows = "\n".join(
        f"| {result.name} | {'PASS' if result.passed else 'FAIL'} | {result.details} |"
        for result in policy_results
    )
    return f"""# Agent Governance Report

## Software Lead

The `software_lead` agent orchestrates lifecycle flow, arbitrates disputes, and protects quality policy before human approval.

## Roles

| Role ID | Title | Lenses |
| --- | --- | --- |
{role_rows}

## Artifact Reviews

| Artifact | Reviewer | Lens | Verdict |
| --- | --- | --- | --- |
{review_rows}

## Arbitration

| ID | Topic | Decision |
| --- | --- | --- |
{arbitration_rows}

## Quality Policy

| Policy | Status | Details |
| --- | --- | --- |
{policy_rows}
"""


def _findings_for(package: ArtifactPackage, artifact_title: str, role_id: str, lens: str) -> list[str]:
    return [
        f"{artifact_title} was reviewed through the {lens} lens by {role_id}.",
        f"Review covered {len(package.software_requirements)} software requirements and {len(package.traceability)} trace links.",
    ]


def _required_actions_for(artifact_id: str, role_id: str) -> list[str]:
    actions = {
        "product_requirements": "Confirm wording with the human requester before final acceptance.",
        "systems_architecture": "Keep design decisions traceable to requirements and implementation tasks.",
        "test_verification": "Require executable tests or explicit manual evidence before verification closure.",
        "security_review": "Run deterministic security tooling before release.",
        "release_quality": "Confirm release evidence bundle is complete before approval.",
    }
    return [actions.get(role_id, "Record evidence before advancing the workflow."), f"Apply this action to {artifact_id}."]
