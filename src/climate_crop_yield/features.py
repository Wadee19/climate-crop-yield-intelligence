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
    climate = (
        df[["Code", "Year", "temperature_c", "precipitation_mm"]]
        .drop_duplicates(["Code", "Year"])
        .copy()
    )
    return climate.groupby("Code")[["temperature_c", "precipitation_mm"]].mean()


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add descriptive features used in EDA.

    Full-period climate deviations are descriptive only. The predictive model
    calculates separate train-only normals to avoid leakage.
    """
    validate_panel(df)
    out = df.copy()
    normals = _country_climate_normals(out)
    out["temp_deviation_c"] = out["temperature_c"] - out["Code"].map(
        normals["temperature_c"]
    )
    out["precip_deviation_mm"] = out["precipitation_mm"] - out["Code"].map(
        normals["precipitation_mm"]
    )

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
    """Remove linear time trends inside each country-crop history.

    `yield_detrended_pct` expresses the yield residual as a percentage of that
    country-crop history's mean yield. This makes cross-crop comparisons less
    sensitive to crops having very different absolute t/ha scales.
    """
    validate_panel(df)
    out = df.copy()
    out["temp_detrended_c"] = np.nan
    out["yield_detrended_t_ha"] = np.nan
    out["yield_detrended_pct"] = np.nan

    for (_, _), part in out.groupby(["Code", "crop"]):
        valid = part.dropna(subset=["Year", "temperature_c", "yield_t_ha"])
        if len(valid) < min_observations or valid["Year"].nunique() < min_observations:
            continue

        years = valid["Year"].to_numpy(float)
        temp = valid["temperature_c"].to_numpy(float)
        yield_values = valid["yield_t_ha"].to_numpy(float)
        mean_yield = float(np.mean(yield_values))
        if mean_yield <= 0:
            continue

        temp_resid = _linear_residual(years, temp)
        yield_resid = _linear_residual(years, yield_values)
        out.loc[valid.index, "temp_detrended_c"] = temp_resid
        out.loc[valid.index, "yield_detrended_t_ha"] = yield_resid
        out.loc[valid.index, "yield_detrended_pct"] = 100 * yield_resid / mean_yield

    return out


def add_temperature_bins(df: pd.DataFrame, bins: int = 8) -> pd.DataFrame:
    """Create temperature quantile bins separately inside each crop."""
    out = df.copy()
    out["temp_bin"] = pd.Series(index=out.index, dtype="object")
    for _, part in out.groupby("crop"):
        valid = part["temperature_c"].dropna()
        if valid.nunique() < bins:
            continue
        out.loc[valid.index, "temp_bin"] = pd.qcut(
            valid,
            q=bins,
            duplicates="drop",
        ).astype(str)
    return out


def crop_temperature_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """Relative detrended temperature-yield association by crop.

    The public comparison is percentage yield deviation per +1°C, rather than
    raw t/ha per +1°C, so crops with naturally larger yield scales do not get
    mechanically larger sensitivity values.
    """
    work = add_detrended_residuals(df)
    work = work.dropna(
        subset=["temp_detrended_c", "yield_detrended_pct", "yield_detrended_t_ha"]
    )

    rows = []
    for crop, part in work.groupby("crop"):
        if len(part) < 20 or part["temp_detrended_c"].std() < 1e-8:
            continue
        x = part["temp_detrended_c"].to_numpy(float)
        y_pct = part["yield_detrended_pct"].to_numpy(float)
        y_raw = part["yield_detrended_t_ha"].to_numpy(float)
        rows.append(
            {
                "crop": crop,
                "observations": len(part),
                "yield_change_pct_per_1c": np.polyfit(x, y_pct, deg=1)[0],
                "yield_change_t_ha_per_1c": np.polyfit(x, y_raw, deg=1)[0],
            }
        )

    return pd.DataFrame(rows).sort_values(
        "yield_change_pct_per_1c"
    ).reset_index(drop=True)
