# Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
# Licensed under the Apache License, Version 2.0.
import os
from pathlib import Path
from typing import Optional

import pandas as pd


def load_usage_stats(model_name: str, output_dir: str) -> pd.DataFrame:
    """Load all token usage CSV files for a given model.

    Args:
        model_name: Model identifier (e.g., 'o4-mini-2025-04-16').
        output_dir: Base output directory.

    Returns:
        Concatenated DataFrame of all usage CSVs for the model.
    """
    usage_dir = Path(output_dir) / model_name / "usage"
    if not usage_dir.is_dir():
        return pd.DataFrame()

    dfs = []
    for csv_file in sorted(usage_dir.glob("*.csv")):
        df = pd.read_csv(csv_file)
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def plot_usage(df: pd.DataFrame, output_path: Optional[str] = None):
    """Plot token usage bar chart.

    Args:
        df: DataFrame with 'input_filename' and 'total_tokens' columns.
        output_path: If provided, save the figure to this path instead of showing.
    """
    import matplotlib.pyplot as plt

    if df.empty or "total_tokens" not in df.columns:
        print("No usage data to plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    x_col = "input_filename" if "input_filename" in df.columns else df.columns[0]
    ax.bar(df[x_col], df["total_tokens"])
    ax.set_xlabel("Input File")
    ax.set_ylabel("Total Tokens")
    ax.set_title("Token Usage by Input File")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path)
        print(f"Saved usage plot to {output_path}")
    else:
        plt.show()
