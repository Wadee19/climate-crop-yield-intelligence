# Run in Google Colab

The portfolio notebook is standalone:

`notebooks/01_climate_crop_yield_business_analysis.ipynb`

## Steps

1. Open Google Colab.
2. Upload the notebook.
3. Use a normal **Python CPU runtime**. No GPU is needed.
4. Choose **Runtime → Run all**.

The notebook downloads the public data directly from Our World in Data Grapher endpoints.

No repository ZIP and no local `src/` package install are required.

During the run, figures are saved under:

`/content/climate_crop_figures/`

and the notebook summary is saved under:

`/content/climate_crop_tables/notebook_summary.json`

If OWID changes an endpoint or schema later, the repository's **Live data validation** workflow is designed to catch that before a portfolio update is treated as validated.
