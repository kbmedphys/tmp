# 回帰戦略とポートフォリオ

**User:** Anonymous (kbmedphys@gmail.com)  
**Created:** 12/26/2025 21:46:15  
**Updated:** 1/7/2026 23:07:47  
**Exported:** 1/7/2026 23:17:30  
**Link:** [https://chatgpt.com/c/694e8329-68e8-8321-a9da-9d485961e013](https://chatgpt.com/c/694e8329-68e8-8321-a9da-9d485961e013)  

## Response:
以下では、\*\*あなたの実装（回帰によるシグナル → ウェイト決定）\*\*が、  
添付文献で議論されている ①_Earnings Extrapolation & market timing（Guo）_ と  
②_Forecast-Agnostic Portfolios（Guo–Wachter）_ の理論とどう対応しているかを、  
**計量経済学・資産価格論の文脈**で位置付けて解説します。

* * *

1\. 回帰係数 β の意味：何を推定しているのか
=========================

あなたの `build_beta()` は

$$
y_t = \beta_t x_t + \varepsilon_t
$$

を逐次推定しており、β と w\_raw = β x\_t が **市場の期待収益率の代理変数**になっています。  
ここで β は単なる係数ではなく、**以下の数量と等価**です。

$$
\beta = \frac{\text{Cov}(x_t, r_{t+1})}{\text{Var}(x_t)} = E[r^{(x)}]
$$

つまり、β は **「x というシグナルで構成したロング/ショート・ポートフォリオの期待超過収益」** そのものです。  
この解釈は Forecast-Agnostic Portfolios の文献で明示されています：

> “the beta coefficient in a predictive regression equals the excess return on a portfolio…scaled by exposure to the predictor.”  
> 
> ssrn-5808182

よって、β を推計することは、「x を使った戦略ポートフォリオが**平均何%稼いできたか**」を逐次学習していることに等しく、  
単なる予測パラメータではなく**ポートフォリオの期待リターン推定**になっています。

* * *

2\. 回帰による予測と Forecast-Agnostic Portfolio の違い
============================================

(1) あなたの実装（Forecast-driven）
---------------------------

*   x を入力に β を推定
*   予測戻り `β_t x_t` をポジションに反映
*   β が不安定な時期 → 重い推定誤差を含む
*   高い分散（variance）が発生 → OOS R² が悪化しやすい

(2) Forecast-Agnostic（FA：文献）
----------------------------

*   β の推定値を「方向性（sign）」にしか使わない
*   ボラティリティ・ターゲッティングで position size を固定化
*   係数推定エラーを**意図的に捨てる**ことで OOS 劣化を回避

> “FA portfolios exhibit timing ability without relying on estimated coefficients…  
> positive alpha does not require positive out-of-sample R².”  
> 
> ssrn-5808182

**結論**：  
回帰ベースの戦略は「どれくらい儲かるか」まで当てようとするため外挿誤差を負いやすい。  
FA型は「どちらを向くか」だけに情報利用を抑え、**予測の分散を意図的に削る**点で安定。

* * *

3\. CAPMとαの関係：あなたの β と w\_raw は何を測っているか
=======================================

CAPMの基準で考えると、戦略リターン  $r^{strat}$  は

$$
r^{strat}_t = \alpha + \beta_{mkt} r^{mkt}_t + \varepsilon_t
$$

ここで重要なのは：

| 量 | あなたの実装で対応するもの | CAPM解釈 |
| --- | --- | --- |
| 予測指標 x | News cycle-based signal | 状態変数（非リスク要因） |
| 回帰 β | factor-mimicking portfolioの期待収益率 | **価格付けされたリスクか誤反応かの判断基準** |
| w\_raw = β x | マーケットポジション | リスクプレミア or アノマリの抽出 |

Guoの論文では、newsy / non-newsy で期待収益が符号反転するため、  
\*\*一つのβで市場のリスクプレミアを表現できない（状態依存）\*\*ことが示されています：

> “newsy month returns negatively predict future newsy month returns, and positively predict non-newsy months.”  
> 
> ssrn-3480863

したがって、β を一定のリスク価格と解釈すると**誤る可能性が高い**。  
実際には、β は\*\*投資家の誤反応（diagnostic-expectations / parameter compression）\*\*を吸い上げた数量となります。

* * *

4\. 計量経済学的に見たあなたのパラメータの意味付け
===========================

| 変数 | あなたのコードでの役割 | 計量経済学 / 資産価格論での意味 |
| --- | --- | --- |
| S(t) accumulation | earnings-cycle情報の更新 | 逐次的 signal process / sufficient statistic |
| x(t) = signed deviation | cycleのズレ（過小/過大反応） | 誤反応を測る代理変数 |
| β(t) | factor-mimicking portfolioの推定平均収益 | 状態依存リスク価格 or 誤反応の強度 |
| w\_raw(t) = βx | timingポジション | Intertemporal hedge / behavioral exploitation |

特に x(t) は \*\*状態変数（state variable）\*\*そのものであり、  
β(t) は **その状態変数に価格がついているか**を見ている指標と解釈できます。

* * *

5\. まとめ：あなたの戦略の位置づけ
===================

| 観点 | あなたの実装 | 文献の位置づけ |
| --- | --- | --- |
| 予測の目的 | βxで収益量を当てに行く | 方向性 + ボラターゲット重視 |
| 誤差構造 | β推定誤差が累積して重くなる | βの利用を縮退させて分散抑制 |
| 経済解釈 | 状態依存の expected return モデル | 誤反応・情報処理の非完備性 |
| CAPM整合性 | α≠0 が恒常的に生じうる | リスクベース単独説明は困難 |

* * *

今後の改善提案（コード変更指針）
================

```
# 方向性だけ利用 (FA型に変更)
sign_beta = np.sign(beta.shift(1))
raw = sign_beta * x
w = vol_target * raw / rolling_vol(raw)
w = w.clip(-3, 3)
```

*   期待リターン（βx）⇒ **方向性（sign β）× シグナル強度（x）**
*   ボラ調整導入で **過剰レバレッジ回避**
*   OOS安定性の改善が見込める

* * *

必要なら次のステップへ発展可能です：

*   FA型の完全版コードへの置換
*   CAPM / FF3 / q-factorでのα推定
*   Newsy/Non-newsy の regime回帰 (state-dependent β)

ご希望があれば、**今のプログラム構造を崩さない形でFA版実装**を作成します。  
次に進める場合、以下どれを優先しますか？

1.  現行関数に FA/forecast-driven の切替フラグ追加
2.  ボラティリティターゲッティング統合版
3.  CAPMαの自動推定＋レポート出力機能

番号で指示してください。

## Response:
以下に、**CAPMを基準フレーム**として、添付の2文献の手法がそれぞれ何を意味し、その考え方があなたの上記プログラム（回帰ベース・シグナル構築）とどう対応するかを体系的に整理します。

* * *

1\. 基準：CAPMの観点（比較の土台）
=====================

CAPMでは、任意の戦略リターン  $r^{strat}_t$  は

$$
r^{strat}_t = \alpha + \beta_{mkt} r_{mkt,t} + \varepsilon_t
$$

で評価され、  
**α（アlファ）が正であれば、リスク調整後の超過リターン＝市場に対する優位性**を意味します。

| CAPM基準で問うべきこと | 解釈ポイント |
| --- | --- |
| βは市場リスクの感応度か？ | 戦略がどれだけ市場に連動するか |
| αは0より有意に大きいか？ | 価格付け誤り・誤反応・情報処理の非完備を捉えている可能性 |
| リターン予測はリスク価格なのか誤反応なのか？ | リスクベース説明 vs 認知バイアス/行動的要因 |

* * *

2\. 文献① Guo「Earnings Extrapolation & Newsy/Non-newsy」
=====================================================

**⇒ CAPM的には「αが状態依存的に現れる仕組み」を提示**

文献の核心：

> “newsy month returns negatively predict future newsy months, and positively predict non-newsy months.”  
> （newsyは反転、non-newsyは継続）  
> 
> ssrn-3480863

この現象はCAPM的観点でみると：

| 観点 | 解釈 |
| --- | --- |
| β（市場リスク） | ニューシー月・非ニューシー月で**均一に説明できない** → 状態依存β |
| α（超過収益） | 投資家の誤反応（diagnostic expectations / parameter compression）が生む**時間帯別のα** |
| CAPMとのズレ | 単一β・単一リスク価格では説明できない → **CAPMに対する系統的な補正要因が存在** |

つまり、Guoの文脈ではCAPMが破れ、**αが周期的に現れ得る理論的根拠**が示されています。

* * *

▶ あなたのプログラムとの対応
---------------

あなたの実装はまさにこの構造をコード上で再現しています：

| あなたの変数 | 文献での意味 / CAPM的読み替え |
| --- | --- |
| `month_type`, `is_newsy` | CAPMに対する**状態識別（state variable）** |
| `S`（累積シグナル） | 期待収益率に影響を与える十分統計的情報 |
| `x = sign * (S - \bar{S})` | 認知バイアス由来の**誤反応量（αの発生源）** |
| `β(t)`（逐次回帰） | **状態依存的 risk price / 誤反応係数**の推定 |
| `w_raw = β(t)x(t)` | CAPM世界をずらす**α抽出ポジション** |

> 結論：  
> **あなたの回帰モデルは、Guoが提示した“CAPMからのズレ＝状態依存α”を実務的に推定・抽出する実装になっている。**

* * *

3\. 文献② Guo–Wachter「Forecast-Agnostic Portfolio」
================================================

**⇒ CAPM的には「β推定を捨ててもαは取れる」ことの証明**

> “FA portfolios exhibit timing ability without relying on estimated coefficients…  
> positive alpha does not require positive out-of-sample R².”  
> 
> ssrn-5808182

CAPM観点での含意：

| 論点 | 含意 |
| --- | --- |
| βの利用 | 量的推定を放棄し、符号(sign)のみ利用 |
| αの発生源 | 価格付け誤り・誤反応の持続という**構造的歪み** |
| OOS R²との乖離 | 予測精度（R²）と投資収益（α）は同値ではない |
| CAPM的評価軸 | **αの有無こそが中心**であり、R²は副次指標に格下げ |

FA手法は、CAPMに対して

> “αを取るのにβ推定の精度は必須ではない”

という非常に強い態度を示します。

* * *

▶ あなたのプログラムとの対応
---------------

| あなたの実装 | FA手法に変換する場合 |
| --- | --- |
| `w_raw = βx` | **sign(β) × x** だけ利用（量ではなく方向） |
| 変動レバレッジ | **ボラティリティターゲット化**（5% / 10%等） |
| β推定の不安定性 | **推定誤差を意図的に捨てる**ことでOOS安定化 |

**つまり、あなたの現行コードは「FAの直前段階」にある状態**で、  
・β依存（forecast-driven） → ・βの符号だけ（forecast-agnostic）  
へ1行で変換できます：

```python
w = np.sign(beta.shift(1)) * x.shift(1)
# + volatility targeting + leverage cap
```

これが文献②のエッセンスです。

* * *

4\. 最終整理（全体像）
=============

| 視点 | 文献①（Extrapolation） | 文献②（FA Portfolio） | あなたのプログラム |
| --- | --- | --- | --- |
| CAPMとの関係 | CAPMに状態依存αが生まれる理由を提示 | CAPM評価軸でαを抽出する技術体系 | α源泉の推定と抽出 |
| αの起源 | 認知バイアス / parameter compression | β推定誤差を避ける設計で顕在化 | βxで顕在化、FA化可能 |
| βの意味 | 状態依存的 risk price / 誤反応係数 | 方向性の指標に縮退させる | 係数をそのまま利用 |
| 実務的帰結 | 月次サイクルの識別が鍵 | βの符号＋ボラターゲットで運用可能 | 実務運用に耐える一歩手前 |

* * *

5\. 「結局どう位置付けるか」
================

*   文献①：**CAPMが完全ではない理由と、αが出る構造の理論的根拠**
*   文献②：**その構造を投資戦略に翻訳する実装思想（βの扱い方）**
*   あなたのコード：**両者の接続点にいる。わずかな修正でFAへ移行可能**

* * *

必要であれば、次にどれを実装しますか？

**A)** β依存 → FA化（sign化 + ボラターゲット）  
**B)** CAPM基準αの自動推定（FF3/FF5/Q-factor対応可）  
**C)** News/Non-newsy別の状態依存CAPM（state-dependent β）

番号で回答ください。

## Response:
思考時間: 44s

以下に、**CAPM基準αを自動推定**するための「実務でそのまま使える」最小一式（データ取得→整形→回帰→α・t値）を提示します。  
あなたの戦略（`strategy * rets` など）を入力すれば、\*\*CAPM / FF3 / FF5 / q-factor（q4 / q5）\*\*で一括評価できます。

* * *

0\. 位置づけ（なぜαなのか）
----------------

Forecast-Agnostic Portfolios では、投資戦略の価値判断は \*\*市場に対する超過（＝CAPM α）\*\*で行うのが適切、という立場です（長短ポートフォリオの価値は「市場に勝ったか」ではなく「αがあるか」）。

ssrn-5808182

したがって、あなたの戦略（market timing / long-short）の評価も、まずは \*\*CAPM α（必要なら多因子α）\*\*で揃えるのが自然です。

* * *

1\. データ源（自動取得）
--------------

*   **FF3/FF5（日次）**: Kenneth French Data Library の daily CSV(zip)（3因子・5因子）[タックスクールオブビジネス+2+2](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
*   **q-factor（日次）**: global-q の daily CSV（q5 ファイルには q4 + expected growth も含まれる）[Global-q.org+1](https://global-q.org/factors.html)

* * *

2\. フルコード（貼り付けて実行可）
-------------------

> 依存：`pandas numpy statsmodels requests`

```python
import io
import zipfile
import requests
import numpy as np
import pandas as pd
import statsmodels.api as sm

# ---------------------------
# A) Factor downloaders
# ---------------------------

FF3_DAILY_ZIP = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"
FF5_DAILY_ZIP = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
Q5_DAILY_CSV  = "https://global-q.org/uploads/1/2/2/6/122679606/q5_factors_daily_2024.csv"

def _read_ken_french_zip_csv(url: str) -> pd.DataFrame:
    """
    Ken French の daily factor zip(CSV) を読み込み、DataFrame(index=date) を返す。
    値は % 表記なので小数に直す（例: 0.12% -> 0.0012）。
    """
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(r.content))
    # zipの中は通常 CSV が1つ
    csv_name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
    raw = z.read(csv_name).decode("utf-8", errors="ignore")

    # Ken French CSV はヘッダ/フッタに注釈があるため、日付(8桁)で始まる行だけ抽出
    lines = raw.splitlines()
    data_lines = [ln for ln in lines if len(ln) >= 8 and ln[:8].isdigit()]
    if not data_lines:
        raise ValueError("No daily data rows parsed from Ken French CSV.")

    df = pd.read_csv(io.StringIO("\n".join(data_lines)))
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    df = df.set_index("date").sort_index()

    # % -> decimal
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce") / 100.0

    return df

def load_ff3_daily() -> pd.DataFrame:
    # Columns: Mkt-RF, SMB, HML, RF
    return _read_ken_french_zip_csv(FF3_DAILY_ZIP)

def load_ff5_daily() -> pd.DataFrame:
    # Columns: Mkt-RF, SMB, HML, RMW, CMA, RF
    return _read_ken_french_zip_csv(FF5_DAILY_ZIP)

def load_q5_daily() -> pd.DataFrame:
    """
    global-q の q5 factors (daily) を読み込み。
    想定列（サイト説明に沿う）: date, R_F, R_MKT, R_ME, R_IA, R_ROE, R_EG
    値は小数（0.001=0.1%）で提供されるケースが多いが、念のため%なら自動判定。
    """
    df = pd.read_csv(Q5_DAILY_CSV)
    # date列名の揺れに対応
    date_col = [c for c in df.columns if c.lower() in ("date", "yyyymmdd")][0]
    df[date_col] = pd.to_datetime(df[date_col].astype(str))
    df = df.set_index(date_col).sort_index()

    # 数値化
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # %っぽい（例: 0.12 で 0.12% ではなく 0.12=12% など）を雑に判定して補正
    # 日次で絶対値>1 が頻発するのは通常ありえないため、平均的に大きければ % とみなす
    med_abs = df.abs().median(numeric_only=True)
    if (med_abs > 0.2).any():  # 0.2=20% は日次として大きすぎ → %表記の可能性
        df = df / 100.0

    return df

# ---------------------------
# B) Alpha estimation core
# ---------------------------

def _newey_west_lags(freq: str) -> int:
    # 経験則：月次=6、日次=10〜20程度（お好みで）
    return 6 if freq == "M" else 15

def estimate_alpha(
    strat_ret: pd.Series,
    model: str = "CAPM",       # "CAPM" / "FF3" / "FF5" / "Q4" / "Q5"
    freq: str = "D",           # "D" or "M"
    hac_lags: int | None = None,
) -> dict:
    """
    戦略リターン（トータルリターン、日次or月次）から、
    指定因子モデルで α と t(α) を推定する。

    重要：ここでは "excess return regression" を実施：
        (R_strat - Rf) = alpha + betas' * factors + eps
    """
    strat_ret = strat_ret.dropna().sort_index()

    # --- load factors and build regressor matrix ---
    if model.upper() in ("CAPM", "FF3"):
        ff3 = load_ff3_daily()
        if freq == "M":
            # 月次化（複利）：(1+r).prod()-1
            ff3_m = ff3.resample("M").apply(lambda x: (1 + x).prod() - 1)
            f = ff3_m
        else:
            f = ff3

        rf = f["RF"]
        mktrf = f["Mkt-RF"]
        if model.upper() == "CAPM":
            X = pd.DataFrame({"Mkt-RF": mktrf})
        else:
            X = f[["Mkt-RF", "SMB", "HML"]]

    elif model.upper() == "FF5":
        ff5 = load_ff5_daily()
        if freq == "M":
            ff5_m = ff5.resample("M").apply(lambda x: (1 + x).prod() - 1)
            f = ff5_m
        else:
            f = ff5

        rf = f["RF"]
        X = f[["Mkt-RF", "SMB", "HML", "RMW", "CMA"]]

    elif model.upper() in ("Q4", "Q5"):
        q = load_q5_daily()
        if freq == "M":
            q_m = q.resample("M").apply(lambda x: (1 + x).prod() - 1)
            f = q_m
        else:
            f = q

        # global-q: R_F が無リスク、R_MKT が市場超過（とサイトに記載）:contentReference[oaicite:3]{index=3}
        rf = f["R_F"]
        if model.upper() == "Q4":
            X = f[["R_MKT", "R_ME", "R_IA", "R_ROE"]]
        else:
            X = f[["R_MKT", "R_ME", "R_IA", "R_ROE", "R_EG"]]

        # 列名を一般化（見た目だけ）
        X = X.rename(columns={"R_MKT": "MKT"})

    else:
        raise ValueError("model must be one of: CAPM, FF3, FF5, Q4, Q5")

    # --- align ---
    df = pd.concat([strat_ret.rename("strat"), rf.rename("rf"), X], axis=1).dropna()
    y = (df["strat"] - df["rf"]).rename("strat_excess")
    Xreg = sm.add_constant(df[X.columns], has_constant="add")

    # --- HAC / Newey-West ---
    if hac_lags is None:
        hac_lags = _newey_west_lags(freq)

    res = sm.OLS(y.values, Xreg.values).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})

    # 結果整形
    params = pd.Series(res.params, index=["alpha"] + list(X.columns))
    tvals  = pd.Series(res.tvalues, index=["t_alpha"] + [f"t_{c}" for c in X.columns])

    out = {
        "model": model.upper(),
        "freq": freq,
        "nobs": int(res.nobs),
        "hac_lags": hac_lags,
        "alpha": float(params["alpha"]),
        "t_alpha": float(res.tvalues[0]),
        "betas": params.drop("alpha"),
        "t_betas": pd.Series(res.tvalues[1:], index=X.columns),
        "r2": float(res.rsquared),
    }
    return out

# ---------------------------
# C) Convenience: run all models
# ---------------------------

def estimate_alphas_all_models(
    strat_ret: pd.Series,
    freq: str = "D",
    hac_lags: int | None = None,
) -> pd.DataFrame:
    models = ["CAPM", "FF3", "FF5", "Q4", "Q5"]
    rows = []
    for m in models:
        try:
            r = estimate_alpha(strat_ret, model=m, freq=freq, hac_lags=hac_lags)
            rows.append({
                "model": r["model"],
                "freq": r["freq"],
                "nobs": r["nobs"],
                "hac_lags": r["hac_lags"],
                "alpha": r["alpha"],
                "t_alpha": r["t_alpha"],
                "r2": r["r2"],
            })
        except Exception as e:
            rows.append({
                "model": m, "freq": freq,
                "nobs": np.nan, "hac_lags": hac_lags,
                "alpha": np.nan, "t_alpha": np.nan, "r2": np.nan,
            })
            print(f"[WARN] {m} failed: {e}")
    return pd.DataFrame(rows).set_index("model")
```

* * *

3\. あなたの戦略への接続（最小例）
-------------------

あなたは日次で `strategy * rets` を作っているので、それを `strat_ret` として渡します。

```python
# あなたのコードで既にあるもの：
# rets: 日次SPXリターン（Series）
# strategy: 日次ポジション（Series）
strat_ret_d = (strategy * rets).dropna()

# 推定（まず日次で）
tbl_d = estimate_alphas_all_models(strat_ret_d, freq="D")
print(tbl_d)

# 月次で評価したい場合（戦略トータルリターンを月次に集計して渡す）
strat_ret_m = strat_ret_d.resample("M").apply(lambda x: (1 + x).prod() - 1)
tbl_m = estimate_alphas_all_models(strat_ret_m, freq="M")
print(tbl_m)
```

* * *

4\. 出力の解釈（実務で見る順番）
------------------

1.  **CAPM α**：まず「市場（Mkt-RF）で説明できない収益」があるか
2.  **FF3/FF5 α**：サイズ・バリュー・収益性・投資などの既知因子で落ちないか
3.  **Q4/Q5 α**：q理論系（投資・ROE）で説明される成分か、なお残るか

FAポートフォリオの議論に沿えば、あなたの戦略の価値は「予測R²」よりも、まず \*\*α（特にOOSで頑健なα）\*\*で評価するのが中心になります。

ssrn-5808182

* * *

5\. 次にこちらで追加できる改善（おすすめ順）
------------------------

*   **(i) 年率換算（α×252 等）と情報比・Sharpe・DDを同時出力**
*   **(ii) サンプル分割（2000以前/以後、出版前後、newsy/non-newsy別）でαの安定性診断**
*   **(iii) ボラターゲット後のα推定（文献の運用設計に寄せる）**

どれを先に組み込みますか。番号で指定ください。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)