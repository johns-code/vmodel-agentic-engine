from collections import Counter

from vmodel_engine.agents import DESIGN_ARTIFACTS, arbitrate_agent_disputes, evaluate_quality_policy, perform_artifact_reviews
from vmodel_engine.engine import create_artifact_package


def test_design_artifacts_receive_three_reviews(tmp_path) -> None:
    requirements_file = tmp_path / "brief.txt"
    requirements_file.write_text("- Users must record plant observations.\n", encoding="utf-8")
    package = create_artifact_package(requirements_file, "PlantSpeak")

    reviews = perform_artifact_reviews(package)

    counts = Counter(review.artifact_id for review in reviews)
    for artifact_id, _ in DESIGN_ARTIFACTS:
        assert counts[artifact_id] >= 3
    assert len({(review.reviewer_role, review.lens) for review in reviews}) == len(reviews)


def test_quality_policy_requires_reviews_arbitration_and_traceability(tmp_path) -> None:
    requirements_file = tmp_path / "brief.txt"
    requirements_file.write_text("- Users must record plant observations.\n", encoding="utf-8")
    package = create_artifact_package(requirements_file, "PlantSpeak")
    reviews = perform_artifact_reviews(package)
    arbitrations = arbitrate_agent_disputes(reviews)

    results = evaluate_quality_policy(package, reviews, arbitrations)

    assert all(result.passed for result in results)
    assert any(result.name == "design-artifacts-have-three-reviews" for result in results)
    assert arbitrations[0].raised_by == "test_verification"
