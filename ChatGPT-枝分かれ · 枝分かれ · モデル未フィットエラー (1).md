# 枝分かれ · 枝分かれ · モデル未フィットエラー

**User:** Anonymous (kbmedphys@gmail.com)  
**Created:** 11/26/2025 21:08:44  
**Updated:** 12/3/2025 19:30:13  
**Exported:** 12/3/2025 20:39:53  
**Link:** [https://chatgpt.com/c/6926eda6-367c-8320-9582-0eceb27551d7](https://chatgpt.com/c/6926eda6-367c-8320-9582-0eceb27551d7)  

## Response:
思考時間: 1m 50s

やりたいことは、

*   **ジャンプペナルティ λ を固定ではなく、時系列クロスバリデーションで定期的に選び直す**
*   その λ を使って JumpModel＋XGBClassifier でオンラインに regime 予測を回す

という形ですよね。  
添付論文では、各資産ごとに

*   5 年の検証窓で 0/1 戦略の Sharpe を最大化するように λ を選び、
*   その λ を次の 6 ヶ月のライブ期間で固定して使う

という「ウォークフォワード型 TS-CV」をやっています。

2406.09578v2

ここでは、**あなたの簡易実装に合わせた、少し簡略化した TS-CV のコード**を提案します。

* * *

方針（あなたのコードに合わせた形）
-----------------

1.  **補助関数 `select_jump_penalty_on_window` を作る**
    *   入力: ある資産のリターン（`rets_window: pd.Series`）、候補 λ のグリッド
    *   窓の中を **train / validation に分割**（例: 7:3）
    *   各 λ について:
        *   train 部分で JumpModel をフィット → ラベル（regime）を生成
        *   ラベルを 1 日先シフトして教師データにし、XGBClassifier を学習
        *   validation 期間で **0/1 戦略をシミュレーション**  
            （レジーム予測が「強気」なら翌日のリターンにフル投資、弱気なら 0% 投資）
        *   その日次リターンから Sharpe を計算
    *   Sharpe 最大の λ を返す
2.  **`run` の中で、一定間隔ごとにこの関数を呼び出して λ を更新**
    *   たとえば `cv_window_days = 252 * 5`（5 年分）、
    *   `cv_freq_days = 21 * 3`（3 ヶ月ごとに λ を見直し）など
    *   `obs`（これまでのリターン）の末尾 `cv_window_days` を取り出して TS-CV をかける
    *   そこで得た `best_lambda` で JumpModel を作り直してから学習する
3.  **ラベルの定義**
    *   `rearange_labels` は、**平均リターンが小さい方を 0、大きい方を 1** に貼り直しているので、
    *   `n_regimes=2` のときは **label=1 が「強気」レジーム** とみなせるようにしておきます。

* * *

追加・修正コード例
---------

### 1\. ジャンプペナルティを TS-CV で選ぶ関数

```python
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
import misc

def select_jump_penalty_on_window(
    rets_window: pd.Series,
    n_regimes: int,
    lambda_grid,
    train_ratio: float = 0.7,
):
    """
    rets_window: ある資産の日次リターン（Series, index は DatetimeIndex）
    lambda_grid: 候補の jump_penalty の配列（例: [0.0, 0.1, 0.3, 1, 3, 10, 30, 100]）
    """
    n = len(rets_window)
    if n < 100:  # データが短すぎる場合は適当に最初の λ を返す
        return lambda_grid[0]

    # 1) 特徴量を作る（あなたの feature_engineer をそのまま利用）
    X = misc.feature_engineer(rets_window)

    # クリッピング・スケーリングは JumpModel / XGB と同じ前処理に合わせる
    clipper = misc.Clipper(mul=3)
    scaler = misc.Scaler()
    X_clipped = clipper.fit_transform(X)
    X_scaled = scaler.fit_transform(X_clipped)   # np.ndarray になる想定

    # 2) train / validation に分割
    split_idx = int(n * train_ratio)
    # train 部分
    X_train = X_scaled[:split_idx]
    rets_train = rets_window.iloc[:split_idx]

    # validation 部分 (翌日のリターンを使うので -1 まで)
    X_val_all = X_scaled[split_idx-1:-1]      # 特徴量の位置 i から i+1 のリターンを予測
    rets_val_all = rets_window.iloc[split_idx:]  # i+1 のリターン

    if len(rets_val_all) < 10:
        return lambda_grid[0]

    best_lambda = None
    best_sharpe = -np.inf

    for lam in lambda_grid:
        # 3) train 部分で JumpModel をフィット
        jm = misc.JumpModel(n_regimes=n_regimes, jump_penalty=lam)
        jm.fit(X_train)

        # ラベルをリターンで並び替え（bullish=1, bearish=0 のように）
        labels_train = misc.rearange_labels(jm.labels, rets_train.values)

        # 1 日先ラベルを教師データにする
        # y[t] = s_{t+1}、特徴量は x_t
        y = labels_train[1:split_idx]          # 長さ split_idx-1
        X_clf = X_scaled[:split_idx-1]

        # 安全チェック
        if len(np.unique(y)) < 2:
            # 片方のクラスしかないときはこの λ はパス（Sharpe はかなり悪いものとして扱う）
            continue

        clf = XGBClassifier()
        clf.fit(X_clf, y.astype(int))

        # 4) validation 部分で 0/1 戦略のリターンをシミュレーション
        daily_returns = []
        # val 部分に対応するインデックス（X_val_all, rets_val_all はずらしてある）
        for i in range(len(X_val_all)):
            # 時点 i+split_idx-1 の特徴量から、翌日 (i+split_idx) の regime を予測するイメージ
            x_i = X_val_all[i].reshape(1, -1)
            pred_regime_next = clf.predict(x_i)[0]

            # bullish label は 1 として設計しているので 1 なら risky 資産に 100%、
            # それ以外は rf=0% とする簡易 0/1 戦略
            r_next = float(rets_val_all.iloc[i])
            if pred_regime_next == 1:
                daily_returns.append(r_next)
            else:
                daily_returns.append(0.0)

        daily_returns = np.array(daily_returns)
        if daily_returns.std(ddof=1) == 0:
            sharpe = -np.inf
        else:
            sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std(ddof=1)

        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_lambda = lam

    # すべての λ で Sharpe が NaN / -inf になった場合の fallback
    if best_lambda is None:
        best_lambda = lambda_grid[0]

    return best_lambda
```

> ※ 本家論文では
> 
> *   11 年の訓練窓 ＋ 5 年の検証窓
> *   6 ヶ月ごとに λ を更新  
>     というもう少しリッチなスキームですが、上の関数は「ひとつのロールング窓の中で train/val を分けて Sharpe 最大の λ を選ぶ」簡易版です。
>     2406.09578v2
>     

* * *

### 2\. `run` に TS-CV を組み込んだバージョン

元の `run` を少し拡張して、

*   `lambda_grid`
*   `cv_window_days`
*   `cv_freq_days`

を引数として受け取り、**一定間隔ごとに λ を選び直す**ようにします。

```python
def run_with_online_lambda(
    rets: pd.Series,
    start_idx: int,
    n_regimes: int,
    init_jump_penalty: float,
    fit_freq_days: int,
    lambda_grid=None,
    cv_window_days: int = 252 * 5,   # 5 年分くらい
    cv_freq_days: int = 21 * 3,      # 3 ヶ月ごとに λ 見直し
):
    """
    rets: ある資産の日次リターン（Series）
    fit_freq_days: JumpModel / XGB の再学習頻度（日数ベース）
    """
    if lambda_grid is None:
        lambda_grid = [0.0, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

    scaler = misc.Scaler()
    clipper = misc.Clipper(mul=3)

    current_lambda = init_jump_penalty
    model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=current_lambda)
    clf = XGBClassifier()

    last_fit_date = None
    last_cv_date = None

    def should_fit(last_date, current_date, freq_days):
        current = current_date.date()
        if last_date is None:
            return True
        delta = current - last_date
        return delta.days >= freq_days

    n = rets.shape[0]
    current_idx = start_idx
    end_idx = n - 1

    w = np.ones(n)              # regime 予測 or 重みの placeholder
    lambda_path = np.full(n, np.nan)  # 各時点で使われた λ を記録しておくと後で可視化などに便利

    while True:
        current_idx += 1
        obs = rets.iloc[:current_idx]      # ここまでの履歴
        current_date = obs.index[-1]

        # --- ここで一定間隔ごとに TS-CV をかけて jump_penalty を更新 ---
        if should_fit(last_cv_date, current_date, cv_freq_days) and len(obs) >= cv_window_days:
            window = obs.iloc[-cv_window_days:]
            best_lambda = select_jump_penalty_on_window(
                window,
                n_regimes=n_regimes,
                lambda_grid=lambda_grid,
            )
            current_lambda = best_lambda
            last_cv_date = current_date.date()
            # 新しい λ で JumpModel を作り直す（パラメータはこのあと fit し直す）
            model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=current_lambda)

        # --- モデルの再学習（JumpModel + XGB） ---
        if should_fit(last_fit_date, current_date, fit_freq_days):
            last_fit_date = current_date.date()

            X = misc.feature_engineer(obs)
            X_processed = scaler.fit_transform(clipper.fit_transform(X))

            model.fit(X_processed)
            labels = misc.rearange_labels(model.labels, obs.values)

            # s_{t+1} を教師ラベルにする
            y = pd.Series(labels).shift(-1)
            y_idx = y.dropna().index

            clf.fit(
                pd.DataFrame(X_processed, columns=X.columns).iloc[:len(y_idx)],
                y.dropna().astype(int)
            )
        else:
            # 前回の scaler / clipper / model を使って変換と regime 推定だけやる
            X = misc.feature_engineer(obs)
            X_processed = scaler.transform(clipper.transform(X))
            pred_labels, pred_probs = model.prediction(X_processed)
            labels = misc.rearange_labels(pred_labels, obs.values)

        # --- 最後のサンプルに対する regime 予測を XGB で出す ---
        X_processed = scaler.transform(clipper.transform(misc.feature_engineer(obs)))
        x_last = pd.DataFrame(X_processed, columns=misc.feature_engineer(obs).columns).iloc[[-1]]
        w[current_idx] = clf.predict(x_last)[0]   # ここでは単に regime ラベルを保存

        lambda_path[current_idx] = current_lambda

        if current_idx == end_idx:
            break

    return w, lambda_path
```

呼び出し側は、もともとのループを少し変えて：

```python
assets = rets.columns
start_idx = 1000
n_regimes = 2
init_jump_penalty = 10.0      # 初期値（最初の TS-CV まではこれを使う）
fit_freq_days = 7 * 4         # もともとの freq と同じ 4 週間

lambda_grid = [0.0, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

results = {}

for asset in assets:
    w, lambda_path = run_with_online_lambda(
        rets[asset],
        start_idx=start_idx,
        n_regimes=n_regimes,
        init_jump_penalty=init_jump_penalty,
        fit_freq_days=fit_freq_days,
        lambda_grid=lambda_grid,
        cv_window_days=252*5,
        cv_freq_days=21*3,
    )
    results[asset] = {
        "regime_pred": w,
        "lambda_path": lambda_path,
    }
```

* * *

使い方・調整のポイント
-----------

*   **論文どおりに近づけたい場合**
    *   `cv_window_days` を 252\*5（5 年）
    *   `cv_freq_days` を 21\*6（半年）
    *   `train_ratio` を 11/(11+5) ≈ 0.69 にするとかなり雰囲気が近づきます。
        2406.09578v2
*   **0/1 戦略の定義を変えたい場合**
    *   今は「bullish=1 のとき翌日の risky に 100%、それ以外は 0%」という超シンプル版です。
    *   実務的には、「bear のときは RF を足した total return」「transaction cost」なども考慮できます。
*   **レジームラベルの向き**
    *   `rearange_labels` が「低リターン→0, 高リターン→1」になるよう並べ替えているので、
    *   classifier の出力 1 を「強気」とみなす前提で 0/1 戦略を組んでいます。

* * *

このレベルまで組み込めば、

*   「過去 5 年の窓の中で 0/1 戦略 Sharpe が最大になるように λ を選ぶ」
*   「その λ を数ヶ月〜半年維持してオンラインで regime 予測」

という流れを、自分の実装の中で再現できるようになります。

もし「Sharpe ではなく Sortino で選びたい」「複数資産をまとめた指標で λ を選びたい」などがあれば、その部分だけ差し替えていけば OK です。

## Response:
思考時間: 25s

原因の読みはほぼ当たりで、「λ を更新したタイミングで JumpModel を作り直したのに、その iteration では fit されていないまま `prediction` を呼んでいる」ことが原因です。

* * *

エラーの直接原因
--------

`JumpModel` の実装を見ると：

```python
class JumpModel:
    def fit(self, X):
        ...
        self.centers = best_res["centers"]
        self.probs = best_res["probs"]
        self.labels = best_res["labels"]
        return self
    
    def prediction(self, X):
        labels, probs, val = self.E_step(X, self.centers)
        return labels, probs
```

*   `self.centers` は **`fit()` が初めて呼ばれたときにのみ** 定義されます。
*   それ以前に `prediction()` を呼ぶと、当然 `self.centers` が存在しないので
    > AttributeError: 'JumpModel' object has no attribute 'centers'

になります。

* * *

どこで「未 fit の model」に対して prediction しているか
---------------------------------------

前回渡した `run_with_online_lambda` のロジックを思い出すと、ループ内はざっくりこうなっていました（要点だけ抜粋）：

```python
while True:
    current_idx += 1
    obs = rets.iloc[:current_idx]
    current_date = obs.index[-1]

    # 1) TS-CV で λ を更新
    if should_fit(last_cv_date, current_date, cv_freq_days) and len(obs) >= cv_window_days:
        ...
        current_lambda = best_lambda
        last_cv_date = current_date.date()
        model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=current_lambda)
        # ← ここで新しい model を作り直している（まだ fit していない）

    # 2) JumpModel + XGB を再学習するかどうか
    if should_fit(last_fit_date, current_date, fit_freq_days):
        last_fit_date = current_date.date()
        ...
        model.fit(X_processed)               # ← ここで初めて fit
        ...
        clf.fit(...)
    else:
        X = misc.feature_engineer(obs)
        X_processed = scaler.transform(clipper.transform(X))
        pred_labels, pred_probs = model.prediction(X_processed)
        # ↑ λ 更新直後で、かつ fit_freq_days にまだ達していないと、
        #    「新しい model（未 fit）に対して prediction している」
```

このパターンが今回まさに起きています：

1.  ある日付で
    *   `should_fit(last_cv_date, current_date, cv_freq_days)` が True → λ を更新し `model = JumpModel(...)` で「新品の model」に差し替え
    *   しかし直前に学習したのが最近なので `should_fit(last_fit_date, current_date, fit_freq_days)` が False
2.  その結果、その iteration では `model.fit(...)` が呼ばれず、
3.  `else` に入って `model.prediction(...)` が呼ばれ、`self.centers` が無いので AttributeError になる。

まさに「lambda の更新と model.fit() のタイミングずれ」が原因です 👍

* * *

修正案 1（最小変更）：λ 更新時に「要再学習」フラグを立てる
-------------------------------

一番手軽なのは、**λ を更新して model を作り直したら必ず即座に fit させる**ことです。

`run_with_online_lambda` の TS-CV 部分をこう直してください：

```python
    # --- ここで一定間隔ごとに TS-CV をかけて jump_penalty を更新 ---
    if should_fit(last_cv_date, current_date, cv_freq_days) and len(obs) >= cv_window_days:
        window = obs.iloc[-cv_window_days:]
        best_lambda = select_jump_penalty_on_window(
            window,
            n_regimes=n_regimes,
            lambda_grid=lambda_grid,
        )
        current_lambda = best_lambda
        last_cv_date = current_date.date()

        # 新しい λ で JumpModel を作り直す
        model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=current_lambda)

        # ★ここを追加：この iteration で必ず再学習させる
        last_fit_date = None
```

その上で、`should_fit` 関数はそのまま：

```python
def should_fit(last_date, current_date, freq_days):
    current = current_date.date()
    if last_date is None:
        return True
    delta = current - last_date
    return delta.days >= freq_days
```

こうすると：

*   λ 更新直後は `last_fit_date = None` になり、
*   同じ iteration の `if should_fit(last_fit_date, current_date, fit_freq_days):` が必ず True になる
*   つまり **新品の JumpModel に対して即座に `fit` が走る**ため、
*   その後で `prediction` を呼んでも `self.centers` がちゃんと存在します。

* * *

修正案 2（設計を少しきれいに）：model の生成は常に「fit ブロック」でのみ行う
--------------------------------------------

もう少し設計をきれいにしたいなら、

*   TS-CV ブロックでは **`current_lambda` だけ更新**し、
*   実際に `JumpModel` インスタンスを生成するのは **毎回「fit するときだけ」**

という方針にすると安全です。

イメージ：

```python
model = None
clf = None
last_fit_date = None
current_lambda = init_jump_penalty

while True:
    ...
    # 1) λ だけ更新（model はまだ作らない）
    if should_fit(last_cv_date, current_date, cv_freq_days) and len(obs) >= cv_window_days:
        ...
        current_lambda = best_lambda
        last_cv_date = current_date.date()

    # 2) 必要なら JumpModel + XGB を作り直して fit
    need_fit = (last_fit_date is None) or should_fit(last_fit_date, current_date, fit_freq_days)
    if need_fit:
        last_fit_date = current_date.date()
        X = misc.feature_engineer(obs)
        X_processed = scaler.fit_transform(clipper.fit_transform(X))

        # ← ここで初めて model を作る（最新 λ を使用）
        model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=current_lambda)
        model.fit(X_processed)
        labels = misc.rearange_labels(model.labels, obs.values)

        ...
        clf = XGBClassifier()
        clf.fit(...)

    else:
        # ここに来るときは model / clf は必ず一度は fit 済み
        X = misc.feature_engineer(obs)
        X_processed = scaler.transform(clipper.transform(X))
        pred_labels, pred_probs = model.prediction(X_processed)
        ...
```

この形にしておけば、

*   「未 fit の model」に対して `prediction` を呼ぶ経路がそもそも存在しなくなる  
    （model は必ず `need_fit` ブロックで作られ、同じブロックですぐ `fit` される）。

* * *

まとめ
---

*   エラーの原因は **JumpModel を新しく作り直した直後に、fit せずに prediction してしまったこと**。
*   λ 更新ブロックで `model = JumpModel(...)` としているのに、その iteration では `fit_freq_days` の条件を満たさず `fit()` が走っていない。
*   対策は、
    *   λ 更新時に `last_fit_date = None` をセットして **必ず即座に再学習させる**（最小修正）、  
        または
    *   「model の生成は fit ブロック内だけ」にするように設計を少し整理すること。

まずは修正案 1 の `last_fit_date = None` を足して動かしてみてください。それで AttributeError は消えるはずです。

## Response:
思考時間: 3m 7s

いいですね、ここまでで

*   **JM＋XGB＋時系列CVで λ（Jump Penalty）をオンライン更新**
*   各資産ごとのレジーム予測パス

まではできました。  
ここからは、論文と同じように

> 「資産別レジーム予測 → レジーム別平均リターン → Markowitz MVO で日次ポートフォリオ構築」

まで持って行きます。

* * *

全体像：論文でやっていることを、いまのコードにマッピングすると
-------------------------------

論文の 4.3 節の MV(JM-XGB) はざっくり以下です。

2406.09578v2

1.  各資産ごとに JM をフィット → **bull / bear のラベル**と  
    それぞれのレジームでの**平均リターン**（μ^bull, μ^bear）を計算
2.  レジームラベルを 1 日先にシフトして XGB で **「明日のレジーム」** を予測
3.  明日が bull と予測されたら μ^bull、bear と予測されたら μ^bear  
    （bear ならリターンを −10bps で下限クリップ）  
    → これを **その資産の期待リターン μ\_i,t+1** とする
4.  全資産の μ\_t+1 を並べて **ベクトル μ\_t+1**、共分散 Σ\_t+1 は EWM で推定
5.  これを Markowitz の MVO に入れて **その日のポートフォリオ w\_t** を解く
    *   bear 予測の資産は「投資対象から除外」
    *   bull 資産が 3 本以下なら「全部リスクフリー」に逃げる
        2406.09578v2

これを、いまの Python コードに合わせて

*   **Step1:** 各資産ごとに「レジーム予測＋レジーム別平均リターン」を出す
*   **Step2:** それを束ねて MVO を解き、ポートフォリオのバックテストを回す

という二段階で書きます。

* * *

Step1: run\_with\_online\_lambda を「レジーム別平均 μ 付き」で拡張
---------------------------------------------------

まず、前回の `run_with_online_lambda` を少し整理して、

*   λ のオンライン更新（TS-CV）
*   JM＋XGB の再学習
*   各時点 t で
    *   「明日」のレジーム予測 (`regime_pred[t]`)
    *   そのときに使うレジーム別平均リターン (`mu_bull[t]`, `mu_bear[t]`)
    *   そのとき有効な λ (`lambda_path[t]`)

を全部 Series で返すようにします。

※ ついでに、前回のバグ原因だった「λ 更新後に未 fit モデルで prediction」を踏まえて、  
**モデルの生成・fit のタイミング**を綺麗にしています。

```python
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
import misc

def select_jump_penalty_on_window(
    rets_window: pd.Series,
    n_regimes: int,
    lambda_grid,
    train_ratio: float = 0.7,
):
    """時系列CVで、その窓の中の 0/1 戦略 Sharpe が最大の λ を選ぶ簡易版"""
    n = len(rets_window)
    if n < 100:
        return lambda_grid[0]

    X = misc.feature_engineer(rets_window)

    clipper = misc.Clipper(mul=3)
    scaler = misc.Scaler()
    X_clipped = clipper.fit_transform(X)
    X_scaled = scaler.fit_transform(X_clipped)

    split_idx = int(n * train_ratio)
    X_train = X_scaled[:split_idx]
    rets_train = rets_window.iloc[:split_idx]

    X_val_all = X_scaled[split_idx-1:-1]
    rets_val_all = rets_window.iloc[split_idx:]

    if len(rets_val_all) < 10:
        return lambda_grid[0]

    best_lambda = None
    best_sharpe = -np.inf

    for lam in lambda_grid:
        jm = misc.JumpModel(n_regimes=n_regimes, jump_penalty=lam)
        jm.fit(X_train)

        labels_train = misc.rearange_labels(jm.labels, rets_train.values)

        # s_{t+1} を教師ラベルに
        y = labels_train[1:split_idx]
        X_clf = X_scaled[:split_idx-1]

        if len(np.unique(y)) < 2:
            continue

        clf = XGBClassifier()
        clf.fit(X_clf, y.astype(int))

        daily_returns = []
        for i in range(len(X_val_all)):
            x_i = X_val_all[i].reshape(1, -1)
            pred_regime_next = clf.predict(x_i)[0]
            r_next = float(rets_val_all.iloc[i])
            if pred_regime_next == 1:      # bull のときだけ risky に投資
                daily_returns.append(r_next)
            else:
                daily_returns.append(0.0)

        daily_returns = np.array(daily_returns)
        if daily_returns.std(ddof=1) == 0:
            sharpe = -np.inf
        else:
            sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std(ddof=1)

        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_lambda = lam

    if best_lambda is None:
        best_lambda = lambda_grid[0]

    return best_lambda

def run_with_online_lambda_and_mu(
    rets: pd.Series,
    start_idx: int,
    n_regimes: int,
    init_jump_penalty: float,
    fit_freq_days: int,
    lambda_grid=None,
    cv_window_days: int = 252 * 5,
    cv_freq_days: int = 21 * 3,
):
    """
    単一資産のリターン rets に対して、
    - λ のオンライン更新（TS-CV）
    - JM＋XGB のオンライン学習
    - 明日のレジーム予測、レジーム別平均リターン
    をまとめて返す。
    """
    if lambda_grid is None:
        lambda_grid = [0.0, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

    scaler = misc.Scaler()
    clipper = misc.Clipper(mul=3)

    n = len(rets)
    index = rets.index

    regime_pred = np.full(n, np.nan)
    lambda_path = np.full(n, np.nan)
    mu_bull_path = np.full(n, np.nan)
    mu_bear_path = np.full(n, np.nan)

    current_lambda = init_jump_penalty
    last_cv_date = None
    last_fit_date = None

    model = None
    clf = None
    mu_bull = 0.0
    mu_bear = 0.0

    def should_fit(last_date, current_date, freq_days):
        current = current_date.date()
        if last_date is None:
            return True
        delta = current - last_date
        return delta.days >= freq_days

    # time loop
    for t in range(start_idx, n - 1):
        obs = rets.iloc[: t + 1]
        current_date = obs.index[-1]

        # 1) λ を一定間隔ごとに TS-CV で更新
        if should_fit(last_cv_date, current_date, cv_freq_days) and len(obs) >= cv_window_days:
            window = obs.iloc[-cv_window_days:]
            best_lambda = select_jump_penalty_on_window(
                window,
                n_regimes=n_regimes,
                lambda_grid=lambda_grid,
            )
            current_lambda = best_lambda
            last_cv_date = current_date.date()

            # λ を変えたので次回は必ず再フィット
            last_fit_date = None

        # 2) 必要なら JM + XGB を再フィット
        if (last_fit_date is None) or should_fit(last_fit_date, current_date, fit_freq_days):
            last_fit_date = current_date.date()

            X = misc.feature_engineer(obs)
            X_proc = scaler.fit_transform(clipper.fit_transform(X))

            # JM を現在の λ で fit
            model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=current_lambda)
            model.fit(X_proc)

            labels = misc.rearange_labels(model.labels, obs.values)

            # レジーム別平均リターン（bull=1, bear=0）
            if (labels == 1).any():
                mu_bull = obs.values[labels == 1].mean()
            else:
                mu_bull = 0.0
            if (labels == 0).any():
                mu_bear = obs.values[labels == 0].mean()
            else:
                mu_bear = 0.0

            # s_{t+1} を教師ラベルにする
            y = pd.Series(labels, index=obs.index).shift(-1)
            train_idx = y.dropna().index

            clf = XGBClassifier()
            clf.fit(
                pd.DataFrame(X_proc, index=obs.index).loc[train_idx],
                y.loc[train_idx].astype(int),
            )
        else:
            # モデルは既に fit 済み。特徴量だけ更新して prediction 用に使う
            X = misc.feature_engineer(obs)
            X_proc = scaler.transform(clipper.transform(X))

        # 3) 今日までの情報で「明日のレジーム」を 1 ステップ先予測
        x_last = pd.DataFrame(X_proc, index=obs.index).iloc[[-1]]
        pred_reg = clf.predict(x_last)[0]

        # 保存（t 時点で「t+1 のレジーム」を予測している想定）
        regime_pred[t] = pred_reg
        lambda_path[t] = current_lambda
        mu_bull_path[t] = mu_bull
        mu_bear_path[t] = mu_bear

    out = {
        "regime_pred": pd.Series(regime_pred, index=index),
        "lambda": pd.Series(lambda_path, index=index),
        "mu_bull": pd.Series(mu_bull_path, index=index),
        "mu_bear": pd.Series(mu_bear_path, index=index),
    }
    return out
```

呼び出し側は、複数資産に対してこう回せます：

```python
assets = rets.columns
start_idx = 1000
n_regimes = 2
init_jump_penalty = 10.0
fit_freq_days = 7 * 4

lambda_grid = [0.0, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

asset_results = {}

for asset in assets:
    res = run_with_online_lambda_and_mu(
        rets[asset],
        start_idx=start_idx,
        n_regimes=n_regimes,
        init_jump_penalty=init_jump_penalty,
        fit_freq_days=fit_freq_days,
        lambda_grid=lambda_grid,
        cv_window_days=252*5,
        cv_freq_days=21*3,
    )
    asset_results[asset] = res
```

ここまでで、各資産ごとに

*   `regime_pred[t]` : t 時点での「t+1 のレジーム（0=bear,1=bull）予測」
*   `mu_bull[t], mu_bear[t]` : その時点で有効な **レジーム別平均リターン**
*   `lambda[t]` : その時点で使っている λ

が揃いました。

* * *

Step2: 資産横断で期待リターンベクトル μ\_t を作り、MVO でポートフォリオ構築
----------------------------------------------

次に、論文 4.2–4.3 節にならって、  
**レジーム予測を使った Markowitz MVO** のバックテストを書きます。

2406.09578v2

ここでは

*   共分散は EWM(halflife=252)
*   bear 予測の資産は「投資対象から除外」  
    （＝その資産の重みを 0 に縛る）
*   bull 資産が 3 本以下なら 100% リスクフリー
*   目的関数は
    $$
     \min_w \frac{\gamma_{\text{risk}}}{2} w^\top \Sigma w - \mu^\top w + \gamma_{\text{trade}} \|w - w_{\text{prev}}\|_1
    $$
    という Boyd et al. (2017) 型の単期トレーディングコスト付き MVO に近い形
    2406.09578v2

を Python + cvxpy で実装します。

```python
import cvxpy as cp

def ewm_cov_matrix(rets_window: pd.DataFrame, halflife: int = 252):
    """
    pandas の ewm().cov() を使って、窓の最後の時点の共分散行列だけを取り出す。
    """
    # マルチインデックス (date, asset) で返ってくるので xs で最後の date を抜く
    cov_all = rets_window.ewm(halflife=halflife).cov()
    last_date = rets_window.index[-1]
    cov_last = cov_all.xs(last_date, level=0)
    return cov_last.values  # (n_assets, n_assets)

def backtest_mv_jm_xgb(
    rets_df: pd.DataFrame,
    asset_results: dict,
    start_idx: int,
    rf_daily: float = 0.0,
    gamma_risk: float = 10.0,
    gamma_trade: float = 1.0,
    w_lb: float = 0.0,
    w_ub: float = 0.40,
    max_leverage: float = 1.0,
    cov_halflife: int = 252,
    min_bullish: int = 4,
    bear_floor: float = -0.001,   # bear 予測時の μ の下限（-10bps）
):
    """
    rets_df: (T, N) 日次リターン
    asset_results: {asset: {"regime_pred", "mu_bull", "mu_bear", "lambda"}}
                   Step1 の出力をそのまま渡す想定
    start_idx: ポートフォリオ構築を開始するインデックス（学習期間の後）
    """
    dates = rets_df.index
    assets = list(rets_df.columns)
    n_assets = len(assets)
    n = len(dates)

    # 結果格納用
    weights_hist = np.zeros((n, n_assets))
    port_ret = np.zeros(n)
    lambda_hist = np.zeros((n, n_assets))

    w_prev = np.zeros(n_assets)

    for t in range(start_idx, n - 1):
        date_t = dates[t]
        next_date = dates[t + 1]

        # --- 1) 各資産の regime 予測とレジーム別 μ から μ_t ベクトルを作る ---
        mu_vec = np.zeros(n_assets)
        bullish_mask = np.zeros(n_assets, dtype=bool)

        for j, asset in enumerate(assets):
            res = asset_results[asset]
            reg = res["regime_pred"].loc[date_t]
            mu_bull = res["mu_bull"].loc[date_t]
            mu_bear = res["mu_bear"].loc[date_t]
            lam = res["lambda"].loc[date_t]

            # bull / bear で期待リターンを出し分け（論文 4.3 節）
            if reg == 1:
                mu_j = mu_bull
                bullish_mask[j] = True
            else:
                mu_j = max(mu_bear, bear_floor)

            mu_vec[j] = mu_j
            lambda_hist[t, j] = lam

        # bull 予測の資産が少ない時は「全額リスクフリー」
        if bullish_mask.sum() < min_bullish:
            w_opt = np.zeros(n_assets)
        else:
            # bearish 予測の資産は weight を 0 に縛る
            active_idx = np.where(bullish_mask)[0]

            # --- 2) 共分散 Σ_t を EWM で推定 ---
            # ここでは単純に start から t まで全期間を使う
            cov_window = rets_df.iloc[: t + 1]
            Sigma = ewm_cov_matrix(cov_window, halflife=cov_halflife)

            # cvxpy で QP を解く
            w = cp.Variable(n_assets)

            # 目的関数
            risk_term = 0.5 * gamma_risk * cp.quad_form(w, Sigma)
            ret_term = - mu_vec @ w
            trade_term = gamma_trade * cp.norm1(w - w_prev)

            obj = cp.Minimize(risk_term + ret_term + trade_term)

            constraints = []

            # ロングオンリー + 上限
            constraints += [w >= w_lb, w <= w_ub]

            # レバレッジ制約: Σ w_j ≤ max_leverage
            constraints += [cp.sum(w) <= max_leverage]

            # bearish 予測の資産は weight=0
            for j in range(n_assets):
                if not bullish_mask[j]:
                    constraints.append(w[j] == 0.0)

            prob = cp.Problem(obj, constraints)
            prob.solve(solver=cp.OSQP)   # OSQP など、環境に応じて

            if w.value is None:
                # 最適化失敗時は前回ウェイトをそのまま使う
                w_opt = w_prev.copy()
            else:
                w_opt = np.array(w.value).flatten()

        # --- 3) ウェイト・リターン・ポートフォリオ価値を更新 ---
        weights_hist[t, :] = w_opt

        # 実際の次日の実現リターン
        r_next_vec = rets_df.iloc[t + 1].values

        risky_ret = np.dot(w_opt, r_next_vec)
        rf_weight = max(0.0, 1.0 - w_opt.sum())
        total_ret = risky_ret + rf_weight * rf_daily

        port_ret[t + 1] = total_ret
        w_prev = w_opt

    weights_hist_df = pd.DataFrame(weights_hist, index=dates, columns=assets)
    lambda_hist_df = pd.DataFrame(lambda_hist, index=dates, columns=assets)
    port_ret_series = pd.Series(port_ret, index=dates)

    # cumulative wealth (初期 1 として)
    wealth = (1.0 + port_ret_series).cumprod()

    return {
        "weights": weights_hist_df,
        "lambda": lambda_hist_df,
        "port_ret": port_ret_series,
        "wealth": wealth,
    }
```

使い方：

```python
# Step1 で作った asset_results を使う
start_idx_port = 1500   # 学習期間＋CV 期間を十分にとってから

mv_res = backtest_mv_jm_xgb(
    rets_df=rets,
    asset_results=asset_results,
    start_idx=start_idx_port,
    rf_daily=0.0,         # 必要なら FRED 等から取った RF をここに
    gamma_risk=10.0,
    gamma_trade=1.0,
    w_lb=0.0,
    w_ub=0.40,
    max_leverage=1.0,
    cov_halflife=252,
    min_bullish=4,
    bear_floor=-0.001,
)

mv_weights = mv_res["weights"]
mv_wealth = mv_res["wealth"]
```

あとは

*   `mv_wealth` をプロットして「Buy&Hold」「MinVar」「MV(JM-XGB)」と比較、
*   各資産のウェイト推移 `mv_weights` のヒートマップや、  
    特定期間のリスクオン／リスクオフの挙動をチェック、

していけば、論文のポートフォリオ構築パートとほぼ同じ流れになります。

2406.09578v2

* * *

ここからの発展（やるなら）
-------------

*   **MinVar(JM-XGB)** もほぼ同じ枠組みで書けます  
    （μ を使わず、bullish 資産だけで分散最小化＋制約、というだけ）
*   論文通りに
    *   11 年訓練＋5 年検証で λ を選ぶ
    *   6 ヶ月ごとのウォークフォワード  
        に寄せたい場合は、`select_jump_penalty_on_window` の窓幅と split を微調整すれば OK です。
*   リスクフリーレート `rf_daily` を FRED 3M T-bill などから取って入れると、  
    さらに論文に近づきます。

まずはこの骨格で動かしてみて、

*   期待リターン μ\_t のパス（bull/bear で切り替わる様子）
*   レジーム予測とウェイトの関係  
    をチェックしながらチューニングしていくのが良いと思います。

## Response:
思考時間: 14s

OK、その3つを**同じ価格（資産価値）時系列**で比較できるように一気に仕上げます。

前提として：

*   `rets` は **日次ログリターン**（`rets = np.log(df).diff().dropna()`）
*   `mv_res = backtest_mv_jm_xgb(...)` は前回の MV(JM-XGB) の結果

とします。

* * *

0\. ログリターン → 通常リターン
-------------------

ポートフォリオ価値の計算は通常リターンでやった方が自然なので、  
ここで一度変換しておきます。

```python
# rets: ログリターン DataFrame (T, N)
rets_arith = np.exp(rets) - 1.0   # 通常リターン
```

以降のバックテストは基本的に `rets_arith` を使います  
（JumpModel や feature\_engineer は今まで通り `rets` を使って OK）。

* * *

1\. Buy & Hold バックテスト
---------------------

*   開始時点で等ウェイト（もしくは指定ウェイト）を決めて、そのままホールド
*   途中でリバランスなし

```python
import numpy as np
import pandas as pd

def backtest_buy_and_hold(
    rets_df: pd.DataFrame,
    start_idx: int,
    init_weights: np.ndarray = None,
):
    """
    rets_df: 通常リターン DataFrame (T, N)
    start_idx: ポートフォリオ構築を開始する index（mv_res と揃える）
    init_weights: 初期ウェイト (N,)。None の場合は等ウェイト
    """
    dates = rets_df.index
    assets = rets_df.columns
    n_assets = len(assets)
    n = len(dates)

    if init_weights is None:
        init_weights = np.ones(n_assets) / n_assets

    w = init_weights.copy()
    weights_hist = np.zeros((n, n_assets))
    port_ret = np.zeros(n)

    for t in range(start_idx, n - 1):
        weights_hist[t, :] = w
        r_next = rets_df.iloc[t + 1].values
        port_ret[t + 1] = float(np.dot(w, r_next))

    weights_df = pd.DataFrame(weights_hist, index=dates, columns=assets)
    port_ret_series = pd.Series(port_ret, index=dates)
    wealth = (1.0 + port_ret_series).cumprod()

    return {
        "weights": weights_df,
        "port_ret": port_ret_series,
        "wealth": wealth,
    }
```

* * *

2\. MinVar バックテスト（ロールング最小分散）
----------------------------

*   各日 t で、過去のリターンを使って EWM 共分散を推定
*   単純な **unconditional 最小分散**（レジームは使わない）
*   ロングオンリー・レバレッジ ≤ 1

前回の `ewm_cov_matrix` を流用します。

```python
import cvxpy as cp

def ewm_cov_matrix(rets_window: pd.DataFrame, halflife: int = 252):
    cov_all = rets_window.ewm(halflife=halflife).cov()
    last_date = rets_window.index[-1]
    cov_last = cov_all.xs(last_date, level=0)
    return cov_last.values  # (N, N)

def backtest_minvar(
    rets_df: pd.DataFrame,
    start_idx: int,
    cov_halflife: int = 252,
    w_lb: float = 0.0,
    w_ub: float = 0.40,
    max_leverage: float = 1.0,
):
    """
    rets_df: 通常リターン DataFrame (T, N)
    start_idx: ポートフォリオ構築開始 index（mv_res と揃える）
    """
    dates = rets_df.index
    assets = rets_df.columns
    n_assets = len(assets)
    n = len(dates)

    weights_hist = np.zeros((n, n_assets))
    port_ret = np.zeros(n)

    for t in range(start_idx, n - 1):
        # 共分散推定に使う過去データ（シンプルに start_idx から t まで）
        cov_window = rets_df.iloc[: t + 1]
        Sigma = ewm_cov_matrix(cov_window, halflife=cov_halflife)

        w = cp.Variable(n_assets)
        # min (1/2) w' Σ w
        obj = cp.Minimize(0.5 * cp.quad_form(w, Sigma))

        constraints = [
            w >= w_lb,
            w <= w_ub,
            cp.sum(w) <= max_leverage,
        ]

        prob = cp.Problem(obj, constraints)
        prob.solve(solver=cp.OSQP)

        if w.value is None:
            # 最適化失敗時は等ウェイト
            w_opt = np.ones(n_assets) / n_assets
        else:
            w_opt = np.array(w.value).flatten()

        weights_hist[t, :] = w_opt
        r_next = rets_df.iloc[t + 1].values
        port_ret[t + 1] = float(np.dot(w_opt, r_next))

    weights_df = pd.DataFrame(weights_hist, index=dates, columns=assets)
    port_ret_series = pd.Series(port_ret, index=dates)
    wealth = (1.0 + port_ret_series).cumprod()

    return {
        "weights": weights_df,
        "port_ret": port_ret_series,
        "wealth": wealth,
    }
```

* * *

3\. MV(JM-XGB) の結果をそのまま利用
-------------------------

前回の `backtest_mv_jm_xgb` を

```python
mv_res = backtest_mv_jm_xgb(
    rets_df=rets_arith,        # ← 通常リターンを渡す
    asset_results=asset_results,
    start_idx=start_idx_port,
    rf_daily=0.0,
    gamma_risk=10.0,
    gamma_trade=1.0,
    w_lb=0.0,
    w_ub=0.40,
    max_leverage=1.0,
    cov_halflife=252,
    min_bullish=4,
    bear_floor=-0.001,
)
mv_wealth = mv_res["wealth"]
```

のようにしておけば OK です  
（`rets_df` 引数だけ `rets` → `rets_arith` に変更しておいてください）。

* * *

4\. 3戦略の価格（資産価値）時系列を比較プロット
--------------------------

3 つのバックテストを同じ `start_idx` から始めるように揃えます。  
（`start_idx_port` は MV(JM-XGB) で使った開始インデックス）

```python
start_idx = start_idx_port  # MV(JM-XGB) で使ったものに合わせる

# 1) Buy & Hold
bh_res = backtest_buy_and_hold(
    rets_df=rets_arith,
    start_idx=start_idx,
    init_weights=None,   # None なら等ウェイト
)

# 2) MinVar
mv_minvar_res = backtest_minvar(
    rets_df=rets_arith,
    start_idx=start_idx,
    cov_halflife=252,
    w_lb=0.0,
    w_ub=0.40,
    max_leverage=1.0,
)

# 3) MV(JM-XGB) は前回までの mv_res を再利用（rets_df を rets_arith に修正しておく）
mv_jm_wealth = mv_res["wealth"]

# 各 wealth を同じ期間に揃える
common_index = mv_jm_wealth.index[start_idx:]
bh_wealth = bh_res["wealth"].loc[common_index]
minvar_wealth = mv_minvar_res["wealth"].loc[common_index]
mv_jm_wealth = mv_jm_wealth.loc[common_index]

import matplotlib.pyplot as plt

plt.figure(figsize=(10, 5))
plt.plot(common_index, bh_wealth, label="Buy & Hold (EW)")
plt.plot(common_index, minvar_wealth, label="MinVar")
plt.plot(common_index, mv_jm_wealth, label="MV(JM-XGB)")
plt.legend()
plt.ylabel("Wealth (Initial = 1)")
plt.xlabel("Date")
plt.title("Strategy Comparison: Buy&Hold vs MinVar vs MV(JM-XGB)")
plt.grid(True)
plt.tight_layout()
plt.show()
```

* * *

5\. チェックポイント
------------

*   **インデックスの揃え方**
    *   `start_idx` を JumpModel / XGB の学習に使った期間よりも後ろに置く
    *   3 戦略とも同じ `start_idx` を使う
*   **ログリターン vs 通常リターン**
    *   JM・特徴量はこれまで通り `rets`（ログ）で計算して OK
    *   ポートフォリオ価値は `rets_arith = exp(rets) - 1` で計算するのが自然
*   **MinVar を JM 連動にしたい場合**
    *   「bull 予測資産だけで分散最小化する MinVar(JM-XGB)」も同じ枠組みで作れます  
        （`backtest_mv_jm_xgb` の目的関数から期待リターン項を消すだけ）。

* * *

このコードを入れてもらえれば、  
同じグラフ上で **Buy&Hold / MinVar / MV(JM-XGB)** の wealth 曲線が見えるはずです。

実際に描いてみて、

*   MV(JM-XGB) がどの局面でリスクオフ（フラット）になっているか
*   MinVar と比べてどの程度ドローダウンが抑えられているか

などもすぐ確認できると思います。

## Response:
思考時間: 15s

これは **プロットするときの `bh_wealth`（と他2つ）の形が 2次元（DataFrame）になっている** のが原因です。

`plt.plot(x, y)` に **DataFrame** を渡すと、  
内部で `y[:, None]` のようなインデックスを試みて、  
pandas 2.x ではそれが禁止されたため

> Multi-dimensional indexing (e.g. `obj[:, None]`) is no longer supported.

というエラーになります。

* * *

1\. まず shape を確認してみてください
------------------------

```python
print(type(bh_wealth), bh_wealth.shape)
print(type(minvar_wealth), minvar_wealth.shape)
print(type(mv_jm_wealth), mv_jm_wealth.shape)
```

ここが、

*   期待している形：`<class 'pandas.Series'> (T,)`
*   今なっている形：`<class 'pandas.DataFrame'> (T, 1)` など

になっているはずです。

どこかで

```python
bh_wealth = bh_res["wealth"].loc[common_index]
```

のときに `"wealth"` が **Series ではなく DataFrame の列**として扱われているか、  
あるいはインデックス合わせの過程で DataFrame になっています。

* * *

2\. シリーズに統一してからプロットする
---------------------

一番簡単な対処は、プロット前に **必ず 1次元 Series（or ndarray）にする** ことです。

```python
# それぞれ Series（or 1次元 array）に落としておく
bh_wealth = bh_res["wealth"].loc[common_index].squeeze()
minvar_wealth = mv_minvar_res["wealth"].loc[common_index].squeeze()
mv_jm_wealth = mv_res["wealth"].loc[common_index].squeeze()

# 念のため index も揃える
common_index = bh_wealth.index.intersection(minvar_wealth.index).intersection(mv_jm_wealth.index)
bh_wealth = bh_wealth.loc[common_index]
minvar_wealth = minvar_wealth.loc[common_index]
mv_jm_wealth = mv_jm_wealth.loc[common_index]
```

その上でプロットを：

```python
plt.figure(figsize=(10, 5))
plt.plot(common_index, bh_wealth.values,      label="Buy & Hold (EW)")
plt.plot(common_index, minvar_wealth.values,  label="MinVar")
plt.plot(common_index, mv_jm_wealth.values,   label="MV(JM-XGB)")
plt.legend()
plt.ylabel("Wealth (Initial = 1)")
plt.xlabel("Date")
plt.title("Strategy Comparison: Buy&Hold vs MinVar vs MV(JM-XGB)")
plt.grid(True)
plt.tight_layout()
plt.show()
```

ポイントは：

*   `Series` であっても `plt.plot(series.index, series.values)` としてしまえば確実に 1次元になる
*   もしまだ DataFrame の可能性があるなら `.squeeze()` か `.iloc[:, 0]` で 1列目を取る

* * *

3\. もう少し堅牢に書くなら
---------------

最初から「wealth は必ず Series にする」と決めておくと安全です。

バックテスト関数の最後で：

```python
wealth = (1.0 + port_ret_series).cumprod()
wealth = wealth.astype(float)      # 念のため
```

としておけば、

```python
bh_res["wealth"]  # <- ここは常に Series
```

のように扱えるので、エラーの温床が減ります。

* * *

ひとまず上の `.squeeze()` + `.values` で描けるはずなので、  
一度修正してグラフが出るか確認してみてください。

## Response:
了解です。「各時点のウェイト総和＝1（100%）」という **予算制約（budget constraint）** を常に成立させたい、ということですね。

結論としては：

* * *

✔ ウェイト総和＝1 にするための修正点（最重要）
=========================

**MVO・MinVar いずれも最適化制約に  
`cp.sum(w) == 1` を追加するだけで実現できます。**

ただし **JM による bullish / bearish の除外を維持する場合** は  
bearish（=除外）資産の分だけ、bullish 資産が **比率で按分されて合計 1** になるように設計します。

* * *

🔧 1. MinVar の修正版（常に Σ w\_j = 1）
================================

あなたの `backtest_minvar` を下のように修正できます。

```python
def backtest_minvar(
    rets_df: pd.DataFrame,
    start_idx: int,
    cov_halflife: int = 252,
    w_lb: float = 0.0,
    w_ub: float = 0.40,
):
    dates = rets_df.index
    assets = rets_df.columns
    n_assets = len(assets)
    n = len(dates)

    weights_hist = np.zeros((n, n_assets))
    port_ret = np.zeros(n)

    for t in range(start_idx, n - 1):
        cov_window = rets_df.iloc[: t + 1]
        Sigma = ewm_cov_matrix(cov_window, halflife=cov_halflife)

        w = cp.Variable(n_assets)

        # ===== 目的関数 =====
        obj = cp.Minimize(0.5 * cp.quad_form(w, Sigma))

        # ===== 制約 =====
        constraints = [
            w >= w_lb,
            w <= w_ub,
            cp.sum(w) == 1.0,     # ★★ これが必須 ★★
        ]

        prob = cp.Problem(obj, constraints)
        prob.solve(solver=cp.OSQP)

        if w.value is None:
            w_opt = np.ones(n_assets) / n_assets
        else:
            w_opt = np.array(w.value).flatten()

        weights_hist[t] = w_opt
        r_next = rets_df.iloc[t + 1].values
        port_ret[t + 1] = float(np.dot(w_opt, r_next))

    weights_df = pd.DataFrame(weights_hist, index=dates, columns=assets)
    port_ret_series = pd.Series(port_ret, index=dates)
    wealth = (1.0 + port_ret_series).cumprod()

    return {
        "weights": weights_df,
        "port_ret": port_ret_series,
        "wealth": wealth,
    }
```

これで **毎日ポートフォリオ重みは必ず合計1** になります。

* * *

🔧 2. MV(JM-XGB) の修正版
=====================

### → bearish 資産を 0 にしつつ、bullish 資産で合計 1 にしたい

あなたの MV(JM-XGB) は bearish 資産を除外しますよね：

```python
for j in range(n_assets):
    if not bullish_mask[j]:
        constraints.append(w[j] == 0)
```

この制約を残したまま総和＝1 にするには、  
**「bullish 資産のウェイトのみ」で Σ w\_j = 1 を課す** 必要があります。

* * *

✔ 修正（最小変更）
----------

```python
# bearish は w_j = 0
for j in range(n_assets):
    if not bullish_mask[j]:
        constraints.append(w[j] == 0)

# bullish 資産のみに対して予算制約
constraints.append(cp.sum(w[bullish_mask]) == 1.0)
```

### ※ 注意点

*   論文のように「bullish < 4 のときは RF に逃げる」処理を入れたい場合、
    *   そのケースだけは「フルリスクフリー → risky 重み合計0」になるため  
        → **資産重みの合計は 0**（＝現金100%）
*   「常に risky 資産で合計1」としたいなら  
    → bullish<4 の分岐を消すか、または bearish が多い日も含めて bullish に比例按分します。

* * *

🧩 3. 完成形（MV(JM-XGB) の最適化制約）
============================

あなたの `backtest_mv_jm_xgb` 内の最適化部分を以下のように書き換えます：

```python
# ====== 2) 最適化問題 ======
w = cp.Variable(n_assets)

risk_term  = 0.5 * gamma_risk * cp.quad_form(w, Sigma)
ret_term   = - mu_vec @ w
trade_term = gamma_trade * cp.norm1(w - w_prev)
obj = cp.Minimize(risk_term + ret_term + trade_term)

constraints = [
    w >= w_lb,
    w <= w_ub,
]

# bearish は投資禁止
for j in range(n_assets):
    if not bullish_mask[j]:
        constraints.append(w[j] == 0)

# bullish 資産だけで総和 1 にする（ここが重要！）
constraints.append(cp.sum(w[bullish_mask]) == 1.0)

prob = cp.Problem(obj, constraints)
prob.solve(solver=cp.OSQP)
```

* * *

📌 4. 牛クマが極端に偏った日の扱い（重要）
========================

論文（セクター ETF）でも起きますが、  
**bullish 資産が少なすぎる日（例：1銘柄だけ）** の場合：

*   Σ w = 1 を課すと → 1銘柄に 100% 乗る
*   ダウンサイド・リスクが急増する

したがって、安定のために以下のいずれかを推奨します：

* * *

### ✔ 推奨A（論文と同じ）

**bullish < 4 の日は risky=0、RF=100% とする**

既にあなたのコードにもある：

```python
if bullish_mask.sum() < min_bullish:
    w_opt = np.zeros(n_assets)
```

※ この場合 **weights の合計は 0**（= risky 0%、現金100%）  
→ グラフ化時は

```
total_weight = risky_weight_sum + rf_weight
```

と解釈すればよい。

* * *

### ✔ 推奨B（常に w\_sum=1 にしたいなら）

**bullish が 1~2 銘柄しかなくても、強制的に Σ w = 1 にする**

ただしこれは「ハイリスク集中」になるため、  
実務ではあまり推奨されません。

* * *

🔎 結論（最重要ポイント）
==============

### **「各時点でウェイト総和＝1」にしたいだけなら以下の1行を追加するだけ。**

* * *

**MinVar**
----------

```python
constraints.append(cp.sum(w) == 1.0)
```

* * *

**MV(JM-XGB)**
--------------

```python
constraints.append(cp.sum(w[bullish_mask]) == 1.0)
```

bearish 禁止を維持したまま  
bullish 資産で正規化されるようになります。

* * *

必要なら、

*   「現金（RF）重みも含めて Σ w = 1」にするか
*   「risky のみ Σ w =1」にするか
*   「bull < 4 のときどう扱うか」

など、運用ルールをどう整理したいかに合わせて  
完全版のコードを再構築しますのでお知らせください。

## Response:
思考時間: 6s

了解です、ルールを整理すると：

*   **全資産 bear（bull が 1つもない）**  
    → risky 資産は全部 0、**現金 100%**
*   **bull が 1つ以上ある場合**  
    → **bull の資産だけで合計 100% を配分**（risky 内で Σw=1, 現金 0）

にしたい、ということですね。

`backtest_mv_jm_xgb` の中の最適化部分だけ、そこに合わせて書き換えればOKです。

* * *

修正すべきポイント（ループ内の if 部分）
----------------------

今はだいたいこんな流れになっているはずです：

```python
if bullish_mask.sum() < min_bullish:
    w_opt = np.zeros(n_assets)
else:
    # 共分散推定
    cov_window = rets_df.iloc[: t + 1]
    Sigma = ewm_cov_matrix(cov_window, halflife=cov_halflife)

    w = cp.Variable(n_assets)

    risk_term  = 0.5 * gamma_risk * cp.quad_form(w, Sigma)
    ret_term   = - mu_vec @ w
    trade_term = gamma_trade * cp.norm1(w - w_prev)
    obj = cp.Minimize(risk_term + ret_term + trade_term)

    constraints = [
        w >= w_lb,
        w <= w_ub,
        # 以前はここに sum(w) <= max_leverage とかがあったはず
    ]

    for j in range(n_assets):
        if not bullish_mask[j]:
            constraints.append(w[j] == 0.0)

    prob = cp.Problem(obj, constraints)
    prob.solve(...)
    ...
```

これを、あなたのルールに合わせて以下のように変更します。

* * *

修正版コード（ループ内の MVO 部分）
--------------------

```python
    # --- 2) MVO 最適化 ---
    n_bull = bullish_mask.sum()

    if n_bull == 0:
        # ① 全資産 bear の場合：risk 資産は全部 0 → 現金 100%
        w_opt = np.zeros(n_assets)

    else:
        # ② bull が 1つ以上ある場合：bull 資産だけで Σw=1 にする（現金 0）
        cov_window = rets_df.iloc[: t + 1]
        Sigma = ewm_cov_matrix(cov_window, halflife=cov_halflife)

        w = cp.Variable(n_assets)

        risk_term  = 0.5 * gamma_risk * cp.quad_form(w, Sigma)
        ret_term   = - mu_vec @ w
        trade_term = gamma_trade * cp.norm1(w - w_prev)
        obj = cp.Minimize(risk_term + ret_term + trade_term)

        constraints = [
            w >= w_lb,
            w <= w_ub,
        ]

        # bearish 予測の資産は weight=0
        for j in range(n_assets):
            if not bullish_mask[j]:
                constraints.append(w[j] == 0.0)

        # ★ bull 資産だけで合計 1（現金 0）★
        constraints.append(cp.sum(w[bullish_mask]) == 1.0)

        prob = cp.Problem(obj, constraints)
        prob.solve(solver=cp.OSQP)

        if w.value is None:
            # 解けなかったときは、bull 資産に等分配（正規化）する
            w_opt = np.zeros(n_assets)
            w_opt[bullish_mask] = 1.0 / n_bull
        else:
            w_opt = np.array(w.value).flatten()
```

その下の部分（リターン計算）はこのままで大丈夫です：

```python
    weights_hist[t, :] = w_opt

    # 実際の次日の実現リターン
    r_next_vec = rets_df.iloc[t + 1].values

    risky_ret = np.dot(w_opt, r_next_vec)
    rf_weight = max(0.0, 1.0 - w_opt.sum())  # ← ここで現金比率が決まる

    total_ret = risky_ret + rf_weight * rf_daily

    port_ret[t + 1] = total_ret
    w_prev = w_opt
```

この設計だと：

*   **bull ≥ 1 の日**
    *   制約 `sum(w[bullish_mask]) == 1.0` → `w_opt.sum() == 1.0`
    *   `rf_weight = 1 - 1 = 0` → 現金 0、risky 100%
*   **全て bear の日（n\_bull == 0）**
    *   `w_opt = 0` ベクトル
    *   `rf_weight = 1 - 0 = 1` → 現金 100%

となって、希望どおりのルールになります。

* * *

もし MinVar 側も同じルール（レジームは使わず常に Σw=1, RF=0）で揃えたい場合は、  
別途 MinVar の制約も `cp.sum(w) == 1.0` に直せばOKです。

まずはこの修正を入れて、各時点の `weights_hist.sum(axis=1)` と `rf_weight` が  
想定どおり（all-bear だけ risky=0、それ以外は risky=1）になっているか確認してみてください。

## Response:
OK、整理して**フルコード一式＋使い方**をまとめます。  
前提として、`misc.py` はすでにあるもの（JumpModel / feature\_engineer など）を使います。

* * *

1\. 必要な import
--------------

```python
import datetime
import warnings
warnings.simplefilter('ignore')

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import cvxpy as cp
from xgboost import XGBClassifier

import misc  # あなたの JumpModel / feature_engineer など
```

* * *

2\. ジャンプペナルティ λ を TS-CV で選ぶ関数
-----------------------------

```python
def select_jump_penalty_on_window(
    rets_window: pd.Series,
    n_regimes: int,
    lambda_grid,
    train_ratio: float = 0.7,
):
    """
    時系列 CV を用いて、その窓の中で 0/1 戦略 Sharpe を最大にする λ を選ぶ簡易版。

    rets_window: 単一資産のログリターン（Series, DateTimeIndex）
    lambda_grid: 候補の jump_penalty の配列（例: [0.0, 0.1, 0.3, 1, 3, 10, 30, 100]）
    """
    n = len(rets_window)
    if n < 100:
        return lambda_grid[0]

    # 特徴量
    X = misc.feature_engineer(rets_window)

    clipper = misc.Clipper(mul=3)
    scaler = misc.Scaler()
    X_clipped = clipper.fit_transform(X)
    X_scaled = scaler.fit_transform(X_clipped)

    split_idx = int(n * train_ratio)
    X_train = X_scaled[:split_idx]
    rets_train = rets_window.iloc[:split_idx]

    X_val_all = X_scaled[split_idx-1:-1]
    rets_val_all = rets_window.iloc[split_idx:]

    if len(rets_val_all) < 10:
        return lambda_grid[0]

    best_lambda = None
    best_sharpe = -np.inf

    for lam in lambda_grid:
        # 1) train 部分で JumpModel をフィット
        jm = misc.JumpModel(n_regimes=n_regimes, jump_penalty=lam)
        jm.fit(X_train)

        labels_train = misc.rearange_labels(jm.labels, rets_train.values)

        # 2) s_{t+1} を教師ラベルにする
        y = labels_train[1:split_idx]
        X_clf = X_scaled[:split_idx-1]

        if len(np.unique(y)) < 2:
            continue

        clf = XGBClassifier()
        clf.fit(X_clf, y.astype(int))

        # 3) validation 部分で 0/1 戦略リターンを計算
        daily_returns = []
        for i in range(len(X_val_all)):
            x_i = X_val_all[i].reshape(1, -1)
            pred_reg_next = clf.predict(x_i)[0]
            r_next = float(rets_val_all.iloc[i])
            if pred_reg_next == 1:   # bull なら risky
                daily_returns.append(r_next)
            else:                    # bear なら cash
                daily_returns.append(0.0)

        daily_returns = np.array(daily_returns)
        if daily_returns.std(ddof=1) == 0:
            sharpe = -np.inf
        else:
            sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std(ddof=1)

        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_lambda = lam

    if best_lambda is None:
        best_lambda = lambda_grid[0]

    return best_lambda
```

* * *

3\. 単一資産に対するオンライン λ 更新＋レジーム予測＋レジーム別 μ
-------------------------------------

```python
def run_with_online_lambda_and_mu(
    rets: pd.Series,
    start_idx: int,
    n_regimes: int,
    init_jump_penalty: float,
    fit_freq_days: int,
    lambda_grid=None,
    cv_window_days: int = 252 * 5,
    cv_freq_days: int = 21 * 3,
):
    """
    単一資産のログリターン rets に対して、
    - λ のオンライン更新（TS-CV）
    - JM＋XGB のオンライン学習
    - 各時点の「明日のレジーム予測」とレジーム別平均リターン μ_bull, μ_bear
    を返す。
    """
    if lambda_grid is None:
        lambda_grid = [0.0, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

    scaler = misc.Scaler()
    clipper = misc.Clipper(mul=3)

    n = len(rets)
    index = rets.index

    regime_pred = np.full(n, np.nan)
    lambda_path = np.full(n, np.nan)
    mu_bull_path = np.full(n, np.nan)
    mu_bear_path = np.full(n, np.nan)

    current_lambda = init_jump_penalty
    last_cv_date = None
    last_fit_date = None

    model = None
    clf = None
    mu_bull = 0.0
    mu_bear = 0.0

    def should_fit(last_date, current_date, freq_days):
        current = current_date.date()
        if last_date is None:
            return True
        delta = current - last_date
        return delta.days >= freq_days

    # 時間ループ
    for t in range(start_idx, n - 1):
        obs = rets.iloc[: t + 1]
        current_date = obs.index[-1]

        # 1) λ の TS-CV 更新
        if should_fit(last_cv_date, current_date, cv_freq_days) and len(obs) >= cv_window_days:
            window = obs.iloc[-cv_window_days:]
            best_lambda = select_jump_penalty_on_window(
                window,
                n_regimes=n_regimes,
                lambda_grid=lambda_grid,
            )
            current_lambda = best_lambda
            last_cv_date = current_date.date()

            # λ を変えたので次回必ず再フィット
            last_fit_date = None

        # 2) 必要なら JM + XGB を再フィット
        if (last_fit_date is None) or should_fit(last_fit_date, current_date, fit_freq_days):
            last_fit_date = current_date.date()

            X = misc.feature_engineer(obs)
            X_proc = scaler.fit_transform(clipper.fit_transform(X))

            # JM fit
            model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=current_lambda)
            model.fit(X_proc)

            labels = misc.rearange_labels(model.labels, obs.values)

            # レジーム別 μ
            if (labels == 1).any():
                mu_bull = obs.values[labels == 1].mean()
            else:
                mu_bull = 0.0
            if (labels == 0).any():
                mu_bear = obs.values[labels == 0].mean()
            else:
                mu_bear = 0.0

            # s_{t+1} を教師ラベルに
            y = pd.Series(labels, index=obs.index).shift(-1)
            train_idx = y.dropna().index

            clf = XGBClassifier()
            clf.fit(
                pd.DataFrame(X_proc, index=obs.index).loc[train_idx],
                y.loc[train_idx].astype(int),
            )
        else:
            X = misc.feature_engineer(obs)
            X_proc = scaler.transform(clipper.transform(X))

        # 3) 「明日のレジーム」を 1ステップ先予測
        x_last = pd.DataFrame(X_proc, index=obs.index).iloc[[-1]]
        pred_reg = clf.predict(x_last)[0]

        regime_pred[t] = pred_reg
        lambda_path[t] = current_lambda
        mu_bull_path[t] = mu_bull
        mu_bear_path[t] = mu_bear

    out = {
        "regime_pred": pd.Series(regime_pred, index=index),
        "lambda": pd.Series(lambda_path, index=index),
        "mu_bull": pd.Series(mu_bull_path, index=index),
        "mu_bear": pd.Series(mu_bear_path, index=index),
    }
    return out
```

* * *

4\. 共分散推定（EWM）
--------------

```python
def ewm_cov_matrix(rets_window: pd.DataFrame, halflife: int = 252):
    """
    過去リターンから EWM 共分散を推定し、最後の時点の共分散行列を返す。
    rets_window: 通常リターン DataFrame (T, N)
    """
    cov_all = rets_window.ewm(halflife=halflife).cov()
    last_date = rets_window.index[-1]
    cov_last = cov_all.xs(last_date, level=0)
    return cov_last.values  # (N, N)
```

* * *

5\. MV(JM-XGB) バックテスト（bull>=1 なら risky 100%, 全bearなら cash 100%）
---------------------------------------------------------------

```python
def backtest_mv_jm_xgb(
    rets_df: pd.DataFrame,     # 通常リターン (T, N)
    asset_results: dict,       # 各資産の run_with_online_lambda_and_mu 結果
    start_idx: int,
    rf_daily: float = 0.0,
    gamma_risk: float = 10.0,
    gamma_trade: float = 1.0,
    w_lb: float = 0.0,
    w_ub: float = 0.40,
    cov_halflife: int = 252,
    bear_floor: float = -0.001,   # bear μ の下限（-10bps）など
):
    """
    MV(JM-XGB) ポートフォリオをバックテストする。

    ルール:
    - 各資産ごとに「明日のレジーム予測」とレジーム別 μ_bull, μ_bear を用意
    - reg=1 (bull) → μ_bull, reg=0 (bear) → max(μ_bear, bear_floor)
    - bull 資産が 1つ以上ある場合:
        ・bear の w_j=0
        ・bull 資産だけで Σ w_j = 1（現金 0）
    - bull が 0（全て bear）の場合:
        ・全 risky 資産 w_j=0（現金 100%）
    """
    dates = rets_df.index
    assets = list(rets_df.columns)
    n_assets = len(assets)
    n = len(dates)

    weights_hist = np.zeros((n, n_assets))
    port_ret = np.zeros(n)
    lambda_hist = np.zeros((n, n_assets))

    w_prev = np.zeros(n_assets)

    for t in range(start_idx, n - 1):
        date_t = dates[t]

        # 1) μ ベクトルと bull/bear 情報を作る
        mu_vec = np.zeros(n_assets)
        bullish_mask = np.zeros(n_assets, dtype=bool)

        for j, asset in enumerate(assets):
            res = asset_results[asset]
            reg = res["regime_pred"].loc[date_t]
            mu_bull = res["mu_bull"].loc[date_t]
            mu_bear = res["mu_bear"].loc[date_t]
            lam = res["lambda"].loc[date_t]

            if reg == 1:
                mu_j = mu_bull
                bullish_mask[j] = True
            else:
                mu_j = max(mu_bear, bear_floor)

            mu_vec[j] = mu_j
            lambda_hist[t, j] = lam

        n_bull = bullish_mask.sum()

        if n_bull == 0:
            # 全 bear → risky 0, 現金 100%
            w_opt = np.zeros(n_assets)
        else:
            # bull ≥ 1 → bull 資産だけで Σw=1
            cov_window = rets_df.iloc[: t + 1]
            Sigma = ewm_cov_matrix(cov_window, halflife=cov_halflife)

            w = cp.Variable(n_assets)

            risk_term  = 0.5 * gamma_risk * cp.quad_form(w, Sigma)
            ret_term   = - mu_vec @ w
            trade_term = gamma_trade * cp.norm1(w - w_prev)
            obj = cp.Minimize(risk_term + ret_term + trade_term)

            constraints = [
                w >= w_lb,
                w <= w_ub,
            ]

            # bear 資産は w=0
            for j in range(n_assets):
                if not bullish_mask[j]:
                    constraints.append(w[j] == 0.0)

            # bull 資産だけで合計 1
            constraints.append(cp.sum(w[bullish_mask]) == 1.0)

            prob = cp.Problem(obj, constraints)
            prob.solve(solver=cp.OSQP)

            if w.value is None:
                # 解けない場合は bull 資産に等分配
                w_opt = np.zeros(n_assets)
                w_opt[bullish_mask] = 1.0 / n_bull
            else:
                w_opt = np.array(w.value).flatten()

        # 3) リターンと wealth 更新
        weights_hist[t, :] = w_opt
        r_next_vec = rets_df.iloc[t + 1].values

        risky_ret = np.dot(w_opt, r_next_vec)
        rf_weight = max(0.0, 1.0 - w_opt.sum())   # bull>=1 の日は 0, all-bearの日は1
        total_ret = risky_ret + rf_weight * rf_daily

        port_ret[t + 1] = total_ret
        w_prev = w_opt

    weights_hist_df = pd.DataFrame(weights_hist, index=dates, columns=assets)
    lambda_hist_df = pd.DataFrame(lambda_hist, index=dates, columns=assets)
    port_ret_series = pd.Series(port_ret, index=dates)
    wealth = (1.0 + port_ret_series).cumprod()

    return {
        "weights": weights_hist_df,
        "lambda": lambda_hist_df,
        "port_ret": port_ret_series,
        "wealth": wealth,
    }
```

* * *

6\. Buy&Hold / MinVar（比較用）
--------------------------

```python
def backtest_buy_and_hold(
    rets_df: pd.DataFrame,
    start_idx: int,
    init_weights: np.ndarray = None,
):
    dates = rets_df.index
    assets = rets_df.columns
    n_assets = len(assets)
    n = len(dates)

    if init_weights is None:
        init_weights = np.ones(n_assets) / n_assets

    w = init_weights.copy()
    weights_hist = np.zeros((n, n_assets))
    port_ret = np.zeros(n)

    for t in range(start_idx, n - 1):
        weights_hist[t, :] = w
        r_next = rets_df.iloc[t + 1].values
        port_ret[t + 1] = float(np.dot(w, r_next))

    weights_df = pd.DataFrame(weights_hist, index=dates, columns=assets)
    port_ret_series = pd.Series(port_ret, index=dates)
    wealth = (1.0 + port_ret_series).cumprod()

    return {
        "weights": weights_df,
        "port_ret": port_ret_series,
        "wealth": wealth,
    }

def backtest_minvar(
    rets_df: pd.DataFrame,
    start_idx: int,
    cov_halflife: int = 252,
    w_lb: float = 0.0,
    w_ub: float = 0.40,
):
    dates = rets_df.index
    assets = rets_df.columns
    n_assets = len(assets)
    n = len(dates)

    weights_hist = np.zeros((n, n_assets))
    port_ret = np.zeros(n)

    for t in range(start_idx, n - 1):
        cov_window = rets_df.iloc[: t + 1]
        Sigma = ewm_cov_matrix(cov_window, halflife=cov_halflife)

        w = cp.Variable(n_assets)
        obj = cp.Minimize(0.5 * cp.quad_form(w, Sigma))

        constraints = [
            w >= w_lb,
            w <= w_ub,
            cp.sum(w) == 1.0,   # 常に risky 資産で 100%
        ]

        prob = cp.Problem(obj, constraints)
        prob.solve(solver=cp.OSQP)

        if w.value is None:
            w_opt = np.ones(n_assets) / n_assets
        else:
            w_opt = np.array(w.value).flatten()

        weights_hist[t, :] = w_opt
        r_next = rets_df.iloc[t + 1].values
        port_ret[t + 1] = float(np.dot(w_opt, r_next))

    weights_df = pd.DataFrame(weights_hist, index=dates, columns=assets)
    port_ret_series = pd.Series(port_ret, index=dates)
    wealth = (1.0 + port_ret_series).cumprod()

    return {
        "weights": weights_df,
        "port_ret": port_ret_series,
        "wealth": wealth,
    }
```

* * *

7\. 使い方例（from ダウンロード → 比較プロットまで）
--------------------------------

```python
# 1) データ取得
start_date = "2013-01-01"
end_date = datetime.datetime.now().strftime("%Y-%m-%d")

ticker = [
    "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"
]
df = yf.download(ticker, start=start_date, end=end_date)["Close"]

# ログリターン（JM / 特徴量用）
rets_log = np.log(df).diff().dropna()
# 通常リターン（ポートフォリオ計算用）
rets_arith = np.exp(rets_log) - 1.0

assets = rets_log.columns

# 2) 各資産について JM-XGB (オンライン λ 更新＋μ 推定)
start_idx_jm = 1000
n_regimes = 2
init_jump_penalty = 10.0
fit_freq_days = 7 * 4

lambda_grid = [0.0, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

asset_results = {}
for asset in assets:
    res = run_with_online_lambda_and_mu(
        rets=rets_log[asset],
        start_idx=start_idx_jm,
        n_regimes=n_regimes,
        init_jump_penalty=init_jump_penalty,
        fit_freq_days=fit_freq_days,
        lambda_grid=lambda_grid,
        cv_window_days=252*5,
        cv_freq_days=21*3,
    )
    asset_results[asset] = res

# 3) MV(JM-XGB) ポートフォリオ
start_idx_port = 1500   # 学習・CV の分だけ余裕を持たせる
mv_res = backtest_mv_jm_xgb(
    rets_df=rets_arith,
    asset_results=asset_results,
    start_idx=start_idx_port,
    rf_daily=0.0,
    gamma_risk=10.0,
    gamma_trade=1.0,
    w_lb=0.0,
    w_ub=0.40,
    cov_halflife=252,
    bear_floor=-0.001,
)
mv_wealth = mv_res["wealth"]

# 4) Buy&Hold / MinVar
bh_res = backtest_buy_and_hold(
    rets_df=rets_arith,
    start_idx=start_idx_port,
    init_weights=None,   # 等ウェイト
)
minvar_res = backtest_minvar(
    rets_df=rets_arith,
    start_idx=start_idx_port,
    cov_halflife=252,
    w_lb=0.0,
    w_ub=0.40,
)

# 5) 共通インデックスで比較
common_index = mv_wealth.index[start_idx_port:]
bh_wealth = bh_res["wealth"].loc[common_index].squeeze()
minvar_wealth = minvar_res["wealth"].loc[common_index].squeeze()
mv_wealth = mv_wealth.loc[common_index].squeeze()

plt.figure(figsize=(10, 5))
plt.plot(common_index, bh_wealth.values,     label="Buy & Hold (EW)")
plt.plot(common_index, minvar_wealth.values, label="MinVar")
plt.plot(common_index, mv_wealth.values,     label="MV(JM-XGB)")
plt.legend()
plt.ylabel("Wealth (Initial = 1)")
plt.xlabel("Date")
plt.title("Strategy Comparison: Buy&Hold vs MinVar vs MV(JM-XGB)")
plt.grid(True)
plt.tight_layout()
plt.show()
```

* * *

これで：

*   λ のオンライン更新（TS-CV）
*   各資産のレジーム別 μ 推定
*   「bull>=1 なら risky100%（bull 内で Σw=1）、全bearなら cash100%」
*   Buy&Hold / MinVar / MV(JM-XGB) の wealth 比較

まで一通り回せるはずです。  
もしどこかの部分で shape や index が合わないなど出たら、その箇所を貼ってくれればそこだけピンポイントで直します。

## Response:
思考時間: 1m 27s

いいですね、ちょうど論文に「XGBoost で何を入れているか」がかなり丁寧に書いてあるので、それをそのまま取り込む形で拡張していきましょう。

2406.09578v2

論文の構成はざっくりこうです：

*   **JM（Jump Model）用の特徴量**：各資産のリターンから作る 8 個の「return features」
    *   DD（downside deviation）のログ × 2つのハーフライフ
    *   平均リターン × 3つのハーフライフ
    *   Sortino ratio × 3つのハーフライフ
        2406.09578v2
*   **XGBoost 用の特徴量**：上の 8 個 ＋ マクロ要因 5 個（2Y 金利・イールドカーブ・VIX・stock-bond 相関）
    2406.09578v2

あなたのコードでは、

*   JM はすでに `misc.feature_engineer(rets)` を使っている
*   XGBoost の説明変数はまだシンプル

なので：

1.  **JM 用の特徴量関数**（論文 Table 2 を反映）
2.  **XGBoost 用の拡張特徴量関数**（JM 用 + Table 3 のマクロ）
3.  **使い方：run の中で XGB の X を差し替える例**

という流れでフルコードを出します。

* * *

1\. JM 用の特徴量（return features 8個）
--------------------------------

まずは `misc.py` に、JM 用に論文の Table 2 に対応する関数を追加します。

2406.09578v2

```python
# misc.py に追加

import numpy as np
import pandas as pd

def _ewm_mean(x: pd.Series, hl: int) -> pd.Series:
    """Exponentially weighted moving average."""
    return x.ewm(halflife=hl, adjust=False).mean()

def _ewm_downside_log(x: pd.Series, hl: int) -> pd.Series:
    """
    EWM downside deviation (log scale).
    論文では downside deviation をログ変換して使っている。:contentReference[oaicite:4]{index=4}
    """
    neg = x.clip(upper=0.0)  # マイナスリターンのみ
    dd = np.sqrt((neg**2).ewm(halflife=hl, adjust=False).mean())
    return np.log(dd + 1e-8)

def _ewm_sortino(x: pd.Series, hl: int) -> pd.Series:
    """
    EWM Sortino ratio = (EWM mean) / (EWM downside deviation).
    downside はログスケールではなく実数レベルで割る。
    """
    mu = _ewm_mean(x, hl)
    dd_log = _ewm_downside_log(x, hl)
    dd = np.exp(dd_log)  # 逆変換
    return mu / (dd + 1e-8)

def feature_engineer_jm(rets: pd.Series) -> pd.DataFrame:
    """
    JumpModel 用の特徴量（論文 Table 2 準拠）:contentReference[oaicite:5]{index=5}

    rets : 単一資産の「超過リターン」シリーズを想定（log でも arith でも OK、一貫していればよい）
    戻り値 : index=日付, 各種 EWM 特徴量の DataFrame
    """
    feats = pd.DataFrame(index=rets.index)

    # Downside Deviation (log scale), halflife 5, 21
    feats["dd_log_hl5"] = _ewm_downside_log(rets, 5)
    feats["dd_log_hl21"] = _ewm_downside_log(rets, 21)

    # Average return, halflife 5, 10, 21
    for hl in [5, 10, 21]:
        feats[f"mean_hl{hl}"] = _ewm_mean(rets, hl)

    # Sortino ratio, halflife 5, 10, 21
    for hl in [5, 10, 21]:
        feats[f"sortino_hl{hl}"] = _ewm_sortino(rets, hl)

    return feats
```

※ もともとの `feature_engineer(rets)` は JM 用に使っていると思うので、

*   そのまま残して
*   新しく `feature_engineer_jm` を **JM 用**  
    という役割分担にしておくと混乱しません。

* * *

2\. XGBoost 用の拡張特徴量（JM＋マクロ 5個）
------------------------------

論文 Table 3 の macro features に相当する部分を、別関数で実装します。

2406.09578v2

### マクロデータの想定

`macro_df` という DataFrame を次のように想定します（列名は自由ですが、関数の引数で指定できるようにします）：

*   2年金利：`col_2y`（例: FRED の `DGS2`）
*   10年金利：`col_10y`（例: `DGS10`） → slope = 10y - 2y
*   VIX：`col_vix`（例: `VIXCLS`）
*   株リターン：`col_stock_ret`（例: S&P500 or LargeCap の日次リターン）
*   債券リターン：`col_bond_ret`（例: AggBond の日次リターン）

```python
# misc.py に追加

def feature_engineer_xgb(
    rets: pd.Series,
    macro_df: pd.DataFrame,
    col_2y: str = "y2",
    col_10y: str = "y10",
    col_vix: str = "vix",
    col_stock_ret: str = "stock_ret",
    col_bond_ret: str = "bond_ret",
) -> pd.DataFrame:
    """
    XGBoost 用の拡張特徴量（return features 8個 + macro features 5個）。:contentReference[oaicite:7]{index=7}

    Parameters
    ----------
    rets : pd.Series
        対象資産の日次（超過）リターン。
    macro_df : pd.DataFrame
        日付 index を rets と揃えたマクロ系列 DataFrame。
        以下の列を含むことを想定:
          - col_2y       : 米2年国債金利
          - col_10y      : 米10年国債金利
          - col_vix      : VIX インデックス
          - col_stock_ret: 株式リターン（例: S&P500）
          - col_bond_ret : 債券リターン（例: AggBond）

    Returns
    -------
    feats_xgb : pd.DataFrame
        JM 用 return features + macro features を結合した説明変数。
    """
    # --- 1) JM 用の return features ---
    feats = feature_engineer_jm(rets).copy()

    # --- 2) macro_df を rets の index に合わせて揃える ---
    macro = macro_df[[col_2y, col_10y, col_vix, col_stock_ret, col_bond_ret]].copy()
    macro = macro.reindex(rets.index).ffill()  # 日付を揃えつつ前方埋め

    # 2-year yield: difference & EWMA(hl=21)
    y2 = macro[col_2y]
    y2_diff = y2.diff()
    feats["y2_diff"] = y2_diff
    feats["y2_diff_ewm21"] = y2_diff.ewm(halflife=21, adjust=False).mean()

    # Yield curve slope = 10y - 2y
    slope = macro[col_10y] - macro[col_2y]
    feats["slope_ewm10"] = slope.ewm(halflife=10, adjust=False).mean()

    slope_diff = slope.diff()
    feats["slope_diff_ewm21"] = slope_diff.ewm(halflife=21, adjust=False).mean()

    # VIX log-diff & EWMA(hl=63)
    vix = macro[col_vix]
    vix_ld = np.log(vix.replace(0, np.nan)).diff()
    feats["vix_ld_ewm63"] = vix_ld.ewm(halflife=63, adjust=False).mean()

    # Stock-Bond correlation, 1-year rolling
    stock_ret = macro[col_stock_ret]
    bond_ret = macro[col_bond_ret]
    feats["stock_bond_corr_1y"] = stock_ret.rolling(window=252).corr(bond_ret)

    # 最後に NaN を少し埋める（先頭の窓不足など）
    feats = feats.fillna(method="bfill").fillna(method="ffill")

    return feats
```

これで、論文の XGB 部分で使っている説明変数セット（return features + macro 5 個）とかなり近いものになります。

2406.09578v2

* * *

3\. run 内での使い方（XGBoost 用 X を差し替える）
----------------------------------

あなたの現在の `run` 関数は、ざっくりこんな構造でした：

```python
def run(rets, start_idx, n_regimes, jump_penalty, freq):
    scaler = misc.Scaler()
    clipper = misc.Clipper(mul=3)
    model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=jump_penalty)
    clf = XGBClassifier()

    ...
    while True:
        ...
        obs = rets[:current_idx]
        X = misc.feature_engineer(obs)  # ← ここを差し替える
        if should_fit(...):
            X_processed = scaler.fit_transform(clipper.fit_transform(X))
            model.fit(X_processed)
            ...
            clf.fit(X_processed.loc[y_idx], y.loc[y_idx].astype(int))
        ...
```

これを、

*   JM 用：`feature_engineer_jm`
*   XGB 用：`feature_engineer_xgb`

に分けて使う形に書き換えます。

### 3-1. run のシグネチャに macro\_df を追加

```python
def run(
    rets: pd.Series,
    start_idx: int,
    n_regimes: int,
    jump_penalty: float,
    freq: int,
    macro_df: pd.DataFrame,
):
    """
    rets     : 単一資産のログリターン
    macro_df : マクロ系列 (2y,10y,VIX,stock_ret,bond_ret などを含む DataFrame)
    """
    scaler_jm = misc.Scaler()
    clipper_jm = misc.Clipper(mul=3)

    scaler_xgb = misc.Scaler()
    clipper_xgb = misc.Clipper(mul=3)

    model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=jump_penalty)
    clf = XGBClassifier()

    last_fit_date = None

    def should_fit(last_fit_date, current_date, freq):
        current = current_date.date()
        if last_fit_date is None:
            return True
        delta = current - last_fit_date
        return delta.days >= freq

    n = rets.shape[0]
    current_idx = start_idx
    end_idx = n - 1
    w = np.ones(n)

    while True:
        current_idx += 1
        obs = rets.iloc[:current_idx]
        current_date = obs.index[-1]

        # --- JM 用特徴量 ---
        X_jm = misc.feature_engineer_jm(obs)

        # --- XGB 用特徴量（JM + macro）---
        X_xgb = misc.feature_engineer_xgb(
            obs,
            macro_df=macro_df,
            col_2y="y2",
            col_10y="y10",
            col_vix="vix",
            col_stock_ret="stock_ret",
            col_bond_ret="bond_ret",
        )

        if should_fit(last_fit_date, current_date, freq):
            last_fit_date = current_date.date()

            # JM の学習
            X_jm_proc = scaler_jm.fit_transform(clipper_jm.fit_transform(X_jm))
            model.fit(X_jm_proc)

            labels = misc.rearange_labels(model.labels, obs.values)
            y = pd.Series(labels, index=obs.index).shift(-1)
            y_idx = y.dropna().index

            # XGB の学習（拡張特徴量を使用）
            X_xgb_proc = scaler_xgb.fit_transform(clipper_xgb.fit_transform(X_xgb))
            X_clf = pd.DataFrame(X_xgb_proc, index=obs.index, columns=X_xgb.columns)

            clf.fit(
                X_clf.loc[y_idx],
                y.loc[y_idx].astype(int),
            )

        else:
            # 再学習なしで特徴量だけ更新
            X_jm_proc = scaler_jm.transform(clipper_jm.transform(X_jm))
            X_xgb_proc = scaler_xgb.transform(clipper_xgb.transform(X_xgb))

        # 最新日の XGB 入力で regime 予測
        X_clf_latest = pd.DataFrame(
            X_xgb_proc,
            index=obs.index,
            columns=X_xgb.columns,
        ).iloc[[-1]]

        w[current_idx] = clf.predict(X_clf_latest)[0]

        if current_idx == end_idx:
            break

    return w
```

* * *

4\. マクロ DataFrame のイメージ（簡単な例）
-----------------------------

最後に、「macro\_df をどう作るか」のイメージだけ示しておきます。  
（ここは既に FRED 用のコードを持っているなら、その出力を整形すれば OK です）

```python
# 例: 2年/10年金利, VIX, S&P500, AggBond を取得して整形したと仮定

macro_df = pd.DataFrame(index=some_index)
macro_df["y2"]        = series_2y_yield
macro_df["y10"]       = series_10y_yield
macro_df["vix"]       = series_vix
macro_df["stock_ret"] = sp500_returns  # 例えば SPY の log/arith リターン
macro_df["bond_ret"]  = aggbond_returns

# sector ETF 1つに対して
asset = "XLB"
w = run(
    rets=rets[asset],
    start_idx=1000,
    n_regimes=2,
    jump_penalty=10.0,
    freq=28,
    macro_df=macro_df,
)
```

* * *

これで、

*   論文準拠の **return features 8個**（DD, mean, Sortino × 複数 HL）
*   論文 Table 3 の **macro features 5個**（2Y diff, slope, slope diff, VIX logdiff, stock-bond corr）  
    を XGBoost の説明変数に取り込める形になりました。
    2406.09578v2

あとは、

*   どのマクロ系列を使うか（SPY / AGG なのか、LargeCap / AggBond なのか）
*   どの資産を `stock_ret` / `bond_ret` にするか

をあなたの環境に合わせて macro\_df を作ってあげれば、そのまま動かせるはずです。

## Response:
思考時間: 1m 8s

やりたいことは：

> JM→レジーム → LGBM で s\_{t+1} を予測 →  
> その予測に基づく **0/1 戦略 or 1/0 戦略** で  
> 「何もしない or Buy&Hold」よりマシなパフォーマンスを出したい

ですね。

今のコードを見ると、**ロジック＆ラベリングの設計**がかなり効いていて、

*   時間軸のずれ（どのリターンにどのシグナルを掛けるか）
*   1/0 vs 0/1 のどちらが「bull」なのか
*   特徴量の情報量不足
*   出力ラベルの 0/1 をそのままシグナルにしている（確率使ってない）

あたりが、パフォーマンスが出ない主因になりそうです。

ここでは

1.  **バックテストの時間整合性をきちんと取る**
2.  **0/1 と 1/0 の両方を自動で評価し、良い方の戦略を採用**
3.  **LightGBM の「確率」を使って閾値付きシグナルにする**
4.  （オプション）**テクニカルな追加特徴量**を少し入れる

までを、一気にコード改良します。

* * *

1\. シグナルとリターンの時間整合性を修正
----------------------

いま：

```python
w[current_idx] = clf.predict(... 最新行 ...)
...
ax.plot((1 + w * rets).cumprod())
```

となっていて、**時点 t のシグナル w\_t を同じ日のリターン r\_t に掛けている**状態です。

しかし教師ラベルは `y = labels.shift(-1)` なので、

*   特徴量 X\_t → ラベル y\_t = s\_{t+1}
*   つまり「**翌日のレジーム**」を学習

しているのに、実際のトレードでは **その日のリターンに掛けてしまっている**。  
正しくは

> 時点 t で予測したシグナル w\_t を、t+1 日目のリターンに掛ける

なので、バックテスト用には「**1 日シフト**」が必要です。

### ✅ バックテスト用の関数を追加（0/1 戦略のパフォーマンス）

```python
def backtest_binary_signal(log_rets: pd.Series, w: pd.Series):
    """
    log_rets: ログリターン（Series, index=日付）
    w       : {0,1} のシグナル（同じ index）
              解釈: 日付 t における w[t] は「t+1 日に risky に乗るかどうか」を表す

    戻り値:
      - wealth: 初期1の資産曲線（Series）
      - sharpe: 年率換算シャープレシオ（単純計算）
    """
    # ログ→通常リターン
    r = np.exp(log_rets) - 1.0

    # 時間整合性: w[t] を r[t+1] に掛ける → index を1日ずらす
    w = w.astype(float)
    w_lag = w.shift(1).fillna(0.0)   # 初日シグナルは使えないので 0

    aligned_index = log_rets.index
    w_lag = w_lag.reindex(aligned_index).fillna(0.0)

    strat_ret = w_lag * r
    wealth = (1.0 + strat_ret).cumprod()

    if strat_ret.std(ddof=1) == 0:
        sharpe = 0.0
    else:
        sharpe = np.sqrt(252) * strat_ret.mean() / strat_ret.std(ddof=1)

    return wealth, sharpe
```

以後、戦略の評価は

```python
wealth_01, sharpe_01 = backtest_binary_signal(rets[asset], out["w"])
```

のように行います。

* * *

2\. 0/1 vs 1/0 を**自動で比較して良い方を採用**
---------------------------------

同じシグナル `w` に対して、

*   「1 のときロング、0 のときキャッシュ」：`w`
*   「0 のときロング、1 のときキャッシュ」：`1 - w`

の Sharpe を両方計算し、**Sharpe が高い方のマッピングを自動採用**します。

```python
def choose_best_mapping(log_rets: pd.Series, w_raw: pd.Series):
    """
    w_raw: {0,1} の生シグナル
    戻り値:
      - best_w: 採用するシグナル ({0,1})
      - info  : dict（どっちを採用したか、Sharpeなど）
    """
    w_raw = pd.Series(w_raw, index=log_rets.index)

    wealth_01, sharpe_01 = backtest_binary_signal(log_rets, w_raw)
    wealth_10, sharpe_10 = backtest_binary_signal(log_rets, 1 - w_raw)

    if sharpe_10 > sharpe_01:
        return (1 - w_raw), {
            "mode": "long_when_0",
            "sharpe": sharpe_10,
            "alt_sharpe": sharpe_01,
            "wealth": wealth_10,
        }
    else:
        return w_raw, {
            "mode": "long_when_1",
            "sharpe": sharpe_01,
            "alt_sharpe": sharpe_10,
            "wealth": wealth_01,
        }
```

これを `run_with_online_lambda` の**外側**で使います：

```python
out = run_with_online_lambda(...)
w_raw = out["w"]

w_best, info = choose_best_mapping(rets[asset], w_raw)
print(asset, info["mode"], info["sharpe"])

# プロットも w_best ベースに
wealth = info["wealth"]
plt.figure(figsize=(7,3))
plt.plot(wealth.index, wealth.values, label=f"Strategy ({info['mode']})")
plt.plot(wealth.index, (1+ (np.exp(rets[asset])-1)).cumprod(), label="Buy&Hold", alpha=0.5)
plt.legend(); plt.grid(); plt.show()
```

これで「0/1 戦略がダメだが 1/0 戦略は効く」ケースも自動で拾えます。

* * *

3\. LightGBM の**確率**と閾値を使ってシグナルを洗練
----------------------------------

いまは

```python
w[current_idx] = clf.predict(... 最新行 ...)
```

と、**0/1 のハードな予測**をそのままシグナルにしています。  
これだと

*   クラス境界ギリギリのサンプルでも 0/1 に振り分けられ、
*   ノイズトレードが多くなる

ので、**予測確率 `predict_proba` を使って、閾値を調整**します。

### ✅ run\_with\_online\_lambda のシグナル部分を修正

`run_with_online_lambda` の最後の方を次のように変更します（差分だけ示します）：

```python
# 置き換え前：
# w[current_idx] = clf.predict(
#     pd.DataFrame(X2_processed, columns=X2.columns).iloc[[-1]]
# )

# 置き換え後：
X2_df = pd.DataFrame(X2_processed, index=obs.index, columns=X2.columns)
x_latest = X2_df.iloc[[-1]]

# 確率で取得
proba = clf.predict_proba(x_latest)[0, 1]  # クラス1（bull）である確率

# 閾値（例: 0.55）を超えたときだけロング、それ以外はキャッシュ
threshold = 0.55
w[current_idx] = 1.0 if proba > threshold else 0.0
```

さらに、後で分析できるように**予測確率の path**も返すと便利です：

```python
proba_path = np.full(n, np.nan)
...
proba_path[current_idx] = proba
...
out = {
    "w": pd.Series(w, index=index),
    "lambda": pd.Series(lambdas, index=index),
    "mu_bull": pd.Series(mu_bull_path, index=index),
    "mu_bear": pd.Series(mu_bear_path, index=index),
    "proba": pd.Series(proba_path, index=index),
}
```

これで、

*   ROC を見て閾値をチューニング
*   高確信なときだけトレードする戦略

などにも発展させやすくなります。

* * *

4\. 特徴量の軽い拡張（テクニカル）
-------------------

すでに `feature_engineer` には

*   downside deviation (log, hl=5,21)
*   mean (hl=5,10,21)

が入っていますが、**勢い（モメンタム）とボラももう1,2個足す**だけでも改善余地があります。

```python
def feature_engineer(rets):
    def ewm_mean(x, hl):
        return x.ewm(halflife=hl, adjust=False).mean()
    
    def ewm_downside(x, hl):
        neg = x.clip(upper=0)
        dd = np.sqrt((neg**2).ewm(halflife=hl, adjust=False).mean())
        return np.log(dd + 1e-8)

    def ewm_vol(x, hl):
        return np.log(x.ewm(halflife=hl, adjust=False).std() + 1e-8)

    feats = pd.DataFrame(index=rets.index)
    
    # Downside
    feats["dd_log_hl5"] = ewm_downside(rets, 5)
    feats["dd_log_hl21"] = ewm_downside(rets, 21)
    
    # Mean (momentum-ish)
    for hl in [5, 10, 21]:
        feats[f"mean_hl{hl}"] = ewm_mean(rets, hl)

    # Volatility
    feats["vol_log_hl21"] = ewm_vol(rets, 21)
    feats["vol_log_hl63"] = ewm_vol(rets, 63)

    # 単純な過去リターン（1〜5日のラグ）
    for lag in [1, 2, 5]:
        feats[f"ret_lag{lag}"] = rets.shift(lag)

    return feats
```

すでに `feature_engineer_with_extra` で `extra_df` を結合する設計になっているので、  
マクロを足したくなったら、`extra_df` に VIX や slope などを入れれば OK です。

* * *

5\. 全体の流れ（改良版の使い方）
------------------

1.  これまで通り yfinance で `rets`（ログリターン）を作る
2.  `run_with_online_lambda` を実行して `out["w"]` を得る
3.  `choose_best_mapping` を呼んで、0/1 vs 1/0 で良い方を採用
4.  wealth 曲線を Buy&Hold と一緒にプロットして確認

イメージ：

```python
res = {}
for asset in assets:
    out = run_with_online_lambda(
        rets[asset],
        start_idx,
        n_regimes,
        init_lambda,
        lambda_grid,
        fit_freq_days,
        tscv_freq_days,
        tscv_window,
        tscv=True,
        extra_features=None,  # マクロ追加したければここに DF を渡す
    )
    w_raw = out["w"]

    w_best, info = choose_best_mapping(rets[asset], w_raw)
    print(asset, info["mode"], "Sharpe:", info["sharpe"])

    # プロット
    r = np.exp(rets[asset]) - 1.0
    wealth_bh = (1.0 + r).cumprod()
    wealth_str = info["wealth"]

    plt.figure(figsize=(7,3))
    plt.plot(wealth_bh.index, wealth_bh.values, label="Buy&Hold", alpha=0.5)
    plt.plot(wealth_str.index, wealth_str.values, label=f"Strategy ({info['mode']})")
    plt.legend(); plt.grid(); plt.title(asset); plt.show()

    res[asset] = {"raw": out, "signal": w_best, "info": info}
```

* * *

まとめ
---

こちらでやったこと：

*   **シグナルとリターンの時間軸を正しく揃えたバックテスト**
*   **0/1 vs 1/0 を両方 Sharpe で評価して良い方を自動採用**
*   **LightGBM の確率＋閾値を使ったノイズ抑制**
*   **特徴量にボラとラグリターンを追加**

これで、

> 「0/1 戦略ではパフォーマンス出なかったが、1/0 戦略だと有意に改善する」

というケースを自動的に拾えるはずですし、  
少なくとも「ラベリング／時間整合性のミスで負けている」という状態はだいぶ解消できるはずです。

一度この形で各セクター ETF の Sharpe（Buy&Hold vs Strategy）を出してみて、  
どの銘柄では効いて、どこでは効かないかを見てから、さらに

*   閾値調整（0.55 → 0.6, 0.65）
*   マクロ特徴量の追加

などを入れていくのが良いと思います。

## Response:
思考時間: 37s

OK、いまの枠組みを保ちつつ、

*   LightGBM
*   オンライン λ 更新
*   時間整合性を取ったバックテスト
*   0/1 と 1/0 のどちらが良いか自動で選ぶ

までを全部入りで **フルコード** にします。

`misc.py` とメインスクリプトを分けて書きます。

* * *

misc.py（そのまま保存して使う）
-------------------

```python
# misc.py
import numpy as np
import pandas as pd
from sklearn.cluster import kmeans_plusplus
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist

class JumpModel:
    def __init__(self, n_regimes=2, jump_penalty=0, max_iter=10, tol=1e-08, n_init=10):
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
                if len(np.unique(labels_right[labels_left == label])) != 1:
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
        if self.ub is None and self.lb is None:
            return X
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

def feature_engineer(rets: pd.Series) -> pd.DataFrame:
    """
    JM/XGB 共通のベース特徴量。
    Downside, mean, vol, ラグリターンなどを入れる。
    """
    def ewm_mean(x, hl):
        return x.ewm(halflife=hl, adjust=False).mean()
    
    def ewm_downside(x, hl):
        neg = x.clip(upper=0)
        dd = np.sqrt((neg**2).ewm(halflife=hl, adjust=False).mean())
        return np.log(dd + 1e-8)

    def ewm_vol(x, hl):
        return np.log(x.ewm(halflife=hl, adjust=False).std() + 1e-8)
    
    feats = pd.DataFrame(index=rets.index)
    
    # Downside
    feats["dd_log_hl5"] = ewm_downside(rets, 5)
    feats["dd_log_hl21"] = ewm_downside(rets, 21)
    
    # Mean
    for hl in [5, 10, 21]:
        feats[f"mean_hl{hl}"] = ewm_mean(rets, hl)

    # Volatility
    feats["vol_log_hl21"] = ewm_vol(rets, 21)
    feats["vol_log_hl63"] = ewm_vol(rets, 63)

    # Lagged returns
    for lag in [1, 2, 5]:
        feats[f"ret_lag{lag}"] = rets.shift(lag)

    return feats

def feature_engineer_with_extra(rets: pd.Series, extra_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    ベース特徴量 + extra_df（マクロなど）を結合する。
    """
    base_feats = feature_engineer(rets)
    
    if extra_df is None:
        return base_feats
    
    extra_aligned = extra_df.reindex(rets.index).ffill().bfill()
    extra_aligned = extra_aligned.fillna(0.0)
    
    feats = pd.concat([base_feats, extra_aligned], axis=1)
    return feats

def rearange_labels(labels, vals):
    """
    クラスタラベルを「平均リターンの低い順」に 0,1,... へ並べ替える。
    labels: np.array（クラスタ番号）
    vals  : pd.Series または np.array（リターン系列）
    """
    vals_arr = np.asarray(vals)
    mean_vals = {label: vals_arr[labels == label].mean() for label in np.unique(labels)}
    sorted_vals = sorted(mean_vals.items(), key=lambda x: x[1])
    rearange_map = {new_key: old_key for new_key, (old_key, value) in enumerate(sorted_vals)}
    rearange_labels = [rearange_map[label] for label in labels]
    return np.array(rearange_labels)
```

* * *

メインスクリプト（戦略・オンラインλ・バックテスト）
--------------------------

```python
import datetime
import importlib
import warnings
warnings.simplefilter('ignore')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from lightgbm import LGBMClassifier

import misc
importlib.reload(misc)

def create_clf():
    """
    LightGBM の分類器を作るヘルパー。
    ラベルは 0/1 の二値なので objective='binary'。
    """
    clf = LGBMClassifier(
        objective="binary",
        n_estimators=200,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )
    return clf

def backtest_binary_signal(log_rets: pd.Series, w: pd.Series):
    """
    log_rets: ログリターン（Series, index=日付）
    w       : {0,1} のシグナル（同じ index）
              解釈: 日付 t における w[t] は「t+1 日に risky に乗るかどうか」を表す。

    戻り値:
      wealth: 初期1の資産曲線（Series）
      sharpe: 年率換算シャープレシオ
    """
    r = np.exp(log_rets) - 1.0

    w = w.astype(float)
    # w[t] を r[t+1] に掛ける → w を1日遅らせる
    w_lag = w.shift(1).fillna(0.0)
    w_lag = w_lag.reindex(log_rets.index).fillna(0.0)

    strat_ret = w_lag * r
    wealth = (1.0 + strat_ret).cumprod()

    if strat_ret.std(ddof=1) == 0:
        sharpe = 0.0
    else:
        sharpe = np.sqrt(252) * strat_ret.mean() / strat_ret.std(ddof=1)

    return wealth, sharpe

def choose_best_mapping(log_rets: pd.Series, w_raw: pd.Series):
    """
    w_raw: {0,1} の生シグナル。
    0/1戦略と1/0戦略の Sharpe を比較し、良い方を返す。
    戻り値:
      best_w: 採用するシグナル ({0,1})
      info  : dict（mode, sharpe, alt_sharpe, wealth）
    """
    w_raw = pd.Series(w_raw, index=log_rets.index)

    wealth_01, sharpe_01 = backtest_binary_signal(log_rets, w_raw)
    wealth_10, sharpe_10 = backtest_binary_signal(log_rets, 1 - w_raw)

    if sharpe_10 > sharpe_01:
        return (1 - w_raw), {
            "mode": "long_when_0",
            "sharpe": sharpe_10,
            "alt_sharpe": sharpe_01,
            "wealth": wealth_10,
        }
    else:
        return w_raw, {
            "mode": "long_when_1",
            "sharpe": sharpe_01,
            "alt_sharpe": sharpe_10,
            "wealth": wealth_01,
        }

def select_lambda(window: pd.Series, n_regimes, current_lambda, lambda_grid, train_ratio):
    """
    時系列CVで λ を選ぶ関数（0/1ストラテジーの Sharpe 最大化）。
    window: 単一資産のログリターン（Series）
    """
    n = len(window)
    if n < 100:
        return current_lambda
    
    X = misc.feature_engineer(window)
    scaler = misc.Scaler()
    clipper = misc.Clipper(mul=3)
    X_processed = scaler.fit_transform(clipper.fit_transform(X))
    
    split_idx = int(n * train_ratio)
    X_train = X_processed[:split_idx]
    X_valid = X_processed[split_idx-1:-1]
    rets_train = window.iloc[:split_idx]
    rets_valid = window.iloc[split_idx:]
    
    if len(rets_valid) < 10:
        return current_lambda 

    best_lambda = None
    best_sharpe = -np.inf
    for lambd in lambda_grid:
        model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=lambd)
        model.fit(X_train)
        labels_train = misc.rearange_labels(model.labels, rets_train.values)
        
        y = labels_train[1:split_idx]        # s_{t+1}
        X_clf = X_processed[:split_idx-1]    # X_t
        if len(np.unique(y)) < 2:
            continue

        clf = create_clf()
        clf.fit(X_clf, y.astype(int))

        daily_returns = []
        # validation 部分: X_valid[i] で予測 → 翌日の rets_valid[i]
        for idx in range(len(X_valid)):
            x_i = X_valid[idx].reshape(1, -1)
            proba = clf.predict_proba(x_i)[0, 1]
            # 閾値固定でもよいが、CV 内ではシンプルに 0.5 で判定
            pred_regime_next = 1 if proba > 0.5 else 0
            r_next = float(rets_valid.iloc[idx])
            if pred_regime_next == 1:
                daily_returns.append(r_next)
            else:
                daily_returns.append(0.0)
        
        daily_returns = np.array(daily_returns)

        if daily_returns.std(ddof=1) == 0:
            sharpe = -np.inf
        else:
            sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std(ddof=1)

        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_lambda = lambd
    
    if best_lambda is None:
        best_lambda = current_lambda

    return best_lambda

def run_with_online_lambda(
    rets, 
    start_idx, 
    n_regimes, 
    init_lambda,
    lambda_grid, 
    fit_freq_days,
    tscv_freq_days,
    tscv_window,
    tscv=True,
    extra_features=None,
    proba_threshold=0.55,   # シグナル用の閾値
):
    """
    JumpModel + LightGBM + オンライン λ 更新付きのレジーム予測。

    戻り値:
      out = {
        "w":        シグナル (0/1) Series,
        "lambda":   λ の時系列 Series,
        "mu_bull":  bull regime の平均リターンの時系列,
        "mu_bear":  bear regime の平均リターンの時系列,
        "proba":    LightGBM のクラス1確率の時系列,
      }
    """
    if lambda_grid is None:
        lambda_grid = [0.0, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

    scaler = misc.Scaler()
    clipper = misc.Clipper(mul=3)
    scaler2 = misc.Scaler()
    clipper2 = misc.Clipper(mul=3)
    
    model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=init_lambda)
    clf = create_clf()
    
    last_fit_date = None
    last_tscv_date = None

    def should_fit(last_fit_date, current_date, freq_days):
        current = current_date.date()
        if last_fit_date is None:
            return True
        delta = current - last_fit_date
        return delta.days >= freq_days
    
    index = rets.index
    n = rets.shape[0]
    current_idx = start_idx
    end_idx = n - 1

    w = np.ones(n)
    lambdas = np.full(n, init_lambda)
    proba_path = np.full(n, np.nan)
    current_lambda = init_lambda
    mu_bull_path = np.full(n, np.nan)
    mu_bear_path = np.full(n, np.nan)

    # mu_bull, mu_bear の初期値（最初のループで上書きされる想定だが安全のため）
    mu_bull = 0.0
    mu_bear = 0.0

    while True:
        current_idx += 1
        obs = rets[:current_idx]
        current_date = obs.index[-1]

        # λ の TS-CV 更新
        if tscv and should_fit(last_tscv_date, current_date, tscv_freq_days) and len(obs) >= tscv_window:
            window = obs.iloc[-tscv_window:]
            selected_lambda = select_lambda(window, n_regimes, current_lambda, lambda_grid, train_ratio=0.7)
            current_lambda = selected_lambda
            model = misc.JumpModel(n_regimes=n_regimes, jump_penalty=current_lambda)
            last_tscv_date = current_date.date()
            last_fit_date = None
        
        X = misc.feature_engineer(obs)
        X2 = misc.feature_engineer_with_extra(obs, extra_df=extra_features)
        
        if should_fit(last_fit_date, current_date, fit_freq_days):
            last_fit_date = current_date.date()
            X_processed = scaler.fit_transform(clipper.fit_transform(X))
            X2_processed = scaler2.fit_transform(clipper2.fit_transform(X2))
            
            model.fit(X_processed)
            labels = misc.rearange_labels(model.labels, obs.values)

            if (labels == 1).any():
                mu_bull = obs.values[labels == 1].mean()
            else:
                mu_bull = 0.0
            if (labels == 0).any():
                mu_bear = obs.values[labels == 0].mean()
            else:
                mu_bear = 0.0

            y = pd.Series(labels, index=obs.index).shift(-1)
            y_idx = y.dropna().index
            clf = create_clf()
            clf.fit(
                pd.DataFrame(X2_processed, index=obs.index, columns=X2.columns).loc[y_idx], 
                y.loc[y_idx].astype(int)
            )
        else:
            X_processed = scaler.transform(clipper.transform(X))
            X2_processed = scaler2.transform(clipper2.transform(X2))
            
            pred_labels, pred_probs = model.prediction(X_processed)
            labels = misc.rearange_labels(pred_labels, obs.values)

        X2_df = pd.DataFrame(X2_processed, index=obs.index, columns=X2.columns)
        x_latest = X2_df.iloc[[-1]]
        proba = clf.predict_proba(x_latest)[0, 1]
        proba_path[current_idx] = proba

        # 閾値を超えたときだけロング、それ以外キャッシュ
        w[current_idx] = 1.0 if proba > proba_threshold else 0.0
        lambdas[current_idx] = current_lambda
        mu_bull_path[current_idx] = mu_bull
        mu_bear_path[current_idx] = mu_bear

        if current_idx == end_idx:
            break
    
    out = {
        "w": pd.Series(w, index=index),
        "lambda": pd.Series(lambdas, index=index),
        "mu_bull": pd.Series(mu_bull_path, index=index),
        "mu_bear": pd.Series(mu_bear_path, index=index),
        "proba": pd.Series(proba_path, index=index),
    }
    return out

def plot_price_and_signal(log_rets: pd.Series, w: pd.Series, title=""):
    """
    簡易プロット: Buy&Hold とバイナリ戦略の価格曲線。
    """
    r = np.exp(log_rets) - 1.0
    wealth_bh = (1.0 + r).cumprod()

    wealth_strat, _ = backtest_binary_signal(log_rets, w)

    plt.figure(figsize=(8, 4))
    plt.plot(wealth_bh.index, wealth_bh.values, label="Buy & Hold", alpha=0.6)
    plt.plot(wealth_strat.index, wealth_strat.values, label="Binary Strategy", alpha=0.8)
    plt.grid(True)
    plt.legend()
    plt.title(title)
    plt.tight_layout()
    plt.show()

# ======================
# 実行部
# ======================

start_date = "2000-01-01"
end_date = datetime.datetime.now().strftime("%Y-%m-%d")

ticker = [
    "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"
]
df = yf.download(ticker, start=start_date, end=end_date)["Close"]
rets = np.log(df).diff().dropna()

assets = rets.columns

start_idx = 1000
n_regimes = 2
init_lambda = 100.0
lambda_grid = [0.0, 5.0, 10.0, 50.0, 100.0]
fit_freq_days = 7 * 4
tscv_freq_days = 21 * 3
tscv_window = 252 * 5

results = {}

for asset in assets:
    print(f"=== {asset} ===")
    out = run_with_online_lambda(
        rets[asset],
        start_idx=start_idx,
        n_regimes=n_regimes,
        init_lambda=init_lambda,
        lambda_grid=lambda_grid,
        fit_freq_days=fit_freq_days,
        tscv_freq_days=tscv_freq_days,
        tscv_window=tscv_window,
        tscv=True,
        extra_features=None,      # ここにマクロDFを渡せば features に追加可能
        proba_threshold=0.55,
    )

    w_raw = out["w"]
    w_best, info = choose_best_mapping(rets[asset], w_raw)

    print("  mode:", info["mode"])
    print("  Sharpe:", info["sharpe"], "(alt:", info["alt_sharpe"], ")")

    # プロット（Buy&Hold vs ベスト戦略）
    wealth = info["wealth"]
    r = np.exp(rets[asset]) - 1.0
    wealth_bh = (1.0 + r).cumprod()

    plt.figure(figsize=(8, 4))
    plt.plot(wealth_bh.index, wealth_bh.values, label="Buy & Hold", alpha=0.6)
    plt.plot(wealth.index, wealth.values, label=f"Strategy ({info['mode']})", alpha=0.8)
    plt.grid(True)
    plt.legend()
    plt.title(asset)
    plt.tight_layout()
    plt.show()

    results[asset] = {
        "out": out,
        "w_raw": w_raw,
        "w_best": w_best,
        "info": info,
    }
```

* * *

この状態で：

*   各セクター ETF ごとに
    *   オンライン λ 更新
    *   LightGBM で s\_{t+1} クラス予測（確率ベースで閾値判断）
    *   0/1・1/0 の両方を Sharpe で評価して良い方を採用

まで一通り回ります。

さらに改良したくなったら、

*   `extra_features` に VIX や slope などのマクロ DF を渡す
*   `proba_threshold` を 0.6, 0.65 などに変えてみる

みたいな形で上に積んでいけます。

## Response:
思考時間: 14s

これはだいぶ「それっぽく動くように書けているが、最後のところで NaN にやられた」パターンです 😇

エラーの本質はここです：

> `ValueError: Input contains NaN.`

`model.fit(X_processed)` の直前で `X_processed` に NaN が混ざっていて、  
`StandardScaler`（もしくはその後の k-means）が落ちています。

### どこで NaN が出ているか？

`misc.feature_engineer` を見ると：

```python
feats["dd_log_hl5"]  = ewm_downside(rets, 5)
feats["dd_log_hl21"] = ewm_downside(rets, 21)
for hl in [5, 10, 21]:
    feats[f"mean_hl{hl}"] = ewm_mean(rets, hl)
for lag in [1, 2, 5]:
    feats[f"ret_lag{lag}"] = rets.shift(lag)
```

*   EWM 系は**初期部分**が NaN
*   `rets.shift(lag)` も**先頭 lag 行**が NaN
*   さらに log/std で ±inf → NaN になることもあり得る

この NaN をそのまま `Scaler` → `JumpModel` に渡しているので落ちています。

* * *

1\. 一番簡単で安全な修正：`feature_engineer` の最後で NaN / inf を潰す
----------------------------------------------------

`misc.py` の `feature_engineer` を **このように差し替えてください**：

```python
def feature_engineer(rets: pd.Series) -> pd.DataFrame:
    """
    JM/XGB 共通のベース特徴量。
    Downside, mean, vol, ラグリターンなどを入れる。
    """
    def ewm_mean(x, hl):
        return x.ewm(halflife=hl, adjust=False).mean()
    
    def ewm_downside(x, hl):
        neg = x.clip(upper=0)
        dd = np.sqrt((neg**2).ewm(halflife=hl, adjust=False).mean())
        return np.log(dd + 1e-8)

    def ewm_vol(x, hl):
        return np.log(x.ewm(halflife=hl, adjust=False).std() + 1e-8)
    
    feats = pd.DataFrame(index=rets.index)
    
    # Downside
    feats["dd_log_hl5"] = ewm_downside(rets, 5)
    feats["dd_log_hl21"] = ewm_downside(rets, 21)
    
    # Mean
    for hl in [5, 10, 21]:
        feats[f"mean_hl{hl}"] = ewm_mean(rets, hl)

    # Volatility
    feats["vol_log_hl21"] = ewm_vol(rets, 21)
    feats["vol_log_hl63"] = ewm_vol(rets, 63)

    # Lagged returns
    for lag in [1, 2, 5]:
        feats[f"ret_lag{lag}"] = rets.shift(lag)

    # ===== ここが重要：NaN / inf を潰す =====
    feats = feats.replace([np.inf, -np.inf], np.nan)
    # まず後ろ方向に埋め、その後前方向で埋める（先頭・末尾の窓不足対策）
    feats = feats.bfill().ffill()
    # それでも残ったものは 0 で埋める（ほぼない想定）
    feats = feats.fillna(0.0)

    return feats
```

`feature_engineer_with_extra` の方も、最後に軽く掃除を入れておくと安心です：

```python
def feature_engineer_with_extra(rets: pd.Series, extra_df: pd.DataFrame = None) -> pd.DataFrame:
    base_feats = feature_engineer(rets)
    
    if extra_df is None:
        return base_feats
    
    extra_aligned = extra_df.reindex(rets.index).ffill().bfill()
    extra_aligned = extra_aligned.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    
    feats = pd.concat([base_feats, extra_aligned], axis=1)
    return feats
```

この修正だけで、`X_processed = scaler.fit_transform(clipper.fit_transform(X))` に入る行列は  
**NaN / inf を含まない**ことが保証されます。

修正後は忘れずに：

```python
import importlib
import misc
importlib.reload(misc)
```

を実行してください。

* * *

2\. それでも怖い場合の保険（run\_with\_online\_lambda 側）
--------------------------------------------

念のため `run_with_online_lambda` の「学習時」にもチェックを入れておくと、  
万が一 extra\_features 側から NaN が混入しても防げます。

`run_with_online_lambda` の `if should_fit(...):` ブロック内を、ほんの少しだけ強化：

```python
if should_fit(last_fit_date, current_date, fit_freq_days):
    last_fit_date = current_date.date()
    X_processed = scaler.fit_transform(clipper.fit_transform(X))
    X2_processed = scaler2.fit_transform(clipper2.fit_transform(X2))

    # 念のため、ここでも NaN チェック
    if np.isnan(X_processed).any() or np.isinf(X_processed).any():
        raise ValueError("X_processed に NaN / inf が残っています")
    if np.isnan(X2_processed).any() or np.isinf(X2_processed).any():
        raise ValueError("X2_processed に NaN / inf が残っています")

    model.fit(X_processed)
    labels = misc.rearange_labels(model.labels, obs.values)
    ...
```

ここでまたエラーが出るようなら、「どの列に NaN が来ているか」を print して特定できますが、  
`feature_engineer` 側できちんと埋めておけば、まず大丈夫なはずです。

* * *

3\. 実行の流れ
---------

1.  `misc.py` の `feature_engineer` / `feature_engineer_with_extra` を上のように更新
2.  `importlib.reload(misc)` で再読み込み
3.  そのまま同じメインスクリプトを実行

これで、少なくとも「Input contains NaN」で止まるのは解消されます。  
その上で、0/1 vs 1/0 の Sharpe やシグナル挙動を見て、  
さらに中身（特徴量追加・閾値調整・lambda\_grid 調整など）を詰めていく段階に進めるはずです。

## Response:
思考時間: 1m 8s

了解です。「LightGBM＋オンラインλ」で作ったレジーム情報を使って、  
**レジームを考慮した MVO ポートフォリオ**を組むフルコードをまとめます。

ポイントだけ先に整理すると：

*   各資産について `run_with_online_lambda` の結果 `out` を `asset_results[asset]` に格納しておく
*   その中の
    *   `w[t]` … 「t 時点の bull/bear 予測（= 次の1ステップ分のレジーム予測）」
    *   `mu_bull[t], mu_bear[t]` … t までのデータで推定したレジーム別平均リターン
    *   `lambda[t]` … その時点で採用されているジャンプペナルティ
*   を使って、
    *   bull 予測の資産だけに投資（bear は weight=0）
    *   bull 資産の中で MVO（risk−return−トランザクションコスト）
    *   bull 資産のウェイト合計を 1 に制約（全 bear の日は現金 100％）

というロジックでポートフォリオを組みます。

* * *

1\. レジーム考慮 MVO 関数（フルコード）
------------------------

```python
import cvxpy as cp
import numpy as np
import pandas as pd

def backtest_mv_jm_lgbm(
    rets_df: pd.DataFrame,     # 通常リターン (T, N)  log→exp-1 済み
    asset_results: dict,       # 各資産の run_with_online_lambda の out
    start_idx: int,
    rf_daily: float = 0.0,
    gamma_risk: float = 10.0,
    gamma_trade: float = 1.0,
    w_lb: float = 0.0,
    w_ub: float = 0.40,
    cov_halflife: int = 252,
    bear_floor: float = -0.001,   # bear μ の下限（-10bps）など
):
    """
    レジーム（bull/bear）とレジーム別 μ を用いた MVO バックテスト。

    Parameters
    ----------
    rets_df : pd.DataFrame
        通常リターン (T, N)。列=資産、index=DateTimeIndex。
    asset_results : dict
        各資産について run_with_online_lambda の戻り値 out を格納した dict。
        例: asset_results[asset]["w"], ["mu_bull"], ["mu_bear"], ["lambda"]
    start_idx : int
        ポートフォリオバックテスト開始インデックス（十分な学習期間を空ける）。
    rf_daily : float
        日次の無リスク利子率。
    gamma_risk : float
        リスク項の重み（大きいほど分散を嫌う）。
    gamma_trade : float
        売買コスト（ポジション変更の L1 ノルム）の重み。
    w_lb, w_ub : float
        各資産のウェイト下限・上限。
    cov_halflife : int
        EWM 共分散のハーフライフ（日数）。
    bear_floor : float
        bear regime の μ の下限（極端なマイナスを切るため）。

    Returns
    -------
    results : dict
        {
          "weights": (T,N) DataFrame,
          "lambda":  (T,N) DataFrame,
          "port_ret": Series,
          "wealth":   Series,
        }
    """

    def ewm_cov_matrix(rets_window: pd.DataFrame, halflife: int = 252):
        """
        過去リターンから EWM 共分散を推定し、最後の時点の共分散行列を返す。
        rets_window: 通常リターン DataFrame (T, N)
        """
        cov_all = rets_window.ewm(halflife=halflife).cov()
        last_date = rets_window.index[-1]
        cov_last = cov_all.xs(last_date, level=0)
        return cov_last.values  # (N, N)

    dates = rets_df.index
    assets = list(rets_df.columns)
    n_assets = len(assets)
    n = len(dates)

    weights_hist = np.zeros((n, n_assets))
    port_ret = np.zeros(n)
    lambda_hist = np.zeros((n, n_assets))
    w_prev = np.zeros(n_assets)

    for t in range(start_idx, n - 1):
        date_t = dates[t]

        # 1) μ ベクトルと bull/bear 情報を作る
        mu_vec = np.zeros(n_assets)
        bullish_mask = np.zeros(n_assets, dtype=bool)

        for j, asset in enumerate(assets):
            res = asset_results[asset]  # run_with_online_lambda の out

            # その日の bull/bear 予測（= 次の日のレジーム予測）
            reg = res["w"].loc[date_t]

            # レジーム別 μ と λ
            mu_bull = res["mu_bull"].loc[date_t]
            mu_bear = res["mu_bear"].loc[date_t]
            lam = res["lambda"].loc[date_t]

            # ラベル解釈: w==1 を bull とみなす
            if reg == 1:
                mu_j = mu_bull
                bullish_mask[j] = True
            else:
                # bear μ があまりにも悪すぎるときは下限で切る
                mu_j = max(mu_bear, bear_floor)

            mu_vec[j] = mu_j
            lambda_hist[t, j] = lam

        n_bull = bullish_mask.sum()

        if n_bull == 0:
            # 全 bear → risky 0, 現金 100%
            w_opt = np.zeros(n_assets)
        else:
            # bull ≥ 1 → bull 資産だけで Σw=1（現金 0）
            cov_window = rets_df.iloc[: t + 1]
            Sigma = ewm_cov_matrix(cov_window, halflife=cov_halflife)
            
            w = cp.Variable(n_assets)

            # MVO 目的関数: リスク + ( -期待リターン ) + 売買コスト
            risk_term  = 0.5 * gamma_risk * cp.quad_form(w, Sigma)
            ret_term   = - mu_vec @ w
            trade_term = gamma_trade * cp.norm1(w - w_prev)
            obj = cp.Minimize(risk_term + ret_term + trade_term)

            constraints = [
                w >= w_lb,
                w <= w_ub,
            ]

            # bear 資産は w=0
            for j in range(n_assets):
                if not bullish_mask[j]:
                    constraints.append(w[j] == 0.0)

            # bull 資産だけで合計 1
            constraints.append(cp.sum(w[bullish_mask]) == 1.0)

            prob = cp.Problem(obj, constraints)
            prob.solve(solver=cp.OSQP)

            if w.value is None:
                # 解けない場合は bull 資産に等分配
                w_opt = np.zeros(n_assets)
                w_opt[bullish_mask] = 1.0 / n_bull
            else:
                w_opt = np.array(w.value).flatten()
        
        # 3) リターンと wealth 更新
        weights_hist[t, :] = w_opt
        r_next_vec = rets_df.iloc[t + 1].values  # t+1日の実現リターン

        risky_ret = np.dot(w_opt, r_next_vec)
        rf_weight = max(0.0, 1.0 - w_opt.sum())   # bull>=1 の日は 0, all-bearの日は1
        total_ret = risky_ret + rf_weight * rf_daily

        port_ret[t + 1] = total_ret
        w_prev = w_opt

    weights_hist_df = pd.DataFrame(weights_hist, index=dates, columns=assets)
    lambda_hist_df = pd.DataFrame(lambda_hist, index=dates, columns=assets)
    port_ret_series = pd.Series(port_ret, index=dates)
    wealth = (1.0 + port_ret_series).cumprod()

    return {
        "weights": weights_hist_df,
        "lambda": lambda_hist_df,
        "port_ret": port_ret_series,
        "wealth": wealth,
    }
```

* * *

2\. 使い方：オンライン λ＋LightGBM の結果からポートフォリオを構築
----------------------------------------

ここでは、すでに

*   `run_with_online_lambda`（前の改良版）
*   `misc.feature_engineer` など

が実装されている前提で、  
**レジーム推定 → asset\_results を作成 → ポートフォリオ構築 → プロット**  
までの流れを示します。

```python
# 1) データ取得（log return & arithmetic return）

start_date = "2000-01-01"
end_date = datetime.datetime.now().strftime("%Y-%m-%d")

ticker = [
    "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"
]
df = yf.download(ticker, start=start_date, end=end_date)["Close"]
rets_log = np.log(df).diff().dropna()
rets_arith = np.exp(rets_log) - 1.0   # ポートフォリオ用

assets = rets_log.columns

# 2) 各資産について run_with_online_lambda を回し、
#    レジーム予測・レジーム別 μ・λ の path を取得する。

start_idx_signal = 1000  # シグナル生成開始（JM/XGB の学習用に余裕をとる）
n_regimes = 2
init_lambda = 100.0
lambda_grid = [0.0, 5.0, 10.0, 50.0, 100.0]
fit_freq_days = 7 * 4
tscv_freq_days = 21 * 3
tscv_window = 252 * 5

asset_results = {}

for asset in assets:
    print(f"=== Signal building for {asset} ===")
    out = run_with_online_lambda(
        rets=rets_log[asset],
        start_idx=start_idx_signal,
        n_regimes=n_regimes,
        init_lambda=init_lambda,
        lambda_grid=lambda_grid,
        fit_freq_days=fit_freq_days,
        tscv_freq_days=tscv_freq_days,
        tscv_window=tscv_window,
        tscv=True,
        extra_features=None,   # マクロを足したければここに DataFrame を渡す
        proba_threshold=0.55,
    )
    asset_results[asset] = out

# 3) レジーム考慮 MVO バックテスト

start_idx_port = 1500  # シグナル学習期間 + 多少のバッファ

mv_res = backtest_mv_jm_lgbm(
    rets_df=rets_arith,
    asset_results=asset_results,
    start_idx=start_idx_port,
    rf_daily=0.0,
    gamma_risk=5.0,
    gamma_trade=1.0,
    w_lb=0.0,
    w_ub=0.40,
    cov_halflife=252,
    bear_floor=-0.001,
)

mv_wealth = mv_res["wealth"]

# 4) 比較用: 単純 Buy&Hold ポートフォリオ（等ウェイト）

def backtest_buy_and_hold(rets_df: pd.DataFrame, start_idx: int):
    dates = rets_df.index
    n_assets = rets_df.shape[1]
    weights = np.ones(n_assets) / n_assets
    port_ret = np.zeros(len(dates))

    for t in range(start_idx, len(dates) - 1):
        r_next = rets_df.iloc[t+1].values
        port_ret[t+1] = np.dot(weights, r_next)

    wealth = (1.0 + pd.Series(port_ret, index=dates)).cumprod()
    return wealth

bh_wealth = backtest_buy_and_hold(rets_arith, start_idx_port)

# 5) プロット

common_index = mv_wealth.index[max(start_idx_port, start_idx_signal):]

plt.figure(figsize=(10, 5))
plt.plot(common_index, bh_wealth.loc[common_index], label="Buy & Hold (EW)", alpha=0.6)
plt.plot(common_index, mv_wealth.loc[common_index], label="MV(JM-LGBM regime)", alpha=0.9)
plt.grid(True)
plt.legend()
plt.title("Regime-aware MV Portfolio vs Buy&Hold")
plt.tight_layout()
plt.show()
```

* * *

3\. 情報リークの整理（簡単に）
-----------------

*   `run_with_online_lambda`
    *   各時点 t で
        *   JM は `rets[:t+1]` だけを使う
        *   μ\_bull/μ\_bear はその時点までのデータに対するレジーム平均
        *   LGBM のラベルは `s_{t+1}`（1ステップ先のレジーム）
        *   予測は「時刻 t の特徴量」から「t+1 のレジーム」を当てに行く
*   `backtest_mv_jm_lgbm`
    *   日付 t の `w[t]` / `mu_bull[t]` / `mu_bear[t]` を使って
        *   ウェイト `w_opt[t]` を決め
        *   実際には `r_{t+1}` に適用してポートフォリオを更新

となっているので、  
**常に「t までの情報」で t+1 のリスクテイクを決めている構造**になっており、  
未来のリターンを覗き見していないことが保証されます。

* * *

この形で一度、

*   `gamma_risk`, `gamma_trade`
*   `proba_threshold`
*   `bear_floor`

あたりを少し振って、  
「どの程度 Buy&Hold / MinVar に対して優位性が出るか」  
を見てみるのが次のステップかなと思います。

もし MinVar との 3本比較（Buy&Hold, MinVar, MV(JM-LGBM)）のコードもまとめたい場合は、  
そこも含めて一式出します。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)