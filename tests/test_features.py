import numpy as np
import pandas as pd

from climate_crop_yield.features import add_features, add_temperature_bins, crop_temperature_sensitivity


def fixture_panel():
    rows = []
    for code, base_temp in [("AAA", 15.0), ("BBB", 25.0)]:
        for crop, base_yield in [("Wheat", 4.0), ("Maize", 6.0)]:
            for i, year in enumerate(range(2000, 2010)):
                rows.append({"Entity": code, "Code": code, "Year": year, "crop": crop, "yield_t_ha": base_yield + 0.1 * i, "temperature_c": base_temp + 0.2 * i, "precipitation_mm": 500 + 10 * i, "fertilizer_kg_ha": 100 + i, "irrigated_land_pct": 20 + i})
    return pd.DataFrame(rows)


def test_add_features_centers_temperature_by_country():
    out = add_features(fixture_panel())
    means = out.groupby("Code")["temp_deviation_c"].mean()
    assert np.allclose(means.values, 0.0)


def test_temperature_bins_are_created():
    out = add_temperature_bins(add_features(fixture_panel()), bins=4)
    assert out["temp_bin"].notna().all()
    assert out["temp_bin"].nunique() == 4


def test_sensitivity_returns_each_crop():
    out = crop_temperature_sensitivity(add_features(fixture_panel()))
    assert set(out["crop"]) == {"Wheat", "Maize"}
