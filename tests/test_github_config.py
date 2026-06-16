import json
from pathlib import Path

from vmodel_engine.github import load_github_project_config


def test_load_github_project_config(tmp_path: Path) -> None:
    config_path = tmp_path / "github.json"
    config_path.write_text(
        json.dumps(
            {
                "owner": "johns-code",
                "project_number": 2,
                "project_title": "PlantSpeak",
                "project_url": "https://github.com/users/johns-code/projects/2",
            }
        ),
        encoding="utf-8",
    )

    config = load_github_project_config(config_path)

    assert config.owner == "johns-code"
    assert config.project_number == 2
    assert config.project_title == "PlantSpeak"
