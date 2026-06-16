# MVP Architecture

## Purpose

The engine coordinates a V-model software delivery lifecycle where every artifact is inspectable and every gate can be verified with deterministic evidence.

## Initial Architecture

The MVP is a Python CLI that transforms a requirements brief into lifecycle artifacts. The implementation keeps generation deterministic so tests can assert the artifact contract before LLM agents are introduced.

## Agent Roles

| Role | MVP Responsibility | Future Tooling |
| --- | --- | --- |
| Requirements | Parse the submitted brief into structured needs and requirements. | LLM-backed elicitation with human review. |
| Systems/design | Create architecture and detailed design placeholders. | LangGraph/CrewAI workflow plus ADR generation. |
| Planning | Create requirement-linked tasks. | GitHub Issues or Jira MCP integration. |
| Development | Not implemented in MVP. | OpenHands, SWE-agent, branch and PR automation. |
| Test | Create linked test plans. | pytest, Jest, Playwright generation and execution. |
| Verification | Produce pending verification report. | CI status checks and test result ingestion. |
| Validation | Produce pending validation report. | Acceptance workflow and human approval gate. |
| Review/security | Produce pending review reports. | Semgrep, Trivy, dependency review, code review. |
| Release | Produce initial release notes. | Signed release package and traceability evidence bundle. |

## Quality Gates

Agents may create proposals and implementation changes. Gates should be deterministic:

- Schema validation for generated artifacts.
- Unit and integration tests for generated code.
- Static analysis and dependency scans.
- CI status checks.
- Human approval before final acceptance and release.

## Extension Points

- Replace deterministic requirement extraction with an LLM adapter.
- Add a work item adapter for GitHub Issues or Jira.
- Add SCM automation for branches, commits, and pull requests.
- Add CI evidence ingestion for verification reports.
- Add project templates for Python CLI, FastAPI, Node service, and frontend apps.
