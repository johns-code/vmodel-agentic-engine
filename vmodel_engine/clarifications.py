from __future__ import annotations

from pathlib import Path

from vmodel_engine.intake import read_requirements_input
from vmodel_engine.questions import ClarificationQuestion, create_question, pending_required_questions


def generate_lead_clarifications(requirements_path: Path, run_dir: Path) -> list[ClarificationQuestion]:
    text = read_requirements_input(requirements_path)
    lowered = text.lower()
    generated: list[ClarificationQuestion] = []

    generated.extend(_core_product_questions(run_dir))

    if "icd" in lowered:
        generated.append(
            create_question(
                run_dir,
                "Which ICD capabilities or commands are in scope for the first acceptance release?",
                "The requirements say to build ICD capabilities, but the first releasable slice needs an explicit scope boundary.",
                topic="icd-scope",
            )
        )
        generated.append(
            create_question(
                run_dir,
                "Should dev mode expose the same ICD interface as target hardware mode, using canned sensor data where hardware is unavailable?",
                "This affects whether PC-side tests can validate behavior before target hardware is present.",
                topic="dev-mode-icd",
            )
        )
    if any(term in lowered for term in ["firmware", "embedded", "mcu", "microcontroller", "target hardware"]):
        generated.append(
            create_question(
                run_dir,
                "Which target-platform build path should be authoritative for CI or manual verification?",
                "The requirements identify an embedded target, but the project still needs one selected build authority and evidence path.",
                topic="firmware-build",
            )
        )
    if "dev board" in lowered or "00fxdevkt" in lowered:
        generated.append(
            create_question(
                run_dir,
                "What exact evidence should count as passing dev-board testing when target-board peripherals are unavailable?",
                "Several hardware functions are unavailable on the dev board, so verification needs explicit substitute evidence.",
                topic="dev-board-evidence",
            )
        )
    if "i2c" in lowered:
        generated.append(
            create_question(
                run_dir,
                "For unavailable external bus devices, should the implementation use compile-time stubs, runtime dev-mode providers, or a hardware abstraction layer selected at startup?",
                "The implementation architecture depends on how simulated device data is injected when target hardware is unavailable.",
                topic="i2c-abstraction",
            )
        )
        generated.append(
            create_question(
                run_dir,
                "What should the system do when an I2C device is missing, unresponsive, or returns invalid data?",
                "Error handling behavior is required for both verification and target-board readiness.",
                topic="i2c-errors",
            )
        )
    if any(term in lowered for term in ["sensor", "measurement", "measure", "calibration", "reading"]):
        generated.append(
            create_question(
                run_dir,
                "What measurement cadence, averaging, units, and calibration assumptions should be used for the first release?",
                "The measurement sources are identified, but the expected measurement behavior is not yet testable.",
                topic="measurement-behavior",
            )
        )
    if "led" in lowered or "actuator" in lowered:
        generated.append(
            create_question(
                run_dir,
                "What actuator sequencing, intensity defaults, timing, and settling delay are required during measurement?",
                "External actuators and switching channels are specified, but measurement sequencing needs acceptance criteria.",
                topic="led-measurement-sequence",
            )
        )
    if "pc as the smart" in lowered or "smartdevice" in lowered:
        generated.append(
            create_question(
                run_dir,
                "Should the PC smart-device test interface use BLE, UART, a mocked transport, or more than one transport for the first release?",
                "The transport choice determines test harness design and which ICD paths can be verified on a laptop.",
                topic="pc-test-transport",
            )
        )

    return generated


def ensure_clarifications_answered(requirements_path: Path, run_dir: Path) -> list[ClarificationQuestion]:
    generate_lead_clarifications(requirements_path, run_dir)
    return pending_required_questions(run_dir)


def _core_product_questions(run_dir: Path) -> list[ClarificationQuestion]:
    return [
        create_question(
            run_dir,
            "What is the smallest user-visible behavior that should count as the first successful release?",
            "The Software Lead needs a release objective before allowing implementation to proceed.",
            topic="release-objective",
        ),
        create_question(
            run_dir,
            "Which acceptance tests must a human be able to run on this laptop before approving the first release?",
            "Human validation criteria must be known before release notes and validation reports can be closed.",
            topic="acceptance-tests",
        ),
    ]
