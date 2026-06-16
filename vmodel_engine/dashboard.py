from __future__ import annotations

import json
import mimetypes
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from vmodel_engine.questions import answer_question, create_question, load_questions


VMODEL_STAGES = [
    ("User Needs", "left", "artifacts/01-user-needs.md"),
    ("System Requirements", "left", "artifacts/02-system-requirements.md"),
    ("Software Requirements", "left", "artifacts/03-software-requirements.md"),
    ("Architecture", "left", "artifacts/04-architecture-design.md"),
    ("Detailed Design", "left", "artifacts/05-detailed-design-notes.md"),
    ("Implementation Plan", "left", "artifacts/06-implementation-task-plan.md"),
    ("Code Implementation", "bottom", "generated-project"),
    ("Unit Verification", "right", "artifacts/08-unit-test-plan.md"),
    ("Integration Verification", "right", "artifacts/09-integration-test-plan.md"),
    ("System Verification", "right", "artifacts/10-system-test-plan.md"),
    ("Acceptance Validation", "right", "artifacts/11-acceptance-test-plan.md"),
]


def collect_dashboard_state(run_dir: Path) -> dict[str, object]:
    workflow = _read_json(run_dir / "workflow-run.json", {})
    delivery = _read_json(run_dir / "delivery-result.json", {})
    gates = _read_json(run_dir / "gate-results.json", [])
    governance = _read_json(run_dir / "agent-governance" / "quality-policy-results.json", [])
    reviews = _read_json(run_dir / "agent-governance" / "artifact-reviews.json", [])
    arbitrations = _read_json(run_dir / "agent-governance" / "arbitration-records.json", [])
    work_items = _read_json(run_dir / "work-items" / "index.json", [])
    artifacts = _list_files(run_dir / "artifacts", [".md", ".json"])
    source_docs = _list_files(run_dir / "docs" / "source-requirements", [".txt", ".md", ".docx", ".pdf"])
    if not source_docs:
        source_docs = _list_files(run_dir / "delivery-checkout" / "docs" / "source-requirements", [".txt", ".md", ".docx", ".pdf"])
    questions = [asdict(item) for item in load_questions(run_dir)]
    return {
        "run_dir": str(run_dir),
        "workflow": workflow,
        "delivery": delivery,
        "gates": gates,
        "quality_policies": governance,
        "reviews": reviews,
        "arbitrations": arbitrations,
        "work_items": work_items,
        "artifacts": artifacts,
        "source_docs": source_docs,
        "questions": questions,
        "vmodel": _vmodel_status(run_dir),
    }


def serve_dashboard(run_dir: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    run_dir = run_dir.resolve()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_text(_INDEX_HTML, "text/html")
                return
            if parsed.path == "/api/state":
                self._send_json(collect_dashboard_state(run_dir))
                return
            if parsed.path.startswith("/files/"):
                relative = unquote(parsed.path.removeprefix("/files/"))
                self._send_file(run_dir, relative)
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            payload = self._read_json_body()
            if parsed.path == "/api/questions":
                item = create_question(
                    run_dir,
                    str(payload.get("question", "")).strip(),
                    str(payload.get("context", "")).strip(),
                    str(payload.get("asked_by", "software_lead")).strip() or "software_lead",
                )
                self._send_json(asdict(item), status=HTTPStatus.CREATED)
                return
            if parsed.path.startswith("/api/questions/") and parsed.path.endswith("/answer"):
                question_id = parsed.path.split("/")[3]
                item = answer_question(run_dir, question_id, str(payload.get("answer", "")).strip())
                self._send_json(asdict(item))
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json_body(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def _send_json(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
            content = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def _send_text(self, text: str, content_type: str) -> None:
            content = text.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def _send_file(self, root: Path, relative: str) -> None:
            path = (root / relative).resolve()
            if not path.is_file() or root not in path.parents:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content = path.read_bytes()
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Dashboard serving {run_dir} at http://{host}:{port}")
    server.serve_forever()


def _read_json(path: Path, fallback: object) -> object:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _list_files(root: Path, suffixes: list[str]) -> list[dict[str, object]]:
    if not root.exists():
        return []
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in suffixes:
            relative = path.relative_to(root.parent)
            files.append({"name": path.name, "path": str(relative).replace("\\", "/"), "size": path.stat().st_size})
    return files


def _vmodel_status(run_dir: Path) -> list[dict[str, str]]:
    stages = []
    for title, side, relative in VMODEL_STAGES:
        exists = (run_dir / relative).exists()
        stages.append({"title": title, "side": side, "status": "complete" if exists else "pending", "path": relative})
    return stages


_INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>V-Model Dashboard</title>
  <style>
    :root { color-scheme: light; --ink: #172026; --muted: #60717c; --line: #d6dee3; --ok: #177245; --warn: #9b5b00; --bad: #b42318; --bg: #f6f8fa; --panel: #ffffff; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Arial, Helvetica, sans-serif; background: var(--bg); color: var(--ink); }
    header { padding: 18px 24px; background: #11212b; color: white; display: flex; justify-content: space-between; gap: 18px; align-items: center; }
    header h1 { margin: 0; font-size: 22px; letter-spacing: 0; }
    header p { margin: 4px 0 0; color: #cbd7de; font-size: 13px; }
    main { padding: 20px 24px 32px; display: grid; gap: 16px; }
    section { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 16px; }
    h2 { margin: 0 0 12px; font-size: 16px; }
    h3 { margin: 14px 0 8px; font-size: 14px; }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
    .wide { grid-column: 1 / -1; }
    .metric { display: grid; gap: 4px; padding: 12px; border: 1px solid var(--line); border-radius: 6px; }
    .metric b { font-size: 20px; }
    .muted { color: var(--muted); font-size: 13px; }
    .vmodel { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
    .stage { border: 1px solid var(--line); border-left: 5px solid var(--muted); border-radius: 6px; padding: 10px; min-height: 62px; }
    .stage.complete { border-left-color: var(--ok); }
    .stage.pending { border-left-color: var(--warn); }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; padding: 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
    th { color: var(--muted); font-weight: 700; }
    a { color: #0b5cad; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .status { font-weight: 700; }
    .pass { color: var(--ok); }
    .fail { color: var(--bad); }
    form { display: grid; gap: 8px; }
    input, textarea { width: 100%; border: 1px solid var(--line); border-radius: 5px; padding: 9px; font: inherit; }
    button { border: 0; border-radius: 5px; padding: 9px 12px; background: #174ea6; color: white; font-weight: 700; cursor: pointer; }
    button:hover { background: #0f3b7d; }
    @media (max-width: 900px) { .grid, .vmodel { grid-template-columns: 1fr; } header { display: block; } }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>V-Model Delivery Dashboard</h1>
      <p id="run-dir"></p>
    </div>
    <div id="top-status"></div>
  </header>
  <main>
    <section class="wide">
      <h2>Lifecycle Path</h2>
      <div class="vmodel" id="vmodel"></div>
    </section>
    <div class="grid">
      <section>
        <h2>Delivery</h2>
        <div id="delivery"></div>
      </section>
      <section>
        <h2>Gates</h2>
        <div id="gates"></div>
      </section>
      <section>
        <h2>Agent Governance</h2>
        <div id="governance"></div>
      </section>
    </div>
    <section class="wide">
      <h2>Artifacts</h2>
      <table><thead><tr><th>Name</th><th>Path</th><th>Size</th></tr></thead><tbody id="artifacts"></tbody></table>
    </section>
    <section class="wide">
      <h2>Issues and Work Items</h2>
      <table><thead><tr><th>ID</th><th>Title</th><th>Requirements</th><th>Status / URL</th></tr></thead><tbody id="issues"></tbody></table>
    </section>
    <section class="wide">
      <h2>Clarifications</h2>
      <div class="grid">
        <div>
          <h3>Ask The User</h3>
          <form id="ask-form">
            <input name="asked_by" value="software_lead" aria-label="Asked by">
            <textarea name="question" rows="3" placeholder="Question for the user"></textarea>
            <textarea name="context" rows="2" placeholder="Context"></textarea>
            <button type="submit">Add Question</button>
          </form>
        </div>
        <div class="wide">
          <h3>Question Queue</h3>
          <div id="questions"></div>
        </div>
      </div>
    </section>
  </main>
  <script>
    async function loadState() {
      const res = await fetch('/api/state');
      const state = await res.json();
      render(state);
    }
    function text(value, fallback='') { return value === undefined || value === null || value === '' ? fallback : value; }
    function render(state) {
      document.getElementById('run-dir').textContent = state.run_dir;
      const workflowStatus = text(state.workflow.status, 'unknown');
      document.getElementById('top-status').innerHTML = `<b>${workflowStatus}</b>`;
      document.getElementById('vmodel').innerHTML = state.vmodel.map(s => `<div class="stage ${s.status}"><b>${s.title}</b><div class="muted">${s.side} · ${s.status}</div></div>`).join('');
      const pr = state.delivery.pull_request;
      document.getElementById('delivery').innerHTML = `
        <div class="metric"><span class="muted">Repository</span><b>${link(state.delivery.repository_url)}</b></div>
        <div class="metric"><span class="muted">Project</span><b>${link(state.delivery.project_url)}</b></div>
        <div class="metric"><span class="muted">Pull Request</span><b>${pr ? link(pr.url, '#' + pr.number) : 'Not created'}</b></div>`;
      document.getElementById('gates').innerHTML = rows(state.gates, g => `<tr><td>${g.name}</td><td class="${g.passed ? 'pass' : 'fail'}">${g.passed ? 'PASS' : 'FAIL'}</td><td>${(g.output || '').slice(0, 180)}</td></tr>`);
      document.getElementById('governance').innerHTML = `
        <div class="metric"><span class="muted">Reviews</span><b>${state.reviews.length}</b></div>
        <div class="metric"><span class="muted">Arbitrations</span><b>${state.arbitrations.length}</b></div>
        ${rows(state.quality_policies, p => `<tr><td>${p.name}</td><td class="${p.passed ? 'pass' : 'fail'}">${p.passed ? 'PASS' : 'FAIL'}</td><td>${p.details}</td></tr>`)}`;
      document.getElementById('artifacts').innerHTML = state.artifacts.map(a => `<tr><td>${a.name}</td><td><a href="/files/${a.path}" target="_blank">${a.path}</a></td><td>${a.size}</td></tr>`).join('');
      const deliveryIssues = state.delivery.issues || [];
      const localItems = state.work_items || [];
      document.getElementById('issues').innerHTML = deliveryIssues.length
        ? deliveryIssues.map(i => `<tr><td>#${i.number}</td><td>${i.title}</td><td>${(i.requirement_ids || []).join(', ')}</td><td>${link(i.url)}</td></tr>`).join('')
        : localItems.map(i => `<tr><td>${i.id}</td><td>${i.title}</td><td>${(i.requirement_ids || []).join(', ')}</td><td>${i.status}</td></tr>`).join('');
      renderQuestions(state.questions || []);
    }
    function rows(items, renderRow) { return `<table><tbody>${items.map(renderRow).join('')}</tbody></table>`; }
    function link(url, label) { return url ? `<a href="${url}" target="_blank">${label || url}</a>` : ''; }
    function renderQuestions(questions) {
      document.getElementById('questions').innerHTML = questions.length ? questions.map(q => `
        <section>
          <b>${q.id}: ${q.question}</b>
          <p class="muted">${q.asked_by} · ${q.status} · ${q.context || ''}</p>
          ${q.answer ? `<p>${q.answer}</p>` : `<form onsubmit="answerQuestion(event, '${q.id}')"><textarea name="answer" rows="2" placeholder="Your answer"></textarea><button type="submit">Answer</button></form>`}
        </section>`).join('') : '<p class="muted">No open clarification questions.</p>';
    }
    document.getElementById('ask-form').addEventListener('submit', async event => {
      event.preventDefault();
      const form = new FormData(event.target);
      await fetch('/api/questions', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(Object.fromEntries(form)) });
      event.target.question.value = '';
      event.target.context.value = '';
      await loadState();
    });
    async function answerQuestion(event, id) {
      event.preventDefault();
      const form = new FormData(event.target);
      await fetch(`/api/questions/${id}/answer`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(Object.fromEntries(form)) });
      await loadState();
    }
    loadState();
    setInterval(loadState, 5000);
  </script>
</body>
</html>
"""
