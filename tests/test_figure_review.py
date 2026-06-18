from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from replication_manager.figure_review import review_one_figure
from replication_manager.models import FigureMatch, PackageManifest, PaperManifest


def write_agent(directory: Path, body: str) -> str:
    script = directory / "agent.py"
    script.write_text(body, encoding="utf-8")
    return f"{sys.executable} {script}"


class FigureReviewTests(unittest.TestCase):
    def _match(self) -> FigureMatch:
        return FigureMatch(
            figure_number="1",
            caption="Coefficient Plot",
            matched=True,
            artifact_path="/tmp/figure_1.png",
            score=0.8,
        )

    def _paper(self) -> PaperManifest:
        return PaperManifest(source="paper.pdf", title="Paper", line_count=1)

    def _package(self) -> PackageManifest:
        return PackageManifest(source="pkg", root="/tmp/pkg")

    def test_no_command_marks_cannot_assess(self) -> None:
        reviewed = review_one_figure(
            match=self._match(),
            paper=self._paper(),
            package=self._package(),
            paper_image_path=None,
            agent_command=None,
            timeout_seconds=5,
        )
        self.assertFalse(reviewed.matched)
        self.assertEqual(reviewed.review_status, "cannot_assess")
        self.assertIn("No local figure review agent", reviewed.review_reason)

    def test_valid_matched_json_marks_matched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            command = write_agent(
                Path(tmp),
                "import json, sys\njson.dump({'status':'matched','score':0.93,'reason':'same trend'}, sys.stdout)\n",
            )
            reviewed = review_one_figure(
                match=self._match(),
                paper=self._paper(),
                package=self._package(),
                paper_image_path="/tmp/paper.png",
                agent_command=command,
                timeout_seconds=5,
            )
        self.assertTrue(reviewed.matched)
        self.assertEqual(reviewed.review_status, "matched")
        self.assertEqual(reviewed.review_score, 0.93)
        self.assertEqual(reviewed.paper_image_path, "/tmp/paper.png")

    def test_partial_and_mismatch_do_not_count_as_matched(self) -> None:
        for status, score in [("partially_matched", 0.5), ("mismatched", 0.0)]:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                command = write_agent(
                    Path(tmp),
                    f"import json, sys\njson.dump({{'status':'{status}','score':{score},'reason':'reviewed'}}, sys.stdout)\n",
                )
                reviewed = review_one_figure(
                    match=self._match(),
                    paper=self._paper(),
                    package=self._package(),
                    paper_image_path=None,
                    agent_command=command,
                    timeout_seconds=5,
                )
                self.assertFalse(reviewed.matched)
                self.assertEqual(reviewed.review_status, status)

    def test_invalid_json_marks_cannot_assess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            command = write_agent(Path(tmp), "print('not json')\n")
            reviewed = review_one_figure(
                match=self._match(),
                paper=self._paper(),
                package=self._package(),
                paper_image_path=None,
                agent_command=command,
                timeout_seconds=5,
            )
        self.assertFalse(reviewed.matched)
        self.assertEqual(reviewed.review_status, "cannot_assess")
        self.assertIn("valid JSON", reviewed.review_reason)

    def test_nonzero_exit_marks_cannot_assess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            command = write_agent(Path(tmp), "import sys\nsys.stderr.write('failed')\nsys.exit(2)\n")
            reviewed = review_one_figure(
                match=self._match(),
                paper=self._paper(),
                package=self._package(),
                paper_image_path=None,
                agent_command=command,
                timeout_seconds=5,
            )
        self.assertFalse(reviewed.matched)
        self.assertEqual(reviewed.review_status, "cannot_assess")
        self.assertIn("exited with code 2", reviewed.review_reason)


if __name__ == "__main__":
    unittest.main()
