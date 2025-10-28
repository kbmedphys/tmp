
import numpy as np
from typing import Callable, Tuple, Optional

def _bisection_for_target_zero(
    f: Callable[[float], float],
    lo: float,
    hi: float,
    tol: float = 1e-6,
    max_iter: int = 80,
    expand_hi: bool = True,
    max_hi: float = 1e12,
) -> float:
    """
    Solve f(x) ≈ 0 using bisection with optional high-bound expansion.
    Assumes f is monotone decreasing in x for our use-case
    (withdrawal ↑ -> terminal wealth median ↓).
    """
    flo = f(lo)
    fhi = f(hi)

    # If high bound is not enough (fhi > 0), expand it until fhi <= 0 or max_hi reached.
    if expand_hi:
        while fhi > 0.0 and hi < max_hi:
            hi = min(max_hi, hi * 2.0 if hi > 0 else 1.0)
            fhi = f(hi)

    # If even at lo we are already <= 0, return lo (cannot withdraw anything positive)
    if flo <= 0.0:
        return lo

    # Standard bisection
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fmid = f(mid)
        if abs(fmid) <= tol:
            return mid
        if fmid > 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def ann_rate_to_monthly_amount(rate_ann: float, init_val: float) -> float:
    """
    Convert an annual withdrawal *rate of initial wealth* into a *monthly fixed amount*.
    amount_per_month = rate_ann * init_val / 12
    """
    return float(rate_ann) * float(init_val) / 12.0


def monthly_amount_to_ann_rate(monthly_amount: float, init_val: float) -> float:
    """
    Inverse of ann_rate_to_monthly_amount (rate of initial wealth per year).
    """
    if init_val <= 0:
        return 0.0
    return float(monthly_amount) * 12.0 / float(init_val)


def find_monthly_withdrawal_amount_for_median_zero(
    simulate_fn: Callable[[float], np.ndarray],
    low_amt: float = 0.0,
    high_amt: Optional[float] = None,
    tol: float = 1e-6,
    max_iter: int = 80,
) -> float:
    """
    Search a constant *monthly withdrawal amount* so that median(terminal_wealths) ≈ 0.

    simulate_fn(monthly_amount) -> np.ndarray shape [n_paths]
        Returns terminal wealth for each scenario/path.

    high_amt:
        If None, we set to a heuristic based on simulate_fn(0).
    """

    def g(a: float) -> float:
        term = simulate_fn(a)
        term = np.asarray(term).astype(float)
        if term.ndim == 0:
            med = float(term)
        else:
            med = float(np.median(term))
        return med  # target is 0

    # Heuristic high bound if not provided:
    if high_amt is None:
        term0 = simulate_fn(0.0)
        # Use a fraction of initial wealth proxy if available.
        # If median is already <= 0 at zero withdrawal, return 0 directly via bisection routine.
        # Otherwise start with something proportional to median wealth / horizon (rough heuristic).
        med0 = float(np.median(np.asarray(term0))) if np.ndim(term0) > 0 else float(term0)
        # Avoid zeros; try a modest positive bound first
        high_amt = max(1.0, abs(med0) / 120.0)

    amt = _bisection_for_target_zero(
        f=lambda a: g(a),
        lo=low_amt,
        hi=high_amt,
        tol=tol,
        max_iter=max_iter,
        expand_hi=True,
        max_hi=1e12
    )
    return amt


def solve_monthly_amount_for_glide(
    GlidePathPortfolioCls,
    weights_df,
    rets_paths: np.ndarray,      # shape: [n_paths, T, n_assets]
    init_rt: int,
    init_val: float,
    contribution: float,
    const: bool = False,
    pre_scenario: Optional[np.ndarray] = None,  # shape: [T+1] or None (applied to every path if provided)
    low_amt: float = 0.0,
    high_amt: Optional[float] = None,
    tol: float = 1e-6,
    max_iter: int = 80,
) -> Tuple[float, np.ndarray]:
    """
    Find a constant *monthly withdrawal amount* for GlidePathPortfolio so that the
    median terminal wealth across rets_paths is ~ 0.

    Returns:
        (monthly_amount, terminals), where terminals is shape [n_paths]
    """
    rets_paths = np.asarray(rets_paths, dtype=float)
    assert rets_paths.ndim == 3, "rets_paths must be shape [n_paths, T, n_assets]"

    n_paths, T, n_assets = rets_paths.shape

    def simulate_fn(monthly_amount: float) -> np.ndarray:
        terminals = np.empty(n_paths, dtype=float)
        for i in range(n_paths):
            gp = GlidePathPortfolioCls(weights_df)
            rets = rets_paths[i]  # shape [T, n_assets]
            S, X, W = gp.run(
                rets=rets,
                init_rt=init_rt,
                init_val=init_val,
                contribution=contribution,
                withdrawal=monthly_amount,
                const=const,
                pre_scenario=pre_scenario
            )
            terminals[i] = float(S[-1])
        return terminals

    # run solver
    monthly_amount = find_monthly_withdrawal_amount_for_median_zero(
        simulate_fn=simulate_fn,
        low_amt=low_amt,
        high_amt=high_amt,
        tol=tol,
        max_iter=max_iter
    )

    # compute terminals at the solved amount (so caller has them without re-solving)
    terminals = simulate_fn(monthly_amount)
    return monthly_amount, terminals


def solve_annual_rate_of_initial_for_glide(
    GlidePathPortfolioCls,
    weights_df,
    rets_paths: np.ndarray,   # shape: [n_paths, T, n_assets]
    init_rt: int,
    init_val: float,
    contribution: float,
    const: bool = False,
    pre_scenario: Optional[np.ndarray] = None,
    low_rate_ann: float = 0.0,
    high_rate_ann: float = 0.20,
    tol: float = 1e-6,
    max_iter: int = 80,
) -> Tuple[float, float, np.ndarray]:
    """
    Convenience wrapper that solves for an *annual rate of initial wealth*.
    Internally converts to a constant monthly amount: amount = rate_ann * init_val / 12.

    Returns:
        (rate_ann, monthly_amount, terminals_at_solution)
    """
    rets_paths = np.asarray(rets_paths, dtype=float)
    assert rets_paths.ndim == 3, "rets_paths must be shape [n_paths, T, n_assets]"

    def simulate_fn_from_rate(rate_ann: float) -> np.ndarray:
        monthly_amount = ann_rate_to_monthly_amount(rate_ann, init_val=init_val)
        # We'll reuse the monthly solver's internal simulate function idea (inline here)
        n_paths = rets_paths.shape[0]
        terminals = np.empty(n_paths, dtype=float)
        for i in range(n_paths):
            gp = GlidePathPortfolioCls(weights_df)
            rets = rets_paths[i]
            S, X, W = gp.run(
                rets=rets,
                init_rt=init_rt,
                init_val=init_val,
                contribution=contribution,
                withdrawal=monthly_amount,
                const=const,
                pre_scenario=pre_scenario
            )
            terminals[i] = float(S[-1])
        return terminals

    def f(rate_ann: float) -> float:
        term = simulate_fn_from_rate(rate_ann)
        return float(np.median(term))

    # bisection on annual rate directly with expansion on high bound
    rate_ann = _bisection_for_target_zero(
        f=f,
        lo=low_rate_ann,
        hi=high_rate_ann,
        tol=tol,
        max_iter=max_iter,
        expand_hi=True,
        max_hi=10.0  # up to 1000% if needed
    )
    monthly_amount = ann_rate_to_monthly_amount(rate_ann, init_val=init_val)
    terminals = simulate_fn_from_rate(rate_ann)
    return rate_ann, monthly_amount, terminals


def _solve_monthly_amount_for_scenario_zero(
    GlidePathPortfolioCls,
    weights_df,
    T: int,
    n_assets: int,
    init_rt: int,
    init_val: float,
    contribution: float,
    const: bool = True,
    pre_scenario: Optional[np.ndarray] = None,
    low_amt: float = 0.0,
    high_amt: Optional[float] = None,
    tol: float = 1e-8,
    max_iter: int = 100,
) -> float:
    '''
    Find a constant MONTHLY withdrawal AMOUNT so that the final `scenario[-1] ≈ 0`.
    This uses the GlidePathPortfolio.run(...) recursion with `const=True` by default.
    Note:
      - `rets` do not affect `scenario` or `rt` path when const=True (only contributions/withdrawals and mu,sigma enter).
      - We therefore pass zeros rets of shape [T, n_assets] safely.
    '''
    import numpy as np

    zeros_rets = np.zeros((T, n_assets), dtype=float)

    def g(amount: float) -> float:
        gp = GlidePathPortfolioCls(weights_df)
        S, X, W = gp.run(
            rets=zeros_rets,
            init_rt=init_rt,
            init_val=init_val,
            contribution=contribution,
            withdrawal=amount,
            const=const,
            pre_scenario=pre_scenario,
        )
        # gp.scenario is length T+1
        return float(gp.scenario[-1])  # target to match 0

    # heuristic for high bound if needed: start from init_val / T
    if high_amt is None:
        high_amt = max(1e-12, init_val / max(1, T))

    # We need f(lo)>0 and f(hi)<=0 for standard bisection direction. If not, expand hi.
    flo = g(low_amt)
    fhi = g(high_amt)
    expand = 0
    while fhi > 0.0 and expand < 60:
        high_amt *= 2.0
        fhi = g(high_amt)
        expand += 1

    # If even low gives <=0, return low
    if flo <= 0.0:
        return low_amt

    # bisection
    lo, hi = low_amt, high_amt
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fmid = g(mid)
        if abs(fmid) <= tol:
            return mid
        if fmid > 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def solve_monthly_amount_for_scenario_zero_glide(
    GlidePathPortfolioCls,
    weights_df,
    init_rt: int,
    init_val: float,
    contribution: float,
    T: int,
    n_assets: int,
    const: bool = True,
    pre_scenario: Optional[np.ndarray] = None,
    low_amt: float = 0.0,
    high_amt: Optional[float] = None,
    tol: float = 1e-8,
    max_iter: int = 100,
):
    '''
    Public wrapper for scenario[-1]==0 target.
    Returns:
      monthly_amount
    '''
    return _solve_monthly_amount_for_scenario_zero(
        GlidePathPortfolioCls=GlidePathPortfolioCls,
        weights_df=weights_df,
        T=T,
        n_assets=n_assets,
        init_rt=init_rt,
        init_val=init_val,
        contribution=contribution,
        const=const,
        pre_scenario=pre_scenario,
        low_amt=low_amt,
        high_amt=high_amt,
        tol=tol,
        max_iter=max_iter,
    )


def solve_annual_rate_of_initial_for_scenario_zero_glide(
    GlidePathPortfolioCls,
    weights_df,
    init_rt: int,
    init_val: float,
    contribution: float,
    T: int,
    n_assets: int,
    const: bool = True,
    pre_scenario: Optional[np.ndarray] = None,
    low_rate_ann: float = 0.0,
    high_rate_ann: float = 0.20,
    tol: float = 1e-8,
    max_iter: int = 100,
):
    '''
    Solve for an ANNUAL rate (of initial wealth) such that scenario[-1] ≈ 0.
    Internally uses monthly_amount = rate_ann * init_val / 12 and bisection on the rate.
    Returns:
      rate_ann, monthly_amount
    '''
    def f_rate(rate_ann: float) -> float:
        amt = ann_rate_to_monthly_amount(rate_ann, init_val=init_val)
        return _solve_monthly_amount_for_scenario_zero(
            GlidePathPortfolioCls=GlidePathPortfolioCls,
            weights_df=weights_df,
            T=T, n_assets=n_assets,
            init_rt=init_rt, init_val=init_val, contribution=contribution,
            const=const, pre_scenario=pre_scenario,
            low_amt=amt, high_amt=amt*1.0001, tol=1e-12, max_iter=2  # quick eval path to compute scenario[-1] at that amt
        )

    # We don't actually need a nested solve: define a direct g(rate) = scenario_final_at_monthly_amount(rate).
    import numpy as np

    def g(rate_ann: float) -> float:
        amt = ann_rate_to_monthly_amount(rate_ann, init_val=init_val)
        # compute scenario final at this amount
        import numpy as _np
        zeros_rets = _np.zeros((T, n_assets), dtype=float)
        gp = GlidePathPortfolioCls(weights_df)
        S, X, W = gp.run(
            rets=zeros_rets,
            init_rt=init_rt,
            init_val=init_val,
            contribution=contribution,
            withdrawal=amt,
            const=const,
            pre_scenario=pre_scenario,
        )
        return float(gp.scenario[-1])

    # Ensure high bound makes scenario <= 0 by expansion
    lo, hi = low_rate_ann, high_rate_ann
    flo, fhi = g(lo), g(hi)
    expand = 0
    while fhi > 0.0 and hi < 10.0 and expand < 60:  # up to 1000%/year
        hi *= 2.0
        fhi = g(hi)
        expand += 1
    if flo <= 0.0:
        return lo, ann_rate_to_monthly_amount(lo, init_val=init_val)

    # bisection on rate
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fmid = g(mid)
        if abs(fmid) <= tol:
            amt = ann_rate_to_monthly_amount(mid, init_val=init_val)
            return mid, amt
        if fmid > 0.0:
            lo = mid
        else:
            hi = mid
    mid = 0.5 * (lo + hi)
    return mid, ann_rate_to_monthly_amount(mid, init_val=init_val)
