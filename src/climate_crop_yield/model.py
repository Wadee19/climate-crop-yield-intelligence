from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


NUMERIC_FEATURES = [
    "temperature_c",
    "temp_deviation_c",
    "precipitation_mm",
    "precip_deviation_mm",
    "fertilizer_kg_ha",
    "irrigated_land_pct",
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
            ("imputer", SimpleImputer(strategy="median")),
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
        n_estimators=250,
        min_samples_leaf=3,
        random_state=random_state,
        n_jobs=-1,
    )

    return Pipeline([("prep", pre), ("model", reg)])


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

    crop_medians = train.groupby("crop")["yield_t_ha"].median()
    global_median = float(y_train.median())
    baseline_pred = test["crop"].map(crop_medians).fillna(global_median).to_numpy()
    baseline_mae = float(mean_absolute_error(y_test, baseline_pred))

    model = build_model(random_state=random_state)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    pred_df = test[["Entity", "Code", "Year", "crop", "yield_t_ha"]].copy()
    pred_df["predicted_yield_t_ha"] = pred
    pred_df["abs_error"] = (pred_df["yield_t_ha"] - pred_df["predicted_yield_t_ha"]).abs()

    metrics = {
        "mae": float(mean_absolute_error(y_test, pred)),
        "r2": float(r2_score(y_test, pred)),
        "baseline_mae": baseline_mae,
        "mae_improvement_vs_baseline_pct": float(
            100 * (baseline_mae - mean_absolute_error(y_test, pred)) / baseline_mae
        ),
    }

    return ModelResult(
        model=model,
        metrics=metrics,
        predictions=pred_df,
        split_year=split_year,
        baseline_mae=baseline_mae,
    )
