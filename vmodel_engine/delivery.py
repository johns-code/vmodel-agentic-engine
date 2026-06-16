from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

from vmodel_engine.clarifications import ensure_clarifications_answered
from vmodel_engine.engine import build_project
from vmodel_engine.github import add_issue_to_project, create_issue, ensure_repo, load_github_project_config
from vmodel_engine.intake import copy_source_requirements
from vmodel_engine.models import DeliveryIssue, DeliveryPullRequest, DeliveryResult
from vmodel_engine.questions import questions_path


def deliver_project(
    requirements_path: Path,
    output_dir: Path,
    repo: str,
    project_name: str,
    project_type: str = "python-cli",
    require_clarifications: bool = True,
) -> DeliveryResult:
    if require_clarifications:
        pending = ensure_clarifications_answered(requirements_path, output_dir)
        if pending:
            questions = "\n".join(f"- {item.id}: {item.question}" for item in pending)
            raise RuntimeError(
                "delivery blocked pending required Software Lead clarifications:\n"
                f"{questions}\n"
                "Answer them in the dashboard or with the question-answer command, then rerun delivery."
            )
    run = build_project(requirements_path, output_dir, project_name, project_type)
    config = load_github_project_config()
    repo_url = ensure_repo(repo, f"{project_name} generated and governed by vmodel-agentic-engine", public=True)
    checkout_dir = output_dir / "delivery-checkout"
    _fresh_clone(repo_url, checkout_dir)
    _ensure_git_identity(checkout_dir)

    _copy_tree(output_dir / "artifacts", checkout_dir / "docs" / "vmodel")
    _copy_tree(output_dir / "agent-governance", checkout_dir / "docs" / "agent-governance")
    copy_source_requirements(requirements_path, checkout_dir / "docs" / "source-requirements")
    if questions_path(output_dir).exists():
        _copy_file(questions_path(output_dir), checkout_dir / "docs" / "agent-governance" / "orchestrator-questions.json")
    _copy_file(output_dir / "workflow-run.json", checkout_dir / "docs" / "vmodel" / "workflow-run.json")
    _copy_file(output_dir / "gate-results.json", checkout_dir / "docs" / "vmodel" / "gate-results.json")
    _copy_tree(output_dir / "release-evidence", checkout_dir / "docs" / "release-evidence")
    _remove_product_ci(checkout_dir)
    _commit_all(checkout_dir, "Add V-model lifecycle artifacts")
    _push(checkout_dir, "main")

    issues = _create_delivery_issues(repo, config.owner, config.project_number, output_dir)
    branch = "agent/generated-implementation"
    _checkout_branch(checkout_dir, branch)
    _write_product_ci(checkout_dir)
    _copy_generated_project(output_dir / "generated-project", checkout_dir)
    _commit_all(checkout_dir, "Add generated PlantSpeak implementation")
    _push(checkout_dir, branch)
    pull_request = _create_or_view_pr(repo, branch, project_name, issues)

    result = DeliveryResult(
        repository=repo,
        repository_url=repo_url,
        project_url=config.project_url,
        branch=branch,
        artifacts_committed=True,
        issues=issues,
        pull_request=pull_request,
        workflow_status=run.status,
        local_run_dir=str(output_dir),
    )
    (output_dir / "delivery-result.json").write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    return result


def _fresh_clone(repo_url: str, checkout_dir: Path) -> None:
    if checkout_dir.exists():
        shutil.rmtree(checkout_dir, onexc=_make_writable)
    checkout_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", repo_url, str(checkout_dir)], check=True, capture_output=True, text=True)
    if not (checkout_dir / ".git").exists():
        subprocess.run(["git", "init"], cwd=checkout_dir, check=True, capture_output=True, text=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=checkout_dir, check=True, capture_output=True, text=True)


def _make_writable(function, path, excinfo) -> None:
    os.chmod(path, stat.S_IWRITE)
    function(path)


def _ensure_git_identity(cwd: Path) -> None:
    subprocess.run(["git", "config", "user.name", "johns-code"], cwd=cwd, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "81149847+johns-code@users.noreply.github.com"],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"))


def _copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _copy_generated_project(source: Path, target: Path) -> None:
    for item in source.iterdir():
        destination = target / item.name
        if item.name == ".git":
            continue
        if item.is_dir():
            _copy_tree(item, destination)
        else:
            _copy_file(item, destination)


def _write_product_ci(repo_dir: Path) -> None:
    workflow = repo_dir / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        """name: CI

on:
  push:
    branches: ["main", "agent/**"]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install package
        run: python -m pip install -e .[dev]
      - name: Run tests
        run: python -m pytest
""",
        encoding="utf-8",
    )


def _remove_product_ci(repo_dir: Path) -> None:
    workflow = repo_dir / ".github" / "workflows" / "ci.yml"
    if workflow.exists():
        workflow.unlink()


def _commit_all(cwd: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=cwd, check=True, capture_output=True, text=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=cwd, check=False)
    if diff.returncode == 0:
        return
    subprocess.run(["git", "commit", "-m", message], cwd=cwd, check=True, capture_output=True, text=True)


def _push(cwd: Path, branch: str) -> None:
    command = ["git", "push", "-u", "origin", branch]
    if branch != "main":
        command.append("--force-with-lease")
    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)


def _checkout_branch(cwd: Path, branch: str) -> None:
    subprocess.run(["git", "checkout", "-B", branch], cwd=cwd, check=True, capture_output=True, text=True)


def _create_delivery_issues(repo: str, owner: str, project_number: int, output_dir: Path) -> list[DeliveryIssue]:
    issue_files = sorted((output_dir / "work-items").glob("LOCAL-*.json"))
    issues: list[DeliveryIssue] = []
    for issue_file in issue_files:
        item = json.loads(issue_file.read_text(encoding="utf-8"))
        body = (
            f"Source task: {item['source_task_id']}\n"
            f"Requirements: {', '.join(item['requirement_ids'])}\n\n"
            f"{item['description']}\n\n"
            "V-model artifacts are committed under `docs/vmodel/`."
        )
        title = _issue_title(item)
        issue = create_issue(repo, title, body)
        add_issue_to_project(owner, project_number, issue["url"])
        issues.append(
            DeliveryIssue(
                id=str(issue["id"]),
                number=int(issue["number"]),
                title=str(issue["title"]),
                url=str(issue["url"]),
                requirement_ids=list(item["requirement_ids"]),
            )
        )
    return issues


def _issue_title(item: dict[str, object]) -> str:
    requirement_id = str(item["requirement_ids"][0])
    description = str(item["description"])
    capability = description.split("The software shall implement:", 1)[-1].strip()
    capability = capability.rstrip(".")
    if len(capability) > 90:
        capability = capability[:87].rstrip() + "..."
    return f"{requirement_id}: {capability}"


def _create_or_view_pr(repo: str, branch: str, project_name: str, issues: list[DeliveryIssue]) -> DeliveryPullRequest:
    issue_refs = "\n".join(f"- Closes #{issue.number}: {issue.title}" for issue in issues)
    body = f"""Generated implementation for {project_name}.

## Linked Issues

{issue_refs}

## V-Model Evidence

- Lifecycle artifacts: `docs/vmodel/`
- Agent governance: `docs/agent-governance/`
- Release evidence: `docs/release-evidence/`
"""
    completed = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--base",
            "main",
            "--head",
            branch,
            "--title",
            "Add generated PlantSpeak implementation",
            "--body",
            body,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 and "already exists" not in completed.stderr:
        raise RuntimeError((completed.stdout + completed.stderr).strip())
    if completed.returncode != 0:
        data = subprocess.run(
            ["gh", "pr", "view", branch, "--repo", repo, "--json", "number,title,url,state"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    else:
        pr_url = completed.stdout.strip()
        data = subprocess.run(
            ["gh", "pr", "view", pr_url, "--repo", repo, "--json", "number,title,url,state"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    pr = json.loads(data)
    return DeliveryPullRequest(
        number=int(pr["number"]),
        title=str(pr["title"]),
        url=str(pr["url"]),
        branch=branch,
        status=str(pr["state"]),
    )
