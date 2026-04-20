# Replication Manager

A pre-submission replication framework that takes a paper and its replication package, runs the code in a clean sandbox, and generates a report comparing reported and reproduced outputs.

Inspired by Yiqing Xu and Leo Yang Yang's ["Scaling Reproducibility: An AI-Assisted Workflow for Large-Scale Replication and Reanalysis"](https://yiqingxu.org/papers/2026_ai/AI_reproducibility.pdf).

![System Flowchart](docs/flowchart.svg)

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"

replication-manager run \
  --paper paper.pdf \
  --package replication_package/ \
  --output-dir runs/check
```

## System Architecture

The system uses a compact three-phase, multi-agent workflow with deterministic skills:

### Phase A: Acquisition & Screening

| Agent | Skill | Purpose |
|-------|-------|---------|
| Coordinator | `intake_sources` | Materialize paper (PDF/HTML/text) and package (ZIP/dir/GitHub) |
| Coordinator | `profile_paper` | Extract tables, figures, and numeric claims from the paper |
| Coordinator | `inspect_package` | Discover scripts, artifacts, and environment files |
| Coordinator | `screen_package` | Classify scripts (lightweight/GPU/heavy), detect visualization code, check data availability |
| Executor | `prepare_workspace` | Create sandbox with isolated venv, R libs, and dependency bootstrap |
| Executor | `execute_package` | Run scripts in DAG-ordered sequence |

### Phase B: Verification & Analysis

| Agent | Skill | Purpose |
|-------|-------|---------|
| Executor | `diagnose_execution` | Identify environment gaps, blocked stages, and missing dependencies |
| Reporter | `match_outputs` | Precision-aware numeric matching, table comparison, image hashing for figures |
| Analyst | `analyze_results` | Filter coincidental matches (citations, versions), compute adjusted verdict |

### Phase C: Reporting

| Agent | Skill | Purpose |
|-------|-------|---------|
| Reporter | `write_report` | Generate HTML and Markdown reports with side-by-side figure comparison |

## Key Features

- **Smart screening**: Classifies scripts as lightweight/GPU/heavy before execution. Detects whether visualization scripts exist in the package.
- **Coincidental match filtering**: Separates substantive research findings from citation numbers, version numbers, and equation references.
- **Side-by-side figure comparison**: Downloads published figures from journal HTML (Nature/Springer CDN) and compares against replicated artifacts.
- **Source data awareness**: Identifies source data files for each figure and reports when visualization code is missing.
- **Adjusted verdicts**: Reports match rates based on substantive claims only, not raw totals inflated by coincidental matches.

## Usage

```bash
# Full run
replication-manager run --paper paper.pdf --package package/ --output-dir runs/test

# Screen only (no execution)
replication-manager run --paper paper.pdf --package package/ --output-dir runs/test --no-execute

# Skip GPU and heavy-compute scripts
replication-manager run --paper paper.pdf --package package/ --output-dir runs/test --skip-heavy

# Remote paper + local package
replication-manager run --paper https://example.com/paper.pdf --package package.zip --output-dir runs/test

# Debug without sandbox
replication-manager run --paper paper.pdf --package package/ --output-dir runs/debug --no-sandbox
```

## Output Layout

```
output-dir/
  report.html              # Interactive HTML report with figure comparison
  report.md                # Markdown report
  summary.json             # Condensed run metrics
  inputs/                  # Materialized paper and package
  workspace/               # Extracted package contents
  sandbox/                 # Isolated execution environment
  artifacts/
    paper_manifest.json    # Extracted claims, tables, figures
    package_manifest.json  # Scripts, artifacts, environment files
    screening_report.json  # Script classifications, viz detection, recommendations
    comparison.json        # Numeric/table/figure match details
    analysis.json          # Claim classifications, adjusted verdict
```

## Example: Nature Paper Replication

The `examples/nature-ai-impacts/` directory contains the replication package for [Hao et al. (2026) "AI tools expand scientists' impact but contract science's focus"](https://doi.org/10.1038/s41586-025-09922-y) (*Nature*).

```bash
replication-manager run \
  --paper examples/nature-ai-impacts/paper.pdf \
  --package examples/nature-ai-impacts/ \
  --output-dir runs/nature \
  --skip-heavy
```

Results from the included final run (`runs/nature-final/`):
- **234 numeric claims** extracted, **47 filtered** as coincidental
- **131/187 substantive claims matched** (70%)
- **Adjusted verdict: largely reproducible**
- 14 published figures with HTML-downloaded images; 11 have source data but no visualization scripts provided

## Screening Intelligence

The screening phase detects:
- **GPU scripts**: torch, tensorflow, cuda imports
- **Heavy-compute scripts**: chunked reads, distributed processing, large-data indicators
- **Visualization scripts**: matplotlib, seaborn, ggplot, savefig, plotly usage
- **Source data**: SourceData files matching figure numbers
- **Missing inputs**: referenced data files not present in the package

When visualization scripts are absent but source data exists, the screening report flags this gap.

## Claude Code Skills

The `.claude/skills/` directory provides Claude Code skills for interactive use:

- **`/replicate-paper`** — End-to-end replication with screening, execution, analysis, and reporting
- **`/inspect-replication`** — Quick feasibility check without execution
- **`/analyze-replication`** — AI-powered post-comparison analysis: classify claims, assess figures, compute adjusted verdict

## Supported Environments

- Python dependencies from `requirements.txt`, `pyproject.toml`, `setup.py`
- R dependencies from `renv.lock`, `install.R`, `packages.R`
- Conda environments from `environment.yml`
- Code Ocean capsule layouts with mount path shimming
- Stata `.do` execution via `REPLICATION_MANAGER_STATA_BIN`

## Module Map

| Module | Purpose |
|--------|---------|
| `workflow.py` | Skill-based state machine orchestrating the three-phase pipeline |
| `screening.py` | Pre-execution feasibility analysis and script classification |
| `analysis.py` | Post-comparison heuristic filtering and adjusted verdict computation |
| `paper.py` | PDF/HTML/text parsing with pdfplumber structured table extraction |
| `compare.py` | Precision-aware numeric matching and optional image hashing |
| `sandbox.py` | Isolated execution with Python venv, R libs, conda support |
| `dag.py` | Script dependency graph for topological execution ordering |
| `reporting.py` | HTML/Markdown report generation with side-by-side figure comparison |
| `runner.py` | Script execution with timeout, logging, and output capture |

## Development

```bash
python -m pytest tests/ -v
```

## Notes

- Arbitrary replication packages can execute arbitrary code. Use an OS-level sandbox or container when needed.
- PDF export requires a modern pango library (>=1.50). On older systems, only HTML and Markdown reports are generated.
- This tool only installs dependencies declared in supported manifests. Hidden machine-specific dependencies are exactly what this workflow is meant to expose.
