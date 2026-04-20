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

### Step 5: AI Analysis

After the run completes, analyze the results intelligently:

1. Read `report.md` and look at the numeric comparison table
2. For each numeric match, determine if it's a **substantive** research finding or a **coincidental** match (citation number, version number, equation reference, etc.)
3. Assess each figure: does source data exist? Would it need GPU/heavy compute to reproduce?
4. Compute an adjusted match rate counting only substantive claims
5. Write the analysis to `analysis.json` in the output directory

This step is critical because raw numeric matching can inflate rates by counting coincidental matches (e.g., "refs. 37,38" matching a 37.0 in the data).

### Step 6: Report Results

After analysis:
1. Present the **adjusted verdict** (not the raw one)
2. Show how many claims were filtered as coincidental with examples
3. Highlight the substantive match rate
4. For figures: which have source data, which need compute, which are infeasible
5. Provide the path to `report.html` for interactive browsing with side-by-side figure comparison
6. Give specific recommendations for improving the replication
