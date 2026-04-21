---
name: replicate-figures
description: Replicate figures from source data in a replication package. Analyzes published figure panels, maps them to source data files, generates matplotlib visualizations for each panel separately. Use when user says "replicate figures", "reproduce figures", "visualize source data", "regenerate plots".
argument-hint: [package-path] [output-dir]
allowed-tools: Bash(*), Read, Grep, Glob, Edit, Write, Agent
---

# Replicate Figures

Replicate figures from source data: $ARGUMENTS

## Workflow

### Step 1: Locate inputs

Find the replication package and any existing run artifacts:

- If a previous replication run exists (e.g., `runs/nature-final/`), use its `artifacts/paper_manifest.json` for figure metadata
- If no prior run, locate source data files directly (pattern: `SourceData_Fig*.xlsx`, `Supplementary_FigS*.xlsx`)

### Step 2: Environment setup

```bash
source <repo-root>/.venv/bin/activate
```

### Step 3: Discover and replicate

Use the `figgen` module to discover source data and replicate all figures:

```python
from replication_manager.figgen import replicate_all_figures, generate_summary_html
results = replicate_all_figures(package_dir, output_dir)
html_path = generate_summary_html(results, output_dir)
```

Or via CLI:
```bash
python -c "
from replication_manager.figgen import replicate_all_figures, generate_summary_html
from pathlib import Path
results = replicate_all_figures('<package-dir>', '<output-dir>')
html = generate_summary_html(results, Path('<output-dir>'))
print(f'Gallery: {html}')
for r in results:
    print(f'  Fig {r.figure_number}: {r.status} ({len(r.output_paths)} panels)')
"
```

### Step 4: Review and refine

After automatic generation:

1. Open the gallery HTML to review all panels
2. For each panel, compare with the published figure in the paper:
   - Check if the plot type matches (line vs bar vs box)
   - Check if axes, labels, and legends are reasonable
   - Note any panels that need manual adjustment
3. If a multi-panel figure has sub-panels (a, b, c, d...), each should be a separate PNG

### Step 5: Manual refinement (if needed)

If automatic inference got the plot type wrong, manually adjust:

```python
from replication_manager.figgen import read_excel_panels, render_panel
panels = read_excel_panels(Path("source_data/SourceData_Fig1.xlsx"), "1")
for p in panels:
    p.plot_type = "line_with_error"  # override if needed
    render_panel(p, Path(f"output/panel_{p.sheet_name}.png"))
```

### Step 6: Report

Present results:
- Total figures replicated vs total with source data
- Gallery HTML path for visual review
- Any panels that failed or need manual attention
- Side-by-side comparison notes with published figures
