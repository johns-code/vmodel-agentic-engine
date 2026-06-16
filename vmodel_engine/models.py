from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class UserNeed:
    id: str
    statement: str
    rationale: str
    source: str = "user_brief"


@dataclass(frozen=True)
class Requirement:
    id: str
    parent_id: str
    statement: str
    priority: str
    acceptance_criteria: list[str]


@dataclass(frozen=True)
class ImplementationTask:
    id: str
    title: str
    description: str
    requirement_ids: list[str]
    suggested_owner_role: str
    status: str = "planned"
    external_ref: str | None = None


@dataclass(frozen=True)
class TraceLink:
    requirement_id: str
    user_need_id: str
    design_refs: list[str]
    task_refs: list[str]
    test_refs: list[str]
    verification_refs: list[str]
    status: str


@dataclass(frozen=True)
class ArtifactPackage:
    project_name: str
    created_at: str
    source_brief: str
    user_needs: list[UserNeed] = field(default_factory=list)
    system_requirements: list[Requirement] = field(default_factory=list)
    software_requirements: list[Requirement] = field(default_factory=list)
    implementation_tasks: list[ImplementationTask] = field(default_factory=list)
    traceability: list[TraceLink] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkItem:
    id: str
    title: str
    description: str
    requirement_ids: list[str]
    source_task_id: str
    status: str


@dataclass(frozen=True)
class GateResult:
    name: str
    command: list[str]
    passed: bool
    exit_code: int
    output: str


@dataclass(frozen=True)
class ToolStatus:
    name: str
    purpose: str
    command: str
    available: bool
    version_output: str = ""


@dataclass(frozen=True)
class AgentRole:
    id: str
    title: str
    mission: str
    authority: str
    lenses: list[str]


@dataclass(frozen=True)
class ArtifactReview:
    id: str
    artifact_id: str
    artifact_title: str
    reviewer_role: str
    lens: str
    verdict: str
    findings: list[str]
    required_actions: list[str]


@dataclass(frozen=True)
class ArbitrationRecord:
    id: str
    topic: str
    raised_by: str
    counterparty: str
    decision: str
    rationale: str
    required_follow_up: list[str]


@dataclass(frozen=True)
class QualityPolicyResult:
    name: str
    passed: bool
    details: str


@dataclass(frozen=True)
class WorkflowRun:
    project_name: str
    project_type: str
    status: str
    artifact_dir: str
    generated_project_dir: str
    work_items: list[WorkItem]
    gate_results: list[GateResult]
    tool_statuses: list[ToolStatus]
    artifact_reviews: list[ArtifactReview]
    arbitration_records: list[ArbitrationRecord]
    quality_policy_results: list[QualityPolicyResult]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
