# 論文解説手法再現

**User:** Anonymous  
**Created:** 7/22/2026 19:52:56  
**Updated:** 7/23/2026 0:02:36  
**Exported:** 7/23/2026 7:42:55  
**Link:** [https://chatgpt.com/c/6a60a0cd-2b8c-83ee-b004-c50dd959bc9d](https://chatgpt.com/c/6a60a0cd-2b8c-83ee-b004-c50dd959bc9d)  

## Prompt:
2026/7/22 19:52:54

各ドキュメントについて内容をそれぞれ再現できる粒度で解説して。特に手法については定式化を含むこと

[Attachment: Narrative Momentum.pdf]

[Attachment: Thematic Investing A Risk-based Perspective(3).pdf]

[Attachment: Thematic Investing as Missing Factors.pdf]

[Attachment: Allocating to Thematic Investments(3).pdf]

[Attachment: Episodic Factor Pricing.pdf]

## Response:
2026/7/22 19:52:56

> **パーソナライズ中**
>
>
> **パーソナライズし、調査テーマ、目標、投資理論を確認した**
>
> 
>
> 8m 45s考えました

# 全体像

5本の論文は、同じ「テーマ／ファクター投資」を扱っていますが、解いている問題は異なります。

| 論文 | 主な問い | テーマ・ファクターの表現 | 中心手法 | 運用上の役割 |
|---|---|---|---|---|
| **Narrative Momentum** | 注目が高まるナラティブは将来リターンを予測するか | ニュース強度と株価感応度 | Narrative beta、mimicking portfolio、attention momentum | **アルファ・シグナル生成** |
| **Thematic Investing: A Risk-based Perspective** | テーマ・バスケットは既存リスクモデル外の共通変動を持つか | Barra残差間の一時的相関 | 平均ペアワイズ残差相関、Mosaic＋bootstrap | **テーマの真正性・coherence診断** |
| **Thematic Investing as Missing Factors** | テーマを既存リスクモデルにどう追加するか | 銘柄別テーマスコア | クロスセクション純化、FWL、拡張共分散 | **純化テーマ構築・リスク管理** |
| **Allocating to Thematic Investments** | テーマ資産を伝統資産とどう配分するか | テーマ指数・ファンド収益率 | 市場・地域・スタイル・業種分解、LASSO、robust optimization | **戦略的資産配分** |
| **Episodic Factor Pricing** | ファクターは常時有効か、それとも時々だけ有効か | 企業特性の横断面予測力 | SED、LASSOによるpricing-on/off判定 | **ファクター・タイミング** |

以下では、各論文を独立に再現できるよう、データ、推定式、ポートフォリオ構築、検証方法、再現上の不足点まで整理します。

---

# 1. Narrative Momentum

## 1.1 研究仮説

この論文の中心仮説は、

> 投資家は、あるナラティブへのメディア注目が長期的に高まっていることを株価へ十分速く織り込まない

というものです。

347のナラティブについてメディア強度を作り、各ナラティブに対する株価感応度を推定し、その感応度を使ってナラティブ模倣ポートフォリオを構築します。そのうえで、最近注目が高まったナラティブをロング、注目が低下したナラティブをショートします。ベースラインの6か月形成・6か月保有戦略は年率8.42%、FF6アルファ7.30%と報告されています。`Narrative Momentum.pdf`

---

## 1.2 データ

### メディアデータ

- 期間：2012-2023年
- ニュース件数：約1,327万件
- 情報源：約2.3万のデジタル媒体
- ナラティブ数：347
- タクソノミー源：
  - Reuters
  - IPTC
  - Bloombergマクロニュースタグ
  - アナリストとの対話を通じたテーマ候補
- 一部の頑健性検証ではJEL分類と交差する53のevergreen narrativesを使用

株価・企業データはCRSP、Compustat、アナリスト予想はI/B/E/S、リスクファクターはFama-FrenchおよびHou-Xue-Zhang、産業分類はGICSを使用しています。`Narrative Momentum.pdf`

---

## 1.3 ナラティブ強度

ナラティブ $n$ の日次ネガティブ強度を

$$
I_{n,d}^{-}
=
\frac{N_{n,d}^{-}}{N_d}
$$

とします。

- $N_{n,d}^{-}$：日 $d$ においてナラティブ $n$ に関連し、ネガティブと分類された記事数
- $N_d$：同日の全ニュース・ディスカッション量

ポジティブ強度 $I_{n,d}^{+}$ も同様です。値域は $[0,1]$ です。月次強度は日次強度の月内平均です。`Narrative Momentum.pdf`

ベースラインではネガティブ強度を使います。これは「ネガティブなナラティブほど情報量が多く測定精度が高い」という実務的理由によるものであり、ポジティブ強度や正負合計強度でも頑健性検証を行っています。

---

## 1.4 株式のNarrative beta

### 週次データの整合

株価リターンとニュース強度の情報期間を次のように揃えます。

- 株価リターン：前週水曜日終値から当週水曜日終値
- ニュース強度：前週木曜日から当週水曜日までの日次強度平均

週次強度は

$$
I_{n,w}
=
\frac{1}{D_w}
\sum_{d\in\{\text{Thu}_{w-1},\ldots,\text{Wed}_{w}\}}
I_{n,d}^{-}
$$

週次変化は

$$
\Delta I_{n,w}=I_{n,w}-I_{n,w-1}
$$

です。

### 回帰式

銘柄 $i$、ナラティブ $n$ について、週次ローリング回帰を行います。

$$
r_{i,w}^{e}
=
\alpha_i
+
\beta_{m,i}r_{m,w}^{e}
+
\beta_{n,i}\Delta I_{n,w}
+
\varepsilon_{i,w}.
\tag{1}
$$

ここで、

- $r_{i,w}^{e}$：銘柄 $i$ の超過リターン
- $r_{m,w}^{e}$：市場超過リターン
- $\beta_{n,i}$：銘柄 $i$ のナラティブ $n$ に対する感応度

です。

推定条件は、

- 直近52週を使用
- 最低26週の有効観測
- 月末と推定期間の間に最低1日の間隔を置く

です。`Narrative Momentum.pdf`

### betaの経済的意味

強度が「ネガティブ記事の比率」であるため、

- $\beta_{n,i}>0$：そのナラティブについてネガティブ報道が増えると相対的に上昇する銘柄
- $\beta_{n,i}<0$：ネガティブ報道が増えると相対的に下落する銘柄

です。

これは単なる「ニュースで企業名が何回言及されたか」ではなく、市場がナラティブを当該企業にとってプラス／マイナスのどちらと解釈しているかを含みます。

---

## 1.5 Narrative-mimicking portfolio

月 $t$ の初めに、月 $t-1$ の最終週までの情報で推定された $\hat\beta_{n,i,t-1}$ により銘柄を順位付けします。

ナラティブ $n$ について、

- 上位25銘柄をロング
- 下位25銘柄をショート
- ユニバースは時価総額上位3,000銘柄
- 株価1ドル超
- 毎月リバランス

とします。`Narrative Momentum.pdf`

ベースラインは各レッグを時価総額加重します。上位集合を $H_{n,t}$、下位集合を $L_{n,t}$ とすると、

$$
w_{i,n,t}^{+}
=
\frac{MC_{i,t-1}}
{\sum_{j\in H_{n,t}}MC_{j,t-1}},
\qquad i\in H_{n,t},
$$

$$
w_{i,n,t}^{-}
=
-
\frac{MC_{i,t-1}}
{\sum_{j\in L_{n,t}}MC_{j,t-1}},
\qquad i\in L_{n,t}.
$$

したがってナラティブ模倣リターンは

$$
R_{n,t}^{NM}
=
\sum_i w_{i,n,t}r_{i,t}.
$$

各模倣ポートフォリオはネット0、グロス2です。

---

## 1.6 Narrative momentum signal

ナラティブ強度の単なる前月差ではなく、直近 $J$ か月平均と、その直前 $J$ か月平均の差を使います。

$$
S_{n,t}^{(J)}
=
\frac{1}{J}
\sum_{\ell=1}^{J} I_{n,t-\ell}
-
\frac{1}{J}
\sum_{\ell=J+1}^{2J} I_{n,t-\ell}.
\tag{2}
$$

例えば $J=6$ なら、

$$
S_{n,t}^{(6)}
=
\overline I_{n,t-6:t-1}
-
\overline I_{n,t-12:t-7}.
$$

月 $t-1$ の最終日は計算から除外し、月末近辺の情報リークを避けています。形成期間は

$$
J\in\{1,3,6,9,12\}
$$

です。`Narrative Momentum.pdf`

各月、

- $S_{n,t}^{(J)}$ 上位10ナラティブ：rising
- 下位10ナラティブ：declining
- 残り：middle

と分類します。

---

## 1.7 メタ・ナラティブ戦略

rising側とdeclining側の平均模倣リターンを

$$
R_{t}^{rise}
=
\frac{1}{10}
\sum_{n\in\mathcal T_t} R_{n,t}^{NM},
$$

$$
R_{t}^{decline}
=
\frac{1}{10}
\sum_{n\in\mathcal B_t} R_{n,t}^{NM}
$$

とします。

最終スプレッドは

$$
R_t^{spread}
=
\frac{1}{2}
\left(
R_t^{rise}-R_t^{decline}
\right).
\tag{3}
$$

各 $R_{n,t}^{NM}$ 自体がグロス2のL/Sであるため、rising portfolioをロングしdeclining portfolioをショートすると形式上グロス4になります。したがって $1/2$ を掛け、最終ポートフォリオをグロス2へ正規化します。`Narrative Momentum.pdf`

---

## 1.8 複数月保有のladdered portfolio

保有期間は

$$
K\in\{1,3,6,9\}
$$

です。

$K>1$ の場合は、各月に新しいコホートを開始し、直近 $K$ 個のコホートを等ウェイトで保有します。

月 $q$ に形成したコホートの月 $t$ のリターンを $R_{q,t}^{spread}$ とすると、

$$
R_t^{ladder}
=
\frac{1}{K}
\sum_{h=0}^{K-1}
R_{t-h,t}^{spread}.
\tag{4}
$$

重要なのは、

- 選択されたナラティブ集合は各コホートの $K$ か月間固定
- 各ナラティブの模倣ポートフォリオは、最新betaにより毎月組み替える

ことです。すなわち、「Recession」というファクターを6か月保有する一方、そのファクターを複製する個別銘柄ウェイトは毎月更新します。`Narrative Momentum.pdf`

---

## 1.9 ベースライン結果

$J=6,K=6$ では、

- rising leg：年率13.30%
- declining leg：年率-3.54%
- spread：年率8.42%、$t=2.79$
- FF6 alpha：年率7.30%、$t=2.42$

です。リターンは主としてrising側から生じますが、イベント時系列分析では両レッグが寄与しています。`Narrative Momentum.pdf`

---

## 1.10 価格モメンタムとの識別

ナラティブ注目度モメンタムが、模倣ポートフォリオ自体の価格モメンタムではないことを確認するため、二段階ソートを行います。

1. ナラティブ模倣ポートフォリオを過去 $M$ か月リターンで
   - 上位30%
   - 中央40%
   - 下位30%
   に分ける。
2. 各価格モメンタム群の中で、強度変化によりrising／decliningを選ぶ。
3. 各価格モメンタム群のrising-minus-decliningを平均する。

$M=J=K=6$ のprice-momentum-controlled spreadは年率4.20%、FF6 alpha 4.04%です。したがってリターンは低下するものの消滅しません。

これは回帰による厳密なゼロbeta化ではなく、「価格モメンタム・ビン内で注目度を比較する条件付き二重ソート」です。

---

## 1.11 Factor momentumとの識別

Hou-Xue-Zhangの122ファクターについて、

- 過去1か月リターン
- 過去12か月リターン

のそれぞれで十分位ソートし、上位十分位ロング・下位十分位ショートのfactor momentumを構築します。

FF6にこれら2つのfactor momentumを加えた回帰でも、narrative spreadのアルファが残るため、既存ファクターのモメンタムによる説明ではないとしています。

---

## 1.12 投資家の過小反応の検証

### アナリスト予想誤差

形成月 $t$、将来時点 $k$、銘柄 $i$ について、

$$
FE_{i,t,k}
=
\frac{
ActualEPS_{i,t-1+k+\tau}
-
ForecastEPS_{i,t-1}
}{
Price_{i,t-1}
}.
\tag{5}
$$

- $ForecastEPS_{i,t-1}$：形成時点のアナリスト予想中央値
- $ActualEPS$：該当会計年度について将来最初に公表される実績EPS
- $\tau\in\{0,\ldots,11\}$
- 全期間で1%・99% winsorize
- 銘柄からナラティブポートフォリオへ時価加重
- ナラティブ間は等ウェイト

rising narrativesに敏感な株式では予想誤差が正となり、おおむね9か月継続します。これはアナリストが将来利益を過小予想していたことを意味します。

### Frog-in-the-pan smoothness

週次強度変化の連続性を

$$
Smooth_{n,t}
=
\frac{
\left|\operatorname{mean}(\Delta I_{n,w})\right|
}{
\operatorname{sd}(\Delta I_{n,w})
}
\tag{6}
$$

で測ります。

$J=1,3,6,9,12$ に対応して、9、26、52、78、104週の履歴を使用します。値が高いほど、強度が大きなジャンプではなく小さな変化を連続的に積み上げています。

連続的に注目が高まるナラティブほどmomentumが強く、情報が小刻みに到来すると投資家が見落としやすいという説明と整合します。

### Quarter-life

ナラティブ強度にAR(12)を推定します。

$$
I_{n,t}
=
c_n+\sum_{\ell=1}^{12}\phi_{n,\ell}I_{n,t-\ell}
+\epsilon_{n,t}.
\tag{7}
$$

単位ショックに対するインパルス応答が0.25未満になるまでの月数をquarter-lifeとします。

$$
QL_n
=
\min
\left\{
h:
IRF_n(h)<0.25
\right\}.
$$

quarter-lifeが中央値以上のナラティブの方が、attention momentumは強いと報告されています。

---

## 1.13 業種・タグ分解

### 業種分解

銘柄リターンを

$$
r_{i,t}
=
r_{g(i),t}^{industry}
+
r_{i,t}^{within}
\tag{8}
$$

に分解します。

- $r_{g(i),t}^{industry}$：銘柄 $i$ が属する業種の時価加重リターン
- $r_{i,t}^{within}=r_{i,t}-r_{g(i),t}^{industry}$

12、30、49業種分類のいずれでも、narrative momentumの大部分は業種間配分ではなく、同一業種内の銘柄選択から生じます。

### タグ分解

347ナラティブを14グループに分け、

$$
R_{n,t}
=
\overline R_{tag(n),t}
+
\left(R_{n,t}-\overline R_{tag(n),t}\right)
$$

と分解します。

J=6、K=6では、spread returnのうち

- tag内超過成分：年率6.03%
- tag平均成分：年率2.38%

であり、より細かなナラティブ固有効果が中心です。`Narrative Momentum.pdf`

---

## 1.14 株式レベルFama-MacBeth検証

銘柄 $i$ のrising exposureを概念的に

$$
E_{i,t}^{rise}
=
\sum_{n\in\mathcal T_t}
\hat\beta_{n,i,t}
S_{n,t}^{(6)}
\tag{9}
$$

とし、declining側も同様に構築します。

これらの6か月平均と、

- log book-to-market
- log market cap
- 過去1か月リターン
- 過去12か月リターン
- investment
- profitability

を説明変数として、毎月横断面回帰を行います。

$$
r_{i,t+1}
=
a_t
+
\gamma_{rise,t}E_{i,t}^{rise}
+
\gamma_{decl,t}E_{i,t}^{decl}
+
\delta_t'Z_{i,t}
+
u_{i,t+1}.
\tag{10}
$$

月次係数を時系列平均し、Fama-MacBeth $t$ 統計量を算出します。OLSと時価総額WLSの両方で、rising exposureが将来収益率を正に予測します。

---

## 1.15 再現手順

```text
1. 日次記事を narrative × sentiment に分類する
2. 日次・週次・月次 narrative intensity を作る
3. 水曜-水曜の株式超過リターンを作る
4. 各月末、各 narrative × stock について52週ローリング回帰
5. beta上位25・下位25でVW narrative-mimicking portfolioを作る
6. 月次 narrative intensity trend S(J)を計算
7. top 10 / bottom 10 narrativesを選択
8. rising-minus-declining spreadを構築し、1/2でgross調整
9. K本の重複コホートを平均
10. FF6 alpha、Newey-West t、価格モメンタム二重ソート等を評価
```

### 完全再現上の最大の障害

アルゴリズムは比較的明確ですが、MKT MediaStatsの

- point-in-time記事アーカイブ
- 347ナラティブの辞書・分類器
- sentiment分類
- media reservoir

が非公開です。したがって、公開ニュースから近似版は作れても、論文数値の完全一致は困難です。

---

# 2. Thematic Investing: A Risk-based Perspective

## 2.1 研究仮説

この論文はテーマを、

> 既存リスクモデルで説明した後にも、構成銘柄の残差リターン間に一時的かつ有意な共通相関を生じさせる要因

と定義します。

すなわち、「テーマ名が付いているか」ではなく、「既存業種・スタイル因子で説明できない共通変動があるか」でテーマのcoherenceを判定します。統計的に有意な平均残差相関を持つバスケットは、既存モデルがリスクを過小評価し、かつ残差リターンにトレンドが現れると報告されています。`Thematic Investing A Risk-based Perspective(3).pdf`

---

## 2.2 基本リスクモデル

日 $t$ の銘柄リターンを

$$
\mathbf r_t
=
\mathbf X_t\mathbf b_t+\mathbf u_t
\tag{11}
$$

とします。

- $\mathbf X_t$：業種・スタイル等の因子エクスポージャ
- $\mathbf b_t$：当日の横断面ファクターリターン
- $\mathbf u_t$：残差リターン

標準的な資産共分散は

$$
\mathbf V_t
=
\mathbf X_t\mathbf F_t\mathbf X_t'
+
\boldsymbol\Delta_t
\tag{12}
$$

です。

$\boldsymbol\Delta_t$ が対角行列であることは、

$$
\operatorname{Cov}(u_{i,t},u_{j,t})=0,
\qquad i\neq j
$$

を仮定しています。

---

## 2.3 テーマを追加した真のモデル

テーマが存在する期間には、

$$
\mathbf r_t
=
\mathbf X_t\mathbf b_t
+
\mathbf Y_t\mathbf g_t
+
\mathbf u_t'
\tag{13}
$$

と考えます。

- $\mathbf Y_t$：テーマエクスポージャ
- $\mathbf g_t$：テーマリターン
- $\mathbf u_t'$：テーマを除去した真の固有リターン

既存モデルが $\mathbf Y_t\mathbf g_t$ を持たない場合、これが $\mathbf u_t$ に混入します。その結果、同じテーマに属する銘柄間で、

$$
\operatorname{Cov}(u_i,u_j)>0
$$

が観測されます。

論文は、

- factor：広範かつ持続的
- theme：狭く一時的

と区別します。同じテーマが長期間・広範に横断面を説明し続けるなら、それはもはやthemeではなくfactorと呼ぶべきだという整理です。

---

## 2.4 平均ペアワイズ残差相関

テーマバスケット内に $N$ 銘柄があるとします。観測期間の残差相関行列を $\boldsymbol\rho$ とすると、平均ペアワイズ相関は

$$
\overline\rho
=
\frac{2}{N(N-1)}
\sum_{1\le i<j\le N}
\rho_{ij}.
\tag{14}
$$

論文ではAPCまたはaverage pairwise correlationと呼びます。`Thematic Investing A Risk-based Perspective(3).pdf`

単純に $\overline\rho>0$ であるだけでは不十分です。横断面回帰から推定された残差には、

- 残差平均がゼロになる制約
- 回帰による残差分散の下方バイアス
- 時変エクスポージャ
- 時変固有ボラティリティ
- 残差と因子エクスポージャの直交制約

があるため、通常の相関検定をそのまま使えません。

---

## 2.5 単純bootstrapの考え方

残差行列を

$$
\mathbf H
=
\begin{bmatrix}
u_{1,1}&\cdots&u_{1,N}\\
\vdots&&\vdots\\
u_{T,1}&\cdots&u_{T,N}
\end{bmatrix}
\in\mathbb R^{T\times N}
\tag{15}
$$

とします。

### ステップ1：銘柄ごとの時系列を独立にシャッフル

各列を独立に置換して

$$
\mathbf H^*
$$

を作ります。

これにより、

- 各銘柄残差の周辺分布
- 平均
- 分散
- 歪度
- 尖度

は概ね保存されますが、銘柄間の同時点相関は破壊されます。

### ステップ2：疑似トータルリターンを復元

元の因子リターンを使って

$$
\mathbf r_t^*
=
\mathbf X_t\hat{\mathbf b}_t
+
\mathbf u_t^*
\tag{16}
$$

を作ります。

### ステップ3：再度横断面回帰

$$
\mathbf r_t^*
=
\mathbf X_t\hat{\mathbf b}_t^*
+
\mathbf u_t^{**}.
\tag{17}
$$

この再推定により、疑似残差 $\mathbf u_t^{**}$ は再び $\mathbf X_t$ に直交します。

### ステップ4：帰無分布

各bootstrap反復 $b=1,\ldots,B$ で

$$
\overline\rho_b^*
$$

を計算し、

$$
z
=
\frac{
\overline\rho_{\mathrm{obs}}
-
\operatorname{mean}_b(\overline\rho_b^*)
}{
\operatorname{sd}_b(\overline\rho_b^*)
}
\tag{18}
$$

を求めます。

---

## 2.6 なぜ単純bootstrapでは不十分か

単純シャッフルは、

- 回帰残差の分散が推定上縮小している問題
- 回帰によって残差間に入る人工的構造
- 残差の自己相関
- 時間とともに変化する分布

を十分に処理しません。

単純法は $z$ 値を過大評価しやすいため、論文はMosaic＋bootstrapを使います。`Thematic Investing A Risk-based Perspective(3).pdf`

---

## 2.7 Mosaic＋bootstrap

論文記載のデフォルト構成は次の通りです。

1. 時系列を連続する10日間の非重複ブロックに分割する。
2. 各10日ブロックについて、銘柄をランダムに $K$ 個のグループへ分ける。
3. 各グループの銘柄数が、使用因子数の最低5倍となる最大の $K$ を使う。
4. 銘柄グループ×時間ブロックの各tile内で、別々に回帰・残差化する。
5. 残差を時間ブロック単位で置換する。
6. APCを再計算して帰無分布を作る。

時間ブロックをまとめて置換することで残差の短期自己相関を保存し、銘柄ブロックごとに別回帰を行うことで、異なるブロック間に回帰由来の人工相関が生じないようにします。`Thematic Investing A Risk-based Perspective(3).pdf`

実際にはSpector et al.のMosaic permutation理論に依存しているため、厳密な再現には同論文または実装コードも必要です。

---

## 2.8 実証設定

- 米国大型・流動性株：約1,100銘柄
- 期間：1999-2024年
- 日次超過リターン
- Barra GEM3
  - 34業種因子
  - 11スタイル因子
- 横断面OLS
- 市場全体のAPC：30日ローリング
- 頑健性：BlackRock独自BFREモデル

GEM3とBFREによるテーマバスケットのpre-release／post-release $z$ 値の相関は84%／86%で、リスクモデルを変えても結論は大きく変わりません。`Thematic Investing A Risk-based Perspective(3).pdf`

---

## 2.9 テーマバスケットの検証

Goldman Sachsの145のマクロテーマバスケットについて、リリース日前後60暦日の残差相関を評価します。

$z\ge2$ を有意とすると、

- リリース前60日：61/145、42%
- リリース後60日：60/145、41%
- pre/post $z$ の相関：49%

です。`Thematic Investing A Risk-based Perspective(3).pdf`

したがって、

1. 多くのブローカー・テーマは実際に既存因子外の共通変動を持つ。
2. そのcoherenceは公表前だけでなく、公表後も少なくとも60日程度持続する。

と解釈しています。

---

## 2.10 テーマ相関によるリスク過小評価

各銘柄の固有ボラティリティを共通に $\sigma_\epsilon$、各ペアの相関を $\rho$、等ウェイトを $1/N$ とします。

ポートフォリオ残差分散は

$$
\sigma_{p,\epsilon}^{2}
=
\frac{1}{N^2}
\left[
N\sigma_\epsilon^2
+
N(N-1)\rho\sigma_\epsilon^2
\right].
$$

したがって、

$$
\sigma_{p,\epsilon}
=
\sigma_\epsilon
\sqrt{
\frac{1+(N-1)\rho}{N}
}.
\tag{19}
$$

相関をゼロと仮定したモデル予測は

$$
\sigma_{p,\epsilon}^{model}
=
\frac{\sigma_\epsilon}{\sqrt N}.
\tag{20}
$$

例えば $\sigma_\epsilon=25\%$、$\rho=0.06$ なら、

- $N=50$：モデル3.5%、実際7.0%
- $N=20$：モデル5.6%、実際8.2%

となります。銘柄数を増やしても共通テーマリスクは分散されないため、銘柄数が多いほどモデルの過小評価倍率が大きくなります。`Thematic Investing A Risk-based Perspective(3).pdf`

---

## 2.11 残差リターンのトレンド検証

テーマ公表日だけに結果が依存しないよう、各バスケットについて、

- 公表日
- 公表日の約2年前から2年後までに配置した追加4時点

の合計5評価時点を設定します。

評価日 $\tau$ ごとに、

- 過去60日累積残差リターン $R_{b,\tau}^{past}$
- 将来60日累積残差リターン $R_{b,\tau}^{future}$
- 過去60日のAPC $z_{b,\tau}$

を計算します。

そのうえで、

$$
R_{b,\tau}^{future}
=
\alpha_g
+
\gamma_g R_{b,\tau}^{past}
+
\epsilon_{b,\tau},
\qquad
g=
\begin{cases}
coherent,&z_{b,\tau}\ge2,\\
noncoherent,&z_{b,\tau}<2.
\end{cases}
\tag{21}
$$

を推定します。

結果は、

| グループ | $\hat\gamma$ | $t$ 値 | 観測数 | $R^2$ |
|---|---:|---:|---:|---:|
| $z\ge2$ | 0.126 | 2.11 | 238 | 0.02 |
| $z<2$ | 0.028 | 0.47 | 458 | 0.000 |

です。coherent basketだけで残差モメンタムが現れます。`Thematic Investing A Risk-based Perspective(3).pdf`

### 注意

この論文は「過去残差リターンが正なら買う」という完全な投資戦略のバックテストを掲載していません。

- リバランスルール
- ポジションサイズ
- ロング／ショートの扱い
- 取引費用
- ベンチマーク

までは定義していないため、「実装可能性を示した診断研究」であり、完成された運用戦略研究ではありません。論文自身も、完全なバックテストを将来研究としています。`Thematic Investing A Risk-based Perspective(3).pdf`

---

## 2.12 再現手順

```text
1. 日次個別株超過リターンと日次Barra exposureを準備
2. 各日、横断面回帰から残差を推定
3. 対象テーマバスケットごとに過去30日または60日の残差相関行列を計算
4. APCを計算
5. Mosaic tileを作成
   - 10日ブロック
   - 銘柄をランダム群へ分割
   - 各群の銘柄数 >= 5 × 因子数
6. tileごとに残差化し、ブロック置換bootstrap
7. APCの帰無分布とz-scoreを推定
8. z>=2をcoherent themeと判定
9. リスク予測に非対角残差共分散を追加
10. 過去・将来60日残差リターン回帰でトレンドを検証
```

### 完全再現上の障害

- Goldman Sachsのpoint-in-time構成銘柄
- Barra GEM3
- Mosaic permutationの完全仕様
- Hazeltreeフロー
- Reuters broker report corpus

が必要です。

---

# 3. Thematic Investing as Missing Factors

## 3.1 研究仮説

この論文は、テーマを「既存ベンダーリスクモデルにまだ含まれていないファクター」と捉えます。

テーマは次の3軸でファクターへ移行すると整理されます。

1. emerging $\rightarrow$ established
2. transient $\rightarrow$ persistent
3. local $\rightarrow$ pervasive

新しく、一時的で、一部銘柄にしか効かないテーマは、標準リスクモデルに組み込まれにくい一方、該当銘柄のリスクを支配することがあります。`Thematic Investing as Missing Factors.pdf`

---

## 3.2 真のモデルとベンダーモデル

資産数を $u$、既存ファクター数を $v$、テーマ数を $m$ とします。

### 真のモデル

$$
\mathbf r
=
\mu\mathbf 1
+
\mathbf X_V\mathbf B_V
+
\mathbf X_M\mathbf B_M
+
\boldsymbol\varepsilon.
\tag{22}
$$

- $\mathbf X_V\in\mathbb R^{u\times v}$：ベンダー因子エクスポージャ
- $\mathbf X_M\in\mathbb R^{u\times m}$：テーマエクスポージャ
- $\mathbf B_V,\mathbf B_M$：各ファクターのリターン
- $\boldsymbol\varepsilon$：真の固有リターン

### 不完全なベンダーモデル

$$
\mathbf r
=
\mu\mathbf 1
+
\mathbf X_V\mathbf B_V^*
+
\boldsymbol\varepsilon_V^*.
\tag{23}
$$

テーマを省略すると、標準的なomitted-variable biasにより、

$$
E[\widehat{\mathbf B}_V^*]
=
\mathbf B_V
+
(\mathbf X_V'\mathbf X_V)^{-1}
\mathbf X_V'\mathbf X_M
\mathbf B_M.
\tag{24}
$$

したがって、既存ファクターとテーマが直交していなければ、テーマリターンの一部がベンダーファクターリターンに混入します。`Thematic Investing as Missing Factors.pdf`

---

## 3.3 テーマエクスポージャの純化

テーマエクスポージャを既存因子空間へ射影します。

$$
\mathbf X_M
=
\mathbf X_V\boldsymbol\theta
+
\mathbf e_M,
\tag{25}
$$

$$
\boldsymbol\theta
=
(\mathbf X_V'\mathbf X_V)^{-1}
\mathbf X_V'\mathbf X_M.
\tag{26}
$$

これを

$$
\mathbf X_M
=
\mathbf X_{M\parallel V}
+
\mathbf X_{M\perp V}
\tag{27}
$$

と書き、

$$
\mathbf X_{M\parallel V}
=
\mathbf X_V
(\mathbf X_V'\mathbf X_V)^{-1}
\mathbf X_V'\mathbf X_M,
\tag{28}
$$

$$
\mathbf X_{M\perp V}
=
\mathbf e_M
=
\left[
\mathbf I
-
\mathbf X_V(\mathbf X_V'\mathbf X_V)^{-1}\mathbf X_V'
\right]\mathbf X_M.
\tag{29}
$$

このとき、

$$
\mathbf X_V'\mathbf X_{M\perp V}=0.
\tag{30}
$$

$\mathbf X_{M\parallel V}$ は既存の業種・スタイル等で複製可能な部分、$\mathbf X_{M\perp V}$ は既存因子では複製できない純粋なテーマ部分です。`Thematic Investing as Missing Factors.pdf`

### WLSで実装する場合

実務的には回帰ウェイト $\mathbf W$ を使い、

$$
\boldsymbol\theta_W
=
(\mathbf X_V'\mathbf W\mathbf X_V)^{-1}
\mathbf X_V'\mathbf W\mathbf X_M,
\tag{31}
$$

$$
\mathbf X_V'\mathbf W\mathbf X_{M\perp V}=0
$$

とする方が自然です。

論文の数式はOLS表記ですが、実証ではGEM-LTと平方根時価総額ウェイトを用いるため、既存リスクモデルの推定規約と同じウェイトを使う実装が整合的です。

---

## 3.4 ベンダーファクターリターンを変更しない理由

テーマ寄与は

$$
\mathbf X_M\mathbf B_M
=
\mathbf X_{M\parallel V}\mathbf B_M
+
\mathbf X_{M\perp V}\mathbf B_M.
\tag{32}
$$

既存因子で説明可能な前半は、既に $\mathbf B_V^*$ に混入しています。

したがって、

$$
\mathbf r
=
\mu\mathbf 1
+
\mathbf X_V\mathbf B_V^*
+
\mathbf X_{M\perp V}\mathbf B_M
+
\boldsymbol\varepsilon.
\tag{33}
$$

と書けます。

この仕様は、

- ベンダーが公表する因子リターン $\mathbf B_V^*$ をそのまま保存
- 既存因子と直交するテーマだけを追加

する構造です。

---

## 3.5 FWLによるテーマリターン推定

ベンダー残差を

$$
\boldsymbol\varepsilon_V^*
=
\mathbf r-\mu\mathbf1-\mathbf X_V\mathbf B_V^*
$$

とします。

Frisch-Waugh-Lovell定理により、

$$
\boldsymbol\varepsilon_V^*
=
\mathbf X_{M\perp V}\mathbf B_M
+
\boldsymbol\varepsilon.
\tag{34}
$$

したがって各日 $t$ のテーマリターンは、ベンダー残差を純化テーマエクスポージャへ横断面回帰すれば得られます。`Thematic Investing as Missing Factors.pdf`

単一テーマ $m$ なら、

$$
\widehat B_{M,m,t}
=
\frac{
x_{M\perp V,m,t}'W_t\varepsilon_{V,t}^*
}{
x_{M\perp V,m,t}'W_tx_{M\perp V,m,t}
}.
\tag{35}
$$

論文では、テーマ間を相互に直交化せず、各テーマを1本ずつ推定します。そのため、推定されたテーマリターン同士は相関を持ち得ます。これは「AIとCloudの重複」などを意図的に残す仕様です。`Thematic Investing as Missing Factors.pdf`

---

## 3.6 拡張ファクター共分散行列

既存因子と純化テーマを結合します。

$$
\mathbf X
=
[\mathbf X_V,\mathbf X_{M\perp V}].
\tag{36}
$$

ファクター共分散を

$$
\boldsymbol\Sigma_{f,\perp}
=
\begin{bmatrix}
\boldsymbol\Sigma_V^*
&
\boldsymbol\Sigma_{V,M\perp V}
\\
\boldsymbol\Sigma_{V,M\perp V}'
&
\boldsymbol\Sigma_{M\perp V}
\end{bmatrix}
\tag{37}
$$

とします。

純化エクスポージャが既存エクスポージャと横断面で直交していても、テーマリターンと既存ファクターリターンは時系列で相関し得るため、交差ブロックは一般にゼロではありません。

推定仕様は、

- ボラティリティ・相関のhalf-life：252営業日
- Menchero-Ji法により正定値化
- 既存因子ブロックとテーマブロックは保存
- 交差共分散ブロックを固有値条件に基づき縮小

です。`Thematic Investing as Missing Factors.pdf`

### 資産共分散

実装上必要な資産共分散は

$$
\boxed{
\boldsymbol\Sigma_{\mathrm{asset},\perp}
=
\mathbf X
\boldsymbol\Sigma_{f,\perp}
\mathbf X'
+
\boldsymbol\Delta_{\varepsilon,\perp}
}
\tag{38}
$$

です。

本文のEquation (13)は

$$
\Sigma_\perp=\Sigma_{f,\perp}+\Delta_{\varepsilon,\perp}
$$

と略記されていますが、両者の次元はそのままでは一致しません。後続のEquation (15)では明確に $\mathbf X\Sigma_f\mathbf X'$ が使われているため、実装では式(38)と解釈する必要があります。`Thematic Investing as Missing Factors.pdf`

---

## 3.7 固有リスクの再計算

テーマを追加すると、それまで固有リスクとされていた変動の一部がテーマリスクになります。

論文の補足仕様では、銘柄 $i$ のベンダー総分散 $\sigma_{i,V}^2$ から拡張ファクター分散を差し引き、

$$
\sigma_{i,\varepsilon}^{2}
=
\sigma_{i,V}^{2}
-
[\mathbf X_V,\mathbf X_M]_i
\boldsymbol\Sigma_{f,\perp}
[\mathbf X_V,\mathbf X_M]_i'.
\tag{39}
$$

として固有分散を再計算します。`Thematic Investing as Missing Factors.pdf`

実装上は、

$$
\sigma_{i,\varepsilon}^{2}
\leftarrow
\max(\sigma_{i,\varepsilon}^{2},\epsilon)
$$

と下限を設け、負分散を防ぐ必要があります。

---

## 3.8 RavenPackによるテーマスコア

論文では、RavenPackが会社とテーマを同一記事内のentityとして識別したデータを使用します。

フィルター条件は、

$$
Relevance_{\text{firm}}\ge90,
\qquad
Relevance_{\text{theme}}\ge90.
$$

会社 $i$ のテーマ記事量を $Volume_i$、全記事量を $TotalVolume_i$ とし、いずれも36か月ローリング平均とします。

$$
TF_i
=
\frac{
Volume_i
}{
\max(50,TotalVolume_i)
}.
\tag{40}
$$

$\max(50,\cdot)$ により、ニュース量が少ない銘柄の分母を最低50にし、少数記事による極端なスコアを抑えます。

次に、

- 上位5%をwinsorize
- 下位1%をwinsorize
- 月次横断面で0-1へmin-max変換

します。

$$
Score_i
=
\frac{
TF_i-\min_j TF_j
}{
\max_j TF_j-\min_j TF_j
}.
\tag{41}
$$

これが生テーマエクスポージャ $\mathbf X_M$ です。`Thematic Investing as Missing Factors.pdf`

---

## 3.9 テーマポートフォリオ最適化

テーマ間の相対ウェイトを

$$
\mathbf s_M\in\mathbb R^m
$$

とし、総合テーマスコアベクトルを

$$
\mathbf a
=
\mathbf X_{M\perp V}\mathbf s_M
\tag{42}
$$

とします。

最小分散テーマポートフォリオは

$$
\min_{\boldsymbol\omega}
\boldsymbol\omega'
\boldsymbol\Sigma_{\mathrm{asset},\perp}
\boldsymbol\omega
\tag{43}
$$

subject to

$$
\boldsymbol\omega'
\mathbf X_{M\perp V}\mathbf s_M
=
S_T.
\tag{44}
$$

- $\mathbf s_M=(1/m)\mathbf1$：全テーマを同等に扱う
- 単一テーマ：対象テーマだけ1、他を0
- $S_T$：ポートフォリオ全体のテーマ強度目標

です。$S_T$ を高くすると集中度とリスクが上昇します。`Thematic Investing as Missing Factors.pdf`

### KKTによる閉形式

以下は論文に明示されていないものの、式(43)-(44)から直接得られる実装式です。

制約がテーマ目標だけなら、

$$
\boxed{
\boldsymbol\omega^*
=
\frac{
S_T
\boldsymbol\Sigma^{-1}\mathbf a
}{
\mathbf a'
\boldsymbol\Sigma^{-1}\mathbf a
}
}
\tag{45}
$$

です。

予算制約も含め、

$$
\mathbf C'
\boldsymbol\omega
=
\mathbf d
$$

と書けば、

$$
\boxed{
\boldsymbol\omega^*
=
\boldsymbol\Sigma^{-1}\mathbf C
\left(
\mathbf C'\boldsymbol\Sigma^{-1}\mathbf C
\right)^{-1}
\mathbf d
}
\tag{46}
$$

です。

例えば、

- long-only total portfolio：

$$
\mathbf C=[\mathbf1,\mathbf a],
\qquad
\mathbf d=[1,S_T]'.
$$

- active portfolio：

$$
\mathbf C=[\mathbf1,\mathbf a],
\qquad
\mathbf d=[0,S_T]'.
$$

非負制約、個別ウェイト上限、turnover制約を加える場合は二次計画問題として解きます。

---

## 3.10 リスク分解

ポートフォリオのシステマティック分散は

$$
\sigma_T^2
=
\omega'
X\Sigma_{f,\perp}X'
\omega.
$$

これを展開すると、

$$
\sigma_T^2
=
\sigma_V^2
+
\sigma_{M\perp V}^2
+
2\sigma_{V,M\perp V}.
\tag{47}
$$

- $\sigma_V^2$：既存因子由来
- $\sigma_{M\perp V}^2$：純化テーマ由来
- $\sigma_{V,M\perp V}$：既存因子リターンとテーマリターンの共分散寄与

です。

テーマを追加すれば常にリスクが増えるとは限りません。交差共分散が十分負なら、拡張後のリスクが低下する場合もあります。

---

## 3.11 実証結果

データ仕様は、

- RavenPack：2014年1月-2025年6月
- ACWI IMI構成銘柄の日次リターン：2017年以降
- MSCI Barra GEM-LT
  - 16スタイル
  - 45業種
  - market factor
- テーマ：
  - AI
  - Robotics
  - Cybersecurity
  - Blockchain
  - Cloud
- factor volatility・correlation half-life：252日

です。`Thematic Investing as Missing Factors.pdf`

純化回帰のAdjusted $R^2$ は、そのテーマが既存因子でどの程度説明されるかを表します。AIは2017年18%から2020年37%、2023年32%、2025年65%まで上昇し、Software・Semiconductor業種因子との重複が拡大しています。`Thematic Investing as Missing Factors.pdf`

### ETFとの比較

- AIQの約10%のTEの大半はbeta・業種・スタイルで、5テーマの寄与は0.45%
- 純化AIポートフォリオのTEは約2.16%で、1.57%がテーマ寄与
- ARKKのTE約18.85%はほぼbeta・スタイル・固有リスクで、対象5テーマの寄与はゼロ
- 純化multi-theme portfolioはTE約2.20%、うち1.55%がテーマ寄与

です。`Thematic Investing as Missing Factors.pdf`

要するに、名称上の「テーマETF」と、純化されたテーマリスクを持つポートフォリオは同じものではありません。

---

## 3.12 再現手順

```text
1. 月次の企業×テーマ記事スコアを作る
2. 36か月平均、relevance filter、winsorize、min-max変換
3. 月末ごとにテーマスコアをBarra exposureへ横断面回帰
4. 回帰残差を純化テーマ exposure とする
5. ベンダー残差を純化テーマ exposureへ日次横断面回帰
6. 日次テーマ factor returnを得る
7. 252日half-lifeでテーマ・既存因子の共分散を推定
8. Menchero-Ji等で正定値化
9. 固有分散を再推定
10. asset covariance = X F X' + Delta を構築
11. テーマ目標を制約とする最小分散QPを解く
12. beta/style/industry/theme/specificへリスク寄与を分解
```

---

# 4. Allocating to Thematic Investments

## 4.1 研究目的

この論文は、テーマを

> 資産クラス、地域、業種、スタイルに追加される投資次元

と捉え、テーマ投資を伝統的マルチアセットポートフォリオへ組み込む方法を扱います。

重要なのは、テーマ指数のリターンをそのまま「テーマ・リターン」と見なさず、

1. 市場beta
2. 地域・スタイル・業種
3. 純粋なテーマ成分

へ分解することです。`Allocating to Thematic Investments(3).pdf`

---

## 4.2 テーマの代表リターン

5テーマを扱います。

- Disruptive Technology
- Sustainable Water
- Sustainable Food
- Energy Transition
- Environmental Sustainability

各株式テーマについて、異なるプロバイダーの2指数を等ウェイトで合成します。Environmental SustainabilityについてはGreen Bond指数も使用します。`Allocating to Thematic Investments(3).pdf`

テーマ $h$ の代表リターンは概念的に

$$
R_{h,t}
=
\frac{1}{K_h}
\sum_{k=1}^{K_h}R_{h,k,t}.
\tag{48}
$$

---

## 4.3 市場・地域・スタイル・業種分解

テーマ超過リターンを

$$
XR_{h,t}
=
XR_{h,t}^{market}
+
XR_{h,t}^{region/style/sector}
+
XR_{h,t}^{pure}.
\tag{49}
$$

と分解します。`Allocating to Thematic Investments(3).pdf`

### Step 1：テーマの市場beta除去

株式テーマはMSCI ACWI、債券テーマはBloomberg Global Aggregateを市場ベンチマークとします。

$$
XR_{h,t}
=
\alpha_h
+
\beta_h^M XR_{M,t}
+
\varepsilon_{h,t}^{M}.
\tag{50}
$$

$\varepsilon_{h,t}^{M}$ は市場betaを除去したテーマリターンです。

### Step 2：候補指数も市場中立化

地域・スタイル・業種指数 $j$ ごとに、

$$
XR_{j,t}
=
\alpha_j
+
\beta_j^M XR_{M,t}
+
\varepsilon_{j,t}^{M}.
\tag{51}
$$

これにより、説明変数同士の共通市場betaを事前に除去します。

### Step 3：LASSOによる変数選択

候補は、

- 株式指数128本
- 債券指数46本
- 週次観測約260個

です。

$$
\widehat{\boldsymbol\beta}^{LASSO}
=
\arg\min_{\boldsymbol\beta}
\left\{
\sum_{t=1}^{T}
\left(
\varepsilon_{h,t}^{M}
-
\sum_{j=1}^{J}
\beta_j\varepsilon_{j,t}^{M}
\right)^2
+
\lambda\sum_{j=1}^{J}|\beta_j|
\right\}.
\tag{52}
$$

$\lambda$ はクロスバリデーションの最小MSEから1標準誤差以内にある、より強く縮小された値、すなわちlambda-1SEを採用します。`Allocating to Thematic Investments(3).pdf`

### Step 4：選択変数によるOLS再推定

LASSOで非ゼロとなった集合を $\mathcal S_h$ とし、

$$
\varepsilon_{h,t}^{M}
=
\alpha_h^{S}
+
\sum_{j\in\mathcal S_h}
\widetilde\beta_{h,j}
\varepsilon_{j,t}^{M}
+
\delta_{h,t}^{pure}.
\tag{53}
$$

$\delta_{h,t}^{pure}$ がpure thematic returnです。

LASSO係数をそのまま純化に使うのではなく、選択後に通常回帰を行い、残差をテーマ固有成分とするのが論文の手順です。

---

## 4.4 マクロ資産配分リスクモデル

17の主要資産の月次現地通貨リターン共分散行列を

$$
\widehat{\boldsymbol\Sigma}_R
$$

とし、PCAを行います。

$$
\widehat{\boldsymbol\Sigma}_R
=
\mathbf Q\boldsymbol\Lambda\mathbf Q'.
\tag{54}
$$

最初の6固有ベクトルを採用します。

$$
\mathbf f_t
=
\mathbf Q_6'\mathbf R_t.
\tag{55}
$$

6因子は経済的に、

1. Market Risk
2. Duration
3. Corporate Spreads
4. Emerging Markets / Commodities
5. US
6. Asia / Japan

と解釈されます。

最初の6PCで全分散の約87%を説明し、構築期間内では互いに直交します。`Allocating to Thematic Investments(3).pdf`

テーマ $h$ のマクロ因子回帰は

$$
R_{h,t}
=
\alpha_h
+
\boldsymbol\beta_h'\mathbf f_t
+
u_{h,t}.
\tag{56}
$$

---

## 4.5 リスクの3分解

テーマの総分散を

$$
\sigma_h^2
=
\sigma_{h,sys}^2
+
\sigma_{h,specific}^2
+
\sigma_{h,theme}^2
\tag{57}
$$

と整理します。

### Systematic volatility

$$
\sigma_{h,sys}^2
=
\boldsymbol\beta_h'
\boldsymbol\Sigma_f
\boldsymbol\beta_h.
\tag{58}
$$

### Specific volatility

6PCで説明されない、伝統的資産クラス側の13%の分散に由来する部分です。

### Thematic volatility

既存マクロ因子にも、伝統資産モデルのspecific riskにも対応しないテーマ固有部分です。

論文はこの3分解の結果を提示していますが、specific volatilityとthematic volatilityの分離推定式を完全には記載していません。したがって、表を数値まで完全再現するには、著者の基礎リスクモデル実装または関連論文の仕様が必要です。テーマ株式については、thematic volatilityが全て有意な大きさを持つと報告されています。`Allocating to Thematic Investments(3).pdf`

---

## 4.6 期待リターン

伝統資産・伝統因子については1954年まで遡る長期リターンを使用し、長期Sharpe ratioを0.3-0.4程度と仮定しています。

テーマ期待リターンは、

$$
E[R_h]
=
\boldsymbol\beta_h'\boldsymbol\lambda_f
+
\alpha_h^{theme}.
\tag{59}
$$

テーマ固有アルファは、テーマ固有リスクにinformation ratioを掛ける形で解釈できます。

$$
\alpha_h^{theme}
=
IR_h^{theme}
\sigma_{h,theme}.
\tag{60}
$$

実証例では

$$
IR_h^{theme}=0.3
$$

を仮定します。これは推定結果ではなく、投資家の将来見通し・確信度を表す入力パラメータです。IRをゼロにすれば、テーマ資産は純粋な分散投資源としてのみ選択されます。`Allocating to Thematic Investments(3).pdf`

したがって、論文の配分結果は「テーマに正のアルファがある」という仮定にかなり依存します。

---

## 4.7 Robust portfolio optimization

論文はrobust optimizationを使用したと述べていますが、目的関数と不確実性集合を本文中に完全には記載せず、Yin et al.およびPerchet et al.へ委ねています。`Allocating to Thematic Investments(3).pdf`

このため、PDF単体から最終ウェイトを完全一致させることはできません。

### 論文の記述と整合する最小実装例

以下は論文に明記された式ではなく、記述を実装可能な形に落とした一例です。

$$
\max_{\mathbf w\in\mathcal W}
\left[
\mathbf w'\widehat{\boldsymbol\mu}
-
\delta\sqrt{\mathbf w'\boldsymbol\Omega_\mu\mathbf w}
-
\frac{\gamma}{2}\mathbf w'\boldsymbol\Sigma\mathbf w
-
\frac{\kappa}{2}
(\mathbf w-\mathbf w_A)'
\boldsymbol\Sigma
(\mathbf w-\mathbf w_A)
\right].
\tag{61}
$$

- $\boldsymbol\Omega_\mu$：期待リターン推定誤差共分散
- $\delta$：推定不確実性への保守性
- $\gamma$：絶対リスク回避度
- $\kappa$：core-only portfolio $\mathbf w_A$ に対するTE回避度
- $\mathcal W=\{\mathbf w:\mathbf1'\mathbf w=1,\mathbf w\ge0\}$

です。

第2項がrobust mean-uncertainty penalty、第4項がcoreに対するtracking-error penaltyです。

---

## 4.8 A・B・Cポートフォリオ

各リスクプロファイルについて3種類を作ります。

### Portfolio A

- Core assetsのみ
- 欧州株
- 北米株
- EUR IG債
- USD IG債
- cash

### Portfolio B

- Core
- Diversification satellite
  - 小型株
  - 日本株
  - 新興国株
  - 不動産
  - 新興国債券等

### Portfolio C

- Core
- Diversification satellite
- Thematic investments

共通制約は、

$$
\mathbf1'\mathbf w=1,\qquad
\mathbf w\ge0.
\tag{62}
$$

レバレッジ・ショートは禁止です。Satelliteの大きさは、同じリスクプロファイルのPortfolio Aに対するtracking-error aversionで調整されます。

---

## 4.9 主な結果

テーマを追加したPortfolio Cでは、

- Conservative：satellite約29%
- Moderately Aggressive：約41%
- Coreに対するTE：約0.8-1.2%

となります。

一部のテーマ投資は新興国株など既存のdiversifierを置き換えます。低リスクのEnvironmental Sustainability Bondは、株式テーマより大きな配分を得ます。`Allocating to Thematic Investments(3).pdf`

Portfolio CとBの差分TEの大部分は、

$$
TE_{theme}
$$

であり、伝統的マクロ因子のTE差は小さいです。つまり、オプティマイザーは既存因子エクスポージャを大きく変えず、正のアルファを付与したテーマ固有リスクを追加します。`Allocating to Thematic Investments(3).pdf`

---

## 4.10 再現手順

```text
1. 各テーマについて複数プロバイダー指数を等ウェイト合成
2. 週次USDリターンを水曜-水曜で作成
3. テーマと候補指数をそれぞれ市場回帰し、市場残差を取得
4. テーマ残差を候補指数残差へLASSO回帰
5. lambda-1SEで説明変数を選択
6. 選択後OLSからpure thematic returnを計算
7. 17資産の月次共分散にPCA
8. 上位6PCをマクロ因子としてテーマbetaを推定
9. systematic / specific / thematic riskへ分解
10. factor premia + IR×thematic volatilityで期待リターンを構築
11. Core / Diversification / Themeの投資可能集合を定義
12. fully-invested、long-only、TE penalty付きrobust optimizationを実行
```

### 再現性上の重要な限界

5本の中で、論文単体から最終ウェイトを完全再現しにくいのがこの論文です。

理由は、

- robust optimizationの完全な目的関数が省略
- 不確実性集合・キャリブレーションが省略
- specific riskとthematic riskの詳細な分離式が省略
- 使用指数データが主にBloomberg

であるためです。

---

# 5. Episodic Factor Pricing

## 5.1 研究仮説

通常のファクターモデルは、「各ファクターは常時価格付けされている」と暗黙に仮定します。

本論文はこれを否定し、

> 企業特性が横断面リターンを予測できるpricing-on状態と、予測できないpricing-off状態が切り替わる

と考えます。

ファクターリターンそのものを直接予測するのではなく、「そのファクターの基礎特性が来月の株式横断面を説明できるか」を予測します。`Episodic Factor Pricing.pdf`

---

## 5.2 データ

- CRSP米国普通株
- NYSE、AMEX、Nasdaq
- 211企業特性：Chen-Zimmermann
- 期間：1970年1月-2023年12月
- 最初の5年間を初期推定期間
- OOS評価：1975年1月-2023年12月
- 211特性の分類：
  - Momentum
  - Value/Growth
  - Investment
  - Profitability
  - Intangibles
  - Trading Frictions

代表ファクターとして、MKT、SMB、HML、RMW、CMA、UMD、ROE、IA、BABも使用します。`Episodic Factor Pricing.pdf`

---

## 5.3 特性の横断面標準化

各月・各特性について銘柄をrank化します。

$$
C_{j,i,t}
=
\frac{
rank(C_{j,i,t}^{raw})
}{
N_{j,t}
}
-
0.5.
\tag{63}
$$

したがって、

$$
C_{j,i,t}\in[-0.5,0.5].
$$

この変換は、

- 外れ値に頑健
- 特性の絶対値より順位情報を重視
- 月ごとの分布変化を抑制

するためです。

---

## 5.4 Fama-MacBeth型のOOS予測

各特性 $j$ について毎月、単変量横断面回帰を行います。

$$
r_{i,t}
=
a_{j,t}
+
b_{j,t}C_{j,i,t-1}
+
\varepsilon_{i,t}.
\tag{64}
$$

推定ウェイトは前月末時価総額です。

月 $t+1$ の予測には、月 $t$ までに推定された全係数の時系列平均を使います。

$$
\widehat r_{j,i,t+1|t}
=
\overline a_{j,t}
+
\overline b_{j,t}C_{j,i,t},
\tag{65}
$$

$$
\overline a_{j,t}
=
\frac{1}{M_t}
\sum_{\tau\le t}\widehat a_{j,\tau},
\qquad
\overline b_{j,t}
=
\frac{1}{M_t}
\sum_{\tau\le t}\widehat b_{j,\tau}.
\tag{66}
$$

係数をexpanding averageすることで、月次係数のノイズと過学習を抑えます。

---

## 5.5 SED：横断面予測力の尺度

市場共通成分を除いたリターンを

$$
dr_{i,t}=r_{i,t}-\overline r_t
$$

とし、予測値も

$$
d\widehat r_{j,i,t}
=
\widehat r_{j,i,t|t-1}
-
\overline{\widehat r}_{j,t|t-1}
$$

とdemeanします。

特性 $j$ のcross-sectional squared-error differenceは

$$
SED_{j,t}
=
\frac{1}{N_t}
\sum_{i=1}^{N_t}
\left[
(dr_{i,t})^2
-
\left(
dr_{i,t}
-
d\widehat r_{j,i,t}
\right)^2
\right].
\tag{67}
$$

基準モデルは全銘柄について

$$
d\widehat r_{i,t}^{bench}=0
$$

と予測します。すなわち、「期待リターンの横断面差はない」という予測です。

したがって、

$$
SED_{j,t}>0
$$

なら、特性 $j$ に基づく予測の方が基準モデルよりMSFEが小さいことを意味します。

市場リターンをdemeanすることが重要で、これにより「市場全体の上昇予測」と「銘柄間の相対リターン予測」を分離します。

---

## 5.6 pricing-on/offの予測

SEDを前月市場ボラティリティで正規化します。

$$
Y_{j,t}
=
\frac{SED_{j,t}}{\sigma_{M,t-1}}.
\tag{68}
$$

予測モデルは

$$
Y_{j,t}
=
\gamma_{0,j}
+
\boldsymbol\gamma_j'\mathbf Z_{t-1}
+
e_{j,t}.
\tag{69}
$$

説明変数は28個です。

### 16マクロ変数

- dividend-price ratio
- dividend yield
- book-to-market
- earnings-price
- Treasury bill rate
- default yield spread
- long-term return
- net equity expansion
- stock variance
- stock return
- long-term yield
- inflation
- default return spread
- term spread
- payout ratio
- corporate bond return

### 5センチメント変数

- dividend premium
- IPO初日リターン
- IPO件数
- closed-end fund discount
- share turnover

### 7つの過去SED

$$
1,3,6,9,12,18,24
$$

か月平均です。

LASSO推定は

$$
\widehat{\boldsymbol\gamma}_{j,t}
=
\arg\min_{\gamma_0,\boldsymbol\gamma}
\left\{
\sum_{\tau\le t}
\left(
Y_{j,\tau}
-
\gamma_0
-
\boldsymbol\gamma'\mathbf Z_{\tau-1}
\right)^2
+
\lambda\|\boldsymbol\gamma\|_1
\right\}.
\tag{70}
$$

- expanding window
- $\lambda$ はAICで選択
- 時点 $t$ までの情報のみ使用

です。`Episodic Factor Pricing.pdf`

来月の状態を

$$
I_{j,t+1|t}
=
\mathbf1
\left\{
\widehat{SED}_{j,t+1|t}>0
\right\}
\tag{71}
$$

と定義します。

- $I=1$：pricing-on
- $I=0$：pricing-off

閾値0には、「特性予測がno-dispersion benchmarkを上回る」という経済的意味があります。

---

## 5.7 予測精度評価

月次OOS $R^2$ は

$$
R_{OS,t}^2
=
1-
\frac{
\sum_i w_{i,t}
\left(
dr_{i,t}-d\widehat r_{i,t}
\right)^2
}{
\sum_i w_{i,t}(dr_{i,t})^2
}.
\tag{72}
$$

期間平均は

$$
R_{OS}^2
=
\frac1T\sum_tR_{OS,t}^2.
\tag{73}
$$

また、Mincer-Zarnowitz型横断面回帰

$$
r_{i,t}
=
\alpha_t
+
\delta_t\widehat r_{i,t|t-1}
+
v_{i,t}
\tag{74}
$$

を推定します。

- $\delta=1$：無偏
- $\delta<1$：予測分散が過大
- $\delta>1$：予測分散が過小

です。

経済的価値は、予測上位十分位ロング・下位十分位ショートで評価します。

---

## 5.8 FF3・FF5の結果

価値加重で、

### FF3

- on：
  - $R_{OS}^2=0.21\%$
  - 月次L/S 1.21%
  - 年率Sharpe 0.95
- off：
  - $R_{OS}^2=-0.31\%$
  - 月次L/S -0.35%
  - Sharpe -0.28

### FF5

- on：
  - $R_{OS}^2=0.24\%$
  - 月次L/S 1.36%
  - Sharpe 1.06
- off：
  - $R_{OS}^2=-0.30\%$
  - 月次L/S -0.18%
  - Sharpe -0.15

です。

個別ファクターでも、

- SMB：on 0.73%、off -0.21%
- HML：on 0.60%、off 約-0.20%
- RMW：on 0.51%
- CMA：on 0.38%

となります。pricing-on/offは単なる高・低市場ボラティリティの代理ではなく、各ボラティリティ・サブサンプル内でも効果が残ります。`Episodic Factor Pricing.pdf`

---

## 5.9 Multifactor portfolio

ファクターリターンベクトルを $\mathbf R_t$ とします。

unmanaged MVE portfolioは、

$$
\max_{\boldsymbol\omega\ge0}
\left[
\boldsymbol\omega'\widehat{\boldsymbol\mu}
-
\frac{\gamma}{2}
\boldsymbol\omega'
\widehat{\boldsymbol\Sigma}
\boldsymbol\omega
\right],
\qquad
\gamma=5.
\tag{75}
$$

ファクターはzero-cost portfolioなので、

$$
\mathbf1'\boldsymbol\omega=1
$$

は課しません。

初期60か月で推定し、その後expanding windowで毎月更新します。

---

## 5.10 pricing-state-managed portfolio

off状態でも完全にゼロにせず、retention ratio $\eta$ を残します。

$$
d_{k,t}
=
\eta+(1-\eta)I_{k,t|t-1}.
\tag{76}
$$

したがって、

- on：$d=1$
- off：$d=\eta$

です。

managed portfolio returnは

$$
R_{PMP,t}
=
\boldsymbol\omega_{t|t-1}'
\operatorname{diag}(\mathbf d_t)
\mathbf R_t.
\tag{77}
$$

結果は、

- FF3：Sharpe 0.50 $\rightarrow$ 0.88
- FF5＋UMD：1.06 $\rightarrow$ 1.31
- 9ファクター：1.18 $\rightarrow$ 1.56

です。

---

## 5.11 取引費用込み最適化

取引費用込みでは、

$$
\max_{\boldsymbol\omega\ge0}
\left[
\boldsymbol\omega'\widehat{\boldsymbol\mu}
-
TC_d(\boldsymbol\omega)
-
\frac{\gamma}{2}
\boldsymbol\omega'
\widehat{\boldsymbol\Sigma}
\boldsymbol\omega
\right].
\tag{78}
$$

ファクター $k$ の個別株ウェイトを $x_{k,t}$ とし、

$$
\mathbf W_t(\boldsymbol\omega)
=
\mathbf X_t\boldsymbol\omega.
\tag{79}
$$

リバランス前のドリフト後ウェイトは

$$
\mathbf W_t^*
=
\mathbf W_t
\circ
(\mathbf1+\mathbf R_{t+1}^{stock}).
\tag{80}
$$

取引量は

$$
\Delta\mathbf W_{t+1}
=
\mathbf W_{t+1}-\mathbf W_t^*.
\tag{81}
$$

平均取引費用は

$$
TC_d(\boldsymbol\omega)
=
\frac{1}{T-1}
\sum_{t=1}^{T-1}
\left\|
\boldsymbol\Lambda_t
\Delta\mathbf W_{t+1}(\boldsymbol\omega)
\right\|_1.
\tag{82}
$$

異なるファクター間の売買をまず個別株レベルでnettingし、その後に取引費用を課します。

費用込み9ファクターでは、

- unmanaged Sharpe：約0.94
- managed：約1.02-1.07
- unmanagedとmanagedを同時最適化するPMP+：最大約1.10

です。

---

## 5.12 State-dependent SDF

状態依存SDFを

$$
M_{t+1}^{I}
=
1-
\sum_{k=1}^{K}
\left(
\alpha_k
+
\beta_k\widetilde I_{k,t+1|t}
\right)
\widetilde r_{k,t+1}
\tag{83}
$$

とします。

$$
\widetilde I_{k,t+1|t}
=
I_{k,t+1|t}-E[I_k].
$$

ファクター間相関を無視した簡略化では、

$$
E_t[r_{k,t+1}]
=
\left(
\alpha_k+\beta_k\widetilde I_{k,t+1|t}
\right)
\operatorname{Var}_t(r_{k,t+1}).
\tag{84}
$$

そこで、実現価格リスクを

$$
RP_{k,t+1}
=
\frac{
r_{k,t+1}
}{
\sigma_{k,t}^{2}
}
$$

とし、

$$
RP_{k,t+1}
=
\alpha_k
+
\beta_k\widetilde I_{k,t+1|t}
+
\varepsilon_{k,t+1}
\tag{85}
$$

を推定します。

$\beta_k>0$ なら、pricing-on状態でrisk priceが高いことを意味します。8ファクター全てで $\hat\beta_k>0$ で、市場ボラティリティの逆数を追加しても符号が維持されます。`Episodic Factor Pricing.pdf`

---

## 5.13 211ファクターへの拡張

月 $t$ にpricing-onであるファクター数を

$$
Breadth_t
=
\sum_{j=1}^{211}I_{j,t}
\tag{86}
$$

とします。

- 平均：約125
- 最小：84
- 最大：162
- 景気後退期に低下
- 景気拡大期に回復

というprocyclicalな性質を持ちます。`Episodic Factor Pricing.pdf`

各カテゴリー内で、事前ボラティリティ10%へ調整したファクターをpricing-on/offに分けて等ウェイトします。

$$
R_{c,on,t}
=
\frac{
\sum_{j\in c}I_{j,t}R_{j,t}
}{
\sum_{j\in c}I_{j,t}
}.
\tag{87}
$$

例えばSharpeは、

- Value：on 1.83、off 0.20
- Investment：on 1.68、off 0.78
- Intangibles：on 2.08、off 0.96
- Trading Frictions：on 1.72、off 0.70

です。`Episodic Factor Pricing.pdf`

---

## 5.14 pricing-on signal ensemble

各特性の株式リターン予測 $\widehat r_{j,i,t+1}$ を合成します。

### 単純平均

$$
Comb_{i,t+1}^{naive}
=
\frac{1}{J_t}
\sum_{j=1}^{J_t}
\widehat r_{j,i,t+1}.
\tag{88}
$$

### pricing-onだけを平均

$$
Comb_{i,t+1}^{on}
=
\frac{1}{N_{on,t}}
\sum_{j=1}^{J_t}
I_{j,t}
\widehat r_{j,i,t+1}.
\tag{89}
$$

### pricing-offだけを平均

$$
Comb_{i,t+1}^{off}
=
\frac{1}{N_{off,t}}
\sum_{j=1}^{J_t}
(1-I_{j,t})
\widehat r_{j,i,t+1}.
\tag{90}
$$

月次で銘柄を十分位ソートし、上位ロング・下位ショートします。

全期間の月次H-Lは、

- $Comb^{on}$：1.98%、$t=9.00$
- $Comb^{naive}$：1.36%、$t=6.29$
- $Comb^{off}$：-0.12%、非有意

です。

年率では、

| Signal | Return | Vol | Sharpe | MaxDD |
|---|---:|---:|---:|---:|
| Naive | 16.33% | 16.67% | 0.98 | 53.46% |
| On | 23.76% | 19.54% | 1.22 | 40.76% |
| Off | -1.49% | 18.69% | -0.08 | 93.69% |

となります。`Episodic Factor Pricing.pdf`

---

## 5.15 再現手順

```text
1. CRSP月次リターンと211特性をpoint-in-timeで準備
2. 各月・各特性をrank / N - 0.5へ変換
3. 特性ごとに時価総額WLS横断面回帰
4. 過去係数のexpanding averageで翌月リターン予測
5. 実現後にSEDを計算
6. SED、マクロ、センチメントを用いてexpanding LASSO
7. AICでlambda選択
8. 翌月SED予測が正ならpricing-on
9. on/off別にファクターリターン、R2、L/Sを評価
10. MVE factor portfolioを推定
11. off factorをretention ratio etaへ縮小
12. 必要に応じて株式レベルで売買netting・取引費用を控除
13. 211予測をon-only ensembleへ集約
```

### 再現上の注意

- 特性データのpoint-in-time処理
- CRSP delisting return
- book equity等のpublication lag
- Chen-Zimmermannの正確な特性定義
- AICによるLASSO選択の実装差
- 個別株取引費用系列
- 各ファクターの個別株ウェイト履歴

が結果へ大きく影響します。

---

# 6. 5論文の手法上の違い

## 6.1 「純化」の意味は論文ごとに異なる

### Narrative Momentum

株式リターンを市場リターンとナラティブ強度変化へ時系列回帰します。

$$
r_{i,w}
\sim
r_{m,w}
+
\Delta I_{n,w}.
$$

ここで得るのは、**株価のナラティブ感応度**です。

### Risk-based Perspective

Barra因子で日次横断面リターンを説明した残差について、銘柄間相関を測ります。

$$
r_t-X_tb_t=u_t.
$$

得るのは、**既存リスクモデル外に共通変動が残っているかという診断**です。

### Missing Factors

生テーマスコアを既存因子エクスポージャへ横断面射影します。

$$
X_{M\perp V}
=
(I-P_V)X_M.
$$

得るのは、**既存因子で複製不能なテーマエクスポージャ**です。

### Allocating to Thematic Investments

テーマ指数リターンを市場、地域、業種、スタイル指数リターンへ時系列回帰します。

$$
R_{theme,t}
\sim
R_{market,t}
+
R_{sector/style/region,t}.
$$

得るのは、**テーマ指数リターンの純粋残差成分**です。

したがって、Missing Factorsの純化は「銘柄横断面のエクスポージャ純化」、Somefun et al.の純化は「テーマ指数時系列のリターン純化」であり、同じ処理ではありません。

---

## 6.2 Narrative betaとNarrative scoreは別物

### Narrative Momentum

$$
\beta_{n,i}
=
\frac{
\operatorname{Cov}(r_i,\Delta I_n\mid r_m)
}{
\operatorname{Var}(\Delta I_n\mid r_m)
}.
$$

市場がナラティブを銘柄にとってプラス／マイナスのどちらと評価したかを含みます。

### Missing Factors

$$
Score_i
=
\text{企業とテーマが同一記事で関連付けられる頻度}.
$$

企業の事業内容とテーマの関連度を測りますが、リターンの方向性は直接含みません。

両者を統合する場合、

- text score：構造的・事業的関連性
- return beta：市場が評価した方向性と感応度

として別々の特徴量にする方が自然です。

---

# 7. 5論文を統合した実務フレームワーク

以下は各論文そのものではなく、5本を一貫した運用工程へ統合した構成です。

## 第1段階：テーマスコアの作成

RavenPack型の企業別スコア、事業売上比率、LLM/NLP、アナリスト分類などから

$$
X_{M,t}^{raw}
$$

を作ります。

## 第2段階：既存因子から純化

$$
X_{M\perp V,t}
=
\left(
I-X_{V,t}(X_{V,t}'W_tX_{V,t})^{-1}X_{V,t}'W_t
\right)
X_{M,t}^{raw}.
$$

## 第3段階：テーマファクターリターンの推定

$$
r_{\varepsilon V,t}^{*}
=
X_{M\perp V,t}B_{M,t}
+
\varepsilon_t.
$$

各テーマを1本ずつ、または適切な正則化を伴う同時回帰で推定します。

## 第4段階：テーマcoherenceの検定

テーマ構成銘柄の既存因子残差について、

$$
\overline\rho_{M,t}
=
\frac{2}{N_M(N_M-1)}
\sum_{i<j}\rho_{ij,t}
$$

を計算し、Mosaic＋bootstrapで

$$
z_{M,t}
$$

を求めます。

$$
z_{M,t}\ge2
$$

のテーマだけを「現在、独立した共通ドライバーとして顕在化している」と判定できます。

## 第5段階：Narrative momentum signal

$$
S_{M,t}^{attention}
=
\overline I_{M,t-J:t-1}
-
\overline I_{M,t-2J:t-J-1}.
$$

- $S>0$：注目拡大
- $S<0$：注目縮小

です。

## 第6段階：pricing-on/off判定

テーマファクターの関連企業スコアが将来横断面を説明できるかについてSEDを作り、

$$
I_{M,t+1}
=
\mathbf1\{
\widehat{SED}_{M,t+1|t}>0
\}
$$

を推定します。

Narrative momentumが正でもpricing-offなら、ポジションを縮小します。

$$
\widetilde S_{M,t}
=
S_{M,t}^{attention}
\left[
\eta+(1-\eta)I_{M,t+1}
\right].
$$

## 第7段階：拡張リスクモデル

$$
\Sigma_{asset,t}^{aug}
=
[X_{V,t},X_{M\perp V,t}]
\Sigma_{f,t}^{aug}
[X_{V,t},X_{M\perp V,t}]'
+
\Delta_t^{aug}.
$$

## 第8段階：最終ポートフォリオ

テーマ期待リターンを

$$
\mu_{M,t}
=
c_1S_{M,t}^{attention}
+
c_2Mom_{M,t}^{return}
+
c_3z_{M,t}
$$

などで構築し、

$$
\max_w
\left[
w'\mu_t
-
\frac{\gamma}{2}w'\Sigma_{asset,t}^{aug}w
-
\lambda_{TC}\|w-w_{t-1}^{drift}\|_1
\right]
$$

を、

- benchmark neutrality
- Barra factor neutrality
- sector/country/currency上限
- gross・net制約
- 銘柄ウェイト上限
- turnover制約
- borrowability制約

の下で解きます。

---

# 8. 再現性の評価

| 論文 | 手法の記述 | データ入手性 | 数値完全再現 |
|---|---|---|---|
| Narrative Momentum | 高い | 低い | 困難 |
| Risk-based Perspective | 中程度 | 低い | 困難 |
| Missing Factors | 高いが一部略記あり | 低い | 困難 |
| Allocating to Thematic Investments | 最適化仕様が不足 | 低い | 特に困難 |
| Episodic Factor Pricing | 比較的高い | 中程度 | 5本中では最も可能 |

最も学術的に自己完結しているのは **Episodic Factor Pricing**、テーマリスクモデルとして最も直接実装しやすいのは **Thematic Investing as Missing Factors** です。一方、**Allocating to Thematic Investments** は配分思想は明確ですが、本文だけでは最適化結果の完全再現に必要な仕様が不足しています。

5本を実務上つなぐ場合は、

$$
\boxed{
\text{テーマ定義}
\rightarrow
\text{純化}
\rightarrow
\text{coherence検定}
\rightarrow
\text{attention signal}
\rightarrow
\text{pricing-state判定}
\rightarrow
\text{拡張リスクモデルによる配分}
}
$$

という順序が最も整合的です。

## Prompt:
2026/7/22 23:43:35

各ドキュメントについて内容をそれぞれ再現できる粒度で解説して。特に手法については定式化を含むこと

[Attachment: THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf]

[Attachment: Factor Momentum and the Momentum Factor.pdf]

[Attachment: Factor Momentum Everywhere(2).pdf]

[Attachment: Factor Momentum.pdf]

## Response:
2026/7/22 23:43:37

> **パーソナライズ中**
>
>
> **パーソナライズし、レビュー形式とデータ焦点を確認**
>
> 
>
> 11m 38s考えました

# 対象ドキュメントと位置づけ

今回は、添付された以下の4本を対象とします。

| ドキュメント | 中心的な問い | 主たる手法 | 投資実務上の用途 |
|---|---|---|---|
| **THEME: Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics** | テーマ文と銘柄を意味的に結びつけ、さらに短期リターン情報を加えて銘柄検索できるか | LoRA、contrastive learning、triplet loss | テーマ・ユニバース生成、テーマ内銘柄ランキング |
| **Factor Momentum and the Momentum Factor** | 個別株モメンタムは、他のファクターのモメンタムの集約ではないか | 二値型TSFM、PCファクター、momentum-neutral factor | ファクター・タイミング、株式モメンタムの発生源分析 |
| **Factor Momentum Everywhere** | より広範なファクター群を、連続的なシグナルでタイミングできるか | ボラティリティ調整TSFM、CSFM | 実装可能なファクター・アロケーション |
| **Factor Momentum** | 短期の業種モメンタムはファクター・モメンタムで説明できるか | 1か月CSFM、industry-neutral factor、systematic industry | 業種・テーマバスケットのファクター複製とタイミング |

以下では、論文に明記された仕様と、再現に必要だが論文中で不足している仕様を区別します。数式番号は説明のために付け直しています。

---

# 1. THEME: Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics

## 1.1 研究目的

THEMEは、テーマ投資における二つの問題を同時に扱います。

第一は、一般的な埋め込みモデルでは、金融資産間のテーマ上の関係を十分に表現できないことです。第二は、企業のテーマ関連性が固定的ではなく、企業戦略、ニュース、規制、市場動向に応じて変化することです。

そこで本論文は、

1. テーマのテキストと、その構成銘柄のテキストを意味的に近づける。
2. 過去リターンを使って、同一テーマ内で将来リターンが相対的に高い銘柄をテーマに近づける。

という二段階の学習を行います。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

ページ3のFigure 2では、ユーザーのテーマ記述を埋め込み、事前計算された銘柄埋め込みとの類似度検索を行い、上位銘柄をポートフォリオ候補として返す実務フローが示されています。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

---

## 1.2 データ構造：Thematic Representation Set

テーマ集合を

$$
\mathcal T=\{t_1,\ldots,t_M\},
$$

銘柄集合を

$$
\mathcal S=\{s_1,\ldots,s_N\}
$$

とします。

テーマ $i$ と銘柄 $j$ の関係を

$$
A_{ij}
=
\begin{cases}
1,&\text{銘柄 }j\text{ がテーマ }i\text{ の構成銘柄}\\
0,&\text{その他}
\end{cases}
$$

で表します。

TRSは、各テーマについて少なくとも次を持つデータセットです。

$$
\text{TRS record}
=
(\text{theme label},
\text{theme description},
\text{constituent stocks}).
$$

論文の出発点は1,153の実在テーマETFです。ETFのテーマ記述と構成銘柄に加え、業種・セクター分類を利用して約200テーマへ拡張します。各銘柄のテキストプロファイルはSEC開示と金融ニュースを集約して作り、一つの銘柄が複数テーマに所属することを許容します。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

実験時の具体的なデータ構成は次のとおりです。

- テーマETF：1,153本
- 対象米国株：約3,000銘柄
- 構成銘柄10銘柄未満のETFを除外
- 残存ETF：969本
- 学習：678
- 検証：97
- テスト：194
- TRS拡張後の学習テーマ：196
- temporal stageの価格履歴：約2年
- 過去リターン窓：60営業日
- 将来リターン窓：14営業日

`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

### 再現に必要な入力

| 入力 | 頻度 | 時点管理 |
|---|---:|---|
| ETFテーマ名・説明文 | ETF組成時点 | point-in-time |
| ETF構成銘柄 | 各リバランス時点 | point-in-time必須 |
| SEC文書 | 文書公表日 | 将来文書を混入させない |
| 金融ニュース | 記事公開時刻 | 検索時点以前のみ |
| 個別株調整後価格 | 日次 | delisting・corporate action処理 |
| セクター・業種分類 | 月次またはイベント時 | 過去時点の分類を保存 |

特に、ETFの「最新構成銘柄」を過去時点へ遡及利用すると、明確なlook-ahead biasになります。

---

## 1.3 Stage 1：テーマと銘柄の意味的整合

### 基礎モデル

事前学習済みテキスト埋め込みモデルを

$$
f_\Phi(\cdot)
$$

とします。基礎パラメータ $\Phi$ は固定し、LoRAパラメータ $\theta$ のみを学習します。

LoRA適用後のモデルを

$$
f'_\theta(\cdot)
$$

と表します。

テーマ記述 $t_i$ と銘柄プロファイル $s_j$ をそれぞれ

$$
z_i=f'_\theta(t_i)\in\mathbb R^d,
$$

$$
h_j=f'_\theta(s_j)\in\mathbb R^d
\tag{1}
$$

へ変換します。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

通常は類似度計算前に

$$
\widetilde z_i=\frac{z_i}{\|z_i\|_2},
\qquad
\widetilde h_j=\frac{h_j}{\|h_j\|_2}
$$

と正規化し、

$$
\operatorname{sim}(z_i,h_j)
=
\frac{z_i'h_j}{\|z_i\|_2\|h_j\|_2}
$$

をcosine similarityとして使います。

---

### 正例と負例

テーマ $i$ をanchorとし、

- 正例：$A_{ij}=1$ の構成銘柄
- 負例：$A_{ik}=0$ の非構成銘柄

を使います。

正例銘柄を $h_j^+$、負例集合を $\mathcal N_i$ とすると、論文のsemantic alignment lossは

$$
\mathcal L_{\mathrm{align}}
=
-
\log
\frac{
\exp\left(
\operatorname{sim}(z_i,h_j^+)/\tau
\right)
}{
\exp\left(
\operatorname{sim}(z_i,h_j^+)/\tau
\right)
+
\sum_{k\in\mathcal N_i}
\exp\left(
\operatorname{sim}(z_i,h_k^-)/\tau
\right)
}.
\tag{2}
$$

$\tau>0$ はtemperatureです。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

ミニバッチ全体では

$$
\widehat{\mathcal L}_{\mathrm{align}}
=
\frac{1}{|\mathcal B|}
\sum_{(i,j)\in\mathcal B}
\mathcal L_{\mathrm{align}}(i,j)
\tag{3}
$$

を最小化します。

### 経済的意味

この段階では、リターンはまだ使用しません。学習するのは

> テーマ $i$ の事業・技術・産業上の意味に、銘柄 $j$ がどれだけ近いか

です。

したがって、Stage 1出力はテーマの**構造的エクスポージャ**に相当します。

---

## 1.4 Stage 2：短期リターンによるTemporal Refinement

ページ4のFigure 3は、Stage 1のsemantic embeddingへ過去リターン情報を融合する二段階構造を示しています。事前学習モデルは固定、LoRAと後段adapterが学習対象です。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

### 過去リターン系列

時点 $t$ における銘柄 $j$ の過去 $L$ 日リターンを

$$
\mathbf r_{j,t}^{(L)}
=
\left(
r_{j,t-L+1},\ldots,r_{j,t}
\right)'
\in\mathbb R^L
\tag{4}
$$

とします。

論文では

$$
L=60
$$

です。

### Fusion adapter

2層adapterを

$$
A_\phi(\cdot,\cdot)
$$

とし、semantic embeddingと過去リターンを融合します。

$$
h'_{j,t}
=
A_\phi
\left(
h_j,\mathbf r_{j,t}^{(L)}
\right).
\tag{5}
$$

論文は「2-layer adapter」と記載しますが、

- 各層の次元
- 活性化関数
- return encoder
- layer normalization
- dropout
- semantic embeddingとreturn vectorの結合方法

は明示していません。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

---

### 将来リターンラベル

銘柄 $j$ の将来 $H$ 日累積リターンを

$$
G_{j,t}^{(H)}
=
\prod_{\ell=1}^{H}
(1+r_{j,t+\ell})
-1
\tag{6}
$$

とします。

論文では

$$
H=14
$$

です。

テーマ $i$ に属する二銘柄 $p,n$ を抽出し、

$$
G_{p,t}^{(H)}>G_{n,t}^{(H)}
$$

なら、

- $p$：positive stock
- $n$：negative stock

とします。

ここでpositive／negativeはテーマとの関係の有無ではなく、**同じテーマ構成銘柄内での将来リターンの大小**です。

---

### Triplet loss

テーマembedding $z_i$ をanchorとして、

$$
\mathcal L_{\mathrm{triplet}}
=
\left[
\operatorname{sim}(z_i,h'_{n,t})
-
\operatorname{sim}(z_i,h'_{p,t})
+
m
\right]_+,
\tag{7}
$$

$$
[x]_+=\max(x,0)
$$

を最小化します。

目的は

$$
\operatorname{sim}(z_i,h'_{p,t})
\ge
\operatorname{sim}(z_i,h'_{n,t})+m
$$

とすることです。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

したがって、最終embeddingは純粋なテーマ関連度ではなく、

$$
\text{semantic relevance}
+
\text{recent-return-conditioned ranking}
$$

を混合した表現です。

---

## 1.5 推論

ユーザー入力のテーマ記述を $q$ とすると、

$$
z_q=f'_\theta(q).
\tag{8}
$$

各銘柄の時点 $t$ のスコアを

$$
Score_{j,t}(q)
=
\operatorname{sim}
\left(
z_q,h'_{j,t}
\right)
\tag{9}
$$

とし、降順にランキングします。

上位 $K$ 銘柄集合は

$$
\mathcal P_t^{(K)}(q)
=
\operatorname{TopK}_{j}
Score_{j,t}(q).
\tag{10}
$$

この集合をテーマ・スクリーニング、指数設計、ポートフォリオ構築に用います。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

---

## 1.6 検索性能の評価

テーマクエリ $i$ の真の関連銘柄集合を $\mathcal R_i$、検索上位 $K$ を $\widehat{\mathcal R}_{i,K}$ とします。

### Hit Rate

$$
HR@K
=
\frac{1}{M_{\mathrm{test}}}
\sum_{i=1}^{M_{\mathrm{test}}}
\mathbf 1
\left\{
\left|
\mathcal R_i
\cap
\widehat{\mathcal R}_{i,K}
\right|
\ge1
\right\}.
\tag{11}
$$

### Precision

$$
P@K
=
\frac{1}{M_{\mathrm{test}}}
\sum_{i=1}^{M_{\mathrm{test}}}
\frac{
\left|
\mathcal R_i
\cap
\widehat{\mathcal R}_{i,K}
\right|
}{K}.
\tag{12}
$$

評価対象は

$$
K\in\{3,5,10\}
$$

です。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

例えばLinq-Embed-Mistralでは、

- $HR@3:0.5155\rightarrow0.8196$
- $P@3:0.3522\rightarrow0.6289$

へ改善しています。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

---

## 1.7 ポートフォリオ評価

時点 $t$ に検索された上位 $K$ 銘柄を等ウェイトします。

$$
w_{j,t}
=
\begin{cases}
1/K,&j\in\mathcal P_t^{(K)},\\
0,&\text{otherwise}.
\end{cases}
\tag{13}
$$

翌日から14営業日のポートフォリオ日次リターンは

$$
r_{p,t+h}
=
\frac1K
\sum_{j\in\mathcal P_t^{(K)}}r_{j,t+h},
\qquad h=1,\ldots,14.
\tag{14}
$$

論文のテスト期間は2024年4月23日から2025年4月29日で、各検索窓の後続14日リターンを連結して日次系列を作ります。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

評価指標は

$$
CR_T
=
\prod_{t=1}^{T}(1+r_{p,t})-1,
\tag{15}
$$

$$
SR
=
\frac{\overline r_p}{\sigma(r_p)}
\sqrt{252},
\tag{16}
$$

$$
MDD
=
\min_t
\left[
\frac{V_t}{\max_{s\le t}V_s}-1
\right].
\tag{17}
$$

`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

gte-Qwen2-7B-instructの上位3銘柄では、

- Sharpe：0.5014から0.7592
- 累積リターン：9.17%から16.45%
- MDD：-24.27%から-23.78%

へ改善しています。`THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf`

---

## 1.8 再現アルゴリズム

```text
1. ETFごとにpoint-in-timeのテーマ説明と構成銘柄を収集する
2. ETF・業種分類・ニュースからTRSを構築する
3. 各銘柄について、当該時点以前のSEC文書とニュースを集約する
4. 基礎embedding modelを固定し、LoRAだけをStage 1で学習する
5. theme-stock正例とnon-member負例でInfoNCE lossを最小化する
6. Stage 1のstock embeddingを固定または低学習率で保持する
7. 過去60日リターンをadapterへ入力する
8. 同一テーマ内の銘柄ペアを14日先リターンで順序付けする
9. triplet lossでadapterを学習する
10. 推論時点では、過去60日までの情報だけでfusion embeddingを作る
11. query-themeとのcosine similarityでtop-Kを選ぶ
12. 翌営業日から14日間等ウェイト保有する
```

---

## 1.9 完全再現できない部分

PDFだけでは、次が不足しています。

- LoRA rank、alpha、dropout、target module
- optimizer、learning rate、batch size、epoch数
- temperature $\tau$
- triplet margin $m$
- 負例数とhard-negative sampling
- return vectorの標準化方法
- 2層adapterの隠れ次元と活性化関数
- テキストの最大長、文書集約、pooling方法
- 14日窓を何日間隔で開始するか
- 重複する14日ポートフォリオをどのように統合するか
- 取引費用、turnover、corporate action
- ETF構成のpoint-in-time履歴

したがって、**手法の構造的再現は可能ですが、Table 1・2の数値完全再現はPDF単体では不可能**です。

また、ETF単位のランダム分割では、同一銘柄や近似テーマがtrainとtestの双方へ入る可能性があります。再現時には、

$$
\text{stock overlap},
\quad
\text{theme-semantic overlap},
\quad
\text{ETF-family overlap}
$$

を別途監査すべきです。

---

# 2. Factor Momentum and the Momentum Factor

## 2.1 中心仮説

本論文の主張は、

> 個別株モメンタムは独立したファクターではなく、複数の既存ファクターの自己相関を動的にタイミングした結果である

というものです。

多くのファクターは正の自己相関を持ち、過去1年間がプラスだったファクターの翌月リターンは、過去1年間がマイナスだった場合より高くなります。さらに、高固有値PCファクターのモメンタムが個別株モメンタムを説明すると結論づけます。`Factor Momentum and the Momentum Factor.pdf`

---

## 2.2 Off-the-shelf factorデータ

データ源は、

- Kenneth French Data Library
- AQR
- Stambaugh

です。

15の米国ファクターと7つの米国外ファクター、合計22本を使います。ファクターリターンが直接提供されない場合は、原論文に準拠して上位3十分位平均から下位3十分位平均を引きます。`Factor Momentum and the Momentum Factor.pdf`

stock momentumとの機械的重複を避けるため、米国・グローバルmomentum factorを除き、主戦略では最大20ファクターを取引します。

---

## 2.3 ファクター自己相関の検定

ファクター $k$ の過去12か月リターンを

$$
M_{k,t}^{12}
=
\sum_{\ell=1}^{12}f_{k,t-\ell}
\tag{18}
$$

とし、

$$
D_{k,t}
=
\mathbf1
\left\{
M_{k,t}^{12}>0
\right\}
\tag{19}
$$

を定義します。

将来ファクターリターンについて、

$$
f_{k,t}
=
\alpha_k
+
\beta_kD_{k,t}
+
\varepsilon_{k,t}
\tag{20}
$$

を推定します。

- $\alpha_k$：過去1年間がマイナスだった後の平均リターン
- $\alpha_k+\beta_k$：過去1年間がプラスだった後の平均リターン

です。

20の非momentum factorをプールした結果は、

$$
\widehat\alpha=0.06\%\text{/月},
$$

$$
\widehat\beta=0.45\%\text{/月},
$$

したがって

$$
E[f_t\mid M^{12}>0]
=
0.51\%\text{/月}
$$

です。プール回帰の標準誤差は月でclusterします。`Factor Momentum and the Momentum Factor.pdf`

---

## 2.4 二値型Time-series Factor Momentum

利用可能なファクター数を $K_t$ とし、

$$
s_{k,t}
=
\operatorname{sign}
\left(
M_{k,t}^{12}
\right)
\in\{-1,+1\}
\tag{21}
$$

とします。

論文の説明およびTable 3のスケールと整合する戦略リターンは

$$
R_{t+1}^{TSFM}
=
\frac{1}{K_t}
\sum_{k=1}^{K_t}
s_{k,t}f_{k,t+1}.
\tag{22}
$$

です。

この仕様では、全ファクターを等しい絶対ウェイト $1/K_t$ で保有し、符号だけを変更します。正シグナルの本数と負シグナルの本数が異なるため、ファクター空間でのネットエクスポージャは必ずしもゼロになりません。

例えば正シグナルが11、負シグナルが6なら、戦略は正方向へネットロングです。論文も、TSFMは平均的にロング11、ショート6と記載しています。`Factor Momentum and the Momentum Factor.pdf`

結果は、

- 年率リターン：3.92%
- 年率標準偏差：4.16%
- Sharpe：0.94
- $t=7.01$

です。`Factor Momentum and the Momentum Factor.pdf`

---

## 2.5 Cross-sectional Factor Momentum

月 $t$ における過去12か月リターンの中央値を

$$
m_t
=
\operatorname{median}_{k}
M_{k,t}^{12}
$$

とします。

$$
c_{k,t}
=
\begin{cases}
+1,&M_{k,t}^{12}>m_t,\\
-1,&M_{k,t}^{12}\le m_t.
\end{cases}
\tag{23}
$$

戦略リターンは

$$
R_{t+1}^{CSFM}
=
\frac{1}{K_t}
\sum_{k=1}^{K_t}
c_{k,t}f_{k,t+1}.
\tag{24}
$$

ファクター数が偶数で上下同数なら、

$$
R_{t+1}^{CSFM}
=
\frac12
\left(
\overline f_{W,t+1}
-
\overline f_{L,t+1}
\right).
\tag{25}
$$

論文の脚注も、cross-sectional strategyの平均リターンがwinnerとloserの差の半分であると説明しています。`Factor Momentum and the Momentum Factor.pdf`

結果は、

- 年率リターン：2.40%
- 標準偏差：3.55%
- Sharpe：0.68
- $t=5.04$

です。

---

## 2.6 なぜTSFMがCSFMを上回るか

論文は分析用に連続ウェイトを導入します。この連続ウェイトは主戦略の二値ウェイトとは別物です。

過去リターンを $r_{k,-t}$、その横断面平均を $\bar r_{-t}$ とすると、

$$
w_{k,t}^{CS}
=
r_{k,-t}-\bar r_{-t}.
\tag{26}
$$

収益は

$$
\pi_{k,t}^{CS}
=
(r_{k,-t}-\bar r_{-t})r_{k,t}.
\tag{27}
$$

ファクター数を $K$、過去・将来リターンのcross-autocovariance matrixを

$$
\Omega
=
E
\left[
(\mathbf r_{-t}-\boldsymbol\mu)
(\mathbf r_t-\boldsymbol\mu)'
\right]
$$

とすると、

$$
E[\pi_t^{CS}]
=
\frac{1}{K}\operatorname{Tr}(\Omega)
-
\frac{1}{K^2}
\mathbf1'\Omega\mathbf1
+
\sigma_\mu^2.
\tag{28}
$$

これは

$$
E[\pi_t^{CS}]
=
\underbrace{
\frac{K-1}{K^2}\operatorname{Tr}(\Omega)
}_{\text{own-factor autocovariance}}
-
\underbrace{
\frac{1}{K^2}
\left[
\mathbf1'\Omega\mathbf1-\operatorname{Tr}(\Omega)
\right]
}_{\text{cross-factor serial covariance}}
+
\underbrace{\sigma_\mu^2}_{\text{factor mean dispersion}}
\tag{29}
$$

と分解できます。`Factor Momentum and the Momentum Factor.pdf`

一方、time-series連続ウェイトは

$$
w_{k,t}^{TS}=r_{k,-t}
$$

なので、

$$
E[\pi_t^{TS}]
=
\frac1K\operatorname{Tr}(\Omega)
+
\frac1K
\sum_{k=1}^{K}\mu_k^2.
\tag{30}
$$

`Factor Momentum and the Momentum Factor.pdf`

実証分解は次のとおりです。

| 戦略 | 構成要素 | 年率寄与 |
|---|---|---:|
| CSFM | own autocovariance | +2.54% |
|  | cross-serial covariance | -1.00% |
|  | mean dispersion | +0.48% |
|  | 合計 | 2.16% |
| TSFM | own autocovariance | +2.67% |
|  | squared means | +1.76% |
|  | 合計 | 4.51% |

`Factor Momentum and the Momentum Factor.pdf`

CSFMは必ず相対的winnerを買い、relative loserを売ります。しかし、全ファクターの期待リターンが正になる局面では、relative loserも正の将来リターンを持ち得ます。そのため、CSFMは不必要にショートを作ります。

---

## 2.7 Formation periodとholding period

形成期間 $J$、保有期間 $H$ を1か月から24か月まで変化させます。

$H>1$ の場合は、重複コホートを

$$
R_t^{(J,H)}
=
\frac1H
\sum_{h=1}^{H}
R_{t-h,t}^{(J)}
\tag{31}
$$

として平均します。

これは、月 $t-H,\ldots,t-1$ に形成した $H$ 個のポートフォリオの当月リターンを等ウェイトするJegadeesh-Titman方式です。`Factor Momentum and the Momentum Factor.pdf`

論文では、TSFMもCSFMも保有期間1か月で最も強くなります。

---

## 2.8 高固有値PCファクター

### 個別特性ファクターの構築

特性 $c_{i,j,t}$ を月次横断面順位へ変換します。

$$
q_{i,j,t}
=
\frac{
\operatorname{rank}(c_{i,j,t})
}{
n_t+1
}.
\tag{32}
$$

これを中心化・gross normalizationします。

$$
w_{i,j,t}
=
\frac{
q_{i,j,t}-\bar q_{j,t}
}{
\sum_{\ell=1}^{n_t}
|q_{\ell,j,t}-\bar q_{j,t}|
}.
\tag{33}
$$

したがって、

$$
\sum_iw_{i,j,t}=0,
\qquad
\sum_i|w_{i,j,t}|=1.
$$

特性が欠損の場合は $w_{i,j,t}=0$ とします。

翌月ファクターリターンは

$$
f_{j,t+1}
=
\sum_iw_{i,j,t}r_{i,t+1}.
\tag{34}
$$

54特性からmomentum関連7特性を除き、47ファクターを使います。また、時価総額が市場全体の0.01%未満の超小型株を除きます。`Factor Momentum and the Momentum Factor.pdf`

---

### OOS PCA

月末 $t$ において、日次47ファクターリターンの拡大型相関行列を

$$
C_t
=
\operatorname{Corr}
\left(
\mathbf f_d;\ d\le t
\right)
$$

とします。

固有値分解は

$$
C_t
=
V_t\Lambda_tV_t'.
\tag{35}
$$

第 $k$ 主成分の月次リターンは

$$
p_{k,\tau|t}
=
v_{k,t}'\mathbf f_\tau.
\tag{36}
$$

月 $t+1$ のリターンも、月末 $t$ までに推定した同じ $v_{k,t}$ で計算します。

次に、月末 $t$ までの平均を除き、PCファクターの分散を元ファクターの平均分散へ合わせます。

$$
\widetilde p_{k,\tau|t}
=
a_{k,t}
\left(
p_{k,\tau|t}
-
\bar p_{k,t}
\right),
\tag{37}
$$

$$
a_{k,t}
=
\sqrt{
\frac{
K^{-1}\sum_{j=1}^{K}
\widehat{\operatorname{Var}}_t(f_j)
}{
\widehat{\operatorname{Var}}_t(p_k)
}
}.
\tag{38}
$$

式(37)-(38)は、論文の「平均をゼロにし、元ファクターの平均分散へleverする」という記述を実装式にしたものです。手順自体は論文に明記されています。`Factor Momentum and the Momentum Factor.pdf`

PC momentum signalは

$$
M_{k,t}^{PC}
=
\frac1{12}
\sum_{\ell=0}^{11}
\widetilde p_{k,t-\ell|t}
\tag{39}
$$

です。

$$
R_{t+1}^{PCFMOM}
=
\frac1K
\sum_k
\operatorname{sign}
(M_{k,t}^{PC})
\widetilde p_{k,t+1|t}.
\tag{40}
$$

過去シグナルと将来リターンを同じ月末 $t$ のrotationで計算することが重要です。最低10年のデータを要求するため、PC戦略は1973年7月から始まります。`Factor Momentum and the Momentum Factor.pdf`

固有ベクトルの符号は任意ですが、過去・将来を同じベクトルで評価すれば、

$$
v\rightarrow-v
$$

によりシグナルと将来PCリターンが同時に反転するため、戦略リターンは不変です。

---

## 2.9 個別株モメンタムへの伝播

個別株リターンを

$$
R_{i,t}
=
\sum_{k=1}^{K}
\beta_i^kf_{k,t}
+
\varepsilon_{i,t}
\tag{41}
$$

とします。

線形な個別株モメンタム戦略の期待収益は、論文の分解を整理すると

$$
\begin{aligned}
E[\pi_t^{stockmom}]
=&
\sum_{k=1}^{K}
\operatorname{Cov}(f_{k,-t},f_{k,t})
\operatorname{Var}(\beta^k)
\\
&+
\sum_{k\ne l}
\operatorname{Cov}(f_{k,-t},f_{l,t})
\operatorname{Cov}(\beta^k,\beta^l)
\\
&+
\frac1N\sum_i
\operatorname{Cov}(\varepsilon_{i,-t},\varepsilon_{i,t})
+
\operatorname{Var}(\mu_i).
\end{aligned}
\tag{42}
$$

第一項が特に重要です。

$$
\text{stock momentum}
\propto
\text{factor autocorrelation}
\times
\text{cross-sectional beta dispersion}.
$$

同じファクターへ全銘柄が同じbetaを持つなら、そのファクターのモメンタムは銘柄横断面へ伝播しません。銘柄ごとのbeta差が大きいほど、ファクター・モメンタムが個別株winner-loser差として表れます。

---

## 2.10 Residual momentumとomitted-factor problem

研究者が真のモデル

$$
R_{i,t}
=
\beta_{i,1}F_{1,t}
+
\beta_{i,2}F_{2,t}
+
\varepsilon_{i,t}
$$

のうち $F_1$ しか認識していない場合、推定残差は

$$
\widehat\varepsilon_{i,t}
=
R_{i,t}-\beta_{i,1}F_{1,t}
=
\beta_{i,2}F_{2,t}
+
\varepsilon_{i,t}.
\tag{43}
$$

$F_2$ が自己相関を持てば、真の固有リターンがIIDでも推定残差はモメンタムを示します。

実証では、

- beta推定：$t-72$ から $t-13$
- 最低36か月
- residual momentum signal：$t-12$ から $t-2$
- size×residual momentumの2×3ポートフォリオ

を使います。

平均月次リターンは、

- raw return momentum：0.45%
- CAPM residual：0.58%
- FF3 residual：0.44%
- FF5 residual：0.37%

ですが、高固有値PC factor momentumを制御すると全てのalphaがほぼゼロになります。

---

## 2.11 Momentum-neutral factor

元のファクター銘柄ウェイトを $\mathbf w_t$、各銘柄の過去リターンを

$$
\mathbf r_t^{mom}
=
(r_{1,t-12:t-2},\ldots,r_{N,t-12:t-2})'
$$

とします。

新ウェイト $\mathbf x_t$ を

$$
\min_{\mathbf x_t}
\|\mathbf x_t-\mathbf w_t\|_2^2
\tag{44}
$$

subject to

$$
\mathbf1'\mathbf x_t=0,
\tag{45}
$$

$$
(\mathbf r_t^{mom})'\mathbf x_t=0
\tag{46}
$$

として求めます。

これは、元ファクターから個別株モメンタム・エクスポージャだけを最小変更で除去する処理です。`Factor Momentum and the Momentum Factor.pdf`

行列

$$
Z_t=
[\mathbf1,\mathbf r_t^{mom}]
$$

を使えば、解は射影残差として

$$
\boxed{
\mathbf x_t
=
\left[
I
-
Z_t(Z_t'Z_t)^{-1}Z_t'
\right]
\mathbf w_t
}
\tag{47}
$$

です。

これは横断面回帰

$$
w_{i,t}
=
a_t+b_tr_{i,t-12:t-2}+x_{i,t}
\tag{48}
$$

の残差と一致します。`Factor Momentum and the Momentum Factor.pdf`

momentum-neutral factorから抽出した高固有値PCのFMOMは、元ファクターのFMOMより強く、FF5 alphaの $t$ 値は7.53です。`Factor Momentum and the Momentum Factor.pdf`

---

## 2.12 シミュレーション

対称ファクター仕様では、

- 2,000銘柄
- 672か月
- 10ファクター
- 銘柄固有ショックはIID
- ファクター期待リターンはAR(1)
- beta平均0、分散1
- AR係数 $\kappa=0.9$
- 銘柄分散の40%をファクター、60%を固有リターン
- ファクター分散の5%を時変プレミアム、95%をファクターショック

とします。

$$
\lambda_{k,t}
=
\kappa\lambda_{k,t-1}
+
\omega_{k,t},
\tag{49}
$$

$$
f_{k,t}
=
\lambda_{k,t}
+
\eta_{k,t},
\tag{50}
$$

$$
R_{i,t}
=
\sum_k\beta_i^kf_{k,t}
+
\varepsilon_{i,t}.
\tag{51}
$$

ショック分散は

$$
\sigma_\varepsilon^2=0.6,
\qquad
\sigma_\omega^2=0.00038,
\qquad
\sigma_\eta^2=0.038.
$$

`Factor Momentum and the Momentum Factor.pdf`

真の固有リターンに自己相関がなくても、認識するファクター数が少ないとresidual momentumが有意になります。全10ファクターをモデルへ含めるとresidual momentumは消滅します。

---

## 2.13 再現の判定基準

| 中間出力 | 論文の目標値 |
|---|---:|
| 過去1年negative後の平均factor return | 0.06%/月 |
| positive後 | 0.51%/月 |
| binary TSFM | 年率3.92%、$t=7.01$ |
| binary CSFM | 年率2.40%、$t=5.04$ |
| PC 1-10 FMOM | 0.19%/月、$t\approx7.1$ |
| Momentum-neutral PC FMOM alpha $t$ | 7.53 |
| UMD alpha after PC1-10 FMOM | 約ゼロ |

完全再現では、公表ファクターデータの改訂版差、PC用日次47ファクター、各銘柄のpoint-in-time特性が主な障害です。

---

# 3. Factor Momentum Everywhere

## 3.1 Ehsani-Linnainmaaとの違い

本論文はファクター・モメンタムを、単なる

$$
+1/-1
$$

ではなく、過去リターンをボラティリティで割った**連続シグナル**で実装します。

また、

- 65ファクター
- 米国以外への拡張
- 複数形成期間
- turnoverと取引費用
- stock momentumやvalueとの組合せ

まで検証しています。論文のcombined TSFMの年率Sharpeは0.84です。`Factor Momentum Everywhere(2).pdf`

---

## 3.2 65ファクターの構築

各月、特性値を上下1% winsorizeします。

米国ではNYSE時価総額中央値でSmall／Largeへ分けます。各size group内で特性を

- Low：下位30%
- Middle：中央40%
- High：上位30%

に分けます。

国際株ではsize cutoffに時価総額80パーセンタイルを使います。`Factor Momentum Everywhere(2).pdf`

各6ポートフォリオを時価加重し、

$$
f_{j,t}
=
\frac12
\left(
R_{Large,High,t}
+
R_{Small,High,t}
\right)
-
\frac12
\left(
R_{Large,Low,t}
+
R_{Small,Low,t}
\right).
\tag{52}
$$

各ファクターは、原論文で予測される期待リターン方向が正となるよう、符号を固定します。これはサンプル内平均でre-signする処理ではありません。`Factor Momentum Everywhere(2).pdf`

---

## 3.3 ファクター自己相関

各ファクターについて

$$
f_{i,t}
=
a_i+\rho_if_{i,t-1}+u_{i,t}
\tag{53}
$$

を推定します。

結果は、

- 65本中59本で $\widehat\rho_i>0$
- 49本で5%有意
- 平均AR(1)：0.11

です。`Factor Momentum Everywhere(2).pdf`

---

## 3.4 連続型TSFM signal

ファクター $i$、形成期間 $j$ について、

$$
M_{i,j,t}
=
\sum_{\tau=1}^{j}
f_{i,t-\tau+1}.
\tag{54}
$$

ボラティリティを

$$
\sigma_{i,j,t}
$$

とします。論文の仕様は、

$$
\sigma_{i,j,t}
=
\begin{cases}
\text{過去3年の年率ボラティリティ},&j<12,\\
\text{過去10年の年率ボラティリティ},&j\ge12.
\end{cases}
\tag{55}
$$

シグナルは

$$
s_{i,j,t}
=
\operatorname{clip}
\left(
\frac{M_{i,j,t}}{\sigma_{i,j,t}},
-2,2
\right).
\tag{56}
$$

タイミング済みファクターリターンは

$$
f_{i,j,t+1}^{TS}
=
s_{i,j,t}f_{i,t+1}.
\tag{57}
$$

です。`Factor Momentum Everywhere(2).pdf`

論文の式では形成期間のリターンを $\sqrt j$ 等で追加調整しません。再現では式(56)をそのまま使う必要があります。

---

## 3.5 Long legとShort legの正規化

正シグナル集合を

$$
\mathcal L_t
=
\{i:s_{i,j,t}>0\},
$$

負シグナル集合を

$$
\mathcal S_t
=
\{i:s_{i,j,t}\le0\}
$$

とします。

$$
A_t^+
=
\sum_{i\in\mathcal L_t}s_{i,j,t},
$$

$$
A_t^-
=
-\sum_{i\in\mathcal S_t}s_{i,j,t}>0.
$$

最終ウェイトは

$$
w_{i,j,t}
=
\begin{cases}
\dfrac{s_{i,j,t}}{A_t^+},&
i\in\mathcal L_t,\\[8pt]
\dfrac{s_{i,j,t}}{A_t^-},&
i\in\mathcal S_t.
\end{cases}
\tag{58}
$$

負集合では $s_i<0$ なので、ウェイトも負です。

したがって、

$$
\sum_{i\in\mathcal L_t}w_{i,j,t}=1,
$$

$$
\sum_{i\in\mathcal S_t}w_{i,j,t}=-1.
$$

最終リターンは

$$
R_{j,t+1}^{TSFM}
=
\sum_iw_{i,j,t}f_{i,t+1}.
\tag{59}
$$

これは

- long 1ドル
- short 1ドル
- net 0
- gross 2

です。論文も各レッグをunit leverageへ再調整すると明記しています。`Factor Momentum Everywhere(2).pdf`

これはEhsani-Linnainmaaの式(22)とは異なります。Ehsani-Linnainmaaは全ファクターを同じ絶対ウェイトで保有するため、ネットが必ずしもゼロになりません。

---

## 3.6 個別ファクターのtiming alpha

ファクター $i$ のタイミング戦略が、単なる当該ファクターのpassive exposureではないかを

$$
f_{i,j,t}^{TS}
=
\alpha_{i,j}
+
\beta_{i,j}f_{i,t}
+
e_{i,j,t}
\tag{60}
$$

で検証します。

1か月形成では、

- 65ファクター中61で $\widehat\alpha>0$
- 47で統計的有意

です。`Factor Momentum Everywhere(2).pdf`

---

## 3.7 形成期間

検証される形成窓は、

$$
1\text{-}1,\;
1\text{-}3,\;
1\text{-}6,\;
1\text{-}12,\;
1\text{-}36,\;
1\text{-}60,\;
2\text{-}12,\;
13\text{-}60.
$$

例えば、

$$
M_{i,2-12,t}
=
\sum_{\ell=2}^{12}f_{i,t-\ell+1},
$$

$$
M_{i,13-60,t}
=
\sum_{\ell=13}^{60}f_{i,t-\ell+1}.
$$

結果は、

| 形成期間 | 年率リターン | Sharpe |
|---|---:|---:|
| 1-1 | 約12.0% | 0.84 |
| 1-12 | 9.5% | 0.70 |
| 1-60 | 7.1% | 0.72 |
| 2-12 | - | 0.54 |
| 13-60 | - | 0.53 |

です。`Factor Momentum Everywhere(2).pdf`

株式モメンタムが1か月ではreversal、6-12か月でmomentum、長期ではreversalとなるのに対して、ファクターでは幅広い期間でcontinuationが残ります。

---

## 3.8 Cross-sectional Factor Momentum

形成リターンを横断面でdemeanします。

$$
\widetilde M_{i,j,t}
=
M_{i,j,t}
-
\frac1{K_t}
\sum_{k=1}^{K_t}M_{k,j,t}.
\tag{61}
$$

その後、

$$
s_{i,j,t}^{CS}
=
\operatorname{clip}
\left(
\frac{\widetilde M_{i,j,t}}
{\sigma_{i,j,t}},
-2,2
\right)
\tag{62}
$$

とし、式(58)と同じlong／short正規化を行います。

論文は「CSFMは形成期間リターンを横断面demeanし、それ以外はTSFMと同じ」と定義しています。`Factor Momentum Everywhere(2).pdf`

TSFMとCSFMの相関は極めて高く、

- 1-1：0.99
- 1-12：0.98
- 1-60：0.91
- 13-60：0.85

です。`Factor Momentum Everywhere(2).pdf`

ただしspanning regressionでは、

$$
R_t^{TSFM}
=
\alpha+\beta R_t^{CSFM}+\varepsilon_t
$$

の $\alpha$ は正である一方、逆回帰ではCSFMのalphaが負になる傾向があります。TSFMの方が、全ファクターが正になる局面を適切にロングできるためです。

---

## 3.9 株式・業種モメンタムとの関係

相関構造には形成期間依存性があります。

| Factor momentum | UMD | STR | Industry momentum |
|---|---:|---:|---:|
| TSFM 1-1 | 0.09 | -0.80 | 0.21 |
| TSFM 1-12 | 0.75 | -0.35 | 0.77 |
| TSFM 2-12 | 0.77 | -0.22 | 0.77 |
| TSFM 13-60 | 0.20 | -0.12 | 0.05 |

`Factor Momentum Everywhere(2).pdf`

1か月TSFMはstock short-term reversalと強い負相関を持ちます。したがって、短期ファクター継続と短期個別株反転は異なる現象です。

UMDは2-12 TSFMの一部を説明しますが、それ以外の形成期間ではTSFMに年率2%以上のalphaが残ります。`Factor Momentum Everywhere(2).pdf`

---

## 3.10 取引費用

月次turnoverを

$$
TO_t
=
\sum_i
|w_{i,t}-w_{i,t-1}|
\tag{63}
$$

とし、年率turnoverを

$$
TO_{\mathrm{ann}}
=
12\cdot\frac1T\sum_tTO_t
\tag{64}
$$

と定義します。

これはgross asset valueに対する、売買双方を含むtwo-sided volumeです。`Factor Momentum Everywhere(2).pdf`

取引費用はturnover 1単位あたり10bpです。

月次ネットリターンは

$$
R_{t}^{net}
=
R_t^{gross}
-
0.001\,TO_t.
\tag{65}
$$

1-12 TSFMは、

- Gross Sharpe：0.70
- Net Sharpe：0.63

です。UMDのNet Sharpeは0.51、FF5内で最大のRMWは0.45です。`Factor Momentum Everywhere(2).pdf`

### 注意

厳密な実務コストを計算するには、ファクター配分ウェイトだけでなく、

$$
\mathbf w_t^{stock}
=
W_t^{factor}\mathbf a_t^{factor}
$$

という個別株レベルの合成ウェイトを作り、ファクター間の売買をnettingしてからturnoverを計算すべきです。論文の簡略表現だけでは、factor-level turnoverかstock-level turnoverかが完全には明確ではありません。

---

## 3.11 国際検証

国際サンプルは、

- Europe
- Pacific
- Global ex-US＋Canada

です。

62ファクターについて、

- 平均AR(1)：0.10
- 51/62で正
- 30/62で有意
- TSFM Sharpe：0.73
- untimed EW factorに対する年率alpha：6.6%

です。`Factor Momentum Everywhere(2).pdf`

また、65の細かなファクターを

- valuation
- momentum
- earnings quality
- sustainable growth
- management
- risk

の6つの広範なtheme factorへ集約しても、factor momentumが再現されると報告しています。ただし、この検証は詳細結果が未報告です。`Factor Momentum Everywhere(2).pdf`

---

## 3.12 再現アルゴリズム

```text
1. 各特性をpoint-in-timeで構築し、上下1%をwinsorize
2. NYSE時価総額中央値でSmall/Large
3. 各size群内で特性を30/40/30分割
4. 各ポートフォリオを時価加重
5. 0.5*(LH+SH)-0.5*(LL+SL)で65ファクターを作る
6. 各ファクターの形成期間累積リターンを計算
7. j<12なら過去3年、j>=12なら過去10年のvolを推定
8. signal = clip(formation return / vol, -2, 2)
9. 正負各レッグを+1/-1へ正規化
10. 翌月ファクターリターンを適用
11. 個別株レベルへ展開してturnover・費用を計算
12. EW factor、FF5、UMD、INDMOM、STRに対してspanning test
```

### 再現上の不足

- 65特性の完全なpoint-in-time定義はAppendixと原論文群が必要
- 会計情報の具体的publication lag
- 各ファクターの月次／年次リバランス差
- ボラティリティ計算時の最低観測数
- 欠損ファクターを集約から除くか0とするか
- 個別株レベルの取引費用計算方法
- tangency portfolioはfull-sample ex postであり、OOS戦略ではない

---

# 4. Factor Momentum

## 4.1 研究目的

この論文は、特に**1か月の短期cross-sectional factor momentum**を扱います。

中心仮説は、

> 業種モメンタムは業種固有の自己相関ではなく、業種ごとに異なるファクターbetaを通じてファクター・モメンタムが伝播したものである

というものです。

さらに、

- industry-neutral factorにもmomentumがある。
- factorから作ったsystematic industryにもmomentumがある。
- 高固有値PC factor momentumがindustry momentumを説明する。

ことを示します。`Factor Momentum.pdf`

---

## 4.2 データと前処理

- CRSP：NYSE、AMEX、Nasdaq
- common share code：10、11
- CRSP delisting returnを使用
- performance-related delistingでreturn欠損時：
  - NYSE・AMEX：-30%
  - Nasdaq：-55%
- Compustat会計データは6か月lag
- ファクター期間：1963年7月-2020年12月
- ファクター数：43

momentum・short-term reversal関連の特性とindustry concentration factorは、識別上の重複を避けるため除外します。`Factor Momentum.pdf`

---

## 4.3 Standard factorとIndustry-neutral factor

各特性 $c_{i,t}$ について、NYSE時価総額中央値と30／70パーセンタイルによる2×3 independent sortを行います。

標準ファクターは

$$
f_t
=
\frac12
(R_{S,H,t}+R_{B,H,t})
-
\frac12
(R_{S,L,t}+R_{B,L,t}).
\tag{66}
$$

各ポートフォリオは時価加重です。

Industry-neutral factorでは、まず49業種内で特性をdemeanします。

$$
\widetilde c_{i,t}
=
c_{i,t}
-
\frac{
\sum_{j:g(j)=g(i)}
\omega_{j,t}c_{j,t}
}{
\sum_{j:g(j)=g(i)}
\omega_{j,t}
}.
\tag{67}
$$

論文は「cross-sectional industry average」を引くと記載しているため、厳密には等ウェイト平均を基本仕様とするのが安全です。

その後、$\widetilde c_{i,t}$ について同じ2×3 sortを行います。これにより、long・short legの業種配分が概ね一致します。`Factor Momentum.pdf`

---

## 4.4 短期Cross-sectional Factor Momentum

月 $t$ の43ファクターリターンの中央値を

$$
m_t=\operatorname{median}_{k}f_{k,t}
$$

とします。

winner・loser集合は

$$
\mathcal W_t=\{k:f_{k,t}>m_t\},
$$

$$
\mathcal L_t=\{k:f_{k,t}\le m_t\}.
$$

論文の「above-medianをlong、below-medianをshort」という記述と報告リターンのスケールに整合する実装は

$$
R_{t+1}^{FMOM}
=
\frac1{|\mathcal W_t|}
\sum_{k\in\mathcal W_t}f_{k,t+1}
-
\frac1{|\mathcal L_t|}
\sum_{k\in\mathcal L_t}f_{k,t+1}.
\tag{68}
$$

です。

- formation：1か月
- holding：1か月
- monthly rebalance
- gross 2
- net 0

となります。

結果は、

- 平均月次リターン：0.64%
- $t=6.11$
- FF5 alpha：0.70%、$t=6.60$
- FF5＋UMD alpha：0.66%、$t=6.12$
- FF5＋UMD＋12か月TSFM alpha：0.52%、$t=5.01$

です。`Factor Momentum.pdf`

この短期CSFMは、Ehsani-Linnainmaaの12か月TSFMとは別の現象です。

---

## 4.5 Industry momentum

20業種の時価加重リターンを $R_{j,t}^{ind}$ とし、

$$
\mathcal W_t^{ind}
=
\{j:R_{j,t}^{ind}>\operatorname{median}_lR_{l,t}^{ind}\},
$$

$$
\mathcal L_t^{ind}
=
\{j:R_{j,t}^{ind}\le\operatorname{median}_lR_{l,t}^{ind}\}.
$$

$$
R_{t+1}^{IMOM}
=
\overline R_{\mathcal W_t^{ind},t+1}^{ind}
-
\overline R_{\mathcal L_t^{ind},t+1}^{ind}.
\tag{69}
$$

1か月formation・1か月holdingのindustry momentumは、FF5＋UMDでも月次alpha 0.38%、$t=4.42$です。長期industry momentumはUMDでほぼ説明されます。`Factor Momentum.pdf`

---

## 4.6 Industry-neutral factorによる識別

「factor momentumは、factorが持つ業種betの結果にすぎない」という逆因果を排除するため、式(67)で作ったindustry-neutral factorについて同じFMOMを構築します。

結果は、

- 標準factor momentum FF5 alpha：0.70%、$t=6.60$
- industry-neutral factor momentum：0.62%、$t=6.88$

です。

industry momentumを右辺へ加えてもfactor momentumのalphaは残ります。一方、industry momentumのalphaは、

- FF5のみ：0.45%、$t=5.15$
- 標準FMOMを追加：0.08%、$t=1.16$
- industry-neutral FMOMを追加：0.07%、$t=1.03$

へ低下します。`Factor Momentum.pdf`

したがって、方向は

$$
\text{factor momentum}
\rightarrow
\text{industry momentum}
$$

であり、逆ではないと解釈されます。

---

## 4.7 ファクター・モメンタムの業種への伝播

業種 $j$ のリターンを

$$
R_{j,t}^{ind}
=
\boldsymbol\beta_{j,t}'\mathbf F_t
+
u_{j,t}
\tag{70}
$$

とします。

業種固有成分が自己相関を持たないと仮定すると、

$$
\operatorname{Cov}
(R_{j,t}^{ind},R_{j,t+1}^{ind})
=
\boldsymbol\beta_{j,t}'
\Omega_F
\boldsymbol\beta_{j,t},
\tag{71}
$$

$$
\Omega_F
=
\operatorname{Cov}(\mathbf F_t,\mathbf F_{t+1}).
$$

業種横断面におけるbetaの分散が大きいほど、

$$
\operatorname{Var}_j(\boldsymbol\beta_j)
$$

ファクター自己相関が業種winner-loser差として強く現れます。

---

## 4.8 業種betaの異質性の検証

日次market-adjusted industry returnを

$$
y_{j,d}
=
R_{j,d}^{ind}-R_{m,d}
$$

とします。

因子リターンを $\mathbf F_d$、業種dummyを $D_j$、四半期dummyを $Q_q$ として、最も一般的な仕様は

$$
\begin{aligned}
y_{j,d}
=&\alpha
+\boldsymbol\beta'\mathbf F_d
+\sum_jD_j\boldsymbol\gamma_j'\mathbf F_d
\\
&+\sum_qQ_q\boldsymbol\delta_q'\mathbf F_d
+\sum_{j,q}D_jQ_q\boldsymbol\eta_{j,q}'\mathbf F_d
+\varepsilon_{j,d}.
\end{aligned}
\tag{72}
$$

これにより、

1. 全業種・全期間でbeta一定
2. 時間だけ変化
3. 業種だけ変化
4. 業種・時間の双方で変化

を比較します。

Adjusted $R^2$ は次のように増加します。

| モデル | Static | 時間変化 | 業種変化 | 業種×時間変化 |
|---|---:|---:|---:|---:|
| FF3 | 1.4% | 3.6% | 12.7% | 28.8% |
| FF5 | 2.2% | 4.0% | 16.7% | 35.1% |
| 9-factor | 2.8% | 4.6% | 21.9% | 44.7% |

`Factor Momentum.pdf`

つまり、業種betaは横断面でも時系列でも大きく異なります。

---

## 4.9 Systematic industry

月末 $t$ に、直近3か月の日次データで各業種のfactor betaを推定します。

$$
R_{j,d}^{ind}
=
\alpha_{j,t}
+
\boldsymbol\beta_{j,t}'\mathbf F_d
+
e_{j,d},
\qquad
d\in\mathcal D_{t-2:t}.
\tag{73}
$$

systematic industry returnを

$$
R_{j,t'}^{sys}
=
\widehat{\boldsymbol\beta}_{j,t}'\mathbf F_{t'},
\qquad
t'\in\{t,t+1\}
\tag{74}
$$

と定義します。

- 月 $t$ のsystematic returnで業種をランキング
- 月 $t+1$ のsystematic returnで運用成績を評価

します。

同じ $\widehat\beta_{j,t}$ を月 $t$ と月 $t+1$ に使うため、月 $t+1$ はbeta推定に対してOOSです。`Factor Momentum.pdf`

systematic industry momentumは

$$
R_{t+1}^{SYSIMOM}
=
\overline R_{\mathcal W_t^{sys},t+1}^{sys}
-
\overline R_{\mathcal L_t^{sys},t+1}^{sys}.
\tag{75}
$$

---

## 4.10 Systematic industryの結果

factor modelを拡張すると、systematic industry momentumは強まり、実際のindustry momentum alphaは小さくなります。

| Systematic industry構築因子 | Systematic momentum FF5 alpha | Industry momentum残存alpha |
|---|---:|---:|
| CAPM | 0.25% | 0.38% |
| FF3 | 0.54% | 0.23% |
| FF5 | 0.53% | 0.20% |
| FF5＋LTREV＋RVAR | 0.60% | 0.14% |
| 9-factor | 0.66% | 0.09% |

9-factorではindustry momentumのalphaの79%が除去され、残存alphaは非有意です。`Factor Momentum.pdf`

---

## 4.11 Industry-neutral factorのPCA

43のindustry-neutral factorを日次で10%年率ボラティリティへ調整し、月末 $t$ までの拡大型データでPCAを行います。

$$
\widetilde{\mathbf F}_d
=
D_t^{-1}\mathbf F_d,
$$

$$
C_t
=
\operatorname{Corr}
(\widetilde{\mathbf F}_d;\ d\le t),
$$

$$
C_t
=
V_t\Lambda_tV_t'.
\tag{76}
$$

利用可能期間の関係から41PCを使います。

PCリターンは

$$
P_{k,t'|t}
=
v_{k,t}'\widetilde{\mathbf F}_{t'},
\qquad t'\in\{t,t+1\}.
\tag{77}
$$

月 $t$ のPCリターンでabove／below medianへ分け、月 $t+1$ を保有します。`Factor Momentum.pdf`

結果は、

- PC 1-5：FF5 alpha 0.76%/月、$t=6.11$
- PC 6-10：0.16%、$t=1.26$

です。

PC 1-5 momentumを右辺へ加えると、その他の全PC群のalphaは非有意になります。`Factor Momentum.pdf`

industry momentumも、PC 1-5 momentumを制御すると

$$
0.38\%\rightarrow0.08\%
$$

へ低下し、$t=0.86$ となります。

---

## 4.12 シミュレーション

### 株式リターン

$$
R_{i,t}
=
\sum_{f=1}^{F}
\beta_i^fr_{f,t}
+
\varepsilon_{i,t}
+
\delta_{g(i),t}.
\tag{78}
$$

- $\varepsilon_{i,t}$：企業固有ショック
- $\delta_{g(i),t}$：業種固有ショック

### beta構造

$$
\beta_i^f
=
B_{g(i)}^f
+
\xi_i^f.
\tag{79}
$$

- $B_{g(i)}^f$：同一業種で共有するbeta
- $\xi_i^f$：銘柄固有beta

### ファクターリターン

$$
r_{f,t}
=
\lambda_{f,t}
+
\eta_{f,t},
\tag{80}
$$

$$
\lambda_{f,t}
=
\kappa\lambda_{f,t-1}
+
\omega_{f,t}.
\tag{81}
$$

全ショックは相互に独立です。`Factor Momentum.pdf`

パラメータは、

- $N=2,000$
- $T=678$
- factor数 $F=20$
- industry数 $J=20$
- 業種割当は一様
- beta総分散を1
- 業種beta寄与率

$$
\theta
=
\frac{\sigma_B^2}
{\sigma_B^2+\sigma_\xi^2}
\in\{0,0.1,\ldots,0.5\}
$$

- factor return分散の10%を時変プレミアム
- $\kappa=0.8$
- 株式リターン分散の40%をfactor
- 企業固有30%、業種固有30%
- $\sigma_\omega^2=0.00072$
- $\sigma_\eta^2=0.018$
- 各仕様100,000回

です。`Factor Momentum.pdf`

$\theta=0$ ならindustry momentumの平均 $t$ 値は0.09ですが、$\theta=0.5$ では4.51となります。一方、factor momentumを制御するとindustry momentumはほぼ消えます。`Factor Momentum.pdf`

---

# 5. 三つのFactor Momentum論文の違い

| 項目 | Factor Momentum and the Momentum Factor | Factor Momentum Everywhere | Factor Momentum |
|---|---|---|---|
| 基本シグナル | 過去12か月の符号 | 過去リターン÷volの連続値 | 過去1か月の横断面順位 |
| 主戦略 | TSFM | TSFM | CSFM |
| ウェイト | 全factor等絶対ウェイト | signal比例、各レッグ±1 | winner／loser各レッグ等ウェイト |
| Net | 一般に0ではない | 0 | 0 |
| Gross | 1 | 2 | 2 |
| 主形成期間 | 12か月 | 1か月～60か月 | 1か月 |
| 主な説明対象 | 個別株momentum | 広範なfactor timing | industry momentum |
| PC入力 | 47 standard factor | 主分析ではなし | 43 industry-neutral factor |
| 高固有値PC | 上位10 | - | 上位5 |
| 取引費用 | 主分析なし | 10bp/turnover | 主分析なし |

同じ「factor momentum」という名称でも、実装は同一ではありません。

### Ehsani-Linnainmaa型

$$
w_{k,t}
=
\frac1K
\operatorname{sign}
\left(
\sum_{\ell=1}^{12}f_{k,t-\ell}
\right).
$$

長期・二値・ファクター横断面でnetが変動します。

### Gupta-Kelly型

$$
w_{k,t}
\propto
\operatorname{clip}
\left(
\frac{
\sum_{\ell=1}^{J}f_{k,t-\ell+1}
}{
\sigma_{k,t}
},
-2,2
\right),
$$

その後long／shortをそれぞれ1へ正規化します。

### Arnott et al.型

$$
w_{k,t}
=
\begin{cases}
1/N_W,&f_{k,t}>\operatorname{median}(f_t),\\
-1/N_L,&f_{k,t}\le\operatorname{median}(f_t).
\end{cases}
$$

短期・相対順位・market-neutralです。

---

# 6. THEMEとFactor Momentumを統合する場合の解釈

THEMEのStage 2は、一見するとfactor momentumに似ていますが、正確には異なります。

THEMEは、テーマ $q$ に対する銘柄スコアを

$$
Score_{i,t}^{THEME}(q)
=
\operatorname{sim}
\left(
z_q,
A_\phi(h_i,\mathbf r_{i,t}^{(60)})
\right)
$$

として作ります。

これは

$$
\text{テーマ関連性}
\times
\text{銘柄固有の短期相対リターン予測}
$$

です。

一方、factor momentumはテーマまたはファクター・ポートフォリオのリターン

$$
F_{q,t}
$$

自体をタイミングします。

したがって、両者を統合する際は二層に分けるのが自然です。

### 第1層：テーマ内銘柄選択

$$
w_{i,q,t}^{within}
=
g
\left(
Score_{i,t}^{THEME}(q)
\right).
$$

### 第2層：テーマ間アロケーション

テーマポートフォリオリターンを

$$
F_{q,t+1}
=
\sum_i
w_{i,q,t}^{within}
r_{i,t+1}
$$

とし、

$$
a_{q,t}^{TSFM}
=
\operatorname{clip}
\left(
\frac{
\sum_{\ell=1}^{J}F_{q,t-\ell+1}
}{
\sigma_{q,t}
},
-2,2
\right).
$$

最終ウェイトは

$$
w_{i,t}^{final}
=
\sum_q
a_{q,t}^{TSFM}
w_{i,q,t}^{within}.
\tag{82}
$$

この構造なら、

- THEME：テーマ構成銘柄とテーマ内順位
- Factor Momentum：テーマ間の時間配分

を明確に分離できます。

---

# 7. 再現性の評価

| 論文 | 手法構造の再現 | 報告数値の完全再現 | 主な障害 |
|---|---|---|---|
| THEME | 中 | 低 | 学習ハイパーパラメータ、TRS、テキスト処理、rolling仕様が不足 |
| Factor Momentum and the Momentum Factor | 高 | 中 | 47 factorの日次データ、データ改訂、銘柄特性 |
| Factor Momentum Everywhere | 高 | 中 | 65特性の完全定義、stock-level turnover |
| Factor Momentum | 高 | 中～高 | CRSP・Compustat、43 factorの日次再構築 |

---

# 8. 実装時の最低限の検証項目

## データ検証

$$
\text{signal date}
<
\text{trade date}
\le
\text{return evaluation date}
$$

を全レコードで確認します。

- 会計情報の公表lag
- ETF構成のpoint-in-time性
- SEC・ニュースのtimestamp
- delisting return
- survivorship bias
- corporate action
- stale price

を監査します。

## ウェイト検証

THEME等ウェイトなら

$$
\sum_iw_{i,t}=1.
$$

Gupta-Kelly TSFMなら

$$
\sum_{i:w_i>0}w_i=1,
\qquad
\sum_{i:w_i<0}w_i=-1.
$$

Ehsani-Linnainmaaなら

$$
\sum_i|w_i|=1.
$$

momentum-neutral factorなら

$$
\mathbf1'\mathbf x_t=0,
$$

$$
(\mathbf r_t^{mom})'\mathbf x_t=0.
$$

## PC検証

$$
V_t'V_t=I,
$$

$$
\operatorname{Corr}
(P_{k,\tau|t},P_{l,\tau|t})
\approx0
\quad(k\ne l,\ \tau\le t).
$$

同一の $V_t$ で過去シグナルと翌月リターンを計算します。

## 最終再現判定

各論文について、まず以下の少数の数値を再現すべきです。

1. THEME：Linqの $HR@3$、$P@3$、gte-Qwenの $SR@3$
2. Ehsani-Linnainmaa：6bp／51bp、TSFM年率3.92%、PC1-10の $t\approx7$
3. Gupta-Kelly：平均AR(1)=0.11、TSFM 1-1 Sharpe 0.84、1-12 Sharpe 0.70
4. Arnott et al.：短期FMOM 64bp／月、industry-neutral FMOM、PC1-5 alpha 76bp／月

これらが一致しない状態で、Sharpe、spanning test、統合戦略まで進むべきではありません。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)