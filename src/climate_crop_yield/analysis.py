from __future__ import annotations

import numpy as np
import pandas as pd

from climate_crop_yield.features import add_detrended_residuals


def yield_change_summary(
    df: pd.DataFrame,
    early_years: tuple[int, int] = (1990, 1994),
    recent_years: tuple[int, int] = (2019, 2023),
    min_years_per_window: int = 3,
) -> pd.DataFrame:
    """Compare crop yield using the same country cohort in both windows.

    Country-crop histories need observations in both windows. This avoids a
    headline change being driven by different countries entering/leaving the sample.
    """
    early = (
        df[df["Year"].between(*early_years)]
        .groupby(["Code", "crop"])["yield_t_ha"]
        .agg(early_median="median", early_n="count")
        .reset_index()
    )
    recent = (
        df[df["Year"].between(*recent_years)]
        .groupby(["Code", "crop"])["yield_t_ha"]
        .agg(recent_median="median", recent_n="count")
        .reset_index()
    )
    matched = early.merge(recent, on=["Code", "crop"], how="inner")
    matched = matched[
        (matched["early_n"] >= min_years_per_window)
        & (matched["recent_n"] >= min_years_per_window)
        & (matched["early_median"] > 0)
    ].copy()

    rows = []
    for crop, part in matched.groupby("crop"):
        early_median = float(part["early_median"].median())
        recent_median = float(part["recent_median"].median())
        rows.append(
            {
                "crop": crop,
                "early_median": early_median,
                "recent_median": recent_median,
                "change_pct": 100 * (recent_median - early_median) / early_median,
                "matched_countries": int(part["Code"].nunique()),
            }
        )

    return pd.DataFrame(rows).sort_values("change_pct", ascending=False).reset_index(drop=True)


def build_risk_table(
    df: pd.DataFrame,
    min_observations: int = 20,
) -> pd.DataFrame:
    """Screen country-crop histories using two scale-aware detrended signals.

    Components:
    1) detrended yield volatility in percentage points;
    2) negative relative temperature-yield slope (% yield deviation per +1°C).

    Both are percentile-ranked and equally weighted. This is a descriptive
    prioritization screen, not a causal damage estimate or loss probability.
    """
    detrended = add_detrended_residuals(df, min_observations=min_observations)

    base = (
        detrended.groupby(["Code", "Entity", "crop"])
        .agg(
            detrended_yield_std_pct=("yield_detrended_pct", "std"),
            observations=("yield_detrended_pct", "count"),
        )
        .reset_index()
    )

    valid = detrended.dropna(subset=["temp_detrended_c", "yield_detrended_pct"])
    rows = []
    for (code, crop), part in valid.groupby(["Code", "crop"]):
        if len(part) < min_observations or part["temp_detrended_c"].std() < 1e-8:
            continue
        slope = np.polyfit(
            part["temp_detrended_c"].to_numpy(float),
            part["yield_detrended_pct"].to_numpy(float),
            deg=1,
        )[0]
        rows.append(
            {
                "Code": code,
                "crop": crop,
                "temp_slope_pct_per_c": slope,
            }
        )

    risk = base.merge(pd.DataFrame(rows), on=["Code", "crop"], how="inner")
    risk = risk[
        (risk["observations"] >= min_observations)
        & risk["detrended_yield_std_pct"].notna()
    ].copy()

    risk["warming_penalty_pct_per_c"] = (-risk["temp_slope_pct_per_c"]).clip(lower=0)
    risk["volatility_rank"] = risk["detrended_yield_std_pct"].rank(pct=True)
    risk["warming_penalty_rank"] = risk["warming_penalty_pct_per_c"].rank(pct=True)
    risk["screening_score"] = (
        risk["volatility_rank"] + risk["warming_penalty_rank"]
    ) / 2

    return risk.sort_values(
        ["screening_score", "warming_penalty_pct_per_c"],
        ascending=[False, False],
    ).reset_index(drop=True)
