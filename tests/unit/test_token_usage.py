"""Tests for src/utils/token_usage.py — CSV loading and plot utilities."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.utils.token_usage import load_usage_stats, plot_usage


class TestLoadUsageStats:
    def test_missing_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            df = load_usage_stats("nonexistent_model", tmpdir)
        assert df.empty

    def test_empty_usage_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            usage_dir = Path(tmpdir) / "my_model" / "usage"
            usage_dir.mkdir(parents=True)
            df = load_usage_stats("my_model", tmpdir)
        assert df.empty

    def test_single_csv_loaded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            usage_dir = Path(tmpdir) / "my_model" / "usage"
            usage_dir.mkdir(parents=True)
            csv_path = usage_dir / "run1.csv"
            pd.DataFrame({"input_filename": ["pt1.txt"], "total_tokens": [1234]}).to_csv(csv_path, index=False)

            df = load_usage_stats("my_model", tmpdir)

        assert len(df) == 1
        assert df["total_tokens"].iloc[0] == 1234

    def test_multiple_csvs_concatenated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            usage_dir = Path(tmpdir) / "my_model" / "usage"
            usage_dir.mkdir(parents=True)
            for i in range(3):
                pd.DataFrame({"input_filename": [f"pt{i}.txt"], "total_tokens": [100 * i]}).to_csv(
                    usage_dir / f"run{i}.csv", index=False
                )

            df = load_usage_stats("my_model", tmpdir)

        assert len(df) == 3
        assert set(df["input_filename"]) == {"pt0.txt", "pt1.txt", "pt2.txt"}


class TestPlotUsage:
    def test_empty_dataframe_returns_early(self, capsys):
        plot_usage(pd.DataFrame())
        captured = capsys.readouterr()
        assert "No usage data" in captured.out

    def test_missing_total_tokens_column_returns_early(self, capsys):
        df = pd.DataFrame({"input_filename": ["pt1.txt"], "other_col": [999]})
        plot_usage(df)
        captured = capsys.readouterr()
        assert "No usage data" in captured.out

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.subplots")
    @patch("matplotlib.pyplot.tight_layout")
    @patch("matplotlib.pyplot.xticks")
    def test_plot_with_output_path_saves_file(self, mock_xticks, mock_tight, mock_subplots, mock_savefig, capsys):
        mock_ax = MagicMock()
        mock_subplots.return_value = (MagicMock(), mock_ax)
        df = pd.DataFrame({"input_filename": ["pt1.txt"], "total_tokens": [1000]})
        plot_usage(df, output_path="/tmp/test_plot.png")
        mock_savefig.assert_called_once_with("/tmp/test_plot.png")

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.subplots")
    @patch("matplotlib.pyplot.tight_layout")
    @patch("matplotlib.pyplot.xticks")
    def test_plot_without_output_path_calls_show(self, mock_xticks, mock_tight, mock_subplots, mock_show):
        mock_ax = MagicMock()
        mock_subplots.return_value = (MagicMock(), mock_ax)
        df = pd.DataFrame({"input_filename": ["pt1.txt"], "total_tokens": [1000]})
        plot_usage(df)
        mock_show.assert_called_once()
