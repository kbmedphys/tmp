# 枝分かれ · 専門家向け解説

**User:** Anonymous (kbmedphys@gmail.com)  
**Created:** 12/17/2025 17:23:03  
**Updated:** 12/17/2025 19:54:09  
**Exported:** 12/17/2025 19:55:45  
**Link:** [https://chatgpt.com/c/69426863-2390-8323-9751-4672ff98b358](https://chatgpt.com/c/69426863-2390-8323-9751-4672ff98b358)  

## Response:
思考時間: 17s

以下は、添付論文 **“Forecast-Agnostic Portfolios” (Guo & Wachter, 2025-11-25)** の内容を、**専門家向け**に、**数理を省略せず**に整理した解説です。本文の主張は「**予測回帰の係数推定（β̂）に依存しない** “forecast-agnostic (FA)” ポートフォリオ」を作ると、伝統的な **out-of-sample  $R^2$ ** が負になりがちな予測子でも、**CAPM α（アルファ）としては有意に正**になり得る、という点にあります。

ssrn-5808182

* * *

1\. 問題設定：予測回帰と out-of-sample  $R^2$  の「悲観的結論」
---------------------------------------------

### 1.1 標準の予測回帰

論文が基礎に置くのは、株式市場（市場超過収益）に対する標準的な予測回帰です：

ssrn-5808182

$$
r_{t+1} = \alpha + \beta x_t + v_{t+1},
$$
*    $r_{t+1}$ ：（月次 or 四半期などの）市場の超過収益
*    $x_t$ ：時点  $t$  で観測可能な予測子
*    $v_{t+1}$ ：平均ゼロで時点  $t$  の情報と無相関（条件付平均ゼロの誤差）

実務では  $(\hat\alpha_t,\hat\beta_t)$  を **expanding window**（時点  $t$  までのデータ）で逐次推定し、それを用いた予測  $\hat r_{t+1|t}=\hat\alpha_t+\hat\beta_t x_t$  を作ります。

ssrn-5808182

### 1.2 Goyal–Welch 型 out-of-sample  $R^2$ 

論文が繰り返し参照する（Goyal & Welch 系の）OOS  $R^2$  は、

$$
R^2_{\text{OOS}} =1-\frac{\sum_{t=0}^T\left[r_t-(\hat\alpha_{t-1}+\hat\beta_{t-1}x_{t-1})\right]^2} {\sum_{t=0}^T\left[r_t-\bar r_{t-1}\right]^2},
$$

で、ベンチマークは expanding mean  $\bar r_{t-1}$ （過去平均）です。

ssrn-5808182

**結論（既存文献）：** 多くの予測子は OOS  $R^2$  が負になり、「予測には使えない」という評価になりがちです。

ssrn-5808182

さらに Campbell–Thompson (2008) のように「株式リスクプレミアムは負になりにくい」という制約（負の予測を切り捨て）を課しても、中央値が負のまま、という状況が述べられます。

ssrn-5808182

* * *

2\. 論文の中核：Forecast-Agnostic (FA) ポートフォリオと “FA alpha”
----------------------------------------------------

### 2.1 発想：回帰係数の推定を「捨てる」

この論文は、予測子の有用性を **「予測誤差（MSE）＝OOS  $R^2$ 」** で見るのではなく、\*\*投資家の観点（αが出るか）\*\*で測る指標として **forecast-agnostic alpha** を提案します。

ssrn-5808182

ここで重要なのは：

*   OOS  $R^2$  は「予測（ $\hat\beta$  推定）を正確にやれ」という要請が強い
*   一方、投資家は「市場に対するロング・ショートのオーバーレイが **α** を生むか」が本丸
*   そこで「 $\hat\beta$  を推定して数値予測する」工程を外し、**予測子の“水準”だけ**で市場のロング/ショートを決める（ただし方向の符号だけは最小限使う）

という立場です。

ssrn-5808182

* * *

3\. FA ポートフォリオの厳密定義（実装可能な逐次版）
-----------------------------

以下では、論文の構成に沿って「生の（unscaled）→符号付け→ボラターゲット→レバ制約」の順に定義します。

ssrn-5808182

### 3.1 逐次 demean：未来情報を使わない中心化

時点  $t-1$  までの情報で予測子の expanding mean を

$$
\bar x_{t-1} = \frac{1}{t-1}\sum_{s=1}^{t-1} x_s
$$

とし、取引に使う “中心化予測子” を

$$
\tilde x_{t-1} = x_{t-1} - \bar x_{t-1}
$$

と置きます。これは「当時点で利用可能なデータだけ」で作るため、ルックアヘッドを回避します。

ssrn-5808182

### 3.2 方向（符号）だけ回帰から取得： $\text{sign}(\hat\beta)$ 

論文は「回帰係数そのもの（大きさ）ではなく **符号だけ**」を使います。すなわち expanding window で（市場超過収益を）回帰し、係数の符号

$$
s_{t-1}=\text{sign}(\hat\beta_{t-1})
$$

を取り、**市場への未スケール・未制約の生ウェイト**を

$$
w^{\text{raw}}_{t-1} = s_{t-1}\,\tilde x_{t-1}
$$

のように構成するイメージです（本文では「demeaned predictor を使い、回帰係数の符号を掛ける」と説明）。

ssrn-5808182

この段階の（超過）リターンは

$$
r^{\text{raw}}_{t} = w^{\text{raw}}_{t-1}\, mkt_t
$$

（ここで  $mkt_t$  は市場超過収益）です。

ssrn-5808182

### 3.3 ボラティリティ・ターゲッティング（一定リスク予算）

次に、時点  $t-1$  までの “raw ポートフォリオ収益” の（expanding）標準偏差を

$$
\bar\sigma^{x}_{t-1}=\text{Std}\left(r^{\text{raw}}_{1},\dots,r^{\text{raw}}_{t-1}\right)
$$

とし、月次ターゲット・ボラ  $\sigma^\*$ （本文の例は 5%）でスケールしたウェイトを

$$
w_{t-1} = w^{\text{raw}}_{t-1}\cdot \frac{\sigma^\*}{\bar\sigma^{x}_{t-1}}
$$

とします。

ssrn-5808182

この操作により、\*\*予測子ごとのリスク量を揃える（equal risk budget）\*\*形になり、 $\hat\beta$  の推定誤差がポジション量に伝播しにくくなります。

### 3.4 実務上のレバレッジ制約（winsorize）

最後に実現可能性のため市場ウェイトを

$$
w_{t-1}\leftarrow \min\{3,\max\{-3,w_{t-1}\}\}
$$

のように  $[-3,3]$  にクリップします（論文は  $\pm 300\%$  の制約）。

ssrn-5808182

ssrn-5808182

* * *

4\. 評価指標：なぜ「平均リターン」ではなく「α」なのか
-----------------------------

Goyal et al. (2024) が検討した “bull/bear portfolios” は、係数推定依存を減らす目的は似ていますが、評価が「市場より勝つか（平均収益）」に寄っている、と本論文は批判します。市場超過収益は平均的に正なので、ロング/ショート戦略に「市場より高い平均」を要求するのは厳しすぎる、という理屈です。したがって **CAPM に対する α** で測るべきだ、と述べます。

ssrn-5808182

* * *

5\. 最大の理論的ポイント：回帰係数  $\beta$  は「あるポートフォリオの平均収益」である
--------------------------------------------------

論文が提示する核心的な等式は次です：  
**予測回帰で得る  $\beta$  は、実は“係数ポートフォリオ”の平均超過収益に等しい**。

ssrn-5808182

### 5.1 サンプル内回帰係数の形

全期間（長さ  $T$ ）で、 $mkt_t$  を  $x_{t-1}$  と定数で回帰したとき（平均を  $\bar x$  とする）、傾き係数は

\\beta^x =\\frac{\\frac{1}{T}\\sum\_t (x\_{t-1}-\\bar x)\\,mkt\_t}{\\frac{1}{T}\\sum\_t (x\_{t-1}-\\bar x)^2}. \\\] :contentReference\[oaicite:17\]{index=17} これを次のように書き換えます。ポートフォリオ・ウェイト \\\[ w\_{t-1} =\\frac{(x\_{t-1}-\\bar x)}{\\frac{1}{T}\\sum\_t (x\_{t-1}-\\bar x)^2}

と定義すると、上式は

$$
\beta^x = \frac{1}{T}\sum_t w_{t-1} mkt_t
$$

となり、\*\* $\beta^x$  は「 $w_{t-1}$  で市場に投資し続けたゼロコスト戦略の平均超過収益」\*\*だと解釈できます。

ssrn-5808182

加えて、論文はこの  $w_{t-1}$  が

1.   $x$  に線形、
2.  サンプル内平均が 0（市場中立の平均）、
3.  ある種のスケーリング（単位エクスポージャ）  
    を満たす、と説明します。
    ssrn-5808182

### 5.2 ここから出る「R²が正になるには自己予測が必要」という主張

OOS  $R^2$  の計算は expanding window の  $\hat\beta_{t-1}$  を使って数値予測を作るわけですが、これは暗に「係数ポートフォリオの期待収益（=  $\beta$ ）が十分安定で、過去から未来へ精度高く外挿できる」ことを要請している、と論じます。

ssrn-5808182

しかし、もし expanding  $\hat\beta$  が常に真の  $\beta$  に張り付くほど安定なら、係数ポートフォリオはほぼ確実に稼げ、シャープレシオが極端に大きくなる（極限では分散 0、IR 無限大の裁定に近い）というパラドックスが出る。つまり「OOS  $R^2$  を良くする」には、**市場リターンの予測**に加えて \*\*“その予測子に基づく戦略リターン自体の予測（自己認識・self-awareness）”\*\*が必要で、その要求はデータ量的に厳しすぎる、という整理です。

ssrn-5808182

一方 FA は、過去の係数推定のブレに応じてポジション量を増減しない（一定リスク予算）ため、この「自己予測」誤差を経路から外す、という位置づけになります。

ssrn-5808182

* * *

6\. 実証結果の要点：OOS  $R^2$  が負でも FA α が正になる（平均的に）
---------------------------------------------

論文は Goyal et al. (2024) が整理した 46 予測子について、FA ポートフォリオの CAPM α を計測し、**平均・中央値で正**、かつパネル回帰などで統計的に有意であると報告します（平均 α が月次で十数bp程度、など）。

ssrn-5808182

また、FA α と OOS  $R^2$  の相関は高くなく（おおむね 0.2 程度）、評価が大きく食い違うことを強調します。

ssrn-5808182

* * *

7\. シミュレーション：なぜ FA α の方が「検出力（power）」が高いのか
-----------------------------------------

### 7.1 シミュレーション設計（要点）

論文は「現実データ並みの弱い予測力」を模した Monte Carlo を作り、以下の統計を比較します：平均  $|t|$ 、IS  $R^2$ 、OOS  $R^2$ 、制約付き OOS  $R^2$ 、FA α。

ssrn-5808182

結論は、**真に予測可能性が存在していても**、現実程度の弱さだと OOS  $R^2$  の中央値が負になり得る一方、FA α は正を示しやすく、単独統計として power が高い、というものです。

ssrn-5808182

ここでの理屈は明確で：

*   OOS  $R^2$  は  $\hat\beta$  の逐次推定誤差（分散）を強く食らう
*   FA は係数推定を “符号” に限定し、さらにリスク量を固定することで推定誤差の影響（分散）を大きく落とす
*   弱いシグナル環境では **バイアス‐バリアンス・トレードオフ**の観点で「単純化が勝つ」
    ssrn-5808182

という構造です。

* * *

8\. FA と対比される “Forecast-Driven (FD)” 戦略：いつ複雑さが勝つか
-------------------------------------------------

論文は Campbell–Thompson 型の意思決定（期待収益×リスク許容度で市場ウェイトを決める）に近い FD 戦略も定義し、データ量や予測力が十分強いときには FD が FA を上回り得ることを示します。

ssrn-5808182

FD の代表的な構成は、expanding 推定した係数と demeaned predictor の積に、リスク回避度などから導かれる定数（本文では 200）を掛けてポジション化し、同様に  $\pm 3$  で制約します。

ssrn-5808182

そして「データが 5倍、20倍」や「予測力が 3倍」などの世界では、OOS  $R^2$  が正になり、FD が FA の上に追加 α を生み始める、という整理です。

ssrn-5808182

要するに、**現実の弱い予測力×有限サンプル**では FA が優位になりやすい、という “サンプルサイズ依存の結論” を明確にします。

* * *

9\. 追加論点：出版後のアルファ消滅（arbitrage / crowding）
-----------------------------------------

論文は、予測子（学術提案）の **出版後**に FA α が概ね 0 になる（統計的に有意でない）一方、出版前（pre-sample）では高めである、と報告し、Mclean & Pontiff (2016) 的に「発見後に裁定される」可能性を示唆します。

ssrn-5808182

また、リスク説明がある予測子でも同様に post-sample で弱まる傾向があることを示し、単純な “リスクベースで安定” という主張に疑義を投げます。

ssrn-5808182

* * *

10\. 制約（economic/statistical constraints）の再解釈：良くなるのは「経済的に正しい」からだけではない
---------------------------------------------------------------------

Campbell–Thompson (2008) の非負制約（予測リスクプレミアム < 0 を切る）は OOS  $R^2$  を改善しますが、論文は「改善理由は経済制約の正しさというより、**極端な推定値を抑えて分散を減らすこと**かもしれない」と論じ、対称な上側制約（極端に高い予測も抑える）でも似た改善が出ることを示します。

ssrn-5808182

さらに、経済モデルが係数の値（例えば SVIX 系で係数が 1/12 など）を与えるケースでは、それを「データが少ない中での shrinkage target」として解釈し、\*\*self-awareness 要件（係数ポートフォリオの将来平均を知る）\*\*を補う役割がある、と位置付けます。

ssrn-5808182

* * *

まとめ（論文の貢献を数理的に一言で）
==================

*   予測回帰の  $\beta$  は、適切に定義した “係数ポートフォリオ” の平均リターンとして解釈できる。
    ssrn-5808182
*   OOS  $R^2$  で勝つには「市場リターンの予測」に加えて「係数ポートフォリオのリターン予測（自己予測）」が必要になり、弱い予測力・有限サンプルでは極めて難しい。
    ssrn-5808182
*   そこで、係数推定の大きさを捨て、符号＋ボラターゲット＋レバ制約という **低分散**なルールで作る FA ポートフォリオを使うと、OOS  $R^2$  が負でも CAPM α としては正になり得る。
    ssrn-5808182
    ssrn-5808182

* * *

もし次に「実装」まで含めたい場合は、あなたが以前構築している **逐次回帰・rolling/expanding・ボラターゲット**の枠組みに合わせて、

1.  FA ポートフォリオ（上の定義そのまま）
2.  FD ポートフォリオ（論文の 200 スケール版）
3.  OOS  $R^2$  と FA α の同時比較（予測子46本をパネルで）  
    を完全に統合した Python を提示できます。

## Response:
以下では、**新たに添付された Guo (2020) “Earnings Extrapolation and Predictable Stock Market Returns”** と、先に議論した **Guo & Wachter (2025) “Forecast-Agnostic Portfolios”** の **理論的・実証的な関連性**、および \*\*統合可能性（1つの研究／実装フレームとしてどう結び付けられるか）\*\*を、専門家向けに体系的に整理します。  
両論文は一見「異なるテーマ（季節性 vs 投資評価指標）」に見えますが、**実は同一の中核問題――弱い予測可能性・推定誤差・投資家の意思決定――を異なる層から扱っている**と解釈できます。

* * *

1\. 各論文の役割分担（位置づけの整理）
---------------------

### (A) Earnings Extrapolation (EE, 2020) の本質

EE 論文の核心は：

*   **市場リターンの自己相関は一様ではない**
*   とくに「**newsy months（四半期の第1月）**」と「**non-newsy months**」で
    *   newsy → **リバーサル（負の自己相関）**
    *   non-newsy → **モメンタム（正の自己相関）**
*   このパターンは
    *   会計情報の **発表タイミング構造**
    *   投資家の **earnings extrapolation（不完全な期待形成）**  
        により生じる

という **「予測可能性の源泉（economic mechanism）」** を与える論文です。  
EE は **予測子そのものを構造的に分解**します（return を month-type で条件付け）。

> EE は _why predictability exists_ を説明する論文  
> 
> ssrn-3480863

* * *

### (B) Forecast-Agnostic Portfolios (FA, 2025) の本質

一方 FA 論文は：

*   **予測回帰の OOS R² が負でも**
*   投資家にとって重要なのは
    $$
    \text{「予測誤差」ではなく「α（付加価値）」}
    $$
*   回帰係数  $\beta$  を
    > **「あるポートフォリオの平均リターン」**  
    > と解釈し、
*    $\hat\beta$  の **大きさの推定を捨て、符号と水準だけを使う**  
    → **bias–variance tradeoff を最適化**

という **「評価指標と投資実装の再定義」** を行う論文です。

> FA は _how predictability should be used / evaluated_ を与える論文  
> 
> ssrn-5808182

* * *

2\. 両論文の理論的な接点（深いレベル）
---------------------

### 2.1 「予測可能性はあるが、数値予測は不安定」という共通認識

| 観点 | EE (2020) | FA (2025) |
| --- | --- | --- |
| 予測可能性 | **強く存在**（条件付） | **存在を前提** |
| 問題点 | 無条件では相殺される |  $\hat\beta_t$  が不安定 |
| 核心 | **条件付構造の見落とし** | **自己予測（self-awareness）問題** |

EE は

> 「予測は _条件を間違えると_ 見えなくなる」

FA は

> 「予測は _推定しようとすると_ 壊れる」

と言っており、**両者は矛盾ではなく補完関係**にあります。

* * *

### 2.2 FA の「係数ポートフォリオ解釈」と EE の「newsy 構造」

FA の重要な定理：

$$
\beta = \frac{1}{T}\sum_t \underbrace{ \frac{x_{t-1}-\bar x} {\frac{1}{T}\sum (x_{t-1}-\bar x)^2} }_{\text{係数ポートフォリオの weight}} \cdot mkt_t
$$

つまり、

> **予測回帰の係数 =  
> 予測子に比例した market-timing ポートフォリオの平均収益**

EE 論文では、

$$
x_t = \sum_{j=1}^4 mktnm(t,j)
$$

（過去の newsy month リターン）

が **経済的に意味を持つ predictor** であることを示しています。

👉 結果として：

*   EE が構築した **newsy-based predictor**
*   を FA の枠組みで **forecast-agnostic portfolio** に変換すると
    
$$
\text{EE の構造的予測子} \;\Longrightarrow\; \text{FA α を生む「係数ポートフォリオ」}
$$

という **完全な理論的一貫性**が成立します。

* * *

3\. 統合可能な研究フレーム（理論 × 実装）
------------------------

### 3.1 統合①：EE 予測子 × FA 評価指標

**最も自然な統合**

1.  EE で定義された
    *   newsy return
    *   non-newsy return
    *   lagged newsy sums
2.  を predictor  $x_t$  として
3.  FA portfolio を構築
4.  評価は
    *   CAPM α
    *   予測 OOS R² ではなく **FA α**

**期待される結果**

*   OOS R²：  
    → 月次で不安定（とくに newsy month）
*   FA α：  
    → 正で有意（構造的ミスプライシングを捉える）

👉 EE が示した「予測可能性の源泉」が、  
FA によって **投資可能な形で可視化**される。

* * *

### 3.2 統合②：「条件付 FA（Regime-aware FA）」への拡張

EE の最大の特徴は

> **dependent variable の timing による非定常性**

これを FA に組み込むと：

$$
w_{t-1} = \begin{cases} +s \cdot (x_{t-1}-\bar x_{t-1}) & t \in \text{non-newsy} \\ -s \cdot (x_{t-1}-\bar x_{t-1}) & t \in \text{newsy} \end{cases}
$$

という **符号切替型 FA** が理論的に正当化されます。

*   EE：  
    「news y / non-newsy で期待収益の符号が逆」
*   FA：  
    「符号だけを使うのが最適」

👉 **EE は FA の sign rule を“内生化”する理論**と解釈可能。

* * *

### 3.3 統合③：FA の「self-awareness 問題」への EE 的解決

FA の核心問題：

> OOS R² が正になるには  
> 「予測子ポートフォリオの将来リターンを予測できる」  
> ＝ self-awareness が必要

EE はこれに対し：

*   「予測が失敗するのは  
    _投資家が earnings cycle の非一様性を無視するから_」
*   つまり  
    **誤りはランダムではなく、構造的**

という説明を与えます。

👉 統合すると：

*   **EE：予測誤差は構造的（month-type に依存）**
*   **FA：その誤差を推定に使うと分散爆発**
*   ⇒ **推定を捨てた FA が合理的**

という **理論的補強関係**が成立。

* * *

4\. 研究・実装としての統合アウトライン（提案）
-------------------------

### 論文としての統合構成案

1.  **Section 1**  
    EE による earnings-cycle-driven predictability
2.  **Section 2**  
    予測回帰と OOS R² の限界
3.  **Section 3**  
    FA α の理論（係数＝ポートフォリオ）
4.  **Section 4**  
    EE predictors × FA portfolios
5.  **Section 5**  
    newsy / non-newsy conditional FA
6.  **Section 6**  
    投資家行動（extrapolation × bias-variance）
7.  **Section 7**  
    post-publication arbitrage

* * *

5\. 結論（統合的理解）
-------------

*   **EE 論文**は
    > _どこに予測可能性があるか_  
    > を説明する
*   **FA 論文**は
    > _それをどう使えば投資価値に変換できるか_  
    > を説明する

両者を統合すると：

> **「弱く、非定常で、条件付な予測可能性」を  
> 推定誤差に壊されずに α に変換する最適戦略**

という **一貫した理論・実証・実装フレーム**が完成します。

* * *

次のステップとして有益なのは：

*   EE predictors を用いた **FA / conditional-FA の完全 Python 実装**
*   「EE × FA × Method6（あなたの既存 z\*\_t）」の **三者比較**
*   newsy / non-newsy 別の **α 分解スライド**

です。  
どこまで踏み込みたいか、指示いただければそこから具体化します。

## Response:
承知しました。以下では、あなたの提示コード（Method6 の定義・month\_type=N/R/3・ボラターゲット等）を前提にして、

1.  **EE predictors を用いた FA / conditional-FA の完全 Python 実装**
2.  **EE × FA × Method6 ×（既存 z\*\_t） 三者（＋市場）比較の統合コード**
3.  **newsy / non-newsy 別の α 分解（回帰＋寄与分解）と “スライド原稿”**

を **そのまま動かせる形**で提示します。

* * *

0\. 設計方針（あなたの実装と整合）
===================

*   month\_type は \*\*あなたの `classify_month_type`（N/R/3）\*\*をそのまま使用。
*   EE predictor は、Guo(2020) の “newsy month return が将来を予測”の実装に合わせて、あなたが既に使っている \*\*「直近 4 つの newsy 月リターンの和」\*\*を基本とします（以下 `S_t`）。
    *   これが EE の “flagship signal” に対応する最短ルートです（EE 本文の回帰式（1）と整合）。
*   FA は Guo & Wachter(2025) の定義：
    *   **(i)** predictor を expanding mean で demean
    *   **(ii)** 回帰係数は **符号のみ**使用（sign）
    *   **(iii)** 目標ボラに合わせてスケール
    *   **(iv)** レバ ±3 でクリップ
*   conditional-FA は EE の含意（newsy vs non-newsy で予測符号が反転）を実装に落とし込み：
    *   **月タイプに応じて sign を切り替える**（最小限の条件付け）

* * *

1\. 統合 Python 実装（コピペで実行可）
=========================

> 重要：あなたの `load_ff_monthly_from_ken_french`, `classify_month_type`, `annualized_stats` は再利用します。  
> 下のコードは、それらが同一ファイル内にある前提で “追記” してください。

```python
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import statsmodels.api as sm

# ============================================================
# A. 共通ユーティリティ
# ============================================================

def clip_leverage(w: pd.Series, L: float = 3.0) -> pd.Series:
    return w.clip(lower=-L, upper=L)

def expanding_demean(s: pd.Series) -> pd.Series:
    """
    x_t - mean_{u<=t} x_u を作る。
    実運用で t の時点に利用できるのは「t まで」だが、
    重み w_{t} に使うのは通常 x_{t} を観測した直後（t 終値）なのでOK。
    あなたの Method6 は x_{t} を t のトレードに使う設計なので、整合。
    """
    return s - s.expanding().mean()

def realized_vol_expanding(r: pd.Series) -> pd.Series:
    """
    逐次で vol を推定：t 時点のスケールには t-1 までの情報を使う。
    """
    vol = r.expanding().std(ddof=1).shift(1)
    return vol

def capm_alpha_tstat(port_excess: pd.Series, mkt_excess: pd.Series):
    """
    port_excess_t = alpha + beta * mkt_excess_t + eps
    """
    df = pd.concat([port_excess.rename("p"), mkt_excess.rename("m")], axis=1).dropna()
    X = sm.add_constant(df["m"])
    res = sm.OLS(df["p"], X).fit()
    alpha = float(res.params["const"])
    tstat = float(res.tvalues["const"])
    beta  = float(res.params["m"])
    return alpha, tstat, beta, res

# ============================================================
# B. EE predictors（Guo 2020）: newsy月ベース signal S_t
# ============================================================

def compute_newsy_sum_signal(mkt_total: pd.Series, k_lags: int = 4):
    """
    EE の 'flagship signal' に対応：
    S_t = 直近 k 個の Newsy 月（N）の market total return の合計
    返すのは S_t（各月に対応）と month_type。
    """
    idx = mkt_total.index
    month_type = classify_month_type(idx)
    is_newsy = (month_type == "N")
    news = mkt_total[is_newsy]

    S = pd.Series(index=idx, dtype=float)
    for t in idx:
        past = news[news.index <= t]
        if len(past) >= k_lags:
            S[t] = past.iloc[-k_lags:].sum()
        else:
            S[t] = np.nan
    return S, month_type

# ============================================================
# C. FA / conditional-FA（Guo & Wachter 2025）実装
# ============================================================

def build_fa_weights_from_predictor(
    predictor: pd.Series,
    mkt_excess: pd.Series,
    month_type: pd.Series,
    min_obs: int = 120,
    target_vol: float = 0.05,
    L: float = 3.0,
    use_conditional_sign: bool = False,
):
    """
    Forecast-Agnostic portfolio (FA):
      1) predictor を expanding で demean
      2) sign(β_hat) のみ利用（β_hat は expanding 回帰で推定）
      3) raw weight = sign * demeaned_predictor
      4) raw strat return = w_raw * mkt_excess
      5) expanding vol で target_vol にスケール（時点tのスケールは t-1まで）
      6) leverage clip ±L

    conditional-FA:
      - use_conditional_sign=True の場合、月タイプで符号を切替える。
        EE の含意に合わせ、基本は
            N(月) : sign = -1
            (R or 3): sign = +1
        ただし、FA の思想（符号はデータに喋らせる）も残すため、
        ベースの sign(β_hat) を掛け合わせる設計にしている。
    """
    df = pd.concat([
        predictor.rename("pred"),
        mkt_excess.rename("mkt_excess"),
        month_type.rename("month_type")
    ], axis=1).dropna(subset=["mkt_excess"])

    # 1) demean（逐次平均）
    df["pred_dm"] = df["pred"] - df["pred"].expanding().mean()

    # 2) expanding 回帰で β_hat の符号だけ取る
    #    mkt_excess_t = a + b * pred_dm_{t-1} + e_t を想定し、右辺は 1期ラグ
    #    ここでは実装上、pred_dm を shift(1) して回帰。
    b_sign = pd.Series(index=df.index, dtype=float)
    x_lag = df["pred_dm"].shift(1)
    y = df["mkt_excess"]

    for i, t in enumerate(df.index):
        mask = (df.index <= t) & x_lag.notna() & y.notna()
        if mask.sum() < min_obs:
            b_sign[t] = np.nan
            continue
        xi = x_lag[mask].values
        yi = y[mask].values
        denom = np.sum((xi - xi.mean())**2)
        if denom <= 0:
            b_sign[t] = np.nan
            continue
        # OLS slope
        b = np.sum((xi - xi.mean()) * (yi - yi.mean())) / denom
        b_sign[t] = 1.0 if b >= 0 else -1.0

    df["b_sign"] = b_sign

    # 3) raw weight
    base_sign = df["b_sign"].fillna(1.0)

    if use_conditional_sign:
        # EE の month-type による条件付け（最小限の “理論注入”）
        cond = pd.Series(1.0, index=df.index)
        cond[df["month_type"] == "N"] = -1.0
        # R,3 は +1 のまま
        df["sign_used"] = base_sign * cond
    else:
        df["sign_used"] = base_sign

    df["w_raw"] = df["sign_used"] * df["pred_dm"]

    # 4) raw excess return
    df["strat_excess_raw"] = df["w_raw"] * df["mkt_excess"]

    # 5) vol targeting（逐次）
    vol = realized_vol_expanding(df["strat_excess_raw"])
    scale_t = target_vol / vol
    scale_t = scale_t.replace([np.inf, -np.inf], np.nan).fillna(1.0)

    df["w_scaled"] = df["w_raw"] * scale_t
    df["w_scaled"] = clip_leverage(df["w_scaled"], L=L)

    # clip 後のリターン
    df["strat_excess"] = df["w_scaled"] * df["mkt_excess"]

    # 出力
    out = df[["pred","pred_dm","b_sign","sign_used","w_raw","w_scaled","strat_excess_raw","strat_excess","month_type"]].copy()
    out.attrs["target_vol"] = target_vol
    out.attrs["L"] = L
    out.attrs["min_obs"] = min_obs
    out.attrs["conditional"] = use_conditional_sign
    return out

# ============================================================
# D. Method6（あなたの既存実装）を “戦略リターン” に整形
# ============================================================

def method6_strategy_df(ff: pd.DataFrame, w_raw: pd.Series, target_vol: float = 0.05, L: float = 3.0):
    """
    あなたの vol_target_from_weights は「全期間で1回スケール」なので、
    FA と同じ比較軸に揃えるため、Method6 も逐次 vol-target（t-1まで）にする版。
    """
    mkt_excess = ff["mkt_excess"]
    rf = ff["rf"]
    month_type = classify_month_type(ff.index)

    df = pd.concat([mkt_excess, rf, w_raw.rename("w_raw"), month_type.rename("month_type")], axis=1).dropna(subset=["mkt_excess","rf"])
    df["strat_excess_raw"] = df["w_raw"] * df["mkt_excess"]

    vol = realized_vol_expanding(df["strat_excess_raw"])
    scale_t = target_vol / vol
    scale_t = scale_t.replace([np.inf, -np.inf], np.nan).fillna(1.0)

    df["w_scaled"] = clip_leverage(df["w_raw"] * scale_t, L=L)
    df["strat_excess"] = df["w_scaled"] * df["mkt_excess"]
    df["strat_total"] = df["rf"] + df["strat_excess"]

    df.attrs["target_vol"] = target_vol
    df.attrs["L"] = L
    return df

# ============================================================
# E. α 分解：newsy / non-newsy 別（回帰と寄与）
# ============================================================

def alpha_decomposition_by_monthtype(strat_excess: pd.Series, mkt_excess: pd.Series, month_type: pd.Series):
    """
    1) 全期間 CAPM alpha
    2) newsy(N) / non-newsy(R,3) それぞれの部分サンプル alpha
    3) “寄与分解”の簡易版：
       alpha_all ≈ sum_g (pi_g * alpha_g) + 交差項
       ※交差項が出る可能性があるため、数値で併記する。
    """
    # 全体
    a_all, t_all, b_all, _ = capm_alpha_tstat(strat_excess, mkt_excess)

    # 部分サンプル
    isN = (month_type == "N")
    isNN = ~isN

    a_N, t_N, b_N, _ = capm_alpha_tstat(strat_excess[isN], mkt_excess[isN])
    a_NN, t_NN, b_NN, _ = capm_alpha_tstat(strat_excess[isNN], mkt_excess[isNN])

    # 重み（観測比率）
    pi_N = float(isN.loc[strat_excess.dropna().index].mean())
    pi_NN = 1.0 - pi_N

    approx = pi_N * a_N + pi_NN * a_NN
    cross = a_all - approx

    out = pd.DataFrame({
        "group": ["ALL", "N(newsy)", "Non-newsy(R,3)"],
        "alpha(monthly)": [a_all, a_N, a_NN],
        "tstat(alpha)": [t_all, t_N, t_NN],
        "beta": [b_all, b_N, b_NN],
    })
    info = {
        "pi_N": pi_N,
        "pi_NN": pi_NN,
        "alpha_weighted_avg": approx,
        "alpha_all": a_all,
        "cross_term": cross,
    }
    return out, info

# ============================================================
# F. 三者（＋市場）比較：統合 main
# ============================================================

def compare_ee_fa_method6_zstar(
    ff: pd.DataFrame,
    zstar: pd.Series,
    min_obs: int = 120,
    target_vol: float = 0.05,
    L: float = 3.0,
    lookback_years_method6: int = 20,
):
    """
    戻り値:
      dict of strategy dfs:
        - "FA(EE)" : EE predictor に基づく FA
        - "cFA(EE)": EE predictor に基づく conditional-FA
        - "Method6"
        - "zstar"
        - "mkt"
      plus: summary tables
    """
    idx = ff.index
    month_type = classify_month_type(idx)

    # 市場系列
    mkt_excess = ff["mkt_excess"].copy()
    rf = ff["rf"].copy()
    mkt_total = (mkt_excess + rf).rename("mkt_total")

    # ---- EE predictor: S_t（newsy sum）
    S, month_type2 = compute_newsy_sum_signal(mkt_total, k_lags=4)
    # predictor をここでは S_{t-1}（情報時点整合）として扱う：t のポジションは t-1 の情報で決まる
    pred_ee = S.shift(1).rename("EE_S_lag")

    # ---- FA / conditional-FA
    fa = build_fa_weights_from_predictor(
        predictor=pred_ee,
        mkt_excess=mkt_excess,
        month_type=month_type,
        min_obs=min_obs,
        target_vol=target_vol,
        L=L,
        use_conditional_sign=False,
    )
    cfa = build_fa_weights_from_predictor(
        predictor=pred_ee,
        mkt_excess=mkt_excess,
        month_type=month_type,
        min_obs=min_obs,
        target_vol=target_vol,
        L=L,
        use_conditional_sign=True,
    )

    # ---- Method6（あなたの rolling β_t x_t を再利用）
    # build_method6_raw_weights_rolling はあなたの既存関数
    _, _, w_m6 = build_method6_raw_weights_rolling(ff, lookback_years=lookback_years_method6, min_obs=min_obs)
    m6 = method6_strategy_df(ff, w_m6, target_vol=target_vol, L=L)

    # ---- zstar（既存シリーズを戦略へ：FA と同じ “予測子→重み” 変換）
    # ここでは zstar を “predictor” とみなし、FA と同じ作りで market tilt を作る（符号はデータ駆動）
    zstar = zstar.reindex(idx).rename("zstar")
    z_fa = build_fa_weights_from_predictor(
        predictor=zstar,
        mkt_excess=mkt_excess,
        month_type=month_type,
        min_obs=min_obs,
        target_vol=target_vol,
        L=L,
        use_conditional_sign=False,
    )

    # ---- リターン series 整形
    out = {}

    out["FA(EE)"] = pd.DataFrame({
        "strat_excess": fa["strat_excess"],
        "strat_total": rf.reindex(fa.index) + fa["strat_excess"],
        "w": fa["w_scaled"],
        "month_type": fa["month_type"]
    })

    out["cFA(EE)"] = pd.DataFrame({
        "strat_excess": cfa["strat_excess"],
        "strat_total": rf.reindex(cfa.index) + cfa["strat_excess"],
        "w": cfa["w_scaled"],
        "month_type": cfa["month_type"]
    })

    out["Method6"] = m6[["strat_excess","strat_total","w_scaled","month_type"]].rename(columns={"w_scaled":"w"})

    out["zstar"] = pd.DataFrame({
        "strat_excess": z_fa["strat_excess"],
        "strat_total": rf.reindex(z_fa.index) + z_fa["strat_excess"],
        "w": z_fa["w_scaled"],
        "month_type": z_fa["month_type"]
    })

    out["mkt"] = pd.DataFrame({
        "strat_excess": mkt_excess,
        "strat_total": mkt_total,
        "w": 1.0,  # buy&hold
        "month_type": month_type
    })

    # ---- サマリー（年率統計 + CAPM alpha）
    rows = []
    for name, df_ in out.items():
        r_tot = df_["strat_total"].dropna()
        mu_a, sd_a, sh = annualized_stats(r_tot)

        a, t, b, _ = capm_alpha_tstat(df_["strat_excess"], mkt_excess)

        rows.append({
            "name": name,
            "ann_return": mu_a,
            "ann_vol": sd_a,
            "sharpe": sh,
            "alpha_m": a,
            "t(alpha)": t,
            "beta": b
        })
    summary = pd.DataFrame(rows).set_index("name").sort_values("t(alpha)", ascending=False)

    return out, summary

# ============================================================
# G. 可視化（累積資産、weights、α分解）
# ============================================================

def plot_wealth_curves(strat_dict, ff: pd.DataFrame, title="Cumulative Wealth"):
    mkt_total = (ff["mkt_excess"] + ff["rf"])
    plt.figure(figsize=(14, 5))
    for name, df in strat_dict.items():
        r = df["strat_total"].dropna()
        w = (1.0 + r).cumprod()
        plt.plot(w, label=name, linewidth=2 if name != "mkt" else 1.5, linestyle="--" if name=="mkt" else "-")
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.show()

def plot_weights(strat_dict, start=None, end=None, title="Strategy Weights"):
    plt.figure(figsize=(14, 5))
    for name, df in strat_dict.items():
        if name == "mkt":
            continue
        w = df["w"]
        if start is not None:
            w = w.loc[start:]
        if end is not None:
            w = w.loc[:end]
        plt.plot(w, label=name, linewidth=1.5)
    plt.axhline(0.0, linewidth=1)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.show()

def run_alpha_decomp_all(strat_dict, ff: pd.DataFrame):
    mkt_excess = ff["mkt_excess"]
    month_type = classify_month_type(ff.index)

    out_tables = {}
    out_infos = {}
    for name, df in strat_dict.items():
        if name == "mkt":
            continue
        tab, info = alpha_decomposition_by_monthtype(
            strat_excess=df["strat_excess"],
            mkt_excess=mkt_excess,
            month_type=month_type.reindex(df.index)
        )
        out_tables[name] = tab
        out_infos[name] = info
    return out_tables, out_infos
```

* * *

2\. 使い方（あなたの main を置き換える最小例）
============================

以下をあなたの `if __name__ == "__main__":` の末尾に追加してください。

```python
if __name__ == "__main__":
    csv_path = "F-F_Research_Data_Factors.csv"
    ff = load_ff_monthly_from_ken_french(csv_path)

    # 例：期間を揃える（あなたと同様）
    ff = ff.loc[:"2018-01-01"].copy()

    # ====== 既存 z*_t をここで準備（あなたの既存実装から Series を渡す） ======
    # 例：ダミー（必ずあなたの z*_t に置換してください）
    # zstar = pd.Series(0.0, index=ff.index)
    # ※本番は、あなたが既に作っている z*_t（オンライン版など）を代入
    zstar = pd.Series(np.nan, index=ff.index)  # placeholder

    # zstar が NaN だと zstar 戦略が無意味になるので、最低限のガード
    # （実運用では削除してOK）
    if zstar.notna().sum() < 200:
        # サンプルとして “EE predictor の demean” を入れて動作確認だけ可能に
        mkt_total = ff["mkt_excess"] + ff["rf"]
        S, _ = compute_newsy_sum_signal(mkt_total, k_lags=4)
        zstar = (S.shift(1) - S.shift(1).expanding().mean()).fillna(0.0)

    strat_dict, summary = compare_ee_fa_method6_zstar(
        ff=ff,
        zstar=zstar,
        min_obs=120,
        target_vol=0.05,
        L=3.0,
        lookback_years_method6=20
    )

    print("\n=== Summary (annual stats + CAPM alpha) ===")
    print(summary)

    plot_wealth_curves(strat_dict, ff, title="Cumulative Wealth: EE×FA×Method6×z*")

    plot_weights(strat_dict, start="1970-01-01", title="Scaled Weights (post-1970)")

    # newsy / non-newsy α 分解
    tables, infos = run_alpha_decomp_all(strat_dict, ff)

    for name, tab in tables.items():
        print(f"\n=== Alpha Decomposition: {name} ===")
        print(tab)
        info = infos[name]
        print(f"pi_N={info['pi_N']:.3f}, alpha_weighted_avg={info['alpha_weighted_avg']:.6f}, "
              f"alpha_all={info['alpha_all']:.6f}, cross_term={info['cross_term']:.6f}")
```

* * *

3\. α 分解 “スライド原稿”（newsy / non-newsy 別）
======================================

以下は PowerPoint 1–2枚でそのまま貼れる体裁（日本語・専門家向け）です。  
（あなたの好み的に英語スライドが必要なら、このまま英訳できます。）

* * *

Slide 1: Earnings-Cycle Predictability と Forecast-Agnostic 実装の統合
----------------------------------------------------------------

**目的**

*   Earnings Extrapolation (EE) が示す **newsy / non-newsy の条件付予測可能性**を、  
    Forecast-Agnostic (FA) の思想（推定誤差を抑える）で **実運用可能な market-timing** に落とす。

**EE predictor（実装）**

*    $S_t = \sum_{j=1}^{4} r^{\text{tot}}_{nm(t,j)}$ （直近 4 つの newsy 月トータルリターン合計）
*   newsy 月（N）は四半期第1月、non-newsy は R/3

**FA portfolio（実装）**

*   予測子を逐次平均で中心化： $\tilde x_t = x_t - \bar x_t$ 
*   係数推定は **符号のみ**： $s_t=\text{sign}(\hat\beta_t)$ 
*   raw weight： $w^{raw}_t = s_t\tilde x_t$ 
*   逐次ボラターゲット： $w_t = w^{raw}_t \cdot \sigma^\*/\hat\sigma_{t-1}$ 
*   レバ制約： $w_t\in[-3,3]$ 

**conditional-FA（EE の含意の注入）**

*   月タイプで符号を反転（newsy は reversal、non-newsy は continuation）
    $$
    w^{raw}_t = s_t \cdot c_t \cdot \tilde x_t,\quad c_t= \begin{cases} -1 & t\in N\\ +1 & t\in R,3 \end{cases}
    $$

* * *

Slide 2: CAPM α の newsy / non-newsy 分解（回帰ベース）
---------------------------------------------

**評価：CAPM α（全期間）**

$$
r^{strat}_t = \alpha + \beta\, r^{mkt}_t + \varepsilon_t
$$

**部分サンプル α**

*   newsy（N）
    $$
    r^{strat}_t = \alpha_N + \beta_N r^{mkt}_t + \varepsilon_t,\quad t\in N
    $$
*   non-newsy（R,3）
    $$
    r^{strat}_t = \alpha_{NN} + \beta_{NN} r^{mkt}_t + \varepsilon_t,\quad t\in R,3
    $$

**分解（加重平均＋交差項）**

$$
\alpha_{\text{ALL}} = \pi_N \alpha_N + (1-\pi_N)\alpha_{NN} + \underbrace{\Delta}_{\text{交差項}}
$$
*    $\pi_N$ ：newsy 月比率（理論上 ≈ 1/3）
*    $\Delta\neq0$  は「サンプル分割による β の差・共分散構造の違い」を表す

**示したい事実（想定される解釈）**

*   EE×FA では、α は **non-newsy 側で主に生成**されやすい
*   conditional-FA は、newsy 側の reversal を能動的に取りにいくため、**α の源泉が分散**し得る
*   Method6 / z\*\_t は、あなたの構造的（mispricing）設計により、α がどの月タイプに集中するかが重要な診断になる

* * *

4\. 追加で入れると強い診断（任意だが推奨）
=======================

あなたが以前から気にしている「2020年以降で弱い」問題に直結するので、次の2つを加えると議論が締まります。

1.  **時変 α（rolling CAPM alpha）**：10年ローリングで α と t 値の推移
2.  **month\_type 別の戦略リターン分解**：
    *    $E[r^{strat}|N]$ ,  $E[r^{strat}|R]$ ,  $E[r^{strat}|3]$ 
    *   戦略が “N で稼ぐのか / N で守るのか” を明示

必要なら、そのコードもこの枠組みに自然に追加します（あなたの `plot` 方針に合わせて matplotlib で分離プロット）。

* * *

次にあなたがやること（最小）
--------------

*   上の統合コードに対して、あなたの既存 `z*_t`（Series）を `zstar` に渡すだけです。
    *   “オンラインで有効な予測子をモニタして切替える” という今の問題意識とも整合します。

z\*\_t の元コード（関数名と返り値だけでも）をこのスレッドに貼っていただければ、\*\*z\*\_t をこの三者比較フレームに完全統合（同じボラターゲット・同じ α 分解）\*\*した最終版に整形します。

## Response:
以下では、あなたが運用対象としている 4 つ（**EE→FA**, **EE→conditional-FA**, **Method 6**, **z\*\_t（既存）**）を、\*\*学術的に「何を推定し／何を捨て／どの仮定で α を狙うのか」\*\*という観点で、できるだけ厳密に整理します。加えて、**OOS R² と α の関係**、**bias–variance**、\*\*実装上の非自明点（情報集合・ボラターゲット・制約）\*\*まで含めます。

* * *

1\. 共通の枠組み：予測回帰と投資家の意思決定
------------------------

### 1.1 予測回帰（time-series predictability）

市場超過収益  $r_{t+1}$  と予測子  $x_t$  に対し、標準形は

$$
r_{t+1}=\alpha+\beta x_t+\varepsilon_{t+1},\qquad \mathbb{E}[\varepsilon_{t+1}\mid\mathcal{F}_t]=0.
$$

ここで問題は「 $\beta$  を推定して **数値予測**を作り、その予測でポジション量を決める」ことが有限標本で不安定になりやすい点です。特に expanding/rolling による  $\hat\beta_t$  は、予測力が弱いと **推定誤差分散が支配的**になり、OOS の MSE（＝OOS R²）を悪化させます。

### 1.2 投資パフォーマンス評価：なぜ平均収益ではなく α か

市場は平均超過収益が正になりやすいので、「ロング・ショート（市場へのティルト）戦略が市場より平均収益で勝つ」ことを要求するのは過剰に厳しい。投資家が市場を既に保有しているなら、追加ポジションの価値は

$$
r^{\text{strat}}_t = \alpha + \beta^{\text{strat}} r^{mkt}_t + u_t
$$

の \*\* $\alpha$ （CAPM alpha）\*\*として測るのが自然です。

* * *

2\. EE predictors を用いた FA（Forecast-Agnostic）運用
----------------------------------------------

### 2.1 EE（Earnings Extrapolation）の学術的意味：条件付の予測可能性

EE の主張（要点）は「市場リターンの自己相関（モメンタム／リバーサル）が一様ではなく、**四半期決算情報の到来タイミング（newsy month）に条件付く**」というものです。

*   newsy month（四半期の第1月）では **リバーサル（負の自己相関）**
*   non-newsy（残り）では **モメンタム（正の自己相関）**

これを抽象化すると、期待収益は

$$
\mathbb{E}[r_{t+1}\mid \mathcal{F}_t] = \alpha + \beta(\text{month type})\cdot x_t
$$

のように **係数が状態（month type）で変わる**、すなわち「条件付線形予測」です。

あなたの EE predictor（例：直近 4 つの newsy 月トータルリターン合計  $S_t$ ）は、まさに「決算情報が市場に織り込まれる周期」によって生じる **ミスプライシングの蓄積**（または投資家の期待形成誤差）を proxy します。

### 2.2 FA の学術的意義：係数推定の“量”を捨て、符号と水準で tilting

FA の基本は「予測回帰の係数  $\beta$  を逐次推定して数値予測を作る」のではなく、

*   予測子の **水準**（中心化された  $x_t-\bar x_t$ ）
*   係数の **符号**（ $\text{sign}(\hat\beta_t)$ ）

だけを用いて市場へのロング／ショートを決めることです。

典型的には（あなたの実装と同型に）

1.  逐次中心化
    
$$
\tilde x_t = x_t - \bar x_t,\quad \bar x_t=\frac{1}{t}\sum_{s\le t}x_s
$$
2.  expanding 回帰の符号のみ
    
$$
s_t=\text{sign}(\hat\beta_t)
$$
3.  raw weight
    
$$
w^{raw}_t = s_t \tilde x_t
$$
4.  リスク予算（ボラターゲット）でスケール
    
$$
w_t = w^{raw}_t \cdot \frac{\sigma^\*}{\hat\sigma_{t-1}}
$$
5.  実行可能性制約
    
$$
w_t \in [-L, L]
$$

### 2.3 学術的に何が起きているか（bias–variance の観点）

*   **捨てたもの**： $|\hat\beta_t|$  の情報（“どれだけ儲かるか”の推定）
*   **残したもの**：方向（符号）と状態（ $x$  水準）
*   **得たもの**：推定誤差分散の大幅減（ $\hat\beta$  を乗数にしない）

弱い予測力では、数値予測の改善よりも **分散削減**の便益が勝ち、結果として **OOS R² は悪いままでも α は正**になり得ます。

* * *

3\. EE predictors を用いた conditional-FA 運用
----------------------------------------

### 3.1 conditional-FA の本質：状態依存の符号を理論から注入

EE は「newsy / non-newsy で符号が変わる（reversal vs momentum）」という、**状態依存の方向性**を与えます。これを最小限に FA へ注入すると

$$
w^{raw}_t = s_t \cdot c_t \cdot \tilde x_t, \quad c_t= \begin{cases} -1 & t \in \text{Newsy}\\ +1 & t \in \text{Non-newsy} \end{cases}
$$

となります（あなたの設計どおり）。ここで

*    $s_t$ ：データ駆動の “全体符号”
*    $c_t$ ：EE 理論が示す “状態での符号反転”

という二層構造です。

### 3.2 学術的含意：部分的構造モデル（semi-structural shrinkage）

conditional-FA は、

*   完全構造モデル（状態ごとに  $\beta_N, \beta_{NN}$  を推定）
*   完全非構造（FA：符号以外は捨てる）

の中間です。状態依存の符号は \*\*強い事前（prior）\*\*として働き、

*   推定パラメータ数を増やさず
*   方向性だけ理論整合させる

ため、やはり bias–variance のトレードオフで “分散を抑えつつミススペックを減らす” 位置づけになります。

* * *

4\. Method 6（あなたのコード）による運用：構造モデル型のオンライン推定
-----------------------------------------

### 4.1 モデル式（あなたの実装に忠実）

あなたの Method 6 は、トータルリターン  $R^{tot}_t$  を

$$
R^{tot}_t=\mu_{t-1} + \beta x_t + \varepsilon_t, \quad \mu_{t-1}=\mathbb{E}[R^{tot}_t\mid \mathcal{F}_{t-1}] \approx \text{expanding mean of } R^{tot}
$$

と書き、平均を差し引いた

$$
y_t = R^{tot}_t - \mu_{t-1}
$$

に対して **切片なし**で

$$
y_t = \beta x_t + \varepsilon_t
$$

を推定しています（あなたの closed-form 推定式は）

$$
\hat\beta_t = \frac{\sum_{s \le t} x_s y_s}{\sum_{s \le t} x_s^2}.
$$

そして raw weight を

$$
w^{raw}_t = \hat\beta_t x_t
$$

と置きます。

### 4.2 学術的意味：最小二乗推定 + “期待収益の構造化”

Method 6 は FA と異なり、 $\hat\beta_t$  の **大きさ**を使います。これは

*    $x_t$  がミスプライシングの強度（あなたの  $S$  を中心化し符号調整したもの）
*    $\beta$  がそのミスプライシングが将来収益へ移る “変換率”

という、より **構造的解釈**を持ちます。

ただし、 $|\hat\beta_t|$  を掛ける以上、有限標本では

*    $\hat\beta_t$  の推定誤差が weight の分散を増やす
*   これが OOS 性能を押し下げうる

という FA 論文の指摘と同じリスクを内包します。

### 4.3 rolling 推定の学術的位置づけ

rolling（例：20年）にするのは

*   構造変化（time-variation）を許容
*   ただしサンプルサイズ減で推定分散が上がる

というトレードオフです。現代データで「効果が薄い」場合、rolling はしばしば合理的ですが、最終的には **推定分散とバイアス**のどちらが支配的かを診断する必要があります。

* * *

5\. z\*\_t（既存）運用：オンライン予測子選択・縮約・複数シグナル統合の系統
------------------------------------------

あなたの z\*\_t は（過去ログから）単一予測子ではなく、

*   いくつかの月タイプ（N/R/3）や信号（nr+P4 等）をモニタ
*   “オンラインで有効な予測子を切り替える”
*   ボラターゲットや制約を付ける

という設計思想でした。

学術的には、これは以下のいずれか（または混合）として理解できます。

### 5.1 Model Selection / Model Averaging（逐次）

*   各候補モデル  $k$  が予測  $\hat r^{(k)}_{t+1}$  を出す
*   損失（予測誤差や投資効用）に基づき重み  $p^{(k)}_t$  を更新
*   最終予測  $\sum_k p^{(k)}_t \hat r^{(k)}_{t+1}$  または best-k を採択

これは統計学的には Bayesian model averaging / exponential weights / online learning の系統です。

### 5.2 Shrinkage / Regularization

予測子が多いほど推定分散が増えるため、

*   係数を縮約（ridge / lasso / Bayes prior）
*   あるいは FA 的に “符号だけ使う” などの極端な縮約

でノイズを抑える方向です。

### 5.3 Regime-dependent policy（状態依存ルール）

month\_type やボラ状態を regime とし、

*   regime ごとに異なる予測子（または異なる符号）を採用
*   あるいは threshold で切替

という設計で、EE と非常に相性が良いです。

* * *

6\. 4 手法の比較：何を仮定し、何を推定し、どこで α を狙うか
----------------------------------

### 6.1 仮定と推定の強さ（弱→強）

*   **FA(EE)**：最小限（符号＋水準、量を捨てる）
*   **conditional-FA(EE)**：状態依存の符号という理論を注入（だが係数量は捨てる）
*   **Method 6**： $\beta$  の量を推定し、 $w=\beta x$ （構造モデル寄り）
*   **z\*\_t**：複数信号の選択・重み付け（最も複雑、設計次第で高分散にも低分散にも）

### 6.2 期待される経験則（学術的予測）

*   サンプルが短く予測が弱い：FA / conditional-FA が有利（分散優位）
*   予測力が強くデータが十分：Method 6 / z\*\_t が有利（バイアス低下）
*   構造が条件付（EE のように符号が変わる）：conditional-FA が有利になり得る

* * *

7\. newsy / non-newsy 別 α 分解が意味するもの（解釈）
---------------------------------------

あなたの分析設計（部分サンプル CAPM）で得る

$$
\alpha_N,\ \alpha_{NN}
$$

は単なる “どの月で儲かったか” 以上に、

*   EE の仮説（newsy = reversal）が戦略の源泉か
*   それとも non-newsy のトレンド追随が源泉か
*   あるいは単なる露出差（ $\beta_N \neq \beta_{NN}$ ）か

を分離する診断になります。

特に conditional-FA では、設計上

*   N で符号を反転させる

ため、 $\alpha_N$  が改善するなら EE の経済メカニズムに整合的、改善しないなら「符号反転は過剰」または「市場構造が変わった」可能性が高い、という解釈が可能です。

* * *

8\. 実務上の注意（学術的にも重要）
-------------------

1.  **情報集合の整合（look-ahead）**
    *    $x_t$  を作る際、必ず “t 時点で利用可能” なデータだけを使用する
    *   特に決算カレンダーに絡むデータは月末確定タイミングが論点になる
2.  **ボラターゲットの逐次性**
    *   全期間一括スケールは「当時点では未知の将来分散」を使うことになる
    *   FA/conditional-FA と比較するなら、Method 6 も逐次スケールが望ましい（提示コードはその版）
3.  **レバ制約**
    *   理論上は線形だが、実務ではクリップが不可避
    *   クリップが α を「削る」だけでなく「tail risk を抑え t 値を改善」することもある（分散削減効果）

* * *

ここまでの要約（ワンパラ）
=============

*   **FA(EE)** は「推定係数の量を捨てる」ことで弱い予測の世界で bias–variance を最適化し、OOS R² が負でも α を得うる。
*   **conditional-FA(EE)** は EE が示す条件付構造（newsy vs non-newsy）を “符号の事前” として注入し、分散を増やさずにミススペックを減らす。
*   **Method 6** は  $\beta$  をオンライン推定し  $w=\beta x$  とする構造モデル型で、強いシグナルでは有利だが、推定分散の影響を受けやすい。
*   **z\*\_t** はオンライン学習・モデル選択／縮約の設計次第で、最も適応的になり得る一方で、複雑さが分散を招く可能性もある。

* * *

必要であれば、あなたの “既存 z\*\_t” の数式定義（どの信号をどう合成し、どの損失で切替えるか）に合わせて、上の説明を \*\*完全に論文調（定理・命題・補題）\*\*に落とし込み、比較の理論節（“FA vs Method6 vs online selection” の bias–variance 分解）まで書き起こします。

## Response:
以下、提示された **Summary（年率統計＋CAPM α）** と **newsy / non-newsy 別 α 分解**を、学術的に一貫する形で解釈します。結論から言うと、結果はかなり明確で、

1.  **EE サイクルを条件付けに使う（cFA）ほど α が強くなる**
2.  α の源泉は主に **Non-newsy（R,3）月**で、FA(EE) と zstar は **Newsy（N）月で負の α** を出している
3.  cFA と Method6 は **N 月の符号反転を取り込んだ（あるいは内生的にそうなる）ため N 月で α が正に転じ、全体 α が大きく改善**
4.  いずれも \*\*市場βがほぼ 0（むしろわずかに負）\*\*なので、これは「市場リスクを取って得た収益」ではなく **market-neutral に近い異常収益**として読める

という構図です。

* * *

1\. Summary（年率統計＋CAPM α）の解釈
---------------------------

### 1.1 まず見るべきは α と t 値

*   **cFA(EE)**: 月次 α = **0.00563**（約 0.563% / 月）、t=**4.89**
*   **Method6**: 月次 α = **0.00495**、t=**3.65**
*   **FA(EE)**: 月次 α = **0.00281**、t=**2.44**
*   **zstar**: 月次 α = **0.00265**、t=**2.14**

この順位は「理論注入（条件付符号）と構造推定（β\_t x\_t）が、単純 FA より有効だった」ことを示しています。

特に **cFA(EE)** の t=4.89 は、単なる偶然や過剰適合では説明しにくい強さで、少なくとも **“この期間サンプルでは” 統計的に強固**です。

### 1.2 β（市場露出）が小さく負 → “市場タイミング”ではなく “ほぼ市場中立α”

β が

*   cFA: -0.034
*   Method6: -0.057
*   FA: -0.048
*   zstar: -0.036

といずれも **ほぼ 0**で、やや負。  
これは次を意味します：

*   これら戦略の収益は「市場上昇局面に強く乗った」結果ではない
*   **市場因子をほぼ消した残差（u\_t）で稼いでいる**
*   投資家の視点では、既存の株式保有（β≈1）に対して \*\*“ヘッジ的に追加して α を積む”\*\*タイプのストラテジー

一方、市場（mkt）は β=1、α≈0 は当然です（CAPMベンチマーク）。

### 1.3 Sharpe の順位と α の順位が一致しているのが重要

Sharpe：

*   cFA 0.71（最良）
*   mkt 0.63
*   Method6 0.54
*   FA 0.46
*   zstar 0.42

あなたのボラターゲット設計（一定リスク予算）下で、**Sharpe の改善＝α の改善**になっている。  
これは「単なるレバ調整やリスク取りではなく、真にリスク調整後収益が改善」していることを示唆します。

* * *

2\. α 分解（newsy / non-newsy）で見える “勝ち筋”
-------------------------------------

ここが本題で、EE と FA を統合した意味が最も出ています。

### 2.1 FA(EE) と zstar：N 月で負、Non-newsy で正

**FA(EE)**

*   ALL: +0.00281
*   N: **\-0.00416**（t=-2.25）
*   Non-newsy: **+0.00621**（t=4.32）

**zstar** も同型

*   N: **\-0.00465**（t=-2.46）
*   Non-newsy: **+0.00624**（t=3.93）

これは非常に重要で、次の読みになります：

*   あなたの EE predictor（新sy合計）や zstar が捉えるシグナルは、  
    **Non-newsy（月R,3）では “順張り的に効く”**（モメンタム側）
*   しかし **Newsy（月N）では符号が逆**で、同じポジションを続けると損する（リバーサル側）

つまり EE の含意（newsy では reversal）が、まさにこの **N 月の負 α**として観測されています。  
FA(EE) は「符号を全期間で一貫にした」ため、N 月で取りこぼし（逆張りできずに負 α）を出している、と解釈できます。

### 2.2 cFA(EE)：N 月が正に転じ、Non-newsy の正は維持

**cFA(EE)**

*   ALL: +0.00563（t=4.89）
*   N: **+0.00417**（t=2.24）
*   Non-newsy: **+0.00629**（t=4.32）

ここで見てよい因果は単純です：

*   conditional-FA は **N 月で符号を反転**させる設計
*   その結果、FA(EE) で負だった N 月の α が **正に反転**
*   Non-newsy の α はほぼ同水準のまま
*   よって全体 α が **約2倍**に増えた（0.0028 → 0.0056）

これは EE×FA の統合がうまくいっている典型例で、**EE が示した「条件付の符号」を、FA の低分散実装で取り込むと α が増える**、というストーリーが成立しています。

### 2.3 Method6：N と Non-newsy の両方で安定して正

**Method6**

*   ALL: +0.00495（t=3.65）
*   N: +0.00481（t=2.10）
*   Non-newsy: +0.00494（t=2.94）

Method6 は N / Non-newsy の差が小さく、**どちらでもプラス**です。  
これは「β\_t x\_t の構造推定」が、結果的に

*   N 月では（あなたの x\_t の sign 調整＋β推定を通じて）逆符号方向を取り込み
*   Non-newsy では順符号方向を取り込み

という **より滑らかな適応**になっている可能性が高いです。  
ただし cFA より Sharpe / t(α) が低いのは、Method6 が ** $\hat\beta_t$  の推定分散**を抱えており、FA 系よりノイズが残る（FA論文の bias–variance の論点）と整合的です。

* * *

3\. cross\_term がほぼ 0：分解がきれいに成立している
-----------------------------------

各戦略で

*   cross\_term ≈ 0.00005（月次で 0.5bp 程度）

と極小です。  
これは「全体 α は、ほぼ単純に **(1/3)×N α + (2/3)×Non-newsy α** で説明できる」ことを意味し、**月タイプで分割するだけで α の構造がほぼ解ける**、という強いメッセージです。

* * *

4\. 実務・研究上の含意（次に何を確かめるべきか）
--------------------------

### 4.1 もっとも自然な解釈（学術ストーリー）

*   **予測可能性は主に Non-newsy で発現**（正の α）
*   **Newsy では符号が反転**し、無条件運用（FA(EE), zstar）だと負 α が出る
*   EE が示す条件付構造を使って **符号反転を組み込むと（cFA）全体 α が大きく改善**
*   Method6 は構造推定でそれを部分的に内生化するが、推定ノイズが残るため cFA に劣後

このまま論文レベルの説明が組めます。

### 4.2 ただし “異常にきれい” なので確認すべき点

この結果が強い分、以下は必ず検証すると良いです（反証可能性を高めるため）。

1.  **取引タイミング（x\_t の利用時点）**
    *   予測子が当月末に確定し、翌月に投資する、という情報整合が崩れていないか
    *   特に S\_t（newsy月合計）をいつ観測した扱いにしているか
2.  **逐次ボラターゲットの実装差**
    *   cFA が N 月で正になったのが「符号」だけでなく「ボラ推定の窓」由来でないか
    *   例：N 月だけ分散構造が違い、スケールが偏っていないか
3.  **サブサンプル安定性（post-2000 / post-2010 / post-2020）**
    *   あなたが懸念している “2020年以降の弱化” は、まさにここで再確認すべきです
    *   N/Non-newsy 別に α がどちらで崩れるのかを見ると原因が特定しやすい

* * *

5\. 端的な結論
---------

*   **cFA(EE) が最も優れている理由**は、EE の「newsy で符号反転」という条件付構造を、FA の「低分散・符号中心の実装」で取り込み、**N 月の負 α を正 α に転換した**からです。
*   **FA(EE) と zstar が N 月で負 α**なのは、条件付構造（reversal）を無視したためと整合的です。
*   **Method6 は両方で正**だが、推定ノイズの分だけ cFA に劣後している可能性が高いです。

* * *

必要なら、次の 2 点を追加で出すと解釈がさらに確定します（コードもすぐ書けます）：

1.  **rolling 10年の α（全体/N/Non-newsy）推移プロット**
2.  **月タイプ別の平均ポジション（w）と、そのときの市場リターンの分布**（符号反転が効いているかの直接証拠）

希望する期間（例：1970以降／1990以降／2000以降／2020以降）を指定いただければ、その前提で出力形式も含めて整えます。

## Response:
承知しました。ここでは **CAPM（資本資産価格モデル）そのものの意味**から出発し、**今回の結果をどう読むべきか**を、専門性を保ちつつも「なぜこの α が重要なのか」が直感的に分かるように整理します。  
（数式 → 経済解釈 → 今回の数値、の順で説明します。）

* * *

1\. そもそも CAPM とは何か（今回の分析に必要な最小限）
--------------------------------

### 1.1 CAPM の基本式

CAPM は、

> **市場リスク（β）で説明できない部分は、理論上存在しない**

という仮説です。式で書くと

$$
\mathbb{E}[R_i - R_f] = \beta_i \, \mathbb{E}[R_m - R_f]
$$
*    $R_i$ ：資産（または戦略） $i$  のリターン
*    $R_f$ ：無リスク金利
*    $R_m$ ：市場ポートフォリオ
*    $\beta_i$ ：市場に対する感応度（市場リスク量）

つまり、

> **β だけで期待収益は決まる**  
> → β を取らない限り、余分な期待収益は得られない

というのが CAPM の主張です。

* * *

### 1.2 実証で使う形（α・β 分解）

実務・実証では、次の回帰で検証します：

$$
R^{\text{strat}}_t - R_f = \alpha + \beta (R_{m,t} - R_f) + \varepsilon_t
$$
*   **β（ベータ）**  
    → 市場が 1% 動いたとき、戦略が平均どれだけ動くか
*   **α（アルファ）**  
    → 市場リスクでは説明できない「余剰収益」

> CAPM が正しければ  
> ** $\alpha = 0$ ** でなければならない

したがって、

*   **α が正で統計的に有意**  
    → CAPM では説明できないリターン源泉がある  
    → 「投資戦略として意味がある」

という解釈になります。

* * *

2\. 今回の分析で「α」を見る理由（R²ではダメなのか？）
------------------------------

### 2.1 OOS R² が示すのは「予測の上手さ」

OOS R² は、

> 「市場リターンを数値として当てられたか」

を見る指標です。  
しかし、

*   市場リターンの予測は非常にノイズが大きい
*   β の推定誤差が支配的になりやすい

という問題があります。

* * *

### 2.2 投資家が本当に欲しいのは「α」

投資家の視点では、

*   すでに市場（β≈1）を保有している
*   追加戦略は **市場とは独立に儲かるか** が重要

したがって、

> **市場とどれだけ相関しないか（β）**  
> **市場では説明できない収益があるか（α）**

が本質になります。

今回あなたが見ている **CAPM α** は、まさに

> 「市場を取り除いた後に、まだ残る利益」

を定量化しています。

* * *

3\. 今回の Summary を CAPM の視点で読む
-----------------------------

再掲します：

```
         ann_return  ann_vol  sharpe   alpha_m  t(alpha)   beta
cFA(EE)    0.0972     0.136   0.713   0.00563     4.89    -0.034
Method6    0.0871     0.161   0.540   0.00495     3.65    -0.057
FA(EE)     0.0621     0.136   0.457   0.00281     2.44    -0.048
zstar      0.0612     0.147   0.416   0.00265     2.14    -0.036
mkt        0.1156     0.184   0.629   ~0          1.88     1.00
```

### 3.1 β の解釈（最重要ポイント）

*   市場：β = **1.00**  
    → 市場が 1% 上がれば 1% 上がる（当然）
*   他の戦略：β ≈ **0（むしろやや負）**

これは、

> **これらの戦略は市場リスクをほとんど取っていない**

ことを意味します。

つまり、

*   市場が上がっても下がっても
*   市場とは独立に

収益を出している可能性が高い、ということです。

* * *

### 3.2 α の解釈（何がすごいのか）

たとえば **cFA(EE)**：

*   月次 α = **0.563%**
*   年率換算 ≈ **6.8%**
*   t 値 = **4.89**（非常に強い）

これは、

> 「市場リスクをほぼ 0 に抑えたまま、  
> 年率で 6–7% の超過収益を生んでいる」

という意味になります。

CAPM の世界では、これは **理論的に“ありえない”** はずの結果です。

* * *

4\. newsy / non-newsy 分解を CAPM で理解する
------------------------------------

### 4.1 FA(EE)：なぜ N 月で α が負なのか

```
FA(EE):
  N(newsy)       α = -0.00416
  Non-newsy      α = +0.00621
```

CAPM 的には、

*   市場 β で説明できない部分（α）が
*   月タイプによって **符号ごと変わる**

ということを意味します。

これは、

> CAPM が想定する「一様なリスク・リターン構造」が  
> 実際には **決算サイクルで破れている**

ことの直接的証拠です。

* * *

### 4.2 cFA(EE)：なぜ改善したのか

```
cFA(EE):
  N(newsy)       α = +0.00417
  Non-newsy      α = +0.00629
```

cFA は、

*   CAPM が無視している  
    **「状態（newsy / non-newsy）」**
*   に応じてポジションの **符号を切り替えた**

その結果、

> 市場 β では説明できない負の歪み（N 月）を  
> 正の α に変換できた

と解釈できます。

* * *

### 4.3 Method6：構造推定で CAPM を部分的に超える

Method6 は、

*   CAPM の β ではなく
*   **mispricing 指標  $x_t$ ** に対する β を推定

しているため、

> 市場 β では説明できない変動を  
> 別の因子（EE 的 mispricing）で説明

していると見なせます。

そのため、

*   CAPM α が正
*   かつ N / Non-newsy で比較的安定

という結果になります。

* * *

5\. 直感的なたとえ（CAPMを噛み砕く）
----------------------

### 市場＝「天気」、戦略＝「傘の売上」

*   CAPM：  
    「雨（市場）が降れば、傘は売れる。  
    晴れ（市場）なら売れない。」
*   あなたの戦略：  
    「雨の日でも、晴れの日でも、  
    **決算発表の翌月はなぜか傘が売れる**」

CAPM では説明できないこの売上増が **α** です。

* * *

6\. まとめ（CAPM視点での結論）
-------------------

1.  **CAPM は市場リスク（β）しか見ていない**
2.  今回の戦略は **β≈0** なのに **α>0**
3.  つまり
    *   市場リスクでは説明できない
    *   決算サイクル（EE）由来の構造的な歪み  
        を捉えている
4.  cFA(EE) は
    *   CAPM が無視する「状態依存性」を
    *   最小限のルールで取り込んだため
    *   最も強い α を示した

* * *

### 次にやると説得力が最大になること

*   **Fama–French 3因子 / 5因子回帰**  
    → α が “市場以外の既知因子” でも消えないか確認
*   **post-2000 / post-2010 / post-2020 の α 分解**  
    → 裁定・弱化の検証

必要であれば、**CAPM → FF3/FF5 への拡張コードと、同じ形式の α 分解表**をすぐに用意できます。

## Response:
思考時間: 12s

以下に、あなたの現在のフレーム（`ff` に `mkt_excess`,`rf` があり、戦略ごとに `strat_excess` を持つ）へ **そのまま接続できる**形で、

*   **CAPM → FF3（Fama-French 3因子）→ FF5（5因子）** の α 推定
*   **newsy / non-newsy 別の α 分解（各モデルで）**
*   **サブサンプル（post-2000 / post-2010 / post-2020 など）での頑健性チェック**

を追加する完全実装を提示します。  
（t値は標準の OLS か、より実務的に **Newey–West(HAC)** を選べるようにします。）

* * *

1) 追加コード（ロード・回帰・分解・サブサンプル）
--------------------------

> あなたの `load_ff_monthly_from_ken_french` / `classify_month_type` / `annualized_stats` / `compare_ee_fa_method6_zstar` 等と同じファイルに追記してください。

```python
import pandas as pd
import numpy as np
import statsmodels.api as sm

# ============================================================
# (1) Ken French CSV ローダ（FF3 / FF5）
# ============================================================

def _load_kenfrench_monthly_table(csv_path: str, cols_needed: list):
    """
    Ken French の csv（冒頭コメント＋月次テーブル＋年次テーブル）から
    月次部分だけを切り出して cols_needed を返す汎用ローダ。

    想定列名例:
      - FF3: 'Mkt-RF','SMB','HML','RF'
      - FF5: 'Mkt-RF','SMB','HML','RMW','CMA','RF'
    """
    raw = pd.read_csv(csv_path, skiprows=4)

    # 月次行は 'YYYYMM' が数値として入っている
    num = pd.to_numeric(raw.iloc[:, 0], errors='coerce')
    mask_monthly = num > 10000
    monthly = raw.loc[mask_monthly].copy()

    # 日付列名はファイルにより 'Unnamed: 0' など。先頭列を date とみなす
    date_col = monthly.columns[0]
    monthly = monthly.rename(columns={date_col: "date"})
    monthly["date"] = pd.to_datetime(monthly["date"].astype(int), format="%Y%m")
    monthly = monthly.set_index("date").sort_index()

    # 必要列を numeric 化
    for c in cols_needed:
        if c not in monthly.columns:
            raise KeyError(f"Column '{c}' not found in {csv_path}. Available: {list(monthly.columns)[:15]} ...")
        monthly[c] = pd.to_numeric(monthly[c], errors="coerce")

    out = monthly[cols_needed].dropna()

    # % -> 小数へ
    out = out / 100.0
    return out

def load_ff3_from_ken_french(csv_path_ff3: str) -> pd.DataFrame:
    """
    F-F_Research_Data_Factors.csv など（FF3）から
    月次の Mkt-RF, SMB, HML, RF を取り出して返す。
    """
    df = _load_kenfrench_monthly_table(csv_path_ff3, ["Mkt-RF", "SMB", "HML", "RF"])
    df = df.rename(columns={"Mkt-RF": "mkt_excess", "RF": "rf", "SMB": "smb", "HML": "hml"})
    return df[["mkt_excess", "smb", "hml", "rf"]]

def load_ff5_from_ken_french(csv_path_ff5: str) -> pd.DataFrame:
    """
    F-F_Research_Data_5_Factors_2x3.csv など（FF5）から
    月次の Mkt-RF, SMB, HML, RMW, CMA, RF を取り出して返す。
    """
    df = _load_kenfrench_monthly_table(csv_path_ff5, ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
    df = df.rename(columns={"Mkt-RF": "mkt_excess", "RF": "rf", "SMB": "smb", "HML": "hml", "RMW": "rmw", "CMA": "cma"})
    return df[["mkt_excess", "smb", "hml", "rmw", "cma", "rf"]]

# ============================================================
# (2) 回帰：CAPM / FF3 / FF5（OLS or HAC(Newey-West)）
# ============================================================

def fit_factor_alpha(
    strat_excess: pd.Series,
    factor_df: pd.DataFrame,
    factor_cols: list,
    hac_lags: int = 6,
    use_hac: bool = True,
):
    """
    strat_excess_t = alpha + sum_k beta_k * factor_k,t + eps_t

    factor_df は少なくとも factor_cols を含む DataFrame（index=月末）。
    t値は use_hac=True の場合 Newey-West (HAC) を用いる。
    """
    df = pd.concat([strat_excess.rename("p"), factor_df[factor_cols]], axis=1).dropna()
    X = sm.add_constant(df[factor_cols])
    model = sm.OLS(df["p"], X)

    if use_hac:
        res = model.fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    else:
        res = model.fit()

    alpha = float(res.params["const"])
    t_alpha = float(res.tvalues["const"])
    betas = {c: float(res.params[c]) for c in factor_cols}
    t_betas = {c: float(res.tvalues[c]) for c in factor_cols}
    return alpha, t_alpha, betas, t_betas, res

# ============================================================
# (3) month_type 分解：N vs Non-newsy（R,3）
# ============================================================

def factor_alpha_decomposition_by_monthtype(
    strat_excess: pd.Series,
    factor_df: pd.DataFrame,
    month_type: pd.Series,
    factor_cols: list,
    hac_lags: int = 6,
    use_hac: bool = True,
):
    """
    ALL / N / Non-newsy で同じ因子回帰を行い、alpha を比較する。
    """
    idx = strat_excess.dropna().index
    mt = month_type.reindex(idx)

    def _run(mask, label):
        a, t, betas, tbetas, _ = fit_factor_alpha(
            strat_excess=strat_excess.loc[mask],
            factor_df=factor_df,
            factor_cols=factor_cols,
            hac_lags=hac_lags,
            use_hac=use_hac
        )
        row = {"group": label, "alpha(monthly)": a, "t(alpha)": t}
        # beta も主要だけ載せる（全部載せたいなら factor_cols を回す）
        for c in factor_cols:
            row[f"beta_{c}"] = betas[c]
            row[f"t_{c}"] = tbetas[c]
        return row

    mask_all = idx
    mask_N = idx[mt == "N"]
    mask_NN = idx[mt != "N"]

    rows = []
    rows.append(_run(mask_all, "ALL"))
    rows.append(_run(mask_N, "N(newsy)"))
    rows.append(_run(mask_NN, "Non-newsy(R,3)"))

    # 重み（観測比率）と “加重平均との差” を参考情報として返す
    pi_N = float((mt == "N").mean())
    pi_NN = 1.0 - pi_N
    a_all = rows[0]["alpha(monthly)"]
    a_N = rows[1]["alpha(monthly)"]
    a_NN = rows[2]["alpha(monthly)"]
    approx = pi_N * a_N + pi_NN * a_NN
    cross = a_all - approx

    tab = pd.DataFrame(rows)
    info = {"pi_N": pi_N, "pi_NN": pi_NN, "alpha_weighted_avg": approx, "alpha_all": a_all, "cross_term": cross}
    return tab, info

# ============================================================
# (4) 複数戦略 × 複数モデル（CAPM/FF3/FF5）まとめて表にする
# ============================================================

def evaluate_strategies_factor_models(
    strat_dict: dict,
    ff3: pd.DataFrame,
    ff5: pd.DataFrame | None,
    month_type: pd.Series,
    hac_lags: int = 6,
    use_hac: bool = True,
):
    """
    strat_dict[name] は最低限 'strat_excess' を持つ DataFrame を想定。
    戻り値:
      - summary_table: 戦略×モデルの alpha/t を縦持ちで返す
      - decomp_tables: { (name, model): (table, info) }
    """
    rows = []
    decomp = {}

    # モデル定義
    models = [
        ("CAPM", ff3, ["mkt_excess"]),
        ("FF3",  ff3, ["mkt_excess", "smb", "hml"]),
    ]
    if ff5 is not None:
        models.append(("FF5", ff5, ["mkt_excess", "smb", "hml", "rmw", "cma"]))

    for name, df in strat_dict.items():
        if name == "mkt":
            # 市場自体の alpha は 0 付近で当然なので省略するならここで continue
            pass

        if "strat_excess" not in df.columns:
            continue

        p = df["strat_excess"].copy()

        for model_name, facdf, faccols in models:
            a, t, betas, tbetas, _ = fit_factor_alpha(
                strat_excess=p,
                factor_df=facdf,
                factor_cols=faccols,
                hac_lags=hac_lags,
                use_hac=use_hac,
            )
            row = {"strategy": name, "model": model_name, "alpha_m": a, "t(alpha)": t}
            for c in faccols:
                row[f"beta_{c}"] = betas[c]
                row[f"t_{c}"] = tbetas[c]
            rows.append(row)

            tab, info = factor_alpha_decomposition_by_monthtype(
                strat_excess=p,
                factor_df=facdf,
                month_type=month_type,
                factor_cols=faccols,
                hac_lags=hac_lags,
                use_hac=use_hac,
            )
            decomp[(name, model_name)] = (tab, info)

    summary = pd.DataFrame(rows).sort_values(["model", "t(alpha)"], ascending=[True, False])
    return summary, decomp

# ============================================================
# (5) サブサンプル検証（post-2000 / post-2010 / post-2020 等）
# ============================================================

def evaluate_subperiods(
    strat_dict: dict,
    ff3: pd.DataFrame,
    ff5: pd.DataFrame | None,
    month_type: pd.Series,
    subperiods: list,
    hac_lags: int = 6,
    use_hac: bool = True,
):
    """
    subperiods: list of tuples (label, start_date, end_date_or_None)
    例: [("post2000","2000-01-01",None), ("post2010","2010-01-01",None), ...]
    """
    out = []
    for label, start, end in subperiods:
        for name, df in strat_dict.items():
            if "strat_excess" not in df.columns:
                continue

            p = df["strat_excess"].copy()
            if end is None:
                p = p.loc[start:]
            else:
                p = p.loc[start:end]

            mt = month_type.reindex(p.index)

            # CAPM/FF3/FF5
            model_list = [
                ("CAPM", ff3, ["mkt_excess"]),
                ("FF3",  ff3, ["mkt_excess","smb","hml"]),
            ]
            if ff5 is not None:
                model_list.append(("FF5", ff5, ["mkt_excess","smb","hml","rmw","cma"]))

            for model_name, facdf, faccols in model_list:
                a, t, betas, tbetas, _ = fit_factor_alpha(p, facdf, faccols, hac_lags=hac_lags, use_hac=use_hac)
                out.append({
                    "period": label,
                    "strategy": name,
                    "model": model_name,
                    "alpha_m": a,
                    "t(alpha)": t,
                    **{f"beta_{c}": betas[c] for c in faccols},
                })
    return pd.DataFrame(out).sort_values(["period","model","t(alpha)"], ascending=[True, True, False])
```

* * *

2) 実行例（あなたの既存 `strat_dict` をそのまま使う）
-----------------------------------

あなたがすでに作っている `strat_dict`（`compare_ee_fa_method6_zstar` の戻り値）を使って、以下を実行してください。

```python
# ===== FF3 / FF5 読み込み =====
ff3 = load_ff3_from_ken_french("F-F_Research_Data_Factors.csv")

# FF5 ファイルがある場合のみ（なければ None にして OK）
try:
    ff5 = load_ff5_from_ken_french("F-F_Research_Data_5_Factors_2x3.csv")
except Exception as e:
    print("FF5 file not loaded. Using only CAPM/FF3. Reason:", e)
    ff5 = None

# 既存 strat_dict, ff（mkt_excess, rf）, month_type を使う
month_type = classify_month_type(ff.index)

# ===== 戦略×モデルのα表（HACあり推奨） =====
summary_factors, decomp_factors = evaluate_strategies_factor_models(
    strat_dict=strat_dict,
    ff3=ff3,
    ff5=ff5,
    month_type=month_type,
    hac_lags=6,
    use_hac=True,
)

print("\n=== Factor Alpha Summary (HAC) ===")
print(summary_factors)

# ===== 分解表の例：cFA(EE) の FF3 分解 =====
tab, info = decomp_factors[("cFA(EE)", "FF3")]
print("\n=== Decomposition: cFA(EE) under FF3 (HAC) ===")
print(tab)
print(info)

# ===== サブサンプル検証 =====
subperiods = [
    ("post2000", "2000-01-01", None),
    ("post2010", "2010-01-01", None),
    ("post2020", "2020-01-01", None),
]
subres = evaluate_subperiods(
    strat_dict=strat_dict,
    ff3=ff3,
    ff5=ff5,
    month_type=month_type,
    subperiods=subperiods,
    hac_lags=6,
    use_hac=True,
)
print("\n=== Subperiod Alpha (HAC) ===")
print(subres)
```

* * *

3) この追加分析で「何が分かるか」（解釈の要点）
-------------------------

### (A) CAPM α が FF3/FF5 でも残るか？

*   CAPM は市場因子（MKT）しか除去しません。
*   FF3/FF5 はサイズ（SMB）、バリュー（HML）、収益性（RMW）、投資（CMA）まで除去します。

したがって、もし **cFA(EE) の α が FF5 でも強く残る**なら、

*   「市場・サイズ・バリュー・収益性・投資」で説明できない
*   **決算サイクル（EE）× mispricing 的なリターン源泉**  
    が示唆され、学術的主張が一段強くなります。

逆に FF3/FF5 で α が大きく縮むなら、

*   実は **既知因子へのエクスポージャ**で説明される部分が大きい  
    という整理になります。

### (B) newsy / non-newsy 分解が FF3/FF5 下でも同じ形か？

あなたの結果では、FA(EE) と zstar が **N 月で負 α**でした。  
FF3/FF5 でも同様なら、「決算サイクルの条件付構造」が因子では消えない＝理論整合性が高い。  
もし FF3/FF5 で N 月の負 α が消えるなら、N 月の負は因子（例えば HML/SMB）に由来していた可能性が出ます。

### (C) post-2020 で崩れるか？

あなたが問題意識として持っている “2020年以降の弱化” を、CAPM/FF3/FF5 のどのモデルでも確認できます。

*   post-2020 で α が落ちるなら **裁定（arbitrage）や市場構造変化**の示唆
*   逆に CAPM では落ちるが FF5 では落ちない、などの差が出ると **因子構造の変化**が疑えます。

* * *

必要なら、上の出力（`summary_factors` と `subres` と特定戦略の `decomp`）をそのまま \*\*「newsy / non-newsy 別の α 分解スライド（FF3/FF5版）」\*\*として、見出し＋箇条書き＋結論まで整形した原稿も作れます。

## Response:
以下、いただいた \*\*CAPM/FF3（HAC）結果・cFA(EE)の分解・サブサンプル（post2000/2010/2020）\*\*を、CAPM/FFの意味に立ち返りつつ、論理的に解釈します。結論は、

*   **α は CAPM でも FF3 でも有意に残っている（少なくとも全期間・post2000では強い）**
*   **ただし 2010 以降、とくに 2020 以降は統計的確度が大きく落ちる（t 値が 1〜1.7程度）**
*   **cFA(EE) の “newsy 条件付け” は N 月の負の歪みを弱めるが、FF3 下では α の主戦場は依然 Non-newsy**
*   **FF3 で α が少し縮むのは、SMB/HML へのエクスポージャが一部寄与していた（完全な異常収益ではない）**

です。

* * *

1) Factor Alpha Summary（HAC）：CAPM→FF3で何が起きたか
--------------------------------------------

### 1.1 α は FF3 を入れても「残る」＝市場・サイズ・バリューでは説明しきれない

各戦略の月次 α（HAC t 値）：

*   **cFA(EE)**：CAPM 0.00563 (t=4.31) → FF3 0.00509 (t=4.14)
*   **Method6**：CAPM 0.00495 (t=3.03) → FF3 0.00474 (t=2.90)
*   **FA(EE)**：CAPM 0.00281 (t=2.49) → FF3 0.00256 (t=2.32)
*   **zstar**：CAPM 0.00265 (t=2.34) → FF3 0.00230 (t=2.04)

**解釈：**

*   FF3 を入れると α が **少し減る**が、**t はほぼ維持**（特に cFA/Method6）
*   つまり、あなたの戦略収益の一部は **SMB/HML への露出**で説明できるが、**それだけでは説明できない“残差のα”が強く残る**。

学術的には、これは

*   「単なる size/value ローテーションではない」
*   「EE×ミスプライシング（あるいは状態依存の誤価格）に由来する追加収益がある」  
    という主張をサポートします。

### 1.2 β（mkt）が統計的に有意でない＝市場中立に近い“α戦略”

FF3 下の  $\beta_{mkt}$  の t 値は、各戦略で **\-1.2〜-1.4**程度で有意ではありません。

**解釈：**

*   市場の上げ下げを当てに行く戦略（market timing）というより、
*   **市場に対する純粋なリスク量は小さく、残差リターン（α）で稼いでいる**  
    という読みが強いです。

* * *

2) cFA(EE) の FF3 分解：どの月で α が出ているか
---------------------------------

### 2.1 ALL / N / Non-newsy の α（FF3, HAC）

*   ALL：α = **0.005087** (t=4.14)
*   N：α = **0.003016** (t=1.82)
*   Non-newsy：α = **0.006131** (t=4.07)

**重要な含意：**

*   cFA(EE) は「N 月で符号反転」を入れたので N 月もプラスになっているが、**統計的確度は Non-newsy が圧倒的**。
*   したがって、戦略のコア収益源泉は依然として **R,3（月の“非newsy”）に集中**している。

これは EE の物語（newsy と non-newsy で力学が違う）と整合的で、

*   N は “歪みの反転” を取りにいく局面
*   Non-newsy は “ドリフト／継続” で稼ぐ局面  
    という整理ができます。

### 2.2 SMB/HML 露出の意味（FF3 下で α が少し縮む理由）

cFA(EE) の FF3 係数：

*   ALL：SMB 0.142（t=1.21）、HML 0.206（t=1.89）
*   Non-newsy：SMB 0.256（t=1.65）、HML 0.257（t=2.12）

**解釈：**

*   Non-newsy 局面で **HML（バリュー）露出がやや有意（t≈2.1）**。
*   つまり、Non-newsy で稼いでいる部分の一部は「バリュー要因」と共通する成分が含まれている可能性がある。
*   そのため **CAPM α → FF3 α でわずかに縮小**する。

ただし縮小幅は

*   0.00563 → 0.00509（月次で 0.00054 ≒ 5.4bp）  
    程度で小さく、**中核 α は依然として残る**のがポイントです。

### 2.3 分解の cross\_term がほぼ 0：構造がきれい

cross\_term ≈ -5e-06 と極小。

**解釈：**

*   全体 α が「N と Non-newsy の単純加重平均」でほぼ説明できる
*   つまり **month-type で切っただけでリターン生成構造がほぼ特定できている**  
    → 研究として非常に“書きやすい”結果です（説明力が高い）。

* * *

3) サブサンプル（post2000 / post2010 / post2020）：安定性の読み
------------------------------------------------

ここが実務・学術の両方で最重要です。

### 3.1 post2000：最も強い（有意性が高い）

CAPM（HAC）で

*   Method6 α=0.00691 (t=3.13)
*   cFA α=0.00440 (t=3.05)
*   FA / zstar も α≈0.0033 (t≈2.05)

FF3（HAC）でも同様に有意。

**解釈：**

*   **2000年以降ではこの現象はかなり明確に働いていた**
*   特に Method6 が強いのは「構造推定（β\_t x\_t）が、近年データではうまくハマった」可能性がある。

### 3.2 post2010：弱まる（t が 2 前後、FA/zstar は 1 程度）

CAPM：

*   Method6 t=2.00
*   cFA t=1.84
*   FA/zstar t≈1.02（有意でない）

FF3：

*   Method6 t=2.17
*   cFA t=2.01
*   FA/zstar t≈1.10

**解釈：**

*   2010 以降は「単純 FA（無条件）では取り切れない」
*   一方で cFA と Method6 のように **構造（条件付け or β推定）を入れるとギリギリ残る**。
*   これは「裁定が進み、プレーンなシグナルは弱まったが、条件付けを入れるとまだ残る」という典型的な絵です。

### 3.3 post2020：さらに弱い（t≈1.3〜1.7）

CAPM：

*   Method6 t=1.43
*   cFA t=1.32
*   FA/zstar t≈1.09

FF3：

*   Method6 t=1.72
*   cFA t=1.59
*   FA/zstar t≈1.29〜1.31

**解釈（重要）**

*   点推定の α 自体は依然プラス（例：cFA FF3 0.00566、Method6 FF3 0.00715）だが、
*   **標準誤差が大きくなり、統計的確信が下がっている**。

これは通常、次のどれか（複合）で起きます：

1.  **サンプルが短い（post2020 は観測数が少ない）**
2.  **ボラや自己相関が強くなり HAC の SE が増える**
3.  **構造変化で真の α が小さくなった（裁定・市場構造変化）**
4.  “N/R/3 の定義（カレンダー）”が実際の決算情報到来とズレてきた（会計公表のタイミングが変化、速報化など）

この結果だけだと「消えた」とは断言できず、より正確には  
\*\*“2020以降は統計的に弱く、確証度が落ちた”\*\*です。

* * *

4) ここから導ける、整理された学術的結論
---------------------

1.  **全期間では**
    *   cFA(EE) が最も強い α（CAPM/FF3 両方で t>4）
    *   Method6 が次点（t≈3）
    *   FA(EE)/zstar も有意だが弱い（t≈2）
2.  **FF3 を入れても α は大きくは崩れない**  
    → 「市場・サイズ・バリューでは説明しきれない要素」がある  
    → ただし Non-newsy では HML 露出が一部効いており、αの一部は因子成分と重なる可能性
3.  **時代が新しくなるほど弱化する傾向が強い**
    *   post2000 強い
    *   post2010 中程度
    *   post2020 弱い  
        → “裁定の進行”か “構造変化/タイミングズレ”の疑いが濃い

* * *

5) 次にやるべき「最短の追加診断」（強い順）
-----------------------

FF5 が無い状況でも、説得力を一段上げる診断は次です（必要ならコードもすぐ出します）。

1.  **rolling 10年の FF3 α（ALL/N/Non-newsy）**
    *   α の弱化が「いつから」「どの月タイプで」起きたかが一目で分かる
2.  **N/R/3 を “決算発表カレンダー（本当の earnings announcement）” に寄せた proxy**
    *   例えば FRED / Quandl を使わず無料でできる範囲で、四半期発表集中月を近似
3.  **HML 露出の制御**
    *   Non-newsy の HML が t≈2 なので、HML 中立化（ヘッジ）して α が残るか確認
    *   これで「バリューで説明されるだけ」を排除できる

* * *

6) FF5 ファイルが無い件（実務対応）
---------------------

Ken French の 5因子データはファイル名が環境で異なることが多いです。一般には

*   `F-F_Research_Data_5_Factors_2x3.csv`
*   `F-F_Research_Data_5_Factors_2x3.CSV`
*   zip の中の別名  
    などがあります。

**手元にファイルがあるが名前が違う**ケースが多いので、ディレクトリにある CSV 名一覧を出して、その中から自動検出する関数も作れます（ローカルにあることが前提）。

* * *

必要なら、次の回答で **rolling 10年の FF3 α（ALL/N/Non-newsy）をプロット**するコード（matplotlib、色指定なし、個別図）を追加し、あなたの「2020以降の弱化」を **どの月タイプが原因か**まで落とし込みます。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)