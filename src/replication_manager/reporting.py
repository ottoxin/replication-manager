from __future__ import annotations

from pathlib import Path

from jinja2 import Environment

from .models import ComparisonBundle, ExecutionRecord, PackageManifest, PaperManifest, SandboxManifest
from .utils import ensure_dir


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
    h2 { margin-top: 28px; font-size: 1.35rem; }
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
    th { background: #f2ebdf; }
    .matched { color: var(--ok); font-weight: 700; }
    .missing { color: var(--bad); font-weight: 700; }
    code {
      background: #f2ebdf;
      border-radius: 6px;
      padding: 2px 5px;
    }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>{{ paper.title }}</h1>
      <p>Verdict: <strong>{{ comparison.summary.verdict }}</strong></p>
      <div class="metrics">
        <div class="metric">
          <span>Numeric match rate</span>
          <strong>{{ pct(comparison.summary.numeric_match_rate) }}</strong>
        </div>
        <div class="metric">
          <span>Table match rate</span>
          <strong>{{ pct(comparison.summary.table_match_rate) }}</strong>
        </div>
        <div class="metric">
          <span>Figure match rate</span>
          <strong>{{ pct(comparison.summary.figure_match_rate) }}</strong>
        </div>
      </div>
      <p>Paper source: <code>{{ paper.source }}</code></p>
      <p>Package source: <code>{{ package.source }}</code></p>
      <p>Sandbox root: <code>{{ sandbox.root }}</code></p>
    </section>

    <section>
      <h2>Sandbox</h2>
      <table>
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>Enabled</td><td>{{ 'yes' if sandbox.enabled else 'no' }}</td></tr>
          <tr><td>Project root</td><td><code>{{ sandbox.project_root }}</code></td></tr>
          <tr><td>Python executable</td><td><code>{{ sandbox.python_executable if sandbox.python_executable else 'system default' }}</code></td></tr>
          <tr><td>R library dir</td><td><code>{{ sandbox.r_library_dir if sandbox.r_library_dir else 'system default' }}</code></td></tr>
        </tbody>
      </table>
    </section>

    <section>
      <h2>Dependency Bootstrap</h2>
      <table>
        <thead>
          <tr>
            <th>Step</th>
            <th>Language</th>
            <th>Status</th>
            <th>Return code</th>
            <th>Duration (s)</th>
          </tr>
        </thead>
        <tbody>
        {% for record in sandbox.install_records %}
          <tr>
            <td><code>{{ record.label }}</code></td>
            <td>{{ record.language }}</td>
            <td class="{{ 'matched' if record.status == 'success' else 'missing' if record.status == 'failed' else '' }}">{{ record.status }}</td>
            <td>{{ record.return_code if record.return_code is not none else '-' }}</td>
            <td>{{ "%.3f"|format(record.duration_seconds) }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>

    <section>
      <h2>Execution</h2>
      <table>
        <thead>
          <tr>
            <th>Script</th>
            <th>Language</th>
            <th>Status</th>
            <th>Return code</th>
            <th>Duration (s)</th>
          </tr>
        </thead>
        <tbody>
        {% for record in execution_records %}
          <tr>
            <td><code>{{ record.script_path }}</code></td>
            <td>{{ record.language }}</td>
            <td class="{{ 'matched' if record.status == 'success' else 'missing' if record.status == 'failed' else '' }}">{{ record.status }}</td>
            <td>{{ record.return_code if record.return_code is not none else '-' }}</td>
            <td>{{ "%.3f"|format(record.duration_seconds) }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>

    <section>
      <h2>Table Comparison</h2>
      <table>
        <thead>
          <tr>
            <th>Paper table</th>
            <th>Matched artifact</th>
            <th>Score</th>
            <th>Matched values</th>
          </tr>
        </thead>
        <tbody>
        {% for match in comparison.table_matches %}
          <tr>
            <td>Table {{ match.table_number }}: {{ match.table_title }}</td>
            <td>{{ match.artifact_path if match.artifact_path else '—' }}</td>
            <td>{{ "%.2f"|format(match.overlap_score) }}</td>
            <td>{{ match.matched_values }}/{{ match.paper_values }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>

    <section>
      <h2>Figure Comparison</h2>
      <table>
        <thead>
          <tr>
            <th>Paper figure</th>
            <th>Matched artifact</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
        {% for match in comparison.figure_matches %}
          <tr>
            <td>Figure {{ match.figure_number }}: {{ match.caption }}</td>
            <td>{{ match.artifact_path if match.artifact_path else '—' }}</td>
            <td>{{ "%.2f"|format(match.score) }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>

    <section>
      <h2>Numeric Comparison</h2>
      <table>
        <thead>
          <tr>
            <th>Paper claim</th>
            <th>Source</th>
            <th>Matched artifact</th>
            <th>Score</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
        {% for match in comparison.numeric_matches %}
          <tr>
            <td><code>{{ match.claim_raw }}</code></td>
            <td>{{ match.claim_source }}</td>
            <td>{{ match.artifact_path if match.artifact_path else '—' }}</td>
            <td>{{ "%.2f"|format(match.score) }}</td>
            <td class="{{ 'matched' if match.matched else 'missing' }}">{{ 'matched' if match.matched else 'missing' }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>
  </main>
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
) -> tuple[Path, Path]:
    ensure_dir(output_dir)
    environment = Environment(trim_blocks=True, lstrip_blocks=True)
    environment.globals["pct"] = lambda value: f"{value * 100:.1f}%"
    context = {
        "paper": paper,
        "package": package,
        "sandbox": sandbox,
        "execution_records": execution_records,
        "comparison": comparison,
    }

    markdown = environment.from_string(MARKDOWN_TEMPLATE).render(**context).strip() + "\n"
    html = environment.from_string(HTML_TEMPLATE).render(**context)

    markdown_path = output_dir / "report.md"
    html_path = output_dir / "report.html"
    markdown_path.write_text(markdown)
    html_path.write_text(html)
    return markdown_path, html_path
