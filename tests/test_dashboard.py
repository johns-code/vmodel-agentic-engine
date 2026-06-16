from pathlib import Path

from vmodel_engine.dashboard import collect_dashboard_state
from vmodel_engine.engine import build_project
from vmodel_engine.questions import answer_question, create_question


def test_dashboard_state_includes_vmodel_and_questions(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("- Users must record observations.\n", encoding="utf-8")
    run_dir = tmp_path / "run"
    build_project(requirements, run_dir, "PlantSpeak")
    question = create_question(run_dir, "Which sensor mode should be default?", "Firmware behavior")
    answer_question(run_dir, question.id, "Use dev mode first.")

    state = collect_dashboard_state(run_dir)

    assert state["workflow"]["status"] == "ready_for_human_acceptance"
    assert len(state["vmodel"]) >= 10
    assert state["questions"][0]["status"] == "answered"
