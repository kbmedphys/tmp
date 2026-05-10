"""エンドツーエンドパイプライン。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import PipelineConfig, load_config
from .data_io import (
    load_market_turnover,
    load_prices,
    load_theme_definitions,
    load_theme_holdings,
    save_csv,
    save_parquet,
)
from .dedup import deduplicate_headlines
from .embeddings import encode_texts_with_cache
from .exposure import build_exposure
from .headlines import fetch_headlines
from .intensity import build_topic_intensity
from .market import build_market_targets, build_theme_market_series
from .preprocess import clean_headlines
from .supervised import fit_supervised_models
from .theme import build_theme_profiles, map_topics_to_themes
from .topics import build_topic_tables, fit_topic_model, transform_topics
from .trends import build_trends_alerts_rankings



def _select_fit_sample(df: pd.DataFrame, cfg: PipelineConfig) -> pd.DataFrame:
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce")

    fit_start = cfg.topic_model.fit_start
    fit_end = cfg.topic_model.fit_end

    if fit_start:
        out = out[out["timestamp"] >= pd.to_datetime(fit_start, utc=True)]
    if fit_end:
        out = out[out["timestamp"] <= pd.to_datetime(fit_end, utc=True)]

    if out.empty:
        raise ValueError("BERTopic学習期間に該当するニュースがありません。")
    return out.reset_index(drop=True)



def run_pipeline(config_path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    cfg = load_config(config_path)

    raw_df, normalized_df = fetch_headlines(cfg)
    clean_df = clean_headlines(
        normalized_df,
        mode=cfg.preprocess.low_information_mode,
        min_chars=cfg.preprocess.min_headline_chars,
    )

    cache_path = cfg.resolve_path(cfg.embedding.headline_cache_path)
    assert cache_path is not None

    emb_meta, all_embeddings = encode_texts_with_cache(
        ids=clean_df["news_id"],
        texts=clean_df["headline_clean"],
        cache_path=cache_path,
        model_name=cfg.embedding.model_name,
        batch_size=cfg.embedding.batch_size,
        normalize_embeddings=cfg.embedding.normalize_embeddings,
    )

    dedup_df, dedup_log = deduplicate_headlines(
        clean_df,
        embeddings=all_embeddings,
        similarity_threshold=cfg.dedup.similarity_threshold,
        window_hours=cfg.dedup.window_hours,
    )

    # news_idキーで clean_df の埋め込み行番号を再取得
    clean_pos = clean_df.reset_index()[["index", "news_id"]]
    dedup_indexer = (
        dedup_df[["news_id"]]
        .merge(clean_pos, on="news_id", how="left")["index"]
        .to_numpy(dtype=int)
    )
    dedup_emb = all_embeddings[dedup_indexer]

    fit_df = _select_fit_sample(dedup_df, cfg)
    dedup_pos = dedup_df.reset_index()[["index", "news_id"]]
    fit_idx = (
        fit_df[["news_id"]]
        .merge(dedup_pos, on="news_id", how="left")["index"]
        .to_numpy(dtype=int)
    )
    fit_emb = dedup_emb[fit_idx]

    topic_model, fit_tables = fit_topic_model(fit_df, fit_emb, cfg.topic_model)
    topic_assignments = transform_topics(dedup_df, topic_model, dedup_emb)
    topic_tables = build_topic_tables(topic_assignments, topic_model, cfg.topic_model.top_n_headlines)

    daily_intensity, weekly_intensity, outlier_stats = build_topic_intensity(
        topic_assignments,
        weekly_rule=cfg.topic_intensity.weekly_rule,
        ewma_span=cfg.topic_intensity.ewma_span,
        lookback=cfg.topic_intensity.lookback,
        z_threshold=cfg.topic_intensity.z_threshold,
        aggregate_timezone=cfg.topic_intensity.aggregate_timezone,
    )

    theme_df = load_theme_definitions(cfg.resolve_path(cfg.paths.theme_definitions_path))
    theme_profiles = build_theme_profiles(theme_df)
    topic_theme_map = map_topics_to_themes(
        topic_tables["topic_summary"],
        theme_profiles,
        model_name=cfg.embedding.model_name,
        similarity_threshold=cfg.theme_map.similarity_threshold,
        top_n_themes_per_topic=cfg.theme_map.top_n_themes_per_topic,
    )

    exposure_daily = build_exposure(daily_intensity, topic_theme_map, intensity_col="topic_ewma")

    holdings = load_theme_holdings(cfg.resolve_path(cfg.paths.theme_holdings_path))
    prices = load_prices(cfg.resolve_path(cfg.paths.prices_path))
    market_turn = load_market_turnover(cfg.resolve_path(cfg.paths.market_turnover_path))

    theme_market = build_theme_market_series(holdings, prices)
    targets = build_market_targets(theme_market, market_turnover_df=market_turn, horizon=5)

    beta_df, pred_df = fit_supervised_models(
        exposure_daily,
        targets,
        model_type=cfg.regression.model_type,
        min_obs_per_theme=cfg.regression.min_obs_per_theme,
        time_series_splits=cfg.regression.time_series_splits,
        ridge_alphas=cfg.regression.ridge_alphas,
        elasticnet_alphas=cfg.regression.elasticnet_alphas,
        elasticnet_l1_ratio=cfg.regression.elasticnet_l1_ratio,
    )

    trend_df, alert_df, ranking_df, explanation_df = build_trends_alerts_rankings(
        exposure_daily,
        beta_df,
        topic_tables["topic_summary"],
        topic_theme_map,
        theme_profiles,
        trend_ewma_span=cfg.trend.trend_ewma_span,
        trend_lookback=cfg.trend.trend_lookback,
        surge_threshold=cfg.trend.surge_threshold,
        uptrend_threshold=cfg.trend.uptrend_threshold,
        persistent_threshold=cfg.trend.persistent_threshold,
    )

    table_dir = cfg.resolve_path(cfg.paths.output_tables_dir)
    assert table_dir is not None
    save_parquet(normalized_df, table_dir / "news_normalized.parquet")
    save_parquet(clean_df, table_dir / "news_clean.parquet")
    save_parquet(dedup_df, table_dir / "news_dedup.parquet")
    save_parquet(dedup_log, table_dir / "dedup_log.parquet")
    save_parquet(emb_meta, table_dir / "headline_embedding_meta.parquet")
    save_parquet(topic_assignments, table_dir / "topic_assignments.parquet")
    save_parquet(topic_tables["topic_summary"], table_dir / "topic_summary.parquet")
    save_parquet(outlier_stats, table_dir / "topic_outlier_stats.parquet")
    save_parquet(daily_intensity, table_dir / "topic_intensity_daily.parquet")
    save_parquet(weekly_intensity, table_dir / "topic_intensity_weekly.parquet")
    save_parquet(theme_profiles, table_dir / "theme_profiles.parquet")
    save_parquet(topic_theme_map, table_dir / "topic_theme_map.parquet")
    save_parquet(exposure_daily, table_dir / "theme_topic_exposure_daily.parquet")
    save_parquet(targets, table_dir / "market_targets.parquet")
    save_parquet(beta_df, table_dir / "model_betas.parquet")
    save_parquet(pred_df, table_dir / "model_predictions.parquet")
    save_parquet(trend_df, table_dir / "theme_trends.parquet")
    save_parquet(alert_df, table_dir / "theme_alerts.parquet")
    save_parquet(ranking_df, table_dir / "theme_rankings.parquet")
    save_parquet(explanation_df, table_dir / "theme_explanations.parquet")

    save_csv(ranking_df, table_dir / "theme_rankings.csv")
    save_csv(alert_df, table_dir / "theme_alerts.csv")

    return {
        "raw_df": raw_df,
        "normalized_df": normalized_df,
        "clean_df": clean_df,
        "dedup_df": dedup_df,
        "dedup_log": dedup_log,
        "topic_assignments": topic_assignments,
        "topic_summary": topic_tables["topic_summary"],
        "daily_intensity": daily_intensity,
        "weekly_intensity": weekly_intensity,
        "topic_theme_map": topic_theme_map,
        "exposure_daily": exposure_daily,
        "targets": targets,
        "beta_df": beta_df,
        "pred_df": pred_df,
        "trend_df": trend_df,
        "alert_df": alert_df,
        "ranking_df": ranking_df,
        "explanation_df": explanation_df,
        "fit_tables": fit_tables["train_assignments"],
    }
