from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactQualityIssue:
    artifact: str
    check: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


SYSTEM_TEST_COLUMNS = [
    "ID",
    "Test",
    "Preconditions",
    "Command / Procedure",
    "Expected Result",
    "Evidence Artifact",
    "Requirements",
    "Limits",
    "Failure Action",
]


FORBIDDEN_SYSTEM_TEST_PHRASES = [
    "SW-001 through SW-014",
    "SW-002 through SW-010",
    "All requirements",
    "all requirements",
    "all checks true",
    "PR CI plus local report",
    "CLI tests",
    "Human-approved deferred evidence",
]


def evaluate_system_test_plan(path: Path) -> list[ArtifactQualityIssue]:
    content = path.read_text(encoding="utf-8")
    issues: list[ArtifactQualityIssue] = []
    artifact = str(path)

    header = _first_table_header(content)
    missing_columns = [column for column in SYSTEM_TEST_COLUMNS if column not in header]
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="system-test-required-columns",
            passed=not missing_columns,
            message="All required system test columns are present."
            if not missing_columns
            else f"Missing required columns: {', '.join(missing_columns)}",
        )
    )

    rows = _table_rows(content)
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="system-test-row-count",
            passed=len(rows) >= 5,
            message="At least five system tests are defined." if len(rows) >= 5 else "System test plan must define at least five tests.",
        )
    )

    forbidden = [phrase for phrase in FORBIDDEN_SYSTEM_TEST_PHRASES if phrase in content]
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="system-test-no-vague-coverage",
            passed=not forbidden,
            message="No vague coverage/evidence phrases detected."
            if not forbidden
            else f"Vague phrases detected: {', '.join(forbidden)}",
        )
    )

    required_evidence = ["docs/test-evidence/ST-001.json", "docs/test-evidence/ST-002.txt", "docs/test-evidence/ST-003.json"]
    missing_evidence = [evidence for evidence in required_evidence if evidence not in content]
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="system-test-evidence-artifacts-named",
            passed=not missing_evidence,
            message="Required evidence artifacts are named."
            if not missing_evidence
            else f"Missing evidence artifact names: {', '.join(missing_evidence)}",
        )
    )

    has_limits = "Does not prove" in content and "target-board" in content
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="system-test-dev-mode-limits-explicit",
            passed=has_limits,
            message="Dev-mode limits are explicit."
            if has_limits
            else "System test plan must explicitly state what dev-mode tests do not prove.",
        )
    )

    has_failure_action = "Create or update a GitHub issue" in content
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="system-test-failure-action",
            passed=has_failure_action,
            message="Failure action is defined."
            if has_failure_action
            else "System test plan must define defect creation/update rules for failures.",
        )
    )
    return issues


def system_test_plan_passes(path: Path) -> bool:
    return all(issue.passed for issue in evaluate_system_test_plan(path))


def _first_table_header(content: str) -> list[str]:
    for line in content.splitlines():
        if line.startswith("|") and "---" not in line:
            return [cell.strip() for cell in line.strip("|").split("|")]
    return []


def _table_rows(content: str) -> list[str]:
    rows = []
    for line in content.splitlines():
        if not line.startswith("|"):
            continue
        if "---" in line:
            continue
        if line.startswith("| ID |") or line.startswith("| Check |") or line.startswith("| Review Theme |"):
            continue
        rows.append(line)
    return rows
