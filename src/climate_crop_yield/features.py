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


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add interpretable climate and yield features without leaking future values."""
    validate_panel(df)
    out = df.copy()

    country_temp_mean = out.groupby("Code")["temperature_c"].transform("mean")
    country_rain_mean = out.groupby("Code")["precipitation_mm"].transform("mean")

    out["temp_deviation_c"] = out["temperature_c"] - country_temp_mean
    out["precip_deviation_mm"] = out["precipitation_mm"] - country_rain_mean

    out["yield_log1p"] = np.log1p(out["yield_t_ha"].clip(lower=0))

    out["yield_yoy_pct"] = (
        out.sort_values(["Code", "crop", "Year"])
        .groupby(["Code", "crop"])["yield_t_ha"]
        .pct_change(fill_method=None)
        .mul(100)
    )

    # Winsorize only for plotting / descriptive stability.
    if out["yield_yoy_pct"].notna().any():
        lo, hi = out["yield_yoy_pct"].quantile([0.01, 0.99])
        out["yield_yoy_pct_w"] = out["yield_yoy_pct"].clip(lo, hi)
    else:
        out["yield_yoy_pct_w"] = out["yield_yoy_pct"]

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
    """Simple within-crop slope: yield ~ country-centered temperature deviation."""
    rows = []
    for crop, part in df.dropna(subset=["yield_t_ha", "temp_deviation_c"]).groupby("crop"):
        if len(part) < 20 or part["temp_deviation_c"].nunique() < 3:
            continue

        x = part["temp_deviation_c"].to_numpy(float)
        y = part["yield_t_ha"].to_numpy(float)
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
