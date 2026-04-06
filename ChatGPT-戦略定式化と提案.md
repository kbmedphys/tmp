# 戦略定式化と提案

**User:** Kentaro Baba (kencharoffx@gmail.com)  
**Created:** 4/6/2026 21:15:41  
**Updated:** 4/6/2026 21:54:04  
**Exported:** 4/6/2026 23:04:57  
**Link:** [https://chatgpt.com/c/69d3a35d-8b34-83a6-b033-613e707e7927](https://chatgpt.com/c/69d3a35d-8b34-83a6-b033-613e707e7927)  

## Response:
2026/4/6 21:15:40

> **ノートブックのセル内容を検査**
>
>
> **Inspecting configuration and functions**
>
>
> **検査対象のセル6の解析**
>
>
> **関数定義の抽出と表示**
>
>
> **引用方法の検討**
>
> ファイルからの引用が必要なので、アップロードされたノートブックを引用できるか確認したいです。しかし、ファイル検索がそれを返さなかったので、インターネットの情報に基づいた引用を使うほうが良いかもしれません。ノートブックを「添付ノートブック（コード確認ベース）」として言及するのが適切かもしれません。
>
> 思考時間: 1m 27s

はい。  
このノートブック戦略は、かなり自然に次の3層へ分解して定式化できます。

1.  **テーマETFの共通因子を抽出する層**
2.  **その因子にモメンタムをかける層**
3.  **因子シグナルをETFウェイトへ戻す層**

この分解で見ると、3本の論文との対応関係がかなり明確です。加えて、**収益源泉を Fama-French 5 factor + Mom でどこまで説明できるか**、さらに**説明できない残差が「テーマ固有プレミアム」なのか、単なるPCA由来のローテーション益なのか**も整理できます。テーマ投資側の論文は「テーマには伝統因子エクスポージャとテーマ固有成分の両方がある」と明示しており、テーマの追加価値はその分解で考えるべきだとしています。

Allocating to Thematic Investme…

また、同論文はテーマのリスクのかなりの部分が伝統因子で説明される一方、テーマごとに無視できない specific risk も残ると述べています。

Allocating to Thematic Investme…

まず、添付ノートブック戦略の実態
----------------

コード確認ベースで、この戦略は概ね以下です。

*   テーマETF日次価格を週次に集約
*   週次リバランス時点ごとに、過去60か月相当の週次リターン窓で **rolling PCA**
*   PCAスコアの当期値を「因子リターン」とみなす
*   その因子リターンに対して **1か月と12か月の複合モメンタム** を計算
*   PC1を除外し、上位3因子をロングする long-only の因子配分を作る
*   その因子ウェイトを
    *   PCA loadings に直接戻す版（S2-L）
    *   ETF→因子回帰betaに戻す版（S2-R）  
        の2方式でETFウェイト化
*   シグナル更新は週次だが、保有ウェイトと損益計算は日次で実行
*   EQW をベンチマークに比較

この設計は、発想としては **“theme ETF universe 内で latent factor を作り、その factor momentum を取りに行く”** です。  
つまり、個別ETFモメンタムというより、**テーマ空間の因子モメンタム戦略**です。

* * *

3本の論文との対応
---------

### 1) _Allocating to Thematic Investments_ との対応

この論文の主張は、テーマ投資の収益・リスクは

$$
r^{\text{theme}}_{t+1} = \beta_t^\top f_{t+1} + \alpha^{\text{theme}}_{t+1} + \varepsilon_{t+1}
$$

のように、  
**伝統因子への曝露** と **テーマ固有成分** に分けて理解すべき、というものです。テーマをポートフォリオに入れるには、まずそのテーマの代表リターン系列を作り、それを伝統的なコア資産やリスク因子に回帰して「何が既知のリスクで、何が新しいのか」を見よ、という立場です。

あなたのノートブックは、これをより戦術的にやっていて、テーマETF群から latent factor を内生的に作っています。  
対応づけると、

*   論文: 「テーマ代表系列を作る」
*   ノート: 「テーマETFパネルから rolling PCA でテーマ代表因子を作る」

です。

したがって、ノートブック戦略の経済的解釈は

$$
r_{i,t+1} = \sum_{k=1}^{K}\ell_{i,k,t} F_{k,t+1} + u_{i,t+1}
$$
*    $r_{i,t+1}$ : ETF  $i$  のリターン
*    $F_{k,t+1}$ : テーマETFユニバースから抽出した latent factor
*    $\ell_{i,k,t}$ : ETF の factor loading
*    $u_{i,t+1}$ : ETF固有成分

です。  
この時点で、**テーマETFの背後にある共通ドライバーを抽出している**という意味で、テーマ論文と整合的です。

* * *

### 2) _Factor Momentum Everywhere_ との対応

この論文の中心は、収益源泉が「個別銘柄モメンタム」だけでなく、**因子そのもののモメンタム**でも説明できる、という点です。特に time-series factor momentum は、各因子の過去リターンに応じて因子エクスポージャを上下させる戦略として定義されます。論文では、1か月、2-12か月、13-60か月など複数の形成期間でも有意な persistence があり、FF5 では十分説明されないと報告しています。

ノートブックはほぼこの構造で、

$$
M_{k,t} = \sum_{L \in \mathcal{L}} \omega_L \cdot \text{Mom}_{k,t}^{(L)}
$$
 
$$
\text{Mom}_{k,t}^{(L)} = \sum_{j=s(L)}^{L} F_{k,t-j}
$$

として、因子  $k$  ごとのモメンタムを測り、  
それをトップ3選抜で

$$
a_{k,t} = \text{Allocate}(M_{k,t})
$$

として因子ウェイトへ変換しています。

つまりノート戦略の中核は

$$
r^{\text{strategy}}_{t+1} = \sum_{k=1}^{K} a_{k,t} F_{k,t+1}
$$

です。  
これはそのまま **TSFM on latent theme factors** です。

特に重要なのは、AQR論文が「数十個の細粒度因子でなくても、少数の broad theme factors でも同じ現象が出る」と述べている点です。

Factor Momentum Everywhere

この意味で、あなたの戦略は論文の拡張ではなく、かなり直接的な応用になっています。

* * *

### 3) _Understanding Momentum and Reversal_ との対応

この論文は、モメンタムを「アノマリー」とみるより、**条件付きベータの時間変動を粗く捉えたフィルター**として理解すべきだと主張します。価格トレンド特性は将来ベータを予測し、より構造的な conditional model を使うと momentum alpha はかなり縮小する、という立場です。

ノートブック戦略は厳密なIPCAではありませんが、考え方としては近いです。  
rolling PCA により、毎期

$$
\ell_{i,t} = \ell(z_{i,t})
$$

のように、ETFの共通因子への感応度が更新されていると解釈できます。  
さらに S2-R は

$$
r_{i,\tau} = \alpha_{i,t} + \beta_{i,t}^\top F_{\tau} + \epsilon_{i,\tau}, \quad \tau \in [t-W+1,t]
$$

で rolling beta を推定し、

$$
w_{i,t} \propto \beta_{i,t}^\top a_t
$$

と ETF 配分へ戻しているので、  
これはかなり明確に **“条件付きベータ経由の expected return”** という読み方ができます。

したがって、この論文との整合的な解釈は、

*   単純なETF価格モメンタムを取っているのではない
*   テーマETF群の内部で変動する共通因子と、その条件付きエクスポージャの時間変動を取っている
*   したがって、収益の源泉は「テーマ固有の期待リターン変動」だけでなく、「条件付きベータの変動を捉えたこと」にある可能性が高い

です。

* * *

以上を踏まえた、戦略の統一定式化
----------------

いちばん自然な書き方は次です。

### Step 1: テーマETFパネル

ETF  $i=1,\dots,N$  の週次リターンを  $r_{i,t}$  とする。

### Step 2: rolling latent factor model

各時点  $t$  で、過去  $W$  期間のリターン行列  $R_t \in \mathbb{R}^{W \times N_t}$  に rolling PCA を当て、

$$
R_t \approx S_t L_t^\top
$$
*    $S_t \in \mathbb{R}^{W \times K}$ : 因子スコア
*    $L_t \in \mathbb{R}^{N_t \times K}$ : 因子ローディング

とする。  
当期因子リターンを

$$
F_t := S_t[W,:]
$$

と置く。

### Step 3: factor momentum signal

各因子  $k$  について

$$
M_{k,t} = \sum_{L \in \mathcal{L}} \omega_L \sum_{j=s(L)}^{L} F_{k,t-j}
$$

ここで  $\mathcal{L}=\{1,12\}$  で、skip を入れるなら  $s(L)=2$  など。

### Step 4: factor allocation

トップ  $m$  因子を選び

$$
a_{k,t} = \begin{cases} 1/m_t & \text{if } k \in \text{Top}_m(M_t),\ M_{k,t}>0\\ 0 & \text{otherwise} \end{cases}
$$

とする。

### Step 5A: loading-based ETF mapping (S2-L)

$$
w^{(L)}_{i,t} = \frac{\max\{0,\sum_{k=1}^K \ell_{i,k,t} a_{k,t}\}}{\sum_j \max\{0,\sum_{k=1}^K \ell_{j,k,t} a_{k,t}\}}
$$

### Step 5B: regression-beta-based ETF mapping (S2-R)

過去  $W_\beta$  期間で

$$
r_{i,\tau} = \alpha_{i,t} + \beta_{i,t}^\top F_{\tau} + \epsilon_{i,\tau}
$$

を推定し、

$$
w^{(R)}_{i,t} = \frac{\max\{0,\beta_{i,t}^\top a_t\}}{\sum_j \max\{0,\beta_{j,t}^\top a_t\}}
$$

とする。

### Step 6: daily implementation

週次リバランス日に決定した  $w_t$  を次回リバランスまで日次で保持し、

$$
r^{p}_{d+1} = w_t^\top r_{d+1} - c \cdot \text{Turnover}_{d+1}
$$

で日次損益を計算する。

* * *

収益源泉の仮説
-------

この戦略の収益源泉は、少なくとも3つに分けて検証すべきです。

### 仮説A: 伝統因子エクスポージャ起因

テーマETFは growth / quality / market / investment / profitability / momentum に偏りやすいので、  
戦略リターン  $r^p_t$  を

$$
r^p_t - r^f_t = \alpha + b_M MKT_t + b_S SMB_t + b_H HML_t + b_R RMW_t + b_C CMA_t + b_U UMD_t + \varepsilon_t
$$

で回帰したとき、alpha が小さければ、収益は主に既知因子の動的ローテーションです。

### 仮説B: 因子モメンタム起因

AQR 論文と整合的に、latent theme factors 自体の persistence により、

$$
\mathbb{E}[F_{k,t+1} \mid M_{k,t}] > 0
$$

が成立している可能性です。  
この場合、収益源泉は「ETF選択」ではなく **theme-factor timing** です。

### 仮説C: 条件付きベータ起因

Understanding Momentum and Reversal と整合的に、モメンタムは将来ベータの proxy であり、

$$
\mu_{i,t} = \beta_{i,t}^\top \lambda_t
$$

の変動を捉えている可能性です。  
この場合、alpha というより **conditional risk premium harvesting** に近いです。

* * *

改良案
---

ここからが重要です。  
現状戦略は面白いですが、論文と照らすと改良余地がかなりあります。

### 改良案1: PCA因子ではなく「説明可能因子」に寄せる

現状の最大の弱点は、PCA因子が**経済的に解釈しにくい**ことです。  
収益源泉特定が目的なら、rolling PCA は便利でも、最終的には説明しにくいです。

より良いのは、

*   PCAは探索用に残す
*   本番戦略は
    *   FF5 + UMD
    *   セクター
    *   金利/VIX/ドル
    *   テーマ代表指数  
        などの**観測可能因子**でベータを推定し、そこに因子モメンタムをかける

ことです。

これは AQR 論文の「factor momentum」と、BNP 論文の「テーマと伝統因子の分解」の両方にきれいに乗ります。

### 改良案2: S2-L より S2-R を主系にする

S2-L は PCA loading に直接ウェイトを戻しているため、  
**cross-sectional covariance structure をそのまま売買信号にしている**面が強いです。  
これは実装上は軽いですが、経済解釈は弱いです。

一方 S2-R は rolling regression beta を介すため、

$$
w_{i,t} \propto \beta_{i,t}^\top a_t
$$

となり、**条件付きベータの時間変動**という解釈が立ちます。  
収益源泉の説明可能性を優先するなら、主戦略は S2-R の方が良いです。

### 改良案3: 因子期待リターンに VAR / state model を入れる

Understanding Momentum and Reversal は、単純な過去リターン平均より、構造的な conditional expected return の方が強いと示しています。VAR による  $\lambda_t$  予測も試しています。

Understanding Momentum and Reve…

したがって因子モメンタムを

$$
M_{k,t} = \sum_j F_{k,t-j}
$$

だけで作るのではなく、

$$
\hat{\lambda}_{t} = \Pi_0 + \Pi_1 F_t
$$

あるいは macro も入れて

$$
\hat{\lambda}_{t} = g(F_t, \text{VIX}_t, \text{rates}_t,\dots)
$$

とする方が論文整合的です。

### 改良案4: PC1除外を明示的な「市場中立化」に置き換える

今は `exclude_pcs=[1]` により PC1 を落としています。  
これは「市場成分を除きたい」という意図だと思いますが、PCAのPC1は毎回意味が少し変わるので不安定です。

より良いのは、

*   FF market に対して beta-neutral
*   EQW theme basket に対して beta-neutral
*   あるいは MKT, QQQ, XLK などに対して residualize

です。  
これは「何を除いて何を取りたいか」が明確になります。

### 改良案5: 収益源泉分析を前提に、残差戦略を分離

最終的にやるべきは、

1.  元戦略
2.  FF5+UMD でヘッジ後の残差戦略
3.  テーマ内 latent factor への寄与のみ
4.  ETF固有残差モメンタム

を分けることです。

特に、

$$
r^p_t = \hat{b}_t^\top X_t + \hat{\alpha}_t + \varepsilon_t
$$

として、  
戦略収益を「既知因子寄与」と「残差寄与」に分解しないと、収益源泉の議論は曖昧なままです。

* * *

Codex実装に向けた、推奨する新しい戦略定義
-----------------------

実装対象としては、次の形が最も筋が良いです。

### 推奨定義

**Conditional Theme Factor Momentum Strategy**

1.  テーマETF週次リターンから rolling latent factors  $F_t$  を推定
2.  ETFごとに rolling beta  $\beta_{i,t}$  を推定
3.  因子期待リターンは単純モメンタムまたは VAR で予測
4.  ETF expected return を
    
$$
\hat{\mu}_{i,t} = \beta_{i,t}^\top \hat{\lambda}_t
$$

で作る  
5\. long-only なら上位ETFへ配分、LSなら cross-sectional demean  
6\. 日次で保有・日次損益計算  
7\. 最後に FF5+UMD, market, sector, EQW-theme に対して attribution

この形なら、

*   AQR論文の factor momentum
*   Kelly/Moskowitz/Pruitt の conditional beta
*   BNP の thematic alpha decomposition

を全部つなげられます。

* * *

実証で必須の検証
--------

Codex実装前に、分析設計として以下は必須です。

### 1\. 因子リターン自体の persistence

$$
F_{k,t+1} = a_k + c_k M_{k,t} + e_{k,t+1}
$$

### 2\. 戦略リターンの因子分解

$$
r^p_t-r^f_t = \alpha + B^\top FF5_t + u \cdot UMD_t + \epsilon_t
$$

### 3\. 時変ベータの寄与

rolling window で  $b_t$  を推定し、  
alpha が安定して残るか確認

### 4\. 残差モメンタムの有無

FF5+UMD で残差化したETFリターンに対し、同じ戦略を再実行

### 5\. S2-L と S2-R の比較

*   どちらが Sharpe で勝つか
*   どちらが説明可能性で勝つか
*   どちらが turnover / crash sensitivity が低いか

* * *

結論
--

このノートブック戦略は、論文対応としては次のように整理できます。

*   **Thematic Investments**:  
    テーマETFの収益を、伝統因子成分とテーマ固有成分に分けて捉える枠組み。ノートの universe 設計と「テーマ共通ドライバー抽出」はこれに対応。
*   **Factor Momentum Everywhere**:  
    ノートの中核そのもの。rolling PCA で作った latent theme factors に time-series factor momentum をかけている。
*   **Understanding Momentum and Reversal**:  
    収益源泉は単純な価格追随ではなく、条件付きベータや条件付き期待収益の変動を捉えている可能性が高い。特に S2-R はこの解釈に近い。

そして、**収益源泉特定が目的なら、現状のままより「S2-R中心 + 予測  $\hat{\lambda}_t$  明示化 + FF5+UMD attribution」へ再定式化した方がよい**です。

次に進めるなら、私はそのまま **Codex実装用の仕様書レベル**で、

*   数式仕様
*   モジュール分割
*   検証項目
*   出力図表
*   FF5+Mom attribution の実装要件

まで落とし込んで書けます。

## Response:
2026/4/6 21:25:53

> **Inspecting notebook for specific keywords**
>
>
> **Inspecting notebook cells directly**
>
>
> **関数定義の検査**
>
>
> 思考時間: 1m 0s

承知しました。  
では、**Codexでそのまま実装に落とせる粒度**で、以下の順で整理します。

1.  **3論文と現行ノートブックの対応関係**
2.  **新たに採用すべき戦略の定式化**
3.  **収益源泉を特定するための分解設計**
4.  **改良案の優先順位**
5.  **Codex実装仕様書のたたき台**

* * *

1\. 3論文と現行ノートブック戦略の対応関係
=======================

1.1 現行ノートブックのコア
---------------

添付ノートブックを確認すると、戦略の骨格は次です。

*   テーマETFの日次価格を読み込む
*   リバランス頻度を週次または月次に設定
*   過去60か月相当の窓で **rolling PCA**
*   抽出された因子の当期スコアを **factor return** とみなす
*   その factor return に対して **1か月 + 12か月（skipあり）** の複合モメンタムを計算
*   上位因子に配分
*   ETFへの写像を
    *   **PCA loading 直写像**
    *   **rolling regression beta 写像**  
        の2通りで実行
*   実際の損益計算は **日次ループ内** で行い、週次リバランス日はその中でだけ更新する

つまり現行戦略は、要するに

$$
\text{Theme ETF panel} \rightarrow \text{latent factors} \rightarrow \text{factor momentum} \rightarrow \text{ETF mapping} \rightarrow \text{daily P\&L}
$$

です。

* * *

1.2 _Allocating to Thematic Investments_ との対応
---------------------------------------------

この論文の重要点は、**テーマ投資の収益は伝統因子エクスポージャとテーマ固有成分に分解して理解すべき**という点です。テーマ系列をまず作り、それを既存リスク因子やコア資産に対して分解することが、戦略設計の出発点だとしています。

Allocating to Thematic Investme…

また、テーマの代表系列は既存テーマ指数でもよいし、複数ファンドのリターンから Lasso 等で合成して作ってもよいとしています。  
さらに、テーマは市場因子などの伝統因子に大きく晒されるため、テーマをそのまま「純粋な新しいリスク源泉」と見なしてはいけないと読めます。

Allocating to Thematic Investme…

現行ノートブックは、これをより機械的に実装していて、**テーマETF群から rolling PCA で代表因子を内生的に作っている**と解釈できます。

* * *

1.3 _Factor Momentum Everywhere_ との対応
-------------------------------------

この論文の中心主張は、**モメンタムは個別資産だけでなく因子にも存在する**、しかも time-series factor momentum はかなり頑健だということです。1か月形成が特に強い一方、2–12か月や13–60か月にも寄与があると示しています。さらに FF5 では大半を説明しきれないと報告しています。

現行ノートブックはまさに

$$
F_{k,t} \text{ に対して } \text{TSFM}
$$

をやっています。  
つまり経済的には **“theme latent factors に対する factor momentum 戦略”** です。

* * *

1.4 _Understanding Momentum and Reversal_ との対応
----------------------------------------------

この論文は、モメンタムを「単純なアノマリー」とみるのではなく、**条件付きベータや条件付き期待収益の時間変動を捉える粗いフィルター**として理解すべきだと主張しています。価格トレンド特性は将来ベータを予測し、条件付きモデルを入れると従来の momentum alpha はかなり縮む、という方向です。

現行ノートブックのうち特に regression-beta 版は、

$$
r_{i,\tau} = \alpha_{i,t} + \beta_{i,t}^{\top}F_{\tau} + \varepsilon_{i,\tau}
$$

を rolling に推定して ETF 配分へ戻しているので、かなりこの論文の考え方に近いです。  
したがって、この戦略の収益源泉は単純な「テーマ価格の追随」ではなく、**条件付きエクスポージャ変動を通じた expected return の抽出**である可能性があります。

* * *

2\. 新たに採用すべき戦略の定式化
==================

ここでは、**論文整合性**と**収益源泉の特定しやすさ**の両方を満たす形に再定式化します。

2.1 投資ユニバース
-----------

時点  $t$  におけるテーマETFの集合を  $i=1,\dots,N_t$  とし、週次リターンを

$$
r_{i,t}
$$

とする。

* * *

2.2 latent theme factor の推定
---------------------------

各意思決定時点  $t$  で、過去  $W_P$  期間の週次リターン行列

$$
R_t \in \mathbb{R}^{W_P \times N_t}
$$

に rolling PCA を適用し、

$$
R_t \approx S_t L_t^\top
$$

とする。

*    $S_t \in \mathbb{R}^{W_P \times K_t}$ : 因子スコア
*    $L_t \in \mathbb{R}^{N_t \times K_t}$ : ETFごとの因子ローディング

当期因子リターンは

$$
F_t = S_t[W_P,:]
$$

と置く。

* * *

2.3 factor momentum signal
--------------------------

各因子  $k$  について、skip を含む複合モメンタムを

$$
M_{k,t} = \sum_{L\in\mathcal{L}} \omega_L \sum_{j=s(L)}^{L} F_{k,t-j}
$$

で定義する。

ここで現行ノートブックに沿えば、

*    $\mathcal{L} = \{1, 12\}$ 
*    $\omega_1=\omega_{12}=0.5$ 
*   monthly意味の skip=1 を週次へ変換

です。

* * *

2.4 factor allocation
---------------------

factor モメンタムが高い因子を選び、

$$
a_{k,t} = \text{Allocate}(M_{k,t})
$$

とする。  
現行戦略に即せば top-m 方式で

$$
a_{k,t} = \begin{cases} 1/m_t & \text{if } k \in \text{Top}_m(M_t),\ M_{k,t}>0 \\ 0 & \text{otherwise} \end{cases}
$$

です。

* * *

2.5 ETF expected return への写像
----------------------------

ここが重要です。  
今後は **loading-based を補助分析、regression-beta-based を本戦略** にするのがよいです。

### A. loading-based

$$
\hat{\mu}^{(L)}_{i,t} = \sum_{k=1}^{K_t} \ell_{i,k,t} a_{k,t}
$$

### B. regression-beta-based

過去  $W_\beta$  期間で

$$
r_{i,\tau} = \alpha_{i,t} + \beta_{i,t}^\top F_\tau + \varepsilon_{i,\tau}
$$

を推定し、

$$
\hat{\mu}^{(R)}_{i,t} = \beta_{i,t}^{\top} a_t
$$

とする。

本戦略は B を採用する。

* * *

2.6 ポートフォリオウェイト
---------------

long-only の場合は

$$
w_{i,t} = \frac{\max(0,\hat{\mu}_{i,t})} {\sum_j \max(0,\hat{\mu}_{j,t})}
$$

cap を入れるならクリップ後に再正規化する。

* * *

2.7 日次実装
--------

週次意思決定時点  $t$  で求めた  $w_t$  を、次の意思決定まで日次で保持し、

$$
r^{p}_{d+1} = w_t^\top r_{d+1} - c \cdot \text{Turnover}_{d+1}
$$

で日次損益を計算する。  
これは今のノートブックの daily stepwise 実装と整合的です。

* * *

3\. 収益源泉を特定するための分解設計
====================

ユーザーの目的はここが本丸です。  
したがって、単に Sharpe を出すのではなく、**戦略収益をどこまで既知因子で説明できるか** を明示的に評価します。

3.1 第1分解: FF5 + Mom による説明
-------------------------

取得可能とのことなので、まずは

$$
r^p_t - r^f_t = \alpha + b_M \, MKT_t + b_S \, SMB_t + b_H \, HML_t + b_R \, RMW_t + b_C \, CMA_t + b_U \, MOM_t + \varepsilon_t
$$

を全期間・サブ期間で推定します。

見るべきものは

*    $\alpha$ 
*    $R^2$ 
*   各  $b$  の安定性
*   rolling alpha

です。

### 解釈

*    $\alpha \approx 0$  なら  
    収益源泉は主として既知因子のダイナミック配分
*    $\alpha > 0$  が安定なら  
    latent theme factor timing に固有の情報がある可能性

* * *

3.2 第2分解: 戦略を「因子寄与」と「残差寄与」に分ける
------------------------------

各ETFについてまず FF5+Mom 回帰を行い、

$$
r_{i,t}-r^f_t = \gamma_i^\top X_t + u_{i,t}
$$

とする。  
ここで  $X_t=(MKT,SMB,HML,RMW,CMA,MOM)$ 。

その上で

### a. raw returns に戦略を実行

$$
\text{StrategyRaw}
$$

### b. residual returns  $u_{i,t}$  に同じ戦略を実行

$$
\text{StrategyResidual}
$$

とする。

### 解釈

*   residual でも強いなら  
    テーマ固有、または latent covariance 構造由来の超過収益がある
*   residual で消えるなら  
    既知因子ローテーションの焼き直しである可能性が高い

この分解は、テーマ論文の「伝統因子 + specific component」という整理に最も素直に対応します。

Allocating to Thematic Investme…

* * *

3.3 第3分解: factor momentum 自体の有効性
--------------------------------

latent factor  $F_{k,t}$  に対して

$$
F_{k,t+1} = c_k + \phi_k M_{k,t} + e_{k,t+1}
$$

あるいは portfolio sort を行い、

$$
\mathbb{E}[F_{k,t+1} \mid M_{k,t} \text{ high}] > \mathbb{E}[F_{k,t+1} \mid M_{k,t} \text{ low}]
$$

を確認します。

これで収益源泉が

*   ETF選択の巧さなのか
*   latent factor の persistence そのものなのか

を切り分けられます。

* * *

3.4 第4分解: conditional beta 仮説
-----------------------------

regression-beta 版について、将来 realized beta の予測力を見ます。

$$
\beta^{\text{realized}}_{i,t+1:t+h} = a + c \, \hat{\beta}_{i,t} + \eta_{i,t+h}
$$

もしここが効いているなら、戦略は単なるモメンタムではなく、**条件付きベータ変動の捕捉**に近いです。  
これは _Understanding Momentum and Reversal_ の主張と整合的です。

* * *

4\. 改良案の優先順位
============

優先度A: regression-beta 版を主戦略にする
------------------------------

最優先です。  
理由は、収益源泉の解釈が最も明快だからです。

loading-based は機械的で便利ですが、

*   PCA軸の意味が回ごとに変わる
*   loading をそのまま expected return proxy にする経済的意味が弱い

という弱点があります。

regression-beta 版なら

$$
\hat{\mu}_{i,t} = \beta_{i,t}^{\top} a_t
$$

と読めるので、説明性が高いです。

* * *

優先度A: FF5+Mom residual 戦略も必ず併走
------------------------------

収益源泉の特定が目的なら、これは必須です。  
元戦略だけでは議論が止まります。

* * *

優先度B: PC1除外を明示的ヘッジへ変更
---------------------

今の `exclude_pcs=[1]` は実務上はよくある処理ですが、経済解釈が曖昧です。  
PC1 は「市場」っぽいことが多いものの、時期により意味がズレます。

代わりに

*   EQW theme basket beta-neutral
*   MKT beta-neutral
*   あるいは QQQ / XLK などテーマに近い市場 proxy に中立化

の方がよいです。

* * *

優先度B: factor expected return 予測に VAR を追加
----------------------------------------

AQR論文は複数の形成期間を重ねる構成を示し、IPCA論文は time-varying  $\lambda_t$  を検討しています。  
したがって

$$
\hat{\lambda}_{t+1} = A_0 + A_1 F_t
$$

や macro を足した

$$
\hat{\lambda}_{t+1} = g(F_t, VIX_t, \text{rates}_t, \dots)
$$

も改良候補です。  
ただし第1段階では、まず単純モメンタム版を固めるべきです。

* * *

優先度C: PCA から observable factor への置換
-----------------------------------

中期的には有力です。  
ただし最初からやると戦略の同一性が崩れるので、Phase 1では latent factor 版を実装し、その後 comparative study として

*   latent factor momentum
*   observable factor momentum

を比較するのがよいです。

* * *

5\. Codex実装仕様書のたたき台
===================

以下をそのまま `SPEC.md` に入れられるレベルで書きます。

* * *

5.1 Objective
-------------

テーマETFユニバースから rolling latent factor を抽出し、factor momentum に基づいて ETF 配分を決定する。  
収益源泉を以下に分解して検証する。

1.  既知の FF5+Mom 因子エクスポージャ
2.  latent theme factor persistence
3.  conditional beta variation
4.  テーマ固有残差成分

* * *

5.2 Strategy Variants
---------------------

実装する戦略は4本。

### V1. Baseline-L

*   rolling PCA
*   factor momentum
*   loading-based ETF mapping

### V2. Baseline-R

*   rolling PCA
*   factor momentum
*   regression-beta-based ETF mapping

### V3. Residual-R

*   ETF returns を FF5+Mom で residualize
*   residual returns 上で V2 を実行

### V4. Beta-neutral-R

*   V2 をベース
*   EQW theme basket または MKT に beta-neutral overlay

* * *

5.3 Inputs
----------

### Price / volume

*   テーマETF日次 Adjusted Close
*   出来高

### Factor data

*   Fama-French 5 factors
*   Momentum factor
*   Risk-free rate

### Optional macro

*   VIX
*   ^IRX
*   CNY=X

* * *

5.4 Core Parameters
-------------------

```
rebalance: W-FRI
execution_lag_days: 1
cost_bps_one_way: 10
pca_window_months: 60
regression_window_months: 60
min_obs_months: 24
n_components: 8
exclude_pcs: [1]   # baseline only
factor_mom_lookbacks_months: [1, 12]
factor_mom_skip_months: 1
combine_weights: {1: 0.5, 12: 0.5}
factor_weighting: top_m
top_m_factors: 3
long_only: true
weight_cap: null
```

* * *

5.5 Walk-forward rules
----------------------

各日次ステップ  $d$  において、

1.   $d$  がリバランス適用日なら、直前の週次意思決定時点  $t$  を参照
2.   $t$  までのデータだけを用いて
    *   rolling PCA
    *   factor momentum
    *   regression beta
    *   portfolio weights  
        を更新
3.  そのウェイトで当日以降の日次リターンを計算

look-ahead は禁止。

* * *

5.6 Performance outputs
-----------------------

最低限、以下を全戦略で出力。

*   CAGR
*   AnnVol
*   Sharpe
*   MaxDD
*   Calmar
*   Skew
*   Kurtosis
*   VaR\_5%
*   CVaR\_5%
*   Turnover
*   Months / Days
*   Hit ratio

* * *

5.7 Attribution outputs
-----------------------

### A. Factor regression

*   full sample FF5+Mom regression
*   expanding / rolling 36m regression
*   alpha, t-stat, R²

### B. Residual test

*   raw strategy vs residual strategy

### C. Factor persistence

*   factor-level predictive regressions
*   decile/quintile sort of future factor returns by momentum signal

### D. Conditional beta test

*   predicted beta vs realized beta
*   cross-sectional slope and R²

* * *

5.8 Required figures
--------------------

*   累積リターン
*   drawdown
*   ETF daily weights
*   factor weights
*   factor momentum heatmap
*   rolling alpha vs FF5+Mom
*   residual strategy vs raw strategy
*   predicted beta vs realized beta scatter
*   factor contribution bar chart

* * *

5.9 Decision criteria
---------------------

戦略の採否は次で判断。

1.  V2 が V1 より説明可能性で優位か
2.  V3 に有意な alpha が残るか
3.  FF5+Mom で説明後も収益が残るか
4.  turnover 控除後でも有効か
5.  beta-neutral 化で crash sensitivity が改善するか

* * *

最後に結論
=====

実装方針としては、まず **Baseline-R を主戦略** にして、その上で **Residual-R と FF5+Mom attribution を必須で併走** するのが最も筋が良いです。

要するに、新しい定式化は

$$
\text{Theme ETF returns} \rightarrow \text{rolling latent factors} \rightarrow \text{factor momentum} \rightarrow \text{ETF conditional betas} \rightarrow \text{portfolio}
$$

であり、収益源泉の検証は

$$
\text{portfolio return} = \text{FF5+Mom explained part} + \text{theme-specific residual part}
$$

という分解で行う、ということです。

次に、これをそのままCodexへ渡せるように **`SPEC.md` 形式の完成版** と **`Execution Prompt.md`** の2本に整えて出します。

## Response:
2026/4/6 21:35:45

> 思考時間: 4s

以下に、**Codexへそのまま渡せる形**で

*   `SPEC.md`
*   `EXECUTION_PROMPT.md`

の2本をまとめます。  
そのままコピペして使えるよう、実装前提・数式・検証項目まで含めています。

* * *

SPEC.md
=======

````
# SPEC.md
# Project: theme-etf-factor-momentum
# Objective:
#   テーマETFユニバースに対して rolling latent factor を抽出し、
#   factor momentum に基づくETF配分戦略を構築する。
#   併せて、収益源泉が
#   (1) FF5+Mom により説明される既知因子エクスポージャなのか、
#   (2) latent theme factor persistence なのか、
#   (3) conditional beta variation なのか、
#   (4) テーマ固有残差なのか
#   を明示的に検証する。

## 1. Research Question

本プロジェクトの主目的は、テーマETFローテーション戦略の収益源泉を特定することである。

現行戦略は、
1. テーマETF群から rolling PCA で latent factor を抽出し、
2. その factor return に factor momentum を適用し、
3. ETFへの写像を通じて portfolio weights を生成し、
4. 日次でP&Lを計算する
構造を持つ。

この構造は、
- テーマ投資の収益を「伝統因子 + テーマ固有成分」に分けて考える枠組み
- factor momentum
- momentum を条件付きベータ変動として理解する枠組み
の3つと整合的である。

本実装では、上記3つの視点を統合しつつ、
「この戦略は何を取っているのか」を再現可能な形で明示する。

---

## 2. Strategy Definition

### 2.1 Universe

- 入力対象はテーマETFの日次 Adjusted Close
- 必要に応じて Volume も取得
- リターン計算は日次ベース
- シグナル生成・リバランス判定は週次ベース
- P&L, NAV, weights の保持は日次ベース

### 2.2 Weekly Aggregation

日次リターン系列から週次リターン系列を作成する。

- rebalance frequency は基本 `W-FRI`
- 月次比較用に `ME` もサポートする
- pandas の `M` は使わず `ME` を使うこと

### 2.3 Rolling Latent Factors

各リバランス時点 t において、過去 `W_pca` 期間の週次ETFリターン行列を

\[
R_t \in \mathbb{R}^{W_{pca} \times N_t}
\]

とする。

この行列に rolling PCA を適用し、

\[
R_t \approx S_t L_t^\top
\]

と表す。

- \(S_t\): factor scores
- \(L_t\): ETF loadings
- \(N_t\): その時点で投資可能なETF数
- launch 前データは missing として扱い、投資不可とする

当期 latent factor return は、score の最新行を用いて

\[
F_t = S_t[W_{pca}, :]
\]

と定義する。

### 2.4 Factor Momentum Signal

因子 k の時点 t における momentum signal を

\[
M_{k,t}
=
\sum_{L \in \mathcal{L}} \omega_L
\sum_{j=s(L)}^{L} F_{k,t-j}
\]

と定義する。

baseline では

- lookbacks = [1, 12]
- weights = [0.5, 0.5]
- skip = 1 month
- ただし実際の系列は週次なので、月→週変換は明示的ルールで行うこと

### 2.5 Factor Allocation

factor momentum signal に基づき、上位因子を選択する。

baseline では top-m allocation:

\[
a_{k,t}
=
\begin{cases}
1/m_t & \text{if } k \in \text{Top}_m(M_t), \; M_{k,t} > 0 \\
0     & \text{otherwise}
\end{cases}
\]

- default `top_m_factors = 3`
- long-only
- 選択対象から除外する PC を指定可能
- baseline では `exclude_pcs=[1]` を許容するが、後述の beta-neutral variant を優先比較対象とする

### 2.6 ETF Mapping

ETF expected return proxy を2通りで定義する。

#### Variant L: Loading-based

\[
\hat{\mu}^{(L)}_{i,t}
=
\sum_{k=1}^{K_t} \ell_{i,k,t} a_{k,t}
\]

#### Variant R: Regression-beta-based

過去 `W_beta` 期間の週次データに対して、

\[
r_{i,\tau}
=
\alpha_{i,t}
+
\beta_{i,t}^\top F_{\tau}
+
\varepsilon_{i,\tau}
\]

を rolling OLS で推定し、

\[
\hat{\mu}^{(R)}_{i,t}
=
\beta_{i,t}^\top a_t
\]

とする。

**主戦略は Variant R とする。**

理由:
- 条件付きベータ変動として解釈しやすい
- 収益源泉分析との整合性が高い
- loading-based より経済的意味づけが明確

### 2.7 Portfolio Weights

long-only の場合

\[
w_{i,t}
=
\frac{\max(0,\hat{\mu}_{i,t})}
{\sum_j \max(0,\hat{\mu}_{j,t})}
\]

- 全銘柄が非正なら cash または EQW fallback を設定可能
- default は cash fallback = 0, つまり当該時点はノーポジでもよい
- optional に weight cap を実装可能

### 2.8 Daily Execution

週次リバランス日に更新された portfolio weights を、次回リバランス日まで日次で保持する。

日次 portfolio return は

\[
r^p_{d+1}
=
w_t^\top r_{d+1}
-
\text{cost}_{d+1}
\]

で定義する。

取引コストは turnover に対して one-way bps を適用する。

\[
\text{cost}_{d+1}
=
c \cdot \sum_i |w_{i,d}^{post} - w_{i,d}^{pre}|
\]

---

## 3. Core Hypotheses

### H1. Theme-factor momentum hypothesis

latent theme factor 自体に persistence が存在し、factor momentum が正の予測力を持つ。  
factor momentum は個別銘柄モメンタムとは別に独立した収益源泉となりうる。:contentReference[oaicite:1]{index=1}

### H2. Conditional beta hypothesis

戦略収益は単純な価格追随ではなく、テーマETFの conditional beta variation を捉えた結果である可能性がある。  
momentum/price trend は将来ベータの予測子となりうる。:contentReference[oaicite:2]{index=2}

### H3. Thematic residual hypothesis

テーマETF収益の一部は FF5+Mom では説明できず、テーマ固有成分として残る可能性がある。  
テーマ投資は伝統因子曝露だけでなく、独自のテーマ成分を含むべきだという考えと整合的である。:contentReference[oaicite:3]{index=3}

---

## 4. Required Strategy Variants

以下の4戦略を必須実装とする。

### V1. Baseline-L
- rolling PCA
- factor momentum
- loading-based ETF mapping

### V2. Baseline-R
- rolling PCA
- factor momentum
- regression-beta-based ETF mapping

### V3. Residual-R
- 各ETFリターンを FF5+Mom で residualize
- residual return に対して V2 と同一ロジックを適用

### V4. BetaNeutral-R
- V2 をベース
- テーマEQWバスケットまたは MKT に対して beta-neutral overlay を適用

---

## 5. Data Requirements

### 5.1 ETF Data
- daily adjusted close
- daily volume (可能なら)
- ticker metadata
- launch date は最初に取得可能な日付を用いる

### 5.2 Risk Factor Data
- Fama-French 5 factors
- Momentum factor
- Risk-free rate

### 5.3 Optional Macro
- VIX
- ^IRX
- CNY=X

---

## 6. Backtest Rules

- シグナル計算はその時点までの情報のみ使用
- execution lag を実装し、look-ahead を禁止
- pre-launch ETF は非投資対象
- weights はリバランス日以外更新しない
- NAV, P&L, turnover は日次で計算
- benchmark は EQW theme ETF basket を必須で用意する

---

## 7. Attribution / Source-of-Return Analysis

### 7.1 FF5 + Mom regression

戦略超過収益について

\[
r^p_t - r^f_t
=
\alpha
+
b_M MKT_t
+
b_S SMB_t
+
b_H HML_t
+
b_R RMW_t
+
b_C CMA_t
+
b_U MOM_t
+
\varepsilon_t
\]

を full sample および rolling で推定する。

出力:
- alpha
- t-stat(alpha)
- R^2
- factor loadings
- rolling alpha
- rolling factor loadings

### 7.2 Residual strategy test

各ETFについて

\[
r_{i,t} - r^f_t = \gamma_i^\top X_t + u_{i,t}
\]

を推定し、残差 \(u_{i,t}\) に対して同じ戦略を実行する。

比較:
- raw strategy
- residual strategy

解釈:
- residual strategy が有効なら theme-specific component が残る
- 有効でなければ既知因子ローテーション色が強い

### 7.3 Factor persistence test

latent factor について

\[
F_{k,t+1} = c_k + \phi_k M_{k,t} + e_{k,t+1}
\]

を推定するか、signal sort により将来リターン差を確認する。

### 7.4 Conditional beta test

regression-beta-based mapping において、
推定された beta が将来 realized beta をどれだけ予測するかを確認する。

---

## 8. Metrics

必須出力指標:

- CAGR
- AnnVol
- Sharpe
- Sortino
- MaxDD
- Calmar
- Skew
- Kurtosis
- VaR_5%
- CVaR_5%
- Hit ratio
- Avg turnover
- Exposure concentration
- Average number of holdings
- Months / Days

---

## 9. Required Figures

### Performance
- cumulative NAV
- drawdown
- rolling Sharpe
- turnover

### Portfolio structure
- daily ETF weights
- factor weights
- top holdings over time

### Attribution
- rolling alpha vs FF5+Mom
- rolling factor loadings
- raw vs residual strategy NAV
- contribution by factor
- predicted vs realized beta scatter

### Factor dynamics
- factor momentum heatmap
- future factor return by signal bucket
- latent factor cumulative returns

---

## 10. File / Module Layout

Recommended minimal structure:

projects/theme-etf-factor-momentum/
├─ README.md
├─ SPEC.md
├─ EXECUTION_PROMPT.md
├─ docs/
│  ├─ sources/
│  └─ notes/
│     ├─ 00_doc_index.md
│     ├─ 10_requirements.md
│     ├─ 20_assumptions.md
│     └─ 30_plan.md
├─ src/theme_etf_factor_momentum/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ data.py
│  ├─ factors.py
│  ├─ pca_model.py
│  ├─ signals.py
│  ├─ mapping.py
│  ├─ portfolio.py
│  ├─ backtest.py
│  ├─ attribution.py
│  ├─ metrics.py
│  └─ reporting.py
├─ notebooks/
│  └─ main.ipynb
├─ data/
│  ├─ raw/
│  └─ processed/
└─ outputs/
   ├─ figures/
   ├─ tables/
   └─ logs/

---

## 11. Default Configuration

```python
REBALANCE = "W-FRI"
EXEC_LAG_DAYS = 1
COST_BPS_ONE_WAY = 10.0

PCA_WINDOW_WEEKS = 60 * 4
BETA_WINDOW_WEEKS = 60 * 4
MIN_OBS_WEEKS = 24 * 4

N_COMPONENTS = 8
EXCLUDE_PCS = [1]

FACTOR_MOM_LOOKBACK_MONTHS = [1, 12]
FACTOR_MOM_SKIP_MONTHS = 1
FACTOR_MOM_WEIGHTS = [0.5, 0.5]

TOP_M_FACTORS = 3
LONG_ONLY = True
WEIGHT_CAP = None

BETA_NEUTRAL_TARGET = "EQW_THEME"   # or "MKT"
````

* * *

12\. Acceptance Criteria
------------------------

以下を満たすこと。

1.  V1, V2, V3, V4 が leakage-free に再現可能
2.  日次P&Lで週次リバランスが正しく実装されている
3.  FF5+Mom attribution が動作する
4.  raw vs residual の比較が可能
5.  outputs に図表・テーブルが保存される
6.  main.ipynb から end-to-end 実行できる

````

---

# EXECUTION_PROMPT.md

```markdown
# EXECUTION_PROMPT.md

あなたは Codex として、このプロジェクトを既存ルールに従い実装すること。

## 0. Workspace / Environment Rules

- workspace 直下の AGENTS.md を最優先で確認すること
- project 直下の AGENTS.md があれば必ず確認すること
- Python 環境は `~/workspace/envs/` 配下の uv 管理環境のみを使うこと
- conda, poetry, pipenv は使わないこと
- pip install を直接実行しないこと
- 必要依存は提案し、`uv add` 前提で整理すること
- 破壊的変更は避けること
- 出力物は `outputs/` 配下に保存すること
- 説明・コメント・要約は日本語で記述すること

---

## 1. Goal

テーマETFユニバースに対して、rolling latent factor + factor momentum 戦略を実装せよ。  
加えて、収益源泉を FF5+Mom / residual / conditional beta の観点から分解できるようにせよ。

本プロジェクトでは、単なるバックテスト再現ではなく、**収益源泉特定** が主目的である。

---

## 2. Implementation Scope

必須実装は以下。

### Strategy variants
- V1: Baseline-L
- V2: Baseline-R
- V3: Residual-R
- V4: BetaNeutral-R

### Required capabilities
- 日次価格から週次シグナル生成
- rolling PCA
- factor momentum calculation
- loading-based mapping
- regression-beta-based mapping
- daily stepwise backtest
- FF5+Mom attribution
- residualized strategy backtest
- reporting / plotting / table export

---

## 3. Economic Interpretation to Preserve

実装にあたり、以下の解釈が崩れないこと。

1. テーマETF群から latent factor を抽出する
2. latent factor 自体の momentum を取る
3. ETF weights は factor exposure 経由で生成する
4. 収益が既知因子なのかテーマ固有なのかを分解する

特に Variant R は

\[
\hat{\mu}_{i,t} = \beta_{i,t}^\top a_t
\]

という expected return proxy を明示的に保持すること。

---

## 4. Data Handling Rules

### ETF returns
- 日次 Adjusted Close から日次リターンを作る
- 週次リターンは日次から集約する
- pre-launch 期間は NaN とし、投資対象外にする
- launch date は利用可能な最初の日とする

### Factor data
- Fama-French 5 factor + Momentum + RF を読み込めるようにする
- 日次または月次の入力差は吸収し、分析に必要な頻度へ整形する

### Alignment
- すべての時系列は look-ahead のない形で index を厳密に整列する
- execution lag を必ず反映する

---

## 5. Code Design Requirements

以下の分離を守ること。

- `data.py`
  - データ取得、整形、頻度変換
- `factors.py`
  - FF5+Mom, RF 読み込みと整形
- `pca_model.py`
  - rolling PCA と latent factor extraction
- `signals.py`
  - factor momentum signal
- `mapping.py`
  - loading-based / regression-beta-based mapping
- `portfolio.py`
  - weights normalization, caps, neutralization
- `backtest.py`
  - daily stepwise backtest
- `attribution.py`
  - factor regressions, residualization, beta tests
- `metrics.py`
  - performance metrics
- `reporting.py`
  - figures / tables / export

過剰抽象化は不要。  
可読性を優先し、main.ipynb から end-to-end 実行できるようにすること。

---

## 6. Core Numerical Rules

### Rolling PCA
- 過去窓のみ使用
- window 長未満なら計算しない
- 有効銘柄数が不足する場合は component 数を縮小可能にする
- PCA 軸の符号反転問題に対処すること
  - 前時点と相関最大になるよう符号を合わせるなど、時系列的一貫性を確保する

### Factor momentum
- lookbacks = [1, 12] months
- combine weights = [0.5, 0.5]
- skip = 1 month
- 週次系列へ変換する際の月→週換算は明示関数化すること

### Regression-beta mapping
- rolling OLS を用いる
- 使用する説明変数は contemporaneous latent factor returns
- t 時点の portfolio decision には t までのデータしか使わない
- insufficient observations なら NaN を返し、そのETFは当期非採用にしてよい

### Daily backtest
- 日次ループ内で、週次リバランス日だけ weights を更新する
- 後から週次 weights を日次へ単純展開するだけの構造にしないこと
- ただし計算結果としては、stepwise daily implementation になっていること

---

## 7. Attribution Requirements

以下は必須。

### 7.1 Full-sample factor regression
戦略超過収益を FF5+Mom に回帰し、
- alpha
- t-stat
- R²
- 各 factor loading
を出力すること。

### 7.2 Rolling regression
36か月または適切な窓で rolling alpha / rolling betas を算出すること。

### 7.3 Residualized ETF returns
各ETFを FF5+Mom で residualize し、その residual series に対して V2 を再実行すること。

### 7.4 Factor persistence
latent factor signal が将来 latent factor return を予測するかを確認すること。

### 7.5 Conditional beta test
regression-beta-based signal の beta が、将来 realized beta をどの程度予測するかを確認すること。

---

## 8. Reporting Requirements

以下を outputs に保存すること。

### Tables
- performance summary
- factor regression summary
- rolling alpha summary
- turnover summary
- holdings concentration summary

### Figures
- cumulative NAV
- drawdown
- ETF weights over time
- factor weights over time
- raw vs residual NAV
- rolling alpha
- rolling factor loadings
- factor momentum heatmap
- predicted vs realized beta scatter

ファイル命名は予測可能な規則に従うこと。

例:
- `outputs/figures/nav_baseline_r.png`
- `outputs/tables/perf_summary.csv`

---

## 9. Notebook Requirement

`notebooks/main.ipynb` を主実行入口とすること。

Notebook には最低限以下の順を持たせること。

1. config 読み込み
2. data load
3. weekly feature construction
4. strategy run (V1-V4)
5. attribution
6. metrics
7. figures / tables export
8. summary display

Notebook 単体で end-to-end 実行可能にすること。

---

## 10. Validation Checklist

実装後、必ず以下を確認すること。

- [ ] leakage がない
- [ ] pre-launch ETF に投資していない
- [ ] weekly signal / daily P&L の整合がある
- [ ] V1-V4 全て動作する
- [ ] FF5+Mom attribution が動作する
- [ ] residual strategy が動作する
- [ ] output files が保存される
- [ ] main.ipynb だけで再現できる

---

## 11. Priority Order

優先順位は以下。

1. V2 Baseline-R
2. FF5+Mom attribution
3. V3 Residual-R
4. V1 Baseline-L
5. V4 BetaNeutral-R
6. 追加の改良比較

まずは説明可能性の高い Variant R を完成させること。

---

## 12. Expected Final Deliverables

最終成果物は以下。

- `src/theme_etf_factor_momentum/*.py`
- `notebooks/main.ipynb`
- `outputs/figures/*`
- `outputs/tables/*`
- `README.md`
- 実装メモおよび assumptions を `docs/notes/` に保存

---

## 13. Important Notes

- 目的は Sharpe 最大化だけではない
- 収益源泉の説明可能性を最優先する
- loading-based variant は補助比較であり、主戦略は regression-beta-based
- PC1 除外は baseline として残してよいが、beta-neutral 比較も必ず実装する
- 実装は最小構成・可読性重視で行うこと
````

* * *

必要なら次に、これをさらに実務向けにして

*   `README.md`
*   `docs/notes/10_requirements.md`
*   `docs/notes/20_assumptions.md`
*   `docs/notes/30_plan.md`

まで一式で整えます。

## Response:
2026/4/6 21:41:47

> **考えながらデータの作成方法を検討中**
>
> ユーザーは「一式揃えてください」と言っているので、恐らくファイルをセットとして提供するべきです。単純にインラインで提供するのは不十分かもしれません。Markdownファイルを作成し、ZIP形式で提供するのが良さそうです。必要に応じて、引用を追加して、正確性を記録します。
>
> **ファイル作成方針の検討中**
>
> ユーザーがファイルをリクエストしているので、これらのファイルにはリンクを含めた説明を追加します。引用については、外部ソースを使ったことを示す場合に必要かもしれませんが、独自に作成したファイルには不要です。最終回答では、ファイルの内容を簡単に説明します。
>
> **ディレクトリとファイルのセット作成**
>
>
> **コンテンツファイルの作成**
>
> コンテンツファイルを作成する必要がありそうです。どの形式で提供すれば最適かを考えているところです。ユーザーのニーズに合わせて、適切なファイル形式や内容を整えることが重要ですね。
>
> **生成するコンテンツファイル**
>
>
> 思考時間: 7m 0s

一式を揃えました。

ダウンロードはこちらです。  
theme-etf-factor-momentum\_bundle.zip

個別ファイルもあります。  
README.md  
SPEC.md  
EXECUTION\_PROMPT.md  
00\_doc\_index.md  
10\_requirements.md  
20\_assumptions.md  
30\_plan.md

必要なら次に、これに合わせて `src/` の各 Python ファイルの雛形まで埋めます。

## Response:
2026/4/6 21:51:48

> **確認と編集作業**
>
> ユーザーの依頼に基づいて、AGENTSのreadmeに関連する内容を含むファイルを更新する必要があります。現在のデータの修正が必要で、ファイルの内容を確認して変更を加えます。特にCanmoreは必要なさそうなので、テキストファイルを編集していきます。
>
> **ファイル内容を表示および確認**
>
>
> **ドキュメント更新と調整**
>
> 複数のドキュメントを更新する必要があります。AGENTS関連の内容を既存のファイルに追加し、指定された内容をREADME SPEC EXECとノートに反映させます。また、AGENTS.mdファイルを作成し、必要な内容を追加します。「このファイルは workspace/AGENTS.md に次ぐ優先度で適用される」と明記する必要があります。
>
> **Updating documentation and creating AGENTS.md file**
>
>
> 思考時間: 1m 53s

反映しました。  
指定内容を追加し、**project用 `AGENTS.md` を新規作成**したうえで、`README.md` / `SPEC.md` / `EXECUTION_PROMPT.md` / notes も更新しています。

更新版はこちらです。  
theme-etf-factor-momentum\_bundle\_v2.zip

個別ファイル:  
AGENTS.md  
README.md  
SPEC.md  
EXECUTION\_PROMPT.md

今回の反映内容は次の通りです。

*   `workspace/AGENTS.md` を最初に必ず読むこと
*   この project の `AGENTS.md` は `workspace/AGENTS.md` に次ぐ優先度で適用されること
*   Prefer explicit python path を `envs/base/.venv/bin/python` に固定
*   実装は **`notebooks/main.ipynb` の1ファイル完結** に変更
*   `src/` への分散実装前提を外し、notebook中心の構成へ修正

必要なら次に、**この新ルールに合わせた `main.ipynb` のセル構成案** まで作ります。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)