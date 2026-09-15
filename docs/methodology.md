# Methodology Notes

## Unit of analysis

The core panel is **country × year × crop**.

V1 analyzes six crops from 1990–2023:

- Wheat
- Maize
- Rice
- Potatoes
- Soybeans
- Barley

Only true three-letter ISO country / territory codes are retained. OWID aggregate rows such as `OWID_AFR` and `OWID_WRL` are excluded before the datasets are merged.

## Data overlap and coverage

The 1990–2023 window was selected to create useful overlap between crop yield, temperature, precipitation, fertilizer and irrigation data.

The validated live panel contains:

- 24,892 country-year-crop rows
- 187 countries / territories
- 100% yield coverage
- 97.59% temperature coverage
- 97.59% precipitation coverage
- 97.15% fertilizer coverage
- 22.64% irrigation coverage

Because irrigation is observed for less than one quarter of the panel, it is used for exploratory analysis only and is **not** included in the core predictive model.

## Long-term crop trends

Yield trends are summarized by comparing the median crop yield in 1990–1994 with 2019–2023.

This comparison is descriptive. It does not attribute yield improvement to climate, fertilizer, technology or any other single cause.

## Climate deviations for EDA

The notebook creates country-centered temperature and precipitation deviations for descriptive plots:

`annual value - country mean over the analysis panel`

These full-period deviations are useful for EDA but are deliberately **not used as predictive features**, because doing so would let the test period influence the climate normal.

## Detrended temperature sensitivity

A raw temperature-yield correlation is strongly confounded by time. Agricultural productivity has generally improved over the same decades in which temperatures have trended upward.

To reduce this trend confounding, V1 removes a linear year trend separately inside every country × crop history for both:

- annual temperature, and
- crop yield.

The pooled crop-level sensitivity is then estimated from:

`detrended yield residual ~ detrended temperature residual`

This asks whether warmer-than-trend years tend to coincide with yield above or below that production system's own trend.

It is still an **association**, not a causal treatment effect.

## No single-degree optimum

The earlier university analysis selected one exact observed temperature with the highest mean yield and treated it as an optimum.

V1 does not do this. Exact continuous values are too sparse and noisy for that interpretation. Temperature ranges / bins are used instead, and any apparent optimum is treated as descriptive rather than physiological proof.

## Risk prioritization score

The country-crop risk screen combines:

1. **yield volatility** — coefficient of variation of historical yield, and
2. **warming penalty** — the negative part of the country-crop detrended temperature-yield slope.

Each component is converted to a percentile rank, and the two ranks are averaged.

The score is intended to answer:

> Which country-crop histories deserve deeper local investigation first?

It is not an insurance model, crop-loss probability, causal climate-damage estimate or investment recommendation by itself.

A country-crop history must have at least 15 usable observations to enter the ranking.

## Predictive evaluation

The forecasting experiment uses a strict time split:

- **Train:** years before 2018
- **Test:** 2018 onward

The model does not use the full-period descriptive climate deviations.

Instead, country climate / fertilizer normals are calculated from the **training period only**, and the predictive features are:

- temperature anomaly from the train-period country normal,
- precipitation anomaly from the train-period country normal,
- fertilizer anomaly from the train-period country normal,
- crop identity.

The model predicts a residual correction around each country × crop's historical training-period yield level.

## Baselines

V1 reports three baselines instead of comparing the model only with an easy global average:

1. crop median from the training period,
2. country × crop median from the training period,
3. persistence — the final observed pre-2018 yield for that country × crop.

The persistence baseline is the hardest comparison because annual crop yield often has strong temporal continuity.

Validated 2018+ results:

- crop median MAE: 3.4478 t/ha
- country × crop median MAE: 1.6192 t/ha
- climate-anomaly residual model MAE: 1.4473 t/ha
- persistence MAE: 0.8976 t/ha
- model R²: 0.9038

The model improves on the static country × crop median by 10.62%, but it does not beat persistence. That failure is retained as a real project result.

## Causal limitations

All climate and management variables are observational and aggregated at country-year level.

Associations must not be described as treatment effects.

The data do not directly capture growing-season heat extremes, rainfall timing, soil properties, planting dates, cultivar choice, irrigation efficiency, farm-level management, prices or policy changes.

The project therefore treats V1 as a reproducible screening and decision-support analysis, not a farm-level causal model.
