from __future__ import annotations

import re

from vmodel_engine.models import Requirement, UserNeed


_BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+")


def split_requirement_brief(brief: str) -> list[str]:
    """Extract candidate requirement statements from a high-level brief."""
    lines = [line.strip() for line in brief.splitlines() if line.strip()]
    requirement_lines = [
        line
        for line in lines
        if not line.startswith("#")
        and not line.lower().startswith("reference documents:")
        and not line.lower().startswith("the following source documents")
    ]
    bullet_items = [_BULLET_RE.sub("", line).strip() for line in requirement_lines if _BULLET_RE.match(line)]
    prose_lines = [_BULLET_RE.sub("", line).strip() for line in requirement_lines if not _BULLET_RE.match(line)]
    prose_candidates = []
    for sentence in re.split(r"(?<=[.!?])\s+", " ".join(prose_lines)):
        cleaned = sentence.strip(" .")
        if cleaned and _is_actionable_statement(cleaned):
            prose_candidates.append(cleaned)
    if bullet_items:
        return _dedupe_preserve_order(prose_candidates + bullet_items)

    sentences = re.split(r"(?<=[.!?])\s+", " ".join(requirement_lines))
    candidates = [sentence.strip(" .") for sentence in sentences if sentence.strip(" .")]
    return _dedupe_preserve_order(candidates)


def build_requirements(brief: str) -> tuple[list[UserNeed], list[Requirement], list[Requirement]]:
    candidates = split_requirement_brief(brief)
    if not candidates:
        raise ValueError("requirements brief is empty")

    needs: list[UserNeed] = []
    system_requirements: list[Requirement] = []
    software_requirements: list[Requirement] = []

    for index, statement in enumerate(candidates, start=1):
        need_id = f"UN-{index:03d}"
        sys_id = f"SYS-{index:03d}"
        sw_id = f"SW-{index:03d}"
        normalized = _normalize_statement(statement)

        needs.append(
            UserNeed(
                id=need_id,
                statement=normalized,
                rationale="Captured from the submitted high-level requirements brief.",
            )
        )
        system_requirements.append(
            Requirement(
                id=sys_id,
                parent_id=need_id,
                statement=f"The system shall support: {normalized}",
                priority=_priority_for(normalized),
                acceptance_criteria=[
                    "The capability is represented in structured requirements.",
                    "The capability has trace links to design, task, and test artifacts.",
                ],
            )
        )
        software_requirements.append(
            Requirement(
                id=sw_id,
                parent_id=sys_id,
                statement=f"The software shall implement: {normalized}",
                priority=_priority_for(normalized),
                acceptance_criteria=[
                    "Automated or manual tests can verify the behavior.",
                    "Verification evidence is recorded before release.",
                ],
            )
        )

    return needs, system_requirements, software_requirements


def _normalize_statement(statement: str) -> str:
    cleaned = re.sub(r"\s+", " ", statement).strip()
    return cleaned[:1].lower() + cleaned[1:] if cleaned else cleaned


def _priority_for(statement: str) -> str:
    lowered = statement.lower()
    if any(word in lowered for word in ("must", "required", "secure", "safety", "critical")):
        return "must"
    if any(word in lowered for word in ("should", "important", "prefer")):
        return "should"
    return "could"


def _is_actionable_statement(statement: str) -> bool:
    lowered = statement.lower()
    if any(phrase in lowered for phrase in ("should not", "must not", "not become a requirement")):
        return False
    return any(
        lowered.startswith(prefix)
        for prefix in (
            "build ",
            "use ",
            "develop ",
            "produce ",
            "support ",
            "implement ",
            "test ",
            "verify ",
        )
    ) or any(word in lowered for word in (" must ", " should ", " shall ", " required "))


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output
