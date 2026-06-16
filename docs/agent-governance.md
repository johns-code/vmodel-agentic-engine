# Agent Governance

The engine is designed as an agentic software team with deterministic quality policy.

## Lead Agent

The Software Lead Agent orchestrates the workflow, resolves disputes, and enforces quality policy before human approval. The lead agent is the arbiter when development speed conflicts with verification rigor.

## Review Policy

Each design artifact must receive at least three independent reviews with different role/lens combinations.

Current design artifacts under review:

- Architecture/design document
- Detailed design notes
- Test strategy

Current review lenses include:

- User value
- Architecture risk
- Threat modeling
- Modularity
- Testability
- Auditability
- Acceptance validity
- Coverage
- Dependency risk

## Arbitration Policy

When development and test agents disagree, the Software Lead Agent records an arbitration decision. The default rule is that deterministic evidence wins over implementation convenience.

## Quality Policy Gates

The workflow blocks acceptance unless:

- Each design artifact has at least three reviews.
- Software lead arbitration has been recorded for dev/test quality tension.
- Every software requirement has trace links to tasks, tests, and verification evidence.
