from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONFIG_PATH = Path("config/github.json")


@dataclass(frozen=True)
class GitHubProjectConfig:
    owner: str
    project_number: int
    project_title: str
    project_url: str
    default_project_type: str = "python-cli"


@dataclass(frozen=True)
class GitHubProjectStatus:
    configured: GitHubProjectConfig
    reachable: bool
    title: str = ""
    project_id: str = ""
    item_count: int = 0
    field_count: int = 0
    error: str = ""


def load_github_project_config(path: Path = DEFAULT_CONFIG_PATH) -> GitHubProjectConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return GitHubProjectConfig(
        owner=data["owner"],
        project_number=int(data["project_number"]),
        project_title=data["project_title"],
        project_url=data["project_url"],
        default_project_type=data.get("default_project_type", "python-cli"),
    )


def inspect_github_project(config: GitHubProjectConfig) -> GitHubProjectStatus:
    command = [
        "gh",
        "project",
        "view",
        str(config.project_number),
        "--owner",
        config.owner,
        "--format",
        "json",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return GitHubProjectStatus(
            configured=config,
            reachable=False,
            error=(completed.stdout + completed.stderr).strip(),
        )

    data = json.loads(completed.stdout)
    return GitHubProjectStatus(
        configured=config,
        reachable=True,
        title=data.get("title", ""),
        project_id=data.get("id", ""),
        item_count=data.get("items", {}).get("totalCount", 0),
        field_count=data.get("fields", {}).get("totalCount", 0),
    )


def render_github_project_status(status: GitHubProjectStatus) -> str:
    if not status.reachable:
        return f"GitHub Project unreachable: {status.error}"
    return "\n".join(
        [
            f"GitHub Project: {status.title}",
            f"Owner: {status.configured.owner}",
            f"Number: {status.configured.project_number}",
            f"URL: {status.configured.project_url}",
            f"Project ID: {status.project_id}",
            f"Items: {status.item_count}",
            f"Fields: {status.field_count}",
        ]
    )
