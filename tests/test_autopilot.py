from __future__ import annotations

from pathlib import Path

import subprocess

from vmodel_engine.autopilot import write_plantspeak_documentation, write_plantspeak_vertical_slice


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
    assert "Traceability links requirements to code and tests" in audit
    assert "| Local test evidence captured | PASS |" in audit
