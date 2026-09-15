# Methodology Notes

## Unit of analysis
Country × year × crop.

## Main period
1990–2023, chosen to maximize overlap between crop, climate, fertilizer and irrigation data.

## Why country-centered temperature?
A raw global temperature-yield correlation mostly compares different climates, countries, technologies and crop systems.
The project therefore adds a within-country temperature deviation:

`annual temperature - country's mean temperature over the analysis panel`

This does not create causality, but it is a more relevant descriptive signal for "warmer-than-usual years".

## No single-degree optimum
The old analysis selected an exact observed temperature with the highest mean yield.
V1 replaces this with temperature bins to reduce sensitivity to noisy or sparse exact values.

## Predictive evaluation
The predictive model uses a time split:
- Train: years before 2018
- Test: 2018 onward

The model is compared against a simple crop-median baseline from the training period.

## Causal limitations
Fertilizer, irrigation and climate variables are observational and aggregated.
Associations must not be described as treatment effects.
