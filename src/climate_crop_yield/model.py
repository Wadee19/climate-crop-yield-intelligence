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


MODEL_NUMERIC_FEATURES = [
    "temp_anomaly_c",
    "precip_anomaly_mm",
    "fertilizer_anomaly_kg_ha",
]
MODEL_CATEGORICAL_FEATURES = ["crop"]

SOURCE_FEATURES = [
    "temperature_c",
    "precipitation_mm",
    "fertilizer_kg_ha",
]


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
            ("num", numeric, MODEL_NUMERIC_FEATURES),
            ("cat", categorical, MODEL_CATEGORICAL_FEATURES),
        ]
    )

    reg = RandomForestRegressor(
        n_estimators=250,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=-1,
    )

    return Pipeline([("prep", pre), ("model", reg)])


def _safe_improvement(model_mae: float, baseline_mae: float) -> float:
    if baseline_mae == 0:
        return float("nan")
    return float(100 * (baseline_mae - model_mae) / baseline_mae)


def _map_group_values(
    frame: pd.DataFrame,
    values: pd.Series,
) -> np.ndarray:
    keys = pd.MultiIndex.from_frame(frame[["Code", "crop"]])
    return values.reindex(keys).to_numpy(dtype=float)


def _baseline_predictions(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Create time-safe baselines and the training country-crop reference level."""
    global_median = float(train["yield_t_ha"].median())

    crop_medians = train.groupby("crop")["yield_t_ha"].median()
    crop_test = test["crop"].map(crop_medians).fillna(global_median).to_numpy()
    crop_train = train["crop"].map(crop_medians).fillna(global_median).to_numpy()

    country_crop_medians = train.groupby(["Code", "crop"])["yield_t_ha"].median()
    cc_test = _map_group_values(test, country_crop_medians)
    cc_test = np.where(np.isnan(cc_test), crop_test, cc_test)

    cc_train = _map_group_values(train, country_crop_medians)
    cc_train = np.where(np.isnan(cc_train), crop_train, cc_train)

    last_rows = (
        train.sort_values(["Code", "crop", "Year"])
        .groupby(["Code", "crop"], as_index=False)
        .tail(1)
        .set_index(["Code", "crop"])["yield_t_ha"]
    )
    persistence = _map_group_values(test, last_rows)
    persistence = np.where(np.isnan(persistence), cc_test, persistence)

    return (
        {
            "crop_median": crop_test,
            "country_crop_median": cc_test,
            "persistence": persistence,
        },
        cc_train,
    )


def _add_train_based_anomalies(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create climate/input anomalies using training-period country normals only."""
    unique_train = (
        train[["Code", "Year"] + SOURCE_FEATURES]
        .drop_duplicates(["Code", "Year"])
        .copy()
    )
    normals = unique_train.groupby("Code")[SOURCE_FEATURES].mean()
    global_normals = unique_train[SOURCE_FEATURES].mean()

    names = {
        "temperature_c": "temp_anomaly_c",
        "precipitation_mm": "precip_anomaly_mm",
        "fertilizer_kg_ha": "fertilizer_anomaly_kg_ha",
    }

    def transform(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        for source, target in names.items():
            normal = out["Code"].map(normals[source]).fillna(global_normals[source])
            out[target] = out[source] - normal
        return out

    return transform(train), transform(test)


def fit_time_split(
    df: pd.DataFrame,
    split_year: int = 2018,
    random_state: int = 42,
) -> ModelResult:
    needed = set(SOURCE_FEATURES + ["crop", "Code", "yield_t_ha", "Year"])
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing modeling columns: {sorted(missing)}")

    model_df = df.dropna(subset=["yield_t_ha"]).copy()
    train = model_df[model_df["Year"] < split_year].copy()
    test = model_df[model_df["Year"] >= split_year].copy()

    if train.empty or test.empty:
        raise ValueError("Time split produced an empty train or test set")

    baselines, train_reference = _baseline_predictions(train, test)
    train, test = _add_train_based_anomalies(train, test)

    X_train = train[MODEL_NUMERIC_FEATURES + MODEL_CATEGORICAL_FEATURES]
    X_test = test[MODEL_NUMERIC_FEATURES + MODEL_CATEGORICAL_FEATURES]

    # Learn only the deviation from the historical country-crop yield level.
    y_train_residual = train["yield_t_ha"].to_numpy() - train_reference

    model = build_model(random_state=random_state)
    model.fit(X_train, y_train_residual)
    residual_pred = model.predict(X_test)
    pred = baselines["country_crop_median"] + residual_pred

    y_test = test["yield_t_ha"].to_numpy()
    model_mae = float(mean_absolute_error(y_test, pred))
    baseline_maes = {
        name: float(mean_absolute_error(y_test, values))
        for name, values in baselines.items()
    }

    pred_df = test[["Entity", "Code", "Year", "crop", "yield_t_ha"]].copy()
    pred_df["historical_country_crop_yield_t_ha"] = baselines["country_crop_median"]
    pred_df["persistence_yield_t_ha"] = baselines["persistence"]
    pred_df["predicted_yield_t_ha"] = pred
    pred_df["predicted_residual_t_ha"] = residual_pred
    pred_df["abs_error"] = np.abs(y_test - pred)
    pred_df["persistence_abs_error"] = np.abs(y_test - baselines["persistence"])

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
