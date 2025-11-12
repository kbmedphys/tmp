# 専門家向け解説

**User:** Anonymous (kbmedphys@gmail.com)  
**Created:** 11/12/2025 14:41:54  
**Updated:** 11/12/2025 19:03:53  
**Exported:** 11/12/2025 20:45:00  
**Link:** [https://chatgpt.com/c/69141e21-f434-8320-a094-56fa36fe7e12](https://chatgpt.com/c/69141e21-f434-8320-a094-56fa36fe7e12)  

## Response:
以下は、添付論文 **“Dynamic Asset Allocation with Asset-Specific Regime Forecasts” (Yizhan Shu, Chenyu Yu, John Mulvey, 2024)** の内容を専門家向けに日本語で詳細に解説したものです

2406.09578v2

。  
本論文は、金融市場における\*\*資産ごとのレジーム予測を組み込んだ動的資産配分（Dynamic Asset Allocation）\*\*の新しい枠組みを提示しています。

* * *

🔹 1. 研究背景と目的
-------------

### マーコウィッツ理論の限界

Markowitz（1952）の平均分散理論では、ポートフォリオ最適化は

1.  リターンとリスクの予測（forecasting）
2.  最適化（optimization）  
    の2段階で行われます。  
    しかし、**予測の誤差**が大きいと、最適化段階は「誤差増幅器（error maximizer）」になりうる（Michaud, 1989）。

本研究は、リターンそのものを予測する代わりに、**市場レジーム（bullish/bearish状態）を予測対象とする**ことで、信号対雑音比（SNR）を高め、より頑健な最適化を実現することを目的としています。

* * *

🔹 2. 従来手法との違い
--------------

従来のレジームベース手法は、マクロ経済指標や株価指数を基に**全資産共通の経済レジーム**（例：景気拡張・後退）を推定していました（Ang & Bekaert, 2004 など）。  
本研究の革新点は、**各資産ごとに独立した市場レジームを識別・予測**する点にあります。これにより、資産間で異なる市場ダイナミクスを捉え、ポートフォリオ全体の柔軟性と多様性を向上させます

2406.09578v2

。

* * *

🔹 3. モデル構造の概要
--------------

### ハイブリッド・レジーム予測フレームワーク

本研究は2段階の「**unsupervised-supervised hybrid**」構造を採用します。

1.  **レジーム識別（Identification）**
    *   モデル：**Statistical Jump Model (JM)**
    *   目的：過去データからレジーム（bull/bear）を**教師なしで**識別
    *   特徴量：資産リターン系列から導かれる8種の指標（移動平均リターン・ダウンサイド偏差・Sortino比など）
    *   出力：各日付に対するレジームラベル  $s_t$ 
2.  **レジーム予測（Forecasting）**
    *   モデル：**XGBoost分類器**（Gradient Boosted Decision Tree）
    *   目的：翌日のレジームを**教師ありで**予測
    *   特徴量：
        *   資産固有のリターン特徴（上記8種）
        *   クロスアセット・マクロ特徴（5種：金利・イールドカーブ・VIX・株債相関など）
    *   出力：翌日のレジーム確率  $f_{t+1}$ 

この「**クラスタリング→分類**」構成により、レジームラベルを教師信号として活用し、ノイズを抑えた予測が可能となります

2406.09578v2

。

* * *

🔹 4. Statistical Jump Model（JM）の詳細
-----------------------------------

### モデル定式化

時系列特徴  $x_t \in \mathbb{R}^D$  に対し、JMは以下の最適化問題を解きます：

$$
\min_{\Theta,S} \sum_{t=0}^{T-1} l(x_t,\theta_{s_t}) + \lambda \sum_{t=1}^{T-1} \mathbf{1}_{\{s_{t-1} \neq s_t\}}
$$
*    $l(\cdot,\cdot)$ ：距離（通常は二乗誤差）
*    $\lambda$ ：**ジャンプペナルティ（jump penalty）**  
    → レジーム遷移の頻度を抑え、時系列の平滑性を調整
*    $s_t \in \{0,1\}$ ：各期のレジーム（bull/bear）

 $\lambda$  を大きくするとレジームはより**持続的（persistent）**になり、小さいと**高頻度で切り替わる**ようになります。  
したがって  $\lambda$  はSNRの調整パラメータとして機能します

2406.09578v2

。

### 特徴量設計

| 種類 | ハーフライフ | 内容 |
| --- | --- | --- |
| Downside Deviation（対数） | 5日・21日 | 下方リスク指標 |
| 平均リターン | 5, 10, 21日 | リターン傾向 |
| Sortino Ratio | 5, 10, 21日 | リスク調整リターン |

これらの特徴量は各資産ごとに計算され、JMが**資産固有の市場レジーム**を抽出します。

* * *

🔹 5. ハイパーパラメータ最適化
------------------

### 時系列クロスバリデーション

*   検証期間：直近5年間
*   評価指標：**0/1戦略のSharpe比**

0/1戦略とは、予測レジームがbullishなら100%リスク資産、bearishなら100%無リスク資産に投資する単純戦略。  
各資産においてこのSharpe比を最大化する $\lambda$ を選択し、次の半年間に適用します

2406.09578v2

。

* * *

🔹 6. ポートフォリオ最適化ステップ
--------------------

### 共通数理形式

$$
\max_w \; w^\top \mu - \gamma_{\text{risk}} w^\top \Sigma w - \gamma_{\text{trade}} a \|w - w_{\text{pre}}\|_1
$$

subject to:

$$
0 \le w \le w_{ub}, \quad 1^\top w \le L
$$
*    $\mu$ ：リターン予測（レジーム依存）
*    $\Sigma$ ：EWM共分散（半減期252日）
*    $a$ ：取引コスト（5bps）

* * *

🔹 7. 三つのポートフォリオモデル
-------------------

| モデル | レジーム活用方法 | 特徴 |
| --- | --- | --- |
| **MinVar (JM-XGB)** | bullish資産に10bpsリターンを割当 | 低リスク・高安定性 |
| **MV (JM-XGB)** | JMのレジーム別平均リターンを利用 | 平均分散最適化 |
| **EW (JM-XGB)** | bullish資産間で均等配分 | ベンチマーク比較用 |

いずれも、bullish資産が3銘柄以下の場合は**全額リスクフリー**とする安全弁を設けています

2406.09578v2

。

* * *

🔹 8. 実証分析（1991–2023）
---------------------

### データセット

*   12資産＋無リスク資産  
    （例：S&P500, EAFE, EM, AggBond, REIT, Commodity, Gold など）
*   日次リターン：Bloomberg
*   リスクフリー：3M Treasury（FRED）

### 主な結果

1.  **0/1戦略**
    *   すべての資産で最大ドローダウンが大幅減少（例：S&P500では半減）
    *   Sharpe比は買い持ち戦略を一貫して上回る
2.  **JM-XGBポートフォリオ**
    *   MinVar, MV, EWのいずれのモデルでも**リスク調整後パフォーマンスが改善**
    *   ベア局面で有効な**ダウンサイド保護効果**を確認
3.  **資産間の多様なレジーム挙動**
    *   REITのベア局面はLargeCapより早期（サブプライム影響）
    *   債券と株式でレジーム非同期性を観測 → 分散効果を強化

* * *

🔹 9. 理論的含意と実務的貢献
-----------------

*   **理論的貢献**
    *   レジーム識別（unsupervised）と予測（supervised）を明確に分離
    *   ジャンプモデルによりレジームラベルの**SNR最適化**を定量的に実施
    *   「asset-specific regime」という新しい概念を導入
*   **実務的貢献**
    *   各資産ごとのレジーム情報をポートフォリオ最適化に統合
    *   取引コストを考慮した**実運用可能なフレームワーク**
    *   Gurobiによる高速最適化（12資産で1日あたり5秒以内）

* * *

🔹 10. まとめと今後の展望
----------------

本研究は、レジーム予測を資産単位で生成し、Markowitz最適化に統合することで、

*   ノイズに強く、
*   動的に適応し、
*   ダウンサイドリスクを軽減する

ポートフォリオ構築法を実現しました。  
今後は、**レジーム情報を共分散構造にも組み込む拡張**や、**マルチファクター・ブラックリッターマンモデルとの統合**が期待されます。

* * *

ご希望があれば、この内容を\*\*スライド構成（概要→モデル→実証→結論）\*\*にまとめる英語版または日本語版の発表用資料として整形することも可能です。作成いたしましょうか？

## Response:
思考時間: 23s

了解です。論文のJMで使う「資産ごとのリターン由来の8特徴量」を作る Python 実装を用意しました。  
（EWM＝指数加重、DD＝ダウンサイド偏差（ログ変換版で特徴量化）、平均リターン、Sortino 比）

*   DD（ログ）：半減期 5, 21 日
*   平均リターン：半減期 5, 10, 21 日
*   Sortino 比：半減期 5, 10, 21 日（= 平均 / DD）
*   標準化：学習区間で z-score を学習し、適用（スキーマは scikit-learn 風）

単一資産 Series でも、複数資産 DataFrame でも動きます（列ごとに独立に計算）。

```python
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Iterable, Optional, Dict, Tuple, Union

ArrayLike = Union[pd.Series, pd.DataFrame]

def _ewm_mean(x: pd.Series, halflife: int) -> pd.Series:
    return x.ewm(halflife=halflife, adjust=False, min_periods=1).mean()

def _ewm_downside_dev(ret: pd.Series, halflife: int, eps: float = 1e-12) -> pd.Series:
    """
    EWM 下でのダウンサイド偏差（負リターンの二乗平均の平方根）。
    """
    neg = ret.clip(upper=0.0)
    var_dd = neg.pow(2).ewm(halflife=halflife, adjust=False, min_periods=1).mean()
    dd = np.sqrt(var_dd).clip(lower=eps)  # 数値安定化
    return dd

def _ensure_df(x: ArrayLike) -> pd.DataFrame:
    if isinstance(x, pd.Series):
        return x.to_frame("asset")
    elif isinstance(x, pd.DataFrame):
        return x
    else:
        raise TypeError("Input must be pandas Series or DataFrame.")

@dataclass
class JMFeatureEngineer:
    """
    Jump Model (JM) 用の特徴量エンジニアリング:
      - DD(log): halflife in {5, 21}
      - Mean:    halflife in {5, 10, 21}
      - Sortino: halflife in {5, 10, 21}
    学習（fit）区間で各特徴を z-score 化するための平均・標準偏差を保持。
    """
    dd_halflives: Iterable[int] = (5, 21)
    mean_halflives: Iterable[int] = (5, 10, 21)
    sortino_halflives: Iterable[int] = (5, 10, 21)
    eps: float = 1e-12

    # feature_name -> (mean, std)
    scalers_: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    fitted_: bool = False

    def compute_raw_features(
        self,
        excess_returns: ArrayLike,
    ) -> pd.DataFrame:
        """
        生の特徴量を計算（標準化はしない）。
        Parameters
        ----------
        excess_returns : Series or DataFrame
            超過リターン（例：資産リターン - 無リスクリターン）。日次推奨。
        Returns
        -------
        DataFrame: 列は MultiIndex (asset, feature) で返す
        """
        df = _ensure_df(excess_returns).copy()
        # 列名を string に統一
        df.columns = [str(c) for c in df.columns]

        out_cols = {}
        for col in df.columns:
            r = df[col].astype(float)

            # Downside Deviation (log)
            for hl in self.dd_halflives:
                dd = _ewm_downside_dev(r, halflife=hl, eps=self.eps)
                dd_log = np.log(dd)  # 論文は DD をログ変換して特徴化
                out_cols[(col, f"dd_log_hl{hl}")] = dd_log

            # EWM Mean
            for hl in self.mean_halflives:
                mu = _ewm_mean(r, halflife=hl)
                out_cols[(col, f"mean_hl{hl}")] = mu

            # Sortino Ratio = Mean / DD（DD はログ変換せずに使用）
            for hl in self.sortino_halflives:
                mu = _ewm_mean(r, halflife=hl)
                dd = _ewm_downside_dev(r, halflife=hl, eps=self.eps)
                sortino = mu / dd.replace(0, np.nan)
                out_cols[(col, f"sortino_hl{hl}")] = sortino

        feat = pd.DataFrame(out_cols)
        feat.columns = pd.MultiIndex.from_tuples(feat.columns, names=["asset", "feature"])
        return feat

    def fit(
        self,
        features: pd.DataFrame,
        train_slice: Optional[slice] = None,
    ) -> "JMFeatureEngineer":
        """
        学習区間（train_slice）で各特徴の平均・標準偏差を学習（z-score 用）。
        features: MultiIndex columns: (asset, feature)
        train_slice: 例) slice("2000-01-01", "2010-12-31") または None（全期間）
        """
        if train_slice is not None:
            X = features.loc[train_slice]
        else:
            X = features

        # 特徴ごと（asset 別に同名 feature は同じスケーリングにしたい場合は、
        # 下の groupby level を "feature" のみに変える。ここでは資産別に独立スケーリング）
        for col in X.columns:
            s = X[col].astype(float)
            m = float(s.mean(skipna=True))
            v = float(s.std(skipna=True, ddof=0))
            # ゼロ分散対策
            if not np.isfinite(v) or v < self.eps:
                v = 1.0
            self.scalers_[str(col)] = (m, v)

        self.fitted_ = True
        return self

    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        学習済みスケーラで z-score 標準化。
        """
        if not self.fitted_:
            raise RuntimeError("Call fit() before transform().")
        Z = pd.DataFrame(index=features.index, columns=features.columns, dtype=float)
        for col in features.columns:
            key = str(col)
            m, v = self.scalers_.get(key, (0.0, 1.0))
            Z[col] = (features[col].astype(float) - m) / v
        return Z

    def fit_transform(
        self,
        features: pd.DataFrame,
        train_slice: Optional[slice] = None,
    ) -> pd.DataFrame:
        self.fit(features, train_slice=train_slice)
        return self.transform(features)

def compute_excess_return(
    asset_returns: ArrayLike,
    rf_returns: Optional[pd.Series] = None,
) -> ArrayLike:
    """
    超過リターンを計算。rf_returns が None の場合はそのまま返す。
    - asset_returns: Series or DataFrame（パーセントではなく実数：0.01 = 1%）
    - rf_returns:    Series（日次の無リスクリターン）
    """
    X = _ensure_df(asset_returns).astype(float)
    if rf_returns is None:
        return X if isinstance(asset_returns, pd.DataFrame) else X.iloc[:, 0]
    rf = rf_returns.reindex(X.index).astype(float).fillna(0.0)
    if isinstance(asset_returns, pd.Series):
        return (X.iloc[:, 0] - rf).rename(asset_returns.name)
    else:
        return X.sub(rf, axis=0)

# ===== 使い方（例） =====
if __name__ == "__main__":
    # ダミーデータ作成（実運用では実データに置き換え）
    idx = pd.date_range("2000-01-01", "2024-12-31", freq="B")
    np.random.seed(7)
    # 年率 ~10%・年ボラ ~15% を日次に換算したラフな擬似データ
    mu_d = 0.10 / 252
    sig_d = 0.15 / np.sqrt(252)
    r1 = pd.Series(np.random.normal(mu_d, sig_d, len(idx)), index=idx, name="assetA")
    r2 = pd.Series(np.random.normal(mu_d*0.7, sig_d*1.2, len(idx)), index=idx, name="assetB")
    rf = pd.Series(0.02/252, index=idx, name="rf")  # 年率2%相当の一定無リスク

    # 複数資産の DataFrame
    R = pd.concat([r1, r2], axis=1)

    # 超過リターン
    Rex = compute_excess_return(R, rf_returns=rf)

    # 特徴量計算
    fe = JMFeatureEngineer()
    raw_feat = fe.compute_raw_features(Rex)

    # 学習区間（例：2000-01-01〜2010-12-31）で標準化を学習し、全期間に適用
    Z = fe.fit_transform(raw_feat, train_slice=slice("2000-01-01", "2010-12-31"))

    # 単一資産だけを渡す場合（Series）
    Rex_single = compute_excess_return(r1, rf_returns=rf)
    raw_single = fe.compute_raw_features(Rex_single)
    Z_single = fe.fit_transform(raw_single, train_slice=slice("2000-01-01", "2010-12-31"))

    # 結果の列（MultiIndex）：(asset, feature)
    print(Z.columns[:10])
    print(Z.tail())
```

### 実装メモ

*   \*\*DD（ログ）\*\*は `np.log(DD)` を採用（数値安定化のためクリップ＆epsを付与）。
*   **Sortino 比** は `平均 / DD`（DD はログ前の値を使用）。
*   **標準化**は資産×特徴の各列ごと（列単位）に z-score。資産横断で同一特徴を共通スケーリングしたい場合は `fit()` 内で列レベルを `"feature"` のみにまとめる実装に変更してください。
*   **学習窓**は論文にならい「過去11年」を想定できます。運用時は半年ごとに `fit` し直す運用が自然です。
*   **入力**は「**超過リターン**」を想定。`compute_excess_return` で無リスクを差し引けます。

必要であれば、この出力フォーマットから **JM 学習器（クラスタ数=2）用に X 行列を作るヘルパ**や、**半減期の候補を変える設定**、**学習窓ローリングのユーティリティ**も追記します。

## Response:
以下は、JM（Jump Model）用特徴量を**最小構成で計算するシンプル実装**です。  
依存は `pandas` と `numpy` のみです。

```python
import pandas as pd
import numpy as np

def jm_features(returns: pd.Series) -> pd.DataFrame:
    """
    JM（Statistical Jump Model）用特徴量の最小実装。
    入力: returns … 資産の超過リターン（Series, indexは日付）
    出力: DataFrame（8列）
    """
    # 指数加重移動平均
    def ewm_mean(x, hl): return x.ewm(halflife=hl, adjust=False).mean()
    def ewm_downside(x, hl):
        neg = x.clip(upper=0)
        dd = np.sqrt((neg**2).ewm(halflife=hl, adjust=False).mean())
        return np.log(dd + 1e-8)  # log変換
    
    feats = pd.DataFrame(index=returns.index)
    
    # Downside Deviation (log)
    feats["dd_log_hl5"] = ewm_downside(returns, 5)
    feats["dd_log_hl21"] = ewm_downside(returns, 21)
    
    # 平均リターン
    for hl in [5, 10, 21]:
        feats[f"mean_hl{hl}"] = ewm_mean(returns, hl)
    
    # Sortino比 = 平均 / DD（非log版）
    for hl in [5, 10, 21]:
        dd = np.sqrt((returns.clip(upper=0)**2).ewm(halflife=hl, adjust=False).mean())
        feats[f"sortino_hl{hl}"] = ewm_mean(returns, hl) / (dd + 1e-8)
    
    return feats

# === 使用例 ===
if __name__ == "__main__":
    np.random.seed(0)
    idx = pd.date_range("2020-01-01", "2024-12-31", freq="B")
    r = pd.Series(np.random.normal(0.0003, 0.01, len(idx)), index=idx)
    
    features = jm_features(r)
    print(features.head())
```

### 🔍 説明

| 特徴量 | 内容 | 半減期 |
| --- | --- | --- |
| `dd_log_hl5`, `dd_log_hl21` | ダウンサイド偏差（log） | 5日・21日 |
| `mean_hl5`, `mean_hl10`, `mean_hl21` | 指数加重平均リターン | 5,10,21日 |
| `sortino_hl5`, `sortino_hl10`, `sortino_hl21` | Sortino比 | 5,10,21日 |

この関数で得られる8列の特徴量を、各資産ごとに JM の入力特徴として利用できます。

## Response:
了解です。**JMで得たレジームラベル（0/1）を「翌日レジーム」へ教師あり学習する XGBoost 最小実装**を示します。  
入力は「特徴量 DataFrame（行=日付、列=特徴）」「JMが付与済みのレジーム Series（0/1、行=日付、当日レジーム）」の2つだけ。  
出力は学習済みモデルと、テスト区間の予測確率・予測ラベルです（オプションで確率のEWM平滑化も可）。

```python
# 最小依存: pandas, numpy, xgboost
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from dataclasses import dataclass
from xgboost import XGBClassifier

@dataclass
class XGBRegimeForecaster:
    """
    Jump Model（JM）で推定した当日レジーム s_t (0/1) を教師信号に、
    特徴量 x_t から翌日レジーム s_{t+1} を予測する最小実装。

    - feat_df: 形状 (T, D) の特徴量（行=日付index, 列=特徴）
    - regime_labels: 形状 (T,) の Series（JMの当日レジーム 0/1）
                     ※ 0=ブル、1=ベア（論文に合わせるならこの向き）
    - horizon: 既定=1（翌日レジームを予測）
    - train_end: 学習期間の最終日（文字列 "YYYY-MM-DD" など）。
                 None の場合は先頭80%を学習に使用（時系列スプリット）
    - smooth_halflife: 予測確率の指数平滑の半減期（Noneで平滑なし）
    - xgb_params: XGBClassifier のパラメータ（指定しなければデフォルト最小構成）
    """
    feat_df: pd.DataFrame
    regime_labels: pd.Series
    horizon: int = 1
    train_end: Optional[str] = None
    smooth_halflife: Optional[int] = None
    xgb_params: Optional[Dict[str, Any]] = None

    def fit_predict(self):
        # 1) 教師信号を horizon だけ先にシフト（s_{t+1} を t の特徴で当てる）
        y = self.regime_labels.shift(-self.horizon).reindex(self.feat_df.index)
        # ラベルが欠ける末尾を落とす
        valid_idx = y.dropna().index
        X = self.feat_df.loc[valid_idx]
        y = y.loc[valid_idx].astype(int)

        # 2) 時系列スプリット（train_end 指定が無い場合は 8:2）
        if self.train_end is not None:
            train_mask = X.index <= pd.to_datetime(self.train_end)
        else:
            split = int(len(X) * 0.8)
            train_mask = pd.Series(False, index=X.index)
            train_mask.iloc[:split] = True

        X_train, y_train = X.loc[train_mask], y.loc[train_mask]
        X_test,  y_test  = X.loc[~train_mask], y.loc[~train_mask]

        # 3) XGBoost 最小構成（ヒストグラム分割で高速）
        params = dict(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            random_state=42,
            n_jobs=-1,
        )
        if self.xgb_params:
            params.update(self.xgb_params)

        clf = XGBClassifier(**params)
        clf.fit(X_train, y_train)

        # 4) 予測（確率）
        proba_test = pd.Series(
            clf.predict_proba(X_test)[:, 1],
            index=X_test.index,
            name="p_bear_next"
        )

        # 5) オプション: 確率の指数平滑（レジーム持続性の弱さを緩和）
        if self.smooth_halflife is not None and self.smooth_halflife > 0:
            proba_smoothed = proba_test.ewm(halflife=self.smooth_halflife, adjust=False).mean()
        else:
            proba_smoothed = proba_test.copy()

        # 6) 閾値 0.5 でクラス化（>0.5 をベア=1）
        y_pred = (proba_smoothed >= 0.5).astype(int)
        y_pred.name = "y_pred_bear_next"

        # 7) 返却（学習器・テスト期間の実測/確率/予測）
        return {
            "model": clf,
            "X_train": X_train, "y_train": y_train,
            "X_test": X_test,   "y_test": y_test,
            "proba_raw": proba_test,
            "proba_smoothed": proba_smoothed,
            "y_pred": y_pred,
            "feature_importance": pd.Series(clf.feature_importances_, index=X.columns, name="gain")
        }

# ===== 使い方（最小例） =====
if __name__ == "__main__":
    # ダミーデータ作成: 特徴量(3列) + JMラベル(0/1)
    idx = pd.date_range("2010-01-01", "2020-12-31", freq="B")
    rng = np.random.default_rng(0)
    feat = pd.DataFrame({
        "mean_hl5":  rng.normal(0, 1, len(idx)),
        "dd_log_hl5":rng.normal(0, 1, len(idx)),
        "sortino_hl5":rng.normal(0, 1, len(idx)),
    }, index=idx)

    # JMで得た当日レジーム（0=ブル, 1=ベア）と仮定（ここではダミー）
    base = rng.normal(0, 1, len(idx)).cumsum()
    regime = pd.Series((base > np.median(base)).astype(int), index=idx, name="regime_t")

    forecaster = XGBRegimeForecaster(
        feat_df=feat,
        regime_labels=regime,
        horizon=1,                 # s_{t+1} を予測
        train_end="2017-12-31",    # 時系列で学習期間を区切る（未指定なら8:2）
        smooth_halflife=8,         # 予測確率を少し平滑化（無しなら None）
        xgb_params=None            # 追加/上書きしたい時に辞書を渡す
    )
    res = forecaster.fit_predict()

    print("Test AUC-ish quick check (not exact AUC):",
          np.corrcoef(res["y_test"], res["proba_smoothed"])[0,1])
    print("Feature importance (gain):")
    print(res["feature_importance"].sort_values(ascending=False).head())

    # レジームに基づく 0/1 戦略の簡易ビュー（ベア=1なら無リスクと仮定）
    # ここではテスト期間の「資産リターン」をダミー生成して評価例を付与
    r_test = pd.Series(rng.normal(0.0003, 0.01, len(res["y_test"])), index=res["y_test"].index)
    rf_test = pd.Series(0.02/252, index=r_test.index)  # 年率2%の無リスク
    # 予測がベア=1のときは rf、ブル=0のときは r を採用
    strategy_ret = np.where(res["y_pred"]==1, rf_test.values, r_test.values)
    strat = pd.Series(strategy_ret, index=r_test.index)
    sharpe = strat.mean() / strat.std(ddof=0) * np.sqrt(252)
    print("0/1 strategy Sharpe (test):", sharpe)
```

### 使い方の要点

*   **学習データ**
    *   `feat_df`: JM特徴量（例：先に作成した `jm_features()` の出力や追加マクロ特徴を連結したもの）。
    *   `regime_labels`: JMで得た**当日**レジーム（0/1）。本実装内で `shift(-1)` し、**翌日ラベル**を教師信号にします。
*   **時系列分割**
    *   `train_end="YYYY-MM-DD"` を指定すると、その日までを学習、その後をテストにします。未指定なら 8:2 で先頭を学習に。
*   **確率の平滑化**
    *   `smooth_halflife` を指定すると `predict_proba` の系列に EWM 平滑をかけ、持続性のブレを抑えます（例：8）。
*   **しきい値**
    *   既定は 0.5（>0.5 をベア=1）。必要に応じて変数化してください。

必要であれば、**マクロ特徴（2Y金利、10Y-2Yスロープ、VIX、株債相関）を追加して `feat_df` に結合する最小関数**や、**複数資産を同時に回すラッパ**、\*\*0/1戦略の評価関数（リターン系列を渡してSharpe/MDDを算出）\*\*もすぐ足します。

## Response:
了解です。論文の Table 3 に沿って、**2Y金利・10Y–2Yスロープ・VIX・株債相関**を計算し、既存の `feat_df`（行=日付・列=特徴）に結合する**最小実装**です。依存は `pandas` と `numpy` のみ。

```python
import pandas as pd
import numpy as np

def add_macro_features(
    feat_df: pd.DataFrame,
    y2: pd.Series,          # 米国2年金利（実数 or %。単位は一貫していればOK）
    y10: pd.Series,         # 米国10年金利
    vix: pd.Series,         # VIX指数（レベル）
    stock_ret: pd.Series,   # 株式リターン（例：LargeCap日次リターン）
    bond_ret: pd.Series,    # 債券リターン（例：AggBond日次リターン）
    corr_window: int = 252  # 株債相関のローリング窓（営業日換算で1年）
) -> pd.DataFrame:
    """
    論文のクロスアセット・マクロ特徴を計算して feat_df に結合（最小実装）。

    - 2Y金利の差分のEWMA(hl=21): y2_diff_ewm21
    - イールドカーブ(10Y-2Y)のEWMA(hl=10): slope_ewm10
    - イールドカーブ差分のEWMA(hl=21): slope_diff_ewm21
    - VIXのlog差分のEWMA(hl=63): vix_logdiff_ewm63
    - 株債相関（ローリング相関, 窓=252営業日）: stock_bond_corr_252d
    """
    # インデックス整形 & アライン
    idx = pd.Index(feat_df.index).sort_values()
    y2  = y2.reindex(idx).astype(float)
    y10 = y10.reindex(idx).astype(float)
    vix = vix.reindex(idx).astype(float)
    stock_ret = stock_ret.reindex(idx).astype(float)
    bond_ret  = bond_ret.reindex(idx).astype(float)

    # ユーティリティ
    def ewm_mean(x, hl): 
        return x.ewm(halflife=hl, adjust=False).mean()

    # 2Y金利 差分のEWMA(hl=21)
    y2_diff_ewm21 = ewm_mean(y2.diff(), hl=21).rename("y2_diff_ewm21")

    # イールドカーブ（10Y-2Y）
    slope = (y10 - y2)
    slope_ewm10       = ewm_mean(slope, hl=10).rename("slope_ewm10")
    slope_diff_ewm21  = ewm_mean(slope.diff(), hl=21).rename("slope_diff_ewm21")

    # VIX: log差分のEWMA(hl=63)
    vix_logdiff = np.log(vix.replace(0, np.nan)).diff()  # 0回避
    vix_logdiff_ewm63 = ewm_mean(vix_logdiff, hl=63).rename("vix_logdiff_ewm63")

    # 株債相関（ローリング相関）
    stock_bond_corr = stock_ret.rolling(corr_window).corr(bond_ret).rename(f"stock_bond_corr_{corr_window}d")

    macro = pd.concat(
        [y2_diff_ewm21, slope_ewm10, slope_diff_ewm21, vix_logdiff_ewm63, stock_bond_corr],
        axis=1
    )

    return pd.concat([feat_df, macro], axis=1)

# ===== 使い方（最小例） =====
if __name__ == "__main__":
    np.random.seed(7)
    idx = pd.date_range("2012-01-01", "2024-12-31", freq="B")

    # 例: 既存のJM特徴（ダミー3列）
    feat_df = pd.DataFrame({
        "mean_hl5":   np.random.normal(0, 1, len(idx)),
        "dd_log_hl5": np.random.normal(0, 1, len(idx)),
        "sortino_hl5":np.random.normal(0, 1, len(idx)),
    }, index=idx)

    # マクロ入力（ダミー）
    y2  = pd.Series(0.02 + 0.00001*np.arange(len(idx)) + np.random.normal(0, 0.0005, len(idx)), index=idx)  # 2Y
    y10 = pd.Series(0.03 + 0.00001*np.arange(len(idx)) + np.random.normal(0, 0.0005, len(idx)), index=idx)  # 10Y
    vix = pd.Series(18 + np.random.normal(0, 0.5, len(idx)), index=idx)  # レベル
    stock_ret = pd.Series(np.random.normal(0.0003, 0.01, len(idx)), index=idx)
    bond_ret  = pd.Series(np.random.normal(0.00015, 0.004, len(idx)), index=idx)

    feat_all = add_macro_features(feat_df, y2, y10, vix, stock_ret, bond_ret)
    print(feat_all.tail())
```

### メモ

*   **単位**：金利・VIXの単位は差分/比率で使うため、%でも実数でも一貫していれば問題ありません（差分は「％ポイント差」になります）。
*   **指数平滑(EWMA)**：
    *   2Y差分→hl=21、スロープ→hl=10、スロープ差分→hl=21、VIX log差分→hl=63（論文設定）
*   **株債相関**：`Series.rolling(window).corr(other)` で高速に算出（ここでは 252 営業日 ≒ 1年）。
*   **アライン**：`feat_df.index` に全入力Seriesを `reindex` して結合（最小実装のため欠損埋めはしません）。

この `feat_all` をそのまま `XGBRegimeForecaster(feat_df=feat_all, ...)` に渡せば、JMラベルから**翌日レジーム確率**を予測できます。

## Response:
Federal Reserve Bank of St. Louis の Federal Reserve Economic Data (FRED) からマクロ変数を取得するために必要な API キーについて、以下に整理します。

* * *

### ✅ 必要なキー／準備事項

1.  FRED 用の **API キー（32 文字の英数字・小文字）** を取得する。 [FRED+1](https://fred.stlouisfed.org/docs/api/api_key.html?utm_source=chatgpt.com)
2.  API を呼び出す際は、URL クエリパラメータまたは HTTP ヘッダーにこのキーを含める。例えば：
    ```
    https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key=<あなたのキー>&file_type=json
    ```
    [FRED+1](https://fred.stlouisfed.org/docs/api/api_key.html?utm_source=chatgpt.com)  
    またバージョン 2 以降では、ヘッダーに `Authorization: Bearer <キー>` を使えるという説明もあります。 [FRED](https://fred.stlouisfed.org/docs/api/fred/v2/api_key.html?utm_source=chatgpt.com)
3.  アカウント登録が必要。ログイン後に「Request or view your API keys」から自分専用のキーを発行できます。 [FRED+1](https://fred.stlouisfed.org/docs/api/api_key.html?utm_source=chatgpt.com)
4.  Python などで利用するライブラリ（例： fredapi ）を使う場合は、環境変数 `FRED_API_KEY` にキーを設定するのが一般的です。 [PyPI+1](https://pypi.org/project/fredapi/?utm_source=chatgpt.com)

* * *

もしよろしければ、 **2 年金利・10 年‐2 年スロープ・VIX・株債相関** を FRED からダウンロードするサンプルコード（キー読み込み込み）も作成できます。いかがしますか？

## Response:
良い質問です。  
FRED（Federal Reserve Economic Data）で、論文で使われたようなマクロ変数（2Y金利、10Y–2Yスロープ、VIX、株債相関）を取得するための代表的 **ticker（series ID）** を以下にまとめます。  
これらは FRED の REST API や Python ライブラリ（`fredapi`）で直接利用可能です。

* * *

📊 主なマクロ変数の FRED Ticker 一覧
--------------------------

| 目的 | 内容 | FRED Ticker | 単位・備考 |
| --- | --- | --- | --- |
| **短期金利** | 米国2年国債利回り | `DGS2` | 日次、単位: %、U.S. Treasury Constant Maturity 2-Year |
| **長期金利** | 米国10年国債利回り | `DGS10` | 日次、単位: %、U.S. Treasury Constant Maturity 10-Year |
| **イールドスプレッド** | 10年－2年スプレッド | `T10Y2Y` | 日次、単位: %、(10Y – 2Y) 自動計算済み series |
| **ボラティリティ指標** | CBOE Volatility Index (VIX) | `VIXCLS` | 日次、単位: index level |
| **株式リターン** | S&P500日次リターン | `SP500` | 日次、index。リターンにする場合は `pct_change()` |
| **債券リターン** | Bloomberg Barclays U.S. Aggregate Bond Index (近似代替) | `BAMLCC0A0CMTRIV` | 日次、Total Return Index（ICE BofA U.S. Corporate, proxy） |
| **無リスク金利** | 3か月国庫短期証券利回り | `TB3MS` | 月次（必要なら日次補間） |
| **インフレ率（補足）** | 消費者物価指数（CPI） | `CPIAUCSL` | 月次、補足指標に使用可能 |

* * *

💡 Python での取得例（`fredapi`）
--------------------------

```python
from fredapi import Fred
import pandas as pd

fred = Fred(api_key="YOUR_FRED_API_KEY")

# 金利系
y2 = fred.get_series('DGS2')      # 2年金利
y10 = fred.get_series('DGS10')    # 10年金利
slope = fred.get_series('T10Y2Y') # 10Y-2Y スプレッド

# ボラティリティ
vix = fred.get_series('VIXCLS')

# 株式・債券リターン系列
sp500 = fred.get_series('SP500')
bond_index = fred.get_series('BAMLCC0A0CMTRIV')

# 株債リターン
stock_ret = sp500.pct_change()
bond_ret  = bond_index.pct_change()

# 結合（必要に応じて）
macro_df = pd.concat([y2, y10, slope, vix, stock_ret, bond_ret], axis=1)
macro_df.columns = ["y2", "y10", "slope", "vix", "stock_ret", "bond_ret"]
```

* * *

🔍 参考
-----

| 変数 | 出典URL |
| --- | --- |
| DGS2 | [https://fred.stlouisfed.org/series/DGS2](https://fred.stlouisfed.org/series/DGS2) |
| DGS10 | [https://fred.stlouisfed.org/series/DGS10](https://fred.stlouisfed.org/series/DGS10) |
| T10Y2Y | [https://fred.stlouisfed.org/series/T10Y2Y](https://fred.stlouisfed.org/series/T10Y2Y) |
| VIXCLS | [https://fred.stlouisfed.org/series/VIXCLS](https://fred.stlouisfed.org/series/VIXCLS) |
| SP500 | [https://fred.stlouisfed.org/series/SP500](https://fred.stlouisfed.org/series/SP500) |
| BAMLCC0A0CMTRIV | [https://fred.stlouisfed.org/series/BAMLCC0A0CMTRIV](https://fred.stlouisfed.org/series/BAMLCC0A0CMTRIV) |
| TB3MS | [https://fred.stlouisfed.org/series/TB3MS](https://fred.stlouisfed.org/series/TB3MS) |

* * *

もしご希望があれば、これらをすべて自動で取得・加工して  
`add_macro_features()` に直接渡せる形（DataFrame）に整える  
完全な Python スクリプト（ダウンロード＋整形）もお作りします。  
作成しますか？

## Response:
思考時間: 1m 0s

了解です。論文の XGBoost で使っている**マクロ特徴に限定**すると、FRED から必要になる ticker（series ID）は次のとおりです（株債相関は“計算”なので FRED の ticker はありません）。

必要な FRED ticker（XGBoost用マクロ特徴に対応）
---------------------------------

*   **2年金利（US 2Y Treasury Constant Maturity）**: `DGS2`
    *   使い方：差分 → EWMA(halflife=21) を特徴化（`y2_diff_ewm21`）
*   **イールドカーブ・スロープ（10Y−2Y）**: `T10Y2Y`
    *   使い方：レベルの EWMA(hl=10)（`slope_ewm10`）と、差分の EWMA(hl=21)（`slope_diff_ewm21`）
    *   ※ スロープを自前計算するなら `DGS10` と `DGS2` から `DGS10 - DGS2` でも可（論文はスロープ系列を直接利用）
*   **VIX（CBOE Volatility Index）**: `VIXCLS`
    *   使い方：`log(VIX)` の差分 → EWMA(hl=63)（`vix_logdiff_ewm63`）

FRED に ticker が無いもの
-------------------

*   **株債相関（Stock–Bond Correlation）**: なし（自前計算）
    *   S&P 500（例：`SP500`）と **Bloomberg US Aggregate Bond Index（AggBond）** の**日次リターン**から、ローリング相関（例：252 営業日）を計算
    *   ※ AggBond のトータルリターン指数は **FREDには直接の公式系列がありません**（論文では Bloomberg 由来データを使用）。どうしても FRED で代替するなら近似として **社債TR**（例：`BAMLCC0A0CMTRIV` 等）を使う手もありますが、厳密には別物です。

* * *

### 最小マッピング例（Python用）

```python
FRED_TICKERS = {
    "y2": "DGS2",        # 2Y yield
    "slope_10y_2y": "T10Y2Y",  # 10Y-2Y spread
    "vix": "VIXCLS",     # VIX index (level)
    # "y10": "DGS10",    # 自前で slope = DGS10 - DGS2 を作る場合のみ
    # "spx": "SP500",    # 株債相関を計算するなら使う（価格指数→pct_change）
    # AggBond は FRED なし（Bloomberg由来）。代替の例: "BAMLCC0A0CMTRIV"
}
```

この3系列（`DGS2`, `T10Y2Y`, `VIXCLS`）に、手元の **S&P500 リターン** と **AggBond リターン** を組み合わせれば、論文の XGBoost で用いたマクロ特徴だけに絞って再現できます。

## Response:
了解。FREDの **3系列（DGS2, T10Y2Y, VIXCLS）だけ** を取得し、XGBoost用マクロ特徴（論文準拠）を作って返す**最小実装**です。追加依存は `requests` と `pandas`、`numpy` のみ。

```python
import requests
import pandas as pd
import numpy as np

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

def _get_fred_series(series_id: str, api_key: str, start: str, end: str) -> pd.Series:
    """
    FRED から series_id を日次で取得し、pd.Series(date -> float) を返す最小実装。
    start/end は 'YYYY-MM-DD' 文字列。
    """
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
        "observation_end": end,
        "frequency": "d",          # 日次
        "aggregation_method": "eop" # 月次/週次が来ても期末値で揃える保険
    }
    r = requests.get(FRED_BASE, params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("observations", [])
    dates = [pd.to_datetime(d["date"]).normalize() for d in data]
    vals = pd.to_numeric([d["value"] for d in data], errors="coerce")
    s = pd.Series(vals, index=pd.DatetimeIndex(dates, name="date")).sort_index()
    return s.dropna()

def build_xgb_macro_features_from_fred(
    api_key: str,
    start: str,
    end: str,
    eps: float = 1e-12
) -> pd.DataFrame:
    """
    論文の XGBoost で使った3系列に限定したマクロ特徴量を生成して返す。

    - 2年金利 (DGS2): 差分の EWMA(hl=21) → y2_diff_ewm21
    - 10Y-2Y スロープ (T10Y2Y):
        レベルの EWMA(hl=10)           → slope_ewm10
        差分の EWMA(hl=21)              → slope_diff_ewm21
    - VIX (VIXCLS): log差分の EWMA(hl=63) → vix_logdiff_ewm63
    """
    # 1) FRED から 3 系列を取得
    y2   = _get_fred_series("DGS2",   api_key, start, end)     # 2Y yield (%)
    slope= _get_fred_series("T10Y2Y", api_key, start, end)     # 10Y-2Y (%)
    vix  = _get_fred_series("VIXCLS", api_key, start, end)     # VIX (level)

    # 2) 共通日付に揃える（最小実装: 内積集合でドロップ）
    idx = y2.index.intersection(slope.index).intersection(vix.index)
    y2, slope, vix = y2.loc[idx], slope.loc[idx], vix.loc[idx]

    # 3) ユーティリティ
    def ewm_mean(x: pd.Series, hl: int) -> pd.Series:
        return x.ewm(halflife=hl, adjust=False, min_periods=1).mean()

    # 4) 特徴量生成（単位は一貫していればOK。差分→％ポイント、VIXはログ差分）
    y2_diff_ewm21      = ewm_mean(y2.diff(), hl=21).rename("y2_diff_ewm21")
    slope_ewm10        = ewm_mean(slope, hl=10).rename("slope_ewm10")
    slope_diff_ewm21   = ewm_mean(slope.diff(), hl=21).rename("slope_diff_ewm21")
    vix_logdiff        = np.log(vix.replace(0, np.nan) + eps).diff()
    vix_logdiff_ewm63  = ewm_mean(vix_logdiff, hl=63).rename("vix_logdiff_ewm63")

    # 5) 結合して返す
    feats = pd.concat(
        [y2_diff_ewm21, slope_ewm10, slope_diff_ewm21, vix_logdiff_ewm63],
        axis=1
    )
    return feats

# ===== 使い方（最小例） =====
if __name__ == "__main__":
    # 事前に FRED の API キーを取得してください（文字列32文字程度）
    API_KEY = "YOUR_FRED_API_KEY"
    feats_macro = build_xgb_macro_features_from_fred(
        api_key=API_KEY,
        start="2010-01-01",
        end="2025-12-31"
    )
    print(feats_macro.tail())
```

### メモ

*   3系列だけ取得しているので、**株債相関は含めていません**（論文でもXGBに入れるマクロはこの3系列＋株債相関でしたが、相関は自前計算が必要です）。
*   欠損は最小実装のため **内積集合で落とす** だけにしています（必要なら `bfill/ffill` などを追加してください）。
*   単位は FRED のまま（% レベルや index レベル）。差分・ログ差分・EWMA なので単位一貫性があれば学習上は問題になりにくいです。
*   そのまま `feat_df`（JMの特徴）に `pd.concat([feat_df, feats_macro], axis=1)` で結合し、XGBoost の学習に渡せます。

## Response:
このエラーは、`response.json()` の中身が期待通りに `"observations"` を含んでいない（空または API キーが無効）場合に、  
`pd.DataFrame(observations)` が **空の DataFrame**（列なし）を返してしまい、  
その後の `df["date"]` にアクセスして **KeyError: 'date'** が起きたケースです。

* * *

### ✅ 対処法：安全に取得・検査するよう修正

以下のように `get_fred_data()` を書き換えてください。  
空データやAPIエラー時にも安全に動作します。

```python
import requests
import pandas as pd

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

def get_fred_data(series_id, start_date, end_date, api_key):
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }
    response = requests.get(FRED_URL, params=params, timeout=30)

    # --- 応答を安全に処理 ---
    if response.status_code != 200:
        raise RuntimeError(f"FRED API error {response.status_code}: {response.text}")

    data = response.json()
    if "observations" not in data:
        raise ValueError(f"No 'observations' in response for {series_id}: {data}")

    observations = data["observations"]
    if not observations:  # 空リスト
        print(f"Warning: no data returned for {series_id}")
        return pd.DataFrame(columns=["value"], index=pd.DatetimeIndex([], name="date"))

    # --- DataFrame変換 ---
    df = pd.DataFrame(observations)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"Unexpected FRED format for {series_id}: {df.head()}")

    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[["date", "value"]].set_index("date")
    return df
```

* * *

### ✅ 使用例

```python
API_KEY = "あなたのFRED_API_KEY"
start_date = "2010-01-01"
end_date   = "2025-12-31"

y2    = get_fred_data("DGS2",   start_date, end_date, API_KEY)
slope = get_fred_data("T10Y2Y", start_date, end_date, API_KEY)
vix   = get_fred_data("VIXCLS", start_date, end_date, API_KEY)

print(y2.tail(), slope.tail(), vix.tail())
```

* * *

### 💡補足

`KeyError: 'date'` が出たときに確認すべきポイント：

1.  **APIキーが正しいか？**  
    → 無効なキーだと `"error_message"` のみ返り `"observations"` がありません。
2.  **series\_id が存在するか？**  
    → 誤って `"T10Y2"` などにすると `"observations"` が空になります。
3.  **期間にデータがあるか？**  
    → 古すぎる・未来日を指定すると空のリストになります。

* * *

この修正版を使えば、キーが無効・データが空・形式が変わった場合も明示的に例外を出し、原因をすぐ把握できます。

## Response:
完璧です。その意図であれば、**3か月国債（DGS3MO）を基準インデックスにして全データをリサンプル・整列**するのが正解です。  
下のようにすれば、`rf_fred` の営業日ベースに他の金利やリターン系列を揃えられます。

* * *

### ✅ 推奨実装例

```python
import numpy as np
import pandas as pd

# --- 無リスク金利の取得 ---
rf_fred = get_fred_data("DGS3MO", start_date, end_date, api_key=API_KEY)  # 年率(%)
rf = np.log1p(rf_fred / 100) / 252.0  # 日次対数リターンに換算

# --- 他のリターンやマクロ系列（例：rets, y2, slope, vix）をこの rf に合わせる ---
# full_index を rf をベースに構築
full_index = rf.index.union(rets.index).sort_values()

# reindex で揃え、ffill で前方補完
raw_data = (
    pd.concat(
        [
            rets.reindex(full_index),
            y2.reindex(full_index),
            slope.reindex(full_index),
            vix.reindex(full_index),
            rf.reindex(full_index),
        ],
        axis=1
    )
    .ffill()
    .dropna()
)

raw_data.columns = ["rets", "y2", "slope", "vix", "rf"]
```

* * *

### 💡ポイント

1.  **`rf_fred`をベースに統一**  
    → 3か月国債はほぼ常に営業日データを持っているため、安定した日付ベースになります。
2.  **`np.log1p(rf_fred / 100) / 252` の意味**  
    年率（%）を日次対数リターン換算したものです：
    $$
    r_f^{(d)} = \frac{\ln(1 + r_f^{(\text{annual})}/100)}{252}
    $$
3.  **`union` と `ffill`**  
    → `rets` に欠損がある場合も、`rf` の日付に揃えて前方補完。  
    → `dropna()` は完全欠損列を削除。
4.  **マクロ特徴を作るときも同様に**  
    `build_xgb_macro_features_from_fred()` の出力（`feats_macro`）も `reindex(full_index)` → `ffill()` で統一。

* * *

### 🔧 結果的に

この構造にすると：

*   `rf` の日付がベース（安定）
*   すべてのシリーズが同じ index
*   モデル学習や特徴量結合が安全に行える

* * *

もしご希望があれば、  
`get_fred_data()` → `rf` → `build_xgb_macro_features_from_fred()` までを一連のパイプラインで処理し、  
**共通日付で統合済みの DataFrame**（`rets`, `rf`, `macro_features` を列に持つ）を自動生成する関数も作成できます。  
作成しますか？

## Response:
了解です。**各マクロ系列をまず“論文どおりに前処理”してから、共通日付に揃える**ワンストップ関数を用意しました。  
取得対象は FRED の 3 系列（`DGS2`, `T10Y2Y`, `VIXCLS`）＋無リスク（`DGS3MO`）です。  
依存は `requests`, `pandas`, `numpy` のみ。

```python
import requests
import pandas as pd
import numpy as np

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

# ---------- 安全版 FRED フェッチ ----------
def get_fred_data(series_id: str, start_date: str, end_date: str, api_key: str) -> pd.Series:
    """
    FREDから series_id を取得して pd.Series(date->float) を返す（安全版）。
    値はそのまま（% やレベル）。欠損・フォーマット異常は例外。
    """
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
        "frequency": "d",           # 可能なら日次を要求
        "aggregation_method": "eop" # 週次/月次が混在していても期末を選択
    }
    r = requests.get(FRED_URL, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"FRED API error {r.status_code}: {r.text}")

    data = r.json()
    if "observations" not in data:
        raise ValueError(f"No 'observations' in response for {series_id}: {data}")

    obs = data["observations"]
    if not obs:
        # 空のときは空Seriesを返す（後段のunionで消える可能性あり）
        return pd.Series(dtype=float, name=series_id)

    df = pd.DataFrame(obs)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"Unexpected FRED format for {series_id}: {df.head()}")

    s = pd.to_numeric(df["value"], errors="coerce")
    idx = pd.to_datetime(df["date"]).values
    out = pd.Series(s.values, index=pd.DatetimeIndex(idx, name="date")).sort_index()
    return out.dropna().rename(series_id)

# ---------- 論文どおりの前処理（各系列を単独で加工） ----------
def _ewm_mean(x: pd.Series, hl: int) -> pd.Series:
    return x.ewm(halflife=hl, adjust=False, min_periods=1).mean()

def preprocess_y2_diff_ewm21(y2: pd.Series) -> pd.Series:
    # 2年金利(DGS2)の差分→EWMA(hl=21)
    return _ewm_mean(y2.diff(), hl=21).rename("y2_diff_ewm21")

def preprocess_slope_features(slope: pd.Series) -> pd.DataFrame:
    # 10Y-2Yスロープ(T10Y2Y)：レベルEWMA(hl=10)、差分EWMA(hl=21)
    s_ewm10      = _ewm_mean(slope, hl=10).rename("slope_ewm10")
    s_diff_ewm21 = _ewm_mean(slope.diff(), hl=21).rename("slope_diff_ewm21")
    return pd.concat([s_ewm10, s_diff_ewm21], axis=1)

def preprocess_vix_logdiff_ewm63(vix: pd.Series, eps: float = 1e-12) -> pd.Series:
    # VIX(VIXCLS)：log差分→EWMA(hl=63)
    vld = np.log(vix.replace(0, np.nan) + eps).diff()
    return _ewm_mean(vld, hl=63).rename("vix_logdiff_ewm63")

def preprocess_rf_daily_logret(rf_3mo_annual_pct: pd.Series) -> pd.Series:
    # 無リスク金利(DGS3MO, 年率%) → 日次ログリターン換算
    return (np.log1p(rf_3mo_annual_pct / 100.0) / 252.0).rename("rf")

# ---------- パイプライン：前処理→共通日付揃え ----------
def build_regime_xgb_dataset_with_macro(
    rets: pd.Series,   # 対象資産の日次リターン（例：超過ではなく生リターン）
    start_date: str,
    end_date: str,
    api_key: str,
    base_on_rf: bool = True,
    dropna: bool = True,
) -> pd.DataFrame:
    """
    1) FREDから DGS2, T10Y2Y, VIXCLS, DGS3MO を取得
    2) 各シリーズを「論文の前処理」で個別に加工（y2_diff_ewm21, slope_ewm10, slope_diff_ewm21, vix_logdiff_ewm63, rf）
    3) その“加工済み系列”に対して共通日付インデックスを作成し、reindex→ffill で整列
       - base_on_rf=True のときは rf と rets を union したインデックスをベースに
       - base_on_rf=False のときは全加工系列＋rets の union をベースに
    4) 列を結合して返す（列: ["rets","rf","y2_diff_ewm21","slope_ewm10","slope_diff_ewm21","vix_logdiff_ewm63"]）
    """
    # --- FRED raw fetch ---
    y2_raw    = get_fred_data("DGS2",   start_date, end_date, api_key)
    slope_raw = get_fred_data("T10Y2Y", start_date, end_date, api_key)
    vix_raw   = get_fred_data("VIXCLS", start_date, end_date, api_key)
    rf_raw    = get_fred_data("DGS3MO", start_date, end_date, api_key)

    # --- 論文どおりの前処理（各シリーズを独立に加工する）---
    y2_diff_ewm21     = preprocess_y2_diff_ewm21(y2_raw)
    slope_feats       = preprocess_slope_features(slope_raw)          # 2列
    vix_logdiff_ewm63 = preprocess_vix_logdiff_ewm63(vix_raw)
    rf_daily_logret   = preprocess_rf_daily_logret(rf_raw)

    # --- ベースとなるインデックス（前処理済みのあとに作る）---
    if base_on_rf:
        base_index = rf_daily_logret.index.union(rets.index).sort_values()
    else:
        base_index = rets.index
        for s in [rf_daily_logret, y2_diff_ewm21, slope_feats.iloc[:,0], slope_feats.iloc[:,1], vix_logdiff_ewm63]:
            base_index = base_index.union(s.index)
        base_index = base_index.sort_values()

    # --- reindex→ffill で共通日付に揃える（前処理済みの系列に対して）---
    pieces = [
        rets.reindex(base_index).rename("rets"),
        rf_daily_logret.reindex(base_index),
        y2_diff_ewm21.reindex(base_index),
        slope_feats.reindex(base_index),
        vix_logdiff_ewm63.reindex(base_index),
    ]
    df = pd.concat(pieces, axis=1).ffill()

    if dropna:
        df = df.dropna()

    # 列順の明示
    cols = ["rets", "rf", "y2_diff_ewm21", "slope_ewm10", "slope_diff_ewm21", "vix_logdiff_ewm63"]
    df = df.loc[:, [c for c in cols if c in df.columns]]

    return df

# --------- 使い方（最小例） ---------
if __name__ == "__main__":
    # ダミーの資産リターンを用意（実運用では実データに置き換え）
    idx = pd.date_range("2012-01-01", "2025-10-31", freq="B")
    np.random.seed(42)
    rets = pd.Series(np.random.normal(0.0003, 0.01, len(idx)), index=idx, name="rets")

    API_KEY = "YOUR_FRED_API_KEY"
    start, end = "2011-01-01", "2025-12-31"

    df_all = build_regime_xgb_dataset_with_macro(
        rets=rets,
        start_date=start,
        end_date=end,
        api_key=API_KEY,
        base_on_rf=True,   # rf + rets をベースに共通日付を作成
        dropna=True
    )
    print(df_all.tail())
```

### ポイント

*   **順番の厳守**：`DGS2 / T10Y2Y / VIXCLS / DGS3MO` を**まず個別に前処理**（`y2_diff_ewm21`, `slope_ewm10`, `slope_diff_ewm21`, `vix_logdiff_ewm63`, `rf`）し、その**前処理済み系列**に対して **共通日付インデックス** を作っています。
*   **ベース選択**：`base_on_rf=True` で、前メッセージのご意向どおり **rf（＋rets）をベース**に整列します（False にすれば全系列 union ベース）。
*   **無リスクの単位変換**：`DGS3MO`（年率％）→**日次ログリターン**へ変換（`ln(1+年率%/100)/252`）。
*   **欠損処理**：最小実装では `ffill`→`dropna`。必要に応じて `bfill` やウィンドウ要件を調整してください。
*   **そのまま学習へ**：返却 `df_all` を、既存の JM 特徴量と `pd.concat([...], axis=1)` で結合し、XGBoost の `feat_df` に入れれば OK です。

## Response:
了解です。XGBoost 部分だけ **LightGBM に差し替え**た最小実装を用意しました。  
インターフェース／処理フローは**ほぼそのまま**で、学習器だけ `lightgbm.LGBMClassifier` に置き換えています。

> 依存: `pandas`, `numpy`, `lightgbm`  
> インストール例: `pip install lightgbm`

```python
# 最小依存: pandas, numpy, lightgbm
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from dataclasses import dataclass
from lightgbm import LGBMClassifier

@dataclass
class LGBMRegimeForecaster:
    """
    JMで得た当日レジーム s_t (0/1) を教師信号に、
    特徴量 x_t から翌日レジーム s_{t+1} を予測（LightGBM版、XGB版と同じ使い方）。

    - feat_df: (T, D) の特徴量 DataFrame（行=日付 index, 列=特徴）
    - regime_labels: (T,) の Series（JMの当日レジーム 0/1）
    - horizon: 既定=1（翌日レジームを予測）
    - train_end: 学習期間の最終日（"YYYY-MM-DD"）。None なら先頭80%を学習に使用
    - smooth_halflife: 予測確率のEWMA半減期（None なら平滑なし）
    - lgbm_params: LGBMClassifier のパラメータ（未指定なら最小構成）
    """
    feat_df: pd.DataFrame
    regime_labels: pd.Series
    horizon: int = 1
    train_end: Optional[str] = None
    smooth_halflife: Optional[int] = None
    lgbm_params: Optional[Dict[str, Any]] = None

    def fit_predict(self):
        # 1) 教師信号を horizon だけ先にシフト（s_{t+1} を t の特徴で当てる）
        y = self.regime_labels.shift(-self.horizon).reindex(self.feat_df.index)
        valid_idx = y.dropna().index
        X = self.feat_df.loc[valid_idx]
        y = y.loc[valid_idx].astype(int)

        # 2) 時系列スプリット（train_end 指定が無い場合は 8:2）
        if self.train_end is not None:
            train_mask = X.index <= pd.to_datetime(self.train_end)
        else:
            split = int(len(X) * 0.8)
            train_mask = pd.Series(False, index=X.index)
            train_mask.iloc[:split] = True

        X_train, y_train = X.loc[train_mask], y.loc[train_mask]
        X_test,  y_test  = X.loc[~train_mask], y.loc[~train_mask]

        # 3) LightGBM 最小構成（XGBoost版に近い挙動）
        params = dict(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=-1,            # LightGBMはデフォルトで深さ制限なし
            num_leaves=31,           # depth~5 相当
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary",
            random_state=42,
            n_jobs=-1,
            metric="binary_logloss",
        )
        if self.lgbm_params:
            params.update(self.lgbm_params)

        clf = LGBMClassifier(**params)
        clf.fit(X_train, y_train)

        # 4) 予測（確率）
        proba_test = pd.Series(
            clf.predict_proba(X_test)[:, 1],
            index=X_test.index,
            name="p_bear_next"
        )

        # 5) オプション: 確率の指数平滑
        if self.smooth_halflife is not None and self.smooth_halflife > 0:
            proba_smoothed = proba_test.ewm(halflife=self.smooth_halflife, adjust=False).mean()
        else:
            proba_smoothed = proba_test.copy()

        # 6) 閾値 0.5 でクラス化（>0.5 をベア=1）
        y_pred = (proba_smoothed >= 0.5).astype(int)
        y_pred.name = "y_pred_bear_next"

        # 7) 返却
        # LightGBM の feature_importances_ はデフォルトで "split"（分割回数）
        fi = pd.Series(clf.feature_importances_, index=X.columns, name="importance_split")

        return {
            "model": clf,
            "X_train": X_train, "y_train": y_train,
            "X_test": X_test,   "y_test": y_test,
            "proba_raw": proba_test,
            "proba_smoothed": proba_smoothed,
            "y_pred": y_pred,
            "feature_importance": fi.sort_values(ascending=False),
        }

# ===== 使い方（最小例） =====
if __name__ == "__main__":
    # ダミーデータ作成: 特徴量(3列) + JMラベル(0/1)
    idx = pd.date_range("2010-01-01", "2020-12-31", freq="B")
    rng = np.random.default_rng(0)
    feat = pd.DataFrame({
        "mean_hl5":   rng.normal(0, 1, len(idx)),
        "dd_log_hl5": rng.normal(0, 1, len(idx)),
        "sortino_hl5":rng.normal(0, 1, len(idx)),
    }, index=idx)

    # JMで得た当日レジーム（ダミー）
    base = rng.normal(0, 1, len(idx)).cumsum()
    regime = pd.Series((base > np.median(base)).astype(int), index=idx, name="regime_t")

    forecaster = LGBMRegimeForecaster(
        feat_df=feat,
        regime_labels=regime,
        horizon=1,                 # s_{t+1} を予測
        train_end="2017-12-31",    # 未指定なら 8:2 時系列スプリット
        smooth_halflife=8,         # 予測確率を平滑化（無しなら None）
        lgbm_params=None           # 追加/上書きパラメータを渡せます
    )
    res = forecaster.fit_predict()

    print("Quick check corr(y, p):",
          np.corrcoef(res["y_test"], res["proba_smoothed"])[0, 1])
    print("Feature importance (split counts):")
    print(res["feature_importance"].head())

    # 簡易 0/1 戦略評価のサンプル
    r_test = pd.Series(rng.normal(0.0003, 0.01, len(res["y_test"])), index=res["y_test"].index)
    rf_test = pd.Series(0.02/252, index=r_test.index)
    strat = pd.Series(np.where(res["y_pred"]==1, rf_test.values, r_test.values), index=r_test.index)
    sharpe = strat.mean() / strat.std(ddof=0) * np.sqrt(252)
    print("0/1 strategy Sharpe (test):", sharpe)
```

### ほぼ互換で使うためのメモ

*   `XGBClassifier` → `LGBMClassifier` に置換。その他は同じI/Fで使えます。
*   特徴量DFやレーベル、時系列スプリット、確率の EWM 平滑、0.5 閾値も同じ。
*   重要度は `feature_importances_`（LightGBMは既定で「split」尺度）。`importance_type="gain"` を指定したい場合は `lgbm_params={"importance_type": "gain"}` を渡してください。
*   大きなデータでは `device_type="gpu"`（要ビルド環境）や `num_leaves`・`min_data_in_leaf` の調整が効きます。

## Response:
了解。**(A) 各資産クラスごとの 0/1 戦略評価** と **(B) 各資産クラスの 0/1 戦略を用いた MV ポートフォリオ構築** を、依存最小（`numpy`/`pandas` のみ）でまとめて書きます。  
前提：各資産ごとに日次リターン `rets[asset]`、無リスク `rf`、予測レジーム `pred[asset]`（**ベア=1のとき無リスク、ブル=0のとき当該資産**）が与えられているとします。

```python
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple

# =========================
# 0) ユーティリティ
# =========================
def _align_to_index(base_index: pd.DatetimeIndex, s: pd.Series) -> pd.Series:
    return s.reindex(base_index).ffill()

def _perf_stats(r: pd.Series, ann_factor: int = 252) -> dict:
    """単一系列の評価指標を返す（年率換算: 平均・ボラ・Sharpe・MDD・CAGR）。"""
    r = r.dropna()
    if len(r) == 0:
        return {"ann_mean": np.nan, "ann_vol": np.nan, "sharpe": np.nan, "mdd": np.nan, "cagr": np.nan}
    ann_mean = r.mean() * ann_factor
    ann_vol  = r.std(ddof=0) * np.sqrt(ann_factor)
    sharpe   = np.nan if ann_vol == 0 else ann_mean / ann_vol
    # 最大ドローダウン
    cum = (1 + r).cumprod()
    peak = cum.cummax()
    dd = cum / peak - 1.0
    mdd = dd.min()
    # CAGR（期間年数を近似）
    n_years = max((r.index[-1] - r.index[0]).days / 365.25, 1e-9)
    cagr = cum.iloc[-1] ** (1 / n_years) - 1
    return {"ann_mean": ann_mean, "ann_vol": ann_vol, "sharpe": sharpe, "mdd": mdd, "cagr": cagr}

# =========================
# (A) 各資産クラス 0/1 戦略の評価
# =========================
def build_binary_strategy_returns(
    rets: Dict[str, pd.Series],
    rf: pd.Series,
    pred: Dict[str, pd.Series],
    base_index: Optional[pd.DatetimeIndex] = None
) -> pd.DataFrame:
    """
    各資産の 0/1 戦略リターンを作る。
    pred[asset] == 1 の日→ rf、== 0 の日→ rets[asset] を採用。
    """
    # ベース日付（指定なければ rf と全資産の union）
    if base_index is None:
        base_index = rf.index
        for a in rets:
            base_index = base_index.union(rets[a].index)
        for a in pred:
            base_index = base_index.union(pred[a].index)
        base_index = base_index.sort_values()

    rf_a = _align_to_index(base_index, rf)
    out = {}
    for a, r in rets.items():
        p = pred[a]
        r_a = _align_to_index(base_index, r)
        p_a = _align_to_index(base_index, p).fillna(1)  # 欠損日は保守的にベア(=1)扱い
        strat = np.where(p_a.values.astype(int) == 1, rf_a.values, r_a.values)
        out[a] = pd.Series(strat, index=base_index, name=a)
    return pd.DataFrame(out)

def evaluate_binary_strategies(
    strat_df: pd.DataFrame, ann_factor: int = 252
) -> pd.DataFrame:
    """
    各列（資産）の 0/1 戦略に対して評価指標を計算。
    """
    stats = {}
    for col in strat_df.columns:
        stats[col] = _perf_stats(strat_df[col], ann_factor=ann_factor)
    return pd.DataFrame(stats).T[["ann_mean", "ann_vol", "sharpe", "mdd", "cagr"]]

# =========================
# (B) 0/1 戦略から MV ポートフォリオ構築
# =========================
def _gmv_weights(cov: np.ndarray, long_only_clip: bool = True) -> np.ndarray:
    """
    GMV（全体分散最小）重み。簡易長期のみ対応: クリップして正規化（ヒューリスティック）。
    """
    n = cov.shape[0]
    ones = np.ones((n, 1))
    # 数値安定のため対角に微小リッジ
    cov_ = cov + 1e-8 * np.eye(n)
    inv = np.linalg.pinv(cov_)
    w = (inv @ ones) / (ones.T @ inv @ ones)  # 和=1
    w = w.ravel()
    if long_only_clip:
        w = np.clip(w, 0, None)
        s = w.sum()
        w = w / s if s > 0 else np.ones(n) / n
    return w

def _mv_weights(mu: np.ndarray, cov: np.ndarray, risk_aversion: float = 3.0,
                long_only_clip: bool = True) -> np.ndarray:
    """
    単純 MV: argmax w^T mu - (risk_aversion/2) w^T Σ w
    → 一様和=1制約をカンタンに近似: いったん無制約解 w* = (1/λ) Σ^{-1} μ を算出し、正規化。
      長期のみは負をクリップして再正規化（ヒューリスティック）。
    """
    cov_ = cov + 1e-8 * np.eye(len(mu))
    inv = np.linalg.pinv(cov_)
    w = (1.0 / max(risk_aversion, 1e-8)) * (inv @ mu)
    # 和=1 へ正規化
    s = w.sum()
    w = w / s if np.isfinite(s) and abs(s) > 1e-12 else w
    if long_only_clip:
        w = np.clip(w, 0, None)
        s = w.sum()
        w = w / s if s > 0 else np.ones_like(w) / len(w)
    return w

def build_static_mv_from_binary_strategies(
    strat_df: pd.DataFrame,
    mode: str = "mv",                 # "mv" or "gmv"
    risk_aversion: float = 3.0,       # mode="mv" のとき有効
    use_ewm: bool = True,             # 共分散推定：EWM or 単純標本
    halflife: int = 252,
    long_only_clip: bool = True
) -> Tuple[pd.Series, float, float]:
    """
    0/1 戦略のリターン列（列=資産）から、単一の静的 MV 重みを算出。
    戻り値: (weights, port_ann_mean, port_ann_vol)
    """
    X = strat_df.dropna(how="any")
    if len(X) == 0:
        raise ValueError("No overlapping data in strat_df.")

    if use_ewm:
        mu = X.ewm(halflife=halflife, adjust=False).mean().iloc[-1].values
        cov = X.ewm(halflife=halflife, adjust=False).cov().dropna().iloc[-len(X.columns):].values.reshape(len(X.columns), len(X.columns))
    else:
        mu = X.mean().values
        cov = X.cov().values

    if mode == "gmv":
        w = _gmv_weights(cov, long_only_clip=long_only_clip)
    else:
        w = _mv_weights(mu, cov, risk_aversion=risk_aversion, long_only_clip=long_only_clip)

    # ポート期待リターン・ボラ（年率）
    ann = 252
    port_mean = float((X @ w).mean() * ann)
    port_vol  = float((X @ w).std(ddof=0) * np.sqrt(ann))
    return pd.Series(w, index=X.columns, name="weight"), port_mean, port_vol

def build_rolling_mv_portfolio(
    strat_df: pd.DataFrame,
    window: int = 252,                 # 推定窓（日）
    rebalance_freq: str = "M",         # "M"（月次）/ "W"（週次）/ "D"（日次）
    mode: str = "mv",                  # "mv" or "gmv"
    risk_aversion: float = 3.0,
    long_only_clip: bool = True
) -> Tuple[pd.Series, pd.DataFrame]:
    """
    過去 window で μ, Σ を推定し、指定頻度でリバランスする MV バックテスト。
    戻り値: (portfolio_returns, weights_history)
    """
    X = strat_df.dropna(how="any").copy()
    if len(X) < window + 5:
        raise ValueError("Not enough data for rolling MV.")

    # リバランス日
    rebal_days = X.resample(rebalance_freq).last().index
    rebal_days = [d for d in rebal_days if d in X.index and X.index.get_loc(d) >= window]
    weights_hist = []
    port_ret = pd.Series(0.0, index=X.index)

    for d in rebal_days:
        loc = X.index.get_loc(d)
        hist = X.iloc[loc - window:loc]  # 直近 window
        mu = hist.mean().values
        cov = hist.cov().values
        if mode == "gmv":
            w = _gmv_weights(cov, long_only_clip=long_only_clip)
        else:
            w = _mv_weights(mu, cov, risk_aversion=risk_aversion, long_only_clip=long_only_clip)
        w_s = pd.Series(w, index=X.columns, name=d)
        weights_hist.append(w_s)

        # 次のリバランス直前までこの w を適用
        next_loc = X.index.get_loc(rebal_days[rebal_days.index(d)+1]) if d != rebal_days[-1] else len(X)
        sl = slice(loc, next_loc)  # d 当日含む
        port_ret.iloc[sl] = (X.iloc[sl] @ w)

    W = pd.DataFrame(weights_hist)
    return port_ret, W

# =========================
# 使い方（最小例）
# =========================
if __name__ == "__main__":
    np.random.seed(0)
    idx = pd.date_range("2015-01-01", "2025-10-31", freq="B")
    # ダミー：3資産のリターン
    rets = {
        "Equity": pd.Series(np.random.normal(0.0005, 0.01, len(idx)), index=idx),
        "Bond":   pd.Series(np.random.normal(0.0002, 0.004, len(idx)), index=idx),
        "Gold":   pd.Series(np.random.normal(0.0001, 0.013, len(idx)), index=idx),
    }
    rf = pd.Series(0.02/252, index=idx)  # 年率2%相当
    # ダミー：レジーム予測（ベア=1なら rf 採用）
    pred = {
        "Equity": pd.Series((np.random.rand(len(idx)) > 0.6).astype(int), index=idx),
        "Bond":   pd.Series((np.random.rand(len(idx)) > 0.4).astype(int), index=idx),
        "Gold":   pd.Series((np.random.rand(len(idx)) > 0.5).astype(int), index=idx),
    }

    # (A) 各資産の 0/1 戦略リターン & 評価
    strat_df = build_binary_strategy_returns(rets, rf, pred)             # 列=資産
    stats_df = evaluate_binary_strategies(strat_df)
    print("Per-asset 0/1 stats:\n", stats_df, "\n")

    # (B-1) 静的 MV（全期間で一度推定）
    w_static, pm, pv = build_static_mv_from_binary_strategies(
        strat_df, mode="mv", risk_aversion=3.0, use_ewm=False, long_only_clip=True
    )
    print("Static MV weights:\n", w_static, "\nAnnualized mean/vol:", pm, pv, "\n")

    # (B-2) ローリング MV（月次リバランス）
    port_ret, W = build_rolling_mv_portfolio(
        strat_df, window=252, rebalance_freq="M", mode="mv", risk_aversion=3.0, long_only_clip=True
    )
    print("Rolling MV portfolio Sharpe:",
          (port_ret.mean()*252) / (port_ret.std(ddof=0)*np.sqrt(252)))
    print("Weights (last 5 rebalances):\n", W.tail())
```

### 使い方まとめ

*   **(A)** `build_binary_strategy_returns()` で資産ごとの 0/1 戦略リターンを作り、`evaluate_binary_strategies()` で Sharpe/MDD/CAGR を一覧化。
*   **(B-1)** `build_static_mv_from_binary_strategies()` は全期間で μ, Σ を推定して **静的** 重みを出します（`mode="gmv"` も可）。
*   **(B-2)** `build_rolling_mv_portfolio()` は過去 `window` 日で推定し、指定頻度で**リバランス**してバックテストします。

> 注：MV 最適化は依存を増やさないため、**長期のみ制約**は「負ウェイトを 0 でクリップ → 再正規化」のヒューリスティックで実装しています。厳密な制約付き二次計画にしたい場合は `cvxpy` 等に置き換えてください。

## Response:
思考時間: 22s

以下は、添付論文の**資産ごとのレジームを織り込んだ平均分散（MV）ポートフォリオ**の構成方法の要点です。

1) 期待リターン  $\mu$  の作り方（資産別レジーム反映）
---------------------------------

*   各資産  $i$  について、JM（Jump Model）で過去データを **bull/bear** にラベル付けし、学習窓内で**レジーム別の平均リターン**（bull 平均、bear 平均）を計算しておく。最適ジャンプ・ペナルティ  $\hat\lambda$  を選んだ JM に基づく値を使う。
    2406.09578v2
*   翌日のレジームを JM→XGBoost（論文の実装）で**予測**し、**予測レジームに対応する平均リターン**をその資産の**翌日期待リターン**  $\mu_i$  として採用する。例えば「明日 bull 予測」なら bull 期の平均を使う。
    2406.09578v2
*   **bear 予測時の極端値抑制**：bear での期待リターンは **−10 bps に上限（キャップ）** する（極端な負値の影響を抑える目的）。
    2406.09578v2

> 直感：レジーム識別→レジーム予測→「予測レジームに対応する履歴平均」を使う、という順で  $\mu$  を決める。

2) 共分散  $\Sigma$  の推定
---------------------

*   **指数加重移動（EWM）共分散**を使用。**半減期 252 日**。レジーム情報は当面 $\mu$ 側にのみ反映（ $\Sigma$  は通常推定）。
    2406.09578v2
*   MV セクションでも同様に **EWM 共分散（HL=252）** を採用。
    2406.09578v2

3) 最適化（長期のみ、取引コスト項あり）
---------------------

*   ベースの目的関数は Markowitz の
    $$
    \max_{w}\; w^\top \mu \;-\; \gamma_{\mathrm{risk}}\, w^\top \Sigma w \;-\; \gamma_{\mathrm{trade}}\cdot \text{(取引コスト項)}
    $$
    を長期のみ制約（上限など）下で解くという実務設定。論文内のパラメータは ** $\gamma_{\mathrm{risk}}=10.0$ **（レジーム対応 MV）、** $\gamma_{\mathrm{trade}}=1.0$ ** を採用（ベースライン MV は  $\gamma_{\mathrm{risk}}=5.0,\ \gamma_{\mathrm{trade}}=0$ ）。
    2406.09578v2
*   **安全弁**：**bull 予測の資産が 3 本以下**のときは、**100% 無リスク**に退避（集中リスク回避）。
    2406.09578v2

4) 参考：MinVar との一貫点
------------------

*   MinVar でも「**bull 予測資産のみに投資**」という使い方（bull と判定された集合内での最小分散）や、少数資産しか bull でないときの **無リスク 100%** 退避ルールを採用している。MV も同系の実装方針で、差は  $\mu$  の使い方（レジーム別平均）と  $\gamma$  設定。
    2406.09578v2

* * *

### まとめ（実装観点）

*   ** $\mu_i$ **：資産  $i$  の**予測レジーム r** に対応する「学習窓の JM（ $\hat\lambda$ ）で bull/bear ごとに計算した履歴平均」。bear なら  $\max(\mu_i,\ -10\text{bps})$  でクリップ。
    2406.09578v2
*   ** $\Sigma$ **：EWM 共分散（HL=252）。
    2406.09578v2
*   **最適化**：長期のみ、 $\gamma_{\mathrm{risk}}=10.0$ 、 $\gamma_{\mathrm{trade}}=1.0$ 、**bull 資産 ≤3 本なら無リスク 100%**。
    2406.09578v2

必要なら、上記ロジックをそのまま踏襲した **MV（JM-XGB）重み算出の関数**（ $\mu$  生成→EWM  $\Sigma$ →二次計画/ヒューリスティック）をコードで用意します。

## Response:
了解です。**資産ごとのレジーム予測を反映した平均分散（MV）ポートフォリオ**を、そのまま使える最小実装で用意しました。  
依存は `numpy` と `pandas` のみ（制約付きQPは使わず、長期のみはクリップ＋再正規化のヒューリスティック）。

*   レジーム別期待リターンは **EWM 条件付き平均**（JMラベル 0=ブル / 1=ベア）
*   ベア側は **−10bps/日で下限クリップ**（論文の極端値抑制に対応；変更可）
*   共分散は **EWM(halflife=252)**
*   **安全弁**：ブル予測資産が **3 本以下**なら、その期間は **無リスク 100%**
*   リバランスは既定 **月次**（`rebalance_freq` で変更可）

```python
import numpy as np
import pandas as pd
from typing import Tuple, Optional

# ========= ユーティリティ =========
def ewm_mean(x: pd.Series, halflife: int) -> pd.Series:
    return x.ewm(halflife=halflife, adjust=False, min_periods=1).mean()

def ewm_conditional_mean(r: pd.Series, label: pd.Series, cond: int, halflife: int) -> pd.Series:
    """
    条件付きEWM平均: E[r | label==cond] を時点ごとに推定
      = EWM( r * I{label==cond} ) / EWM( I{label==cond} )
    """
    I = (label == cond).astype(float)
    num = ewm_mean(r * I, halflife=halflife)
    den = ewm_mean(I,     halflife=halflife).replace(0, np.nan)
    return (num / den).fillna(0.0)

def ewm_cov_matrix(df: pd.DataFrame, halflife: int) -> np.ndarray:
    """
    EWM共分散行列（pandasのEWM.covの最後のスライスを抽出）
    """
    # pandas の EWM.cov は長くなるので、直近の共分散行列を取り出す
    cov_df = df.ewm(halflife=halflife, adjust=False).cov()
    # 直近日のブロックを取得
    last_idx = cov_df.index.get_level_values(0).max()
    C = cov_df.loc[last_idx]
    # 欠損があればゼロ埋め＋対角補正
    C = C.reindex(index=df.columns, columns=df.columns).fillna(0.0)
    # 数値安定化
    C.values[np.diag_indices_from(C.values)] += 1e-8
    return C.values

def mv_weights_long_only(mu: np.ndarray, Sigma: np.ndarray, gamma: float = 10.0,
                         w_ub: Optional[float] = None) -> np.ndarray:
    """
    ヒューリスティックMV解:
      w* = (1/gamma) * Σ^{-1} μ を求め、負を0にクリップ→上限制約あれば適用→和を<=1に正規化
    """
    inv = np.linalg.pinv(Sigma)
    w = (inv @ mu) / max(gamma, 1e-8)
    # 長期のみ
    w = np.clip(w, 0, None)
    # 上限あれば適用
    if w_ub is not None:
        w = np.minimum(w, w_ub)
    s = w.sum()
    if not np.isfinite(s) or s <= 0:
        # すべて0なら等分配（または全キャッシュにしたいならゼロのままでも可）
        w = np.ones_like(w) / len(w)
        s = 1.0
    # 和=1の範囲に正規化（キャッシュ許容なら和<=1にしたい場合は scale<=1も可）
    w = w / s
    return w

# ========= 主要関数：レジーム対応MV（ローリング運用） =========
def regime_mv_portfolio(
    rets_df: pd.DataFrame,          # 各資産の日次リターン（列=資産名）
    rf: pd.Series,                  # 無リスク日次リターン
    jm_labels_df: pd.DataFrame,     # JMラベル（0=ブル,1=ベア）列は rets_df と同じ資産名・同じindex
    pred_regime_df: pd.DataFrame,   # 翌日レジーム予測（0=ブル,1=ベア）列は rets_df と同じ資産名・同じindex
    halflife_mu: int = 126,         # 期待リターン推定のEWM半減期（約半年）
    halflife_cov: int = 252,        # 共分散推定のEWM半減期（約1年）
    bear_cap_bps_per_day: float = -10.0,  # ベア平均の下限（bps/日）。例:-10→-0.001/日
    min_bull_assets: int = 3,       # ブル資産本数がこの閾値以下なら無リスク100%
    gamma: float = 10.0,            # リスク回避度
    w_ub: Optional[float] = None,   # 各資産の上限（None=制約なし、例:0.2）
    rebalance_freq: str = "M"       # "M" 月次 / "W" 週次 / "D" 日次
) -> Tuple[pd.Series, pd.DataFrame]:
    """
    レジーム別EWM平均→予測レジームに応じた μ、EWMΣ、長期のみMV で重みを算出し、
    指定頻度でリバランスして運用。戻り値: (ポート日次リターン, 重み履歴)
    """
    # インデックス整列
    idx = rets_df.index.union(rf.index).union(jm_labels_df.index).union(pred_regime_df.index)
    idx = idx.sort_values()
    R  = rets_df.reindex(idx).ffill()
    RF = rf.reindex(idx).ffill()
    L  = jm_labels_df.reindex(idx).ffill()       # JMラベル
    P  = pred_regime_df.reindex(idx).ffill()     # 予測

    assets = list(R.columns)
    n = len(assets)

    # リバランス日
    rebal_days = R.resample(rebalance_freq).last().index
    # 実データに存在する日に限定
    rebal_days = [d for d in rebal_days if d in R.index]

    weights_hist = []
    port_ret = pd.Series(index=R.index, dtype=float)

    bps2daily = bear_cap_bps_per_day / 10000.0  # bps/日 → 実数/日

    for t in rebal_days:
        loc = R.index.get_loc(t)

        # 直近までのデータで EWM 条件付き平均（各資産ごと）
        bull_means = []
        bear_means = []
        for a in assets:
            r_a = R[a].iloc[:loc+1]
            l_a = L[a].iloc[:loc+1]
            mu_bull = ewm_conditional_mean(r_a, l_a, cond=0, halflife=halflife_mu).iloc[-1]
            mu_bear = ewm_conditional_mean(r_a, l_a, cond=1, halflife=halflife_mu).iloc[-1]
            # ベアは下限クリップ
            mu_bear = max(mu_bear, bps2daily)
            bull_means.append(mu_bull)
            bear_means.append(mu_bear)
        bull_means = np.array(bull_means)
        bear_means = np.array(bear_means)

        # 予測レジームに応じて μ を選択（当日 t の予測を使用し、t→次リバランスまで固定）
        pred_today = P.iloc[loc].values.astype(int)  # shape=(n,)
        mu = np.where(pred_today == 0, bull_means, bear_means)

        # 安全弁：ブル資産が少なければ無リスク100%
        if (pred_today == 0).sum() <= min_bull_assets:
            w = np.zeros(n)
            # 次のリバランス直前まで rf を適用
            next_loc = (R.index.get_loc(rebal_days[rebal_days.index(t)+1])
                        if t != rebal_days[-1] else len(R))
            port_slice = slice(loc, next_loc)
            port_ret.iloc[port_slice] = RF.iloc[port_slice]
            weights_hist.append(pd.Series(w, index=assets, name=t))
            continue

        # EWM共分散（直近まで）
        Sigma = ewm_cov_matrix(R.iloc[:loc+1], halflife=halflife_cov)

        # MV（長期のみ, 和=1に正規化）
        w = mv_weights_long_only(mu, Sigma, gamma=gamma, w_ub=w_ub)

        # 次のリバランス直前までこの重みを適用（ポート= w^T R + 残余キャッシュ*rf も選べるが、ここは和=1）
        next_loc = (R.index.get_loc(rebal_days[rebal_days.index(t)+1])
                    if t != rebal_days[-1] else len(R))
        sl = slice(loc, next_loc)
        port_ret.iloc[sl] = (R.iloc[sl] @ w).values  # 全額リスク資産に投資
        weights_hist.append(pd.Series(w, index=assets, name=t))

    W = pd.DataFrame(weights_hist)

    return port_ret.dropna(), W

# ========= サンプル（ダミーデータ） =========
if __name__ == "__main__":
    np.random.seed(7)
    idx = pd.date_range("2015-01-01", "2025-10-31", freq="B")

    # 3資産のダミー日次リターン
    rets_df = pd.DataFrame({
        "Equity": np.random.normal(0.0005, 0.01,  len(idx)),
        "Bond":   np.random.normal(0.0002, 0.004, len(idx)),
        "Gold":   np.random.normal(0.0001, 0.013, len(idx)),
    }, index=idx)

    # 無リスク（年率2%相当の一定）
    rf = pd.Series(0.02/252, index=idx)

    # JMラベル（0ブル/1ベア）。ここではダミー：閾値で分割
    jm_labels_df = pd.DataFrame(index=idx, columns=rets_df.columns, dtype=int)
    jm_labels_df["Equity"] = (np.sin(np.linspace(0, 60, len(idx))) > 0).astype(int)  # 0/1を交互に
    jm_labels_df["Bond"]   = (np.cos(np.linspace(0, 40, len(idx))) > 0).astype(int)
    jm_labels_df["Gold"]   = (np.sin(np.linspace(0, 30, len(idx))) > 0).astype(int)

    # 翌日レジーム予測（0ブル/1ベア）。ここもダミーで生成
    pred_regime_df = (pd.DataFrame({
        "Equity": (np.random.rand(len(idx)) > 0.4).astype(int),
        "Bond":   (np.random.rand(len(idx)) > 0.5).astype(int),
        "Gold":   (np.random.rand(len(idx)) > 0.5).astype(int),
    }, index=idx)).astype(int)

    # 実行
    port_ret, W = regime_mv_portfolio(
        rets_df, rf, jm_labels_df, pred_regime_df,
        halflife_mu=126, halflife_cov=252,
        bear_cap_bps_per_day=-10.0,  # -10bps/日
        min_bull_assets=3,
        gamma=10.0,
        w_ub=0.5,                    # 各資産50%上限（必要なければ None）
        rebalance_freq="M"
    )

    # 簡易評価
    ann = 252
    ann_mean = port_ret.mean() * ann
    ann_vol  = port_ret.std(ddof=0) * np.sqrt(ann)
    sharpe   = ann_mean / ann_vol
    print("Portfolio (MV w/ regimes) — ann.mean, ann.vol, Sharpe:",
          round(ann_mean,4), round(ann_vol,4), round(sharpe,3))
    print("Weights (last 6 rebalances):\n", W.tail(6))
```

### 使い方・差し替えポイント

*   `jm_labels_df` は **JMの当日ラベル**（0=ブル/1=ベア）を入れてください。
*   `pred_regime_df` は **翌日予測レジーム**（0/1）。当日リバランスで次期まで固定します。
*   ベア下限 `bear_cap_bps_per_day` は既定 **−10 bps/日**（= −0.001）。月次下限や年率下限にしたい場合はここを調整してください。
*   安全弁：`min_bull_assets`（既定3）。これ以下なら **無リスク 100%** に退避。
*   和=1・長期のみ・上限 `w_ub` を満たすよう、**擬似MV解**（逆行列×μ→クリップ→正規化）で実装しています。厳密QPにしたい場合は `cvxpy` などに切替えてください。

必要なら、この重みの上に **取引コスト（L1）** を近似的に入れる版や、**bull のみで投資する MinVar** 版も追加でお出しできます。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)