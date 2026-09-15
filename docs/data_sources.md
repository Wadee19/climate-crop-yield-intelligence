# Data Sources

The project uses public Our World in Data Grapher endpoints so the notebook and live validation can rebuild the panel without committing third-party raw data.

## Crop yields

Source family: **Food and Agriculture Organization of the United Nations (FAO), Production: Crops and livestock products**, processed/distributed through Our World in Data. Some OWID crop-yield pages may combine additional national sources for specific countries or recent years.

Unit used by the project: **tonnes per hectare**.

Grapher series:

- `wheat-yields`
- `maize-yields`
- `rice-yields`
- `potato-yields`
- `soybean-yields`
- `barley-yields`

## Temperature

Series: `average-annual-surface-temperature`

Source: **Copernicus Climate Change Service / ERA5**, processed by Our World in Data.

Unit: **°C**, annual average surface air temperature at 2 m.

## Precipitation

Series: `average-precipitation-per-year`

Source: **Copernicus Climate Change Service / ERA5**, processed by Our World in Data.

Unit: **millimeters per year**.

## Fertilizer

Series: `fertilizer-use-in-kg-per-hectare-of-arable-land`

Source: **FAO via World Bank World Development Indicators**, processed by Our World in Data.

Unit: **kg per hectare of arable land**.

## Irrigation

Series: `agricultural-land-irrigation`

Source: **FAO via World Bank World Development Indicators**, processed by Our World in Data.

Unit: **% of total agricultural land**.

The source page describes irrigated agricultural area as land purposely provided with water by artificial means.

## Programmatic endpoint pattern

CSV:

`https://ourworldindata.org/grapher/<slug>.csv?v=1&csvType=full&useColumnShortNames=false`

Metadata:

`https://ourworldindata.org/grapher/<slug>.metadata.json?v=1&csvType=full&useColumnShortNames=false`

## Reproducibility

Raw third-party data are not committed to the repository.

The live-data workflow downloads the sources again and validates that the panel can still be rebuilt.

Source metadata was reviewed again during the final portfolio audit in September 2026.
