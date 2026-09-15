from __future__ import annotations

import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sklearn

from climate_crop_yield.analysis import build_risk_table, yield_change_summary
from climate_crop_yield.data import build_analysis_panel
from climate_crop_yield.features import add_features, crop_temperature_sensitivity, validate_panel
from climate_crop_yield.model import fit_time_split

SUMMARY_PATH = Path("reports/tables/live_analysis_summary.json")
FIG_DIR = Path("reports/figures")
PALETTE = "Set2"


def pct(value: float) -> float:
    return round(float(value), 2)


def save_figures(
    trend: pd.DataFrame,
    sensitivity: pd.DataFrame,
    risk: pd.DataFrame,
    result,
) -> None:
    """Save README-ready figures from the same live analysis used for validation."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    # 1) Matched-country yield change. Using the same countries in both windows
    # avoids making a long-run change look larger or smaller because the sample changed.
    plt.figure(figsize=(9, 5.5))
    plot = trend.sort_values("change_pct", ascending=False)
    ax = sns.barplot(data=plot, x="crop", y="change_pct", hue="crop", palette=PALETTE, legend=False)
    ax.set_title("Matched-country median yield change, 1990–1994 vs 2019–2023")
    ax.set_xlabel("")
    ax.set_ylabel("Median yield change (%)")
    for patch, value in zip(ax.patches, plot["change_pct"]):
        ax.annotate(f"{value:.1f}%", (patch.get_x() + patch.get_width()/2, patch.get_height()),
                    ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "01_matched_yield_change.png", dpi=180, bbox_inches="tight")
    plt.close()

    # 2) Relative temperature sensitivity. Percentage units make the six crops comparable.
    plt.figure(figsize=(9, 5.5))
    plot = sensitivity.sort_values("yield_change_pct_per_1c")
    ax = sns.barplot(data=plot, x="crop", y="yield_change_pct_per_1c", hue="crop", palette=PALETTE, legend=False)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("Detrended yield association per +1°C")
    ax.set_xlabel("")
    ax.set_ylabel("Yield deviation (% of system mean per +1°C)")
    for patch, value in zip(ax.patches, plot["yield_change_pct_per_1c"]):
        ax.annotate(f"{value:.2f}%", (patch.get_x() + patch.get_width()/2, patch.get_height()),
                    ha="center", va="top" if value < 0 else "bottom",
                    xytext=(0, -4 if value < 0 else 3), textcoords="offset points", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "03_temperature_sensitivity_relative.png", dpi=180, bbox_inches="tight")
    plt.close()

    # 3) Screening plot. This is a prioritization screen, not a loss probability.
    plt.figure(figsize=(10, 6.5))
    sns.scatterplot(
        data=risk,
        x="warming_penalty_pct_per_c",
        y="detrended_yield_std_pct",
        hue="crop",
        size="screening_score",
        sizes=(25, 180),
        palette=PALETTE,
        alpha=0.65,
    )
    for _, row in risk.head(8).iterrows():
        plt.annotate(
            f"{row['Entity']} – {row['crop']}",
            (row["warming_penalty_pct_per_c"], row["detrended_yield_std_pct"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )
    plt.title("Climate screening — where should I investigate first?")
    plt.xlabel("Negative detrended temperature association (% yield per +1°C)")
    plt.ylabel("Detrended yield volatility (%)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "07_screening_priority.png", dpi=180, bbox_inches="tight")
    plt.close()

    # 4) Model ablation and baselines. This answers what climate adds, what fertilizer adds,
    # and whether either beats a strong recent-history baseline.
    m = result.metrics
    model_table = pd.DataFrame(
        {
            "Method": [
                "Persistence",
                "Climate only",
                "Climate + fertilizer",
                "Country × crop median",
                "Crop median",
            ],
            "MAE": [
                m["persistence_mae"],
                m["climate_only_mae"],
                m["climate_plus_fertilizer_mae"],
                m["country_crop_median_mae"],
                m["crop_median_mae"],
            ],
        }
    ).sort_values("MAE")
    plt.figure(figsize=(10, 5.5))
    ax = sns.barplot(data=model_table, x="Method", y="MAE", hue="Method", palette=PALETTE, legend=False)
    ax.set_title("2018+ holdout — climate value, fertilizer value and strong baselines")
    ax.set_xlabel("")
    ax.set_ylabel("MAE (t/ha) — lower is better")
    ax.tick_params(axis="x", rotation=12)
    for patch, value in zip(ax.patches, model_table["MAE"]):
        ax.annotate(f"{value:.3f}", (patch.get_x() + patch.get_width()/2, patch.get_height()),
                    ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "08_model_ablation_baselines.png", dpi=180, bbox_inches="tight")
    plt.close()

    # 5) Error by crop for the full model.
    error_by_crop = (
        result.predictions.groupby("crop")["abs_error"]
        .mean()
        .sort_values(ascending=False)
        .rename("MAE")
        .reset_index()
    )
    plt.figure(figsize=(9, 5.2))
    ax = sns.barplot(data=error_by_crop, x="crop", y="MAE", hue="crop", palette=PALETTE, legend=False)
    ax.set_title("Climate + fertilizer model error by crop")
    ax.set_xlabel("")
    ax.set_ylabel("MAE (t/ha)")
    for patch, value in zip(ax.patches, error_by_crop["MAE"]):
        ax.annotate(f"{value:.2f}", (patch.get_x() + patch.get_width()/2, patch.get_height()),
                    ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "10_error_by_crop.png", dpi=180, bbox_inches="tight")
    plt.close()


def main() -> None:
    df = build_analysis_panel(start_year=1990, end_year=2023)
    validate_panel(df)
    df = add_features(df)

    report = {
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "dataset": {
            "rows": int(len(df)),
            "countries": int(df["Code"].nunique()),
            "crops": int(df["crop"].nunique()),
            "start_year": int(df["Year"].min()),
            "end_year": int(df["Year"].max()),
            "coverage_pct": {
                col: pct(100 * df[col].notna().mean())
                for col in [
                    "yield_t_ha",
                    "temperature_c",
                    "precipitation_mm",
                    "fertilizer_kg_ha",
                    "irrigated_land_pct",
                ]
            },
        },
    }

    trend = yield_change_summary(df)
    report["matched_country_yield_change"] = [
        {
            "crop": row["crop"],
            "early_median_t_ha": round(float(row["early_median"]), 4),
            "recent_median_t_ha": round(float(row["recent_median"]), 4),
            "change_pct": round(float(row["change_pct"]), 2),
            "matched_countries": int(row["matched_countries"]),
        }
        for _, row in trend.iterrows()
    ]

    sensitivity = crop_temperature_sensitivity(df)
    report["relative_temperature_sensitivity_pct_per_1c"] = {
        row["crop"]: round(float(row["yield_change_pct_per_1c"]), 4)
        for _, row in sensitivity.iterrows()
    }

    risk = build_risk_table(df)
    report["top_screening_segments"] = [
        {
            "country": row["Entity"],
            "code": row["Code"],
            "crop": row["crop"],
            "screening_score": round(float(row["screening_score"]), 4),
            "detrended_yield_std_pct": round(float(row["detrended_yield_std_pct"]), 4),
            "relative_temp_slope_pct_per_c": round(float(row["temp_slope_pct_per_c"]), 4),
            "observations": int(row["observations"]),
        }
        for _, row in risk.head(15).iterrows()
    ]

    result = fit_time_split(df, split_year=2018, random_state=42)
    report["model_metrics"] = {k: round(float(v), 4) for k, v in result.metrics.items()}
    error_by_crop = (
        result.predictions.groupby("crop")["abs_error"]
        .agg(["mean", "median", "count"])
        .sort_values("mean", ascending=False)
        .reset_index()
    )
    report["full_model_error_by_crop"] = [
        {
            "crop": row["crop"],
            "mean_abs_error": round(float(row["mean"]), 4),
            "median_abs_error": round(float(row["median"]), 4),
            "n": int(row["count"]),
        }
        for _, row in error_by_crop.iterrows()
    ]

    save_figures(trend, sensitivity, risk, result)

    summary_json = json.dumps(report, indent=2, sort_keys=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(summary_json + "\n", encoding="utf-8")
    print("=== LIVE ANALYSIS REPORT START ===")
    print(summary_json)
    print("=== LIVE ANALYSIS REPORT END ===")
    print(f"LIVE_ANALYSIS_SUMMARY={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
