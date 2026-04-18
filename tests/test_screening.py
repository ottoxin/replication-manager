from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from replication_manager.models import (
    FigureClaim, PackageManifest, PaperManifest, ScriptRecord, FigureArtifact,
)
from replication_manager.screening import (
    classify_figure,
    classify_script,
    check_data_availability,
    estimate_compute,
    filter_reproducible_figures,
    filter_runnable_scripts,
    screen_package,
)


class ScriptClassificationTests(unittest.TestCase):
    def test_detects_gpu_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "train.py"
            script.write_text("import torch\nmodel = torch.nn.Linear(10, 5)\nmodel.to(device)\n")
            record = ScriptRecord(path=str(script), language="python", priority=1)
            result = classify_script(record, Path(tmp))
            self.assertEqual(result.category, "gpu_required")
            self.assertFalse(result.runnable)

    def test_detects_heavy_compute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "process.py"
            script.write_text("df = pd.read_csv('data.csv', chunksize=100000)\n")
            record = ScriptRecord(path=str(script), language="python", priority=1)
            result = classify_script(record, Path(tmp))
            self.assertEqual(result.category, "heavy_compute")
            self.assertFalse(result.runnable)

    def test_detects_lightweight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "simple.py"
            script.write_text("print('hello world')\n")
            record = ScriptRecord(path=str(script), language="python", priority=1)
            result = classify_script(record, Path(tmp))
            self.assertEqual(result.category, "lightweight")
            self.assertTrue(result.runnable)

    def test_detects_missing_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "analyze.py"
            script.write_text("df = pd.read_csv('data/missing_file.csv')\n")
            record = ScriptRecord(path=str(script), language="python", priority=1)
            result = classify_script(record, Path(tmp))
            self.assertEqual(result.category, "data_processing")
            self.assertFalse(result.runnable)
            self.assertIn("data/missing_file.csv", result.missing_data)


class FigureClassificationTests(unittest.TestCase):
    def test_detects_manual_figure(self) -> None:
        figure = FigureClaim(number="1", caption="Study workflow diagram", source="Line 1")
        package = PackageManifest(source="pkg", root="/tmp")
        result = classify_figure(figure, package, Path("/tmp"))
        self.assertEqual(result.category, "manual")

    def test_detects_schematic(self) -> None:
        figure = FigureClaim(number="1", caption="Schematic overview of the method", source="Line 1")
        package = PackageManifest(source="pkg", root="/tmp")
        result = classify_figure(figure, package, Path("/tmp"))
        self.assertEqual(result.category, "manual")

    def test_detects_reproducible_with_script_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "plot.py"
            script.write_text("# Generate figure_1\nplt.savefig('figure_1.png')\n")
            figure = FigureClaim(number="1", caption="Main results", source="Line 1")
            package = PackageManifest(
                source="pkg", root=tmp,
                scripts=[ScriptRecord(path=str(script), language="python", priority=1)],
            )
            result = classify_figure(figure, package, Path(tmp))
            self.assertEqual(result.category, "reproducible")

    def test_detects_reproducible_with_artifact(self) -> None:
        figure = FigureClaim(number="2", caption="Comparison plot", source="Line 5")
        package = PackageManifest(
            source="pkg", root="/tmp",
            figure_artifacts=[FigureArtifact(path="/tmp/output/figure_2.png", label="figure_2", extension=".png")],
        )
        result = classify_figure(figure, package, Path("/tmp"))
        self.assertEqual(result.category, "reproducible")


class ComputeEstimateTests(unittest.TestCase):
    def test_parses_readme_estimates(self) -> None:
        readme = "Step 1 takes ~3 CPU days\nStep 2 takes ~14 GPU days\n"
        result = estimate_compute(readme, [])
        self.assertIn("CPU", result)
        self.assertIn("GPU", result)

    def test_lightweight_estimate(self) -> None:
        from replication_manager.screening import ScriptClassification
        classes = [ScriptClassification(
            path="/tmp/a.py", language="python",
            category="lightweight", reason="ok", runnable=True,
        )]
        result = estimate_compute("", classes)
        self.assertIn("Lightweight", result)


class FilterTests(unittest.TestCase):
    def test_filter_runnable_scripts(self) -> None:
        from replication_manager.screening import ScriptClassification
        scripts = [
            ScriptRecord(path="/a.py", language="python", priority=1),
            ScriptRecord(path="/b.py", language="python", priority=1),
        ]
        classes = [
            ScriptClassification(path="/a.py", language="python", category="lightweight", reason="ok", runnable=True),
            ScriptClassification(path="/b.py", language="python", category="gpu_required", reason="gpu", runnable=False),
        ]
        filtered = filter_runnable_scripts(scripts, classes)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].path, "/a.py")

    def test_filter_reproducible_figures(self) -> None:
        from replication_manager.screening import FigureClassification
        figures = [
            FigureClaim(number="1", caption="Results", source="L1"),
            FigureClaim(number="2", caption="Workflow diagram", source="L2"),
        ]
        classes = [
            FigureClassification(number="1", caption="Results", category="reproducible", reason="ok"),
            FigureClassification(number="2", caption="Workflow diagram", category="manual", reason="schematic"),
        ]
        filtered = filter_reproducible_figures(figures, classes)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].number, "1")


class DataAvailabilityTests(unittest.TestCase):
    def test_detects_available_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data" / "input.csv").write_text("a,b\n1,2\n")
            package = PackageManifest(source="pkg", root=tmp, scripts=[])
            available, missing = check_data_availability(package, root)
            self.assertTrue(any("data/" in a for a in available))

    def test_detects_intermediate_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "result_alltime").mkdir()
            (root / "result_alltime" / "data.pkl").write_bytes(b"fake")
            package = PackageManifest(source="pkg", root=tmp, scripts=[])
            available, missing = check_data_availability(package, root)
            self.assertTrue(any("result_alltime" in a for a in available))


if __name__ == "__main__":
    unittest.main()
