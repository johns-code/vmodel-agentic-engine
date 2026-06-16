from __future__ import annotations

from pathlib import Path

from vmodel_engine.artifacts import write_artifact_package
from vmodel_engine.engine import create_artifact_package


def generate_initial_artifacts(requirements_path: Path, output_dir: Path, project_name: str | None = None) -> list[Path]:
    package = create_artifact_package(requirements_path, project_name)
    return write_artifact_package(package, output_dir)
