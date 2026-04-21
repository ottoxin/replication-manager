# Replication Manager

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[all]"
```

## Test
```bash
python -m pytest tests/ -v
```

## Key Commands
```bash
# Full run
replication-manager run --paper paper.pdf --package package/ --output-dir runs/test

# Inspect only (no execution)
replication-manager run --paper paper.pdf --package package/ --output-dir runs/test --no-execute

# Skip GPU and heavy-compute scripts, replicate from intermediate results
replication-manager run --paper paper.pdf --package package/ --output-dir runs/test --skip-heavy
```

## Architecture
- `workflow.py` — skill-based state machine: intake → profile → inspect → screen → sandbox → execute → compare → report
- `screening.py` — pre-execution feasibility analysis: classifies scripts (lightweight/GPU/heavy), detects manual figures, checks data availability
- `dag.py` — builds script dependency graph for topological execution ordering
- `paper.py` — PDF/HTML/text parsing with pdfplumber structured table extraction
- `compare.py` — precision-aware numeric matching + optional image hashing for figures
- `sandbox.py` — isolated execution with Python venv, R libs, conda env support
- `figgen.py` — figure replication from source data (xlsx/csv), auto plot type inference, per-panel rendering

## Skills (in .claude/skills/)
- `replicate-paper` — end-to-end replication with screening
- `inspect-replication` — quick feasibility check without execution
- `replicate-figures` — replicate figures from source data, split multi-panel figures
