import numpy as np
import pandas as pd

from climate_crop_yield.features import add_detrended_residuals, add_features, add_temperature_bins, crop_temperature_sensitivity


def fixture_panel():
    rows = []
    shocks = [-0.35, 0.20, -0.10, 0.45, -0.25, 0.15, 0.30, -0.40, 0.10, -0.05]
    for code, base_temp in [("AAA", 15.0), ("BBB", 25.0)]:
        for crop, base_yield, pct_response in [("Wheat", 4.0, -5.0), ("Potatoes", 20.0, -5.0)]:
            for i, year in enumerate(range(2000, 2010)):
                shock = shocks[i]
                trend_yield = base_yield * (1 + 0.01 * i)
                yield_value = trend_yield * (1 + pct_response / 100 * shock)
                rows.append({
                    "Entity": code, "Code": code, "Year": year, "crop": crop,
                    "yield_t_ha": yield_value,
                    "temperature_c": base_temp + 0.08 * i + shock,
                    "precipitation_mm": 500 + 10 * i,
                    "fertilizer_kg_ha": 100 + i,
                    "irrigated_land_pct": 20 + i,
                })
    return pd.DataFrame(rows)


def test_add_features_centers_temperature_by_country():
    out = add_features(fixture_panel())
    means = out.groupby("Code")["temp_deviation_c"].mean()
    assert np.allclose(means.values, 0.0)


def test_temperature_bins_are_created_within_crop():
    out = add_temperature_bins(add_features(fixture_panel()), bins=4)
    assert out["temp_bin"].notna().all()
    assert all(part["temp_bin"].nunique() == 4 for _, part in out.groupby("crop"))


def test_detrending_removes_linear_year_component():
    out = add_detrended_residuals(fixture_panel())
    valid = out.dropna(subset=["temp_detrended_c", "yield_detrended_t_ha"])
    for _, part in valid.groupby(["Code", "crop"]):
        year = part["Year"].to_numpy(float)
        assert abs(np.polyfit(year, part["temp_detrended_c"], 1)[0]) < 1e-10
        assert abs(np.polyfit(year, part["yield_detrended_t_ha"], 1)[0]) < 1e-10


def test_relative_sensitivity_is_scale_aware_across_crops():
    out = crop_temperature_sensitivity(fixture_panel()).set_index("crop")
    wheat = out.loc["Wheat", "yield_change_pct_per_1c"]
    potatoes = out.loc["Potatoes", "yield_change_pct_per_1c"]
    assert wheat < 0 and potatoes < 0
    assert abs(wheat - potatoes) < 0.5
