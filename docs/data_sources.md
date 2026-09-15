# Data Sources

All V1 data are public and downloaded at run time from reproducible Our World in Data Grapher endpoints. Raw third-party datasets are not committed to the repository.

## Crop yields

**Provider:** Food and Agriculture Organization of the United Nations (FAO), Production: Crops and livestock products, distributed through Our World in Data.

**Unit:** tonnes per hectare.

V1 crops:

- Wheat
- Maize
- Rice
- Potatoes
- Soybeans
- Barley

The exact Grapher slugs are defined in `src/climate_crop_yield/data.py`.

## Climate

**Provider:** Copernicus Climate Change Service / ERA5, distributed through Our World in Data.

- Average annual surface temperature — °C
- Annual precipitation — millimeters

Annual country averages are useful for a broad panel study but do not capture growing-season heat extremes or rainfall timing.

## Management

**Provider:** FAO via World Bank / Our World in Data.

- Fertilizer use — kilograms per hectare of arable land
- Share of agricultural land irrigated — % of total agricultural land

The fertilizer source notes methodology revisions and incomplete consistency across countries and over time. These variables are therefore treated as observational context, not causal treatment variables.

Irrigation has limited matched coverage in the final crop panel and is kept exploratory.

## Filtering

The analysis retains three-letter country / territory codes and removes OWID aggregate rows such as `OWID_WRL` and `OWID_AFR`.

## Reproducibility

The notebook and package use the same public Grapher endpoints. Source URLs are generated from the slugs in `src/climate_crop_yield/data.py`.
