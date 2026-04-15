from __future__ import annotations

import tempfile
import unittest
import zipfile
import json
from pathlib import Path

from replication_manager.paper import extract_paper_manifest
from replication_manager.pipeline import run_pipeline


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class PaperParsingTests(unittest.TestCase):
    def test_extracts_tables_figures_and_claims(self) -> None:
        manifest = extract_paper_manifest(FIXTURES / "sample_paper.txt")
        self.assertEqual(manifest.title, "A Minimal Replication Paper")
        self.assertEqual(len(manifest.tables), 1)
        self.assertEqual(manifest.tables[0].number, "1")
        self.assertEqual(len(manifest.figures), 1)
        self.assertGreaterEqual(len(manifest.numeric_claims), 8)


class PipelineTests(unittest.TestCase):
    def test_end_to_end_run_with_zip_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "sample_package.zip"
            source_dir = FIXTURES / "sample_package"

            with zipfile.ZipFile(zip_path, "w") as handle:
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        handle.write(file_path, file_path.relative_to(source_dir))

            result = run_pipeline(
                paper_source=str(FIXTURES / "sample_paper.txt"),
                package_source=str(zip_path),
                output_dir=temp_path / "run",
                execute=True,
                timeout_seconds=60,
            )

            self.assertTrue(result.report_markdown.exists())
            self.assertTrue(result.report_html.exists())
            self.assertEqual(result.comparison.summary.verdict, "fully reproducible")
            self.assertGreaterEqual(result.comparison.summary.numeric_match_rate, 0.8)
            self.assertEqual(result.comparison.summary.table_match_rate, 1.0)
            self.assertEqual(result.comparison.summary.figure_match_rate, 1.0)
            self.assertTrue(result.sandbox_manifest.enabled)
            self.assertGreaterEqual(len(result.sandbox_manifest.install_records), 1)
            self.assertTrue(
                any(item.label.startswith("pip-install-requirements") for item in result.sandbox_manifest.install_records)
            )
            self.assertTrue(result.execution_records[0].command[0].endswith("/.venv/bin/python"))

            runtime_path = Path(result.package_manifest.root) / "outputs" / "runtime.json"
            runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
            self.assertTrue(runtime["python"].endswith("/.venv/bin/python"))


if __name__ == "__main__":
    unittest.main()
