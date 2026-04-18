---
name: inspect-replication
description: Quick inspection and screening of a replication package without execution. Use when user says "inspect package", "check replication package", "what's in this package", or wants to understand feasibility before running.
argument-hint: [package-path-or-url]
allowed-tools: Bash(*), Read, Grep, Glob, Write
---

# Inspect Replication Package

Inspect and screen: $ARGUMENTS

## Workflow

### Step 1: Activate Environment

```bash
source <repo-root>/.venv/bin/activate
```

### Step 2: Run Inspection with Screening

```bash
replication-manager run \
  --paper <paper-path> \
  --package <package-path> \
  --output-dir <output-dir> \
  --no-execute \
  --log-level INFO
```

### Step 3: Read Screening Report

Read `artifacts/screening_report.json` and report:

1. **Compute estimate**: How long would full execution take
2. **Script breakdown**: Lightweight / GPU / heavy-compute / missing-data
3. **Data availability**: What data is present, what's missing
4. **Figure classifications**: Which figures are reproducible vs manually created
5. **Recommendations**: What the tool suggests

### Step 4: Summarize Feasibility

Tell the user:
- Whether full execution is feasible on the current system
- Whether `--skip-heavy` mode would still produce useful results
- What data/models need to be downloaded separately
- Whether an HPC job or GPU machine is needed
