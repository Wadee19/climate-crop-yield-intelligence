import numpy as np
import pandas as pd

from climate_crop_yield.model import _add_train_based_anomalies, fit_time_split


def fixture_model_panel():
    rows = []
    for code, temp in [("AAA", 15), ("BBB", 22), ("CCC", 28)]:
        for crop, base in [("Wheat", 3.0), ("Maize", 5.0)]:
            for year in range(2005, 2023):
                t = temp + 0.05 * (year - 2005)
                rows.append({
                    "Entity": code, "Code": code, "Year": year, "crop": crop,
                    "yield_t_ha": base + 0.03 * (year - 2005) - 0.02 * (t - temp),
                    "temperature_c": t,
                    "precipitation_mm": 500 + (year % 5) * 10,
                    "fertilizer_kg_ha": 100 + (year - 2005),
                    "irrigated_land_pct": 30 + (year % 4),
                })
    return pd.DataFrame(rows)


def test_train_based_anomalies_do_not_use_future_test_values():
    train = pd.DataFrame({
        "Code": ["AAA", "AAA"], "Year": [2016, 2017],
        "temperature_c": [10.0, 12.0], "precipitation_mm": [100.0, 120.0],
        "fertilizer_kg_ha": [50.0, 70.0],
    })
    test = pd.DataFrame({
        "Code": ["AAA"], "Year": [2018], "temperature_c": [100.0],
        "precipitation_mm": [500.0], "fertilizer_kg_ha": [300.0],
    })
    _, out = _add_train_based_anomalies(train, test)
    assert np.isclose(out.iloc[0]["temp_anomaly_c"], 89.0)
    assert np.isclose(out.iloc[0]["precip_anomaly_mm"], 390.0)
    assert np.isclose(out.iloc[0]["fertilizer_anomaly_kg_ha"], 240.0)


def test_time_split_reports_climate_ablation_and_strong_baselines():
    result = fit_time_split(fixture_model_panel(), split_year=2018, random_state=1)
    expected = {
        "crop_median_mae", "country_crop_median_mae", "climate_only_mae",
        "climate_plus_fertilizer_mae", "persistence_mae", "full_model_r2",
    }
    assert expected.issubset(result.metrics)
    assert all(result.metrics[key] >= 0 for key in expected if key != "full_model_r2")
    assert len(result.predictions) > 0
    assert result.predictions["Year"].min() >= 2018
    assert "climate_only_predicted_yield_t_ha" in result.predictions
    assert "predicted_yield_t_ha" in result.predictions
