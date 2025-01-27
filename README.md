# tmp

import numpy as np
from scipy.optimize import minimize

# 投資データ (価格と保有比率)
prices_portfolio = np.array([[1.0, 1.2], [1.1, 0.9], [0.8, 1.5]])  # 各観測の資産価格
quantities_portfolio = np.array([[0.6, 0.4], [0.5, 0.5], [0.7, 0.3]])  # 各観測の保有割合

def calculate_hmi_with_scipy(prices, quantities):
    T = len(prices)  # 観測の数

    # 目的関数: HMIを最大化 (負の符号で最小化問題に変換)
    def objective(x):
        A = x[:T]  # A_tの値 (バイナリ相当)
        return -np.sum(A) / T

    # 制約条件を構築
    constraints = []
    bounds = []

    # 変数の範囲設定
    for t in range(T):
        bounds.append((0, 1))  # A_tのバイナリ範囲
    for t in range(T):
        for v in range(T):
            bounds.append((0, 1))  # U_{t,v}の範囲
    for t in range(T):
        bounds.append((0, 1))  # u_tの範囲

    # 制約条件 (IP-1, IP-2): u の順序を守る
    for t in range(T):
        for v in range(T):
            constraints.append({
                'type': 'ineq',
                'fun': lambda x, t=t, v=v: x[T + t * T + v] - (x[2 * T + t] - x[2 * T + v])
            })  # IP-1
            constraints.append({
                'type': 'ineq',
                'fun': lambda x, t=t, v=v: (x[2 * T + t] - x[2 * T + v]) - x[T + t * T + v]
            })  # IP-2

    # 制約条件 (IP-5, IP-6): GARPを満たす部分集合 A_t を設定
    alpha = 100  # 適当な大きな値
    delta = 0.01  # 適当な小さな値
    for t in range(T):
        for v in range(T):
            constraints.append({
                'type': 'ineq',
                'fun': lambda x, t=t, v=v: \
                    alpha * (x[T + t * T + v] + 1 - x[t]) - (np.dot(prices[t], quantities[t]) - np.dot(prices[t], quantities[v]) + delta)
            })  # IP-5
            constraints.append({
                'type': 'ineq',
                'fun': lambda x, t=t, v=v: \
                    (np.dot(prices[v], quantities[v]) - np.dot(prices[t], quantities[t])) - alpha * (x[T + v * T + t] + x[t] - 2)
            })  # IP-6

    # 初期値
    x0 = np.zeros(T + T * T + T)  # A, U, u の初期値

    # 最適化実行
    result = minimize(objective, x0, bounds=bounds, constraints=constraints, method='SLSQP')

    # 結果の取得
    if result.success:
        x = result.x
        hmi_value = -result.fun
        selected_observations = [t for t in range(T) if x[t] > 0.5]
        return hmi_value, selected_observations
    else:
        raise ValueError("Optimization failed")

# 投資データに基づくHMI計算
hmi_value_portfolio, selected_observations_portfolio = calculate_hmi_with_scipy(prices_portfolio, quantities_portfolio)
hmi_value_portfolio, selected_observations_portfolio
