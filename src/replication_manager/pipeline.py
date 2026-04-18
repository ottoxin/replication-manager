from __future__ import annotations

from pathlib import Path

from .models import RunResult
from .workflow import run_agentic_workflow


def run_pipeline(
    *,
    paper_source: str,
    package_source: str,
    output_dir: str | Path,
    execute: bool = True,
    sandbox: bool = True,
    install_dependencies: bool = True,
    timeout_seconds: int = 600,
    stata_bin: str | None = None,
) -> RunResult:
    """Run the full replication pipeline: intake → profile → inspect → sandbox → execute → compare → report."""
    return run_agentic_workflow(
        paper_source=paper_source,
        package_source=package_source,
        output_dir=output_dir,
        execute=execute,
        sandbox=sandbox,
        install_dependencies=install_dependencies,
        timeout_seconds=timeout_seconds,
        stata_bin=stata_bin,
    )
