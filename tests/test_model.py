import pandas as pd

from climate_crop_yield.features import add_features
from climate_crop_yield.model import fit_time_split


def fixture_model_panel():
    rows = []
    for code, temp in [("AAA", 15), ("BBB", 22), ("CCC", 28)]:
        for crop, base in [("Wheat", 3.0), ("Maize", 5.0)]:
            for year in range(2005, 2023):
                t = temp + 0.05 * (year - 2005)
                rows.append({"Entity": code, "Code": code, "Year": year, "crop": crop, "yield_t_ha": base + 0.03 * (year - 2005) - 0.02 * (t-temp), "temperature_c": t, "precipitation_mm": 500 + (year % 5) * 10, "fertilizer_kg_ha": 100 + (year - 2005), "irrigated_land_pct": 30 + (year % 4)})
    return pd.DataFrame(rows)


def test_time_split_model_runs():
    df = add_features(fixture_model_panel())
    result = fit_time_split(df, split_year=2018, random_state=1)
    assert result.metrics["mae"] >= 0
    assert len(result.predictions) > 0
    assert result.predictions["Year"].min() >= 2018
