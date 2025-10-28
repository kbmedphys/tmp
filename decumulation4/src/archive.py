import numpy as np
import pandas as pd
from scipy.stats import norm 

class FixedPortfolio:
    def __init__(self, weights):
        self.weights = weights.iloc[:, 3:].values
        self.sigma = weights.iloc[:, 1].values
        self.mu = weights.iloc[:, 2].values
        self.dt = 1/12

    def get_scenario(self, rt, init_val, contri, withdr):
        except_ret = (self.mu[rt] - 0.5 * np.power(self.sigma[rt], 2)) * self.dt
        val = init_val * np.exp(except_ret)
        val += contri
        val -= withdr
        return val
    
    def get_const_scenario(self, rt, init_val, n_steps, schedule_mode, q):
        
        if schedule_mode == "mean":
            g = (1.0 + self.mu[rt]) ** self.dt
        elif schedule_mode == "median":
            g = float(np.exp((self.mu[rt] - 0.5 * self.sigma[rt]**2) * self.dt))
        elif schedule_mode == "quantile":
            g_med = float(np.exp((self.mu[rt] - 0.5 * self.sigma[rt]**2) * self.dt))
            zq = norm.ppf(q)
            g = float(np.exp((self.mu[rt] - 0.5 * self.sigma[rt]**2) * self.dt + (self.sigma[rt]*np.sqrt(self.dt)) * zq))
        else:
            raise ValueError("schedule_mode must be 'mean' or 'median'")
        
        if abs(g - 1.0) < 1e-12:
            A = init_val / n_steps
        else:
            A = ( (g**n_steps) * init_val * (g - 1.0) ) / ( (g**n_steps) - 1.0 )
        
        S_med = np.zeros(n_steps + 1)
        S_hat = np.zeros(n_steps + 1)
        S_med[0] = init_val
        S_hat[0] = init_val
        for t in range(1, n_steps + 1):
            S_med[t] = g_med * S_med[t-1] - A
            S_hat[t] = g * S_hat[t-1] - A
        
        return S_med, S_hat, float(A)
    
    def run(self, rets, init_rt, init_val, contribution, withdrawal, const, q):
        n = rets.shape[0] + 1
        m = rets.shape[1]
        current_idx = 0
        end_idx = n - 1

        rt = init_rt
        scenario, scenario_q, W = self.get_const_scenario(rt, init_val, n, schedule_mode="quantile", q=q)
        #scenario, W = self.get_const_scenario(rt, init_val, n, schedule_mode="median", q=q)

        contributions = contribution * np.ones(n)
        withdrawals = W * np.ones(n)
        total_withdrawal = 0

        S = np.zeros(n)
        S[current_idx] = init_val
        w = np.zeros((n, m))
        w[current_idx] = self.weights[rt]
        x = np.zeros((n, m))
        x[current_idx] = self.weights[rt] * (init_val + contributions[current_idx])
        
        record_withdrawals = np.zeros(n)
        record_withdrawals[current_idx] = 0
        while True:
            current_idx += 1
            withdrawal_const = 1 if const else (S[current_idx-1] / scenario[current_idx-1] if scenario[current_idx-1] != 0 else 1.0)
            S[current_idx] = np.dot(1 + rets[current_idx-1], x[current_idx-1])
            S[current_idx] += contributions[current_idx]
            current_withdrawal = (withdrawals[current_idx] * withdrawal_const) if S[current_idx] >= (withdrawals[current_idx] * withdrawal_const) else S[current_idx]
            S[current_idx] -= current_withdrawal
            total_withdrawal -= current_withdrawal
            record_withdrawals[current_idx] = current_withdrawal

            if np.abs(np.sum(w[current_idx-1] - self.weights[rt])) > 0:
                x[current_idx] = S[current_idx] * self.weights[rt]
            else:
                x[current_idx] = x[current_idx-1] * (1 + rets[current_idx-1])
                x[current_idx] += (contributions[current_idx] * self.weights[rt])
                x_withdrawal = (withdrawals[current_idx]* self.weights[rt]) * withdrawal_const
                x_withdrawal = x_withdrawal if np.sum(x[current_idx]) >= np.sum(x_withdrawal) else x[current_idx]
                x[current_idx] -= x_withdrawal
            
            if S[current_idx] > 0:
                w[current_idx] = x[current_idx] / S[current_idx]
            else:
                w[current_idx] = 0

            if current_idx == end_idx:
                break
            
        self.scenario = scenario
        self.scenario_q = scenario_q
        self.record_withdrawals = record_withdrawals
        self.total_withdrawal = total_withdrawal
        self.W = W
        return S, x, w
    
    """
    def run(self, rets, init_rt, init_val, contribution, withdrawal, const):
        n = rets.shape[0] + 1
        m = rets.shape[1]
        current_idx = 0
        end_idx = n - 1

        rt = init_rt
        contributions = contribution * np.ones(n)
        withdrawals = withdrawal * np.ones(n)
        total_withdrawal = 0

        S = np.zeros(n)
        S[current_idx] = init_val
        w = np.zeros((n, m))
        w[current_idx] = self.weights[rt]
        x = np.zeros((n, m))
        x[current_idx] = self.weights[rt] * (init_val + contributions[current_idx])
        scenario = np.zeros(n)
        scenario[current_idx] = init_val
        record_withdrawals = np.zeros(n)
        record_withdrawals[current_idx] = 0
        while True:
            current_idx += 1
            withdrawal_const = 1 if const else (S[current_idx-1] / scenario[current_idx-1] if scenario[current_idx-1] != 0 else 1.0)
            scenario[current_idx] = self.get_scenario(rt, scenario[current_idx-1], contributions[current_idx-1], withdrawals[current_idx-1])
            S[current_idx] = np.dot(1 + rets[current_idx-1], x[current_idx-1])
            S[current_idx] += contributions[current_idx]
            current_withdrawal = (withdrawals[current_idx] * withdrawal_const) if S[current_idx] >= (withdrawals[current_idx] * withdrawal_const) else S[current_idx]
            S[current_idx] -= current_withdrawal
            total_withdrawal -= current_withdrawal
            record_withdrawals[current_idx] = current_withdrawal

            if np.abs(np.sum(w[current_idx-1] - self.weights[rt])) > 0:
                x[current_idx] = S[current_idx] * self.weights[rt]
            else:
                x[current_idx] = x[current_idx-1] * (1 + rets[current_idx-1])
                x[current_idx] += (contributions[current_idx] * self.weights[rt])
                x_withdrawal = (withdrawals[current_idx]* self.weights[rt]) * withdrawal_const
                x_withdrawal = x_withdrawal if np.sum(x[current_idx]) >= np.sum(x_withdrawal) else x[current_idx]
                x[current_idx] -= x_withdrawal
            
            if S[current_idx] > 0:
                w[current_idx] = x[current_idx] / S[current_idx]
            else:
                w[current_idx] = 0

            if current_idx == end_idx:
                break
            
        self.scenario = scenario
        self.record_withdrawals = record_withdrawals
        self.total_withdrawal = total_withdrawal
        return S, x, w
    """