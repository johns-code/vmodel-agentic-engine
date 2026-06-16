import json
from pathlib import Path

from vmodel_engine.engine import build_project


def test_build_project_runs_vertical_workflow(tmp_path: Path) -> None:
    requirements_file = tmp_path / "brief.txt"
    requirements_file.write_text(
        "- Users must list structured requirements.\n- The app should print trace status.\n",
        encoding="utf-8",
    )

    run = build_project(requirements_file, tmp_path / "run", "Generated Demo")

    assert run.status == "ready_for_human_acceptance"
    assert len(run.work_items) == 2
    assert all(gate.passed for gate in run.gate_results)
    assert any(tool.name == "pytest" for tool in run.tool_statuses)
    assert len(run.artifact_reviews) == 9
    assert run.arbitration_records
    assert all(result.passed for result in run.quality_policy_results)
    assert (tmp_path / "run" / "artifacts" / "artifact-package.json").exists()
    assert (tmp_path / "run" / "agent-governance" / "README.md").exists()
    assert "[project.optional-dependencies]" in (
        tmp_path / "run" / "generated-project" / "pyproject.toml"
    ).read_text(encoding="utf-8")
    assert (tmp_path / "run" / "work-items" / "LOCAL-001.json").exists()
    assert (tmp_path / "run" / "generated-project" / "generated_demo" / "cli.py").exists()
    workflow = json.loads((tmp_path / "run" / "workflow-run.json").read_text(encoding="utf-8"))
    assert workflow["project_type"] == "python-cli"
    assert workflow["tool_statuses"]
    assert workflow["artifact_reviews"]


def test_build_project_accepts_requirements_directory(tmp_path: Path) -> None:
    requirements_dir = tmp_path / "requirements"
    requirements_dir.mkdir()
    (requirements_dir / "User Requirements.txt").write_text("- Users must record observations.\n", encoding="utf-8")
    (requirements_dir / "Toolchain.md").write_text("- The system should support dev-board testing.\n", encoding="utf-8")

    run = build_project(requirements_dir, tmp_path / "run", "PlantSpeak")

    assert run.status == "ready_for_human_acceptance"
    package = (tmp_path / "run" / "artifacts" / "artifact-package.json").read_text(encoding="utf-8")
    assert "Toolchain.md" in package
