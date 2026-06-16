# V-Model Dashboard

The dashboard is a local web control surface for a workflow run directory.

## Start

```powershell
vmodel-engine dashboard runs\plantspeak-dashboard --port 8766
```

Open:

```text
http://127.0.0.1:8766
```

## Shows

- V-model lifecycle progress
- Artifact links
- Local work items or delivered GitHub issues
- Pull request link when delivery evidence exists
- Test and security gate status
- Agent review counts
- Software Lead arbitration records
- Quality policy status
- Clarification questions and user answers

## Clarification Queue

The Software Lead Agent or another orchestrator role can post questions through the dashboard API:

```http
POST /api/questions
```

Users can answer pending questions in the dashboard. Answers are stored in:

```text
orchestrator-questions.json
```

inside the run directory.
