# 枝分かれ · 専門家向け解説

**User:** Anonymous (kbmedphys@gmail.com)  
**Created:** 11/12/2025 20:47:11  
**Updated:** 11/12/2025 20:55:34  
**Exported:** 11/12/2025 20:58:55  
**Link:** [https://chatgpt.com/c/691473b5-8ef8-8321-beba-5d2e4938c0f8](https://chatgpt.com/c/691473b5-8ef8-8321-beba-5d2e4938c0f8)  

## Response:
以下は、添付論文 **Bai & Perron (2003), "Computation and Analysis of Multiple Structural Change Models"**（_Journal of Applied Econometrics_, Vol.18, pp.1–22）の専門家向け詳細解説です。  
この論文は、1998年の理論論文（Bai and Perron, _Econometrica_）の実証実装編であり、**複数構造変化点（multiple structural breaks）を持つ線形回帰モデルの推定・検定方法の計算的枠組み**を確立した代表的研究です。

* * *

🔹 1. 背景と目的
-----------

構造変化（structural change）問題とは、時系列データにおいて**回帰パラメータが特定の時点で不連続に変化する**場合に、その変化点（break date）を特定することを目的とします。  
従来は単一の変化点を想定した手法（Chow testなど）が主流でしたが、Bai & Perron (1998, 2003) は**複数変化点を同時に推定**できる一般的手法を理論・実装の両面から提示しました。

本稿では特に次の実務的課題を扱います：

1.  **ブレーク日（break date）の推定アルゴリズムの開発**  
    → 動的計画法（dynamic programming）を用いて**O(T²)** の計算量でグローバル最小値を求める。
2.  **信頼区間の構築**  
    → 各種誤差構造（自己相関・分散不均一）に対応。
3.  **構造変化の検定とブレーク数の推定**  
    → Sup-Wald, Double Maximum, Sequential tests を包括的に整理。
4.  **実証応用と実装**  
    → GAUSSプログラムで利用可能な計算手順を示す。

* * *

🔹 2. モデルの定式化
-------------

### 一般形

$$
y_t = x_t' \beta + z_t' \nu_j + u_t, \quad t = T_{j-1}+1, \dots, T_j, \quad j = 1,\dots,m+1
$$
*    $m$ ：構造変化点の数（未知）
*    $x_t$ ：変化しない説明変数
*    $z_t$ ：係数がセグメントごとに変化する変数
*    $\beta$ ：固定パラメータ
*    $\nu_j$ ：セグメント j に特有のパラメータ

これは\*\*部分構造変化モデル（partial structural change model）**であり、  
 $p=0$  の場合には全ての係数が変化する**純構造変化モデル（pure structural change model）\*\*になります。

* * *

🔹 3. 推定アルゴリズム：動的計画法による最適分割
---------------------------

複数のブレーク点を探索するには、全探索では O(T^m) の計算量となり現実的でありません。  
Bai & Perron は、\*\*動的計画法（Dynamic Programming, DP）\*\*を応用し、O(T²) の効率的アルゴリズムを提示しました。

### 手順概要

1.  各可能な区間 \[i, j\] に対し、OLS による **SSR(i,j)**（残差平方和）を計算。  
    → これにより **T(T+1)/2** の「三角行列」を構築（Figure 1参照）。
2.  DPを用い、次の再帰式で最適分割を求める：
    $$
    SSR(\{T_m, T\}) = \min_{h \le j \le T-h} [ SSR(\{T_{m-1}, j\}) + SSR(j+1, T) ]
    $$
    → 各サブサンプルで最小SSRを保存し、順次更新。
3.   $m$  個のブレークを持つ最小SSRパーティションを決定。  
    → **グローバル最小値**が保証される。

### 計算特性

*   計算負荷の中心はSSR行列の構築（O(T²)）
*    $m$  の増加に対して計算時間の増加はごくわずか
*   通常のサンプルサイズ（例：T=200–1000）では実用的に高速

* * *

🔹 4. 部分構造変化モデルへの拡張
-------------------

 $\beta$  が共通パラメータの場合、分割が未知では  $\beta$  の推定も難しくなります。  
そこで **Sargan (1964)** に基づく反復最適化法を導入します：

1.  初期値  $\beta^{(0)}$  を固定し、DPでブレーク点を推定。
2.  得られた区間に基づき、OLSで  $\beta, \nu$  を同時更新。
3.  収束まで反復（通常は1〜2回で収束）。

初期値には「全係数変化モデル」を用いて推定した値を採用することで局所解を回避。

* * *

🔹 5. 信頼区間の構築
-------------

### （1）係数推定値

ブレーク推定誤差は漸近的に無視可能（T倍速収束）であるため、  
通常の OLS と同様に √T-漸近正規分布を持つ：

$$
\sqrt{T}(\hat{\theta} - \theta_0) \xrightarrow{d} N(0, V^{-1} \Omega V^{-1})
$$

ここで、Ωは系列相関・異分散を許す一般化分散。  
HAC推定（Andrews, 1991）を利用。

* * *

### （2）ブレーク日（Break Date）の分布

推定されたブレーク点  $\hat{T}_i$  は、真値  $T_i^0$  から定数オーダーで収束する：

$$
(\hat{T}_i - T_i^0) \Rightarrow \arg\max_s V_i(s)
$$
*    $V_i(s)$ ：ブラウン運動（Weiner過程）を用いた確率過程
*   分布は変化幅（Δ\_i）や分散構造に依存
*   対称的な二側Brownian motion型の分布として近似可能

これを用いて**整数区間での信頼区間**（例えば±k期間）を構築します。

* * *

🔹 6. 構造変化検定
------------

### (1) SupF 検定（no break vs k breaks）

$$
F_T(\tau_1, ..., \tau_k) = \frac{(SSR_0 - SSR_k)/kq}{SSR_k/(T - (k+1)q)}
$$
*   帰無仮説：構造変化なし
*   対立仮説：k個の変化あり
*   最小SSRを達成するブレーク点におけるF値を取る（SupF）

* * *

### (2) Double Maximum 検定

ブレーク数 m が未知の場合：

*   **UDmax**：均一重み
*   **WDmax**：p値等重み
    $$
    UD = \max_{1\le m \le M} F_T(m)
    $$

→  $M=5$  程度で十分。ε（トリミング率）=0.05〜0.25 の臨界値を提供。

* * *

### (3) Sequential 検定 (supF(ℓ+1|ℓ))

順次的に「ℓ個 vs ℓ+1個のブレーク」を比較。  
実際の推定ではこの手法（逐次追加法）が最も安定。

* * *

🔹 7. ブレーク数の決定
--------------

情報量基準に基づく選択も可能：

*   **BIC**（Yao, 1988）：過大推定しがち
*   **LWZ**（Liu–Wu–Zidek, 1997）：過少推定傾向
*   **Sequential supF test**：実務上最も堅牢

* * *

🔹 8. 実践的推奨事項（Bai & Perron 2000 シミュレーションに基づく）
---------------------------------------------

| 条件 | 推奨トリミング ε | 推奨方法 |
| --- | --- | --- |
| 同分散・無相関 | 0.05 | SupF / Sequential |
| 異分散または系列相関あり | ≥0.15–0.20 | Sequential test 推奨 |
| 小標本 (T<100) | ≥0.15 | BICとSequential併用 |
| 大標本 (T>200) | 0.10 以下可 | DPアルゴリズム安定 |

* * *

🔹 9. 意義と応用
-----------

本論文は、構造変化モデルの理論と実務を統合した決定的研究であり：

*   **マクロ経済のレジーム転換分析**（例：景気転換点）
*   **金融時系列のパラメータ変動検出**（例：ボラティリティ体制）
*   **政策効果の時点特定**（例：制度改革前後の回帰差）

など、多くの応用研究の標準手法となっています。

* * *

🔹 10. まとめ：技術的要点
----------------

| 項目 | 内容 |
| --- | --- |
| モデル | 部分／純構造変化モデル |
| 推定法 | 動的計画法によるグローバル最適化 |
| 計算量 | O(T²)（従来の O(T^m) に比べ劇的に改善） |
| 信頼区間 | Brownian-motionベースの近似分布 |
| 検定 | SupF, Double Max, Sequential |
| 実装 | GAUSSコード付属、現在はR/Pythonにも移植（`strucchange`, `ruptures`など） |

* * *

ご希望であれば、  
この論文を基にした **Python実装（DPアルゴリズム＋SupF検定）** の完全スクリプトも作成可能です。  
ご要望ありますか？

## Response:
思考時間: 4m 29s

以下で、

1.  **Bai & Perron 型のブレークポイントモデル（純構造変化）**
2.  **論文 3.6 節の閾値モデル（threshold model）**

を、それぞれ

*   論文の内容を簡潔に整理
*   それに対応する **Python 実装コード**

という順で示します。

* * *

1\. 純構造変化モデル（multiple structural breaks）の実装
-------------------------------------------

### 1.1 モデルとアルゴリズムの要点

論文の基本形（純構造変化）は

$$
y_t = z_t' \nu_j + u_t, \quad t = T_{j-1}+1,\dots,T_j,\quad j=1,\dots,m+1
$$
*    $m$ ：ブレーク数（未知）
*   各セグメント  $j$  ごとに係数  $\nu_j$  が異なる
*   ブレーク点  $T_1,\dots,T_m$  を **OLS の残差平方和（SSR）を最小化する分割**として求める
    J of Applied Econometrics - 200…
    。

**重要ポイント（論文）

J of Applied Econometrics - 200…

**

*   全ての可能な区間  $[i,j]$  に対して OLS の SSR を計算し、**三角行列**として保持。
*   任意の m 分割の SSR は、これら区間 SSR の線形和で書ける。
*   そこで、動的計画法（Dynamic Programming）で
    $$
    SSR_{k}(1..t) = \min_{s} \{ SSR_{k-1}(1..s) + SSR(s+1..t) \}
    $$
    を再帰的に計算し、**O(T²)** でグローバル最小の分割を得る
    J of Applied Econometrics - 200…
    。

以下の実装は：

*   **純構造変化モデルのみ**（すべての係数がセグメントごとに変化）
*   共分散構造の推定や HAC は入れていない（単純な OLS ベースの推定）
*   最小セグメント長  $h$  を強制（trimming 相当）

* * *

### 1.2 Python 実装コード

```python
import numpy as np

def ols_segment_SSR_precompute(y, Z):
    """
    y: shape (T,)
    Z: shape (T, q)
    各 t までの累積クロスプロダクトを事前計算し、
    任意区間 [i, j] の SSR を高速に計算できるようにする。
    """
    y = np.asarray(y)
    Z = np.asarray(Z)
    T, q = Z.shape

    Sy = np.zeros(T + 1)            # 累積 y'y
    SZZ = np.zeros((T + 1, q, q))   # 累積 Z'Z
    SZy = np.zeros((T + 1, q))      # 累積 Z'y

    for t in range(T):
        Sy[t+1] = Sy[t] + y[t]**2
        SZZ[t+1] = SZZ[t] + np.outer(Z[t], Z[t])
        SZy[t+1] = SZy[t] + Z[t] * y[t]

    return Sy, SZZ, SZy

def segment_SSR(i, j, Sy, SZZ, SZy, ridge=1e-12):
    """
    区間 [i, j]（両端含む）での回帰 y ~ Z の SSR を計算。
    SSR = y'y - (Z'y)' (Z'Z)^{-1} (Z'y)
    """
    Syy = Sy[j+1] - Sy[i]
    SZZ_seg = SZZ[j+1] - SZZ[i]
    SZy_seg = SZy[j+1] - SZy[i]

    # 数値安定化用のごく弱いリッジ
    SZZ_reg = SZZ_seg + ridge * np.eye(SZZ_seg.shape[0])

    try:
        beta = np.linalg.solve(SZZ_reg, SZy_seg)
    except np.linalg.LinAlgError:
        beta = np.linalg.lstsq(SZZ_reg, SZy_seg, rcond=None)[0]

    SSR = Syy - SZy_seg @ beta
    return SSR, beta

def fit_pure_structural_breaks(y, Z, m, h):
    """
    純構造変化モデル:
        y_t = z_t' * nu_j + u_t,   t in regime j
    について、Bai & Perron (2003) の動的計画法:contentReference[oaicite:3]{index=3}に基づき
    m 個のブレークを推定する。

    Parameters
    ----------
    y : array-like, shape (T,)
        応答変数
    Z : array-like, shape (T, q)
        説明変数（すべての係数がセグメントごとに変化）
    m : int
        ブレーク数
    h : int
        最小セグメント長（各セグメントに少なくとも h 観測が必要）

    Returns
    -------
    breakpoints : list of int
        ブレークインデックス（0-based, その時点が「セグメントの終わり」）
        例: [24, 60] は
            [0..24], [25..60], [61..T-1] の 3 セグメント。
    coefs : list of ndarray
        各セグメントの OLS 係数ベクトル
    SSR_total : float
        全セグメントの SSR（最小値）
    """
    y = np.asarray(y)
    Z = np.asarray(Z)
    T = len(y)
    K = m + 1  # セグメント数

    if T < K * h:
        raise ValueError("サンプルが短すぎます: T < (m+1)*h")

    # 1. 累積クロスプロダクト
    Sy, SZZ, SZy = ols_segment_SSR_precompute(y, Z)

    # 2. 各区間 [i, j] の SSR を前計算
    SSR_mat = np.full((T, T), np.inf)
    for i in range(T):
        for j in range(i + h - 1, T):
            SSR_mat[i, j], _ = segment_SSR(i, j, Sy, SZZ, SZy)

    # 3. 動的計画法テーブル
    dp = np.full((K, T), np.inf)    # dp[k, t]: 先頭〜t を k+1 セグメントに分割した最小 SSR
    prev = np.full((K, T), -1, int)

    # ベースケース: k = 0 （1セグメント）
    for t in range(h - 1, T):
        # 残りのセグメント (K-1) を入れるために十分な長さが残っているか
        if T - (t + 1) < (K - 1) * h:
            continue
        dp[0, t] = SSR_mat[0, t]
        prev[0, t] = -1

    # 再帰ステップ: k = 1..K-1
    for k in range(1, K):
        for t in range((k + 1) * h - 1, T):
            # 残りのセグメントに必要な長さが残っているか
            if T - (t + 1) < (K - 1 - k) * h:
                continue

            best_val = np.inf
            best_s = -1

            # 一つ前のセグメントの終端 s
            s_min = k * h - 1
            s_max = t - h
            for s in range(s_min, s_max + 1):
                if not np.isfinite(dp[k-1, s]):
                    continue
                val = dp[k-1, s] + SSR_mat[s+1, t]
                if val < best_val:
                    best_val = val
                    best_s = s

            dp[k, t] = best_val
            prev[k, t] = best_s

    # 4. 最後のセグメントは必ず T-1 で終了させる
    last_k = K - 1
    best_end = T - 1
    best_val = dp[last_k, best_end]

    if not np.isfinite(best_val):
        raise ValueError("フルサンプルをカバーする分割が見つかりません。m や h を見直してください。")

    # 5. バックトラックでブレークポイントを復元
    breakpoints = []
    t = best_end
    for k in range(last_k, 0, -1):
        s = prev[k, t]
        breakpoints.append(s)
        t = s
    breakpoints = sorted(breakpoints)

    # 6. 各セグメントの OLS 係数を再推定
    coefs = []
    start = 0
    for bp in breakpoints + [T - 1]:
        _, beta = segment_SSR(start, bp, Sy, SZZ, SZy)
        coefs.append(beta)
        start = bp + 1

    return breakpoints, coefs, best_val
```

#### 簡単な使い方例（シミュレーション）

```python
# 1 つのブレークを持つ単純な例
T = 200
np.random.seed(0)
Z = np.random.randn(T, 1)

true_break = 120
beta1 = 1.0
beta2 = 3.0
sigma = 0.1

y = np.empty(T)
y[:true_break]  = beta1 * Z[:true_break, 0]  + sigma * np.random.randn(true_break)
y[true_break:]  = beta2 * Z[true_break:, 0] + sigma * np.random.randn(T - true_break)

breaks, coefs, ssr = fit_pure_structural_breaks(y, Z, m=1, h=20)
print("推定ブレーク:", breaks)
print("推定係数:", coefs)
```

* * *

2\. 閾値モデル（Threshold Model）の理論と実装
--------------------------------

### 2.1 論文の閾値モデルの内容（3.6 節）

J of Applied Econometrics - 200…

Bai & Perron は、構造変化モデルのアルゴリズムを\*\*閾値回帰（threshold regression）\*\*にも拡張できることを示しています

J of Applied Econometrics - 200…

。

モデル例：

$$
y_t = x_t'\beta + z_t' \nu_j + u_t,\quad \text{if } \gamma_{j-1} < v_t \le \gamma_j,\quad j=1,\dots,m+1
$$
*    $v_t$ ：観測可能な閾値変数（たとえばラグ付き y や別のマクロ指標など）
*    $\gamma_1,\dots,\gamma_m$ ：未知の閾値（thresholds）
*   区間  $(\gamma_{j-1}, \gamma_j]$  が「レジーム  $j$ 」に対応

**キーアイデア

J of Applied Econometrics - 200…

**

1.   $v_t$  の昇順に並び替えた系列  $v_{t_1} \le v_{t_2} \le \dots \le v_{t_T}$  を考える。
2.  並べ替え後の時系列  $(y_{t_r}, x_{t_r}, z_{t_r})_{r=1}^T$  の上で、  
    「ブレーク日による構造変化モデル」として扱うことができる。
3.  並べ替え後の index でのブレークポイント  $T_1,\dots,T_m$  から、  
    閾値は単に
    $$
    \hat{\gamma}_j = v_{t_{T_j}}
    $$
    として復元できる。

つまり、

> **「閾値モデルの推定 ＝ 閾値変数でソートした空間での多重構造変化問題」**

という帰着になり、前節の DP アルゴリズムをそのまま利用できる、というのが論文の主張です

J of Applied Econometrics - 200…

。

* * *

### 2.2 閾値モデルのシンプルな Python 実装

ここでは説明をシンプルにするため、

*    $x_t$ （共通係数）は無し（純閾値モデル）
*   モデルは
    $$
    y_t = z_t' \nu_j + u_t,\quad \gamma_{j-1} < v_t \le \gamma_j
    $$
*   閾値変数  $v_t$  は 1 次元

とします。  
実装の流れ：

1.   $v_t$  の昇順に並べ替える（index を保持）。
2.  並べ替え後の  $(y,Z)$  に対して、**上で実装した `fit_pure_structural_breaks`** を適用。
3.  得られたブレーク位置を閾値  $\gamma_j$  に変換。
4.  その閾値を使って「元の時間順」に戻した上で、各レジームごとに OLS で  $\nu_j$  を推定。

```python
def fit_threshold_model(y, Z, v, m, h):
    """
    閾値モデル（純閾値版）:
        y_t = z_t' * nu_j + u_t,
        gamma_{j-1} < v_t <= gamma_j でレジーム j

    を、Bai & Perron の「閾値変数でソート → ブレーク問題に帰着」という方法で推定する。

    Parameters
    ----------
    y : array-like, shape (T,)
        応答変数
    Z : array-like, shape (T, q)
        説明変数（係数はレジームごとに変化）
    v : array-like, shape (T,)
        閾値変数
    m : int
        閾値の数（＝ ブレーク数）
    h : int
        ソート後の「最小レジーム観測数」（各レジームに少なくとも h 点）

    Returns
    -------
    gammas : list of float
        推定された閾値 (gamma_1, ..., gamma_m)
    coefs : list of ndarray
        各レジームの係数ベクトル
    ssr_sorted : float
        ソート後空間での最小 SSR（参考）
    """
    y = np.asarray(y)
    Z = np.asarray(Z)
    v = np.asarray(v)
    T = len(y)

    # 1. 閾値変数 v の昇順でソート
    idx = np.argsort(v)
    y_sorted = y[idx]
    Z_sorted = Z[idx]
    v_sorted = v[idx]

    # 2. ソート空間で純構造変化モデルとしてブレーク推定
    breakpoints_sorted, coefs_sorted, ssr_sorted = fit_pure_structural_breaks(
        y_sorted, Z_sorted, m=m, h=h
    )

    # 3. ブレーク位置から閾値を復元
    gammas = [v_sorted[bp] for bp in breakpoints_sorted]

    # 4. 閾値に基づいて、元の順序のデータをレジーム分割し係数推定
    coefs = []
    bounds = [-np.inf] + gammas + [np.inf]
    for j in range(len(bounds) - 1):
        mask = (v > bounds[j]) & (v <= bounds[j+1])
        Z_j = Z[mask]
        y_j = y[mask]

        if len(y_j) == 0:
            # 安全のため: 実務では h を大きく取ることで基本的には起こらないようにする
            coefs.append(np.full(Z.shape[1], np.nan))
            continue

        SZZ = Z_j.T @ Z_j
        SZy = Z_j.T @ y_j
        beta_j = np.linalg.lstsq(SZZ, SZy, rcond=None)[0]
        coefs.append(beta_j)

    return gammas, coefs, ssr_sorted
```

#### 閾値モデルの簡単なシミュレーション例

```python
# 閾値 v=0 で係数が変わる単純な例
T = 300
np.random.seed(1)
v = np.random.randn(T)
Z = np.random.randn(T, 1)

beta_low  = 1.0   # v <= 0 のとき
beta_high = -2.0  # v > 0 のとき
sigma = 0.1

y = np.where(v <= 0,
             beta_low  * Z[:, 0],
             beta_high * Z[:, 0]) + sigma * np.random.randn(T)

gammas, coefs, ssr = fit_threshold_model(y, Z, v, m=1, h=30)

print("推定された閾値 gamma:", gammas)
print("レジーム1係数 (v <= gamma):   ", coefs[0])
print("レジーム2係数 (v >  gamma):   ", coefs[1])
```

* * *

3\. まとめと拡張のポイント
---------------

*   上記コードは論文の中核部分：
    *   **O(T²) 動的計画法によるグローバルなブレーク推定**
        J of Applied Econometrics - 200…
    *   **閾値変数でソートして閾値モデルを構造変化問題に帰着するアイデア**
        J of Applied Econometrics - 200…
        を、そのまま Python で再現した、**最小限だけど素直な実装**です。
*   実務レベルで Bai–Perron を完全に再現するには、さらに：
    *   部分構造変化モデル（共通係数 β とセグメント特有係数 ν の両方）
    *   HAC 共分散を用いた Wald 系の検定統計（supF, UDmax, WDmax など）
    *   supF(ℓ+1|ℓ) によるブレーク数の逐次推定
        J of Applied Econometrics - 200…
    *   ブレーク日の漸近分布に基づく信頼区間  
        などを実装する必要があります。

もし、

*   「共通係数 β がある partial structural change モデルも含めて実装したい」
*   「supF 検定や sequential procedure を Python で再現したい」
*   「あなたの実データ（マクロ・金融時系列）にそのまま当てはめるラッパ関数が欲しい」

といったニーズがあれば、その前提でモジュール風に整理したコードも用意できます。

## Response:
思考時間: 58s

了解です。  
ここでは

1.  **supF 検定（H0: ブレークなし vs H1: m 個のブレーク）**
2.  **supF(ℓ+1｜ℓ) を使った sequential procedure（ブレーク数の推定）**

を、前回の **純構造変化モデル用 DP 実装** を拡張する形で Python コード付きで示します。

前提：  
モデルは純構造変化

$$
y_t = z_t' \nu_j + u_t,\quad t \in \text{regime } j
$$

で、各レジームの回帰係数  $\nu_j$  が変化するケースを扱います。

* * *

1\. 下準備：DP と SSR 計算（前回コード＋α）
----------------------------

前回の DP 実装と SSR 関数に、**「与えられたブレーク集合の SSR」を計算するヘルパー**だけを追加します。  
（前回コードをそのまま貼っておきます。もう書いてあれば、このブロックは飛ばしても OK です。）

```python
import numpy as np

def ols_segment_SSR_precompute(y, Z):
    """
    y: shape (T,)
    Z: shape (T, q)
    任意区間 [i, j] の SSR を高速に計算するための累積和を構築。
    """
    y = np.asarray(y)
    Z = np.asarray(Z)
    T, q = Z.shape

    Sy = np.zeros(T + 1)            # 累積 y'y
    SZZ = np.zeros((T + 1, q, q))   # 累積 Z'Z
    SZy = np.zeros((T + 1, q))      # 累積 Z'y

    for t in range(T):
        Sy[t+1] = Sy[t] + y[t]**2
        SZZ[t+1] = SZZ[t] + np.outer(Z[t], Z[t])
        SZy[t+1] = SZy[t] + Z[t] * y[t]

    return Sy, SZZ, SZy

def segment_SSR(i, j, Sy, SZZ, SZy, ridge=1e-12):
    """
    区間 [i, j]（両端含む）での回帰 y ~ Z の SSR を計算。
    SSR = y'y - (Z'y)' (Z'Z)^{-1} (Z'y)
    """
    Syy = Sy[j+1] - Sy[i]
    SZZ_seg = SZZ[j+1] - SZZ[i]
    SZy_seg = SZy[j+1] - SZy[i]

    # 数値安定化用のごく弱いリッジ
    SZZ_reg = SZZ_seg + ridge * np.eye(SZZ_seg.shape[0])

    try:
        beta = np.linalg.solve(SZZ_reg, SZy_seg)
    except np.linalg.LinAlgError:
        beta = np.linalg.lstsq(SZZ_reg, SZy_seg, rcond=None)[0]

    SSR = Syy - SZy_seg @ beta
    return SSR, beta

def fit_pure_structural_breaks(y, Z, m, h):
    """
    純構造変化モデル:
        y_t = z_t' * nu_j + u_t,   t in regime j
    について、Bai & Perron 型 DP【グローバル最小 SSR】で
    m 個のブレークを推定する。

    Parameters
    ----------
    y : (T,)
    Z : (T, q)
    m : int        ブレーク数
    h : int        最小セグメント長

    Returns
    -------
    breakpoints : list[int]
        ブレークインデックス（0-based, その index が「セグメントの終わり」）
    coefs : list[np.ndarray]
        各セグメントの OLS 係数
    SSR_total : float
        最小 SSR
    """
    y = np.asarray(y)
    Z = np.asarray(Z)
    T = len(y)
    K = m + 1  # セグメント数

    if T < K * h:
        raise ValueError("サンプルが短すぎます: T < (m+1)*h")

    # 1. 累積クロスプロダクト
    Sy, SZZ, SZy = ols_segment_SSR_precompute(y, Z)

    # 2. 各区間 [i, j] の SSR を事前計算
    SSR_mat = np.full((T, T), np.inf)
    for i in range(T):
        for j in range(i + h - 1, T):
            SSR_mat[i, j], _ = segment_SSR(i, j, Sy, SZZ, SZy)

    # 3. DP テーブル
    dp = np.full((K, T), np.inf)    # dp[k, t]: 先頭〜t を k+1 セグメントに分割した最小 SSR
    prev = np.full((K, T), -1, int)

    # ベースケース: k = 0（1セグメント）
    for t in range(h - 1, T):
        if T - (t + 1) < (K - 1) * h:
            continue
        dp[0, t] = SSR_mat[0, t]
        prev[0, t] = -1

    # 再帰: k = 1..K-1
    for k in range(1, K):
        for t in range((k + 1) * h - 1, T):
            if T - (t + 1) < (K - 1 - k) * h:
                continue

            best_val = np.inf
            best_s = -1

            s_min = k * h - 1
            s_max = t - h
            for s in range(s_min, s_max + 1):
                if not np.isfinite(dp[k-1, s]):
                    continue
                val = dp[k-1, s] + SSR_mat[s+1, t]
                if val < best_val:
                    best_val = val
                    best_s = s

            dp[k, t] = best_val
            prev[k, t] = best_s

    # 最後のセグメントは T-1 で終了
    last_k = K - 1
    best_end = T - 1
    best_val = dp[last_k, best_end]
    if not np.isfinite(best_val):
        raise ValueError("フルサンプルをカバーする分割が見つかりません。m や h を見直してください。")

    # バックトラックでブレーク復元
    breakpoints = []
    t = best_end
    for k in range(last_k, 0, -1):
        s = prev[k, t]
        breakpoints.append(s)
        t = s
    breakpoints = sorted(breakpoints)

    # 各セグメントの係数再推定
    coefs = []
    Sy, SZZ, SZy = ols_segment_SSR_precompute(y, Z)  # 念のため再計算
    start = 0
    for bp in breakpoints + [T - 1]:
        _, beta = segment_SSR(start, bp, Sy, SZZ, SZy)
        coefs.append(beta)
        start = bp + 1

    return breakpoints, coefs, best_val

def SSR_from_breaks(y, Z, breakpoints):
    """
    与えられたブレーク集合（0-based, セグメント終端）から
    全体の SSR を計算するヘルパー。
    """
    y = np.asarray(y)
    Z = np.asarray(Z)
    T = len(y)

    Sy, SZZ, SZy = ols_segment_SSR_precompute(y, Z)
    bps = list(breakpoints)
    SSR_total = 0.0
    start = 0
    for bp in bps + [T - 1]:
        SSR_seg, _ = segment_SSR(start, bp, Sy, SZZ, SZy)
        SSR_total += SSR_seg
        start = bp + 1
    return SSR_total
```

* * *

2\. supF 検定：H0（ブレーク無し） vs H1（m ブレーク）
------------------------------------

### 2.1 理屈

純構造変化モデルで

*   制約付きモデル（H0：ブレーク無し）：  
    パラメータ数 = q
*   制約無しモデル（H1：m ブレーク）：  
    各レジームで q パラメータ → 合計 (m+1)q 個

残差平方和を

*   SSR₀：ブレーク無し
*   SSRₘ：m ブレーク（最小 SSR：動的計画法で求めたもの）

とすると、通常の回帰 F 検定に対応する統計量は

$$
F_{\text{supF}(m)} = \frac{(SSR_0 - SSR_m)/(m q)}{SSR_m / (T - (m+1)q)}.
$$

Bai–Perron の supF は「ブレーク位置で最適化した F」なので、  
DP によって最小 SSRₘ を使うことで、そのまま supF 統計量になります。  
（p 値・臨界値は **通常の F 分布ではなく** Bai–Perron のシミュレーション表を参照する必要があります）

### 2.2 実装

```python
def supF_0_vs_m(y, Z, m, h):
    """
    supF(m) 検定統計量を計算（H0: ブレーク無し vs H1: m ブレーク）。

    純構造変化モデルを仮定し、i.i.d. 誤差・同分散の通常 F 統計量の形で計算。
    ※ p値は Bai-Perron の臨界値表と比較するのが望ましい。

    Returns
    -------
    F_stat : float
        supF(m) の統計量
    SSR0 : float
        ブレーク無し（1 セグメント）の SSR
    SSRm : float
        m ブレークの最小 SSR（DP による）
    breakpoints_m : list[int]
        m ブレークの推定位置
    """
    y = np.asarray(y)
    Z = np.asarray(Z)
    T, q = Z.shape

    # ブレーク無しの SSR
    Sy, SZZ, SZy = ols_segment_SSR_precompute(y, Z)
    SSR0, _ = segment_SSR(0, T-1, Sy, SZZ, SZy)

    # m ブレークの SSR（グローバル最小）
    breakpoints_m, _, SSRm = fit_pure_structural_breaks(y, Z, m=m, h=h)

    df1 = m * q
    df2 = T - (m + 1) * q
    if df1 <= 0 or df2 <= 0:
        raise ValueError("自由度が負またはゼロになっています。T, m, q を確認してください。")

    F_stat = ((SSR0 - SSRm) / df1) / (SSRm / df2)
    return F_stat, SSR0, SSRm, breakpoints_m
```

* * *

3\. Sequential procedure：supF(ℓ+1｜ℓ) によるブレーク数推定
-----------------------------------------------

### 3.1 考え方

Bai & Perron の sequential 法はざっくりいうと：

1.  まず H0: 0 ブレーク vs H1: 1 ブレークで supF(1) を計算し、  
    \*\*「何らかのブレークが存在するか」\*\*を検定。
2.  有意なら 1 ブレークモデルを受け入れ、次に
    *   H0: 1 ブレーク vs H1: 2 ブレーク  
        → supF(2|1) を計算。
3.  supF(ℓ+1|ℓ) の計算は
    *   現在の ℓ ブレークモデルの各セグメントごとに  
        「そのセグメント内でさらに 1 ブレーク入りうるか？」を supF(1) で調べ、
    *   そのセグメント群の中で最大の F を supF(ℓ+1|ℓ) とする。
4.  これを ℓ = 0,1,... と繰り返し、臨界値を下回ったところで停止。  
    → その ℓ が推定ブレーク数。

ここでは、

*   臨界値との比較は**ユーザー側で**行う前提で
*   Python 関数は  
    「各 ℓ での supF(ℓ+1|ℓ) と、対応するブレーク構造」を返す

ようにします。

### 3.2 実装コード

```python
def supF_1_within_segment(y_seg, Z_seg, h):
    """
    1つのセグメント上で、
    H0: ブレーク無し vs H1: 1 ブレーク
    の supF(1) を計算する補助関数。

    Returns
    -------
    F_stat : float
    SSR0_seg : float
    SSR1_seg : float
    local_break : int or None
        セグメント内のブレーク位置（0-based, セグメント内 index）
    """
    y_seg = np.asarray(y_seg)
    Z_seg = np.asarray(Z_seg)
    n = len(y_seg)
    q = Z_seg.shape[1]

    if n < 2 * h or n <= 2 * q:
        # ブレークを入れられるだけの長さがない
        return np.nan, np.nan, np.nan, None

    # セグメント内での SSR0
    Sy, SZZ, SZy = ols_segment_SSR_precompute(y_seg, Z_seg)
    SSR0_seg, _ = segment_SSR(0, n-1, Sy, SZZ, SZy)

    # セグメント内で 1 ブレーク DP
    try:
        bps_local, _, SSR1_seg = fit_pure_structural_breaks(y_seg, Z_seg, m=1, h=h)
    except ValueError:
        return np.nan, np.nan, np.nan, None

    df1 = 1 * q
    df2 = n - (1 + 1) * q  # (1+1)セグメント
    if df1 <= 0 or df2 <= 0:
        return np.nan, SSR0_seg, SSR1_seg, None

    F_stat = ((SSR0_seg - SSR1_seg) / df1) / (SSR1_seg / df2)
    local_break = bps_local[0] if len(bps_local) > 0 else None
    return F_stat, SSR0_seg, SSR1_seg, local_break

def sequential_break_selection(y, Z, max_breaks, h):
    """
    supF(ℓ+1|ℓ) に基づく sequential procedure を実装。

    手順:
        - ℓ = 0,1,2,... と増やしながら、
          ・ℓ ブレークモデルを DP で推定
          ・各セグメントで supF(1) を計算して supF(ℓ+1|ℓ) を求める
        - ここでは「いつ止めるか」はユーザーが臨界値と比較して判断する前提で、
          各 ℓ に対する情報をすべて返す。

    Parameters
    ----------
    y : (T,)
    Z : (T, q)
    max_breaks : int
        探索する最大ブレーク数 M
    h : int
        最小セグメント長

    Returns
    -------
    results : list[dict]
        各 ℓ (0..max_breaks-1) について以下を含む辞書のリスト:
        - 'ell' : ℓ
        - 'breaks_ell' : ℓ ブレークの推定ブレーク位置（list[int]）
        - 'SSR_ell' : ℓ ブレークモデルの最小 SSR
        - 'supF_ell_plus_1' : supF(ℓ+1|ℓ) の値
        - 'candidate_new_break' : supF を達成する候補追加ブレーク位置（global index）
        - 'segment_index' : どのセグメントに追加されたか（0-based）
    """
    y = np.asarray(y)
    Z = np.asarray(Z)
    T = len(y)
    q = Z.shape[1]

    results = []

    # ℓ = 0: ブレークなし
    Sy_full, SZZ_full, SZy_full = ols_segment_SSR_precompute(y, Z)
    SSR0, _ = segment_SSR(0, T-1, Sy_full, SZZ_full, SZy_full)
    breaks_ell = []  # ℓ=0 なのでブレークなし

    SSR_ell = SSR0
    results.append({
        'ell': 0,
        'breaks_ell': [],
        'SSR_ell': SSR0,
        'supF_ell_plus_1': None,
        'candidate_new_break': None,
        'segment_index': None
    })

    # ℓ = 0..max_breaks-1 で supF(ℓ+1|ℓ) を計算
    for ell in range(0, max_breaks):
        # まず ℓ ブレークモデルのグローバルな推定（ℓ>=1 のとき）
        if ell > 0:
            breaks_ell, _, SSR_ell = fit_pure_structural_breaks(y, Z, m=ell, h=h)

        # セグメント境界を構成（0-based index の終端）
        if len(breaks_ell) == 0:
            seg_ends = [T - 1]
            seg_starts = [0]
        else:
            seg_ends = breaks_ell + [T - 1]
            seg_starts = [0] + [bp + 1 for bp in breaks_ell]

        # 各セグメントで supF(1) を計算
        best_F = -np.inf
        best_new_break = None
        best_seg_idx = None

        for seg_idx, (s, e) in enumerate(zip(seg_starts, seg_ends)):
            y_seg = y[s:e+1]
            Z_seg = Z[s:e+1, :]

            F_seg, SSR0_seg, SSR1_seg, local_break = supF_1_within_segment(y_seg, Z_seg, h=h)
            if np.isnan(F_seg) or local_break is None:
                continue

            if F_seg > best_F:
                best_F = F_seg
                best_seg_idx = seg_idx
                # セグメント内 index → 全体 index に変換
                best_new_break = s + local_break

        results[ell]['supF_ell_plus_1'] = best_F if best_F != -np.inf else None
        results[ell]['candidate_new_break'] = best_new_break
        results[ell]['segment_index'] = best_seg_idx

        # 次のループでは ell を 1 増やし、fit_pure_structural_breaks で ℓ+1 ブレークを推定する想定。
        # 実際に「止める」かどうかは、ユーザーが results[ell]['supF_ell_plus_1'] と
        # Bai-Perron の臨界値表を比較して判断する想定。

    return results
```

* * *

4\. 使い方イメージ
-----------

### 4.1 supF(0 vs m) の例

```python
T = 200
np.random.seed(0)
Z = np.random.randn(T, 1)
true_break = 120
beta1, beta2 = 1.0, 3.0
sigma = 0.2

y = np.empty(T)
y[:true_break]  = beta1 * Z[:true_break, 0]  + sigma * np.random.randn(true_break)
y[true_break:]  = beta2 * Z[true_break:, 0] + sigma * np.random.randn(T - true_break)

F_sup, SSR0, SSR1, breaks_m = supF_0_vs_m(y, Z, m=1, h=20)
print("supF(1) =", F_sup)
print("推定ブレーク位置:", breaks_m)
```

### 4.2 sequential procedure の例

```python
results = sequential_break_selection(y, Z, max_breaks=3, h=20)

for res in results:
    ell = res['ell']
    print(f"\nell = {ell}")
    print("  ブレーク位置 (ell個):", res['breaks_ell'])
    print("  SSR_ell:", res['SSR_ell'])
    print("  supF(ell+1 | ell):", res['supF_ell_plus_1'])
    print("  候補追加ブレーク位置:", res['candidate_new_break'])
```

ここで得られた `supF_ell_plus_1` を、Bai & Perron (2003) や関連の補論で示されている **臨界値表（trim=ε, q 次元などに依存）** と比較して、

*   supF(1|0) が臨界値を超える → 少なくとも 1 ブレークあり
*   supF(2|1) が臨界値を超える → 2 ブレークに増やす
*   supF(3|2) が臨界値を下回る → 推定ブレーク数は 2

といった具合にブレーク数を決めるイメージです。

* * *

5\. 補足
------

*   上記の実装は
    *   純構造変化モデル（全係数がレジームごとに変化）
    *   i.i.d. 誤差・同分散という単純なケース  
        を想定した **基本形** です。
*   Bai–Perron 論文本来は、
    *   部分構造変化（共通係数 β＋変化する係数 ν）
    *   シリアル相関・異分散に対する HAC ロバストな Wald 統計
    *   trimming ε の調整  
        などを含んでいますが、それらは「共分散行列推定」と「制約付き回帰行列の構成」がかなり重たくなるので、  
        必要でしたらそこまで拡張したバージョンも段階的に書いていけます。

もし次のステップとして、

*   partial structural change モデル（β 共通＋ν セグメント別）での sequential procedure
*   あなたのマクロ／金融データに直接適用できるヘルパー関数群

が欲しければ、その前提で設計します。

## Response:
思考時間: 1m 7s

承知しました。\*\*partial structural change モデル（β 共通＋ν セグメント別）**に対して、Bai–Perron（2003）の**Sargan型反復法（§3.4）**と**supF(ℓ+1|ℓ) の逐次手順（§5.3）\*\*に準拠した実装を示します。以下のコードは：

*   共有係数 **β** と、レジームごとの係数 **ν\_j** を同時推定
*   ブレーク集合の探索は \*\*DP（動的計画法）\*\*を「y−Xβ」を被説明変数にして実行
*   逐次手順では、**各セグメント内で 1 ブレーク追加を仮説**として supF(ℓ+1|ℓ) を計算し、最大のセグメントを選んでいく

という流れです（理論背景は該当箇所参照：DP・三角行列 §3.1–3.3、partialモデルの反復スキーム §3.4、逐次検定 §5.3）。

J of Applied Econometrics - 200…

* * *

実装（Python）
==========

> 依存：NumPy のみ。計算を簡潔に保つため、HAC 共分散やクリティカルバリュー表は含めていません（F 値は返します）。  
> 実務では Bai–Perron の臨界値表（trim ε, 次元 q に依存）と照合して採否を判断してください（論文 §5.1–5.3）。
> 
> J of Applied Econometrics - 200…

```python
import numpy as np

# ---------- 汎用: 区間OLSのための前計算とSSR ----------
def ols_segment_SSR_precompute(y, Z):
    y = np.asarray(y); Z = np.asarray(Z)
    T, q = Z.shape
    Sy  = np.zeros(T+1)
    SZZ = np.zeros((T+1, q, q))
    SZy = np.zeros((T+1, q))
    for t in range(T):
        Sy[t+1]  = Sy[t]  + y[t]**2
        SZZ[t+1] = SZZ[t] + np.outer(Z[t], Z[t])
        SZy[t+1] = SZy[t] + Z[t] * y[t]
    return Sy, SZZ, SZy

def segment_SSR(i, j, Sy, SZZ, SZy, ridge=1e-12):
    Syy     = Sy[j+1]  - Sy[i]
    SZZ_seg = SZZ[j+1] - SZZ[i]
    SZy_seg = SZy[j+1] - SZy[i]
    SZZ_reg = SZZ_seg + ridge * np.eye(SZZ_seg.shape[0])
    try:
        beta = np.linalg.solve(SZZ_reg, SZy_seg)
    except np.linalg.LinAlgError:
        beta = np.linalg.lstsq(SZZ_reg, SZy_seg, rcond=None)[0]
    SSR = Syy - SZy_seg @ beta
    return SSR, beta

# ---------- DP: 純構造変化（y ~ Z）で m ブレークを推定 ----------
def fit_pure_structural_breaks(y, Z, m, h):
    y = np.asarray(y); Z = np.asarray(Z)
    T = len(y); K = m + 1
    if T < K*h:
        raise ValueError("T < (m+1)*h")

    Sy, SZZ, SZy = ols_segment_SSR_precompute(y, Z)

    # 事前計算: 任意区間のSSR（長さ>=hのみ）
    SSR_mat = np.full((T, T), np.inf)
    for i in range(T):
        for j in range(i + h - 1, T):
            SSR_mat[i, j], _ = segment_SSR(i, j, Sy, SZZ, SZy)

    # DP
    dp   = np.full((K, T), np.inf)
    prev = np.full((K, T), -1, int)

    # k=0（1セグメント）
    for t in range(h-1, T):
        if T - (t+1) < (K-1)*h:  # 残りが埋まるか
            continue
        dp[0, t] = SSR_mat[0, t]
        prev[0, t] = -1

    # k=1..K-1
    for k in range(1, K):
        for t in range((k+1)*h - 1, T):
            if T - (t+1) < (K-1-k)*h:
                continue
            best_val, best_s = np.inf, -1
            s_min, s_max = k*h - 1, t - h
            for s in range(s_min, s_max+1):
                if not np.isfinite(dp[k-1, s]): 
                    continue
                val = dp[k-1, s] + SSR_mat[s+1, t]
                if val < best_val:
                    best_val, best_s = val, s
            dp[k, t] = best_val
            prev[k, t] = best_s

    # 最後は常に T-1 で閉じる
    last_k = K - 1
    best_end = T - 1
    if not np.isfinite(dp[last_k, best_end]):
        raise ValueError("DP: no full-sample partition; adjust m or h.")

    # 復元
    bps = []
    t = best_end
    for k in range(last_k, 0, -1):
        s = prev[k, t]
        bps.append(s)
        t = s
    bps = sorted(bps)

    # 係数（参考）
    coefs = []
    start = 0
    for bp in bps + [T-1]:
        _, beta = segment_SSR(start, bp, Sy, SZZ, SZy)
        coefs.append(beta)
        start = bp + 1

    return bps, coefs, dp[last_k, best_end]

# ---------- 部分構造変化: Zをブロック化 ----------
def build_block_Z(Z, breaks):
    """
    breaks: [b1, b2, ...]  各要素はそのセグメントの終端（0-based）
    返り値: Z_block （列数 = (m+1)*q）
    """
    Z = np.asarray(Z)
    T, q = Z.shape
    bps = list(breaks)
    seg_ends   = bps + [T-1]
    seg_starts = [0] + [b+1 for b in bps]
    cols = []
    for s, e in zip(seg_starts, seg_ends):
        Zj = np.zeros_like(Z)
        Zj[s:e+1, :] = Z[s:e+1, :]
        cols.append(Zj)
    Z_block = np.concatenate(cols, axis=1)
    return Z_block

def ssr_given_breaks_partial(y, X, Z, breaks, ridge=1e-12):
    """
    与えられたブレーク集合で、Y ~ [X, Z_block] のOLSを実施して SSR を返す
    """
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    Zb = build_block_Z(Z, breaks)
    W  = np.concatenate([X, Zb], axis=1)  # [X | Z1 | ... | Z_{m+1}]
    WTW = W.T @ W + ridge * np.eye(W.shape[1])
    WTy = W.T @ y
    beta_all = np.linalg.lstsq(WTW, WTy, rcond=None)[0]
    resid = y - W @ beta_all
    SSR = float(resid.T @ resid)
    # 分解（任意）：β と ν_j
    p = X.shape[1]
    q = Z.shape[1]
    m = len(breaks)
    beta = beta_all[:p]
    nus  = [beta_all[p + j*q : p + (j+1)*q] for j in range(m+1)]
    return SSR, beta, nus

# ---------- 初期値（論文 §3.5 の実用策に倣う簡易版） ----------
def init_beta_via_pure(y, X, Z, m, h):
    """
    純構造変化として [X|Z] をまとめて変化させる近似でブレークを推定し、
    そこで得た Z 側の係数で y - Z_block*nu を作って X で回帰 → β初期値
    """
    Ztilde = np.concatenate([X, Z], axis=1)  # 便宜的にまとめる
    bps0, coefs0, _ = fit_pure_structural_breaks(y, Ztilde, m=m, h=h)
    # Z部分だけ取り出して、y - Z_block * nu_Z を作る
    T, p = X.shape
    q     = Z.shape[1]
    Zb = build_block_Z(Z, bps0)
    # 純構造の各セグメント係数 coefs0[j] は次元 (p+q,)
    nuZ = np.concatenate([c[p:] for c in coefs0])  # 連結（長さ=(m+1)*q）
    y_tilde = y - Zb @ nuZ
    beta0 = np.linalg.lstsq(X, y_tilde, rcond=None)[0]
    return beta0

# ---------- 部分構造変化: 反復アルゴリズム（Sargan型; §3.4） ----------
def fit_partial_structural_breaks(y, X, Z, m, h, max_iter=10, tol=1e-9):
    """
    共有β + セグメント別ν を同時推定。
    Step A: β固定で y - Xβ を被説明変数として純構造DP → ブレーク更新
    Step B: ブレーク固定で Y ~ [X | Z_block] を OLS → (β, ν) 更新
    収束まで繰り返し（通常 1-2回で収束が多いと論文は報告）。
    """
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    T = len(y)
    p = X.shape[1]; q = Z.shape[1]

    beta = init_beta_via_pure(y, X, Z, m, h)

    prev_SSR = np.inf
    breaks = None
    for it in range(max_iter):
        # Step A: β固定 → y - Xβ で DP
        y_tilde = y - X @ beta
        breaks_A, _, _ = fit_pure_structural_breaks(y_tilde, Z, m=m, h=h)

        # Step B: ブレーク固定で (β, ν) を同時OLS
        SSR, beta_new, nus = ssr_given_breaks_partial(y, X, Z, breaks_A)

        # 収束判定
        if abs(prev_SSR - SSR) <= tol:
            breaks = breaks_A
            beta = beta_new
            break
        prev_SSR = SSR
        beta = beta_new
        breaks = breaks_A

    if breaks is None:
        # 最後に一度評価
        y_tilde = y - X @ beta
        breaks, _, _ = fit_pure_structural_breaks(y_tilde, Z, m=m, h=h)
        SSR, beta, nus = ssr_given_breaks_partial(y, X, Z, breaks)

    return breaks, beta, nus, SSR

# ---------- supF(0 vs m) for partial model ----------
def supF_0_vs_m_partial(y, X, Z, m, h):
    """
    H0: m=0（ブレーク無し; y ~ X + Z）
    H1: m ブレーク（β共通, νセグメント別）を fit_partial_structural_breaks で推定
    F = ((SSR0 - SSRm)/(m*q)) / (SSRm/(T - p - (m+1)*q))
    """
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    T = len(y); p = X.shape[1]; q = Z.shape[1]

    # SSR0: ブレーク無しで Y ~ [X|Z]
    W0 = np.concatenate([X, Z], axis=1)
    b0 = np.linalg.lstsq(W0, y, rcond=None)[0]
    res0 = y - W0 @ b0
    SSR0 = float(res0.T @ res0)

    # SSRm: 部分構造ブレーク
    bps, beta, nus, SSRm = fit_partial_structural_breaks(y, X, Z, m=m, h=h)

    df1 = m * q
    df2 = T - p - (m + 1) * q
    if df1 <= 0 or df2 <= 0:
        raise ValueError("df invalid; check T, p, q, m.")
    F = ((SSR0 - SSRm) / df1) / (SSRm / df2)
    return F, SSR0, SSRm, bps, beta, nus

# ---------- supF(ℓ+1 | ℓ) の逐次手順（partial model） ----------
def best_one_more_break_in_segment(y, X, Z, breaks_ell, seg_index, h):
    """
    既存のℓブレーク partition のセグメント seg_index 内に
    1つブレークを追加する候補を総当たりで探索し、最良SSRと位置を返す。
    ※ βは各候補ごとに [X|Z_block] で同時OLS。（実装簡略のため再推定）
    """
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    T = len(y)
    bps = list(breaks_ell)
    seg_ends   = bps + [T-1]
    seg_starts = [0] + [b+1 for b in bps]
    s, e = seg_starts[seg_index], seg_ends[seg_index]

    # h を満たす分割のみ
    cand_min = s + h - 1
    cand_max = e - h
    best_SSR = np.inf
    best_bp  = None
    for bp in range(cand_min, cand_max + 1):
        new_breaks = sorted(bps + [bp])
        SSR, _, _ = ssr_given_breaks_partial(y, X, Z, new_breaks)
        if SSR < best_SSR:
            best_SSR = SSR
            best_bp  = bp
    return best_SSR, best_bp

def sequential_procedure_partial(y, X, Z, max_breaks, h):
    """
    Bai–Perron の supF(ℓ+1|ℓ) に基づく逐次法（partial model版の実装）。
    各ℓについて：
      1) ℓブレークの最良partition（DP×反復）とSSR_ell
      2) 各セグメントで 1 ブレーク追加 → 最良SSR_candidate と場所
      3) supF(ℓ+1|ℓ) = ((SSR_ell - SSR_candidate)/q) / (SSR_candidate/(T - p - (ℓ+2)q))
         を計算し、「最大」のセグメントと位置を記録
    返値は各ℓの集計（F値/候補位置など）。採否は外部で臨界値と比較してください。
    """
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    T = len(y); p = X.shape[1]; q = Z.shape[1]

    results = []

    # ℓ=0 から開始
    # ℓ=0: partitionは空、SSR_0 は [X|Z] のOLS
    W0 = np.concatenate([X, Z], axis=1)
    b0 = np.linalg.lstsq(W0, y, rcond=None)[0]
    res0 = y - W0 @ b0
    SSR_ell = float(res0.T @ res0)
    breaks_ell = []

    results.append({
        'ell': 0,
        'breaks_ell': [],
        'SSR_ell': SSR_ell,
        'supF_ell_plus_1': None,
        'candidate_new_break': None,
        'segment_index': None
    })

    for ell in range(0, max_breaks):
        if ell > 0 or ell == 0:
            # ℓブレークの最良partition（DP+反復）
            breaks_ell, beta, nus, SSR_ell = fit_partial_structural_breaks(y, X, Z, m=ell, h=h)

        # セグメント群
        T = len(y)
        seg_ends   = breaks_ell + [T-1]
        seg_starts = [0] + [b+1 for b in breaks_ell]

        best_SSR_candidate = np.inf
        best_bp_candidate  = None
        best_seg_idx       = None

        for seg_idx in range(len(seg_starts)):
            # このセグメント内だけで 1ブレーク追加
            SSR_cand, bp_cand = best_one_more_break_in_segment(y, X, Z, breaks_ell, seg_idx, h)
            if bp_cand is None:
                continue
            if SSR_cand < best_SSR_candidate:
                best_SSR_candidate = SSR_cand
                best_bp_candidate  = bp_cand
                best_seg_idx       = seg_idx

        if best_bp_candidate is None:
            # 追加不能（長さ制約等）
            F_val = None
        else:
            df1 = q
            df2 = T - p - (ell + 2)*q
            if df1 <= 0 or df2 <= 0:
                F_val = None
            else:
                F_val = ((SSR_ell - best_SSR_candidate)/df1) / (best_SSR_candidate/df2)

        results.append({
            'ell': ell,
            'breaks_ell': breaks_ell,
            'SSR_ell': SSR_ell,
            'supF_ell_plus_1': F_val,
            'candidate_new_break': best_bp_candidate,
            'segment_index': best_seg_idx
        })

    return results
```

* * *

使い方（最小例）
--------

```python
# ダミーデータ生成：β共通、νがブレークで変わる
np.random.seed(0)
T = 300
p, q = 2, 1
X = np.c_[np.ones(T), np.random.randn(T)]     # 共有β（定数＋補助）
Z = np.random.randn(T, q)                      # セグメント別 ν の説明変数
beta_true = np.array([1.0, -0.5])              # 共有
breaks_true = [120, 220]                       # 2ブレーク → 3セグメント
nus_true = [np.array([0.5]), np.array([2.0]), np.array([-1.0])]
y = np.empty(T)
start = 0
for bp, nu in zip(breaks_true + [T-1], nus_true):
    seg_idx = slice(start, bp+1)
    y[seg_idx] = X[seg_idx]@beta_true + Z[seg_idx]@nu + 0.2*np.random.randn(len(range(start, bp+1)))
    start = bp+1

# まず m固定の supF(0 vs m) を求める（例：m=2）
F_sup, SSR0, SSRm, bps, beta_hat, nus_hat = supF_0_vs_m_partial(y, X, Z, m=2, h=20)
print("supF(0 vs 2) =", F_sup)
print("推定ブレーク:", bps)
print("推定β:", beta_hat)

# 次に逐次手順（最大ブレーク数上限を指定）
seq = sequential_procedure_partial(y, X, Z, max_breaks=4, h=20)
for r in seq:
    print(r['ell'], r['breaks_ell'], r['supF_ell_plus_1'], r['candidate_new_break'])
```

* * *

実務メモ
----

*   \*\*部分構造変化（β 共通）\*\*に対して DP を直接使えない理由と、**Sargan型の交互最適化**で解く流れは論文 §3.4 が元ネタです（StepA: β固定→純構造でブレーク、StepB: ブレーク固定→\[X|Z\_block\]で同時OLS）。一回で収束するケースが多いのも同セクションの実務的所見に一致します。
    J of Applied Econometrics - 200…
*   **逐次手順 supF(ℓ+1|ℓ)** は、現在の ℓ ブレーク分割の**各セグメント**で「さらに 1 ブレーク」を試し、その中の**最大 F**を supF(ℓ+1|ℓ) とする構成（論文 §5.3）。上の実装では、各候補ブレークごとに \[X|Z\_block\] で OLS を解き SSR を比較する素直実装です。
    J of Applied Econometrics - 200…
*   **F 値の自由度**（同分散・i.i.d. 想定の簡易版）
    *   H0: ℓ ブレーク（パラメータ自由度 = p + (ℓ+1)q）
    *   H1: ℓ+1 ブレーク（パラメータ自由度 = p + (ℓ+2)q）
    *   よって **df1 = q**, **df2 = T − p − (ℓ+2)q** を使用。
*   実務での採否は、**trim ε と q に応じた Bai–Perron の臨界値表**で行ってください（§5.1–5.3, 付随メモ・追加表）。系列相関や異分散を許す場合は**ε を大きめ**に（例：0.15〜0.20）するのが推奨（§5.5）。
    J of Applied Econometrics - 200…
*   本コードは**ロバスト共分散（HAC）や p 値**を計算していません。必要なら、各ケースに応じた共分散（論文 §5.1 の行列式とケース分け）で Wald/F を組み直してください。
    J of Applied Econometrics - 200…

* * *

必要でしたら、\*\*HAC対応の supF、UDmax/WDmax、ブレーク日信頼区間（§4）\*\*まで含めた拡張版も用意します。

## Response:
了解です。\*\*partial structural change（β共通＋νセグメント別）\*\*について、

*   **HAC（Newey–West）対応 supF(0 vs m)**
*   **HAC 対応 supF(ℓ+1｜ℓ) による逐次手順**
*   **UDmax / WDmax（m を 1..M の範囲で探索）**
*   **ブレーク日 信頼区間（近傍プロフィール法による近似的 CI）**

を、前回コードを拡張して “そのまま動く最小実装” を示します。  
（注）ロバスト臨界値はテーブル依存です。コードは**統計量**を返します。採否は、トリミング率 ε、q 次元などに応じた臨界値と比較してください。

* * *

0) 依存関数（前回の partial 実装＋HAC）
===========================

```python
import numpy as np

# -------------------- 累積クロスプロダクトと区間SSR --------------------
def ols_segment_SSR_precompute(y, Z):
    y = np.asarray(y); Z = np.asarray(Z)
    T, q = Z.shape
    Sy  = np.zeros(T+1)
    SZZ = np.zeros((T+1, q, q))
    SZy = np.zeros((T+1, q))
    for t in range(T):
        Sy[t+1]  = Sy[t]  + y[t]**2
        SZZ[t+1] = SZZ[t] + np.outer(Z[t], Z[t])
        SZy[t+1] = SZy[t] + Z[t] * y[t]
    return Sy, SZZ, SZy

def segment_SSR(i, j, Sy, SZZ, SZy, ridge=1e-12):
    Syy     = Sy[j+1]  - Sy[i]
    SZZ_seg = SZZ[j+1] - SZZ[i]
    SZy_seg = SZy[j+1] - SZy[i]
    SZZ_reg = SZZ_seg + ridge * np.eye(SZZ_seg.shape[0])
    try:
        beta = np.linalg.solve(SZZ_reg, SZy_seg)
    except np.linalg.LinAlgError:
        beta = np.linalg.lstsq(SZZ_reg, SZy_seg, rcond=None)[0]
    SSR = Syy - SZy_seg @ beta
    return SSR, beta

# -------------------- 純構造変化 DP（y ~ Z をK分割） --------------------
def fit_pure_structural_breaks(y, Z, m, h):
    y = np.asarray(y); Z = np.asarray(Z)
    T = len(y); K = m + 1
    if T < K*h:
        raise ValueError("T < (m+1)*h")

    Sy, SZZ, SZy = ols_segment_SSR_precompute(y, Z)

    SSR_mat = np.full((T, T), np.inf)
    for i in range(T):
        for j in range(i + h - 1, T):
            SSR_mat[i, j], _ = segment_SSR(i, j, Sy, SZZ, SZy)

    dp   = np.full((K, T), np.inf)
    prev = np.full((K, T), -1, int)

    for t in range(h-1, T):
        if T - (t+1) < (K-1)*h:
            continue
        dp[0, t] = SSR_mat[0, t]
        prev[0, t] = -1

    for k in range(1, K):
        for t in range((k+1)*h - 1, T):
            if T - (t+1) < (K-1-k)*h:
                continue
            best_val, best_s = np.inf, -1
            s_min, s_max = k*h - 1, t - h
            for s in range(s_min, s_max+1):
                if not np.isfinite(dp[k-1, s]): 
                    continue
                val = dp[k-1, s] + SSR_mat[s+1, t]
                if val < best_val:
                    best_val, best_s = val, s
            dp[k, t] = best_val
            prev[k, t] = best_s

    last_k = K - 1
    best_end = T - 1
    if not np.isfinite(dp[last_k, best_end]):
        raise ValueError("DP failed; adjust m or h.")

    bps = []
    t = best_end
    for k in range(last_k, 0, -1):
        s = prev[k, t]
        bps.append(s)
        t = s
    bps = sorted(bps)

    # 係数（参考）
    coefs = []
    start = 0
    for bp in bps + [T-1]:
        _, beta = segment_SSR(start, bp, Sy, SZZ, SZy)
        coefs.append(beta)
        start = bp + 1

    return bps, coefs, dp[last_k, best_end]

# -------------------- partial：Z をレジームごとにブロック化 --------------------
def build_block_Z(Z, breaks):
    Z = np.asarray(Z)
    T, q = Z.shape
    bps = list(breaks)
    seg_ends   = bps + [T-1]
    seg_starts = [0] + [b+1 for b in bps]
    cols = []
    for s, e in zip(seg_starts, seg_ends):
        Zj = np.zeros_like(Z)
        Zj[s:e+1, :] = Z[s:e+1, :]
        cols.append(Zj)
    Z_block = np.concatenate(cols, axis=1)
    return Z_block

def ssr_given_breaks_partial(y, X, Z, breaks, ridge=1e-12):
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    Zb = build_block_Z(Z, breaks)
    W  = np.concatenate([X, Zb], axis=1)  # [X | Z1 | ... | Z_{m+1}]
    WTW = W.T @ W + ridge * np.eye(W.shape[1])
    WTy = W.T @ y
    theta = np.linalg.lstsq(WTW, WTy, rcond=None)[0]
    resid = y - W @ theta
    SSR = float(resid.T @ resid)
    p = X.shape[1]; q = Z.shape[1]; m = len(breaks)
    beta = theta[:p]
    nus  = [theta[p + j*q : p + (j+1)*q] for j in range(m+1)]
    return SSR, beta, nus

def init_beta_via_pure(y, X, Z, m, h):
    Ztilde = np.concatenate([X, Z], axis=1)
    bps0, coefs0, _ = fit_pure_structural_breaks(y, Ztilde, m=m, h=h)
    p = X.shape[1]; q = Z.shape[1]
    Zb = build_block_Z(Z, bps0)
    nuZ = np.concatenate([c[p:] for c in coefs0])   # 各セグメントのZ係数を連結
    y_tilde = y - Zb @ nuZ
    beta0 = np.linalg.lstsq(X, y_tilde, rcond=None)[0]
    return beta0

def fit_partial_structural_breaks(y, X, Z, m, h, max_iter=10, tol=1e-9):
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    beta = init_beta_via_pure(y, X, Z, m, h)
    prev_SSR = np.inf
    breaks = None
    for it in range(max_iter):
        y_tilde = y - X @ beta
        breaks_A, _, _ = fit_pure_structural_breaks(y_tilde, Z, m=m, h=h)
        SSR, beta_new, nus = ssr_given_breaks_partial(y, X, Z, breaks_A)
        if abs(prev_SSR - SSR) <= tol:
            breaks = breaks_A; beta = beta_new
            break
        prev_SSR = SSR
        beta = beta_new
        breaks = breaks_A

    if breaks is None:
        y_tilde = y - X @ beta
        breaks, _, _ = fit_pure_structural_breaks(y_tilde, Z, m=m, h=h)
        SSR, beta, nus = ssr_given_breaks_partial(y, X, Z, breaks)
    return breaks, beta, nus, SSR
```

* * *

1) HAC（Newey–West）共分散と Wald 検定
==============================

*   回帰  $y = W\theta + u$  に対して  
     $\widehat{\mathrm{Var}}(\hat\theta) = (W'W)^{-1}\, S \,(W'W)^{-1}$   
     $S = \Gamma_0 + \sum_{k=1}^L w_k(\Gamma_k + \Gamma_k')$   
    ここで  $\Gamma_k = \sum_{t=k}^{T-1} u_t u_{t-k}\, w_t w_{t-k}'$ 、  
     $w_k = 1 - \frac{k}{L+1}$ （Bartlett 重み）。
*   線形制約  $R\theta = 0$  に対する **Wald**：  
     $W = (R\hat\theta)'(R \widehat{\mathrm{Var}}(\hat\theta) R')^{-1}(R\hat\theta)$   
    χ²\_{r}（r=制約本数）に漸近的に従う。便宜上 **F 形式** =  $W/r$ 。

**部分構造変化：制約行列  $R$ **

*   H0: 「ν\_1 = ν\_2 = … = ν\_{m+1}」（Z 係数は全期間で同一）
*   パラメータ順を  $[\beta, \nu_1, \nu_2, …, \nu_{m+1}]$  とすると、  
     $R$  は「隣接差分」
    $$
    R = \begin{bmatrix} 0 & I_q & -I_q & 0 & \cdots & 0 \\ 0 & 0 & I_q & -I_q & \cdots & 0 \\ \vdots & & & \ddots & \ddots & \vdots \\ 0 & \cdots & 0 & I_q & -I_q \end{bmatrix}
    $$
    次元は  $(mq) \times [p + (m+1)q]$ 。

```python
# -------------------- Newey–West （回帰用サンドウィッチ中核） --------------------
def newey_west_cov(W, u, L=None):
    """
    Var(theta_hat) = (W'W)^{-1} S (W'W)^{-1}
    S = Γ0 + sum_{k=1..L} w_k (Γk + Γk')
    Γk = sum_{t=k..T-1} u_t u_{t-k} * w_t w_{t-k}'
    """
    W = np.asarray(W); u = np.asarray(u)
    T, k = W.shape
    if L is None:
        # 推奨デフォルト: floor(4*(T/100)^(2/9)) など。ここでは sqrt(T) 系でも可。
        L = int(np.floor(4 * (T / 100.0) ** (2/9))) if T >= 50 else max(1, int(np.sqrt(T)/2))
    XtX_inv = np.linalg.pinv(W.T @ W)  # 安定化
    S = np.zeros((k, k))
    # Γ0
    for t in range(T):
        wt = W[t:t+1, :]
        S += (u[t]**2) * (wt.T @ wt)
    # Γk
    for lag in range(1, L+1):
        weight = 1.0 - lag / (L + 1.0)
        G = np.zeros((k, k))
        for t in range(lag, T):
            wt = W[t:t+1, :]
            ws = W[t-lag:t-lag+1, :]
            G += (u[t] * u[t-lag]) * (wt.T @ ws)
        S += weight * (G + G.T)
    Var = XtX_inv @ S @ XtX_inv
    return Var

def hac_wald(W, y, theta_hat, R, L=None):
    """
    HAC Wald: W = (Rθ)' [R Var(θ) R']^{-1} (Rθ)
    戻り値: (Wald, df=r, F=Wald/r)
    """
    resid = y - W @ theta_hat
    Var = newey_west_cov(W, resid, L=L)
    Rtheta = R @ theta_hat
    RVRT = R @ Var @ R.T
    # 逆が不安定なとき擬似逆行列
    RVRT_inv = np.linalg.pinv(RVRT)
    Wald = float(Rtheta.T @ RVRT_inv @ Rtheta)
    r = R.shape[0]
    F = Wald / r
    return Wald, r, F
```

* * *

2) HAC supF(0 vs m)（partial）
============================

*   **H1**：m ブレーク（β 共通＋ν セグメント別）を `fit_partial_structural_breaks` で推定し、  
     $W = [X \mid Z\_1 \mid \cdots \mid Z\_{m+1}]$  上の OLS パラメータ  $\hat\theta$  を取得
*   **H0**：ν が同一（= ブレーク無し）という**線形制約**  $R\theta=0$  に対して **HAC Wald** を計算
*   返却：**Wald**, df = mq, **F（Wald/mq）** とブレーク位置など

```python
def build_R_no_breaks(p, q, m):
    """
    R: (mq) x (p + (m+1)q)
    制約: ν1 = ν2 = ... = ν_{m+1}  <=>  それぞれの隣接差分が 0
    """
    r = m * q
    k = p + (m+1)*q
    R = np.zeros((r, k))
    row = 0
    for j in range(m):  # j: 0..m-1 で (ν_{j+1} - ν_j) を作る (1-basedを意識すると 2..m+1 - 1..m)
        # 列インデックス（βは飛ばす）
        block_j   = p + j*q
        block_j1  = p + (j+1)*q
        # ν_{j+1} - ν_j
        R[row:row+q, block_j:block_j+q]   = -np.eye(q)
        R[row:row+q, block_j1:block_j1+q] =  np.eye(q)
        row += q
    return R

def supF_0_vs_m_partial_HAC(y, X, Z, m, h, L=None, ridge=1e-12):
    """
    H0: ν一定（ブレークなし） vs H1: mブレーク（partial）
    HAC Wald（F = Wald/(mq)）と推定ブレーク等を返す。
    """
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    T, p = X.shape
    q = Z.shape[1]

    # H1推定
    bps, beta, nus, SSRm = fit_partial_structural_breaks(y, X, Z, m=m, h=h)
    Zb = build_block_Z(Z, bps)
    W  = np.concatenate([X, Zb], axis=1)
    theta = np.concatenate([beta] + nus)

    # R を組み、HAC Wald
    R = build_R_no_breaks(p, q, m)
    Wald, r, F = hac_wald(W, y, theta, R, L=L)
    return {'Wald': Wald, 'df': r, 'F': F, 'breaks': bps, 'beta': beta, 'nus': nus, 'SSRm': SSRm}
```

* * *

3) HAC supF(ℓ+1｜ℓ) 逐次手順（partial）
================================

各 ℓ について：

*   まず `fit_partial_structural_breaks` で ℓ ブレークの最良分割を得る（H0 側）
*   **各セグメント**で「+1 ブレーク」を入れた候補を総当たり（h 制約付き）で探索し、  
    その中で **最良 SSR** を与える candidate を選ぶ（H1 側）
*   H0（ℓ ブレーク）と H1（ℓ+1 ブレーク候補）から **HAC Wald(F)** を計算

```python
def best_one_more_break_in_segment_partial(y, X, Z, breaks_ell, seg_index, h):
    """
    ℓブレーク partition の seg_index 内へ 1ブレーク追加。
    追加後の SSR を最小化する bp を総当たりで探索（簡易実装）。
    """
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    T = len(y)
    bps = list(breaks_ell)
    seg_ends   = bps + [T-1]
    seg_starts = [0] + [b+1 for b in bps]
    s, e = seg_starts[seg_index], seg_ends[seg_index]
    cand_min = s + h - 1
    cand_max = e - h
    best_SSR = np.inf; best_bp = None
    for bp in range(cand_min, cand_max + 1):
        new_breaks = sorted(bps + [bp])
        SSR, _, _ = ssr_given_breaks_partial(y, X, Z, new_breaks)
        if SSR < best_SSR:
            best_SSR, best_bp = SSR, bp
    return best_SSR, best_bp

def sequential_partial_HAC(y, X, Z, max_breaks, h, L=None):
    """
    HAC対応 supF(ℓ+1|ℓ) 逐次手順。
    各ℓで:
      - ℓブレーク partition を反復法で推定（H0）
      - 各セグメントに+1ブレーク候補を入れ最良候補（H1）
      - R: 「νは各セグメントで同一」制約を 'H0 vs H1(1つ増やした)' の差分で構成する代わりに、
            実装簡略上、H1のW=[X|Z_block(ℓ+1)] と θ を用い、
            “全νが等しい” 制約で Wald を計算 → supF(ℓ+1|ℓ) として扱う
    """
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    T, p = X.shape; q = Z.shape[1]

    results = []

    # ℓ=0: ブレークなし
    W0 = np.concatenate([X, Z], axis=1)
    theta0 = np.linalg.lstsq(W0, y, rcond=None)[0]
    res0 = y - W0 @ theta0
    SSR0 = float(res0.T @ res0)

    results.append({'ell': 0, 'breaks_ell': [], 'SSR_ell': SSR0,
                    'supF_ell_plus_1': None, 'candidate_new_break': None, 'segment_index': None})

    for ell in range(0, max_breaks):
        # H0: ℓブレーク推定
        if ell == 0:
            breaks_ell = []
            SSR_ell = SSR0
        else:
            breaks_ell, beta_ell, nus_ell, SSR_ell = fit_partial_structural_breaks(y, X, Z, m=ell, h=h)

        # +1 の候補探索
        seg_ends   = breaks_ell + [T-1]
        seg_starts = [0] + [b+1 for b in breaks_ell]

        best_SSR_cand = np.inf; best_bp = None; best_seg = None
        for seg_idx in range(len(seg_starts)):
            SSR_cand, bp_cand = best_one_more_break_in_segment_partial(y, X, Z, breaks_ell, seg_idx, h)
            if bp_cand is None:
                continue
            if SSR_cand < best_SSR_cand:
                best_SSR_cand, best_bp, best_seg = SSR_cand, bp_cand, seg_idx

        if best_bp is None:
            F_val = None
        else:
            # H1: ℓ+1 ブレークモデルを組んで HAC Wald (R: ν全等式) を評価
            bps1 = sorted(breaks_ell + [best_bp])
            Zb1 = build_block_Z(Z, bps1)
            W1  = np.concatenate([X, Zb1], axis=1)
            theta1 = np.linalg.lstsq(W1, y, rcond=None)[0]
            R1 = build_R_no_breaks(p, q, len(bps1))
            Wald, r, F_val = hac_wald(W1, y, theta1, R1, L=L)

        results.append({'ell': ell, 'breaks_ell': breaks_ell, 'SSR_ell': SSR_ell,
                        'supF_ell_plus_1': F_val, 'candidate_new_break': best_bp, 'segment_index': best_seg})
    return results
```

* * *

4) UDmax / WDmax（HAC）
=====================

*   **UDmax**：m = 1..M での supF(0 vs m)（HAC）の**最大値**
*   **WDmax**：同じだが、m ごとに**重み  $w_m$ ** を掛けて最大化（重みは引数で指定、デフォルトは全て 1.0）

```python
def udmax_wdmax_partial_HAC(y, X, Z, M, h, L=None, weights=None):
    """
    m=1..M について supF(0 vs m)（HAC）を計算し、
    UDmax = max_m F_m,  WDmax = max_m (w_m * F_m) を返す。
    """
    if weights is None:
        weights = {m: 1.0 for m in range(1, M+1)}
    vals = {}
    for m in range(1, M+1):
        out = supF_0_vs_m_partial_HAC(y, X, Z, m=m, h=h, L=L)
        vals[m] = out['F']
    UDmax = max(vals.values()) if len(vals) else None
    WDmax = max((weights.get(m, 1.0) * vals[m] for m in vals)) if len(vals) else None
    return {'UDmax': UDmax, 'WDmax': WDmax, 'by_m': vals}
```

* * *

5) ブレーク日の信頼区間（近傍プロフィール法の近似）
===========================

厳密には論文の漸近分布やブートストラップを使いますが、  
**実務的な近似**として：

*   推定されたブレーク  $\hat T_i$  の近傍で、**そのブレークのみ**を動かし（他は固定）、
*   各候補 b について **制約付き最小 SSR** を計算
*   **LR 近似**：
    $$
    LR(b) = \frac{SSR(b) - SSR_{\min}}{\widehat{\sigma}^2}
    $$
    を、適当な χ²\_q または F\_{q,df2} の閾値に照らし、  
     $LR(b) \le c$  を満たす b の集合を CI とする。  
    （ $\widehat{\sigma}^2 = SSR_{\min}/df2$  を近似的に使用）

```python
def break_ci_profile(y, X, Z, breaks, which, h, alpha=0.05, use_F=True):
    """
    'breaks[which]' の近傍で、そのブレーク位置だけ動かし（他は固定）、
    制約付き最小SSR(b) をプロファイルし、近似的CIを返す。

    use_F=True の場合、
      LR(b) = (SSR(b) - SSR_min) / (SSR_min / df2)
      として F_{q, df2} の (1-alpha) 分位 c を閾値にすれば、
      LR(b) <= c を満たす b の範囲がCIの近似（df2 = T - p - (m+1)q）。

    ★注意：分位点cは標準のF分布に依存します。ここでは c を関数引数で与える運用を想定し、
            コードでは c を返さず、“LRプロファイル”そのものを返します。
    """
    y = np.asarray(y); X = np.asarray(X); Z = np.asarray(Z)
    T, p = X.shape; q = Z.shape[1]
    m = len(breaks)
    assert 0 <= which < m, "which は既存ブレークのインデックス"

    # まず unrestricted (fix other breaks) での最小SSR
    SSR_min, _, _ = ssr_given_breaks_partial(y, X, Z, breaks)

    # 探索可能範囲：隣のブレークと h の制約を守る
    left  = (breaks[which-1] + h) if which > 0 else (h-1)
    right = (breaks[which+1] - h) if which < m-1 else (T - 1 - h)

    prof = []
    df2 = T - p - (m+1)*q
    sigma2 = SSR_min / max(df2, 1)

    for b in range(left, right + 1):
        if b == breaks[which]:
            LR = 0.0
        else:
            bps = breaks.copy()
            bps[which] = b
            bps.sort()
            SSR_b, _, _ = ssr_given_breaks_partial(y, X, Z, bps)
            if use_F:
                LR = (SSR_b - SSR_min) / max(sigma2, 1e-12)   # 近似的F比
            else:
                LR = (SSR_b - SSR_min)                        # 近似的LR差
        prof.append((b, LR))

    # prof: list of (break_pos, LR_value)
    # ここで、ユーザが F_{q,df2;1-alpha} などの閾値 c を設定して、
    # [b: LR(b) <= c] の最小-最大を信頼区間として採用できます。
    return {'profile': prof, 'df2': df2, 'sigma2': sigma2, 'left': left, 'right': right}
```

> **使い方（CI）**
> 
> 1.  既に推定した `breaks` を与える。
> 2.  `break_ci_profile` が返す `profile` から、例えば `c = scipy.stats.f.ppf(1-alpha, q, df2)` を閾値として、  
>     `[(b, LR) for (b, LR) in profile if LR <= c]` の b の最小と最大を CI（近似）とする。
>     

* * *

6) 使い方サンプル（最小）
==============

```python
# ダミーデータ：β共通、νは3レジーム
np.random.seed(1)
T = 350
p, q = 2, 1
X = np.c_[np.ones(T), np.random.randn(T)]
Z = np.random.randn(T, q)
beta_true = np.array([0.5, -0.3])
breaks_true = [130, 240]
nus_true = [np.array([0.8]), np.array([2.0]), np.array([-1.2])]
y = np.empty(T)
start = 0
for bp, nu in zip(breaks_true + [T-1], nus_true):
    sl = slice(start, bp+1)
    y[sl] = X[sl] @ beta_true + Z[sl] @ nu + 0.2*np.random.randn(sl.stop - sl.start)
    start = bp+1

h = 20

# HAC supF(0 vs m)
out2 = supF_0_vs_m_partial_HAC(y, X, Z, m=2, h=h, L=None)
print("HAC supF(0 vs 2): F =", out2['F'], " breaks:", out2['breaks'])

# HAC sequential
seq = sequential_partial_HAC(y, X, Z, max_breaks=4, h=h, L=None)
for r in seq:
    print(r['ell'], "breaks:", r['breaks_ell'], " supF(ell+1|ell):", r['supF_ell_plus_1'],
          " cand:", r['candidate_new_break'])

# UDmax / WDmax
udw = udmax_wdmax_partial_HAC(y, X, Z, M=4, h=h, L=None)
print("UDmax:", udw['UDmax'], " WDmax:", udw['WDmax'])

# CI（例：最初のブレークの近傍プロファイル）
# まず m=2 推定：
bps, beta_hat, nus_hat, SSR = fit_partial_structural_breaks(y, X, Z, m=2, h=h)
ci_info = break_ci_profile(y, X, Z, bps, which=0, h=h, alpha=0.05, use_F=True)
# ここで scipy 等で c=F_{q,df2;1-alpha} を取り、profile から閾値以下の範囲を取る。
# 例: 
# from scipy.stats import f
# c = f.ppf(0.95, q, max(ci_info['df2'],1))
# CI = [b for b,LR in ci_info['profile'] if LR <= c]; (min(CI), max(CI))
```

* * *

メモ・拡張
-----

*   ここでは **HAC（NW）を素直に実装**し、**Wald を F=χ²/r 形式**にしています。  
    Bai–Perron の厳密なロバスト検定はケース分け（系列相関・異分散）やトリミングの影響があり、  
    **臨界値は通常の F 分布ではなく**論文付属の数値表を使います。  
    本コードは **統計量の計算**までをカバーし、採否は **外部の臨界値**で判定してください。
*   `sequential_partial_HAC` では、各 ℓ の **最良候補**を返します。  
    実運用では、`supF_ell_plus_1` を臨界値と比較し、**有意なら** ℓ→ℓ+1 に進みます。
*   CI は実務では **ブートストラップ**や論文の**漸近分布**に基づく法が望ましいですが、  
    ここでは**近傍プロファイル**での**近似 CI**を提供しました（軽量・実装簡単）。

必要なら、

*   **トリミング率 ε を明示指定**して探索範囲をハードに制約する版、
*   **HAC のラグ L の自動選択（Andrews 型）**、
*   **ブートストラップ CI（残差・WBS など）**  
    にも拡張できます。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)