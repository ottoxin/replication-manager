from __future__ import annotations

from pathlib import Path

from jinja2 import Environment

from .log import get_logger
from .models import (
    AgentRecord,
    ComparisonBundle,
    ExecutionRecord,
    PackageManifest,
    PaperManifest,
    SandboxManifest,
    SkillRecord,
)
from .utils import ensure_dir, read_text_safely

logger = get_logger("reporting")


MARKDOWN_TEMPLATE = """
# Replication Report

## Summary

- Paper: {{ paper.title }}
- Verdict: **{{ comparison.summary.verdict }}**
- Numeric match rate: {{ pct(comparison.summary.numeric_match_rate) }} ({{ comparison.summary.matched_numeric_claims }}/{{ comparison.summary.total_numeric_claims }})
- Table match rate: {{ pct(comparison.summary.table_match_rate) }} ({{ comparison.summary.matched_tables }}/{{ comparison.summary.total_tables }})
- Figure match rate: {{ pct(comparison.summary.figure_match_rate) }} ({{ comparison.summary.matched_figures }}/{{ comparison.summary.total_figures }})

## Inputs

- Paper source: `{{ paper.source }}`
- Package source: `{{ package.source }}`
- Package root: `{{ package.root }}`

## Sandbox

- Enabled: {{ "yes" if sandbox.enabled else "no" }}
- Sandbox root: `{{ sandbox.root }}`
- Project root: `{{ sandbox.project_root }}`
- Python executable: `{{ sandbox.python_executable if sandbox.python_executable else "system default" }}`
- R library dir: `{{ sandbox.r_library_dir if sandbox.r_library_dir else "system default" }}`

## Dependency Bootstrap

| Step | Language | Status | Return code | Duration (s) |
| --- | --- | --- | --- | ---: |
{% for record in sandbox.install_records -%}
| `{{ record.label }}` | {{ record.language }} | {{ record.status }} | {{ record.return_code if record.return_code is not none else "-" }} | {{ "%.3f"|format(record.duration_seconds) }} |
{% endfor %}

## Agent Workflow

| Agent | Role | Phase | Status | Summary |
| --- | --- | --- | --- | --- |
{% for agent in agent_trace -%}
| {{ agent.name }} | {{ agent.role }} | {{ agent.phase }} | {{ agent.status }} | {{ agent.summary }} |
{% endfor %}

## Skill Workflow

| Skill | Agent | Phase | Status | Summary |
| --- | --- | --- | --- | --- |
{% for skill in skill_trace -%}
| {{ skill.name }} | {{ skill.agent }} | {{ skill.phase }} | {{ skill.status }} | {{ skill.summary }} |
{% endfor %}

{% if screening %}
## Screening

- Compute estimate: {{ screening.compute_estimate }}
- Total scripts: {{ screening.total_scripts }} ({{ screening.runnable_scripts }} runnable, {{ screening.gpu_scripts }} GPU, {{ screening.heavy_scripts }} heavy)
- Available data: {{ screening.available_data | length }} source(s)
- Missing data: {{ screening.missing_data | length }} file(s)

### Script Classifications

| Script | Category | Runnable | Reason |
| --- | --- | --- | --- |
{% for s in screening.script_classifications -%}
| `{{ s.path }}` | {{ s.category }} | {{ "yes" if s.runnable else "no" }} | {{ s.reason }} |
{% endfor %}

{% if screening.figure_classifications %}
### Figure Classifications

| Figure | Category | Reason |
| --- | --- | --- |
{% for f in screening.figure_classifications -%}
| Figure {{ f.number }}: {{ f.caption }} | {{ f.category }} | {{ f.reason }} |
{% endfor %}
{% endif %}

### Recommendations

{% for rec in screening.recommendations -%}
- {{ rec }}
{% endfor %}
{% endif %}

## Diagnostics

{% if diagnostic_notes -%}
{% for note in diagnostic_notes -%}
- {{ note }}
{% endfor %}
{% else -%}
- No additional workflow diagnostics were generated.
{% endif %}

## Execution

| Script | Language | Status | Return code | Duration (s) |
| --- | --- | --- | --- | ---: |
{% for record in execution_records -%}
| `{{ record.script_path }}` | {{ record.language }} | {{ record.status }} | {{ record.return_code if record.return_code is not none else "-" }} | {{ "%.3f"|format(record.duration_seconds) }} |
{% endfor %}

## Table Comparison

| Paper table | Matched artifact | Score | Matched values |
| --- | --- | ---: | ---: |
{% for match in comparison.table_matches -%}
| Table {{ match.table_number }}: {{ match.table_title }} | {{ match.artifact_path if match.artifact_path else "—" }} | {{ "%.2f"|format(match.overlap_score) }} | {{ match.matched_values }}/{{ match.paper_values }} |
{% endfor %}

## Figure Comparison

| Paper figure | Matched artifact | Score |
| --- | --- | ---: |
{% for match in comparison.figure_matches -%}
| Figure {{ match.figure_number }}: {{ match.caption }} | {{ match.artifact_path if match.artifact_path else "—" }} | {{ "%.2f"|format(match.score) }} |
{% endfor %}

## Numeric Comparison

| Paper claim | Source | Matched artifact | Score | Status |
| --- | --- | --- | ---: | --- |
{% for match in comparison.numeric_matches -%}
| `{{ match.claim_raw }}` | {{ match.claim_source }} | {{ match.artifact_path if match.artifact_path else "—" }} | {{ "%.2f"|format(match.score) }} | {{ "matched" if match.matched else "missing" }} |
{% endfor %}
"""


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Replication Report</title>
  <style>
    :root {
      --bg: #f6f2e8;
      --panel: #fffdf8;
      --ink: #1d1f21;
      --muted: #5b5f63;
      --accent: #9d3d24;
      --line: #d8ccbb;
      --ok: #2a6f4f;
      --warn: #8a5a00;
      --bad: #8a1c1c;
    }
    body {
      margin: 0;
      background:
        radial-gradient(circle at top right, rgba(157, 61, 36, 0.12), transparent 28%),
        linear-gradient(180deg, #efe7d6 0%, var(--bg) 30%, #f9f6ef 100%);
      color: var(--ink);
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
    }
    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 20px 64px;
    }
    .hero {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 28px;
      box-shadow: 0 18px 50px rgba(66, 38, 17, 0.08);
    }
    h1, h2 {
      margin: 0 0 14px;
      line-height: 1.1;
    }
    h1 { font-size: 2.4rem; }
    h2 { margin-top: 28px; font-size: 1.35rem; cursor: pointer; }
    h2:hover { color: var(--accent); }
    p, li { color: var(--muted); }
    .metrics {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 20px;
    }
    .metric {
      background: #faf6ef;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px 16px;
    }
    .metric strong {
      display: block;
      color: var(--accent);
      font-size: 1.5rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      overflow: hidden;
      margin-top: 12px;
    }
    th, td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 0.95rem;
    }
    th { background: #f2ebdf; cursor: pointer; user-select: none; }
    th:hover { background: #e8dfcf; }
    .matched { color: var(--ok); font-weight: 700; }
    .warn { color: var(--warn); font-weight: 700; }
    .missing { color: var(--bad); font-weight: 700; }
    code {
      background: #f2ebdf;
      border-radius: 6px;
      padding: 2px 5px;
      font-size: 0.85rem;
    }
    .filter-bar {
      margin: 12px 0 6px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .filter-bar button {
      padding: 5px 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      cursor: pointer;
      font-size: 0.85rem;
    }
    .filter-bar button.active {
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }
    .filter-bar input {
      padding: 5px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      font-size: 0.85rem;
      flex: 1;
      min-width: 180px;
    }
    .log-preview {
      display: none;
      background: #1e1e1e;
      color: #d4d4d4;
      padding: 12px 16px;
      border-radius: 8px;
      font-family: monospace;
      font-size: 0.8rem;
      max-height: 300px;
      overflow-y: auto;
      white-space: pre-wrap;
      margin-top: 6px;
    }
    .log-toggle {
      cursor: pointer;
      color: var(--accent);
      text-decoration: underline;
      font-size: 0.85rem;
    }
    .collapsible { transition: max-height 0.3s ease; overflow: hidden; }
    .suggestion {
      background: #fef9e7;
      border-left: 4px solid var(--warn);
      padding: 10px 14px;
      margin: 8px 0;
      border-radius: 0 8px 8px 0;
      font-size: 0.9rem;
    }
    .nav-toc {
      position: fixed;
      top: 40px;
      right: 20px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px 16px;
      font-size: 0.8rem;
      max-width: 200px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .nav-toc a { display: block; padding: 3px 0; color: var(--muted); text-decoration: none; }
    .nav-toc a:hover { color: var(--accent); }
    @media (max-width: 1400px) { .nav-toc { display: none; } }
    @media print { .filter-bar, .nav-toc, .log-toggle { display: none; } }
  </style>
</head>
<body>
  <nav class="nav-toc">
    <strong>Sections</strong>
    <a href="#summary">Summary</a>
    <a href="#sandbox">Sandbox</a>
    <a href="#screening">Screening</a>
    <a href="#workflow">Workflow</a>
    <a href="#diagnostics">Diagnostics</a>
    <a href="#bootstrap">Bootstrap</a>
    <a href="#execution">Execution</a>
    <a href="#tables">Tables</a>
    <a href="#figures">Figures</a>
    <a href="#numerics">Numerics</a>
  </nav>
  <main>
    <section class="hero" id="summary">
      <h1>{{ paper.title }}</h1>
      <p>Verdict: <strong>{{ comparison.summary.verdict }}</strong></p>
      <div class="metrics">
        <div class="metric">
          <span>Numeric match rate</span>
          <strong>{{ pct(comparison.summary.numeric_match_rate) }}</strong>
          <small>{{ comparison.summary.matched_numeric_claims }}/{{ comparison.summary.total_numeric_claims }}</small>
        </div>
        <div class="metric">
          <span>Table match rate</span>
          <strong>{{ pct(comparison.summary.table_match_rate) }}</strong>
          <small>{{ comparison.summary.matched_tables }}/{{ comparison.summary.total_tables }}</small>
        </div>
        <div class="metric">
          <span>Figure match rate</span>
          <strong>{{ pct(comparison.summary.figure_match_rate) }}</strong>
          <small>{{ comparison.summary.matched_figures }}/{{ comparison.summary.total_figures }}</small>
        </div>
      </div>
      <p>Paper source: <code>{{ paper.source }}</code></p>
      <p>Package source: <code>{{ package.source }}</code></p>
    </section>

    <section id="sandbox">
      <h2>Sandbox</h2>
      <table>
        <tbody>
          <tr><td>Enabled</td><td>{{ 'yes' if sandbox.enabled else 'no' }}</td></tr>
          <tr><td>Project root</td><td><code>{{ sandbox.project_root }}</code></td></tr>
          <tr><td>Python</td><td><code>{{ sandbox.python_executable if sandbox.python_executable else 'system default' }}</code></td></tr>
          <tr><td>R library</td><td><code>{{ sandbox.r_library_dir if sandbox.r_library_dir else 'system default' }}</code></td></tr>
        </tbody>
      </table>
    </section>

    {% if screening %}
    <section id="screening">
      <h2>Screening</h2>
      <div class="metrics">
        <div class="metric">
          <span>Compute estimate</span>
          <strong style="font-size:1rem">{{ screening.compute_estimate }}</strong>
        </div>
        <div class="metric">
          <span>Runnable</span>
          <strong>{{ screening.runnable_scripts }}/{{ screening.total_scripts }}</strong>
        </div>
        <div class="metric">
          <span>GPU required</span>
          <strong>{{ screening.gpu_scripts }}</strong>
        </div>
        <div class="metric">
          <span>Heavy compute</span>
          <strong>{{ screening.heavy_scripts }}</strong>
        </div>
      </div>
      {% if screening.available_data %}
      <h3>Available Data</h3>
      <ul>{% for d in screening.available_data %}<li>{{ d }}</li>{% endfor %}</ul>
      {% endif %}
      {% if screening.missing_data %}
      <h3>Missing Data</h3>
      <ul>{% for d in screening.missing_data %}<li><code>{{ d }}</code></li>{% endfor %}</ul>
      {% endif %}
      <h3>Script Classifications</h3>
      <div class="filter-bar">
        <button class="active" onclick="filterTable(this, 'screen-table', 'all')">All</button>
        <button onclick="filterTable(this, 'screen-table', 'lightweight')">Lightweight</button>
        <button onclick="filterTable(this, 'screen-table', 'gpu_required')">GPU</button>
        <button onclick="filterTable(this, 'screen-table', 'heavy_compute')">Heavy</button>
        <button onclick="filterTable(this, 'screen-table', 'data_processing')">Missing Data</button>
      </div>
      <table id="screen-table">
        <thead><tr><th>Script</th><th>Category</th><th>Runnable</th><th>Reason</th></tr></thead>
        <tbody>
        {% for s in screening.script_classifications %}
          <tr data-status="{{ s.category }}">
            <td><code>{{ basename(s.path) }}</code></td>
            <td class="{{ 'matched' if s.category == 'lightweight' else 'warn' if s.category == 'heavy_compute' else 'missing' if s.category == 'gpu_required' else 'warn' }}">{{ s.category }}</td>
            <td>{{ "yes" if s.runnable else "no" }}</td>
            <td>{{ s.reason }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
      {% if screening.figure_classifications %}
      <h3>Figure Classifications</h3>
      <table>
        <thead><tr><th>Figure</th><th>Category</th><th>Reason</th></tr></thead>
        <tbody>
        {% for f in screening.figure_classifications %}
          <tr>
            <td>Figure {{ f.number }}: {{ f.caption }}</td>
            <td class="{{ 'matched' if f.category == 'reproducible' else 'warn' if f.category == 'manual' else '' }}">{{ f.category }}</td>
            <td>{{ f.reason }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
      {% endif %}
      <h3>Recommendations</h3>
      {% for rec in screening.recommendations %}
        <div class="suggestion">{{ rec }}</div>
      {% endfor %}
    </section>
    {% endif %}

    <section id="workflow">
      <h2>Skill Workflow</h2>
      <table>
        <thead><tr><th>Skill</th><th>Agent</th><th>Phase</th><th>Status</th><th>Summary</th></tr></thead>
        <tbody>
        {% for skill in skill_trace %}
          <tr>
            <td>{{ skill.name }}</td><td>{{ skill.agent }}</td><td>{{ skill.phase }}</td>
            <td class="{{ 'matched' if skill.status == 'success' else 'missing' if skill.status == 'failed' else 'warn' }}">{{ skill.status }}</td>
            <td>{{ skill.summary }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>

    <section id="diagnostics">
      <h2>Diagnostics & Suggestions</h2>
      {% if diagnostic_notes %}
        {% for note in diagnostic_notes %}
          <div class="suggestion">{{ note }}</div>
        {% endfor %}
      {% else %}
        <p>No issues detected.</p>
      {% endif %}
      {% if suggestions %}
        <h3>Fix Suggestions</h3>
        {% for suggestion in suggestions %}
          <div class="suggestion">{{ suggestion }}</div>
        {% endfor %}
      {% endif %}
    </section>

    <section id="bootstrap">
      <h2>Dependency Bootstrap</h2>
      <table>
        <thead><tr><th>Step</th><th>Language</th><th>Status</th><th>RC</th><th>Duration</th><th>Logs</th></tr></thead>
        <tbody>
        {% for record in sandbox.install_records %}
          <tr>
            <td><code>{{ record.label }}</code></td>
            <td>{{ record.language }}</td>
            <td class="{{ 'matched' if record.status == 'success' else 'missing' if record.status == 'failed' else 'warn' }}">{{ record.status }}</td>
            <td>{{ record.return_code if record.return_code is not none else '-' }}</td>
            <td>{{ "%.1f"|format(record.duration_seconds) }}s</td>
            <td>
              {% if record.stderr_path %}
                <span class="log-toggle" onclick="toggleLog(this)">stderr</span>
                <div class="log-preview">{{ log_content(record.stderr_path) }}</div>
              {% endif %}
            </td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>

    <section id="execution">
      <h2>Execution</h2>
      <div class="filter-bar">
        <button class="active" onclick="filterTable(this, 'exec-table', 'all')">All</button>
        <button onclick="filterTable(this, 'exec-table', 'success')">Success</button>
        <button onclick="filterTable(this, 'exec-table', 'failed')">Failed</button>
        <button onclick="filterTable(this, 'exec-table', 'blocked')">Blocked</button>
        <button onclick="filterTable(this, 'exec-table', 'skipped')">Skipped</button>
        <input type="text" placeholder="Search scripts..." oninput="searchTable(this, 'exec-table')">
      </div>
      <table id="exec-table">
        <thead><tr><th>Script</th><th>Language</th><th>Status</th><th>RC</th><th>Duration</th><th>Logs</th></tr></thead>
        <tbody>
        {% for record in execution_records %}
          <tr data-status="{{ record.status }}">
            <td><code>{{ basename(record.script_path) }}</code></td>
            <td>{{ record.language }}</td>
            <td class="{{ 'matched' if record.status == 'success' else 'missing' if record.status == 'failed' else 'warn' }}">{{ record.status }}{% if record.message %} <small>({{ record.message[:80] }})</small>{% endif %}</td>
            <td>{{ record.return_code if record.return_code is not none else '-' }}</td>
            <td>{{ "%.1f"|format(record.duration_seconds) }}s</td>
            <td>
              {% if record.stderr_path %}
                <span class="log-toggle" onclick="toggleLog(this)">stderr</span>
                <div class="log-preview">{{ log_content(record.stderr_path) }}</div>
              {% endif %}
              {% if record.stdout_path %}
                <span class="log-toggle" onclick="toggleLog(this)">stdout</span>
                <div class="log-preview">{{ log_content(record.stdout_path) }}</div>
              {% endif %}
            </td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>

    <section id="tables">
      <h2>Table Comparison</h2>
      <div class="filter-bar">
        <button class="active" onclick="filterMatch(this, 'tbl-cmp', 'all')">All</button>
        <button onclick="filterMatch(this, 'tbl-cmp', 'matched')">Matched</button>
        <button onclick="filterMatch(this, 'tbl-cmp', 'missing')">Missing</button>
      </div>
      <table id="tbl-cmp">
        <thead><tr><th>Paper table</th><th>Matched artifact</th><th>Score</th><th>Values</th></tr></thead>
        <tbody>
        {% for match in comparison.table_matches %}
          <tr data-matched="{{ 'matched' if match.matched else 'missing' }}">
            <td>Table {{ match.table_number }}: {{ match.table_title }}</td>
            <td>{{ basename(match.artifact_path) if match.artifact_path else '—' }}</td>
            <td>{{ "%.2f"|format(match.overlap_score) }}</td>
            <td>{{ match.matched_values }}/{{ match.paper_values }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>

    <section id="figures">
      <h2>Figure Comparison</h2>
      <div class="filter-bar">
        <button class="active" onclick="filterMatch(this, 'fig-cmp', 'all')">All</button>
        <button onclick="filterMatch(this, 'fig-cmp', 'matched')">Matched</button>
        <button onclick="filterMatch(this, 'fig-cmp', 'missing')">Missing</button>
      </div>
      <table id="fig-cmp">
        <thead><tr><th>Paper figure</th><th>Matched artifact</th><th>Score</th></tr></thead>
        <tbody>
        {% for match in comparison.figure_matches %}
          <tr data-matched="{{ 'matched' if match.matched else 'missing' }}">
            <td>Figure {{ match.figure_number }}: {{ match.caption }}</td>
            <td>{{ basename(match.artifact_path) if match.artifact_path else '—' }}</td>
            <td>{{ "%.2f"|format(match.score) }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>

    <section id="numerics">
      <h2>Numeric Comparison</h2>
      <div class="filter-bar">
        <button class="active" onclick="filterMatch(this, 'num-cmp', 'all')">All</button>
        <button onclick="filterMatch(this, 'num-cmp', 'matched')">Matched</button>
        <button onclick="filterMatch(this, 'num-cmp', 'missing')">Missing</button>
        <input type="text" placeholder="Search claims..." oninput="searchTable(this, 'num-cmp')">
      </div>
      <table id="num-cmp">
        <thead><tr><th>Claim</th><th>Source</th><th>Artifact</th><th>Score</th><th>Status</th></tr></thead>
        <tbody>
        {% for match in comparison.numeric_matches %}
          <tr data-matched="{{ 'matched' if match.matched else 'missing' }}">
            <td><code>{{ match.claim_raw }}</code></td>
            <td>{{ match.claim_source }}</td>
            <td>{{ basename(match.artifact_path) if match.artifact_path else '—' }}</td>
            <td>{{ "%.2f"|format(match.score) }}</td>
            <td class="{{ 'matched' if match.matched else 'missing' }}">{{ 'matched' if match.matched else 'missing' }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>
  </main>
  <script>
    function toggleLog(el) {
      const pre = el.nextElementSibling || el.parentElement.querySelector('.log-preview');
      if (!pre) return;
      pre.style.display = pre.style.display === 'block' ? 'none' : 'block';
    }
    function filterTable(btn, tableId, status) {
      btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('#' + tableId + ' tbody tr').forEach(row => {
        row.style.display = (status === 'all' || row.dataset.status === status) ? '' : 'none';
      });
    }
    function filterMatch(btn, tableId, status) {
      btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('#' + tableId + ' tbody tr').forEach(row => {
        row.style.display = (status === 'all' || row.dataset.matched === status) ? '' : 'none';
      });
    }
    function searchTable(input, tableId) {
      const q = input.value.toLowerCase();
      document.querySelectorAll('#' + tableId + ' tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    }
    document.querySelectorAll('th').forEach(th => {
      th.addEventListener('click', () => {
        const table = th.closest('table');
        const idx = Array.from(th.parentElement.children).indexOf(th);
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        const asc = th.dataset.sort !== 'asc';
        th.dataset.sort = asc ? 'asc' : 'desc';
        rows.sort((a, b) => {
          const va = a.children[idx]?.textContent || '';
          const vb = b.children[idx]?.textContent || '';
          const na = parseFloat(va), nb = parseFloat(vb);
          if (!isNaN(na) && !isNaN(nb)) return asc ? na - nb : nb - na;
          return asc ? va.localeCompare(vb) : vb.localeCompare(va);
        });
        const tbody = table.querySelector('tbody');
        rows.forEach(r => tbody.appendChild(r));
      });
    });
  </script>
</body>
</html>
"""


def render_reports(
    output_dir: Path,
    paper: PaperManifest,
    package: PackageManifest,
    sandbox: SandboxManifest,
    execution_records: list[ExecutionRecord],
    comparison: ComparisonBundle,
    agent_trace: list[AgentRecord],
    skill_trace: list[SkillRecord],
    diagnostic_notes: list[str],
    screening=None,
) -> tuple[Path, Path]:
    ensure_dir(output_dir)
    logger.info("Rendering reports to %s", output_dir)

    suggestions = generate_suggestions(execution_records, comparison, sandbox, diagnostic_notes)

    def log_content(path: str | None) -> str:
        if not path:
            return ""
        text = read_text_safely(Path(path))
        lines = text.strip().splitlines()
        if len(lines) > 50:
            lines = lines[-50:]
        return "\n".join(lines) or "(empty)"

    def basename(path: str | None) -> str:
        if not path:
            return ""
        return Path(path).name

    environment = Environment(trim_blocks=True, lstrip_blocks=True, autoescape=True)
    environment.globals["pct"] = lambda value: f"{value * 100:.1f}%"
    environment.globals["log_content"] = log_content
    environment.globals["basename"] = basename
    context = {
        "paper": paper,
        "package": package,
        "sandbox": sandbox,
        "execution_records": execution_records,
        "comparison": comparison,
        "agent_trace": agent_trace,
        "skill_trace": skill_trace,
        "diagnostic_notes": diagnostic_notes,
        "suggestions": suggestions,
        "screening": screening,
    }

    md_env = Environment(trim_blocks=True, lstrip_blocks=True)
    md_env.globals["pct"] = lambda value: f"{value * 100:.1f}%"
    markdown = md_env.from_string(MARKDOWN_TEMPLATE).render(**context).strip() + "\n"
    html = environment.from_string(HTML_TEMPLATE).render(**context)

    markdown_path = output_dir / "report.md"
    html_path = output_dir / "report.html"
    markdown_path.write_text(markdown)
    html_path.write_text(html)
    return markdown_path, html_path


def generate_suggestions(
    execution_records: list[ExecutionRecord],
    comparison: ComparisonBundle,
    sandbox: SandboxManifest,
    diagnostic_notes: list[str],
) -> list[str]:
    suggestions: list[str] = []

    failed = [r for r in execution_records if r.status == "failed"]
    blocked = [r for r in execution_records if r.status == "blocked"]
    skipped = [r for r in execution_records if r.status == "skipped"]

    if failed:
        for r in failed[:3]:
            stderr = ""
            if r.stderr_path:
                stderr = read_text_safely(Path(r.stderr_path)).strip().splitlines()[-3:] if Path(r.stderr_path).exists() else []
                stderr = " | ".join(stderr) if stderr else ""
            name = Path(r.script_path).name
            if "ModuleNotFoundError" in stderr or "there is no package" in stderr.lower():
                suggestions.append(f"{name}: Missing dependency. Check requirements.txt or install the package manually.")
            elif "FileNotFoundError" in stderr or "cannot open" in stderr.lower():
                suggestions.append(f"{name}: Missing input file. Ensure upstream scripts ran successfully first.")
            else:
                suggestions.append(f"{name}: Script failed (rc={r.return_code}). Check stderr log for details.")

    if blocked:
        suggestions.append(
            f"{len(blocked)} script(s) blocked on missing inputs. "
            "Run upstream scripts first or provide the required data files."
        )

    if skipped:
        stata_skipped = [r for r in skipped if r.language == "stata"]
        if stata_skipped:
            suggestions.append(
                "Stata scripts were skipped. Set --stata-bin or REPLICATION_MANAGER_STATA_BIN to execute .do files."
            )

    if comparison.summary.numeric_match_rate < 0.5 and comparison.summary.total_numeric_claims > 0:
        suggestions.append(
            "Low numeric match rate. This may indicate the package outputs use different formatting "
            "or the scripts did not produce the expected output files."
        )

    return suggestions
