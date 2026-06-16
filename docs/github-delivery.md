# GitHub Delivery Workflow

The `deliver` command is the first end-to-end GitHub delivery path.

## Command

```powershell
vmodel-engine deliver examples\plantspeak_requirements.txt --repo johns-code/plantspeak --output runs\plantspeak-delivery --project-name "PlantSpeak"
```

## What It Does

- Runs the governed V-model workflow locally.
- Creates the target product repo if it does not exist.
- Commits lifecycle artifacts to `docs/vmodel/`.
- Commits agent governance evidence to `docs/agent-governance/`.
- Commits release evidence to `docs/release-evidence/`.
- Creates real GitHub Issues for implementation tasks.
- Adds issues to the configured GitHub Project.
- Creates or updates `agent/generated-implementation`.
- Pushes generated code and product CI to the implementation branch.
- Opens or updates an implementation pull request.

## Current PlantSpeak Delivery

- Product repo: `https://github.com/johns-code/plantspeak`
- Project: `https://github.com/users/johns-code/projects/2`
- PR: `https://github.com/johns-code/plantspeak/pull/6`

## Current Limits

This is a deterministic generated implementation path. The next step is replacing the template implementation worker with OpenHands or SWE-agent while keeping the same issue, PR, artifact, CI, and evidence gates.
