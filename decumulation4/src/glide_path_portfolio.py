import numpy as np
import pandas as pd
from scipy.stats import norm 

class GlidePathPortfolio:
    def __init__(self, weights):
        self.weights = weights.iloc[:, 3:].values
        self.sigma = weights.iloc[:, 1].values
        self.mu = weights.iloc[:, 2].values
        self.dt = 1/12
        self.k = -0.842

    def get_scenario(self, rt, init_val, contri, withdr):
        except_ret = (self.mu[rt] - 0.5 * np.power(self.sigma[rt], 2)) * self.dt
        val = init_val * np.exp(except_ret)
        val += contri
        val -= withdr
        return val
    
    def run(self, rets, init_rt, init_val, contribution, withdrawal, const, pre_scenario=None):
        n = rets.shape[0] + 1
        m = rets.shape[1]
        current_idx = 0
        end_idx = n - 1

        rt = init_rt
        contributions = contribution * np.ones(n)
        withdrawals = withdrawal * np.ones(n)
        total_withdrawal = 0

        scenario_flag = False if pre_scenario is None else True

        S = np.zeros(n)
        S[current_idx] = init_val
        w = np.zeros((n, m))
        w[current_idx] = self.weights[rt]
        x = np.zeros((n, m))
        x[current_idx] = self.weights[rt] * (init_val + contributions[current_idx])
        
        scenario = np.zeros(n)
        scenario[current_idx] = pre_scenario[current_idx] if scenario_flag else init_val
        record_rt = np.zeros(n)
        record_rt[current_idx] = rt
        record_withdrawals = np.zeros(n)
        record_withdrawals[current_idx] = 0
        while True:
            current_idx += 1
            withdrawal_const = 1 if const else (S[current_idx-1] / scenario[current_idx-1] if scenario[current_idx-1] != 0 else 1.0)
            scenario[current_idx] = pre_scenario[current_idx] if scenario_flag else self.get_scenario(rt, scenario[current_idx-1], contributions[current_idx-1], withdrawals[current_idx-1])

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

            X1 = total_withdrawal + scenario[current_idx-1] * np.exp(
                (self.mu[rt] - 0.5 * np.power(self.sigma[rt], 2)) * self.dt + self.sigma[rt] * np.sqrt(self.dt) * self.k
            )
            X2 = (total_withdrawal + scenario[current_idx-1]) * np.exp(
                (self.mu[init_rt] - 0.5 * np.power(self.sigma[init_rt], 2)) * self.dt + self.sigma[init_rt] * np.sqrt(self.dt) * self.k
            )
            rt = rt if X1 >= X2 else np.maximum(rt - 1, 0) 
            record_rt[current_idx] = rt
            if current_idx == end_idx:
                break
            
        self.scenario = scenario
        self.record_rt = record_rt
        self.record_withdrawals = record_withdrawals
        self.total_withdrawal = total_withdrawal
        return S, x, w