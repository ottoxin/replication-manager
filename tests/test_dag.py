from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from replication_manager.dag import (
    analyze_script_io,
    build_dependency_graph,
    get_execution_order,
    topological_sort,
)
from replication_manager.models import ScriptRecord


class DagTests(unittest.TestCase):
    def test_detects_python_io(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "analysis.py"
            script.write_text(
                "import pandas as pd\n"
                "df = pd.read_csv('data/input.csv')\n"
                "df.to_csv('output/results.csv')\n"
            )
            record = ScriptRecord(path=str(script), language="python", priority=1)
            inputs, outputs = analyze_script_io(record, Path(tmp))
            self.assertIn("data/input.csv", inputs)
            self.assertIn("output/results.csv", outputs)

    def test_detects_r_io(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "analysis.R"
            script.write_text(
                'd <- read.csv("data/input.csv")\n'
                'write.csv(d, "output/table1.csv")\n'
                'ggsave("output/figure1.png")\n'
            )
            record = ScriptRecord(path=str(script), language="r", priority=1)
            inputs, outputs = analyze_script_io(record, Path(tmp))
            self.assertIn("data/input.csv", inputs)
            self.assertIn("output/table1.csv", outputs)
            self.assertIn("output/figure1.png", outputs)

    def test_detects_stata_io(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "analysis.do"
            script.write_text(
                'use "data/survey.dta"\n'
                'outreg2 using "output/table1.tex"\n'
            )
            record = ScriptRecord(path=str(script), language="stata", priority=1)
            inputs, outputs = analyze_script_io(record, Path(tmp))
            self.assertIn("data/survey.dta", inputs)
            self.assertIn("output/table1.tex", outputs)

    def test_builds_dependency_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            s1 = Path(tmp) / "01_clean.py"
            s1.write_text("df.to_csv('output/clean.csv')\n")
            s2 = Path(tmp) / "02_analyze.py"
            s2.write_text("df = pd.read_csv('output/clean.csv')\ndf.to_csv('output/results.csv')\n")
            s3 = Path(tmp) / "03_plot.py"
            s3.write_text("df = pd.read_csv('output/results.csv')\ndf.to_csv('output/plot_data.csv')\n")

            scripts = [
                ScriptRecord(path=str(s3), language="python", priority=1),
                ScriptRecord(path=str(s1), language="python", priority=0),
                ScriptRecord(path=str(s2), language="python", priority=1),
            ]
            graph = build_dependency_graph(scripts, Path(tmp))
            self.assertIn(str(s1), graph[str(s2)])
            self.assertIn(str(s2), graph[str(s3)])
            self.assertEqual(graph[str(s1)], [])

    def test_topological_sort_respects_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            s1 = Path(tmp) / "01_clean.py"
            s1.write_text("df.to_csv('output/clean.csv')\n")
            s2 = Path(tmp) / "02_analyze.py"
            s2.write_text("df = pd.read_csv('output/clean.csv')\n")

            scripts = [
                ScriptRecord(path=str(s2), language="python", priority=1),
                ScriptRecord(path=str(s1), language="python", priority=0),
            ]
            ordered = topological_sort(scripts, Path(tmp))
            paths = [s.path for s in ordered]
            self.assertLess(paths.index(str(s1)), paths.index(str(s2)))

    def test_handles_circular_deps_gracefully(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            s1 = Path(tmp) / "a.py"
            s1.write_text("pd.read_csv('b_out.csv')\ndf.to_csv('a_out.csv')\n")
            s2 = Path(tmp) / "b.py"
            s2.write_text("pd.read_csv('a_out.csv')\ndf.to_csv('b_out.csv')\n")

            scripts = [
                ScriptRecord(path=str(s1), language="python", priority=1),
                ScriptRecord(path=str(s2), language="python", priority=1),
            ]
            ordered = get_execution_order(scripts, Path(tmp))
            self.assertEqual(len(ordered), 2)


class IntegrationTests(unittest.TestCase):
    def test_multifile_r_pipeline_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            s1 = root / "master.R"
            s1.write_text('source("01_clean.R")\nsource("02_analyze.R")\n')
            s2 = root / "01_clean.R"
            s2.write_text('d <- read.csv("data/raw.csv")\nwrite.csv(d, "data/clean.csv")\n')
            s3 = root / "02_analyze.R"
            s3.write_text('d <- read.csv("data/clean.csv")\nwrite.csv(d, "output/results.csv")\n')

            scripts = [
                ScriptRecord(path=str(s3), language="r", priority=2),
                ScriptRecord(path=str(s1), language="r", priority=0),
                ScriptRecord(path=str(s2), language="r", priority=1),
            ]
            ordered = get_execution_order(scripts, root)
            paths = [s.path for s in ordered]
            self.assertLess(paths.index(str(s2)), paths.index(str(s3)))


if __name__ == "__main__":
    unittest.main()
