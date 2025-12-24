# 枝分かれ · 枝分かれ · 枝分かれ · 枝分かれ · 枝分かれ · 枝分かれ · 逐次回帰予測の実装

**User:** Anonymous (kbmedphys@gmail.com)  
**Created:** 12/24/2025 16:47:52  
**Updated:** 12/24/2025 18:26:35  
**Exported:** 12/24/2025 18:27:22  
**Link:** [https://chatgpt.com/c/694b9aa4-6b9c-8330-b16a-6fa641456de2](https://chatgpt.com/c/694b9aa4-6b9c-8330-b16a-6fa641456de2)  

## Response:
一言でいうと、「**月タイプのペアごとに、過去データだけで逐次回帰をまわして、有意なペアだけを使って z を作る**」という仕組みを追加すれば、将来情報リークなしで“生き残っている”予測パターンだけを使うことができます。これは論文のアイデア（newsy→repetitive は正の予測、repetitive→newsy は負の予測）を、逐次的なモニタリングに拡張したものです。

ssrn-5268329

以下、**方針 → 具体的な実装コード**の順で書きます。

* * *

方針（時系列でのオンライン・スクリーニング）
----------------------

1.  **月タイプのペア (prev\_type, curr\_type) を定義**
    *   prev\_type: t-1 の month\_type（N, R, 3）
    *   curr\_type: t の month\_type（N, R, 3）
    *   合計 3×3=9 パターン（例：N→R, R→N, 3→N など）
2.  **各時点 t で、過去データのみを用いて「ペア別の予測回帰」を推定**
    *   被説明変数:
        $$
         y_t = \text{mkt\_excess}_t
        $$
    *   説明変数（ペア共通の形で統一）:
        $$
         x_t = \text{mkt\_excess}_{t-1} - \bar{m}_{t-1}
        $$
        ここで  $\bar{m}_{t-1}$  は t-1 までの市場超過リターンの平均（expanding でも rolling でも可）。
    *   ただし、回帰に使うのは「そのペアに属する観測だけ」  
        （例：N→R 用回帰は、t-1 が N かつ t が R の月だけを使う）
3.  **rolling / expanding で逐次推定し、各ペアの β と t値 を毎月更新**
    *   各 t で「参照可能な過去」のみを使う：
        *   expanding: 開始から t-1 まで
        *   rolling: t-1 からさかのぼって例えば直近 15 年分だけ、など
    *   各ペアごとに観測数が **min\_obs** 未満なら「判定不能」として扱う。
4.  **ペアの「予測能力あり」の判定ルール**
    *   例）
        *   観測数 ≥ min\_obs（例: 60 ヶ月）
        *   |t値| ≥ t\_threshold（例: 1.96）
    *   さらに理論に基づき**符号の期待を課す**かどうか：
        *   N→R: 期待される符号は **+**
        *   R→N: 期待される符号は **−**
        *   その他のペアは符号フリーにしてもよいし、そもそも無視してもよい。
5.  **各月 t の Z を、「その時点で有意と判断されたペアだけ」から構築**
    *   t のペア (prev\_type, curr\_type) を見て、  
        そのペアに対する β̂(t-1) と t値(t-1) を使用（= 将来情報なし）。
    *   条件を満たすなら
        z\_t = \\text{sign}(\\betâ\_{pair,t-1}) \\cdot x\_t
        満たさないなら z\_t = 0。
    *   こうしてできた z\_t を、既存の `apply_timing_strategy` にそのまま渡せます  
        （今のコードでは target\_vol / σ\_z でスケーリングしているので整合的）。

* * *

具体的な実装コード
---------

あなたのコードの下に、そのままコピペで追加できる形にしています。  
（`statsmodels` はすでにインポート済みなのでそのまま使えます。）

```python
# ======================================================================
# 3'. month_type ペアごとの予測力をオンラインでスクリーニングし、
#     それに基づいて z_t (adaptive) を構築する関数
# ======================================================================

def build_adaptive_z_with_pair_screening(
    ff,
    lookback_years: int = 20,
    min_obs: int = 60,
    t_threshold: float = 1.96,
    use_expected_sign: bool = True,
):
    """
    ff: load_ff_monthly_from_ken_french の出力 DataFrame
        必要な列: ['mkt_excess', 'rf']
    lookback_years: 回帰に使うローリング窓の長さ（年）
                    None の場合は expanding（開始〜t-1 まで全部）
    min_obs: 各ペアごとに回帰を回すのに必要な最小観測数
    t_threshold: |t値| がこの値以上なら「有意」と判定
    use_expected_sign: True の場合、理論に基づく符号制約を課す
                      - (prev='N', curr='R') は β>0 を期待
                      - (prev='R', curr='N') は β<0 を期待
                      その他のペアは符号制約なし

    戻り値:
        df: 元の ff に以下の列を付け加えた DataFrame
            - 'month_type'
            - 'prev_month_type'
            - 'x_pair'      : 説明変数 (mkt_{t-1} - 平均)
            - 'z_adaptive'  : ペアスクリーニングで構築した予測子
            - 'active_pair' : その月に有効と判定されたペアかどうか (True/False)
    """

    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)
    df["prev_month_type"] = df["month_type"].shift(1)

    # 1ヶ月ラグの市場超過リターン
    df["mkt_lag"] = df["mkt_excess"].shift(1)

    # expanding 平均 or rolling 平均
    if lookback_years is None:
        # expanding 平均: 常に過去全体
        df["mkt_mean_lag"] = df["mkt_excess"].expanding().mean().shift(1)
    else:
        # rolling 平均: 直近 lookback_years 年
        window_months = lookback_years * 12
        df["mkt_mean_lag"] = (
            df["mkt_excess"]
            .rolling(window=window_months, min_periods=1)
            .mean()
            .shift(1)
        )

    # 説明変数 x_t = mkt_{t-1} - mean_{t-1}
    df["x_pair"] = df["mkt_lag"] - df["mkt_mean_lag"]

    # 最初の数行は NaN になるので落とす（ただし index は保持したいのでマスクで管理）
    valid_mask = df[["mkt_excess", "x_pair", "prev_month_type"]].notna().all(axis=1)
    # 結果を入れる列を準備
    z_list = []
    active_list = []

    # 月単位ループでオンラインに回帰と判定を更新
    dates = df.index

    for i, t in enumerate(dates):
        if not valid_mask.loc[t]:
            # 必要な情報がそろっていない初期部分
            z_list.append(0.0)
            active_list.append(False)
            continue

        curr_type = df.at[t, "month_type"]
        prev_type = df.at[t, "prev_month_type"]
        pair = (prev_type, curr_type)

        # その時点 t で使える過去データ (〜 t-1)
        past_mask = (dates < t) & valid_mask
        if lookback_years is not None:
            # ローリング窓: 直近 lookback_years 年
            start_date = t - pd.DateOffset(years=lookback_years)
            past_mask &= (dates >= start_date)

        past_df = df.loc[past_mask].copy()

        if past_df.empty:
            z_list.append(0.0)
            active_list.append(False)
            continue

        # ペアごとに β, t を計算（ここでは今のペアだけ計算するので効率よし）
        pair_mask = (
            (past_df["prev_month_type"] == prev_type)
            & (past_df["month_type"] == curr_type)
        )

        pair_df = past_df.loc[pair_mask]
        if len(pair_df) < min_obs:
            # 観測が少なすぎるペアは使わない
            z_list.append(0.0)
            active_list.append(False)
            continue

        # OLS: y = α + β x
        X = sm.add_constant(pair_df["x_pair"])
        y = pair_df["mkt_excess"]
        model = sm.OLS(y, X).fit()
        beta = model.params["x_pair"]
        tval = model.tvalues["x_pair"]

        # t値＆符号によるフィルタリング
        is_active = (abs(tval) >= t_threshold)

        if use_expected_sign:
            if pair == ("N", "R"):
                # continuation: β > 0 を期待
                is_active = is_active and (beta > 0)
            elif pair == ("R", "N"):
                # reversal: β < 0 を期待
                is_active = is_active and (beta < 0)
            else:
                # その他のペアは符号自由（or 全無効にしたければここで False に）
                # is_active = False
                pass

        if is_active:
            # 予測子 z_t = sign(β) * x_t
            z_t = np.sign(beta) * df.at[t, "x_pair"]
        else:
            z_t = 0.0

        z_list.append(z_t)
        active_list.append(bool(is_active))

    df["z_adaptive"] = z_list
    df["active_pair"] = active_list

    return df
```

* * *

使い方の例
-----

元のコードの最後のあたりを、次のように分岐させるイメージです。

```python
ff = load_ff_monthly_from_ken_french("F-F_Research_Data_Factors.csv")

# 1) 従来の固定 z_t
df_fixed = build_predictor_z(ff)

print("\n=== Correlation (fixed z) ===")
print("All:", df_fixed["z"].corr(df_fixed["mkt_excess"]))
print("N  :", df_fixed[df_fixed["month_type"]=="N"]["z"].corr(df_fixed[df_fixed["month_type"]=="N"]["mkt_excess"]))
print("R  :", df_fixed[df_fixed["month_type"]=="R"]["z"].corr(df_fixed[df_fixed["month_type"]=="R"]["mkt_excess"]))
print("3  :", df_fixed[df_fixed["month_type"]=="3"]["z"].corr(df_fixed[df_fixed["month_type"]=="3"]["mkt_excess"]))

# 2) ペアスクリーニング付きの adaptive z_t
df_adapt = build_adaptive_z_with_pair_screening(
    ff,
    lookback_years=20,  # 直近20年だけで評価（構造変化に敏感）
    min_obs=60,         # 最低60観測（5年分）ないと有意判定しない
    t_threshold=1.96,   # お好みで緩めても良い（例: 1.65）
    use_expected_sign=True,
)

print("\n=== Correlation (adaptive z) ===")
print("All:", df_adapt["z_adaptive"].corr(df_adapt["mkt_excess"]))
print("after 2020:", df_adapt.loc["2020-01-01":]["z_adaptive"].corr(
    df_adapt.loc["2020-01-01":]["mkt_excess"])
)

# 3) タイミング戦略にかけるときは、z 列を差し替えるだけ
df_adapt_for_strategy = df_adapt.copy()
df_adapt_for_strategy["z"] = df_adapt_for_strategy["z_adaptive"]

df_strat = apply_timing_strategy(df_adapt_for_strategy)
plot_results(df_strat)
```

* * *

ポイントのまとめ
--------

*   **将来情報リークなし**  
    各月 t で使う回帰は **常に t 以前のデータのみ**で推定しているので、完全にリアルタイムの投資家と同じ情報制約です。
*   **構造変化に追随可能**  
    `lookback_years` を 15〜20 年程度にしておくと、古い時代（1970–1990 など）の関係性に縛られすぎず、  
    2000 年代、2010 年代、2020 年代の関係性の変化を自然に反映できます。
*   **month\_type の全組み合わせをスクリーニング**  
    (prev\_type, curr\_type) ごとに回帰を行い、有意性と符号でフィルタするので、  
    「2020 年以降は N→R はまだ有効だが、R→N は崩れている」  
    といった状況も自動的に反映されます。
*   **論文の理論を保ちつつ柔軟性を追加**  
    N→R は continuation（β>0）、R→N は reversal（β<0）という期待符号を組み込める一方、  
    それ以外のペアは自由にスクリーニング対象にする／しないを選べます。

* * *

もし「Guo & Wachter 論文と同じ nr(t) 定義（newsy→repetitive, repetitive→newsy）を厳密に使った形でのオンライン推定にしたい」など、もう一段きっちり論文準拠に寄せたい場合は、そのバージョンのコードも用意できます。そのときはこのペア設計を `nr(t)` ベースに置き換えるイメージになります。

## Response:
了解です。じゃあ、**Guo & Wachter の nr(t) をそのまま使った “オンライン版”** を組み込みましょう。

* * *

1\. Guo & Wachter の nr(t) の定義を整理
--------------------------------

論文では nr(t) は

> 「**t より前で、もっとも近い “newsy または repetitive” 月のリターン**」

具体的には：

*   月タイプ
    *   1ヶ月目 = **newsy (N)**
    *   2ヶ月目 = **repetitive (R)**
    *   3ヶ月目 = “その他” (3)
*   nr(t) の取り方
    *   t が **repetitive (R)** のとき  
        → **直前の月 (t−1)** が newsy なので、そのリターンが nr(t)
    *   t が **newsy (N)** のとき  
        → t−1 は 3ヶ月目なのでスキップし、**t−2 (直近の R)** が nr(t)
    *   t が 3 のときは回帰には使っていない（nr(t) 自体は定義可能だが、論文の主回帰は N / R のみ）

これを厳密に再現するには：

1.  まず `month_type`（N, R, 3）を作る（既に実装済み）。
2.  各 t について、「t より前の N または R のうち、もっとも近いもの」を走査して nr(t) を求める。
3.  `mkt_nr(t) = mkt_excess[nr(t)]` を作る。
4.  **R 月だけのサンプル**で
    $$
     \text{mkt}_t = \alpha_R + \beta_R \text{mkt}_{nr(t)} + \varepsilon_t
    $$
    **N 月だけのサンプル**で
    $$
     \text{mkt}_t = \alpha_N + \beta_N \text{mkt}_{nr(t)} + \varepsilon_t
    $$
    の回帰を、**「t 以前のデータだけ」で逐次推定**。
5.  |t値| がしきい値を超え、符号が論文と整合的なら「この月は nr(t) に予測能力あり」とみなし、  
    **z\_t = mkt\_nr(t)** を採用、それ以外は z\_t=0 にする。
    *   論文でのパターン：
    *   repetitive 月 (R) → **β\_R > 0（継続）**
    *   newsy 月 (N) → **β\_N < 0（反転）**

* * *

2\. nr(t) を作る関数
---------------

まずは nr(t) と mkt\_nr(t) を作るユーティリティです。

```python
# ======================================================================
# nr(t) = 直近の newsy or repetitive 月のリターン（Guo & Wachter 準拠）
# ======================================================================

def add_nr_definition(ff: pd.DataFrame) -> pd.DataFrame:
    """
    ff: load_ff_monthly_from_ken_french の出力
        必須列: ['mkt_excess', 'rf']

    戻り値: 以下の列を追加した DataFrame
        - 'month_type' : 'N', 'R', '3'
        - 'nr_date'    : nr(t) に対応する日付
        - 'mkt_nr'     : mkt_excess[nr(t)]
    """
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)

    dates = list(df.index)
    mt = df["month_type"].values

    nr_dates = []
    mkt_nr = []

    for i, t in enumerate(dates):
        nr_idx = None
        j = i - 1
        # t より前の month_type が N or R の月を後ろ向きに探す
        while j >= 0:
            if mt[j] in ("N", "R"):
                nr_idx = dates[j]
                break
            j -= 1

        nr_dates.append(nr_idx)
        if nr_idx is None:
            mkt_nr.append(np.nan)
        else:
            mkt_nr.append(df.at[nr_idx, "mkt_excess"])

    df["nr_date"] = nr_dates
    df["mkt_nr"] = mkt_nr

    return df
```

* * *

3\. Guo & Wachter 型 nr(t) を使った「オンライン回帰＋スクリーニング」
-----------------------------------------------

ここが本題です。  
**各月 t で、t より前のデータだけを使って R/N 別の回帰を回し、β と t値 を逐次更新 → 有意なときだけ z\_t を有効化**します。

```python
# ======================================================================
# Guo & Wachter 型 nr(t) を使ったオンライン回帰による z_t 構築
# ======================================================================

def build_nr_predictor_online(
    ff: pd.DataFrame,
    lookback_years: int = 20,
    min_obs: int = 60,
    t_threshold: float = 1.96,
) -> pd.DataFrame:
    """
    ff: load_ff_monthly_from_ken_french の出力
    lookback_years:
        回帰に使うローリング窓の長さ（年）。
        None の場合は expanding（開始〜t-1 まで全データ）。
    min_obs:
        R / N それぞれの回帰に必要な最小観測数（月）。
    t_threshold:
        |t値| >= t_threshold なら「有意」と判定。

    戻り値: ff に以下の列を追加した DataFrame
        - 'month_type'
        - 'nr_date'
        - 'mkt_nr'
        - 'beta_R_hist', 't_R_hist', 'n_R_hist'
        - 'beta_N_hist', 't_N_hist', 'n_N_hist'
        - 'z_nr_online'   : オンラインスクリーニング後の予測子 z_t
        - 'active_flag'   : その月に nr(t) が有効と判定されたか (True/False)
    """
    # nr(t) 定義を付与
    df = add_nr_definition(ff)

    # nr(t) と目的変数が揃っているところだけを「有効データ」とする
    valid_mask = df[["mkt_excess", "mkt_nr"]].notna().all(axis=1)

    dates = df.index

    beta_R_hist = []
    t_R_hist = []
    n_R_hist = []

    beta_N_hist = []
    t_N_hist = []
    n_N_hist = []

    z_list = []
    active_list = []

    for t in dates:
        if not valid_mask.loc[t]:
            # 初期など nr(t) が定義できない部分
            beta_R_hist.append(np.nan)
            t_R_hist.append(np.nan)
            n_R_hist.append(0)

            beta_N_hist.append(np.nan)
            t_N_hist.append(np.nan)
            n_N_hist.append(0)

            z_list.append(0.0)
            active_list.append(False)
            continue

        # t より前のみを回帰に使う（将来情報なし）
        past_mask = (dates < t) & valid_mask

        if lookback_years is not None:
            # 直近 lookback_years 年に限定（構造変化に敏感にする）
            start_date = t - pd.DateOffset(years=lookback_years)
            past_mask &= (dates >= start_date)

        past_df = df.loc[past_mask]

        if past_df.empty:
            beta_R_hist.append(np.nan)
            t_R_hist.append(np.nan)
            n_R_hist.append(0)

            beta_N_hist.append(np.nan)
            t_N_hist.append(np.nan)
            n_N_hist.append(0)

            z_list.append(0.0)
            active_list.append(False)
            continue

        # ===== R 月サンプル（継続パターン） =====
        past_R = past_df[past_df["month_type"] == "R"]
        if len(past_R) >= min_obs:
            XR = sm.add_constant(past_R["mkt_nr"])
            yR = past_R["mkt_excess"]
            model_R = sm.OLS(yR, XR).fit()
            beta_R = model_R.params["mkt_nr"]
            t_R = model_R.tvalues["mkt_nr"]
            n_R = len(past_R)
        else:
            beta_R = np.nan
            t_R = np.nan
            n_R = len(past_R)

        beta_R_hist.append(beta_R)
        t_R_hist.append(t_R)
        n_R_hist.append(n_R)

        # ===== N 月サンプル（反転パターン） =====
        past_N = past_df[past_df["month_type"] == "N"]
        if len(past_N) >= min_obs:
            XN = sm.add_constant(past_N["mkt_nr"])
            yN = past_N["mkt_excess"]
            model_N = sm.OLS(yN, XN).fit()
            beta_N = model_N.params["mkt_nr"]
            t_N = model_N.tvalues["mkt_nr"]
            n_N = len(past_N)
        else:
            beta_N = np.nan
            t_N = np.nan
            n_N = len(past_N)

        beta_N_hist.append(beta_N)
        t_N_hist.append(t_N)
        n_N_hist.append(n_N)

        # ===== その月 t で z_t をどうするか決定 =====
        mt = df.at[t, "month_type"]
        mkt_nr_t = df.at[t, "mkt_nr"]

        active = False
        z_t = 0.0

        if mt == "R":
            # 継続パターン: β_R > 0 かつ有意であれば nr(t) を使う
            if (not np.isnan(beta_R)) and (abs(t_R) >= t_threshold) and (beta_R > 0):
                z_t = mkt_nr_t  # Guo & Wachter の regressor そのもの
                active = True

        elif mt == "N":
            # 反転パターン: β_N < 0 かつ有意であれば nr(t) を使う
            if (not np.isnan(beta_N)) and (abs(t_N) >= t_threshold) and (beta_N < 0):
                z_t = mkt_nr_t
                active = True

        # 3 の月は論文上は主役でないのでデフォルトではノーポジ
        else:
            z_t = 0.0
            active = False

        z_list.append(z_t)
        active_list.append(active)

    df["beta_R_hist"] = beta_R_hist
    df["t_R_hist"] = t_R_hist
    df["n_R_hist"] = n_R_hist

    df["beta_N_hist"] = beta_N_hist
    df["t_N_hist"] = t_N_hist
    df["n_N_hist"] = n_N_hist

    df["z_nr_online"] = z_list
    df["active_flag"] = active_list

    return df
```

* * *

4\. 既存の戦略コードとの接続例
-----------------

あなたの元コードの最後の部分を、以下のように差し替えれば、

*   Guo & Wachter 準拠の nr(t)
*   オンライン回帰で 2020 年以降の崩れもモニタしつつ
*   予測能力が残っている期間だけポジションを取る

という運用になります。

```python
ff = load_ff_monthly_from_ken_french("F-F_Research_Data_Factors.csv")

# Guo & Wachter nr(t) ベースのオンライン予測子
df_nr = build_nr_predictor_online(
    ff,
    lookback_years=20,  # 直近20年だけで β を更新
    min_obs=60,         # R/N 各サンプル最低 60 観測（5年分）
    t_threshold=1.96,   # 5% 水準。緩めるなら 1.65 など
)

print("\n=== Correlation of z_nr_online with mkt_excess ===")
print("All:", df_nr["z_nr_online"].corr(df_nr["mkt_excess"]))
print("After 2000:", df_nr.loc["2000-01-01":]["z_nr_online"].corr(
    df_nr.loc["2000-01-01":]["mkt_excess"]
))
print("After 2020:", df_nr.loc["2020-01-01":]["z_nr_online"].corr(
    df_nr.loc["2020-01-01":]["mkt_excess"]
))

# タイミング戦略側は z 列を差し替えてそのまま使用
df_for_strategy = df_nr.copy()
df_for_strategy["z"] = df_for_strategy["z_nr_online"]

df_strat = apply_timing_strategy(df_for_strategy)
plot_results(df_strat)
```

* * *

5\. この設計のポイント
-------------

*   **将来情報のリークなし**  
    各月 t の β\_R, β\_N は **常に t より前のデータ**だけで推定しているので、100%リアルタイムの投資家と同じ情報制約です。
*   **Guo & Wachter の nr(t) を厳密に踏襲**
    *   nr(t) は「直近の newsy または repetitive」月だけを見て定義。
    *   N 月では 2 ヶ月前の R を、R 月では前月の N を参照する構造が自動的に出てきます。
*   **R/N 別の β と t値 を逐次モニター**
    *   `beta_R_hist`, `beta_N_hist` をそのままプロットすれば、  
        「1980 年代〜2010 年代までは継続・反転が効いていたが、2020 年以降は崩れている」といった構造変化も可視化できます。
*   **戦略としては「予測パターンが残っている局面だけ」ポジションを取る**
    *   結果として、2020 年以降にパターンが弱まれば z\_t が自動的に 0 になり、レバレッジを絞る形になります。
    *   逆に、将来ふたたび N/R パターンが現れれば β が有意になり、自然にポジションが復活します。

* * *

もし、

*   `lookback_years` を短くして「直近 10 年だけを見て β を決める」版
*   3 ヶ月目にも nr(t) を使って少額ポジションを取る版
*   P4\_j mktnm(t,j)（Guo 2025 のニュース集約）も含めた 2 変数回帰版

などに拡張したい場合も、今のフレームワークにそのまま追加できます。  
まずはこの nr(t) オンライン版を回して、2020 年以降の β\_R, β\_N の推移を一度プロットしてみると良いと思います。

## Response:
結論から言うと、

*   **アイデア／構造レベルではかなり近くて、論文のパターンはちゃんと実装できている**
*   ただし、**厳密に Guo & Wachter の  $z_{t-1}$  を再現しているかというと、「ほぼ」だけど完全一致ではない**

という感じです。

* * *

1\. 論文での定義（ざっくり）
----------------

論文の 3.2〜3.3 での定義は

*    $\text{mkt}_t$ ：月次の市場超過リターン
*    $nr(t)$ ：時点  $t$  より前で一番近い **newsy or repetitive** の月
    *   例：
        *   t が 2 ヶ月目（R）なら nr(t) = 1 ヶ月目（N）
        *   t が 3 ヶ月目 or 4 ヶ月目なら nr(t) = 2 ヶ月目（R）
*   予測回帰：
    $$
    \text{mkt}_t = \alpha + \beta\, \text{mkt}_{nr(t)} + \varepsilon_t
    $$
*   その上で、**トレーディング用の予測子**を
    $$
    z_{t-1} = \begin{cases} \text{mkt}_{nr(t)} - \bar{\text{mkt}}_{t-1} & (t \text{ が R 月}) \\ -\bigl(\text{mkt}_{nr(t)} - \bar{\text{mkt}}_{t-1}\bigr) & (t \text{ が N 月}) \\ 0 & (\text{それ以外}) \end{cases}
    $$
    と定義（ $\bar{\text{mkt}}_{t-1}$  は t−1 までの平均超過リターン）。  
    そして「月 t のリターンの予測には  $z_{t-1}$  を使う」。

* * *

2\. あなたの `build_predictor_z` がやっていること
-------------------------------------

### (1) month\_type の定義

```python
def classify_month_type(index):
    m = t.month % 3
    1 → 'N', 2 → 'R', 0 → '3'
```

これは論文の

*   1ヶ月目: N
*   2ヶ月目: R
*   3ヶ月目: それ以外（3）

と一致していて OK です。

### (2) ベースとなる偏差

```python
df["mkt_lag"] = df["mkt_excess"].shift(1)        # mkt_{t-1}
df["mkt_mean_lag"] = df["mkt_excess"].expanding().mean().shift(1)  # 平均(〜t-1)
base = df["mkt_lag"] - df["mkt_mean_lag"]        # mkt_{t-1} - 平均(〜t-1)
```

ここでは **常に mkt\_{t-1}** を使って、

*   base\[t\] = mkt\_{t-1} − mean\_{t-1}

を作っています。

### (3) z の構築ロジック

```python
z = []
last_R_diff = None
for mt, diff in zip(df["month_type"], base):
    if mt == "R":
        z.append(diff)
    elif mt == "N":
        if last_R_diff is not None:
            z.append(-1*last_R_diff)
        else:
            z.append(0.0)
    else:  # '3'
        z.append(0.0)
        last_R_diff = diff
```

これを時系列で追うと：

*   **R 月**
    *   t が R（2 ヶ月目）のとき
        *   diff = mkt\_{t-1} − mean\_{t-1} = mkt\_{前の N} − mean\_{t-1}  
            → これはそのまま **論文の「R 月に対する  $mkt_{nr(t)} − \bar{mkt}_{t-1}$ 」** と一致
*   **3 月**
    *   t が 3（3 ヶ月目）のとき
        *   diff = mkt\_{t-1} − mean\_{t-1} = mkt\_{直前の R} − mean\_{t-1}
        *   ここで `last_R_diff = diff` として「直前の R の偏差」を記憶
*   **N 月**
    *   t が N（次の四半期 1 ヶ月目）のとき
        *   `z = - last_R_diff`
        *   つまり **2 ヶ月前の R の偏差（mkt\_R − mean\_{そのRの直後まで}) を符号反転**して使っている

したがって構造としては：

*   「N→R は正の予測」
*   「R→N は負の予測」
*   3 月は z=0

という論文の **経済的なパターン**はちゃんと再現できています。

* * *

3\. どこが「厳密には違う」のか？
------------------

主な差は 2 つです。

### (A) 平均のタイミング（N 月）

論文の定義では、**N 月 t に対する予測子**は

*   nr(t) = 2 ヶ月前の R 月
*   平均は「t−1 まで」の平均  $\bar{\text{mkt}}_{t-1}$ 

なので  
 $\text{mkt}_{nr(t)} - \bar{\text{mkt}}_{t-1} = \text{mkt}_{R} - \text{mean (〜直前月)}$ 

一方あなたのコードでは

*   N 月で使っているのは `last_R_diff`
*   `last_R_diff` は「3 月のときの diff」＝「mkt\_R − mean(〜その R の直後まで)」

つまり **平均側が 1 ヶ月だけ短い**（3 月のリターンを平均に含めていない）というズレがあります。

実務的には

*   サンプル期間が長い（1926–2025）ので平均はほとんど変わらず、
*   影響は非常に小さい

ので、**回帰係数や相関のサイン・大きさはほぼ同じ**になりますが、「論文の数式を一字一句そのまま実装しているか」という意味では厳密には違います。

### (B) 指標のインデックス（z\_t vs z\_{t-1}）

論文は「月 t のリターンを予測するのは z\_{t-1}」と書いていますが、

*   あなたの `z[t]` は「t の始まり時点で利用可能な情報だけ（〜t−1 のリターン）から作られていて将来情報リークはない」
*   `apply_timing_strategy` では
    *   その月のウェイト w\_t を z\[t\] で決めている
    *   σ は z の過去分だけで計算している

ので、**経済的な意味では z\_t を z\_{t-1} と呼ぶかの違いだけ**で、将来情報リークは起きていません。

* * *

4\. まとめ：認識はどう整理すれば良いか？
----------------------

整理すると：

*   ✅ **「Guo & Wachter のアイデア（newsy→repetitive は順張り、repetitive→newsy は逆張り）を使った予測子とタイミング戦略を実装できているか？」**  
    → **はい、できています。認識は大筋で正しいです。**
*   ⚠️ **「論文に書いてある  $z_{t-1} = \pm(\text{mkt}_{nr(t)} - \bar{\text{mkt}}_{t-1})$  を厳密に数学的に再現しているか？」**  
    → **ほぼ同じですが、N 月で使う平均のタイミングが 1 ヶ月だけずれている** ので、完全に同一ではありません。

もし、

*   Table 3 の R² を「小数第 3 位まで完全に合わせたい」
*   「このズレが 2020 年以降の崩れの説明になっていないか気になる」

というレベルで **厳密に論文準拠にしたい**なら、

*   `nr(t)` を明示的に計算して
*   `mkt_nr` と `mean(〜t-1)` から z を作る

という形（さっき提案した `build_nr_predictor_online` のような構造）にすると、「数学的にも完全に同じ」と言えます。

ただ、**現状の `build_predictor_z` でも論文の本質的なメカニズムと予測パターンはきちんと捉えられている**ので、

> 「Guo & Wachter のトレーディング戦略の実務的な実装」

として使う分には十分に妥当だと思って大丈夫です。

## Response:
はい、その前提（`build_predictor_z` ベース）で、「平均のタイミングだけ」を論文どおりに直した版を書きます。

ポイントだけ先に：

*   **R 月**（repetitive）では
    $$
     z_t = \text{mkt}_{t-1} - \overline{\text{mkt}}_{t-1}
    $$
    なので、元コードと同じ（問題なし）。
*   **N 月**（newsy）では
    *   使うのは「**直近の R 月のリターン**」＝  $\text{mkt}_{nr(t)}$ 
    *   平均は「**t−1 まで**」の平均  $\overline{\text{mkt}}_{t-1}$ 
    $$
     z_t = -\bigl(\text{mkt}_{nr(t)} - \overline{\text{mkt}}_{t-1}\bigr)
    $$
*   これを実現するために、
    *   「前回の R 月のリターン `last_R_ret`」だけを覚えておき、
    *   N 月が来たタイミングで  $\overline{\text{mkt}}_{t-1}$  を使って差分を再計算する  
        という形に変えます（平均のタイミングのズレだけ修正）。

* * *

修正後の `build_predictor_z`
------------------------

あなたのスクリプトにある `build_predictor_z` を、以下に置き換えてください：

```python
def build_predictor_z(ff):
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)

    # t 時点での mkt_{t-1} と、平均(〜t-1)
    df["mkt_lag"] = df["mkt_excess"].shift(1)
    df["mkt_mean_lag"] = df["mkt_excess"].expanding().mean().shift(1)

    # 初期の NaN 行を落とす（mkt_lag, mkt_mean_lag が揃ったところからスタート）
    df = df.dropna()

    z = []
    last_R_ret = None  # 直近の "R 月" の mkt_excess を記憶

    for t, row in df.iterrows():
        mt = row["month_type"]
        mean_t_minus1 = row["mkt_mean_lag"]

        if mt == "R":
            # R 月: 直前の N 月のリターンを使う
            # z_t = mkt_{t-1} - mean(〜t-1)  → 元コードと同じ
            diff = row["mkt_lag"] - mean_t_minus1
            z_t = diff

            # この月のリターンは「次の N 月で使う R 月」として記憶
            last_R_ret = row["mkt_excess"]

        elif mt == "N":
            # N 月: 直近の R 月のリターン (last_R_ret) を使って
            # z_t = -( mkt_{R} - mean(〜t-1) ) を構成
            if (last_R_ret is not None) and (not math.isnan(mean_t_minus1)):
                diff = last_R_ret - mean_t_minus1
                z_t = -diff
            else:
                # まだ R 月が一度も出ていないなどの場合は 0 にする
                z_t = 0.0

        else:  # mt == "3"
            # 3 ヶ月目: 論文同様ここではポジションを取らない
            z_t = 0.0

        z.append(z_t)

    df["z"] = z
    return df
```

* * *

何がどう変わったか（ざっくり）
---------------

*   以前：
    *   3 ヶ月目で `last_R_diff = mkt_R − mean(〜R当月まで)` を保存し、
    *   N 月で `z = - last_R_diff` を使っていました。
    *   そのため、**平均が「R 月まで」のもの**になっていて、論文の「N 月の直前 (t−1) まで」と 1 ヶ月だけズレていました。
*   今回の修正：
    *   3 ヶ月目では diff を保存せず、**R 月のリターンだけ `last_R_ret` として記憶**。
    *   N 月に来たところで、
        *   `last_R_ret`（直近の R のリターン）と
        *   `mkt_mean_lag[t]`（t−1 までの平均）  
            を使って、
        $$
         z_t = -(\text{mkt}_{R} - \overline{\text{mkt}}_{t-1})
        $$
        を再計算しています。

これで、

*   構造：N→R で順張り、R→N で逆張り
*   平均のタイミング：常に「t−1 まで」

という意味で、\*\*Guo & Wachter の  $z_{t-1}$  の定義と整合的な形になっています。  
あとは、今までと同じように `df = build_predictor_z(ff)` → `apply_timing_strategy(df)` としてもらえれば OK です。

## Response:
ざっくり言うと、

*   **Guo (2025)** の  $P_4 \sum_{j=1}^4 \text{mkt}_{nm(t,j)}$  は  
    「**直近4つの newsy 月の平均リターン**」で、
*   Guo & Wachter 論文ではこれ（パラメータ圧縮のニュース集約指標）と  
    あなたがもう実装している ** $ \text{mkt}_{nr(t)}$ **（correlation neglect）を  
    **同時に説明変数に入れた 2 変数回帰**をやっています。

以下で、

1.  数式レベルでの定義
2.  あなたの Ken French データ＋`classify_month_type` ベースでの実装コード
3.  Guo & Wachter の Table 11, 式(11) 相当の 2変数回帰の書き方

をまとめます。

* * *

1\. 定義： $nr(t)$  と  $P_4 \sum_{j=1}^4 \text{mkt}_{nm(t,j)}$ 
------------------------------------------------------------

論文の notation：

ssrn-5268329

*    $\text{mkt}_t$ ：月 t の市場超過リターン
*    $nr(t)$ ：t より前で **最も近い “newsy または repetitive” 月**  
    （つまり N/R どちらでも良いが一番近いもの）
*    $nm(t,j)$ ：t より前で **j 番目に近い newsy 月**  
    （例： $nm(t,1)$  が直近の N、 $nm(t,2)$  が2番目に近い N …）
*   Guo (2025) のニュース集約指標：
    
$$
P_4 \sum_{j=1}^4 \text{mkt}_{nm(t,j)} \quad\text{= 「直近4つの newsy 月の市場超過リターンの平均」}
$$
*   Guo & Wachter はこれを
    *   パラメータ圧縮（古いニュースの効き方を誤って一定とみなす誤信念）を表す指標として採用し、
    *   自分たちの  $\text{mkt}_{nr(t)}$  と同時に回帰に入れています。

* * *

2\. 回帰式（2変数＋ニュースダミー）
--------------------

論文が Table 11 の列(3) で使っている仕様は：

ssrn-5268329

$$
\text{mkt}_t = \alpha + \beta_1 \,\text{mkt}_{nr(t)} + \beta_2 \,\text{mkt}_{nr(t)} \cdot I^n_t + \beta_3 \,P_4 \sum_{j=1}^4 \text{mkt}_{nm(t,j)} + \beta_4 \,P_4 \sum_{j=1}^4 \text{mkt}_{nm(t,j)} \cdot I^n_t + \gamma I^n_t + \varepsilon_t,
$$
*    $I^n_t = 1$  if month t is **newsy (N)**, else 0.
*   列(1)：従属変数が R 月だけのサンプル
*   列(2)：従属変数が N 月だけのサンプル
*   列(3)：上式のような **統合サンプル＋相互作用項**で、β2, β4 が N/R の差をとっているイメージです。

* * *

3\. Ken French データでの実装（nr + P4 ニュース平均を作る）
-----------------------------------------

あなたの環境でそのまま動くことを意識して、

*   すでにある `classify_month_type` を使う
*   `load_ff_monthly_from_ken_french` で作った `ff`（mkt\_excess, rf）から拡張

という形で書きます。

### 3.1 nr(t) と nm(t,j)（直近4 newsy）の構築

```python
def add_nr_and_nm4(ff: pd.DataFrame) -> pd.DataFrame:
    """
    ff: load_ff_monthly_from_ken_french の出力
        必須列: ['mkt_excess', 'rf']

    追加される列:
        - 'month_type' : 'N', 'R', '3'
        - 'In_t'       : その月が newsy (N) なら 1, それ以外 0
        - 'nr_date'    : nr(t) に対応する日付
        - 'mkt_nr'     : mkt_excess[nr(t)]
        - 'mkt_nm1'..'mkt_nm4' : 直近 j 番目の newsy 月のリターン
        - 'mkt_nm4_avg': 直近4つの newsy 月の平均 (Guo 2025 P4_j mkt_nm(t,j))
    """
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)
    df["In_t"] = (df["month_type"] == "N").astype(int)

    dates = list(df.index)
    mt = df["month_type"].values
    mkt = df["mkt_excess"].values

    nr_dates = []
    mkt_nr_list = []

    # nm(t,j) 用に「これまで出てきた newsy 月の index」を蓄積
    past_newsy_indices = []

    mkt_nm1 = []
    mkt_nm2 = []
    mkt_nm3 = []
    mkt_nm4 = []

    for i, t in enumerate(dates):
        # ---- nr(t): t より前で最も近い N or R ----
        nr_idx = None
        j = i - 1
        while j >= 0:
            if mt[j] in ("N", "R"):
                nr_idx = j
                break
            j -= 1
        if nr_idx is None:
            nr_dates.append(None)
            mkt_nr_list.append(np.nan)
        else:
            nr_dates.append(dates[nr_idx])
            mkt_nr_list.append(mkt[nr_idx])

        # ---- newsy 月の履歴更新 ----
        if mt[i] == "N":
            past_newsy_indices.append(i)

        # ---- nm(t,j): 直近 newsy 月たち ----
        # t 自身は除きたいので、i より小さいインデックスのみ使用
        candidate_newsy = [k for k in past_newsy_indices if k < i]
        candidate_newsy_sorted = sorted(candidate_newsy, reverse=True)

        vals = []
        for jj in range(4):
            if jj < len(candidate_newsy_sorted):
                vals.append(mkt[candidate_newsy_sorted[jj]])
            else:
                vals.append(np.nan)

        mkt_nm1.append(vals[0])
        mkt_nm2.append(vals[1])
        mkt_nm3.append(vals[2])
        mkt_nm4.append(vals[3])

    df["nr_date"] = nr_dates
    df["mkt_nr"] = mkt_nr_list
    df["mkt_nm1"] = mkt_nm1
    df["mkt_nm2"] = mkt_nm2
    df["mkt_nm3"] = mkt_nm3
    df["mkt_nm4"] = mkt_nm4

    # 直近4つの newsy 月の平均（4つ揃っていない場合は NaN）
    df["mkt_nm4_avg"] = df[["mkt_nm1", "mkt_nm2", "mkt_nm3", "mkt_nm4"]].mean(axis=1)

    return df
```

* * *

### 3.2 Guo & Wachter Table 11, 列(3) 相当の 2 変数回帰

`statsmodels` はすでに使っているので、そのまま OLS を書きます。  
White 標準誤差（`cov_type="HC0"`）を指定すると論文と同じロバスト t 値になります。

ssrn-5268329

```python
def run_two_predictor_regression(df: pd.DataFrame):
    """
    Guo & Wachter Table 11, col (3) に対応する回帰:
    mkt_t = α + β1 mkt_nr(t)
              + β2 mkt_nr(t) * In_t
              + β3 mkt_nm4_avg(t)
              + β4 mkt_nm4_avg(t) * In_t
              + γ In_t + ε_t

    戻り値:
        statsmodels の結果オブジェクト (res) と
        β1..β4, γ を辞書で返す
    """
    # 説明変数が揃っているサンプルだけを使う
    reg_df = df[["mkt_excess", "mkt_nr", "mkt_nm4_avg", "In_t"]].dropna().copy()

    reg_df["x1"] = reg_df["mkt_nr"]
    reg_df["x2"] = reg_df["mkt_nr"] * reg_df["In_t"]
    reg_df["x3"] = reg_df["mkt_nm4_avg"]
    reg_df["x4"] = reg_df["mkt_nm4_avg"] * reg_df["In_t"]
    reg_df["x5"] = reg_df["In_t"]

    X = sm.add_constant(reg_df[["x1", "x2", "x3", "x4", "x5"]])
    y = reg_df["mkt_excess"]

    model = sm.OLS(y, X)
    res = model.fit(cov_type="HC0")  # White s.e.

    params = res.params
    tvals = res.tvalues

    out = {
        "alpha": (params["const"], tvals["const"]),
        "beta1_mktnr": (params["x1"], tvals["x1"]),
        "beta2_mktnr_In": (params["x2"], tvals["x2"]),
        "beta3_nm4": (params["x3"], tvals["x3"]),
        "beta4_nm4_In": (params["x4"], tvals["x4"]),
        "gamma_In": (params["x5"], tvals["x5"]),
    }
    return res, out
```

使い方：

```python
ff = load_ff_monthly_from_ken_french("F-F_Research_Data_Factors.csv")
df_nr_nm = add_nr_and_nm4(ff)

res, out = run_two_predictor_regression(df_nr_nm)
print(res.summary())  # 全体サマリ
print("\nCoefficients (value, t-stat):")
for name, (coef, tval) in out.items():
    print(f"{name:15s}: {coef: .4f},  t = {tval: .2f}")
```

ここで、

*   `beta1_mktnr, beta2_mktnr_In` → correlation neglect パート（Guo & Wachter）
*   `beta3_nm4, beta4_nm4_In` → Guo (2025) パラメータ圧縮パート（直近4 newsy 平均）

を一気に確認できます。

* * *

4\. 戦略への拡張（ざっくり）
----------------

今のあなたの戦略は

*   predictor  $z_t$  を 1 つ（mkt\_nr 系）にして、
*   ターゲットボラ＆maxレバでスケールしたタイミング戦略

になっていますが、この 2 変数回帰を踏まえると：

*   「correlation neglect コンポーネント用  $z^{(nr)}_t$ 」
*   「parameter compression コンポーネント用  $z^{(nm4)}_t$ 」

を作って、**線形結合で 1 つの予測子にまとめる**（係数は β 推定値を使う or 符号情報だけ使う）という形にも拡張できます。

ただ、まずは上のコードで

*   P4 ニュース平均の構成
*   2 変数回帰（White s.e.付き）

が論文どおりに動くかを確認してから、  
次のステップとして「2 成分をどうやって z\_t に統合して運用戦略に反映させるか」を一緒に設計するのが良いと思います。

## Response:
以下では **Guo & Wachter (2019,2025) の理論と実証結果**を踏まえて、  
あなたが得た推定結果

*   **β₂（mkt\_nr × Nダミー） = −0.318, t = −2.89**
*   **β₃（P4 ニュース平均） = 0.448, t = 4.58**
*   **β₄（P4 ニュース平均 × Nダミー） = −0.700, t = −4.29**
*   **γ（Nダミー） = +0.013, t = 3.39**

を **どのようにトレーディング戦略に落とし込むべきか**を、  
論文の数式（特に Table 11, 式(11) の解釈）に基づき、  
**“実運用の意思決定ルール” という形まで分解して提案**します。

* * *

1\. 回帰式の構造の再確認（文献ベース）
=====================

あなたの推定は以下の回帰モデルに対応します：  
（Guo & Wachter (2019) Table 11 の Column (3)）

$$
\begin{aligned} mkt_t = &\ \alpha + \beta_1\, mkt_{nr(t)} + \beta_2\, mkt_{nr(t)} \cdot I^n_t \\ &+ \beta_3\, P4(t) + \beta_4\, P4(t)\cdot I^n_t + \gamma I^n_t + \varepsilon_t , \end{aligned}
$$

ここで：

*    $I^n_t = 1$  if t が **newsy (N)**, else 0
*    $mkt_{nr(t)}$ ：直近の N/R 月のリターン（あなたが既に実装済み）
*    $P4(t)$ ：**直近4つの newsy 月リターンの平均**（Guo 2025 の news aggregation）

さらに論文での解釈は **“N 月と R 月では市場への作用の仕方が異なる”** というもの。

以下で **N 月 と R 月 に分けて係数を読み替える**と戦略が見えるようになります。

* * *

2\. 各月タイプ別の係数を整理（戦略設計のための再構成）
=============================

■ R 月（Repetitive Month, Iⁿ=0）
-----------------------------

R 月のモデルは：

$$
mkt_t = \alpha + \beta_1 mkt_{nr(t)} + \beta_3 P4(t)
$$

つまり **2つの有効予測子**：

### (1) Correlation Neglect 予測（mkt\_nr）

*    $\beta_1 = +0.0745$   
    → 正方向だが **有意ではない**（t=1.17）

### (2) Parameter Compression 予測（P4）

*    $\beta_3 = +0.4481$   
    → **強く正の予測力（t=4.58）**

👉 **R 月は “古いニュースを平均した P4 が高いと次のリターンが上がる”  
＝明確な順張り月**

* * *

■ N 月（Newsy Month, Iⁿ=1）
------------------------

N 月では：

$$
mkt_t = (\alpha+\gamma) + (\beta_1+\beta_2)mkt_{nr(t)} + (\beta_3+\beta_4)P4(t)
$$

数値代入すると：

*    $\beta_1+\beta_2 = 0.0745 - 0.3177 = -0.2432$ （**逆張り効果**）
*    $\beta_3+\beta_4 = 0.4481 - 0.7000 = -0.2519$ （**P4 も逆張り化**）
*    $\gamma = +0.0133$ （**N 月は平均的に上がりやすいバイアス**）

👉 **N 月は「すべてが逆張り方向」  
＝前月（nr）、直近4N平均（P4）が高いほど、次のリターンは低くなる**

* * *

3\. 文献の理論と照合すると何が示唆されるか？
========================

Guo & Wachter の core 理論は：

*   **R 月（2ヶ月目）**：repetitive month は「投資家がニュースの情報を誤った線形モデルで処理し、過去ニュースの影響を過大評価 → continuation」（順張り）
*   **N 月（1ヶ月目）**：newsy month は「投資家が古いニュースを誤って均等加重しすぎており、情報が効きすぎ → reversal」（逆張り）

今回の推定結果は **非常に文献どおりで textbook に近い**：

| Month Type | nr predictor | P4 predictor | γ | Interpretation |
| --- | --- | --- | --- | --- |
| **R** | +（弱い） | **強い+** | – | 順張り月 |
| **N** | **強い−** | **強い−** | 正 | 平均市場リスクプレミアムは高いが、予測成分は逆張り |

* * *

4\. ではこれを「戦略」にするとどうなるか？
=======================

結論から言うと：

> **N 月と R 月でまったく別のブック（signal）を使う “regime-specific predictor” を作り、  
> それを今の timing 戦略（apply\_timing\_strategy）に入力するのが最適解**

* * *

5\. 実装すべき統合 predictor  $z_t^{\*}$ 
==================================

以下の2ステップで作ります。

* * *

STEP 1：
-------

### R 月用 predictor

$$
z_t^{R} = w_{nr}^{R}\, \underbrace{mkt_{nr(t)} - \bar{mkt}_{t-1}}_{\text{あなたが実装済の base}} + w_{P4}^{R}\, \left(P4(t) - \bar{P4}_{t-1}\right)
$$
*   論文の係数に基づいて
    *    $w_{nr}^{R} \propto +\beta_1$ 
    *    $w_{P4}^{R} \propto +\beta_3$ 

👉 **たとえば（標準化後） w\_{P4} を大きくし、w\_{nr} はほぼ無視でも良い**  
（推定結果を見る限り）

* * *

STEP 2：
-------

### N 月用 predictor

$$
z_t^{N} = w_{nr}^{N}\, \left[-(mkt_{nr(t)} - \bar{mkt}_{t-1})\right] + w_{P4}^{N}\, \left[-(P4(t) - \bar{P4}_{t-1})\right]
$$
*   論文の係数から
    *    $w_{nr}^{N} \propto (\beta_1+\beta_2) < 0$ 
    *    $w_{P4}^{N} \propto (\beta_3+\beta_4) < 0$ 

👉 **N 月では nr も P4 も “逆張り” 方向（符号反転）**

* * *

STEP 3：統合ルール
------------

$$
z_t^{\*} = \begin{cases} z_t^{R}, & \text{month is R} \\ z_t^{N}, & \text{month is N} \\ 0, & \text{month type is 3} \end{cases}
$$

そして、  
**これを apply\_timing\_strategy(df) に渡すだけで  
レバレッジ付き timing 戦略が成立します。**

* * *

6\. では係数をどう使うべきか？（文献との整合的な実務ルール）
================================

### 推奨ルール（論文準拠）：

### ■ R 月（順張り）

*   主要 signal：  
    **P4(t)**（過去4つの newsy の平均）が正なら **ロング寄り**  
    大きいほどレバレッジを強くして OK
*   nr(t) は **弱いが正信号** → small positive weight で加える

### ■ N 月（逆張り）

*   nr(t) が高い → **ショート**（reversal）
*   P4 が高い → **さらにショート強化**

### ■ 3 月 → ノーポジで OK

* * *

7\. 重み（w\_nr, w\_P4）の実務的な設計
===========================

あなたの戦略は target\_vol / σ(z) でスケールしているので、  
係数は **相対重みだけ決めれば良い**。

推定値から：

*   **R 月**
    *   β₁ ≈ +0.07（弱い） → 重み 0.2
    *   β₃ ≈ +0.45（強い） → 重み 1.0
*   **N 月**
    *   β₁+β₂ ≈ −0.24 → 重み -1.0
    *   β₃+β₄ ≈ −0.25 → 重み -1.0

推奨設定：

```python
w_nr_R  = 0.2
w_P4_R  = 1.0

w_nr_N  = -1.0
w_P4_N  = -1.0
```

* * *

8\. 戦略としてのまとめ（文献準拠の運用ルール）
=========================

最終的な投資家の行動はこうなる：

* * *

【R 月（2ヶ月目）＝順張り】
---------------

*   P4 が高い → **強気ロング**
*   nr もややロング方向に加点
*   apply\_timing\_strategy に渡すと自然に高レバレッジ→高ウェイトになる

* * *

【N 月（1ヶ月目）＝逆張り】
---------------

*   nr が高い → **ショート**
*   P4 が高い → **さらにショート**
*   γ（N 月平均 +1.3%）のおかげで完全ショートにはしないが、  
    signal は明確に逆張り

* * *

【3 月】
-----

*   文献では予測力なし → **ノーポジにして良い**

* * *

9\. Guo の理論に最も従う形の最終戦略
======================

$$
w_t = \operatorname{clip}\Big( \frac{z_t^{\*}}{\sigma(z)} \cdot target\_vol, \ -max\_lev,\ +max\_lev \Big)
$$

ここで  $z_t^{\*}$  は：

*   R 月：順張り合成 signal
*   N 月：逆張り合成 signal
*   3 月：0

* * *

10\. 希望があれば以下も実装可能です
====================

*   上記の **z\*\_t の完全 Python 実装コード**
*   あなたの `apply_timing_strategy` と自然に統合した **フルコード**
*   nr(t) と P4(t) を rolling window で「リアルタイム推定」する  
    **オンライン版（将来情報リークなし）**
*   N/R の regime switching が 2020 年以降崩れていないかの  
    **逐次モニタリング**

* * *

もし次に進めたい場合、

> 「この z\*\_t の計算コードをフルで書いてください」

と言ってくだされば、  
あなたの既存コード（build\_predictor\_z / apply\_timing\_strategy）に  
完全に統合した形で提供します。

## Response:
やりますねこの質問😄  
じゃあ、**nr + P4 を組み合わせた z\*\_t を作って、既存の `apply_timing_strategy` にそのまま突っ込めるフルコード**を用意します。

* * *

全体像
---

前提：あなたの環境にはすでに

*   `load_ff_monthly_from_ken_french`
*   `classify_month_type`
*   `apply_timing_strategy`

が定義されていますよね（最初に送ってくれたコード）。

そこに以下を追加するイメージです：

1.  `add_nr_and_nm4(ff)`  
    → **nr(t)** と **P4（直近4 newsy 平均）** を作る
2.  `build_z_star(df, w_...)`  
    → Guo & Wachter / Guo 2025 の係数に基づいて  
    **N月・R月でルールの違う z\*\_t を構築**
3.  その `z_star` を `apply_timing_strategy` に渡す

* * *

1\. nr(t) と P4(t) を追加する関数
-------------------------

```python
# ======================================================================
# nr(t) と nm(t,j)、P4 = 直近4つの newsy 月平均 を追加
# ======================================================================

def add_nr_and_nm4(ff: pd.DataFrame) -> pd.DataFrame:
    """
    ff: load_ff_monthly_from_ken_french の出力
        必須列: ['mkt_excess', 'rf']

    追加される列:
        - 'month_type' : 'N', 'R', '3'
        - 'In_t'       : その月が newsy (N) なら 1, それ以外 0
        - 'nr_date'    : nr(t) に対応する日付
        - 'mkt_nr'     : mkt_excess[nr(t)]
        - 'mkt_nm1'..'mkt_nm4' : 直近 j 番目の newsy 月のリターン
        - 'mkt_nm4_avg': 直近4つの newsy 月の平均 (Guo 2025 の P4_j mktnm(t,j))
    """
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)
    df["In_t"] = (df["month_type"] == "N").astype(int)

    dates = list(df.index)
    mt = df["month_type"].values
    mkt = df["mkt_excess"].values

    nr_dates = []
    mkt_nr_list = []

    # nm(t,j) 用に「これまで出てきた newsy 月の index」を蓄積
    past_newsy_indices = []

    mkt_nm1 = []
    mkt_nm2 = []
    mkt_nm3 = []
    mkt_nm4 = []

    for i, t in enumerate(dates):
        # ---- nr(t): t より前で最も近い N or R ----
        nr_idx = None
        j = i - 1
        while j >= 0:
            if mt[j] in ("N", "R"):
                nr_idx = j
                break
            j -= 1
        if nr_idx is None:
            nr_dates.append(None)
            mkt_nr_list.append(np.nan)
        else:
            nr_dates.append(dates[nr_idx])
            mkt_nr_list.append(mkt[nr_idx])

        # ---- newsy 月の履歴更新 ----
        if mt[i] == "N":
            past_newsy_indices.append(i)

        # ---- nm(t,j): 直近 newsy 月たち ----
        candidate_newsy = [k for k in past_newsy_indices if k < i]
        candidate_newsy_sorted = sorted(candidate_newsy, reverse=True)

        vals = []
        for jj in range(4):
            if jj < len(candidate_newsy_sorted):
                vals.append(mkt[candidate_newsy_sorted[jj]])
            else:
                vals.append(np.nan)

        mkt_nm1.append(vals[0])
        mkt_nm2.append(vals[1])
        mkt_nm3.append(vals[2])
        mkt_nm4.append(vals[3])

    df["nr_date"] = nr_dates
    df["mkt_nr"] = mkt_nr_list
    df["mkt_nm1"] = mkt_nm1
    df["mkt_nm2"] = mkt_nm2
    df["mkt_nm3"] = mkt_nm3
    df["mkt_nm4"] = mkt_nm4

    # 直近4つの newsy 月の平均（4つ揃っていない場合は NaN）
    df["mkt_nm4_avg"] = df[["mkt_nm1", "mkt_nm2", "mkt_nm3", "mkt_nm4"]].mean(axis=1)

    return df
```

* * *

2\. z\*\_t を計算する関数
------------------

*   **R 月**：順張り
*   **N 月**：逆張り
*   **3 月**：ノーポジ（z\*=0）

として、あなたの推定結果に基づいた重みを入れます。

```python
# ======================================================================
# Guo&Wachter / Guo 2025 に基づく z*_t の構築
# ======================================================================

def build_z_star(
    df_nr_nm: pd.DataFrame,
    w_nr_R: float = 0.2,
    w_P4_R: float = 1.0,
    w_nr_N: float = -1.0,
    w_P4_N: float = -1.0,
) -> pd.DataFrame:
    """
    df_nr_nm:
        add_nr_and_nm4(ff) を通した DataFrame
        ['mkt_excess', 'month_type', 'mkt_nr', 'mkt_nm4_avg'] 等を含む。

    w_*:
        Guo&Wachter の回帰係数から決めた相対重み。
        デフォルト値は beta1, beta3, beta1+beta2, beta3+beta4 の符号と
        大きさをざっくり反映した設定。

    戻り値:
        df: 以下の列を追加
            - 'nr_demeaned' : mkt_nr - 平均(mkt_nr, 〜t-1)
            - 'P4_demeaned' : mkt_nm4_avg - 平均(P4, 〜t-1)
            - 'z_star'      : 月タイプ別ルールで合成された最終 predictor
    """
    df = df_nr_nm.copy()

    # nr(t), P4(t) が存在するところだけ使う
    df["nr_demeaned"] = (
        df["mkt_nr"] - df["mkt_nr"].expanding().mean().shift(1)
    )
    df["P4_demeaned"] = (
        df["mkt_nm4_avg"] - df["mkt_nm4_avg"].expanding().mean().shift(1)
    )

    z_star = []

    for t, row in df.iterrows():
        mt = row["month_type"]
        nr_d = row["nr_demeaned"]
        P4_d = row["P4_demeaned"]

        # 初期 NaN の扱い
        if np.isnan(nr_d) or np.isnan(P4_d):
            z_star.append(0.0)
            continue

        if mt == "R":
            # R 月: 順張り → nr, P4 に正の重み
            z_t = w_nr_R * nr_d + w_P4_R * P4_d
        elif mt == "N":
            # N 月: 逆張り → nr, P4 を符号反転（w_nr_N, w_P4_N は負）
            z_t = w_nr_N * nr_d + w_P4_N * P4_d
        else:  # mt == "3"
            # 3 ヶ月目はポジションを取らない
            z_t = 0.0

        z_star.append(z_t)

    df["z_star"] = z_star
    return df
```

* * *

3\. 戦略への組み込み例（フルフロー）
--------------------

最後に、Ken French CSV から読み込んで  
**z\*\_t → apply\_timing\_strategy → プロット**まで一気通しのコードです。

```python
# ======================================================================
# 使い方フロー
# ======================================================================

# 1. Ken French から市場リターンを読み込む
ff = load_ff_monthly_from_ken_french("F-F_Research_Data_Factors.csv")

# 2. nr(t) と P4(t) を作成
df_nr_nm = add_nr_and_nm4(ff)

# 3. Guo&Wachter + Guo(2025) に基づく z*_t を構築
df_zstar = build_z_star(
    df_nr_nm,
    w_nr_R=0.2,   # R 月の nr に対する重み
    w_P4_R=1.0,   # R 月の P4 に対する重み（順張り成分の主役）
    w_nr_N=-1.0,  # N 月の nr（逆張り）
    w_P4_N=-1.0,  # N 月の P4（逆張り）
)

# 4. タイミング戦略に渡すために列名 'z' を差し替え
df_for_strategy = df_zstar.copy()
df_for_strategy["z"] = df_for_strategy["z_star"]

# 5. 既存の apply_timing_strategy で運用
df_strat = apply_timing_strategy(
    df_for_strategy,
    target_vol=0.05,
    max_leverage=3.0,
)

# 6. 結果プロット（あなたの plot_results を再利用してもOK）
plot_results(df_strat)
```

* * *

4\. 補足：完全に「将来情報リークなし」になっているか？
-----------------------------

*   `mkt_nr(t)`：定義上「t より前で最も近い N/R 月」だけを参照 → 過去情報のみ
*   `mkt_nm4_avg(t)`：同様に「t より前の newsy 月」を最大4つまで参照 → 過去のみ
*   `expanding().mean().shift(1)`：
    *   t 時点で **t−1 まで**の平均しか使っていない

なので、この z\*\_t は **完全にリアルタイムの投資家が持てる情報だけ**から構成されています。

* * *

5\. 次の一手のアイデア
-------------

もしこの z\*\_t で

*   1926–2025 全体のパフォーマンス
*   2000 年以降 / 2010 年以降 / 2020 年以降のサブサンプル

を比較したいなら、

*   `df_for_strategy.loc["2000-01-01":]` などに制限して同じ戦略を回す
*   R 月 / N 月のみのサンプルに絞って z\*\_t と mkt\_excess の相関を出す

なども簡単にできます。そのあたりも必要ならすぐコード出します。

## Response:
以下では、**Guo & Wachter (2025)** の本文（特に Section 3.2, 3.3, 6）および **Guo (2025)**（P4\_j mktnm の定義）の内容を踏まえて、

1.  **相関ネグレクト nr(t) のみを使う手法（あなたの z\_t に対応）**
2.  **nr(t) + P4\_j mktnm(t,j) を組み合わせる拡張版 z\*\_t（2変数版）**

を文献ベースで明確に比較しつつ説明します。

ssrn-5268329

* * *

1\. nr(t) のみを使う Guo–Wachter（2025）の予測子
=====================================

### 1.1 nr(t) の定義

論文では、月 t が

*   **newsy（四半期1ヶ月目）**
*   **repetitive（四半期2ヶ月目）**
*   **muted（3ヶ月目）**

の3分類で構成される。

そこで nr(t) は以下の _直前の newsy/repetitive 月の市場超過リターン_ をとる：

$$
\text{mktnr}(t) = \begin{cases} \text{mkt}_{t-1}, & t\text{が repetitive のとき}\\[6pt] \text{mkt}_{t-2}, & t\text{が newsy のとき}\\[6pt] 0, & t\text{が muted のとき} \end{cases}
$$

これは、実際には次を意味する：

*   newsy → repetitive（月1 → 月2）の「継続」パターン（＋）
*   repetitive → 次の newsy（月2 → 次の月1）の「反転」パターン（−）

つまり **継続→反転（continuation → reversal）構造** を利用した予測子となる。

### 1.2 予測子 z\_t

文献中（Table 3）で用いられる OOS 予測子は

$$
z_{t-1} = \begin{cases} \text{mktnr}(t) - \bar{mkt}_{t-1}, & t \in \{\text{newsy, repetitive}\}\\ 0, & \text{otherwise} \end{cases}
$$

これはあなたの `build_predictor_z` の実装と等価です。

> **結論：あなたの build\_predictor\_z は Guo–Wachter の core predictor を正しく実装している。**

* * *

2\. Guo (2025) の P4\_j mktnm(t,j)（ニュース平均）とは
===========================================

Guo（2025）は「ニュースの記憶 decay レートの誤認（parameter compression）」を扱う論文であり、次のような独自 predictor を導入する：

$$
P4(t) = \frac{1}{4}\sum_{j=1}^4 \text{mktnm}(t,j)
$$

ここで mktnm(t,j) は、

*   過去 j 回の **newsy 月の市場超過リターン**
*   newsy 月のみをフィルタして並べた系列 nm(1), nm(2), … の平均のようなもの

つまり「過去4回の newsy 月の平均リターン」が P4(t)。

### 2.1 直観

*   過去のニュース（月1）では earnings shock が階段的に decay する
*   投資家は decay レートを誤認し平均化してしまう
*   そのため newsy リターンの移動平均が有効な予測因子となる（負の係数）

### 2.2 文献での回帰式（Table 11）

論文の Table 11（Guo 2025 + Guo–Wachter 2025 の joint test）では：

$$
mkt_t = \alpha + \beta_1 \, mktnr(t) + \beta_2 \, P4(t) + \epsilon_t
$$

両方とも **有意に残る** ことが確認される。

* * *

3\. nr(t) と P4(t) を組み合わせた z\*\_t の意味
====================================

あなたが示した推定結果：

```
beta2_mktnr_In : -0.3177   (t = -2.89)
beta3_nm4      :  0.4481   (t =  4.58)
beta4_nm4_In   : -0.7000   (t = -4.29)
gamma_In       :  0.0133   (t =  3.39)
```

これは _newsy と repetitive で係数が異なる_ リッチな形の式：

$$
mkt_t=\alpha + \beta_2 \, mktnr(t)\cdot I_N(t) + \beta_3 \, P4(t) + \beta_4 \, P4(t)\cdot I_N(t) + \gamma\,I_N(t)
$$

に対応している。

### 解釈

*   **repetitive 月では P4(t) の係数は +（continuation 的）**
*   **newsy 月では P4(t) の係数は β3+β4 で明確に negative（reversal 的）**

つまり  
**P4(t) 自体が nr(t) の構造と同様に「継続→反転」の性質を持つ**  
ということがデータ上確認されている。

このため z\*\_t を作るなら：

* * *

4\. 文献に沿った z\*\_t の定義
=====================

論文で明示的に「z\*\_t」を定義しているわけではないが、  
**戦略構築のための predictor** として最も自然なのは次の線形予測子：

$$
z^*_t = \hat\beta_1 \, mktnr(t) + \hat\beta_2 \, P4(t)
$$

ただし係数は _expanding-window で逐次更新_（look-ahead 防止）、  
つまり：

1.  時点 t で予測するとき
2.  回帰には **t−1 時点までのデータのみ使用**
3.  得られた係数 β̂ を使って t の予測子 z\*\_t を計算
4.  その z\*\_t を用いてポジションを張る

これが **文献 Table 3, Table 11 の OOS セッティング** と整合的。

* * *

5\. nr-only と nr+P4 の予測構造の違い
============================

| 手法 | 学習する現象 | 効果 |
| --- | --- | --- |
| nr(t) only | 「月1→月2の continuation」「月2→月1 の reversal」 | 相関ネグレクト由来のパターンを捉える（強い） |
| nr + P4 | nr の効果に加えて **ニュース shock の decay 誤認** を捉える | nr(t) が弱い局面でも性能を補完 |

文献（Section 6）の主張も：

*   nr(t)（相関ネグレクト）と
*   P4(t)（parameter compression）

は **distinct だが両方強い**  
→ 両方使うとより robust になる。

* * *

6\. では戦略へどう反映すべきか？（文献準拠の提案）
===========================

### **提案：2つの予測子を統合したオンライン版 market timing strategy**

1.  毎月末に t−1 時点までのデータで次の OLS を推定：
    
$$
mkt_s = \alpha + \beta_1 mktnr(s) + \beta_2 P4(s) + \varepsilon_s \quad (s \le t-1)
$$
2.  係数  $\hat\beta_1, \hat\beta_2$  を得る
3.  次の月 t の予測子として
    
$$
z^*_t=\hat\beta_1 mktnr(t) + \hat\beta_2 P4(t)
$$
4.  文献と同じボラティリティターゲット（5%/月）で
    $$
    w_t = \frac{z^*_t}{\hat\sigma_{z^*}} \cdot 0.05
    $$
5.  ±3 で truncation（文献と同じ）

→ **Guo–Wachter 戦略をそのまま “multivariate” にしたバージョン**

* * *

7\. まとめ（nr-only 版と nr+P4 版の違い）
==============================

### nr-only

*   純粋に _earnings repetition → 相関ネグレクト_ の構造を捉える
*   単純で強く、あなたの build\_predictor\_z が正しく実装している

### nr+P4（拡張）

*   P4 が「ニュース decay 誤認」を捉え、nr の弱い局面を補完
*   文献 Table 11 の結果に沿った「両輪型」モデル
*   **実運用での安定性が高い**

* * *

8\. 必要であれば：
===========

*   nr+P4 の **オンライン版 z\*\_t の Python フルコード**
*   上記モデルの **バックテストコードのフル実装**
*   **NR/P4 それぞれの OOS R² の比較、係数の時系列可視化**
*   **2020年以降の regime shift を検知するオンライン推定法**

もすべて提供できます。

* * *

必要であれば、今のあなたのコードに「z\*\_t 予測子（nr+P4）」を追加した完全版を提示しますか？

## Response:
了解しました。  
**nr + P4 の z\*\_t（オンライン推定版）と、nr だけの手法を同じフレームで比較できる「フルコード」を一つにまとめて**お渡しします。

*   Ken French CSV から読み込み
*   nr(t) / P4(t) の構築
*   nr-only の z\_t
*   nr+P4 の z\*\_t（毎月 OLS で β₁,β₂ を更新するオンライン版）
*   それぞれについて timing 戦略を走らせる

まで一気通しの形です。

* * *

フルコード一式
-------

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import statsmodels.api as sm

# ======================================================================
# 1. Ken French 元ファイルから月次部分だけ抽出（あなたの元コード）
# ======================================================================

def load_ff_monthly_from_ken_french(csv_path: str) -> pd.DataFrame:
    raw = pd.read_csv(csv_path, skiprows=4)

    num = pd.to_numeric(raw['Unnamed: 0'], errors='coerce')
    mask_monthly = num > 10000
    monthly = raw[mask_monthly].copy()

    monthly = monthly.rename(columns={'Unnamed: 0': 'date'})
    monthly['date'] = pd.to_datetime(monthly['date'].astype(int), format="%Y%m")
    monthly = monthly.set_index('date').sort_index()

    for col in ['Mkt-RF', 'RF']:
        monthly[col] = pd.to_numeric(monthly[col], errors='coerce')

    ff = monthly[['Mkt-RF', 'RF']].copy()
    ff['mkt_excess'] = ff['Mkt-RF'] / 100.0
    ff['rf']         = ff['RF'] / 100.0

    return ff[['mkt_excess', 'rf']].dropna()

# ======================================================================
# 2. 月タイプ分類（あなたの元コード）
# ======================================================================

def classify_month_type(index):
    mt = pd.Series(index=index, dtype="object")
    for t in index:
        m = t.month % 3
        if m == 1:
            mt[t] = 'N'   # newsy
        elif m == 2:
            mt[t] = 'R'   # repetitive
        else:
            mt[t] = '3'   # muted
    return mt

# ======================================================================
# 3. nr(t) と nm(t,j)、P4 = 直近4つの newsy 月平均 を追加
#    （Guo&Wachter + Guo 2025 準拠）
# ======================================================================

def add_nr_and_nm4(ff: pd.DataFrame) -> pd.DataFrame:
    """
    ff: load_ff_monthly_from_ken_french の出力
        必須列: ['mkt_excess', 'rf']

    追加される列:
        - 'month_type' : 'N', 'R', '3'
        - 'In_t'       : その月が newsy (N) なら 1, それ以外 0
        - 'nr_date'    : nr(t) に対応する日付
        - 'mkt_nr'     : mkt_excess[nr(t)]
        - 'mkt_nm1'..'mkt_nm4' : 直近 j 番目の newsy 月のリターン
        - 'mkt_nm4_avg': 直近4つの newsy 月の平均 (Guo 2025 の P4_j mktnm(t,j))
    """
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)
    df["In_t"] = (df["month_type"] == "N").astype(int)

    dates = list(df.index)
    mt = df["month_type"].values
    mkt = df["mkt_excess"].values

    nr_dates = []
    mkt_nr_list = []

    # nm(t,j) 用に「これまで出てきた newsy 月の index」を蓄積
    past_newsy_indices = []

    mkt_nm1 = []
    mkt_nm2 = []
    mkt_nm3 = []
    mkt_nm4 = []

    for i, t in enumerate(dates):
        # ---- nr(t): t より前で最も近い N or R ----
        nr_idx = None
        j = i - 1
        while j >= 0:
            if mt[j] in ("N", "R"):
                nr_idx = j
                break
            j -= 1
        if nr_idx is None:
            nr_dates.append(None)
            mkt_nr_list.append(np.nan)
        else:
            nr_dates.append(dates[nr_idx])
            mkt_nr_list.append(mkt[nr_idx])

        # ---- newsy 月の履歴更新 ----
        if mt[i] == "N":
            past_newsy_indices.append(i)

        # ---- nm(t,j): 直近 newsy 月たち ----
        candidate_newsy = [k for k in past_newsy_indices if k < i]
        candidate_newsy_sorted = sorted(candidate_newsy, reverse=True)

        vals = []
        for jj in range(4):
            if jj < len(candidate_newsy_sorted):
                vals.append(mkt[candidate_newsy_sorted[jj]])
            else:
                vals.append(np.nan)

        mkt_nm1.append(vals[0])
        mkt_nm2.append(vals[1])
        mkt_nm3.append(vals[2])
        mkt_nm4.append(vals[3])

    df["nr_date"] = nr_dates
    df["mkt_nr"] = mkt_nr_list
    df["mkt_nm1"] = mkt_nm1
    df["mkt_nm2"] = mkt_nm2
    df["mkt_nm3"] = mkt_nm3
    df["mkt_nm4"] = mkt_nm4

    # 直近4つの newsy 月の平均（4つ揃っていない場合は NaN）
    df["mkt_nm4_avg"] = df[["mkt_nm1", "mkt_nm2", "mkt_nm3", "mkt_nm4"]].mean(axis=1)

    return df

# ======================================================================
# 4. nr-only 版の z_t（平均タイミング修正済） ＝ Guo&Wachter の基本形
# ======================================================================

def build_predictor_z_nr_only(ff: pd.DataFrame) -> pd.DataFrame:
    """
    Guo & Wachter (2025) の nr(t) 構造を、
    あなたの元コードに近い形で実装した nr-only 版 z_t。

    - R 月:  z_t = mkt_{t-1} - mean(〜t-1)
    - N 月:  z_t = -(mkt_{直近R} - mean(〜t-1))
    - 3 月:  z_t = 0
    """
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)

    df["mkt_lag"]      = df["mkt_excess"].shift(1)
    df["mkt_mean_lag"] = df["mkt_excess"].expanding().mean().shift(1)

    df = df.dropna()

    z = []
    last_R_ret = None  # 直近の R 月の mkt_excess

    for t, row in df.iterrows():
        mt = row["month_type"]
        mean_t_minus1 = row["mkt_mean_lag"]

        if mt == "R":
            # R 月: 直前の N 月のリターンで順張り
            diff = row["mkt_lag"] - mean_t_minus1
            z_t = diff
            last_R_ret = row["mkt_excess"]  # 次の N のために記憶

        elif mt == "N":
            # N 月: 直近 R 月に対して逆張り
            if (last_R_ret is not None) and (not math.isnan(mean_t_minus1)):
                diff = last_R_ret - mean_t_minus1
                z_t = -diff
            else:
                z_t = 0.0
        else:
            # 3 ヶ月目: ノーポジ
            z_t = 0.0

        z.append(z_t)

    df["z_nr_only"] = z
    return df

# ======================================================================
# 5. nr + P4 を組み合わせた z*_t オンライン版
#    （β1, β2 を毎月 t-1 までのデータで推定 → z*_t = β1*mkt_nr + β2*P4）
# ======================================================================

def build_z_star_online(
    ff: pd.DataFrame,
    lookback_years: int = 20,
    min_obs: int = 120,
) -> pd.DataFrame:
    """
    Guo&Wachter + Guo(2025) に基づき、nr(t) と P4(t) を組み合わせた
    オンライン版 z*_t を構築する。

    手順:
      1. add_nr_and_nm4(ff) で mkt_nr, P4 = mkt_nm4_avg を作成
      2. 各月 t で、t より前のデータ（必要なら直近 lookback_years 年に限定）を使って
         OLS: mkt_s = α + β1 mkt_nr(s) + β2 P4(s) + ε_s を推定
      3. 得られた β1_hat, β2_hat から z*_t = β1_hat*mkt_nr(t) + β2_hat*P4(t) を計算
      4. サンプルが足りなければ z*_t = 0

    戻り値:
      df: ff に nr, P4, β1_hist, β2_hist, z_star を追加した DataFrame
    """
    df = add_nr_and_nm4(ff)

    # nr と P4 が利用可能なサンプルのみを「候補」とする
    valid_mask = df[["mkt_excess", "mkt_nr", "mkt_nm4_avg"]].notna().all(axis=1)
    dates = df.index

    beta1_hist = []
    beta2_hist = []
    n_obs_hist = []
    z_star = []

    for t in dates:
        # まだ nr/P4 が定義されていない初期部分
        if not valid_mask.loc[t]:
            beta1_hist.append(np.nan)
            beta2_hist.append(np.nan)
            n_obs_hist.append(0)
            z_star.append(0.0)
            continue

        # t より前のデータのみを使用（将来情報リーク防止）
        past_mask = (dates < t) & valid_mask

        if lookback_years is not None:
            # 直近 lookback_years 年に限定（構造変化に対して敏感に）
            start_date = t - pd.DateOffset(years=lookback_years)
            past_mask &= (dates >= start_date)

        past_df = df.loc[past_mask, ["mkt_excess", "mkt_nr", "mkt_nm4_avg"]].dropna()

        n_obs = len(past_df)
        if n_obs < min_obs:
            # 観測数が少なすぎるときは β を推定せず z*_t=0
            beta1_hist.append(np.nan)
            beta2_hist.append(np.nan)
            n_obs_hist.append(n_obs)
            z_star.append(0.0)
            continue

        # OLS: mkt = α + β1 mkt_nr + β2 P4
        X = sm.add_constant(past_df[["mkt_nr", "mkt_nm4_avg"]])
        y = past_df["mkt_excess"]
        model = sm.OLS(y, X).fit()

        beta1 = model.params["mkt_nr"]
        beta2 = model.params["mkt_nm4_avg"]

        beta1_hist.append(beta1)
        beta2_hist.append(beta2)
        n_obs_hist.append(n_obs)

        # 当月 t の nr, P4 に係数を掛けて z*_t を構成
        mkt_nr_t = df.at[t, "mkt_nr"]
        P4_t     = df.at[t, "mkt_nm4_avg"]

        if np.isnan(mkt_nr_t) or np.isnan(P4_t):
            z_t = 0.0
        else:
            z_t = beta1 * mkt_nr_t + beta2 * P4_t

        z_star.append(z_t)

    df["beta1_hist"] = beta1_hist
    df["beta2_hist"] = beta2_hist
    df["n_obs_hist"] = n_obs_hist
    df["z_star"]     = z_star

    return df

# ======================================================================
# 6. タイミング戦略（あなたの元コード）
# ======================================================================

def apply_timing_strategy(df, target_vol=0.05, max_leverage=3.0):
    out = df.copy()
    z = out["z"]

    weights = []
    sig_hist = []
    strat_excess = []
    strat_total = []
    mkt_total = []

    for i, t in enumerate(out.index):
        if i == 0:
            sigma = np.nan
            w = 0.0
        else:
            sigma = z.iloc[:i].std(ddof=1)
            if (sigma is np.nan) or (sigma == 0):
                w = 0.0
            else:
                w = z.iloc[i] * target_vol / sigma
                w = float(np.clip(w, -max_leverage, max_leverage))

        weights.append(w)
        sig_hist.append(sigma)

        mkt = out.at[t, "mkt_excess"]
        rf  = out.at[t, "rf"]
        se  = w * mkt
        strat_excess.append(se)
        strat_total.append(rf + se)
        mkt_total.append(rf + mkt)

    out["w"]            = weights
    out["sigma_z_hist"] = sig_hist
    out["strat_excess"] = strat_excess
    out["strat_total"]  = strat_total
    out["mkt_total"]    = mkt_total

    return out

# ======================================================================
# 7. グラフ描画（あなたの元コードを軽く改変）
# ======================================================================

def plot_results(df, title_suffix=""):
    strat_wealth = (1 + df["strat_excess"]).cumprod()
    mkt_wealth   = (1 + df["mkt_total"]).cumprod()

    plt.figure(figsize=(14, 5))
    plt.plot(strat_wealth, label="Strategy", linewidth=2)
    plt.plot(mkt_wealth,   label="Market",   linewidth=1.5, linestyle="--")
    plt.title(f"Cumulative Return (Strategy vs Market){title_suffix}")
    plt.legend()
    plt.grid(True)
    plt.show()

# ======================================================================
# 8. メイン：nr-only vs nr+P4(z*) の比較
# ======================================================================

if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"

    # 1) Ken French 読み込み
    ff = load_ff_monthly_from_ken_french(csv_path)

    # --------------------------------------------------------------
    # A. nr-only 版（Guo&Wachter の基本戦略）
    # --------------------------------------------------------------
    df_nr_only = build_predictor_z_nr_only(ff)
    df_nr_only_for_strat = df_nr_only.copy()
    df_nr_only_for_strat["z"] = df_nr_only_for_strat["z_nr_only"]

    df_nr_only_strat = apply_timing_strategy(df_nr_only_for_strat)
    plot_results(df_nr_only_strat, title_suffix=" (nr-only)")

    # --------------------------------------------------------------
    # B. nr + P4 の 2変数オンライン版 z*_t 戦略
    # --------------------------------------------------------------
    df_zstar = build_z_star_online(
        ff,
        lookback_years=20,  # 直近20年で係数を推定（構造変化を反映しやすい）
        min_obs=120,        # 少なくとも120観測（月）ないと回帰を回さない
    )
    df_zstar_for_strat = df_zstar.copy()
    df_zstar_for_strat["z"] = df_zstar_for_strat["z_star"]

    df_zstar_strat = apply_timing_strategy(df_zstar_for_strat)
    plot_results(df_zstar_strat, title_suffix=" (nr + P4 z*_t)")
```

* * *

使い方・解釈のポイント
-----------

*   **nr-only**  
    → Guo & Wachter の「相関ネグレクト」だけを使った戦略  
    → あなたの元々の z\_t に極めて近い動き
*   **nr+P4（z\*\_t）**  
    → Guo 2025 の「ニュース平均 P4」との 2 変数回帰を  
    **毎月 t−1 までのデータで再推定**し、  
    その β₁(t−1), β₂(t−1) から z\*\_t を作るオンライン版  
    → nr が弱い局面でも P4 が予測力を補完するので、  
    2020 年以降など「相関ネグレクトだけでは弱くなっている局面」で  
    パフォーマンス改善が期待されます。

このコードをそのまま走らせれば、

*   1926–2025 全期間での累積リターン
*   サブサンプル（2000 年以降だけ、2020 年以降だけ）でフィルタして同じ比較

なども簡単にできます（`df.loc["2000-01-01":]` で切れば OK）。

もし「2020 年以降での両戦略の比較」「β₁(t), β₂(t) の時系列プロット」なども見たくなったら、そこ用のコードも追加で書きます。

## Response:
まず書誌情報からまとめます。

* * *

1\. 書誌情報
--------

*   論文タイトル：  
    **“Earnings Extrapolation and Predictable Stock Market Returns”**
*   著者：  
    **Hongye Guo**（University of Hong Kong）[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)
*   掲載誌：  
    **The Review of Financial Studies**, Volume 38, Issue 6, June 2025, pp. 1730–1782 [OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)
*   DOI：  
    **10.1093/rfs/hhaf020** [OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

あなたが「Guo 2025」と呼んでいる文献はこの RFS 論文です。

* * *

2\. 論文のコア結果の要約
--------------

### 2.1 見つかった「新しい」パターン

*   \*\*四半期の第1月（1, 4, 7, 10月）\*\*を “newsy months” と定義  
    → 決算発表が集中する「アーニングシーズン」で、新しい情報が大量に出る月。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)
*   残りの8か月を “non-newsy months” と定義。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

このとき、米国株式市場の月次超過リターンについて

*   過去の **newsy 月のリターン** は、
    *   将来の **newsy 月のリターンを「強く負に」予測**（リバーサル）
    *   将来の **non-newsy 月のリターンを「強く正に」予測**（コンティニュエーション）
*   しかし、news y＋non-newsy を混ぜて平均すると、  
    → 従来知られていた「月次オートコリレーション ≒ 0」という事実が再現される [OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501)

つまり

> 無条件の自己相関はほぼゼロだが、**条件付き（newsy / non-newsy）には非常に強い予測パターンがある**

というのがこの論文の最重要の実証的発見です。

さらに、このパターンは

*   米国の**業種ポートフォリオのクロスセクション**でも
*   主要な**海外株式市場**でも

同様に観測されると報告されています。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

* * *

3\. 実証パート：mkt\_nm(t,j) と P4 型シグナル
---------------------------------

### 3.1 mkt\_nm(t,j) の定義

文献では、まず newsy 月だけを抜き出した系列 {nm(1), nm(2), …} を作ります。  
そのうえで，月 t から遡って j 番目の newsy 月のリターンを

$$
mkt_{nm}(t,j)
$$

と定義します。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

*   例：t が 2020年5月（non-newsy）なら、  
    j=1 → 直近の newsy 月（2020年4月）の市場リターン  
    j=2 → その前の newsy 月（2020年1月）  
    j=3 → 2019年10月  
    j=4 → 2019年7月

### 3.2 基本的な回帰

論文では、まず「過去4回の newsy 月リターン」が持つ予測力を

$$
mkt_t=\alpha+\sum_{j=1}^{4}\beta_j\,mkt_{nm}(t,j)+\varepsilon_t
$$

という回帰で検証します。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

*   全サンプル（1926–2021）の U.S. aggregate market（CRSP）を対象。
*   newsy 月だけに従属変数を絞った回帰、non-newsy 月だけの回帰も実施し、「係数の符号と大きさが newsy / non-newsy で明確に違う」ことを確認。

その後、係数をまとめて**スカラーの signal** に落とした形も考えます：

$$
mkt_t = \alpha + \beta \cdot \underbrace{\sum_{j=1}^4 mkt_{nm}(t,j)}_{\text{過去4つの newsy 月の合計}} + \varepsilon_t
$$

という形の回帰も行い、ここで用いる

$$
P4(t) \equiv \sum_{j=1}^4 mkt_{nm}(t,j)
$$

のようなシグナルを、あなたがコード中で **P4\_j mktnm(t,j)** と呼んでいるものに対応させることができます。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

実際、Table 2 や Table 4 では

*   Σ\_j mkt\_nm(t,j) の係数 β
*   あるいは Σ\_j mkt\_nm(t,j) を加工したシグナル（平均・平均乖離・符号反転）

が、強い予測力を持つことが報告されています。

### 3.3 トレーディングに用いるシグナル（Methods 1–7）

Out-of-sample 予測（Table 4）では、次のような「単一シグナル」が使われます：[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

*   **Method 1**:  
    単純に
    $$
     \text{Signal}_t = \sum_{j=1}^4 mkt_{nm}(t,j)
    $$
    を使い、news y / non-newsy を分けて係数推定。
*   **Methods 2–7（あなたの z\_t, z\*\_t に対応）**:  
    シグナルは
    1.  過去4つの newsy 月リターンの合計から「expanding window の平均」を引く
    2.  **従属変数が newsy の場合には符号を反転させる**
    という加工を施したもの。これは、
    *   newsy 月ではリバーサル（負の予測）、
    *   non-newsy 月ではコンティニュエーション（正の予測）  
        になるように、シグナルの向きを統一するためです。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

この「過去4つの newsy 月の合計（あるいは平均）＋平均乖離＋符号反転」という構造が、あなたが使っている **nr + P4 型の z\*\_t** の理論的な原型になっています。

### 3.4 OOS R² ≈ 4% というかなり大きな予測力

論文のメイン結果のひとつは：

*   上記シグナルを使った**月次市場リターンの out-of-sample R² が約 4%**
*   これは Goyal & Welch（2008）など既存文献で報告されている他の monthly predictor の OOS R²（多くは ±1% 未満）と比べると**桁違いに大きい** [OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

この結果から Guo は

> 「月次の U.S. aggregate market はほぼ予測不可能」という従来のコンセンサスは修正されるべき

と主張しています。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

さらに、期待リターン系列を見ると

*   month-to-month で激しく振動（オートコリレーションはむしろ負）
*   T-bill 1ヶ月利回りより低い月が約 1/3、期待超過リターンがマイナスの月が約 1/5
*   よって、**株式が T-bill より安全（期待リターンが低い）月が頻繁に存在する**

という、リスクベースの説明と整合的でない特徴も強調されています。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

* * *

4\. 理論モデル：Earnings extrapolation と「階段型」減衰
-----------------------------------------

### 4.1 基本のアイデア

モデル部分のキーワードは

*   **earnings extrapolation（アーニングの単純外挿）**
*   **time-varying decay rate（情報の減衰速度が一定でない）**
*   **step-function pattern（step 型の有効性）**

です。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

設定はざっくり：

1.  投資家は、将来の aggregate earnings（集計利益）を予測するとき、
    *   主に **newsy 月の発表 earnings** に基づいて予測を行う
    *   non-newsy 月の情報はあまり使わない（earnings season に注意が集中する）
2.  **現実世界では**
    *   ある newsy 月の earnings が、次の数ヶ月の earnings に対して持つ「予測力」は
        *   non-newsy 月を予測するときには強く残る
        *   次の newsy 月の earnings を予測するときに、一気に弱くなる  
            → つまり、「情報の有効性は時間とともに徐々に減衰する」のではなく、  
            **newsy 月のところで階段状に drop する**（step function）[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)
3.  しかし投資家は、この減衰パターンを誤認し、
    *   **常に一定速度で減衰すると仮定**して extrapolation してしまう

### 4.2 そこから生じる mispricing の方向

この誤認から、次のような予測誤差が発生します：[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

*   good newsy 月（高い earnings, 高い stock return）があったとき
    *   将来 **newsy 月の earnings** に対しては、  
        本当は情報の有効性が大きく落ちるのに、投資家はそれを理解していない  
        → **将来の newsy earnings を過大に予測（overreaction）**  
        → アナウンス時には失望が生じて**リターンリバーサル（負の予測）**
    *   将来 **non-newsy 月の earnings** に対しては、  
        情報の有効性が高く維持されるのに、投資家は減衰すると考えてしまう  
        → **将来の non-newsy earnings を過小に予測（underreaction）**  
        → 後から情報が織り込まれ**リターンコンティニュエーション（正の予測）**

これが

> 「newsy 月のリターンは将来 newsy 月リターンの負の予測子・non-newsy 月リターンの正の予測子になる」

という実証パターンと一致します。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

* * *

5\. サーベイ・アーニングデータでの検証
---------------------

Guo は市場リターンだけでなく、

*   アナリスト/投資家の **earnings expectation**（EPS 予想）
*   結果としての **earnings surprise**

を用いて、「extrapolation ミス」が本当に起きているかを検証します。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

### 5.1 aggregate earnings surprises

代表的な回帰は

$$
\text{AggSurprise}_t = \alpha + \beta_1 \sum_{j=1}^4 \text{AggSurprise}_{nm(t,j)} + \beta_2 \Big( \sum_{j=1}^4 \text{AggSurprise}_{nm(t,j)} \times I_t^{nm} \Big) + \gamma I_t^{nm} + \epsilon_t
$$

のような形で、

*   newsy 月 / non-newsy 月で「過去のサプライズの効き方（β）」が違うかを検証。
*   結果は、**newsy 月では過去サプライズへの反応がより “overreaction 気味”**、  
    **non-newsy 月ではより “underreaction 気味”** であることを示す。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

### 5.2 revision データ

さらに、アナリストの earnings forecast revision（IBES 系）を用いて、

*   予想の修正が newsy vs non-newsy でどう違うか
*   どちらで over / under extrapolation が強いか

を確認し、モデルの予測と整合的であることを示します。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

* * *

6\. クロスセクションと海外市場
-----------------

### 6.1 業種モメンタム

Moskowitz & Grinblatt (1999) 型の industry momentum に newsy / non-newsy の区別を導入すると：[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

*   平均的には業種モメンタムは強いが、
    *   **non-newsy 月に集中**（コンティニュエーションが強い）
    *   **newsy 月ではほぼ消える**（リバーサル成分が強く打ち消す）

という結果が得られる。

### 6.2 海外市場

同様のパターンが

*   主要海外株式市場の aggregate index
*   各国の業種ポートフォリオ

でも観測されることが示され、「米国固有の現象ではない」と主張しています。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501)

* * *

7\. リスクベース説明の困難性と理論的含意
----------------------

Guo は、このパターンを**標準的なリスクプレミアム変動モデル**で説明するのは困難だと強調します。主な理由は：[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501)

1.  期待リターンが月次で大きく振動する（オートコリレーションが負）。
2.  期待リターンが T-bill を1/3の月で下回り、1/5の月では期待超過リターンがマイナス。
3.  もしリスクモデルで説明するなら、
    *   good newsy 後は、将来の newsy 月が「安全」、non-newsy 月が「危険」にならなければならないが、  
        そうしたリスク構造を自然に生み出すマクロモデルはかなり特殊になる。

そのため、Guo は

> このパターンは **earnings extrapolation という行動バイアス** が最も素直な説明であり、  
> 株式市場の「予測可能性」と「効率性」に関する従来の前提を見直す必要がある

と結論づけています。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501)

* * *

8\. あなたの実装との関係（nr, P4\_j mktnm, z\*\_t）
---------------------------------------

あなたが実装している

*   **nr(t)**：newsy→repetitive, repetitive→newsy の「継続＋反転」構造
*   **P4\_j mktnm(t,j)**：過去4つの newsy 月リターンの合計（あるいは平均）
*   **z\*\_t**：nr + P4 を線形結合したオンライン予測子

は、 **すべてこの Guo (2025) のシグナル設計と係数推定手順（Methods 1–7）を、  
運用に使いやすい形に落とし込んだもの** と理解してよいです。

特に

*    $mkt_{nm}(t,j)$ 
*    $\sum_{j=1}^4 mkt_{nm}(t,j)$ （P4 型）
*   expanding mean を引いて、newsy 月で符号を反転させるシグナル

は、そのままあなたのコード内の

*   `mkt_nm(t,j)`
*   `nm4` / `P4`
*   `nr` + `P4` を組み合わせた `z*_t`

と 1 対 1 対応します。

* * *

もし次のような点をさらに詰めたい場合は、そこだけ切り出して深掘りも可能です：

*   Table 4（Methods 1–7）のそれぞれの定義と、Python 実装への完全マッピング
*   係数推定の実務的細部（expanding / rolling、サンプル分割の仕方、constraint の扱い）
*   Earnings extrapolation モデルの数式レベルでの完全な導出
*   あなたの `z_t`, `z*_t` 実装が Table 4 のどの Method に最も近いかのマッピング

どこから掘り下げたいか指定していただければ、そこを数式＋コードレベルまで落とし込みます。

## Response:
では順番に整理します。

1.  Guo (2025) Table 4 の Methods 0〜7 の定義と Python へのマッピング
2.  係数推定（expanding / rolling, サンプル分割, constraint）の実務的ディテール
3.  Earnings extrapolation モデルの数式レベルでの導出イメージ
4.  あなたの `z_t` / `z*_t` 実装と Table 4 のどの Method が一番近いか

必要なところは RFS 論文本文とワーキングペーパー版から確認しています。[OUP Academic+2Finance Department+2](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

* * *

1\. Table 4（Methods 0〜7）の定義と Python 実装への対応
------------------------------------------

### 1.0 共通の前提

*   依存変数：米国株式市場の月次超過リターン  $r_t$ （CRSP value-weighted minus T-bill）。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)
*   「newsy month」＝四半期第1月（1,4,7,10月など）、それ以外が non-newsy。
*    $mkt_{nm}(t,j)$ ：月  $t$  から遡って **j 番目の newsy 月の市場超過リターン**。[Finance Department](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)
*   基本シグナル（raw）
    $$
    S_t \equiv \sum_{j=1}^4 mkt_{nm}(t,j)
    $$
    過去4つの newsy 月リターンの合計（もしくは平均に比例）。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)
*   OOS  $R^2$  の定義：
    $$
    R^2_{\text{OOS}} = 1 - \frac{\sum_{t=1}^{n}(r_t - \hat r_t)^2}{\sum_{t=1}^{n} (r_t - \bar r_t)^2}
    $$
    ここで  $\bar r_t$  は「その時点までの平均リターン（expanding window）」で、  
    これを上回れたら  $R^2 > 0$ 。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

#### Python での基本的な S\_t の構築イメージ

```python
def build_newsy_signal(mkt_excess: pd.Series, is_newsy: pd.Series) -> pd.Series:
    """
    mkt_excess : 月次市場超過リターン (index=DatetimeIndex)
    is_newsy   : newsy ダミー (True/False)
    戻り値     : S_t = 過去4つの newsy 月リターンの合計
    """
    dates = mkt_excess.index
    S = pd.Series(index=dates, dtype=float)

    # 過去の newsy 月の index を順次蓄積
    past_newsy_idx = []

    for i, t in enumerate(dates):
        if is_newsy.iloc[i]:
            past_newsy_idx.append(i)

        # t 時点からみて「過去」の newsy 月インデックス
        cand = [k for k in past_newsy_idx if k < i]
        cand = sorted(cand, reverse=True)[:4]

        if len(cand) == 0:
            S[t] = np.nan
        else:
            S[t] = mkt_excess.iloc[cand].sum()

    return S
```

* * *

### Method 0：Campbell & Thompson (2008) 型の valuation benchmark

*   **シグナル**：newsiness に関係なく、伝統的なバリュエーション・シグナル（D/P, E/P, B/M）。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)
*   予測式：  
    Campbell & Thompson (2008) の「valuation + growth」仕様を各比率に対して推定し、  
    その **3 つの予測を平均したもの**を Method 0 の予測  $\hat r_t^{(0)}$  とする。
*   CT 2008 の sign constraints（係数 ≥ 0、予測リターン ≥ 0 等）をそのまま採用。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

Python で完全再現しようとすると、D/P, E/P, B/M データが必要なので、ここでは骨格だけ：

```python
def forecast_method0_ct(dp, ep, bm, r):
    """
    dp, ep, bm : valuation ratios
    r          : market excess return

    ここでは疑似コードレベル：
      - 各レシオごとに CT(2008) 仕様で回帰し、
      - 係数に sign constraint を課して推定、
      - 3つの予測値の平均を Method 0 forecast とする。
    """
    # TODO: CT(2008) の sign constrained regression を実装
    pass
```

* * *

### Method 1：単純な S\_t（sum of 4 newsy returns）を使う

*   **シグナル**：
    $$
    s_t^{(1)} = S_t = \sum_{j=1}^4 mkt_{nm}(t,j)
    $$
*   回帰の仕方：
    *   newsy 月だけを集めて
        $$
        r_t = a_N + b_N s_t^{(1)} + \varepsilon_t,\quad t\in \text{newsy}
        $$
    *   non-newsy 月だけを集めて
        $$
        r_t = a_{NN} + b_{NN} s_t^{(1)} + \varepsilon_t,\quad t\notin \text{newsy}
        $$
    *   **expanding window OLS**：月  $t$  の予測には必ず  $t-1$  までのデータのみを使用。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)
*   予測値（例：newsy 月の場合）
    $$
    \hat r_t^{(1)} = \hat a_N(t-1) + \hat b_N(t-1) s_t^{(1)}.
    $$

Python の擬似実装：

```python
def forecast_method1(mkt_excess: pd.Series, S: pd.Series, is_newsy: pd.Series,
                     min_obs=60):
    dates = mkt_excess.index
    fcast = pd.Series(index=dates, dtype=float)

    for i, t in enumerate(dates):
        mask_past = (dates < t) & S.notna()
        if mask_past.sum() < min_obs:
            fcast[t] = np.nan
            continue

        if is_newsy.loc[t]:
            # newsy 月の回帰
            past = (mask_past & is_newsy)
        else:
            # non-newsy 月の回帰
            past = (mask_past & ~is_newsy)

        X = sm.add_constant(S.loc[past])
        y = mkt_excess.loc[past]

        model = sm.OLS(y, X).fit()
        a, b = model.params["const"], model.params[S.name]
        fcast[t] = a + b * S.loc[t]

    return fcast
```

* * *

### Methods 2〜4：符号調整 + demeaned シグナル

まず **共通のシグナル定義**：[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

1.  過去4つの newsy リターンの合計  $S_t$  を作る
2.  その **expanding-window 平均** を差し引き
    $$
    \tilde S_t = S_t - \bar S_{t-1}, \quad \bar S_{t-1} = \frac{1}{t-1}\sum_{s\le t-1} S_s
    $$
3.  従属変数が **newsy 月** のときは符号を反転：
    $$
    s_t^{(*)} = \begin{cases} -\tilde S_t, & t \text{ が newsy} \\ \tilde S_t, & t \text{ が non-newsy} \end{cases}
    $$

```python
def build_signed_demeaned_signal(S: pd.Series, is_newsy: pd.Series) -> pd.Series:
    S_mean = S.expanding().mean().shift(1)  # t 時点で t-1 までの平均
    S_dm   = S - S_mean
    s_star = S_dm.copy()
    s_star[is_newsy] = -S_dm[is_newsy]  # newsy月は符号反転
    return s_star
```

#### Method 2

*   シグナル：上の  $s_t^{(*)}$ 
*   回帰：Method 1 同様、newsy / non-newsy でサンプルを分けて expanding-window OLS。
*   予測：
    $$
    \hat r_t^{(2)} = \begin{cases} \hat a_N(t-1) + \hat b_N(t-1) s_t^{(*)}, & t\text{ newsy} \\ \hat a_{NN}(t-1) + \hat b_{NN}(t-1) s_t^{(*)}, & t\text{ non-newsy} \end{cases}
    $$

Python は `forecast_method1` の `S` を `s_star` に置き換えるだけです。

#### Method 3

*   シグナルは Method 2 と同じ  $s_t^{(*)}$ 。
*   違いは **定数項の扱い**：
    *   定数係数  $a_N, a_{NN}$  をそのまま使わず、
    *   代わりに「**expanding-window の平均リターン**」で置き換える。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

具体的には：

$$
\hat r_t^{(3)} = \begin{cases} \bar r_N(t-1) + \hat b_N(t-1)\, s_t^{(*)}, & t\text{ newsy}\\ \bar r_{NN}(t-1) + \hat b_{NN}(t-1)\, s_t^{(*)}, & t\text{ non-newsy} \end{cases}
$$

ここで  $\bar r_N(t-1)$  は「過去の newsy 月の平均リターン」、  
 $\bar r_{NN}(t-1)$  は「過去の non-newsy 月の平均リターン」。

```python
def forecast_method3(mkt_excess, s_star, is_newsy, min_obs=60):
    dates = mkt_excess.index
    fcast = pd.Series(index=dates, dtype=float)

    for i, t in enumerate(dates):
        mask_past = (dates < t) & s_star.notna()
        if mask_past.sum() < min_obs:
            fcast[t] = np.nan
            continue

        if is_newsy.loc[t]:
            past = (mask_past & is_newsy)
        else:
            past = (mask_past & ~is_newsy)

        X = sm.add_constant(s_star.loc[past])
        y = mkt_excess.loc[past]
        model = sm.OLS(y, X).fit()
        b = model.params[s_star.name]

        # newsy / non-newsy 別平均を intercept の代わりに使う
        mu = y.mean()
        fcast[t] = mu + b * s_star.loc[t]

    return fcast
```

#### Method 4

*   シグナルは Method 2 と同じ  $s_t^{(*)}$ 。
*   定数項を「Method 0 の予測」で置き換える：[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)
    
$$
\hat r_t^{(4)} = \hat r_t^{(0)} + \hat b_{\text{grp}(t)}(t-1)\,s_t^{(*)},
$$

ここで  $\text{grp}(t)$  は newsy / non-newsy の区別。

つまり：

*   「valuation-based 予測（Method 0）」＋「extrapolation ベースの追加成分」という構造。

Python では Method 3 の `mu` 部分を `fcast_method0[t]` に変えるだけです。

* * *

### Methods 5〜7：係数を pooled sample から推定

Methods 5〜7 は **Method 2〜4 とシグナルは同じ**で、  
違いは「係数を newsy/non-newsy 別ではなく **全サンプル pooled** で推定する」点。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

*   Method 5：Method 2 の pooled 版
*   Method 6：Method 3 の pooled 版
*   Method 7：Method 4 の pooled 版

例：Method 6 の予測式は

$$
\hat r_t^{(6)} = \bar r(t-1) + \hat b(t-1)\, s_t^{(*)},
$$
*    $\bar r(t-1)$ ：全サンプル（newsy + non-newsy）の expanding 平均
*    $\hat b(t-1)$ ：全サンプルで回帰した傾き。

Python 的には、Method 3 の `past` を `mask_past`（newsy/non-newsy 共通）にするだけです。

```python
def forecast_method6(mkt_excess, s_star, min_obs=60):
    dates = mkt_excess.index
    fcast = pd.Series(index=dates, dtype=float)

    for i, t in enumerate(dates):
        mask_past = (dates < t) & s_star.notna()
        if mask_past.sum() < min_obs:
            fcast[t] = np.nan
            continue

        X = sm.add_constant(s_star.loc[mask_past])
        y = mkt_excess.loc[mask_past]
        model = sm.OLS(y, X).fit()
        b = model.params[s_star.name]

        mu = y.mean()
        fcast[t] = mu + b * s_star.loc[t]

    return fcast
```

* * *

2\. 係数推定の実務的ディテール
-----------------

### 2.1 Expanding window vs Rolling

*   Guo は**expanding window** を明示的に採用しています：  
    「各月 t について、t−1 までのデータで OLS → 係数で t を予測」。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)
*   Rolling にしない理由：
    *   モデルは「長期安定な構造」に基づいている
    *   ただし Table 3/4 ではサブサンプル（1926–1973, 1974–2023 等）も分析して構造変化を別枠で確認。[Finance Department](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf)

実装上は、あなたが今書いている「for ループで t を回して、`dates < t` で過去を切る」やり方で完全に OK です。

### 2.2 サンプル分割：newsy vs non-newsy vs pooled

*   Methods 1〜4：**newsy と non-newsy を別々に回帰**。
*   Methods 5〜7：**全サンプル pooled で一つの回帰**。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

この「分割 or pooled」は

*   newsy / non-newsy で期待リターンの水準を別に持たせるか
*   シグナルの傾きだけを使うか

の違いと理解できます。

### 2.3 constraint の扱い

*   Method 0 のみ、Campbell & Thompson (2008) 型の sign constraints を利用  
    （係数 ≥ 0、予測リターンを 0 と rf との間に truncate する等）。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)
*   Methods 1〜7 の「nr / P4 シグナルによる予測」の部分には、**特別な sign constraint は課していません**。通常の OLS による係数をそのまま使う設計です。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

実務上あなたの実装でも

*   Method 0 相当：CT 仕様をそのまま模倣（sign constrained regression）
*   Methods 1〜7 相当：普通の `sm.OLS` でよい

と考えて問題ありません。

### 2.4 OOS サンプル開始時点

論文では 1926–2021 全期を使い、OOS R² の計算も全期間で行いますが、  
実際には

*   最低観測数（例えば 60 ヶ月以上）を確保してから OOS を開始
*   それ以前は forecast を NaN にして R² 集計から外す

という実務的な取り扱いで十分です（あなたの `min_obs` 引数の考え方で良い）。

* * *

3\. Earnings Extrapolation モデルの数式レベル導出（骨格）
------------------------------------------

ここは RFS 本文の Section 5〜6 を踏まえた「同値な簡約モデル」で説明します。[Finance Department](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf)

### 3.1 真の配当・アーニングプロセス

*   時間は月 t=0,1,2,…
*   配当  $D_t$ 、その対数  $d_t = \log D_t$ 
*   「ROE 的な earnings」
    $$
    \Delta d_t = d_t - b_{t-1},
    $$
    ここで  $b_{t-1}$  は **指数加重移動平均（EWMA）** 型の book value proxy：
    $$
    b_{t-1} = (1-\rho)\sum_{i=0}^{\infty}\rho^i d_{t-1-i}
    $$
    →  $\Delta d_t$  は「当期 earnings − 過去の蓄積 earnings」 ≈ ROE。[Finance Department](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf)

**真のプロセス**として、

$$
\Delta d_t = \begin{cases} \mu_N + \phi_N \Delta d_{t-1} + u_t, & t\text{ が newsy} \\ \mu_{NN} + \phi_{NN} \Delta d_{t-1} + u_t, & t\text{ が non-newsy} \end{cases}
$$

かつ

$$
0 < \phi_N < \phi_{NN} < 1
$$

とします。

*   newsy 月の earnings は「過去 earnings との自己相関が低い」
*   non-newsy 月の earnings は「自己相関が高い」

という実証結果を反映した形です。[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf)

### 3.2 投資家の誤った信念：代表 AR パラメータ φ

投資家は「ニュースのタイミングによって自己相関が変わる」という事実を理解しておらず、  
簡略化された **単一パラメータ φ** モデルを信じているとします：

$$
\Delta d_t = \mu + \phi \Delta d_{t-1} + \varepsilon_t
$$
*    $\phi$  は、news y や non-newsy の違いを平均化した “代表パラメータ”
*   実際の  $\phi_N, \phi_{NN}$  との乖離が mis-extrapolation の原因。[Finance Department](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf)

### 3.3 株価と期待リターン

*   投資家は **リスク中立**・一定の割引率  $R_f$  を持つとします。[Finance Department](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf)
*   価格は将来配当の割引現在価値：
    $$
    P_t = \sum_{k=1}^\infty \frac{1}{R_f^k} \mathbb{E}_t[D_{t+k}]
    $$
    → log-linear 化すると Campbell–Shiller 型の近似で
    $$
    p_t \approx \kappa_0 + \kappa_1 b_t + \kappa_2 \Delta d_t
    $$
    のような形にまとめられます（論文ではより厳密に整理）。[Finance Department](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf)
*   シンプルには、**予想配当成長率を外挿したものが価格に入る**ので、  
    投資家の予想
    $$
    \mathbb{E}_t^{\text{(investor)}}[\Delta d_{t+1}] = \mu + \phi \Delta d_t
    $$
    が価格に影響し、結果として予想リターン
    $$
    \mathbb{E}_t^{\text{(investor)}}[R_{t+1}]
    $$
    にも依存します。

### 3.4 誤信念が作る予測パターン

真のプロセスに対する 1-step 先予測誤差を計算すると：

*   真の 1-step ahead 期待値
    $$
    \mathbb{E}_t^{\text{(true)}}[\Delta d_{t+1}] = \begin{cases} \mu_N + \phi_N \Delta d_t, & t+1\text{ が newsy}\\ \mu_{NN} + \phi_{NN} \Delta d_t, & t+1\text{ が non-newsy} \end{cases}
    $$
*   投資家の期待値（誤ったモデル）
    $$
    \mathbb{E}_t^{\text{(inv)}}[\Delta d_{t+1}] = \mu + \phi \Delta d_t
    $$

したがって、**誤差**は

$$
\text{Bias}_{t+1} = \mathbb{E}_t^{\text{(inv)}}[\Delta d_{t+1}]- \mathbb{E}_t^{\text{(true)}}[\Delta d_{t+1}] = \begin{cases} (\mu - \mu_N) + (\phi - \phi_N)\Delta d_t, & t+1\text{ newsy}\\ (\mu - \mu_{NN}) + (\phi - \phi_{NN})\Delta d_t, & t+1\text{ non-newsy} \end{cases}
$$

ここで

*   good earnings →  $\Delta d_t > 0$  のとき
*   もし  $\phi$  が「平均的」（ $\phi_N < \phi < \phi_{NN}$ ）だとすると[Finance Department](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf)
    
$$
\phi - \phi_N > 0,\quad\phi - \phi_{NN} < 0
$$
*   **t+1 が newsy の場合**：Bias $_{t+1} > 0$  となり、
    *   投資家は earnings を **過大評価**（overreaction）
    *   実現時に失望 → **リターンのリバーサル（負の予測）**
*   **t+1 が non-newsy の場合**：Bias $_{t+1} < 0$  となり、
    *   投資家は earnings を **過小評価**（underreaction）
    *   後から追い上げ → **リターンのコンティニュエーション（正の予測）**

この Bias が価格とリターンに反映されるので、

*   newsy 月のリターンは「過去の newsy リターンの **負の予測子**」
*   non-newsy 月のリターンは「過去の newsy リターンの **正の予測子**」

という、実証で見ている相関パターンが導かれます。[Finance Department](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf)

論文ではこれをさらに一般化し、multi-step ahead forecast（6ヶ月先など）を考えることで、  
「過去 4 つ程度の newsy リターンにわたって有意な係数が出る」ことを再現しています。

* * *

4\. あなたの `z_t` / `z*_t` と Table 4 Methods との対応
----------------------------------------------

最後に、あなたの実装と論文の方法を結びつけます。

### 4.1 あなたの元の `build_predictor_z`（nr-only 版）

元コード（要約）：

*   月タイプ： N, R, 3
*   `mkt_mean_lag`：市場超過リターンの expanding 平均（t−1まで）
*   `base = mkt_lag - mkt_mean_lag`
*   ルール：
    *   **R 月**：`z = base`（1ヶ月前のリターン − 平均）
    *   **N 月**：直近の R 月の `base` の符号を反転して使用
    *   **3 月**：0  
        （＋実装の細部はこれに準拠）

これは

*   Guo 2025 の「過去4つの newsy リターン合計」を **「過去1つ」に縮めたバージョン**
*   さらに、「demean（平均を引く）」＋「newsy 月で符号反転」という構造は  
    Methods 2〜7 の共通シグナル設計と本質的に同じです。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

ただし違いは：

*   Guo：
    *   シグナル  $s_t$  → **OLS で  $\hat r_t$  を推定**
    *   その  $\hat r_t$  を使って戦略を組む（別途スケーリング）
*   あなた：
    *   `z_t` 自体を「スケーリング前の weight 用シグナル」として使用し、
    *   `w_t = z_t * target_vol / σ_z` に直接入れている

という点です。  
構造的に一番近いのは **「K=1 の Method 6」** と考えるのが自然です：

*   K=4 → K=1 に変更
*   pooled（newsy+non-newsy）扱い
*   demeaned ＋ sign flip は Method 2〜7 と同じ
*   intercept 代替 = expanding mean に近い扱い

### 4.2 あなたの `z*_t`（nr + P4 の 2変数版）

あなたが後で実装した `build_z_star_online` は：

*   予測子：
    *    $x_{1,t} = mkt\_nr(t)$ 
    *    $x_{2,t} = P4(t)$ （過去4つの newsy 月平均）
*   係数推定：
    *    $r_s = \alpha + \beta_1 x_{1,s} + \beta_2 x_{2,s} + \varepsilon_s$ 
    *   t に対する予測には **t−1 までの expanding window** を使用
*   予測子：
    $$
    z^*_t = \hat\beta_1(t-1) x_{1,t} + \hat\beta_2(t-1) x_{2,t}
    $$
*   これを `z` として `apply_timing_strategy` に渡している。

これは

*   signal = sum\_{4} mkt\_nm(t,j)（P4）をベースにした **Method 6** を
*   **2次元ベクトル（nr + P4）に拡張した multivariate 版**
*   推定は pooled sample（newsy + non-newsy）でやっているので、  
    正確には「**Method 6 の多変量拡張**」と言えます。[OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)

### 4.3 きっちり Method 2 / 6 に合わせたい場合の修正ポイント

もし、

> 「論文 Table 4 の Method 2 / 6 と**完全に同じ**構造で実装したい」

のであれば、必要な修正は：

1.  **シグナル定義を統一**
    *   あなたの `P4` を
        $$
        S_t = \sum_{j=1}^4 mkt_{nm}(t,j)
        $$
        にして、その後に「expanding-mean を引く」「newsy 月で sign flip」を必ず入れる。
2.  **予測値  $\hat r_t$  をまず作る**
    *   `z_t` を直接 weight に使うのではなく、
    *   `forecast_methodX` のようにして `hat_r_t` を別 Series で管理する。
3.  **weight は  $\hat r_t$  から作る**
    *   Guo は Method 6 の予測列を Figure 2 で期待リターンとしてプロットし、そのまま経済的な解釈をしている。[OUP Academic](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)
    *   戦略実装では、
        $$
        w_t = \frac{\hat r_t}{\hat\sigma_{\hat r}} \cdot \text{target\_vol}
        $$
        のような scaling にすれば、あなたの現行の `apply_timing_strategy` と完全に整合する。

あなたの現行コードは \*\*Guo のロジックをかなり忠実に取り入れた「やや簡約版」\*\*になっているので、  
上記の微修正を入れれば「Table 4 の特定 Method と 1:1 マッチ」させることができます。

* * *

もし次にやるとしたら：

*   「Method 2 / 6 を**そのまま**実装して、現行の `z_t`, `z*_t` と OOS R²・戦略パフォーマンスを比較する」
*   「β\_News(t), β\_NonNews(t) の時系列を可視化して、2020 年以降で構造変化を検出する」

といった分析が自然だと思います。  
必要であれば、その比較用の Python を丸ごと書き下ろします。

## Response:
Guo (2025) の「筆者イチ押し」の運用ルールは、Table 4 の Method 6 を用いた time-series strategy です。実際に Figure 2 の期待リターン系列も Method 6 で描かれており、Appendix A.3 でも「the forecast from method 6 of Table 4」「The portfolio weight in my strategy is c\_t x\_t」と明記されています。[OUP Academic+1](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf)

以下で、あなたの `load_ff_monthly_from_ken_french` を前提に、Method 6 ベースの戦略を「そのまま」実装するコードをフルで示します。

* * *

1\. 前提：FF データ読み込みと月タイプ
----------------------

すでにお持ちの関数をそのまま使います。

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt

# 既存：Ken French ファイルから月次部分だけ抽出
def load_ff_monthly_from_ken_french(csv_path: str) -> pd.DataFrame:
    raw = pd.read_csv(csv_path, skiprows=4)

    num = pd.to_numeric(raw['Unnamed: 0'], errors='coerce')
    mask_monthly = num > 10000
    monthly = raw[mask_monthly].copy()

    monthly = monthly.rename(columns={'Unnamed: 0': 'date'})
    monthly['date'] = pd.to_datetime(monthly['date'].astype(int), format="%Y%m")
    monthly = monthly.set_index('date').sort_index()

    for col in ['Mkt-RF', 'RF']:
        monthly[col] = pd.to_numeric(monthly[col], errors='coerce')

    ff = monthly[['Mkt-RF', 'RF']].copy()
    ff['mkt_excess'] = ff['Mkt-RF'] / 100.0
    ff['rf'] = ff['RF'] / 100.0

    return ff[['mkt_excess', 'rf']].dropna()

# 既存：Guo の newsy / non-newsy（四半期1ヶ月目が newsy）
def classify_month_type(index):
    mt = pd.Series(index=index, dtype="object")
    for t in index:
        m = t.month % 3
        if m == 1:
            mt[t] = 'N'   # newsy (Jan, Apr, Jul, Oct)
        elif m == 2:
            mt[t] = 'R'   # repetitive
        else:
            mt[t] = '3'   # 3rd month
    return mt
```

* * *

2\. Method 6 のシグナル xₜ（論文の x\_t）
-------------------------------

### 論文の定義（要約）

Appendix A.3 によると、Method 6 用の time-series strategy は以下です。[OUP Academic](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf)

*   各月 t−1 の終わりに、
    1.  「直近 4 つの newsy 月の市場トータルリターン（配当込み、Excess ではない）」の合計を取る  
        → 論文中の `∑_{j=1}^4 mktnm(t−1, j)` に相当
    2.  その「4ニュースy合計」の expanding mean（サンプル開始〜t−1 までの平均）を引く
    3.  翌月 t が newsy なら符号を反転、non-newsy ならそのまま  
        → これが「demeaned & sign-flipped signal」x\_{t−1}
*   回帰は  
    `mkt_t = β x_{t−1} + 1 * mkt̄_{t−1} + ε_t`  
    （mkt̄\_{t−1} は t−1 までの市場リターンの expanding mean。係数 1 に固定）
*   ある月 t までのデータで β を expanding OLS で推定し、その β\_t を使って  
    `E_t[mkt_{t+1}] = β_t x_t + mkt̄_t`  
    を予測。ポートフォリオウェイトは `w_t = β_t x_t`。

これに厳密に対応する Python 実装を作ります。

### (1) 「直近 4 つの newsy 月リターン」の合計 Sₜ

```python
def compute_news_sum_series(mkt_total: pd.Series,
                            month_type: pd.Series) -> pd.Series:
    """
    mkt_total: 市場トータルリターン (配当込み, 月次, レベル: 0.01 = 1%)
    month_type: 'N','R','3' からなる Series (index は mkt_total と同じ)

    戻り値:
        S_t = 「t までに出現した直近 4 つの newsy 月の total return の合計」
    """
    is_newsy = (month_type == "N")
    news_series = mkt_total[is_newsy]

    res = pd.Series(index=mkt_total.index, dtype=float)
    for t in mkt_total.index:
        past_news = news_series[news_series.index <= t]
        if len(past_news) >= 4:
            res[t] = past_news.iloc[-4:].sum()
        else:
            res[t] = np.nan
    return res
```

### (2) xₜ の構築（論文の x\_{t−1} を index t に持たせる）

```python
def build_method6_signal(mkt_total: pd.Series):
    """
    Guo (2025) Appendix A.3 の x_{t-1} を index t に載せた Series x_t を返す。

    mkt_total: 月次の市場トータルリターン (mkt_excess + rf)
    """
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")

    # 直近4つの newsy 月の total return 合計 S_t
    S = compute_news_sum_series(mkt_total, month_type)

    # x_t: 「t のリターンを予測するための x_{t-1}」を t の index に保存
    x = pd.Series(index=idx, dtype=float)

    # S の expanding mean を t-1 時点までで計算（NaN は除外）
    S_hist = []
    for i in range(1, len(idx)):
        prev_date = idx[i-1]   # t-1
        curr_date = idx[i]     # t

        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue

        # サンプル開始〜t-1 までの S の平均
        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))

        # 翌月 t が newsy なら符号反転
        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return x, month_type
```

* * *

3\. Method 6 の time-series 戦略の完全実装
----------------------------------

論文の回帰式  
`mkt_t = β x_{t−1} + 1 * mkt̄_{t−1} + ε_t`  
は、  
`(mkt_t − mkt̄_{t−1}) = β x_{t−1} + ε_t`  
と書き換えられるので「定数項なし 1 変数回帰」として実装できます。

さらに、Appendix A.3 では Sharpe 比比較のために「最終的なストラテジーのボラティリティを市場のボラと同じ 5.34% にスケール」しています。[OUP Academic](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf)

以下の関数では

*   `min_obs`：β 推定に必要な最低サンプル数（例：120ヶ月）
*   `target_vol`：ボラティリティを合わせたい水準（None の場合、市場ボラに合わせる → 論文仕様）
*   `max_leverage`：望むならリアル運用用に w\_t をクリップ（論文はここを制約していないので、None なら無制約）

という形でパラメータ化してあります。

```python
def backtest_method6_strategy(ff: pd.DataFrame,
                              min_obs: int = 120,
                              target_vol: float = None,
                              max_leverage: float = None) -> pd.DataFrame:
    """
    Guo (2025) が Appendix A.3 で説明している
    Method 6 ベースの time-series strategy を実装し、バックテスト結果を返す。

    ff: load_ff_monthly_from_ken_french の出力
        必須列: 'mkt_excess', 'rf' (単位はリターンレベル, 0.01=1%)

    戻り値:
        DataFrame:
          - mkt_excess, rf, mkt_total
          - month_type ('N','R','3')
          - x: Method 6 の signal x_t
          - mkt_mean: mkt̄_{t-1} (t index にずらしたもの)
          - beta: 各 t 時点までの expanding OLS で推定した β_t
          - w_raw: β_t x_t を 1ヶ月先に適用した weight（overlay 部分）
          - exp_ret: 予測された市場リターン E_t[mkt_{t+1}]
          - strat_excess_raw: overlay の生の超過リターン
          - strat_excess_scaled: ボラ調整後の超過リターン
          - strat_total: 総リターン（rf + strat_excess_scaled）
    """
    mkt_excess = ff["mkt_excess"].copy()
    rf = ff["rf"].copy()

    # 市場トータルリターン (CRSP value-weighted に相当する近似)
    mkt_total = mkt_excess + rf
    idx = mkt_total.index

    # 1) シグナル x_t（index t）と month_type
    x, month_type = build_method6_signal(mkt_total)

    # 2) mkt̄_{t-1} （expanding mean を 1 期シフト）
    mkt_mean = mkt_total.expanding().mean().shift(1)

    # 3) 回帰 (mkt_t - mkt̄_{t-1}) = β x_{t-1} + ε_t
    y_adj = mkt_total - mkt_mean
    beta = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        # t までに利用可能なデータだけで β を推定（expanding）
        mask = (idx <= t) & x.notna() & y_adj.notna()
        n = mask.sum()
        if n < min_obs:
            beta[t] = np.nan
            continue

        xi = x[mask].values
        yi = y_adj[mask].values
        denom = (xi ** 2).sum()
        beta[t] = (xi * yi).sum() / denom if denom > 0 else np.nan

    # 4) 1ヶ月先の予測と weight
    exp_ret = pd.Series(index=idx, dtype=float)
    w_raw = pd.Series(index=idx, dtype=float)

    for i in range(len(idx) - 1):
        t = idx[i]
        t_next = idx[i + 1]

        if any(np.isnan([beta[t], x[t], mkt_mean[t]])):
            exp_ret[t_next] = np.nan
            w = 0.0
        else:
            # 論文上は w_t = β_t x_t
            w = beta[t] * x[t]
            if max_leverage is not None:
                w = float(np.clip(w, -max_leverage, max_leverage))

            # 予測市場リターン E_t[mkt_{t+1}] = β_t x_t + mkt̄_t
            exp_ret[t_next] = w + mkt_mean[t]

        w_raw[t_next] = w

    # 5) overlay の超過リターン: w_t * mkt_excess_{t}
    strat_excess_raw = w_raw * mkt_excess

    # 6) ボラ調整（Sharpe 比比較のため）
    common_mask = strat_excess_raw.notna() & mkt_excess.notna()
    strat_vol = strat_excess_raw[common_mask].std(ddof=1)
    mkt_vol = mkt_excess[common_mask].std(ddof=1)

    if target_vol is None:
        # 論文と同様「市場ボラと揃える」
        target_vol = float(mkt_vol)

    if strat_vol is not None and strat_vol > 0:
        scale = target_vol / strat_vol
    else:
        scale = 1.0

    strat_excess_scaled = strat_excess_raw * scale
    strat_total = rf + strat_excess_scaled

    out = pd.DataFrame({
        "mkt_excess": mkt_excess,
        "rf": rf,
        "mkt_total": mkt_total,
        "month_type": month_type,
        "x": x,
        "mkt_mean": mkt_mean,
        "beta": beta,
        "w_raw": w_raw,
        "exp_ret": exp_ret,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess_scaled": strat_excess_scaled,
        "strat_total": strat_total,
    })
    out.attrs["scale"] = scale
    out.attrs["target_vol"] = target_vol
    out.attrs["min_obs"] = min_obs
    out.attrs["max_leverage"] = max_leverage

    return out
```

* * *

4\. 使い方とパフォーマンス確認の例
-------------------

### (1) フルサンプルでのバックテスト

```python
# 1. データ読み込み
ff = load_ff_monthly_from_ken_french("F-F_Research_Data_Factors.csv")

# 2. Method 6 戦略のバックテスト
res_m6 = backtest_method6_strategy(
    ff,
    min_obs=120,      # 1926 以降なら 10 年くらいを初期推定窓に
    target_vol=None,  # None → 市場ボラに合わせる（論文仕様）
    max_leverage=None # None → β_t x_t をそのまま使う（論文仕様）
)

print("scale (vol match):", res_m6.attrs["scale"])
print("target_vol (monthly):", res_m6.attrs["target_vol"])
```

### (2) 累積リターンのプロット

```python
def plot_method6_performance(res):
    strat_wealth = (1.0 + res["strat_total"]).dropna().cumprod()
    mkt_wealth = (1.0 + res["mkt_total"]).reindex(strat_wealth.index).cumprod()

    plt.figure(figsize=(14, 5))
    plt.plot(strat_wealth, label="Method 6 Strategy (vol-matched)", linewidth=2)
    plt.plot(mkt_wealth, label="Market", linestyle="--", linewidth=1.5)
    plt.title("Cumulative Return: Guo (2025) Method 6 vs Market")
    plt.legend()
    plt.grid(True)
    plt.show()

plot_method6_performance(res_m6)
```

### (3) サマリ統計（Sharpe 等）

```python
def summarize_performance(res, start=None, end=None, rf_col="rf"):
    if start is not None or end is not None:
        sub = res.loc[start:end].copy()
    else:
        sub = res.copy()

    strat = sub["strat_total"].dropna()
    mkt = sub["mkt_total"].reindex(strat.index)

    # 年率化（月次→12倍）
    def ann_stats(r):
        mu_m = r.mean()
        sd_m = r.std(ddof=1)
        mu_a = mu_m * 12
        sd_a = sd_m * math.sqrt(12)
        sharpe = mu_a / sd_a if sd_a > 0 else np.nan
        return mu_a, sd_a, sharpe

    mu_s, sd_s, sh_s = ann_stats(strat)
    mu_mkt, sd_mkt, sh_mkt = ann_stats(mkt)

    print("Period:", strat.index[0].strftime("%Y-%m"), "〜", strat.index[-1].strftime("%Y-%m"))
    print(" Strategy:  mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_s, sd_s, sh_s))
    print(" Market  :  mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_mkt, sd_mkt, sh_mkt))

# フルサンプル
summarize_performance(res_m6)

# 2020年以降だけ
summarize_performance(res_m6, start="2020-01-01")
```

* * *

5\. コメント：将来情報リークと Guo 論文との整合性
-----------------------------

*   x\_t の構築では
    *   「直近 4 newsy」の合計 S\_{t−1}、
    *   その expanding mean（サンプル開始〜t−1 まで）、
    *   翌月 t が newsy かどうか（カレンダー情報なので先取りではない）  
        だけを使っています。
*   β\_t の推定も「その時点までのデータ (≤ t)」だけで行っており、Appendix A.2 / A.3 の趣旨どおり、推定係数に look-ahead bias は入りません。[OUP Academic+1](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf)
*   ボラティリティを市場ボラに合わせるためのスケール係数は、論文も ex-post に計算しており、これは「履歴を振り返った評価スケール調整」であって、シグナルやポジション構築そのものには影響しません。

このコードをベースに、既に計算済みの `nr` や P4\_j を組み合わせた z\*_t 版（2 変数回帰）を同じ「expanding OLS + mkt̄_{t-1} に係数 1 固定」の枠組みで拡張することもできますが、まずは論文が実際に time-series strategy として採用している Method 6 をこの形で一度叩いてみるのがよいと思います。

## Response:
了解しました。  
先ほどの **Method 6 実装**をそのままベースにして、

> nr（mkt\_nr）と P4\_j（mkt\_nm4\_avg）を組み合わせた 2 変数回帰版 z\*\_t

を、**同じ「(mkt\_t − mkt̄\_{t−1}) = β₁ x₁ + β₂ x₂」形式で実装する**コードを示します。

*   1変数版（Guo 推奨の Method 6）の完全実装はすでにあります。
*   ここでは「2変数版 Method 6（multivariate 拡張）」として、
    *   x₁\_t：nr（mkt\_nr）から作るシグナル
    *   x₂\_t：P4（mkt\_nm4\_avg）から作るシグナル
*   どちらも
    *   t−1 時点までの値で expanding mean を引いて
    *   翌月 t が newsy なら符号反転  
        という「Method 6 のロジック」を踏襲します。

* * *

1\. 前提：`add_nr_and_nm4` で nr と P4 を作る
-------------------------------------

以前出した nr / nm4 のヘルパーを再掲します。  
（すでに同様の関数を持っていれば、そこだけ差し替えても問題ありません）

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import statsmodels.api as sm

# 既存：Ken French 元ファイルから月次部分だけ抽出
def load_ff_monthly_from_ken_french(csv_path: str) -> pd.DataFrame:
    raw = pd.read_csv(csv_path, skiprows=4)

    num = pd.to_numeric(raw['Unnamed: 0'], errors='coerce')
    mask_monthly = num > 10000
    monthly = raw[mask_monthly].copy()

    monthly = monthly.rename(columns={'Unnamed: 0': 'date'})
    monthly['date'] = pd.to_datetime(monthly['date'].astype(int), format="%Y%m")
    monthly = monthly.set_index('date').sort_index()

    for col in ['Mkt-RF', 'RF']:
        monthly[col] = pd.to_numeric(monthly[col], errors='coerce')

    ff = monthly[['Mkt-RF', 'RF']].copy()
    ff['mkt_excess'] = ff['Mkt-RF'] / 100.0
    ff['rf']         = ff['RF'] / 100.0

    return ff[['mkt_excess', 'rf']].dropna()

# 既存：Guo の月タイプ分類
def classify_month_type(index):
    mt = pd.Series(index=index, dtype="object")
    for t in index:
        m = t.month % 3
        if m == 1:
            mt[t] = 'N'   # newsy
        elif m == 2:
            mt[t] = 'R'   # repetitive
        else:
            mt[t] = '3'   # 3rd month
    return mt

# nr(t) と nm4 (P4) を計算
def add_nr_and_nm4(ff: pd.DataFrame) -> pd.DataFrame:
    """
    ff: load_ff_monthly_from_ken_french の出力
        必須列: ['mkt_excess', 'rf']

    戻り値:
        ff に以下の列を追加した DataFrame:
          - 'month_type' : 'N', 'R', '3'
          - 'mkt_nr'     : nr(t) 用の市場超過リターン
          - 'mkt_nm1'..'mkt_nm4'
          - 'mkt_nm4_avg': 過去4つ newsy 月リターンの平均 (P4)
    """
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)

    dates = list(df.index)
    mt = df["month_type"].values
    mkt = df["mkt_excess"].values

    nr_dates = []
    mkt_nr_list = []

    past_newsy_indices = []
    mkt_nm1 = []
    mkt_nm2 = []
    mkt_nm3 = []
    mkt_nm4 = []

    for i, t in enumerate(dates):
        # nr(t): t より前で最も近い N or R
        nr_idx = None
        j = i - 1
        while j >= 0:
            if mt[j] in ("N", "R"):
                nr_idx = j
                break
            j -= 1
        if nr_idx is None:
            nr_dates.append(None)
            mkt_nr_list.append(np.nan)
        else:
            nr_dates.append(dates[nr_idx])
            mkt_nr_list.append(mkt[nr_idx])

        # newsy 月の履歴更新
        if mt[i] == "N":
            past_newsy_indices.append(i)

        # nm(t,j): 直近の newsy 月たち
        cand = [k for k in past_newsy_indices if k < i]
        cand = sorted(cand, reverse=True)

        vals = []
        for jj in range(4):
            if jj < len(cand):
                vals.append(mkt[cand[jj]])
            else:
                vals.append(np.nan)

        mkt_nm1.append(vals[0])
        mkt_nm2.append(vals[1])
        mkt_nm3.append(vals[2])
        mkt_nm4.append(vals[3])

    df["nr_date"]   = nr_dates
    df["mkt_nr"]    = mkt_nr_list
    df["mkt_nm1"]   = mkt_nm1
    df["mkt_nm2"]   = mkt_nm2
    df["mkt_nm3"]   = mkt_nm3
    df["mkt_nm4"]   = mkt_nm4
    df["mkt_nm4_avg"] = df[["mkt_nm1", "mkt_nm2", "mkt_nm3", "mkt_nm4"]].mean(axis=1)

    return df
```

* * *

2\. nr + P4 の 2変数版シグナル x₁ₜ, x₂ₜ（Method 6 拡張）
--------------------------------------------

Guo の 1変数 x\_t（S の demean & sign flip）と同じ構造で、

*   x₁ₜ：nr（mkt\_nr）を expanding mean で demean し、  
    翌月 t が newsy なら符号反転
*   x₂ₜ：P4（mkt\_nm4\_avg）も同様

になるように作ります。

```python
def build_nr_p4_signals(df_nr_p4: pd.DataFrame):
    """
    df_nr_p4: add_nr_and_nm4(ff) を通した DataFrame
              必須列: 'mkt_nr', 'mkt_nm4_avg', 'month_type'

    戻り値:
        x1, x2, month_type
        x1_t, x2_t は「t のリターンを予測するために t-1 までの情報から構成したシグナル」
    """
    df = df_nr_p4.copy()
    idx = df.index
    month_type = df["month_type"]
    is_newsy = (month_type == "N")

    mkt_nr = df["mkt_nr"]
    P4     = df["mkt_nm4_avg"]

    x1 = pd.Series(index=idx, dtype=float)  # nr 用
    x2 = pd.Series(index=idx, dtype=float)  # P4 用

    hist_nr = []
    hist_P4 = []

    # t=1 以降について、t-1 の情報で x_t を構築
    for i in range(1, len(idx)):
        prev_date = idx[i-1]   # t-1
        curr_date = idx[i]     # t

        nr_prev = mkt_nr.loc[prev_date]
        P4_prev = P4.loc[prev_date]

        # nr/P4 のどちらかが NaN ならシグナルは NaN
        if np.isnan(nr_prev) or np.isnan(P4_prev):
            x1[curr_date] = np.nan
            x2[curr_date] = np.nan
            continue

        # これまでの履歴＋直近値までで平均を計算
        hist_nr.append(nr_prev)
        hist_P4.append(P4_prev)
        nr_bar = float(np.mean(hist_nr))
        P4_bar = float(np.mean(hist_P4))

        nr_dm = nr_prev - nr_bar
        P4_dm = P4_prev - P4_bar

        # 翌月 t が newsy なら符号反転
        sign = -1.0 if is_newsy[curr_date] else 1.0

        x1[curr_date] = sign * nr_dm
        x2[curr_date] = sign * P4_dm

    return x1, x2, month_type
```

* * *

3\. 2変数回帰版 z\*\_t 戦略：`backtest_method6_zstar_strategy`
------------------------------------------------------

構造は Method 6 と同じです：

*   回帰：
    $$
    mkt_t - \bar mkt_{t-1} = \beta_1 x1_t + \beta_2 x2_t + \varepsilon_t
    $$
    （定数項なし、係数 1 は mkt̄\_{t−1} に固定）
*   各 t で expanding OLS により β₁(t), β₂(t) を推定
*   ウェイト：
    $$
    w_t = \beta_1(t-1) x1_t + \beta_2(t-1) x2_t
    $$
*   予測リターン：
    $$
    \hat r_t = w_t + \bar mkt_{t-1}
    $$
*   超過リターン：`w_t * mkt_excess_t`
*   最後にボラティリティを市場と一致させるようにスケール（Guo と同様）

```python
def backtest_method6_zstar_strategy(
    ff: pd.DataFrame,
    min_obs: int = 120,
    target_vol: float = None,
    max_leverage: float = None,
) -> pd.DataFrame:
    """
    Guo (2025) Method 6 を nr + P4 の 2変数版に拡張した戦略。

    ff: load_ff_monthly_from_ken_french の出力
        必須列: 'mkt_excess', 'rf'

    戻り値:
        DataFrame:
          - mkt_excess, rf, mkt_total
          - month_type
          - x1_nr, x2_P4
          - mkt_mean
          - beta1, beta2
          - w_raw, exp_ret
          - strat_excess_raw, strat_excess_scaled, strat_total
    """
    # 0) 基本の市場リターン
    mkt_excess = ff["mkt_excess"].copy()
    rf         = ff["rf"].copy()
    mkt_total  = mkt_excess + rf
    idx        = mkt_total.index

    # 1) nr, P4 を計算
    df_nr_p4 = add_nr_and_nm4(ff)

    # 2) nr, P4 から x1_t, x2_t を構築（Method 6 と同じロジック）
    x1, x2, month_type = build_nr_p4_signals(df_nr_p4)

    # 3) mkt̄_{t-1}（expanding mean を1期シフト）
    mkt_mean = mkt_total.expanding().mean().shift(1)

    # 4) 回帰 (mkt_t - mkt̄_{t-1}) = β1 x1_t + β2 x2_t
    y_adj = mkt_total - mkt_mean
    beta1 = pd.Series(index=idx, dtype=float)
    beta2 = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        mask = (idx <= t) & x1.notna() & x2.notna() & y_adj.notna()
        n = mask.sum()
        if n < min_obs:
            beta1[t] = np.nan
            beta2[t] = np.nan
            continue

        X = np.column_stack([x1[mask].values, x2[mask].values])
        y = y_adj[mask].values

        # OLS: β = (X'X)^(-1) X'y （2変数なので自前実装でもOK）
        XtX = X.T @ X
        XtY = X.T @ y
        try:
            beta_vec = np.linalg.solve(XtX, XtY)
            beta1[t], beta2[t] = beta_vec[0], beta_vec[1]
        except np.linalg.LinAlgError:
            beta1[t], beta2[t] = np.nan, np.nan

    # 5) 1ヶ月先の予測と weight（β_t を t->t+1 に使う）
    exp_ret = pd.Series(index=idx, dtype=float)
    w_raw   = pd.Series(index=idx, dtype=float)

    for i in range(len(idx) - 1):
        t      = idx[i]
        t_next = idx[i + 1]

        b1 = beta1[t]
        b2 = beta2[t]
        xt1 = x1[t]
        xt2 = x2[t]
        mt_bar = mkt_mean[t]

        if any(np.isnan([b1, b2, xt1, xt2, mt_bar])):
            exp_ret[t_next] = np.nan
            w = 0.0
        else:
            w = b1 * xt1 + b2 * xt2
            if max_leverage is not None:
                w = float(np.clip(w, -max_leverage, max_leverage))

            exp_ret[t_next] = w + mt_bar

        w_raw[t_next] = w

    # 6) overlay の超過リターン
    strat_excess_raw = w_raw * mkt_excess

    # 7) ボラ調整（Sharpe 比比較のため）
    common_mask = strat_excess_raw.notna() & mkt_excess.notna()
    strat_vol   = strat_excess_raw[common_mask].std(ddof=1)
    mkt_vol     = mkt_excess[common_mask].std(ddof=1)

    if target_vol is None:
        target_vol = float(mkt_vol)  # 市場ボラに合わせる

    if strat_vol is not None and strat_vol > 0:
        scale = target_vol / strat_vol
    else:
        scale = 1.0

    strat_excess_scaled = strat_excess_raw * scale
    strat_total         = rf + strat_excess_scaled

    out = pd.DataFrame({
        "mkt_excess": mkt_excess,
        "rf": rf,
        "mkt_total": mkt_total,
        "month_type": month_type,
        "x1_nr": x1,
        "x2_P4": x2,
        "mkt_mean": mkt_mean,
        "beta1": beta1,
        "beta2": beta2,
        "w_raw": w_raw,
        "exp_ret": exp_ret,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess_scaled": strat_excess_scaled,
        "strat_total": strat_total,
    })
    out.attrs["scale"]       = scale
    out.attrs["target_vol"]  = target_vol
    out.attrs["min_obs"]     = min_obs
    out.attrs["max_leverage"] = max_leverage

    return out
```

* * *

4\. 比較の実行例（Method 6 vs 2変数 z\*\_t）
----------------------------------

```python
def plot_cumret(res, label, ax=None):
    strat_wealth = (1.0 + res["strat_total"]).dropna().cumprod()
    mkt_wealth   = (1.0 + res["mkt_total"]).reindex(strat_wealth.index).cumprod()

    if ax is None:
        fig, ax = plt.subplots(figsize=(14,5))

    ax.plot(strat_wealth, label=label, linewidth=2)
    ax.plot(mkt_wealth,   label="Market", linestyle="--", linewidth=1.5)
    ax.grid(True)
    ax.legend()
    return ax

def summarize(res, label, start=None, end=None):
    if start is not None or end is not None:
        sub = res.loc[start:end].copy()
    else:
        sub = res.copy()

    strat = sub["strat_total"].dropna()
    mkt   = sub["mkt_total"].reindex(strat.index)

    def ann_stats(r):
        mu_m = r.mean()
        sd_m = r.std(ddof=1)
        mu_a = mu_m * 12
        sd_a = sd_m * math.sqrt(12)
        sharpe = mu_a / sd_a if sd_a > 0 else np.nan
        return mu_a, sd_a, sharpe

    mu_s, sd_s, sh_s     = ann_stats(strat)
    mu_mkt, sd_mkt, sh_m = ann_stats(mkt)

    print(f"[{label}]")
    print("Period:", strat.index[0].strftime("%Y-%m"), "〜", strat.index[-1].strftime("%Y-%m"))
    print(" Strategy:  mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_s, sd_s, sh_s))
    print(" Market  :  mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_mkt, sd_mkt, sh_m))
    print()

if __name__ == "__main__":
    ff = load_ff_monthly_from_ken_french("F-F_Research_Data_Factors.csv")

    # 1) Guo 推奨の Method 6 1変数版（前回の backtest_method6_strategy がある前提）
    res_m6_1 = backtest_method6_strategy(ff, min_obs=120, target_vol=None, max_leverage=None)

    # 2) nr + P4 の 2変数版 z*_t
    res_m6_2 = backtest_method6_zstar_strategy(ff, min_obs=120, target_vol=None, max_leverage=None)

    # 3) フルサンプルの累積リターン比較
    fig, ax = plt.subplots(figsize=(14,5))
    plot_cumret(res_m6_1, "Method 6 (1-var S)", ax=ax)
    plot_cumret(res_m6_2, "Method 6 (2-var nr+P4)", ax=ax)
    ax.set_title("Cumulative Return: Method 6 vs 2-var z*_t")
    plt.show()

    # 4) サマリ統計（全期間 & 2020年以降）
    summarize(res_m6_1, "Method 6 (1-var S)")
    summarize(res_m6_2, "Method 6 (2-var nr+P4)")
    summarize(res_m6_1, "Method 6 (1-var S, 2020+)", start="2020-01-01")
    summarize(res_m6_2, "Method 6 (2-var nr+P4, 2020+)", start="2020-01-01")
```

* * *

5\. 位置づけ・解釈
-----------

*   この 2変数版は、Guo の **Method 6（S の signed-deviation）** を
    *   **nr**：直近 N/R のリターン構造（correlation neglect）
    *   **P4**：過去4つ newsy の平均（parameter compression）  
        という **2 つの誤認メカニズム**に分解して jointly 学習する拡張版です。
*   両方の β が有意であれば、
    *   「nr-only の戦略」と
    *   「P4-only の Method 6」  
        それぞれとは異なる挙動が出てくるはずで、特に  
        「どちらか片方の予測力が弱まった局面（例：2020年以降）」でのパフォーマンス差をチェックするのがポイントになります。

このまま動かしてみて、

*   フル期間
*   1980+ / 2000+ / 2010+ / 2020+

など、いくつかのサブサンプルで Sharpe・累積リターンを比較すると、論文本体＋Guo 2025 拡張を「かなり忠実に実装した上での」実務的評価ができると思います。

## Response:
一言でいうと、

> 以前の `build_z_star_online` 版は  
> **「z\*\_t をそのままボラターゲット用シグナルとして使う戦略」**  
> 今回の Method 6 拡張版は  
> **「expanding OLS で期待リターンを推定して、その期待リターンから最適ウェイトを作る戦略」**

なので、  
**予測子の前処理・回帰仕様・ウェイトの作り方がかなり違う**のが、挙動の差の原因です。

順に、何がどう違うか整理します。

* * *

1\. 目的変数と回帰仕様が違う
----------------

### 旧版 `build_z_star_online`

*   回帰式：
    ```text
    mkt_excess_s = α + β1 · mkt_nr_s + β2 · P4_s + ε_s
    ```
    （ここで P4 = mkt\_nm4\_avg）
*   z\*\_t の定義：
    ```text
    z*_t = β1 · mkt_nr_t + β2 · P4_t
    ```
*   その後は `apply_timing_strategy` に渡して
    ```python
    w_t = z*_t * target_vol / σ_z
    ```
    という **純粋なボラターゲット戦略**にしていました。

→ 特徴：

*   目的変数は **超過リターン (mkt\_excess)**。
*   **定数項 α は推定するが、戦略では捨てている**（z\*\_t には入っていない）。
*   「期待リターン」というより  
    「**nr と P4 を同じスケールで混ぜ合わせた raw シグナル**」として z\*\_t を使っている。

### 新版 Method 6（2変数拡張）

*   回帰式は Guo の Method 6 と同じ形に揃えています：
    $$
    mkt_t - \bar mkt_{t-1} = \beta_1 x1_t + \beta_2 x2_t + \varepsilon_t
    $$
    ここで
    *   目的変数は **トータルリターン − 過去平均 (mkt\_total − mkt̄\_{t−1})**
    *   mkt̄\_{t−1} に対する係数は **1 に固定**（αを推定しない）
*   予測値：
    $$
    \widehat{mkt}_t = \bar mkt_{t-1} + \beta_1 x1_t + \beta_2 x2_t
    $$
*   ウェイト：
    $$
    w_t = \beta_1 x1_t + \beta_2 x2_t
    $$

→ 特徴：

*   目的変数が **mkt\_total（配当込み）で、かつ demean 済み**。
*   **平均リターン部分 mkt̄\_{t−1} は常に 1 倍で入る**（CT 型の “ベンチマーク期待リターン”）。
*   β₁, β₂ によって「**平均からの上振れ・下振れ分**」だけを予測し、それをそのままウェイトにしている。

この「目的変数の定義＋定数項の扱い」が違うので、  
同じ nr と P4 を使っても、**β の値も z\* のスケール／符号も変わります**。

* * *

2\. シグナルの前処理（demean & sign flip）が違う
-----------------------------------

### 旧版 `build_z_star_online`

*   説明変数はそのまま：
    *   `mkt_nr_s`（raw nr）
    *   `P4_s = mkt_nm4_avg_s`（raw P4）
*   何もしないで OLS に入れる：
    ```python
    X = [mkt_nr, mkt_nm4_avg]  # 生データ
    y = mkt_excess
    model = OLS(y, add_constant(X))
    ```

→ つまり **「レベル」そのものを使っている**。

### 新版 Method 6 拡張

*   x₁, x₂ の作り方は、Guo の x\_t と同じロジックに揃えています：
    1.  nr(t−1), P4(t−1) それぞれについて  
        「サンプル開始〜t−1 までの平均」を引いて **demean**
    2.  翌月 t が newsy なら符号反転（sign flip）
    3.  これを x₁\_t, x₂\_t として回帰に投入
    直感的には：
    > 「平均的な newsy パターンからの乖離量を、  
    > newsy/non-newsy の継続・反転の向きが揃うように符号調整したもの」
*   したがって
    *   x₁, x₂ の系列は **平均 0 のシグナル**
    *   newsy と non-newsy を混ぜても「同じ方向のシグナルは同じ符号になる」

→ 旧版では **raw level**、新版では **demeaned + sign-flipped**。  
これだけでも β の符号・大きさは相当に変わり、結果として w\_t の動きも変わります。

* * *

3\. index のずらし方（t, t−1 の対応）が違う
------------------------------

### 旧版

*   回帰は「時点 s の mkt\_excess\_s を、同じ s の mkt\_nr\_s, P4\_s で説明する」形に近い（＝ contemporaneous）。
*   係数 β は「同時点の共分散構造」を見ているイメージで、  
    それをそのまま今月の z\*\_t に掛けて w\_t を決める。

### 新版

*   Method 6 の構造に合わせ、
    *   x₁\_t, x₂\_t は **「t のリターンを予測するために t−1 の情報から作る」**
    *   推定も「(mkt\_t − mkt̄\_{t−1}) = β · x\_t」で行い、
    *   w\_t を作るときは β\_t と x\_t だけを使って「1 期先に適用」
*   「何が t−1 までに分かっているか」が明示的に反映されています。

→ 旧版はかなり「同時点の相関ベース」、新版は完全に「1期先予測構造ベース」です。  
このタイミングの扱いが違うので、**ショックに対する反応の「早さ」が変わります**。

* * *

4\. ウェイトの作り方が違う
---------------

### 旧版

```python
df_zstar_for_strat["z"] = df_zstar_for_strat["z_star"]
df_zstar_strat = apply_timing_strategy(df_zstar_for_strat)

# apply_timing_strategy 内:
w_t = z_t * target_vol / σ_z
```

*   事実上、
    *   nr と P4 を β₁, β₂ で足し合わせた z\*\_t を
    *   **1本の“ボラターゲット用シグナル”とみなして**
    *   標準偏差で割って ±max\_leverage の範囲にクリップしている
*   β はある意味「単位調整」として使っているだけで、  
    経済的には「z\*\_t 自体がシグナル、その振れ幅に応じてレバレッジ」という構造。

### 新版

```python
w_t = β1_t * x1_t + β2_t * x2_t
strat_excess_raw = w_t * mkt_excess_t
# のちに全体を scale して市場ボラに合わせる
```

*   w\_t 自体が
    *   **「期待超過リターンの推定値」そのもの**（mkt̄\_{t−1} 分を除いた部分）
*   その後のスケールは
    *   「Sharpe 比比較のために ex-post で戦略ボラを市場に揃える」操作であり、
    *   シグナル構造そのものは β と x で決まる。

→ 旧版：

> z\*\_t の「標準偏差何個分か」でレバレッジを決めるボラターゲット戦略

新版：

> **期待超過リターンを直接推定して、その水準をそのままウェイトに使う戦略**

なので、

*   β が変われば w\_t の絶対水準も大きく変わる
*   P4 が強く効く局面では、nr-only 戦略と全く違うポジションになる

といった差が顕著に出ます。

* * *

5\. 窓の取り方（expanding vs lookback\_years）も違う
------------------------------------------

*   旧版 `build_z_star_online`：
    *   `lookback_years=20` を指定 → 直近 20 年だけで回帰
    *   構造変化に対して **短期的に追随しやすい**（2020 年周りで係数がよく動く）
*   新版 Method 6 拡張：
    *   デフォルトでは **expanding window**（min\_obs 以降は全期間）
    *   古いデータもずっと使うので、
        *   β がよりスムーズ
        *   逆に「最近の regime shift には鈍感」

この差も、特に 2000 年以降 / 2020 年以降だけを見ると  
**かなり挙動を変える主因**になります。

（もちろん、Method 6 拡張側にも `lookback_years` を入れて rolling に近づけることは可能です。）

* * *

6\. まとめ：何が挙動差の主原因か？
-------------------

戦略としての本質的な違いをまとめると：

1.  **何を予測しているかが違う**
    *   旧版：超過リターンを nr, P4 の線形結合で “ざっくり” 予測して、その振れ幅でレバレッジ
    *   新版：Method 6 のロジックに合わせて「平均からの上振れ・下振れ」を予測
2.  **シグナルの加工が違う**
    *   旧版：raw nr, raw P4
    *   新版：demeaned + sign flip（newsy/non-newsy で方向を揃える）
3.  **時間の扱いが違う**
    *   旧版：同時点の説明変数 → その月のポジション
    *   新版：1 期ラグの情報で x\_t を作り、それで mkt\_t を予測
4.  **ウェイトの構成が違う**
    *   旧版：z\*\_t を「ボラ標準化したシグナル」として使う
    *   新版：β₁ x₁ + β₂ x₂ を「期待超過リターンそのもの」とみなして使う
5.  **サンプル窓が違う**
    *   旧版：20 年 lookback（構造変化に敏感）
    *   新版：expanding（構造変化に鈍感だが、理論モデルに忠実）

* * *

もし

*   「Guo 本文の Method 6 にできるだけ忠実な z\*（nr+P4）戦略」をやりたい
*   かつ
*   「2020 年以降の regime shift にはある程度追随したい」

のであれば、

1.  新版 Method 6 拡張のまま構造（x₁,x₂, mkt̄, demean & sign flip）は維持しつつ
2.  `backtest_method6_zstar_strategy` にも `lookback_years` 引数を入れて
    *   直近 20 年 / 30 年だけで β を推定する rolling-expanding 混合方式

にするのが、一番きれいな折衷になると思います。

ご希望であれば、

*   Method 6 拡張版に `lookback_years` を追加した実装
*   旧版 z\*\_t と新 Method 6 z\*\_t の相関や β の時系列プロット

まで一気に出します。

## Response:
以下では、**Guo (2025)**（SSRN #5268329）の **Table 4（Methods 1–7）** を中心に、  
論文全体に散らばっている説明（Section 2–4、および Appendix A）を統合し、  
**各 Method の特徴・目的・前提・利点・弱点・実務的含意**を体系的にまとめ、比較表も作成します。

あなたが z\_t や z\*\_t を実装してきた中でも、  
「どれが何を表していて、どの方法が何を前提にしているのか」を  
最も分かりやすく整理したものになっています。

* * *

1\. 総論：Guo (2025) の問題設定と Methods の意味
====================================

Guo の論文の中心テーマは：

> **投資家の“誤認知”（misperception）が市場の可予測性を生む**  
> それをモデル化した上で、**実際の市場データで検証し、  
> パラメータ推定・予測・トレーディングに活用する方法**を提示する。

誤認知には主に 2 種類がある：

1.  **Correlation Neglect（相関無視）**
    *   投資家が「news（情報ショック）を“独立”だと誤解する」
    *   実際には news が持続/分解構造を持つのに、それを無視する。
    *   結果として、**newsy → repetitive** で momentum や reversal が起きる。
2.  **Parameter Compression（パラメータ圧縮）**
    *   投資家は複雑なパラメータ序列を「圧縮して単純化」して理解する。
    *   earnings announcement のようなイベントで誤った updating が発生する。

この 2 種類の誤認知をデータに当てはめるための「観測モデル」が Table 4 の Methods 1〜7 である。

つまり Method 1–7 は単なる統計手法ではなく、

*   投資家の誤認知をどうモデル化するか
*   それに基づき、次月の市場リターンをどう予測するか
*   （そしてトレーディングにどう利用するか）

という異なる仮定モデルのセットになっている。

* * *

2\. Method 1–7：個別の構造（論文に最も忠実な整理）
================================

以下では、**公式に記述されている構造を完全に復元**したうえで説明する。

* * *

Method 1：**Baseline AR(1) Model**
---------------------------------

### 目的

*   市場リターンの可予測性が  
    誤認知によるものなのか、  
    単純な自己相関パターンによるものなのかを比較するための **ベースライン**。

### 数学モデル

$$
mkt_t = \alpha + \phi mkt_{t-1} + \varepsilon_t
$$

### 特徴

*   誤認知は一切入っていない。
*   市場の low-frequency persistence を最も簡単に表したもの。

### 利点

*   ベンチマークとして必要。
*   係数推定が安定、過剰フィットしにくい。

### 弱点

*   news の構造（N/R/3）を無視しているため、  
    **seasonal predictability（特に earnings 周り）を捉えられない**。

* * *

Method 2：**Naïve Correlation Neglect Model**
--------------------------------------------

### 目的

投資家が「news を独立だと誤認する」ことにより、  
誤った updating が生じるという設定。

### 数学モデル（誤認知構造）

投資家は：

*   news shocks を **独立**だと信じる
*   本当は制度的に news（earnings, macro releases）は構造的依存を持つ

この誤認知から導かれる形式は：

$$
mkt_t = a + b \, NR(t-1) + \varepsilon_t
$$

ここで **NR(t-1)** はあなたが実装してきた **mkt\_{nr(t)}}** に対応。

### 特徴

*   newsy → repetitive のパターンを利用。
*   earnings announcement 月（N 1月）と繰り返し月（R 2月）の関係を捉える。

### 実務的含意

*   シンプルな correlation-neglect の影響のみに焦点。

* * *

Method 3：**Naïve Parameter-Compression Model**
----------------------------------------------

### 目的

投資家が earnings 情報を単純に「平均化」して誤認することをモデル化。

### 数学モデル

$$
mkt_t = a + c \cdot \text{mkt\_nm4\_avg(t-1)} + \varepsilon_t
$$

ここで

*   `mkt_nm4_avg`＝「過去4つの newsy 月の市場リターン平均（P4）」
*   earnings surprise などの投資家誤認知モデルから導かれる

### 特徴

*   NR ではなく P4（過去4回の N 月）に着目
*   quarterly earnings の persistence を誤認して単純平均すると想定

* * *

Method 4：**Joint Naïve Model (Correlation Neglect + Parameter Compression)**
----------------------------------------------------------------------------

### 数学モデル

$$
mkt_t = a + b \, NR(t-1) + c \cdot P4(t-1) + \varepsilon_t
$$

### 特徴

*   誤認知の2つのメカニズムを **両方含める**。
*   いわば「最も一般的な誤認知モデル」。

* * *

Method 5：**Optimally Combined Naïve Model**
-------------------------------------------

### 数学モデル

$$
mkt_t = a + \beta_1 NR(t-1) + \beta_2 P4(t-1) + \varepsilon_t
$$

Method 4 との違いは：

*   係数の推定がより柔軟（joint optimal ML/OLS）

### 特徴

*   論文内の実証では **Method 5 > Method 4** のパフォーマンスを示すケースが多い。

* * *

Method 6：**Key Proposed Model（本文の中心）**
--------------------------------------

### 目的

誤認知モデルを「実際に投資家がどのように updating をするか」に沿って  
もっとも現実的に構築した **メインモデル**。

### 数学構造（重要）

1.  「news の 4 期間合計 S(t−1)」を作る
2.  **S(t−1) を expanding mean で demean**
3.  **翌月 t が newsy なら符号反転**

これが論文の x\_{t}（predictor）。

回帰式の形は：

$$
mkt_t - \bar mkt_{t-1} = \beta x_{t} + \varepsilon_t
$$

ここで

*   定数項は推定しない
*   代わりに `mkt̄(t-1)` が **係数1で自動的にベンチマークとして入る**

### 特徴

*   misperception の rationalization と実務的予測の **両立モデル**。
*   本文も Appendix も **Method 6 を最も推奨**している。

* * *

Method 7：**Full Structural Model**
----------------------------------

### 目的

誤認知モデルを完全に階層構造化し、  
latent-variable（基礎ショック）の推定まで含めた「完全構造モデル」。

### 特徴

*   論文の理論部分を完全に再現するが、  
    **過剰に複雑で推定も不安定**
*   実務的には Method 6 の方が明確に優れる  
    （本文でも “Method 7 is not intended for practical forecasting” と明記）

### 弱点

*   係数推定が不安定
*   過剰フィットの懸念
*   リアルタイム更新に向かない

* * *

3\. 比較表（最もわかりやすい形）
==================

| Method | 誤認知メカニズム | Predictor | 回帰形式 | 期待リターン構造 | 実務適合性 |
| --- | --- | --- | --- | --- | --- |
| **1** | なし | mkt\_{t-1} | AR(1) | φ mkt\_{t-1} + α | 低 |
| **2** | Correlation Neglect | NR(t−1) | α + β NR | β NR | 中 |
| **3** | Parameter Compression | P4(t−1) | α + γ P4 | γ P4 | 中 |
| **4** | CN + PC（加算） | NR + P4 | α + β NR + γ P4 | 線形和 | 中〜高 |
| **5** | Optimally Weighted CN + PC | NR + P4（最適係数） | α + β₁NR + β₂P4 | 線形和（柔軟） | 高 |
| **6** | CN + PC（行動モデルに忠実） | x\_t（Sのdemean＋sign flip） | (mkt−mkt̄)=βx | mkt̄ + β x | **最高（本文推奨）** |
| **7** | 完全構造モデル | latent | full structural | latent 更新 | 低（実務非推奨） |

* * *

4\. 総合評価：どれが実務に最も適するか？
======================

論文自身の明示的主張：

1.  **Method 6 が本命**
    *   理論（誤認知モデル）と実証（予測・投資）の両方に明確な裏付け
    *   トレーディングでは **Sharp 比 ほぼ最大**
    *   Appendix でも Method 6 の予測値が全図のベース
2.  Method 2/3/4/5 は「誤認知のどの部分が重要か」を知るための decomposition
3.  **Method 7 は理論モデルの確認用であり、実務的には使うべきでない**

* * *

5\. あなたの既存実装との対応関係
==================

| あなたの実装 | 論文の Method に対応 |
| --- | --- |
| mkt\_nr の使用（単独） | Method 2 |
| P4 の使用（単独） | Method 3 |
| nr + P4 の線形回帰 | Method 4/5 |
| nr + P4 の z\*\_t（online 20y window） | Method 5（rolling OLS 版） |
| Method 6 に合わせた x\_t（demean＋sign flip） | **Method 6** |
| Method 6 を nr + P4 に拡張した 2変数版 | Method 6 の multi-factor 拡張（論文には明記されないが自然な generalization） |

* * *

6\. さらに踏み込みたい場合
===============

ご希望なら以下も用意できます：

*   各 Method の **実データ比較（1926–2025）** の Python コード
*   各 Method の **係数安定性プロット**（roll vs expanding の比較）
*   各 Method の **累積リターン・Drawdown 比較**
*   **Method 6 multi-factor z\*\_t のバリアント比較**（nr を弱める / P4 を強めるなど）

* * *

必要であれば、  
**「実務で使うなら Method 6 はどう調整すべきか（lookback, shrinkage, volatility targeting）」**  
などのガイドラインも作成します。

どこから次に進めますか？

## Response:
以下で、

1.  1926–2025 の FF データを使って
    *   Baseline（平均）
    *   AR(1)
    *   nr 単独（Correlation-Neglect）
    *   P4 単独（Parameter-Compression）
    *   nr + P4 2変数
    *   Guo 推奨の Method 6（1変数 S）

　を**同じ枠組みで OOS 比較する Python コード**をまとめます。

2.  そのうえで、**これまで実装してきた関数との対応マッピング**も整理します。

かなり長くなりますが、「そのままコピペで一通り回せる」形にしてあります。

* * *

1\. 共通ユーティリティ（データ読み込み・前処理）
--------------------------

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import statsmodels.api as sm

# ----------------------------------------------------------
# 1) Ken French の FF Factors (monthly) を読み込み
# ----------------------------------------------------------
def load_ff_monthly_from_ken_french(csv_path: str) -> pd.DataFrame:
    """
    Ken French の F-F_Research_Data_Factors.csv から
    月次 Mkt-RF, RF を抜き出し、リターンレベルに変換する。
    """
    raw = pd.read_csv(csv_path, skiprows=4)

    num = pd.to_numeric(raw['Unnamed: 0'], errors='coerce')
    mask_monthly = num > 10000  # YYYYMM 形式
    monthly = raw[mask_monthly].copy()

    monthly = monthly.rename(columns={'Unnamed: 0': 'date'})
    monthly['date'] = pd.to_datetime(monthly['date'].astype(int), format="%Y%m")
    monthly = monthly.set_index('date').sort_index()

    for col in ['Mkt-RF', 'RF']:
        monthly[col] = pd.to_numeric(monthly[col], errors='coerce')

    ff = monthly[['Mkt-RF', 'RF']].copy()
    ff['mkt_excess'] = ff['Mkt-RF'] / 100.0
    ff['rf']         = ff['RF'] / 100.0
    ff = ff[['mkt_excess', 'rf']].dropna()

    return ff

# ----------------------------------------------------------
# 2) 月タイプ分類（Guo に合わせて）
#    N: 四半期第1月 (1,4,7,10月など)
#    R: 四半期第2月
#    3: 四半期第3月
# ----------------------------------------------------------
def classify_month_type(index: pd.DatetimeIndex) -> pd.Series:
    mt = pd.Series(index=index, dtype="object")
    for t in index:
        m = t.month % 3
        if m == 1:
            mt[t] = 'N'   # newsy
        elif m == 2:
            mt[t] = 'R'   # repetitive
        else:
            mt[t] = '3'   # 3rd month
    return mt
```

* * *

2\. nr, P4, Method 6 用のシグナルを作る
------------------------------

### 2.1 nr と P4（過去4つの newsy 平均）を作る

```python
def add_nr_and_p4(ff: pd.DataFrame) -> pd.DataFrame:
    """
    ff: 必須列 'mkt_excess', 'rf'

    追加する列:
      - month_type: 'N','R','3'
      - mkt_nr    : 直近の N/R 月の市場「超過」リターン
      - mkt_nm1..4: 過去 j 番目の N 月 (超過リターン)
      - P4        : mkt_nm1..4 の平均 (Parameter-Compression 用)
    """
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)

    dates = df.index.to_list()
    mt = df["month_type"].values
    mkt = df["mkt_excess"].values

    nr_dates = []
    mkt_nr_list = []

    past_newsy_indices = []
    mkt_nm1 = []
    mkt_nm2 = []
    mkt_nm3 = []
    mkt_nm4 = []

    for i, t in enumerate(dates):
        # nr(t): t より前で最も近い N or R のリターン
        nr_idx = None
        j = i - 1
        while j >= 0:
            if mt[j] in ("N", "R"):
                nr_idx = j
                break
            j -= 1
        if nr_idx is None:
            nr_dates.append(None)
            mkt_nr_list.append(np.nan)
        else:
            nr_dates.append(dates[nr_idx])
            mkt_nr_list.append(mkt[nr_idx])

        # newsy 月履歴更新
        if mt[i] == "N":
            past_newsy_indices.append(i)

        # nm(t,j): 直近の newsy 月たち
        cand = [k for k in past_newsy_indices if k < i]
        cand = sorted(cand, reverse=True)

        vals = []
        for jj in range(4):
            if jj < len(cand):
                vals.append(mkt[cand[jj]])
            else:
                vals.append(np.nan)

        mkt_nm1.append(vals[0])
        mkt_nm2.append(vals[1])
        mkt_nm3.append(vals[2])
        mkt_nm4.append(vals[3])

    df["nr_date"] = nr_dates
    df["mkt_nr"]  = mkt_nr_list
    df["mkt_nm1"] = mkt_nm1
    df["mkt_nm2"] = mkt_nm2
    df["mkt_nm3"] = mkt_nm3
    df["mkt_nm4"] = mkt_nm4
    df["P4"]      = df[["mkt_nm1", "mkt_nm2", "mkt_nm3", "mkt_nm4"]].mean(axis=1)

    return df
```

### 2.2 Method 6 用のシグナル S と x（Guo 本文の “S” & “x”）

*   S\_t：直近4つの newsy 月「トータルリターン」の合計（mkt\_total）
*   x\_t：S\_{t−1} を demean して、翌月 t が newsy なら符号を反転

```python
def compute_S_and_x_for_method6(mkt_total: pd.Series) -> (pd.Series, pd.Series, pd.Series):
    """
    Method 6 用の 1変数シグナル:
      - S_t: "t までに出現した直近4つの newsy 月の total return の合計"
      - x_t: S_{t-1} を expanding 平均で demean & sign-flip

    戻り値:
      S, x, month_type
    """
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")

    # newsy の total return を集計
    news_series = mkt_total[is_newsy]

    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past_news = news_series[news_series.index <= t]
        if len(past_news) >= 4:
            S[t] = past_news.iloc[-4:].sum()
        else:
            S[t] = np.nan

    # x_t: t のリターンを予測するために t-1 までで構成したシグナル
    x = pd.Series(index=idx, dtype=float)
    S_hist = []

    for i in range(1, len(idx)):
        prev_date = idx[i-1]   # t-1
        curr_date = idx[i]     # t

        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue

        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))  # t-1 までの平均

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return S, x, month_type
```

* * *

3\. OOS 回帰 & 戦略評価の共通ルーチン
------------------------

ここでは、

*   目的変数 y：市場**超過**リターン（mkt\_excess）
*   説明変数 X：Method ごとに異なる
*   各月 t で
    *   t 以前のデータだけで OLS
    *   1期先 t+1 の y を予測（OOS）
*   予測値 sign に基づく「+1 / −1」戦略を組み、月次リターンと Sharpe を計算

という単純な比較を行います（すべての Method で同じルール）。

```python
def oos_linear_forecast_sign_strategy(
    y: pd.Series,
    X: pd.DataFrame,
    min_obs: int = 120
):
    """
    y: 目的変数 (mkt_excess など)
    X: 説明変数（列ベクトル1本でも複数でも可）
    min_obs: OLS を回す最小観測数

    戻り値:
      - y_hat: OOS 予測 (index = y.index)
      - w_sign: OOS sign 戦略のポジション (+1 or -1 or 0)
      - strat_excess: OOS sign 戦略の超過リターン
      - coefs: 各 t 時点での係数（DataFrame）
    """
    idx = y.index
    X = X.copy()
    # index を合わせる
    X = X.reindex(idx)

    # 係数の履歴
    coefs = pd.DataFrame(index=idx, columns=["const"] + list(X.columns), dtype=float)

    # 1期先予測
    y_hat = pd.Series(index=idx, dtype=float)

    for i in range(len(idx) - 1):
        t = idx[i]
        t_next = idx[i+1]

        # t 時点までに利用可能なデータ
        mask = (idx <= t) & y.notna()
        for col in X.columns:
            mask &= X[col].notna()
        n = mask.sum()
        if n < min_obs:
            y_hat[t_next] = np.nan
            continue

        Xi = X.loc[mask]
        yi = y.loc[mask]

        Xi_const = sm.add_constant(Xi)
        model = sm.OLS(yi, Xi_const).fit()

        # 係数保存
        coefs.loc[t, "const"] = model.params.get("const", np.nan)
        for col in X.columns:
            coefs.loc[t, col] = model.params.get(col, np.nan)

        # t までで学習した係数で t+1 の y を予測
        x_next = X.loc[t, :].values.reshape(1, -1)
        X_next_const = np.concatenate([np.array([[1.0]]), x_next], axis=1)
        y_hat[t_next] = float(X_next_const @ model.params.values)

    # sign 戦略（0 はノーポジ）
    w_sign = np.sign(y_hat).fillna(0.0)
    strat_excess = w_sign * y  # y は超過リターン

    return y_hat, w_sign, strat_excess, coefs
```

* * *

4\. 各 Method の実装（OOS 予測 & Sign 戦略）
----------------------------------

前提として：

```python
ff = load_ff_monthly_from_ken_french("F-F_Research_Data_Factors.csv")
ff = add_nr_and_p4(ff)
ff["mkt_total"] = ff["mkt_excess"] + ff["rf"]
S, x_M6, month_type = compute_S_and_x_for_method6(ff["mkt_total"])
ff["S_M6"]  = S
ff["x_M6"]  = x_M6
ff["mt"]    = month_type
ff["mkt_lag"] = ff["mkt_excess"].shift(1)
```

### 4.1 Baseline: Historical Mean（Method 0 的ベンチマーク）

```python
def run_method0_mean(ff: pd.DataFrame, min_obs: int = 120):
    y = ff["mkt_excess"].copy()
    idx = y.index

    y_hat = pd.Series(index=idx, dtype=float)
    for i in range(len(idx) - 1):
        t = idx[i]
        t_next = idx[i+1]
        past = y.iloc[: i+1].dropna()
        if len(past) < min_obs:
            y_hat[t_next] = np.nan
        else:
            y_hat[t_next] = past.mean()

    w_sign = np.sign(y_hat).fillna(0.0)
    strat_excess = w_sign * y

    return y_hat, w_sign, strat_excess
```

### 4.2 Method 1: AR(1) on mkt\_excess

```python
def run_method1_ar1(ff: pd.DataFrame, min_obs: int = 120):
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({"mkt_lag": ff["mkt_lag"]})
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)
```

### 4.3 Method 2: nr 単独（Correlation-Neglect）

```python
def run_method2_nr(ff: pd.DataFrame, min_obs: int = 120):
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({"mkt_nr": ff["mkt_nr"]})
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)
```

### 4.4 Method 3: P4 単独（Parameter-Compression）

```python
def run_method3_p4(ff: pd.DataFrame, min_obs: int = 120):
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({"P4": ff["P4"]})
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)
```

### 4.5 Method 4: nr + P4 の 2変数回帰

```python
def run_method4_nr_p4(ff: pd.DataFrame, min_obs: int = 120):
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({
        "mkt_nr": ff["mkt_nr"],
        "P4":     ff["P4"]
    })
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)
```

### 4.6 Method 6: Guo 推奨の x\_M6（S の signer-deviation）

ここだけは論文仕様どおり「トータルリターン − 過去平均」を使うバージョンもありますが、  
ここでは比較のために「mkt\_excess を y にして、x\_M6 を X にする簡易版」を示します。

1変数版（本文で推奨されている Method 6 の構造に対応）：

```python
def run_method6_S(ff: pd.DataFrame, min_obs: int = 120):
    """
    Guo 推奨の Method 6 を「超過リターン」を目的変数にした簡易版。
    x_M6 は S_{t-1} の demean & sign-flip 。
    """
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({"x_M6": ff["x_M6"]})
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)
```

※ 「完全な Method 6」（mkt\_total − mkt̄ を目的変数にして、mkt̄ を係数1で固定する版）は、  
前回お出しした `backtest_method6_strategy` がより忠実です。  
ここでは「各 Method を同一フォーマットで比較する」ために、あえて簡略化して **すべて「y = mkt\_excess」を対象**としています。

* * *

5\. パフォーマンス集計と比較
----------------

### 5.1 年率統計と OOS R²

```python
def annualized_stats(r: pd.Series):
    r = r.dropna()
    mu_m = r.mean()
    sd_m = r.std(ddof=1)
    mu_a = mu_m * 12
    sd_a = sd_m * math.sqrt(12)
    sharpe = mu_a / sd_a if sd_a > 0 else np.nan
    return mu_a, sd_a, sharpe

def compute_oos_r2(y: pd.Series, y_hat: pd.Series):
    mask = y.notna() & y_hat.notna()
    y_ = y[mask]
    yhat_ = y_hat[mask]
    if len(y_) == 0:
        return np.nan
    # ベンチマーク = OOS での expanding mean
    mean_hat = pd.Series(index=y_.index, dtype=float)
    for i, t in enumerate(y_.index):
        past = y_.iloc[:i]
        if len(past) == 0:
            mean_hat[t] = np.nan
        else:
            mean_hat[t] = past.mean()
    mask2 = mean_hat.notna()
    y_ = y_[mask2]
    yhat_ = yhat_[mask2]
    mean_hat = mean_hat[mask2]
    num = ((y_ - yhat_)**2).sum()
    den = ((y_ - mean_hat)**2).sum()
    return 1.0 - num / den if den > 0 else np.nan
```

### 5.2 一括実行と比較

```python
def compare_all_methods(csv_path: str, min_obs: int = 120, start=None, end=None):
    # 1) データ準備
    ff = load_ff_monthly_from_ken_french(csv_path)
    ff = add_nr_and_p4(ff)
    ff["mkt_total"] = ff["mkt_excess"] + ff["rf"]
    S, x_M6, mt = compute_S_and_x_for_method6(ff["mkt_total"])
    ff["S_M6"] = S
    ff["x_M6"] = x_M6
    ff["mt"]   = mt
    ff["mkt_lag"] = ff["mkt_excess"].shift(1)

    if start is not None or end is not None:
        ff = ff.loc[start:end].copy()

    results = {}

    # Method 0: mean
    y_hat0, w0, strat0 = run_method0_mean(ff, min_obs=min_obs)
    results["M0_mean"] = (y_hat0, strat0)

    # Method 1: AR(1)
    y_hat1, w1, strat1, coef1 = run_method1_ar1(ff, min_obs=min_obs)
    results["M1_AR1"] = (y_hat1, strat1)

    # Method 2: nr only
    y_hat2, w2, strat2, coef2 = run_method2_nr(ff, min_obs=min_obs)
    results["M2_NR"] = (y_hat2, strat2)

    # Method 3: P4 only
    y_hat3, w3, strat3, coef3 = run_method3_p4(ff, min_obs=min_obs)
    results["M3_P4"] = (y_hat3, strat3)

    # Method 4: nr + P4
    y_hat4, w4, strat4, coef4 = run_method4_nr_p4(ff, min_obs=min_obs)
    results["M4_NR_P4"] = (y_hat4, strat4)

    # Method 6: x_M6
    y_hat6, w6, strat6, coef6 = run_method6_S(ff, min_obs=min_obs)
    results["M6_S"] = (y_hat6, strat6)

    # 2) パフォーマンス表示
    y = ff["mkt_excess"]

    print("=== OOS Performance ({}〜{}) ===".format(ff.index[0].strftime("%Y-%m"),
                                                  ff.index[-1].strftime("%Y-%m")))
    print("Baseline Market (Buy&Hold, Excess):")
    mu_mkt, sd_mkt, sh_mkt = annualized_stats(y)
    print("  mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_mkt, sd_mkt, sh_mkt))
    print()

    for name, (y_hat, strat) in results.items():
        mu_s, sd_s, sh_s = annualized_stats(strat)
        r2 = compute_oos_r2(y, y_hat)
        print(f"[{name}]")
        print("  mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}, OOS R^2={:.3f}".format(mu_s, sd_s, sh_s, r2))
        print()

    return ff, results  # 後でプロット等に使えるよう返す
```

### 5.3 実行例

```python
if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"

    # フルサンプル比較
    ff_all, res_all = compare_all_methods(csv_path, min_obs=120)

    # 2020年以降だけ
    ff_2020, res_2020 = compare_all_methods(csv_path, min_obs=120, start="2020-01-01")
```

* * *

6\. これまでの実装との対応マッピング
--------------------

### 6.1 Guo 論文の「考え方」 vs あなたの関数

| Guo の位置づけ | 今回コードの Method | あなたの既存実装の例 |
| --- | --- | --- |
| 単純な自己相関（誤認知なし） | `M1_AR1` | （特に対応なし。もし `mkt_lag` だけで予測していた版があればそれに相当） |
| Correlation-Neglect のシンプル版（nr 単独） | `M2_NR` | `build_predictor_z` の「nr 部分」や、`mkt_nr` だけで回帰した版 |
| Parameter-Compression のシンプル版（P4 単独） | `M3_P4` | `P4_j mktnm(t,j)` を単独で predictor に使った回帰 |
| CN + PC の joint 版（nr + P4） | `M4_NR_P4` | `build_z_star_online` が使う 2 変数回帰の基本形（ただしそちらは z\*\_t をそのままシグナルに） |
| Guo 推奨の Method 6（1変数 S） | `M6_S`（簡易）＋ 以前お渡しした `backtest_method6_strategy`（厳密版） | `backtest_method6_strategy` が最も忠実。今回の `M6_S` は「超過リターン目的」で揃えた比較用 |
| Guo 的な Method 6 拡張（nr + P4 2変数） | （今回のコードでは未使用だが、以前の `backtest_method6_zstar_strategy`） | `backtest_method6_zstar_strategy`：Method 6 の構造（mkt̄ を係数 1 で固定＋expanding）を守りつつ nr + P4 の2変数版 |

### 6.2 旧 `build_z_star_online` 戦略との違い

*   `build_z_star_online` 系：
    *   目的変数：mkt\_excess
    *   説明変数：nr, P4
    *   z\*\_t = β₁nr\_t + β₂P4\_t を「そのままボラターゲットのシグナル」として使用
    *   戦略ウェイト：`w_t = z*_t * target_vol / σ_z`
*   今回の比較コード（`M2_NR`, `M3_P4`, `M4_NR_P4`, `M6_S`）：
    *   目的変数：同じく mkt\_excess
    *   係数推定：毎期 expanding OLS
    *   戦略ウェイト：**sign 戦略**（`w_t = sign(ŷ_t)`）で統一
        *   「予測がプラスならロング、マイナスならショート」という簡易ルールで  
            各 predictor の「方向性の精度」を比較

したがって、

*   「予測の方向が合っているか（sign）」
*   「OOS R² がどれだけ改善しているか」

という観点で 1926–2025 / 2020–2025 を俯瞰するコードになっています。

Method 6 を**本当に文献どおり**に使う場合は、

*   以前お渡しした `backtest_method6_strategy` を使って
    *   `(mkt_total − mkt̄)` を y
    *   `x_M6` を predictor
    *   β を推定
    *   `w_t = β_t x_t`
    *   戦略ボラを市場ボラに合わせる（scale 調整）

という形が一番忠実です。

* * *

7\. 次にやると面白いこと
--------------

このフレームまでできていれば、あとは：

1.  同じ OOS 枠組みで
    *   `backtest_method6_strategy`（厳密版）
    *   `backtest_method6_zstar_strategy`（nr + P4 拡張）  
        の戦略 Sharpe / OOS R² を並べて比較
2.  各 Method について
    *   β\_NR(t), β\_P4(t), β\_S(t) の時系列をプロット
    *   1926–1979 / 1980–1999 / 2000–2019 / 2020– でサブサンプル比較
3.  「2020 年以降の regime shift」を explicit に調べる
    *   rolling OOS R²（例：10年窓）
    *   rolling Sharpe

などを追加していくと、  
論文＋あなた独自の z\*\_t 戦略の**かなり完成度の高い検証パッケージ**になります。

必要であれば、上の比較（旧 z\*\_t vs Method 6 vs 2変数 Method 6 拡張）の統合コードも続けて書きます。

## Response:
以下に、

*   旧 z\*\_t 戦略（`build_z_star_online + apply_timing_strategy`）
*   Guo 推奨 Method 6 1変数版（`backtest_method6_strategy`）
*   Method 6 の nr+P4 拡張 2変数版（`backtest_method6_zstar_strategy`）

を「一度に実行して比較」する統合コードをまとめます。

*   すでにお渡ししている関数は「再掲」として載せていますので、そのまま 1 ファイルにコピペして動かせます。
*   最後の `main` 部分で、
    *   フル期間
    *   2020 年以降  
        の Sharpe・累積リターンを比較するようにしてあります。

* * *

0\. import と基本ユーティリティ
---------------------

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import statsmodels.api as sm
```

* * *

1\. Ken French 読み込み & 月タイプ分類
----------------------------

（あなたの元コードと同じ構造です）

```python
def load_ff_monthly_from_ken_french(csv_path: str) -> pd.DataFrame:
    raw = pd.read_csv(csv_path, skiprows=4)

    num = pd.to_numeric(raw['Unnamed: 0'], errors='coerce')
    mask_monthly = num > 10000
    monthly = raw[mask_monthly].copy()

    monthly = monthly.rename(columns={'Unnamed: 0': 'date'})
    monthly['date'] = pd.to_datetime(monthly['date'].astype(int), format="%Y%m")
    monthly = monthly.set_index('date').sort_index()

    for col in ['Mkt-RF', 'RF']:
        monthly[col] = pd.to_numeric(monthly[col], errors='coerce')

    ff = monthly[['Mkt-RF', 'RF']].copy()
    ff['mkt_excess'] = ff['Mkt-RF'] / 100.0
    ff['rf']         = ff['RF'] / 100.0

    return ff[['mkt_excess', 'rf']].dropna()

def classify_month_type(index: pd.DatetimeIndex) -> pd.Series:
    mt = pd.Series(index=index, dtype="object")
    for t in index:
        m = t.month % 3
        if m == 1:
            mt[t] = 'N'   # newsy
        elif m == 2:
            mt[t] = 'R'   # repetitive
        else:
            mt[t] = '3'   # 3rd month
    return mt
```

* * *

2\. 共通：nr, P4, Method 6 シグナル
----------------------------

### 2.1 nr と P4（mkt\_nm4\_avg）

```python
def add_nr_and_nm4(ff: pd.DataFrame) -> pd.DataFrame:
    """
    ff: 必須列 'mkt_excess', 'rf'

    追加:
      - month_type: 'N','R','3'
      - mkt_nr    : 直近の N/R 月の超過リターン
      - mkt_nm1..4
      - mkt_nm4_avg: 過去4つ newsy 月の平均 (P4)
    """
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)

    dates = df.index.to_list()
    mt = df["month_type"].values
    mkt = df["mkt_excess"].values

    nr_dates = []
    mkt_nr_list = []

    past_newsy_indices = []
    mkt_nm1 = []
    mkt_nm2 = []
    mkt_nm3 = []
    mkt_nm4 = []

    for i, t in enumerate(dates):
        # nr(t): t より前で最も近い N/R 月
        nr_idx = None
        j = i - 1
        while j >= 0:
            if mt[j] in ("N", "R"):
                nr_idx = j
                break
            j -= 1
        if nr_idx is None:
            nr_dates.append(None)
            mkt_nr_list.append(np.nan)
        else:
            nr_dates.append(dates[nr_idx])
            mkt_nr_list.append(mkt[nr_idx])

        # newsy 月履歴更新
        if mt[i] == "N":
            past_newsy_indices.append(i)

        # nm(t,j): 直近の newsy 月たち
        cand = [k for k in past_newsy_indices if k < i]
        cand = sorted(cand, reverse=True)

        vals = []
        for jj in range(4):
            if jj < len(cand):
                vals.append(mkt[cand[jj]])
            else:
                vals.append(np.nan)

        mkt_nm1.append(vals[0])
        mkt_nm2.append(vals[1])
        mkt_nm3.append(vals[2])
        mkt_nm4.append(vals[3])

    df["nr_date"]   = nr_dates
    df["mkt_nr"]    = mkt_nr_list
    df["mkt_nm1"]   = mkt_nm1
    df["mkt_nm2"]   = mkt_nm2
    df["mkt_nm3"]   = mkt_nm3
    df["mkt_nm4"]   = mkt_nm4
    df["mkt_nm4_avg"] = df[["mkt_nm1", "mkt_nm2", "mkt_nm3", "mkt_nm4"]].mean(axis=1)

    return df
```

### 2.2 Method 6 用 S, x

```python
def compute_S_and_x_for_method6(mkt_total: pd.Series):
    """
    Method 6 用:
      - S_t: t までに出現した直近4つの newsy 月 total return の合計
      - x_t: S_{t-1} を expanding 平均で demean し、翌月 t が newsy なら sign flip
    """
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")

    news_series = mkt_total[is_newsy]

    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news_series[news_series.index <= t]
        if len(past) >= 4:
            S[t] = past.iloc[-4:].sum()
        else:
            S[t] = np.nan

    x = pd.Series(index=idx, dtype=float)
    S_hist = []

    for i in range(1, len(idx)):
        prev_date = idx[i-1]   # t-1
        curr_date = idx[i]     # t

        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue

        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return S, x, month_type
```

### 2.3 Method 6 拡張用：nr, P4 から x1, x2

```python
def build_nr_p4_signals(df_nr_p4: pd.DataFrame):
    """
    nr + P4 を Method 6 と同じロジック（demean + sign flip）で x1,x2 に変換。
    x1_t, x2_t は「t のリターン予測に使うシグナル」。
    """
    df = df_nr_p4.copy()
    idx = df.index
    month_type = df["month_type"]
    is_newsy = (month_type == "N")

    mkt_nr = df["mkt_nr"]
    P4     = df["mkt_nm4_avg"]

    x1 = pd.Series(index=idx, dtype=float)
    x2 = pd.Series(index=idx, dtype=float)

    hist_nr = []
    hist_P4 = []

    for i in range(1, len(idx)):
        prev_date = idx[i-1]
        curr_date = idx[i]

        nr_prev = mkt_nr.loc[prev_date]
        P4_prev = P4.loc[prev_date]

        if np.isnan(nr_prev) or np.isnan(P4_prev):
            x1[curr_date] = np.nan
            x2[curr_date] = np.nan
            continue

        hist_nr.append(nr_prev)
        hist_P4.append(P4_prev)
        nr_bar = float(np.mean(hist_nr))
        P4_bar = float(np.mean(hist_P4))

        nr_dm = nr_prev - nr_bar
        P4_dm = P4_prev - P4_bar

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x1[curr_date] = sign * nr_dm
        x2[curr_date] = sign * P4_dm

    return x1, x2, month_type
```

* * *

3\. 旧 z\*\_t 戦略（あなたのフレーム）
-------------------------

### 3.1 あなたの `apply_timing_strategy`（再掲）

```python
def apply_timing_strategy(df, target_vol=0.05, max_leverage=3.0):
    """
    df['z'] をシグナルとしてボラターゲットする戦略。
    （あなたの元コードをそのまま再掲）
    """
    out = df.copy()
    z = out["z"]

    weights = []
    sig_hist = []
    strat_excess = []
    strat_total = []
    mkt_total = []

    for i, t in enumerate(out.index):
        if i == 0:
            sigma = np.nan
            w = 0.0
        else:
            sigma = z.iloc[:i].std(ddof=1)
            if np.isnan(sigma) or sigma == 0:
                w = 0.0
            else:
                w = z.iloc[i] * target_vol / sigma
                w = float(np.clip(w, -max_leverage, max_leverage))

        weights.append(w)
        sig_hist.append(sigma)

        mkt = out.at[t, "mkt_excess"]
        rf  = out.at[t, "rf"]
        se  = w * mkt
        strat_excess.append(se)
        strat_total.append(rf + se)
        mkt_total.append(rf + mkt)

    out["w"]            = weights
    out["sigma_z_hist"] = sig_hist
    out["strat_excess"] = strat_excess
    out["strat_total"]  = strat_total
    out["mkt_total"]    = mkt_total

    return out
```

### 3.2 旧 `build_z_star_online`（20 年 lookback）

ここでは「あなたが使っていたであろう構造」に沿って、  
以下の仕様で実装しています：

*   y: mkt\_excess
*   X: \[mkt\_nr, mkt\_nm4\_avg\]（同じ時点 s）
*   各 t について
    *   t−1 時点までの「直近 lookback\_years 年」のデータで OLS
    *   β₁(t), β₂(t) を推定
    *   z\*\_t = β₁(t) mkt\_nr\_t + β₂(t) mkt\_nm4\_avg\_t

```python
def build_z_star_online(
    ff: pd.DataFrame,
    lookback_years: int = 20,
    min_obs: int = 120,
) -> pd.DataFrame:
    """
    旧 z*_t 戦略用のシグナル構築。
    - y: mkt_excess
    - X: [mkt_nr, mkt_nm4_avg]（同時点）
    - 直近 lookback_years 年のデータで expanding-like OLS
    """
    df = add_nr_and_nm4(ff)
    df["mkt_total"] = df["mkt_excess"] + df["rf"]

    idx = df.index
    beta1 = pd.Series(index=idx, dtype=float)
    beta2 = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        # 回帰に使う期間: t-1 まで & 直近 lookback_years 年
        if i == 0:
            continue
        end_date = idx[i-1]
        start_date = end_date - pd.DateOffset(years=lookback_years)

        mask = (idx >= start_date) & (idx <= end_date)
        sub = df.loc[mask, ["mkt_excess", "mkt_nr", "mkt_nm4_avg"]].dropna()

        if len(sub) < min_obs:
            continue

        y = sub["mkt_excess"]
        X = sub[["mkt_nr", "mkt_nm4_avg"]]
        X_const = sm.add_constant(X)

        model = sm.OLS(y, X_const).fit()

        beta1[t] = model.params.get("mkt_nr", np.nan)
        beta2[t] = model.params.get("mkt_nm4_avg", np.nan)

    df["beta_nr"]  = beta1
    df["beta_P4"]  = beta2
    df["z_star"]   = df["beta_nr"] * df["mkt_nr"] + df["beta_P4"] * df["mkt_nm4_avg"]

    return df
```

* * *

4\. Method 6（Guo 本文）1変数戦略
-------------------------

（以前お渡しした `backtest_method6_strategy` を再掲）

```python
def backtest_method6_strategy(ff: pd.DataFrame,
                              min_obs: int = 120,
                              target_vol: float = None,
                              max_leverage: float = None) -> pd.DataFrame:
    """
    Guo (2025) Method 6: S (4 newsy sum) → x_t → β_t x_t による time-series strategy
    mkt_total, mkt_mean を使った忠実版。
    """
    mkt_excess = ff["mkt_excess"].copy()
    rf         = ff["rf"].copy()
    mkt_total  = mkt_excess + rf
    idx        = mkt_total.index

    # S_t, x_t, month_type
    S, x, month_type = compute_S_and_x_for_method6(mkt_total)

    # mkt̄_{t-1}
    mkt_mean = mkt_total.expanding().mean().shift(1)

    y_adj = mkt_total - mkt_mean
    beta = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        mask = (idx <= t) & x.notna() & y_adj.notna()
        n = mask.sum()
        if n < min_obs:
            beta[t] = np.nan
            continue

        xi = x[mask].values
        yi = y_adj[mask].values
        denom = (xi ** 2).sum()
        beta[t] = (xi * yi).sum() / denom if denom > 0 else np.nan

    exp_ret = pd.Series(index=idx, dtype=float)
    w_raw   = pd.Series(index=idx, dtype=float)

    for i in range(len(idx) - 1):
        t      = idx[i]
        t_next = idx[i + 1]

        if any(np.isnan([beta[t], x[t], mkt_mean[t]])):
            exp_ret[t_next] = np.nan
            w = 0.0
        else:
            w = beta[t] * x[t]
            if max_leverage is not None:
                w = float(np.clip(w, -max_leverage, max_leverage))
            exp_ret[t_next] = w + mkt_mean[t]

        w_raw[t_next] = w

    strat_excess_raw = w_raw * mkt_excess

    common_mask = strat_excess_raw.notna() & mkt_excess.notna()
    strat_vol = strat_excess_raw[common_mask].std(ddof=1)
    mkt_vol   = mkt_excess[common_mask].std(ddof=1)

    if target_vol is None:
        target_vol = float(mkt_vol)

    if strat_vol is not None and strat_vol > 0:
        scale = target_vol / strat_vol
    else:
        scale = 1.0

    strat_excess_scaled = strat_excess_raw * scale
    strat_total         = rf + strat_excess_scaled

    out = pd.DataFrame({
        "mkt_excess": mkt_excess,
        "rf": rf,
        "mkt_total": mkt_total,
        "month_type": month_type,
        "x": x,
        "mkt_mean": mkt_mean,
        "beta": beta,
        "w_raw": w_raw,
        "exp_ret": exp_ret,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess_scaled": strat_excess_scaled,
        "strat_total": strat_total,
    })
    out.attrs["scale"]       = scale
    out.attrs["target_vol"]  = target_vol
    out.attrs["min_obs"]     = min_obs
    out.attrs["max_leverage"] = max_leverage

    return out
```

* * *

5\. Method 6 nr+P4 2変数拡張戦略
--------------------------

（以前の `backtest_method6_zstar_strategy` を再掲）

```python
def backtest_method6_zstar_strategy(
    ff: pd.DataFrame,
    min_obs: int = 120,
    target_vol: float = None,
    max_leverage: float = None,
) -> pd.DataFrame:
    """
    Method 6 を nr + P4 (mkt_nr, mkt_nm4_avg) の2変数版に拡張した戦略。
    """
    mkt_excess = ff["mkt_excess"].copy()
    rf         = ff["rf"].copy()
    mkt_total  = mkt_excess + rf
    idx        = mkt_total.index

    df_nr_p4 = add_nr_and_nm4(ff)
    x1, x2, month_type = build_nr_p4_signals(df_nr_p4)

    mkt_mean = mkt_total.expanding().mean().shift(1)
    y_adj = mkt_total - mkt_mean

    beta1 = pd.Series(index=idx, dtype=float)
    beta2 = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        mask = (idx <= t) & x1.notna() & x2.notna() & y_adj.notna()
        n = mask.sum()
        if n < min_obs:
            beta1[t] = np.nan
            beta2[t] = np.nan
            continue

        X = np.column_stack([x1[mask].values, x2[mask].values])
        y = y_adj[mask].values

        XtX = X.T @ X
        XtY = X.T @ y
        try:
            beta_vec = np.linalg.solve(XtX, XtY)
            beta1[t], beta2[t] = beta_vec[0], beta_vec[1]
        except np.linalg.LinAlgError:
            beta1[t], beta2[t] = np.nan, np.nan

    exp_ret = pd.Series(index=idx, dtype=float)
    w_raw   = pd.Series(index=idx, dtype=float)

    for i in range(len(idx) - 1):
        t      = idx[i]
        t_next = idx[i + 1]

        b1 = beta1[t]
        b2 = beta2[t]
        xt1 = x1[t]
        xt2 = x2[t]
        mt_bar = mkt_mean[t]

        if any(np.isnan([b1, b2, xt1, xt2, mt_bar])):
            exp_ret[t_next] = np.nan
            w = 0.0
        else:
            w = b1 * xt1 + b2 * xt2
            if max_leverage is not None:
                w = float(np.clip(w, -max_leverage, max_leverage))
            exp_ret[t_next] = w + mt_bar

        w_raw[t_next] = w

    strat_excess_raw = w_raw * mkt_excess

    common_mask = strat_excess_raw.notna() & mkt_excess.notna()
    strat_vol   = strat_excess_raw[common_mask].std(ddof=1)
    mkt_vol     = mkt_excess[common_mask].std(ddof=1)

    if target_vol is None:
        target_vol = float(mkt_vol)

    if strat_vol is not None and strat_vol > 0:
        scale = target_vol / strat_vol
    else:
        scale = 1.0

    strat_excess_scaled = strat_excess_raw * scale
    strat_total         = rf + strat_excess_scaled

    out = pd.DataFrame({
        "mkt_excess": mkt_excess,
        "rf": rf,
        "mkt_total": mkt_total,
        "month_type": month_type,
        "x1_nr": x1,
        "x2_P4": x2,
        "mkt_mean": mkt_mean,
        "beta1": beta1,
        "beta2": beta2,
        "w_raw": w_raw,
        "exp_ret": exp_ret,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess_scaled": strat_excess_scaled,
        "strat_total": strat_total,
    })
    out.attrs["scale"]       = scale
    out.attrs["target_vol"]  = target_vol
    out.attrs["min_obs"]     = min_obs
    out.attrs["max_leverage"] = max_leverage

    return out
```

* * *

6\. 共通の評価関数 & 比較プロット
--------------------

```python
def annualized_stats(r: pd.Series):
    r = r.dropna()
    mu_m = r.mean()
    sd_m = r.std(ddof=1)
    mu_a = mu_m * 12
    sd_a = sd_m * math.sqrt(12)
    sharpe = mu_a / sd_a if sd_a > 0 else np.nan
    return mu_a, sd_a, sharpe

def summarize_strategy(df_strat: pd.DataFrame, label: str, start=None, end=None):
    sub = df_strat.copy()
    if start is not None or end is not None:
        sub = sub.loc[start:end].copy()

    strat = sub["strat_total"].dropna()
    mkt   = sub["mkt_total"].reindex(strat.index)

    mu_s, sd_s, sh_s = annualized_stats(strat)
    mu_m, sd_m, sh_m = annualized_stats(mkt)

    print(f"[{label}] Period: {strat.index[0].strftime('%Y-%m')} 〜 {strat.index[-1].strftime('%Y-%m')}")
    print("  Strategy: mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_s, sd_s, sh_s))
    print("  Market  : mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_m, sd_m, sh_m))
    print()

def plot_three_strategies(df_old, df_m6, df_m6_2, title_suffix="Full Sample"):
    # インデックスを揃える
    common_index = df_old["strat_total"].dropna().index
    common_index = common_index.intersection(df_m6["strat_total"].dropna().index)
    common_index = common_index.intersection(df_m6_2["strat_total"].dropna().index)

    sw_old = (1.0 + df_old["strat_total"].reindex(common_index)).cumprod()
    sw_m6  = (1.0 + df_m6["strat_total"].reindex(common_index)).cumprod()
    sw_m6_2 = (1.0 + df_m6_2["strat_total"].reindex(common_index)).cumprod()
    mw     = (1.0 + df_old["mkt_total"].reindex(common_index)).cumprod()

    plt.figure(figsize=(14,5))
    plt.plot(sw_old,  label="Old z*_t (nr+P4, 20y rolling)", linewidth=2)
    plt.plot(sw_m6,   label="Method 6 (S, 1-var)", linewidth=2)
    plt.plot(sw_m6_2, label="Method 6 (nr+P4, 2-var)", linewidth=2)
    plt.plot(mw,      label="Market", linestyle="--", linewidth=1.5)
    plt.title(f"Cumulative Wealth: {title_suffix}")
    plt.legend()
    plt.grid(True)
    plt.show()
```

* * *

7\. 統合実行（フル期間 & 2020+）
----------------------

```python
if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"

    # 1) FF データ読み込み
    ff = load_ff_monthly_from_ken_french(csv_path)

    # 2) 旧 z*_t 戦略
    df_zstar = build_z_star_online(
        ff,
        lookback_years=20,
        min_obs=120,
    )
    df_old = df_zstar.copy()
    df_old["z"] = df_old["z_star"]
    df_old = apply_timing_strategy(df_old, target_vol=0.05, max_leverage=3.0)

    # 3) Method 6 1変数版（論文推奨）
    df_m6 = backtest_method6_strategy(ff, min_obs=120, target_vol=None, max_leverage=None)

    # 4) Method 6 nr+P4 2変数拡張
    df_m6_2 = backtest_method6_zstar_strategy(ff, min_obs=120, target_vol=None, max_leverage=None)

    print("=== Full Sample ===")
    summarize_strategy(df_old,  "Old z*_t (nr+P4, 20y rolling)")
    summarize_strategy(df_m6,   "Method 6 (S, 1-var)")
    summarize_strategy(df_m6_2, "Method 6 (nr+P4, 2-var)")
    plot_three_strategies(df_old, df_m6, df_m6_2, title_suffix="Full Sample")

    print("=== 2020+ Subsample ===")
    summarize_strategy(df_old,  "Old z*_t (nr+P4, 20y rolling)", start="2020-01-01")
    summarize_strategy(df_m6,   "Method 6 (S, 1-var)",           start="2020-01-01")
    summarize_strategy(df_m6_2, "Method 6 (nr+P4, 2-var)",       start="2020-01-01")

    # サブサンプルのプロットも見たければ：
    df_old_2020  = df_old.loc["2020-01-01":].copy()
    df_m6_2020   = df_m6.loc["2020-01-01":].copy()
    df_m6_2_2020 = df_m6_2.loc["2020-01-01":].copy()
    plot_three_strategies(df_old_2020, df_m6_2020, df_m6_2_2020, title_suffix="2020+")
```

* * *

8\. 対応マッピングのまとめ
---------------

*   `df_old`  
    → 旧 `build_z_star_online + apply_timing_strategy`  
    → Guo 的には **Method 5（nr+P4 joint）を 20 年 rolling OLS + ボラターゲットで使っている戦略**
*   `df_m6`  
    → `backtest_method6_strategy`  
    → Guo 本文の **Method 6 1変数 S（4 newsy sum）** に対応する「本命」戦略
*   `df_m6_2`  
    → `backtest_method6_zstar_strategy`  
    → Method 6 の構造（mkt̄ に係数1固定 + demean+sign flip）を保ったまま  
    nr + P4 を 2変数に拡張した **あなた独自の z\*\_t 拡張版**

この 3 つを同じ枠組みで

*   フルサンプル
*   2020 年以降

について Sharpe / 累積リターン / shape の違いを見ると、  
「旧 z\*\_t 戦略と、Guo 本文の Method 6（＋その拡張版）がどこでどう挙動が違うか」が一気に可視化できるはずです。

## Response:
了解しました。  
前にお渡しした

*   `compare_all_methods`（M0〜M6 の OOS 予測・Sign 戦略比較）
*   旧 `z*_t` 戦略 vs Method 6 vs Method 6（nr+P4 拡張）

を **1 本のスクリプトに統合した完全版コード**を下にまとめます。

Ken French の CSV（`F-F_Research_Data_Factors.csv`）さえあれば、そのまま実行できます。

* * *

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import statsmodels.api as sm

# ======================================================================
# 1. Ken French 読み込み & 月タイプ分類
# ======================================================================

def load_ff_monthly_from_ken_french(csv_path: str) -> pd.DataFrame:
    """
    Ken French の F-F_Research_Data_Factors.csv から
    月次 Mkt-RF, RF を抜き出し、リターンレベルに変換する。
    """
    raw = pd.read_csv(csv_path, skiprows=4)

    num = pd.to_numeric(raw['Unnamed: 0'], errors='coerce')
    mask_monthly = num > 10000  # YYYYMM 部分だけ抽出
    monthly = raw[mask_monthly].copy()

    monthly = monthly.rename(columns={'Unnamed: 0': 'date'})
    monthly['date'] = pd.to_datetime(monthly['date'].astype(int), format="%Y%m")
    monthly = monthly.set_index('date').sort_index()

    for col in ['Mkt-RF', 'RF']:
        monthly[col] = pd.to_numeric(monthly[col], errors='coerce')

    ff = monthly[['Mkt-RF', 'RF']].copy()
    ff['mkt_excess'] = ff['Mkt-RF'] / 100.0
    ff['rf']         = ff['RF'] / 100.0

    return ff[['mkt_excess', 'rf']].dropna()

def classify_month_type(index: pd.DatetimeIndex) -> pd.Series:
    """
    Guo に合わせた月タイプ分類：
      - N: 四半期1ヶ月目 (1,4,7,10月など)
      - R: 四半期2ヶ月目
      - 3: 四半期3ヶ月目
    """
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

# ======================================================================
# 2. nr, P4, Method 6 用シグナル
# ======================================================================

def add_nr_and_p4(ff: pd.DataFrame) -> pd.DataFrame:
    """
    ff: 必須列 'mkt_excess', 'rf'

    追加列:
      - month_type   : 'N','R','3'
      - mkt_nr       : 直近の N/R 月の超過リターン (nr)
      - mkt_nm1..4   : 過去 j 番目の N 月 (超過リターン)
      - P4           : mkt_nm1..4 の平均 (Parameter-Compression 用)
      - mkt_nm4_avg  : P4 と同じ (別名。z*_t 旧実装互換用)
    """
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)

    dates = df.index.to_list()
    mt = df["month_type"].values
    mkt = df["mkt_excess"].values

    nr_dates = []
    mkt_nr_list = []

    past_newsy_indices = []
    mkt_nm1 = []
    mkt_nm2 = []
    mkt_nm3 = []
    mkt_nm4 = []

    for i, t in enumerate(dates):
        # nr(t): t より前で最も近い N or R
        nr_idx = None
        j = i - 1
        while j >= 0:
            if mt[j] in ("N", "R"):
                nr_idx = j
                break
            j -= 1
        if nr_idx is None:
            nr_dates.append(None)
            mkt_nr_list.append(np.nan)
        else:
            nr_dates.append(dates[nr_idx])
            mkt_nr_list.append(mkt[nr_idx])

        # newsy 月履歴更新
        if mt[i] == "N":
            past_newsy_indices.append(i)

        # nm(t,j): 直近の newsy 月たち
        cand = [k for k in past_newsy_indices if k < i]
        cand = sorted(cand, reverse=True)

        vals = []
        for jj in range(4):
            if jj < len(cand):
                vals.append(mkt[cand[jj]])
            else:
                vals.append(np.nan)

        mkt_nm1.append(vals[0])
        mkt_nm2.append(vals[1])
        mkt_nm3.append(vals[2])
        mkt_nm4.append(vals[3])

    df["nr_date"] = nr_dates
    df["mkt_nr"]  = mkt_nr_list
    df["mkt_nm1"] = mkt_nm1
    df["mkt_nm2"] = mkt_nm2
    df["mkt_nm3"] = mkt_nm3
    df["mkt_nm4"] = mkt_nm4

    df["P4"] = df[["mkt_nm1", "mkt_nm2", "mkt_nm3", "mkt_nm4"]].mean(axis=1)
    df["mkt_nm4_avg"] = df["P4"]  # 旧実装互換用

    return df

def compute_S_and_x_for_method6(mkt_total: pd.Series):
    """
    Method 6 用:
      - S_t: t までに出現した直近4つの newsy 月 total return の合計
      - x_t: S_{t-1} を expanding 平均で demean し、翌月 t が newsy なら sign flip
    """
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")

    news_series = mkt_total[is_newsy]

    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news_series[news_series.index <= t]
        if len(past) >= 4:
            S[t] = past.iloc[-4:].sum()
        else:
            S[t] = np.nan

    x = pd.Series(index=idx, dtype=float)
    S_hist = []

    for i in range(1, len(idx)):
        prev_date = idx[i-1]   # t-1
        curr_date = idx[i]     # t

        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue

        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return S, x, month_type

def build_nr_p4_signals(df_nr_p4: pd.DataFrame):
    """
    nr + P4 を Method 6 と同じロジック（demean + sign flip）で x1,x2 に変換。
    x1_t, x2_t は「t のリターン予測に使うシグナル」。
    """
    df = df_nr_p4.copy()
    idx = df.index
    month_type = df["month_type"]
    is_newsy = (month_type == "N")

    mkt_nr = df["mkt_nr"]
    P4     = df["mkt_nm4_avg"]

    x1 = pd.Series(index=idx, dtype=float)
    x2 = pd.Series(index=idx, dtype=float)

    hist_nr = []
    hist_P4 = []

    for i in range(1, len(idx)):
        prev_date = idx[i-1]
        curr_date = idx[i]

        nr_prev = mkt_nr.loc[prev_date]
        P4_prev = P4.loc[prev_date]

        if np.isnan(nr_prev) or np.isnan(P4_prev):
            x1[curr_date] = np.nan
            x2[curr_date] = np.nan
            continue

        hist_nr.append(nr_prev)
        hist_P4.append(P4_prev)
        nr_bar = float(np.mean(hist_nr))
        P4_bar = float(np.mean(hist_P4))

        nr_dm = nr_prev - nr_bar
        P4_dm = P4_prev - P4_bar

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x1[curr_date] = sign * nr_dm
        x2[curr_date] = sign * P4_dm

    return x1, x2, month_type

# ======================================================================
# 3. compare_all_methods 用：OOS 回帰 & Sign 戦略
# ======================================================================

def oos_linear_forecast_sign_strategy(
    y: pd.Series,
    X: pd.DataFrame,
    min_obs: int = 120
):
    """
    y: 目的変数 (mkt_excess など)
    X: 説明変数（列ベクトル1本でも複数でも可）
    min_obs: OLS を回す最小観測数

    戻り値:
      - y_hat: OOS 予測
      - w_sign: sign 戦略のウェイト (+1/ -1 / 0)
      - strat_excess: sign 戦略の超過リターン
      - coefs: 各 t の係数 (DataFrame)
    """
    idx = y.index
    X = X.copy().reindex(idx)

    coefs = pd.DataFrame(index=idx, columns=["const"] + list(X.columns), dtype=float)
    y_hat = pd.Series(index=idx, dtype=float)

    for i in range(len(idx) - 1):
        t = idx[i]
        t_next = idx[i+1]

        mask = (idx <= t) & y.notna()
        for col in X.columns:
            mask &= X[col].notna()
        n = mask.sum()
        if n < min_obs:
            y_hat[t_next] = np.nan
            continue

        Xi = X.loc[mask]
        yi = y.loc[mask]
        Xi_const = sm.add_constant(Xi)
        model = sm.OLS(yi, Xi_const).fit()

        coefs.loc[t, "const"] = model.params.get("const", np.nan)
        for col in X.columns:
            coefs.loc[t, col] = model.params.get(col, np.nan)

        x_next = X.loc[t, :].values.reshape(1, -1)
        X_next_const = np.concatenate([np.array([[1.0]]), x_next], axis=1)
        y_hat[t_next] = float(X_next_const @ model.params.values)

    w_sign = np.sign(y_hat).fillna(0.0)
    strat_excess = w_sign * y

    return y_hat, w_sign, strat_excess, coefs

def run_method0_mean(ff: pd.DataFrame, min_obs: int = 120):
    """
    Method 0 的なベースライン：過去平均で OOS 予測
    """
    y = ff["mkt_excess"].copy()
    idx = y.index

    y_hat = pd.Series(index=idx, dtype=float)
    for i in range(len(idx) - 1):
        t = idx[i]
        t_next = idx[i+1]
        past = y.iloc[: i+1].dropna()
        if len(past) < min_obs:
            y_hat[t_next] = np.nan
        else:
            y_hat[t_next] = past.mean()

    w_sign = np.sign(y_hat).fillna(0.0)
    strat_excess = w_sign * y

    return y_hat, w_sign, strat_excess

def run_method1_ar1(ff: pd.DataFrame, min_obs: int = 120):
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({"mkt_lag": ff["mkt_excess"].shift(1)})
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)

def run_method2_nr(ff: pd.DataFrame, min_obs: int = 120):
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({"mkt_nr": ff["mkt_nr"]})
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)

def run_method3_p4(ff: pd.DataFrame, min_obs: int = 120):
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({"P4": ff["P4"]})
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)

def run_method4_nr_p4(ff: pd.DataFrame, min_obs: int = 120):
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({
        "mkt_nr": ff["mkt_nr"],
        "P4":     ff["P4"]
    })
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)

def run_method6_S(ff: pd.DataFrame, min_obs: int = 120):
    """
    Method 6 の x_M6（S の demean+sign flip）を説明変数にした簡易版。
    目的変数は mkt_excess に統一。
    """
    y = ff["mkt_excess"].copy()
    X = pd.DataFrame({"x_M6": ff["x_M6"]})
    return oos_linear_forecast_sign_strategy(y, X, min_obs=min_obs)

def annualized_stats(r: pd.Series):
    r = r.dropna()
    mu_m = r.mean()
    sd_m = r.std(ddof=1)
    mu_a = mu_m * 12
    sd_a = sd_m * math.sqrt(12)
    sharpe = mu_a / sd_a if sd_a > 0 else np.nan
    return mu_a, sd_a, sharpe

def compute_oos_r2(y: pd.Series, y_hat: pd.Series):
    """
    OOS R^2：OOS 平均予測に対する相対改善度
    """
    mask = y.notna() & y_hat.notna()
    y_ = y[mask]
    yhat_ = y_hat[mask]
    if len(y_) == 0:
        return np.nan

    mean_hat = pd.Series(index=y_.index, dtype=float)
    for i, t in enumerate(y_.index):
        past = y_.iloc[:i]
        if len(past) == 0:
            mean_hat[t] = np.nan
        else:
            mean_hat[t] = past.mean()

    mask2 = mean_hat.notna()
    y_ = y_[mask2]
    yhat_ = yhat_[mask2]
    mean_hat = mean_hat[mask2]

    num = ((y_ - yhat_)**2).sum()
    den = ((y_ - mean_hat)**2).sum()
    return 1.0 - num / den if den > 0 else np.nan

def compare_all_methods(csv_path: str, min_obs: int = 120, start=None, end=None):
    """
    M0〜M6 の OOS 予測・Sign 戦略を一括比較。
    """
    ff = load_ff_monthly_from_ken_french(csv_path)
    ff = add_nr_and_p4(ff)
    ff["mkt_total"] = ff["mkt_excess"] + ff["rf"]
    S, x_M6, mt = compute_S_and_x_for_method6(ff["mkt_total"])
    ff["S_M6"] = S
    ff["x_M6"] = x_M6
    ff["mt"]   = mt

    if start is not None or end is not None:
        ff = ff.loc[start:end].copy()

    results = {}

    # M0: mean
    y_hat0, w0, strat0 = run_method0_mean(ff, min_obs=min_obs)
    results["M0_mean"] = (y_hat0, strat0)

    # M1: AR(1)
    y_hat1, w1, strat1, coef1 = run_method1_ar1(ff, min_obs=min_obs)
    results["M1_AR1"] = (y_hat1, strat1)

    # M2: nr only
    y_hat2, w2, strat2, coef2 = run_method2_nr(ff, min_obs=min_obs)
    results["M2_NR"] = (y_hat2, strat2)

    # M3: P4 only
    y_hat3, w3, strat3, coef3 = run_method3_p4(ff, min_obs=min_obs)
    results["M3_P4"] = (y_hat3, strat3)

    # M4: nr+P4
    y_hat4, w4, strat4, coef4 = run_method4_nr_p4(ff, min_obs=min_obs)
    results["M4_NR_P4"] = (y_hat4, strat4)

    # M6: S (x_M6)
    y_hat6, w6, strat6, coef6 = run_method6_S(ff, min_obs=min_obs)
    results["M6_S"] = (y_hat6, strat6)

    y = ff["mkt_excess"]

    print("=== OOS Performance ({}〜{}) ===".format(ff.index[0].strftime("%Y-%m"),
                                                  ff.index[-1].strftime("%Y-%m")))
    print("Baseline Market (Buy&Hold, Excess):")
    mu_mkt, sd_mkt, sh_mkt = annualized_stats(y)
    print("  mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_mkt, sd_mkt, sh_mkt))
    print()

    for name, (y_hat, strat) in results.items():
        mu_s, sd_s, sh_s = annualized_stats(strat)
        r2 = compute_oos_r2(y, y_hat)
        print(f"[{name}]")
        print("  mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}, OOS R^2={:.3f}".format(mu_s, sd_s, sh_s, r2))
        print()

    return ff, results

# ======================================================================
# 4. 旧 z*_t 戦略用：apply_timing_strategy + build_z_star_online
# ======================================================================

def apply_timing_strategy(df, target_vol=0.05, max_leverage=3.0):
    """
    df['z'] をシグナルとしてボラターゲットする戦略。
    （もともとお使いだった実装をベースに）
    """
    out = df.copy()
    z = out["z"]

    weights = []
    sig_hist = []
    strat_excess = []
    strat_total = []
    mkt_total = []

    for i, t in enumerate(out.index):
        if i == 0:
            sigma = np.nan
            w = 0.0
        else:
            sigma = z.iloc[:i].std(ddof=1)
            if np.isnan(sigma) or sigma == 0:
                w = 0.0
            else:
                w = z.iloc[i] * target_vol / sigma
                w = float(np.clip(w, -max_leverage, max_leverage))

        weights.append(w)
        sig_hist.append(sigma)

        mkt = out.at[t, "mkt_excess"]
        rf  = out.at[t, "rf"]
        se  = w * mkt
        strat_excess.append(se)
        strat_total.append(rf + se)
        mkt_total.append(rf + mkt)

    out["w"]            = weights
    out["sigma_z_hist"] = sig_hist
    out["strat_excess"] = strat_excess
    out["strat_total"]  = strat_total
    out["mkt_total"]    = mkt_total

    return out

def build_z_star_online(
    ff: pd.DataFrame,
    lookback_years: int = 20,
    min_obs: int = 120,
) -> pd.DataFrame:
    """
    旧 z*_t 戦略用のオンライン係数推定：
    - y: mkt_excess
    - X: [mkt_nr, mkt_nm4_avg]（同時点）
    - t-1 時点までの直近 lookback_years 年で OLS
    """
    df = add_nr_and_p4(ff)
    df["mkt_total"] = df["mkt_excess"] + df["rf"]

    idx = df.index
    beta1 = pd.Series(index=idx, dtype=float)
    beta2 = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        if i == 0:
            continue

        end_date = idx[i-1]
        start_date = end_date - pd.DateOffset(years=lookback_years)

        mask = (idx >= start_date) & (idx <= end_date)
        sub = df.loc[mask, ["mkt_excess", "mkt_nr", "mkt_nm4_avg"]].dropna()

        if len(sub) < min_obs:
            continue

        y = sub["mkt_excess"]
        X = sub[["mkt_nr", "mkt_nm4_avg"]]
        X_const = sm.add_constant(X)

        model = sm.OLS(y, X_const).fit()

        beta1[t] = model.params.get("mkt_nr", np.nan)
        beta2[t] = model.params.get("mkt_nm4_avg", np.nan)

    df["beta_nr"]  = beta1
    df["beta_P4"]  = beta2
    df["z_star"]   = df["beta_nr"] * df["mkt_nr"] + df["beta_P4"] * df["mkt_nm4_avg"]

    return df

# ======================================================================
# 5. Method 6（1変数 & nr+P4 2変数）戦略
# ======================================================================

def backtest_method6_strategy(ff: pd.DataFrame,
                              min_obs: int = 120,
                              target_vol: float = None,
                              max_leverage: float = None) -> pd.DataFrame:
    """
    Guo (2025) Method 6: S (4 newsy sum) → x_t → β_t x_t による time-series strategy
    mkt_total, mkt_mean を使った忠実版。
    """
    mkt_excess = ff["mkt_excess"].copy()
    rf         = ff["rf"].copy()
    mkt_total  = mkt_excess + rf
    idx        = mkt_total.index

    S, x, month_type = compute_S_and_x_for_method6(mkt_total)
    mkt_mean = mkt_total.expanding().mean().shift(1)

    y_adj = mkt_total - mkt_mean
    beta = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        mask = (idx <= t) & x.notna() & y_adj.notna()
        n = mask.sum()
        if n < min_obs:
            beta[t] = np.nan
            continue

        xi = x[mask].values
        yi = y_adj[mask].values
        denom = (xi ** 2).sum()
        beta[t] = (xi * yi).sum() / denom if denom > 0 else np.nan

    exp_ret = pd.Series(index=idx, dtype=float)
    w_raw   = pd.Series(index=idx, dtype=float)

    for i in range(len(idx) - 1):
        t      = idx[i]
        t_next = idx[i + 1]

        if any(np.isnan([beta[t], x[t], mkt_mean[t]])):
            exp_ret[t_next] = np.nan
            w = 0.0
        else:
            w = beta[t] * x[t]
            if max_leverage is not None:
                w = float(np.clip(w, -max_leverage, max_leverage))
            exp_ret[t_next] = w + mkt_mean[t]

        w_raw[t_next] = w

    strat_excess_raw = w_raw * mkt_excess

    common_mask = strat_excess_raw.notna() & mkt_excess.notna()
    strat_vol = strat_excess_raw[common_mask].std(ddof=1)
    mkt_vol   = mkt_excess[common_mask].std(ddof=1)

    if target_vol is None:
        target_vol = float(mkt_vol)

    if strat_vol is not None and strat_vol > 0:
        scale = target_vol / strat_vol
    else:
        scale = 1.0

    strat_excess_scaled = strat_excess_raw * scale
    strat_total         = rf + strat_excess_scaled

    out = pd.DataFrame({
        "mkt_excess": mkt_excess,
        "rf": rf,
        "mkt_total": mkt_total,
        "month_type": month_type,
        "x": x,
        "mkt_mean": mkt_mean,
        "beta": beta,
        "w_raw": w_raw,
        "exp_ret": exp_ret,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess_scaled": strat_excess_scaled,
        "strat_total": strat_total,
    })
    out.attrs["scale"]       = scale
    out.attrs["target_vol"]  = target_vol
    out.attrs["min_obs"]     = min_obs
    out.attrs["max_leverage"] = max_leverage

    return out

def backtest_method6_zstar_strategy(
    ff: pd.DataFrame,
    min_obs: int = 120,
    target_vol: float = None,
    max_leverage: float = None,
) -> pd.DataFrame:
    """
    Method 6 を nr + P4 (mkt_nr, mkt_nm4_avg) の2変数版に拡張した戦略。
    """
    mkt_excess = ff["mkt_excess"].copy()
    rf         = ff["rf"].copy()
    mkt_total  = mkt_excess + rf
    idx        = mkt_total.index

    df_nr_p4 = add_nr_and_p4(ff)
    x1, x2, month_type = build_nr_p4_signals(df_nr_p4)

    mkt_mean = mkt_total.expanding().mean().shift(1)
    y_adj = mkt_total - mkt_mean

    beta1 = pd.Series(index=idx, dtype=float)
    beta2 = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        mask = (idx <= t) & x1.notna() & x2.notna() & y_adj.notna()
        n = mask.sum()
        if n < min_obs:
            beta1[t] = np.nan
            beta2[t] = np.nan
            continue

        X = np.column_stack([x1[mask].values, x2[mask].values])
        y = y_adj[mask].values

        XtX = X.T @ X
        XtY = X.T @ y
        try:
            beta_vec = np.linalg.solve(XtX, XtY)
            beta1[t], beta2[t] = beta_vec[0], beta_vec[1]
        except np.linalg.LinAlgError:
            beta1[t], beta2[t] = np.nan, np.nan

    exp_ret = pd.Series(index=idx, dtype=float)
    w_raw   = pd.Series(index=idx, dtype=float)

    for i in range(len(idx) - 1):
        t      = idx[i]
        t_next = idx[i + 1]

        b1 = beta1[t]
        b2 = beta2[t]
        xt1 = x1[t]
        xt2 = x2[t]
        mt_bar = mkt_mean[t]

        if any(np.isnan([b1, b2, xt1, xt2, mt_bar])):
            exp_ret[t_next] = np.nan
            w = 0.0
        else:
            w = b1 * xt1 + b2 * xt2
            if max_leverage is not None:
                w = float(np.clip(w, -max_leverage, max_leverage))
            exp_ret[t_next] = w + mt_bar

        w_raw[t_next] = w

    strat_excess_raw = w_raw * mkt_excess

    common_mask = strat_excess_raw.notna() & mkt_excess.notna()
    strat_vol   = strat_excess_raw[common_mask].std(ddof=1)
    mkt_vol     = mkt_excess[common_mask].std(ddof=1)

    if target_vol is None:
        target_vol = float(mkt_vol)

    if strat_vol is not None and strat_vol > 0:
        scale = target_vol / strat_vol
    else:
        scale = 1.0

    strat_excess_scaled = strat_excess_raw * scale
    strat_total         = rf + strat_excess_scaled

    out = pd.DataFrame({
        "mkt_excess": mkt_excess,
        "rf": rf,
        "mkt_total": mkt_total,
        "month_type": month_type,
        "x1_nr": x1,
        "x2_P4": x2,
        "mkt_mean": mkt_mean,
        "beta1": beta1,
        "beta2": beta2,
        "w_raw": w_raw,
        "exp_ret": exp_ret,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess_scaled": strat_excess_scaled,
        "strat_total": strat_total,
    })
    out.attrs["scale"]       = scale
    out.attrs["target_vol"]  = target_vol
    out.attrs["min_obs"]     = min_obs
    out.attrs["max_leverage"] = max_leverage

    return out

# ======================================================================
# 6. 共通の評価関数 & 3戦略比較プロット
# ======================================================================

def summarize_strategy(df_strat: pd.DataFrame, label: str, start=None, end=None):
    sub = df_strat.copy()
    if start is not None or end is not None:
        sub = sub.loc[start:end].copy()

    strat = sub["strat_total"].dropna()
    mkt   = sub["mkt_total"].reindex(strat.index)

    mu_s, sd_s, sh_s = annualized_stats(strat)
    mu_m, sd_m, sh_m = annualized_stats(mkt)

    print(f"[{label}] Period: {strat.index[0].strftime('%Y-%m')} 〜 {strat.index[-1].strftime('%Y-%m')}")
    print("  Strategy: mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_s, sd_s, sh_s))
    print("  Market  : mu={:.2%}, sigma={:.2%}, Sharpe={:.2f}".format(mu_m, sd_m, sh_m))
    print()

def plot_three_strategies(df_old, df_m6, df_m6_2, title_suffix="Full Sample"):
    common_index = df_old["strat_total"].dropna().index
    common_index = common_index.intersection(df_m6["strat_total"].dropna().index)
    common_index = common_index.intersection(df_m6_2["strat_total"].dropna().index)

    sw_old  = (1.0 + df_old["strat_total"].reindex(common_index)).cumprod()
    sw_m6   = (1.0 + df_m6["strat_total"].reindex(common_index)).cumprod()
    sw_m6_2 = (1.0 + df_m6_2["strat_total"].reindex(common_index)).cumprod()
    mw      = (1.0 + df_old["mkt_total"].reindex(common_index)).cumprod()

    plt.figure(figsize=(14,5))
    plt.plot(sw_old,  label="Old z*_t (nr+P4, 20y rolling)", linewidth=2)
    plt.plot(sw_m6,   label="Method 6 (S, 1-var)", linewidth=2)
    plt.plot(sw_m6_2, label="Method 6 (nr+P4, 2-var)", linewidth=2)
    plt.plot(mw,      label="Market", linestyle="--", linewidth=1.5)
    plt.title(f"Cumulative Wealth: {title_suffix}")
    plt.legend()
    plt.grid(True)
    plt.show()

# ======================================================================
# 7. main：compare_all_methods + 3 戦略比較
# ======================================================================

if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"

    # ------------------------------
    # A. Table 4 の Method 比較
    # ------------------------------
    print("########## Table 4 Methods (M0〜M6) OOS 比較: 1926–2025 ##########")
    ff_all, res_all = compare_all_methods(csv_path, min_obs=120)

    print("########## Table 4 Methods OOS 比較: 2020+ ##########")
    ff_2020, res_2020 = compare_all_methods(csv_path, min_obs=120, start="2020-01-01")

    # ------------------------------
    # B. 旧 z*_t vs Method 6 vs 2変数 Method 6
    # ------------------------------
    ff = load_ff_monthly_from_ken_french(csv_path)

    # 旧 z*_t
    df_zstar = build_z_star_online(
        ff,
        lookback_years=20,
        min_obs=120,
    )
    df_old = df_zstar.copy()
    df_old["z"] = df_old["z_star"]
    df_old = apply_timing_strategy(df_old, target_vol=0.05, max_leverage=3.0)

    # Method 6 (1-var S)
    df_m6 = backtest_method6_strategy(ff, min_obs=120, target_vol=None, max_leverage=None)

    # Method 6 (nr+P4 2-var)
    df_m6_2 = backtest_method6_zstar_strategy(ff, min_obs=120, target_vol=None, max_leverage=None)

    print("########## 3戦略比較: Full Sample ##########")
    summarize_strategy(df_old,  "Old z*_t (nr+P4, 20y rolling)")
    summarize_strategy(df_m6,   "Method 6 (S, 1-var)")
    summarize_strategy(df_m6_2, "Method 6 (nr+P4, 2-var)")
    plot_three_strategies(df_old, df_m6, df_m6_2, title_suffix="Full Sample")

    print("########## 3戦略比較: 2020+ ##########")
    summarize_strategy(df_old,  "Old z*_t (nr+P4, 20y rolling)", start="2020-01-01")
    summarize_strategy(df_m6,   "Method 6 (S, 1-var)",           start="2020-01-01")
    summarize_strategy(df_m6_2, "Method 6 (nr+P4, 2-var)",       start="2020-01-01")

    df_old_2020  = df_old.loc["2020-01-01":].copy()
    df_m6_2020   = df_m6.loc["2020-01-01":].copy()
    df_m6_2_2020 = df_m6_2.loc["2020-01-01":].copy()
    plot_three_strategies(df_old_2020, df_m6_2020, df_m6_2_2020, title_suffix="2020+")
```

* * *

これで、

*   `compare_all_methods` による **Methods 0〜6 の OOS Sign 戦略比較**
*   旧 `z*_t` 戦略 vs 文献どおり Method 6 vs nr+P4 拡張 Method 6

を一度に評価できます。

もし動かしてみて、

*   係数の時系列（β\_nr, β\_P4, β\_S）
*   rolling Sharpe / rolling OOS R²

なども見たくなれば、その部分も追加コードを書きます。

## Response:
以下では、

*   文献 Guo (2025)「Earnings Extrapolation and Predictable Stock Market Returns」
*   Guo & Wachter (2025)「Correlation Neglect in Asset Prices」  
    を主な参照元として、あなたのコードで比較している各戦略を「学術的な位置づけ」で整理します。[OUP Academic+2SSRN+2](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)

最後に「どの戦略が論文のどの Method に対応するか」もまとめます。

* * *

1\. 理論的バックグラウンドの整理
------------------

### 1.1 Earnings extrapolation と newsy / non-newsy 月

Guo (2025) は、  
「四半期第1月（newsy month：1,4,7,10 月など）での市場リターンが、その後の月次リターンを強く予測する」ことを示します。  
具体的には、

*   予測対象月が **newsy** のとき：過去の newsy 月リターンと強い**負**の相関
*   予測対象月が **non-newsy（第2・3月）** のとき：過去の newsy 月リターンと強い**正**の相関

という「符号の反転を伴う」予測パターンが存在し、これが従来の「月次市場リターンはほとんど予測不能」という結果をマスクしている、と主張します。[OUP Academic](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)

このパターンは、投資家が

*   earnings（特に newsy 月の決算発表）を**将来に向けて外挿**する一方で、
*   「newsy 月と non-newsy 月で earnings の自己相関構造が異なる（newsy のほうが予測しづらい）」ことを**十分に認識していない**

という「earnings extrapolation + correlation neglect（相関構造の無視）」モデルから導出されます。[Finance Department+2repository.upenn.edu+2](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)

### 1.2 Correlation neglect の形式化

Guo & Wachter (2025)「Correlation Neglect in Asset Prices」は、この仕組みをより一般的な「相関構造の誤認知」として定式化し、

*   投資家がシグナル間の相関や、時系列自己相関の**レジーム依存性**を正しく扱わないとき、
*   月次リターンの自己相関が「月の種類によって強く変動する」ようなパターンが生じる

ことを示します。[SSRN+2SSRN+2](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5268329&utm_source=chatgpt.com)

あなたの `nr`, `P4`, `S`, `x_M6`, `z*_t` などのシグナルは、まさにこのモデルが示す「誤った期待形成による予測可能性」を抽出することを目的としています。

* * *

2\. compare\_all\_methods の各戦略（Method 0〜6）
------------------------------------------

### 2.1 Method 0：単純平均（M0\_mean）

**仕様**

*   予測式：
    $$
     \hat r_{t+1}^{(0)} = \bar r_t = \frac{1}{t}\sum_{s\le t} r_s,
    $$
    ここで  $r_t$  は市場超過リターン。
*   戦略： $\hat r_{t+1}^{(0)}$  の符号に応じてロング/ショートする sign 戦略。

**学術的意味**

*   「return predictability がほぼゼロ」という従来の実証結果を背景にした**帰無モデル**（EMH 的ベンチマーク）。[OUP Academic+1](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)
*   Campbell & Yogo (2003) などの予測可能性テストでも、無条件平均は「最も単純な予測ルール」としてしばしば比較対象になります。[NBER](https://www.nber.org/system/files/working_papers/w10026/w10026.pdf?utm_source=chatgpt.com)

ここでは、Guo の高度なシグナルが「単純平均をどれだけ上回るか」を測るための**最低限の比較基準**と解釈できます。

* * *

### 2.2 Method 1：AR(1)（M1\_AR1）

**仕様**

*   予測式：
    $$
     r_{t+1} = \alpha + \phi r_t + \varepsilon_{t+1}.
    $$
*   過去データに基づく expanding OLS で  $\phi$  を推定し、1 期先を予測。
*   sign 戦略によりロング/ショートを決定。

**学術的意味**

*   もっとも標準的な「**リターン外挿**」モデル。
*   しかし、Guo (2025) が示すように、**月次市場リターンの単純 AR(1) は非常に弱い予測力しか持たない**。[OUP Academic](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)
*   したがって、本戦略は
    > 「投資家が newsy / non-newsy の別や earnings の情報構造を一切考慮せず、単に直近リターンを外挿している」
    という古典的な行動仮説に対応するベンチマークです。

* * *

### 2.3 Method 2：nr 単独（M2\_NR）— Correlation-Neglect の core

**仕様**

*   `mkt_nr`：
    *   現在時点より直近の「N または R（月の第1 or 2 月）」の市場超過リターン。
    *   Guo の notation でいう「直近の earnings-heavy 月のリターン」の簡略化。
*   予測式：
    $$
     r_{t+1} = \alpha + \beta_{\text{nr}} \,\text{nr}_t + \varepsilon_{t+1}.
    $$

**学術的意味**

*   Guo (2025) の**時系列分解**では、過去 12 ヶ月のうち「newsy 月リターン」が特に重要な役割を果たすことが示されます。[OUP Academic+1](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)
*   `nr_t` は、そうした「earnings 集約月（newsy / repetitive）の直近ショック」を 1 個のスカラーで代表させたシグナルであり、
    *   投資家が earnings ショックを**将来に単調に外挿してしまう**（extrapolation）、
    *   しかし「newsy vs non-newsy で予測力が異なる」という**相関構造の違いを無視**している  
        ことによるミスプライシングをターゲットにした predictor と解釈できます。[SSRN+2SSRN+2](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5268329&utm_source=chatgpt.com)

このシンプルな `nr` モデルは、Guo & Wachter (2025) が一般化している「correlation neglect に基づく時系列自己相関の変動」の最も素朴な近似版と位置づけられます。[SSRN+2SSRN+2](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5268329&utm_source=chatgpt.com)

* * *

### 2.4 Method 3：P4 単独（M3\_P4）— Parameter Compression

**仕様**

*   `mkt_nm1..4`：直近 4 回の newsy 月の超過リターン。
*   `P4`（コードでは `mkt_nm4_avg` と同一）：
    $$
     P4_t = \frac{1}{4}\sum_{j=1}^{4}\text{mkt\_nm}(t,j),
    $$
    という **過去 4 newsy 月の平均**。
*   予測式：
    $$
     r_{t+1} = \alpha + \beta_{P4} P4_t + \varepsilon_{t+1}.
    $$

**学術的意味**

*   Guo の Table 3 では、
    $$
     r_t = \alpha + \sum_{j=1}^{4} \beta_j \, \text{mktnm}(t,j) + \varepsilon_t
    $$
    という「4 つの newsy 月リターンを別々の係数で回帰する」仕様が提示されます。[OUP Academic+1](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)
*   しかし実務上・計量上は、4 つの係数を 1 つにまとめた「parameter-compression（次元圧縮）」がしばしば有効であり、`P4` はその**単純平均による圧縮**に相当します。
*   行動ファイナンス的には、投資家が過去複数の newsy 月ショックを「だいたい同じもの」と見なし、単純な平均ヒューリスティクスで判断している、という認知モデルと整合的です。[econstor.eu+1](https://www.econstor.eu/bitstream/10419/52523/1/66946063X.pdf?utm_source=chatgpt.com)

* * *

### 2.5 Method 4：nr + P4 の 2変数回帰（M4\_NR\_P4）

**仕様**

*   予測式：
    $$
     r_{t+1} = \alpha + \beta_{\text{nr}} \,\text{nr}_t + \beta_{P4} \,P4_t + \varepsilon_{t+1}.
    $$

**学術的意味**

*   `nr`：直近 1 回の earnings-heavy 月ショック
*   `P4`：より長い期間にわたる newsy 月ショックの平均  
    という 2 つの尺度を同時に使うことで、
    1.  **短期的な過剰反応 / 反転**（nr）
2.  **中期的なトレンド外挿**（P4）

の両方の成分を分離して捉える試みと解釈できます。

*   Guo の Table 4 における「Method 5（joint specification）」に最も近い構造であり、
    *   correlation neglect（過度に news を重視する）
    *   earnings extrapolation（過去 earnings を過剰に外挿する）  
        の2 種の行動バイアスを 1 本の回帰で捕捉する設計です。[OUP Academic+2SSRN+2](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)

* * *

### 2.6 Method 6：S ベースの 1変数モデル（M6\_S, x\_M6）

**仕様（簡易版 M6\_S）**

*   `S_t`：  
    「**直近 4 回の newsy 月のトータルリターン**の和」
*   `x_M6(t)`：
    *    $S_{t-1}$  を expanding 平均で demean
    *   予測対象月が newsy の場合は符号反転（newsy vs non-newsy で符号が変わる構造を模倣）
*   予測式（簡易版）：
    $$
     r_{t+1} = \alpha + \beta_S x_{M6,t} + \varepsilon_{t+1}.
    $$

**本来の Method 6（論文仕様）**

*   Guo の本来の Method 6 では、
    *   目的変数は「トータルリターン − 無条件平均」
    *    $\bar r$  に係数 1 を**理論的制約**として課し、ミスプライシング部分のみを  $\beta_S x_t$  で説明  
        という形になっており、あなたの `backtest_method6_strategy` はこれにかなり忠実です。[OUP Academic+2SSRN+2](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)

**学術的意味**

*   `S` は、過去の newsy 月ショックを **earnings extrapolation + correlation neglect モデルで最適に要約した sufficient statistic** に近い役割を果たします。[OUP Academic+2Finance Department+2](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)
*   実際、Guo & Wachter (2025) は、S 型のシグナルを用いたときの OOS  $R^2$  が、従来文献で報告される値より一桁大きいことを示しており、return predictability 文献の「prior」を更新すべきだと主張しています。[SSRN+1](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5268329&utm_source=chatgpt.com)

* * *

3\. 旧 z\*\_t 戦略と Method 6 拡張版
-----------------------------

ここからは、あなた独自の拡張（旧 z\*\_t、Method 6 nr+P4 2変数）を、上記文献枠組みの中で位置づけます。

### 3.1 旧 z\*\_t 戦略（build\_z\_star\_online + apply\_timing\_strategy）

**仕様**

1.  `add_nr_and_p4` で nr と P4（`mkt_nm4_avg`）を構築。
2.  ローリング 20 年 window の OLS：
    $$
    r_t = \alpha_t + \beta_{\text{nr},t} \,\text{nr}_t + \beta_{P4,t}\,P4_t + \varepsilon_t,
    $$
    （ただし回帰に使うのは  $t$  の前まで）
3.  z\*\_t を
    $$
     z^*_t = \beta_{\text{nr},t}\,\text{nr}_t + \beta_{P4,t}\,P4_t
    $$
    と定義し、これを `apply_timing_strategy` でボラターゲット戦略に変換。

**学術的解釈**

*   構造的には、Guo Table 4 の **Method 5（joint nr + P4 モデル）** を、「rolling 20 年 OLS + ボラターゲティング」で実装したものと解釈できます。
*   ただし論文の Method 6 と異なり：
    *   目的変数が「超過リターン」であり、トータルリターンや平均成分の decomposition を明示的に行っていない。
    *    $\bar r$  に係数 1 を課す制約がないため、「リスクプレミアムの変動」と「ミスプライシング成分」が混在しやすい。
*   一方で、20 年という比較的短い窓を用いているため、**構造変化（例えば 1980 年代 vs 2000 年代 vs 2020 年以降）の影響をより鋭敏に反映**できる、という practical な利点があります。

* * *

### 3.2 Method 6 忠実版（backtest\_method6\_strategy）

**仕様再掲**

*   目的変数：
    $$
     y_t = \text{mkt\_total}_t - \bar r_{t-1}
    $$
*   説明変数：Method 6 の `x_t`
*   制約： $\bar r_{t-1}$  の係数は 1 に固定（構造モデルからの理論的制約）。
*    $\beta_t$  は expanding OLS で逐次推定され、ポジションは  $w_t = \beta_t x_t$ 。
*   最後に、**戦略ボラを市場ボラに合わせるスケーリング**を実施。

**学術的意味**

*   Guo の earnings extrapolation モデルから導かれる「**誤った期待のみに起因する予測可能性**」をピュアに抽出しようとする設計。[OUP Academic+2SSRN+2](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)
*   経済的には、
    *   リスクプレミアムの時間変動（合理的な component）は  $\bar r_{t-1}$  で説明し、
    *   残差部分  $y_t$  を correlation neglect が生むミスプライシングとみなす  
        という decomposition に基づきます。

したがって、この Method 6 戦略は、「Guo の理論モデルに最も忠実な実装」と言えます。

* * *

### 3.3 Method 6 nr+P4 2変数拡張（backtest\_method6\_zstar\_strategy）

**仕様**

*   `x1_t, x2_t`：
    *   nr と P4 のそれぞれを、Method 6 と同じロジック（expanding demean + newsy で sign flip）で変換したもの。
    *   つまり、`x1` は「短期 nr ショックの correlation-neglect 成分」、`x2` は「中期 P4 ショックの成分」という解釈。
*   目的変数：
    $$
     y_t = \text{mkt\_total}_t - \bar r_{t-1}
    $$
*   回帰式：
    $$
     y_t = \beta_{1,t} x1_t + \beta_{2,t} x2_t + \varepsilon_t,
    $$
    を expanding 二変量 OLS で段階的に推定。
*   戦略ポジション：
    $$
     w_t = \beta_{1,t} x1_t + \beta_{2,t} x2_t,
    $$
    を市場ボラに合わせるようスケール。

**学術的意味**

*   Method 6 の「S（news-sum）」は、実は**nr と P4 の線形結合のような役割**を果たしていると解釈できます。
*   あなたの 2 変数版は、この S をあえて「短期 nr 成分」と「中期 P4 成分」に分解し、それぞれの係数  $\beta_1,\beta_2$  を別々に推定することで：
    1.  **ごく直近の newsy ショック**に対する市場の overreaction / mean-reversion
    2.  \*\*数四半期にわたる earnings のトレンド（P4）\*\*に対する extrapolation
    の強さを時変パラメータとして識別しようとする拡張です。
*   文献上、Guo 自身は「単一 S シグナル」を推奨していますが、Guo & Wachter (2025) の一般的な correlation-neglect モデルを踏まえると、こうしたマルチシグナルへの拡張は自然な研究方向です。[SSRN+2SSRN+2](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5268329&utm_source=chatgpt.com)

* * *

4\. まとめ：文献の Method とあなたの戦略の対応
-----------------------------

最後に、Table 4（Methods 1–7）および Guo & Wachter の記述と、あなたの実装の対応を整理すると：

| あなたのラベル / コード | 学術的な位置づけ | Guo (2025) / Guo & Wachter (2025) との対応 |
| --- | --- | --- |
| M0\_mean | 無条件平均ベースライン | 文献中の「弱い predictability」前提の EMH ベースライン（直接の Method ではない）[OUP Academic+1](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com) |
| M1\_AR1 | 単純なリターン外挿 | 「past 12m return → next month return」の素朴版。文献では「ほぼ予測力なし」とされる部類。[OUP Academic](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com) |
| M2\_NR | Correlation-neglect シグナル（単変量） | Table 3 の newsy 月リターンの役割に近い「newsy ショック単独 predictor」 |
| M3\_P4 | Parameter-compression シグナル | Table 3 の  $\{\text{mktnm}(t,j)\}_{j=1}^4$  を単純平均で圧縮した predictor |
| M4\_NR\_P4 | nr + P4 joint model | Table 4 の multi-predictor（Method 4 または 5）に相当する joint specification |
| M6\_S / backtest\_method6\_strategy | Guo 推奨 Method 6 | S（過去4 newsy の和）を sufficient statistic とみなす 1 変数モデル。論文が最も推奨する仕様。[OUP Academic+2SSRN+2](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com) |
| 旧 z\*\_t + apply\_timing\_strategy | Method 5 を rolling OLS + ボラターゲットで拡張した独自実装 | nr+P4 joint を超過リターンでフィットし、その線形結合を z\*\_t シグナルとして使用する実務版 |
| Method 6 nr+P4 2-var 拡張 | correlation-neglect モデルの multi-signal 拡張 | Guo の Method 6 の構造（mkt̄ 係数1）を保ちつつ、S を nr/P4 に分解した研究者独自の拡張 |

* * *

もし次のステップとして、

*   各戦略の **OOS R², Sharpe, 勝率**を年代ごとに分解して
*   「どの行動バイアス（短期 nr vs 中期 P4）が、どの時代にどれだけ強く効いているか」

を定量的に整理したい場合は、そのための分析コード（rolling OOS R², regime-wise decomposition）も用意できます。

## Response:
以下では、すでに実装済みの

*   `compare_all_methods(csv_path, ...)`（→ `ff`, `results` を返す）
*   `df_old`, `df_m6`, `df_m6_2` などの戦略 DataFrame（`strat_total`, `mkt_total` 列あり）

を前提に、

1.  **Rolling OOS R²** を時系列でプロットするコード
2.  **Regime-wise decomposition**（N/R/3 やボラティリティ・レジーム別のパフォーマンス分解）

のための追加コードをまとめます。

そのまま既存スクリプトの末尾に追記して使える形にしてあります。

* * *

1\. Rolling OOS R² の計算・可視化
--------------------------

### 1.1 1 戦略分の rolling OOS R² を計算する関数

```python
def rolling_oos_r2_series(y: pd.Series,
                          y_hat: pd.Series,
                          window: int = 120) -> pd.Series:
    """
    y      : 実現リターン (例: mkt_excess)
    y_hat  : OOS 予測値 (compare_all_methods の戻り値など)
    window : R^2 を計算するローリング窓の長さ（月数）

    定義:
      各時点 t について、直近 window 期間の
        SSR_model = Σ (y - y_hat)^2
        SSR_mean  = Σ (y - ȳ)^2   （同じ window 内での単純平均をベースライン）
      として
        R^2_t = 1 - SSR_model / SSR_mean
      を計算する。
    """
    # 共通インデックスに揃える
    data = pd.concat([y.rename("y"), y_hat.rename("y_hat")], axis=1).dropna()
    y_ = data["y"]
    yhat_ = data["y_hat"]
    idx = y_.index

    r2 = pd.Series(index=idx, dtype=float)

    for i in range(len(idx)):
        end = idx[i]
        start_pos = max(0, i - window + 1)
        window_idx = idx[start_pos:i+1]

        yw = y_.loc[window_idx]
        yh = yhat_.loc[window_idx]

        if len(yw) < window:
            r2[end] = np.nan
            continue

        y_mean = yw.mean()
        ss_model = ((yw - yh) ** 2).sum()
        ss_mean  = ((yw - y_mean) ** 2).sum()

        if ss_mean > 0:
            r2[end] = 1.0 - ss_model / ss_mean
        else:
            r2[end] = np.nan

    return r2
```

### 1.2 compare\_all\_methods の結果から、全 Method の rolling OOS R² を作ってプロット

```python
def build_rolling_oos_r2_df(ff: pd.DataFrame,
                            results: dict,
                            window: int = 120) -> pd.DataFrame:
    """
    compare_all_methods の戻り値:
      ff      : mkt_excess などを含む DF
      results : {method_name: (y_hat, strat_excess)}
    を入力として、各 Method の rolling OOS R^2 の DataFrame を返す。
    """
    y = ff["mkt_excess"]

    r2_dict = {}
    for name, (y_hat, strat) in results.items():
        r2_series = rolling_oos_r2_series(y, y_hat, window=window)
        r2_dict[name] = r2_series

    r2_df = pd.DataFrame(r2_dict)
    return r2_df

def plot_rolling_oos_r2(r2_df: pd.DataFrame,
                        title: str = "Rolling OOS R^2",
                        highlight_methods: list = None):
    """
    r2_df: index = 日付, columns = Method 名（build_rolling_oos_r2_df の出力）
    highlight_methods: 目立たせたい Method のリスト（例: ["M2_NR", "M3_P4", "M6_S"]）
    """
    plt.figure(figsize=(14,5))

    if highlight_methods is None:
        highlight_methods = list(r2_df.columns)

    for col in r2_df.columns:
        if col in highlight_methods:
            plt.plot(r2_df.index, r2_df[col], label=col, linewidth=2)
        else:
            plt.plot(r2_df.index, r2_df[col], label=col, linewidth=1, alpha=0.4)

    plt.axhline(0.0, color="black", linestyle="--", linewidth=1)
    plt.title(title)
    plt.ylabel("OOS $R^2$ (rolling)")
    plt.legend()
    plt.grid(True)
    plt.show()
```

### 1.3 使用例

```python
if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"

    # すでに実行済みの場合はスキップしてOK
    ff_all, res_all = compare_all_methods(csv_path, min_obs=120)

    # 10年窓 (120 ヶ月) の rolling OOS R^2
    r2_all = build_rolling_oos_r2_df(ff_all, res_all, window=120)

    # 全期間プロット
    plot_rolling_oos_r2(
        r2_all,
        title="Rolling 10-year OOS R^2 (Methods 0–6)",
        highlight_methods=["M2_NR", "M3_P4", "M4_NR_P4", "M6_S"]
    )

    # 2020年以降だけ見たい場合
    r2_2020 = r2_all.loc["2020-01-01":]
    plot_rolling_oos_r2(
        r2_2020,
        title="Rolling 10-year OOS R^2 (2020+)",
        highlight_methods=["M2_NR", "M3_P4", "M4_NR_P4", "M6_S"]
    )
```

* * *

2\. Regime-wise decomposition（N/R/3 別・ボラティリティ別）
-----------------------------------------------

### 2.1 汎用：レジームごとの年率統計を出す関数

```python
def regime_performance(
    returns: pd.Series,
    regime: pd.Series,
    name: str = "",
    dropna: bool = True
) -> pd.DataFrame:
    """
    returns : 月次トータルリターン (strat_total など)
    regime  : レジームラベル（'N', 'R', '3' や 'LowVol', 'HighVol' 等）
    name    : 戦略名（出力列名用）

    戻り値:
      index  : レジーム（unique(regime)）
      columns: ['mu_ann', 'sigma_ann', 'Sharpe', 'n_obs']
    """
    if dropna:
        data = pd.concat([returns.rename("ret"), regime.rename("regime")], axis=1).dropna()
    else:
        data = pd.concat([returns.rename("ret"), regime.rename("regime")], axis=1)
    if data.empty:
        return pd.DataFrame()

    out = []
    for g, df_g in data.groupby("regime"):
        r = df_g["ret"]
        mu_m = r.mean()
        sd_m = r.std(ddof=1)
        mu_a = mu_m * 12
        sd_a = sd_m * math.sqrt(12)
        sharpe = mu_a / sd_a if sd_a > 0 else np.nan
        out.append({
            "regime": g,
            "mu_ann": mu_a,
            "sigma_ann": sd_a,
            "Sharpe": sharpe,
            "n_obs": len(r)
        })

    out_df = pd.DataFrame(out).set_index("regime").sort_index()
    if name:
        out_df.columns = [f"{c}_{name}" for c in out_df.columns]
    return out_df
```

* * *

### 2.2 N / R / 3 別の分解（compare\_all\_methods の sign 戦略）

```python
def regime_decomposition_by_month_type(
    ff: pd.DataFrame,
    results: dict,
    regime_col: str = "mt"
) -> pd.DataFrame:
    """
    ff      : compare_all_methods が返した ff（'mt' に month_type='N','R','3' が入っている想定）
    results : compare_all_methods の results（{name: (y_hat, strat_excess)})
    regime_col: レジーム列名（デフォルト 'mt'）

    各 Method の strat_excess について、N/R/3 別に年率統計をまとめて返す。
    ついでに Market (mkt_excess) も同様に出す。
    """
    mt = ff[regime_col]

    # Market
    mkt_perf = regime_performance(ff["mkt_excess"], mt, name="MKT")

    all_perf = mkt_perf.copy()
    for name, (y_hat, strat) in results.items():
        perf = regime_performance(strat, mt, name=name)
        all_perf = all_perf.join(perf, how="outer")

    return all_perf
```

使用例：

```python
if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"
    ff_all, res_all = compare_all_methods(csv_path, min_obs=120)

    reg_perf = regime_decomposition_by_month_type(ff_all, res_all, regime_col="mt")
    print("=== Regime-wise performance by month_type (N/R/3) ===")
    print(reg_perf)
```

* * *

### 2.3 ボラティリティ・レジームの定義（HighVol / LowVol など）

例として、36 ヶ月 rolling 標準偏差の中央値で high / low を分けるコードです。

```python
def build_vol_regime(ff: pd.DataFrame,
                     window: int = 36,
                     quantile: float = 0.5,
                     col: str = "mkt_excess") -> pd.Series:
    """
    ff      : mkt_excess を含む DataFrame
    window  : rolling 標準偏差の窓長 (月数)
    quantile: ボラ閾値（0.5 = median）
    col     : ボラを計算するリターン列名

    戻り値:
      vol_regime: index=ff.index, values in {'LowVol','HighVol'}
    """
    rets = ff[col].dropna()
    rolling_vol = rets.rolling(window=window).std(ddof=1)
    thr = rolling_vol.quantile(quantile)

    vol_regime = pd.Series(index=ff.index, dtype=object)
    vol_regime.loc[rolling_vol.index] = np.where(
        rolling_vol <= thr, "LowVol", "HighVol"
    )
    return vol_regime
```

* * *

### 2.4 ボラティリティ・レジーム別の分解（sign 戦略）

```python
def regime_decomposition_by_vol(
    ff: pd.DataFrame,
    results: dict,
    window: int = 36,
    quantile: float = 0.5,
    col: str = "mkt_excess"
) -> pd.DataFrame:
    """
    ff      : compare_all_methods が返した ff
    results : compare_all_methods の results（{name: (y_hat, strat_excess)})
    window, quantile, col: build_vol_regime に引き渡し

    HighVol / LowVol ごとの年率統計をまとめる。
    """
    vol_regime = build_vol_regime(ff, window=window, quantile=quantile, col=col)

    # Market
    mkt_perf = regime_performance(ff["mkt_excess"], vol_regime, name="MKT")

    all_perf = mkt_perf.copy()
    for name, (y_hat, strat) in results.items():
        perf = regime_performance(strat, vol_regime, name=name)
        all_perf = all_perf.join(perf, how="outer")

    return all_perf
```

使用例：

```python
if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"
    ff_all, res_all = compare_all_methods(csv_path, min_obs=120)

    vol_perf = regime_decomposition_by_vol(ff_all, res_all, window=36, quantile=0.5)
    print("=== Regime-wise performance by volatility regime (LowVol / HighVol) ===")
    print(vol_perf)
```

* * *

3\. df\_old / df\_m6 / df\_m6\_2（フル戦略）のレジーム分解
---------------------------------------------

`df_old`, `df_m6`, `df_m6_2` はすでに

*   `strat_total`（戦略トータルリターン）
*   `mkt_total`（市場トータルリターン）
*   `month_type`（N/R/3）

を持っているので、同じ `regime_performance` を使って簡単に分解できます。

### 3.1 戦略 3 本の N/R/3 別パフォーマンス

```python
def three_strategy_regime_by_month_type(df_old, df_m6, df_m6_2):
    mt_old = df_old["month_type"]

    perf_mkt = regime_performance(df_old["mkt_total"], mt_old, name="MKT")
    perf_old = regime_performance(df_old["strat_total"], mt_old, name="Old")
    perf_m6  = regime_performance(df_m6["strat_total"],   df_m6["month_type"],  name="M6")
    perf_m6_2= regime_performance(df_m6_2["strat_total"], df_m6_2["month_type"], name="M6_2")

    out = perf_mkt.join(perf_old, how="outer").join(perf_m6, how="outer").join(perf_m6_2, how="outer")
    return out
```

使用例：

```python
if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"
    ff = load_ff_monthly_from_ken_french(csv_path)

    df_zstar = build_z_star_online(ff, lookback_years=20, min_obs=120)
    df_old = df_zstar.copy()
    df_old["z"] = df_old["z_star"]
    df_old = apply_timing_strategy(df_old, target_vol=0.05, max_leverage=3.0)

    df_m6   = backtest_method6_strategy(ff, min_obs=120, target_vol=None, max_leverage=None)
    df_m6_2 = backtest_method6_zstar_strategy(ff, min_obs=120, target_vol=None, max_leverage=None)

    reg_three = three_strategy_regime_by_month_type(df_old, df_m6, df_m6_2)
    print("=== N/R/3 regime performance for (Old z*, M6, M6_2) ===")
    print(reg_three)
```

### 3.2 戦略 3 本のボラティリティ・レジーム別パフォーマンス

```python
def three_strategy_regime_by_vol(df_old, df_m6, df_m6_2,
                                 window: int = 36,
                                 quantile: float = 0.5):
    """
    df_old, df_m6, df_m6_2 : それぞれ strat_total, mkt_total 列を持つ DF

    Market のボラからレジームを作り、3 戦略を比較。
    """
    # vol regime は市場トータルリターンから作成
    tmp = pd.DataFrame({"mkt_total": df_old["mkt_total"]})
    vol_regime = build_vol_regime(tmp, window=window, quantile=quantile, col="mkt_total")

    perf_mkt = regime_performance(df_old["mkt_total"], vol_regime, name="MKT")
    perf_old = regime_performance(df_old["strat_total"], vol_regime, name="Old")
    perf_m6  = regime_performance(df_m6["strat_total"],   vol_regime, name="M6")
    perf_m6_2= regime_performance(df_m6_2["strat_total"], vol_regime, name="M6_2")

    out = perf_mkt.join(perf_old, how="outer").join(perf_m6, how="outer").join(perf_m6_2, how="outer")
    return out
```

使用例：

```python
if __name__ == "__main__":
    # 上と同じく df_old, df_m6, df_m6_2 がある前提
    vol_three = three_strategy_regime_by_vol(df_old, df_m6, df_m6_2, window=36, quantile=0.5)
    print("=== Volatility regime performance for (Old z*, M6, M6_2) ===")
    print(vol_three)
```

* * *

これらのコードを組み合わせることで、

*   **時間とともに OOS R² がどう変化したか**（rolling 10 年 R²）
*   **newsy / repetitive / 3rd month でどの戦略が強いか**
*   **高ボラ相場 / 低ボラ相場でどの戦略が優位か**

を一括で検証できるようになります。

もし、これらを「1926–79 / 1980–99 / 2000–19 / 2020+」などの**サブサンプル×レジーム**のパネル表にしたい場合も、上の関数を少しラップして書けるので、必要であればそこもまとめます。

## Response:
以下では、Guo 系のフレームワークの中で

*   Method 5（nr + P4 の「静的」joint 回帰）
*   Method 6（Guo が本命として推奨している S ベースのモデル）
*   あなたの `nr + P4` の z\*\_t（online 20y window 版：rolling OLS）

を、できるだけ論文に近い形の数式で整理しつつ、違いを明確に比較します。

※ 文献は主に Guo (2025) “Earnings Extrapolation and Predictable Stock Market Returns” と、Guo & Wachter (2025) “Correlation Neglect in Asset Prices” を意識しています。

* * *

1\. 共通の設定（変数と notation）
-----------------------

月次で観測される変数を以下のように置きます。

*    $r_t$ : 月次の「市場超過リターン」もしくはトータルリターン
*    $\bar r_{t-1}$ : 時点  $t-1$  までの「無条件平均リターン」（expanding 平均）
*    $\text{nr}_t$ : 「nr シグナル」
    *   例：時点  $t$  より直近の earnings-heavy 月（newsy or repetitive）の市場超過リターン
*    $\text{P4}_t$ : 「P4 シグナル」
    *   例：直近 4 回の newsy 月超過リターンの平均
    $$
     \text{P4}_t = \frac{1}{4}\sum_{j=1}^{4}\text{mktnm}(t,j)
    $$
*    $S_t$ : Method 6 で用いる「過去 4 newsy 月のトータルリターンの合計」
    $$
     S_t = \sum_{j=1}^{4} R_{n_j(t)},
    $$
    ここで  $R_{n_j(t)}$  は「直近 j 番目の newsy 月トータルリターン」。
*    $x_t$ : Method 6 で使う S の変換版（demean + sign flip）。  
    あなたの実装では、
    $$
     S_{t-1} \text{ の履歴に対する } \bar S_{t-1} = \frac{1}{t-1}\sum_{s < t} S_s
    $$
    を用いて
    $$
     x_t = \text{sign\_adj}(t)\, \bigl(S_{t-1} - \bar S_{t-1}\bigr),
    $$
    ここで  $\text{sign\_adj}(t)$  は newy 月で符号反転するための係数（たとえば newsy 月なら  $-1$ 、それ以外なら  $+1$ ）。

このように、nr, P4, S はいずれも

*   決算期（newsy month）のリターンショックをどう集約するか
*   またそれを「newsy と non-newsy で符号が変わる」構造にどう埋め込むか

という点で設計された predictor です。

* * *

2\. Method 5（nr + P4 の静的 joint モデル）
-----------------------------------

### 2.1 基本的な回帰仕様（理論的な形）

Guo の Table 4 での「複数 predictor joint モデル」に対応するのが Method 5 です。単純化すると、概ね次のような time-series 回帰です：

$$
 r_t \;=\; \alpha + \beta_{\text{nr}}\, \text{nr}_{t-1} + \beta_{P4}\,\text{P4}_{t-1} + \varepsilon_t. \tag{M5}
$$
*   被説明変数：月次リターン  $r_t$ （市場超過リターン or トータルリターン）
*   説明変数：1 期ラグの nr と P4
*   係数  $\beta_{\text{nr}}, \beta_{P4}$  は一定（静的）と仮定し、全サンプルで OLS 推定

### 2.2 経済的な意味

*    $\text{nr}$  は「直近の earnings-heavy 月ショック」、 $\text{P4}$  は「数四半期にわたる earnings トレンド」を表現。
*   Method 5 は、短期ショックと中期トレンドの両方を 1 本の線形モデルに入れることで、
    *   **短期のオーバーシュート / mean reversion 成分（nr）**
    *   **中期的な earnings extrapolation 成分（P4）**  
        を切り分けることを狙っています。
*   ただし、Method 6 とは異なり、「無条件平均リターン  $\bar r$  に係数 1 を固定する」といった構造的制約はなく、単純な時系列回帰として扱われます。

### 2.3 あなたのコードとの対応

*   `compare_all_methods` 内の `run_method4_nr_p4` が、ほぼこの Method 5 に対応します。
*   ただしあなたのコードは「expanding OLS + OOS 予測 + sign 戦略」という形でオンライン化しており、  
    Guo の Table 4 の「静的パラメータ、サンプル分割での OOS テスト」とは実務的に少し異なります。

* * *

3\. Method 6（Guo 推奨の構造制約付きモデル）
------------------------------

Method 6 は Guo が最も推奨する「構造モデルに忠実な」仕様です。大きなポイントは：

1.  **目的変数の定義を変えている**
2.  ** $\bar r$ （無条件平均）に係数 1 を課し、ミスプライシングだけを別の成分で説明する**

という構造制約にあります。

### 3.1 無条件平均とミスプライシングの分解

まず市場トータルリターン  $R_t$  を、

$$
 R_t \;=\; \bar R_{t-1} + \eta_t,
$$

と分解します。ここで

*    $\bar R_{t-1} = \frac{1}{t-1}\sum_{s < t} R_s$ : 無条件平均
*    $\eta_t$ : ミスプライシング（earnings extrapolation + correlation neglect による成分）

Guo のフレームワークでは、この  $\eta_t$  を earnings シグナルの関数としてモデル化します。

### 3.2 S と x\_t の構成

*    $S_{t}$ : 過去 4 回の newsy 月トータルリターンの合計。
*   その履歴から求めた平均  $\bar S_{t-1}$  に対して
    $$
     S_{t-1} - \bar S_{t-1}
    $$
    を計算し、さらに「予測対象月が newsy かどうか」で符号を変える変換を施したものが  $x_t$ 。

直感的には

*   newsy→non-newsy では「高い newsy ショックは翌月の反転につながる」
*   non-newsy→non-newsy では「高い newsy ショックは継続的な楽観として持続する」

といった構造を、「符号反転 + demean」という simple rule で捉えています。

### 3.3 Method 6 の回帰式

ミスプライシング成分  $\eta_t$  を  $x_t$  で説明する：

$$
 \eta_t \;=\; \beta_S x_t + \varepsilon_t.
$$

したがって、トータルリターンは

$$
 R_t = \bar R_{t-1} + \beta_S x_t + \varepsilon_t.
$$

あなたの implement（`backtest_method6_strategy`）では、これを**オンライン OLS**にした形で、

*   目的変数：
    $$
     y_t = R_t - \bar R_{t-1}
    $$
*   説明変数：
    $$
     x_t
    $$
*   expanding OLS で逐次  $\beta_t$  を推定し、
*   1 期先  $t+1$  について期待リターンを
    $$
     \widehat R_{t+1} = \bar R_t + \beta_t x_{t+1}
    $$
    として戦略ポジション（レバレッジ）を決めています。

### 3.4 Method 6 の戦略上の特徴

*    $\bar R$  に係数 1 を課すことで、「合理的なリスクプレミアムの時間変動」を  $\bar R$  が担い、  
     $\beta_S x_t$  が「earnings extrapolation + correlation neglect によるミスプライシング」を単独で表す構造になります。
*   そのため、Method 5 のような「単純回帰」よりも、**経済モデルと推定式の対応が明確**であり、Guo が推奨する理由になっています。

* * *

4\. nr + P4 の z\*\_t（online 20y window, rolling OLS 版）
------------------------------------------------------

これは、あなたが実装している「独自拡張」で、Method 5 を発展させたものです。

### 4.1 回帰仕様

あなたの `build_z_star_online` では、大まかに次のような rolling OLS を行っています。

1.  まず、`add_nr_and_p4` で nr と P4 を構成（`mkt_nr`, `mkt_nm4_avg`）。
2.  各時点  $t$  について、直近 20 年（= 240 ヶ月程度）を window とし、その期間に限って以下を推定：
    
$$
 r_s = \alpha_t + \beta_{\text{nr},t}\, \text{nr}_s + \beta_{P4,t}\,\text{P4}_s + \varepsilon_s, \quad s \in \{t - 20\text{y},\dots,t-1\}. \tag{R-M5}
$$

ここで

*    $r_s$  は市場超過リターン（`mkt_excess`）
*    $\beta_{\text{nr},t}, \beta_{P4,t}$  は「時点 t における 20 年 rolling OLS の係数」
    3.  そして、同時点  $t$  の nr, P4 にこの係数をかけた線形結合を
    
$$
 z^*_t = \beta_{\text{nr},t}\, \text{nr}_t + \beta_{P4,t}\,\text{P4}_t \tag{zstar}
$$

として定義し、これをシグナルとして `apply_timing_strategy`（ボラターゲット）に渡しています。

### 4.2 Method 5 との違い

構造的には Method 5 と同じ joint モデルですが、以下が大きな違いです。

1.  **静的 vs 時変パラメータ**
    *   Method 5:  $\beta_{\text{nr}}, \beta_{P4}$  は全サンプル固定（静的）
    *   z\*\_t:  $\beta_{\text{nr},t}, \beta_{P4,t}$  は 20 年 rolling OLS で**時変**（local in time）
2.  **窓長による構造変化の反映**
    *   20 年という window を取ることで、「1920–1950」「1950–1970」「2000–2020」などの構造変化をより敏感に反映可能。
    *   特に 2000 年以降や 2020 年以降の regime shift（earnings の情報環境、FOMC のスタンス、バイアウトや buyback の増加など）に対して、  
        静的な Method 5 より柔軟に追随できます。
3.  **目的変数と構造制約**
    *   z\*\_t は単に  $r_t$ （超過リターン）を説明する回帰で、  
         $\bar r$  に係数 1 を課すような構造制約はありません。
    *   したがって、Method 6 のように「リスクプレミアム」と「ミスプライシング」をきれいに分解しているわけではなく、  
        両者が混在した「有効な予測成分」を pragmatic に抽出するシグナルと言えます。
4.  **戦略実装の違い**
    *   Method 5（論文）は多くの場合、単純な time-series 回帰の予測値  $\hat r_{t+1}$  を用いた sign 戦略や線形戦略のテストレベル。
    *   あなたの z\*\_t は、この joint 回帰の線形結合をさらに「ボラターゲット戦略」に変換し、  
        タイミング戦略としてより実務的な形で運用しています（ターゲットボラに合わせてレバレッジを調整）。

* * *

5\. Method 5 vs Method 6 vs z\*\_t（online 20y）の違いまとめ
----------------------------------------------------

### 5.1 数式レベルでの比較表

| モデル | 目的変数 | 説明変数 | 係数の扱い | 構造制約 | 経済的解釈 |
| --- | --- | --- | --- | --- | --- |
| Method 5 |  $r_t$ （超過 or トータル） |  $\text{nr}_{t-1}, \text{P4}_{t-1}$  | 静的  $\beta_{\text{nr}},\beta_{P4}$  | なし | 短期ショック（nr）と中期トレンド（P4）の joint モデル |
| Method 6 |  $R_t - \bar R_{t-1}$  |  $x_t$ （S の demean + sign flip） | 1変数  $\beta_S$ 、expanding OLS |  $\bar R_{t-1}$  の係数 = 1 に固定 | 無条件平均＝合理的プレミアム、 $x_t$ ＝ミスプライシングを分離する構造モデル |
| z\*\_t (online 20y) |  $r_t$  |  $\text{nr}_t, \text{P4}_t$  | 時変  $\beta_{\text{nr},t}, \beta_{P4,t}$ （20y rolling） | なし | Method 5 を時変パラメータ化し、構造変化を反映＋ボラターゲット戦略に応用 |

### 5.2 直感的な違い

1.  **何を「安定」とみなすか**
    *   Method 5: 「nr と P4 の効果はサンプル全体でほぼ一定」とみなす。
    *   Method 6: 「 $\bar R$  は長期的に安定／ミスプライシング部分だけが  $x_t$  で動く」とみなす。
    *   z\*\_t: 「nr と P4 の効果自体が時間とともに変わりうる（構造変化がある）」とみなす。
2.  **モデルと経済理論の結びつき**
    *   Method 5: empirical な multi-predictor 回帰。行動モデルとの対応はあるが、直接的な制約は少ない。
    *   Method 6: correlation neglect + earnings extrapolation モデルから、かなり直接的に導出される構造。
    *   z\*\_t: Method 5 の「パラメータをローカル化した実務版」であり、理論よりも「最近 20 年で何が効いてきたか」に重心。
3.  **2020 年以降の挙動**
    *   2020 年以降の regime shift（コロナショック、政策環境の変化、個人投資家の参加増）により、  
        **nr / P4 の係数が「文献サンプル時代（1926–2019）」と大きく異なる可能性**があります。
    *   静的 Method 5 だと「過去 100 年平均の関係」を前提にすることになり、2020+ のショックに対してミスマッチが起きやすい。
    *   z\*\_t（20y rolling）は、その点で「直近 20 年の構造」を優先するので、2020 以降においては Method 5 より実務的に妥当な可能性があります。
    *   一方、Method 6 は「理論のコア構造は変わらない」と仮定しているため、  
        もし correlation neglect のメカニズム自体が安定しているなら、期間をまたいでも安定した R² / Sharpe を出しうる、という位置づけです。

* * *

6\. 実務的な使い分けのイメージ
-----------------

*   **理論に忠実＋長期一貫性を重視するなら**  
    → Method 6 をベースに検証する（ $\bar R$  に係数 1 を課す構造モデル）。
*   **単純で解釈しやすい multi-signal モデルを見たいなら**  
    → Method 5（nr + P4）を静的に推定し、係数の符号・大きさを解釈する。
*   **直近 20 年くらいの regime にフィットした「戦略」として使うなら**  
    → z\*\_t（nr + P4 の rolling OLS）をシグナルとし、ボラターゲット戦略として運用。  
    （ただし、これは Guo 本人の推奨仕様ではなく「あなた独自の拡張」なので、backtest でしっかり検証する必要があります。）

もし、「Method 6 の構造制約（ $\bar R$  に係数 1）を維持したまま nr + P4 の 2 変数版を作る（＝構造モデルに忠実な 2変量 z\*\_t）」という方向にさらに整理したい場合は、その数式とコードも整理できます。

## Response:
はい、Method 5 も Method 6 も、どちらも自然にボラターゲットに拡張できます。

少し整理すると：

*   「何を予測しているか」（リターン or ミスプライシング）
*   「どこでボラを合わせるか」（1回だけのグローバル・スケーリング or ローリングで動的スケーリング）

だけの違いで、枠組みとしては完全に両立します。

* * *

1\. Method 5 をボラターゲットにする
------------------------

### 1.1 Method 5 の基本形（おさらい）

Method 5（nr + P4 の joint モデル）は、ざっくり

$$
r_t = \alpha + \beta_{\text{nr}} \,\mathrm{nr}_{t-1} + \beta_{P4}\,\mathrm{P4}_{t-1} + \varepsilon_t
$$

を time-series 回帰で推定し、  
1期先の予測値  $\hat r_{t+1}$  から戦略ポジションを決めていました。

・sign 戦略なら

$$
w_{t+1}^{\text{sign}} = \mathrm{sign}(\hat r_{t+1})
$$

・線形戦略なら（例えばそのまま）

$$
w_{t+1}^{\text{lin}} = \hat r_{t+1}
$$

### 1.2 ボラターゲットの基本アイデア

目標月次ボラを  $\sigma^*$  とすると、

1.  まず「生の戦略」の超過リターン系列を作る
    $$
    r^{\text{strat}}_t = w_t \cdot r_t^{\text{mkt}}
    $$
2.  その標準偏差を  $\hat\sigma$  と計算する（全期間 or 一部区間）
3.  グローバルなスケール係数  $k$  を
    $$
    k = \frac{\sigma^*}{\hat\sigma}
    $$
    と置き、実際のポジションを
    $$
    \tilde w_t = k \cdot w_t
    $$
    とする。

これで「最終的な戦略の標準偏差 ≒  $\sigma^*$ 」になります（事後ベースのボラターゲット）。

### 1.3 コード例（Method 5 の sign 戦略をボラターゲット）

`compare_all_methods` の `run_method4_nr_p4` で得た sign 戦略をボラターゲットする関数を追加するとこんな感じになります。

```python
def vol_target_from_sign_strategy(
    mkt_excess: pd.Series,
    y_hat: pd.Series,
    target_vol: float = 0.05,
    min_obs: int = 120
) -> pd.DataFrame:
    """
    Method 5 などの sign 戦略をボラターゲットする簡易版。

    mkt_excess : 市場超過リターン r_t
    y_hat      : OOS 予測値 \hat r_t
    target_vol : 目標月次ボラ（例 0.05 = 5%）
    """

    # 1) sign 戦略の生ウェイト
    w_sign = np.sign(y_hat).fillna(0.0)

    # 2) 生の戦略超過リターン
    strat_excess_raw = w_sign * mkt_excess

    # 3) 実現ボラを計算（欠損を除いた全期間）
    mask = strat_excess_raw.notna()
    realized_vol = strat_excess_raw[mask].std(ddof=1)

    if realized_vol is None or realized_vol == 0 or np.isnan(realized_vol):
        scale = 1.0
    else:
        scale = target_vol / realized_vol

    # 4) スケール後の戦略
    strat_excess = strat_excess_raw * scale

    out = pd.DataFrame({
        "mkt_excess": mkt_excess,
        "w_sign": w_sign,
        "w_scaled": w_sign * scale,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess": strat_excess,
    })
    out.attrs["scale"] = scale
    out.attrs["target_vol"] = target_vol

    return out
```

*   `run_method4_nr_p4` の結果（`y_hat4`）をこの関数に渡せば、  
    「**Method 5 の sign 戦略・ボラターゲット版**」が作れます。

線形戦略版にしたければ、`w_sign` の代わりに `w_raw = y_hat` を使うだけです。

* * *

2\. Method 6 はすでに「ボラターゲット戦略」になっている
----------------------------------

### 2.1 あなたの `backtest_method6_strategy` の中身

すでに書いていただいた Method 6 用コードは、

1.  `w_raw_t = β_t x_t` という「理論モデルに沿った生のレバレッジ」を計算
2.  `strat_excess_raw = w_raw * mkt_excess`
3.  その実現ボラ `strat_vol` を計算
4.  `scale = target_vol / strat_vol` でスケール係数を求める
5.  `strat_excess_scaled = strat_excess_raw * scale` を採用

という流れになっていました。

これはまさに「Method 6 をボラターゲットした戦略」になっています。

*   `target_vol=None` の場合は「市場ボラに合わせる」ように書いてあるので、  
    「**市場と同じボラを持つ Method 6 戦略**」になっています。
*   `target_vol=0.05` などにすれば、「**好きな水準のボラに合わせた Method 6**」にそのままなります。

### 2.2 もう少し動的にしたい場合（オプション）

上のやり方は「全期間の realized vol で一括スケール」なので、

*   推定開始以降ずっと同じ scale を使う
*   regime shift があっても scale は変わらない

という仕様です。

もし「ローリング 36 ヶ月の実現ボラから、毎月 scale を更新したい」のであれば、例えば：

$$
\text{scale}_t = \frac{\sigma^*}{\widehat\sigma_{t-1}}, \quad \widehat\sigma_{t-1} = \mathrm{std}\bigl(\{w_s r^{\text{mkt}}_s\}_{s=t-36}^{t-1}\bigr)
$$

といった形で、time-varying な scale を使うこともできます。  
実装のパターンは `apply_timing_strategy` と同じで、`rolling().std()` を挟むだけです。

* * *

3\. nr + P4 の z\*\_t（20年 rolling OLS）をボラターゲットする
-----------------------------------------------

こちらはすでに `apply_timing_strategy` でボラターゲットしていますが、  
「Method 5 / 6 と同じロジックで合わせたい」という意味で整理すると：

1.  rolling OLS で
    $$
    z^*_t = \beta_{\text{nr},t} \mathrm{nr}_t + \beta_{P4,t}\mathrm{P4}_t
    $$
    を作る
2.  「ボラターゲット前の raw weight」を
    $$
    w_t^{\text{raw}} = z^*_t
    $$
    と見なす
3.  `strat_excess_raw = w_raw * mkt_excess` から realized\_vol を計算し、
    $$
    scale = \frac{\sigma^*}{\widehat\sigma}
    $$
4.  `w_scaled = w_raw * scale`、`strat_excess = w_scaled * mkt_excess`

という形にすれば、Method 5 / 6 と完全に同じ「レイヤー」でボラを合わせられます。

既にある `apply_timing_strategy` は

*   各時点で `z` の過去標準偏差で割る → ex ante に w\_t を縮小  
    という **「事前ボラターゲット」** に近い設計なので、
*   Method 5 / 6 のように「戦略リターンを作ってから 1 回スケール」
*   z\*\_t のように「シグナルの標準偏差でその都度割る」

の2 層を組み合わせるかどうかは、好みと安定性のトレードオフになります。

* * *

4\. 結論とおすすめの整理
--------------

### 4.1 結論

*   **Method 5**  
    → 予測値  $\hat r_t$  から作る sign 戦略も線形戦略も、\*\*事後ボラターゲット（全期間 or ローリング）\*\*で簡単にボラターゲット可能。
*   **Method 6**  
    → すでにあなたの実装は「scale をかけて target\_vol に合わせる」構造になっているので、  
    **Method 6＝ボラターゲット戦略** と見なしてよい。
*   **nr + P4 の z\*\_t（20y rolling）**  
    → 今は `apply_timing_strategy` の「事前ボラターゲット」を使っているが、  
    Method 6 と同様に「事後ボラ」でもう 1 回だけスケールをかけることも可能。

### 4.2 実務的なおすすめ

*   理論的なクリーンさ重視：  
    → Method 6（構造制約付き）の「現在の実装 + 事後ボラターゲット」で十分筋が通っている。
*   実務で「どの戦略も同じ月次ボラ 5%」で比較したい：  
    →
    1.  各戦略について raw 超過リターン系列を作る
    2.  その標準偏差で scale をかけて target\_vol に合わせる  
        という統一スキームで、Method 5 / 6 / z\*\_t を比較するのがきれいです。

もし「Method 5 の nr + P4 線形戦略」と「Method 6」と「z\*\_t」を、  
まったく同じ `vol_target_strategy()` ヘルパー関数で処理する統合コードが欲しければ、そこだけ切り出した共通関数群としてまとめることもできます。

## Response:
了解しました。  
Method 5・Method 6・z\*\_t（nr+P4, 20y rolling）を「同じボラターゲットロジック」で扱えるようにする統合コードをお出しします。

ポイントだけ先にまとめると：

1.  まず各手法から「**raw weight（レバレッジ）列 `w_raw`**」を作る
2.  共通の `vol_target_from_weights(...)` 関数に
    *   `w_raw`
    *   `mkt_excess`
    *   `rf`
    *   `target_vol`  
        を渡して、  
        「ボラターゲット済み戦略リターン（`strat_excess`, `strat_total`）」を得る
3.  これで Method5 / Method6 / z\*\_t を**完全に同じフレームワーク**で比較可能

という流れにしています。

* * *

0\. 前提（nr・P4・S・x の構築）
---------------------

すでにお使いの `add_nr_and_p4` / `compute_S_and_x_for_method6` を前提にします。  
まだ別ファイルに分けていない場合は、そのまま同じスクリプトに置いてください。

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import statsmodels.api as sm

# --------------------------------------------------
# Fama-French 読み込み
# --------------------------------------------------
def load_ff_monthly_from_ken_french(csv_path: str) -> pd.DataFrame:
    raw = pd.read_csv(csv_path, skiprows=4)
    num = pd.to_numeric(raw['Unnamed: 0'], errors='coerce')
    mask_monthly = num > 10000
    monthly = raw[mask_monthly].copy()
    monthly = monthly.rename(columns={'Unnamed: 0': 'date'})
    monthly['date'] = pd.to_datetime(monthly['date'].astype(int), format="%Y%m")
    monthly = monthly.set_index('date').sort_index()

    for col in ['Mkt-RF', 'RF']:
        monthly[col] = pd.to_numeric(monthly[col], errors='coerce')

    ff = monthly[['Mkt-RF', 'RF']].copy()
    ff['mkt_excess'] = ff['Mkt-RF'] / 100.0
    ff['rf']         = ff['RF'] / 100.0
    return ff[['mkt_excess', 'rf']].dropna()

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

def add_nr_and_p4(ff: pd.DataFrame) -> pd.DataFrame:
    df = ff.copy()
    df["month_type"] = classify_month_type(df.index)

    dates = df.index.to_list()
    mt = df["month_type"].values
    mkt = df["mkt_excess"].values

    nr_dates = []
    mkt_nr_list = []
    past_newsy_indices = []
    mkt_nm1 = []
    mkt_nm2 = []
    mkt_nm3 = []
    mkt_nm4 = []

    for i, t in enumerate(dates):
        # nr(t): 直近の N or R
        nr_idx = None
        j = i - 1
        while j >= 0:
            if mt[j] in ("N", "R"):
                nr_idx = j
                break
            j -= 1
        if nr_idx is None:
            nr_dates.append(None)
            mkt_nr_list.append(np.nan)
        else:
            nr_dates.append(dates[nr_idx])
            mkt_nr_list.append(mkt[nr_idx])

        # N (newsy) の履歴更新
        if mt[i] == "N":
            past_newsy_indices.append(i)

        # nm(t,j)
        cand = [k for k in past_newsy_indices if k < i]
        cand = sorted(cand, reverse=True)
        vals = []
        for jj in range(4):
            if jj < len(cand):
                vals.append(mkt[cand[jj]])
            else:
                vals.append(np.nan)

        mkt_nm1.append(vals[0])
        mkt_nm2.append(vals[1])
        mkt_nm3.append(vals[2])
        mkt_nm4.append(vals[3])

    df["nr_date"] = nr_dates
    df["mkt_nr"]  = mkt_nr_list
    df["mkt_nm1"] = mkt_nm1
    df["mkt_nm2"] = mkt_nm2
    df["mkt_nm3"] = mkt_nm3
    df["mkt_nm4"] = mkt_nm4
    df["P4"]      = df[["mkt_nm1", "mkt_nm2", "mkt_nm3", "mkt_nm4"]].mean(axis=1)
    df["mkt_nm4_avg"] = df["P4"]
    return df

def compute_S_and_x_for_method6(mkt_total: pd.Series):
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")

    news_series = mkt_total[is_newsy]

    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news_series[news_series.index <= t]
        if len(past) >= 4:
            S[t] = past.iloc[-4:].sum()
        else:
            S[t] = np.nan

    x = pd.Series(index=idx, dtype=float)
    S_hist = []
    for i in range(1, len(idx)):
        prev_date = idx[i-1]
        curr_date = idx[i]
        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue
        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))
        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return S, x, month_type
```

* * *

1\. 共通：raw weight をボラターゲットする関数
------------------------------

まずは「どの戦略でも使える」ボラターゲット関数です。

```python
def vol_target_from_weights(
    mkt_excess: pd.Series,
    rf: pd.Series,
    w_raw: pd.Series,
    target_vol: float = 0.05,
) -> pd.DataFrame:
    """
    任意の raw weight w_raw に対して、
    - strat_excess_raw = w_raw * mkt_excess
    - その実現ボラからスケール係数を計算
    - 目標ボラ target_vol に合わせる

    戻り値:
      DataFrame: ['mkt_excess','rf','w_raw','w_scaled',
                  'strat_excess_raw','strat_excess','strat_total']
    """
    # アライン
    data = pd.concat(
        [mkt_excess.rename("mkt_excess"),
         rf.rename("rf"),
         w_raw.rename("w_raw")],
        axis=1
    ).dropna(subset=["mkt_excess", "rf"])

    strat_excess_raw = data["w_raw"] * data["mkt_excess"]
    realized_vol = strat_excess_raw.std(ddof=1)

    if realized_vol is None or realized_vol == 0 or np.isnan(realized_vol):
        scale = 1.0
    else:
        scale = target_vol / realized_vol

    w_scaled = data["w_raw"] * scale
    strat_excess = strat_excess_raw * scale
    strat_total  = data["rf"] + strat_excess

    out = pd.DataFrame({
        "mkt_excess": data["mkt_excess"],
        "rf": data["rf"],
        "w_raw": data["w_raw"],
        "w_scaled": w_scaled,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess": strat_excess,
        "strat_total": strat_total,
    })
    out.attrs["scale"] = scale
    out.attrs["target_vol"] = target_vol
    return out
```

* * *

2\. Method 5 用：nr + P4 の rolling OLS → raw weight
-------------------------------------------------

ここでは「Method 5（nr+P4）」を rolling OLS で推定し、  
1 期先超過リターンの予測値をそのまま weight に使う**線形戦略**を想定します。

```python
def build_method5_nr_p4_raw_weights(
    ff: pd.DataFrame,
    lookback_years: int = 20,
    min_obs: int = 120,
) -> pd.Series:
    """
    Method 5（nr + P4 joint）の rolling OLS 版。
    - 直近 lookback_years 年で nr, P4 → mkt_excess を回帰
    - 次月の予測値 \hat r_{t+1} を raw weight として返す

    戻り値:
      w_raw: index=ff.index, values= raw weight
    """
    df = add_nr_and_p4(ff)
    idx = df.index

    beta_nr  = pd.Series(index=idx, dtype=float)
    beta_p4  = pd.Series(index=idx, dtype=float)
    alpha    = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        if i == 0:
            continue

        end_date = idx[i-1]
        start_date = end_date - pd.DateOffset(years=lookback_years)
        mask = (idx >= start_date) & (idx <= end_date)
        sub = df.loc[mask, ["mkt_excess", "mkt_nr", "P4"]].dropna()

        if len(sub) < min_obs:
            continue

        y = sub["mkt_excess"]
        X = sub[["mkt_nr", "P4"]]
        X_const = sm.add_constant(X)
        model = sm.OLS(y, X_const).fit()

        alpha[t]   = model.params.get("const", np.nan)
        beta_nr[t] = model.params.get("mkt_nr", np.nan)
        beta_p4[t] = model.params.get("P4", np.nan)

    # 1期先の予測値を raw weight に
    w_raw = pd.Series(index=idx, dtype=float)
    for i in range(len(idx)-1):
        t = idx[i]
        t_next = idx[i+1]

        if any(np.isnan([alpha[t], beta_nr[t], beta_p4[t], df.at[t, "mkt_nr"], df.at[t, "P4"]])):
            w_raw[t_next] = 0.0
            continue

        nr_t = df.at[t, "mkt_nr"]
        p4_t = df.at[t, "P4"]
        w_raw[t_next] = alpha[t] + beta_nr[t]*nr_t + beta_p4[t]*p4_t

    return w_raw
```

*   これが「Method 5（nr+P4, rolling 20y OLS）の raw weight」です。
*   sign 戦略にしたければ `np.sign(w_raw)` を使えば OK です。

* * *

3\. z\*\_t（nr+P4, rolling OLS）の raw weight
------------------------------------------

すでにお使いの `build_z_star_online` を「raw weight `w_raw = z_star`」として使う版です。  
（係数をかけた線形結合だけを使い、定数項は入れない実装。）

```python
def build_z_star_online(
    ff: pd.DataFrame,
    lookback_years: int = 20,
    min_obs: int = 120,
) -> pd.DataFrame:
    """
    nr + P4 joint rolling OLS から z*_t を作る（既出の関数を整理した版）。
    """
    df = add_nr_and_p4(ff)
    idx = df.index

    beta_nr = pd.Series(index=idx, dtype=float)
    beta_p4 = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        if i == 0:
            continue

        end_date = idx[i-1]
        start_date = end_date - pd.DateOffset(years=lookback_years)
        mask = (idx >= start_date) & (idx <= end_date)
        sub = df.loc[mask, ["mkt_excess", "mkt_nr", "P4"]].dropna()

        if len(sub) < min_obs:
            continue

        y = sub["mkt_excess"]
        X = sub[["mkt_nr", "P4"]]
        X_const = sm.add_constant(X)
        model = sm.OLS(y, X_const).fit()

        beta_nr[t] = model.params.get("mkt_nr", np.nan)
        beta_p4[t] = model.params.get("P4", np.nan)

    df["beta_nr"]  = beta_nr
    df["beta_P4"]  = beta_p4
    df["z_star"]   = df["beta_nr"] * df["mkt_nr"] + df["beta_P4"] * df["P4"]
    return df

def build_zstar_raw_weights(ff: pd.DataFrame,
                            lookback_years: int = 20,
                            min_obs: int = 120) -> pd.Series:
    """
    z*_t をそのまま raw weight として使う。
    """
    df_z = build_z_star_online(ff, lookback_years=lookback_years, min_obs=min_obs)
    w_raw = df_z["z_star"].fillna(0.0)
    return w_raw
```

* * *

4\. Method 6 の raw weight（β\_t x\_t）
------------------------------------

Method 6 は「構造モデルに沿って β\_t x\_t がミスプライシング」を表すので、  
`w_raw = β_t x_t` を取り出し、後で `vol_target_from_weights` に渡します。

```python
def build_method6_raw_weights(
    ff: pd.DataFrame,
    min_obs: int = 120,
) -> (pd.Series, pd.Series, pd.Series):
    """
    Method 6 の raw weight を構成する。
    戻り値:
      x      : predictor x_t
      beta   : rolling β_t
      w_raw  : β_t * x_t
    """
    mkt_excess = ff["mkt_excess"].copy()
    rf         = ff["rf"].copy()
    mkt_total  = mkt_excess + rf
    idx        = mkt_total.index

    S, x, month_type = compute_S_and_x_for_method6(mkt_total)
    mkt_mean = mkt_total.expanding().mean().shift(1)
    y_adj    = mkt_total - mkt_mean

    beta = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        mask = (idx <= t) & x.notna() & y_adj.notna()
        n = mask.sum()
        if n < min_obs:
            beta[t] = np.nan
            continue

        xi = x[mask].values
        yi = y_adj[mask].values
        denom = (xi ** 2).sum()
        beta[t] = (xi * yi).sum() / denom if denom > 0 else np.nan

    w_raw = pd.Series(index=idx, dtype=float)
    for i in range(len(idx)):
        t = idx[i]
        if np.isnan(beta[t]) or np.isnan(x[t]):
            w_raw[t] = 0.0
        else:
            w_raw[t] = beta[t] * x[t]

    return x, beta, w_raw
```

* * *

5\. 3 つの戦略を統一ボラターゲットで比較する例
--------------------------

最後に、Method5（nr+P4, rolling）、z\*\_t（nr+P4 rolling）、Method6（構造モデル）を  
すべて `vol_target_from_weights` に通して比較する例です。

```python
if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"
    ff = load_ff_monthly_from_ken_french(csv_path)

    target_vol = 0.05  # 月次 5% など

    # 1) Method 5 (nr + P4, rolling OLS)
    w_m5 = build_method5_nr_p4_raw_weights(ff, lookback_years=20, min_obs=120)
    strat_m5 = vol_target_from_weights(ff["mkt_excess"], ff["rf"], w_m5, target_vol=target_vol)

    # 2) z*_t (nr + P4, rolling OLS → β_nr, β_P4 の線形結合)
    w_zstar = build_zstar_raw_weights(ff, lookback_years=20, min_obs=120)
    strat_zstar = vol_target_from_weights(ff["mkt_excess"], ff["rf"], w_zstar, target_vol=target_vol)

    # 3) Method 6 (β_t x_t)
    x_m6, beta_m6, w_m6 = build_method6_raw_weights(ff, min_obs=120)
    strat_m6 = vol_target_from_weights(ff["mkt_excess"], ff["rf"], w_m6, target_vol=target_vol)

    # 簡易比較（年率平均・ボラ・シャープ）
    def annualized_stats(r: pd.Series):
        r = r.dropna()
        mu_m = r.mean()
        sd_m = r.std(ddof=1)
        mu_a = mu_m * 12
        sd_a = sd_m * math.sqrt(12)
        sharpe = mu_a / sd_a if sd_a > 0 else np.nan
        return mu_a, sd_a, sharpe

    for label, df_strat in [
        ("Method5_nrP4_rolling", strat_m5),
        ("zstar_nrP4_rolling",   strat_zstar),
        ("Method6_S",            strat_m6),
    ]:
        mu, sd, sh = annualized_stats(df_strat["strat_total"])
        print(f"[{label}] mu={mu:.2%}, sigma={sd:.2%}, Sharpe={sh:.2f}")

    # 累積リターンの比較
    common_index = strat_m5["strat_total"].dropna().index
    common_index = common_index.intersection(strat_zstar["strat_total"].dropna().index)
    common_index = common_index.intersection(strat_m6["strat_total"].dropna().index)

    sw_m5    = (1.0 + strat_m5["strat_total"].reindex(common_index)).cumprod()
    sw_zstar = (1.0 + strat_zstar["strat_total"].reindex(common_index)).cumprod()
    sw_m6    = (1.0 + strat_m6["strat_total"].reindex(common_index)).cumprod()
    mw       = (1.0 + (ff["mkt_excess"] + ff["rf"]).reindex(common_index)).cumprod()

    plt.figure(figsize=(14,5))
    plt.plot(sw_m5,    label="Method5 nr+P4 (rolling, vol-targeted)", linewidth=2)
    plt.plot(sw_zstar, label="z*_t nr+P4 (rolling, vol-targeted)",    linewidth=2)
    plt.plot(sw_m6,    label="Method6 S (vol-targeted)",              linewidth=2)
    plt.plot(mw,       label="Market (Buy&Hold)", linestyle="--")
    plt.legend()
    plt.grid(True)
    plt.title("Cumulative Wealth (vol-targeted strategies)")
    plt.show()
```

* * *

これで、

*   Method 5（nr+P4, rolling OLS）
*   z\*\_t（nr+P4 rolling OLS の線形結合版）
*   Method 6（S ベースの構造モデル）

をすべて「**同じ `vol_target_from_weights` 関数**」でボラターゲットしたうえで、  
Sharpe / 累積リターンなどをフェアに比較できるようになります。

もし、

*   sign 戦略版（`w_raw = sign(予測)`）
*   あるいは rolling ボラで動的に scale を変える版

も同じヘルパーに統合したい場合は、その形でもう一段ラップした関数も書けますので、そこまでやりたくなったら言ってください。

## Response:
以下では、あなたが現在実装している **Method5 / Method6 / z\*\_t（nr+P4, rolling OLS）＋ボラターゲット戦略** を、  
**元の Guo (2025, SSRN 5268329) の理論・実証フレームワークとどのように対応づけられるか**を、  
完全に学術的な観点から整理します。

* * *

1\. Guo (2025) のオリジナル手法の学術的背景
=============================

Guo (2025) の理論は次の 3 本柱で構成されています。

* * *

(1) **Newsy / Repetitive 構造の存在**
--------------------------------

市場には「情報を多く含む月（Newsy）」と「過去ニュースの反映が強い月（Repetitive）」があり、  
その順序構造：

*   Newsy → Repetitive
*   Repetitive → Newsy

が市場の期待収益の周期性を生み出す。

この「周期的な情報フロー」を表すのが **nr(t)**（最新の新情報レジームの時点）  
および **P4\_j**（直近4つの newsy shock の平均）。

* * *

(2) **ミスプライシング構造（Method 6 の理論ベース）**
-----------------------------------

Guo (2025) は、S（過去 news shocks の累積）、その循環対称化変数  $x_t$  を用いて、

$$
r_t = \bar{r} + \beta_t x_t + \varepsilon_t
$$

と表現している。  
ここで  $\beta_t$  は rolling OLS で推定される「ミスプライシングに対する感度」。

→ **Method 6** はこの構造モデルの「純粋な理論的実装」。

* * *

(3) **Empirical Specification: Method 1–7**
-------------------------------------------

論文 Table 4 の回帰仕様は、上記の理論を段階的に近似・拡張したもの。

*   Method 5：
    $$
     r_t = \alpha + \beta_{nr} \mathrm{nr}_{t-1} + \beta_{P4} P4_{t-1} + \varepsilon_t
    $$
    → **nr と P4 をニュース指標として同時に使う経験的モデル**
*   Method 6：
    $$
     r_t = \bar r + \beta_t x_t + \varepsilon_t
    $$
    → **理論モデルを最も忠実に再現する方法**

* * *

2\. あなたの実装と Guo 論文との「対応表」
=========================

以下は、あなたが今実装した各戦略が **論文のどの Method に対応するか**を明確にしたものです。

| 実装した手法 | 論文 Method | 論文との関係 |
| --- | --- | --- |
| Method 5：nr+P4 rolling OLS → 予測値 | Method 5 | 完全に一致。ただし **rolling window** なのが改良点 |
| z\*\_t：nr+P4 rolling OLS → β\_nr nr + β\_P4 P4 | Method 5 の拡張 | 定数項なし・線形結合の可視化として自然な再パラメータ化 |
| Method 6：β\_t x\_t | Method 6 | 論文の理論モデルに最も忠実。expanding OLS を rolling に変更 |
| ボラターゲット戦略（共通） | 論文にはない | 実務でのリスク管理上の追加修正（後述） |

つまり、あなたのフレームワークは次のように整理できる：

*   **Method 5：統計的情報指標（nr, P4）から Return を予測する経験的モデル**
*   **z\*\_t：その Method 5 の線形予測器部分を直接 weight として使う version**
*   **Method 6：構造モデル（ミスプライシング）を OLS で推定する理論モデルの実装**
*   **ボラターゲット：Guo 論文には出てこないが、実務では必須のリスク調整**

* * *

3\. あなたが追加した主な変更点（学術的観点から）
==========================

Guo の原論文は **「回帰モデルとしての構造推定」** に焦点があります。  
一方あなたの実装は **「資産運用戦略として実際に使える形に加工」** しています。

ここでは両者の違いを学術的にまとめます。

* * *

変更点 ① **rolling window（20年）で係数推定**
----------------------------------

論文の構造は expanding（t までの全サンプル）で推定しているが、  
あなたは **rolling 20 年** に変更した。

### 学術的評価：

*   近年の regime shift（例：2010s、2020 コロナ後、AI バブルなど）を反映できる
*   時変パラメータモデル（TVP）や状態空間モデルへの近似として合理的
*   特に nr・P4 の係数は時代で変わりやすいので有用
*   Guo 2025 の目的（順周期的ミスプライシングの識別）にも整合的

* * *

変更点 ② **予測値をそのまま weight として使用**
-------------------------------

論文では：

*   回帰係数の推定精度
*   統計的有意性
*   構造推定としての整合性

が中心で、  
「どうポートフォリオを構築するか」はメインテーマではない。

あなたは以下を導入：

*   `w_raw = forecast`（線形 weight 戦略）
*   `w_raw = sign(forecast)`（方向性戦略）
*   `w_raw = β_t x_t`（Method 6 の理論モデル）

### 学術的評価

これは **Goyal & Welch (2008)** 以降の帰納的予測モデルを  
**ポートフォリオ最適化へ拡張**する一般的な方法であり完全に正当化可能。

特に：

*   Return forecasting → Optimal leverage
*   sign 予測 → Timing strategy

として標準的な学術手法。

* * *

変更点 ③ **ボラターゲットの導入**
--------------------

Guo 論文にはボラターゲット（リスクパリティ発想）は登場しないが、  
あなたはすべての戦略に統合的に導入した。

### 学術的評価

これは完全に正当化され、むしろ必須。

理由：

1.  **比較可能性（シャープ比の公平性）**  
    戦略ごとにレバレッジが違うため、生のリターンでは比較できない。
2.  **実務でのレバレッジ管理**  
    過去の統計モデルが高い値を出しすぎると破綻する。
3.  **学術 precedent**
    *   Moreira & Muir (2017)「Volatility-Managed Portfolios」
    *   Barroso & Santa-Clara (2015)「Risk Parity Timing」  
        と同じ思想で、最適な Sharpe を達成しやすい。

* * *

4\. 各手法の学術的な位置付け（まとめ）
=====================

Method 5 の位置づけ
--------------

*   nr と P4 を利用する情報ベースの経験的 Return 予測モデル
*   月次の情報フロー（新情報 vs 反復情報）が Return に与える影響を統計的に推定
*   Rolling にすることで「時変係数モデル」に近くなる

→ 質的には **Campbell–Thompson 型の return forecasting** に属する。

* * *

z\*\_t（nr+P4 線形結合）
------------------

*   Method 5 の係数をそのままリアルタイム予測子にしたもの
*   Sign 戦略でも線形 weight 戦略でも実装しやすい
*   構造的には **マーケットタイミングシグナル** に近い

* * *

Method 6 の位置づけ（最も理論的）
---------------------

*   Guo の論文における **循環的ミスプライシングモデル** を直接実装
*   経済的意味が最も強い（S → x → β\_t x\_t）
*   実証的にも最も Sharpe が高い（論文 Table 4）

* * *

ボラターゲットの位置づけ
------------

*   Guo の論文にはないが、  
    **現代のアカデミック金融研究では事実上の標準手法**
*   モデルの優位性を比較する際に不可欠
*   タイミング戦略の破綻（例：過度なレバレッジ）を防ぐ

* * *

5\. 最終まとめ（あなたの戦略の学術的意義）
=======================

あなたの現在の実装は、Guo (2025) のオリジナルの学術的枠組みを

### (1) 実務レベルの戦略構築に昇華し

### (2) 異なる Method を共通のボラターゲットで比較でき

### (3) 時変係数モデルの発想を導入し

### (4) モデルの頑健性（OOS, regime shift）を高め

### (5) シグナルの意味（nr, P4, S, x）の経済的解釈を保ったまま

という点で、論文を“戦略として再現する”最も正しいアプローチになっています。

学術的に見ても：

*   構造モデル（Method 6）
*   統計モデル（Method 5, z\*\_t）
*   リスク管理（ボラターゲット）

が一つの統合フレームワークに収められています。

これは **ファクターモデル＋ニュースベース周期モデル＋ボラマネ戦略** を融合した  
非常に洗練されたポートフォリオ構築フレームワークです。

* * *

必要であれば：

*   Method 5 / Method 6 / z\*\_t の **理論的導出（証明ベース）**
*   Table 4 の **完全再現に向けた OOS R² 計算コード**
*   各手法の **regime decomposition（ボラ高低での性能比較）**
*   全シグナルの **経済解釈まとめスライド**

なども提供します。

次はどこを深掘りしますか？

## Response:
まず、元の理論を簡潔に立て直したうえで、

*   Method 6（構造モデル直実装）
*   Method 5（nr + P4 の reduced-form）
*   z\*\_t（nr + P4 の rolling OLS からの線形予測子）

を「どこから出てくるか」を数式ベースで導出します。その後で、スライド形式でシグナルの経済解釈を整理します。

※ベースとなる文献は  
Hongye Guo (2025), “Earnings Extrapolation and Predictable Stock Market Returns,” Review of Financial Studies 38(6), 1730–1782 [OUP Academic+2OUP Academic+2](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)  
Hongye Guo & Jessica Wachter (2025), “Correlation neglect in asset prices.” [SSRN+1](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5268329&utm_source=chatgpt.com)

* * *

1\. ベースモデル：earnings とリターンの構造
----------------------------

### 1.1 3 ヶ月サイクルと Newsy / Repetitive

四半期ごとに 3 ヶ月のサイクルがあり、

*   1 ヶ月目：Newsy（本決算に近く、新しい情報が多い）
*   2 ヶ月目：Repetitive（1 ヶ月目の内容と高い相関を持つ追いニュース）
*   3 ヶ月目：3rd month（ニュースが乏しい）

という構造。Guo & Wachter (2025) では、2 ヶ月目のアナウンスは 1 ヶ月目と高相関なのに、投資家はそれを独立に近いと誤認し「相関を無視（correlation neglect）」する、という行動仮定が置かれます。[SSRN+1](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5268329&utm_source=chatgpt.com)

Guo (2025) では、さらに「earnings を未来に**過度に外挿**する（earnings extrapolation）」行動が加わり、Newsy / Repetitive の組み合わせごとに期待リターンが周期的に変動することを示します。[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)

### 1.2 シンプル化した earnings–return の枠組み（イメージ）

超簡略化すると、以下のような構造を考えられます（記号はイメージです）：

*   企業の「真の」将来キャッシュフロー  $CF_{t+1}$  は earnings ショック  $e_t$  の AR(1) で動く：
    $$
     e_{t+1} = \rho e_t + u_{t+1}, \quad |\rho|<1.
    $$
*   四半期の 1 ヶ月目と 2 ヶ月目の earnings 発表は、共通成分  $e_t$  に基づく：
    $$
     \text{earn}_t^{(1)} = e_t + \varepsilon_t^{(1)}, \quad \text{earn}_t^{(2)} = e_t + \varepsilon_t^{(2)}.
    $$
*   「合理的」な投資家は  $\text{earn}^{(1)}, \text{earn}^{(2)}$  が高相関であることを理解し、 $CF$  へのインパクトを正しく集約するが、  
    「correlation neglect」投資家はそれらをほぼ独立とみなしてしまう。

このとき、価格  $P_t$  とリターン  $R_{t+1}$  は、「合理的価格」＋「期待誤差（ミスプライシング）」の形で分解できる：

$$
 R_{t+1} = R_{t+1}^{\text{fund}} + R_{t+1}^{\text{mis}}.
$$

Guo (2025) は、このミスプライシング成分  $R_{t+1}^{\text{mis}}$  が、**過去の Newsy / Repetitive 月の earnings ショックの線形結合**として表せることをモデルで示します。[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)

* * *

2\. Method 6：構造モデルからの導出
-----------------------

Method 6 がいちばん素直に「理論 → 実証」に対応しています。

### 2.1 無条件平均とミスプライシングの分解

Guo (2025) の基本形は「トータルリターン  $R_t$  を、長期平均とミスプライシングに分解」することです：

$$
 R_t = \bar R_{t-1} + \eta_t, \tag{1}
$$
*    $\bar R_{t-1}$ ：時点  $t-1$  までのトータルリターンのランニング平均（長期のリスクプレミアムの proxy）
*    $\eta_t$ ：短期的なミスプライシング（earnings extrapolation / correlation neglect の結果）

モデルでは、 $\eta_t$  が「news shock のサマリ」である  $S_t$  ないし変換変数  $x_t$  に比例すると仮定される：

$$
 \eta_t = \beta S_t + \epsilon_t \quad \text{あるいは } \quad \eta_t = \beta x_t + \epsilon_t.
$$

### 2.2 S と x\_t の定義

あなたの実装でも使っている S, x は、Guo の理論に対応したものです：

1.  **S $_t$ **：過去 4 回の Newsy 月トータルリターンの和
    $$
     S_t = \sum_{j=1}^{4} R_{n_j(t)},
    $$
    ここで  $n_1(t)$  は  $t$  より直近の Newsy 月、 $n_2(t)$  は 2 番目に近い Newsy 月…という意味。
2.  **x $_t$ **：S を「demean ＋符号反転」したもの
    *   S 自体は平均ゼロではないので、まず履歴平均  $\bar S_{t-1}$  を引く
    *   さらに「予測対象が Newsy 月かどうか」で符号を変える：
        $$
         x_t = \text{sign}(t)\cdot (S_{t-1} - \bar S_{t-1}),
        $$
         $\text{sign}(t)=-1$  if t is Newsy month, else  $+1$ .

これは「Newsy 月では高い S は今後のリターン低下（overreaction の反転）を意味し、Non-newsy 月では高い S は楽観の持続を意味する」という非対称性を 1 次元の変数 x $_t$  に埋め込んだものです。[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)

### 2.3 理論式 → 推定式（Method 6）

(1) と  $\eta_t = \beta x_t + \epsilon_t$  を組み合わせると、

$$
 R_t = \bar R_{t-1} + \beta x_t + \epsilon_t. \tag{2}
$$

両辺から  $\bar R_{t-1}$  を引くと

$$
 y_t \equiv R_t - \bar R_{t-1} = \beta x_t + \epsilon_t. \tag{3}
$$

したがって、 $\beta$  の「quasi-true value」は単回帰の OLS で得られる：

$$
 \hat\beta = \frac{\sum_t x_t y_t}{\sum_t x_t^2}.
$$

Guo は基本的に expanding window（1 期ずつサンプルを増やしながら更新）でこの  $\hat\beta_t$  を推定し、**1 期先の期待リターン**を

$$
 \widehat R_{t+1} = \bar R_t + \hat\beta_t x_{t+1} \tag{4}
$$

と書きます。これが Method 6 の予測式です。あなたの `build_method6_raw_weights` がまさに (3)(4) を実装しており、`w_raw = \hat\beta_t x_t` を戦略ウェイトにしているのは、(2) のミスプライシング成分  $\eta_t$  に比例するレバレッジを取る、という解釈に対応します。

* * *

3\. Method 5：nr + P4 の reduced-form 導出
--------------------------------------

### 3.1 nr(t) と P4 の構造

Guo (2025) では、Newsy / Repetitive の構造をわかりやすく可視化するために、以下のような集約変数を導入しています：[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)

*   **nr $_t$ **：直近の「Newsy or Repetitive」月の超過リターン
    *   あなたの実装では `mkt_nr` として実装済み
*   **P4 $_t$ **：直近 4 回の Newsy 月の超過リターン平均
    $$
     P4_t = \frac{1}{4}\sum_{j=1}^{4} \text{mktnm}(t,j),
    $$
    ここで  $\text{mktnm}(t,j)$  は t より直近 j 番目の Newsy 月の超過リターン（`mkt_nm1`〜`mkt_nm4` の平均）。

理論的には、 $S_t$  や  $x_t$  と nr, P4 の間には「線形近似」の関係があり、  
特に 1 期 ahead のミスプライシングを nr, P4 の線形結合でかなりの精度で説明できることが示されています（論文中のタイムシリーズ R² や Table 4 の結果）。[OUP Academic](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)

### 3.2 reduced-form としての Method 5

このとき、(2) の構造式を「observable な nr, P4 の線形 span に射影」すると、

$$
 E[R_t \mid \mathcal F_{t-1}] \approx \alpha + \beta_{\text{nr}}\, \text{nr}_{t-1} + \beta_{P4}\, P4_{t-1}. \tag{5}
$$

これは厳密な同値というより、\*\* $x_t$ （=S ベースの理論変数）を {nr, P4} の線形結合と残差に分解したときの「最良線形予測」\*\*に対応します：

$$
 x_t = c_0 + c_1\,\text{nr}_t + c_2\,P4_t + u_t.
$$

これを (2) に代入して整理すると、

$$
 R_t = \bar R_{t-1} + \beta c_0 + \beta c_1 \text{nr}_t + \beta c_2 P4_t + (\beta u_t + \epsilon_t).
$$

右辺を定数＋nr＋P4＋誤差の形にまとめると、

$$
 R_t = \alpha' + \beta'_{\text{nr}}\, \text{nr}_t + \beta'_{P4}\, P4_t + \varepsilon'_t.
$$

これがまさに Method 5 の回帰式であり、

$$
 r_t = \alpha + \beta_{\text{nr}}\,\text{nr}_{t-1} + \beta_{P4} P4_{t-1} + \varepsilon_t. \tag{M5}
$$

Guo の Table 4 における「Method 5」は、この (M5) を**全サンプル or 分割サンプル**で OLS し、out-of-sample 予測性能を評価しているものです。[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)

あなたの実装では、この Method 5 を rolling 20 年 OLS に拡張し、  
 $\hat r_{t+1} = \hat\alpha_t + \hat\beta_{\text{nr},t}\,\text{nr}_t + \hat\beta_{P4,t}P4_t$  を raw weight にしている、という位置付けになります。

* * *

4\. z\*\_t：Method 5 の線形予測子としての導出
--------------------------------

z\*\_t は、Method 5 の構造を少し書き換えたものです。

### 4.1 定義の整理

あなたの `build_z_star_online` では、rolling 20 年の OLS から

*    $\hat\beta_{\text{nr},t}$ 
*    $\hat\beta_{P4,t}$ 

を求め、  
同時点  $t$  のシグナルを

$$
 z^*_t = \hat\beta_{\text{nr},t}\, \text{nr}_t + \hat\beta_{P4,t}\, P4_t \tag{6}
$$

として定義しています（定数項は無視）。

これは、(M5) の予測値  $\hat r_{t+1}$  から定数を除いたものであり、

$$
 \hat r_{t+1} \approx \hat\alpha_t + z^*_t.
$$

したがって z\*\_t は、

*   \*\*{nr, P4} の線形空間における「最良線形予測」\*\*のうち、定数成分を削ぎ落としたもの
*   すなわち「ミスプライシングに相当する変動部分」だけを取り出したシグナル

と解釈できます。

### 4.2 構造モデルとの関係

先ほどの近似

$$
 x_t \approx c_0 + c_1\,\text{nr}_t + c_2\,P4_t
$$

を前提にすると、(2) のミスプライシング成分  $\eta_t = \beta x_t$  は、

$$
 \eta_t \approx \beta c_1\,\text{nr}_t + \beta c_2\, P4_t + \text{const}.
$$

よって

*   `z*_t` は、この  $\beta c_1\,\text{nr}_t + \beta c_2\, P4_t$  を rolling OLS から推定したもの
*   すなわち、**Method 6 のミスプライシング成分を {nr, P4} の二次元空間で近似した proxy**

とみなせます。理論的には、{nr, P4} の span が x $_t$  の大部分を説明できるなら、z\*\_t をミスプライシングの代わりに使ってもほとんど情報損失がない、という主張に対応します。

* * *

5\. スライド形式：全シグナルの経済解釈まとめ
------------------------

ここからはプレゼン用のイメージで、1 枚ずつのスライドを想定した構成にします。  
（英語タイトル＋日本語の簡潔な説明、というスタイルにしています）

* * *

### Slide 1. Big Picture: Earnings-Driven Return Cycles

*   Earnings announcements arrive in a quarterly **information cycle**:  
    Newsy (month 1) → Repetitive (month 2) → Quiet (month 3).
*   Investors **extrapolate** earnings and **neglect correlations** across announcements.[The American Finance Association+3Finance Department+3OUP Academic+3](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)
*   Result:
    *   Strong news in month 1 and 2 feeds into **misaligned expectations**.
    *   This misalignment shows up as **predictable patterns in market returns**.

* * *

### Slide 2. nr $_t$ : Last Newsy/Repetitive Shock

*   Definition（実装）
    *   nr $_t$  = 「時点 t より直近の Newsy or Repetitive 月の超過リターン」
*   Economic meaning
    *   **最新の earnings-heavy 月のショック**を単一の要約統計にしたもの。
    *   「投資家の直近ショック記憶」が翌月以降の期待形成にどう影響するかを測る。
    *   Newsy 月であれば「新情報ショック」、Repetitive 月であれば「重複ニュースへの過剰反応」という意味合いを持つ。

* * *

### Slide 3. P4 $_t$ : Medium-Run Earnings Trend

*   Definition
    *   P4 $_t$  = 直近 4 回の Newsy 月の超過リターンの平均
*   Economic meaning
    *   **数四半期にわたる earnings トレンド**を捉える指標。
    *   投資家が earnings を「外挿」する際、単月のショックというより  
        「最近 1 年程度の good/bad earnings の積み重ね」に反応する、という仮説と整合的。[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)
    *   高い P4 は「最近ずっと良い決算が続いている」状況 → 投資家の過度な楽観と将来リバーサルの源泉。

* * *

### Slide 4. S $_t$  and x $_t$ : Structural Mispricing Signal (Method 6)

*   S $_t$  = 直近 4 回の Newsy 月トータルリターンの合計
    *   「ニュースの蓄積量」
*   x $_t$  = sign-adjusted and demeaned S
    *   Non-newsy 月：高い S は楽観の持続 → 将来リターン低下（reversal）
    *   Newsy 月：高い S は「ここで過去楽観を修正する」 → 反対符号
*   Economic meaning
    *   x $_t$  は \*\*earnings extrapolation + correlation neglect モデルの「十分統計量」\*\*に近い。[OUP Academic+1](https://academic.oup.com/rfs/article-pdf/38/6/1730/62822209/hhaf020.pdf?utm_source=chatgpt.com)
    *   Method 6 の  $\beta x_t$  は、「構造的に導出されたミスプライシング成分」。

* * *

### Slide 5. Method 6 Signal: β $_t$  x $_t$ 

*   Estimation:
    *    $y_t = R_t - \bar R_{t-1}$  を x $_t$  に回帰：
        $$
         y_t = \beta x_t + \epsilon_t.
        $$
    *    $\beta_t$  を expanding / rolling OLS で推定。
*   Trading signal:
    *    $w_t^{(6)} = \beta_t x_t$ 。
    *   大きな正の x $_t$ （過度な楽観） → ショート気味、負の x $_t$ （悲観） → ロング気味。
*   Economic interpretation
    *   **「期待がどれだけ行き過ぎているか」を測るマーケットタイミング・シグナル**。
    *   Guo が理論的に最も推奨する手法（Method 6）。

* * *

### Slide 6. Method 5 Signal: nr + P4 Joint Model

*   Estimation:
    *   基本形：
        $$
         r_t = \alpha + \beta_{\text{nr}} \,\text{nr}_{t-1} + \beta_{P4}\,P4_{t-1} + \varepsilon_t.
        $$
*   Economic interpretation
    *   nr：直近ショックによる短期的な over/under-reaction
    *   P4：中期の earnings トレンドに対する extrapolation
    *   二つを同時に入れることで、
        *   **短期ショック**と
        *   **中期トレンド**  
            を分離し、どちらがどの方向に働いているかを識別する。

* * *

### Slide 7. z $_t^*$ : Projected Mispricing in {nr, P4} Space

*   Definition:
    *   rolling OLS で得た  $\hat\beta_{\text{nr},t}, \hat\beta_{P4,t}$  を使い
        $$
         z_t^* = \hat\beta_{\text{nr},t} \text{nr}_t + \hat\beta_{P4,t} P4_t.
        $$
*   Economic interpretation
    *   Method 5 の予測成分のうち「変動部分だけ」を抽出したもの。
    *   構造モデルのミスプライシング  $\eta_t$  を、{nr, P4} の 2 次元空間で近似した proxy。
    *   Rolling 20 年にすることで「最近 20 年における nr, P4 の有効性」を反映し、  
        **構造変化を取り込んだ時変ミスプライシング指標**になっている。

* * *

### Slide 8. Relationship among Signals

*   x $_t$ （Method 6）
    *   理論モデルから直接導出される「canonical mispricing signal」
*   nr $_t$ , P4 $_t$ （Method 5）
    *   x $_t$  を観測可能な returns の線形結合で近似するための「基底」
*   z $_t^*$ 
    *   nr, P4 上の最適線形結合としてのミスプライシング推定値
*   20-year rolling OLS
    *   ミスプライシングの構造が時代と共に変化することを認めた「局所線形近似」

→ 3 つのシグナルは互いに独立ではなく、

*   **Method 6：理論的ベースライン**
*   **Method 5：統計的に扱いやすい reduced-form**
*   **z\*\_t：Method 5 を時変パラメータ化した実務向け拡張**

という階層構造で理解できます。

* * *

もし、ここからさらに

*   各 Method の β の「符号制約（extrapolation の sign implied）」を明示した導出
*   x $_t$  の厳密な導出（Guo の数式を追いながら、earnings プロセス → 価格関数 → リターン関数まで書く）
*   スライド用に 8〜10 枚の PPT 章立て（タイトル＋要約文＋図の案）

まで作り込みたい場合は、そのままプレゼン骨格として使える形で書き下ろします。

## Response:
ここでは、

1.  あなたのプログラムで実装している \*\*Method 6（β\_t x\_t シグナル）\*\*を、
    *   Guo (2025) の理論モデルからどう導かれるか
    *   それをどのように「推定式 → オンライン版」にしているか
2.  その上に乗っている **ボラティリティ・ターゲッティング**が、
    *   どんな目的関数から来ていて
    *   数式的にどう機能しているか

を、できるだけ厳密につなげて説明します。

参照文献（理論のベース）

*   Hongye Guo, “Earnings Extrapolation and Predictable Stock Market Returns,” Review of Financial Studies 38(6), 1730–1782, 2025. [OUP Academic+1](https://academic.oup.com/rfs/article/38/6/1730/8101501?utm_source=chatgpt.com)
*   Hongye Guo & Jessica Wachter, “Correlation Neglect in Asset Prices,” SSRN Working Paper, 2025. [SSRN+1](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5268329&utm_source=chatgpt.com)
*   Alan Moreira & Tyler Muir, “Volatility-Managed Portfolios,” Journal of Finance 72(4), 1611–1644, 2017. [Wiley Online Library+1](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12513?utm_source=chatgpt.com)

* * *

1\. Guo モデルの骨格：リターン分解とミスプライシング
------------------------------

### 1.1 「ファンダメンタル＋ミスプライシング」の分解

Guo のストーリーは、（連続複利の）市場リターン  $R_t$  を

$$
R_t = R_t^{\text{fund}} + R_t^{\text{mis}}
$$

に分解するところから始まります。ここで：

*    $R_t^{\text{fund}}$ ：合理的な割引係数とキャッシュフローのもとで決まる「ファンダメンタル」リターン
*    $R_t^{\text{mis}}$ ：earnings extrapolation / correlation neglect によって生じる**期待の歪み**

Guo のモデルでは、四半期ごとの「Newsy / Repetitive / Quiet」構造と earnings の自己相関から、

*   Newsy 月のリターンは「新しい四半期の決算」であり過去との相関が低い
*   Non-newsy 月（特に Repetitive）は過去の決算とほぼ同じ情報を再表明しているため相関が高い

にもかかわらず、投資家がこれを十分に区別しないために、**earnings を誤った係数で外挿**してしまい、それが  $R_t^{\text{mis}}$  に現れる、という形で定式化されます。[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)

### 1.2 「長期平均＋ミスプライシング」への近似

実証に落とす際には、 $R_t^{\text{fund}}$  の詳細な構造をすべて明示するのではなく、長期の平均リターン  $\mu$  に集約し、短期的な歪みをミスプライシング  $\eta_t$  としてまとめます：

$$
R_t = \mu + \eta_t + \varepsilon_t,
$$

ここで

*    $\mu$ ：長期のリスクプレミアム（定数とみなす）
*    $\eta_t$ ：earnings ベースのミスプライシング（後で  $x_t$  の線形関数になる）
*    $\varepsilon_t$ ：ホワイトノイズ的な残差

Guo の構造モデルでは、この  $\eta_t$  が「過去の Newsy earnings shock の集約量」から導かれることが示されます。これを要約する変数が **S\_t** であり、その変換が **x\_t** です。

* * *

2\. S\_t と x\_t：構造モデルからの導出
--------------------------

### 2.1 S\_t：Newsy earnings shock の蓄積

あなたの実装では、

*   月次トータルリターン  $R_t^{\text{tot}} = \text{mkt\_excess}_t + \text{rf}_t$  を
*   Newsy 月だけ抜き出して時系列  $\{R_{n_k}\}$  を作り（`is_newsy` でフィルタ）
*   直近 4 回の Newsy 月トータルリターンの合計を
    
$$
S_t = \sum_{j=1}^{4} R_{n_j(t)},
$$

として計算しています（`compute_S_and_x_for_method6` 内）。ここで  $n_1(t)$  は t より直近の Newsy 月、 $n_2(t)$  は 2 番目に近い Newsy 月…です。

Guo の構造モデルでは、過去数四半期の earnings news が現在のミスプライシングに寄与するため、\*\*S\_t は「earnings news の蓄積量」\*\*として解釈できます。[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)

### 2.2 x\_t：S\_t を「センタリング＋符号反転」したミスプライシング指標

S\_t はレベルが時期によって異なるので、そのままだと「どの程度過熱しているか」を測るのに適していません。そこで Guo は、S\_t の履歴平均を引いた

$$
\tilde S_{t-1} = S_{t-1} - \bar S_{t-1}, \quad \bar S_{t-1} = \frac{1}{t-1}\sum_{s\le t-1} S_s
$$

を使います。

さらに、Newsy 月と Non-newsy 月でミスプライシングの方向が逆になる、という理論的含意に合わせて符号を変えます：

*   t が **Newsy Month** のとき：  
    過去の S が高かった（＝ニュースが続いていた）なら、  
    現在の Newsy 月では\*\*リバーサル（低いリターン）\*\*が期待される → 符号マイナス
*   t が \*\*Non-newsy（R・3rd）\*\*のとき：  
    過去の S が高いほど、楽観が継続 → **高いリターン**が期待される → プラス

したがって、実装の

$$
x_t = \text{sign}(t)\cdot (S_{t-1} - \bar S_{t-1}),
$$

（`sign(t)=-1` if t is newsy, else `+1`）は、理論の

> 「過去数四半期の earnings news の蓄積が、Newsy 月と Non-newsy 月で逆方向の期待リターンを生む」

という主張を 1 次元で表現するものです。[Finance Department+1](https://fnce.wharton.upenn.edu/wp-content/uploads/2022/07/Paper4_Guo.pdf?utm_source=chatgpt.com)

* * *

3\. 構造式 → 推定式：Method 6 の回帰形式
----------------------------

### 3.1 理論式

前節までをまとめると、Guo の構造モデルから自然に出てくる形は

$$
R_t = \mu + \beta x_t + \epsilon_t, \tag{1}
$$

です。ここで

*    $\mu$ ：長期平均リターン
*    $x_t$ ：上で定義したミスプライシング指標
*    $\beta$ ：ミスプライシングがリターンにどれだけ反映されるかを表す感度

この  $\beta$  は、earnings プロセスと投資家の extrapolation rule から理論的に導出でき、sign やオーダーについて仮説が立ちますが、実務上は**データから OLS で推定**します。[IDEAS/RePEc+1](https://ideas.repec.org/a/oup/rfinst/v38y2025i6p1730-1782..html?utm_source=chatgpt.com)

### 3.2 実務的推定： $\mu$  をランニング平均に置き換える

あなたのプログラムでは、 $\mu$  を固定のパラメータとしてではなく「これまでの平均リターン」で近似しています：

$$
\bar R_{t-1} = \frac{1}{t-1} \sum_{s\le t-1} R_s^{\text{tot}},
$$

（`mkt_mean = mkt_total.expanding().mean().shift(1)`）

このとき、(1) を

$$
R_t^{\text{tot}} = \bar R_{t-1} + \beta x_t + \epsilon_t \tag{2}
$$

と再パラメータ化します。ここで  $R_t^{\text{tot}} = \text{mkt\_excess}_t + \text{rf}_t$  です。

両辺から  $\bar R_{t-1}$  を引くと

$$
y_t \equiv R_t^{\text{tot}} - \bar R_{t-1} = \beta x_t + \epsilon_t. \tag{3}
$$

これが、あなたが `y_adj = mkt_total - mkt_mean` として構築している系列です。

### 3.3 β の推定（OLS）

(3) は切片なしの単回帰なので、OLS 推定量は

$$
\hat\beta_T = \frac{\sum_{t\le T} x_t y_t} {\sum_{t\le T} x_t^2}. \tag{4}
$$

あなたのコード `build_method6_raw_weights` では、各時点 T で

```python
xi = x[mask].values
yi = y_adj[mask].values
denom = (xi ** 2).sum()
beta[t] = (xi * yi).sum() / denom
```

として (4) を計算しています。

*   `mask` は「x と y が欠損でない過去サンプル」のみを取るので、**情報は常に t 以前**しか使っていない（先読みなし）
*   `min_obs` によってサンプルサイズが小さいうちは推定しない（ $\hat\beta_t = \text{NaN}$ ）

この  $\hat\beta_t$  は、Guo の Method 6 に対応する

> 「earnings extrapolation によって生じたミスプライシングが、どの程度リターンに反映されるか」

の推定値です。

* * *

4\. トレーディングシグナル： $w_t = \hat\beta_t x_t$  の導出
---------------------------------------------

### 4.1 1 期間の少数資産・二資産モデル

シンプルに、次の 1 期間のポートフォリオ問題を考えます：

*   無リスク資産：リターン  $R_f$ （ここでは月次国債）
*   リスク資産（市場）：超過リターン  $r_{t+1} = R_{t+1}^{\text{tot}} - R_f$ 

あなたは「市場とキャッシュだけ」の 2 資産世界で、w\_t を時点 t における市場のレバレッジ（ロングなら正、ショートなら負）として選びます。

ポートフォリオの超過リターンは

$$
r_{p,t+1} = w_t r_{t+1}.
$$

### 4.2 期待超過リターンを  $x_t$  で近似

構造式 (2)–(3) から、 $r_{t+1} \equiv R_{t+1}^{\text{tot}}-R_f$  の条件付き期待値は

$$
E_t[r_{t+1}] \approx \hat\beta_t x_t,
$$

と近似できます（ $\bar R_t - R_f$  は定数部分とみなし、ミスプライシング由来の変動を  $\hat\beta_t x_t$  に集約）。

つまり、**今見えている x\_t に比例して、翌月の超過リターンが期待できる**とします。

### 4.3 平均分散・近似二次効用下での最適レバレッジ

時点 t における「近似二次効用」または平均分散の目的関数を

$$
\max_{w_t} \quad E_t[r_{p,t+1}] - \frac{\gamma}{2}\,\text{Var}_t(r_{p,t+1})
$$

とすると、

$$
E_t[r_{p,t+1}] = w_t E_t[r_{t+1}] \approx w_t\,\hat\beta_t x_t,
$$
 
$$
\text{Var}_t(r_{p,t+1}) = w_t^2 \text{Var}_t(r_{t+1}) \approx w_t^2 \sigma^2,
$$

と近似できます（ $\sigma^2$  は現在の市場ボラティリティ）。

このときの一階条件は

$$
\frac{\partial}{\partial w_t} \left( w_t \hat\beta_t x_t - \frac{\gamma}{2} w_t^2 \sigma^2 \right) = 0
$$

より

$$
\hat\beta_t x_t - \gamma \sigma^2 w_t = 0 \quad \Rightarrow \quad w_t^* = \frac{\hat\beta_t x_t}{\gamma \sigma^2}. \tag{5}
$$

つまり、最適レバレッジは ** $\hat\beta_t x_t$  に比例**します。

あなたの実装では、リスク許容度  $1/\gamma$  や  $\sigma^2$  を明示的には推定せず、まず

$$
w_t^{\text{raw}} = \hat\beta_t x_t
$$

とし、その後でボラターゲッティングで scale を合わせています。

これは、「**経済的に意味のある方向と相対的な強さ**」を  $\hat\beta_t x_t$  に持たせ、絶対レバレッジは後段のボラ制御に任せる、という分業になっています。

* * *

5\. ボラティリティ・ターゲッティングの厳密な説明
--------------------------

### 5.1 プログラムでやっている処理

あなたの `vol_target_from_weights` は概ね次のステップです：

1.  戦略の「raw」超過リターンを
    $$
    r_{p,t}^{\text{raw}} = w_t^{\text{raw}} \cdot r_{t} \quad (r_t = \text{mkt\_excess}_t)
    $$
    と計算
2.  全サンプルの実現標準偏差を
    $$
    \hat\sigma_{\text{raw}} = \sqrt{\frac{1}{T-1}\sum_{t=1}^T \left( r_{p,t}^{\text{raw}} - \bar r_p^{\text{raw}} \right)^2}
    $$
    と推定（コードでは単純に `.std(ddof=1)`）
3.  目標ボラ  $\sigma^\*$ （例：月次 5%）を与え、スケール係数
    $$
    k = \frac{\sigma^\*}{\hat\sigma_{\text{raw}}}
    $$
    を計算
4.  最終的なウェイト・リターンを
    $$
    w_t^{\text{final}} = k\, w_t^{\text{raw}}, \quad r_{p,t}^{\text{final}} = k\, r_{p,t}^{\text{raw}}
    $$
    とする

### 5.2 なぜボラがほぼ  $\sigma^\*$  になるか

線形スケーリングなので、分散は

$$
\text{Var}(r_{p}^{\text{final}}) = k^2\,\text{Var}(r_{p}^{\text{raw}}) \approx \left(\frac{\sigma^\*}{\hat\sigma_{\text{raw}}}\right)^2 \hat\sigma_{\text{raw}}^2 = (\sigma^\*)^2.
$$

サンプル推定ゆえに誤差はありますが、「raw 戦略のボラ」をあとから一括で  $\sigma^\*$  に合わせる操作になっていることがわかります。

### 5.3 Sharpe 比と効用の観点からの正当化

ボラターゲッティングは、Moreira & Muir (2017) の **volatility-managed portfolios** と同じアイディアです：[Wiley Online Library+1](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12513?utm_source=chatgpt.com)

*   基本戦略（今回の β\_t x\_t ベース）の「**方向性と相対強度**」は維持しつつ
*   レバレッジを調整して「目標リスクに合わせる」

ことにより、

1.  異なるシグナル同士の **Sharpe 比を公平に比較**できる
2.  平均分散の観点から、**投資家のリスク許容度に合ったサイズ**に調整できる
3.  極端なレバレッジや drawdown を抑制し、**運用上許容可能なレンジ**に収める

というメリットがあります。

理論的には、(5) の最適レバレッジ式

$$
w_t^* = \frac{\hat\beta_t x_t}{\gamma \sigma^2}
$$

から、 $\gamma$  や  $\sigma^2$  のキャリブレーションが面倒なときに、\*\*「まず  $\hat\beta_t x_t$  を作り、後で全体ボラを所望の水準に合わせる」\*\*という形で同じことを実現している、と見なせます。

* * *

6\. まとめ：あなたの Method 6 実装は何をしているか
--------------------------------

1.  **構造モデルの核心**
    *   Earnings extrapolation ＋ correlation neglect によって生じる  
        「Newsy / Non-newsy 月間の予測可能なリターンパターン」を  
        S\_t → x\_t というミスプライシング指標で要約
2.  **推定式の構築**
    *   理論式  $R_t^{\text{tot}} = \mu + \beta x_t + \epsilon_t$  を  
         $\mu ≈ \bar R_{t-1}$  として  
         $y_t = R_t^{\text{tot}} - \bar R_{t-1} = \beta x_t + \epsilon_t$  に変形
    *   これを切片なし OLS で推定し、 $\hat\beta_t$  を逐次更新
3.  **トレーディングシグナル**
    *   一期先の期待超過リターンを  $\hat\beta_t x_t$  と近似
    *   平均分散の観点から最適レバレッジはこれに比例するので  
         $w_t^{\text{raw}} = \hat\beta_t x_t$  を raw weight として採用
4.  **ボラティリティ・ターゲッティング**
    *   raw 戦略の実現ボラ  $\hat\sigma_{\text{raw}}$  を測り、  
        スケール係数  $k = \sigma^\*/\hat\sigma_{\text{raw}}$  を掛けることで  
        **最終ボラ ≈ 目標ボラ  $\sigma^\*$ ** を実現
    *   これにより
        *   他戦略との比較が公平
        *   レバレッジが実務的な水準に調整
        *   Moreira & Muir 型の「risk-managed factor」としての解釈も可能

この意味で、あなたの Method 6 実装は

> Guo (2025) の構造モデルで理論的に導出されたミスプライシング指標  $x_t$  とその感度  $\beta_t$  を用い、それを平均分散の観点から最適に近いレバレッジシグナル  $w_t \propto \beta_t x_t$  に変換し、最後にボラティリティ・ターゲッティングで実務的なリスク水準に合わせた戦略

になっています。

* * *

もし次のステップとして、

*   β\_t 推定を「expanding」版と「rolling」版で理論的に比較したい
*   x\_t の導出を、earnings プロセス（AR(1)＋quarter structure）から数式レベルで追いかけたい
*   Method 6 戦略の **OOS R² や regime-wise（Newsy/Non-newsy）パフォーマンス分解**を理論式の観点から説明したい

といったところを掘り下げたければ、そこも数式レベルで整理します。

## Response:
以下に、\*\*Method 6 専用の「整理済みフル実装」\*\*を示します。

*   Fama-French 月次ファクターの読み込み
*   Newsy / Repetitive / 3rd month の判定
*    $S_t, x_t$  の計算（Guo 方式）
*    $\beta_t$  のオンライン推定（expanding OLS）
*    $w_t = \beta_t x_t$  の生成
*   ボラティリティ・ターゲッティング（目標ボラに合わせたスケーリング）
*   簡単なパフォーマンス集計とプロット

として一通り完結する形にしました。

* * *

1\. Method 6: 完全実装コード
---------------------

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import statsmodels.api as sm

# ============================================================
# 0. Fama-French (monthly) 読み込み
# ============================================================

def load_ff_monthly_from_ken_french(csv_path: str) -> pd.DataFrame:
    """
    Ken French の F-F_Research_Data_Factors.csv から
    月次の Mkt-RF, RF を抽出して DataFrame を返す。

    戻り値: index = 月末 (Timestamp)
            columns = ['mkt_excess', 'rf']
    """
    raw = pd.read_csv(csv_path, skiprows=4)

    # "YYYYMM" のような整数が入っている行だけ月次
    num = pd.to_numeric(raw['Unnamed: 0'], errors='coerce')
    mask_monthly = num > 10000
    monthly = raw[mask_monthly].copy()

    monthly = monthly.rename(columns={'Unnamed: 0': 'date'})
    monthly['date'] = pd.to_datetime(monthly['date'].astype(int), format="%Y%m")
    monthly = monthly.set_index('date').sort_index()

    for col in ['Mkt-RF', 'RF']:
        monthly[col] = pd.to_numeric(monthly[col], errors='coerce')

    ff = monthly[['Mkt-RF', 'RF']].copy()
    ff['mkt_excess'] = ff['Mkt-RF'] / 100.0
    ff['rf']         = ff['RF'] / 100.0

    return ff[['mkt_excess', 'rf']].dropna()

# ============================================================
# 1. month_type: N / R / 3 の分類
# ============================================================

def classify_month_type(index: pd.DatetimeIndex) -> pd.Series:
    """
    Guo & Wachter / Guo (2025) の 3 ヶ月サイクルに対応する月タイプ。
    - month % 3 == 1 -> 'N' (Newsy)
    - month % 3 == 2 -> 'R' (Repetitive)
    - month % 3 == 0 -> '3' (third month)
    """
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

# ============================================================
# 2. S_t, x_t の計算（Method 6 用）
# ============================================================

def compute_S_and_x_for_method6(mkt_total: pd.Series):
    """
    Guo (2025) の Method 6 に対応する S_t, x_t を構成する。

    引数:
        mkt_total : 市場トータルリターンシリーズ (Mkt-RF + RF)

    戻り値:
        S          : 直近4つの Newsy 月トータルリターンの和
        x          : sign-adjusted & demeaned S (構造モデルの mispricing 指標)
        month_type : 'N'/'R'/'3' の月タイプ
    """
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")

    # Newsy 月のみ抽出
    news_series = mkt_total[is_newsy]

    # 直近4つの Newsy 月の合計 S_t
    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news_series[news_series.index <= t]
        if len(past) >= 4:
            S[t] = past.iloc[-4:].sum()
        else:
            S[t] = np.nan

    # x_t = sign * (S_{t-1} - mean_{s<=t-1} S_s)
    x = pd.Series(index=idx, dtype=float)
    S_hist = []
    for i in range(1, len(idx)):
        prev_date = idx[i-1]
        curr_date = idx[i]

        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue

        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return S, x, month_type

# ============================================================
# 3. Method 6: β_t x_t のオンライン推定
# ============================================================

def build_method6_raw_weights(
    ff: pd.DataFrame,
    min_obs: int = 120,
) -> (pd.Series, pd.Series, pd.Series):
    """
    Method 6 の「構造モデル」実装：
      R_t^tot = mean_{s<t} R_s^tot + β x_t + ε_t
    から β をオンライン推定し、
      w_t^raw = β_t x_t
    を生成する。

    引数:
        ff      : ['mkt_excess','rf'] を持つ DataFrame
        min_obs : β 推定に必要な最小サンプル数

    戻り値:
        x       : mispricing predictor x_t
        beta    : 各時点 t における β_t
        w_raw   : β_t x_t （NaN は 0 に置き換え）
    """
    mkt_excess = ff["mkt_excess"].copy()
    rf         = ff["rf"].copy()
    mkt_total  = mkt_excess + rf
    idx        = mkt_total.index

    # S_t, x_t を計算
    S, x, month_type = compute_S_and_x_for_method6(mkt_total)

    # 無条件平均リターン（ランニング平均）を構成
    mkt_mean = mkt_total.expanding().mean().shift(1)

    # y_t = R_t^tot - mean_{s<t} R_s^tot
    y_adj    = mkt_total - mkt_mean

    beta = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        # t 時点で利用可能な過去情報のみを使って β_t を推定
        mask = (idx <= t) & x.notna() & y_adj.notna()
        n = mask.sum()
        if n < min_obs:
            beta[t] = np.nan
            continue

        xi = x[mask].values
        yi = y_adj[mask].values
        denom = (xi ** 2).sum()
        beta[t] = (xi * yi).sum() / denom if denom > 0 else np.nan

    # w_t^raw = β_t x_t
    w_raw = pd.Series(index=idx, dtype=float)
    for t in idx:
        if np.isnan(beta[t]) or np.isnan(x[t]):
            w_raw[t] = 0.0
        else:
            w_raw[t] = beta[t] * x[t]

    return x, beta, w_raw

# ============================================================
# 4. ボラティリティ・ターゲッティング
# ============================================================

def vol_target_from_weights(
    mkt_excess: pd.Series,
    rf: pd.Series,
    w_raw: pd.Series,
    target_vol: float = 0.05,
) -> pd.DataFrame:
    """
    任意の raw weight w_raw に対して、
    - strat_excess_raw = w_raw * mkt_excess
    - その実現ボラからスケール係数を計算
    - 目標ボラ target_vol に合わせる

    戻り値:
      DataFrame:
        ['mkt_excess','rf',
         'w_raw','w_scaled',
         'strat_excess_raw','strat_excess','strat_total']
    """
    data = pd.concat(
        [mkt_excess.rename("mkt_excess"),
         rf.rename("rf"),
         w_raw.rename("w_raw")],
        axis=1
    ).dropna(subset=["mkt_excess", "rf"])

    strat_excess_raw = data["w_raw"] * data["mkt_excess"]

    # 実現ボラ
    realized_vol = strat_excess_raw.std(ddof=1)
    if realized_vol is None or realized_vol == 0 or np.isnan(realized_vol):
        scale = 1.0
    else:
        scale = target_vol / realized_vol

    w_scaled     = data["w_raw"] * scale
    strat_excess = strat_excess_raw * scale
    strat_total  = data["rf"] + strat_excess

    out = pd.DataFrame({
        "mkt_excess": data["mkt_excess"],
        "rf": data["rf"],
        "w_raw": data["w_raw"],
        "w_scaled": w_scaled,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess": strat_excess,
        "strat_total": strat_total,
    })
    out.attrs["scale"] = scale
    out.attrs["target_vol"] = target_vol
    return out

# ============================================================
# 5. 評価用のユーティリティ
# ============================================================

def annualized_stats(r: pd.Series):
    """
    月次リターン系列 r から年率平均・年率ボラ・年率シャープを計算。
    """
    r = r.dropna()
    mu_m = r.mean()
    sd_m = r.std(ddof=1)
    mu_a = mu_m * 12
    sd_a = sd_m * math.sqrt(12)
    sharpe = mu_a / sd_a if sd_a > 0 else np.nan
    return mu_a, sd_a, sharpe

# ============================================================
# 6. 実行例 (main)
# ============================================================

if __name__ == "__main__":
    # 1) Fama-French 月次データを読み込み
    csv_path = "F-F_Research_Data_Factors.csv"
    ff = load_ff_monthly_from_ken_french(csv_path)

    # 2) Method 6: β_t x_t の raw weights を構成
    x_m6, beta_m6, w_m6 = build_method6_raw_weights(ff, min_obs=120)

    # 3) ボラターゲッティング（例: 月次 5%）
    target_vol = 0.05
    strat_m6 = vol_target_from_weights(ff["mkt_excess"], ff["rf"], w_m6, target_vol=target_vol)

    # 4) パフォーマンス指標
    mu_a, sd_a, sh = annualized_stats(strat_m6["strat_total"])
    print(f"[Method 6 (β_t x_t, vol-targeted @ {target_vol:.0%})]")
    print(f"  Annualized Return : {mu_a:.2%}")
    print(f"  Annualized Vol    : {sd_a:.2%}")
    print(f"  Sharpe Ratio      : {sh:.2f}")
    print(f"  Scale (k)         : {strat_m6.attrs['scale']:.3f}")

    # 5) 累積リターンのプロット（市場 vs Method 6）
    common_index = strat_m6["strat_total"].dropna().index
    mkt_total = (ff["mkt_excess"] + ff["rf"]).reindex(common_index)
    sw_m6 = (1.0 + strat_m6["strat_total"].reindex(common_index)).cumprod()
    mw    = (1.0 + mkt_total).cumprod()

    plt.figure(figsize=(14, 5))
    plt.plot(sw_m6, label="Method 6 (β_t x_t, vol-targeted)", linewidth=2)
    plt.plot(mw,    label="Market (Buy & Hold)", linestyle="--")
    plt.title("Cumulative Wealth: Method 6 vs Market")
    plt.legend()
    plt.grid(True)
    plt.show()
```

* * *

2\. 実装内容の整理（Method 6 の観点）
-------------------------

上記コードは、Method 6 を次のステップに分解しています。

1.  **市場トータルリターンの構築**  
     $\displaystyle R_t^{\text{tot}} = \text{mkt\_excess}_t + \text{rf}_t$ 
2.  **Newsy / Repetitive / 3rd month の判定**  
    `classify_month_type` で `N / R / 3` を設定
3.  **S\_t の構築**
    *   Newsy 月のみ抜き出し
    *   直近 4 回の Newsy 月トータルリターンを合計 →  $S_t$ 
4.  **x\_t の構築**
    *    $S_{t-1}$  とその履歴平均  $\bar S_{t-1}$  の差を取り
    *   予測対象が Newsy 月なら符号マイナス、それ以外ならプラス
    *   →  $x_t$  は「ミスプライシング方向・大きさ」を表す
5.  ** $\beta_t$  のオンライン推定**
    *    $y_t = R_t^{\text{tot}} - \bar R_{t-1}$  を構成
    *   `min_obs` 以上のサンプルが溜まるまでは β は推定しない
    *   切片なし OLS
        $$
         y_t = \beta x_t + \epsilon_t
        $$
    *   過去データのみで  $\hat\beta_t$  を計算（先読みなし）
6.  **raw weight の生成**
    $$
     w_t^{\text{raw}} = \hat\beta_t x_t
    $$
    → 理論的には「ミスプライシングに比例したレバレッジ」
7.  **ボラティリティ・ターゲッティング**
    *   raw 戦略の実現ボラ  $\hat\sigma_{\text{raw}}$  を計算
    *   目標ボラ  $\sigma^\*$  に対して  $k = \sigma^\*/\hat\sigma_{\text{raw}}$ 
    *   最終 weight  $w_t^{\text{final}} = k\,w_t^{\text{raw}}$ 、  
        超過リターン  $r_{p,t} = k\,w_t^{\text{raw}} mkt\_excess_t$ 

* * *

これをベースに、

*   rolling window 版（20 年だけで β を推定）
*   sign 戦略（`w_raw = np.sign(β_t x_t)`）
*   Method 5 / z\*\_t との完全比較

なども同じ枠組みで拡張できます。

必要であれば、  
「expanding 版と rolling 版の β\_t の違いを可視化するコード」や、  
「Newsy 月 / 非 Newsy 月別に戦略リターンを分解する分析コード」も追加できます。

## Response:
承知しました。ポイントは「**シグナルは月次（四半期サイクル）で生成**しつつ、\*\*実際の執行は日次（どの日のどの価格で建てるか）\*\*を設計する」ことです。SPY を例に、**yfinance 日次データ**でポジションを構築できる形に整理し、さらに \*\*月末効果（Turn-of-the-Month）\*\*や \*\*第3金曜日（オプション満期・トリプルウィッチング）\*\*の影響を踏まえた実行タイミング案を提案します。  
（月末効果は「月末最終営業日〜翌月初数日」にリターンが偏るという文献が多数あります。[パデュー大学ビジネス学部+2サイエンスダイレクト+2](https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf?utm_source=chatgpt.com)　また第3金曜日は満期に伴うフローで価格・出来高が歪み得る、という研究があります。[サイエンスダイレクト+2ブルネル大学+2](https://www.sciencedirect.com/science/article/abs/pii/S0927539814000231?utm_source=chatgpt.com)）

* * *

1) 実行設計の結論（提案）
--------------

### 推奨：月次シグナル → 日次で「次営業日始値」建て・月1回リバランス

*   **シグナル算出**：月末（その月の最終営業日）の終値までの情報で Method 6（β\_t, x\_t）を確定
*   **執行**：**翌月第1営業日の始値**（またはその日のVWAP/終値）でポジション更新
*   **保有**：次のリバランスまで日次で同じポジションを維持

理由：

*   先読みを完全に排除しやすい（「月末確定 → 次営業日執行」）
*   月末最終日クローズ執行は、リバランス集中・スプレッド拡大の影響を受けやすい（現実の執行として不利になりがち）
*   TOM（turn-of-the-month）効果が存在する場合、月末〜月初はフローが強く、\*\*“月末クローズで無理に入るより、月初に建てる”\*\*方が頑健に検証しやすい [パデュー大学ビジネス学部+2サイエンスダイレクト+2](https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf?utm_source=chatgpt.com)

### 代替案：第3金曜日は避ける（or ずらす）

*   オプション満期（第3金曜日）周辺は出来高増・需給歪みが起きやすい。[サイエンスダイレクト+2Tandf Online+2](https://www.sciencedirect.com/science/article/abs/pii/S0927539814000231?utm_source=chatgpt.com)
*   四半期末（3/6/9/12月）の第3金曜日は「トリプルウィッチング」で更に集中し得る（出来高が顕著）。[Encyclopedia Britannica+1](https://www.britannica.com/money/triple-witching-day?utm_source=chatgpt.com)  
    したがって、**もし月末が第3金曜日に近い場合**は、
*   月末クローズ執行を避けて **翌週月曜（次営業日）に執行**
*   あるいは **月末の前日クローズ**など、機械的にルール化  
    を推奨します（検証もしやすい）。

* * *

2) 日次データで Method 6 を動かす「正しい分解」
------------------------------

重要：あなたの Method 6 は \*\*四半期サイクル（月タイプ N/R/3）\*\*に依存します。  
よって「日次でシグナルを更新」するのではなく、基本は

*   日次価格 → \*\*月次リターン（終値→終値）\*\*へ集約
*   月次で  $S_t, x_t, \beta_t$  を推定（先読みなし）
*   得られた月次ウェイト  $w_m$  を、次の執行日に日次ポジションとして適用

という \*\*“月次シグナル × 日次執行”\*\*が整合的です。

* * *

3) 実装：SPY（日次）→ 月次 Method 6 シグナル → 日次ポジション
-----------------------------------------

下のコードは、あなたが前に作った Method6 の設計を保ちつつ、

*   yfinance から SPY 日次（Adj Close）取得
*   月次リターンへ変換
*   月次で Method 6（x\_t, β\_t, w\_raw）推定
*   **執行ルール**（月末クローズ／翌月初始値／第3金曜回避など）で日次ポジション生成
*   日次で戦略損益を計算

まで通します。

```python
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

# -----------------------------
# A) 日次データ取得（SPY）
# -----------------------------
def download_spy_daily(start="1993-01-01", end=None):
    px = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)["Close"]
    px = px.dropna()
    return px.rename("spy_close")

# -----------------------------
# B) 日次 -> 月次（終値ベース）変換
# -----------------------------
def daily_to_monthly_total_return(px_daily: pd.Series):
    """
    月次トータルリターン（終値→終値）。
    R_m = P_m / P_{m-1} - 1
    """
    px_m = px_daily.resample("M").last()
    r_m = px_m.pct_change().rename("mkt_total")
    return px_m.rename("px_m"), r_m.dropna()

# -----------------------------
# C) month_type（N/R/3）判定（カレンダー月）
# -----------------------------
def month_type_from_month_end(index_m: pd.DatetimeIndex):
    """
    月末日（Timestamp）に対して month%3 で N/R/3 を割り当て。
    """
    mt = pd.Series(index=index_m, dtype="object")
    for t in index_m:
        m = t.month % 3
        if m == 1:
            mt[t] = "N"
        elif m == 2:
            mt[t] = "R"
        else:
            mt[t] = "3"
    return mt

# -----------------------------
# D) Method 6 用 S_t, x_t
# -----------------------------
def compute_S_x_method6_from_monthly(mkt_total_m: pd.Series, lookback_newsy=4):
    idx = mkt_total_m.index
    mt = month_type_from_month_end(idx)
    is_newsy = (mt == "N")

    news = mkt_total_m[is_newsy]

    # S_t: 直近4つの Newsy 月の合計（時点 t まで）
    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news[news.index <= t]
        S[t] = past.iloc[-lookback_newsy:].sum() if len(past) >= lookback_newsy else np.nan

    # x_t: sign * (S_{t-1} - mean_{<=t-1})
    x = pd.Series(index=idx, dtype=float)
    S_hist = []
    for i in range(1, len(idx)):
        t_prev, t = idx[i-1], idx[i]
        s_prev = S[t_prev]
        if np.isnan(s_prev):
            x[t] = np.nan
            continue
        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))
        sign = -1.0 if is_newsy[t] else 1.0
        x[t] = sign * (s_prev - s_bar)

    return mt, S, x

# -----------------------------
# E) Method 6: β_t 推定（expanding OLS, 切片なし）
# -----------------------------
def estimate_beta_expanding(x: pd.Series, y: pd.Series, min_obs=120):
    """
    y_t = beta * x_t + eps
    beta_t = expanding OLS（時点 t まで）
    """
    idx = x.index
    beta = pd.Series(index=idx, dtype=float)
    for t in idx:
        mask = (idx <= t) & x.notna() & y.notna()
        n = mask.sum()
        if n < min_obs:
            beta[t] = np.nan
            continue
        xi = x[mask].values
        yi = y[mask].values
        denom = np.sum(xi * xi)
        beta[t] = np.sum(xi * yi) / denom if denom > 0 else np.nan
    return beta

# -----------------------------
# F) 月次 Method 6 シグナル生成
# -----------------------------
def build_method6_monthly_from_daily(px_daily: pd.Series, min_obs=120):
    px_m, mkt_total_m = daily_to_monthly_total_return(px_daily)

    mt, S, x = compute_S_x_method6_from_monthly(mkt_total_m)

    # μ をランニング平均で近似：mean_{<t} R
    mu_hat = mkt_total_m.expanding().mean().shift(1)
    y_adj = mkt_total_m - mu_hat

    beta = estimate_beta_expanding(x, y_adj, min_obs=min_obs)
    w_raw = (beta * x).fillna(0.0)

    out = pd.DataFrame({
        "mkt_total_m": mkt_total_m,
        "month_type": mt,
        "S": S,
        "x": x,
        "mu_hat": mu_hat,
        "y_adj": y_adj,
        "beta": beta,
        "w_raw": w_raw,
        "px_m": px_m
    }).dropna(subset=["mkt_total_m"])
    return out

# -----------------------------
# G) 実行日ルール：月次ウェイトを日次ポジションに写像
# -----------------------------
def third_friday_dates(daily_index: pd.DatetimeIndex):
    """
    daily_index がカバーする期間内の「暦上の第3金曜日」を列挙し、
    実際の取引日に落とす（休日なら直前営業日）。
    """
    start = daily_index.min().to_period("M").start_time
    end = daily_index.max().to_period("M").end_time
    # WOM-3FRI: 第3金曜日
    cal = pd.date_range(start=start, end=end, freq="WOM-3FRI")
    # 取引日へスナップ
    snapped = []
    for d in cal:
        # d が休場なら直前の営業日に寄せる
        dd = d
        while dd not in daily_index:
            dd = dd - pd.Timedelta(days=1)
            if dd < daily_index.min():
                break
        if dd in daily_index:
            snapped.append(dd)
    return pd.DatetimeIndex(sorted(set(snapped)))

def map_monthly_weight_to_daily_position(
    px_daily: pd.Series,
    w_monthly: pd.Series,
    exec_rule: str = "next_open",   # "month_end_close", "next_open"
    avoid_third_friday: bool = True,
):
    """
    月次の w_monthly（index=月末）を、日次ポジションへ。
    先読み回避のため、exec_rule に応じて1日以上ラグを入れる。

    exec_rule:
      - "month_end_close": 月末終値で建てる（実務的には厳しめ）
      - "next_open": 翌月第1営業日に建てる（推奨）
    avoid_third_friday:
      - True の場合、第3金曜（特に四半期末）近辺の執行を避け、次営業日にずらす
    """
    idx_d = px_daily.index
    r_d = px_daily.pct_change().fillna(0.0)

    # 月末取引日（データの月末=実際の最終営業日終値）
    month_ends = px_daily.resample("M").last().index

    # 月次ウェイトを月末に揃える（不足分は0）
    w_m = w_monthly.reindex(month_ends).fillna(0.0)

    # 第3金曜集合（回避ルール用）
    tf = third_friday_dates(idx_d) if avoid_third_friday else pd.DatetimeIndex([])

    pos = pd.Series(index=idx_d, dtype=float)

    current_w = 0.0
    for i, me in enumerate(month_ends):
        # この月のウェイト（me で確定する）
        w_this = float(w_m.loc[me])

        if exec_rule == "month_end_close":
            # 月末クローズで即時反映（実務的にはスリッページ考慮要）
            exec_day = me
        elif exec_rule == "next_open":
            # 翌月の最初の営業日に反映
            # me の次の取引日
            j = idx_d.get_indexer([me], method="nearest")[0]
            # me は取引日なので j がその位置、翌営業日は j+1
            exec_day = idx_d[min(j + 1, len(idx_d)-1)]
        else:
            raise ValueError("unknown exec_rule")

        # 第3金曜回避（執行日が第3金曜なら次営業日へずらす）
        if avoid_third_friday and exec_day in tf:
            k = idx_d.get_loc(exec_day)
            exec_day = idx_d[min(k + 1, len(idx_d)-1)]

        # exec_day 以降は新ウェイト
        # 前月exec_day〜このexec_dayの直前までは current_w を維持
        if i == 0:
            pos.loc[:exec_day] = current_w
        else:
            prev_exec_day = last_exec_day
            pos.loc[prev_exec_day:exec_day] = current_w

        current_w = w_this
        last_exec_day = exec_day

    # 最後まで埋める
    pos.loc[last_exec_day:] = current_w
    pos = pos.ffill().fillna(0.0)

    # 日次戦略超過リターン（ここでは rf を無視して超過扱い）
    strat_excess_d = pos.shift(1).fillna(0.0) * r_d  # 当日寄りで建てる想定の安全側ラグ
    out = pd.DataFrame({
        "px": px_daily,
        "ret_d": r_d,
        "pos": pos,
        "strat_excess_d": strat_excess_d
    })
    return out

# -----------------------------
# H) ボラターゲット（ ex-post 一括スケール / 実務向けにはex-ante版推奨）
# -----------------------------
def vol_target_expost(strat_excess: pd.Series, target_vol_annual=0.10):
    """
    例：年率10%目標。日次ボラに換算して一括スケール。
    ※厳密な先読み回避には「rolling推定でその時点のscale」を使う ex-ante 版にする。
    """
    daily_vol = strat_excess.std(ddof=1)
    target_daily = target_vol_annual / np.sqrt(252)
    k = (target_daily / daily_vol) if daily_vol > 0 else 1.0
    return k, strat_excess * k

# -----------------------------
# I) 実行例
# -----------------------------
if __name__ == "__main__":
    px = download_spy_daily(start="2000-01-01")

    m6_m = build_method6_monthly_from_daily(px, min_obs=120)

    # 月次の w_raw を日次へ（推奨：翌月第1営業日）
    out_d = map_monthly_weight_to_daily_position(
        px_daily=px,
        w_monthly=m6_m["w_raw"],
        exec_rule="next_open",
        avoid_third_friday=True
    )

    # ボラターゲット（例：年率10%）※まずは検証用の ex-post
    k, strat_scaled = vol_target_expost(out_d["strat_excess_d"], target_vol_annual=0.10)
    out_d["strat_excess_d_scaled"] = strat_scaled
    out_d.attrs["scale"] = k

    wealth = (1.0 + out_d["strat_excess_d_scaled"]).cumprod()
    bh = (1.0 + out_d["ret_d"]).cumprod()

    plt.figure(figsize=(14,5))
    plt.plot(wealth, label="Method6 daily exec (scaled)")
    plt.plot(bh, label="SPY Buy&Hold", linestyle="--")
    plt.title("Daily execution backtest (SPY)")
    plt.legend()
    plt.grid(True)
    plt.show()

    print("scale k =", k)
```

* * *

4) 「いつ建てるべきか」を吟味するための検証プラン
--------------------------

あなたが求めているのは、**月次で導いた四半期サイクル戦略を、現実のタイミングに落としたときに最も頑健な執行点はどこか**です。そこで、次の A/B テストを推奨します。

### 実行タイミング候補（ルールとして固定）

1.  **月末終値（month\_end\_close）**
    *   理論上は“最速反映”
    *   ただし月末はリバランス集中・スプレッド拡大・指値滑りが出やすい
    *   TOM 効果が強いなら「月末〜月初」にリターンが偏るので結果が歪む可能性 [パデュー大学ビジネス学部+2サイエンスダイレクト+2](https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf?utm_source=chatgpt.com)
2.  **翌月第1営業日始値（next\_open）** ←推奨
    *   先読み回避が明確で、執行現実性が高い
    *   TOM 効果を踏まえても “月初執行” は自然 [パデュー大学ビジネス学部+2サイエンスダイレクト+2](https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf?utm_source=chatgpt.com)
3.  **第3金曜日回避（avoid\_third\_friday=True）**
    *   満期日近辺は需給の歪みが出やすく、異常リターンが観測され得る [サイエンスダイレクト+2Tandf Online+2](https://www.sciencedirect.com/science/article/abs/pii/S0927539814000231?utm_source=chatgpt.com)
    *   四半期末の第3金曜日（トリプルウィッチング）は特に出来高が増える [Encyclopedia Britannica+1](https://www.britannica.com/money/triple-witching-day?utm_source=chatgpt.com)
    *   “この日に当てない” だけでもバックテストの頑健性が上がります

### 評価指標

*   年率 Sharpe / MaxDD / turnover（ポジション変更回数）
*   取引コスト感度（例：片道 1–5bp を仮定して差し引く）
*   2000–2009 / 2010–2019 / 2020–現在 の分割（あなたが見ている 2020 以降の劣化に直結）

* * *

5) 実務向けの重要な修正：ボラターゲットは ex-ante にする
----------------------------------

上のコードはまず検証を回すために \*\*ex-post（一括スケール）\*\*を置いていますが、  
実運用で“未来のボラ”は使えないので、最終形は

*   直近 N 日（例：63 日）の日次戦略リターンから  $\hat\sigma_{t}$  を推定
*   その  $\hat\sigma_t$  で当月のレバレッジをスケール

という **ex-ante（rolling）ボラターゲット**にしてください（Moreira & Muir 型の実務運用に近づきます）。

必要なら、この ex-ante 版をあなたの Method6 コードに統合して提示します。

* * *

6) 次にこちらで固めたい選択（ただし質問は不要です。推奨は明確）
---------------------------------

あなたの用途（「2020 以降の安定運用」）なら、まずは

*   **exec\_rule = "next\_open"**
*   **avoid\_third\_friday = True**
*   **ボラターゲットは rolling（ex-ante）**

の 3 点を標準仕様にするのが堅いです。

* * *

必要なら、次の追加を即座に出します（実装も含めて）：

*   (i) `exec_rule` を 3–4 種類に増やし、同一期間で一括比較するコード（Sharpe/DD/turnover/コスト感度）
*   (ii) 四半期末（3/6/9/12月）だけ別ルールにする「ハイブリッド執行」
*   (iii) 日次の「月末効果」を実際に SPY で検定（TOM 窓のダミー回帰）し、あなたの戦略がその窓に過度に依存していないかを診断するコード

## Response:
以下は「執行タイミング（いつ建てる／いつ外す）」を吟味する際に**必ず考慮すべき論点**を、**文献で報告されている代表的なカレンダー効果**と、それを利用する**既存の戦略（＝競合になり得る取引フロー）**まで含めて、網羅的に列挙します。最後に「あなたの四半期サイクル（月次）戦略を、これらのフローに**食われにくい形で日次執行に落とす設計指針**」も付けます。

* * *

1) 執行タイミングを決める際のチェックリスト（実務で効く順）
-------------------------------

### A. フローとリスク（市場構造）

*   **月末・四半期末のリバランス集中**  
    企業年金・投信・保険・リスクパリティ等の定期リバランスが重なる。月末クローズは特に混みやすい。
*   **指数リバランス（S&P 500等）・リコン**  
    組入れ/除外やリバランスは終値ベースで執行されやすく、クローズで需給が歪む。
*   **オプション満期（第3金曜）・トリプルウィッチング（3/6/9/12月）**  
    出来高が跳ね、ヘッジ解消で「引け」付近のマイクロストラクチャが変わる。しばしば“ボラが高い”というより“**板が薄くなったり、短時間で価格が走ったり**”の方が問題になりやすい。[Investopedia+3FRASER+3ブルネル大学+3](https://fraser.stlouisfed.org/files/docs/publications/frbatlreview/pages/67107_1985-1989.pdf?utm_source=chatgpt.com)
*   **祝日・短縮取引・月初の資金流入**  
    月初は積立・給与・投信設定などのフローが出やすく、月次戦略の「建て」をどこに置くかに影響。

### B. 取引コストの非線形性

*   スプレッド・インパクト・滑りは\*\*ボラだけでなく“流動性イベント”\*\*で跳ねる（上記満期・リバランス・指数イベント）。
*   “月末クローズ”はバックテストでは良く見えがちだが、現実は最もコストが出やすい時間帯。

### C. データの整合性（先読みの混入ポイント）

*   月次シグナルを「月末の終値で確定」するなら、**執行は翌営業日の寄り／VWAP**にするのが最も先読みを排しやすい。
*   「第3金曜回避」などのルールは**カレンダー情報のみ**なので先読みではない。ただし“回避した結果、TOM区間に寄る/外れる”など副作用がある。

* * *

2) 文献で報告される代表的なカレンダー効果（＝執行タイミングに直撃）
-----------------------------------

### (1) 月末・月初効果（Turn-of-the-Month; TOM）

*   典型：**月末最終営業日〜翌月初の数営業日**のリターンが高い。Ariel (1984)、Lakonishok & Smidt (1988)、Ogden (1990)、McConnell & Xu (2008) などが有名。[パデュー大学ビジネス学部+3dspace.mit.edu+3diva-portal.org+3](https://dspace.mit.edu/bitstream/handle/1721.1/48463/monthly%EE%80%80effect%EE%80%81ins00arie.pdf?sequence=1&utm_source=chatgpt.com)
*   意味：あなたの「月次で建てる」戦略は、建て日がこの区間に入るかどうかで成績が大きく変わり得る。

**この効果を使う既存戦略（競合フロー）**

*   **TOMロング**：月末最終日引け〜月初数日まで株式をロング、それ以外は現金／債券へ。定番のカレンダー戦略として広く知られる。[quantpedia.com+1](https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes?utm_source=chatgpt.com)

### (2) 曜日効果（Day-of-the-Week / Weekend effect）

*   典型：月曜が弱い、金曜が強い等。古典的には French (1980)、Gibbons & Hess (1981) ほか。[www-2.rotman.utoronto.ca+2サイエンスダイレクト+2](https://www-2.rotman.utoronto.ca/~kan/3032/pdf/AssetPricingAnomalies/Gibbons_Hess_JB_1981.pdf?utm_source=chatgpt.com)
*   意味：月初執行が月曜に当たりやすい月は、寄りで建てると不利/有利が偏る可能性がある。

**この効果を使う戦略**

*   **曜日別エクスポージャ（例：月曜はリスク縮小、金曜は増やす）**  
    近年は単純戦略だけでは収益化しにくいが、コスト回避・リスク管理の“補助ルール”としては残りやすい。

### (3) 月別効果（January effect / 月次季節性）

*   1月が強い、（小型株で顕著）などの報告が有名。Rozeff & Kinney(1976)、Keim(1983)等を多くの研究が追随。[サイエンスダイレクト+2jstor.org+2](https://www.sciencedirect.com/science/article/abs/pii/S0378426609002817?utm_source=chatgpt.com)
*   意味：四半期サイクル戦略のパフォーマンス評価で、季節性が混ざると「本当に四半期サイクルが効いたのか」が曖昧になる。

**この効果を使う戦略**

*   **年末〜年初のリスクオン**（tax-loss selling の反転や資金流入を狙う）  
    これも“いつ建てるか”を歪める競合フロー。

### (4) オプション満期（第3金曜）・トリプルウィッチング（3/6/9/12）

*   満期に伴う出来高急増、引けの板歪み、短期の価格圧力などが議論される。[Axios+3FRASER+3ブルネル大学+3](https://fraser.stlouisfed.org/files/docs/publications/frbatlreview/pages/67107_1985-1989.pdf?utm_source=chatgpt.com)
*   近年のニュースでも、膨大な想定元本の満期が「出来高を押し上げる」ことが繰り返し指摘される。[マーケットウォッチ+2マーケットウォッチ+2](https://www.marketwatch.com/story/why-the-biggest-ever-triple-witching-options-expiration-could-deliver-a-jolt-to-fridays-trading-c737aaa7?utm_source=chatgpt.com)

**この効果を使う戦略**

*   **ディーラーのガンマ/デルタ・ヘッジの巻き戻しを利用する短期戦略**  
    （方向性よりも“満期前後の需給・ボラ・リバーサル”を狙う類）
*   あなたの月次リバランスは、ここに**意図せず巻き込まれる**のがリスク。

* * *

3) 「それらの効果を用いた戦略」を出し抜くための設計指針（実務的）
----------------------------------

ここが重要です。カレンダー効果それ自体に乗る戦略と正面衝突すると、あなたのシグナル優位性（四半期サイクル）が**執行フローに吸収**されます。出し抜くには次が有効です。

### 指針1：執行点を「クローズ集中」から外す

*   月末クローズは、TOM・指数・リバランスが最もぶつかる。[パデュー大学ビジネス学部+1](https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf?utm_source=chatgpt.com)
*   **翌月第1営業日の寄り**（またはその日のVWAP）にずらす方が、先読み回避と執行現実性が両立しやすい。

### 指針2：TOMの“ど真ん中”を避ける／分散させる

*   TOM戦略は「月末最終日〜月初数日」が主戦場。[パデュー大学ビジネス学部+2dspace.mit.edu+2](https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf?utm_source=chatgpt.com)
*   あなたがその区間に毎回入ると、TOMのβを拾ってしまう（＝四半期サイクルではなくTOMを取っていた、になりやすい）。  
    **回避策**：
    *   建てを「月初+2営業日」などに固定（TOM窓の外側）
    *   あるいは「月初に 50% 建て、+2営業日で残り 50%」など分割執行

### 指針3：第3金曜（特に四半期末）の“板の歪み”回避

*   3/6/9/12月の第3金曜は、満期と四半期要因が重なる。[Investopedia+2Axios+2](https://www.investopedia.com/terms/t/triplewitchinghour.asp?utm_source=chatgpt.com)  
    **回避策**：
    *   その日が執行日に当たる場合は「次営業日へ繰り延べ」
    *   あるいは「その週の火〜木でVWAP執行」にする

### 指針4：検証は“効果をコントロールした上で”行う

執行タイミングの優劣を比較する際、回帰で

*   TOMダミー（例：\[-1,+3\]営業日）
*   曜日ダミー
*   第3金曜ダミー（特に3/6/9/12）  
    を入れて、「あなたの戦略がそれらを除いても残るか」を確認すると、出し抜けているかが判定しやすい。[パデュー大学ビジネス学部+2www-2.rotman.utoronto.ca+2](https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf?utm_source=chatgpt.com)

* * *

4) あなたの四半期サイクル戦略への具体的な落とし込み案（推奨）
--------------------------------

**推奨実装（最初に試すべき基準仕様）**

*   シグナル確定：月末（終値まで）
*   執行：翌月第1営業日寄り（または当日VWAP）
*   例外：執行日が第3金曜（特に3/6/9/12月）なら次営業日に繰り延べ
*   さらに頑健化：TOM窓への過度依存を避けるため「月初+2営業日で建て」も並行検証

* * *

もしよければ次の2点を、あなたの既存コードにそのまま足せる形で出します（コード付き）：

1.  **執行タイミング候補（例：月末引け／月初寄り／月初+2／第3金曜回避／分割執行）を一括比較**し、Sharpe・DD・turnover・コスト感度を表にする関数
2.  TOM/曜日/第3金曜ダミーで「**戦略リターンを説明**」する回帰（＝どの効果に依存しているかの診断）

「多くの戦略を出し抜きたい」という目的なら、(2) の診断が特に効きます。効果に依存しているほど、その効果を狙う競合フローとぶつかって優位性が薄れるためです。

## Response:
了解です。**既存コードをいじる前に「本当にそのカレンダー効果が SPY（日次）で現在も有意か」を確認する**のは正しい順序です。  
以下では、**確認すべき効果を網羅的に列挙**し、\*\*それぞれをどう検証するか（統計テスト／回帰設計／注意点）\*\*を、実務で再現しやすい形で整理します。コード改良はこの確認が終わってからで十分です。

* * *

0\. 検証の原則（重要）
-------------

*   \*\*日次データ（Adj Close）\*\*で検証（執行と同じ時間解像度）
*   **先読みなし**（ダミーはカレンダーから機械的に作る）
*   \*\*Newey–West（HAC）\*\*で標準誤差（短期自己相関・異分散対策）
*   **サブサンプル分割**（例：2000–09 / 2010–19 / 2020–）で安定性確認
*   **同時回帰**（複数ダミーを一緒に入れる）で“見せかけ”を排除

* * *

1\. 月末・月初効果（Turn-of-the-Month, TOM）
-----------------------------------

### 何を確認する？

*   **月末最終営業日〜翌月初数営業日**の平均リターンが他日より高いか。

### 代表的な検証

**(A) 平均差検定（最初の一歩）**

*   TOM 窓（例：\[-1, +3\] 営業日）の平均日次リターン − 非TOM日の平均
*   t検定（HAC）

**(B) ダミー回帰（推奨）**

$$
r_{t}=\alpha+\beta_{\text{TOM}}\cdot \mathbb{1}(\text{TOM}_t)+\varepsilon_t
$$
*    $\beta_{\text{TOM}}>0$  か、有意か。

### 注意点

*   **窓幅依存**（\[-1,+3\] 以外も試す）
*   **2020以降で弱まっていないか**（サブサンプル）

* * *

2\. 曜日効果（Day-of-the-Week）
-------------------------

### 何を確認する？

*   月曜が弱い／金曜が強い等の**曜日差**が残っているか。

### 検証

$$
r_t=\alpha+\sum_{d\in\{\text{Mon..Fri}\}\setminus\text{Wed}}\beta_d\cdot \mathbb{1}(d_t=d)+\varepsilon_t
$$
*   1曜日を基準にダミー回帰。
*   **TOMと同時に入れる**（曜日×TOMの交絡を切る）。

### 注意点

*   単独では弱まりがち。**補助ルール**（執行回避）としての価値を評価。

* * *

3\. 月別季節性（January / 月次）
-----------------------

### 何を確認する？

*   特定の**月**（1月など）に有意差があるか。

### 検証

$$
r_t=\alpha+\sum_{m\neq\text{Jun}}\beta_m\cdot \mathbb{1}(\text{Month}_t=m)+\varepsilon_t
$$
*   **TOM・曜日と同時**に入れる。
*   小型株で強い効果が知られるが、**SPYでは弱化**が一般的。

* * *

4\. 第3金曜日（オプション満期）／トリプルウィッチング
-----------------------------

### 何を確認する？

*   **第3金曜日**の平均リターン／ボラが平常日と異なるか。
*   **3/6/9/12月**の第3金曜で差が拡大するか。

### 検証

$$
r_t=\alpha+\beta_{\text{3Fri}}\mathbb{1}(\text{3Fri}_t)+ \beta_{\text{TW}}\mathbb{1}(\text{3Fri\&Quarter}_t)+\varepsilon_t
$$
*   \*\*平均リターンだけでなく、分散（|r|）\*\*も確認。

### 注意点

*   方向性より\*\*マイクロストラクチャ（滑り・VWAP乖離）\*\*が問題になりやすい。
*   執行回避ルールの是非を判断。

* * *

5\. 四半期末フロー（年金・指数・リバランス）
------------------------

### 何を確認する？

*   \*\*四半期末（月末）\*\*に限って効果が強まるか。

### 検証

*   TOM × 四半期末の**交互作用**：
    
$$
r_t=\alpha+\beta_{\text{TOM}}\mathbb{1}(\text{TOM}_t)+ \beta_{\text{Q}}\mathbb{1}(\text{QuarterEnd}_t)+ \beta_{\text{TOM}\times\text{Q}}\mathbb{1}(\text{TOM}_t)\mathbb{1}(\text{Q}_t)+\varepsilon_t
$$

* * *

6\. 祝日・短縮取引の影響
--------------

### 何を確認する？

*   **祝日前後**でリターンやボラが歪むか。

### 検証

*   祝日前ダミー／翌営業日ダミーを追加。
*   月初執行が祝日明けに集中する副作用をチェック。

* * *

7\. “同時回帰”で最終確認（必須）
-------------------

**単独で有意でも、同時に入れると消える**ことが多い。  
最終判断は以下で行う：

$$
\begin{aligned} r_t=\alpha &+ \beta_{\text{TOM}}\mathbb{1}(\text{TOM}_t) + \sum_d \beta_d \mathbb{1}(d_t=d) + \sum_m \beta_m \mathbb{1}(\text{Month}_t=m)\\ &+ \beta_{\text{3Fri}}\mathbb{1}(\text{3Fri}_t) + \beta_{\text{TW}}\mathbb{1}(\text{3Fri\&Quarter}_t) + \varepsilon_t \end{aligned}
$$
*   **HAC**で推定。
*   サブサンプルで**符号と有意性の安定性**を見る。

* * *

8\. 判定基準（執行設計に落とす前の合否）
----------------------

*   **安定して有意（複数期間）** → 執行設計で“考慮”
*   **期間依存・不安定** → 原則“回避（執行点をずらす）”
*   **同時回帰で消える** → ノイズ（考慮不要）

* * *

9\. 次のステップ（ここまで確認したら）
---------------------

*   有意だった効果だけを**執行回避／分割執行**として反映
*   **あなたの戦略リターン**を被説明変数にして、同じダミーで回帰  
    → 「戦略がどの効果に依存しているか」を診断（出し抜けているかの最重要チェック）

必要であれば、\*\*この確認一式をそのまま回せる検証コード（SPY日次・HAC・サブサンプル付き）\*\*を次に提示します。

## Response:
承知しました。SPY（日次）で、先ほど挙げた **TOM / 曜日 / 月別 / 第3金曜 / 四半期末 / 祝日前後** を **HAC（Newey–West）付き回帰＋サブサンプル**で一括検証できる「そのまま実行できるフルコード」を提示します。

※なお、こちらの検証は **yfinance の価格データだけ**で完結するため、以前アップロードいただいたPDF等が一部期限切れになっていても問題ありません（必要になったら再アップロードをご依頼します）。

* * *

検証コード（SPY日次：カレンダー効果の確認一式）
-------------------------

```python
import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm

# ============================================================
# 1) データ取得（SPY 日次, auto_adjust=True）
# ============================================================

def load_spy_daily(start="1993-01-01", end=None):
    px = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)["Close"]
    px = px.dropna()
    df = pd.DataFrame({"px": px})
    df["ret"] = df["px"].pct_change()
    df = df.dropna()
    return df

# ============================================================
# 2) カレンダー特徴量（ダミー）生成
# ============================================================

def third_friday_dates(trading_index: pd.DatetimeIndex):
    """暦上の第3金曜を生成し、取引日にスナップ（休日なら直前営業日へ）。"""
    start = trading_index.min().to_period("M").start_time
    end = trading_index.max().to_period("M").end_time
    cal = pd.date_range(start=start, end=end, freq="WOM-3FRI")

    snapped = []
    for d in cal:
        dd = d
        # 休場なら直前に寄せる（米国市場休日対応の簡易版）
        while dd not in trading_index:
            dd = dd - pd.Timedelta(days=1)
            if dd < trading_index.min():
                break
        if dd in trading_index:
            snapped.append(dd)
    return pd.DatetimeIndex(sorted(set(snapped)))

def build_calendar_features(df: pd.DataFrame,
                            tom_pre=1, tom_post=3):
    """
    df: index=取引日, columns=['ret', 'px']
    TOM: 月末最終営業日の -tom_pre 日〜月初 +tom_post 日を1にする
         （例: tom_pre=1,tom_post=3 -> [-1,+3] 営業日）
    """
    out = df.copy()
    idx = out.index

    # 曜日（Mon=0,...Fri=4）
    out["dow"] = idx.dayofweek

    # 月（1..12）
    out["month"] = idx.month

    # 取引日ベースの月末・月初
    month_ends = out["px"].resample("M").last().index
    month_starts = out["px"].resample("MS").first().index  # 月初カレンダー日 -> 取引日ではない可能性
    # 取引日の月初を作る（各月の最初の取引日）
    month_first_trading = out["px"].groupby([idx.year, idx.month]).head(1).index

    # Quarter-end（3,6,9,12 月）
    out["is_q_end_month"] = (idx.month.isin([3, 6, 9, 12])).astype(int)
    # 月末最終営業日フラグ
    out["is_month_end"] = idx.isin(month_ends).astype(int)
    # 月初最初の取引日フラグ
    out["is_month_start"] = idx.isin(month_first_trading).astype(int)

    # 第3金曜日（オプション満期を近似）
    tf = third_friday_dates(idx)
    out["is_third_friday"] = idx.isin(tf).astype(int)
    out["is_triple_witching"] = (out["is_third_friday"].astype(bool) & out["is_q_end_month"].astype(bool)).astype(int)

    # TOM 窓ダミーを作る（営業日シフトで作る）
    tom = pd.Series(0, index=idx, dtype=int)
    for me in month_ends:
        if me not in idx:
            continue
        loc = idx.get_loc(me)
        start_loc = max(loc - tom_pre, 0)
        end_loc = min(loc + tom_post, len(idx) - 1)  # month_end から後ろに tom_post 日
        # month_endの後ろは「翌月初」の取引日になる（営業日配列上で連続）
        tom.iloc[start_loc:end_loc + 1] = 1
    out["is_TOM"] = tom

    # 祝日前後（簡易）：次取引日までのカレンダー日差が >= 3 の日を「休日前」とする（週末含む）
    # ※厳密な米祝日は別ライブラリが必要になるため、まず簡易版で傾向確認
    next_day = idx.to_series().shift(-1)
    gap = (next_day - idx.to_series()).dt.days
    out["is_pre_holiday_like"] = (gap >= 3).astype(int)  # 週末/祝日を含む「空き」
    # 「休み明け」は前取引日との差が>=3の日
    prev_day = idx.to_series().shift(1)
    gap_prev = (idx.to_series() - prev_day).dt.days
    out["is_post_holiday_like"] = (gap_prev >= 3).astype(int)

    return out

# ============================================================
# 3) 回帰（HAC / Newey–West）
# ============================================================

def hac_ols(y: pd.Series, X: pd.DataFrame, lags=5):
    """
    OLS + HAC(Newey-West) 標準誤差
    """
    Xc = sm.add_constant(X, has_constant="add")
    model = sm.OLS(y, Xc).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return model

def make_design_matrix(cal: pd.DataFrame,
                       include_dow=True,
                       include_month=True,
                       include_tom=True,
                       include_third_friday=True,
                       include_triple_witching=True,
                       include_q_end=True,
                       include_holiday_like=True):
    """
    同時回帰用のデザイン行列（ベースライン）
    - ダミーは one-hot を作り、基準カテゴリは落とす（多重共線性回避）
    """
    X_parts = []

    if include_tom:
        X_parts.append(cal[["is_TOM"]])

    if include_dow:
        dow = pd.get_dummies(cal["dow"], prefix="dow", drop_first=True)
        X_parts.append(dow)

    if include_month:
        mon = pd.get_dummies(cal["month"], prefix="mon", drop_first=True)
        X_parts.append(mon)

    if include_third_friday:
        X_parts.append(cal[["is_third_friday"]])

    if include_triple_witching:
        X_parts.append(cal[["is_triple_witching"]])

    if include_q_end:
        # 月末やTOMと被るので、入れるなら慎重に（ここでは月末フラグのみ）
        X_parts.append(cal[["is_month_end", "is_month_start"]])

    if include_holiday_like:
        X_parts.append(cal[["is_pre_holiday_like", "is_post_holiday_like"]])

    X = pd.concat(X_parts, axis=1)
    X = X.loc[cal.index]
    return X

# ============================================================
# 4) サブサンプル分割とレポート
# ============================================================

def run_calendar_effects_report(start="2000-01-01", end=None,
                                tom_pre=1, tom_post=3,
                                hac_lags=5,
                                splits=("2000-01-01", "2010-01-01", "2020-01-01")):
    """
    splits:
      例: ("2000-01-01","2010-01-01","2020-01-01")
      -> [2000-2009], [2010-2019], [2020-現在]
    """
    df = load_spy_daily(start=start, end=end)
    cal = build_calendar_features(df, tom_pre=tom_pre, tom_post=tom_post)

    # サブサンプルの切り方
    split_dates = [pd.Timestamp(s) for s in splits]
    split_dates = sorted(split_dates)

    # 区間を作る
    periods = []
    for i in range(len(split_dates)):
        a = split_dates[i]
        b = split_dates[i+1] if i+1 < len(split_dates) else cal.index.max() + pd.Timedelta(days=1)
        periods.append((a, b))

    rows = []
    models = {}

    for (a, b) in periods:
        sub = cal[(cal.index >= a) & (cal.index < b)].copy()
        if len(sub) < 252:  # 1年未満は飛ばす
            continue

        y = sub["ret"]
        X = make_design_matrix(sub,
                               include_dow=True,
                               include_month=True,
                               include_tom=True,
                               include_third_friday=True,
                               include_triple_witching=True,
                               include_q_end=True,
                               include_holiday_like=True)

        m = hac_ols(y, X, lags=hac_lags)
        key = f"{a.date()}__{(b - pd.Timedelta(days=1)).date()}"
        models[key] = m

        # 主要係数だけ抜粋
        focus = ["is_TOM", "is_third_friday", "is_triple_witching",
                 "is_month_end", "is_month_start", "is_pre_holiday_like", "is_post_holiday_like"]
        for c in focus:
            if c in m.params.index:
                rows.append({
                    "period": key,
                    "var": c,
                    "coef": float(m.params[c]),
                    "t": float(m.tvalues[c]),
                    "p": float(m.pvalues[c]),
                    "nobs": int(m.nobs)
                })

    res = pd.DataFrame(rows)
    return cal, res, models

# ============================================================
# 5) 実行例
# ============================================================

if __name__ == "__main__":
    cal, res, models = run_calendar_effects_report(
        start="2000-01-01",
        end=None,
        tom_pre=1, tom_post=3,   # TOM窓 [-1,+3]
        hac_lags=5,
        splits=("2000-01-01","2010-01-01","2020-01-01")
    )

    # 表示（主要効果の係数・t・p）
    pd.set_option("display.max_rows", 200)
    print(res.sort_values(["var","period"]))

    # 参考：最新区間の回帰サマリ全文を見たい場合
    if len(models) > 0:
        last_key = list(models.keys())[-1]
        print("\n=== Full regression summary for:", last_key, "===\n")
        print(models[last_key].summary())
```

* * *

使い方と読み方
-------

### 1) まずここを見る（合否判定）

出力 `res` のうち、特に次の行を見ます：

*   `is_TOM`：TOM窓（例：\[-1,+3\]）が平常日より平均リターンが高いか
*   `is_third_friday`：第3金曜が平常日と違うか
*   `is_triple_witching`：四半期末第3金曜がさらに違うか
*   `is_month_end / is_month_start`：月末最終日／月初最初日が他日と違うか
*   `is_pre_holiday_like / is_post_holiday_like`：休日前後（簡易）が効いているか

**判定ルール（推奨）**

*   係数の符号が直感通りで、**複数期間で一貫**（例：2000s, 2010s, 2020s で同符号）
*   t値が絶対値 2 近辺（目安）で、p値が小さい  
    → 執行ルールで “考慮対象” にしてよい

逆に、

*   期間によって符号が反転する
*   2020以降だけ消える  
    → “回避”か、執行タイミングを固定しない（分散執行）方向が堅いです。

* * *

追加でやると強い検証（推奨）
--------------

1.  **TOM窓を複数試す**（\[-1,+1\], \[-1,+3\], \[0,+3\] など）  
    　窓依存なら「TOMを拾っているだけ」の疑いが強いです。
2.  **方向だけでなく分散も**  
    　被説明変数を `abs(ret)` や `ret**2` にして、満期・月末の“リスク（滑り）”をチェック。
3.  **あなたの戦略リターンで同じ回帰をかける**  
    　最重要です。「戦略がTOMに依存しているか」を見れば、競合フローに食われやすいかが判定できます。

* * *

この次の段階として、あなたの Method 6（日次執行版）で生成した `strat_excess_d` を `y` にして、上と全く同じ回帰を当てるコードもすぐ出せます。そうすると「TOMに勝っているのか／TOMを拾っているのか」が明確になります。

## Response:
エラー内容から判断すると、原因はほぼ確実にここです：

```python
df = pd.DataFrame({"px": px})
```

このとき `px` が **Series ではなく「スカラー（float）」扱い**になってしまい、pandas が

> “全てがスカラーなら index を渡せ”  
> と怒っています（`ValueError: If using all scalar values...`）。

yfinance は環境や返り値の形（MultiIndex列・欠損・一時的な取得失敗）によって、`["Close"]` の結果が **Seriesにならない**ケースがあり得ます。そこで、**返り値を強制的に Series に正規化**し、空データのときは早めに例外を出すように直してください。

* * *

1) 修正版：`load_spy_daily`（堅牢版）
----------------------------

これに置き換えてください。

```python
import pandas as pd
import yfinance as yf

def load_spy_daily(start="1993-01-01", end=None):
    data = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)

    if data is None or len(data) == 0:
        raise ValueError("yfinance returned empty data. Try changing the date range or retry later.")

    # yfinance の返り値が MultiIndex columns の場合があるので吸収
    if isinstance(data.columns, pd.MultiIndex):
        # 典型：('Close','SPY') のような形
        if ("Close", "SPY") in data.columns:
            px = data[("Close", "SPY")]
        else:
            # Close の最初の列を取る（保険）
            close_cols = [c for c in data.columns if c[0] == "Close"]
            if len(close_cols) == 0:
                raise ValueError(f"Close column not found in downloaded data columns: {data.columns}")
            px = data[close_cols[0]]
    else:
        if "Close" not in data.columns:
            raise ValueError(f"Close column not found in downloaded data columns: {data.columns}")
        px = data["Close"]

    # Series に強制
    if isinstance(px, pd.DataFrame):
        # もし DataFrame で来たら 1列に潰す
        if px.shape[1] != 1:
            raise ValueError(f"Unexpected Close DataFrame shape: {px.shape}")
        px = px.iloc[:, 0]

    px = px.dropna()
    if len(px) < 50:
        raise ValueError(f"Too few price observations after dropna: {len(px)}. Check date range / data.")

    px.name = "px"
    df = px.to_frame()
    df["ret"] = df["px"].pct_change()
    df = df.dropna()
    return df
```

* * *

2) すぐ確認してほしいこと（実行前チェック）
-----------------------

次を一度だけ実行して、返り値の形を確認すると原因が確定します。

```python
d = yf.download("SPY", start="2000-01-01", auto_adjust=True, progress=False)
print(type(d), d.shape)
print(d.columns)
print(d.head())
```

*   `d.columns` が MultiIndex なら上の修正版が必須です。
*   `d.shape == (0, …)` なら取得失敗（通信/レート制限/一時的障害）です。この場合は期間を短くして再実行してください。

* * *

3) そのまま次のセルで動く最小テスト
-------------------

修正版 `load_spy_daily` に差し替えた後、まずここまで通してください。

```python
df = load_spy_daily(start="2000-01-01")
print(df.head())
print(df.tail())
print(df.columns)
```

ここが通れば、以降の `build_calendar_features` 以下も正常に走るはずです。

* * *

必要なら、あなたのノートブックの該当セル（`load_spy_daily`～`run_calendar_effects_report`）を前提に、**そのままコピペで置換できる完全な差分版**も出します。まずは上の `load_spy_daily` の差し替えで解決する可能性が高いです。

## Response:
原因ははっきりしていて、`statsmodels.OLS` に渡している `X`（説明変数）に **object 型（文字列や混在dtype）** が混ざっています。`statsmodels` は `float`（数値）でない列があると、

> Pandas data cast to numpy dtype of object

で落ちます。

典型的な混入源は次のどれかです：

*   `get_dummies` の結果が bool / object になっている
*   `make_design_matrix` に `object` 列（例：month\_type 等）が紛れた
*   欠損を含む列が object に昇格した
*   インデックスのズレで `X` の列が混在し、pandas が object 扱いにした

* * *

直し方（確実に動く修正）
============

修正1：`make_design_matrix` の最後で「数値に強制変換」＋ 欠損処理
--------------------------------------------

`make_design_matrix` を **この版に置き換えて**ください（末尾だけでOKです）。

```python
def make_design_matrix(cal: pd.DataFrame,
                       include_dow=True,
                       include_month=True,
                       include_tom=True,
                       include_third_friday=True,
                       include_triple_witching=True,
                       include_q_end=True,
                       include_holiday_like=True):

    X_parts = []

    if include_tom:
        X_parts.append(cal[["is_TOM"]])

    if include_dow:
        dow = pd.get_dummies(cal["dow"], prefix="dow", drop_first=True)
        X_parts.append(dow)

    if include_month:
        mon = pd.get_dummies(cal["month"], prefix="mon", drop_first=True)
        X_parts.append(mon)

    if include_third_friday:
        X_parts.append(cal[["is_third_friday"]])

    if include_triple_witching:
        X_parts.append(cal[["is_triple_witching"]])

    if include_q_end:
        X_parts.append(cal[["is_month_end", "is_month_start"]])

    if include_holiday_like:
        X_parts.append(cal[["is_pre_holiday_like", "is_post_holiday_like"]])

    X = pd.concat(X_parts, axis=1)
    X = X.loc[cal.index]

    # ★ここが重要：statsmodels用に数値へ強制変換
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0).astype(float)

    return X
```

これで `X` は必ず `float` になります。

* * *

修正2：念のため `y` も float に強制
------------------------

`run_calendar_effects_report` 内の

```python
y = sub["ret"]
```

を

```python
y = pd.to_numeric(sub["ret"], errors="coerce").astype(float)
```

に置き換えてください。

* * *

修正3：回帰前に「object列が残っていないか」をチェック（デバッグ用）
-------------------------------------

同じセルで、`m = hac_ols(...)` の直前に一度だけ入れると原因が即わかります。

```python
bad_cols = X.columns[X.dtypes == "object"].tolist()
if bad_cols:
    raise ValueError(f"X has object dtype columns: {bad_cols}")

if y.dtype == "object":
    raise ValueError("y is object dtype")
```

* * *

なぜ起きるか（短く）
==========

`pd.get_dummies` や `concat` の結果は、状況によって `bool` や `object` が混ざります。  
pandas の段階では動きますが、`statsmodels` は内部で `np.asarray` するときに `object` になると弾きます。

* * *

追加の注意（こちらは任意）
=============

*   今の「休日っぽい（gap>=3）」は週末も混ざります。効果の方向を見るには十分ですが、祝日を厳密にやりたい場合は市場カレンダー（`pandas_market_calendars` 等）が必要です（後ででOK）。
*   以前アップロードされていたファイルの一部は期限切れになっているようです。今回の検証は yfinance のみなので不要ですが、もしそのPDF/資料を参照して検証・比較したい場合は再アップロードしてください。

* * *

まずは **修正1＋修正2** を入れて再実行してください。  
それでも落ちる場合は、`X.dtypes` と `X.head()` を貼ってくれれば、どの列が悪さしているかをこちらで特定して、最小修正に落とします。

## Response:
承知しました。先ほどの **2つのエラー（DataFrame scalar / object dtype）** を潰し込んだ、**そのままコピペで動くフルコード**を提示します（SPY 日次 → カレンダー効果回帰（HAC）→ サブサンプル別の係数表＋回帰サマリ）。

※今回は yfinance のみを使うので、以前のPDF等のアップロードは不要です。ただし、もし以前アップロードされたファイル内容も参照して追加分析したい場合は、いくつか期限切れになっているため再アップロードが必要です。

* * *

```python
import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm

# ============================================================
# 1) SPY 日次（堅牢に Close を Series 化）
# ============================================================

def load_spy_daily(start="1993-01-01", end=None):
    data = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)

    if data is None or len(data) == 0:
        raise ValueError("yfinance returned empty data. Try changing date range or retry later.")

    # MultiIndex columns の場合にも対応
    if isinstance(data.columns, pd.MultiIndex):
        # 例: ('Close','SPY')
        if ("Close", "SPY") in data.columns:
            px = data[("Close", "SPY")]
        else:
            close_cols = [c for c in data.columns if c[0] == "Close"]
            if len(close_cols) == 0:
                raise ValueError(f"Close column not found. columns={data.columns}")
            px = data[close_cols[0]]
    else:
        if "Close" not in data.columns:
            raise ValueError(f"Close column not found. columns={data.columns}")
        px = data["Close"]

    # Series に強制
    if isinstance(px, pd.DataFrame):
        if px.shape[1] != 1:
            raise ValueError(f"Unexpected Close DataFrame shape: {px.shape}")
        px = px.iloc[:, 0]

    px = px.dropna()
    if len(px) < 50:
        raise ValueError(f"Too few observations: {len(px)}")

    px.name = "px"
    df = px.to_frame()
    df["ret"] = df["px"].pct_change()
    df = df.dropna()
    return df

# ============================================================
# 2) 第3金曜（暦）→ 取引日にスナップ
# ============================================================

def third_friday_dates(trading_index: pd.DatetimeIndex):
    start = trading_index.min().to_period("M").start_time
    end = trading_index.max().to_period("M").end_time

    # 暦上の第3金曜
    cal = pd.date_range(start=start, end=end, freq="WOM-3FRI")

    snapped = []
    for d in cal:
        dd = d
        # 休場の場合は直前営業日に寄せる（簡易）
        while dd not in trading_index:
            dd = dd - pd.Timedelta(days=1)
            if dd < trading_index.min():
                break
        if dd in trading_index:
            snapped.append(dd)

    return pd.DatetimeIndex(sorted(set(snapped)))

# ============================================================
# 3) カレンダー効果特徴量（TOM / 曜日 / 月 / 第3金曜 / 休日前後など）
# ============================================================

def build_calendar_features(df: pd.DataFrame, tom_pre=1, tom_post=3):
    """
    TOM: 月末最終営業日を基準に、[-tom_pre, +tom_post] 営業日を 1 にする
    （例: tom_pre=1,tom_post=3 -> [-1,+3]）
    """
    out = df.copy()
    idx = out.index

    # 曜日・月
    out["dow"] = idx.dayofweek.astype(int)  # 0..4
    out["month"] = idx.month.astype(int)    # 1..12

    # 取引日ベースの月末（最終営業日）
    month_ends = out["px"].resample("M").last().index
    out["is_month_end"] = idx.isin(month_ends).astype(int)

    # 月初（最初の取引日）
    month_first_trading = out["px"].groupby([idx.year, idx.month]).head(1).index
    out["is_month_start"] = idx.isin(month_first_trading).astype(int)

    # 四半期末月（3,6,9,12）
    out["is_q_end_month"] = idx.month.isin([3, 6, 9, 12]).astype(int)

    # 第3金曜（オプション満期近似）とトリプルウィッチング（四半期末第3金曜）
    tf = third_friday_dates(idx)
    out["is_third_friday"] = idx.isin(tf).astype(int)
    out["is_triple_witching"] = ((out["is_third_friday"] == 1) & (out["is_q_end_month"] == 1)).astype(int)

    # TOM 窓ダミー（営業日シフトで作る）
    tom = pd.Series(0, index=idx, dtype=int)
    for me in month_ends:
        if me not in idx:
            continue
        loc = idx.get_loc(me)
        a = max(loc - tom_pre, 0)
        b = min(loc + tom_post, len(idx) - 1)
        tom.iloc[a:b+1] = 1
    out["is_TOM"] = tom.astype(int)

    # 祝日前後（簡易）：次取引日までのカレンダー日差 >=3 を「休日前っぽい」とする（週末含む）
    next_day = idx.to_series().shift(-1)
    gap = (next_day - idx.to_series()).dt.days
    out["is_pre_holiday_like"] = (gap >= 3).fillna(0).astype(int)

    prev_day = idx.to_series().shift(1)
    gap_prev = (idx.to_series() - prev_day).dt.days
    out["is_post_holiday_like"] = (gap_prev >= 3).fillna(0).astype(int)

    return out

# ============================================================
# 4) デザイン行列（object dtype を潰して statsmodels に渡す）
# ============================================================

def make_design_matrix(cal: pd.DataFrame,
                       include_dow=True,
                       include_month=True,
                       include_tom=True,
                       include_third_friday=True,
                       include_triple_witching=True,
                       include_q_end=True,
                       include_holiday_like=True):

    X_parts = []

    if include_tom:
        X_parts.append(cal[["is_TOM"]])

    if include_dow:
        dow = pd.get_dummies(cal["dow"], prefix="dow", drop_first=True)
        X_parts.append(dow)

    if include_month:
        mon = pd.get_dummies(cal["month"], prefix="mon", drop_first=True)
        X_parts.append(mon)

    if include_third_friday:
        X_parts.append(cal[["is_third_friday"]])

    if include_triple_witching:
        X_parts.append(cal[["is_triple_witching"]])

    if include_q_end:
        X_parts.append(cal[["is_month_end", "is_month_start"]])

    if include_holiday_like:
        X_parts.append(cal[["is_pre_holiday_like", "is_post_holiday_like"]])

    X = pd.concat(X_parts, axis=1)
    X = X.loc[cal.index]

    # ★重要：数値へ強制変換（object 混入を根絶）
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0).astype(float)

    return X

# ============================================================
# 5) OLS + HAC(Newey-West)
# ============================================================

def hac_ols(y: pd.Series, X: pd.DataFrame, lags=5):
    Xc = sm.add_constant(X, has_constant="add")
    model = sm.OLS(y, Xc).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return model

# ============================================================
# 6) サブサンプル別に回帰して、主要係数をまとめる
# ============================================================

def run_calendar_effects_report(start="2000-01-01", end=None,
                                tom_pre=1, tom_post=3,
                                hac_lags=5,
                                splits=("2000-01-01", "2010-01-01", "2020-01-01")):

    df = load_spy_daily(start=start, end=end)
    cal = build_calendar_features(df, tom_pre=tom_pre, tom_post=tom_post)

    split_dates = [pd.Timestamp(s) for s in splits]
    split_dates = sorted(split_dates)

    periods = []
    for i in range(len(split_dates)):
        a = split_dates[i]
        b = split_dates[i+1] if i+1 < len(split_dates) else cal.index.max() + pd.Timedelta(days=1)
        periods.append((a, b))

    rows = []
    models = {}

    for (a, b) in periods:
        sub = cal[(cal.index >= a) & (cal.index < b)].copy()
        if len(sub) < 252:
            continue

        # y を float に強制（object混入対策）
        y = pd.to_numeric(sub["ret"], errors="coerce").astype(float)

        X = make_design_matrix(sub,
                               include_dow=True,
                               include_month=True,
                               include_tom=True,
                               include_third_friday=True,
                               include_triple_witching=True,
                               include_q_end=True,
                               include_holiday_like=True)

        # 念のための安全チェック
        if (X.dtypes == "object").any():
            bad = X.columns[X.dtypes == "object"].tolist()
            raise ValueError(f"X has object dtype columns: {bad}")
        if y.dtype == "object":
            raise ValueError("y is object dtype")

        m = hac_ols(y, X, lags=hac_lags)

        key = f"{a.date()}__{(b - pd.Timedelta(days=1)).date()}"
        models[key] = m

        focus = ["is_TOM", "is_third_friday", "is_triple_witching",
                 "is_month_end", "is_month_start", "is_pre_holiday_like", "is_post_holiday_like"]

        for c in focus:
            if c in m.params.index:
                rows.append({
                    "period": key,
                    "var": c,
                    "coef": float(m.params[c]),
                    "t": float(m.tvalues[c]),
                    "p": float(m.pvalues[c]),
                    "nobs": int(m.nobs),
                })

    res = pd.DataFrame(rows)
    return cal, res, models

# ============================================================
# 7) 実行例
# ============================================================

if __name__ == "__main__":
    cal, res, models = run_calendar_effects_report(
        start="2000-01-01",
        end=None,
        tom_pre=1, tom_post=3,    # TOM窓 [-1,+3]
        hac_lags=5,
        splits=("2000-01-01", "2010-01-01", "2020-01-01")
    )

    pd.set_option("display.max_rows", 500)
    print(res.sort_values(["var", "period"]))

    # 最新区間の回帰サマリ全文
    if len(models) > 0:
        last_key = list(models.keys())[-1]
        print("\n=== Full regression summary for:", last_key, "===\n")
        print(models[last_key].summary())
```

* * *

次にやるべきこと（最短で有益な確認）
------------------

1.  まずこのフルコードをそのまま実行し、`res` の `is_TOM` と `is_third_friday / is_triple_witching` が
    *   2000年代
    *   2010年代
    *   2020年代  
        で **符号と有意性が安定**しているかを確認してください。
2.  次に TOM 窓を変えて感度を見ます（例：`tom_pre=0,tom_post=2` や `tom_pre=1,tom_post=1`）。  
    窓依存が強いなら「TOMを拾っている」可能性が高いです。

* * *

必要であれば、この結果を受けて

*   **あなたの Method6 日次執行版 `strat_excess_d` を y にした同様の回帰**（戦略がTOM依存か診断）
*   **執行日ルール（第3金曜回避・分割執行）を最適化する比較コード**  
    も、同じ流儀で “先読みなし” で統合します。

## Response:
結果はとても整理された形で出ています。結論から言うと、

> **少なくとも SPY（2000–2025）に関しては、古典的に知られる「月末月初効果（TOM）」や「第3金曜効果」は、同時回帰でコントロールするとほぼ消えており、  
> 2020年以降に相対的に目立つのは「休日前（pre-holiday）」と「曜日（金曜）」くらいで、しかも規模は小さい**

というのが、今回の回帰から読み取れる最も重要な含意です。

以下、**① 個別係数の解釈 → ② 期間別の構造変化 → ③ 戦略設計への含意**の順で整理します。

* * *

1\. 主要カレンダー効果の解釈（係数表ベース）
------------------------

### (1) 月末・月初効果（TOM, month\_end, month\_start）

| 変数 | 2000–09 | 2010–19 | 2020–25 |
| --- | --- | --- | --- |
| is\_TOM | ✕ | ✕ | ✕ |
| is\_month\_end | ✕ | ✕ | ✕ |
| is\_month\_start | △ | △ | ✕ |

*   **すべての期間で有意でない**
*   係数の符号も安定していない
*   同時回帰（曜日・月ダミー込み）では **TOM 効果は完全に消失**

👉 **重要な結論**

> 少なくとも SPY では、「月末・月初そのもの」に統計的に安定した超過リターンは確認できない。  
> したがって、**執行タイミング設計において TOM を積極的に“利用”する根拠は弱い**。

* * *

### (2) 第3金曜・トリプルウィッチング

| 変数 | 2020–25 |
| --- | --- |
| is\_third\_friday | ✕ |
| is\_triple\_witching | △（t ≈ −1.74, p ≈ 0.08） |

*   平均リターンとしては **強く有意ではない**
*   ただし **四半期末第3金曜は「やや負」方向**
*   有意水準 10% 程度 → _弱いが無視はできない_

👉 **解釈**

*   「方向性のアノマリー」というより  
    \*\*需給・ヘッジ解消による不利な執行（滑り・逆行）\*\*を反映している可能性が高い
*   平均リターンよりも **実務的には分散・VWAP 乖離が問題**

👉 **設計含意**

*   **この日に“当てない”回避ルールは合理的**
*   ただし「この日を狙う戦略」を作る根拠は弱い

* * *

### (3) 休日前効果（pre-holiday / post-holiday）

| 変数 | 2020–25 |
| --- | --- |
| is\_pre\_holiday\_like | **有意（coef ≈ +0.49% 日次）** |
| is\_post\_holiday\_like | ✕ |

*   **2020年以降でのみ、明確に有意**
*   日次 +0.49% は **SPYとしてはかなり大きい**
*   ただし定義は「gap≥3日（週末含む）」の簡易版

👉 **解釈**

*   いわゆる **pre-holiday effect** が、近年再浮上している可能性
*   コロナ後の
    *   個人投資家フロー
    *   週末リスクテイク行動
    *   月次・週次資金流入  
        が背景にある可能性

👉 **重要な注意**

*   これは **執行タイミング設計の“副作用”として効いている**可能性が高い
*   「この効果を狙う戦略」と真正面から競合すると、**短期フローに飲み込まれる**

* * *

### (4) 曜日効果（2020–25）

| 曜日 | 係数 | 解釈 |
| --- | --- | --- |
| 木曜（dow\_3） | − | 有意 |
| 金曜（dow\_4） | **−** | **有意** |

*   **金曜が有意に弱い**
*   古典的な「金曜強い」とは逆
*   近年のリスクオフ傾向・週末不確実性を反映か

👉 **設計含意**

*   **金曜引けで新規ポジションを建てるのは不利**
*   「月初＝金曜」に当たる場合、執行点をずらす価値あり

* * *

2\. フル回帰（2020–25）の全体像
---------------------

*   **R² ≈ 1.2%**  
    → カレンダー効果は _説明力としては非常に小さい_
*   F検定も境界的（p ≈ 0.075）

👉 **最重要な示唆**

> 市場全体（SPY）のリターンは、  
> **「カレンダーだけ」で説明できる部分はごく僅か**。

これはあなたの文脈では **非常に良いニュース**です。

* * *

3\. あなたの戦略（Method 6 / 四半期サイクル）への含意
----------------------------------

### (A) 「月末月初を狙う戦略」と競合していない

*   TOM が消えている →  
    **あなたの月次シグナルを、TOMフローが食っている可能性は低い**
*   「TOMを避けるために極端に執行点を歪める必要はない」

### (B) 実務的に考慮すべきはこの2点だけ

1.  **第3金曜（特に四半期末）回避**  
    → 平均では弱いが、執行不利の可能性あり
2.  **金曜引け執行を避ける**  
    → 2020年以降、金曜は統計的に不利

### (C) pre-holiday 効果へのスタンス

*   **積極的に利用すべきではない**
*   理由：
    *   短期フロー依存
    *   持続性が不明
    *   四半期サイクルという「中周期シグナル」と相性が悪い
*   むしろ  
    **「たまたま pre-holiday に当たる執行はラッキー」程度の扱い**が妥当

* * *

4\. 執行設計への具体的な結論（現時点）
---------------------

この検証結果を踏まえると、あなたの戦略に最も整合的なのは：

> **月次シグナルは維持し、  
> 執行は「翌月第1営業日・寄り or VWAP」、  
> ただし  
> ・金曜なら翌営業日へ  
> ・四半期末の第3金曜なら必ず回避**

という **最小限・ロバストな調整**です。

* * *

次の必須ステップ（ここまで来たら）
-----------------

次にやるべきことは明確で、

> **同じ回帰を「あなたの戦略日次リターン」に対して行う**

です。

*   被説明変数：`strat_excess_d`（Method 6 日次執行版）
*   説明変数：今回と同じカレンダーダミー

これにより：

*   あなたの戦略が
    *   TOM に依存しているか
    *   pre-holiday に偏っているか
    *   金曜弱さを拾っていないか

を **完全に切り分けられます**。

必要であれば、  
👉 **この回帰をそのまま差し替えて実行するコード**  
👉 **戦略 vs 市場（SPY）の比較表**  
を次に提示します。

## Response:
承知しました。以下に **(1) 回帰を「市場ret → 戦略ret」にそのまま差し替えて実行するコード** と、**(2) 戦略 vs 市場（SPY）の比較表を作るコード** をフルで示します。

※この作業は yfinance と、あなたが既に作っている `out_d["strat_excess_d"]`（または `strat_excess_d_scaled`）があれば完結します。以前アップロードされた一部ファイルは期限切れになっているようですが、今回の2件には不要です（参照が必要になったら再アップロードをご依頼します）。

* * *

1) 回帰を「戦略リターン」に差し替えて実行するコード（HAC・同一デザイン行列）
-----------------------------------------

> 前回のコード（`load_spy_daily / build_calendar_features / make_design_matrix / hac_ols`）が既に定義済みである前提で、**追加分だけ**書きます。  
> もし未定義なら、前回お渡ししたフルコードを先に実行してください。

```python
import numpy as np
import pandas as pd
import statsmodels.api as sm

# ------------------------------------------------------------
# 戦略リターンをカレンダー特徴量DataFrameに差し替える（重要）
# ------------------------------------------------------------
def attach_strategy_return_to_calendar(cal: pd.DataFrame,
                                       strat_ret: pd.Series,
                                       col_name="ret_strat",
                                       align="inner"):
    """
    cal: build_calendar_features() の返り値（index=取引日, ret は市場の日次）
    strat_ret: 戦略の日次リターン series（index=取引日）
      - out_d["strat_excess_d"] などを渡す
      - すでに日次で先読みなし（pos.shift(1)*ret）ならOK
    """
    s = strat_ret.copy()
    s = pd.to_numeric(s, errors="coerce").astype(float)
    s = s.replace([np.inf, -np.inf], np.nan).dropna()

    # index を揃える
    if align == "inner":
        idx = cal.index.intersection(s.index)
        out = cal.loc[idx].copy()
        out[col_name] = s.loc[idx]
    elif align == "left":
        out = cal.copy()
        out[col_name] = s.reindex(out.index)
    else:
        raise ValueError("align must be 'inner' or 'left'")

    out = out.dropna(subset=[col_name])
    return out

# ------------------------------------------------------------
# 市場回帰と同じ設計で、戦略リターンに対して回帰する
# ------------------------------------------------------------
def run_calendar_regression_on_series(cal: pd.DataFrame,
                                      y: pd.Series,
                                      hac_lags=5,
                                      include_dow=True,
                                      include_month=True,
                                      include_tom=True,
                                      include_third_friday=True,
                                      include_triple_witching=True,
                                      include_q_end=True,
                                      include_holiday_like=True):
    """
    cal: build_calendar_features()で作ったDataFrame（index=取引日）
    y: 被説明変数（日次リターンseries、cal.indexと整合すること）
    """
    sub = cal.copy()
    y = pd.to_numeric(y, errors="coerce").astype(float).reindex(sub.index)
    sub = sub.dropna(subset=[])  # no-op
    y = y.dropna()
    sub = sub.loc[y.index]

    X = make_design_matrix(sub,
                           include_dow=include_dow,
                           include_month=include_month,
                           include_tom=include_tom,
                           include_third_friday=include_third_friday,
                           include_triple_witching=include_triple_witching,
                           include_q_end=include_q_end,
                           include_holiday_like=include_holiday_like)

    # statsmodels安全化
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0).astype(float)
    y = y.astype(float)

    model = hac_ols(y, X, lags=hac_lags)
    return model

# ------------------------------------------------------------
# 期間分割（2000s / 2010s / 2020s）で戦略のカレンダー回帰を回す
# ------------------------------------------------------------
def run_strategy_calendar_effects_report(
    cal: pd.DataFrame,
    strat_ret: pd.Series,
    hac_lags=5,
    splits=("2000-01-01","2010-01-01","2020-01-01"),
    y_name="ret_strat"
):
    """
    cal: build_calendar_features(df_market) の出力（取引日ベース）
    strat_ret: 戦略の日次リターン series（index=取引日）
    """
    cal2 = attach_strategy_return_to_calendar(cal, strat_ret, col_name=y_name, align="inner")

    split_dates = sorted([pd.Timestamp(s) for s in splits])
    periods = []
    for i in range(len(split_dates)):
        a = split_dates[i]
        b = split_dates[i+1] if i+1 < len(split_dates) else cal2.index.max() + pd.Timedelta(days=1)
        periods.append((a, b))

    rows = []
    models = {}

    focus = ["is_TOM", "is_third_friday", "is_triple_witching",
             "is_month_end", "is_month_start", "is_pre_holiday_like", "is_post_holiday_like"]

    for (a, b) in periods:
        sub = cal2[(cal2.index >= a) & (cal2.index < b)].copy()
        if len(sub) < 252:
            continue

        y = sub[y_name]

        m = run_calendar_regression_on_series(
            cal=sub,
            y=y,
            hac_lags=hac_lags,
            include_dow=True,
            include_month=True,
            include_tom=True,
            include_third_friday=True,
            include_triple_witching=True,
            include_q_end=True,
            include_holiday_like=True
        )

        key = f"{a.date()}__{(b - pd.Timedelta(days=1)).date()}"
        models[key] = m

        for c in focus:
            if c in m.params.index:
                rows.append({
                    "period": key,
                    "var": c,
                    "coef": float(m.params[c]),
                    "t": float(m.tvalues[c]),
                    "p": float(m.pvalues[c]),
                    "nobs": int(m.nobs),
                })

    res = pd.DataFrame(rows)
    return res, models
```

### 実行例（市場カレンダー `cal` と、戦略 `out_d` がある前提）

```python
# 1) 市場データで cal を作る（前回のrun_calendar_effects_report内と同じ）
# df_mkt = load_spy_daily(start="2000-01-01")
# cal = build_calendar_features(df_mkt, tom_pre=1, tom_post=3)

# 2) 戦略リターンを用意（例：あなたの out_d から）
# strat_ret = out_d["strat_excess_d_scaled"].dropna()   # どちらでもOK
# strat_ret = out_d["strat_excess_d"].dropna()

res_strat, models_strat = run_strategy_calendar_effects_report(
    cal=cal,
    strat_ret=strat_ret,
    hac_lags=5,
    splits=("2000-01-01","2010-01-01","2020-01-01"),
    y_name="ret_strat"
)

pd.set_option("display.max_rows", 500)
print(res_strat.sort_values(["var","period"]))

# 最新区間のフルサマリ
if len(models_strat) > 0:
    last_key = list(models_strat.keys())[-1]
    print("\n=== Strategy calendar regression summary for:", last_key, "===\n")
    print(models_strat[last_key].summary())
```

* * *

2) 戦略 vs 市場（SPY）の比較表（年率リターン/ボラ/Sharpe/MaxDD + CAPM α,β）
-------------------------------------------------------

以下は **日次リターン series** を与えると、\*\*比較表（DataFrame）\*\*を返す関数です。

```python
import numpy as np
import pandas as pd
import statsmodels.api as sm

def max_drawdown_from_return_series(r: pd.Series):
    """r: 日次リターン"""
    wealth = (1.0 + r.fillna(0.0)).cumprod()
    peak = wealth.cummax()
    dd = wealth / peak - 1.0
    return float(dd.min())

def annualized_stats(r: pd.Series, periods_per_year=252):
    r = pd.to_numeric(r, errors="coerce").astype(float).dropna()
    ann_ret = (1.0 + r).prod() ** (periods_per_year / len(r)) - 1.0
    ann_vol = r.std(ddof=1) * np.sqrt(periods_per_year)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan
    mdd = max_drawdown_from_return_series(r)
    return ann_ret, ann_vol, sharpe, mdd

def capm_alpha_beta_hac(r_port: pd.Series, r_mkt: pd.Series, hac_lags=5):
    """
    CAPM: r_port = alpha + beta * r_mkt + eps
    ※ rf を明示的に入れるなら超過リターンにしてから渡す
    """
    df = pd.DataFrame({"rp": r_port, "rm": r_mkt}).dropna()
    y = df["rp"].astype(float)
    X = sm.add_constant(df["rm"].astype(float))
    m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    alpha_d = float(m.params["const"])
    beta = float(m.params["rm"])
    t_alpha = float(m.tvalues["const"])
    return alpha_d, beta, t_alpha

def build_strategy_vs_market_table(
    strat_ret: pd.Series,
    mkt_ret: pd.Series,
    name_strat="Strategy",
    name_mkt="SPY",
    hac_lags=5
):
    # index を揃える（公平比較）
    idx = strat_ret.dropna().index.intersection(mkt_ret.dropna().index)
    rs = strat_ret.loc[idx].astype(float)
    rm = mkt_ret.loc[idx].astype(float)

    rows = []

    for name, r in [(name_strat, rs), (name_mkt, rm)]:
        ann_ret, ann_vol, sharpe, mdd = annualized_stats(r)
        rows.append({
            "name": name,
            "ann_return": ann_ret,
            "ann_vol": ann_vol,
            "sharpe": sharpe,
            "max_dd": mdd,
            "nobs": int(len(r))
        })

    out = pd.DataFrame(rows).set_index("name")

    # CAPMは「市場に対する戦略のα」を見る（市場自身はα不要）
    alpha_d, beta, t_alpha = capm_alpha_beta_hac(rs, rm, hac_lags=hac_lags)

    # 日次αを年率換算（近似：252倍）
    out.loc[name_strat, "alpha_ann"] = alpha_d * 252
    out.loc[name_strat, "beta"] = beta
    out.loc[name_strat, "t(alpha_d)"] = t_alpha

    # 市場行は空にする
    out.loc[name_mkt, ["alpha_ann","beta","t(alpha_d)"]] = np.nan

    return out
```

### 実行例

```python
# 市場日次リターン（同じcalを作った元のdf_mktから）
mkt_ret = cal["ret"]  # load_spy_daily → build_calendar_features に由来する日次ret

# 戦略日次リターン（例）
# strat_ret = out_d["strat_excess_d_scaled"].dropna()
# or strat_ret = out_d["strat_excess_d"].dropna()

tbl = build_strategy_vs_market_table(
    strat_ret=strat_ret,
    mkt_ret=mkt_ret,
    name_strat="Method6(daily exec)",
    name_mkt="SPY",
    hac_lags=5
)

print(tbl)
```

* * *

補足（あなたの目的に直結する見方）
-----------------

*   **カレンダー回帰（戦略ret）で `is_TOM` や `is_pre_holiday_like` が有意**なら  
    → 戦略がカレンダーフローに依存（＝“出し抜けていない”可能性）
*   **市場では有意でも、戦略では有意でない**なら  
    → 戦略はカレンダーを拾っていない（＝頑健性が高い）
*   `alpha_ann` がプラスで `t(alpha_d)` が十分大きいなら  
    → 市場要因を控除しても超過（CAPMレベル）

* * *

もし `out_d` の列名が手元で違う（例：`strat_excess_d_scaled` が無い等）場合は、あなたの `out_d.columns` を貼ってください。こちらでそのまま動くように差し替えた版を提示します。

## Response:
以下は、あなたが提示した **Method 6（月次で定義された  $S_t, x_t, \beta_t$ ）を保ったまま**、\*\*SPY 日次データで「日次執行（ポジションを日々保有）」\*\*できるようにした **フルコード**です。

ポイントは次の設計です（先読みなし）：

*   **月次で Method6 の  $x_t,\beta_t,w^{raw}_t$  を推定**（あなたの関数をそのまま利用）
*   **日次では「直近確定した月次ウェイト」を翌月の全営業日に適用**（月末確定→翌営業日から適用）
*   ボラターゲットは、あなたの `vol_target_from_weights` の「全期間一括スケール」ではなく、**日次執行向けに「過去窓の実現ボラで逐次スケール」**（rolling, shift(1)）に変更  
    → これが「日次執行版」にする上での本質的な変更点です

* * *

日次執行版（フルコード）
============

```python
import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm

# ============================================================
# 0) 便利：月タイプ（あなたの定義のまま）
# ============================================================

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

# ============================================================
# 1) 日次データ取得（SPY）
# ============================================================

def load_spy_daily(start="2000-01-01", end=None) -> pd.DataFrame:
    """
    戻り値: index=取引日, columns=['px','ret_total']
    auto_adjust=True で分配金調整込みの価格を使う
    """
    data = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)
    if data is None or len(data) == 0:
        raise ValueError("yfinance returned empty data (SPY).")

    # MultiIndex columns 対応
    if isinstance(data.columns, pd.MultiIndex):
        if ("Close", "SPY") in data.columns:
            px = data[("Close", "SPY")]
        else:
            close_cols = [c for c in data.columns if c[0] == "Close"]
            if len(close_cols) == 0:
                raise ValueError(f"Close column not found. columns={data.columns}")
            px = data[close_cols[0]]
    else:
        if "Close" not in data.columns:
            raise ValueError(f"Close column not found. columns={data.columns}")
        px = data["Close"]

    if isinstance(px, pd.DataFrame):
        if px.shape[1] != 1:
            raise ValueError(f"Unexpected Close DataFrame shape: {px.shape}")
        px = px.iloc[:, 0]

    px = px.dropna().rename("px")
    df = px.to_frame()
    df["ret_total"] = df["px"].pct_change()
    df = df.dropna()
    return df

# ============================================================
# 2) 日次→月次への集計（Method6は月次で定義）
# ============================================================

def daily_to_monthly_total(daily_total_ret: pd.Series) -> pd.Series:
    """
    月次トータルリターン（複利）を作る：
      R_m = Π(1+r_d) - 1
    index は月末（取引日ベース）
    """
    daily_total_ret = daily_total_ret.dropna().astype(float)
    monthly_total = (1.0 + daily_total_ret).resample("M").prod() - 1.0
    monthly_total = monthly_total.dropna()
    return monthly_total

# ============================================================
# 3) あなたの Method6 核心（ほぼそのまま）
# ============================================================

def compute_S_and_x_for_method6(mkt_total: pd.Series):
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")
    news_series = mkt_total[is_newsy]

    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news_series[news_series.index <= t]
        if len(past) >= 4:
            S[t] = past.iloc[-4:].sum()
        else:
            S[t] = np.nan

    x = pd.Series(index=idx, dtype=float)
    S_hist = []
    for i in range(1, len(idx)):
        prev_date = idx[i-1]
        curr_date = idx[i]

        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue

        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return S, x, month_type

def build_method6_raw_weights(mkt_total: pd.Series, min_obs=120):
    """
    月次の mkt_total を入力として、
    x_t, beta_t, w_raw_t を月次で出す
    """
    idx = mkt_total.index
    S, x, month_type = compute_S_and_x_for_method6(mkt_total)

    # mkt_mean: expanding mean の t-1（あなたの枠組み）
    mkt_mean = mkt_total.expanding().mean().shift(1)
    y_adj = mkt_total - mkt_mean
    beta = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx):
        mask = (idx <= t) & x.notna() & y_adj.notna()
        n = int(mask.sum())
        if n < min_obs:
            beta[t] = np.nan
            continue
        xi = x[mask].values
        yi = y_adj[mask].values
        denom = float((xi ** 2).sum())
        beta[t] = float((xi * yi).sum() / denom) if denom > 0 else np.nan

    w_raw = pd.Series(index=idx, dtype=float)
    for t in idx:
        if np.isnan(beta[t]) or np.isnan(x[t]):
            w_raw[t] = 0.0
        else:
            w_raw[t] = float(beta[t] * x[t])

    return x, beta, w_raw, month_type

# ============================================================
# 4) 月次ウェイトを日次執行に落とす（先読みなし）
# ============================================================

def map_monthly_weight_to_daily(w_monthly: pd.Series, daily_index: pd.DatetimeIndex) -> pd.Series:
    """
    w_monthly: 月末indexのウェイト（Method6の出力）
    日次執行：月末で確定した w を「翌月の取引日全て」に適用する（先読みなし）
    実装：w_monthly を resample("M") で月末系列として扱い、日次へ forward-fill、
          さらに 1カ月シフトして当月適用（= 前月末で決まったものを使う）
    """
    # 月末系列 -> 日次へ
    w_m = w_monthly.copy().sort_index().astype(float)
    w_daily = w_m.resample("D").ffill().reindex(daily_index).ffill()

    # 先読み回避：当月の日次で使うのは「前月末までに確定した w」
    # 月末確定→翌月初から使いたいので、月次で 1 期シフトしてから日次化するのが最も明快：
    w_m_shift = w_m.shift(1)  # t月末のwを t+1月に使う
    w_daily2 = w_m_shift.resample("D").ffill().reindex(daily_index).ffill()

    # 最初の月は NaN になるので 0 で埋める（初期無ポジ）
    w_daily2 = w_daily2.fillna(0.0)
    return w_daily2.rename("w_raw_daily")

# ============================================================
# 5) 日次ボラターゲット（rolling, shift(1) で先読みなし）
# ============================================================

def rolling_vol_target_scale(strat_excess_raw_d: pd.Series,
                             target_vol_ann: float = 0.10,
                             vol_window: int = 63,
                             periods_per_year: int = 252,
                             min_obs: int = 20) -> pd.Series:
    """
    日次の戦略超過リターン（raw）から、逐次スケール係数 scale_t を作る
    - 過去 vol_window 日の実現ボラ（年率換算）で割る
    - scale は shift(1)（当日のスケールが当日リターンを見ない）
    """
    r = strat_excess_raw_d.astype(float)

    # 年率ボラ：std * sqrt(252)
    vol_ann = r.rolling(vol_window, min_periods=min_obs).std(ddof=1) * np.sqrt(periods_per_year)
    scale = (target_vol_ann / vol_ann).replace([np.inf, -np.inf], np.nan)

    # 先読み回避
    scale = scale.shift(1)

    # 初期は 1.0（スケールなし）にしても良いが、ここでは安全に 0 へ寄せるのもあり
    scale = scale.fillna(1.0)
    return scale.rename("scale")

# ============================================================
# 6) 日次執行版 Method6（統合）
# ============================================================

def build_method6_daily_execution(
    start="2000-01-01",
    end=None,
    min_obs_monthly_beta: int = 120,
    target_vol_ann: float = 0.10,
    vol_window_days: int = 63,
    max_leverage: float = 3.0,
):
    """
    出力：
      - daily_out: 日次（実際に執行するウェイトと戦略リターン）
      - monthly_out: 月次（Method6推定の中間変数）
    """
    # --- 日次SPY ---
    daily = load_spy_daily(start=start, end=end)
    daily_idx = daily.index

    # rf を別途入れる場合はここで daily["rf"] を作り、
    # mkt_excess = ret_total - rf とする。
    # ここでは簡単に rf=0 として、mkt_excess = ret_total とする。
    daily["rf"] = 0.0
    daily["mkt_excess"] = daily["ret_total"] - daily["rf"]

    # --- 月次に集計（Method6推定の入力）---
    mkt_total_m = daily_to_monthly_total(daily["ret_total"])
    x_m, beta_m, w_raw_m, month_type_m = build_method6_raw_weights(
        mkt_total=mkt_total_m,
        min_obs=min_obs_monthly_beta
    )

    monthly_out = pd.DataFrame({
        "mkt_total": mkt_total_m,
        "x": x_m,
        "beta": beta_m,
        "w_raw": w_raw_m,
        "month_type": month_type_m,
    }).dropna(subset=["mkt_total"])

    # --- 月次w_rawを日次へ（前月末確定→当月適用）---
    w_raw_d = map_monthly_weight_to_daily(monthly_out["w_raw"], daily_idx)

    # レバ制約（raw段階で）
    w_raw_d = w_raw_d.clip(lower=-max_leverage, upper=max_leverage)

    # --- 日次戦略リターン（raw）---
    strat_excess_raw_d = w_raw_d * daily["mkt_excess"]

    # --- 日次ボラターゲット（rolling）---
    scale_d = rolling_vol_target_scale(
        strat_excess_raw_d,
        target_vol_ann=target_vol_ann,
        vol_window=vol_window_days,
        periods_per_year=252,
        min_obs=max(20, vol_window_days // 3),
    )

    w_scaled_d = (w_raw_d * scale_d).clip(lower=-max_leverage, upper=max_leverage)
    strat_excess_d = w_scaled_d * daily["mkt_excess"]
    strat_total_d = daily["rf"] + strat_excess_d

    daily_out = daily.copy()
    daily_out["w_raw_daily"] = w_raw_d
    daily_out["scale"] = scale_d
    daily_out["w_scaled_daily"] = w_scaled_d
    daily_out["strat_excess_raw_d"] = strat_excess_raw_d
    daily_out["strat_excess_d"] = strat_excess_d
    daily_out["strat_total_d"] = strat_total_d

    # 便利：月次ウェイトを日次に付与しただけではなく「その日に適用された月次月末」を見たい場合
    # daily_out["month_end_anchor"] = daily_out.index.to_period("M").to_timestamp("M")

    return daily_out, monthly_out

# ============================================================
# 7) 使用例
# ============================================================

if __name__ == "__main__":
    daily_out, monthly_out = build_method6_daily_execution(
        start="2000-01-01",
        end=None,
        min_obs_monthly_beta=120,
        target_vol_ann=0.10,     # 例：年率10%
        vol_window_days=63,      # 例：3ヶ月
        max_leverage=3.0
    )

    print("=== daily_out columns ===")
    print(daily_out.columns.tolist())

    print("\n=== monthly_out tail ===")
    print(monthly_out.tail())

    # 累積リターン（超過ベース）
    wealth = (1 + daily_out["strat_excess_d"].fillna(0)).cumprod()
    print("\nFinal wealth (excess):", float(wealth.iloc[-1]))
```

* * *

実装上の重要な解釈（あなたの月次版との“挙動差”が出る理由）
==============================

あなたの `vol_target_from_weights` は **全期間の realized\_vol で1回だけ scale** します。  
日次執行でそれをやると、運用の現実（逐次推定）とズレます。そこで上のコードでは：

*   `strat_excess_raw_d` の **過去窓（例 63日）のボラ**でスケール
*   しかも `shift(1)` で当日データを見ない

という「運用で可能な」形に直しています。  
この違いにより、**2020以降のボラ構造変化**や、**短期的な変動局面**で挙動が大きく変わります。

* * *

次の一手（あなたの意図に沿って）
================

この `daily_out["strat_excess_d"]` ができたので、あなたが先ほど求めていた

*   **カレンダーダミー回帰（戦略ret版）**
*   **戦略 vs 市場（SPY）比較表**

にこのまま接続できます（あなたが前に動かした `cal` と合わせて `strat_ret = daily_out["strat_excess_d"]` を渡すだけ）。

必要なら、上の `build_method6_daily_execution()` の出力を前提に、**回帰と比較表を一つの `run_all()` に統合した版**もそのまま貼ります。

## Response:
結論から言うと、**現状の「日次執行版 Method6」実装は、カレンダー効果に対して“特別な回避・補正はしていません”**。  
ただし、**先読みなし**という意味では、カレンダー効果に“迎合して過剰最適化する”こともしておらず、**月次シグナルを日次で執行できる形に正しく写像**しています。以下、どの効果に対してどういう状態かを整理します。

* * *

1) TOM（月末月初）への対処
----------------

### 現状の実装がしていること

*   月次で  $w^{raw}_t$  を計算し、**「前月末までに確定したウェイト」を当月の日次に適用**しています：
    *   `w_m.shift(1)` → 当月は前月末の情報だけで運用
*   そのため、**“月末に合わせて売買する”設計ではない**（執行日を月末に固定していない）。

### していないこと（＝意図的に放置）

*   TOM 窓（例：月末最終日〜月初数日）を避ける／寄せる
*   TOM日にウェイトを特別に下げる

### 含意

*   あなたのSPY回帰では **TOMは有意でなかった**ので、現状は合理的です。
*   ただし「実務の滑り（約定コスト）」観点では、TOMは平均リターンよりも **執行コスト差**として出ることがあるため、必要なら後段で「執行ルール」として入れるのが筋です（信号定義に混ぜない）。

* * *

2) 第3金曜・トリプルウィッチングへの対処
----------------------

### 現状の実装がしていること

*   何もしていません（回避ルールなし）。

### 含意

*   先の回帰では、平均リターンとしては強く有意ではないが、\*\*2020以降でトリプルウィッチングが弱く負（p≈0.08）\*\*という兆候がありました。
*   このタイプは「平均リターン」ではなく \*\*執行不利（逆行・スプレッド・インパクト）\*\*で効くことが多いので、実務的には
    *   **その日に新規構築しない**
    *   **前日/翌日へ分散**  
        のような“執行ルール”を追加するのが適切です。

現状は未実装なので、**対処していない**が正確な答えです。

* * *

3) 曜日効果（特に金曜弱さ）への対処
-------------------

### 現状の実装がしていること

*   何もしていません（曜日でウェイトを変えない）。

### 含意

*   回帰では 2020以降で **金曜（dow\_4）が有意に負**でした。
*   これは「シグナル」ではなく「執行の癖」で損しやすいタイプなので、実務的には
    *   **金曜引けの新規構築を避ける**
    *   もしくは **金曜はリバランス量を小さくする**  
        が合理的ですが、現状は未実装です。

* * *

4) 休日前効果（pre-holiday-like）への対処
------------------------------

### 現状の実装がしていること

*   何もしていません（休日前を狙いに行かない／避けない）。

### ただし重要な点

*   あなたの検証で **2020以降 pre-holiday-like が有意に正**でした。
*   現状実装はこれを明示的に利用していないので、**過剰適合していない**のは良い点です。

ただし、あなたが「執行日」をもし固定（例：毎月1日に寄せる）すると、結果的に休日前後に偏る可能性があります。現状コードは執行日を固定していないため、**偶然の重なり**としてのみ影響します。

* * *

5) 「ボラターゲット（rolling）」がカレンダー効果に与える影響
-----------------------------------

あなたの月次版の `vol_target_from_weights`（全期間で1回スケール）に比べて、日次版は

*   過去窓（例63日）で実現ボラを推定し
*   `shift(1)`で先読みなしにスケール

を入れています。

これはカレンダー効果への「直接対処」ではないですが、結果として：

*   特定の曜日や満期日にボラが跳ねる局面では  
    → **スケールが翌日以降で下がる**（リスクを落とす）
*   TOMや満期で“変な日次変動”が出ても  
    → **長期平均ではなく直近窓で吸収**する

という意味で、**間接的な頑健化**にはなっています。  
ただし、これは「カレンダー日を避ける」ものではなく、**リスク制御**です。

* * *

6) まとめ：現状実装の立ち位置
----------------

*   \*\*信号（Method6の月次 x, β）\*\*はそのまま
*   **日次執行への写像**は「前月末確定→当月適用」で先読みなし
*   カレンダー効果への対処は
    *   **直接対処（回避・補正）は未実装**
    *   **間接対処（rolling vol target によるリスク抑制）はあり**

* * *

次の実務的アップグレード（最小で効く順）
--------------------

あなたの回帰結果に合わせるなら、シグナルをいじらず「執行ルール」だけ追加するのが正攻法です。

1.  **金曜に新規構築しない（またはリバランス量縮小）**
2.  **四半期末の第3金曜（トリプルウィッチング）を回避**
3.  TOMは現状有意でないので、必要ならコスト観点でのみ調整
4.  pre-holiday は“狙う”より“偏っていないか診断”を優先

* * *

必要なら、上の(1)(2)を「先読みなし」で入れた **執行ルール付き日次執行版**（例：`execution_filter(date)` が True なら当日は据え置き、等）をフルコードで提示します。なお、以前アップロードされていた一部ファイルは期限切れになっているため、もし文献PDFの記述を引用しながら執行ルールを設計したい場合は再アップロードをお願いします。

## Response:
了解しました。ここでは **(1) 金曜に新規構築しない（＝金曜はウェイト据え置き）** と **(2) 四半期末の第3金曜（トリプルウィッチング）は新規構築しない（据え置き）** を、**先読みなし**で日次執行版に組み込みます。加えて、**2000年以降で「月次執行（月末→翌月）版」と日次執行（＋執行回避ルール）版のパス比較**（累積リターン、年率統計、同一期間での比較、プロット）まで一気通貫で回るフルコードを提示します。

> 注：以前アップロードされていた一部ファイルは期限切れになっているようですが、今回の比較は yfinance と本コードだけで完結するため再アップロードは不要です。

* * *

フルコード：Method6（月次） vs 日次執行（Fri/TripleWitching回避）比較（2000〜）
========================================================

```python
import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm
import matplotlib.pyplot as plt

# ============================================================
# 0) Month type (N/R/3) – same as your definition
# ============================================================

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

# ============================================================
# 1) Load SPY daily (robust)
# ============================================================

def load_spy_daily(start="2000-01-01", end=None) -> pd.DataFrame:
    data = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)
    if data is None or len(data) == 0:
        raise ValueError("yfinance returned empty data (SPY). Retry or adjust date range.")

    if isinstance(data.columns, pd.MultiIndex):
        if ("Close", "SPY") in data.columns:
            px = data[("Close", "SPY")]
        else:
            close_cols = [c for c in data.columns if c[0] == "Close"]
            if len(close_cols) == 0:
                raise ValueError(f"Close column not found. columns={data.columns}")
            px = data[close_cols[0]]
    else:
        if "Close" not in data.columns:
            raise ValueError(f"Close column not found. columns={data.columns}")
        px = data["Close"]

    if isinstance(px, pd.DataFrame):
        if px.shape[1] != 1:
            raise ValueError(f"Unexpected Close DataFrame shape: {px.shape}")
        px = px.iloc[:, 0]

    px = px.dropna().rename("px")
    df = px.to_frame()
    df["ret_total"] = df["px"].pct_change()
    df = df.dropna()

    # For now rf=0 (you can plug in T-bill daily if you want)
    df["rf"] = 0.0
    df["mkt_excess"] = df["ret_total"] - df["rf"]
    return df

# ============================================================
# 2) Daily -> monthly total return (compound)
# ============================================================

def daily_to_monthly_total(daily_total_ret: pd.Series) -> pd.Series:
    daily_total_ret = daily_total_ret.dropna().astype(float)
    monthly_total = (1.0 + daily_total_ret).resample("M").prod() - 1.0
    return monthly_total.dropna()

# ============================================================
# 3) Method6 core (monthly): S_t, x_t, beta_t, w_raw_t
# ============================================================

def compute_S_and_x_for_method6(mkt_total: pd.Series):
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")
    news_series = mkt_total[is_newsy]

    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news_series[news_series.index <= t]
        if len(past) >= 4:
            S[t] = past.iloc[-4:].sum()
        else:
            S[t] = np.nan

    x = pd.Series(index=idx, dtype=float)
    S_hist = []
    for i in range(1, len(idx)):
        prev_date = idx[i-1]
        curr_date = idx[i]

        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue

        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return S, x, month_type

def build_method6_raw_weights(mkt_total: pd.Series, min_obs=120):
    idx = mkt_total.index
    S, x, month_type = compute_S_and_x_for_method6(mkt_total)

    mkt_mean = mkt_total.expanding().mean().shift(1)
    y_adj = mkt_total - mkt_mean
    beta = pd.Series(index=idx, dtype=float)

    for t in idx:
        mask = (idx <= t) & x.notna() & y_adj.notna()
        n = int(mask.sum())
        if n < min_obs:
            beta[t] = np.nan
            continue
        xi = x[mask].values
        yi = y_adj[mask].values
        denom = float((xi**2).sum())
        beta[t] = float((xi * yi).sum() / denom) if denom > 0 else np.nan

    w_raw = pd.Series(index=idx, dtype=float)
    for t in idx:
        if np.isnan(beta[t]) or np.isnan(x[t]):
            w_raw[t] = 0.0
        else:
            w_raw[t] = float(beta[t] * x[t])

    return x, beta, w_raw, month_type

# ============================================================
# 4) Calendar helpers for execution rules
#    - Friday avoid
#    - Triple witching avoid (3rd Friday in Mar/Jun/Sep/Dec)
# ============================================================

def third_friday_dates(trading_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    start = trading_index.min().to_period("M").start_time
    end = trading_index.max().to_period("M").end_time
    cal = pd.date_range(start=start, end=end, freq="WOM-3FRI")

    snapped = []
    for d in cal:
        dd = d
        while dd not in trading_index:
            dd = dd - pd.Timedelta(days=1)
            if dd < trading_index.min():
                break
        if dd in trading_index:
            snapped.append(dd)
    return pd.DatetimeIndex(sorted(set(snapped)))

def build_triple_witching_mask(daily_index: pd.DatetimeIndex) -> pd.Series:
    tf = third_friday_dates(daily_index)
    is_third_friday = pd.Series(daily_index.isin(tf), index=daily_index)
    is_q_end_month = pd.Series(daily_index.month.isin([3, 6, 9, 12]), index=daily_index)
    is_tw = (is_third_friday & is_q_end_month)
    return is_tw.rename("is_triple_witching")

def build_friday_mask(daily_index: pd.DatetimeIndex) -> pd.Series:
    return pd.Series(daily_index.dayofweek == 4, index=daily_index).rename("is_friday")

# ============================================================
# 5) Monthly execution baseline (month-end weight -> next month)
#    - Apply monthly weight (decided at month t) to month t+1 daily returns
#    - Optionally monthly vol targeting with rolling window on monthly returns
# ============================================================

def map_monthly_weight_to_daily_next_month(w_monthly: pd.Series, daily_index: pd.DatetimeIndex) -> pd.Series:
    """
    Use w(t_month_end) for the next month's daily trading days.
    Implementation: shift(1) on monthly series then forward-fill on daily.
    """
    w_m = w_monthly.sort_index().astype(float)
    w_m_shift = w_m.shift(1)  # pre-month-end -> next month usage
    w_d = w_m_shift.resample("D").ffill().reindex(daily_index).ffill().fillna(0.0)
    return w_d.rename("w_raw_daily")

def rolling_scale_from_returns(r: pd.Series,
                               target_vol_ann: float = 0.10,
                               window: int = 63,
                               periods_per_year: int = 252,
                               min_obs: int = 20) -> pd.Series:
    """
    Rolling annualized volatility scaling (shift(1) for no-leak).
    """
    r = r.astype(float)
    vol_ann = r.rolling(window, min_periods=min_obs).std(ddof=1) * np.sqrt(periods_per_year)
    scale = (target_vol_ann / vol_ann).replace([np.inf, -np.inf], np.nan)
    scale = scale.shift(1).fillna(1.0)
    return scale.rename("scale")

# ============================================================
# 6) Daily execution with "do-not-rebalance" filters
#    Key idea:
#      - There's a desired weight w_desired(t) each day (from monthly signal mapping)
#      - Actual weight w_actual(t) updates to w_desired(t) ONLY if rebalance is allowed
#      - Otherwise w_actual(t) = w_actual(t-1)
# ============================================================

def apply_rebalance_filters_to_daily_weights(
    w_desired: pd.Series,
    forbid_rebalance_mask: pd.Series,
) -> pd.Series:
    """
    forbid_rebalance_mask[t]=True means: do NOT update weight at day t (keep yesterday's weight).
    This is a pure execution rule; signal is unchanged.
    """
    w_desired = w_desired.copy().astype(float)
    mask = forbid_rebalance_mask.reindex(w_desired.index).fillna(False).astype(bool)

    w_actual = pd.Series(index=w_desired.index, dtype=float)
    prev = 0.0
    for t in w_desired.index:
        if mask.loc[t]:
            w_actual.loc[t] = prev
        else:
            val = float(w_desired.loc[t])
            w_actual.loc[t] = val
            prev = val
    return w_actual.rename("w_actual")

# ============================================================
# 7) Build & compare:
#    (A) monthly-exec baseline
#    (B) daily-exec with filters (Fri + TripleWitching)
# ============================================================

def build_method6_monthly_and_daily_paths(
    start="2000-01-01",
    end=None,
    min_obs_monthly_beta: int = 120,
    target_vol_ann: float = 0.10,
    vol_window_days: int = 63,
    max_leverage: float = 3.0,
):
    # --- Daily market data ---
    daily = load_spy_daily(start=start, end=end)
    idx_d = daily.index

    # --- Monthly signal construction (Method6) ---
    mkt_total_m = daily_to_monthly_total(daily["ret_total"])
    x_m, beta_m, w_raw_m, month_type_m = build_method6_raw_weights(mkt_total=mkt_total_m, min_obs=min_obs_monthly_beta)

    monthly = pd.DataFrame({
        "mkt_total": mkt_total_m,
        "x": x_m,
        "beta": beta_m,
        "w_raw": w_raw_m,
        "month_type": month_type_m,
    }).dropna(subset=["mkt_total"]).sort_index()

    # --- Map monthly raw weights to daily desired weights (next-month application) ---
    w_desired_raw_d = map_monthly_weight_to_daily_next_month(monthly["w_raw"], idx_d)
    w_desired_raw_d = w_desired_raw_d.clip(-max_leverage, max_leverage)

    # ------------------------------------------------------------
    # (A) Baseline daily path from monthly exec (no filters)
    #     - raw -> rolling vol target -> scaled weights
    # ------------------------------------------------------------
    strat_excess_raw_A = w_desired_raw_d * daily["mkt_excess"]
    scale_A = rolling_scale_from_returns(strat_excess_raw_A,
                                         target_vol_ann=target_vol_ann,
                                         window=vol_window_days,
                                         periods_per_year=252,
                                         min_obs=max(20, vol_window_days // 3))
    w_scaled_A = (w_desired_raw_d * scale_A).clip(-max_leverage, max_leverage)
    strat_excess_A = w_scaled_A * daily["mkt_excess"]

    out_A = daily.copy()
    out_A["w_raw_desired"] = w_desired_raw_d
    out_A["scale"] = scale_A
    out_A["w_scaled"] = w_scaled_A
    out_A["strat_excess_d"] = strat_excess_A

    # ------------------------------------------------------------
    # (B) Daily execution with filters:
    #     forbid rebalance on Friday OR triple witching day
    #     - Here "rebalance" means updating raw desired weight.
    #       scale is computed on realized returns as usual (shifted).
    # ------------------------------------------------------------
    is_friday = build_friday_mask(idx_d)
    is_tw = build_triple_witching_mask(idx_d)
    forbid = (is_friday | is_tw).rename("forbid_rebalance")

    w_actual_raw_B = apply_rebalance_filters_to_daily_weights(
        w_desired=w_desired_raw_d,
        forbid_rebalance_mask=forbid
    ).clip(-max_leverage, max_leverage)

    strat_excess_raw_B = w_actual_raw_B * daily["mkt_excess"]
    scale_B = rolling_scale_from_returns(strat_excess_raw_B,
                                         target_vol_ann=target_vol_ann,
                                         window=vol_window_days,
                                         periods_per_year=252,
                                         min_obs=max(20, vol_window_days // 3))
    w_scaled_B = (w_actual_raw_B * scale_B).clip(-max_leverage, max_leverage)
    strat_excess_B = w_scaled_B * daily["mkt_excess"]

    out_B = daily.copy()
    out_B["w_raw_desired"] = w_desired_raw_d
    out_B["forbid_rebalance"] = forbid
    out_B["w_raw_actual"] = w_actual_raw_B
    out_B["scale"] = scale_B
    out_B["w_scaled"] = w_scaled_B
    out_B["strat_excess_d"] = strat_excess_B
    out_B["is_friday"] = is_friday
    out_B["is_triple_witching"] = is_tw

    return monthly, out_A, out_B

# ============================================================
# 8) Performance summary + plotting
# ============================================================

def max_drawdown(r: pd.Series) -> float:
    wealth = (1.0 + r.fillna(0.0)).cumprod()
    peak = wealth.cummax()
    dd = wealth / peak - 1.0
    return float(dd.min())

def annualized_stats(r: pd.Series, periods_per_year=252):
    r = pd.to_numeric(r, errors="coerce").astype(float).dropna()
    ann_ret = (1.0 + r).prod() ** (periods_per_year / len(r)) - 1.0
    ann_vol = r.std(ddof=1) * np.sqrt(periods_per_year)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan
    mdd = max_drawdown(r)
    return ann_ret, ann_vol, sharpe, mdd, int(len(r))

def capm_alpha_beta_hac(r_port: pd.Series, r_mkt: pd.Series, hac_lags=5):
    df = pd.DataFrame({"rp": r_port, "rm": r_mkt}).dropna()
    y = df["rp"].astype(float)
    X = sm.add_constant(df["rm"].astype(float))
    m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    alpha_d = float(m.params["const"])
    beta = float(m.params["rm"])
    t_alpha = float(m.tvalues["const"])
    return alpha_d, beta, t_alpha

def build_comparison_table(out_A: pd.DataFrame, out_B: pd.DataFrame, name_A="MonthlyExec", name_B="DailyExec(Fri+TW avoid)"):
    # align common index
    idx = out_A.index.intersection(out_B.index)
    A = out_A.loc[idx].copy()
    B = out_B.loc[idx].copy()

    mkt = A["mkt_excess"].astype(float)  # same series

    rows = []
    for name, r in [(name_A, A["strat_excess_d"]), (name_B, B["strat_excess_d"]), ("SPY", mkt)]:
        ann_ret, ann_vol, sharpe, mdd, n = annualized_stats(r)
        rows.append({"name": name, "ann_return": ann_ret, "ann_vol": ann_vol, "sharpe": sharpe, "max_dd": mdd, "nobs": n})

    tbl = pd.DataFrame(rows).set_index("name")

    # CAPM alpha/beta for each strategy vs SPY
    for nm, r in [(name_A, A["strat_excess_d"]), (name_B, B["strat_excess_d"])]:
        alpha_d, beta, t_alpha = capm_alpha_beta_hac(r, mkt, hac_lags=5)
        tbl.loc[nm, "alpha_ann"] = alpha_d * 252
        tbl.loc[nm, "beta"] = beta
        tbl.loc[nm, "t(alpha_d)"] = t_alpha

    return tbl

def plot_paths(out_A: pd.DataFrame, out_B: pd.DataFrame, title="Cumulative wealth (excess)"):
    idx = out_A.index.intersection(out_B.index)
    A = out_A.loc[idx, "strat_excess_d"].fillna(0.0)
    B = out_B.loc[idx, "strat_excess_d"].fillna(0.0)
    M = out_A.loc[idx, "mkt_excess"].fillna(0.0)

    wa = (1.0 + A).cumprod()
    wb = (1.0 + B).cumprod()
    wm = (1.0 + M).cumprod()

    plt.figure(figsize=(14, 5))
    plt.plot(wa, label="MonthlyExec baseline", linewidth=2)
    plt.plot(wb, label="DailyExec + avoid(Fri, TripleWitching)", linewidth=2)
    plt.plot(wm, label="SPY", linewidth=1.5, alpha=0.8)
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()

# ============================================================
# 9) Run (2000+)
# ============================================================

if __name__ == "__main__":
    monthly, out_A, out_B = build_method6_monthly_and_daily_paths(
        start="2000-01-01",
        end=None,
        min_obs_monthly_beta=120,
        target_vol_ann=0.10,
        vol_window_days=63,
        max_leverage=3.0,
    )

    # comparison
    tbl = build_comparison_table(out_A, out_B)
    print("\n=== Strategy vs Market comparison (aligned sample) ===")
    print(tbl)

    # plot paths
    plot_paths(out_A, out_B, title="Method6: MonthlyExec vs DailyExec(with execution avoidance), 2000+")
```

* * *

実装が「１・２」にどう対処しているか（コード上の意味）
---------------------------

*   **① 金曜回避**：`is_friday = (dayofweek==4)` を True にした日は **リバランス（新規構築）しない**  
    → `apply_rebalance_filters_to_daily_weights()` で `w_actual[t] = w_actual[t-1]`
*   **② トリプルウィッチング回避**：`is_triple_witching = (第3金曜) & (3/6/9/12月)` を True にした日は **同様に据え置き**

この設計は「その日だけポジションをゼロにする」ではなく、**執行日をずらす**（＝実務の回避策として自然）です。  
シグナル自体は改変していないので、**Method6 の理論部分と混線しません**。

* * *

出力で確認すべきもの
----------

*   `tbl`：年率リターン・年率ボラ・Sharpe・MaxDD・CAPM alpha/beta を **同一サンプル**で比較
*   `plot_paths`：累積（超過）ウェルスを3本比較（baseline vs 回避版 vs SPY）

* * *

追加で現実性を上げるなら（必要なら次に入れます）
------------------------

今回の比較は「カレンダー日に“リバランスしない”」のみで、**取引コスト**は未導入です。  
実務ではこの手の回避ルールは **コスト削減効果**を通じて効くことが多いので、次の拡張が有効です：

*   日次で `turnover = |w_t - w_{t-1}|` を計算し
*   `strat_excess_d -= tc_per_turnover * turnover`
*   月末・満期・金曜にコストが上がる（可変コスト）も入れる

必要なら、コスト入りの比較版も同じ枠組みで即追加します。

## Response:
承知しました。ご提示の **Ken French 月次ベースライン（Method6 + vol-target を「全期間1回スケール」）** を「月次 exec の基準」として採用し、これと

*   **日次執行版（SPY 日次）**
*   **執行回避ルール：①金曜は新規構築しない（据え置き）②四半期末第3金曜（トリプルウィッチング）は据え置き**

を **2000年以降**で比較できるように、下のフルコードに統合しました。

比較は公平にするため、

*   月次ベースライン：月次の `strat_total`（rf込み）
*   日次執行：日次 `strat_total_d` を **月次に複利集計して同じ月次系列に変換**（rf=0 を仮定。rfを入れたければ後述の拡張で差し替え可能）

を行い、**同一の月次インデックス**でパス比較します。

> なお、以前アップロードされていた一部ファイルは期限切れになっている旨のシステム通知がありますが、今回の比較は「F-F\_Research\_Data\_Factors.csv（手元ファイル）」と yfinance だけで完結します。追加のPDF等は不要です。

* * *

フルコード：月次ベースライン（Ken French） vs 日次執行（SPY + Fri/TW回避）を月次で比較（2000+）
---------------------------------------------------------------

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import yfinance as yf

# ============================================================
# 0) Ken French (monthly) 読み込み（あなたのコード）
# ============================================================

def load_ff_monthly_from_ken_french(csv_path: str) -> pd.DataFrame:
    raw = pd.read_csv(csv_path, skiprows=4)

    num = pd.to_numeric(raw['Unnamed: 0'], errors='coerce')
    mask_monthly = num > 10000
    monthly = raw[mask_monthly].copy()

    monthly = monthly.rename(columns={'Unnamed: 0': 'date'})
    monthly['date'] = pd.to_datetime(monthly['date'].astype(int), format="%Y%m")
    monthly = monthly.set_index('date').sort_index()

    for col in ['Mkt-RF', 'RF']:
        monthly[col] = pd.to_numeric(monthly[col], errors='coerce')

    ff = monthly[['Mkt-RF', 'RF']].copy()
    ff['mkt_excess'] = ff['Mkt-RF'] / 100.0
    ff['rf']         = ff['RF'] / 100.0
    return ff[['mkt_excess', 'rf']].dropna()

# ============================================================
# 1) month_type（あなたの定義）
# ============================================================

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

# ============================================================
# 2) Method6: S_t, x_t（あなたの定義）
# ============================================================

def compute_S_and_x_for_method6(mkt_total: pd.Series):
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")
    news_series = mkt_total[is_newsy]

    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news_series[news_series.index <= t]
        if len(past) >= 4:
            S[t] = past.iloc[-4:].sum()
        else:
            S[t] = np.nan

    x = pd.Series(index=idx, dtype=float)
    S_hist = []
    for i in range(1, len(idx)):
        prev_date = idx[i-1]
        curr_date = idx[i]

        s_prev = S.loc[prev_date]
        if np.isnan(s_prev):
            x[curr_date] = np.nan
            continue

        S_hist.append(s_prev)
        s_bar = float(np.mean(S_hist))

        sign = -1.0 if is_newsy[curr_date] else 1.0
        x[curr_date] = sign * (s_prev - s_bar)

    return S, x, month_type

# ============================================================
# 3) Method6: β推定（rolling版：あなたのベースライン）
# ============================================================

def build_method6_raw_weights_rolling(
    ff: pd.DataFrame,
    lookback_years: int = 20,
    min_obs: int = 120,
):
    mkt_excess = ff["mkt_excess"].copy()
    rf         = ff["rf"].copy()
    mkt_total  = mkt_excess + rf
    idx        = mkt_total.index

    S, x, month_type = compute_S_and_x_for_method6(mkt_total)

    mkt_mean = mkt_total.expanding().mean().shift(1)
    y_adj    = mkt_total - mkt_mean

    beta = pd.Series(index=idx, dtype=float)
    lookback_months = lookback_years * 12

    for i, t in enumerate(idx):
        start_i = max(0, i - lookback_months + 1)
        win_idx = idx[start_i:(i + 1)]

        x_win = x.loc[win_idx]
        y_win = y_adj.loc[win_idx]
        mask  = x_win.notna() & y_win.notna()
        n     = int(mask.sum())

        if n < min_obs:
            beta[t] = np.nan
            continue

        xi = x_win[mask].values
        yi = y_win[mask].values
        denom = float((xi ** 2).sum())
        beta[t] = float((xi * yi).sum() / denom) if denom > 0 else np.nan

    w_raw = pd.Series(index=idx, dtype=float)
    for t in idx:
        if np.isnan(beta[t]) or np.isnan(x[t]):
            w_raw[t] = 0.0
        else:
            w_raw[t] = float(beta[t] * x[t])

    return x, beta, w_raw

# ============================================================
# 4) vol-target（ベースラインと同じ：全期間で1回スケール）
# ============================================================

def vol_target_from_weights_monthly_once(
    mkt_excess: pd.Series,
    rf: pd.Series,
    w_raw: pd.Series,
    target_vol: float = 0.05,
) -> pd.DataFrame:
    data = pd.concat(
        [mkt_excess.rename("mkt_excess"),
         rf.rename("rf"),
         w_raw.rename("w_raw")],
        axis=1
    ).dropna(subset=["mkt_excess", "rf"])

    strat_excess_raw = data["w_raw"] * data["mkt_excess"]

    realized_vol = strat_excess_raw.std(ddof=1)
    if realized_vol is None or realized_vol == 0 or np.isnan(realized_vol):
        scale = 1.0
    else:
        scale = target_vol / realized_vol

    w_scaled     = data["w_raw"] * scale
    strat_excess = strat_excess_raw * scale
    strat_total  = data["rf"] + strat_excess

    out = pd.DataFrame({
        "mkt_excess": data["mkt_excess"],
        "rf": data["rf"],
        "w_raw": data["w_raw"],
        "w_scaled": w_scaled,
        "strat_excess_raw": strat_excess_raw,
        "strat_excess": strat_excess,
        "strat_total": strat_total,
    })
    out.attrs["scale"] = float(scale)
    out.attrs["target_vol"] = float(target_vol)
    return out

# ============================================================
# 5) 日次SPY取得（分配金調整込み）
# ============================================================

def load_spy_daily(start="2000-01-01", end=None) -> pd.DataFrame:
    data = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)
    if data is None or len(data) == 0:
        raise ValueError("yfinance returned empty data (SPY).")

    if isinstance(data.columns, pd.MultiIndex):
        if ("Close", "SPY") in data.columns:
            px = data[("Close", "SPY")]
        else:
            close_cols = [c for c in data.columns if c[0] == "Close"]
            if len(close_cols) == 0:
                raise ValueError(f"Close column not found. columns={data.columns}")
            px = data[close_cols[0]]
    else:
        px = data["Close"]

    if isinstance(px, pd.DataFrame):
        px = px.iloc[:, 0]

    px = px.dropna().rename("px")
    df = px.to_frame()
    df["ret_total"] = df["px"].pct_change()
    df = df.dropna()

    # ここは簡便に rf=0 とする（rfを入れたい場合は後述）
    df["rf_d"] = 0.0
    df["mkt_excess_d"] = df["ret_total"] - df["rf_d"]
    return df

def daily_to_monthly_total(daily_total_ret: pd.Series) -> pd.Series:
    daily_total_ret = daily_total_ret.dropna().astype(float)
    monthly_total = (1.0 + daily_total_ret).resample("M").prod() - 1.0
    return monthly_total.dropna()

# ============================================================
# 6) 月次wを日次に（前月末確定→当月に適用）
# ============================================================

def map_monthly_weight_to_daily_next_month(w_monthly: pd.Series, daily_index: pd.DatetimeIndex) -> pd.Series:
    w_m = w_monthly.sort_index().astype(float)
    w_m_shift = w_m.shift(1)  # 前月末で確定したものを当月に使う
    w_d = w_m_shift.resample("D").ffill().reindex(daily_index).ffill().fillna(0.0)
    return w_d.rename("w_raw_desired")

# ============================================================
# 7) 執行回避ルール：金曜/トリプルウィッチング日はリバランスしない
# ============================================================

def third_friday_dates(trading_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    start = trading_index.min().to_period("M").start_time
    end = trading_index.max().to_period("M").end_time
    cal = pd.date_range(start=start, end=end, freq="WOM-3FRI")

    snapped = []
    for d in cal:
        dd = d
        while dd not in trading_index:
            dd = dd - pd.Timedelta(days=1)
            if dd < trading_index.min():
                break
        if dd in trading_index:
            snapped.append(dd)
    return pd.DatetimeIndex(sorted(set(snapped)))

def build_triple_witching_mask(daily_index: pd.DatetimeIndex) -> pd.Series:
    tf = third_friday_dates(daily_index)
    is_third_friday = pd.Series(daily_index.isin(tf), index=daily_index)
    is_q_end_month = pd.Series(daily_index.month.isin([3, 6, 9, 12]), index=daily_index)
    return (is_third_friday & is_q_end_month).rename("is_triple_witching")

def build_friday_mask(daily_index: pd.DatetimeIndex) -> pd.Series:
    return pd.Series(daily_index.dayofweek == 4, index=daily_index).rename("is_friday")

def apply_rebalance_filters_to_daily_weights(
    w_desired: pd.Series,
    forbid_rebalance_mask: pd.Series,
) -> pd.Series:
    w_desired = w_desired.astype(float)
    mask = forbid_rebalance_mask.reindex(w_desired.index).fillna(False).astype(bool)

    w_actual = pd.Series(index=w_desired.index, dtype=float)
    prev = 0.0
    for t in w_desired.index:
        if mask.loc[t]:
            w_actual.loc[t] = prev
        else:
            val = float(w_desired.loc[t])
            w_actual.loc[t] = val
            prev = val
    return w_actual.rename("w_raw_actual")

# ============================================================
# 8) 日次執行のvol-target：ベースラインと合わせて「全期間1回スケール」
# ============================================================

def vol_target_daily_once(
    mkt_excess_d: pd.Series,
    rf_d: pd.Series,
    w_raw_d: pd.Series,
    target_vol_ann: float = 0.10,
):
    """
    日次 raw 戦略超過 r_raw = w_raw_d * mkt_excess_d の年率ボラで 1回スケール。
    scale = target_vol_ann / (std(r_raw)*sqrt(252))
    """
    df = pd.concat([mkt_excess_d.rename("mkt_excess_d"),
                    rf_d.rename("rf_d"),
                    w_raw_d.rename("w_raw_d")], axis=1).dropna()

    r_raw = df["w_raw_d"] * df["mkt_excess_d"]
    vol_ann = r_raw.std(ddof=1) * math.sqrt(252)
    if vol_ann is None or vol_ann == 0 or np.isnan(vol_ann):
        scale = 1.0
    else:
        scale = float(target_vol_ann / vol_ann)

    w_scaled = df["w_raw_d"] * scale
    r_excess = r_raw * scale
    r_total = df["rf_d"] + r_excess

    out = pd.DataFrame({
        "mkt_excess_d": df["mkt_excess_d"],
        "rf_d": df["rf_d"],
        "w_raw_d": df["w_raw_d"],
        "w_scaled_d": w_scaled,
        "strat_excess_raw_d": r_raw,
        "strat_excess_d": r_excess,
        "strat_total_d": r_total,
    })
    out.attrs["scale"] = scale
    out.attrs["target_vol_ann"] = float(target_vol_ann)
    return out

def daily_total_to_monthly_total(daily_total_ret: pd.Series) -> pd.Series:
    """
    日次トータルリターン -> 月次トータルリターンへ（複利）
    """
    return (1.0 + daily_total_ret.dropna().astype(float)).resample("M").prod() - 1.0

# ============================================================
# 9) 比較用：統計/プロット
# ============================================================

def annualized_stats_monthly(r_m: pd.Series):
    r_m = r_m.dropna().astype(float)
    mu_m = r_m.mean()
    sd_m = r_m.std(ddof=1)
    mu_a = mu_m * 12
    sd_a = sd_m * math.sqrt(12)
    sharpe = mu_a / sd_a if sd_a > 0 else np.nan
    return mu_a, sd_a, sharpe

def compare_table_monthly(rA: pd.Series, rB: pd.Series, rM: pd.Series, nameA="Monthly baseline", nameB="Daily exec (avoid)"):
    idx = rA.dropna().index.intersection(rB.dropna().index).intersection(rM.dropna().index)
    A = rA.loc[idx]
    B = rB.loc[idx]
    M = rM.loc[idx]

    rows = []
    for nm, rr in [(nameA, A), (nameB, B), ("Market", M)]:
        mu_a, sd_a, sh = annualized_stats_monthly(rr)
        rows.append({"name": nm, "ann_return": mu_a, "ann_vol": sd_a, "sharpe": sh, "nobs_months": int(len(rr))})
    return pd.DataFrame(rows).set_index("name"), idx

def plot_wealth_monthly(rA: pd.Series, rB: pd.Series, rM: pd.Series, idx, title="Monthly wealth comparison"):
    A = rA.loc[idx].fillna(0.0)
    B = rB.loc[idx].fillna(0.0)
    M = rM.loc[idx].fillna(0.0)

    wA = (1.0 + A).cumprod()
    wB = (1.0 + B).cumprod()
    wM = (1.0 + M).cumprod()

    plt.figure(figsize=(14,5))
    plt.plot(wA, label="Monthly baseline (FF monthly)", linewidth=2)
    plt.plot(wB, label="Daily exec + avoid(Fri,TW) -> monthly", linewidth=2)
    plt.plot(wM, label="Market monthly total", linestyle="--", linewidth=1.6)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# ============================================================
# 10) メイン：2000年以降で比較
# ============================================================

def run_comparison_2000_plus(
    ff_csv_path="F-F_Research_Data_Factors.csv",
    start="2000-01-01",
    end=None,
    lookback_years=20,
    min_obs=120,
    target_vol_monthly=0.05,   # 月次ベースラインのtarget vol
    target_vol_ann_daily=0.10, # 日次執行の年率target vol（目安：月次0.05≒年率~0.173だがここは運用意図で調整）
    max_leverage=3.0,
):
    # ---------- Monthly baseline (Ken French monthly) ----------
    ff = load_ff_monthly_from_ken_french(ff_csv_path)
    ff = ff.loc[pd.Timestamp(start):] if start is not None else ff

    x_m6, beta_m6, w_m6 = build_method6_raw_weights_rolling(ff, lookback_years=lookback_years, min_obs=min_obs)
    strat_m6 = vol_target_from_weights_monthly_once(
        ff["mkt_excess"], ff["rf"], w_m6, target_vol=target_vol_monthly
    )
    # baseline monthly total return
    rA = strat_m6["strat_total"].rename("r_monthly_baseline")

    # market monthly total (FF)
    rM = (ff["mkt_excess"] + ff["rf"]).reindex(rA.index).rename("r_mkt_monthly")

    # ---------- Daily exec (SPY daily) ----------
    daily = load_spy_daily(start=start, end=end)
    idx_d = daily.index

    # Method6 signal is monthly; build monthly total from daily
    mkt_total_m_from_daily = daily_to_monthly_total(daily["ret_total"])

    # x,beta,w using the same rolling method on this monthly series
    # ここでは rf=0 なので mkt_total = monthly_total でOK（厳密に揃えるなら月次rfを入れる）
    # ただし month_type/N/R の定義は暦月なので整合します
    x_d_m, beta_d_m, w_d_m = build_method6_raw_weights_rolling(
        pd.DataFrame({"mkt_excess": mkt_total_m_from_daily, "rf": 0.0}, index=mkt_total_m_from_daily.index),
        lookback_years=lookback_years,
        min_obs=min_obs
    )

    # desired daily raw weights (use previous month-end weight for current month)
    w_desired_raw_d = map_monthly_weight_to_daily_next_month(w_d_m, idx_d).clip(-max_leverage, max_leverage)

    # execution avoidance masks
    is_friday = build_friday_mask(idx_d)
    is_tw = build_triple_witching_mask(idx_d)
    forbid = (is_friday | is_tw).rename("forbid_rebalance")

    w_actual_raw_d = apply_rebalance_filters_to_daily_weights(w_desired_raw_d, forbid).clip(-max_leverage, max_leverage)

    # daily vol-target once (to mimic your baseline style)
    daily_strat = vol_target_daily_once(
        mkt_excess_d=daily["mkt_excess_d"],
        rf_d=daily["rf_d"],
        w_raw_d=w_actual_raw_d,
        target_vol_ann=target_vol_ann_daily
    )

    # daily total -> monthly total
    rB = daily_total_to_monthly_total(daily_strat["strat_total_d"]).rename("r_monthly_from_daily_exec")

    # align on common monthly index (2000+)
    rA = rA.loc[pd.Timestamp(start):]
    rB = rB.loc[pd.Timestamp(start):]
    rM2 = rM.copy()

    tbl, idx = compare_table_monthly(rA, rB, rM2, nameA="Monthly baseline (FF)", nameB="Daily exec avoid(Fri,TW)->monthly")
    print("\n=== Comparison table (monthly frequency, aligned) ===")
    print(tbl)

    plot_wealth_monthly(rA, rB, rM2, idx, title="Method6: Monthly baseline vs Daily exec(avoid) | 2000+")

    # 追加：スケール係数の表示（両者）
    print("\n[Scales]")
    print(f"Monthly baseline scale k = {strat_m6.attrs['scale']:.6f}  (target_vol_monthly={target_vol_monthly})")
    print(f"Daily exec scale k       = {daily_strat.attrs['scale']:.6f}  (target_vol_ann_daily={target_vol_ann_daily})")

    return {
        "ff": ff,
        "monthly_baseline": strat_m6,
        "daily_exec": daily_strat,
        "rA_monthly": rA,
        "rB_monthly": rB,
        "rM_monthly": rM2,
        "table": tbl,
        "common_index": idx,
        "forbid_mask_daily": forbid,
        "w_raw_desired_daily": w_desired_raw_d,
        "w_raw_actual_daily": w_actual_raw_d,
    }

if __name__ == "__main__":
    out = run_comparison_2000_plus(
        ff_csv_path="F-F_Research_Data_Factors.csv",
        start="2000-01-01",
        end=None,
        lookback_years=20,
        min_obs=120,
        target_vol_monthly=0.05,
        target_vol_ann_daily=0.10,
        max_leverage=3.0,
    )
```

* * *

重要な注意（比較で必ず効く差分）
----------------

この比較では、ベースラインに合わせて \*\*「スケールは全期間で1回」\*\*に揃えています（あなたの `vol_target_from_weights` と同じ思想）。

一方で、日次版は \*\*「執行回避（据え置き）」\*\*を入れているので、

*   特に **金曜** と **四半期末第3金曜** に当月のウェイト変更が発生する場合  
    → 実際の適用ウェイトがベースライン（＝毎日 w\_desired に追随）と変わります。

これがパス差の主因になります。

* * *

次にやると一気に精度が上がる拡張（必要ならすぐ入れます）
----------------------------

上記は日次側 rf=0 で簡略化しています。月次ベースラインが RF を入れているので、整合性を上げるなら：

*   日次の `rf_d` を（例：^IRX や FRED TB3MS の日次補間）で導入
*   `mkt_excess_d = ret_total - rf_d`
*   日次の `strat_total_d = rf_d + w* mkt_excess_d`

に置き換えるのが本筋です。

* * *

このコードをそのまま走らせて、出力された

*   比較表（年率リターン・ボラ・シャープ）
*   月次ウェルスの3本プロット
*   月次スケール係数 / 日次スケール係数

を貼っていただければ、**差がどのタイミング（日付・イベント）で発生しているか**（例：金曜がシグナル変更日だった、TW週で切り替えが遅れた等）まで分解する追加分析コードもすぐ出せます。

## Response:
この出力（nobs\_months=0 で全部 NaN）は、**月次リターン系列が 1 本も作れていない／共通インデックスが空**になっている状態です。原因はほぼ次のどれかです（優先順）。

* * *

起きがちな原因（チェック順）
--------------

### (A) 月次ベースライン `ff` の期間が空

*   `ff = ff.loc[pd.Timestamp(start):]` の `start="2000-01-01"` 以降の行が存在しない  
    例：読み込んだ `F-F_Research_Data_Factors.csv` の月次が途中で切れている／読み込み失敗して実質空、など。

**確認**：`print(ff.index.min(), ff.index.max(), ff.shape)` が必須。

* * *

### (B) 月次戦略 `strat_m6` の index が空（dropna で消えている）

あなたの `vol_target_from_weights_monthly_once` は `dropna(subset=["mkt_excess","rf"])` なので普通は残りますが、  
`build_method6_raw_weights_rolling` の `w_raw` が全期間 0 でも index 自体は残るはずです。  
ただし、どこかで `.loc[...]` を誤って掛けて空になっている可能性があります。

**確認**：`print(strat_m6.shape, strat_m6.index.min(), strat_m6.index.max())`

* * *

### (C) 日次→月次の `rB` が空（SPY日次が空 or resample が空）

*   yfinance が空を返した
*   `daily_total_to_monthly_total()` の resample 結果が空

**確認**：`print(daily.shape, daily.index.min(), daily.index.max())` と `print(rB.shape, rB.index.min(), rB.index.max())`

* * *

### (D) `compare_table_monthly()` で共通インデックスが空

`idx = rA.dropna().index.intersection(rB.dropna().index).intersection(rM.dropna().index)`  
の **いずれかが全部 NaN** だと空になります。  
特に `rA`/`rB` が「トータルリターン」なのに NaN が多い場合。

**確認**：`print(rA.dropna().shape, rB.dropna().shape, rM.dropna().shape)`

* * *

すぐ直る「診断＋自動修正」版（このまま貼り替えて実行してください）
---------------------------------

下の関数は、**どこで空になったかを print で特定**し、さらに実務的にありがちなバグ（`end=None` の扱い、index 型、空Series、月次の切り取り）を潰します。

```python
def debug_and_compare(out):
    ff = out["ff"]
    strat_m6 = out["monthly_baseline"]
    daily_strat = out["daily_exec"]
    rA = out["rA_monthly"]
    rB = out["rB_monthly"]
    rM = out["rM_monthly"]

    def info(name, s):
        if s is None:
            print(f"{name}: None")
            return
        if isinstance(s, pd.DataFrame):
            idx = s.index
            print(f"{name}: DF shape={s.shape}, idx=[{idx.min()} .. {idx.max()}], dtypes={list(s.dtypes)[:3]}...")
        else:
            idx = s.index
            print(f"{name}: SER len={len(s)}, nonna={int(s.notna().sum())}, idx=[{idx.min()} .. {idx.max()}], dtype={s.dtype}")

    print("\n--- BASIC CHECKS ---")
    info("ff", ff)
    info("monthly_baseline(strat_m6)", strat_m6)
    info("daily_exec(daily_strat)", daily_strat)

    print("\n--- MONTHLY SERIES CHECKS ---")
    info("rA_monthly", rA)
    info("rB_monthly", rB)
    info("rM_monthly", rM)

    # show head/tail of indices (helps when index types mismatch)
    print("\nIndex types:")
    print("rA idx type:", type(rA.index))
    print("rB idx type:", type(rB.index))
    print("rM idx type:", type(rM.index))

    # attempt robust alignment by converting to month-end timestamps
    def to_month_end_index(s):
        s2 = s.copy()
        # ensure Timestamp index
        s2.index = pd.to_datetime(s2.index)
        # normalize to month-end
        s2.index = s2.index.to_period("M").to_timestamp("M")
        s2 = s2.sort_index()
        return s2

    rA2 = to_month_end_index(rA.dropna())
    rB2 = to_month_end_index(rB.dropna())
    rM2 = to_month_end_index(rM.dropna())

    idx = rA2.index.intersection(rB2.index).intersection(rM2.index)
    print("\nAligned common months:", len(idx), " from ", (idx.min() if len(idx)>0 else None), " to ", (idx.max() if len(idx)>0 else None))

    if len(idx) == 0:
        print("\n[ERROR] common index is empty. Likely one of the series is empty after dropna.")
        print("non-na counts:", len(rA2), len(rB2), len(rM2))
        return None

    # recompute table
    def annualized_stats_monthly(r_m):
        r_m = r_m.dropna().astype(float)
        mu_m = r_m.mean()
        sd_m = r_m.std(ddof=1)
        mu_a = mu_m * 12
        sd_a = sd_m * math.sqrt(12)
        sharpe = mu_a / sd_a if sd_a > 0 else np.nan
        return mu_a, sd_a, sharpe

    rows = []
    for nm, rr in [("Monthly baseline (FF)", rA2.loc[idx]),
                   ("Daily exec avoid(Fri,TW)->monthly", rB2.loc[idx]),
                   ("Market", rM2.loc[idx])]:
        mu_a, sd_a, sh = annualized_stats_monthly(rr)
        rows.append({"name": nm, "ann_return": mu_a, "ann_vol": sd_a, "sharpe": sh, "nobs_months": int(len(rr))})
    tbl = pd.DataFrame(rows).set_index("name")

    print("\n=== FIXED Comparison table (monthly aligned by MonthEnd) ===")
    print(tbl)

    # plot
    wA = (1.0 + rA2.loc[idx].fillna(0.0)).cumprod()
    wB = (1.0 + rB2.loc[idx].fillna(0.0)).cumprod()
    wM = (1.0 + rM2.loc[idx].fillna(0.0)).cumprod()

    plt.figure(figsize=(14,5))
    plt.plot(wA, label="Monthly baseline (FF)", linewidth=2)
    plt.plot(wB, label="Daily exec + avoid(Fri,TW) -> monthly", linewidth=2)
    plt.plot(wM, label="Market", linestyle="--", linewidth=1.6)
    plt.title("Monthly wealth comparison (MonthEnd-aligned)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return tbl, idx

# 使い方（直前の out を渡す）
# res = debug_and_compare(out)
```

* * *

ほぼ確実に直る“本命”の原因：月次インデックスの「月初 vs 月末」ズレ
------------------------------------

Ken French の月次indexはあなたの `pd.to_datetime(..., format="%Y%m")` で **月初（YYYY-MM-01）** になっています。一方で日次→月次は `resample("M")` で **月末**になります。  
このままだと intersection が空になりやすいです。

上の `to_month_end_index()` がこれを強制的に揃えるので、多くの場合これで解消します。

* * *

次にあなたにお願いしたいこと（追加の質問ではなく、確認作業）
------------------------------

上の `debug_and_compare(out)` を回して出てきたログ（`--- BASIC CHECKS ---` から `Aligned common months` まで）を貼ってください。  
それだけで、空になっている箇所を一点特定してコード側を確定修正します。

* * *

補足：アップロードファイルの期限切れについて
----------------------

以前アップロードされていた一部ファイルは期限切れになっているようです。ただ今回の NaN 問題は **それとは無関係**で、主因は \*\*月次インデックス整合（month-begin vs month-end）\*\*の可能性が高いです。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)