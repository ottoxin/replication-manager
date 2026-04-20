---
name: analyze-replication
description: AI analysis of replication results. Filters coincidental matches, assesses figure reproducibility, and produces a reasoned verdict. Use after a replication run completes, or as part of /replicate-paper.
argument-hint: [output-dir]
allowed-tools: Bash(*), Read, Grep, Glob, Edit, Write
---

# Analyze Replication Results

Analyze the replication results in: $ARGUMENTS

## Step 1: Load Results

Read the comparison data from the run output directory:

1. Read `report.md` for the full comparison overview
2. Read `summary.json` for structured metrics
3. Read `artifacts/comparison.json` if available for detailed numeric/figure matches
4. Read the paper manifest and package manifest from `artifacts/`

## Step 2: Classify Numeric Claims

For each numeric match in the comparison, classify it as:

**Substantive** — an actual research finding, statistic, or data point:
- Percentages, rates, coefficients from results
- Sample sizes, counts of subjects/observations
- Statistical values (p-values, confidence intervals, effect sizes)
- Specific measurements reported in the text

**Coincidental** — a number that matched by chance, not a research finding:
- Citation/reference numbers (e.g., "refs. 37,38" matching 37.0 in data)
- Software version numbers (e.g., "Python 3.11" matching 3.11 in data)
- Equation numbers, figure numbers, table numbers
- Page numbers, line numbers
- Year numbers from bibliography entries
- Numbers from author affiliations or acknowledgements

Use the `claim_context` field (the in-text quote) to determine what kind of number it is. Numbers from the Results, Discussion, or Abstract sections are usually substantive. Numbers from References, Methods (software versions), or captions are often coincidental.

## Step 3: Assess Figure Reproducibility

For each figure in the comparison:
- Check if source data exists (XLSX, CSV files with matching figure numbers)
- Check if the figure-generating script ran successfully
- Check if GPU or heavy compute is needed
- Determine: can this figure be verified from available data?

## Step 4: Compute Adjusted Metrics

Calculate:
- **Adjusted numeric rate**: substantive_matches / total_substantive_claims
- **Figure feasibility**: how many figures have verification data available
- **Overall assessment**: considering what CAN be done vs what CANNOT

## Step 5: Write Analysis

Update the `analysis.json` file in the output directory with:

```json
{
  "substantive_matches": N,
  "coincidental_filtered": N,
  "substantive_missing": N,
  "adjusted_numeric_rate": 0.XX,
  "adjusted_verdict": "largely reproducible",
  "figure_assessments": [...],
  "reasoning": "2-3 paragraph explanation of what was verified, what couldn't be, and why"
}
```

## Step 6: Report

Present the analysis to the user:
1. How many claims were filtered as coincidental (with examples)
2. The adjusted match rate for substantive findings
3. Which figures can/cannot be reproduced and why
4. The adjusted verdict with reasoning
5. Specific recommendations for what would be needed to improve the replication
