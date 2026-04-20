from __future__ import annotations

import tempfile
import unittest
import zipfile
import json
from pathlib import Path

from replication_manager.compare import compare_manifests
from replication_manager.paper import extract_paper_manifest
from replication_manager.models import FigureArtifact, FigureClaim, PackageManifest, PaperManifest, SandboxManifest, ScriptRecord, TableArtifact
from replication_manager.package import inspect_package, materialize_package
from replication_manager.pipeline import run_pipeline
from replication_manager.runner import execute_scripts


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class PaperParsingTests(unittest.TestCase):
    def test_extracts_tables_figures_and_claims(self) -> None:
        manifest = extract_paper_manifest(FIXTURES / "sample_paper.txt")
        self.assertEqual(manifest.title, "A Minimal Replication Paper")
        self.assertEqual(len(manifest.tables), 1)
        self.assertEqual(manifest.tables[0].number, "1")
        self.assertEqual(len(manifest.figures), 1)
        self.assertGreaterEqual(len(manifest.numeric_claims), 7)

    def test_ignores_page_markers_and_prose_mentions_of_tables_and_figures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paper_path = Path(temp_dir) / "paper.txt"
            paper_path.write_text(
                "\n".join(
                    [
                        "===== PAGE 1 =====",
                        "A Real Paper Title",
                        "",
                        "Table 1. Main Results",
                        "1 -0.500 0.100 100",
                        "",
                        "Table 2 summarizes the robustness checks in the text.",
                        "",
                        "Figure 1. Main Funnel",
                        "",
                        "Figure 2 presents the policy timing in the discussion.",
                    ]
                ),
                encoding="utf-8",
            )
            manifest = extract_paper_manifest(paper_path)
            self.assertEqual(manifest.title, "A Real Paper Title")
            self.assertEqual(len(manifest.tables), 1)
            self.assertEqual(manifest.tables[0].title, "Main Results")
            self.assertEqual(len(manifest.figures), 1)
            self.assertEqual(manifest.figures[0].caption, "Main Funnel")

    def test_extracts_split_pdf_title_after_author_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paper_path = Path(temp_dir) / "paper.txt"
            paper_path.write_text(
                "\n".join(
                    [
                        "===== PAGE 1 =====",
                        "Jennifer Pan",
                        "Xu Xu",
                        "Yiqing Xu",
                        "June, 2023",
                        "Working Paper No. wp2044",
                        "Disguised Repression: Targeting Opponents with",
                        "Non-Political Crimes to Undermine Dissent",
                    ]
                ),
                encoding="utf-8",
            )
            manifest = extract_paper_manifest(paper_path)
            self.assertEqual(
                manifest.title,
                "Disguised Repression: Targeting Opponents with Non-Political Crimes to Undermine Dissent",
            )

    def test_extracts_title_after_journal_header_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paper_path = Path(temp_dir) / "paper.txt"
            paper_path.write_text(
                "\n".join(
                    [
                        "===== PAGE 1 =====",
                        "Political Analysis (2026), 0, 1-9",
                        "doi:10.1017/pan.2026.10038",
                        "LETTER",
                        "From Faces to Politics: Vision-Language Models",
                        "(Sometimes) Link Visual Demographic Characteristics",
                        "to Ideological Labels",
                    ]
                ),
                encoding="utf-8",
            )
            manifest = extract_paper_manifest(paper_path)
            self.assertEqual(
                manifest.title,
                "From Faces to Politics: Vision-Language Models (Sometimes) Link Visual Demographic Characteristics to Ideological Labels",
            )

    def test_normalizes_ocr_spaced_table_and_figure_titles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paper_path = Path(temp_dir) / "paper.txt"
            paper_path.write_text(
                "\n".join(
                    [
                        "A Minimal Replication Paper",
                        "",
                        "Table 3. S ELF -CENSORSHIP",
                        "0.125 0.250",
                        "",
                        "Figure 1. W EIBO POSTS CITING DISSIDENTS ’ NAMES BY CRIME TYPES",
                    ]
                ),
                encoding="utf-8",
            )
            manifest = extract_paper_manifest(paper_path)
            self.assertEqual(manifest.tables[0].title, "SELF-CENSORSHIP")
            self.assertEqual(manifest.figures[0].caption, "WEIBO POSTS CITING DISSIDENTS' NAMES BY CRIME TYPES")

    def test_filters_small_scale_numbers_from_claims(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paper_path = Path(temp_dir) / "paper.txt"
            paper_path.write_text(
                "\n".join(
                    [
                        "A Minimal Replication Paper",
                        "",
                        "Table 2. MAIN OUTCOME QUESTIONS",
                        "Scale 1 to 5 and 0 to 1",
                        "",
                        "The reproducibility rate is 94.4%.",
                    ]
                ),
                encoding="utf-8",
            )
            manifest = extract_paper_manifest(paper_path)
            raws = [claim.raw for claim in manifest.numeric_claims]
            self.assertIn("94.4%", raws)
            self.assertNotIn("1", raws)
            self.assertNotIn("5", raws)
            self.assertNotIn("0", raws)

    def test_skips_section_headings_metadata_and_reference_page_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paper_path = Path(temp_dir) / "paper.txt"
            paper_path.write_text(
                "\n".join(
                    [
                        "===== PAGE 1 =====",
                        "This is an Open Access article, distributed under the terms of the Creative Commons Attribution licence.",
                        "licenses/by/4.0), which permitsunrestricted re-use, distribution and reproduction,providedthe original article is properlycited.",
                        "2.1. Main Study Design",
                        "We replicated our main analysis using GPT-4o-2024-11-20.",
                        "We generated 50 completions for each image/prompt combination.",
                        "3.1. Main Analysis",
                        "References",
                        "Gallegos, I. O., et al. 2024. “Bias and Fairness in Large Language Models: A Survey.” Computational Linguistics 50 (3): 1097–1179.",
                        "Karras, T., S. Laine, and T. Aila. 2019. “A Style-Based Generator Architecture for Generative Adversarial Networks.” Proceedings 4401–4410.",
                    ]
                ),
                encoding="utf-8",
            )
            manifest = extract_paper_manifest(paper_path)
            raws = [claim.raw for claim in manifest.numeric_claims]
            self.assertIn("50", raws)
            self.assertNotIn("2.1", raws)
            self.assertNotIn("3.1", raws)
            self.assertNotIn("4.0", raws)
            self.assertNotIn("11", raws)
            self.assertNotIn("20", raws)
            self.assertNotIn("1097", raws)
            self.assertNotIn("4401", raws)


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
            self.assertEqual([agent.name for agent in result.agent_trace], [
                "Coordinator",
                "Executor",
                "Reporter",
                "Analyst",
            ])
            self.assertEqual([skill.name for skill in result.skill_trace], [
                "intake_sources",
                "profile_paper",
                "inspect_package",
                "prepare_workspace",
                "screen_package",
                "execute_package",
                "diagnose_execution",
                "match_outputs",
                "analyze_results",
                "write_report",
            ])
            self.assertGreaterEqual(len(result.sandbox_manifest.install_records), 1)
            self.assertTrue(
                any(item.label.startswith("pip-install-requirements") for item in result.sandbox_manifest.install_records)
            )
            self.assertTrue(result.execution_records[0].command[0].endswith("/.venv/bin/python"))
            self.assertEqual(result.diagnostic_notes, [])

            runtime_path = Path(result.package_manifest.root) / "outputs" / "runtime.json"
            runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
            self.assertTrue(runtime["python"].endswith("/.venv/bin/python"))

    def test_package_materialization_ignores_macosx_wrapper_and_uses_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "wrapped.zip"
            with zipfile.ZipFile(zip_path, "w") as handle:
                handle.writestr("Replication/code/test.R", "cat('ok')\n")
                handle.writestr("__MACOSX/Replication/._test.R", "junk")

            package_input, package_root = materialize_package(
                source=str(zip_path),
                inputs_dir=temp_path / "inputs",
                workspace_dir=temp_path / "workspace",
            )
            manifest = inspect_package(package_input, package_root)
            self.assertEqual(package_root.name, "Replication")
            self.assertEqual(len(manifest.scripts), 1)
            self.assertTrue(manifest.scripts[0].path.endswith("Replication/code/test.R"))

    def test_runner_blocks_script_when_required_inputs_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_root = temp_path / "Replication"
            (package_root / "code").mkdir(parents=True)
            script_path = package_root / "code" / "2_plots.R"
            script_path.write_text('d <- read.table("output/plotstd_attrepdis.txt")\n', encoding="utf-8")

            records = execute_scripts(
                scripts=[ScriptRecord(path=str(script_path), language="r", priority=0)],
                package_root=package_root,
                logs_dir=temp_path / "logs",
                execute=True,
                timeout_seconds=60,
                sandbox=SandboxManifest(
                    enabled=False,
                    root=str(temp_path / "sandbox"),
                    project_root=str(package_root),
                    home_dir=str(temp_path),
                    temp_dir=str(temp_path / "tmp"),
                ),
            )
            self.assertEqual(records[0].status, "blocked")
            self.assertIn("output/plotstd_attrepdis.txt", records[0].message)

    def test_package_inspection_uses_script_comments_to_label_generated_figures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_root = temp_path / "Replication"
            (package_root / "code").mkdir(parents=True)
            (package_root / "graphs").mkdir()
            script_path = package_root / "code" / "3_weibo.R"
            script_path.write_text(
                "\n".join(
                    [
                        "## -----Figure 5. Calls for Critics' Release-----",
                        "# Figure 5a: Monthly release support",
                        'ggsave("./graphs/fg_rlsprop.pdf", width = 10, height = 7)',
                    ]
                ),
                encoding="utf-8",
            )
            (package_root / "graphs" / "fg_rlsprop.pdf").write_text("fake-pdf", encoding="utf-8")

            manifest = inspect_package(package_root, package_root)
            self.assertEqual(len(manifest.figure_artifacts), 1)
            self.assertIn("Calls for Critics' Release", manifest.figure_artifacts[0].label)
            self.assertIn("Monthly release support", manifest.figure_artifacts[0].label)

    def test_package_inspection_detects_codeocean_environment_and_shell_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_root = temp_path / "capsule"
            (package_root / ".codeocean").mkdir(parents=True)
            (package_root / "code").mkdir()
            (package_root / ".codeocean" / "environment.json").write_text(
                '{"installers":{"rcran":{"packages":[{"name":"tidyverse"}]}}}',
                encoding="utf-8",
            )
            (package_root / "code" / "run.sh").write_text("#!/bin/bash\nRscript 01_Main.R\n", encoding="utf-8")

            manifest = inspect_package(package_root, package_root)
            self.assertTrue(any(path.endswith(".codeocean/environment.json") for path in manifest.environment_files))
            self.assertTrue(any(item.language == "shell" and item.path.endswith("run.sh") for item in manifest.scripts))

    def test_pipeline_surfaces_upstream_blockers_in_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            paper_path = temp_path / "paper.txt"
            paper_path.write_text("A Minimal Replication Paper\n", encoding="utf-8")

            package_root = temp_path / "Replication"
            (package_root / "code").mkdir(parents=True)
            (package_root / "code" / "1_reg.do").write_text(
                'outreg2 using "output/plotstd_attrepdis.txt", replace\n',
                encoding="utf-8",
            )
            (package_root / "code" / "2_plots.R").write_text(
                'd <- read.table("output/plotstd_attrepdis.txt")\n',
                encoding="utf-8",
            )

            result = run_pipeline(
                paper_source=str(paper_path),
                package_source=str(package_root),
                output_dir=temp_path / "run",
                execute=True,
                sandbox=False,
                install_dependencies=False,
                timeout_seconds=30,
            )

            self.assertTrue(any("No supported environment manifest" in note for note in result.diagnostic_notes))
            self.assertTrue(any("no Stata executor was configured" in note for note in result.diagnostic_notes))
            self.assertTrue(any("blocked on" in note and "1_reg.do" in note for note in result.diagnostic_notes))

    def test_pipeline_runs_codeocean_style_package_with_local_mount_shim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            paper_path = temp_path / "paper.txt"
            paper_path.write_text(
                "\n".join(
                    [
                        "From Faces to Politics",
                        "",
                        "Table 1. Main Results",
                        "0.55 0.11",
                        "",
                        "Figure 1. Study Design",
                    ]
                ),
                encoding="utf-8",
            )

            package_root = temp_path / "capsule"
            (package_root / ".codeocean").mkdir(parents=True)
            (package_root / "code").mkdir()
            (package_root / "data").mkdir()
            (package_root / ".codeocean" / "environment.json").write_text(
                '{"installers":{"rcran":{"packages":[]}}}',
                encoding="utf-8",
            )
            (package_root / "data" / "input.csv").write_text("estimate,se\n0.55,0.11\n", encoding="utf-8")
            (package_root / "code" / "run.sh").write_text(
                "\n".join(
                    [
                        "#!/bin/bash",
                        "Rscript 01_Main.R",
                        "cp -r 03_output/* ../results/",
                    ]
                ),
                encoding="utf-8",
            )
            (package_root / "code" / "01_Main.R").write_text(
                "\n".join(
                    [
                        'd <- read.csv("/data/input.csv")',
                        'dir.create("03_output/02_tables", recursive = TRUE, showWarnings = FALSE)',
                        'dir.create("03_output/01_figures", recursive = TRUE, showWarnings = FALSE)',
                        'write.table(d, file = "03_output/02_tables/Table_1.tex", row.names = FALSE, col.names = TRUE)',
                        'file.create("03_output/01_figures/Figure_1.png")',
                    ]
                ),
                encoding="utf-8",
            )

            result = run_pipeline(
                paper_source=str(paper_path),
                package_source=str(package_root),
                output_dir=temp_path / "run",
                execute=True,
                timeout_seconds=60,
            )

            self.assertEqual(len(result.execution_records), 1)
            self.assertEqual(result.execution_records[0].status, "success")
            self.assertEqual(result.execution_records[0].language, "shell")
            self.assertEqual(result.comparison.summary.verdict, "fully reproducible")
            self.assertTrue(any("Code Ocean-style package" in note for note in result.sandbox_manifest.notes))
            matched_paths = [match.artifact_path for match in result.comparison.numeric_matches if match.matched]
            self.assertTrue(all(path and ("/results/" in path or "/03_output/" in path) for path in matched_paths))


class ComparisonTests(unittest.TestCase):
    def test_figure_number_bonus_requires_exact_reference_match(self) -> None:
        paper = PaperManifest(
            source="paper.pdf",
            title="Example",
            line_count=1,
            figures=[FigureClaim(number="1", caption="Replication Funnel", source="Line 1")],
        )
        package = PackageManifest(
            source="package.zip",
            root="package",
            figure_artifacts=[
                FigureArtifact(path="graphs/figure_a11.pdf", label="Figure A11. Appendix Funnel", extension=".pdf"),
                FigureArtifact(path="graphs/figure_1.pdf", label="Figure 1. Replication Funnel", extension=".pdf"),
            ],
        )

        comparison = compare_manifests(paper, package)
        self.assertTrue(comparison.figure_matches[0].matched)
        self.assertEqual(comparison.figure_matches[0].artifact_path, "graphs/figure_1.pdf")

    def test_figure_reference_bonus_does_not_override_zero_caption_overlap(self) -> None:
        paper = PaperManifest(
            source="paper.pdf",
            title="Example",
            line_count=1,
            figures=[FigureClaim(number="7", caption="Perceived morality of KOL", source="Line 1")],
        )
        package = PackageManifest(
            source="package.zip",
            root="package",
            figure_artifacts=[
                FigureArtifact(
                    path="graphs/figure_7a.pdf",
                    label="Figure 7. Stance toward critics | Figure 7a: Non-political crimes",
                    extension=".pdf",
                )
            ],
        )

        comparison = compare_manifests(paper, package)
        self.assertFalse(comparison.figure_matches[0].matched)

    def test_appendix_figure_reference_penalizes_caption_only_overlap(self) -> None:
        paper = PaperManifest(
            source="paper.pdf",
            title="Example",
            line_count=1,
            figures=[FigureClaim(number="4", caption="Word frequency regarding critics pre-and post-arrest", source="Line 1")],
        )
        package = PackageManifest(
            source="package.zip",
            root="package",
            figure_artifacts=[
                FigureArtifact(
                    path="graphs/fg_wgqodds.pdf",
                    label="Figure A12. Word frequency regarding critics pre-and post-arrest | Figure A12b: Wang Gongquan Odds",
                    extension=".pdf",
                )
            ],
        )

        comparison = compare_manifests(paper, package)
        self.assertFalse(comparison.figure_matches[0].matched)

    def test_comparison_ignores_input_data_when_outputs_are_absent(self) -> None:
        paper = extract_paper_manifest(FIXTURES / "sample_paper.txt")
        package = PackageManifest(
            source="package.zip",
            root="package",
            table_artifacts=[
                TableArtifact(
                    path="package/data/source.csv",
                    label="raw input data",
                    row_count=2,
                    column_count=2,
                    numeric_values=[1.23, 0.45, 100.0],
                    numeric_raws=["1.23", "0.45", "100"],
                )
            ],
        )

        comparison = compare_manifests(paper, package)
        self.assertEqual(comparison.summary.numeric_match_rate, 0.0)
        self.assertEqual(comparison.summary.table_match_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
