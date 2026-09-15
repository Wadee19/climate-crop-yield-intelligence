from __future__ import annotations

import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

from climate_crop_yield.analysis import build_risk_table, yield_change_summary
from climate_crop_yield.data import build_analysis_panel
from climate_crop_yield.features import add_features, crop_temperature_sensitivity, validate_panel
from climate_crop_yield.model import fit_time_split

SUMMARY_PATH = Path("reports/tables/live_analysis_summary.json")


def pct(value: float) -> float:
    return round(float(value), 2)


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
                for col in ["yield_t_ha", "temperature_c", "precipitation_mm", "fertilizer_kg_ha", "irrigated_land_pct"]
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

    summary_json = json.dumps(report, indent=2, sort_keys=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(summary_json + "\n", encoding="utf-8")
    print("=== LIVE ANALYSIS REPORT START ===")
    print(summary_json)
    print("=== LIVE ANALYSIS REPORT END ===")
    print(f"LIVE_ANALYSIS_SUMMARY={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
