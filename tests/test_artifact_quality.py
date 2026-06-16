from __future__ import annotations

from pathlib import Path

from vmodel_engine.artifact_quality import evaluate_system_test_plan, system_test_plan_passes
from vmodel_engine.autopilot import _plantspeak_system_test_plan


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
