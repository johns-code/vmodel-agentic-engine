from __future__ import annotations

import json
from pathlib import Path


def answer_lead_question(run_dir: Path, question: str) -> str:
    lowered = question.lower()
    if "architecture" in lowered and ("review" in lowered or "comments" in lowered):
        return _architecture_review_summary(run_dir)
    return (
        "Software Lead response: I recorded the question, but I do not yet have an automatic answer path for this topic. "
        "I will treat it as a follow-up item for the orchestrator."
    )


def _architecture_review_summary(run_dir: Path) -> str:
    reviews_path = run_dir / "agent-governance" / "artifact-reviews.json"
    if not reviews_path.exists():
        return "Software Lead response: architecture review comments are not available yet because artifact reviews have not been generated for this run."

    reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
    architecture_reviews = [review for review in reviews if review.get("artifact_id") == "04-architecture-design"]
    if not architecture_reviews:
        return "Software Lead response: no architecture review comments were found for this run."

    lines = ["Software Lead response: Architecture/design review comments:"]
    for review in architecture_reviews:
        lines.append(
            f"- {review['reviewer_role']} ({review['lens']}): {review['verdict']}. "
            f"Findings: {'; '.join(review['findings'])} "
            f"Required actions: {'; '.join(review['required_actions'])}"
        )
    return "\n".join(lines)
