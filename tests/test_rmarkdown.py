import shutil
import subprocess
from pathlib import Path

import pytest

from replication_manager.dag import analyze_script_io
from replication_manager.models import SandboxManifest
from replication_manager.package import discover_scripts
from replication_manager.paper import extract_text
from replication_manager.rmarkdown import extract_r_code
from replication_manager.runner import execute_script, find_missing_inputs


SOURCE = '''---
title: Replication
output: html_document
---
# Treatment effects
Example read.csv("prose.csv") is documentation.
```{r example, eval=FALSE}
read.csv("unused.csv")
```
```{r analysis}
data <- read.csv("input.csv")
write.csv(data, "result.csv", row.names=FALSE)
```
'''


def test_discovery_and_static_inputs(tmp_path):
    source = tmp_path / "analysis.RMD"
    source.write_text(SOURCE)
    scripts = discover_scripts(tmp_path)
    assert len(scripts) == 1
    assert scripts[0].language == "r"
    assert find_missing_inputs(source, tmp_path, "r") == ["input.csv"]
    inputs, outputs = analyze_script_io(scripts[0], tmp_path)
    assert inputs == {"input.csv"}
    assert outputs == {"result.csv"}


def test_fences_and_inline_code():
    code = extract_r_code('''````{r}
x <- 1
````
~~~{python}
read.csv("wrong.csv")
~~~
Inline `r read.csv("inline.csv")`.
''')
    assert "x <- 1" in code
    assert 'read.csv("inline.csv")' in code
    assert "wrong.csv" not in code


def test_paper_source_does_not_treat_code_as_claims(tmp_path):
    source = tmp_path / "paper.Rmd"
    source.write_text(SOURCE + '\nEffect is `r 987654`.\n')
    text = extract_text(source)
    assert "Treatment effects" in text
    assert "987654" not in text
    assert "write.csv" not in text


def test_real_rmarkdown_execution(tmp_path):
    if not shutil.which("Rscript"):
        pytest.skip("Rscript unavailable")
    probe = subprocess.run(
        ["Rscript", "-e", 'quit(status=if(requireNamespace("rmarkdown", quietly=TRUE) && rmarkdown::pandoc_available()) 0 else 1)'],
        capture_output=True, timeout=30,
    )
    if probe.returncode:
        pytest.skip("rmarkdown or Pandoc unavailable")
    # Exercise argument handling with apostrophes and spaces in the path.
    source = tmp_path / "author's analysis.Rmd"
    source.write_text(SOURCE)
    (tmp_path / "input.csv").write_text("value\n42\n")
    script = discover_scripts(tmp_path)[0]
    sandbox = SandboxManifest(False, str(tmp_path), str(tmp_path), str(tmp_path), str(tmp_path))
    logs = tmp_path / "logs"
    logs.mkdir()
    skipped = execute_script(script, tmp_path, logs, False, 60, sandbox, None)
    assert skipped.status == "skipped"
    assert not (tmp_path / "result.csv").exists()
    result = execute_script(script, tmp_path, logs, True, 60, sandbox, None)
    assert result.status == "success", Path(result.stderr_path).read_text() if result.stderr_path else result.message
    assert "42" in (tmp_path / "result.csv").read_text()
    source.write_text('```{r}\nstop("intentional failure")\n```\n')
    failure = execute_script(script, tmp_path, logs, True, 60, sandbox, None)
    assert failure.status == "failed"


@pytest.mark.parametrize("paper_format", ["tex", "docx", "Rmd"])
def test_rmarkdown_package_end_to_end(tmp_path, paper_format):
    from replication_manager.pipeline import run_pipeline

    if not shutil.which("Rscript"):
        pytest.skip("Rscript unavailable")
    probe = subprocess.run(
        ["Rscript", "-e", 'quit(status=if(requireNamespace("rmarkdown", quietly=TRUE) && rmarkdown::pandoc_available()) 0 else 1)'],
        capture_output=True, timeout=30,
    )
    if probe.returncode:
        pytest.skip("rmarkdown or Pandoc unavailable")
    package = tmp_path / "package"
    package.mkdir()
    (package / "data.csv").write_text("value\n1\n2\n3\n4\n")
    (package / "analysis.Rmd").write_text('''---
title: Replication case
output: html_document
---
```{r analysis, echo=FALSE}
data <- read.csv("data.csv")
estimate <- mean(data$value)
# Table 1. Mean outcome
write.csv(data.frame(estimate=estimate), "table_1.csv", row.names=FALSE)
```
''')
    paper = tmp_path / f"paper.{paper_format}"
    if paper_format == "docx":
        docx = pytest.importorskip("docx")
        document = docx.Document()
        document.add_paragraph("Replication case")
        document.add_paragraph("The mean outcome was 2.5.")
        document.add_paragraph("Table 1. Mean outcome")
        table = document.add_table(rows=2, cols=1)
        table.cell(0, 0).text = "estimate"
        table.cell(1, 0).text = "2.5"
        document.save(paper)
    elif paper_format == "tex":
        paper.write_text(r'''\documentclass{article}
\title{Replication case}
\begin{document}
\maketitle
The mean outcome was 2.5.
\begin{table}
\caption{Mean outcome}
\begin{tabular}{r}
estimate \\
2.5 \\
\end{tabular}
\end{table}
\end{document}
''')
    else:
        paper.write_text("# Replication case\nThe mean outcome was 2.5.\n\nTable 1. Mean outcome\nestimate\n2.5\n")
    output = tmp_path / "run"
    result = run_pipeline(
        paper_source=str(paper), package_source=str(package), output_dir=output,
        sandbox=True, install_dependencies=False, timeout_seconds=60,
    )
    assert result.sandbox_manifest.enabled
    assert len(result.execution_records) == 1
    record = result.execution_records[0]
    assert record.status == "success", record.message or Path(record.stderr_path).read_text()
    project = Path(result.sandbox_manifest.project_root)
    assert "2.5" in (project / "table_1.csv").read_text()
    assert (project / "analysis.html").exists()
    assert not (package / "table_1.csv").exists()
    assert any(match.matched and match.claim_value == 2.5 for match in result.comparison.numeric_matches)
    assert Path(result.report_html).is_file()
    assert Path(result.report_markdown).is_file()
