from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .agents import build_agent_trace
from .compare import comparable_figure_artifacts, comparable_table_artifacts, compare_manifests
from .log import get_logger
from .models import (
    AgentRecord,
    ComparisonBundle,
    ExecutionRecord,
    PackageManifest,
    PaperManifest,
    RunResult,
    SandboxManifest,
    SkillRecord,
)
from .package import inspect_package, materialize_package
from .paper import extract_paper_manifest, materialize_paper
from .reporting import render_reports
from .runner import execute_scripts
from .sandbox import prepare_sandbox
from .screening import (
    ScreeningReport,
    filter_reproducible_figures,
    filter_runnable_scripts,
    screen_package,
)
from .utils import ensure_dir, read_text_safely, write_json

logger = get_logger("workflow")


@dataclass
class WorkflowState:
    paper_source: str
    package_source: str
    output_path: Path
    execute: bool
    sandbox_enabled: bool
    install_dependencies: bool
    timeout_seconds: int
    stata_bin: str | None
    skip_heavy: bool
    inputs_dir: Path = field(init=False)
    workspace_dir: Path = field(init=False)
    artifacts_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    sandbox_dir: Path = field(init=False)
    paper_path: Path | None = None
    package_input: Path | None = None
    extracted_package_root: Path | None = None
    package_root: Path | None = None
    paper_manifest: PaperManifest | None = None
    raw_package_manifest: PackageManifest | None = None
    sandbox_manifest: SandboxManifest | None = None
    package_manifest: PackageManifest | None = None
    screening_report: ScreeningReport | None = None
    screening_complete: bool = False
    execution_records: list[ExecutionRecord] = field(default_factory=list)
    comparison: ComparisonBundle | None = None
    report_markdown: Path | None = None
    report_html: Path | None = None
    summary_json: Path | None = None
    skill_trace: list[SkillRecord] = field(default_factory=list)
    agent_trace: list[AgentRecord] = field(default_factory=list)
    diagnostic_notes: list[str] = field(default_factory=list)
    execution_complete: bool = False
    diagnostics_complete: bool = False
    report_written: bool = False

    def __post_init__(self) -> None:
        self.output_path = self.output_path.expanduser().resolve()
        self.inputs_dir = ensure_dir(self.output_path / "inputs")
        self.workspace_dir = ensure_dir(self.output_path / "workspace")
        self.artifacts_dir = ensure_dir(self.output_path / "artifacts")
        self.logs_dir = ensure_dir(self.output_path / "logs")
        self.sandbox_dir = self.output_path / "sandbox"


@dataclass(frozen=True)
class WorkflowSkill:
    name: str
    agent: str
    phase: str
    should_run: Callable[[WorkflowState], bool]
    run: Callable[[WorkflowState], SkillRecord]


def run_agentic_workflow(
    *,
    paper_source: str,
    package_source: str,
    output_dir: str | Path,
    execute: bool = True,
    sandbox: bool = True,
    install_dependencies: bool = True,
    timeout_seconds: int = 600,
    stata_bin: str | None = None,
    skip_heavy: bool = False,
) -> RunResult:
    state = WorkflowState(
        paper_source=paper_source,
        package_source=package_source,
        output_path=Path(output_dir),
        execute=execute,
        sandbox_enabled=sandbox,
        install_dependencies=install_dependencies,
        timeout_seconds=timeout_seconds,
        stata_bin=stata_bin,
        skip_heavy=skip_heavy,
    )
    skills = default_skills()
    max_steps = len(skills) + 2

    for _ in range(max_steps):
        skill = next((item for item in skills if item.should_run(state)), None)
        if skill is None:
            break
        logger.info("[%s] %s → %s", skill.phase, skill.agent, skill.name)
        record = skill.run(state)
        logger.info("  %s: %s", record.status, record.summary)
        state.skill_trace.append(record)
        persist_artifacts(state)
    else:
        raise RuntimeError("Workflow exceeded the expected number of steps.")

    finalize_workflow(state)
    return RunResult(
        output_dir=state.output_path,
        paper_manifest=require(state.paper_manifest, "paper manifest"),
        package_manifest=require(state.package_manifest, "package manifest"),
        sandbox_manifest=require(state.sandbox_manifest, "sandbox manifest"),
        agent_trace=state.agent_trace,
        skill_trace=state.skill_trace,
        execution_records=state.execution_records,
        comparison=require(state.comparison, "comparison bundle"),
        report_markdown=require(state.report_markdown, "Markdown report"),
        report_html=require(state.report_html, "HTML report"),
        summary_json=require(state.summary_json, "summary JSON"),
        diagnostic_notes=state.diagnostic_notes,
    )


def default_skills() -> list[WorkflowSkill]:
    return [
        WorkflowSkill(
            name="intake_sources",
            agent="Coordinator",
            phase="Phase A",
            should_run=lambda state: state.paper_path is None or state.package_input is None,
            run=skill_intake_sources,
        ),
        WorkflowSkill(
            name="profile_paper",
            agent="Coordinator",
            phase="Phase A",
            should_run=lambda state: state.paper_manifest is None and state.paper_path is not None,
            run=skill_profile_paper,
        ),
        WorkflowSkill(
            name="inspect_package",
            agent="Coordinator",
            phase="Phase A",
            should_run=lambda state: state.raw_package_manifest is None and state.extracted_package_root is not None,
            run=skill_inspect_package,
        ),
        WorkflowSkill(
            name="prepare_workspace",
            agent="Executor",
            phase="Phase A",
            should_run=lambda state: state.sandbox_manifest is None and state.raw_package_manifest is not None,
            run=skill_prepare_workspace,
        ),
        WorkflowSkill(
            name="screen_package",
            agent="Coordinator",
            phase="Phase A",
            should_run=lambda state: (
                state.package_manifest is not None
                and state.paper_manifest is not None
                and not state.screening_complete
            ),
            run=skill_screen_package,
        ),
        WorkflowSkill(
            name="execute_package",
            agent="Executor",
            phase="Phase A",
            should_run=lambda state: state.package_manifest is not None and not state.execution_complete,
            run=skill_execute_package,
        ),
        WorkflowSkill(
            name="diagnose_execution",
            agent="Executor",
            phase="Phase B",
            should_run=lambda state: state.execution_complete and not state.diagnostics_complete,
            run=skill_diagnose_execution,
        ),
        WorkflowSkill(
            name="match_outputs",
            agent="Reporter",
            phase="Phase B",
            should_run=lambda state: state.execution_complete and state.comparison is None,
            run=skill_match_outputs,
        ),
        WorkflowSkill(
            name="write_report",
            agent="Reporter",
            phase="Phase C",
            should_run=lambda state: state.comparison is not None and not state.report_written,
            run=skill_write_report,
        ),
    ]


def skill_intake_sources(state: WorkflowState) -> SkillRecord:
    state.paper_path = materialize_paper(state.paper_source, state.inputs_dir)
    _try_fetch_article_html(state.paper_source, state.inputs_dir)
    state.package_input, state.extracted_package_root = materialize_package(
        state.package_source,
        state.inputs_dir,
        state.workspace_dir,
    )
    return SkillRecord(
        name="intake_sources",
        agent="Coordinator",
        phase="Phase A",
        status="success",
        summary=(
            f"Materialized paper input `{state.paper_path.name}` and package input "
            f"`{state.package_input.name}`."
        ),
        artifact_paths=[str(state.paper_path), str(state.package_input)],
    )


def _try_fetch_article_html(paper_source: str, inputs_dir: Path) -> None:
    """If the paper source looks like a journal URL, fetch the HTML for figure extraction."""
    import subprocess

    if not paper_source.startswith("http"):
        return
    html_path = inputs_dir / "article.html"
    if html_path.exists():
        return
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "30", paper_source],
            capture_output=True, timeout=35,
        )
        if result.returncode == 0 and len(result.stdout) > 5000:
            html_path.write_bytes(result.stdout)
            logger.info("Saved article HTML for figure extraction")
    except Exception:
        pass


def skill_profile_paper(state: WorkflowState) -> SkillRecord:
    paper_path = require(state.paper_path, "paper path")
    state.paper_manifest = extract_paper_manifest(paper_path)
    return SkillRecord(
        name="profile_paper",
        agent="Coordinator",
        phase="Phase A",
        status="success",
        summary=(
            f"Extracted {len(state.paper_manifest.tables)} tables, "
            f"{len(state.paper_manifest.figures)} figures, and "
            f"{len(state.paper_manifest.numeric_claims)} numeric claims from the paper."
        ),
        artifact_paths=[state.paper_manifest.source],
    )


def skill_inspect_package(state: WorkflowState) -> SkillRecord:
    package_input = require(state.package_input, "package input")
    package_root = require(state.extracted_package_root, "extracted package root")
    state.raw_package_manifest = inspect_package(package_input, package_root)
    return SkillRecord(
        name="inspect_package",
        agent="Coordinator",
        phase="Phase A",
        status="success",
        summary=(
            f"Inspected the package and found {len(state.raw_package_manifest.scripts)} scripts, "
            f"{len(state.raw_package_manifest.environment_files)} environment files, "
            f"{len(state.raw_package_manifest.table_artifacts)} table-like artifacts, and "
            f"{len(state.raw_package_manifest.figure_artifacts)} figure artifacts."
        ),
        artifact_paths=[state.raw_package_manifest.root],
    )


def skill_prepare_workspace(state: WorkflowState) -> SkillRecord:
    extracted_root = require(state.extracted_package_root, "extracted package root")
    raw_manifest = require(state.raw_package_manifest, "raw package manifest")
    state.sandbox_manifest = prepare_sandbox(
        source_root=extracted_root,
        package_manifest=raw_manifest,
        sandbox_root=state.sandbox_dir,
        enable=state.sandbox_enabled,
        install_dependencies=state.install_dependencies,
        timeout_seconds=state.timeout_seconds,
    )
    state.package_root = Path(state.sandbox_manifest.project_root)
    state.package_manifest = inspect_package(require(state.package_input, "package input"), state.package_root)
    mode = "sandboxed" if state.sandbox_manifest.enabled else "direct"
    return SkillRecord(
        name="prepare_workspace",
        agent="Executor",
        phase="Phase A",
        status="success",
        summary=(
            f"Prepared a {mode} workspace with {len(state.sandbox_manifest.install_records)} bootstrap step(s) "
            f"and {len(state.package_manifest.scripts)} runnable script(s)."
        ),
        artifact_paths=[state.sandbox_manifest.root, state.package_manifest.root],
    )


def skill_screen_package(state: WorkflowState) -> SkillRecord:
    paper = require(state.paper_manifest, "paper manifest")
    package = require(state.package_manifest, "package manifest")
    report = screen_package(paper, package)
    state.screening_report = report
    state.screening_complete = True
    write_json(state.artifacts_dir / "screening_report.json", {
        "total_scripts": report.total_scripts,
        "runnable_scripts": report.runnable_scripts,
        "skipped_scripts": report.skipped_scripts,
        "gpu_scripts": report.gpu_scripts,
        "heavy_scripts": report.heavy_scripts,
        "lightweight_scripts": report.lightweight_scripts,
        "compute_estimate": report.compute_estimate,
        "recommendations": report.recommendations,
        "available_data": report.available_data,
        "missing_data": report.missing_data,
        "script_classifications": [
            {"path": s.path, "category": s.category, "reason": s.reason, "runnable": s.runnable}
            for s in report.script_classifications
        ],
        "figure_classifications": [
            {"number": f.number, "caption": f.caption, "category": f.category, "reason": f.reason}
            for f in report.figure_classifications
        ],
    })

    if state.skip_heavy and report.skipped_scripts > 0:
        filtered = filter_runnable_scripts(package.scripts, report.script_classifications)
        state.package_manifest = PackageManifest(
            source=package.source,
            root=package.root,
            scripts=filtered,
            table_artifacts=package.table_artifacts,
            figure_artifacts=package.figure_artifacts,
            environment_files=package.environment_files,
            notes=package.notes + [
                f"Screening filtered scripts: {len(filtered)} runnable, "
                f"{report.skipped_scripts} skipped (GPU/heavy-compute/missing-data)."
            ],
        )
        logger.info("--skip-heavy: filtered to %d runnable scripts", len(filtered))

    manual_figs = [f for f in report.figure_classifications if f.category == "manual"]
    if manual_figs:
        state.paper_manifest = PaperManifest(
            source=paper.source,
            title=paper.title,
            line_count=paper.line_count,
            numeric_claims=paper.numeric_claims,
            tables=paper.tables,
            figures=filter_reproducible_figures(paper.figures, report.figure_classifications),
        )
        logger.info("Excluded %d manually-created figure(s) from comparison", len(manual_figs))

    state.diagnostic_notes.extend(report.recommendations)

    return SkillRecord(
        name="screen_package",
        agent="Coordinator",
        phase="Phase A",
        status="success",
        summary=(
            f"Screened {report.total_scripts} scripts: {report.runnable_scripts} runnable, "
            f"{report.gpu_scripts} GPU, {report.heavy_scripts} heavy-compute. "
            f"Compute estimate: {report.compute_estimate}."
        ),
        artifact_paths=[],
    )


def skill_execute_package(state: WorkflowState) -> SkillRecord:
    package_manifest = require(state.package_manifest, "package manifest")
    sandbox_manifest = require(state.sandbox_manifest, "sandbox manifest")
    package_root = require(state.package_root, "package root")
    state.execution_records = execute_scripts(
        scripts=package_manifest.scripts,
        package_root=package_root,
        logs_dir=state.logs_dir,
        execute=state.execute,
        timeout_seconds=state.timeout_seconds,
        sandbox=sandbox_manifest,
        stata_bin=state.stata_bin,
    )
    state.package_manifest = inspect_package(require(state.package_input, "package input"), package_root)
    state.execution_complete = True

    success_count = sum(record.status == "success" for record in state.execution_records)
    blocked_count = sum(record.status == "blocked" for record in state.execution_records)
    skipped_count = sum(record.status == "skipped" for record in state.execution_records)
    failed_count = sum(record.status == "failed" for record in state.execution_records)
    status = "success" if failed_count == 0 else "failed"
    return SkillRecord(
        name="execute_package",
        agent="Executor",
        phase="Phase A",
        status=status,
        summary=(
            f"Ran {len(state.execution_records)} script(s): {success_count} succeeded, "
            f"{blocked_count} blocked, {skipped_count} skipped, {failed_count} failed."
        ),
        artifact_paths=[record.script_path for record in state.execution_records],
    )


def skill_diagnose_execution(state: WorkflowState) -> SkillRecord:
    notes = build_diagnostic_notes(state)
    state.diagnostic_notes = notes
    state.diagnostics_complete = True
    return SkillRecord(
        name="diagnose_execution",
        agent="Executor",
        phase="Phase B",
        status="success",
        summary=(
            f"Generated {len(notes)} diagnostic note(s) about environment gaps, skipped stages, "
            f"and blocked dependencies."
        ),
        artifact_paths=[],
    )


def skill_match_outputs(state: WorkflowState) -> SkillRecord:
    state.comparison = compare_manifests(
        require(state.paper_manifest, "paper manifest"),
        require(state.package_manifest, "package manifest"),
        state.execution_records,
    )
    summary = state.comparison.summary
    return SkillRecord(
        name="match_outputs",
        agent="Reporter",
        phase="Phase B",
        status="success",
        summary=(
            f"Computed verdict `{summary.verdict}` with numeric/table/figure rates "
            f"{summary.numeric_match_rate:.1%}/{summary.table_match_rate:.1%}/{summary.figure_match_rate:.1%}."
        ),
        artifact_paths=[],
    )


def skill_write_report(state: WorkflowState) -> SkillRecord:
    state.report_markdown, state.report_html = render_reports(
        output_dir=state.output_path,
        paper=require(state.paper_manifest, "paper manifest"),
        package=require(state.package_manifest, "package manifest"),
        sandbox=require(state.sandbox_manifest, "sandbox manifest"),
        execution_records=state.execution_records,
        comparison=require(state.comparison, "comparison bundle"),
        agent_trace=[],
        skill_trace=state.skill_trace,
        diagnostic_notes=state.diagnostic_notes,
        screening=state.screening_report,
    )
    state.report_written = True
    return SkillRecord(
        name="write_report",
        agent="Reporter",
        phase="Phase C",
        status="success",
        summary="Rendered Markdown and HTML reports from the workflow state.",
        artifact_paths=[str(state.report_markdown), str(state.report_html)],
    )


def build_diagnostic_notes(state: WorkflowState) -> list[str]:
    package_manifest = require(state.package_manifest, "package manifest")
    execution_by_path = {record.script_path: record for record in state.execution_records}
    notes: list[str] = []

    if not require(state.raw_package_manifest, "raw package manifest").environment_files:
        notes.append(
            "No supported environment manifest was detected in the package; reproducibility may depend on "
            "inline installation calls or machine-specific preinstalled software."
        )
    if not comparable_table_artifacts(package_manifest) and not comparable_figure_artifacts(package_manifest):
        notes.append(
            "No output-like tables or figures were detected after execution; static inputs such as `data/`, "
            "README files, and environment manifests were excluded from comparison."
        )

    for record in state.execution_records:
        script_name = Path(record.script_path).name
        if record.language == "stata" and record.status == "skipped":
            notes.append(
                f"`{script_name}` was skipped because no Stata executor was configured. Set `--stata-bin` or "
                "`REPLICATION_MANAGER_STATA_BIN` to execute `.do` files."
            )
        if record.status != "blocked" or not record.message:
            continue

        missing_inputs = parse_missing_inputs(record.message)
        producers = find_producer_scripts(missing_inputs, package_manifest.scripts, exclude_path=record.script_path)
        if producers:
            producer_labels = [
                f"`{Path(path).name}` ({execution_by_path.get(path).status if path in execution_by_path else 'not run'})"
                for path in producers
            ]
            notes.append(
                f"`{script_name}` is blocked on {', '.join(f'`{item}`' for item in missing_inputs)}; "
                f"those paths are referenced in {', '.join(producer_labels)}."
            )
        else:
            notes.append(
                f"`{script_name}` is blocked on {', '.join(f'`{item}`' for item in missing_inputs)} and "
                "the workflow could not identify an upstream producer script."
            )

    return dedupe_notes(notes)


def parse_missing_inputs(message: str) -> list[str]:
    prefix = "Missing required inputs: "
    if not message.startswith(prefix):
        return []
    return [item.strip() for item in message[len(prefix) :].split(",") if item.strip()]


def find_producer_scripts(
    missing_inputs: list[str],
    scripts: list,
    *,
    exclude_path: str,
) -> list[str]:
    producers: list[str] = []
    for script in scripts:
        if script.path == exclude_path:
            continue
        text = read_text_safely(Path(script.path))
        if any(candidate in text for candidate in missing_inputs):
            producers.append(script.path)
    return producers


def dedupe_notes(notes: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for note in notes:
        if note in seen:
            continue
        seen.add(note)
        unique.append(note)
    return unique


def persist_artifacts(state: WorkflowState) -> None:
    if state.paper_manifest is not None:
        write_json(state.artifacts_dir / "paper_manifest.json", state.paper_manifest)
    if state.raw_package_manifest is not None:
        write_json(state.artifacts_dir / "raw_package_manifest.json", state.raw_package_manifest)
    if state.sandbox_manifest is not None:
        write_json(state.artifacts_dir / "sandbox_manifest.json", state.sandbox_manifest)
    if state.package_manifest is not None:
        write_json(state.artifacts_dir / "package_manifest.json", state.package_manifest)
    if state.execution_complete:
        write_json(state.artifacts_dir / "execution_manifest.json", state.execution_records)
    if state.comparison is not None:
        write_json(state.artifacts_dir / "comparison.json", state.comparison)
    write_json(state.artifacts_dir / "skill_trace.json", state.skill_trace)
    write_json(state.artifacts_dir / "diagnostic_notes.json", state.diagnostic_notes)


def finalize_workflow(state: WorkflowState) -> None:
    if state.comparison is None:
        raise RuntimeError("Workflow did not reach the comparison stage.")
    if state.sandbox_manifest is None or state.package_manifest is None or state.paper_manifest is None:
        raise RuntimeError("Workflow did not materialize the required state before finalization.")

    state.agent_trace = build_agent_trace(skill_trace=state.skill_trace, diagnostic_notes=state.diagnostic_notes)
    state.report_markdown, state.report_html = render_reports(
        output_dir=state.output_path,
        paper=state.paper_manifest,
        package=state.package_manifest,
        sandbox=state.sandbox_manifest,
        execution_records=state.execution_records,
        comparison=state.comparison,
        agent_trace=state.agent_trace,
        skill_trace=state.skill_trace,
        diagnostic_notes=state.diagnostic_notes,
        screening=state.screening_report,
    )
    write_json(state.artifacts_dir / "agent_trace.json", state.agent_trace)
    persist_artifacts(state)

    state.summary_json = state.output_path / "summary.json"
    write_json(
        state.summary_json,
        {
            "paper_title": state.paper_manifest.title,
            "paper_source": state.paper_manifest.source,
            "package_source": state.package_manifest.source,
            "sandbox_enabled": state.sandbox_manifest.enabled,
            "sandbox_root": state.sandbox_manifest.root,
            "verdict": state.comparison.summary.verdict,
            "numeric_match_rate": state.comparison.summary.numeric_match_rate,
            "table_match_rate": state.comparison.summary.table_match_rate,
            "figure_match_rate": state.comparison.summary.figure_match_rate,
            "dependency_bootstrap_steps": len(state.sandbox_manifest.install_records),
            "agents": [agent.name for agent in state.agent_trace],
            "skills": [skill.name for skill in state.skill_trace],
            "diagnostic_notes": state.diagnostic_notes,
            "report_markdown": str(state.report_markdown),
            "report_html": str(state.report_html),
        },
    )


def require(value, label: str):
    if value is None:
        raise RuntimeError(f"Workflow is missing {label}.")
    return value
