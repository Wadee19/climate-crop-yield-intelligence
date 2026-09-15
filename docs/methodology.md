# Methodology Notes

## Unit of analysis

The core panel is **country × year × crop** for six crops from **1990–2023**:

Wheat, Maize, Rice, Potatoes, Soybeans and Barley.

Only three-letter country / territory codes are kept. OWID aggregate codes such as `OWID_AFR` and `OWID_WRL` are excluded before the panel is built.

## Validated live panel

The corrected live validation contains:

- **24,892** country-year-crop rows
- **187** countries / territories
- **6** crops
- **100%** yield coverage
- **97.59%** temperature coverage
- **97.59%** precipitation coverage
- **97.15%** fertilizer coverage
- **22.64%** irrigation coverage

Irrigation is therefore exploratory only and is excluded from the core predictive experiment.

## Long-run yield change

The project compares **1990–1994** with **2019–2023** using the **same country cohort in both windows**.

A country-crop history must have at least three observations in each window. The crop-level headline is then based on the median of those matched country medians.

This reduces sample-composition bias from countries entering or leaving the data between the two periods.

## Descriptive climate deviations

For exploratory plots, annual temperature and precipitation are centered around each country's mean over the analysis panel.

One climate observation per country-year is used when calculating the normal, so countries are not implicitly weighted by how many crop records are available.

These full-period deviations are descriptive only.

## Detrended relative temperature association

A raw temperature-yield relationship is confounded by long-run time trends.

For every country × crop history, V1 removes a linear time trend from:

- annual temperature;
- annual crop yield.

The yield residual is then divided by that country-crop history's mean yield and multiplied by 100.

The public cross-crop comparison is therefore:

`detrended yield deviation (%) ~ detrended temperature deviation (°C)`

This produces a relative slope in **% yield deviation per +1°C**.

Why relative units: crops have very different natural yield scales, so raw `t/ha per °C` is retained only as a secondary diagnostic, not the primary cross-crop ranking.

The relationship remains observational and non-causal.

## Temperature ranges

Temperature bins are created **inside each crop**, using eight quantile groups.

The bins are exploratory ranges. They are not interpreted as physiological optima and no exact degree is presented as a universal “best temperature”.

## Management comparison

Irrigation and fertilizer are observational country-level indicators.

For the management plot:

- yield is expressed as an index relative to each crop's median;
- management quartiles are created inside each crop.

This makes the descriptive chart less dominated by differences in absolute crop yield scale. It does not create a causal estimate.

## Screening score

The country-crop priority screen requires at least **20 usable observations** and combines two scale-aware signals:

1. standard deviation of detrended yield residuals, expressed in percentage points;
2. the negative part of the detrended relative temperature-yield slope, expressed as `% yield per +1°C`.

Each component is percentile-ranked, then the two ranks are averaged.

The output is a **screening score** for where deeper investigation may be useful. It is not a loss probability, causal climate-damage estimate, insurance score or investment recommendation.

## Predictive experiment

The forecasting experiment uses a strict time split:

- **Train:** 1990–2017
- **Test:** 2018–2023

All temperature, precipitation and fertilizer normals used for predictive anomalies are calculated from the **training period only**.

The model predicts a residual correction around each country × crop's historical training-period median yield.

## Ablation: climate first, fertilizer second

Two Random Forest models use the same architecture:

### Climate only

- temperature anomaly
- precipitation anomaly
- crop identity

### Climate + fertilizer

- temperature anomaly
- precipitation anomaly
- fertilizer anomaly
- crop identity

This separation prevents fertilizer from being mislabeled as climate information.

Random Forest settings:

- `n_estimators = 250`
- `min_samples_leaf = 5`
- `random_state = 42`

These values are fixed before evaluating the 2018+ holdout and are not tuned against the test period.

## Strong baselines

The models are compared with:

1. crop median from training data;
2. country × crop median from training data;
3. persistence — last observed pre-2018 yield for that country × crop.

Validated corrected holdout results:

- crop median MAE: **3.4478 t/ha**
- country × crop median MAE: **1.6192 t/ha**
- climate-only MAE: **1.4816 t/ha**
- climate + fertilizer MAE: **1.4473 t/ha**
- persistence MAE: **0.8976 t/ha**
- climate + fertilizer R²: **0.9038**

Climate-only improves on the static country × crop median by **8.50%**. Adding fertilizer improves MAE by a further **2.32%** relative to climate-only.

Persistence remains substantially stronger than either ML model.

## Reproducibility guard

The live GitHub Actions workflow:

1. downloads the public data;
2. builds and validates the panel;
3. runs the package analysis;
4. generates the README figures from that live run;
5. executes the standalone portfolio notebook end to end;
6. compares the notebook headline metrics with the package-generated metrics;
7. uploads the summaries, figures and executed notebook as validation artifacts.

This reduces the chance that the README, notebook and package silently drift apart.

## Causal limitations

Country-year data do not directly capture growing-season heat extremes, rainfall timing, crop calendars, local soils, cultivar choice, planting dates, irrigation efficiency, farm-level management, prices or policy changes.

The project is therefore a reproducible screening and predictive case study, not a farm-level causal model.
