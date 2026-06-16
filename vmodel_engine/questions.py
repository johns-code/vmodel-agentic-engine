from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from vmodel_engine.models import utc_now_iso


@dataclass(frozen=True)
class ClarificationQuestion:
    id: str
    question: str
    context: str
    asked_by: str
    status: str
    created_at: str
    required: bool = True
    phase: str = "preflight"
    topic: str = "general"
    answered_at: str | None = None
    answer: str | None = None


def questions_path(run_dir: Path) -> Path:
    return run_dir / "orchestrator-questions.json"


def load_questions(run_dir: Path) -> list[ClarificationQuestion]:
    path = questions_path(run_dir)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [ClarificationQuestion(**item) for item in data]


def create_question(
    run_dir: Path,
    question: str,
    context: str = "",
    asked_by: str = "software_lead",
    required: bool = True,
    phase: str = "preflight",
    topic: str = "general",
) -> ClarificationQuestion:
    questions = load_questions(run_dir)
    for item in questions:
        if item.question == question and item.phase == phase:
            return item
    next_id = f"Q-{len(questions) + 1:003d}"
    item = ClarificationQuestion(
        id=next_id,
        question=question,
        context=context,
        asked_by=asked_by,
        status="pending",
        created_at=utc_now_iso(),
        required=required,
        phase=phase,
        topic=topic,
    )
    _write_questions(run_dir, [*questions, item])
    return item


def answer_question(run_dir: Path, question_id: str, answer: str) -> ClarificationQuestion:
    answer = answer.strip()
    if not answer:
        raise ValueError("answer cannot be empty")
    questions = load_questions(run_dir)
    updated: list[ClarificationQuestion] = []
    answered: ClarificationQuestion | None = None
    for item in questions:
        if item.id == question_id:
            answered = ClarificationQuestion(
                id=item.id,
                question=item.question,
                context=item.context,
                asked_by=item.asked_by,
                status="answered",
                created_at=item.created_at,
                required=item.required,
                phase=item.phase,
                topic=item.topic,
                answered_at=utc_now_iso(),
                answer=answer,
            )
            updated.append(answered)
        else:
            updated.append(item)
    if answered is None:
        raise KeyError(question_id)
    _write_questions(run_dir, updated)
    return answered


def pending_required_questions(run_dir: Path) -> list[ClarificationQuestion]:
    return [item for item in load_questions(run_dir) if item.required and item.status != "answered"]


def _write_questions(run_dir: Path, questions: list[ClarificationQuestion]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    questions_path(run_dir).write_text(json.dumps([asdict(item) for item in questions], indent=2) + "\n", encoding="utf-8")
