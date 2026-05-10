"""topic exposure の正則化回帰。"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler



def _pivot_exposure(exposure_df: pd.DataFrame) -> pd.DataFrame:
    pivot = exposure_df.pivot_table(
        index=["date", "theme_id"],
        columns="topic_id",
        values="theme_topic_exposure",
        aggfunc="sum",
        fill_value=0.0,
    )
    pivot.columns = [f"topic_{c}" for c in pivot.columns]
    return pivot.reset_index()



def _fit_one_model(
    x: pd.DataFrame,
    y: pd.Series,
    model_type: str,
    n_splits: int,
    ridge_alphas: list[float],
    elasticnet_alphas: list[float],
    elasticnet_l1_ratio: list[float],
):
    if len(x) < 6:
        raise ValueError("観測数不足のためモデル推定不可")

    splits = max(2, min(int(n_splits), len(x) - 1))
    tscv = TimeSeriesSplit(n_splits=splits)

    if model_type == "ridge":
        estimator = Ridge(random_state=None)
        param_grid = {"model__alpha": ridge_alphas}
    elif model_type == "elasticnet":
        estimator = ElasticNet(max_iter=20000)
        param_grid = {
            "model__alpha": elasticnet_alphas,
            "model__l1_ratio": elasticnet_l1_ratio,
        }
    else:
        raise ValueError("model_type は 'ridge' または 'elasticnet' を指定してください。")

    pipe = Pipeline([("scaler", StandardScaler()), ("model", estimator)])
    gs = GridSearchCV(pipe, param_grid=param_grid, cv=tscv, scoring="neg_mean_squared_error")
    gs.fit(x, y)
    return gs



def fit_supervised_models(
    exposure_df: pd.DataFrame,
    market_targets_df: pd.DataFrame,
    model_type: str = "ridge",
    min_obs_per_theme: int = 60,
    time_series_splits: int = 5,
    ridge_alphas: list[float] | None = None,
    elasticnet_alphas: list[float] | None = None,
    elasticnet_l1_ratio: list[float] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """テーマごとに attention/return を推定する。"""
    ridge_alphas = ridge_alphas or [0.1, 1.0, 10.0, 100.0]
    elasticnet_alphas = elasticnet_alphas or [0.001, 0.01, 0.1, 1.0]
    elasticnet_l1_ratio = elasticnet_l1_ratio or [0.2, 0.5, 0.8]

    required_exposure = {"date", "theme_id", "topic_id", "theme_topic_exposure"}
    required_targets = {"date", "theme_id", "y_attention", "y_return"}

    missing_e = sorted(required_exposure - set(exposure_df.columns))
    missing_t = sorted(required_targets - set(market_targets_df.columns))
    if missing_e:
        raise ValueError(f"exposure_df 必須カラム不足: {missing_e}")
    if missing_t:
        raise ValueError(f"market_targets_df 必須カラム不足: {missing_t}")

    x_wide = _pivot_exposure(exposure_df)
    dataset = x_wide.merge(market_targets_df[["date", "theme_id", "y_attention", "y_return"]], on=["date", "theme_id"], how="inner")
    dataset["date"] = pd.to_datetime(dataset["date"], errors="coerce")

    feature_cols = [c for c in dataset.columns if c.startswith("topic_")]

    beta_rows: list[dict[str, object]] = []
    pred_rows: list[dict[str, object]] = []

    for target_col in ["y_attention", "y_return"]:
        target_label = "attention" if target_col == "y_attention" else "return"

        for theme_id, g in dataset.groupby("theme_id"):
            g = g.sort_values("date").dropna(subset=[target_col]).copy()
            n_obs = len(g)

            if n_obs < int(min_obs_per_theme):
                beta_rows.append(
                    {
                        "theme_id": str(theme_id),
                        "topic_id": "__SKIPPED__",
                        "target": target_label,
                        "beta": np.nan,
                        "n_obs": int(n_obs),
                        "model_type": model_type,
                        "fitted": False,
                        "scaler": "StandardScaler",
                        "cv": "TimeSeriesSplit",
                        "best_params": "{}",
                    }
                )
                continue

            x = g[feature_cols].fillna(0.0)
            y = g[target_col].astype(float)

            try:
                gs = _fit_one_model(
                    x,
                    y,
                    model_type=model_type,
                    n_splits=time_series_splits,
                    ridge_alphas=ridge_alphas,
                    elasticnet_alphas=elasticnet_alphas,
                    elasticnet_l1_ratio=elasticnet_l1_ratio,
                )
            except ValueError:
                beta_rows.append(
                    {
                        "theme_id": str(theme_id),
                        "topic_id": "__SKIPPED__",
                        "target": target_label,
                        "beta": np.nan,
                        "n_obs": int(n_obs),
                        "model_type": model_type,
                        "fitted": False,
                        "scaler": "StandardScaler",
                        "cv": "TimeSeriesSplit",
                        "best_params": "{}",
                    }
                )
                continue

            model = gs.best_estimator_.named_steps["model"]
            coefs = np.asarray(model.coef_, dtype=float)
            for col, beta in zip(feature_cols, coefs):
                topic_id = col.replace("topic_", "")
                beta_rows.append(
                    {
                        "theme_id": str(theme_id),
                        "topic_id": topic_id,
                        "target": target_label,
                        "beta": float(beta),
                        "n_obs": int(n_obs),
                        "model_type": model_type,
                        "fitted": True,
                        "scaler": "StandardScaler",
                        "cv": "TimeSeriesSplit",
                        "best_params": json.dumps(gs.best_params_, ensure_ascii=False),
                    }
                )

            y_hat = gs.predict(x)
            for dt, y_true, y_pred in zip(g["date"], y, y_hat):
                pred_rows.append(
                    {
                        "date": pd.Timestamp(dt),
                        "theme_id": str(theme_id),
                        "target": target_label,
                        "y_true": float(y_true),
                        "y_pred": float(y_pred),
                        "model_type": model_type,
                    }
                )

    beta_df = pd.DataFrame(beta_rows)
    pred_df = pd.DataFrame(pred_rows)
    return beta_df, pred_df
