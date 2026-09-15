from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "Entity",
    "Code",
    "Year",
    "crop",
    "yield_t_ha",
    "temperature_c",
    "precipitation_mm",
}


def validate_panel(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("Analysis panel is empty")

    duplicated = df.duplicated(["Code", "Year", "crop"]).sum()
    if duplicated:
        raise ValueError(f"Found {duplicated} duplicated country-year-crop rows")

    if (df["yield_t_ha"].dropna() < 0).any():
        raise ValueError("Yield cannot be negative")


def _country_climate_normals(df: pd.DataFrame) -> pd.DataFrame:
    """Country climate means using one observation per country-year, not one per crop."""
    climate = (
        df[["Code", "Year", "temperature_c", "precipitation_mm"]]
        .drop_duplicates(["Code", "Year"])
        .copy()
    )
    return climate.groupby("Code")[["temperature_c", "precipitation_mm"]].mean()


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add descriptive features for EDA.

    Climate deviations here use the full analysis period and are descriptive only.
    The predictive model calculates separate train-only normals.
    """
    validate_panel(df)
    out = df.copy()

    normals = _country_climate_normals(out)
    temp_normal = out["Code"].map(normals["temperature_c"])
    rain_normal = out["Code"].map(normals["precipitation_mm"])

    out["temp_deviation_c"] = out["temperature_c"] - temp_normal
    out["precip_deviation_mm"] = out["precipitation_mm"] - rain_normal
    out["yield_log1p"] = np.log1p(out["yield_t_ha"].clip(lower=0))

    ordered = out.sort_values(["Code", "crop", "Year"])
    yoy = (
        ordered.groupby(["Code", "crop"])["yield_t_ha"]
        .pct_change(fill_method=None)
        .mul(100)
    )
    out["yield_yoy_pct"] = yoy.reindex(out.index)

    if out["yield_yoy_pct"].notna().any():
        lo, hi = out["yield_yoy_pct"].quantile([0.01, 0.99])
        out["yield_yoy_pct_w"] = out["yield_yoy_pct"].clip(lo, hi)
    else:
        out["yield_yoy_pct_w"] = out["yield_yoy_pct"]

    return out


def _linear_residual(year: np.ndarray, values: np.ndarray) -> np.ndarray:
    coef = np.polyfit(year.astype(float), values.astype(float), deg=1)
    return values.astype(float) - np.polyval(coef, year.astype(float))


def add_detrended_residuals(
    df: pd.DataFrame,
    min_observations: int = 8,
) -> pd.DataFrame:
    """Remove linear time trends within each country-crop history.

    The resulting residuals isolate interannual co-movement better than raw levels:
    - temp_detrended_c: temperature departures after removing that system's time trend
    - yield_detrended_t_ha: yield departures after removing that system's time trend

    This is still descriptive, not causal.
    """
    validate_panel(df)
    out = df.copy()
    out["temp_detrended_c"] = np.nan
    out["yield_detrended_t_ha"] = np.nan

    for (_, _), part in out.groupby(["Code", "crop"]):
        valid = part.dropna(subset=["Year", "temperature_c", "yield_t_ha"])
        if len(valid) < min_observations or valid["Year"].nunique() < min_observations:
            continue

        years = valid["Year"].to_numpy(float)
        temp = valid["temperature_c"].to_numpy(float)
        yield_values = valid["yield_t_ha"].to_numpy(float)

        temp_resid = _linear_residual(years, temp)
        yield_resid = _linear_residual(years, yield_values)

        out.loc[valid.index, "temp_detrended_c"] = temp_resid
        out.loc[valid.index, "yield_detrended_t_ha"] = yield_resid

    return out


def add_temperature_bins(df: pd.DataFrame, bins: int = 8) -> pd.DataFrame:
    out = df.copy()
    valid = out["temperature_c"].dropna()
    if valid.nunique() < bins:
        raise ValueError("Not enough distinct temperature values for requested bins")

    out["temp_bin"] = pd.qcut(
        out["temperature_c"],
        q=bins,
        duplicates="drop",
    )
    return out


def crop_temperature_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """Detrended within-country×crop temperature sensitivity by crop.

    Slow technology/yield improvements and slow warming trends are removed inside each
    country-crop history before pooling. The remaining slope is an interannual
    association and must not be interpreted as a causal temperature effect.
    """
    work = add_detrended_residuals(df)
    work = work.dropna(subset=["temp_detrended_c", "yield_detrended_t_ha"])

    rows = []
    for crop, part in work.groupby("crop"):
        if len(part) < 20 or part["temp_detrended_c"].std() < 1e-8:
            continue

        x = part["temp_detrended_c"].to_numpy(float)
        y = part["yield_detrended_t_ha"].to_numpy(float)
        slope = np.polyfit(x, y, deg=1)[0]
        rows.append(
            {
                "crop": crop,
                "n": len(part),
                "yield_change_t_ha_per_1c_deviation": slope,
            }
        )

    return pd.DataFrame(rows).sort_values(
        "yield_change_t_ha_per_1c_deviation"
    ).reset_index(drop=True)
