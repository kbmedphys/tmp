"""Residual RRG diagnostics and quadrant-performance analysis.

Use after running ThemeBasketStrategy.compute(), with results_l3 containing:

- theme_returns
- theme_residual_returns
- optional coherence_gate / coherence_effective_n

The module provides:
1. Residual RRG feature construction.
2. Per-theme quadrant timeline visualization.
3. Quadrant share visualization.
4. Event-level forward-return analysis by quadrant.
5. Equal-weight quadrant-portfolio backtests.

RRG coordinates are transparent proxies, not a proprietary JdK replication:

    residual_relative_return = theme_residual_return - peer_residual_benchmark
    residual_rs_raw          = rolling sum of residual_relative_return
    residual_rs_smoothed     = EWM(residual_rs_raw)
    rs_ratio_proxy           = 100 + scale * rolling_zscore(residual_rs_smoothed)
    rs_momentum_proxy        = 100 + scale * rolling_zscore(delta residual_rs_smoothed)
"""
from __future__ import annotations

import os
from dataclasses import replace
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from theme_basket_strategy import (
    StrategyConfig,
    backtest_theme_weights,
    make_rebalance_dates,
    performance_metrics,
)


QUADRANT_ORDER = ["Leading", "Weakening", "Lagging", "Improving"]
QUADRANT_CODE = {"Lagging": 0, "Improving": 1, "Leading": 2, "Weakening": 3}
CODE_QUADRANT = {v: k for k, v in QUADRANT_CODE.items()}


def rolling_time_series_zscore(
    x: pd.DataFrame,
    window: int = 252,
    min_periods: Optional[int] = None,
    std_floor: float = 1e-8,
    winsor: Optional[float] = 5.0,
) -> pd.DataFrame:
    """Column-wise rolling time-series z-score."""
    if min_periods is None:
        min_periods = max(20, window // 2)
    y = x.copy().sort_index().replace([np.inf, -np.inf], np.nan)
    mu = y.rolling(window=window, min_periods=min_periods).mean()
    sd = y.rolling(window=window, min_periods=min_periods).std(ddof=0)
    z = (y - mu) / sd.clip(lower=std_floor)
    if winsor is not None:
        z = z.clip(-winsor, winsor)
    return z


def _coerce_benchmark(
    residual_returns: pd.DataFrame,
    benchmark: Optional[pd.Series | pd.DataFrame] = None,
) -> pd.Series:
    """Return a date-indexed benchmark series aligned to residual_returns."""
    rr = residual_returns.sort_index()
    if benchmark is None:
        return rr.mean(axis=1, skipna=True)
    if isinstance(benchmark, pd.DataFrame):
        if benchmark.shape[1] != 1:
            raise ValueError("benchmark DataFrame must have exactly one column")
        b = benchmark.iloc[:, 0]
    else:
        b = benchmark
    return pd.Series(b).sort_index().astype(float).reindex(rr.index)


def classify_rrg_quadrant(
    rs_ratio: pd.DataFrame,
    rs_momentum: pd.DataFrame,
    center: float = 100.0,
) -> pd.DataFrame:
    """Classify RRG quadrants from X/Y coordinate matrices."""
    out = pd.DataFrame(index=rs_ratio.index, columns=rs_ratio.columns, dtype=object)
    x = rs_ratio
    y = rs_momentum
    out[(x >= center) & (y >= center)] = "Leading"
    out[(x >= center) & (y < center)] = "Weakening"
    out[(x < center) & (y < center)] = "Lagging"
    out[(x < center) & (y >= center)] = "Improving"
    return out


def make_residual_rrg_features(
    residual_returns: pd.DataFrame,
    benchmark: Optional[pd.Series | pd.DataFrame] = None,
    rs_window: int = 126,
    rs_min_periods: Optional[int] = None,
    smooth_span: int = 10,
    momentum_lag: int = 21,
    z_window: int = 252,
    z_min_periods: Optional[int] = None,
    center: float = 100.0,
    scale: float = 10.0,
    winsor: Optional[float] = 5.0,
) -> Dict[str, pd.DataFrame | pd.Series]:
    """Build residual RRG coordinates and quadrant labels.

    Parameters
    ----------
    residual_returns:
        Date x theme matrix, usually results_l3["theme_residual_returns"].
    benchmark:
        Optional residual benchmark. If None, use equal-weight peer residual average.
    rs_window:
        Window for cumulative residual relative strength.
    smooth_span:
        EWM span for smoothing the residual relative strength.
    momentum_lag:
        Lag used to form the RRG Y-axis momentum proxy.
    z_window:
        Rolling time-series z-score window for axis normalization.
    """
    rr = residual_returns.copy().sort_index().astype(float).replace([np.inf, -np.inf], np.nan)
    if rs_min_periods is None:
        rs_min_periods = max(20, rs_window // 2)
    if z_min_periods is None:
        z_min_periods = max(20, z_window // 2)

    b = _coerce_benchmark(rr, benchmark)
    rel = rr.sub(b, axis=0)

    # Sum of daily residual returns is a transparent log-return approximation.
    rs_raw = rel.rolling(rs_window, min_periods=rs_min_periods).sum()
    rs_smoothed = rs_raw.ewm(span=smooth_span, min_periods=max(3, smooth_span // 2), adjust=False).mean()

    x_z = rolling_time_series_zscore(rs_smoothed, window=z_window, min_periods=z_min_periods, winsor=winsor)
    mom_raw = rs_smoothed - rs_smoothed.shift(momentum_lag)
    y_z = rolling_time_series_zscore(mom_raw, window=z_window, min_periods=z_min_periods, winsor=winsor)

    x = center + scale * x_z
    y = center + scale * y_z
    quadrant = classify_rrg_quadrant(x, y, center=center)

    x_dev = x - center
    y_dev = y - center
    distance = np.sqrt(x_dev.pow(2) + y_dev.pow(2))
    angle = pd.DataFrame(np.degrees(np.arctan2(y_dev, x_dev)), index=x.index, columns=x.columns)

    return {
        "benchmark": b,
        "residual_relative_returns": rel,
        "residual_rs_raw": rs_raw,
        "residual_rs_smoothed": rs_smoothed,
        "rs_ratio": x,
        "rs_momentum": y,
        "quadrant": quadrant,
        "distance": distance,
        "angle_degrees": angle,
        "delta_rs_ratio": x.diff(),
        "delta_rs_momentum": y.diff(),
    }


def quadrant_code_matrix(quadrant: pd.DataFrame) -> pd.DataFrame:
    """Convert quadrant labels to stable integer codes for plotting/export."""
    out = pd.DataFrame(np.nan, index=quadrant.index, columns=quadrant.columns, dtype=float)
    for label, code in QUADRANT_CODE.items():
        out = out.mask(quadrant == label, float(code))
    return out


def _stack_keepna(df: pd.DataFrame, name: Optional[str] = None) -> pd.Series:
    """Stack a DataFrame while retaining missing cells, across pandas versions."""
    try:
        s = df.stack(future_stack=True)
    except TypeError:
        s = df.stack(dropna=False)
    if name is not None:
        s = s.rename(name)
    return s


def quadrant_share(
    quadrant: pd.DataFrame,
    quadrants: Sequence[str] = QUADRANT_ORDER,
) -> pd.DataFrame:
    """Return daily share of themes in each quadrant."""
    q = quadrant.copy()
    out = pd.DataFrame(index=q.index)
    denom = q.notna().sum(axis=1).replace(0, np.nan)
    for name in quadrants:
        out[name] = (q == name).sum(axis=1) / denom
    return out


def _date_slice(df: pd.DataFrame, start=None, end=None) -> pd.DataFrame:
    out = df.copy()
    if start is not None:
        out = out.loc[pd.Timestamp(start):]
    if end is not None:
        out = out.loc[:pd.Timestamp(end)]
    return out


def plot_quadrant_timeline(
    quadrant: pd.DataFrame,
    themes: Optional[Iterable[str]] = None,
    start=None,
    end=None,
    figsize: Tuple[float, float] = (13.0, 7.0),
    title: str = "RRG quadrant timeline by theme",
    output_path: Optional[str] = None,
):
    """Visualize where each theme is located over time.

    The heatmap values are:
    0 Lagging, 1 Improving, 2 Leading, 3 Weakening.
    """
    import matplotlib.pyplot as plt

    q = quadrant.copy().sort_index()
    if themes is not None:
        cols = [c for c in themes if c in q.columns]
        q = q[cols]
    q = _date_slice(q, start, end)
    codes = quadrant_code_matrix(q)

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(codes.T.to_numpy(dtype=float), aspect="auto", interpolation="nearest")
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Theme")
    ax.set_yticks(np.arange(len(codes.columns)))
    ax.set_yticklabels(codes.columns)

    if len(codes.index) > 0:
        n_ticks = min(10, len(codes.index))
        tick_locs = np.linspace(0, len(codes.index) - 1, n_ticks).astype(int)
        ax.set_xticks(tick_locs)
        ax.set_xticklabels([codes.index[i].strftime("%Y-%m-%d") for i in tick_locs], rotation=45, ha="right")

    cbar = fig.colorbar(im, ax=ax, ticks=[0, 1, 2, 3])
    cbar.ax.set_yticklabels([CODE_QUADRANT[i] for i in [0, 1, 2, 3]])
    fig.tight_layout()
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig, ax


def plot_quadrant_share(
    quadrant: pd.DataFrame,
    start=None,
    end=None,
    figsize: Tuple[float, float] = (12.0, 5.0),
    title: str = "Share of themes by RRG quadrant",
    output_path: Optional[str] = None,
):
    """Plot time-series share of themes in each RRG quadrant."""
    import matplotlib.pyplot as plt

    share = _date_slice(quadrant_share(quadrant), start, end)
    fig, ax = plt.subplots(figsize=figsize)
    share.plot(ax=ax)
    ax.set_title(title)
    ax.set_ylabel("Share")
    ax.set_xlabel("Date")
    ax.grid(True, linewidth=0.5, alpha=0.4)
    fig.tight_layout()
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig, ax


def plot_single_theme_rrg_state(
    rrg_features: Dict[str, pd.DataFrame | pd.Series],
    theme: str,
    start=None,
    end=None,
    figsize: Tuple[float, float] = (12.0, 5.0),
    output_path: Optional[str] = None,
):
    """Plot one theme's quadrant code, RS-Ratio and RS-Momentum over time."""
    import matplotlib.pyplot as plt

    q = rrg_features["quadrant"]
    x = rrg_features["rs_ratio"]
    y = rrg_features["rs_momentum"]
    if not isinstance(q, pd.DataFrame) or theme not in q.columns:
        raise KeyError(f"theme {theme!r} not found")

    data = pd.DataFrame({
        "quadrant_code": quadrant_code_matrix(q[[theme]])[theme],
        "rs_ratio": x[theme],
        "rs_momentum": y[theme],
    })
    data = _date_slice(data, start, end)

    fig, ax1 = plt.subplots(figsize=figsize)
    ax1.step(data.index, data["quadrant_code"], where="post", label="Quadrant code")
    ax1.set_yticks([0, 1, 2, 3])
    ax1.set_yticklabels([CODE_QUADRANT[i] for i in [0, 1, 2, 3]])
    ax1.set_ylabel("Quadrant")
    ax1.set_xlabel("Date")

    ax2 = ax1.twinx()
    ax2.plot(data.index, data["rs_ratio"], label="RS-Ratio proxy", alpha=0.7)
    ax2.plot(data.index, data["rs_momentum"], label="RS-Momentum proxy", alpha=0.7)
    ax2.axhline(100.0, linewidth=1)
    ax2.set_ylabel("RRG coordinates")

    ax1.set_title(f"Residual RRG state: {theme}")
    ax1.grid(True, linewidth=0.5, alpha=0.4)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")
    fig.tight_layout()
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig, (ax1, ax2)


def forward_compound_returns(returns: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Forward compound returns from t+1 through t+horizon, aligned at t."""
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    shifted = (1.0 + returns.astype(float)).shift(-1)
    fwd = shifted.rolling(horizon, min_periods=horizon).apply(np.prod, raw=True).shift(-(horizon - 1)) - 1.0
    return fwd


def make_quadrant_event_table(
    theme_returns: pd.DataFrame,
    rrg_features: Dict[str, pd.DataFrame | pd.Series],
    horizons: Sequence[int] = (1, 5, 21, 63),
    signal_dates: Optional[Sequence[pd.Timestamp]] = None,
    rebalance_rule: Optional[str] = "ME",
    use_residual_returns_for_forward: bool = False,
) -> pd.DataFrame:
    """Create long table of signal-date quadrant labels and future returns.

    If ``signal_dates`` is None and ``rebalance_rule`` is not None, observations
    are restricted to rebalance dates. This is preferable to daily overlapping
    samples for strategy diagnostics.
    """
    quadrant = rrg_features["quadrant"]
    if not isinstance(quadrant, pd.DataFrame):
        raise TypeError("rrg_features['quadrant'] must be a DataFrame")

    ret_source = rrg_features["residual_relative_returns"] if use_residual_returns_for_forward else theme_returns
    if not isinstance(ret_source, pd.DataFrame):
        raise TypeError("forward return source must be a DataFrame")

    idx = quadrant.index.intersection(ret_source.index)
    cols = [c for c in quadrant.columns if c in ret_source.columns]
    if signal_dates is None and rebalance_rule is not None:
        signal_idx = make_rebalance_dates(pd.DatetimeIndex(idx), rebalance_rule)
    elif signal_dates is not None:
        signal_idx = pd.DatetimeIndex(signal_dates)
        signal_idx = pd.DatetimeIndex([d for d in signal_idx if d in idx])
    else:
        signal_idx = pd.DatetimeIndex(idx)

    base = _stack_keepna(quadrant.reindex(index=signal_idx, columns=cols), "quadrant").to_frame()
    base.index.names = ["date", "theme"]

    x = rrg_features.get("rs_ratio")
    y = rrg_features.get("rs_momentum")
    distance = rrg_features.get("distance")
    for name, obj in [("rs_ratio", x), ("rs_momentum", y), ("distance", distance)]:
        if isinstance(obj, pd.DataFrame):
            base[name] = _stack_keepna(obj.reindex(index=signal_idx, columns=cols), name)

    ret = ret_source.reindex(columns=cols)
    for h in horizons:
        fwd = forward_compound_returns(ret, h).reindex(index=signal_idx, columns=cols)
        base[f"fwd_{h}d"] = _stack_keepna(fwd, f"fwd_{h}d")

    out = base.reset_index()
    out = out.dropna(subset=["quadrant"])
    return out


def summarize_quadrant_forward_returns(
    event_table: pd.DataFrame,
    horizons: Sequence[int] = (1, 5, 21, 63),
    quadrants: Sequence[str] = QUADRANT_ORDER,
) -> pd.DataFrame:
    """Summarize forward returns by quadrant from event table."""
    rows = []
    for h in horizons:
        col = f"fwd_{h}d"
        if col not in event_table.columns:
            continue
        for q in quadrants:
            s = event_table.loc[event_table["quadrant"] == q, col].dropna().astype(float)
            n = len(s)
            if n == 0:
                rows.append({"horizon": h, "quadrant": q, "n": 0})
                continue
            sd = s.std(ddof=1)
            rows.append({
                "horizon": h,
                "quadrant": q,
                "n": n,
                "mean": s.mean(),
                "median": s.median(),
                "std": sd,
                "hit_rate": (s > 0).mean(),
                "t_stat_naive": s.mean() / (sd / np.sqrt(n)) if sd > 0 and n > 1 else np.nan,
                "p05": s.quantile(0.05),
                "p25": s.quantile(0.25),
                "p75": s.quantile(0.75),
                "p95": s.quantile(0.95),
            })
    return pd.DataFrame(rows)


def plot_quadrant_forward_return_summary(
    summary: pd.DataFrame,
    horizon: int = 21,
    metric: str = "mean",
    figsize: Tuple[float, float] = (8.0, 4.5),
    output_path: Optional[str] = None,
):
    """Bar plot of quadrant forward-return summary for one horizon."""
    import matplotlib.pyplot as plt

    sub = summary[summary["horizon"] == horizon].set_index("quadrant")
    sub = sub.reindex(QUADRANT_ORDER)
    fig, ax = plt.subplots(figsize=figsize)
    sub[metric].plot(kind="bar", ax=ax)
    ax.set_title(f"Forward return by RRG quadrant: {horizon}d, {metric}")
    ax.set_xlabel("Quadrant")
    ax.set_ylabel(metric)
    ax.grid(True, axis="y", linewidth=0.5, alpha=0.4)
    fig.tight_layout()
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig, ax


def backtest_quadrant_portfolios(
    theme_returns: pd.DataFrame,
    quadrant: pd.DataFrame,
    rebalance_rule: str = "ME",
    quadrants: Sequence[str] = QUADRANT_ORDER,
    cost_bps_per_turnover: float = 5.0,
    annualization: int = 252,
) -> Dict[str, object]:
    """Backtest equal-weight portfolios of themes in each RRG quadrant.

    At each rebalance date, each quadrant portfolio equally weights all themes
    currently in that quadrant. P&L uses existing backtest_theme_weights, so
    returns are earned from the next day after signal formation and transaction
    costs are deducted.
    """
    idx = theme_returns.index.intersection(quadrant.index)
    cols = [c for c in theme_returns.columns if c in quadrant.columns]
    ret = theme_returns.reindex(index=idx, columns=cols)
    q = quadrant.reindex(index=idx, columns=cols)
    rebal_dates = make_rebalance_dates(pd.DatetimeIndex(idx), rebalance_rule)

    returns = pd.DataFrame(index=idx)
    metrics = {}
    weights_rebalance = {}
    weights_daily = {}
    details = {}

    for name in quadrants:
        mask = (q.reindex(rebal_dates) == name).astype(float)
        denom = mask.sum(axis=1).replace(0, np.nan)
        w_rebal = mask.div(denom, axis=0).fillna(0.0)
        w_daily = w_rebal.reindex(idx).ffill().fillna(0.0)
        strat_ret, det = backtest_theme_weights(ret, w_daily, cost_bps_per_turnover=cost_bps_per_turnover)
        returns[name] = strat_ret
        metrics[name] = performance_metrics(strat_ret, annualization)
        weights_rebalance[name] = w_rebal
        weights_daily[name] = w_daily
        details[name] = det

    metrics_df = pd.concat(metrics, axis=1).T if metrics else pd.DataFrame()
    return {
        "returns": returns,
        "metrics": metrics_df,
        "weights_rebalance": weights_rebalance,
        "weights_daily": weights_daily,
        "details": details,
    }


def quadrant_transition_matrix(
    quadrant: pd.DataFrame,
    signal_dates: Optional[Sequence[pd.Timestamp]] = None,
    rebalance_rule: Optional[str] = "ME",
    normalize: Optional[str] = "row",
) -> pd.DataFrame:
    """Estimate quadrant transition matrix across signal dates."""
    q = quadrant.copy().sort_index()
    if signal_dates is None and rebalance_rule is not None:
        dates = make_rebalance_dates(pd.DatetimeIndex(q.index), rebalance_rule)
    elif signal_dates is not None:
        dates = pd.DatetimeIndex([d for d in pd.DatetimeIndex(signal_dates) if d in q.index])
    else:
        dates = pd.DatetimeIndex(q.index)
    qs = q.reindex(dates)
    labels = QUADRANT_ORDER
    mat = pd.DataFrame(0.0, index=labels, columns=labels)
    for t0, t1 in zip(qs.index[:-1], qs.index[1:]):
        prev = qs.loc[t0]
        nxt = qs.loc[t1]
        for theme in qs.columns:
            a = prev.get(theme)
            b = nxt.get(theme)
            if a in labels and b in labels:
                mat.loc[a, b] += 1.0
    if normalize == "row":
        mat = mat.div(mat.sum(axis=1).replace(0, np.nan), axis=0)
    elif normalize == "all":
        total = mat.values.sum()
        if total > 0:
            mat = mat / total
    elif normalize is None:
        pass
    else:
        raise ValueError("normalize must be 'row', 'all', or None")
    return mat


def run_residual_rrg_diagnostics(
    results_l3: Dict[str, object],
    benchmark: Optional[pd.Series | pd.DataFrame] = None,
    horizons: Sequence[int] = (1, 5, 21, 63),
    rebalance_rule: str = "ME",
    rs_window: int = 126,
    smooth_span: int = 10,
    momentum_lag: int = 21,
    z_window: int = 252,
    z_min_periods: Optional[int] = 126,
    cost_bps_per_turnover: Optional[float] = None,
    annualization: int = 252,
    output_dir: Optional[str] = None,
) -> Dict[str, object]:
    """End-to-end diagnostics: RRG, timeline, event table, quadrant performance."""
    if "theme_residual_returns" not in results_l3:
        raise KeyError("results_l3 must contain 'theme_residual_returns'")
    if "theme_returns" not in results_l3:
        raise KeyError("results_l3 must contain 'theme_returns'")

    theme_resid = results_l3["theme_residual_returns"].copy()
    theme_returns = results_l3["theme_returns"].copy().reindex(index=theme_resid.index, columns=theme_resid.columns)

    features = make_residual_rrg_features(
        residual_returns=theme_resid,
        benchmark=benchmark,
        rs_window=rs_window,
        smooth_span=smooth_span,
        momentum_lag=momentum_lag,
        z_window=z_window,
        z_min_periods=z_min_periods,
    )

    event_table = make_quadrant_event_table(
        theme_returns=theme_returns,
        rrg_features=features,
        horizons=horizons,
        rebalance_rule=rebalance_rule,
    )
    event_summary = summarize_quadrant_forward_returns(event_table, horizons=horizons)

    cost = 5.0 if cost_bps_per_turnover is None else cost_bps_per_turnover
    quadrant_bt = backtest_quadrant_portfolios(
        theme_returns=theme_returns,
        quadrant=features["quadrant"],
        rebalance_rule=rebalance_rule,
        cost_bps_per_turnover=cost,
        annualization=annualization,
    )
    transitions = quadrant_transition_matrix(features["quadrant"], rebalance_rule=rebalance_rule)
    share = quadrant_share(features["quadrant"])

    out = {
        "features": features,
        "quadrant_code": quadrant_code_matrix(features["quadrant"]),
        "quadrant_share": share,
        "event_table": event_table,
        "event_summary": event_summary,
        "quadrant_backtest": quadrant_bt,
        "transition_matrix": transitions,
    }

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        for key, obj in features.items():
            if isinstance(obj, pd.DataFrame):
                obj.to_csv(os.path.join(output_dir, f"rrg_{key}.csv"), index=True)
            elif isinstance(obj, pd.Series):
                obj.to_csv(os.path.join(output_dir, f"rrg_{key}.csv"), header=True)
        out["quadrant_code"].to_csv(os.path.join(output_dir, "rrg_quadrant_code.csv"), index=True)
        share.to_csv(os.path.join(output_dir, "rrg_quadrant_share.csv"), index=True)
        event_table.to_csv(os.path.join(output_dir, "rrg_quadrant_event_table.csv"), index=False)
        event_summary.to_csv(os.path.join(output_dir, "rrg_quadrant_forward_return_summary.csv"), index=False)
        quadrant_bt["returns"].to_csv(os.path.join(output_dir, "rrg_quadrant_portfolio_returns.csv"), index=True)
        quadrant_bt["metrics"].to_csv(os.path.join(output_dir, "rrg_quadrant_portfolio_metrics.csv"), index=True)
        transitions.to_csv(os.path.join(output_dir, "rrg_quadrant_transition_matrix.csv"), index=True)

    return out
