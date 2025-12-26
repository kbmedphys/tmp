import numpy as np
import pandas as pd

def classify_month_type(index: pd.DatetimeIndex) -> pd.Series:
    mt = pd.Series(index=index, dtype="object")
    for t in index:
        m = t.month % 3
        if m == 1:
            mt[t] = 'N'
        elif m == 2:
            mt[t] = 'R'
        else:
            mt[t] = '3'
    return mt

def build_predictor(mkt: pd.Series):
    index = mkt.index
    month_type = classify_month_type(index)
    is_newsy = (month_type == "N")
    news_series = mkt[is_newsy]

    S = pd.Series(index=index, dtype=float)
    for t in index:
        past = news_series[news_series.index <= t]
        if len(past) >= 4:
            S[t] = past.iloc[-4:].sum()
        else:
            S[t] = np.nan

    x = pd.Series(index=index, dtype=float)
    S_hist = []
    for i in range(1, len(index)):
        prev_date = index[i-1]
        curr_date = index[i]

        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue

        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return S, x

def build_beta(y, x, min_obs):
    index = x.index
    beta = pd.Series(index=index, dtype=float)
    for i, t in enumerate(index):
        mask = (index <= t) & x.notna() & y.notna()
        n = mask.sum()
        if n < min_obs:
            beta[t] = np.nan
            continue

        xi = x[mask].values
        yi = y[mask].values
        denom = (xi ** 2).sum()
        beta[t] = (xi * yi).sum() / denom if denom > 0 else np.nan

    w_raw = pd.Series(index=index, dtype=float)
    for t in index:
        if np.isnan(beta[t]) or np.isnan(x[t]):
            w_raw[t] = 0.0
        else:
            w_raw[t] = beta[t] * x[t]

    return beta, w_raw