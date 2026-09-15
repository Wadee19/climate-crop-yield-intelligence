import pandas as pd

from climate_crop_yield.analysis import yield_change_summary


def test_yield_change_uses_matched_country_cohort():
    rows = []
    for year in [1990, 1991, 1992]:
        rows.append({"Code": "AAA", "crop": "Wheat", "Year": year, "yield_t_ha": 2.0})
    for year in [2019, 2020, 2021]:
        rows.append({"Code": "AAA", "crop": "Wheat", "Year": year, "yield_t_ha": 4.0})
    for year in [2019, 2020, 2021]:
        rows.append({"Code": "BBB", "crop": "Wheat", "Year": year, "yield_t_ha": 100.0})

    result = yield_change_summary(pd.DataFrame(rows), min_years_per_window=3)
    row = result.iloc[0]
    assert row["matched_countries"] == 1
    assert row["change_pct"] == 100.0
