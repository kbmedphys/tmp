# プログラム実装依頼

**User:** Anonymous (kbmedphys@gmail.com)  
**Created:** 1/7/2026 18:44:31  
**Updated:** 1/7/2026 22:16:59  
**Exported:** 1/7/2026 22:21:10  
**Link:** [https://chatgpt.com/c/695e2adf-2f58-8321-9f78-fa5acd312ac4](https://chatgpt.com/c/695e2adf-2f58-8321-9f78-fa5acd312ac4)  

## Response:


## Response:
思考時間: 2m 27s

以下では、

1.  **「月次でそのまま計算した系列」と「日次で執行してから累積した系列」でプロットがズレる理由**（あなたの現行コードで起きているズレの“主要因”）
2.  **PDF（hhaf020.pdf）の time-series strategy（Method 6 相当）の仕様に沿った実装**
3.  **ターゲット・ボラティリティ（Volatility Targeting）を“関数として追記”**（月次・日次の両方で実行）

を、あなたのコードに“継ぎ足す”形で整理して提示します。

* * *

1\. 月次版と日次執行版のプロットがズレる主因（実装上の論点）
--------------------------------

ズレは複数要因が重なりますが、実務的に効いているのは次の3点です。

### (A) **「月次のリターンに w を掛ける」vs「日次で w を掛けて複利で積む」では一致しない**

あなたの月次プロットは

*   月次：`(1 + w_raw * monthly_rets).cumprod()`

ですが、これは「その月の**月次リターン R\_m**に、月初から月末まで一定のエクスポージャ w を“線形に”掛けた」扱いです。

一方、日次執行は

*   日次：`(1 + strategy * rets).cumprod()`

で、実態は「日次リターン r\_d に w を掛けた**日次ポートフォリオ収益**を複利で積む」ことになります。

月次リターン  $R_m=\prod_d(1+r_d)-1$  なので、一般に

$$
\prod_d(1+w r_d) - 1 \neq w\left(\prod_d(1+r_d)-1\right)
$$

特に **|w| が大きい**（ボラターゲットや回帰係数でレバが立つ）ほど乖離します。  
つまり、**月次で“w×月次リターン”にしてしまうと、日次執行の複利と一致しません**。

> 対処：比較するなら、
> 
> *   (i) 月次戦略も「日次リターンに w を掛けて」日次で複利積算する、または
> *   (ii) 日次執行戦略の「日次ポートフォリオ収益」を月次に集計して比較する  
>     のどちらかに揃えるべきです。
>     

* * *

### (B) シグナルのタイミング（t−1月末で作って t月に適用）のズレ

PDFの time-series strategy は、

*   **月末 t−1 時点で**シグナル  $x_{t-1}$  を作り、
*   **月 t の市場リターン**を予測する回帰を更新し、
*   **月 t のポジション**（重み）を  $c_t x_{t-1}$  として取る

という「月次リバランス」構造です（詳細は Appendix の説明）。  
具体的に「次月が newsy なら符号を反転」などのルールを含みます。

hhaf020

あなたの日次ループでは、

*   月末で `current_strategy = beta_last * (S_last - mean(S))` を作り、
*   **各日で** `sign = -1 if newsy else +1` を掛けて `strategy = sign * current_strategy`

としており、**「符号反転を x の構築に入れる」月次版と、「毎日 sign を掛ける」日次版で整合が崩れやすい**です。  
（特に、どの時点の month\_type を使って反転するか：t月か t+1月か、がブレると結果が平気で変わります。）

> 対処：\*\*「月末で決めた w を、翌月（次の月末まで）一定に保つ」\*\*形に統一し、  
> “符号反転”も **月末で確定した月次 w の中に取り込む**のが安全です。

* * *

### (C) 月末の定義（Calendar month end “M” vs Trading month end）

`resample("M")` は「暦上の月末」です。一方、実際のデータは営業日しかありません。  
日次側で「その月の最終営業日」を `groupby(to_period("M")).max()` で取っているので、  
月次側の resample と微妙な非整合が出ることがあります（特に欠損や祝日周り）。

> 対処：月次化は `BME`（business month end）に寄せるのが無難です。

* * *

2\. PDFの time-series strategy（Method 6 相当）の要点（実装で守るべき仕様）
--------------------------------------------------------

PDFの記述（A.3 Time-Series Strategy）では：

*   過去4つの newsy months（Jan/Apr/Jul/Oct）のトータルリターンを用い、
*   expanding mean でデ-ミーンし、
*   次月が newsy なら符号を反転してシグナル化し、
*   制約回帰  $mkt_t = \beta x_{t-1} + 1\cdot \overline{mkt}_{t-1} + \varepsilon_t$  を行い（平均項の係数を1に固定）、
*   予測は  $c_t x_t + \overline{mkt}_t$ 、ポジションは ** $c_t x_t$ **（平均ゼロ付近）、
*   最後に **市場と同じ月次ボラ（例：5.34%/month）になるよう定数でスケール**する
    hhaf020

さらに Table A3 の注記で「市場ボラ（5.34%/month）と同じになるようスケール」や、look-ahead への注意も書かれています。

hhaf020

あなたの実装は「平均項を y = mkt - mean にして定数回帰を消す」という近い形ですが、**“係数=1固定の平均項”を明示していない**ので、PDF通りにするなら「回帰側で平均項を足す」方が一致しやすいです。

* * *

3\. 追記する関数（ターゲット・ボラ＋月次/日次の整合比較）
-------------------------------

下のコードは、あなたのコードに“追記”して使えるように書いています。

*   `load_prices_csv_or_yf()`：prices.csv を優先して読み込み（同じ ^SPX を使う）
*   `to_monthly_returns()`：BME（最終営業日）で月次化
*   `method6_monthly_weight()`：PDFの構造に寄せた **月次のポジション w\_t（= c\_t x\_t）** を作る
*   `daily_execute_monthly_weight()`：w\_t を「月内一定」として日次で執行して複利で積む
*   `vol_target_overlay()`：ターゲットボラ（rolling または expanding）でスケーリング（max leverage 付き）
*   `run_both_and_plot()`：月次版と日次執行版を同じ土俵（日次複利 or 月次集計）で比較

> 重要：**比較のため、月次版も“日次に展開して日次複利”で描けるようにしています。**  
> これで (A) のズレ要因を潰せます。

```python
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# ============================================================
# 0) Data loader (prices.csv を優先)
# ============================================================
def load_prices_csv_or_yf(
    ticker="^SPX",
    csv_path="/mnt/data/prices.csv",
    start="1950-01-01",
    end=None,
    use_yfinance_if_missing=False,
):
    """
    prices.csv があるならそれを使う（推奨）。
    csv は columns: ['Date', '^SPX'] の想定。
    """
    if end is None:
        end = pd.Timestamp.today().strftime("%Y-%m-%d")

    try:
        df = pd.read_csv(csv_path, parse_dates=["Date"]).set_index("Date").sort_index()
        px = df[ticker].dropna()
        px = px.loc[(px.index >= pd.Timestamp(start)) & (px.index <= pd.Timestamp(end))]
        return px
    except Exception as e:
        if not use_yfinance_if_missing:
            raise
        import yfinance as yf
        px = yf.download(ticker, start=start, end=end)["Close"].dropna()
        if isinstance(px, pd.DataFrame):
            px = px[ticker]
        return px

def to_returns(px: pd.Series) -> pd.Series:
    px = px.sort_index()
    return px.pct_change().dropna()

def to_monthly_returns(rets_d: pd.Series, month_end="BME") -> pd.Series:
    """
    日次 -> 月次（最終営業日基準）
    month_end:
      - "BME" (Business Month End) 推奨
      - 互換のため pandas の version によって "BM" を使う場合あり
    """
    # 月次リターン（複利）
    return rets_d.resample(month_end).apply(lambda x: (1 + x).prod() - 1)

# ============================================================
# 1) Month type (N,R,3)
# ============================================================
def classify_month_type(index: pd.DatetimeIndex) -> pd.Series:
    """
    月の種類:
      month % 3 == 1 -> 'N'
      month % 3 == 2 -> 'R'
      month % 3 == 0 -> '3'
    """
    m = index.month % 3
    out = pd.Series(index=index, dtype="object")
    out[m == 1] = "N"
    out[m == 2] = "R"
    out[m == 0] = "3"
    return out

# ============================================================
# 2) Method 6 monthly weight (PDF 構造寄せ)
# ============================================================
def build_signal_x_from_monthly_mkt(mkt_m: pd.Series) -> pd.Series:
    """
    PDFの説明に合わせて:
      - newsy months の過去4つの合計（合計対象は "past four newsy months"）
      - expanding mean でデ-ミーン
      - 次月が newsy なら符号反転（あなたの元コードは「当月が newsy」などが混じりやすいので、
        ここで「t に適用する x_{t-1}」という発想に寄せる）
    実装上、月次インデックス t で定義する x_t を返す（t 月に入る前に確定している想定）。
    """
    idx = mkt_m.index
    mt = classify_month_type(idx)
    is_newsy = (mt == "N")

    # newsy months のみ抜き出し
    news = mkt_m[is_newsy]

    # S_t: その時点までの newsy months の直近4つの合計（定義の近似）
    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news.loc[news.index <= t]
        S.loc[t] = past.iloc[-4:].sum() if len(past) >= 4 else np.nan

    # expanding mean of S（t-1 まででの平均を使う）
    S_bar = S.expanding().mean().shift(1)

    # 「次月が newsy なら符号反転」：t+1 が newsy かどうかで t の符号を決める
    # （PDF記述: "flip the sign if month t is newsy" という表現と
    #  "flip the sign if the next month is newsy" という注記があり得るので、
    #  実装の整合を優先し、"tに投資するために t-1で確定した情報" という観点で統一）
    is_newsy_next = is_newsy.shift(-1).reindex(idx)

    sign = np.where(is_newsy_next.fillna(False), -1.0, 1.0)
    x = sign * (S - S_bar)
    return x

def method6_monthly_weight(
    mkt_m: pd.Series,
    min_obs=120,
    use_constrained_mean_term=True,
) -> pd.Series:
    """
    月次で w_t = c_t * x_t を作る。
    - 回帰は expanding で推定
    - PDFは mean項の係数を1に固定し、定数項の代わりに expanding mean を使う構造:contentReference[oaicite:3]{index=3}
    """
    mkt_m = mkt_m.dropna().sort_index()

    # expanding mean (t-1までの平均)
    mu = mkt_m.expanding().mean().shift(1)

    # signal x_t
    x = build_signal_x_from_monthly_mkt(mkt_m)

    # 回帰ターゲット
    if use_constrained_mean_term:
        # mkt_t = beta * x_{t-1} + 1 * mu_{t-1} + eps
        # => (mkt_t - mu_{t-1}) = beta * x_{t-1} + eps
        y = (mkt_m - mu)
        X = x.shift(1)
    else:
        # あなたの元実装に近い形（参考）
        y = mkt_m - mu
        X = x.shift(1)

    # expanding OLS: y_t = beta_t * X_t
    beta = pd.Series(index=mkt_m.index, dtype=float)
    for t in mkt_m.index:
        mask = (mkt_m.index <= t) & y.notna() & X.notna()
        if mask.sum() < min_obs:
            beta.loc[t] = np.nan
            continue
        res = sm.OLS(y.loc[mask].values, X.loc[mask].values).fit()
        beta.loc[t] = res.params[0]

    # weight: w_t = beta_t * x_t （月末で確定して翌月に使うなら shift で調整）
    w = (beta * x).fillna(0.0)
    return w

# ============================================================
# 3) Daily execution of monthly weights (month内一定)
# ============================================================
def daily_execute_monthly_weight(
    rets_d: pd.Series,
    w_m: pd.Series,
    month_end="BME",
) -> pd.Series:
    """
    月次 weight w_m を、日次に展開して執行。
    - 各月の w を、その月の全営業日に一定で適用（= 月次リバランスの忠実な日次執行）
    - 日次ポートフォリオ収益: r_p,d = w_d * r_mkt,d
    """
    rets_d = rets_d.dropna().sort_index()
    w_m = w_m.dropna().sort_index()

    # 日次を月次キーに落とす（BMEで月を定義）
    month_key_d = rets_d.index.to_period("M")
    month_key_m = w_m.index.to_period("M")

    # 各日付に対応する月の w を割当
    w_d = pd.Series(index=rets_d.index, dtype=float)
    w_map = pd.Series(w_m.values, index=month_key_m)
    w_d[:] = month_key_d.map(w_map).astype(float)

    w_d = w_d.fillna(0.0)
    rp_d = w_d * rets_d
    return rp_d

# ============================================================
# 4) Volatility targeting overlay
# ============================================================
def vol_target_overlay(
    rp: pd.Series,
    target_vol,
    lookback=36,
    mode="rolling",
    annualize_factor=None,
    max_leverage=3.0,
    min_vol=1e-6,
):
    """
    rp: 戦略リターン系列（頻度は rp の index 次第）
    target_vol: ターゲット（同じ頻度の標準偏差ベースで指定）
                例）月次なら 0.0534（=5.34%/month）など:contentReference[oaicite:4]{index=4}
                日次なら年率targetを与えて annualize_factor を設定しても良い
    annualize_factor:
        - 月次: 12
        - 日次: 252
        など。target_vol を「年率」で与えるなら、ここで整合させる。
    mode:
        - "rolling": rolling std
        - "expanding": expanding std（look-ahead回避の注記に対応しやすい）:contentReference[oaicite:5]{index=5}
    戻り:
        scaled_rp: ボラターゲット後のリターン
        scale: 各時点のスケール（レバレッジ係数）
        vol_hat: 推定ボラ
    """
    rp = rp.dropna().sort_index()

    if mode == "rolling":
        vol_hat = rp.rolling(lookback, min_periods=max(5, lookback // 3)).std()
    elif mode == "expanding":
        vol_hat = rp.expanding(min_periods=max(20, lookback)).std()
    else:
        raise ValueError("mode must be 'rolling' or 'expanding'")

    # 年率に合わせる場合
    if annualize_factor is not None:
        vol_hat_ann = vol_hat * np.sqrt(annualize_factor)
        scale = (target_vol / np.maximum(vol_hat_ann, min_vol))
    else:
        scale = (target_vol / np.maximum(vol_hat, min_vol))

    # 将来情報を使わない：t のポジションは t-1 の vol_hat で決める（安全側）
    scale = scale.shift(1).fillna(0.0)

    # レバ上限
    scale = scale.clip(lower=-max_leverage, upper=max_leverage)

    scaled_rp = scale * rp
    return scaled_rp, scale, vol_hat

# ============================================================
# 5) Run both monthly and daily, aligned comparison plots
# ============================================================
def run_both_and_plot(
    px: pd.Series,
    start_plot="2000-01-01",
    start_est="1993-12-31",
    min_obs=120,
    month_end="BME",
    vol_target_monthly=0.0534,  # PDFで言及される市場月次ボラ例:contentReference[oaicite:6]{index=6}
    do_vol_target=True,
):
    rets_d = to_returns(px)
    mkt_m = to_monthly_returns(rets_d, month_end=month_end)

    # --- 月次 w (Method6) ---
    w_m = method6_monthly_weight(mkt_m, min_obs=min_obs)

    # 月次の「そのまま」戦略リターン（線形）ではなく、日次に展開して日次複利で比較する
    rp_d_from_monthly = daily_execute_monthly_weight(rets_d, w_m, month_end=month_end)

    # --- 参考：月次で戦略リターンを作りたい場合（正しい月次集計は日次ポート収益を月次に畳む） ---
    rp_m_from_daily = rp_d_from_monthly.resample(month_end).apply(lambda x: (1 + x).prod() - 1)

    # --- ボラターゲット（PDFの「市場と同じボラへスケール」を一般化） ---
    if do_vol_target:
        # 月次でターゲットを合わせる（rolling 36 months など）
        # 「月次でスケールを決めて日次に展開」するため、まず月次rpを作って月次でscaleを推定
        rp_m = rp_m_from_daily.copy()
        rp_m_vt, scale_m, volhat_m = vol_target_overlay(
            rp_m,
            target_vol=vol_target_monthly,
            lookback=36,
            mode="expanding",      # look-ahead回避の注記に沿わせるなら expanding が無難:contentReference[oaicite:7]{index=7}
            annualize_factor=None,
            max_leverage=3.0,
        )

        # 月次scaleを日次に展開して日次rpに適用
        scale_d = pd.Series(index=rets_d.index, dtype=float)
        scale_map = pd.Series(scale_m.values, index=scale_m.index.to_period("M"))
        scale_d[:] = rets_d.index.to_period("M").map(scale_map).astype(float)
        scale_d = scale_d.fillna(0.0)

        rp_d_from_monthly_vt = scale_d * rp_d_from_monthly
    else:
        rp_d_from_monthly_vt = None

    # --- プロット（同じ土俵：日次複利） ---
    start_plot = pd.Timestamp(start_plot)
    wealth_base = (1 + rp_d_from_monthly.loc[start_plot:]).cumprod()

    plt.figure(figsize=(10, 5))
    plt.plot(wealth_base, label="Method6 (monthly w, executed daily)")

    if rp_d_from_monthly_vt is not None:
        wealth_vt = (1 + rp_d_from_monthly_vt.loc[start_plot:]).cumprod()
        plt.plot(wealth_vt, label="Method6 + VolTarget (monthly scale, executed daily)")

    plt.legend()
    plt.title("Wealth (daily-compounded, aligned)")
    plt.show()

    return {
        "rets_d": rets_d,
        "mkt_m": mkt_m,
        "w_m": w_m,
        "rp_d": rp_d_from_monthly,
        "rp_m": rp_m_from_daily,
        "rp_d_vt": rp_d_from_monthly_vt,
    }

# =========================
# Example run
# =========================
# px = load_prices_csv_or_yf(ticker="^SPX", csv_path="/mnt/data/prices.csv", use_yfinance_if_missing=False)
# out = run_both_and_plot(px, start_plot="2000-01-01", do_vol_target=True)
```

* * *

4\. これで「ズレ」はどう解消されるか（確認ポイント）
----------------------------

上の `run_both_and_plot()` は、比較を **“日次複利”に統一**しています。  
この状態で、

*   旧：`(1 + w_raw * monthly_rets).cumprod()`
*   新：`daily_execute_monthly_weight()` で作った日次戦略収益を cumprod

を比べると、旧コードで見えていたズレの多くは \*\*「月次で線形に掛けたことによるズレ」\*\*だった、と切り分けできます。

* * *

5\. ターゲットボラ実装の考え方（PDFとの対応）
--------------------------

PDFでは「定数でスケールして市場と同じ月次ボラにする」

hhaf020

、およびその先読み懸念への注記

hhaf020

があるので、実装としては：

*   **推定ボラ（expanding or rolling）でスケール係数を決定**
*   \*\*係数は 1期遅らせて適用（shift(1)）\*\*して先読みを回避
*   **max leverage を設定**

が、研究用途でも実務用途でも一番安全です。

* * *

こちらからの最小の確認（1点だけ）
-----------------

ターゲットボラの指定をどちらで合わせたいですか？

*   (i) **月次ターゲット**（例：PDFに合わせて 0.0534 / month）
*   (ii) **年率ターゲット**（例：10%/year など。日次なら252、月次なら12で年率換算）

現状コードは (i) 月次ターゲット（0.0534/month）で書いています。年率で合わせたい場合は、その前提に合わせて `vol_target_overlay()` の `annualize_factor` と `target_vol` を調整します。

2/2

## Response:
承知しました。やりたいことは明確で、実装も筋が良いです。

*   **realized volatility（推定ボラ）は日次リターンから計算**
*   **target volatility は「月次」で与える**
*   **スケーリング係数は“月次で一定”**（＝月内は固定）にして、日次での過剰変動を抑える

という設計にします。これにより「日次で毎日レバを変えてしまうことによる過剰なターンオーバー／ノイズ追随」を抑制できます。

以下に、あなたの既存コードに“関数として付け足す”形で提示します（Method6 の rp\_d を受けて、月次ターゲットでスケールした日次 rp\_d\_vt を返す）。

* * *

1) 日次 realized vol → 月次ターゲットで月次スケール（=月内固定）
------------------------------------------

### 実装方針

*   入力：**日次の戦略リターン** `rp_d`（例：`rp_d = w_d * rets_d`）
*   realized vol 推定：
    *   「その月の realized vol」は、\*\*直近 L 営業日（例：63日=約3か月）\*\*の `rp_d` から推定
    *   ただし **月内固定の係数**にするため、月末時点で推定して翌月に適用（`shift(1)`）
*   スケール係数：
    *   `scale_m = target_vol_monthly / vol_hat_monthly`
    *   レバ上限で clip
*   日次への展開：
    *   その月の全営業日に同じ `scale_m` を適用

* * *

2) 追加する関数（そのまま貼り付け可）
--------------------

```python
import numpy as np
import pandas as pd

def daily_realized_vol_to_monthly_scale(
    rp_d: pd.Series,
    target_vol_monthly: float,
    lookback_days: int = 63,         # 例: 3ヶ月程度（21*3）
    month_end: str = "BME",
    vol_floor: float = 1e-6,
    max_leverage: float = 3.0,
    use_ewma: bool = False,
    ewma_lambda: float = 0.94,
):
    """
    日次リターン rp_d から realized vol を推定し、
    target_vol_monthly（=月次）に合わせて「月次で一定のスケール係数」を作る。

    重要:
    - 係数は月末で確定 → 翌月に適用（shift(1)）して先読み回避。
    - 月内は一定の scale_d を適用し、日次での過剰な変動を抑える。

    Returns
    -------
    rp_d_vt : pd.Series
        月次固定スケーリング後の日次リターン
    scale_d : pd.Series
        日次に展開されたスケーリング係数（月内一定）
    scale_m : pd.Series
        月次スケーリング係数（各月末 index）
    volhat_m : pd.Series
        月次換算の推定ボラ（各月末 index）
    """
    rp_d = rp_d.dropna().sort_index()

    # --- 日次 realized vol 推定（rolling or EWMA）---
    if use_ewma:
        # EWMA variance: var_t = lambda*var_{t-1} + (1-lambda)*r_{t-1}^2
        r2 = rp_d.pow(2)
        var = pd.Series(index=rp_d.index, dtype=float)
        var.iloc[0] = r2.iloc[0]
        for i in range(1, len(r2)):
            var.iloc[i] = ewma_lambda * var.iloc[i-1] + (1 - ewma_lambda) * r2.iloc[i-1]
        vol_d = np.sqrt(var)
    else:
        vol_d = rp_d.rolling(
            lookback_days, min_periods=max(20, lookback_days // 3)
        ).std()

    # --- 「月次換算」へ：月次targetに合わせるため sqrt(営業日数) で換算 ---
    # 月次ボラは概ね sqrt(21) * 日次ボラ（ローカルに営業日数が変わるのが気になるなら 21固定が無難）
    ann_days_in_month = 21.0
    vol_m_equiv = vol_d * np.sqrt(ann_days_in_month)

    # --- 月末（営業日ベース）にサンプリング ---
    volhat_m = vol_m_equiv.resample(month_end).last()

    # スケール係数（月次）
    scale_m = target_vol_monthly / np.maximum(volhat_m, vol_floor)

    # 先読み回避：t月のscaleは t-1月末の推定で決める
    scale_m = scale_m.shift(1).fillna(0.0)

    # レバ上限
    scale_m = scale_m.clip(lower=-max_leverage, upper=max_leverage)

    # --- 月次 scale を日次に展開（月内一定）---
    scale_map = pd.Series(scale_m.values, index=scale_m.index.to_period("M"))
    scale_d = pd.Series(index=rp_d.index, dtype=float)
    scale_d[:] = rp_d.index.to_period("M").map(scale_map).astype(float)
    scale_d = scale_d.fillna(0.0)

    rp_d_vt = scale_d * rp_d
    return rp_d_vt, scale_d, scale_m, volhat_m
```

* * *

3) 既存フローへの組み込み例（Method6 の rp\_d をスケール）
--------------------------------------

あなたの流れ（前回提示した構成）に合わせると、例えばこうです。

```python
# 1) Method6 の「月次wを日次執行」した日次戦略リターン
rp_d = daily_execute_monthly_weight(rets_d, w_m, month_end="BME")

# 2) 日次 realized vol で推定 → 月次ターゲットで月内固定スケール
target_vol_monthly = 0.0534  # 例: 5.34%/month
rp_d_vt, scale_d, scale_m, volhat_m = daily_realized_vol_to_monthly_scale(
    rp_d,
    target_vol_monthly=target_vol_monthly,
    lookback_days=63,       # 平滑化を強くしたいなら 63～126 推奨
    month_end="BME",
    max_leverage=3.0,
    use_ewma=False,         # さらに滑らかにしたいなら True + ewma_lambda調整
)

# 3) プロット（日次複利）
plt_date = "2000-01-01"
plt.figure(figsize=(10,5))
plt.plot((1 + rp_d.loc[plt_date:]).cumprod(), label="Method6 (no VT)")
plt.plot((1 + rp_d_vt.loc[plt_date:]).cumprod(), label="Method6 + VT (monthly scale from daily RV)")
plt.legend()
plt.show()
```

* * *

4) なぜこの設計で「係数の過剰変動」が抑えられるか
--------------------------

*   realized vol は日次から推定するので情報量は確保される
*   しかしスケール係数を **月次で固定**するので、
    *   毎日の微小なボラ変動に追随してレバが上下しない
    *   ターンオーバーとノイズ追随（“過剰な変動”）が抑えられる
*   `lookback_days` を長くするほど、さらに滑らかになる（推奨：63 or 126）

* * *

推奨パラメータ（迷ったらこれ）
---------------

*   `lookback_days=63`（約3か月）
*   `month_end="BME"`
*   `max_leverage=3.0`
*   もっと滑らかにしたいなら `use_ewma=True, ewma_lambda=0.97`（0.94より強く平滑化）

* * *

必要なら、次の追加もすぐ入れられます（質問ではなく提案です）：

*   スケール係数に **月次でも上限変化率（|Δscale\_m|制限）** を入れて、月次でも急変を抑える
*   realized vol を `rp_d`（戦略）ではなく `rets_d`（原資産）から作り、w とは独立にリスク管理する（設計思想の違い）

まずは上記の「日次RV→月次ターゲット→月内固定スケール」で、目的（係数の過剰変動抑制）は達成できます。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)