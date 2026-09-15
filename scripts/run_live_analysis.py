from __future__ import annotations

import json
from pathlib import Path

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
        }
    }

    trend = yield_change_summary(df)
    report["crop_trend_change_pct"] = {
        row["crop"]: round(float(row["change_pct"]), 2)
        for _, row in trend.iterrows()
    }

    sensitivity = crop_temperature_sensitivity(df)
    report["detrended_temperature_sensitivity_t_ha_per_1c"] = {
        row["crop"]: round(float(row["yield_change_t_ha_per_1c_deviation"]), 4)
        for _, row in sensitivity.iterrows()
    }

    risk = build_risk_table(df)
    report["top_risk_segments"] = [
        {
            "country": row["Entity"],
            "code": row["Code"],
            "crop": row["crop"],
            "risk_score": round(float(row["risk_score"]), 4),
            "yield_volatility_cv": round(float(row["volatility_cv"]), 4),
            "detrended_temp_slope": round(float(row["temp_slope"]), 4),
            "observations": int(row["observations"]),
        }
        for _, row in risk.head(15).iterrows()
    ]

    result = fit_time_split(df, split_year=2018, random_state=42)
    report["model_metrics"] = {
        k: round(float(v), 4) for k, v in result.metrics.items()
    }
    error_by_crop = (
        result.predictions.groupby("crop")["abs_error"]
        .agg(["mean", "median", "count"])
        .sort_values("mean", ascending=False)
        .reset_index()
    )
    report["model_error_by_crop"] = [
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
