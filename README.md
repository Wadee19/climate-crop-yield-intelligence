# Climate Crop Yield Intelligence 🌾🌍

### From warming to yield: where climate risk hits agriculture first.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](#)
[![Version](https://img.shields.io/badge/version-v1.0-green.svg)](#)
[![Data](https://img.shields.io/badge/data-FAO%20%7C%20ERA5%20%7C%20World%20Bank-orange.svg)](#)
[![Tests](https://img.shields.io/badge/tests-pytest-lightgrey.svg)](#)

A portfolio-ready data science case study for an agribusiness client that wants to understand how **climate pressure and farm-management conditions relate to crop yield** — and where adaptation work should be prioritized first.

> **Business question:** Which crop-location combinations appear most exposed to warmer and more volatile conditions, and can climate + management variables predict later-period yield better than a simple baseline?

---

## Why this project is different

This is not a notebook full of unrelated plots.

The project follows one decision story:

**Business question → evidence → interpretation → limitation → client action**

V1 covers **six crops**:

`Wheat` · `Maize` · `Rice` · `Potatoes` · `Soybeans` · `Barley`

and combines them with:

- annual surface temperature,
- annual precipitation,
- fertilizer use,
- irrigation coverage.

---

## The questions

1. Which crops improved the most since 1990?
2. What happens in **warmer-than-usual years** inside the same country?
3. Which crops show the strongest negative temperature association?
4. Is there really one “best temperature” for yield?
5. Does more precipitation always mean better yield?
6. Do irrigation and fertilizer appear to reduce climate exposure?
7. Which country-crop combinations combine high volatility with a warming penalty?
8. Can a model trained on the past predict **2018+** yield better than a simple crop baseline?
9. Where does the model fail?

---

## Methodology upgrades

The original idea was useful, but V1 deliberately fixes the weak points that make climate-yield analysis easy to overstate.

| Old shortcut | V1 approach |
|---|---|
| Raw correlation = impact | Association is clearly separated from causation |
| One exact temperature = “best” | Temperature ranges / bins |
| Global temperature comparison | Country-centered temperature deviation |
| Random train/test split | Time split: past → later years |
| Model metric alone | Model vs simple crop baseline |
| Show good predictions only | Error analysis by crop and country |
| Notebook-only project | Package + tests + CI + docs |

---

## Data

The project uses public data from established sources.

**Crop yields:** FAO Production: Crops and livestock products, distributed via Our World in Data.  
**Temperature & precipitation:** Copernicus Climate Change Service ERA5, distributed via Our World in Data.  
**Fertilizer & irrigation:** FAO / World Bank series, distributed via Our World in Data.

The main analysis window is **1990–2023** to create a practical overlap across the datasets.

Raw third-party data is downloaded at run time and is **not committed** to this repository.

See [`docs/data_sources.md`](docs/data_sources.md).

---

## Project structure

```text
climate-crop-yield-intelligence/
├── .github/workflows/
│   └── ci.yml
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── data_sources.md
│   ├── methodology.md
│   └── project_history.md
├── notebooks/
│   └── 01_climate_crop_yield_business_analysis.ipynb
├── reports/
│   ├── figures/
│   └── tables/
├── slides/
│   └── presentation_story.md
├── src/climate_crop_yield/
│   ├── data.py
│   ├── features.py
│   ├── model.py
│   └── plots.py
├── tests/
├── README.md
└── requirements.txt
```

---

## Run it

### Google Colab

Open:

`notebooks/01_climate_crop_yield_business_analysis.ipynb`

and run all cells.

The notebook downloads the latest source CSVs directly from public endpoints.

### Local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest -q
jupyter notebook
```

---

## Modeling design

The V1 model predicts crop yield from:

- absolute annual temperature,
- temperature deviation from the country's mean,
- precipitation,
- precipitation deviation,
- fertilizer use,
- irrigation share,
- crop identity,
- country identity.

The evaluation is intentionally **time-aware**:

- **Train:** before 2018
- **Test:** 2018 onward

It must beat a simple baseline built from each crop's median training-period yield.

---

## What V1 does *not* claim

This project does **not** claim that fertilizer, irrigation, temperature or precipitation *cause* the observed yield changes.

Country-level annual data cannot capture:

- farm-level soil conditions,
- planting dates,
- cultivar choice,
- heat waves inside the growing season,
- rainfall timing,
- irrigation efficiency,
- local input prices,
- management quality.

Those limitations are part of the project design, not hidden in fine print.

See [`docs/methodology.md`](docs/methodology.md).

---

## Presentation

The portfolio presentation is designed as a **10-slide client story**, not a classroom report:

**From Warming to Yield — Where Climate Risk Hits Agriculture First**

See [`slides/presentation_story.md`](slides/presentation_story.md).

---

## Reproducibility

```bash
pytest -q
```

Tests cover:

- OWID schema normalization,
- duplicate / panel validation,
- country-centered climate features,
- temperature binning,
- sensitivity calculation,
- time-split model execution.

CI runs the offline test suite on every push and pull request.

---

<details>
<summary><strong>Project history</strong></summary>

The core business idea was first explored in a university analysis around **2022**.

The **2026** project was rebuilt from the ground up using updated data, six crop series, stronger methodology, a time-aware predictive baseline, error analysis, tests and a reproducible repository structure.

**v1.0 is the first public portfolio release.**

The old university notebook is not included in the main repository; it is retained only as historical source material and a style reference.

</details>

---

## Author

**Ahmed Wadee**

Data Science · AI · Engineering
