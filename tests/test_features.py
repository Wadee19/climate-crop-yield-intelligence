import numpy as np
import pandas as pd

from climate_crop_yield.features import (
    add_detrended_residuals,
    add_features,
    add_temperature_bins,
    crop_temperature_sensitivity,
)


def fixture_panel():
    rows = []
    shocks = [-0.35, 0.20, -0.10, 0.45, -0.25, 0.15, 0.30, -0.40, 0.10, -0.05]
    for code, base_temp in [("AAA", 15.0), ("BBB", 25.0)]:
        for crop, base_yield, response in [
            ("Wheat", 4.0, -0.6),
            ("Maize", 6.0, 0.4),
        ]:
            for i, year in enumerate(range(2000, 2010)):
                shock = shocks[i]
                rows.append(
                    {
                        "Entity": code,
                        "Code": code,
                        "Year": year,
                        "crop": crop,
                        "yield_t_ha": base_yield + 0.12 * i + response * shock,
                        "temperature_c": base_temp + 0.08 * i + shock,
                        "precipitation_mm": 500 + 10 * i,
                        "fertilizer_kg_ha": 100 + i,
                        "irrigated_land_pct": 20 + i,
                    }
                )
    return pd.DataFrame(rows)


def test_add_features_centers_temperature_by_country():
    out = add_features(fixture_panel())
    means = out.groupby("Code")["temp_deviation_c"].mean()
    assert np.allclose(means.values, 0.0)


def test_temperature_bins_are_created():
    out = add_temperature_bins(add_features(fixture_panel()), bins=4)
    assert out["temp_bin"].notna().all()
    assert out["temp_bin"].nunique() == 4


def test_detrending_removes_linear_year_component():
    out = add_detrended_residuals(fixture_panel())
    for _, part in out.dropna(subset=["temp_detrended_c", "yield_detrended_t_ha"]).groupby(["Code", "crop"]):
        year = part["Year"].to_numpy(float)
        temp_slope = np.polyfit(year, part["temp_detrended_c"].to_numpy(float), 1)[0]
        yield_slope = np.polyfit(year, part["yield_detrended_t_ha"].to_numpy(float), 1)[0]
        assert abs(temp_slope) < 1e-10
        assert abs(yield_slope) < 1e-10


def test_sensitivity_recovers_expected_signs_after_detrending():
    out = crop_temperature_sensitivity(fixture_panel()).set_index("crop")
    assert out.loc["Wheat", "yield_change_t_ha_per_1c_deviation"] < 0
    assert out.loc["Maize", "yield_change_t_ha_per_1c_deviation"] > 0
