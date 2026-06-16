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

DETAILED_DESIGN_INPUTS = {
    "docs/vmodel/01-user-needs.md": ["Success Condition", "Dev-mode", "target"],
    "docs/vmodel/02-system-requirements.md": ["Priority", "Acceptance Criteria", "must"],
    "docs/vmodel/03-software-requirements.md": ["Observable Behavior", "Verification Test", "SW-014"],
    "docs/vmodel/04-architecture-design.md": ["Interface Contracts", "Firmware command table", "BLE transport"],
    "docs/vmodel/05-detailed-design-notes.md": ["Data Contracts", "Error And Deferred Behavior", "Dev-Mode Value"],
    "docs/vmodel/06-implementation-task-plan.md": ["Task Policy", "Exit Gate", "TASK-014"],
    "docs/vmodel/07-test-strategy.md": ["target-board evidence", "GitHub Actions", "acceptance validation"],
    "docs/vmodel/08-unit-test-plan.md": ["Test ID", "Unit Under Test", "UT-014"],
    "docs/vmodel/09-integration-test-plan.md": ["Integration", "IT-001", "IT-003"],
    "docs/vmodel/10-system-test-plan.md": ["Preconditions", "Expected Result", "Failure Action"],
    "docs/vmodel/11-acceptance-test-plan.md": ["Acceptance Condition", "Pending human approval", "AT-004"],
    "docs/vmodel/12-requirements-traceability-matrix.md": ["Requirement", "Code", "Tests"],
    "docs/planning/software-lead-execution-plan.md": ["Immediate Lead Actions", "Exit Criteria", "Software Lead"],
    "docs/planning/issue-sequencing-plan.md": ["Dependency", "Exit Gate", "S3 hardware"],
    "docs/planning/risk-register.md": ["Risk", "Mitigation", "Open"],
    "docs/planning/staged-development-test-plan.md": ["PR / Branch", "Files / Modules", "Definition Of Done"],
    "docs/firmware/architecture.md": ["Firmware Layers", "Module Map", "Firmware Interfaces", "Detailed Design Inputs"],
}

FIRMWARE_ARCHITECTURE_REQUIRED_TERMS = [
    "icd_dispatch",
    "measurement_service",
    "hal_i2c",
    "ble_transport",
    "ads1115_driver",
    "pca9846_driver",
    "lp5816_driver",
    "mlx90632_driver",
    "hdc2010_driver",
    "mxc4005_driver",
    "P0_5",
    "P0_11",
    "P0_10",
    "P0_6",
    "P0_8",
    "P0_9",
    "S5",
    "S6",
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


def evaluate_detailed_design_inputs(repo_dir: Path) -> list[ArtifactQualityIssue]:
    issues: list[ArtifactQualityIssue] = []
    for relative, required_terms in DETAILED_DESIGN_INPUTS.items():
        path = repo_dir / relative
        if not path.exists():
            issues.append(
                ArtifactQualityIssue(
                    artifact=relative,
                    check="detailed-design-input-present",
                    passed=False,
                    message=f"Missing required detailed-design input artifact: {relative}",
                )
            )
            continue
        content = path.read_text(encoding="utf-8")
        missing_terms = [term for term in required_terms if term not in content]
        issues.append(
            ArtifactQualityIssue(
                artifact=relative,
                check="detailed-design-input-content",
                passed=not missing_terms,
                message="Artifact contains required detailed-design input markers."
                if not missing_terms
                else f"Missing detailed-design markers: {', '.join(missing_terms)}",
            )
        )

    firmware_path = repo_dir / "docs" / "firmware" / "architecture.md"
    if firmware_path.exists():
        firmware_content = firmware_path.read_text(encoding="utf-8")
        missing_firmware_terms = [term for term in FIRMWARE_ARCHITECTURE_REQUIRED_TERMS if term not in firmware_content]
        issues.append(
            ArtifactQualityIssue(
                artifact=str(firmware_path),
                check="firmware-architecture-specificity",
                passed=not missing_firmware_terms,
                message="Firmware architecture names required modules, pins, drivers, and stages."
                if not missing_firmware_terms
                else f"Missing firmware architecture terms: {', '.join(missing_firmware_terms)}",
            )
        )
    return issues


def detailed_design_inputs_pass(repo_dir: Path) -> bool:
    return all(issue.passed for issue in evaluate_detailed_design_inputs(repo_dir))


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
