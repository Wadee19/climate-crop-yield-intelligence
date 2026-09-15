from __future__ import annotations

import numpy as np
import pandas as pd

from climate_crop_yield.features import add_detrended_residuals


def yield_change_summary(
    df: pd.DataFrame,
    early_years: tuple[int, int] = (1990, 1994),
    recent_years: tuple[int, int] = (2019, 2023),
) -> pd.DataFrame:
    """Compare median crop yield between an early and recent window."""
    early = (
        df[df["Year"].between(*early_years)]
        .groupby("crop")["yield_t_ha"]
        .median()
        .rename("early_median")
    )
    recent = (
        df[df["Year"].between(*recent_years)]
        .groupby("crop")["yield_t_ha"]
        .median()
        .rename("recent_median")
    )
    out = pd.concat([early, recent], axis=1).dropna()
    out["change_pct"] = 100 * (
        out["recent_median"] - out["early_median"]
    ) / out["early_median"]
    return out.sort_values("change_pct", ascending=False).reset_index()


def build_risk_table(
    df: pd.DataFrame,
    min_observations: int = 15,
) -> pd.DataFrame:
    """Rank country-crop histories by detrended volatility and temperature penalty.

    Both components are built from residuals after removing the linear time trend
    inside each country-crop history. This avoids treating a strong long-run yield
    improvement as instability. The score is descriptive prioritization only.
    """
    detrended = add_detrended_residuals(
        df,
        min_observations=min_observations,
    )

    base = (
        detrended.groupby(["Code", "Entity", "crop"])
        .agg(
            yield_mean=("yield_t_ha", "mean"),
            detrended_yield_std=("yield_detrended_t_ha", "std"),
            observations=("yield_t_ha", "size"),
        )
        .reset_index()
    )

    rows = []
    valid = detrended.dropna(
        subset=["temp_detrended_c", "yield_detrended_t_ha"]
    )
    for (code, crop), part in valid.groupby(["Code", "crop"]):
        if len(part) < min_observations or part["temp_detrended_c"].std() < 1e-8:
            continue
        slope = np.polyfit(
            part["temp_detrended_c"].to_numpy(float),
            part["yield_detrended_t_ha"].to_numpy(float),
            deg=1,
        )[0]
        rows.append({"Code": code, "crop": crop, "temp_slope": slope})

    risk = base.merge(pd.DataFrame(rows), on=["Code", "crop"], how="inner")
    risk = risk[
        (risk["observations"] >= min_observations)
        & (risk["yield_mean"] > 0)
        & risk["detrended_yield_std"].notna()
    ].copy()

    risk["volatility_cv"] = risk["detrended_yield_std"] / risk["yield_mean"]
    risk["warming_penalty"] = (-risk["temp_slope"]).clip(lower=0)
    risk["volatility_rank"] = risk["volatility_cv"].rank(pct=True)
    risk["warming_penalty_rank"] = risk["warming_penalty"].rank(pct=True)
    risk["risk_score"] = (
        risk["volatility_rank"] + risk["warming_penalty_rank"]
    ) / 2

    return risk.sort_values(
        ["risk_score", "warming_penalty"],
        ascending=[False, False],
    ).reset_index(drop=True)
