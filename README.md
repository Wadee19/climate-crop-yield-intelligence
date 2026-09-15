# Climate Crop Yield Intelligence 🌾🌍

### From warming to yield: where climate risk hits agriculture first.

[![CI](https://github.com/Wadee19/climate-crop-yield-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/Wadee19/climate-crop-yield-intelligence/actions/workflows/ci.yml)
[![Live Data](https://github.com/Wadee19/climate-crop-yield-intelligence/actions/workflows/live-data-smoke.yml/badge.svg)](https://github.com/Wadee19/climate-crop-yield-intelligence/actions/workflows/live-data-smoke.yml)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Version](https://img.shields.io/badge/version-v1.0-green.svg)
![Data](https://img.shields.io/badge/data-FAO%20%7C%20ERA5%20%7C%20World%20Bank-orange.svg)

A business-first data science case study for an agribusiness client that wants to understand how **climate pressure and farm-management conditions relate to crop yield** — and which crop-location combinations deserve attention first.

> **Business question:** Where do warmer-than-expected conditions and unstable yields appear together, and how much forecasting value do country-level climate variables add beyond simple historical baselines?

---

## V1 at a glance

| | Live validated result |
|---|---:|
| Country × year × crop records | **24,892** |
| Countries / territories | **187** |
| Crops | **6** |
| Analysis period | **1990–2023** |
| Yield coverage | **100%** |
| Temperature / precipitation coverage | **97.59%** |
| Fertilizer coverage | **97.15%** |
| Irrigation coverage | **22.64%** |

Crops in V1:

`Wheat` · `Maize` · `Rice` · `Potatoes` · `Soybeans` · `Barley`

All figures above are produced by the live-data GitHub Actions pipeline — not typed into the project before execution.

---

## What I found

### 1. Yield improved strongly, but not equally

Comparing median yield in **1990–1994** with **2019–2023**:

| Crop | Median yield change |
|---|---:|
| Maize | **+121.60%** |
| Barley | +48.27% |
| Potatoes | +47.00% |
| Rice | +46.66% |
| Wheat | +42.18% |
| Soybeans | +28.67% |

This is a production trend, not a climate effect. Technology, varieties, farm inputs and structural change can move yield at the same time as climate.

### 2. Removing the time trend changes the climate story

A raw temperature-yield relationship can be misleading because both temperature and agricultural productivity changed over time.

So V1 removes the linear time trend **inside each country × crop history** before measuring interannual temperature-yield association.

| Crop | Detrended yield association per +1°C |
|---|---:|
| Potatoes | **-0.2725 t/ha** |
| Maize | **-0.1715 t/ha** |
| Barley | -0.0765 t/ha |
| Soybeans | -0.0752 t/ha |
| Wheat | -0.0443 t/ha |
| Rice | -0.0241 t/ha |

All six pooled slopes are negative after detrending, but these are **descriptive associations, not causal temperature effects**.

### 3. Climate exposure is local, not one global ranking

The risk screen combines two signals:

- yield volatility, and
- a negative **detrended** temperature-yield association.

Highest V1 priority segments include:

| Priority | Country | Crop | Risk score | Detrended temp slope |
|---:|---|---|---:|---:|
| 1 | Cameroon | Potatoes | **0.9904** | -2.9653 |
| 2 | Oman | Barley | **0.9856** | -1.6709 |
| 3 | Oman | Maize | **0.9842** | -1.5755 |
| 4 | Saint Vincent and the Grenadines | Maize | **0.9835** | -2.3649 |
| 5 | Tajikistan | Maize | **0.9760** | -1.3614 |

This score is a **prioritization tool**, not an insurance-grade risk estimate and not proof that temperature caused the yield changes.

### 4. The ML result is useful because the strongest baseline wins

The model trains on years **before 2018** and tests on **2018–2023**.

Instead of comparing only with an easy global baseline, V1 uses three references:

| 2018+ holdout | MAE, t/ha |
|---|---:|
| Crop median baseline | 3.4478 |
| Country × crop historical median | 1.6192 |
| Climate-anomaly residual model | **1.4473** |
| Persistence: last pre-2018 yield | **0.8976** |

The climate-anomaly model improves on the static country × crop median by **10.62%**, with **R² = 0.9038**.

But the simple persistence baseline is substantially better. The model is **61.24% worse in MAE than persistence**.

That is an important result, not something to hide: at this aggregation level, **recent production history is more useful for short-horizon yield prediction than annual climate and fertilizer anomalies alone**.

Potatoes are also the hardest crop for the current model (MAE **3.8919 t/ha**), while soybeans have the lowest error (**0.4160 t/ha**).

---

## Why this project is different

This is not a notebook full of unrelated plots.

The project follows one decision story:

**Business question → evidence → interpretation → limitation → client action**

The rebuild also deliberately corrects shortcuts from the earlier university analysis:

| Old shortcut | V1 approach |
|---|---|
| Raw correlation = impact | Association is separated from causation |
| One exact temperature = “best” | Temperature ranges / bins |
| Compare hot countries with cold countries | Within-system climate deviations |
| Ignore long-term productivity trend | Country × crop detrending |
| Random train/test split | Past → future time split |
| One weak baseline | Crop median + country-crop median + persistence |
| Use every available feature | Coverage decides whether a feature belongs in the core model |
| Show only good model results | Error analysis and baseline failures are explicit |
| Notebook-only project | Package + tests + CI + live-data validation + docs |

---

## Data

The project uses public data from established sources, accessed through reproducible Our World in Data Grapher CSV endpoints.

- **Crop yields:** FAO Production: Crops and livestock products.
- **Temperature & precipitation:** Copernicus Climate Change Service / ERA5.
- **Fertilizer & irrigation:** FAO / World Bank indicator series.

Only ISO-3 country/territory rows are retained; OWID regional aggregates such as `OWID_AFR` and `OWID_WRL` are excluded from the country panel.

Raw third-party datasets are downloaded at runtime and are **not committed** to this repository.

Irrigation is useful for exploratory analysis, but only **22.64%** of the final panel has an observed irrigation value. For that reason it is intentionally **excluded from the core predictive model** instead of being mostly imputed.

See [`docs/data_sources.md`](docs/data_sources.md) and [`docs/methodology.md`](docs/methodology.md).

---

## Business questions

1. Which crops improved the most since 1990?
2. What happens after removing the long-run yield and warming trends?
3. Which crops show the strongest negative interannual temperature association?
4. Is there really one “perfect temperature” for yield?
5. Does more precipitation always mean better yield?
6. What can irrigation and fertilizer tell us — and where is coverage too weak?
7. Which country-crop combinations combine volatility with negative temperature association?
8. Can a model trained on the past beat strong historical baselines on 2018+ data?
9. Where does the model fail?

---

## Modeling design

The predictive task is intentionally different from the descriptive climate analysis.

**Train:** 1990–2017  
**Test:** 2018–2023

The model starts from each country × crop's historical training-period yield level and predicts a residual correction using:

- temperature anomaly relative to the **training-period** country normal,
- precipitation anomaly relative to the **training-period** country normal,
- fertilizer anomaly relative to the **training-period** country normal,
- crop identity.

Using train-only normals prevents future climate information from leaking into the model.

The result is compared with:

1. crop median,
2. country × crop historical median,
3. last observed pre-2018 yield (persistence).

The persistence comparison is the hardest and most decision-relevant baseline in V1.

---

## Project structure

```text
climate-crop-yield-intelligence/
├── .github/workflows/
│   ├── ci.yml
│   └── live-data-smoke.yml
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
├── scripts/
│   └── run_live_analysis.py
├── slides/
│   └── presentation_story.md
├── src/climate_crop_yield/
│   ├── data.py
│   ├── features.py
│   ├── model.py
│   └── plots.py
├── tests/
├── README.md
├── RUN_IN_COLAB.md
├── pyproject.toml
└── requirements.txt
```

---

## Reproduce it

### Google Colab

Open `notebooks/01_climate_crop_yield_business_analysis.ipynb` with the repository available, install the requirements, then **Run all**.

### Local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest -q
python scripts/run_live_analysis.py
jupyter notebook
```

### GitHub Actions

Two workflows protect the project:

- **CI** — runs the offline test suite on every push / pull request.
- **Live data validation** — downloads the real public datasets, rebuilds the analysis panel and runs the full live analysis report.

---

## What V1 does *not* claim

This project does **not** claim that temperature, precipitation, fertilizer or irrigation *cause* the observed yield changes.

Country-level annual data cannot directly capture:

- growing-season heat extremes,
- rainfall timing,
- soil and field conditions,
- planting dates,
- cultivar choice,
- irrigation efficiency,
- local management quality,
- prices and policy changes.

The risk score is a screening tool, and the predictive model is a country-level decision-support baseline — not a farm-level forecasting system.

---

## Presentation

The portfolio presentation is designed as a client story rather than a classroom report:

### **From Warming to Yield — Where Climate Risk Hits Agriculture First**

See [`slides/presentation_story.md`](slides/presentation_story.md).

---

<details>
<summary><strong>Project history</strong></summary>

The core business idea was first explored in a university analysis around **2022**.

The **2026** project was rebuilt from the ground up using updated public data, six crop series, stronger methodology, time-aware model evaluation, error analysis, tests and a reproducible repository structure.

**v1.0 is the first public portfolio release.**

The old university notebook is not included in the main repository; it is retained only as historical source material and a style reference.

</details>

---

## Author

**Ahmed Wadee**  
Data Science · AI · Engineering
