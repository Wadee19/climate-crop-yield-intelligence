# Presentation Story
## From Warming to Yield — Where Climate Pressure Appears First

### Slide 1 — The Business Problem
**Visual:** one crop/climate image + one sentence.

This is an agribusiness decision case study. I want to know which crop-location combinations deserve attention first, and whether annual climate information improves short-horizon yield prediction.

### Slide 2 — The Data Backbone
**Visual:** source pipeline + coverage numbers.

FAO crop yields → ERA5 temperature / precipitation → fertilizer → irrigation → country-year-crop panel.

Validated V1 panel:
- **24,892** country × year × crop rows
- **187** countries / territories
- **6** crops
- **1990–2023**
- yield coverage: **100%**
- temperature / precipitation: **97.59%**
- fertilizer: **97.15%**
- irrigation: **22.64%**

**Decision:** irrigation stays exploratory because most rows do not have an observed value.

### Slide 3 — Yield Changed a Lot, So I Matched the Same Countries
**Visual:** `01_matched_yield_change.png`.

Median yield change from 1990–1994 to 2019–2023, using the same country cohort in both windows:
- Maize: **+106.75%**
- Rice: **+52.40%**
- Potatoes: **+50.06%**
- Barley: **+48.59%**
- Wheat: **+38.51%**
- Soybeans: **+18.02%**

**Why:** I did not want changing country coverage to look like production growth.

### Slide 4 — I Normalized the Temperature Comparison
**Visual:** `03_temperature_sensitivity_relative.png`.

After removing the linear time trend inside each country × crop history, the relative annual temperature associations are:
- Maize: **-4.41% yield per +1°C**
- Soybeans: **-4.38%**
- Barley: **-3.59%**
- Wheat: **-2.39%**
- Potatoes: **-1.47%**
- Rice: **-0.95%**

**Why:** raw `t/ha per °C` was not a fair cross-crop comparison because crop yield scales are very different.

**Takeaway:** all six pooled associations are negative, but they remain observational and non-causal.

### Slide 5 — There Is No Magic Temperature
**Visual:** crop-specific temperature ranges.

I use broad temperature groups inside each crop instead of selecting one exact observed degree and calling it the optimum.

**Why:** I want an exploratory view, not a fake physiological threshold.

### Slide 6 — Management Data Are Useful, but Coverage Matters
**Visual:** normalized management groups + irrigation coverage callout.

Irrigation has only **22.64%** coverage, so I keep it out of the core prediction model.

**Why:** mostly imputing a weakly observed variable would make the model look more complete than the evidence is.

### Slide 7 — Where Should I Investigate First?
**Visual:** screening scatter or top-five table.

Highest corrected V1 screening segments:
1. **Oman × Barley — 0.9930**
2. **Turkmenistan × Maize — 0.9916**
3. **Cape Verde × Maize — 0.9839**
4. **Malawi × Wheat — 0.9832**
5. **Rwanda × Potatoes — 0.9783**

The screen combines detrended yield volatility with negative relative temperature association and requires at least **20 usable observations**.

**Takeaway:** this is a priority screen, not a crop-loss probability.

### Slide 8 — I Separated Climate Value from Fertilizer Value
**Visual:** `08_model_ablation_baselines.png`.

Train: **1990–2017**  
Test: **2018–2023**

MAE:
- Persistence: **0.8976 t/ha**
- Climate + fertilizer: **1.4473**
- Climate only: **1.4816**
- Country × crop historical median: **1.6192**
- Crop median: **3.4478**

Climate-only improves on the country × crop median by **8.50%**. Fertilizer adds a further **2.32%** improvement relative to climate-only. Full-model R² is **0.9038**.

**Takeaway:** climate adds signal, fertilizer adds a little more, but persistence still wins.

### Slide 9 — The Failure Is Part of the Result
**Visual:** error by crop.

Full-model mean absolute error by crop:
- Potatoes: **3.8919 t/ha**
- Maize: **1.3076**
- Rice: **0.7826**
- Barley: **0.7132**
- Wheat: **0.6420**
- Soybeans: **0.4160**

**Takeaway:** recent production history carries more short-horizon predictive information than these annual country-level features alone.

### Slide 10 — What I Would Do Next
**Visual:** 3-step decision playbook.

1. Investigate the highest screening segments with local agronomic context.
2. Add growing-season heat extremes, rainfall timing, crop calendars and more local management data.
3. Keep persistence as the minimum forecasting benchmark; only deploy a more complex model when it beats that benchmark consistently.

### Validation / Reproducibility Footer
The live GitHub Actions workflow:
- rebuilds the public-data panel;
- runs the package analysis;
- generates the validated figures;
- executes the standalone notebook end to end;
- checks notebook/package headline parity;
- uploads the summaries, figures and executed notebook as artifacts.

### Final line
**Climate pressure can be screened more carefully, and a simple baseline can still be the right benchmark.**
