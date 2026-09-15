# Methodology

## Scope

V1 uses a country × year × crop panel for six crops from 1990–2023. The project is a portfolio case study and a country-level screening / forecasting exercise, not a causal agronomy study or a farm-level operational model.

## 1. Long-run yield change

The headline early-vs-recent comparison uses the **same country cohort** in both windows:

- early: 1990–1994
- recent: 2019–2023
- at least 3 observed years in each window

For every country × crop, the median yield is calculated inside each window. Only histories observed in both windows are kept. Crop-level early and recent medians are then calculated across that matched cohort.

This prevents changing country coverage from driving the headline trend.

## 2. Descriptive climate features

For exploratory analysis, annual temperature and precipitation are centered on each country's full-period mean. These full-period deviations are **not** used by the predictive model.

Year-to-year yield change is shown with 1st–99th percentile clipping only for visualization. The original yield observations are unchanged.

## 3. Detrending and cross-crop sensitivity

Temperature and yield can both trend over time. V1 therefore removes a linear time trend inside each country × crop history before comparing annual deviations.

For cross-crop comparison, the yield residual is expressed as a percentage of that country-crop history's mean yield:

`relative yield residual (%) = 100 × detrended yield residual / mean yield`

The public sensitivity metric is the pooled slope:

`relative yield residual (%) ~ detrended temperature residual (°C)`

This is more scale-aware than comparing raw t/ha slopes across crops such as potatoes and wheat. It is still a descriptive association, not a causal temperature effect.

## 4. Temperature ranges

Temperature bins are quantile-based and created **inside each crop**. They are exploratory ranges only; no bin is presented as a physiological optimum.

## 5. Management variables

Irrigation and fertilizer are country-level observational indicators. Irrigation coverage is limited, so irrigation remains exploratory and is not used in the predictive model.

Management plots use a within-crop yield index to avoid directly comparing the absolute t/ha scale of potatoes with cereals. These plots are descriptive and do not estimate treatment effects.

## 6. Screening score

The V1 screening score is a transparent prioritization heuristic with two scale-aware components:

1. standard deviation of detrended relative yield residuals (%), and
2. the negative part of the relative temperature-yield slope (% yield per +1°C).

Country × crop histories need at least **20 usable observations**. Each component is converted to a percentile rank and the two ranks are weighted 50/50.

The score is not a probability of loss, an insurance estimate, or proof that temperature caused yield changes.

## 7. Prediction and leakage control

The predictive task uses a fixed past-to-future split:

- train: 1990–2017
- test: 2018–2023

Each country × crop starts from its training-period median yield. The model predicts a residual correction.

Climate and fertilizer anomalies are calculated using **training-period country normals only**. Test-period values never enter those normals.

Two Random Forest residual models are evaluated with identical settings:

- **climate-only:** temperature anomaly + precipitation anomaly + crop identity
- **climate + fertilizer:** the climate features + fertilizer anomaly + crop identity

This ablation separates the predictive value of climate from the incremental value of fertilizer.

Random Forest settings:

- 250 trees
- `min_samples_leaf = 5`
- `random_state = 42`

These parameters are fixed before test evaluation and are not tuned against the 2018–2023 holdout.

## 8. Baselines

Both models are compared with:

1. crop median,
2. country × crop training-period median,
3. fixed persistence: the last observed pre-2018 yield for that country × crop.

The fixed persistence baseline uses no 2018–2023 labels. It is therefore a clean single-origin benchmark across the full holdout.

## 9. Reproducibility

The repository pins the validated Python data stack in `requirements.txt`. GitHub Actions:

1. downloads the live public datasets,
2. rebuilds the panel,
3. runs the full analysis summary,
4. executes the notebook end to end,
5. uploads the executed notebook, generated figures, and machine-readable summary as an artifact.

Public narrative metrics are normally rounded to three decimals to avoid implying meaningful precision in the last environment-dependent digit.
