# Presentation Story
## From Warming to Yield — Where Climate Risk Hits Agriculture First

### Slide 1 — The Business Problem
**Visual:** one strong crop/climate image + one sentence.

A global agribusiness client needs to know which crop-location combinations deserve attention first under climate pressure — and whether climate variables improve short-horizon yield prediction enough to support decisions.

### Slide 2 — The Data Backbone
**Visual:** 4-source pipeline + coverage numbers.

FAO crop yields → ERA5 temperature / precipitation → fertilizer → irrigation → country-year-crop panel.

Validated V1 panel:
- **24,892** country × year × crop rows
- **187** countries / territories
- **6** crops
- **1990–2023**
- yield coverage: **100%**
- temperature / precipitation: **97.59%**
- fertilizer: **97.15%**
- irrigation: only **22.64%**

**Takeaway:** irrigation stays exploratory because most rows do not have an observed value.

### Slide 3 — Six Crops, Very Different Production Trends
**Visual:** small multiples or indexed crop-yield trend chart.

Median yield change from 1990–1994 to 2019–2023:
- Maize: **+121.60%**
- Barley: **+48.27%**
- Potatoes: **+47.00%**
- Rice: **+46.66%**
- Wheat: **+42.18%**
- Soybeans: **+28.67%**

**Takeaway:** long-run productivity changed a lot, so raw climate-yield correlation is not enough.

### Slide 4 — Removing the Time Trend Changes the Climate Story
**Visual:** detrended crop sensitivity bar chart.

After removing the linear time trend within each country × crop history, all six pooled annual temperature associations are negative:
- Potatoes: **-0.2725 t/ha per +1°C**
- Maize: **-0.1715**
- Barley: **-0.0765**
- Soybeans: **-0.0752**
- Wheat: **-0.0443**
- Rice: **-0.0241**

**Takeaway:** warmer-than-trend years tend to align with lower-than-trend yield in this country-level panel, but this is still association — not causal proof.

### Slide 5 — There Is No Magic Temperature
**Visual:** temperature-bin yield chart.

The earlier university analysis selected one exact observed temperature as the “best”. V1 replaces that with ranges and a more cautious interpretation.

**Takeaway:** one sparse continuous observation should not be presented as a physiological optimum.

### Slide 6 — Water and Management Change the Story
**Visual:** precipitation response + fertilizer groups + irrigation coverage callout.

Climate and management variables are useful context, but their data quality is not equal. Irrigation has only **22.64%** coverage and is excluded from the core model rather than being mostly imputed.

**Takeaway:** feature selection is partly a data-quality decision, not just a modeling decision.

### Slide 7 — The Risk Matrix
**Visual:** 2D matrix: detrended warming penalty × detrended yield volatility.

Highest V1 priority segments:
1. **Oman × Barley — 0.9856**
2. **Oman × Maize — 0.9856**
3. **Rwanda × Potatoes — 0.9794**
4. **Cameroon × Potatoes — 0.9760**
5. **Paraguay × Potatoes — 0.9739**

The volatility component is calculated around each country × crop's own long-run yield trend, so sustained improvement is not mistaken for instability.

**Takeaway:** this is a screening score for where to investigate first, not an insurance-grade probability of loss.

### Slide 8 — Can Climate Features Beat Strong Historical Baselines?
**Visual:** four-bar MAE comparison.

Train: **1990–2017**  
Test: **2018–2023**

MAE:
- Crop median: **3.4478 t/ha**
- Country × crop historical median: **1.6192**
- Climate-anomaly residual model: **1.4473**
- Persistence, last pre-2018 yield: **0.8976**

Model R²: **0.9038**

**Takeaway:** the model improves on the static country × crop median by **10.62%**, but is **61.24% worse than persistence**.

### Slide 9 — The Failure Is Part of the Result
**Visual:** error by crop.

The climate-anomaly model does not beat the strongest simple baseline.

Crop MAE examples:
- Potatoes: **3.8919 t/ha** — hardest crop
- Maize: **1.3076**
- Rice: **0.7826**
- Barley: **0.7132**
- Wheat: **0.6420**
- Soybeans: **0.4160** — lowest error

**Takeaway:** recent production history carries more short-horizon predictive information than annual country-level climate and fertilizer anomalies alone.

### Slide 10 — Client Action
**Visual:** 3-step decision playbook.

1. Prioritize the highest-risk country-crop segments for deeper review.
2. Add local growing-season, heat-extreme, rainfall-timing and farm-management data before operational decisions.
3. Keep persistence as the minimum forecasting benchmark; only deploy a more complex model when it beats that benchmark consistently.

### Validation / Reproducibility Footer
The live GitHub Actions workflow rebuilds the public-data panel, runs the analysis, executes the portfolio notebook end to end, and uploads:
- the executed notebook, and
- `live_analysis_summary.json`

as the `validated-live-analysis` artifact.

### Final line
**Climate risk cannot be removed, but it can be measured earlier, tested honestly and prioritized better.**
