from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class NumericClaim:
    raw: str
    value: float
    decimals: int
    context: str
    source: str


@dataclass
class PaperTable:
    number: str
    title: str
    body: str
    numeric_claims: list[NumericClaim] = field(default_factory=list)


@dataclass
class FigureClaim:
    number: str
    caption: str
    source: str


@dataclass
class PaperManifest:
    source: str
    title: str
    line_count: int
    numeric_claims: list[NumericClaim] = field(default_factory=list)
    tables: list[PaperTable] = field(default_factory=list)
    figures: list[FigureClaim] = field(default_factory=list)


@dataclass
class ScriptRecord:
    path: str
    language: str
    priority: int


@dataclass
class TableArtifact:
    path: str
    label: str
    row_count: int
    column_count: int
    numeric_values: list[float] = field(default_factory=list)
    numeric_raws: list[str] = field(default_factory=list)


@dataclass
class FigureArtifact:
    path: str
    label: str
    extension: str


@dataclass
class PackageManifest:
    source: str
    root: str
    scripts: list[ScriptRecord] = field(default_factory=list)
    table_artifacts: list[TableArtifact] = field(default_factory=list)
    figure_artifacts: list[FigureArtifact] = field(default_factory=list)
    environment_files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ExecutionRecord:
    script_path: str
    language: str
    command: list[str]
    return_code: int | None
    status: str
    duration_seconds: float
    stdout_path: str | None = None
    stderr_path: str | None = None
    message: str | None = None


@dataclass
class BootstrapRecord:
    label: str
    language: str
    command: list[str]
    return_code: int | None
    status: str
    duration_seconds: float
    stdout_path: str | None = None
    stderr_path: str | None = None
    message: str | None = None


@dataclass
class SandboxManifest:
    enabled: bool
    root: str
    project_root: str
    home_dir: str
    temp_dir: str
    python_executable: str | None = None
    r_library_dir: str | None = None
    r_profile_path: str | None = None
    install_records: list[BootstrapRecord] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class NumericMatch:
    claim_raw: str
    claim_value: float
    claim_source: str
    matched: bool
    artifact_path: str | None = None
    artifact_value: float | None = None
    score: float = 0.0
    reason: str | None = None


@dataclass
class TableMatch:
    table_number: str
    table_title: str
    matched: bool
    artifact_path: str | None = None
    overlap_score: float = 0.0
    matched_values: int = 0
    paper_values: int = 0
    paper_body: str | None = None
    artifact_preview: str | None = None


@dataclass
class FigureMatch:
    figure_number: str
    caption: str
    matched: bool
    artifact_path: str | None = None
    score: float = 0.0
    image_similarity: float | None = None


@dataclass
class ComparisonSummary:
    verdict: str
    numeric_match_rate: float
    table_match_rate: float
    figure_match_rate: float
    matched_numeric_claims: int
    total_numeric_claims: int
    matched_tables: int
    total_tables: int
    matched_figures: int
    total_figures: int


@dataclass
class ComparisonBundle:
    summary: ComparisonSummary
    numeric_matches: list[NumericMatch] = field(default_factory=list)
    table_matches: list[TableMatch] = field(default_factory=list)
    figure_matches: list[FigureMatch] = field(default_factory=list)


@dataclass
class RunResult:
    output_dir: Path
    paper_manifest: PaperManifest
    package_manifest: PackageManifest
    sandbox_manifest: SandboxManifest
    agent_trace: list["AgentRecord"]
    skill_trace: list["SkillRecord"]
    execution_records: list[ExecutionRecord]
    comparison: ComparisonBundle
    report_markdown: Path
    report_html: Path
    summary_json: Path
    diagnostic_notes: list[str] = field(default_factory=list)


@dataclass
class AgentRecord:
    name: str
    role: str
    phase: str
    status: str
    summary: str
    artifact_paths: list[str] = field(default_factory=list)


@dataclass
class SkillRecord:
    name: str
    agent: str
    phase: str
    status: str
    summary: str
    artifact_paths: list[str] = field(default_factory=list)
