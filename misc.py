import numpy as np
import pandas as pd
from sklearn.cluster import kmeans_plusplus
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist

class JumpModel:
    def __init__(self, n_regimes=2, jump_penalty=0, max_iter=10, tol=1e-08, n_init = 10):
        self.n_regimes = n_regimes
        self.jump_penalty = jump_penalty * (np.ones((n_regimes, n_regimes)) - np.eye(n_regimes))
        self.max_iter = max_iter
        self.tol = tol
        self.n_init = n_init
        
    def fit(self, X):
        np.random.seed(42)
        random_state = np.random.randint(0, 100, self.n_init)
        init_centers = np.array([
            kmeans_plusplus(X, self.n_regimes, random_state=random_state[idx])[0]
            for idx in range(self.n_init)
        ])
        best_val = np.inf
        best_res = {}
        best_res["labels"] = None
        for idx, centers in enumerate(init_centers):
            labels_pre, val_pre = None, np.inf
            labels, probs, val = self.E_step(X, centers)
            
            num_iter = 0
            while (
                num_iter < self.max_iter
                and (not self.is_same_clustering(labels, labels_pre))
                and val_pre - val > self.tol
            ):
                num_iter += 1
                labels_pre, val_pre = labels, val
                centers = self.M_step(X, probs)
                labels, probs, val = self.E_step(X, centers)
            
            if (not self.is_same_clustering(best_res["labels"], labels)) and val < best_val:
                best_val = val
                best_res["centers"] = centers
                best_res["labels"] = labels
                best_res["probs"] = probs
        
        self.val = best_val
        self.centers = best_res["centers"]
        self.probs = best_res["probs"]
        self.labels = best_res["labels"]
        return self
    
    def prediction(self, X):
        labels, probs, val = self.E_step(X, self.centers)
        return labels, probs
    
    def M_step(self, X, weights):
        weighted_sum = weights.T @ X
        Ns = weights.sum(axis=0, keepdims=True).T
        means = weighted_sum / Ns
        return means
    
    def E_step(self, X, centers):
        penalty_mat = self.jump_penalty
        loss_mat = 0.5 * cdist(X, centers, "sqeuclidean")
        labels, probs, val = self.dp(loss_mat, penalty_mat)
        return labels, probs, val
    
    def dp(self, loss_mat, penalty_mat):
        n_s, n_c = loss_mat.shape
        values, assign = np.empty((n_s, n_c)), np.empty(n_s, dtype=int)
        values[0] = loss_mat[0]
        for t in range(1, n_s):
            values[t] = loss_mat[t] + (values[t-1][:, np.newaxis] + penalty_mat).min(axis=0)
        
        assign[-1] = values[-1].argmin()
        value_opt = values[-1, assign[-1]]
        for t in range(n_s - 1, 0, -1):
            assign[t-1] = (values[t-1] + penalty_mat[:, assign[t]]).argmin()
        
        probs = np.zeros((n_s, n_c))
        probs[range(n_s), assign] = 1
        return assign, probs, value_opt
    
    def is_same_clustering(self, labels1, labels2):
        def is_map_from_left_to_right(labels_left, labels_right):
            if labels_left is None or labels_right is None:
                return False
            assert len(labels_left) == len(labels_right)
            for label in np.unique(labels_left):
                if len(np.unique(labels_right[labels_left==label])) != 1:
                    return False
            return True
        return is_map_from_left_to_right(labels1, labels2) and is_map_from_left_to_right(labels2, labels1)

class Clipper:
    def __init__(self, mul=3):
        self.mul = mul
        self.lb = None
        self.ub = None

    def fit(self, X):
        mean = X.mean(axis=0).to_numpy()
        std = X.std(axis=0).to_numpy()
        self.lb = mean - self.mul * std
        self.ub = mean + self.mul * std
        return self
    
    def transform(self, X):
        if self.ub is None and self.lb is None: return X
        return np.clip(X, self.lb, self.ub)
    
    def fit_transform(self, X):
        return self.fit(X).transform(X)

class Scaler:
    def __init__(self):
        pass

    def fit(self, X):
        self.scaler = StandardScaler().fit(X)
        return self
    
    def transform(self, X):
        return self.scaler.transform(X)
    
    def fit_transform(self, X):
        return self.fit(X).transform(X)

def feature_engineer(rets):
    
    def ewm_mean(x, hl): 
        return x.ewm(halflife=hl, adjust=False).mean()
    
    def ewm_downside(x, hl):
        neg = x.clip(upper=0)
        dd = np.sqrt((neg**2).ewm(halflife=hl, adjust=False).mean())
        return np.log(dd + 1e-8)
    
    feats = pd.DataFrame(index=rets.index)
    
    feats["dd_log_hl5"] = ewm_downside(rets, 5)
    feats["dd_log_hl21"] = ewm_downside(rets, 21)
    
    for hl in [5, 10, 21]:
        feats[f"mean_hl{hl}"] = ewm_mean(rets, hl)
    
    return feats

def rearange_labels(labels, vals):
    mean_vals = {label: vals[labels == label].mean() for label in np.unique(labels)}
    sorted_vals = sorted(mean_vals.items(), key = lambda x: x[1])
    rearange_map = {new_key: old_key for new_key, (old_key, value) in enumerate(sorted_vals)}
    rearange_labels = [rearange_map[label] for label in labels]
    return np.array(rearange_labels)