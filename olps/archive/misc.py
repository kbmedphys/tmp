import numpy as np

class ATVS:
    def __init__(self, prices, vix):
        self.prices = prices
        self.rets = np.diff(self.prices) / self.prices[:-1]
        self.vix = vix
        self.n = self.prices.shape[0]

        self.start_idx = 0
        self.end_idx = self.n - 1
        self.current_idx = self.start_idx

        self.initial_price = 1
        self.initial_x = 1
        self.cost_rate = 1e-03
        self.threshold = 0.025

        self.lookback_window = 100
        self.halflife = 30
        self.days_per_year = 252

        self.target_vol = 0.14
        self.beta = 2.1
        self.xi = 0.2
    
    def reset(self):
        self.current_idx = self.start_idx
    
    def run(self, target_vol=0.14, active=False, both=False):
        self.reset()
        current_idx = self.current_idx
        self.target_vol = target_vol

        self.S = np.zeros(self.n)
        self.x = np.zeros(self.n)
        self.vol = np.zeros(self.n)
        self.smoothed_vix = np.zeros(self.n)
        self.expected_sharpe = np.zeros(self.n)
        self.z_score = np.zeros(self.n)
        
        self.S[current_idx] = self.initial_price
        self.x[current_idx] = self.initial_x
        while True:
            rets = self.rets[current_idx] * self.x[current_idx]
            current_idx += 1
            
            self.S[current_idx] = self.S[current_idx-1] * (1 + rets)
            self.vol[current_idx] = np.maximum(self.get_vol(current_idx), 1e-06)
            self.smoothed_vix[current_idx] = np.maximum(self.get_vix(current_idx), 1e-06)
            self.expected_sharpe[current_idx] = self.beta * np.power(self.smoothed_vix[current_idx], 2) / self.vol[current_idx]
            
            if both:
                self.z_score[current_idx] = self.get_z_score(current_idx)
            else:
                self.z_score[current_idx] = np.maximum(self.get_z_score(current_idx), 0)
            
            if active:
                self.x[current_idx] = np.minimum((self.target_vol / self.vol[current_idx]) * (1 + self.xi * self.z_score[current_idx]), 1)
            else:
                self.x[current_idx] = np.minimum((self.target_vol / self.vol[current_idx]), 1)

            self.x[current_idx] = np.minimum(self.x[current_idx], 1)
            self.x[current_idx] = self.x[current_idx] if np.abs(self.x[current_idx] - self.x[current_idx-1]) >= self.threshold else self.x[current_idx-1]
            self.S[current_idx] -= self.cost_rate * self.S[current_idx] * np.abs(self.x[current_idx] - self.x[current_idx-1])

            if current_idx == self.end_idx:
                break

        return self.S, self.x
    
    def get_z_score(self, current_idx):
        days_per_year = self.days_per_year if self.expected_sharpe[:current_idx+1].shape[0] >= self.days_per_year else self.expected_sharpe[:current_idx+1].shape[0]
        z_score = (self.expected_sharpe[current_idx] - np.mean(self.expected_sharpe[current_idx+1-days_per_year:current_idx+1])) / np.std(self.expected_sharpe[current_idx+1-days_per_year:current_idx+1], ddof=1)
        return z_score

    def get_vix(self, current_idx):
        lookback_window = self.lookback_window if self.rets[:current_idx].shape[0] >= self.lookback_window else self.rets[:current_idx].shape[0]
        halflife = self.halflife if self.rets[:current_idx].shape[0] >= self.halflife else self.rets[:current_idx].shape[0]
        lambd = -np.log(0.5) / halflife
        inv_idx = np.arange(lookback_window-1, -1, -1)
        weights = np.exp(-lambd * inv_idx) / ((1-np.exp(-lambd * lookback_window)) / (1-np.exp(-lambd)))
        vix = np.sum(weights * self.vix[current_idx-lookback_window:current_idx])
        return vix

    def get_vol(self, current_idx):
        lookback_window = self.lookback_window if self.rets[:current_idx].shape[0] >= self.lookback_window else self.rets[:current_idx].shape[0]
        halflife = self.halflife if self.rets[:current_idx].shape[0] >= self.halflife else self.rets[:current_idx].shape[0]
        lambd = -np.log(0.5) / halflife
        inv_idx = np.arange(lookback_window-1, -1, -1)
        weights = np.exp(-lambd * inv_idx) / ((1-np.exp(-lambd * lookback_window)) / (1-np.exp(-lambd)))
        vol = np.sum(weights * np.power(self.rets[current_idx-lookback_window:current_idx] - np.mean(self.rets[current_idx-lookback_window:current_idx]), 2))
        return np.sqrt(vol * self.days_per_year)
