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
    if "da14531" in lowered:
        generated.append(
            create_question(
                run_dir,
                "Which DA14531 build path should be authoritative for CI or manual verification: Keil uVision, command-line UV4 build, or another build script?",
                "The toolchain document lists common options but does not select the project-specific build authority.",
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
                "For unavailable I2C devices, should the firmware use compile-time stubs, runtime dev-mode providers, or a hardware abstraction layer selected at startup?",
                "The implementation architecture depends on how simulated ADS1115, LP5816, MLX90632, HDC2010, and MXC4005 data are injected.",
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
    if "ads1115" in lowered or "photodiode" in lowered or "ppfd" in lowered:
        generated.append(
            create_question(
                run_dir,
                "What measurement cadence, averaging, units, and calibration assumptions should be used for photodiode and PPFD readings in the first release?",
                "The hardware channels are identified, but the measurement behavior is not yet testable.",
                topic="measurement-behavior",
            )
        )
    if "pca9846" in lowered or "lp5816" in lowered:
        generated.append(
            create_question(
                run_dir,
                "What LED sequencing, intensity defaults, timing, and settling delay are required when measuring each wavelength?",
                "External LEDs and mux channels are specified, but measurement sequencing needs acceptance criteria.",
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
            "What is the smallest user-visible behavior that should count as the first successful PlantSpeak release?",
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
