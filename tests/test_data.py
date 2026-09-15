import pandas as pd
import pytest

from climate_crop_yield.data import _country_code_mask, _value_column, owid_csv_url


def test_owid_url_is_csv():
    url = owid_csv_url("wheat-yields")
    assert "wheat-yields.csv" in url
    assert "csvType=full" in url


def test_value_column_detects_single_measure():
    df = pd.DataFrame({"Entity": ["Egypt"], "Code": ["EGY"], "Year": [2020], "Yield": [1.2]})
    assert _value_column(df) == "Yield"


def test_value_column_rejects_ambiguous_frame():
    df = pd.DataFrame({"Entity": ["Egypt"], "Code": ["EGY"], "Year": [2020], "A": [1], "B": [2]})
    with pytest.raises(ValueError):
        _value_column(df)


def test_country_code_mask_rejects_owid_aggregates():
    codes = pd.Series(["EGY", "USA", "OWID_AFR", "OWID_WRL", None, "FRA"])
    assert _country_code_mask(codes).tolist() == [True, True, False, False, False, True]
