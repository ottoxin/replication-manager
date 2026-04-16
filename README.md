# Replication Manager

`replication-manager` is a lightweight pre-submission replication framework inspired by Yiqing Xu and Leo Yang Yang's paper, ["Scaling Reproducibility: An AI-Assisted Workflow for Large-Scale Replication and Reanalysis"](https://yiqingxu.org/papers/2026_ai/AI_reproducibility.pdf).

The main use case is journal submission prep: take a paper plus its replication package, run the package in a clean sandbox, install the declared dependencies, and generate a report showing what reproduced, what is blocked upstream, and what still depends on undeclared environment assumptions.

## Core Workflow

The paper's full system is a three-layer, multi-agent workflow with execution, verification, and diagnostic phases. This repo now keeps that structure in a compact form:

1. A `Coordinator` agent profiles the paper, inspects the package, and builds shared state.
2. An `Executor` agent prepares a clean workspace, runs scripts, and diagnoses blocked stages.
3. A `Reporter` agent matches outputs back to the paper and writes the submission-facing report.

Each agent uses deterministic skills rather than open-ended LLM execution. The main built-in skills are:

- `intake_sources`
- `profile_paper`
- `inspect_package`
- `prepare_workspace`
- `execute_package`
- `diagnose_execution`
- `match_outputs`
- `write_report`

## Pre-Submission Defaults

By default, `replication-manager run` behaves like a pre-submission checker:

- It copies the unpacked package into `output_dir/sandbox/project`.
- It sets a fresh `HOME` and temporary directory.
- It creates a Python virtual environment under `output_dir/sandbox/.venv` when Python execution is involved.
- It disables Python user site-packages inside the sandbox.
- It uses an isolated R library directory under `output_dir/sandbox/r_libs`.
- It bootstraps dependencies before executing the replication scripts.

That is deliberate. If the package only works because your laptop already has the right packages installed, this tool should expose that before submission.

## Supported Dependency Bootstrap

Automatic bootstrap support is pragmatic rather than exhaustive:

- Python dependencies from `requirements.txt`
- Python project install from `pyproject.toml`, `setup.py`, or `setup.cfg`
- R dependencies from `renv.lock`
- R setup scripts from `install.R`, `packages.R`, or `setup.R`

Unsupported environment files are still detected and surfaced in the package manifest and notes.

## What It Keeps From The Paper

- Phase A: acquisition and execution.
- Phase B: reproducibility verification with precision-aware numeric matching.
- Phase C: a report layer that summarizes what matched and what did not.
- Explicit artifacts on disk for each stage.
- A structure that can accept a replication package as a `.zip`.

## What It Simplifies

- A compact three-agent loop instead of a larger multi-agent system.
- Deterministic local skills instead of a live LLM planner.
- No persistent knowledge base of failure patterns.
- No full econometric diagnostics like the paper's IV pipeline.
- No OCR or vision extraction for complicated PDFs.

This is a practical replication checker, not a full reimplementation of the paper's production system.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

The main command accepts a paper path or URL plus a replication package path, directory, or URL.

Recommended pre-submission run:

```bash
replication-manager run \
  --paper /path/to/paper.pdf \
  --package /path/to/replication_package.zip \
  --output-dir runs/pre_submission_check
```

Example with a remote paper:

```bash
replication-manager run \
  --paper https://yiqingxu.org/papers/2026_ai/AI_reproducibility.pdf \
  --package /path/to/replication_package.zip \
  --output-dir runs/ai-reproducibility
```

If you only want to inspect the package and compare already-existing artifacts, skip script execution:

```bash
replication-manager run \
  --paper /path/to/paper.pdf \
  --package /path/to/replication_package.zip \
  --output-dir runs/no-exec \
  --no-execute
```

If you need to debug outside the clean sandbox:

```bash
replication-manager run \
  --paper /path/to/paper.pdf \
  --package /path/to/replication_package.zip \
  --output-dir runs/debug \
  --no-sandbox
```

If you want the clean sandbox but need to skip bootstrap temporarily:

```bash
replication-manager run \
  --paper /path/to/paper.pdf \
  --package /path/to/replication_package.zip \
  --output-dir runs/debug \
  --no-install
```

## Output Layout

Each run writes structured outputs under the chosen output directory:

- `inputs/`: materialized paper and package inputs.
- `workspace/package/`: extracted package contents.
- `sandbox/`: clean execution copy, isolated home/temp directories, virtual environment, and bootstrap logs.
- `artifacts/paper_manifest.json`: extracted tables, figures, and numeric claims from the paper.
- `artifacts/raw_package_manifest.json`: inspection of the unpacked package before sandboxing.
- `artifacts/sandbox_manifest.json`: sandbox configuration and dependency bootstrap records.
- `artifacts/package_manifest.json`: discovered scripts and output candidates after sandbox preparation and execution.
- `artifacts/execution_manifest.json`: execution logs and return codes.
- `artifacts/comparison.json`: match details for numbers, tables, and figures.
- `report.md`: human-readable comparison report.
- `report.html`: browser-friendly report.
- `summary.json`: condensed run summary.

## Design Mapping

The original paper separates planning, execution, and verification. This repo maps that into a small orchestrated workflow:

- `workflow.py`: compact agent loop, skill registry, shared workflow state, and diagnostics.
- `paper.py`: paper parsing and claim extraction.
- `package.py`: package download, unzip, inspection, and artifact collection.
- `sandbox.py`: clean execution copy, environment isolation, and dependency bootstrap.
- `runner.py`: supported script execution.
- `compare.py`: precision-aware matching and verdict logic.
- `agents.py`: concise agent summaries built from the executed skills.
- `reporting.py`: report generation with both agent and skill traces.

## Notes

- `Rscript` is used automatically when available.
- Stata `.do` execution requires setting `REPLICATION_MANAGER_STATA_BIN`.
- This tool only installs dependencies that are declared in supported manifests. Hidden machine-specific dependencies are exactly what this workflow is meant to expose.
- Arbitrary replication packages can execute arbitrary code. Use an OS-level sandbox or container when needed.

## Development

Run the built-in tests with:

```bash
python3 -m unittest discover -s tests -v
```
