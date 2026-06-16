# Tool Integration Strategy

The engine uses open-source developer tools as execution backends and keeps deterministic evidence in generated artifacts.

## Current Local Profile

| Capability | Current Tooling |
| --- | --- |
| Requirements and artifact generation | Built-in deterministic Python pipeline |
| Work item source of truth | File-backed local issue adapter |
| Generated implementation | Python CLI project template |
| Unit verification | pytest |
| Security gate | Built-in smoke scan, with Semgrep/Trivy planned as external scanners |
| Release evidence | JSON and Markdown manifest files |

## Adapter Direction

| Adapter | First External Backend |
| --- | --- |
| Work items | GitHub Issues |
| Source control | Git branches and GitHub pull requests |
| Coding worker | OpenHands or SWE-agent |
| Workflow orchestration | LangGraph |
| Static analysis | Semgrep |
| Dependency and container scanning | Trivy |
| Observability | OpenTelemetry, optionally Langfuse |

Run `vmodel-engine doctor` to see which tools are available in the local environment.
