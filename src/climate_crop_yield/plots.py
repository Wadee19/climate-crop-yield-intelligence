from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PASTEL_10 = [
    "#ff9999",
    "#66b3ff",
    "#99ff99",
    "#ffcc99",
    "#c2c2f0",
    "#ffb3e6",
    "#c4e17f",
    "#f7786b",
    "#aec6cf",
    "#ffcc00",
]


def set_project_style() -> None:
    sns.set_theme(style="whitegrid")
    plt.rcParams["figure.figsize"] = (11, 6)
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.labelsize"] = 11


def label_bars(ax, decimals: int = 2) -> None:
    for patch in ax.patches:
        height = patch.get_height()
        if pd.isna(height):
            continue
        ax.annotate(
            f"{height:.{decimals}f}",
            (patch.get_x() + patch.get_width() / 2, height),
            ha="center",
            va="bottom" if height >= 0 else "top",
            fontsize=9,
            xytext=(0, 3 if height >= 0 else -3),
            textcoords="offset points",
        )
