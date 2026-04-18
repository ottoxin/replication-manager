---
name: replicate-paper
description: Replicate an academic paper using replication-manager. Use when user says "replicate", "reproduce paper", "check replication", "run replication", or provides a paper+package to validate.
argument-hint: [paper-path-or-url] [package-path-or-url]
allowed-tools: Bash(*), Read, Grep, Glob, Edit, Write, Agent, WebFetch
---

# Replicate Paper

Replicate and validate: $ARGUMENTS

## Workflow

### Step 1: Locate Inputs

Identify the paper and replication package:

- **Paper**: PDF, HTML, or text file path, or URL
- **Package**: Local directory, ZIP file, or GitHub URL

If a GitHub URL is given, clone it first. If only a paper URL is given, fetch the page and look for data/code availability sections.

### Step 2: Environment Setup

Activate the replication-manager environment:
```bash
source <repo-root>/.venv/bin/activate
```

If `.venv` doesn't exist, create it:
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[all]"
```

### Step 3: Screen First

Always run screening before full execution to understand feasibility:
```bash
replication-manager run \
  --paper <paper-path> \
  --package <package-path> \
  --output-dir <output-dir> \
  --no-execute \
  --log-level INFO
```

Read the screening report in `artifacts/screening_report.json`. Key things to check:
- How many scripts are GPU/heavy-compute vs lightweight
- What data is available vs missing
- What the compute estimate is
- What the recommendations say

### Step 4: Decide Execution Strategy

Based on screening results:

**If mostly lightweight**: Run full execution
```bash
replication-manager run --paper <paper> --package <package> --output-dir <dir>
```

**If mixed lightweight + heavy**: Use --skip-heavy to auto-skip GPU/heavy scripts
```bash
replication-manager run --paper <paper> --package <package> --output-dir <dir> --skip-heavy
```

**If all heavy/GPU**: Run inspect-only and report what would be needed
```bash
replication-manager run --paper <paper> --package <package> --output-dir <dir> --no-execute
```

### Step 5: Report Results

After the run completes:
1. Read `report.md` for the full comparison
2. Check the screening section for what was skipped and why
3. Present the verdict, match rates, and any suggestions
4. Provide the path to `report.html` for interactive browsing

Key metrics to highlight:
- Verdict (fully/largely/partially/not reproducible)
- How many scripts ran vs skipped
- Numeric/table/figure match rates
- Which figures were classified as manually created
