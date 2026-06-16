from vmodel_engine.requirements import build_requirements, split_requirement_brief


def test_split_requirement_brief_prefers_bullets() -> None:
    brief = """
    Intro text that should not become a requirement.
    - Users must submit requirements.
    - Users must submit requirements.
    - The system should produce artifacts.
    """

    assert split_requirement_brief(brief) == [
        "Users must submit requirements.",
        "The system should produce artifacts.",
    ]


def test_build_requirements_creates_v_model_layers() -> None:
    needs, system_requirements, software_requirements = build_requirements("- Users must submit requirements.")

    assert needs[0].id == "UN-001"
    assert system_requirements[0].id == "SYS-001"
    assert system_requirements[0].parent_id == "UN-001"
    assert software_requirements[0].id == "SW-001"
    assert software_requirements[0].parent_id == "SYS-001"
    assert software_requirements[0].priority == "must"
