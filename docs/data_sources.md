# Data Sources

## Crop yields
Food and Agriculture Organization of the United Nations (FAO), Production: Crops and livestock products,
distributed through Our World in Data Grapher.

V1 crop series:
- Wheat
- Maize
- Rice
- Potatoes
- Soybeans
- Barley

## Climate
Copernicus Climate Change Service / ERA5, distributed through Our World in Data:
- Average annual surface temperature
- Annual precipitation

## Management
FAO data distributed via World Bank / Our World in Data:
- Fertilizer use per hectare of arable land
- Share of agricultural land irrigated

## Reproducibility
The notebook downloads data at run time from the public Grapher CSV endpoints.
Raw third-party datasets are not committed to the repository.

See source URLs in `src/climate_crop_yield/data.py`.
