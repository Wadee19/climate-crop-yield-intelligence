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

    Climate deviations here use the full analysis period and are therefore descriptive,
    not predictive features. The predictive model calculates its own train-only normals.
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
    """Descriptive within-country×crop temperature sensitivity.

    Both temperature and yield are demeaned inside each country-crop history before
    pooling by crop. This removes persistent country/crop yield-level differences and
    makes the slope describe warmer-than-usual years within the same production system.
    """
    work = df.dropna(subset=["yield_t_ha", "temperature_c"]).copy()
    groups = work.groupby(["Code", "crop"])
    work["temp_within_c"] = work["temperature_c"] - groups["temperature_c"].transform("mean")
    work["yield_within_t_ha"] = work["yield_t_ha"] - groups["yield_t_ha"].transform("mean")

    rows = []
    for crop, part in work.groupby("crop"):
        part = part.dropna(subset=["temp_within_c", "yield_within_t_ha"])
        if len(part) < 20 or part["temp_within_c"].nunique() < 3:
            continue

        x = part["temp_within_c"].to_numpy(float)
        y = part["yield_within_t_ha"].to_numpy(float)
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
