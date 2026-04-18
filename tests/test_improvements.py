from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from replication_manager.compare import compute_image_similarity
from replication_manager.log import get_logger, set_level
from replication_manager.paper import extract_paper_manifest, merge_table_sources
from replication_manager.models import PaperTable, NumericClaim
from replication_manager.reporting import generate_suggestions, render_reports
from replication_manager.models import (
    ComparisonBundle, ComparisonSummary, ExecutionRecord,
    PackageManifest, PaperManifest, SandboxManifest,
)


class LoggingTests(unittest.TestCase):
    def test_logger_creation(self) -> None:
        log = get_logger("test")
        self.assertEqual(log.name, "replication_manager.test")

    def test_set_level(self) -> None:
        set_level("DEBUG")
        log = get_logger("test_level")
        self.assertTrue(log.isEnabledFor(10))
        set_level("INFO")


class PdfPlumberTests(unittest.TestCase):
    def test_merge_table_sources_adds_new(self) -> None:
        text_tables = [PaperTable(number="1", title="T1", body="a", numeric_claims=[])]
        plumber_tables = [PaperTable(number="2", title="T2", body="b", numeric_claims=[])]
        merged = merge_table_sources(text_tables, plumber_tables)
        self.assertEqual(len(merged), 2)
        numbers = {t.number for t in merged}
        self.assertEqual(numbers, {"1", "2"})

    def test_merge_table_sources_upgrades_existing(self) -> None:
        claim = NumericClaim(raw="0.5", value=0.5, decimals=1, context="ctx", source="T1")
        text_tables = [PaperTable(number="1", title="T1", body="old", numeric_claims=[])]
        plumber_tables = [PaperTable(number="1", title="T1", body="new", numeric_claims=[claim])]
        merged = merge_table_sources(text_tables, plumber_tables)
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged[0].numeric_claims), 1)


class SuggestionTests(unittest.TestCase):
    def test_generates_suggestion_for_failed_scripts(self) -> None:
        records = [ExecutionRecord(
            script_path="/code/test.py", language="python",
            command=["python", "test.py"], return_code=1,
            status="failed", duration_seconds=1.0,
        )]
        comparison = ComparisonBundle(
            summary=ComparisonSummary(
                verdict="not reproducible", numeric_match_rate=0.0,
                table_match_rate=0.0, figure_match_rate=0.0,
                matched_numeric_claims=0, total_numeric_claims=5,
                matched_tables=0, total_tables=1,
                matched_figures=0, total_figures=1,
            ),
        )
        sandbox = SandboxManifest(
            enabled=True, root="/sandbox", project_root="/project",
            home_dir="/home", temp_dir="/tmp",
        )
        suggestions = generate_suggestions(records, comparison, sandbox, [])
        self.assertTrue(any("test.py" in s for s in suggestions))
        self.assertTrue(any("numeric match" in s.lower() for s in suggestions))

    def test_generates_suggestion_for_blocked_scripts(self) -> None:
        records = [ExecutionRecord(
            script_path="/code/test.R", language="r",
            command=[], return_code=None,
            status="blocked", duration_seconds=0.0,
            message="Missing required inputs: output/data.csv",
        )]
        comparison = ComparisonBundle(
            summary=ComparisonSummary(
                verdict="not reproducible", numeric_match_rate=0.0,
                table_match_rate=0.0, figure_match_rate=0.0,
                matched_numeric_claims=0, total_numeric_claims=0,
                matched_tables=0, total_tables=0,
                matched_figures=0, total_figures=0,
            ),
        )
        sandbox = SandboxManifest(
            enabled=True, root="/sandbox", project_root="/project",
            home_dir="/home", temp_dir="/tmp",
        )
        suggestions = generate_suggestions(records, comparison, sandbox, [])
        self.assertTrue(any("blocked" in s.lower() for s in suggestions))

    def test_stata_skip_suggestion(self) -> None:
        records = [ExecutionRecord(
            script_path="/code/test.do", language="stata",
            command=[], return_code=None,
            status="skipped", duration_seconds=0.0,
            message="No executor available for this script type.",
        )]
        comparison = ComparisonBundle(
            summary=ComparisonSummary(
                verdict="not reproducible", numeric_match_rate=0.0,
                table_match_rate=0.0, figure_match_rate=0.0,
                matched_numeric_claims=0, total_numeric_claims=0,
                matched_tables=0, total_tables=0,
                matched_figures=0, total_figures=0,
            ),
        )
        sandbox = SandboxManifest(
            enabled=True, root="/sandbox", project_root="/project",
            home_dir="/home", temp_dir="/tmp",
        )
        suggestions = generate_suggestions(records, comparison, sandbox, [])
        self.assertTrue(any("stata" in s.lower() for s in suggestions))


class ImageHashTests(unittest.TestCase):
    def test_returns_none_when_library_missing(self) -> None:
        result = compute_image_similarity("/nonexistent/a.png", "/nonexistent/b.png")
        self.assertTrue(result is None or isinstance(result, float))


if __name__ == "__main__":
    unittest.main()
