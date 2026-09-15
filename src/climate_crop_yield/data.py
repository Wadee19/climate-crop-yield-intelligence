from __future__ import annotations

from typing import Iterable

import pandas as pd


OWID_BASE = "https://ourworldindata.org/grapher"

CROP_SLUGS = {
    "Wheat": "wheat-yields",
    "Maize": "maize-yields",
    "Rice": "rice-yields",
    "Potatoes": "potato-yields",
    "Soybeans": "soybean-yields",
    "Barley": "barley-yields",
}

DRIVER_SLUGS = {
    "temperature_c": "average-annual-surface-temperature",
    "precipitation_mm": "average-precipitation-per-year",
    "fertilizer_kg_ha": "fertilizer-use-in-kg-per-hectare-of-arable-land",
    "irrigated_land_pct": "agricultural-land-irrigation",
}


def owid_csv_url(slug: str) -> str:
    return (
        f"{OWID_BASE}/{slug}.csv"
        "?v=1&csvType=full&useColumnShortNames=false"
    )


def _value_column(df: pd.DataFrame) -> str:
    id_cols = {"Entity", "Code", "Year"}
    candidates = [c for c in df.columns if c not in id_cols]
    if len(candidates) != 1:
        raise ValueError(
            "Expected exactly one value column from an OWID Grapher export, "
            f"found {candidates}"
        )
    return candidates[0]


def _country_code_mask(codes: pd.Series) -> pd.Series:
    """Keep ISO-3 country codes and reject OWID aggregate codes such as OWID_AFR."""
    return codes.astype("string").str.fullmatch(r"[A-Z]{3}", na=False)


def read_owid_series(slug: str, value_name: str) -> pd.DataFrame:
    """Download one OWID Grapher series and return a country-year frame."""
    url = owid_csv_url(slug)
    df = pd.read_csv(
        url,
        storage_options={"User-Agent": "climate-crop-yield-intelligence/1.0"},
    )
    value_col = _value_column(df)
    df = df.rename(columns={value_col: value_name})
    df = df[["Entity", "Code", "Year", value_name]].copy()

    # OWID also publishes aggregates with codes such as OWID_AFR / OWID_WRL.
    # The analysis unit is country-year-crop, so only true ISO-3 rows belong here.
    df = df[_country_code_mask(df["Code"])].copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    df["Year"] = df["Year"].astype(int)
    return df


def load_crop_yields(
    crops: Iterable[str] | None = None,
) -> pd.DataFrame:
    selected = list(crops) if crops is not None else list(CROP_SLUGS)
    frames: list[pd.DataFrame] = []

    for crop in selected:
        if crop not in CROP_SLUGS:
            raise KeyError(f"Unknown crop: {crop}")

        part = read_owid_series(
            CROP_SLUGS[crop],
            value_name="yield_t_ha",
        )
        part["crop"] = crop
        frames.append(part)

    out = pd.concat(frames, ignore_index=True)
    return out[["Entity", "Code", "Year", "crop", "yield_t_ha"]]


def load_country_year_drivers() -> pd.DataFrame:
    frames = [
        read_owid_series(slug, value_name=name)
        for name, slug in DRIVER_SLUGS.items()
    ]

    panel = frames[0]
    for frame in frames[1:]:
        panel = panel.merge(frame, on=["Entity", "Code", "Year"], how="outer")

    return panel.sort_values(["Code", "Year"]).reset_index(drop=True)


def build_analysis_panel(
    start_year: int = 1990,
    end_year: int = 2023,
    crops: Iterable[str] | None = None,
    countries: Iterable[str] | None = None,
) -> pd.DataFrame:
    yields = load_crop_yields(crops=crops)
    drivers = load_country_year_drivers()

    panel = yields.merge(
        drivers,
        on=["Entity", "Code", "Year"],
        how="left",
        validate="many_to_one",
    )

    panel = panel[panel["Year"].between(start_year, end_year)].copy()

    if countries is not None:
        country_set = set(countries)
        panel = panel[panel["Code"].isin(country_set)].copy()

    panel = panel.drop_duplicates(["Code", "Year", "crop"])
    return panel.sort_values(["crop", "Code", "Year"]).reset_index(drop=True)
