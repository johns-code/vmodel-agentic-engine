from __future__ import annotations

import argparse
from pathlib import Path

from vmodel_engine.autopilot import progress_delivered_run
from vmodel_engine.clarifications import generate_lead_clarifications
from vmodel_engine.dashboard import serve_dashboard
from vmodel_engine.delivery import deliver_project
from vmodel_engine.engine import build_project
from vmodel_engine.github import inspect_github_project, load_github_project_config, render_github_project_status
from vmodel_engine.pipeline import generate_initial_artifacts
from vmodel_engine.questions import answer_question, load_questions, pending_required_questions
from vmodel_engine.tooling import inspect_tools, render_tool_statuses


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vmodel-engine", description="Generate V-model development artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Generate initial V&V artifacts from a requirements brief.")
    init.add_argument("requirements_file", type=Path, help="Path to a requirements file or directory.")
    init.add_argument("--output", "-o", type=Path, default=Path("runs/latest"), help="Output directory for artifacts.")
    init.add_argument("--project-name", help="Project name to use in generated artifacts.")

    build = subparsers.add_parser("build", help="Run the local end-to-end V-model workflow.")
    build.add_argument("requirements_file", type=Path, help="Path to a requirements file or directory.")
    build.add_argument("--output", "-o", type=Path, default=Path("runs/build"), help="Output directory for the workflow run.")
    build.add_argument("--project-name", help="Project name to use in generated artifacts.")
    build.add_argument("--project-type", default="python-cli", help="Generated project type. Currently: python-cli.")

    deliver = subparsers.add_parser("deliver", help="Deliver a generated project to GitHub repo/issues/PR.")
    deliver.add_argument("requirements_file", type=Path, help="Path to a requirements file or directory.")
    deliver.add_argument("--repo", required=True, help="Target product repository, for example owner/repository.")
    deliver.add_argument("--output", "-o", type=Path, default=Path("runs/delivery"), help="Output directory for local delivery evidence.")
    deliver.add_argument("--project-name", required=True, help="Product project name.")
    deliver.add_argument("--project-type", default="python-cli", help="Generated project type. Currently: python-cli.")
    deliver.add_argument("--allow-pending-clarifications", action="store_true", help="Proceed even when required lead questions are unanswered.")

    autopilot = subparsers.add_parser("autopilot", help="Advance a delivered run through implementation, review, tests, and PR update.")
    autopilot.add_argument("run_dir", type=Path, help="Delivered run directory containing delivery-result.json.")

    clarify = subparsers.add_parser("clarify", help="Generate Software Lead clarification questions.")
    clarify.add_argument("requirements_file", type=Path, help="Path to a requirements file or directory.")
    clarify.add_argument("--output", "-o", type=Path, default=Path("runs/clarify"), help="Run directory for question state.")

    questions = subparsers.add_parser("questions", help="Inspect or answer orchestrator questions.")
    question_subparsers = questions.add_subparsers(dest="questions_command", required=True)
    question_list = question_subparsers.add_parser("list", help="List questions for a run.")
    question_list.add_argument("run_dir", type=Path)
    question_answer = question_subparsers.add_parser("answer", help="Answer a question for a run.")
    question_answer.add_argument("run_dir", type=Path)
    question_answer.add_argument("question_id")
    question_answer.add_argument("answer")

    subparsers.add_parser("ready", help="Print supported project intake capabilities.")
    subparsers.add_parser("doctor", help="Inspect available open-source developer tools.")
    github = subparsers.add_parser("github", help="Inspect configured GitHub integration.")
    github_subparsers = github.add_subparsers(dest="github_command", required=True)
    github_subparsers.add_parser("status", help="Check the configured GitHub Project.")

    dashboard = subparsers.add_parser("dashboard", help="Serve a local V-model progress dashboard.")
    dashboard.add_argument("run_dir", type=Path, help="Run directory to display.")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8765)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "init":
        written = generate_initial_artifacts(args.requirements_file, args.output, args.project_name)
        print(f"Generated {len(written)} artifacts in {args.output}")
        for path in written:
            print(path)
        return 0
    if args.command == "build":
        run = build_project(args.requirements_file, args.output, args.project_name, args.project_type)
        print(f"Workflow status: {run.status}")
        print(f"Artifacts: {run.artifact_dir}")
        print(f"Generated project: {run.generated_project_dir}")
        print("Gates:")
        for gate in run.gate_results:
            status = "PASS" if gate.passed else "FAIL"
            print(f"  {status} {gate.name}")
        print("Agent quality policy:")
        for policy in run.quality_policy_results:
            status = "PASS" if policy.passed else "FAIL"
            print(f"  {status} {policy.name}")
        print(f"Artifact reviews: {len(run.artifact_reviews)}")
        print(f"Arbitrations: {len(run.arbitration_records)}")
        return 0 if run.status == "ready_for_human_acceptance" else 1
    if args.command == "deliver":
        result = deliver_project(
            args.requirements_file,
            args.output,
            args.repo,
            args.project_name,
            args.project_type,
            require_clarifications=not args.allow_pending_clarifications,
        )
        print(f"Delivery status: {result.workflow_status}")
        print(f"Repository: {result.repository_url}")
        print(f"Project: {result.project_url}")
        print(f"Issues created: {len(result.issues)}")
        if result.pull_request:
            print(f"Pull request: {result.pull_request.url}")
        return 0 if result.workflow_status == "ready_for_human_acceptance" else 1
    if args.command == "autopilot":
        result = progress_delivered_run(args.run_dir)
        print(f"Repository: {result.repository}")
        print(f"Branch: {result.branch}")
        print(f"Pull request: {result.pull_request_url}")
        print(f"Local tests: {'PASS' if result.local_tests_passed else 'FAIL'}")
        print(f"Reports: {len(result.reports)}")
        return 0 if result.local_tests_passed else 1
    if args.command == "clarify":
        generated = generate_lead_clarifications(args.requirements_file, args.output)
        pending = pending_required_questions(args.output)
        print(f"Generated/loaded {len(generated)} Software Lead questions in {args.output}")
        print(f"Pending required questions: {len(pending)}")
        for item in pending:
            print(f"{item.id}: {item.question}")
        return 0 if not pending else 2
    if args.command == "questions" and args.questions_command == "list":
        for item in load_questions(args.run_dir):
            marker = "required" if item.required else "optional"
            print(f"{item.id} [{item.status}, {marker}, {item.phase}, {item.topic}] {item.question}")
            if item.answer:
                print(f"  answer: {item.answer}")
        return 0
    if args.command == "questions" and args.questions_command == "answer":
        item = answer_question(args.run_dir, args.question_id, args.answer)
        print(f"Answered {item.id}")
        return 0
    if args.command == "ready":
        print("Ready to accept the first project.")
        print("Supported project types: python-cli")
        print("Input: plain-text requirements brief")
        print("Output: V-model artifacts, local work items, generated project, gate results, release evidence")
        return 0
    if args.command == "doctor":
        print(render_tool_statuses(inspect_tools()))
        return 0
    if args.command == "github" and args.github_command == "status":
        status = inspect_github_project(load_github_project_config())
        print(render_github_project_status(status))
        return 0 if status.reachable else 1
    if args.command == "dashboard":
        serve_dashboard(args.run_dir, args.host, args.port)
        return 0
    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
