# Replication Manager

Pre-submission replication checker: takes a paper and its replication package, runs the code in a clean sandbox, and reports what reproduced and what didn't.

Inspired by Xu & Yang's ["Scaling Reproducibility"](https://yiqingxu.org/papers/2026_ai/AI_reproducibility.pdf) (2026).

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

## What It Does

1. **Screens** the package — classifies scripts as lightweight/GPU/heavy, checks for visualization code and source data
2. **Sandboxes** execution — isolated venv, R libs, dependency bootstrap from declared manifests
3. **Compares** outputs — precision-aware numeric matching, table comparison, figure image hashing
4. **Filters** coincidental matches — separates citations, versions, equation numbers from substantive findings
5. **Reports** — HTML with side-by-side figure comparison, adjusted verdict, claim classifications

See [docs/architecture.md](docs/architecture.md) for the full module map, workflow details, and screening logic.

## Usage

```bash
# Full run
replication-manager run --paper paper.pdf --package package/ --output-dir runs/test

# Screen only (no execution)
replication-manager run --paper paper.pdf --package package/ --output-dir runs/test --no-execute

# Skip GPU and heavy-compute scripts
replication-manager run --paper paper.pdf --package package/ --output-dir runs/test --skip-heavy
```

## Example: Nature Paper

The `examples/nature-ai-impacts/` directory contains the replication package for [Hao et al. (2026)](https://doi.org/10.1038/s41586-025-09922-y), *Nature* 649, 1237–1243.

```bash
replication-manager run \
  --paper examples/nature-ai-impacts/paper.pdf \
  --package examples/nature-ai-impacts/ \
  --output-dir runs/nature \
  --skip-heavy
```

Final run results (`runs/nature-final/`):

| Metric | Value |
|--------|-------|
| Numeric claims extracted | 234 |
| Coincidental filtered | 47 |
| Substantive matched | 131 / 187 (70%) |
| Adjusted verdict | **largely reproducible** |
| Figures with published images | 14 |
| Figures with source data | 11 |
| Visualization scripts in package | 0 |

## Output

```
output-dir/
  report.html           # Interactive report with figure comparison
  report.md             # Markdown report
  summary.json          # Condensed metrics
  artifacts/            # Manifests, comparison data, screening report
```

## Claude Code Skills

For interactive use with [Claude Code](https://claude.ai/code):

- `/replicate-paper` — end-to-end replication
- `/inspect-replication` — feasibility check without execution
- `/analyze-replication` — post-comparison AI analysis

## Development

```bash
pip install -e ".[all]"
python -m pytest tests/ -v
```

## Documentation

- [Architecture & module map](docs/architecture.md)
- [System flowchart](docs/flowchart.svg)
- [Development conversation log](docs/conversation_export.html)
