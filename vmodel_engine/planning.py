from __future__ import annotations

from vmodel_engine.models import ImplementationTask, Requirement, TraceLink


def create_implementation_tasks(software_requirements: list[Requirement]) -> list[ImplementationTask]:
    tasks: list[ImplementationTask] = []
    for index, requirement in enumerate(software_requirements, start=1):
        tasks.append(
            ImplementationTask(
                id=f"TASK-{index:003d}",
                title=f"Implement {requirement.id}",
                description=f"Design, implement, and verify capability for {requirement.statement}",
                requirement_ids=[requirement.id],
                suggested_owner_role="development_agent",
            )
        )
    return tasks


def create_traceability_matrix(
    software_requirements: list[Requirement],
    system_requirements: list[Requirement],
    tasks: list[ImplementationTask],
) -> list[TraceLink]:
    system_by_id = {requirement.id: requirement for requirement in system_requirements}
    task_by_requirement = {
        requirement_id: task.id
        for task in tasks
        for requirement_id in task.requirement_ids
    }
    links: list[TraceLink] = []
    for requirement in software_requirements:
        system_requirement = system_by_id[requirement.parent_id]
        links.append(
            TraceLink(
                requirement_id=requirement.id,
                user_need_id=system_requirement.parent_id,
                design_refs=[f"DES-{requirement.id.removeprefix('SW-')}"],
                task_refs=[task_by_requirement[requirement.id]],
                test_refs=[
                    f"UT-{requirement.id.removeprefix('SW-')}",
                    f"ST-{requirement.id.removeprefix('SW-')}",
                    f"AT-{requirement.id.removeprefix('SW-')}",
                ],
                verification_refs=[f"VER-{requirement.id.removeprefix('SW-')}"],
                status="planned",
            )
        )
    return links
