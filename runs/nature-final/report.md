# Replication Report

## Summary

- Paper: Qianyue Hao1, Fengli Xu1 ✉, Yong Li1,2 ✉ & James Evans3,4 ✉
- Verdict: **largely reproducible**
- Numeric match rate: 70.0% (131/187 substantive)
- Table match rate: 0.0% (0/0)
- Figure match rate: 0.0% (0/14)

### AI Analysis

Of 234 numeric claims extracted from the paper, 47 were classified as coincidental (citation numbers, version numbers, equation references, etc.). Among the 187 substantive claims, 131 (70%) matched values in the source data. 56 substantive claims could not be matched — these may require running the full computational pipeline. Script execution: 0 succeeded, 13 failed, 0 skipped. Failed scripts typically require upstream intermediate data from heavy compute. Of 14 figures, 4 have source data for verification, 10 cannot be reproduced without additional compute. Adjusted verdict: largely reproducible.

- Substantive matches: 131
- Coincidental filtered: 47
- Figures with source data: 4/14

## Inputs

- Paper source: `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/inputs/paper.pdf`
- Package source: `/gpfs/projects/p33196/kym9881/replication-manager/examples/nature-ai-impacts`
- Package root: `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project`

## Sandbox

- Enabled: yes
- Sandbox root: `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox`
- Project root: `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project`
- Python executable: `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/.venv/bin/python`
- R library dir: `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/r_libs`

## Dependency Bootstrap

| Step | Language | Status | Return code | Duration (s) |
| --- | --- | --- | --- | ---: |
| `pip-install-requirements-txt` | python | success | 0 | 166.430 |

## Agent Workflow

| Agent | Role | Phase | Status | Summary |
| --- | --- | --- | --- | --- |
| Coordinator | Plans the next skill and builds the shared replication state. | Phase A | success | Materialized paper input `paper.pdf` and package input `nature-ai-impacts`; Extracted 0 tables, 14 figures, and 234 numeric claims from the paper; Inspected the package and found 44 scripts, 1 environment files, 420 table-like artifacts, and 2 figure artifacts; plus 1 more skill(s). |
| Executor | Prepares the runtime, runs scripts, and diagnoses execution blockers. | Phase A-Phase B | failed | Prepared a sandboxed workspace with 1 bootstrap step(s) and 44 runnable script(s); Ran 13 script(s): 0 succeeded, 0 blocked, 0 skipped, 13 failed; Generated 0 diagnostic note(s) about environment gaps, skipped stages, and blocked dependencies. |
| Reporter | Compares outputs to the paper and compiles the submission-facing report. | Phase B-Phase C | success | Computed verdict `partially reproducible` with numeric/table/figure rates 76.1%/0.0%/0.0%; Rendered Markdown and HTML reports from the workflow state. |
| Analyst | Filters coincidental matches and assesses what can and cannot be replicated. | Phase B | success | Filtered 47 coincidental claims, 131/187 substantive matched (70%). Adjusted verdict: `largely reproducible`. |

## Skill Workflow

| Skill | Agent | Phase | Status | Summary |
| --- | --- | --- | --- | --- |
| intake_sources | Coordinator | Phase A | success | Materialized paper input `paper.pdf` and package input `nature-ai-impacts`. |
| profile_paper | Coordinator | Phase A | success | Extracted 0 tables, 14 figures, and 234 numeric claims from the paper. |
| inspect_package | Coordinator | Phase A | success | Inspected the package and found 44 scripts, 1 environment files, 420 table-like artifacts, and 2 figure artifacts. |
| prepare_workspace | Executor | Phase A | success | Prepared a sandboxed workspace with 1 bootstrap step(s) and 44 runnable script(s). |
| screen_package | Coordinator | Phase A | success | Screened 44 scripts: 13 runnable, 6 GPU, 25 heavy-compute. Compute estimate: Large-scale (41.3 million). |
| execute_package | Executor | Phase A | failed | Ran 13 script(s): 0 succeeded, 0 blocked, 0 skipped, 13 failed. |
| diagnose_execution | Executor | Phase B | success | Generated 0 diagnostic note(s) about environment gaps, skipped stages, and blocked dependencies. |
| match_outputs | Reporter | Phase B | success | Computed verdict `partially reproducible` with numeric/table/figure rates 76.1%/0.0%/0.0%. |
| analyze_results | Analyst | Phase B | success | Filtered 47 coincidental claims, 131/187 substantive matched (70%). Adjusted verdict: `largely reproducible`. |
| write_report | Reporter | Phase C | success | Rendered Markdown and HTML reports from the workflow state. |

## Screening

- Compute estimate: Large-scale (41.3 million)
- Total scripts: 44 (13 runnable, 6 GPU, 25 heavy)
- Available data: 2 source(s)
- Missing data: 0 file(s)

### Script Classifications

| Script | Category | Runnable | Reason |
| --- | --- | --- | --- |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/run_all.sh` | gpu_required | no | Uses GPU libraries (torch/tensorflow/cuda) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_Date.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_Year.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_Field.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_Grant.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_Topic.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Author_Name.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_Author.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_IsData.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Author_Field.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Author_Career.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_IsReview.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_SubField.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/ClassifyWork_Union.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_IsNanoSci.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_Reference.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/SelectWork_Journal.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Space_Author.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/ClassifyWork_Title_Raw.py` | gpu_required | no | Uses GPU libraries (torch/tensorflow/cuda) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Author_Career_Date.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Author_Institution.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_TeamLast.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Topic_Field_SubField.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Space_WorkField.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_Disruption.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/ClassifyWork_Abstract_Raw.py` | gpu_required | no | Uses GPU libraries (torch/tensorflow/cuda) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_PhraseLen2ByYear.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_PhraseLen3ByYear.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/ClassifyWork_Title_Extend1.py` | gpu_required | no | Uses GPU libraries (torch/tensorflow/cuda) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Entropy_WorkField.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Author_PaperByYear.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Space_WorkSubField.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_CoreReference.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_CitationByYear.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/ClassifyWork_Abstract_Extend1.py` | gpu_required | no | Uses GPU libraries (torch/tensorflow/cuda) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Author_CitationByYear.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_Following_Engage.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Space_SpreadByCitation.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/EmbedWork_AbstractTitle_Specter2.py` | gpu_required | no | Uses GPU libraries (torch/tensorflow/cuda) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_CoreCitationByYear.py` | lightweight | yes | No GPU or large-data indicators; inputs available |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_PhraseLen2ByYear_AllFields.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Work_PhraseLen3ByYear_AllFields.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/SelectWork_Year_TitleAbstract_Language.py` | heavy_compute | no | Processes large-scale data (chunked reads / distributed) |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_Distance_Engage_NoEngage_Pairwise.py` | lightweight | yes | No GPU or large-data indicators; inputs available |

### Figure Classifications

| Figure | Category | Reason |
| --- | --- | --- |
| Figure 1 | Increasing prevalence of AI adoption in science: a, Increasing | unknown | No script reference or matching artifact found; may be manually created |
| Figure 2 | AI enlarges paper impact and enhances researcher careers: Fig. 2 | AI enlarges paper impact and enhances researcher careers. | unknown | No script reference or matching artifact found; may be manually created |
| Figure E8: ; χ2 ≥ 84.05, P < 0.001 and df = 1 in a median test on | unknown | No script reference or matching artifact found; may be manually created |
| Figure 3: | AI adoption is associated with a contraction in knowledge extent | unknown | No script reference or matching artifact found; may be manually created |
| Figure 4: | Reduced follow-on engagement and more overlapping works in | unknown | No script reference or matching artifact found; may be manually created |
| Figure E1: | Illustration for the method of identifying AI usage | unknown | No script reference or matching artifact found; may be manually created |
| Figure E2: | Procedure of accuracy evaluation via expert | unknown | No script reference or matching artifact found; may be manually created |
| Figure E3: | Comparison of the total citations of AI and non-AI | unknown | No script reference or matching artifact found; may be manually created |
| Figure E4: | Annual publications of researchers adopting AI and | unknown | No script reference or matching artifact found; may be manually created |
| Figure E5: | Scientists’ career role transition. ( a) The career role | unknown | No script reference or matching artifact found; may be manually created |
| Figure E6: | Team composition of AI and non-AI papers. ( a) AI | unknown | No script reference or matching artifact found; may be manually created |
| Figure E7: | Model fitting the role transition time of junior | unknown | No script reference or matching artifact found; may be manually created |
| Figure E9: | The knowledge extent of AI and non-AI papers in each | unknown | No script reference or matching artifact found; may be manually created |
| Figure E10: | The Matthew effect in citations to AI and non-AI | unknown | No script reference or matching artifact found; may be manually created |

### Recommendations

- Run 13 lightweight script(s) and skip 6 GPU + 25 heavy-compute script(s). Use --skip-heavy to auto-skip.
- Intermediate results are available in the package. Downstream scripts can replicate from these without re-running the full pipeline.
- 14 figure(s) have no matching script or artifact. They may be manually created or generated by undetected code.
- No visualization/plotting scripts found in the package. The paper has 14 figure(s) but the package contains only data-processing code. Figure reproduction requires plotting code not provided by the authors.
- Source data files found (114 file(s)) but no visualization scripts to render them into figures.

## Diagnostics

- No additional workflow diagnostics were generated.

## Execution

| Script | Language | Status | Return code | Duration (s) |
| --- | --- | --- | --- | ---: |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Author_CitationByYear.py` | python | failed | 1 | 1.308 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Author_PaperByYear.py` | python | failed | 1 | 0.081 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Space_SpreadByCitation.py` | python | failed | 1 | 1.312 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_CoreCitationByYear.py` | python | failed | 1 | 0.082 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_CoreReference.py` | python | failed | 1 | 0.082 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_Disruption.py` | python | failed | 1 | 0.082 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_Distance_Engage_NoEngage_Pairwise.py` | python | failed | 1 | 3.855 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_Following_Engage.py` | python | failed | 1 | 0.086 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Calculate_Work_TeamLast.py` | python | failed | 1 | 0.080 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/ClassifyWork_Union.py` | python | failed | 1 | 0.340 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Author_Career.py` | python | failed | 1 | 3.798 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Author_Career_Date.py` | python | failed | 1 | 0.542 |
| `/gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/code/Get_Author_Field.py` | python | failed | 1 | 0.497 |

## Table Comparison

| Paper table | Matched artifact | Score | Matched values |
| --- | --- | ---: | ---: |


## Figure Comparison

| Paper figure | Matched artifact | Score |
| --- | --- | ---: |
| Figure 1 | Increasing prevalence of AI adoption in science: a, Increasing | — | 0.00 |
| Figure 2 | AI enlarges paper impact and enhances researcher careers: Fig. 2 | AI enlarges paper impact and enhances researcher careers. | — | 0.00 |
| Figure E8: ; χ2 ≥ 84.05, P < 0.001 and df = 1 in a median test on | — | 0.00 |
| Figure 3: | AI adoption is associated with a contraction in knowledge extent | — | 0.00 |
| Figure 4: | Reduced follow-on engagement and more overlapping works in | — | 0.00 |
| Figure E1: | Illustration for the method of identifying AI usage | — | 0.00 |
| Figure E2: | Procedure of accuracy evaluation via expert | — | 0.00 |
| Figure E3: | Comparison of the total citations of AI and non-AI | — | 0.00 |
| Figure E4: | Annual publications of researchers adopting AI and | — | 0.00 |
| Figure E5: | Scientists’ career role transition. ( a) The career role | — | 0.00 |
| Figure E6: | Team composition of AI and non-AI papers. ( a) AI | — | 0.00 |
| Figure E7: | Model fitting the role transition time of junior | — | 0.00 |
| Figure E9: | The knowledge extent of AI and non-AI papers in each | — | 0.00 |
| Figure E10: | The Matthew effect in citations to AI and non-AI | — | 0.00 |

## Numeric Comparison

| Paper claim | Source | Context | Paper value | Artifact value | Artifact | Score | Status |
| --- | --- | --- | ---: | ---: | --- | ---: | --- |
| `37,38` | Line 1002 | on the basis of Fleiss's κ (refs. 37,38), which is an unsupervised meas- | 3738.0 | — | — | 0.00 | missing |
| `14.87%` | Line 1017 | which ranges from 14.87% in materials science to 22.15% in geology. | 14.87 | 14.87005593945377 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__DL_era_citation.csv | 1.00 | matched |
| `22.15%` | Line 1017 | which ranges from 14.87% in materials science to 22.15% in geology. | 22.15 | 22.15163297045101 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__DL_era_citation.csv | 1.00 | matched |
| `0.02` | Line 1025 | paper and find that from 13.82% (materials science, σ = 0.02) to 20.28% | 0.02 | 0.02000200020002 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `13.82%` | Line 1025 | paper and find that from 13.82% (materials science, σ = 0.02) to 20.28% | 13.82 | 13.82209346504559 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__DL_era_citation.csv | 1.00 | matched |
| `20.28%` | Line 1025 | paper and find that from 13.82% (materials science, σ = 0.02) to 20.28% | 20.28 | 20.28015877581545 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__DL_era_citation.csv | 1.00 | matched |
| `1.58%` | Line 1031 | illustrates that only 1.58% of papers across all disciplines intentionally | 1.58 | 1.579846821104782 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS31__a.csv | 1.00 | matched |
| `12` | Line 1032 | list the authors in alphabetical order (Supplementary Table 12) and | 12.0 | 12.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig7__Medicine_establish.csv | 1.00 | matched |
| `2,282,029` | Line 1063 | we obtain 2,282,029 scientists in the six disciplines with complete role | 2282029.0 | — | — | 0.00 | missing |
| `64,` | Line 1067 | in previous studies63,64, we further validate our detection results by | 64.0 | 64.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `< 0.01` | Line 1073 | conceptual work significantly rises (P < 0.01 and df = 1 in a Cochran– | 0.01 | 0.0099995507863878 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_disruption.csv | 1.00 | matched |
| `60%` | Line 1075 | tion at a high level (60% or more) on transition to becoming established | 60.0 | 60.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `768` | Line 1146 | {[ ], [] ,… ,[ ]},[ ]∈ , (6)768Rp1 p2 pn pi | 768.0 | — | — | 0.00 | missing |
| `33,` | Line 115 | eras, we fine-tune BERT32,33, an established language model34– 36, on | 33.0 | 33.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `36,` | Line 115 | eras, we fine-tune BERT32,33, an established language model34– 36, on | 36.0 | 36.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `1,000` | Line 1165 | given size. For each domain, we randomly sample 1,000 papers from | 1000.0 | 1000.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS35__a.csv | 1.00 | matched |
| `1,000` | Line 1168 | extent values across these 1,000 random samples, we ensure that the | 1000.0 | 1000.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS37__b.csv | 1.00 | matched |
| `11` | Line 1203 | (− 1) ×1 00 (%). (11)nn(− 1) | 11.0 | 11.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig7__Medicine_quit.csv | 1.00 | matched |
| `3.11` | Line 1227 | This study used Python 3.11.0 with software packages to conduct data | 3.11 | 3.109908738811028 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS11.csv | 1.00 | matched |
| `1.15` | Line 1229 | SciPy (v.1.15.2), scikit-learn (v.1.6.1) and matplotlib (v.3.10.1). The t-SNE | 1.15 | 1.15035325756994 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig2__a.csv | 1.00 | matched |
| `1.6` | Line 1229 | SciPy (v.1.15.2), scikit-learn (v.1.6.1) and matplotlib (v.3.10.1). The t-SNE | 1.6 | 1.600128010240819 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS25__ML_era.csv | 1.00 | matched |
| `3.10` | Line 1229 | SciPy (v.1.15.2), scikit-learn (v.1.6.1) and matplotlib (v.3.10.1). The t-SNE | 3.1 | 3.1 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `16` | Line 1244 | In CVPR'16: Proc. 2016 IEEE conference on computer vision and pattern recognitio | 16.0 | 16.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig7__Medicine_establish.csv | 1.00 | matched |
| `785` | Line 1251 | ACM SIGKDD International Conference on Knowledge Discovery and Data Mining 785–7 | 785.0 | — | — | 0.00 | missing |
| `794` | Line 1251 | ACM SIGKDD International Conference on Knowledge Discovery and Data Mining 785–7 | 794.0 | — | — | 0.00 | missing |
| `0.964` | Line 129 | tioned above, achieving an average Fleiss' κ of 0.964 (refs. 37,38). The | 0.964 | 0.9639999880906176 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Total.csv | 1.00 | matched |
| `37,38` | Line 129 | tioned above, achieving an average Fleiss' κ of 0.964 (refs. 37,38). The | 3738.0 | — | — | 0.00 | missing |
| `0.875` | Line 13 | to identify AI-augmented research, with an F1-score of 0.875 in validation again | 0.875 | 0.8750000158549113 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig4__c.csv | 1.00 | matched |
| `0.875` | Line 130 | BERT model attains an average F1-score of 0.875 in an evaluation that | 0.875 | 0.8750000158549113 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/SourceData_Fig4__c.csv | 1.00 | matched |
| `41.3` | Line 14 | labelled data. Using a dataset of 41.3 million research papers across the natura | 41.3 | 41.30702004369716 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__ML_era_citation.csv | 1.00 | matched |
| `1320` | Line 1411 | evaluation. We randomly sample 1320 papers and delegate three experts to | 1320.0 | 1320.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS1.csv | 1.00 | matched |
| `99%` | Line 1422 | a higher academic impact than non-AI papers. 99% CIs are shown as error bars | 99.0 | 99.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig4__d.csv | 1.00 | matched |
| `5,377,346` | Line 1428 | AI (P < 0.001, n = 5,377,346). On average, researchers adopting AI annually | 5377346.0 | — | — | 0.00 | missing |
| `< 0.001` | Line 1428 | AI (P < 0.001, n = 5,377,346). On average, researchers adopting AI annually | 0.001 | 0.0009997501930778187 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS24__ML_era_disruption.csv | 1.00 | matched |
| `3.02` | Line 1429 | publish 3.02 times more papers compared with those not using AI. 99% CIs | 3.02 | 3.020074349442379 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `99%` | Line 1429 | publish 3.02 times more papers compared with those not using AI. 99% CIs | 99.0 | 99.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig4__d.csv | 1.00 | matched |
| `99%` | Line 1453 | while it remains stable and high after that transition. 99% CIs are shown as err | 99.0 | 99.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS14__a.csv | 1.00 | matched |
| `1.99` | Line 1464 | scientists decreased from 2.89 in non-AI teams to 1.99 in AI teams (31.14%), | 1.99 | 1.990858153801401 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS11.csv | 1.00 | matched |
| `2.89` | Line 1464 | scientists decreased from 2.89 in non-AI teams to 1.99 in AI teams (31.14%), | 2.89 | 2.890202389047483 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS31__a.csv | 1.00 | matched |
| `31.14%` | Line 1464 | scientists decreased from 2.89 in non-AI teams to 1.99 in AI teams (31.14%), | 31.14 | — | — | 0.00 | missing |
| `10.77%` | Line 1465 | while the number of established scientists decreased from 4.01 to 3.58 (10.77%). | 10.77 | 10.7718038385516 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__e.csv | 1.00 | matched |
| `3.58` | Line 1465 | while the number of established scientists decreased from 4.01 to 3.58 (10.77%). | 3.58 | 3.579899497487437 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `4.01` | Line 1465 | while the number of established scientists decreased from 4.01 to 3.58 (10.77%). | 4.01 | 4.009920634920635 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `99%` | Line 1475 | age than those without AI. For all panels, 99% CIs are shown as error bars or | 99.0 | 99.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS30__d.csv | 1.00 | matched |
| `1,137,076` | Line 1486 | established researcher in ( a) biology (n = 625,093), (c) medicine (n = 1,137,07 | 1137076.0 | — | — | 0.00 | missing |
| `625,093` | Line 1486 | established researcher in ( a) biology (n = 625,093), (c) medicine (n = 1,137,07 | 625093.0 | — | — | 0.00 | missing |
| `625,093` | Line 1488 | from junior researcher to leave academia in (b) biology (n = 625,093), (d) medic | 625093.0 | — | — | 0.00 | missing |
| `1,137,076` | Line 1489 | (n = 1,137,076), and (f) physics (n = 120,366). All survival functions can be we | 1137076.0 | — | — | 0.00 | missing |
| `120,366` | Line 1489 | (n = 1,137,076), and (f) physics (n = 120,366). All survival functions can be we | 120366.0 | — | — | 0.00 | missing |
| `70%` | Line 1513 | of knowledge extent can be observed in more than 70% of over two hundred | 70.0 | 70.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `1,000` | Line 1514 | sub-fields ( n = 1,000 samples in each subfield). For all subfields, 99% CIs are | 1000.0 | 1000.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/SourceData_Fig4__a.csv | 1.00 | matched |
| `99%` | Line 1514 | sub-fields ( n = 1,000 samples in each subfield). For all subfields, 99% CIs are | 99.0 | 99.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS30__d.csv | 1.00 | matched |
| `20%` | Line 1523 | with approximately 20% of top papers receiving 80% of citations and 50% | 20.0 | 20.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `50%` | Line 1523 | with approximately 20% of top papers receiving 80% of citations and 50% | 50.0 | 50.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `80%` | Line 1523 | with approximately 20% of top papers receiving 80% of citations and 50% | 80.0 | 80.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__e.csv | 1.00 | matched |
| `95%` | Line 1524 | receiving 95%. This unequal distribution leads to a higher Gini coefficient in | 95.0 | 95.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `100` | Line 1525 | citation patterns surrounding AI research ( P < 0.001, n = 100 sampled paper | 100.0 | 100.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__e.csv | 1.00 | matched |
| `< 0.001` | Line 1525 | citation patterns surrounding AI research ( P < 0.001, n = 100 sampled paper | 0.001 | 0.001000265788825803 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_disruption.csv | 1.00 | matched |
| `99%` | Line 1527 | consistent across all fields examined. For all panels, 99% CIs are shown as erro | 99.0 | 99.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS33__d.csv | 1.00 | matched |
| `1.37` | Line 19 | become research project leaders 1.37 years earlier than those who do not. By con | 1.37 | 1.369984292777794 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS7__b_Overall.csv | 1.00 | matched |
| `4.63%` | Line 20 | AI adoption shrinks the collective volume of scientific topics studied by 4.63%  | 4.63 | 4.62967032967033 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `107` | Line 207 | Number of /f_inely tuned samples (×107) | 107.0 | 107.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `22%` | Line 21 | decreases scientists' engagement with one another by 22%. By consequence, adopti | 22.0 | 22.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `0.93` | Line 239 | reached consensus, with κ ≥ 0.93. Our model identification results have strong | 0.93 | 0.9300004840322535 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `0.85` | Line 240 | accuracy in validation against expert-labelled data, with an F1-score ≥0.85. | 0.85 | 0.8499997193670769 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Materials_Science.csv | 1.00 | matched |
| `15` | Line 241 | c, Relative adoption frequency of the top 15 AI methods across all disciplines | 15.0 | 15.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig7__Medicine_establish.csv | 1.00 | matched |
| `99%` | Line 248 | observations), where 99% confidence intervals (CIs) are shown as error bars | 99.0 | 99.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `0.75%` | Line 260 | In total we identify 310,957 AI-augmented papers, comprising 0.75% | 0.75 | 0.7499991667298735 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `310,957` | Line 260 | In total we identify 310,957 AI-augmented papers, comprising 0.75% | 310957.0 | — | — | 0.00 | missing |
| `< 0.001` | Line 273 | P < 0.001 and degrees of freedom (df) = 1 in a Cochran–Armitage test) | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `1,388.70` | Line 274 | to 51.89 (biology, Z = 1,388.70, P < 0.001 and df = 1 in a Cochran– | 1388.7 | — | — | 0.00 | missing |
| `51.89` | Line 274 | to 51.89 (biology, Z = 1,388.70, P < 0.001 and df = 1 in a Cochran– | 51.89 | — | — | 0.00 | missing |
| `< 0.001` | Line 274 | to 51.89 (biology, Z = 1,388.70, P < 0.001 and df = 1 in a Cochran– | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Materials_Science.csv | 1.00 | matched |
| `135.46` | Line 277 | 135.46 times in geology (Z = 546.81, P < 0.001 and df = 1 in a Cochran– | 135.46 | — | — | 0.00 | missing |
| `546.81` | Line 277 | 135.46 times in geology (Z = 546.81, P < 0.001 and df = 1 in a Cochran– | 546.81 | — | — | 0.00 | missing |
| `< 0.001` | Line 277 | 135.46 times in geology (Z = 546.81, P < 0.001 and df = 1 in a Cochran– | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Medicine.csv | 1.00 | matched |
| `2,237.51` | Line 278 | Armitage test) to 362.16 in physics (Z = 2,237.51, P < 0.001 and df = 1 | 2237.51 | — | — | 0.00 | missing |
| `362.16` | Line 278 | Armitage test) to 362.16 in physics (Z = 2,237.51, P < 0.001 and df = 1 | 362.16 | — | — | 0.00 | missing |
| `< 0.001` | Line 278 | Armitage test) to 362.16 in physics (Z = 2,237.51, P < 0.001 and df = 1 | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Physics.csv | 1.00 | matched |
| `98.70%` | Line 289 | are 98.70% higher than those to non-AI papers on average (Fig. 2a, | 98.7 | — | — | 0.00 | missing |
| `13,` | Line 29 | tion12,13, healthcare14,15 and industry16. Major investments in predictive | 13.0 | 13.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `15` | Line 29 | tion12,13, healthcare14,15 and industry16. Major investments in predictive | 15.0 | 15.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `8.33` | Line 290 | t ≥ 8.33, P < 0.001 and df > 103 in t-test on any year). In addition to higher | 8.33 | 8.326163581360495 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__ML_era_citation.csv | 1.00 | matched |
| `< 0.001` | Line 290 | t ≥ 8.33, P < 0.001 and df > 103 in t-test on any year). In addition to higher | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Total.csv | 1.00 | matched |
| `> 103` | Line 290 | t ≥ 8.33, P < 0.001 and df > 103 in t-test on any year). In addition to higher | 103.0 | 103.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `1%` | Line 308 | 1% | 1.0 | 1.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `10%` | Line 313 | 10% | 10.0 | 10.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `1%` | Line 361 | a, Average (insets: top 1% and 10%) annual citations after publication of AI (re | 1.0 | 1.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `10%` | Line 361 | a, Average (insets: top 1% and 10%) annual citations after publication of AI (re | 10.0 | 10.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig7__Medicine_establish.csv | 1.00 | matched |
| `2,282,029` | Line 371 | (P < 0.001, n = 2,282,029). The survival functions can be well-fit with exponent | 2282029.0 | — | — | 0.00 | missing |
| `< 0.001` | Line 371 | (P < 0.001, n = 2,282,029). The survival functions can be well-fit with exponent | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig4__c.csv | 1.00 | matched |
| `4.06` | Line 381 | lished (Extended Data Fig. 3, t ≥ 4.06, P < 0.001 and df > 103 in a t-test | 4.06 | 4.060193072118115 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `< 0.001` | Line 381 | lished (Extended Data Fig. 3, t ≥ 4.06, P < 0.001 and df > 103 in a t-test | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS30__c.csv | 1.00 | matched |
| `> 103` | Line 381 | lished (Extended Data Fig. 3, t ≥ 4.06, P < 0.001 and df > 103 in a t-test | 103.0 | 103.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `40` | Line 383 | across journals of varying Journal Citation Report quantiles 40 (Sup- | 40.0 | 40.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `14` | Line 384 | plementary Fig. 14). We find that the proportion of AI papers in Q1 | 14.0 | 14.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `18.60%` | Line 385 | journals is 18.60% higher than that of non-AI papers in all journals; in | 18.6 | 18.59957947181166 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS22__DL_era_citation.csv | 1.00 | matched |
| `1.59%` | Line 386 | Q2 journals, the AI proportion is 1.59% higher; whereas Q3 and Q4 jour- | 1.59 | 1.591073147256978 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__e.csv | 1.00 | matched |
| `3629.11` | Line 387 | nals hold a relatively lower proportion of papers with AI (χ2 = 3629.11, | 3629.11 | — | — | 0.00 | missing |
| `< 0.001` | Line 388 | P < 0.001 and df = 3 in a χ2-test). These results indicate a heterogeneous | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS33__c.csv | 1.00 | matched |
| `3.02` | Line 392 | On average, researchers adopting AI annually publish 3.02 times more | 3.02 | 3.020074349442379 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `47.18` | Line 393 | papers (t ≥ 47.18, P < 0.001 and df > 103 in t-test on any discipline) and | 47.18 | 47.18303714260784 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS25__ML_era.csv | 1.00 | matched |
| `< 0.001` | Line 393 | papers (t ≥ 47.18, P < 0.001 and df > 103 in t-test on any discipline) and | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `> 103` | Line 393 | papers (t ≥ 47.18, P < 0.001 and df > 103 in t-test on any discipline) and | 103.0 | 103.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__e.csv | 1.00 | matched |
| `17` | Line 398 | plementary Fig. 17). Furthermore, when controlling for and comparing | 17.0 | 17.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `1.33` | Line 412 | reduced research team sizes, averaging 1.33 (19.29%) fewer scientists | 1.33 | 1.330133830110501 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS14__c.csv | 1.00 | matched |
| `19.29%` | Line 412 | reduced research team sizes, averaging 1.33 (19.29%) fewer scientists | 19.29 | 19.29258353708232 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__ML_era_citation.csv | 1.00 | matched |
| `20.47` | Line 413 | (t = 20.47, P < 0.001 and df > 103 in a t-test; Extended Data Fig. 6). Specifi- | 20.47 | 20.47023360964582 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__ML_era_citation.csv | 1.00 | matched |
| `< 0.001` | Line 413 | (t = 20.47, P < 0.001 and df > 103 in a t-test; Extended Data Fig. 6). Specifi- | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/SourceData_ExtFig10__Materials_Science.csv | 1.00 | matched |
| `> 103` | Line 413 | (t = 20.47, P < 0.001 and df > 103 in a t-test; Extended Data Fig. 6). Specifi- | 103.0 | 103.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS14__a.csv | 1.00 | matched |
| `1.99` | Line 415 | non-AI teams to 1.99 (31.14%) in AI teams (t = 19.02, P < 0.001 and df > 103 | 1.99 | 1.990858153801401 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS11.csv | 1.00 | matched |
| `19.02` | Line 415 | non-AI teams to 1.99 (31.14%) in AI teams (t = 19.02, P < 0.001 and df > 103 | 19.02 | 19.01896788346738 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS25__GAI_era.csv | 1.00 | matched |
| `31.14%` | Line 415 | non-AI teams to 1.99 (31.14%) in AI teams (t = 19.02, P < 0.001 and df > 103 | 31.14 | — | — | 0.00 | missing |
| `< 0.001` | Line 415 | non-AI teams to 1.99 (31.14%) in AI teams (t = 19.02, P < 0.001 and df > 103 | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/SourceData_ExtFig10__Medicine.csv | 1.00 | matched |
| `> 103` | Line 415 | non-AI teams to 1.99 (31.14%) in AI teams (t = 19.02, P < 0.001 and df > 103 | 103.0 | 103.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS5_S6__Chemistry_left.csv | 1.00 | matched |
| `10.77%` | Line 417 | 4.01 in non-AI teams to 3.58 (10.77%) in AI teams (t = 20.82, P < 0.001 and | 10.77 | 10.77102565765381 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS33__a.csv | 1.00 | matched |
| `20.82` | Line 417 | 4.01 in non-AI teams to 3.58 (10.77%) in AI teams (t = 20.82, P < 0.001 and | 20.82 | 20.82060185185185 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__ML_era_citation.csv | 1.00 | matched |
| `3.58` | Line 417 | 4.01 in non-AI teams to 3.58 (10.77%) in AI teams (t = 20.82, P < 0.001 and | 3.58 | 3.579899497487437 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `4.01` | Line 417 | 4.01 in non-AI teams to 3.58 (10.77%) in AI teams (t = 20.82, P < 0.001 and | 4.01 | 4.009920634920635 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `< 0.001` | Line 417 | 4.01 in non-AI teams to 3.58 (10.77%) in AI teams (t = 20.82, P < 0.001 and | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/SourceData_ExtFig10__Physics.csv | 1.00 | matched |
| `> 103` | Line 418 | df > 103 in t-test). This indicates that AI adoption primarily contributes | 103.0 | 103.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS5_S6__Chemistry_middle.csv | 1.00 | matched |
| `45%` | Line 424 | that AI-adopting junior scientists become established scientists is 45%, | 45.0 | 45.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `13.64%` | Line 425 | which is 13.64% higher than for their counterparts who do not adopt | 13.64 | 13.63923070654388 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__Overall_citation.csv | 1.00 | matched |
| `1.40` | Line 426 | AI (t ≥ 1.40, P < 0.2 and df = 90 in a t-test on four out of six disciplines). | 1.4 | 1.400379376542646 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS15__b.csv | 1.00 | matched |
| `90` | Line 426 | AI (t ≥ 1.40, P < 0.2 and df = 90 in a t-test on four out of six disciplines). | 90.0 | 90.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `< 0.2` | Line 426 | AI (t ≥ 1.40, P < 0.2 and df = 90 in a t-test on four out of six disciplines). | 0.2 | 0.2000197099714205 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `0.987` | Line 438 | 8.70 years for those who do not (R2 = 0.987). This demonstrates how AI | 0.987 | 0.987000000593932 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Total.csv | 1.00 | matched |
| `8.70` | Line 438 | 8.70 years for those who do not (R2 = 0.987). This demonstrates how AI | 8.7 | 8.701326952360235 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS25__ML_era.csv | 1.00 | matched |
| `10.77%` | Line 444 | are, on average, 10.77% younger than those involved in non-AI papers | 10.77 | 10.77102565765381 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS33__a.csv | 1.00 | matched |
| `2.12` | Line 445 | (Extended Data Fig. 6; t ≥ 2.12, P < 0.05 and df > 103 in a t-test on most | 2.12 | 2.1217640657364 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS14__b.csv | 1.00 | matched |
| `< 0.05` | Line 445 | (Extended Data Fig. 6; t ≥ 2.12, P < 0.05 and df > 103 in a t-test on most | 0.05 | 0.05 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS16__b.csv | 1.00 | matched |
| `> 103` | Line 445 | (Extended Data Fig. 6; t ≥ 2.12, P < 0.05 and df > 103 in a t-test on most | 103.0 | 103.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS5_S6__Materials_Science_left.csv | 1.00 | matched |
| `26` | Line 45 | scientific writing23– 26 and facilitate the distillation of scientific findings, | 26.0 | 26.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `44` | Line 464 | ground between AI and non-AI papers in each given domain43,44 (Fig. 3b | 44.0 | 44.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `4.63%` | Line 466 | associated with a 4.63% contracted median collective knowledge extent | 4.63 | 4.62967032967033 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `70%` | Line 471 | be observed in more than 70% of them (Extended Data Fig. 9). When we | 70.0 | 70.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `79.20` | Line 474 | knowledge distribution of AI research has a lower entropy (χ2 ≥ 79.20, | 79.2 | — | — | 0.00 | missing |
| `< 0.001` | Line 475 | P < 0.001 and df = 1 in a median test on any discipline), indicating an | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/SourceData_ExtFig10__Total.csv | 1.00 | matched |
| `22` | Line 486 | adoption (Supplementary Figs. 22–24). By contrast, data availability | 22.0 | 22.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig7__Medicine_establish.csv | 1.00 | matched |
| `24` | Line 486 | adoption (Supplementary Figs. 22–24). By contrast, data availability | 24.0 | 24.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `1.91` | Line 500 | is on average 3.46% more expanded than that of non-AI papers (t ≥ 1.91, | 1.91 | 1.909836065573771 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `3.46%` | Line 500 | is on average 3.46% more expanded than that of non-AI papers (t ≥ 1.91, | 3.46 | 3.459265734265734 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_citation.csv | 1.00 | matched |
| `0.1` | Line 501 | P ≤ 0.1 and df > 103 in t-test on 30 out of 32 pairs of data). The contrac- | 0.1 | 0.1000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `30` | Line 501 | P ≤ 0.1 and df > 103 in t-test on 30 out of 32 pairs of data). The contrac- | 30.0 | 30.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `32` | Line 501 | P ≤ 0.1 and df > 103 in t-test on 30 out of 32 pairs of data). The contrac- | 32.0 | 32.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `> 103` | Line 501 | P ≤ 0.1 and df > 103 in t-test on 30 out of 32 pairs of data). The contrac- | 103.0 | 103.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS5_S6__Materials_Science_middle.csv | 1.00 | matched |
| `22%` | Line 511 | spawns 22% less follow-on engagement (t ≥ 8.10, P < 0.001 and df > 103 | 22.0 | 22.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig7__Medicine_quit.csv | 1.00 | matched |
| `8.10` | Line 511 | spawns 22% less follow-on engagement (t ≥ 8.10, P < 0.001 and df > 103 | 8.1 | 8.09869580542827 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__DL_era_citation.csv | 1.00 | matched |
| `< 0.001` | Line 511 | spawns 22% less follow-on engagement (t ≥ 8.10, P < 0.001 and df > 103 | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/SourceData_Fig4__c.csv | 1.00 | matched |
| `> 103` | Line 511 | spawns 22% less follow-on engagement (t ≥ 8.10, P < 0.001 and df > 103 | 103.0 | 103.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS5_S6__Medicine_left.csv | 1.00 | matched |
| `22.20%` | Line 520 | nate the field, with 22.20% of top papers receiving 80% of the citations | 22.2 | 22.20206606132386 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__ML_era_citation.csv | 1.00 | matched |
| `80%` | Line 520 | nate the field, with 22.20% of top papers receiving 80% of the citations | 80.0 | 80.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `54.14%` | Line 521 | and the top 54.14% receiving 95% of citations. This unequal distribution | 54.14 | — | — | 0.00 | missing |
| `95%` | Line 521 | and the top 54.14% receiving 95% of citations. This unequal distribution | 95.0 | 95.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `0.754` | Line 522 | leads to a Gini coefficient of 0.754 in citation patterns surrounding AI | 0.754 | 0.7539981494567133 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Total.csv | 1.00 | matched |
| `0.690` | Line 523 | research, higher than 0.690 for non-AI papers (t = 27.86, P < 0.001 and | 0.69 | 0.6900038498919112 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `27.86` | Line 523 | research, higher than 0.690 for non-AI papers (t = 27.86, P < 0.001 and | 27.86 | 27.86151792047399 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__Overall_citation.csv | 1.00 | matched |
| `< 0.001` | Line 523 | research, higher than 0.690 for non-AI papers (t = 27.86, P < 0.001 and | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS30__c.csv | 1.00 | matched |
| `198` | Line 524 | df = 198 in t-test), signalling a disparity in recognition. | 198.0 | 198.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `590,325,130` | Line 526 | we sample 590,325,130 pairs of papers, where each pair cites the same | 590325130.0 | — | — | 0.00 | missing |
| `768` | Line 530 | between these pairs of papers within our 768-dimensional vector | 768.0 | — | — | 0.00 | missing |
| `18.11%` | Line 532 | that are disengaged from one another tends to be 18.11% larger than | 18.11 | 18.11006888082539 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS22__Overall_citation.csv | 1.00 | matched |
| `76.51%` | Line 534 | the closest disengaged paper pairs are 76.51% closer to one another | 76.51 | — | — | 0.00 | missing |
| `110` | Line 574 | OpenAlex papers = 41.3 million Max length = 288 tokens SPECTER 2.0 parameters =  | 110.0 | 110.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `2.0` | Line 574 | OpenAlex papers = 41.3 million Max length = 288 tokens SPECTER 2.0 parameters =  | 2.0 | 2.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `288` | Line 574 | OpenAlex papers = 41.3 million Max length = 288 tokens SPECTER 2.0 parameters =  | 288.0 | 288.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `41.3` | Line 574 | OpenAlex papers = 41.3 million Max length = 288 tokens SPECTER 2.0 parameters =  | 41.3 | 41.30702004369716 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS24__ML_era_citation.csv | 1.00 | matched |
| `768` | Line 574 | OpenAlex papers = 41.3 million Max length = 288 tokens SPECTER 2.0 parameters =  | 768.0 | — | — | 0.00 | missing |
| `1,000` | Line 600 | extent of AI and non-AI papers in each field ( P < 0.001, n = 1,000 samples in | 1000.0 | 1000.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig4__a.csv | 1.00 | matched |
| `< 0.001` | Line 600 | extent of AI and non-AI papers in each field ( P < 0.001, n = 1,000 samples in | 0.001 | 0.001000100010001 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS33__c.csv | 1.00 | matched |
| `1,000` | Line 602 | d, Knowledge entropy of AI and non-AI papers in each field ( P < 0.001, n = 1,00 | 1000.0 | 1000.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS33__a.csv | 1.00 | matched |
| `< 0.001` | Line 602 | d, Knowledge entropy of AI and non-AI papers in each field ( P < 0.001, n = 1,00 | 0.001 | 0.0009998942170202588 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__GAI_era_disruption.csv | 1.00 | matched |
| `1.5` | Line 605 | quartiles (Q1 and Q3), with 1.5 times the interquartile range shown as whiskers | 1.5 | 1.5 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig6__d.csv | 1.00 | matched |
| `41,298,433` | Line 63 | on scientists and science, covering 41,298,433 research papers span- | 41298433.0 | — | — | 0.00 | missing |
| `31` | Line 65 | roborated using the Web of Science30,31. Notably, we do not focus on | 31.0 | 31.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `99%` | Line 665 | 99% | 99.0 | 99.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `1%` | Line 667 | 1% | 1.0 | 1.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `27,405,011` | Line 713 | families, that is, an original paper and its cumulative citations ( n = 27,405,0 | 27405011.0 | — | — | 0.00 | missing |
| `23,342,516` | Line 716 | (P < 0.001, n = 23,342,516), where there are fewer follow-on interactions among | 23342516.0 | — | — | 0.00 | missing |
| `< 0.001` | Line 716 | (P < 0.001, n = 23,342,516), where there are fewer follow-on interactions among | 0.001 | 0.0009998942170202588 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/source_data/csv/Supplementary_FigS24__GAI_era_disruption.csv | 1.00 | matched |
| `100` | Line 719 | more on a smaller number of top papers ( P < 0.001, n = 100 sampled paper | 100.0 | 100.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `< 0.001` | Line 719 | more on a smaller number of top papers ( P < 0.001, n = 100 sampled paper | 0.001 | 0.0009997501930778187 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/Supplementary_FigS24__ML_era_disruption.csv | 1.00 | matched |
| `590,325,130` | Line 722 | versus disengaged (purple) ( n = 590,325,130 sampled paper pairs). Results | 590325130.0 | — | — | 0.00 | missing |
| `99%` | Line 725 | overlaps in knowledge space. For all panels, 99% CIs are shown as error bars or | 99.0 | 99.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__e.csv | 1.00 | matched |
| `33` | Line 74 | and geology. We then leverage a fine-tuned BERT language model32,33 | 33.0 | 33.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `2281` | Line 778 | scientific research. Nat. Human Behav. 8, 2281–2292 (2024). | 2281.0 | — | — | 0.00 | missing |
| `2292` | Line 778 | scientific research. Nat. Human Behav. 8, 2281–2292 (2024). | 2292.0 | — | — | 0.00 | missing |
| `12` | Line 785 | challenges in K-12 settings. AI Ethics 2, 431–440 (2022). | 12.0 | 12.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `431` | Line 785 | challenges in K-12 settings. AI Ethics 2, 431–440 (2022). | 431.0 | 431.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `440` | Line 785 | challenges in K-12 settings. AI Ethics 2, 431–440 (2022). | 440.0 | 440.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `120` | Line 787 | (or generative AI) in healthcare. npj Digital Med. 6, 120 (2023). | 120.0 | 120.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `4.0` | Line 792 | intelligence in industry 4.0: a survey on what, how, and where. IEEE Trans. Indu | 4.0 | 4.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `11,` | Line 816 | writing in biomedical publications through excess vocabulary. Sci. Adv. 11, eadt | 11.0 | 11.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `57` | Line 826 | understanding. In Proc. 57th Annual Meeting of the Association for Computational | 57.0 | 57.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `38` | Line 829 | Annual Meeting of the Association for Computational Linguistics 38–45 (ACL, 2020 | 38.0 | 38.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `45` | Line 829 | Annual Meeting of the Association for Computational Linguistics 38–45 (ACL, 2020 | 45.0 | 45.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `3613` | Line 831 | In Proc. 57th Annual Meeting of the Association for Computational Linguistics 36 | 3613.0 | — | — | 0.00 | missing |
| `3618` | Line 831 | In Proc. 57th Annual Meeting of the Association for Computational Linguistics 36 | 3618.0 | — | — | 0.00 | missing |
| `57` | Line 831 | In Proc. 57th Annual Meeting of the Association for Computational Linguistics 36 | 57.0 | 57.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `58` | Line 834 | representation learning using citation-informed transformers. In Proc. 58th Annu | 58.0 | 58.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `2270` | Line 835 | Meeting of the Association for Computational Linguistics 2270–2282 (ACL, 2020). | 2270.0 | — | — | 0.00 | missing |
| `2282` | Line 835 | Meeting of the Association for Computational Linguistics 2270–2282 (ACL, 2020). | 2282.0 | — | — | 0.00 | missing |
| `61` | Line 837 | benchmark for scientific document representations. In Proc. 61st Annual Meeting  | 61.0 | 61.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `5548` | Line 838 | Association for Computational Linguistics 5548–5566 (ACL, Canada, 2023). | 5548.0 | — | — | 0.00 | missing |
| `5566` | Line 838 | Association for Computational Linguistics 5548–5566 (ACL, Canada, 2023). | 5566.0 | — | — | 0.00 | missing |
| `11,` | Line 859 | science. Royal Soc. Open Sci. 11, 231130 (2024). | 11.0 | 11.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig7__Medicine_establish.csv | 1.00 | matched |
| `231130` | Line 859 | science. Royal Soc. Open Sci. 11, 231130 (2024). | 231130.0 | — | — | 0.00 | missing |
| `265.7` | Line 881 | OpenAlex contains 265.7 million research papers, along with related | 265.7 | — | — | 0.00 | missing |
| `66,117,158` | Line 883 | sive quantity of papers in the OpenAlex dataset, we select 66,117,158 | 66117158.0 | — | — | 0.00 | missing |
| `53,` | Line 892 | scientific disciplines in MAG52,53, that is, art, biology, business, chem- | 53.0 | 53.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `41,298,433` | Line 914 | majority of OpenAlex articles, resulting in 41,298,433 papers, con- | 41298433.0 | — | — | 0.00 | missing |
| `18,392,040` | Line 915 | taining 18,392,040 in biology, 4,209,771 in chemistry and 2,380,666 | 18392040.0 | — | — | 0.00 | missing |
| `2,380,666` | Line 915 | taining 18,392,040 in biology, 4,209,771 in chemistry and 2,380,666 | 2380666.0 | — | — | 0.00 | missing |
| `4,209,771` | Line 915 | taining 18,392,040 in biology, 4,209,771 in chemistry and 2,380,666 | 4209771.0 | — | — | 0.00 | missing |
| `24,315,342` | Line 916 | in geology, 4,755,717 in materials science, 24,315,342 in medicine and | 24315342.0 | — | — | 0.00 | missing |
| `4,755,717` | Line 916 | in geology, 4,755,717 in materials science, 24,315,342 in medicine and | 4755717.0 | — | — | 0.00 | missing |
| `5,138,488` | Line 917 | 5,138,488 in physics. The selected disciplines cover various dimensions | 5138488.0 | — | — | 0.00 | missing |
| `56` | Line 926 | method55,56. We regard the deep learning era to have begun in 2015, as | 56.0 | 56.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `16` | Line 952 | length of tokenization to be 16 for titles and 256 for abstracts. We design | 16.0 | 16.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig5.csv | 1.00 | matched |
| `256` | Line 952 | length of tokenization to be 16 for titles and 256 for abstracts. We design | 256.0 | 256.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `10%` | Line 957 | we randomly split the positive and negative data into 90% and 10% sets, | 10.0 | 10.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig7__Medicine_quit.csv | 1.00 | matched |
| `90%` | Line 957 | we randomly split the positive and negative data into 90% and 10% sets, | 90.0 | 90.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `1%` | Line 971 | published in these venues as positive cases and randomly sample 1% of | 1.0 | 1.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `26,165` | Line 973 | tive cases, resulting in 26,165 positive and 291,035 negative cases. We | 26165.0 | — | — | 0.00 | missing |
| `291,035` | Line 973 | tive cases, resulting in 26,165 positive and 291,035 negative cases. We | 291035.0 | — | — | 0.00 | missing |
| `30` | Line 974 | fine-tune the pre-trained model for 30 epochs on the training set and | 30.0 | 30.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
| `>100` | Line 981 | venues with >80% AI probability and >100 papers as AI venues. We also | 100.0 | 100.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `>80%` | Line 981 | venues with >80% AI probability and >100 papers as AI venues. We also | 80.0 | 80.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `1%` | Line 985 | and randomly sample 1% of those remaining as negative cases, result- | 1.0 | 1.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig10__Chemistry.csv | 1.00 | matched |
| `231,258` | Line 986 | ing in 31,311 positive and 231,258 negative cases. We then fine-tune the | 231258.0 | — | — | 0.00 | missing |
| `31,311` | Line 986 | ing in 31,311 positive and 231,258 negative cases. We then fine-tune the | 31311.0 | — | — | 0.00 | missing |
| `30` | Line 987 | obtained optimal model in the first stage for another 30 epochs with | 30.0 | 30.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `110` | Line 993 | We arbitrarily sample 220 papers (110 papers × 2 groups) from each | 110.0 | 110.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_Fig1__d.csv | 1.00 | matched |
| `220` | Line 993 | We arbitrarily sample 220 papers (110 papers × 2 groups) from each | 220.0 | 220.0 | /gpfs/projects/p33196/kym9881/replication-manager/runs/nature-final/sandbox/project/results/SourceData_ExtFig9.csv | 1.00 | matched |
