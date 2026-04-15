from __future__ import annotations

from pathlib import Path

from .compare import compare_manifests
from .models import RunResult
from .package import inspect_package, materialize_package
from .paper import extract_paper_manifest, materialize_paper
from .reporting import render_reports
from .runner import execute_scripts
from .sandbox import prepare_sandbox
from .utils import ensure_dir, write_json


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
    output_path = Path(output_dir).expanduser().resolve()
    inputs_dir = ensure_dir(output_path / "inputs")
    workspace_dir = ensure_dir(output_path / "workspace")
    artifacts_dir = ensure_dir(output_path / "artifacts")
    logs_dir = ensure_dir(output_path / "logs")
    sandbox_dir = output_path / "sandbox"

    paper_path = materialize_paper(paper_source, inputs_dir)
    package_input, extracted_package_root = materialize_package(package_source, inputs_dir, workspace_dir)

    paper_manifest = extract_paper_manifest(paper_path)
    raw_package_manifest = inspect_package(package_input, extracted_package_root)
    sandbox_manifest = prepare_sandbox(
        source_root=extracted_package_root,
        package_manifest=raw_package_manifest,
        sandbox_root=sandbox_dir,
        enable=sandbox,
        install_dependencies=install_dependencies,
        timeout_seconds=timeout_seconds,
    )
    package_root = Path(sandbox_manifest.project_root)
    package_manifest = inspect_package(package_input, package_root)
    execution_records = execute_scripts(
        scripts=package_manifest.scripts,
        package_root=package_root,
        logs_dir=logs_dir,
        execute=execute,
        timeout_seconds=timeout_seconds,
        sandbox=sandbox_manifest,
        stata_bin=stata_bin,
    )
    package_manifest = inspect_package(package_input, package_root)
    comparison = compare_manifests(paper_manifest, package_manifest)

    write_json(artifacts_dir / "paper_manifest.json", paper_manifest)
    write_json(artifacts_dir / "raw_package_manifest.json", raw_package_manifest)
    write_json(artifacts_dir / "sandbox_manifest.json", sandbox_manifest)
    write_json(artifacts_dir / "package_manifest.json", package_manifest)
    write_json(artifacts_dir / "execution_manifest.json", execution_records)
    write_json(artifacts_dir / "comparison.json", comparison)

    report_markdown, report_html = render_reports(
        output_dir=output_path,
        paper=paper_manifest,
        package=package_manifest,
        sandbox=sandbox_manifest,
        execution_records=execution_records,
        comparison=comparison,
    )
    summary_json = output_path / "summary.json"
    write_json(
        summary_json,
        {
            "paper_title": paper_manifest.title,
            "paper_source": paper_manifest.source,
            "package_source": package_manifest.source,
            "sandbox_enabled": sandbox_manifest.enabled,
            "sandbox_root": sandbox_manifest.root,
            "verdict": comparison.summary.verdict,
            "numeric_match_rate": comparison.summary.numeric_match_rate,
            "table_match_rate": comparison.summary.table_match_rate,
            "figure_match_rate": comparison.summary.figure_match_rate,
            "dependency_bootstrap_steps": len(sandbox_manifest.install_records),
            "report_markdown": str(report_markdown),
            "report_html": str(report_html),
        },
    )

    return RunResult(
        output_dir=output_path,
        paper_manifest=paper_manifest,
        package_manifest=package_manifest,
        sandbox_manifest=sandbox_manifest,
        execution_records=execution_records,
        comparison=comparison,
        report_markdown=report_markdown,
        report_html=report_html,
        summary_json=summary_json,
    )
