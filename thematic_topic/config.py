"""設定ロードとディレクトリ管理。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LSEGFetchSettings:
    query: str = "Language:LJA AND Source:RTRS"
    start: str = "2024-01-01T00:00:00Z"
    end: str = "2024-12-31T23:59:59Z"
    count: int = 100
    order_by: str = "new_to_old"
    chunk_days: int = 7
    cache_dir: str = "data/raw/headlines"
    force_refresh: bool = False


@dataclass
class PreprocessSettings:
    low_information_mode: str = "drop"
    min_headline_chars: int = 8


@dataclass
class DedupSettings:
    similarity_threshold: float = 0.92
    window_hours: int = 24


@dataclass
class EmbeddingSettings:
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    normalize_embeddings: bool = True
    batch_size: int = 64
    headline_cache_path: str = "data/processed/headline_embeddings.parquet"


@dataclass
class TopicModelSettings:
    top_n_words: int = 15
    top_n_headlines: int = 10
    fit_start: str | None = None
    fit_end: str | None = None
    umap_n_neighbors: int = 15
    umap_n_components: int = 5
    umap_min_dist: float = 0.0
    umap_metric: str = "cosine"
    random_state: int = 42
    hdbscan_min_cluster_size: int = 30
    hdbscan_metric: str = "euclidean"
    hdbscan_cluster_selection_method: str = "eom"
    calculate_probabilities: bool = True
    language: str = "multilingual"
    tokenizer_stopwords: list[str] = field(
        default_factory=lambda: [
            "する",
            "ある",
            "いる",
            "なる",
            "れる",
            "られる",
            "こと",
            "もの",
            "ため",
            "よう",
            "これ",
            "それ",
            "市場",
            "発表",
            "方針",
            "検討",
            "関係者",
            "日本",
            "円",
            "ドル",
            "株",
            "ニュース",
            "ロイター",
        ]
    )


@dataclass
class TopicIntensitySettings:
    weekly_rule: str = "W-FRI"
    ewma_span: int = 5
    lookback: int = 20
    z_threshold: float = 1.0
    aggregate_timezone: str = "Asia/Tokyo"


@dataclass
class ThemeMapSettings:
    similarity_threshold: float = 0.35
    top_n_themes_per_topic: int = 5


@dataclass
class RegressionSettings:
    model_type: str = "ridge"
    min_obs_per_theme: int = 60
    time_series_splits: int = 5
    ridge_alphas: list[float] = field(default_factory=lambda: [0.1, 1.0, 10.0, 100.0])
    elasticnet_alphas: list[float] = field(default_factory=lambda: [0.001, 0.01, 0.1, 1.0])
    elasticnet_l1_ratio: list[float] = field(default_factory=lambda: [0.2, 0.5, 0.8])


@dataclass
class TrendSettings:
    trend_ewma_span: int = 5
    trend_lookback: int = 60
    surge_threshold: float = 2.0
    uptrend_threshold: float = 1.0
    persistent_threshold: int = 5


@dataclass
class PathSettings:
    theme_definitions_path: str = "data/raw/theme_definitions.parquet"
    theme_holdings_path: str = "data/raw/theme_holdings.parquet"
    prices_path: str = "data/raw/prices.parquet"
    market_turnover_path: str | None = None
    output_tables_dir: str = "outputs/tables"
    output_figures_dir: str = "outputs/figures"
    output_logs_dir: str = "outputs/logs"


@dataclass
class PipelineConfig:
    project_root: Path
    lseg_fetch: LSEGFetchSettings = field(default_factory=LSEGFetchSettings)
    preprocess: PreprocessSettings = field(default_factory=PreprocessSettings)
    dedup: DedupSettings = field(default_factory=DedupSettings)
    embedding: EmbeddingSettings = field(default_factory=EmbeddingSettings)
    topic_model: TopicModelSettings = field(default_factory=TopicModelSettings)
    topic_intensity: TopicIntensitySettings = field(default_factory=TopicIntensitySettings)
    theme_map: ThemeMapSettings = field(default_factory=ThemeMapSettings)
    regression: RegressionSettings = field(default_factory=RegressionSettings)
    trend: TrendSettings = field(default_factory=TrendSettings)
    paths: PathSettings = field(default_factory=PathSettings)

    def resolve_path(self, relative_or_abs: str | None) -> Path | None:
        if relative_or_abs is None:
            return None
        candidate = Path(relative_or_abs)
        if candidate.is_absolute():
            return candidate
        return self.project_root / candidate

    def ensure_directories(self) -> None:
        directories = [
            self.resolve_path(self.lseg_fetch.cache_dir),
            self.resolve_path("data/processed"),
            self.resolve_path(self.paths.output_tables_dir),
            self.resolve_path(self.paths.output_figures_dir),
            self.resolve_path(self.paths.output_logs_dir),
        ]
        for directory in directories:
            if directory is not None:
                directory.mkdir(parents=True, exist_ok=True)



def _as_dataclass(data: dict[str, Any], cls: type[Any]) -> Any:
    base = cls()
    for key in data:
        if not hasattr(base, key):
            raise ValueError(f"未知の設定キーです: {cls.__name__}.{key}")
    for key, value in data.items():
        setattr(base, key, value)
    return base



def load_config(path: str | Path | None = None, project_root: str | Path | None = None) -> PipelineConfig:
    if project_root is None:
        project_root = Path.cwd().resolve()
    else:
        project_root = Path(project_root).resolve()

    if path is None:
        path = project_root / "config" / "default.yaml"
    else:
        path = Path(path)
        if not path.is_absolute():
            path = project_root / path

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cfg = PipelineConfig(project_root=project_root)
    if "lseg_fetch" in raw:
        cfg.lseg_fetch = _as_dataclass(raw["lseg_fetch"], LSEGFetchSettings)
    if "preprocess" in raw:
        cfg.preprocess = _as_dataclass(raw["preprocess"], PreprocessSettings)
    if "dedup" in raw:
        cfg.dedup = _as_dataclass(raw["dedup"], DedupSettings)
    if "embedding" in raw:
        cfg.embedding = _as_dataclass(raw["embedding"], EmbeddingSettings)
    if "topic_model" in raw:
        cfg.topic_model = _as_dataclass(raw["topic_model"], TopicModelSettings)
    if "topic_intensity" in raw:
        cfg.topic_intensity = _as_dataclass(raw["topic_intensity"], TopicIntensitySettings)
    if "theme_map" in raw:
        cfg.theme_map = _as_dataclass(raw["theme_map"], ThemeMapSettings)
    if "regression" in raw:
        cfg.regression = _as_dataclass(raw["regression"], RegressionSettings)
    if "trend" in raw:
        cfg.trend = _as_dataclass(raw["trend"], TrendSettings)
    if "paths" in raw:
        cfg.paths = _as_dataclass(raw["paths"], PathSettings)

    cfg.ensure_directories()
    return cfg
