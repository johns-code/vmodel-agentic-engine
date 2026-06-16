from __future__ import annotations

import json
from pathlib import Path

from vmodel_engine.models import ImplementationTask, WorkItem


class LocalIssueTracker:
    """File-backed work item adapter used until GitHub/Jira integrations are configured."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def create_items(self, tasks: list[ImplementationTask]) -> list[WorkItem]:
        issues_dir = self.root / "work-items"
        issues_dir.mkdir(parents=True, exist_ok=True)
        work_items: list[WorkItem] = []
        for index, task in enumerate(tasks, start=1):
            item = WorkItem(
                id=f"LOCAL-{index:003d}",
                title=task.title,
                description=task.description,
                requirement_ids=task.requirement_ids,
                source_task_id=task.id,
                status="open",
            )
            work_items.append(item)
            (issues_dir / f"{item.id}.json").write_text(json.dumps(item.__dict__, indent=2) + "\n", encoding="utf-8")
            (issues_dir / f"{item.id}.md").write_text(_render_item(item), encoding="utf-8")
        (issues_dir / "index.json").write_text(json.dumps([item.__dict__ for item in work_items], indent=2) + "\n", encoding="utf-8")
        return work_items


def _render_item(item: WorkItem) -> str:
    requirements = ", ".join(item.requirement_ids)
    return f"""# {item.id}: {item.title}

Status: {item.status}

Source task: {item.source_task_id}

Requirements: {requirements}

## Description

{item.description}
"""
