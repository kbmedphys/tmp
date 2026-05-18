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
6. NAV + Residual RRG quadrant-regime overlay plots for each theme.

RRG coordinates are transparent proxies, not a proprietary JdK replication:

    residual_relative_return = theme_residual_return - peer_residual_benchmark
    residual_rs_raw          = rolling sum of residual_relative_return
    residual_rs_smoothed     = EWM(residual_rs_raw)
    rs_ratio_proxy           = 100 + scale * rolling_zscore(residual_rs_smoothed)
    rs_momentum_proxy        = 100 + scale * rolling_zscore(delta residual_rs_smoothed)
"""
from __future__ import annotations

VERSION = "2026-05-18-nav-regime-v2"

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



def _nav_from_returns(
    returns: pd.DataFrame,
    start_nav: float = 100.0,
    fill_missing_returns: bool = True,
) -> pd.DataFrame:
    """Convert a return matrix to NAV levels.

    Parameters
    ----------
    returns:
        Date x theme return matrix.
    start_nav:
        Initial NAV level. 100.0 is convenient for percent-like reading.
    fill_missing_returns:
        If True, missing returns are treated as 0 after the first available
        observation. If False, missing returns remain missing.
    """
    r = returns.copy().sort_index().astype(float).replace([np.inf, -np.inf], np.nan)
    if fill_missing_returns:
        r = r.fillna(0.0)
    return (1.0 + r).cumprod() * float(start_nav)


def _coerce_nav_matrix(
    results_l3: Optional[Dict[str, object]] = None,
    theme_nav: Optional[pd.DataFrame] = None,
    theme_returns: Optional[pd.DataFrame] = None,
    start_nav: float = 100.0,
) -> pd.DataFrame:
    """Return a NAV matrix from explicit NAV, explicit returns, or results_l3."""
    if theme_nav is not None:
        nav = theme_nav.copy().sort_index().astype(float).replace([np.inf, -np.inf], np.nan)
        return nav
    if theme_returns is None:
        if results_l3 is None or "theme_returns" not in results_l3:
            raise KeyError("Provide theme_nav, theme_returns, or results_l3 containing 'theme_returns'.")
        theme_returns = results_l3["theme_returns"]
    if not isinstance(theme_returns, pd.DataFrame):
        raise TypeError("theme_returns must be a DataFrame")
    return _nav_from_returns(theme_returns, start_nav=start_nav)


def _regime_spans(
    regime: pd.Series,
) -> List[Tuple[pd.Timestamp, pd.Timestamp, str]]:
    """Compress a regime series into consecutive same-label spans."""
    s = regime.dropna().astype(str).sort_index()
    spans: List[Tuple[pd.Timestamp, pd.Timestamp, str]] = []
    if s.empty:
        return spans
    start = s.index[0]
    prev_date = s.index[0]
    prev_label = s.iloc[0]
    for dt, label in s.iloc[1:].items():
        if label != prev_label:
            spans.append((pd.Timestamp(start), pd.Timestamp(prev_date), str(prev_label)))
            start = dt
            prev_label = label
        prev_date = dt
    spans.append((pd.Timestamp(start), pd.Timestamp(prev_date), str(prev_label)))
    return spans


DEFAULT_QUADRANT_COLORS = {
    "Leading": "#8fd694",
    "Weakening": "#ffd166",
    "Lagging": "#ef476f",
    "Improving": "#6ec6ff",
}


def plot_theme_nav_with_quadrant_regime(
    results_l3: Optional[Dict[str, object]] = None,
    rrg_features: Optional[Dict[str, pd.DataFrame | pd.Series]] = None,
    theme: Optional[str] = None,
    theme_nav: Optional[pd.DataFrame] = None,
    theme_returns: Optional[pd.DataFrame] = None,
    quadrant: Optional[pd.DataFrame] = None,
    start=None,
    end=None,
    start_nav: float = 100.0,
    normalize_nav: bool = True,
    log_nav: bool = False,
    show_quadrant_step: bool = True,
    show_rrg_coordinates: bool = False,
    shade_alpha: float = 0.18,
    transition_lines: bool = False,
    quadrant_colors: Optional[Dict[str, str]] = None,
    figsize: Tuple[float, float] = (13.0, 6.0),
    title: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """Plot one theme's NAV together with its RRG quadrant regime.

    The main axis shows NAV. The chart background is shaded by the theme's
    RRG quadrant regime. Optionally, a second axis shows the quadrant code,
    and a third axis can show RS-Ratio / RS-Momentum proxies.

    Parameters
    ----------
    results_l3:
        Output dict from ThemeBasketStrategy.compute(). Used only when NAV must
        be reconstructed from ``results_l3['theme_returns']``.
    rrg_features:
        Dict from make_residual_rrg_features() or run_residual_rrg_diagnostics()["features"].
        Must contain ``quadrant``; optionally ``rs_ratio`` and ``rs_momentum``.
    theme:
        Theme column name to plot.
    theme_nav:
        Optional Date x theme NAV matrix. Use this if your theme_data is already NAV.
    theme_returns:
        Optional Date x theme return matrix. Used to reconstruct NAV when theme_nav is absent.
    quadrant:
        Optional Date x theme quadrant matrix. If omitted, use rrg_features['quadrant'].
    normalize_nav:
        If True, rebase the first visible NAV to start_nav.
    log_nav:
        If True, use log scale for NAV.
    show_quadrant_step:
        If True, draw the 0/1/2/3 quadrant code on a secondary axis.
    show_rrg_coordinates:
        If True, also draw RS-Ratio and RS-Momentum proxies on a third axis.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    if rrg_features is not None and quadrant is None:
        q_obj = rrg_features.get("quadrant")
        if not isinstance(q_obj, pd.DataFrame):
            raise TypeError("rrg_features['quadrant'] must be a DataFrame")
        quadrant = q_obj
    if quadrant is None:
        raise KeyError("Provide quadrant or rrg_features containing 'quadrant'.")

    nav = _coerce_nav_matrix(results_l3=results_l3, theme_nav=theme_nav, theme_returns=theme_returns, start_nav=start_nav)
    if theme is None:
        if len(nav.columns) != 1:
            raise ValueError("theme must be supplied when NAV has multiple columns")
        theme = str(nav.columns[0])
    if theme not in nav.columns:
        raise KeyError(f"theme {theme!r} not found in NAV/returns columns")
    if theme not in quadrant.columns:
        raise KeyError(f"theme {theme!r} not found in quadrant columns")

    nav_s = nav[theme].copy().sort_index()
    q_s = quadrant[theme].copy().sort_index()
    df = pd.DataFrame({"nav": nav_s}).join(q_s.rename("quadrant"), how="left")
    df["quadrant"] = df["quadrant"].ffill()
    df = _date_slice(df, start, end)
    if df.empty:
        raise ValueError("No data remains after date slicing")
    if normalize_nav:
        first = df["nav"].dropna().iloc[0]
        if np.isfinite(first) and first != 0:
            df["nav"] = df["nav"] / first * float(start_nav)

    colors = DEFAULT_QUADRANT_COLORS.copy()
    if quadrant_colors:
        colors.update(quadrant_colors)

    fig, ax = plt.subplots(figsize=figsize)

    # Background regime shading.
    ymin, ymax = df["nav"].min(), df["nav"].max()
    for s0, s1, label in _regime_spans(df["quadrant"]):
        color = colors.get(label)
        if color is None:
            continue
        # Add a small extension to make single-day regimes visible.
        ax.axvspan(s0, s1, alpha=shade_alpha, color=color, linewidth=0)
        if transition_lines:
            ax.axvline(s0, linewidth=0.7, alpha=0.35)

    ax.plot(df.index, df["nav"], linewidth=1.8, label=f"{theme} NAV")
    ax.set_ylabel("NAV" + (" rebased" if normalize_nav else ""))
    ax.set_xlabel("Date")
    if log_nav:
        ax.set_yscale("log")
    ax.grid(True, linewidth=0.5, alpha=0.4)

    handles = [Patch(facecolor=colors[q], alpha=shade_alpha, label=q) for q in QUADRANT_ORDER if q in colors]

    if show_quadrant_step:
        ax2 = ax.twinx()
        codes = quadrant_code_matrix(df[["quadrant"]].rename(columns={"quadrant": theme}))[theme]
        ax2.step(df.index, codes, where="post", linewidth=1.0, alpha=0.75, label="Quadrant code")
        ax2.set_yticks([0, 1, 2, 3])
        ax2.set_yticklabels([CODE_QUADRANT[i] for i in [0, 1, 2, 3]])
        ax2.set_ylabel("RRG quadrant")
    else:
        ax2 = None

    if show_rrg_coordinates:
        if rrg_features is None:
            raise ValueError("show_rrg_coordinates=True requires rrg_features")
        x_obj = rrg_features.get("rs_ratio")
        y_obj = rrg_features.get("rs_momentum")
        if not isinstance(x_obj, pd.DataFrame) or not isinstance(y_obj, pd.DataFrame):
            raise TypeError("rrg_features must contain DataFrame entries 'rs_ratio' and 'rs_momentum'")
        if theme not in x_obj.columns or theme not in y_obj.columns:
            raise KeyError(f"theme {theme!r} not found in rs_ratio / rs_momentum")
        # Offset a third y-axis to the right.
        ax3 = ax.twinx()
        ax3.spines["right"].set_position(("axes", 1.10))
        x = _date_slice(x_obj[[theme]], start, end)[theme]
        y = _date_slice(y_obj[[theme]], start, end)[theme]
        ax3.plot(x.index, x, linewidth=1.0, alpha=0.65, label="RS-Ratio")
        ax3.plot(y.index, y, linewidth=1.0, alpha=0.65, label="RS-Momentum")
        ax3.axhline(100.0, linewidth=0.8, alpha=0.6)
        ax3.set_ylabel("RRG coordinates")
    else:
        ax3 = None

    line_handles, line_labels = ax.get_legend_handles_labels()
    extra_handles = []
    extra_labels = []
    if ax2 is not None:
        h, l = ax2.get_legend_handles_labels()
        extra_handles += h
        extra_labels += l
    if ax3 is not None:
        h, l = ax3.get_legend_handles_labels()
        extra_handles += h
        extra_labels += l
    ax.legend(line_handles + extra_handles + handles, line_labels + extra_labels + [h.get_label() for h in handles], loc="best")

    ax.set_title(title or f"{theme}: NAV with Residual RRG quadrant regime")
    fig.tight_layout()
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig, ax


def plot_theme_nav_regime_grid(
    results_l3: Optional[Dict[str, object]] = None,
    rrg_features: Optional[Dict[str, pd.DataFrame | pd.Series]] = None,
    themes: Optional[Sequence[str]] = None,
    theme_nav: Optional[pd.DataFrame] = None,
    theme_returns: Optional[pd.DataFrame] = None,
    quadrant: Optional[pd.DataFrame] = None,
    start=None,
    end=None,
    start_nav: float = 100.0,
    normalize_nav: bool = True,
    ncols: int = 2,
    shade_alpha: float = 0.18,
    quadrant_colors: Optional[Dict[str, str]] = None,
    figsize_per_panel: Tuple[float, float] = (6.5, 3.0),
    output_path: Optional[str] = None,
):
    """Plot NAV + quadrant-regime background for multiple themes in a grid."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    if rrg_features is not None and quadrant is None:
        q_obj = rrg_features.get("quadrant")
        if not isinstance(q_obj, pd.DataFrame):
            raise TypeError("rrg_features['quadrant'] must be a DataFrame")
        quadrant = q_obj
    if quadrant is None:
        raise KeyError("Provide quadrant or rrg_features containing 'quadrant'.")

    nav = _coerce_nav_matrix(results_l3=results_l3, theme_nav=theme_nav, theme_returns=theme_returns, start_nav=start_nav)
    common = [c for c in nav.columns if c in quadrant.columns]
    if themes is None:
        themes = common
    else:
        themes = [t for t in themes if t in common]
    if not themes:
        raise ValueError("No requested themes are present in both NAV and quadrant matrices")

    colors = DEFAULT_QUADRANT_COLORS.copy()
    if quadrant_colors:
        colors.update(quadrant_colors)

    n = len(themes)
    ncols = max(1, int(ncols))
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(figsize_per_panel[0] * ncols, figsize_per_panel[1] * nrows),
        squeeze=False,
        sharex=True,
    )

    for ax, theme in zip(axes.ravel(), themes):
        df = pd.DataFrame({"nav": nav[theme]}).join(quadrant[theme].rename("quadrant"), how="left")
        df["quadrant"] = df["quadrant"].ffill()
        df = _date_slice(df, start, end)
        if df.empty:
            ax.set_visible(False)
            continue
        if normalize_nav:
            first = df["nav"].dropna().iloc[0]
            if np.isfinite(first) and first != 0:
                df["nav"] = df["nav"] / first * float(start_nav)
        for s0, s1, label in _regime_spans(df["quadrant"]):
            color = colors.get(label)
            if color is not None:
                ax.axvspan(s0, s1, alpha=shade_alpha, color=color, linewidth=0)
        ax.plot(df.index, df["nav"], linewidth=1.5)
        ax.set_title(str(theme))
        ax.grid(True, linewidth=0.5, alpha=0.4)

    for ax in axes.ravel()[n:]:
        ax.set_visible(False)

    handles = [Patch(facecolor=colors[q], alpha=shade_alpha, label=q) for q in QUADRANT_ORDER if q in colors]
    fig.legend(handles=handles, loc="upper center", ncol=min(4, len(handles)))
    fig.suptitle("Theme NAV with Residual RRG quadrant regime", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig, axes


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


def theme_returns_to_nav(
    theme_returns: pd.DataFrame,
    base: float = 100.0,
) -> pd.DataFrame:
    """Convert theme return matrix to NAV/index levels.

    Parameters
    ----------
    theme_returns:
        Date x theme return matrix. Usually ``results_l3["theme_returns"]``.
    base:
        Initial NAV level.
    """
    ret = theme_returns.copy().sort_index().astype(float).replace([np.inf, -np.inf], np.nan)
    nav = (1.0 + ret.fillna(0.0)).cumprod() * float(base)
    # Keep leading periods with no observations as NaN rather than artificial base values.
    observed = ret.notna().cummax()
    return nav.where(observed)


def _coerce_theme_nav(
    nav_or_returns: pd.DataFrame,
    input_kind: str = "return",
    base: float = 100.0,
) -> pd.DataFrame:
    """Coerce either theme NAV/price data or returns into NAV levels."""
    x = nav_or_returns.copy().sort_index().astype(float).replace([np.inf, -np.inf], np.nan)
    kind = input_kind.lower()
    if kind == "return":
        return theme_returns_to_nav(x, base=base)
    if kind in {"nav", "price", "level"}:
        return x
    if kind == "auto":
        med_abs = np.nanmedian(np.abs(x.to_numpy(dtype=float)))
        return x if med_abs > 2 else theme_returns_to_nav(x, base=base)
    raise ValueError("input_kind must be 'return', 'nav', 'price', 'level', or 'auto'")


def _regime_segments(q: pd.Series) -> List[Tuple[pd.Timestamp, pd.Timestamp, str]]:
    """Compress a quadrant Series into consecutive regime segments."""
    s = q.dropna().copy()
    if s.empty:
        return []
    s.index = pd.DatetimeIndex(s.index)
    segments: List[Tuple[pd.Timestamp, pd.Timestamp, str]] = []
    start = s.index[0]
    prev_date = s.index[0]
    prev_label = str(s.iloc[0])
    for dt, label in s.iloc[1:].items():
        label = str(label)
        if label != prev_label:
            segments.append((pd.Timestamp(start), pd.Timestamp(prev_date), prev_label))
            start = dt
            prev_label = label
        prev_date = dt
    segments.append((pd.Timestamp(start), pd.Timestamp(prev_date), prev_label))
    return segments


def _default_quadrant_styles() -> Dict[str, Dict[str, object]]:
    """Default visual styles for quadrant background bands.

    Users can override this with ``quadrant_styles``. Kept in a helper so that
    batch plots and single plots share the same mapping.
    """
    return {
        "Leading": {"color": "tab:green", "alpha": 0.12},
        "Weakening": {"color": "tab:orange", "alpha": 0.12},
        "Lagging": {"color": "tab:red", "alpha": 0.10},
        "Improving": {"color": "tab:blue", "alpha": 0.10},
    }


def plot_theme_nav_with_rrg_regime(
    nav_or_returns: pd.DataFrame,
    rrg_features: Dict[str, pd.DataFrame | pd.Series],
    theme: str,
    input_kind: str = "return",
    base: float = 100.0,
    start=None,
    end=None,
    logy: bool = False,
    show_quadrant_step: bool = True,
    show_rrg_coordinates: bool = False,
    quadrant_styles: Optional[Dict[str, Dict[str, object]]] = None,
    figsize: Tuple[float, float] = (13.0, 6.0),
    title: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """Plot one theme's NAV together with its RRG quadrant regime.

    The NAV line is plotted on the main axis. RRG regimes are shown as
    background bands. Optionally, a lower panel shows the quadrant code and/or
    RS-Ratio / RS-Momentum proxies.

    Parameters
    ----------
    nav_or_returns:
        Date x theme matrix. Pass ``results_l3["theme_returns"]`` with
        ``input_kind='return'`` or an actual NAV/price matrix with
        ``input_kind='nav'``.
    rrg_features:
        Output ``rrg_diag["features"]`` from ``run_residual_rrg_diagnostics``.
    theme:
        Theme column to plot.
    input_kind:
        'return', 'nav', 'price', 'level', or 'auto'.
    """
    import matplotlib.pyplot as plt

    quadrant = rrg_features.get("quadrant")
    if not isinstance(quadrant, pd.DataFrame):
        raise TypeError("rrg_features must contain DataFrame entry 'quadrant'")
    if theme not in quadrant.columns:
        raise KeyError(f"theme {theme!r} not found in rrg_features['quadrant']")
    if theme not in nav_or_returns.columns:
        raise KeyError(f"theme {theme!r} not found in nav_or_returns")

    nav = _coerce_theme_nav(nav_or_returns, input_kind=input_kind, base=base)
    idx = nav.index.intersection(quadrant.index)
    data = pd.DataFrame({
        "nav": nav.reindex(idx)[theme],
        "quadrant": quadrant.reindex(idx)[theme],
    })

    x = rrg_features.get("rs_ratio")
    y = rrg_features.get("rs_momentum")
    if isinstance(x, pd.DataFrame) and theme in x.columns:
        data["rs_ratio"] = x.reindex(idx)[theme]
    if isinstance(y, pd.DataFrame) and theme in y.columns:
        data["rs_momentum"] = y.reindex(idx)[theme]
    data["quadrant_code"] = quadrant_code_matrix(data[["quadrant"]].rename(columns={"quadrant": theme}))[theme]
    data = _date_slice(data, start, end)

    if data.empty:
        raise ValueError("No data remains after applying start/end filters")

    styles = _default_quadrant_styles()
    if quadrant_styles is not None:
        styles.update(quadrant_styles)

    nrows = 1 + int(show_quadrant_step or show_rrg_coordinates)
    height_ratios = [3.0, 1.2] if nrows == 2 else [1.0]
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=1,
        figsize=figsize,
        sharex=True,
        gridspec_kw={"height_ratios": height_ratios},
    )
    if nrows == 1:
        ax_nav = axes
        ax_state = None
    else:
        ax_nav = axes[0]
        ax_state = axes[1]

    # Background regime bands on all panels.
    segments = _regime_segments(data["quadrant"])
    plot_end_default = data.index[-1]
    for seg_start, seg_end, label in segments:
        # Extend the segment through the next available date when possible so
        # the last observation of each state is visually covered.
        try:
            pos = data.index.get_loc(seg_end)
            if isinstance(pos, (int, np.integer)) and pos + 1 < len(data.index):
                span_end = data.index[pos + 1]
            else:
                span_end = plot_end_default
        except Exception:
            span_end = seg_end
        style = styles.get(label, {"alpha": 0.08})
        ax_nav.axvspan(seg_start, span_end, **style)
        if ax_state is not None:
            ax_state.axvspan(seg_start, span_end, **style)

    ax_nav.plot(data.index, data["nav"], linewidth=1.6, label="NAV")
    ax_nav.set_ylabel("NAV")
    if logy:
        ax_nav.set_yscale("log")
    ax_nav.grid(True, linewidth=0.5, alpha=0.4)
    ax_nav.set_title(title or f"{theme}: NAV with Residual RRG quadrant regimes")
    ax_nav.legend(loc="best")

    if ax_state is not None:
        if show_quadrant_step:
            ax_state.step(data.index, data["quadrant_code"], where="post", label="Quadrant", linewidth=1.2)
            ax_state.set_yticks([0, 1, 2, 3])
            ax_state.set_yticklabels([CODE_QUADRANT[i] for i in [0, 1, 2, 3]])
            ax_state.set_ylabel("Regime")
        if show_rrg_coordinates:
            ax2 = ax_state.twinx()
            if "rs_ratio" in data.columns:
                ax2.plot(data.index, data["rs_ratio"], linestyle="--", alpha=0.8, label="RS-Ratio")
            if "rs_momentum" in data.columns:
                ax2.plot(data.index, data["rs_momentum"], linestyle=":", alpha=0.8, label="RS-Mom")
            ax2.axhline(100.0, linewidth=1)
            ax2.set_ylabel("RRG coordinates")
            lines1, labels1 = ax_state.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax_state.legend(lines1 + lines2, labels1 + labels2, loc="best")
        else:
            ax_state.legend(loc="best")
        ax_state.grid(True, linewidth=0.5, alpha=0.4)
        ax_state.set_xlabel("Date")
    else:
        ax_nav.set_xlabel("Date")

    fig.tight_layout()
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig, axes, data


def plot_all_theme_nav_with_rrg_regime(
    nav_or_returns: pd.DataFrame,
    rrg_features: Dict[str, pd.DataFrame | pd.Series],
    themes: Optional[Iterable[str]] = None,
    input_kind: str = "return",
    base: float = 100.0,
    start=None,
    end=None,
    logy: bool = False,
    show_quadrant_step: bool = True,
    show_rrg_coordinates: bool = False,
    output_dir: str = "output_residual_rrg_nav_regime",
    filename_prefix: str = "nav_rrg_regime",
    close_figures: bool = True,
) -> Dict[str, str]:
    """Save NAV + RRG regime charts for multiple themes.

    Returns a mapping from theme name to saved PNG path.
    """
    import matplotlib.pyplot as plt

    quadrant = rrg_features.get("quadrant")
    if not isinstance(quadrant, pd.DataFrame):
        raise TypeError("rrg_features must contain DataFrame entry 'quadrant'")
    if themes is None:
        theme_list = [c for c in nav_or_returns.columns if c in quadrant.columns]
    else:
        theme_list = [c for c in themes if c in nav_or_returns.columns and c in quadrant.columns]
    if not theme_list:
        raise ValueError("No matching themes found between nav_or_returns and rrg_features['quadrant']")

    os.makedirs(output_dir, exist_ok=True)
    paths: Dict[str, str] = {}
    for theme in theme_list:
        safe_theme = str(theme).replace("/", "_").replace("\\", "_").replace(" ", "_")
        path = os.path.join(output_dir, f"{filename_prefix}_{safe_theme}.png")
        fig, _, _ = plot_theme_nav_with_rrg_regime(
            nav_or_returns=nav_or_returns,
            rrg_features=rrg_features,
            theme=theme,
            input_kind=input_kind,
            base=base,
            start=start,
            end=end,
            logy=logy,
            show_quadrant_step=show_quadrant_step,
            show_rrg_coordinates=show_rrg_coordinates,
            output_path=path,
        )
        paths[str(theme)] = path
        if close_figures:
            plt.close(fig)
    return paths


def _extract_rrg_features(rrg_obj: Dict[str, object]) -> Dict[str, object]:
    """Accept either rrg_diag returned by run_residual_rrg_diagnostics or features dict."""
    if "features" in rrg_obj and isinstance(rrg_obj["features"], dict):
        return rrg_obj["features"]
    return rrg_obj


def _series_from_matrix_or_series(obj: pd.DataFrame | pd.Series, theme: str, name: str) -> pd.Series:
    if isinstance(obj, pd.Series):
        s = obj.copy()
        s.name = theme
        return s.sort_index()
    if not isinstance(obj, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas Series or DataFrame")
    if theme not in obj.columns:
        raise KeyError(f"theme {theme!r} not found in {name}. Available examples: {list(obj.columns[:10])}")
    return obj[theme].copy().sort_index()


def make_theme_nav_series(
    results_l3: Optional[Dict[str, object]] = None,
    theme: Optional[str] = None,
    theme_nav: Optional[pd.DataFrame | pd.Series] = None,
    theme_returns: Optional[pd.DataFrame | pd.Series] = None,
    nav_base: float = 100.0,
) -> pd.Series:
    """Return a single-theme NAV series.

    Priority
    --------
    1. Use ``theme_nav`` if supplied. This should be original NAV/price data.
    2. Use ``theme_returns`` if supplied and reconstruct NAV.
    3. Use ``results_l3["theme_returns"]`` and reconstruct NAV.

    Notes
    -----
    ``ThemeBasketStrategy.compute()`` stores theme returns, not the original
    raw NAV matrix. Therefore, unless original ``theme_data`` is passed via
    ``theme_nav``, this function reconstructs NAV as ``nav_base * cumprod(1+r)``.
    """
    if theme is None:
        raise ValueError("theme must be supplied")

    if theme_nav is not None:
        nav = _series_from_matrix_or_series(theme_nav, theme, "theme_nav")
        return nav.replace([np.inf, -np.inf], np.nan).dropna().astype(float)

    if theme_returns is None:
        if results_l3 is None or "theme_returns" not in results_l3:
            raise KeyError("Provide theme_nav, theme_returns, or results_l3 containing 'theme_returns'.")
        theme_returns = results_l3["theme_returns"]

    ret = _series_from_matrix_or_series(theme_returns, theme, "theme_returns")
    ret = ret.replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(float)
    nav = nav_base * (1.0 + ret).cumprod()
    nav.name = theme
    return nav


def make_theme_nav_regime_table(
    results_l3: Optional[Dict[str, object]],
    rrg_obj: Dict[str, object],
    theme: str,
    theme_nav: Optional[pd.DataFrame | pd.Series] = None,
    theme_returns: Optional[pd.DataFrame | pd.Series] = None,
    nav_base: float = 100.0,
    start=None,
    end=None,
) -> pd.DataFrame:
    """Build one table containing NAV, RRG quadrant and RRG coordinates."""
    features = _extract_rrg_features(rrg_obj)
    q = features.get("quadrant")
    x = features.get("rs_ratio")
    y = features.get("rs_momentum")
    if not isinstance(q, pd.DataFrame):
        raise TypeError("rrg_obj must contain features['quadrant'] as a DataFrame")
    if not isinstance(x, pd.DataFrame) or not isinstance(y, pd.DataFrame):
        raise TypeError("rrg_obj must contain features['rs_ratio'] and features['rs_momentum'] as DataFrames")
    if theme not in q.columns:
        raise KeyError(f"theme {theme!r} not found in RRG features. Available examples: {list(q.columns[:10])}")

    nav = make_theme_nav_series(
        results_l3=results_l3,
        theme=theme,
        theme_nav=theme_nav,
        theme_returns=theme_returns,
        nav_base=nav_base,
    )

    table = pd.DataFrame({
        "nav": nav,
        "quadrant": q[theme],
        "quadrant_code": quadrant_code_matrix(q[[theme]])[theme],
        "rs_ratio": x[theme],
        "rs_momentum": y[theme],
    }).sort_index()
    if "distance" in features and isinstance(features["distance"], pd.DataFrame) and theme in features["distance"].columns:
        table["distance"] = features["distance"][theme]
    if "angle_degrees" in features and isinstance(features["angle_degrees"], pd.DataFrame) and theme in features["angle_degrees"].columns:
        table["angle_degrees"] = features["angle_degrees"][theme]

    table = _date_slice(table, start, end)
    return table.dropna(subset=["nav"])


def plot_theme_nav_with_rrg_regime(
    results_l3: Optional[Dict[str, object]],
    rrg_obj: Dict[str, object],
    theme: str,
    theme_nav: Optional[pd.DataFrame | pd.Series] = None,
    theme_returns: Optional[pd.DataFrame | pd.Series] = None,
    nav_base: float = 100.0,
    start=None,
    end=None,
    include_rrg_coordinates: bool = True,
    use_log_nav: bool = False,
    figsize: Tuple[float, float] = (13.0, 7.0),
    title: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """Plot one theme's NAV and its four RRG quadrant regimes together.

    The figure contains:
    - NAV reconstructed from theme returns, or original NAV if ``theme_nav`` is supplied.
    - Optional RS-Ratio / RS-Momentum time series.
    - A categorical regime band showing Lagging / Improving / Leading / Weakening.

    No explicit color palette is specified; Matplotlib's default color/colormap
    is used so the function remains portable across notebook styles.
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    data = make_theme_nav_regime_table(
        results_l3=results_l3,
        rrg_obj=rrg_obj,
        theme=theme,
        theme_nav=theme_nav,
        theme_returns=theme_returns,
        nav_base=nav_base,
        start=start,
        end=end,
    )
    if data.empty:
        raise ValueError("No data available after applying start/end filters.")

    nrows = 3 if include_rrg_coordinates else 2
    height_ratios = [3.0, 1.4, 0.55] if include_rrg_coordinates else [3.0, 0.55]
    x_int = np.arange(len(data.index))

    fig = plt.figure(figsize=figsize)
    gs = GridSpec(nrows, 1, height_ratios=height_ratios, hspace=0.08, figure=fig)
    ax_nav = fig.add_subplot(gs[0, 0])

    ax_nav.plot(x_int, data["nav"].to_numpy(dtype=float), label="NAV")
    ax_nav.set_ylabel("NAV")
    if use_log_nav:
        ax_nav.set_yscale("log")
    ax_nav.grid(True, linewidth=0.5, alpha=0.4)
    ax_nav.legend(loc="best")
    ax_nav.set_title(title or f"{theme}: NAV and Residual RRG quadrant regime")

    if include_rrg_coordinates:
        ax_rrg = fig.add_subplot(gs[1, 0], sharex=ax_nav)
        ax_rrg.plot(x_int, data["rs_ratio"].to_numpy(dtype=float), label="RS-Ratio proxy")
        ax_rrg.plot(x_int, data["rs_momentum"].to_numpy(dtype=float), label="RS-Momentum proxy")
        ax_rrg.axhline(100.0, linewidth=1)
        ax_rrg.set_ylabel("RRG coordinates")
        ax_rrg.grid(True, linewidth=0.5, alpha=0.4)
        ax_rrg.legend(loc="best")
        ax_band = fig.add_subplot(gs[2, 0], sharex=ax_nav)
        plt.setp(ax_nav.get_xticklabels(), visible=False)
        plt.setp(ax_rrg.get_xticklabels(), visible=False)
    else:
        ax_band = fig.add_subplot(gs[1, 0], sharex=ax_nav)
        plt.setp(ax_nav.get_xticklabels(), visible=False)

    code_values = data["quadrant_code"].to_numpy(dtype=float).reshape(1, -1)
    ax_band.imshow(code_values, aspect="auto", interpolation="nearest", extent=[0, len(data.index) - 1, 0, 1])
    ax_band.set_yticks([])
    ax_band.set_ylabel("Regime")
    ax_band.set_xlabel("Date")

    n_ticks = min(10, len(data.index))
    tick_locs = np.linspace(0, len(data.index) - 1, n_ticks).astype(int)
    ax_band.set_xticks(tick_locs)
    ax_band.set_xticklabels([data.index[i].strftime("%Y-%m-%d") for i in tick_locs], rotation=45, ha="right")
    ax_band.set_xlim(0, len(data.index) - 1)
    ax_nav.set_xlim(0, len(data.index) - 1)
    if include_rrg_coordinates:
        ax_rrg.set_xlim(0, len(data.index) - 1)

    # Put quadrant legend as text, avoiding explicit colors.
    legend_text = " | ".join([f"{QUADRANT_CODE[q]}={q}" for q in ["Lagging", "Improving", "Leading", "Weakening"]])
    ax_band.text(0.01, 1.35, legend_text, transform=ax_band.transAxes, va="bottom", fontsize=9)

    fig.tight_layout()
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig, data


def save_all_theme_nav_regime_plots(
    results_l3: Optional[Dict[str, object]],
    rrg_obj: Dict[str, object],
    themes: Optional[Iterable[str]] = None,
    theme_nav: Optional[pd.DataFrame | pd.Series] = None,
    theme_returns: Optional[pd.DataFrame | pd.Series] = None,
    nav_base: float = 100.0,
    start=None,
    end=None,
    include_rrg_coordinates: bool = True,
    output_dir: str = "output_residual_rrg_nav_regime",
    close_figures: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Save NAV + RRG regime plots for multiple themes.

    Returns a dict of the underlying per-theme data tables.
    """
    import matplotlib.pyplot as plt

    features = _extract_rrg_features(rrg_obj)
    q = features.get("quadrant")
    if not isinstance(q, pd.DataFrame):
        raise TypeError("rrg_obj must contain features['quadrant'] as a DataFrame")
    cols = list(themes) if themes is not None else list(q.columns)
    os.makedirs(output_dir, exist_ok=True)
    tables: Dict[str, pd.DataFrame] = {}
    for theme in cols:
        if theme not in q.columns:
            continue
        safe_theme = str(theme).replace("/", "_").replace("\\", "_").replace(":", "_")
        fig, table = plot_theme_nav_with_rrg_regime(
            results_l3=results_l3,
            rrg_obj=rrg_obj,
            theme=theme,
            theme_nav=theme_nav,
            theme_returns=theme_returns,
            nav_base=nav_base,
            start=start,
            end=end,
            include_rrg_coordinates=include_rrg_coordinates,
            output_path=os.path.join(output_dir, f"{safe_theme}_nav_rrg_regime.png"),
        )
        table.to_csv(os.path.join(output_dir, f"{safe_theme}_nav_rrg_regime.csv"), index=True)
        tables[str(theme)] = table
        if close_figures:
            plt.close(fig)
    return tables
