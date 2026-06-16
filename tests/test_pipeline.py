import json
from pathlib import Path

from vmodel_engine.pipeline import generate_initial_artifacts


def test_generate_initial_artifacts(tmp_path: Path) -> None:
    requirements_file = tmp_path / "brief.txt"
    requirements_file.write_text(
        "- Users must submit requirements.\n- The engine should produce Markdown artifacts.\n",
        encoding="utf-8",
    )

    written = generate_initial_artifacts(requirements_file, tmp_path / "out", "Test Project")

    assert len(written) == 18
    package = json.loads((tmp_path / "out" / "artifact-package.json").read_text(encoding="utf-8"))
    assert package["project_name"] == "Test Project"
    assert len(package["user_needs"]) == 2
    assert len(package["software_requirements"]) == 2
    assert package["traceability"][0]["requirement_id"] == "SW-001"
    assert (tmp_path / "out" / "12-requirements-traceability-matrix.md").exists()
