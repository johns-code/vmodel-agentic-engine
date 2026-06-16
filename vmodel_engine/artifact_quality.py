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

IMPLEMENTATION_PLAN_COLUMNS = [
    "Stage",
    "PR / Branch",
    "Issues",
    "Requirements",
    "Files / Modules",
    "Tests",
    "Docs Updated",
    "Review Agents",
    "CI Gates",
    "Rollback / Failure Action",
    "Definition Of Done",
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

FORBIDDEN_IMPLEMENTATION_PLAN_PHRASES = [
    "one or more issue-linked PRs",
    "Every PR must update",
    "full CI",
    "review checklist",
    "doc quality checks",
    "unit tests for schemas",
    "mock I2C tests",
    "HIL tests with captured logs",
    "agent/*",
    "agent/**",
    "Branch Pattern",
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


def evaluate_implementation_plan(path: Path) -> list[ArtifactQualityIssue]:
    content = path.read_text(encoding="utf-8")
    artifact = str(path)
    issues: list[ArtifactQualityIssue] = []

    header = _first_table_header(content)
    missing_columns = [column for column in IMPLEMENTATION_PLAN_COLUMNS if column not in header]
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="implementation-plan-required-columns",
            passed=not missing_columns,
            message="All required implementation execution columns are present."
            if not missing_columns
            else f"Missing required columns: {', '.join(missing_columns)}",
        )
    )

    rows = _table_rows(content)
    stage_rows = [row for row in rows if row.startswith("| S")]
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="implementation-plan-stage-count",
            passed=len(stage_rows) >= 8,
            message="S0 through S7 implementation stages are defined."
            if len(stage_rows) >= 8
            else "Implementation plan must define S0 through S7 execution rows.",
        )
    )

    required_branches = [
        "agent/generated-implementation",
        "agent/s1-foundation-contracts",
        "agent/s2-devmode-harness",
        "agent/s3-hardware-adapters",
        "agent/s4-ble-icd-transport",
        "agent/s5-firmware-build",
        "agent/s6-hil-qualification",
        "agent/s7-release-candidate",
    ]
    missing_branches = [branch for branch in required_branches if branch not in content]
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="implementation-plan-exact-branches",
            passed=not missing_branches,
            message="Exact branch names are present."
            if not missing_branches
            else f"Missing branch names: {', '.join(missing_branches)}",
        )
    )

    required_files = [
        "plantspeak/contracts.py",
        "plantspeak/trace.py",
        "plantspeak/transport.py",
        "plantspeak/adapters/i2c.py",
        "firmware/README.md",
        "docs/test-evidence/ST-006-hil-report.md",
    ]
    missing_files = [file for file in required_files if file not in content]
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="implementation-plan-files-named",
            passed=not missing_files,
            message="Concrete files/modules are named."
            if not missing_files
            else f"Missing files/modules: {', '.join(missing_files)}",
        )
    )

    required_tests = [
        "tests/test_contracts.py",
        "tests/test_traceability.py",
        "tests/test_transport.py",
        "tests/test_adapters.py",
        "tests/test_system_evidence.py",
    ]
    missing_tests = [test for test in required_tests if test not in content]
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="implementation-plan-tests-named",
            passed=not missing_tests,
            message="Concrete tests are named."
            if not missing_tests
            else f"Missing tests: {', '.join(missing_tests)}",
        )
    )

    forbidden = [phrase for phrase in FORBIDDEN_IMPLEMENTATION_PLAN_PHRASES if phrase in content]
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="implementation-plan-no-vague-execution",
            passed=not forbidden,
            message="No vague implementation execution phrases detected."
            if not forbidden
            else f"Vague phrases detected: {', '.join(forbidden)}",
        )
    )

    has_rollback = "Revert PR branch" in content and "create/update defect issue" in content
    issues.append(
        ArtifactQualityIssue(
            artifact=artifact,
            check="implementation-plan-failure-actions",
            passed=has_rollback,
            message="Rollback and defect actions are defined."
            if has_rollback
            else "Implementation plan must define rollback and defect actions.",
        )
    )
    return issues


def implementation_plan_passes(path: Path) -> bool:
    return all(issue.passed for issue in evaluate_implementation_plan(path))


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
