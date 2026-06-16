from __future__ import annotations

from pathlib import Path

from vmodel_engine.artifact_quality import (
    detailed_design_inputs_pass,
    evaluate_detailed_design_inputs,
    evaluate_detailed_test_design,
    evaluate_integration_test_plan,
    evaluate_implementation_plan,
    evaluate_system_test_plan,
    evaluate_unit_test_plan,
    implementation_plan_passes,
    system_test_plan_passes,
)
from vmodel_engine.autopilot import (
    _firmware_architecture,
    _plantspeak_integration_test_plan,
    _plantspeak_system_test_plan,
    _plantspeak_unit_test_plan,
    _staged_development_test_plan,
)


def test_system_test_plan_quality_rejects_vague_plan(tmp_path: Path) -> None:
    plan = tmp_path / "10-system-test-plan.md"
    plan.write_text(
        """# System Test Plan

| Test ID | Scenario | Requirements | Status | Evidence |
| --- | --- | --- | --- | --- |
| ST-001 | Run self-test and require all checks true. | SW-001 through SW-014 | Implemented | PR CI plus local report |
""",
        encoding="utf-8",
    )

    issues = evaluate_system_test_plan(plan)

    assert not all(issue.passed for issue in issues)
    assert any(issue.check == "system-test-required-columns" and not issue.passed for issue in issues)
    assert any(issue.check == "system-test-no-vague-coverage" and not issue.passed for issue in issues)


def test_generated_system_test_plan_passes_quality_gate(tmp_path: Path) -> None:
    plan = tmp_path / "10-system-test-plan.md"
    plan.write_text(_plantspeak_system_test_plan(), encoding="utf-8")

    issues = evaluate_system_test_plan(plan)

    assert system_test_plan_passes(plan)
    assert all(issue.passed for issue in issues)


def test_implementation_plan_quality_rejects_narrative_plan(tmp_path: Path) -> None:
    plan = tmp_path / "staged-development-test-plan.md"
    plan.write_text(
        """# Staged Development And Test Plan

| Stage | Goal | Branch Pattern | Primary Agents | Required Tests | Exit Criteria |
| --- | --- | --- | --- | --- | --- |
| S1 foundation contracts | Define stable contracts. | `agent/foundation-contracts-*` | Architecture, Development, QA | unit tests for schemas | Contract tests pass. |

Every PR must update V-model docs, tests, traceability, and review evidence.
""",
        encoding="utf-8",
    )

    issues = evaluate_implementation_plan(plan)

    assert not all(issue.passed for issue in issues)
    assert any(issue.check == "implementation-plan-required-columns" and not issue.passed for issue in issues)
    assert any(issue.check == "implementation-plan-no-vague-execution" and not issue.passed for issue in issues)


def test_generated_implementation_plan_passes_quality_gate(tmp_path: Path) -> None:
    plan = tmp_path / "staged-development-test-plan.md"
    plan.write_text(_staged_development_test_plan(), encoding="utf-8")

    issues = evaluate_implementation_plan(plan)

    assert implementation_plan_passes(plan)
    assert all(issue.passed for issue in issues)


def test_firmware_architecture_contains_required_design_inputs() -> None:
    content = _firmware_architecture()

    for term in [
        "Firmware Layers",
        "Module Map",
        "Firmware Interfaces",
        "Detailed Design Inputs",
        "icd_dispatch",
        "measurement_service",
        "hal_i2c",
        "ble_transport",
        "ads1115_driver",
        "P0_8",
        "S6",
    ]:
        assert term in content


def test_detailed_design_input_gate_rejects_missing_package(tmp_path: Path) -> None:
    issues = evaluate_detailed_design_inputs(tmp_path)

    assert not detailed_design_inputs_pass(tmp_path)
    assert any(issue.check == "detailed-design-input-present" and not issue.passed for issue in issues)


def test_unit_test_plan_quality_rejects_status_only_rows(tmp_path: Path) -> None:
    plan = tmp_path / "08-unit-test-plan.md"
    plan.write_text(
        """# Unit Test Plan

| Test ID | Requirement | Unit Under Test | Status | Evidence |
| --- | --- | --- | --- | --- |
| UT-001 | SW-001 | app/icd.py | Implemented | `python -m pytest` |
""",
        encoding="utf-8",
    )

    issues = evaluate_unit_test_plan(plan)

    assert not all(issue.passed for issue in issues)
    assert any(issue.check == "unit-test-plan-required-columns" and not issue.passed for issue in issues)


def test_generated_detailed_test_design_passes_quality_gate(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "vmodel"
    docs_dir.mkdir(parents=True)
    rows = [
        {"unit": f"UT-{index:03d}", "requirement_id": f"SW-{index:03d}", "code": "plantspeak/devices.py"}
        for index in range(1, 15)
    ]
    (docs_dir / "08-unit-test-plan.md").write_text(_plantspeak_unit_test_plan(rows), encoding="utf-8")
    (docs_dir / "09-integration-test-plan.md").write_text(_plantspeak_integration_test_plan(), encoding="utf-8")

    issues = evaluate_detailed_test_design(tmp_path)

    assert all(issue.passed for issue in issues)


def test_integration_test_plan_quality_rejects_vague_ranges(tmp_path: Path) -> None:
    plan = tmp_path / "09-integration-test-plan.md"
    plan.write_text(
        """# Integration Test Plan

| Test ID | Requirements | Integration | Status | Evidence |
| --- | --- | --- | --- | --- |
| IT-001 | SW-006 through SW-010 | Dev-mode measurement integrates values. | Implemented | `tests/test_cli.py` |
""",
        encoding="utf-8",
    )

    issues = evaluate_integration_test_plan(plan)

    assert not all(issue.passed for issue in issues)
    assert any(issue.check == "integration-test-plan-required-columns" and not issue.passed for issue in issues)
