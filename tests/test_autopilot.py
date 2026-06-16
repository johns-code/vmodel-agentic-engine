from __future__ import annotations

from pathlib import Path

import json
import subprocess

from vmodel_engine.autopilot import write_artifact_review_cycle, write_plantspeak_documentation, write_plantspeak_vertical_slice


def test_write_plantspeak_vertical_slice_creates_domain_code(tmp_path: Path) -> None:
    package = {
        "software_requirements": [
            {
                "id": f"SW-{index:03d}",
                "parent_id": f"SYS-{index:03d}",
                "statement": f"requirement {index}",
                "priority": "must",
                "acceptance_criteria": ["covered"],
            }
            for index in range(1, 15)
        ]
    }
    issues = [
        {
            "id": f"issue-{index}",
            "number": 98 + index,
            "title": f"SW-{index:03d}: requirement {index}",
            "url": f"https://example.test/issues/{index}",
            "requirement_ids": [f"SW-{index:03d}"],
        }
        for index in range(1, 15)
    ]

    written = write_plantspeak_vertical_slice(tmp_path, package, issues)

    normalized = {path.replace("\\", "/") for path in written}
    assert "plantspeak/devices.py" in normalized
    assert "plantspeak/icd.py" in normalized
    assert "tests/test_cli.py" in normalized
    assert (tmp_path / "plantspeak" / "data" / "requirements.json").exists()
    assert "P0_5" in (tmp_path / "plantspeak" / "pins.py").read_text(encoding="utf-8")
    assert "canned-dev-mode-data" in (tmp_path / "plantspeak" / "devices.py").read_text(encoding="utf-8")


def test_write_plantspeak_documentation_creates_quality_audit(tmp_path: Path) -> None:
    package = {
        "software_requirements": [
            {
                "id": f"SW-{index:03d}",
                "parent_id": f"SYS-{index:03d}",
                "statement": f"requirement {index}",
                "priority": "must",
                "acceptance_criteria": ["covered"],
            }
            for index in range(1, 15)
        ]
    }
    issues = [
        {
            "id": f"issue-{index}",
            "number": 98 + index,
            "title": f"SW-{index:03d}: requirement {index}",
            "url": f"https://example.test/issues/{index}",
            "requirement_ids": [f"SW-{index:03d}"],
        }
        for index in range(1, 15)
    ]
    local_test = subprocess.CompletedProcess(args=["python", "-m", "pytest"], returncode=0, stdout="11 passed", stderr="")

    written = write_plantspeak_documentation(tmp_path, package, issues, local_test)
    normalized = {path.replace("\\", "/") for path in written}

    assert "docs/vmodel/04-architecture-design.md" in normalized
    assert "docs/planning/software-lead-execution-plan.md" in normalized
    assert "docs/planning/documentation-quality-audit.md" in normalized
    audit = (tmp_path / "docs" / "planning" / "documentation-quality-audit.md").read_text(encoding="utf-8")
    assert "Traceability links requirements to existing tests only" in audit
    assert "| Blocking review comments resolved | PASS |" in audit
    assert "| Local test evidence captured | PASS |" in audit
    assert (tmp_path / "docs" / "planning" / "staged-development-test-plan.md").exists()


def test_write_artifact_review_cycle_requires_three_reviews_per_doc(tmp_path: Path) -> None:
    vmodel_dir = tmp_path / "docs" / "vmodel"
    planning_dir = tmp_path / "docs" / "planning"
    vmodel_dir.mkdir(parents=True)
    planning_dir.mkdir(parents=True)
    for name in ["04-architecture-design.md", "06-implementation-task-plan.md"]:
        (vmodel_dir / name).write_text(f"# {name}\n", encoding="utf-8")
    (planning_dir / "software-lead-execution-plan.md").write_text("# lead\n", encoding="utf-8")

    written = write_artifact_review_cycle(tmp_path)
    normalized = {path.replace("\\", "/") for path in written}

    assert "docs/reviews/artifact-review-cycle.md" in normalized
    assert "docs/reviews/artifact-comments/04-architecture-design.md" in normalized
    summary = json.loads((tmp_path / "docs" / "reviews" / "artifact-review-cycle.json").read_text(encoding="utf-8"))
    assert summary["artifact_count"] == 3
    assert summary["review_count"] == 9
    assert summary["reviews_per_artifact"] == 3
    assert summary["implementation_readiness"] == "blocked_pending_review_actions"
