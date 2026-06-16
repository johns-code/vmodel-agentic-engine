from __future__ import annotations

import argparse
from pathlib import Path

from vmodel_engine.engine import build_project
from vmodel_engine.github import inspect_github_project, load_github_project_config, render_github_project_status
from vmodel_engine.pipeline import generate_initial_artifacts
from vmodel_engine.tooling import inspect_tools, render_tool_statuses


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vmodel-engine", description="Generate V-model development artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Generate initial V&V artifacts from a requirements brief.")
    init.add_argument("requirements_file", type=Path, help="Path to a plain-text requirements brief.")
    init.add_argument("--output", "-o", type=Path, default=Path("runs/latest"), help="Output directory for artifacts.")
    init.add_argument("--project-name", help="Project name to use in generated artifacts.")

    build = subparsers.add_parser("build", help="Run the local end-to-end V-model workflow.")
    build.add_argument("requirements_file", type=Path, help="Path to a plain-text requirements brief.")
    build.add_argument("--output", "-o", type=Path, default=Path("runs/build"), help="Output directory for the workflow run.")
    build.add_argument("--project-name", help="Project name to use in generated artifacts.")
    build.add_argument("--project-type", default="python-cli", help="Generated project type. Currently: python-cli.")

    subparsers.add_parser("ready", help="Print supported project intake capabilities.")
    subparsers.add_parser("doctor", help="Inspect available open-source developer tools.")
    github = subparsers.add_parser("github", help="Inspect configured GitHub integration.")
    github_subparsers = github.add_subparsers(dest="github_command", required=True)
    github_subparsers.add_parser("status", help="Check the configured GitHub Project.")
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
    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
