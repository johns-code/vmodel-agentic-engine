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
    assert (tmp_path / "run" / "artifacts" / "artifact-package.json").exists()
    assert (tmp_path / "run" / "work-items" / "LOCAL-001.json").exists()
    assert (tmp_path / "run" / "generated-project" / "generated_demo" / "cli.py").exists()
    workflow = json.loads((tmp_path / "run" / "workflow-run.json").read_text(encoding="utf-8"))
    assert workflow["project_type"] == "python-cli"
    assert workflow["tool_statuses"]
