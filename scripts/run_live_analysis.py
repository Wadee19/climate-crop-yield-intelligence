from __future__ import annotations

import json

import numpy as np
import pandas as pd

from climate_crop_yield.data import build_analysis_panel
from climate_crop_yield.features import add_features, crop_temperature_sensitivity, validate_panel
from climate_crop_yield.model import fit_time_split


def pct(value: float) -> float:
    return round(float(value), 2)


def build_risk_table(df: pd.DataFrame) -> pd.DataFrame:
    base = (
        df.dropna(subset=["yield_t_ha", "temp_deviation_c"])
        .groupby(["Code", "Entity", "crop"])
        .agg(
            yield_mean=("yield_t_ha", "mean"),
            yield_std=("yield_t_ha", "std"),
            observations=("yield_t_ha", "size"),
        )
        .reset_index()
    )

    slopes = []
    for (code, crop), part in df.dropna(
        subset=["yield_t_ha", "temp_deviation_c"]
    ).groupby(["Code", "crop"]):
        if len(part) < 15 or part["temp_deviation_c"].nunique() < 4:
            continue
        slope = np.polyfit(
            part["temp_deviation_c"].to_numpy(float),
            part["yield_t_ha"].to_numpy(float),
            deg=1,
        )[0]
        slopes.append({"Code": code, "crop": crop, "temp_slope": slope})

    risk = base.merge(pd.DataFrame(slopes), on=["Code", "crop"], how="inner")
    risk = risk[(risk["observations"] >= 15) & (risk["yield_mean"] > 0)].copy()
    risk["volatility_cv"] = risk["yield_std"] / risk["yield_mean"]
    risk["warming_penalty"] = (-risk["temp_slope"]).clip(lower=0)

    # Percentile ranks are less distorted by extreme country-crop values than raw z-scores.
    risk["volatility_rank"] = risk["volatility_cv"].rank(pct=True)
    risk["warming_penalty_rank"] = risk["warming_penalty"].rank(pct=True)
    risk["risk_score"] = (
        risk["volatility_rank"] + risk["warming_penalty_rank"]
    ) / 2

    return risk.sort_values(
        ["risk_score", "warming_penalty"], ascending=[False, False]
    ).reset_index(drop=True)


def main() -> None:
    df = build_analysis_panel(start_year=1990, end_year=2023)
    validate_panel(df)
    df = add_features(df)

    coverage = {
        col: pct(100 * (1 - df[col].isna().mean()))
        for col in [
            "yield_t_ha",
            "temperature_c",
            "precipitation_mm",
            "fertilizer_kg_ha",
            "irrigated_land_pct",
        ]
    }

    dataset_summary = {
        "rows": int(len(df)),
        "countries": int(df["Code"].nunique()),
        "crops": int(df["crop"].nunique()),
        "start_year": int(df["Year"].min()),
        "end_year": int(df["Year"].max()),
        "coverage_pct": coverage,
    }

    early = (
        df[df["Year"].between(1990, 1994)]
        .groupby("crop")["yield_t_ha"]
        .median()
        .rename("early_median")
    )
    recent = (
        df[df["Year"].between(2019, 2023)]
        .groupby("crop")["yield_t_ha"]
        .median()
        .rename("recent_median")
    )
    trend = pd.concat([early, recent], axis=1).dropna()
    trend["change_pct"] = 100 * (
        trend["recent_median"] - trend["early_median"]
    ) / trend["early_median"]
    trend = trend.sort_values("change_pct", ascending=False).reset_index()

    sensitivity = crop_temperature_sensitivity(df)
    risk = build_risk_table(df)

    result = fit_time_split(df, split_year=2018, random_state=42)
    error_by_crop = (
        result.predictions.groupby("crop")["abs_error"]
        .agg(["mean", "median", "count"])
        .sort_values("mean", ascending=False)
        .reset_index()
    )

    report = {
        "dataset": dataset_summary,
        "model_metrics": {k: round(float(v), 4) for k, v in result.metrics.items()},
        "crop_trend_change_pct": {
            row["crop"]: round(float(row["change_pct"]), 2)
            for _, row in trend.iterrows()
        },
        "temperature_sensitivity_t_ha_per_1c": {
            row["crop"]: round(
                float(row["yield_change_t_ha_per_1c_deviation"]), 4
            )
            for _, row in sensitivity.iterrows()
        },
        "top_risk_segments": [
            {
                "country": row["Entity"],
                "code": row["Code"],
                "crop": row["crop"],
                "risk_score": round(float(row["risk_score"]), 4),
                "yield_volatility_cv": round(float(row["volatility_cv"]), 4),
                "temp_slope": round(float(row["temp_slope"]), 4),
                "observations": int(row["observations"]),
            }
            for _, row in risk.head(15).iterrows()
        ],
        "model_error_by_crop": [
            {
                "crop": row["crop"],
                "mean_abs_error": round(float(row["mean"]), 4),
                "median_abs_error": round(float(row["median"]), 4),
                "n": int(row["count"]),
            }
            for _, row in error_by_crop.iterrows()
        ],
    }

    print("=== LIVE ANALYSIS REPORT START ===")
    print(json.dumps(report, indent=2, sort_keys=True))
    print("=== LIVE ANALYSIS REPORT END ===")


if __name__ == "__main__":
    main()
