from pathlib import Path

import pytest

from vmodel_engine.clarifications import ensure_clarifications_answered, generate_lead_clarifications
from vmodel_engine.delivery import deliver_project
from vmodel_engine.questions import answer_question, pending_required_questions


def test_generate_lead_clarifications_for_plantspeak_requirements(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements"
    requirements.mkdir()
    (requirements / "User Requirements.txt").write_text(
        "Build ICD capabilities on DA14531. Use dev board. I2C ADS1115 photodiode PPFD. Use PC as the smartdevice.",
        encoding="utf-8",
    )

    questions = generate_lead_clarifications(requirements, tmp_path / "run")

    assert len(questions) >= 8
    assert any(question.topic == "icd-scope" for question in questions)
    assert any(question.topic == "pc-test-transport" for question in questions)
    assert pending_required_questions(tmp_path / "run")


def test_required_clarifications_can_be_answered(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("Build ICD capabilities on DA14531 with I2C.", encoding="utf-8")
    run_dir = tmp_path / "run"
    pending = ensure_clarifications_answered(requirements, run_dir)

    for item in pending:
        answer_question(run_dir, item.id, "Accepted for test.")

    assert ensure_clarifications_answered(requirements, run_dir) == []


def test_delivery_blocks_on_pending_clarifications(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("Build ICD capabilities on DA14531 with I2C.", encoding="utf-8")

    with pytest.raises(RuntimeError, match="delivery blocked pending required"):
        deliver_project(requirements, tmp_path / "run", "johns-code/example", "PlantSpeak")
