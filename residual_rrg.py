"""Residual RRG utilities for theme-basket rotation.

This module is designed as an add-on to ``theme_basket_strategy.py``.
It uses ``results_l3['theme_residual_returns']`` as the preferred input
and creates a Relative Rotation Graph (RRG)-like representation for themes.

Key idea
--------
Classic RRG is built from relative strength and the momentum of relative
strength. Here we build those quantities from factor-residualized theme
returns, so the chart emphasizes theme-specific residual leadership rather
than market / style / sector beta.

Dependencies: pandas, numpy, matplotlib, and theme_basket_strategy.py.
"""
from __future__ import annotations

import os
from dataclasses import replace
from typing import Dict, Iterable, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from theme_basket_strategy import (
    StrategyConfig,
    backtest_theme_weights,
    construct_theme_weights,
    make_rebalance_dates,
    performance_metrics,
    zscore_cross_sectional,
)


ArrayLikeFrame = Union[pd.DataFrame, pd.Series]


def rolling_time_series_zscore(
    x: pd.DataFrame,
    window: int = 252,
    min_periods: Optional[int] = None,
    std_floor: float = 1e-8,
    winsor: Optional[float] = 5.0,
) -> pd.DataFrame:
    """Rolling time-series z-score for each column.

    Notes
    -----
    The signal at date t uses information up to t. Existing backtest helpers
    in ``theme_basket_strategy.py`` lag weights by one day, so this is safe
    for a daily close-to-close backtest if signals are formed after the close.
    """
    if min_periods is None:
        min_periods = max(20, window // 2)
    y = x.copy().sort_index().replace([np.inf, -np.inf], np.nan)
    mu = y.rolling(window=window, min_periods=min_periods).mean()
    sd = y.rolling(window=window, min_periods=min_periods).std(ddof=0)
    z = (y - mu) / sd.clip(lower=std_floor)
    if winsor is not None:
        z = z.clip(-winsor, winsor)
    return z


def _as_aligned_series(x: pd.Series, index: pd.Index, name: str = "benchmark") -> pd.Series:
    s = x.copy().sort_index().replace([np.inf, -np.inf], np.nan)
    s.name = name
    return s.reindex(index).astype(float)


def residual_relative_strength(
    residual_returns: pd.DataFrame,
    benchmark_returns: Optional[pd.Series] = None,
    window: int = 126,
    min_periods: Optional[int] = None,
    peer_relative: bool = True,
    vol_adjust: bool = True,
    vol_floor: float = 1e-4,
) -> pd.DataFrame:
    """Compute residual relative strength for each theme.

    Parameters
    ----------
    residual_returns:
        Date x theme residual return matrix.
    benchmark_returns:
        Optional benchmark return series. If supplied, each theme residual is
        measured relative to this benchmark. If omitted and ``peer_relative``
        is True, the benchmark is the cross-sectional mean residual return.
    window:
        Lookback window for cumulative relative residual return.
    min_periods:
        Minimum observations. If omitted, max(20, window//2).
    peer_relative:
        If True and benchmark_returns is None, subtract cross-sectional mean.
        If False and no benchmark is supplied, use residual_returns directly.
    vol_adjust:
        If True, divide cumulative relative residual return by rolling
        residual-relative volatility, creating a t-stat-like relative strength.
    vol_floor:
        Lower bound for volatility denominator.

    Returns
    -------
    DataFrame of residual relative strength, date x theme.
    """
    if min_periods is None:
        min_periods = max(20, window // 2)

    ret = residual_returns.copy().sort_index().replace([np.inf, -np.inf], np.nan)

    if benchmark_returns is not None:
        b = _as_aligned_series(benchmark_returns, ret.index)
        rel = ret.sub(b, axis=0)
    elif peer_relative:
        peer = ret.mean(axis=1, skipna=True)
        rel = ret.sub(peer, axis=0)
    else:
        rel = ret

    rs = rel.rolling(window=window, min_periods=min_periods).sum()
    if vol_adjust:
        vol = rel.rolling(window=window, min_periods=min_periods).std(ddof=0)
        rs = rs / vol.clip(lower=vol_floor)
    return rs.replace([np.inf, -np.inf], np.nan)


def classify_rrg_quadrants(
    rs_ratio: pd.DataFrame,
    rs_momentum: pd.DataFrame,
    center: float = 100.0,
) -> pd.DataFrame:
    """Classify each theme/date into RRG quadrants."""
    x = rs_ratio.reindex_like(rs_momentum)
    y = rs_momentum
    quad = pd.DataFrame(np.nan, index=y.index, columns=y.columns, dtype=object)
    valid = x.notna() & y.notna()
    quad[valid & (x >= center) & (y >= center)] = "Leading"
    quad[valid & (x >= center) & (y < center)] = "Weakening"
    quad[valid & (x < center) & (y < center)] = "Lagging"
    quad[valid & (x < center) & (y >= center)] = "Improving"
    return quad


def _angle_diff(theta: pd.DataFrame) -> pd.DataFrame:
    """Wrapped one-period angular difference in radians."""
    d = theta - theta.shift(1)
    return ((d + np.pi) % (2 * np.pi)) - np.pi


def make_residual_rrg(
    residual_returns: pd.DataFrame,
    benchmark_returns: Optional[pd.Series] = None,
    rs_window: int = 126,
    rs_min_periods: Optional[int] = None,
    z_window: int = 252,
    z_min_periods: Optional[int] = None,
    momentum_lag: int = 21,
    smoothing_span: int = 10,
    peer_relative: bool = True,
    vol_adjust: bool = True,
    center: float = 100.0,
    scale: float = 10.0,
    winsor: Optional[float] = 5.0,
) -> Dict[str, pd.DataFrame]:
    """Build residual-RRG coordinates and derived features.

    Output fields
    -------------
    - ``residual_relative_strength``: rolling relative residual strength.
    - ``rs_ratio_z``: time-series z-score of smoothed relative strength.
    - ``rs_momentum_z``: time-series z-score of momentum of relative strength.
    - ``rs_ratio``: RRG x-axis, centered at 100.
    - ``rs_momentum``: RRG y-axis, centered at 100.
    - ``quadrant``: Leading / Weakening / Lagging / Improving.
    - ``distance``: distance from the RRG center.
    - ``angle``: polar angle around the RRG center, radians.
    - ``rotation_speed``: wrapped one-period angle change, radians.
    - ``rrg_score``: simple strategy score; positive in Improving/Leading.
    """
    ret = residual_returns.copy().sort_index().replace([np.inf, -np.inf], np.nan)

    rs_raw = residual_relative_strength(
        ret,
        benchmark_returns=benchmark_returns,
        window=rs_window,
        min_periods=rs_min_periods,
        peer_relative=peer_relative,
        vol_adjust=vol_adjust,
    )

    if smoothing_span and smoothing_span > 1:
        rs_smooth = rs_raw.ewm(span=smoothing_span, adjust=False, min_periods=max(2, smoothing_span // 2)).mean()
    else:
        rs_smooth = rs_raw

    rs_ratio_z = rolling_time_series_zscore(
        rs_smooth,
        window=z_window,
        min_periods=z_min_periods,
        winsor=winsor,
    )

    rs_mom_raw = rs_smooth - rs_smooth.shift(momentum_lag)
    rs_momentum_z = rolling_time_series_zscore(
        rs_mom_raw,
        window=z_window,
        min_periods=z_min_periods,
        winsor=winsor,
    )

    rs_ratio = center + scale * rs_ratio_z
    rs_momentum = center + scale * rs_momentum_z
    quadrant = classify_rrg_quadrants(rs_ratio, rs_momentum, center=center)

    dx = rs_ratio - center
    dy = rs_momentum - center
    distance = np.sqrt(dx.pow(2) + dy.pow(2))
    angle = pd.DataFrame(np.arctan2(dy.to_numpy(dtype=float), dx.to_numpy(dtype=float)), index=ret.index, columns=ret.columns)
    rotation_speed = _angle_diff(angle)

    # A transparent RRG strategy score. The quadrant filter is applied later.
    # This keeps the raw score available for diagnostics.
    rrg_score = 0.55 * rs_ratio_z + 0.45 * rs_momentum_z

    latest_rows = []
    if len(ret.index) > 0:
        last_valid_date = rs_ratio.dropna(how="all").index.max()
        if pd.notna(last_valid_date):
            for theme in ret.columns:
                latest_rows.append({
                    "date": last_valid_date,
                    "theme": theme,
                    "rs_ratio": rs_ratio.at[last_valid_date, theme] if theme in rs_ratio.columns else np.nan,
                    "rs_momentum": rs_momentum.at[last_valid_date, theme] if theme in rs_momentum.columns else np.nan,
                    "quadrant": quadrant.at[last_valid_date, theme] if theme in quadrant.columns else np.nan,
                    "distance": distance.at[last_valid_date, theme] if theme in distance.columns else np.nan,
                    "angle": angle.at[last_valid_date, theme] if theme in angle.columns else np.nan,
                    "rotation_speed": rotation_speed.at[last_valid_date, theme] if theme in rotation_speed.columns else np.nan,
                    "rrg_score": rrg_score.at[last_valid_date, theme] if theme in rrg_score.columns else np.nan,
                })
    latest_summary = pd.DataFrame(latest_rows)
    if not latest_summary.empty:
        latest_summary = latest_summary.sort_values(["quadrant", "rrg_score"], ascending=[True, False])

    return {
        "residual_relative_strength": rs_raw,
        "residual_relative_strength_smooth": rs_smooth,
        "rs_ratio_z": rs_ratio_z,
        "rs_momentum_z": rs_momentum_z,
        "rs_ratio": rs_ratio,
        "rs_momentum": rs_momentum,
        "quadrant": quadrant,
        "distance": distance,
        "angle": angle,
        "rotation_speed": rotation_speed,
        "rrg_score": rrg_score,
        "latest_summary": latest_summary,
    }


def _eligibility_from_results(
    results_l3: Dict[str, object],
    index: pd.Index,
    columns: Sequence[str],
    min_effective_n: float = 5.0,
    use_hard_gate: bool = True,
) -> pd.DataFrame:
    """Build an eligibility mask from Level-3 coherence outputs if available."""
    eligibility = pd.DataFrame(True, index=index, columns=columns)

    apc = results_l3.get("coherence_apc")
    if isinstance(apc, pd.DataFrame):
        eligibility &= apc.reindex(index).ffill().reindex(columns=columns).notna()

    eff = results_l3.get("coherence_effective_n")
    if isinstance(eff, pd.DataFrame):
        eligibility &= eff.reindex(index).ffill().reindex(columns=columns) >= min_effective_n

    if use_hard_gate:
        gate = results_l3.get("coherence_gate")
        if isinstance(gate, pd.DataFrame):
            eligibility &= gate.reindex(index).ffill().reindex(columns=columns).fillna(False)

    return eligibility.fillna(False)


def build_residual_rrg_scores(
    results_l3: Dict[str, object],
    benchmark_returns: Optional[pd.Series] = None,
    rs_window: int = 126,
    rs_min_periods: Optional[int] = None,
    z_window: int = 252,
    z_min_periods: Optional[int] = None,
    momentum_lag: int = 21,
    smoothing_span: int = 10,
    peer_relative: bool = True,
    vol_adjust: bool = True,
    use_hard_gate: bool = True,
    min_effective_n: float = 5.0,
    allowed_quadrants: Tuple[str, ...] = ("Improving", "Leading"),
    require_positive_momentum: bool = True,
    crowding_penalty: float = 0.0,
    winsor: Optional[float] = 5.0,
) -> Dict[str, object]:
    """Create residual-RRG score matrices from ``results_l3``.

    The preferred signal input is ``results_l3['theme_residual_returns']``.
    If unavailable, the function falls back to ``results_l3['theme_returns']``.
    """
    if "theme_residual_returns" in results_l3 and isinstance(results_l3["theme_residual_returns"], pd.DataFrame):
        residual_returns = results_l3["theme_residual_returns"].copy()
    elif "theme_returns" in results_l3 and isinstance(results_l3["theme_returns"], pd.DataFrame):
        residual_returns = results_l3["theme_returns"].copy()
    else:
        raise KeyError("results_l3 must contain 'theme_residual_returns' or 'theme_returns'.")

    rrg = make_residual_rrg(
        residual_returns=residual_returns,
        benchmark_returns=benchmark_returns,
        rs_window=rs_window,
        rs_min_periods=rs_min_periods,
        z_window=z_window,
        z_min_periods=z_min_periods,
        momentum_lag=momentum_lag,
        smoothing_span=smoothing_span,
        peer_relative=peer_relative,
        vol_adjust=vol_adjust,
        winsor=winsor,
    )

    base_score = rrg["rrg_score"].copy()
    quadrant = rrg["quadrant"]
    eligibility = _eligibility_from_results(
        results_l3,
        index=base_score.index,
        columns=base_score.columns,
        min_effective_n=min_effective_n,
        use_hard_gate=use_hard_gate,
    )

    if allowed_quadrants:
        qmask = quadrant.isin(list(allowed_quadrants))
    else:
        qmask = pd.DataFrame(True, index=base_score.index, columns=base_score.columns)

    if require_positive_momentum:
        qmask &= rrg["rs_momentum"] > 100.0

    score = base_score.where(eligibility & qmask)

    if crowding_penalty and crowding_penalty > 0:
        crowd = results_l3.get("crowding_score")
        if isinstance(crowd, pd.DataFrame):
            c = crowd.reindex(score.index).ffill().reindex(columns=score.columns).fillna(0.0)
            # Penalize only positive crowding/acceleration. Negative crowding is not rewarded.
            score = score - crowding_penalty * c.clip(lower=0.0)
            score = score.where(eligibility & qmask)

    return {
        "rrg": rrg,
        "eligibility": eligibility,
        "rrg_strategy_score": score,
    }


def run_residual_rrg_strategy(
    results_l3: Dict[str, object],
    config: Optional[StrategyConfig] = None,
    benchmark_returns: Optional[pd.Series] = None,
    rs_window: int = 126,
    rs_min_periods: Optional[int] = None,
    z_window: int = 252,
    z_min_periods: Optional[int] = None,
    momentum_lag: int = 21,
    smoothing_span: int = 10,
    peer_relative: bool = True,
    vol_adjust: bool = True,
    use_hard_gate: bool = True,
    min_effective_n: float = 5.0,
    allowed_quadrants: Tuple[str, ...] = ("Improving", "Leading"),
    require_positive_momentum: bool = True,
    crowding_penalty: float = 0.0,
    winsor: Optional[float] = 5.0,
    output_dir: Optional[str] = None,
) -> Dict[str, object]:
    """Run a residual-RRG theme rotation backtest.

    Signal is residual-based, but P&L is computed on ``theme_returns`` because
    actual portfolio performance includes all realized theme returns.
    """
    if "theme_returns" not in results_l3 or not isinstance(results_l3["theme_returns"], pd.DataFrame):
        raise KeyError("results_l3 must contain 'theme_returns' for backtesting.")
    theme_returns = results_l3["theme_returns"].copy().sort_index()

    cfg = config or StrategyConfig(
        mode="long_only",
        top_n=5,
        max_theme_weight=0.20,
        use_news=False,
        use_governance=False,
        use_leadlag=False,
        use_valuation=False,
        use_crowding=False,
    )
    # Ensure existing overlay flags do not double-count with RRG score.
    cfg = replace(cfg, use_news=False, use_governance=False, use_leadlag=False, use_valuation=False)

    built = build_residual_rrg_scores(
        results_l3=results_l3,
        benchmark_returns=benchmark_returns,
        rs_window=rs_window,
        rs_min_periods=rs_min_periods,
        z_window=z_window,
        z_min_periods=z_min_periods,
        momentum_lag=momentum_lag,
        smoothing_span=smoothing_span,
        peer_relative=peer_relative,
        vol_adjust=vol_adjust,
        use_hard_gate=use_hard_gate,
        min_effective_n=min_effective_n,
        allowed_quadrants=allowed_quadrants,
        require_positive_momentum=require_positive_momentum,
        crowding_penalty=crowding_penalty,
        winsor=winsor,
    )

    score = built["rrg_strategy_score"].reindex(theme_returns.index).reindex(columns=theme_returns.columns)
    eligibility = built["eligibility"].reindex(theme_returns.index).ffill().reindex(columns=theme_returns.columns).fillna(False)

    rebal_dates = make_rebalance_dates(theme_returns.index, cfg.rebalance)
    weights_rebal = construct_theme_weights(
        score.reindex(rebal_dates),
        cfg,
        gates=eligibility.reindex(rebal_dates).fillna(False),
    )
    weights_daily = weights_rebal.reindex(theme_returns.index).ffill().fillna(0.0)

    strat_ret, details = backtest_theme_weights(
        theme_returns=theme_returns,
        weights_daily=weights_daily,
        cost_bps_per_turnover=cfg.cost_bps_per_turnover,
    )
    metrics = performance_metrics(strat_ret, cfg.annualization)

    out = {
        **built,
        "weights_rebalance": weights_rebal,
        "weights_daily": weights_daily,
        "returns": strat_ret,
        "details": details,
        "metrics": metrics,
        "config": cfg,
    }

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        rrg = built["rrg"]
        for key, obj in rrg.items():
            if isinstance(obj, pd.DataFrame):
                obj.to_csv(os.path.join(output_dir, f"residual_rrg_{key}.csv"), index=True)
        built["eligibility"].to_csv(os.path.join(output_dir, "residual_rrg_eligibility.csv"), index=True)
        built["rrg_strategy_score"].to_csv(os.path.join(output_dir, "residual_rrg_strategy_score.csv"), index=True)
        weights_rebal.to_csv(os.path.join(output_dir, "Residual_RRG_weights_rebalance.csv"), index=True)
        weights_daily.to_csv(os.path.join(output_dir, "Residual_RRG_weights_daily.csv"), index=True)
        strat_ret.to_csv(os.path.join(output_dir, "residual_rrg_strategy_returns.csv"), header=True)
        details.to_csv(os.path.join(output_dir, "residual_rrg_backtest_details.csv"), index=True)
        metrics.to_csv(os.path.join(output_dir, "residual_rrg_metrics.csv"), header=True)

    return out


def plot_residual_rrg(
    rrg: Dict[str, pd.DataFrame],
    date: Optional[pd.Timestamp] = None,
    themes: Optional[Sequence[str]] = None,
    tail: int = 12,
    center: float = 100.0,
    figsize: Tuple[float, float] = (10.0, 8.0),
    title: Optional[str] = None,
    output_path: Optional[str] = None,
    show: bool = True,
):
    """Plot residual-RRG coordinates with short tails.

    Parameters
    ----------
    rrg:
        Output ``out['rrg']`` from ``make_residual_rrg`` or
        ``run_residual_rrg_strategy``.
    date:
        Date to plot. If omitted, uses the last date with any RS-Ratio.
    themes:
        Optional subset/order of themes.
    tail:
        Number of historical observations to draw for each theme.
    output_path:
        If supplied, save the chart to this path.
    show:
        If True, call ``plt.show()``.
    """
    import matplotlib.pyplot as plt

    x = rrg["rs_ratio"].copy()
    y = rrg["rs_momentum"].copy()
    if date is None:
        date = x.dropna(how="all").index.max()
    date = pd.Timestamp(date)
    if date not in x.index:
        pos = x.index.searchsorted(date, side="right") - 1
        if pos < 0:
            raise ValueError("No RRG data available on or before the requested date.")
        date = x.index[pos]

    if themes is None:
        row = x.loc[date].dropna()
        themes = list(row.index)
    else:
        themes = [str(t) for t in themes if str(t) in x.columns]

    fig, ax = plt.subplots(figsize=figsize)
    ax.axhline(center, linewidth=1)
    ax.axvline(center, linewidth=1)
    ax.set_xlabel("Residual RS-Ratio")
    ax.set_ylabel("Residual RS-Momentum")
    ax.set_title(title or f"Residual RRG as of {date.date()}")

    # Quadrant labels.
    xmin = np.nanpercentile(x.loc[:date, themes].to_numpy(dtype=float), 5) if themes else center - 10
    xmax = np.nanpercentile(x.loc[:date, themes].to_numpy(dtype=float), 95) if themes else center + 10
    ymin = np.nanpercentile(y.loc[:date, themes].to_numpy(dtype=float), 5) if themes else center - 10
    ymax = np.nanpercentile(y.loc[:date, themes].to_numpy(dtype=float), 95) if themes else center + 10
    pad_x = max(5.0, 0.15 * (xmax - xmin if np.isfinite(xmax - xmin) else 10.0))
    pad_y = max(5.0, 0.15 * (ymax - ymin if np.isfinite(ymax - ymin) else 10.0))
    ax.set_xlim(min(center - 5, xmin - pad_x), max(center + 5, xmax + pad_x))
    ax.set_ylim(min(center - 5, ymin - pad_y), max(center + 5, ymax + pad_y))
    ax.text(center + pad_x * 0.25, center + pad_y * 0.25, "Leading", fontsize=10)
    ax.text(center + pad_x * 0.25, center - pad_y * 0.75, "Weakening", fontsize=10)
    ax.text(center - pad_x * 1.25, center - pad_y * 0.75, "Lagging", fontsize=10)
    ax.text(center - pad_x * 1.25, center + pad_y * 0.25, "Improving", fontsize=10)

    end_loc = x.index.get_loc(date)
    if not isinstance(end_loc, (int, np.integer)):
        end_loc = int(np.asarray(end_loc).ravel()[-1])
    start_loc = max(0, end_loc - max(1, tail) + 1)
    idx_tail = x.index[start_loc : end_loc + 1]

    for theme in themes:
        xt = x.loc[idx_tail, theme].dropna()
        yt = y.loc[idx_tail, theme].reindex(xt.index).dropna()
        common = xt.index.intersection(yt.index)
        if len(common) == 0:
            continue
        ax.plot(xt.loc[common], yt.loc[common], marker="o", linewidth=1)
        ax.scatter([x.at[date, theme]], [y.at[date, theme]], s=40)
        ax.annotate(theme, (x.at[date, theme], y.at[date, theme]), textcoords="offset points", xytext=(4, 4), fontsize=9)

    fig.tight_layout()
    if output_path is not None:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    return fig, ax
