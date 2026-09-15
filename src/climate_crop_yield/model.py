from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# Irrigation is intentionally excluded from the core model because the live
# country-year panel has low coverage for this feature. It remains useful for
# descriptive analysis on the observed subset.
NUMERIC_FEATURES = [
    "temperature_c",
    "temp_deviation_c",
    "precipitation_mm",
    "precip_deviation_mm",
    "fertilizer_kg_ha",
]

CATEGORICAL_FEATURES = ["crop", "Code"]


@dataclass
class ModelResult:
    model: Pipeline
    metrics: dict[str, float]
    predictions: pd.DataFrame
    split_year: int
    baseline_mae: float


def build_model(random_state: int = 42) -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ]
    )

    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
            ),
        ]
    )

    pre = ColumnTransformer(
        transformers=[
            ("num", numeric, NUMERIC_FEATURES),
            ("cat", categorical, CATEGORICAL_FEATURES),
        ]
    )

    reg = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=3,
        random_state=random_state,
        n_jobs=-1,
    )

    return Pipeline([("prep", pre), ("model", reg)])


def _safe_improvement(model_mae: float, baseline_mae: float) -> float:
    if baseline_mae == 0:
        return float("nan")
    return float(100 * (baseline_mae - model_mae) / baseline_mae)


def _baseline_predictions(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> dict[str, np.ndarray]:
    """Create progressively stronger, time-safe baselines from training data only."""
    global_median = float(train["yield_t_ha"].median())

    crop_medians = train.groupby("crop")["yield_t_ha"].median()
    crop_pred = test["crop"].map(crop_medians).fillna(global_median).to_numpy()

    country_crop_medians = train.groupby(["Code", "crop"])["yield_t_ha"].median()
    cc_keys = pd.MultiIndex.from_frame(test[["Code", "crop"]])
    cc_pred = country_crop_medians.reindex(cc_keys).to_numpy(dtype=float)
    cc_pred = np.where(np.isnan(cc_pred), crop_pred, cc_pred)

    last_rows = (
        train.sort_values(["Code", "crop", "Year"])
        .groupby(["Code", "crop"], as_index=False)
        .tail(1)
        .set_index(["Code", "crop"])["yield_t_ha"]
    )
    persistence_pred = last_rows.reindex(cc_keys).to_numpy(dtype=float)
    persistence_pred = np.where(np.isnan(persistence_pred), cc_pred, persistence_pred)

    return {
        "crop_median": crop_pred,
        "country_crop_median": cc_pred,
        "persistence": persistence_pred,
    }


def fit_time_split(
    df: pd.DataFrame,
    split_year: int = 2018,
    random_state: int = 42,
) -> ModelResult:
    needed = set(NUMERIC_FEATURES + CATEGORICAL_FEATURES + ["yield_t_ha", "Year"])
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing modeling columns: {sorted(missing)}")

    model_df = df.dropna(subset=["yield_t_ha"]).copy()

    train = model_df[model_df["Year"] < split_year].copy()
    test = model_df[model_df["Year"] >= split_year].copy()

    if train.empty or test.empty:
        raise ValueError("Time split produced an empty train or test set")

    X_train = train[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train = train["yield_t_ha"]
    X_test = test[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_test = test["yield_t_ha"]

    baselines = _baseline_predictions(train, test)
    baseline_maes = {
        name: float(mean_absolute_error(y_test, values))
        for name, values in baselines.items()
    }

    model = build_model(random_state=random_state)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    model_mae = float(mean_absolute_error(y_test, pred))

    pred_df = test[["Entity", "Code", "Year", "crop", "yield_t_ha"]].copy()
    pred_df["predicted_yield_t_ha"] = pred
    pred_df["persistence_yield_t_ha"] = baselines["persistence"]
    pred_df["abs_error"] = (pred_df["yield_t_ha"] - pred_df["predicted_yield_t_ha"]).abs()
    pred_df["persistence_abs_error"] = (
        pred_df["yield_t_ha"] - pred_df["persistence_yield_t_ha"]
    ).abs()

    metrics = {
        "model_mae": model_mae,
        "mae": model_mae,
        "r2": float(r2_score(y_test, pred)),
        "crop_median_mae": baseline_maes["crop_median"],
        "country_crop_median_mae": baseline_maes["country_crop_median"],
        "persistence_mae": baseline_maes["persistence"],
        "baseline_mae": baseline_maes["persistence"],
        "mae_improvement_vs_baseline_pct": _safe_improvement(
            model_mae, baseline_maes["persistence"]
        ),
        "mae_improvement_vs_country_crop_median_pct": _safe_improvement(
            model_mae, baseline_maes["country_crop_median"]
        ),
        "test_rows": float(len(test)),
    }

    return ModelResult(
        model=model,
        metrics=metrics,
        predictions=pred_df,
        split_year=split_year,
        baseline_mae=baseline_maes["persistence"],
    )
