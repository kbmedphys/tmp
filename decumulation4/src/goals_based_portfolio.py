import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# ----------------- DP policy with period-end fixed withdrawal (const flag) -----------------
def build_rt_portfolio_returns(df_returns: pd.DataFrame, weights: pd.DataFrame) -> Dict[int, np.ndarray]:
    asset_cols = [c for c in weights.columns if c.startswith("asset")]
    rt_series = {}
    M = df_returns[asset_cols].to_numpy()
    for _, row in weights.iterrows():
        rt = int(row["RT"])
        wv = row[asset_cols].to_numpy(dtype=float)
        r_ser = (M @ wv)
        rt_series[rt] = r_ser.astype(float)
    return rt_series

def _interp1(x, y, xq):
    return np.interp(xq, x, y, left=y[0], right=y[-1])

@dataclass
class DPCfg:
    sims: int = 150
    n_grid: int = 90
    lambda_hi: float = 40.0
    max_bisect: int = 12
    log_margin_hi: float = 0.7

@dataclass
class PolicyDP:
    grid_w: np.ndarray
    policy: List[np.ndarray]
    lambda_star: float
    S: List[np.ndarray]
    R: List[np.ndarray]
    plan_rt: int
    A: float
    scenario: np.ndarray

def fit_dynamic_policy_for_plan_rt(
    model,
    df_returns: pd.DataFrame,
    weights: pd.DataFrame,
    plan_rt: int,
    init_val: float,
    n_steps: int,
    W_target: float,
    W_loss: float,
    p_loss_req: float,
    const: bool = True,   # per your request
    cfg: DPCfg = DPCfg(),
    seed: int = 20250916
) -> PolicyDP:
    rng = np.random.default_rng(seed)
    scenario, scenario_q, A = model.get_const_scenario(plan_rt, init_val, n_steps, schedule_mode="quantile", q=0.5)

    rt_ret = build_rt_portfolio_returns(df_returns, weights)
    #rt_list = sorted(rt_ret.keys())
    rt_list = list(range(0, plan_rt+1)) # no-risk up

    # Pre-sample per RT once (common random numbers, speed-up)
    smp_by_rt = {rt: rt_ret[rt][rng.integers(0, len(rt_ret[rt]), size=cfg.sims)] for rt in rt_list}

    lo = max(1e-6, W_loss*0.9)
    hi = max(W_target, init_val) * np.exp(cfg.log_margin_hi)
    grid_w = np.exp(np.linspace(np.log(lo), np.log(hi), cfg.n_grid))

    def solve_for_lambda(lam: float):
        S_next = (grid_w >= W_target).astype(float)
        R_next = np.ones_like(S_next)
        Pol = [None]*n_steps
        S_list = [None]*(n_steps+1); R_list=[None]*(n_steps+1)
        S_list[n_steps] = S_next.copy(); R_list[n_steps] = R_next.copy()

        for k in reversed(range(n_steps)):
            S_k = np.zeros_like(S_next); R_k = np.zeros_like(R_next); A_k = np.zeros(grid_w.size, dtype=int)
            for i, w in enumerate(grid_w):
                best_val=-1.0; best_rt=rt_list[0]; bestS=0.0; bestR=0.0
                # const=True 固定額 → スケールは常に 1.0
                scale = 1.0
                for rt in rt_list:
                    r_smp = smp_by_rt[rt]
                    w_pre = w*(1.0 + r_smp)
                    withdraw = np.minimum(A*scale, w_pre)
                    w_next = w_pre - withdraw
                    alive = (w_next >= W_loss)
                    if not np.any(alive):
                        s_val = 0.0; r_val = 0.0
                    else:
                        s_val = float(np.mean(_interp1(grid_w, S_next, w_next[alive])))
                        r_val = float(np.mean(_interp1(grid_w, R_next, w_next[alive])))
                    obj = s_val + lam*r_val
                    if obj > best_val:
                        best_val=obj; best_rt=rt; bestS=s_val; bestR=r_val
                S_k[i]=bestS; R_k[i]=bestR; A_k[i]=best_rt
            S_next, R_next = S_k, R_k
            S_list[k]=S_k.copy(); R_list[k]=R_k.copy(); Pol[k]=A_k.copy()
        return Pol, S_list, R_list

    Pol0, S0_list, R0_list = solve_for_lambda(0.0)
    R0 = float(_interp1(grid_w, R0_list[0], np.array([init_val]))[0])
    if R0 >= p_loss_req:
        return PolicyDP(grid_w, Pol0, 0.0, S0_list, R0_list, plan_rt, A, scenario)

    PolH, SH_list, RH_list = solve_for_lambda(cfg.lambda_hi)
    RH = float(_interp1(grid_w, RH_list[0], np.array([init_val]))[0])
    if RH < p_loss_req:
        return PolicyDP(grid_w, PolH, cfg.lambda_hi, SH_list, RH_list, plan_rt, A, scenario)

    loL, hiL = 0.0, cfg.lambda_hi
    best = (PolH, SH_list, RH_list, cfg.lambda_hi)
    for _ in range(cfg.max_bisect):
        mid = 0.5*(loL+hiL)
        PolM, SM_list, RM_list = solve_for_lambda(mid)
        Rmid = float(_interp1(grid_w, RM_list[0], np.array([init_val]))[0])
        if Rmid >= p_loss_req:
            best = (PolM, SM_list, RM_list, mid)
            hiL = mid
        else:
            loL = mid
    PolB, SB_list, RB_list, lam_star = best
    return PolicyDP(grid_w, PolB, lam_star, SB_list, RB_list, plan_rt, A, scenario)

def run_const_dynamic_with_returns(
    model, weights: pd.DataFrame, policy: PolicyDP, init_val: float, rets_path: np.ndarray, const: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    n_steps = rets_path.shape[0]
    asset_cols = [c for c in weights.columns if c.startswith("asset")]
    W_table = {int(row["RT"]): row[asset_cols].to_numpy(dtype=float) for _, row in weights.iterrows()}

    def choose_rt(k: int, w: float) -> int:
        i = np.searchsorted(policy.grid_w, w, side="right") - 1
        i = int(np.clip(i, 0, policy.grid_w.size-1))
        return int(policy.policy[k][i])

    S = np.zeros(n_steps+1); S[0]=init_val
    rt_path = np.zeros(n_steps+1, dtype=int); rt_path[0]=policy.plan_rt
    record_withdrawal = np.zeros(n_steps+1)

    for k in range(1, n_steps+1):
        rt_km1 = choose_rt(k-1, S[k-1])
        wv = W_table[rt_km1]
        r_p = float(rets_path[k-1] @ wv)
        S_pre = S[k-1]*(1.0 + r_p)
        scale = 1.0 # const=True → 固定額
        withdrawal = min(policy.A*scale, S_pre)
        S[k] = S_pre - withdrawal
        record_withdrawal[k] = withdrawal
        rt_path[k] = rt_km1
    return S, rt_path, record_withdrawal