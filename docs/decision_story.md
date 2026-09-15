# Decision Story — What I found, what I changed, and why

I keep this file simple on purpose. It is the short reasoning trail behind the project, so I can come back later and remember **why** the code looks the way it does.

## 1. I found crop scales were very different

Potatoes can have much larger yield values in `t/ha` than cereals.

So I did **not** use raw `t/ha per +1°C` as the main cross-crop sensitivity ranking.

I converted detrended yield residuals into **% of each country-crop system's mean yield** and use `% yield per +1°C` for the public comparison.

Why: I want the comparison to reflect relative movement, not just crop scale.

## 2. I found the early and recent samples could contain different countries

A simple 1990–1994 median versus 2019–2023 median can move because the available country sample changed.

So I match the same country-crop histories across both windows and require at least three observed years in each window.

Why: the long-run change should be about yield movement, not sample composition.

## 3. I found one global temperature binning scheme mixed different crop distributions

Different crops are grown in very different temperature ranges.

So I build temperature quantile bins **inside each crop**.

Why: the chart is exploratory. I do not want one crop's geography to define another crop's temperature groups.

## 4. I found fertilizer was being mixed into the word “climate”

The first predictive draft used temperature, precipitation and fertilizer together.

So I split the experiment into:

- **Climate only** — temperature + precipitation anomalies;
- **Climate + fertilizer** — the same features plus fertilizer anomaly.

Why: now I can answer two separate questions: what climate adds, and what fertilizer adds on top.

## 5. I found full-period climate normals would leak future information into prediction

Full-period country means are useful for descriptive EDA, but the test years should not help define the training normal.

So the predictive model calculates climate and fertilizer normals using **training years only**.

Why: the 2018–2023 holdout stays genuinely future data.

## 6. I found a complex model can look good against a weak baseline

A global or crop-only median is easy to beat.

So I keep three simple references:

- crop median;
- country × crop historical median;
- persistence: the last pre-2018 observed yield.

Why: if the ML model cannot beat recent history, that is important information and I keep it in the project.

## 7. I found irrigation coverage was too weak for the core model

Only about one fifth of the final panel has an observed irrigation value.

So I keep irrigation in exploratory analysis only.

Why: mostly imputing a weakly observed feature can make the model look more complete than the data really is.

## 8. I changed the word “risk” to “screening” where precision matters

The ranking combines detrended volatility and negative relative temperature association. It is not an insurance probability or crop-loss forecast.

So the public language calls it a **screening score** or **priority screen**.

Why: the name should match what the calculation can actually support.

## The rule I want to reuse

For future projects I want the reasoning to read like this:

> **I found X → I changed Y → because Z → I did not use shortcut A because B.**

That is easier to study, easier to review, and harder to fake with pretty charts.
