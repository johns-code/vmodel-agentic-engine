from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/github.json")


@dataclass(frozen=True)
class GitHubProjectConfig:
    owner: str
    project_number: int
    project_title: str
    project_url: str
    default_product_repo: str = ""
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
        default_product_repo=data.get("default_product_repo", ""),
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


def run_gh(args: list[str], cwd: Path | None = None) -> dict[str, Any] | str:
    completed = subprocess.run(["gh", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError((completed.stdout + completed.stderr).strip())
    output = completed.stdout.strip()
    if ("--json" in args or ("--format" in args and "json" in args)) and output:
        return json.loads(output)
    return output


def repo_exists(repo: str) -> bool:
    completed = subprocess.run(["gh", "repo", "view", repo], capture_output=True, text=True, check=False)
    return completed.returncode == 0


def ensure_repo(repo: str, description: str, public: bool = True) -> str:
    if not repo_exists(repo):
        visibility = "--public" if public else "--private"
        run_gh(["repo", "create", repo, visibility, "--description", description])
    data = run_gh(["repo", "view", repo, "--json", "url"])
    assert isinstance(data, dict)
    return str(data["url"])


def create_issue(repo: str, title: str, body: str, labels: list[str] | None = None) -> dict[str, Any]:
    existing = run_gh(["issue", "list", "--repo", repo, "--state", "open", "--json", "number,title,url,id", "--limit", "100"])
    assert isinstance(existing, list)
    for issue in existing:
        if issue.get("title") == title:
            return issue
    args = ["issue", "create", "--repo", repo, "--title", title, "--body", body]
    for label in labels or []:
        args.extend(["--label", label])
    issue_url = run_gh(args)
    assert isinstance(issue_url, str)
    data = run_gh(["issue", "view", issue_url, "--repo", repo, "--json", "number,title,url,id"])
    assert isinstance(data, dict)
    return data


def add_issue_to_project(owner: str, project_number: int, issue_url: str) -> dict[str, Any]:
    data = run_gh(["project", "item-add", str(project_number), "--owner", owner, "--url", issue_url, "--format", "json"])
    assert isinstance(data, dict)
    return data
