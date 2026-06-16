from __future__ import annotations

from pathlib import Path

from vmodel_engine.clarifications import generate_lead_clarifications


PRODUCT_SPECIFIC_TERMS = [
    "PlantSpeak",
    "DA14531",
    "ADS1115",
    "PCA9846",
    "LP5816",
    "MLX90632",
    "HDC2010",
    "MXC4005",
    "P0_5",
    "P0_11",
    "P0_10",
    "P0_6",
    "P0_8",
    "P0_9",
    "photodiode",
    "PPFD",
    "wavelength",
]


def test_reusable_clarification_prompts_do_not_leak_product_terms(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "Build ICD capabilities on DA14531 with I2C, ADS1115 photodiode PPFD, PCA9846, LP5816, and PC smartdevice.",
        encoding="utf-8",
    )

    questions = generate_lead_clarifications(requirements, tmp_path / "run")
    prompt_text = "\n".join(f"{question.question}\n{question.context}" for question in questions)

    leaked_terms = [term for term in PRODUCT_SPECIFIC_TERMS if term in prompt_text]
    assert leaked_terms == []
