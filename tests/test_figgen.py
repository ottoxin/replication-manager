"""Tests for the figure replication module."""

import csv
import tempfile
from pathlib import Path

import pytest

from replication_manager.figgen import (
    _extract_fig_number,
    _infer_plot_type,
    discover_source_data,
    read_source_panels,
    render_panel,
    replicate_figure,
)


def test_extract_fig_number():
    assert _extract_fig_number("SourceData_Fig1.xlsx") == "1"
    assert _extract_fig_number("SourceData_Fig2__a.csv") == "2"
    assert _extract_fig_number("SourceData_ExtFig10.xlsx") == "E10"
    assert _extract_fig_number("Supplementary_FigS5.csv") == "S5"
    assert _extract_fig_number("README.md") is None


def test_discover_prefers_xlsx(tmp_path):
    sd = tmp_path / "source_data"
    sd.mkdir()
    (sd / "SourceData_Fig1.xlsx").touch()
    csv_dir = sd / "csv"
    csv_dir.mkdir()
    (csv_dir / "SourceData_Fig1__a.csv").touch()
    (csv_dir / "SourceData_Fig1__b.csv").touch()

    result = discover_source_data(tmp_path)
    assert "1" in result
    assert len(result["1"]) == 1
    assert result["1"][0].suffix == ".xlsx"


def test_discover_falls_back_to_csv(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    (csv_dir / "SourceData_Fig3__a.csv").touch()
    (csv_dir / "SourceData_Fig3__b.csv").touch()

    result = discover_source_data(tmp_path)
    assert "3" in result
    assert len(result["3"]) == 2
    assert all(p.suffix == ".csv" for p in result["3"])


def _make_csv(path, headers, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for row in rows:
            w.writerow(row)


def test_read_csv_panels(tmp_path):
    _make_csv(tmp_path / "SourceData_Fig1__a.csv",
              ["x", "y1", "y2"],
              [[0, 1.0, 2.0], [1, 3.0, 4.0], [2, 5.0, 6.0]])
    _make_csv(tmp_path / "SourceData_Fig1__b.csv",
              ["x", "val"],
              [["cat1", 10], ["cat2", 20]])

    panels = read_source_panels(
        [tmp_path / "SourceData_Fig1__a.csv", tmp_path / "SourceData_Fig1__b.csv"],
        "1",
    )
    assert len(panels) == 2
    assert panels[0].panel_label == "a"
    assert panels[1].panel_label == "b"


def test_infer_line_plot():
    headers = ["x", "y1", "y2"]
    data = [{"x": i, "y1": i * 2, "y2": i * 3} for i in range(20)]
    assert _infer_plot_type(headers, data, "a") == "line"


def test_infer_bar_plot():
    headers = ["x", "NonAI", "AI"]
    data = [{"x": "Biology", "NonAI": 10, "AI": 20}]
    assert _infer_plot_type(headers, data, "b") == "grouped_bar"


def test_infer_boxplot():
    headers = ["x", "NonAI_median", "NonAI_Q1", "NonAI_Q3"]
    data = [{"x": "A", "NonAI_median": 5, "NonAI_Q1": 3, "NonAI_Q3": 7}]
    assert _infer_plot_type(headers, data, "c") == "boxplot"


def test_render_panel_creates_file(tmp_path):
    from replication_manager.figgen import PanelSpec

    panel = PanelSpec(
        sheet_name="a",
        figure_number="1",
        panel_label="a",
        columns=["x", "y"],
        data=[{"x": i, "y": i ** 2} for i in range(10)],
        plot_type="line",
    )
    out = tmp_path / "panel_a.png"
    result = render_panel(panel, out)
    assert result.exists()
    assert result.stat().st_size > 0


def test_replicate_figure_csv(tmp_path):
    sd = tmp_path / "source"
    sd.mkdir()
    _make_csv(sd / "SourceData_Fig1__a.csv",
              ["x", "y"],
              [[i, i * 2] for i in range(15)])

    out = tmp_path / "output"
    result = replicate_figure([sd / "SourceData_Fig1__a.csv"], "1", out)
    assert result.status == "success"
    assert len(result.output_paths) == 1
    assert Path(result.output_paths[0]).exists()
