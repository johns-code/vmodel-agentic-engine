from __future__ import annotations

from pathlib import Path

from vmodel_engine.autopilot import write_plantspeak_vertical_slice


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

    assert "plantspeak\\devices.py" in written
    assert "plantspeak\\icd.py" in written
    assert "tests\\test_cli.py" in written
    assert (tmp_path / "plantspeak" / "data" / "requirements.json").exists()
    assert "P0_5" in (tmp_path / "plantspeak" / "pins.py").read_text(encoding="utf-8")
    assert "canned-dev-mode-data" in (tmp_path / "plantspeak" / "devices.py").read_text(encoding="utf-8")
