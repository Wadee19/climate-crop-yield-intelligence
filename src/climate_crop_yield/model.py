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


CLIMATE_FEATURES = ["temp_anomaly_c", "precip_anomaly_mm"]
FULL_FEATURES = CLIMATE_FEATURES + ["fertilizer_anomaly_kg_ha"]
MODEL_CATEGORICAL_FEATURES = ["crop"]
SOURCE_FEATURES = ["temperature_c", "precipitation_mm", "fertilizer_kg_ha"]


@dataclass
class ModelResult:
    climate_only_model: Pipeline
    climate_plus_fertilizer_model: Pipeline
    metrics: dict[str, float]
    predictions: pd.DataFrame
    split_year: int


def build_model(numeric_features: list[str], random_state: int = 42) -> Pipeline:
    numeric = Pipeline(
        [("imputer", SimpleImputer(strategy="median", add_indicator=True))]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]
    )
    pre = ColumnTransformer(
        [
            ("num", numeric, numeric_features),
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


def _map_group_values(frame: pd.DataFrame, values: pd.Series) -> np.ndarray:
    keys = pd.MultiIndex.from_frame(frame[["Code", "crop"]])
    return values.reindex(keys).to_numpy(dtype=float)


def _baseline_predictions(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
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


def _fit_residual_model(
    train: pd.DataFrame,
    test: pd.DataFrame,
    train_reference: np.ndarray,
    test_reference: np.ndarray,
    numeric_features: list[str],
    random_state: int,
) -> tuple[Pipeline, np.ndarray]:
    model = build_model(numeric_features=numeric_features, random_state=random_state)
    columns = numeric_features + MODEL_CATEGORICAL_FEATURES
    y_train_residual = train["yield_t_ha"].to_numpy() - train_reference
    model.fit(train[columns], y_train_residual)
    pred = test_reference + model.predict(test[columns])
    return model, pred


def fit_time_split(
    df: pd.DataFrame,
    split_year: int = 2018,
    random_state: int = 42,
) -> ModelResult:
    needed = set(SOURCE_FEATURES + ["crop", "Code", "yield_t_ha", "Year", "Entity"])
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

    climate_model, climate_pred = _fit_residual_model(
        train,
        test,
        train_reference,
        baselines["country_crop_median"],
        CLIMATE_FEATURES,
        random_state,
    )
    full_model, full_pred = _fit_residual_model(
        train,
        test,
        train_reference,
        baselines["country_crop_median"],
        FULL_FEATURES,
        random_state,
    )

    y_test = test["yield_t_ha"].to_numpy()
    climate_mae = float(mean_absolute_error(y_test, climate_pred))
    full_mae = float(mean_absolute_error(y_test, full_pred))
    baseline_maes = {
        name: float(mean_absolute_error(y_test, values))
        for name, values in baselines.items()
    }

    pred_df = test[["Entity", "Code", "Year", "crop", "yield_t_ha"]].copy()
    pred_df["country_crop_median_yield_t_ha"] = baselines["country_crop_median"]
    pred_df["persistence_yield_t_ha"] = baselines["persistence"]
    pred_df["climate_only_predicted_yield_t_ha"] = climate_pred
    pred_df["predicted_yield_t_ha"] = full_pred
    pred_df["abs_error"] = np.abs(y_test - full_pred)
    pred_df["climate_only_abs_error"] = np.abs(y_test - climate_pred)
    pred_df["persistence_abs_error"] = np.abs(y_test - baselines["persistence"])

    metrics = {
        "crop_median_mae": baseline_maes["crop_median"],
        "country_crop_median_mae": baseline_maes["country_crop_median"],
        "climate_only_mae": climate_mae,
        "climate_plus_fertilizer_mae": full_mae,
        "persistence_mae": baseline_maes["persistence"],
        "climate_only_improvement_vs_country_crop_median_pct": _safe_improvement(
            climate_mae, baseline_maes["country_crop_median"]
        ),
        "fertilizer_incremental_improvement_vs_climate_pct": _safe_improvement(
            full_mae, climate_mae
        ),
        "full_model_r2": float(r2_score(y_test, full_pred)),
        "test_rows": float(len(test)),
    }

    return ModelResult(
        climate_only_model=climate_model,
        climate_plus_fertilizer_model=full_model,
        metrics=metrics,
        predictions=pred_df,
        split_year=split_year,
    )
