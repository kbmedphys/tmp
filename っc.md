# 論文の詳細解説

**User:** Anonymous  
**Created:** 9/29/2026 22:06:32  
**Updated:** 9/30/2026 7:47:35  
**Exported:** 9/30/2026 7:48:24  
**Link:** [https://chatgpt.com/c/6abbb7d7-b388-83ee-9a77-bde23003ff14](https://chatgpt.com/c/6abbb7d7-b388-83ee-9a77-bde23003ff14)  

## Response:
2026/9/29 22:06:49 · gpt-5-6-thinking

> **整理して説明を構成中**
>
> 添付論文の目的、アルファの定義、数式の読み方、実証結果、101種類の分類、実務上の意味と限界を、論文の記述に沿って順序立てて詳しく説明する。
>
> **整理して説明を構成した**
>
> 
>
> **構成を具体化中**
>
> 論文の定義、数式演算子、実証統計、相関分析、実装時の注意点を整理する。特に、アルファ値と最終ポートフォリオ収益を混同せず、取引コストや遅延の未提示にも触れる。
>
> 33s考えました

添付論文は Zura Kakushadze の **“101 Formulaic Alphas” (2015)** です。単なる「101個の数式集」ではなく、実務で使われていた短期株式アルファを公開し、その横断的な統計特性まで分析した論文です。特に重要なのは、ここでいう *alpha* はCAPM等の回帰残差としての「学術的α」ではなく、**将来リターンを予測して売買ポジションへ変換するためのシグナル**を意味する点です。`101 Formulaic Alphas.pdf`

---

# 1. この論文が何をしようとしているのか

著者の問題意識は、現代のクオンツ運用では単一の強いシグナルを探すというより、

> 多数の弱く、寿命の短いアルファを大量に生成し、それらを組み合わせて “mega-alpha” を作る

という運用構造になっている、というものです。

多数のアルファをまとめることで、

- alpha間の分散効果
- 一部のalphaが劣化した場合の耐性
- 売買のinternal crossingによる取引コスト低減

が可能になると説明しています。`101 Formulaic Alphas.pdf`

そのうえで、通常は秘匿される実務アルファについて、WorldQuantの許可を得て**101個の具体的な数式を公開**しています。著者によれば、これらはtoy modelではなく実際の運用アルファであり、執筆時点で101個中80個がproductionで使用されていたとされています。`101 Formulaic Alphas.pdf`

論文の主な実証結果は3つです。

1. 101 alphaの相互相関はかなり低い
2. alphaの収益率はalpha自身のボラティリティと強く関係する
3. turnoverは、収益率やalpha間相関をあまり説明しない

Abstractでも、平均保有期間は約0.6～6.4日、平均pairwise correlationは15.9%と報告されています。`101 Formulaic Alphas.pdf`

---

# 2. 101 Alphasの「alpha」とは何か

これは非常に重要です。

この論文におけるalphaは、

$$
\alpha_{i,t}
$$

という「銘柄 $i$ を時点 $t$ でどの程度買う／売るべきか」を表す**cross-sectional signal**と考えるのが適切です。

例えば

$$
\text{rank}(x)
$$

なら、その日の全銘柄について $x$ を順位化します。

したがって、多くの式は

$$
\text{Ticker}\times\text{Date}
$$

のpanel dataから、

$$
\text{AlphaScore}_{i,t}
$$

を生成します。

これはそのままリターンではありません。

実際にバックテストするには、この後に

$$
\text{signal}
\rightarrow
\text{portfolio weight}
\rightarrow
\text{return}
$$

という変換が必要です。

ところが、この**portfolio constructionの詳細は論文にはほとんど書かれていません**。

したがって、

> 「論文の式を正しく実装した」  
> ≠  
> 「論文記載のSharpeを再現できる」

という点が101 Formulaic Alphasを扱ううえで最も重要です。

---

# 3. 基本となるデータ

101 alphaの大部分は非常にシンプルな日次データだけから作られています。

論文で定義されている主要変数は

$$
Open,\ Close,\ High,\ Low,\ Volume,\ VWAP
$$

です。

さらに、

- daily close-to-close return
- market capitalization
- ADV（average daily dollar volume）
- sector
- industry
- subindustry

などが使用されます。`101 Formulaic Alphas.pdf`

著者自身も、これらのalphaは基本的に **price-volume alpha** だと述べています。fundamental dataの使用は限定的で、市場時価総額やindustry classificationなどが一部で使われています。`101 Formulaic Alphas.pdf`

つまり本論文は、

> 「財務指標から割安株を探す」

というタイプのfactor investingではなく、

> **短期的な価格・出来高・流動性・relative price actionの歪みを捕捉する statistical arbitrage**

にかなり近いものです。

---

# 4. 最大の概念：Mean Reversion と Momentum

著者は101 alphaを粗く

- Mean Reversion
- Momentum

という2つの要素で理解できるとしています。`101 Formulaic Alphas.pdf`

## Mean Reversion

論文の単純例は

$$
-\ln\left(
\frac{Open_t}{Close_{t-1}}
\right)
$$

です。

今日の寄付きが昨日終値より高い、

$$
Open_t > Close_{t-1}
$$

ならシグナルは負になります。

つまり、

> ギャップアップした銘柄をshort

です。

逆に、

$$
Open_t < Close_{t-1}
$$

ならlongします。

想定しているのは、

$$
\text{overnight move}
\rightarrow
\text{intraday reversal}
$$

です。`101 Formulaic Alphas.pdf`

---

## Momentum

単純例は

$$
\ln\left(
\frac{Close_{t-1}}{Open_{t-1}}
\right)
$$

です。

昨日、

$$
Close_{t-1}>Open_{t-1}
$$

なら今日long。

昨日上昇した方向が今日も続くという仮説です。`101 Formulaic Alphas.pdf`

ただし実際の101 alphaは、

- reversal
- momentum
- volatility
- volume
- liquidity
- rank
- correlation

を複雑に組み合わせています。

---

# 5. Delay-0 / Delay-1 が極めて重要

この論文を実装するときに最もlook-ahead biasを起こしやすい部分です。

## Delay-0

当日のデータを使って**同日のうちに取引する**alphaです。

例えばCloseを使ってalphaを作り、close近辺で発注するものです。

論文ではAlpha

- #42
- #48
- #53
- #54

の4つがdelay-0だと明示されています。`101 Formulaic Alphas.pdf`

したがってEODデータだけを使って

$$
Close_t
$$

を取得したあと、

$$
Return_{t\rightarrow t+1}
$$

を取るなら問題ありませんが、

$$
Close_t
$$

を使って、

$$
Open_t\rightarrow Close_t
$$

のリターンをバックテストすると典型的なlook-aheadになります。

---

## Delay-1

今日のポジションを、

$$
t-1
$$

までのデータで作るものです。

こちらの方が日次データでは自然に再現できます。

---

# 6. 数式言語を理解すると101個はかなり読みやすくなる

Appendix Aの式は「数式」であると同時に、そのままDSL的なコードになっています。

代表的なoperatorを整理します。

### cross-sectional rank

$$
rank(x)
$$

その日の銘柄間順位です。`101 Formulaic Alphas.pdf`

例えば

```text
rank(close - open)
```

なら、

「今日の日中上昇が他銘柄に比べて大きかった銘柄」

を高scoreにします。

---

### delay

$$
delay(x,d)=x_{t-d}
$$

---

### delta

$$
delta(x,d)=x_t-x_{t-d}
$$

例えば

$$
delta(close,5)
$$

なら5日価格変化。

---

### correlation

$$
correlation(x,y,d)
$$

過去 $d$ 日におけるtime-series correlation。

例えば

$$
correlation(high,volume,5)
$$

は、

> 過去5日間で高値と出来高がどの程度連動しているか

です。

---

### Ts_Rank

$$
TsRank(x,d)
$$

現在の $x_t$ が、自分自身の過去 $d$ 日の中でどの位置にあるか。

ここが

$$
rank()
$$

とはまったく違います。

- `rank()` = 横断面
- `Ts_Rank()` = 時系列

です。

---

### decay_linear

直近を大きく、古いデータを小さくする線形加重平均です。

ウェイトは

$$
d,d-1,\ldots,1
$$

を正規化します。`101 Formulaic Alphas.pdf`

---

### IndNeutralize

$$
IndNeutralize(x,g)
$$

sector / industry / subindustry内でdemeanします。

例えば

$$
x_{i,t}^{neutral}
=
x_{i,t}
-
\bar{x}_{g(i),t}
$$

です。`101 Formulaic Alphas.pdf`

したがって、

> 「Technologyが上がったから買う」

ではなく、

> 「Technology銘柄の中でも他のTechnology銘柄より強いから買う」

というrelative-value signalにできます。

---

# 7. 101 Alphaはどんなタイプに分類できるか

論文自身は厳密なtaxonomyを示していませんが、式を見ると大きく次のグループに整理できます。

| タイプ | 主な情報 |
|---|---|
| Short-term reversal | close、open、delta |
| Intraday reversal | VWAP-Close、Open-Close |
| Momentum | past return、delta |
| Volume-price | volumeと価格のcorrelation |
| Liquidity-conditioned | volume / ADV |
| Volatility | stddev |
| High/Low location | high, low, close |
| Industry-relative | IndNeutralize |
| Composite nonlinear | rank、TsRank、decay、correlationの組合せ |

特に後半の#60以降になると、

$$
Rank,\ TsRank,\ Correlation,\ DecayLinear,\ IndNeutralize
$$

を何層にも組み合わせています。

これは単なる「複雑化」ではなく、

> **異なる時間軸 × 横断面 × liquidity × industry-relative signal**

を掛け合わせている、と理解するとかなり読みやすくなります。

---

# 8. 具体例① Alpha #12

論文の式は

$$
\text{Alpha12}
=
sign(\Delta Volume)
\times
(-\Delta Close)
$$

です。`101 Formulaic Alphas.pdf`

出来高が増加した場合、

$$
sign(\Delta Volume)=+1
$$

なので

$$
Alpha12=-\Delta Close
$$

となります。

つまり、

> 出来高増加を伴って上昇した銘柄を売る  
> 出来高増加を伴って下落した銘柄を買う

という短期reversal的な性格です。

一方、volumeが減少すると符号が反転します。

単純なprice reversalではなく、

> price moveの意味をvolume changeで条件付けしている

点が特徴です。

---

# 9. 具体例② Alpha #22

特に重要な式の一つです。

$$
\boxed{
Alpha22
=
-
\Delta_5
\left[
Corr_5(High,Volume)
\right]
\times
Rank
\left[
StdDev_{20}(Close)
\right]
}
$$

原文は

```text
Alpha#22:
(-1 * (
 delta(correlation(high, volume, 5), 5)
 * rank(stddev(close, 20))
))
```

です。`101 Formulaic Alphas.pdf`

3段階に分けると理解しやすいです。

### Step 1

$$
C_t=Corr_5(High,Volume)
$$

高値と出来高の5日相関。

---

### Step 2

$$
\Delta C_t=C_t-C_{t-5}
$$

つまり、

> High-Volume relationshipが過去5日でどう変化したか

を測っています。

---

### Step 3

$$
Rank(\sigma_{20})
$$

で高ボラ銘柄を増幅します。

最終的に

$$
Alpha22=-\Delta C_t\times VolRank
$$

です。

したがって、

$$
\Delta C_t>0
$$

すなわちHighとVolumeの関係が急速に強くなった銘柄にはnegative signal。

逆に、

$$
\Delta C_t<0
$$

ならpositive signalです。

解釈としては、

> 高値形成と出来高の結び付きが急激に強まった状態を短期的なoverextensionとみなし、その変化をreversalする

タイプに近いです。

さらに高volatility銘柄ほどscoreの絶対値が大きくなります。

重要なのは、**単純なprice momentumではなく「price-volume correlationの変化」のreversal**であることです。

---

# 10. 具体例③ Alpha #42

$$
Alpha42
=
\frac{rank(VWAP-Close)}
{rank(VWAP+Close)}
$$

です。`101 Formulaic Alphas.pdf`

著者自身がこれはdelay-0 mean-reversion alphaだと説明しています。

もし

$$
Close>VWAP
$$

なら、

$$
VWAP-Close<0
$$

なのでsignalは低くなります。

つまり、

> 後場に上昇し、終値がVWAPより上にある銘柄を相対的にshort

という発想です。`101 Formulaic Alphas.pdf`

直感的には

$$
\text{late-day run-up}
\rightarrow
\text{next reversal}
$$

です。

---

# 11. 具体例④ Alpha #101

最もシンプルな式の一つです。

$$
Alpha101
=
\frac{Close-Open}
{High-Low+0.001}
$$

`101 Formulaic Alphas.pdf`

これは実質的に、

> その日の値幅に対して、Open→Closeでどれだけ一方向に動いたか

を表します。

例えば、

$$
High-Low=100
$$

で

$$
Close-Open=80
$$

なら非常に強いup-dayです。

著者はこれをdelay-1 momentum alphaとして説明しています。

つまり、

> 前日に強いintraday trendがあった銘柄は翌日も同じ方向に動く

という仮説です。`101 Formulaic Alphas.pdf`

---

# 12. #58以降で突然「6.02936日」などが出てくる理由

後半には例えば

```text
correlation(..., 6.02936)
decay_linear(..., 7.89291)
Ts_Rank(..., 5.50322)
```

のような不思議な小数が大量に出ます。

しかし論文では、

> non-integer number of days $d$ is converted to floor(d)

と定義されています。`101 Formulaic Alphas.pdf`

したがって

$$
6.02936\rightarrow6
$$

です。

この小数は、式が人間の経済的直感だけから手作業で設計されたというより、

- parameter search
- symbolic search
- automated alpha mining

のような生成過程を強く示唆する形になっています。

ただし、**具体的にどの探索アルゴリズムでこれらのパラメータを得たかは本論文には記載されていません**。

---

# 13. 実証分析に使ったデータ

実証期間は

$$
2010/1/4 \sim 2013/12/31
$$

で、

$$
N=1006
$$

daily observationsです。`101 Formulaic Alphas.pdf`

各alphaについて

- annualized Sharpe
- daily turnover
- cents-per-share
- daily volatility
- annualized return
- alpha間correlation

を計算しています。

---

# 14. 101 alphaのSharpeはかなり高い

Table 1が非常に印象的です。

Annualized Sharpe Ratioは、

| 指標 | Sharpe |
|---|---:|
| Minimum | 1.238 |
| 25% | 1.929 |
| Median | 2.224 |
| Mean | **2.265** |
| 75% | 2.498 |
| Maximum | 4.162 |

となっています。`101 Formulaic Alphas.pdf`

平均Sharpe 2.27という非常に強い結果です。

ただし、この数値をそのまま現在の日本株で期待するのは適切ではありません。

最大の理由は、Table 1直下で明記されている通り、

> **transaction costs, trading costs, price impact等は含まれていない**

からです。`101 Formulaic Alphas.pdf`

short-horizon strategyではこれは決定的です。

---

# 15. TurnoverとHolding Period

平均daily turnoverは

$$
T=0.5456
$$

です。

論文では

$$
HoldingPeriod\simeq\frac{1}{T}
$$

としているため、平均保有期間は

$$
2.391\text{ days}
$$

となります。

範囲は

$$
0.6235\sim6.365\text{ days}
$$

です。`101 Formulaic Alphas.pdf`

つまり101 Formulaic Alphasは基本的に、

> **1日～数日程度のvery short-horizon statistical arbitrage**

だと考えるべきです。

---

# 16. alpha間の相関がかなり低い

pairwise correlationは、

$$
Mean=15.86\%
$$

$$
Median=14.31\%
$$

です。

minimumは

$$
-15.09\%
$$

maximumは

$$
87.33\%
$$

です。`101 Formulaic Alphas.pdf`

ここが論文の大きなメッセージです。

仮に1本1本のalphaが弱くても、

$$
\rho_{ij}\approx0.16
$$

程度なら、

$$
\text{many weak alphas}
\rightarrow
\text{diversified mega-alpha}
$$

という構造が成立します。

これはWorldQuant型の大量alpha研究の基本思想そのものです。

---

# 17. 最大の実証結果：ReturnはVolatilityでかなり説明できる

著者は

$$
\ln R_i
=
a+b\ln\sigma_i+\epsilon_i
$$

を推定しています。

結果は

$$
\boxed{
\ln R
=
-3.509
+
0.761\ln\sigma
}
$$

で、

$$
R^2=0.737
$$

です。`101 Formulaic Alphas.pdf`

したがって

$$
\boxed{
R\propto\sigma^{0.761}
}
$$

というscaling relationになります。

つまり、

> 高収益alphaほど、概して高ボラティリティalphaでもある

という非常に強い関係があります。

ただし指数が

$$
0.761<1
$$

なので、

$$
\frac{R}{\sigma}
$$

であるSharpeはvolatilityと完全比例ではありません。

---

# 18. TurnoverはReturnをほとんど説明しない

次に

$$
\ln R_i
=
a+b\ln\sigma_i+c\ln T_i+\epsilon_i
$$

を推定します。

結果は

$$
b=0.775
$$

に対し、

$$
c=-0.023
$$

で、turnoverのt-statは

$$
-0.57
$$

でした。`101 Formulaic Alphas.pdf`

つまり統計的には、

$$
\boxed{
Return\not\sim Turnover
}
$$

です。

「たくさん売買するalphaほど収益が高い」という単純な関係は見られません。

これは本論文の中心的な結果の一つです。`101 Formulaic Alphas.pdf`

---

# 19. Turnoverはalpha間相関もほとんど説明しない

著者はさらに、

> turnoverの近いalpha同士は似た売買をするので相関も高いのでは？

という仮説を検証しています。

log turnoverから作ったlinear / bilinear項を使ってpairwise correlationを説明します。

ところが、

$$
R^2=0.0127
$$

しかありません。`101 Formulaic Alphas.pdf`

つまり説明できるvariationはわずか

$$
1.27\%
$$

です。

ここは統計を見るうえで面白い点があります。

係数のt-statはそれなりに高いですが、pair数が非常に多いため統計的有意性が出やすい。

しかし、

> **statistically significant ≠ economically explanatory**

です。

著者が「poor explanatory power」と結論しているのはこのためです。`101 Formulaic Alphas.pdf`

---

# 20. ただしTurnoverとVolatilityには関係がある

別の回帰では、

$$
\ln\sigma
=
-6.174
+
0.368\ln T
$$

となっています。

$$
R^2=0.228
$$

です。`101 Formulaic Alphas.pdf`

したがって、

> turnoverが高いalphaほどvolatilityもある程度高い

という関係はあります。

整理すると、

$$
Turnover
\rightarrow
Volatility
$$

にはある程度の関係がある一方、

$$
Turnover
\rightarrow
Return
$$

は直接的には弱い、という構造です。

---

# 21. Figure 1～4は何を意味しているか

論文後半の図もかなり重要です。

### Figure 1 - Distribution

19ページのFigure 1では、

- Sharpe
- log(turnover)
- log(cents-per-share)
- log(volatility)
- log(return)
- correlation

のdensityが示されています。

特にcorrelationは0.1～0.2付近に集中しており、

> 多数のalphaがそれほど強く相関していない

ことが視覚的にも確認できます。`101 Formulaic Alphas.pdf`

---

### Figure 2 - Return vs Volatility

20ページでは

$$
\ln R
$$

と

$$
\ln\sigma
$$

がほぼ直線的に並びます。

まさに

$$
R\sim\sigma^{0.761}
$$

を示すグラフです。`101 Formulaic Alphas.pdf`

---

### Figure 3 - TurnoverとAlpha Correlation

21ページでは点群がかなり散らばっており、

$$
R^2\simeq1.3\%
$$

という弱い説明力を視覚的にも確認できます。`101 Formulaic Alphas.pdf`

---

### Figure 4 - Turnover vs Volatility

22ページでは弱～中程度の右上がり。

$$
\ln\sigma
\simeq
-6.174+0.368\ln T
$$

です。`101 Formulaic Alphas.pdf`

---

# 22. この論文を再現するときの最大の問題

この論文は式を公開していますが、**完全なstrategy specificationではありません**。

特に次が欠けています。

### ① Universe

どの株式を対象にしたのか。

- 上場全銘柄
- top 500 liquidity
- top 2000
- penny stocks除外

などで結果は大幅に変わります。

---

### ② Position sizing

alpha scoreから、

$$
w_{i,t}
$$

をどう作ったのかが不明です。

例えば、

$$
w_i=
\frac{\alpha_i}
{\sum_j|\alpha_j|}
$$

なのか、

rankしてlong-short decileなのか、

risk scalingをしたのかは明確でありません。

---

### ③ Dollar neutrality

本文ではquant alpha portfolioにdollar-neutralを示唆する議論がありますが、101個それぞれの完全なproduction portfolio constructionは公開されていません。

---

### ④ Transaction costs

Sharpe等はgrossです。

これはholding period 1～数日のstrategyでは重大です。

---

### ⑤ VWAP

Yahoo Finance等の日次データだけでは正しいVWAPを通常取得できません。

$$
TypicalPrice\times Volume
$$

から作るpseudo-VWAPとは別物です。

---

### ⑥ Point-in-time industry

sector / industry分類を現在のclassificationで過去に遡ると、

classification look-ahead

が入り得ます。

---

### ⑦ Delay-0 execution

closeを見てcloseで取引するalphaは、実務上、

> close直前までにsignalを計算してMOC等で執行

する必要があります。

EODの確定Closeを使って同日のclose executionとするとlook-aheadです。

---

# 23. この論文の本当に重要なメッセージ

101個の式自体も興味深いのですが、研究上さらに重要なのは次の4点です。

## ① 強い単一factorを探しているわけではない

$$
\text{many modest predictors}
$$

を大量に持つ思想です。

---

## ② Alpha diversificationが重要

平均相関

$$
15.9\%
$$

なので、個別alphaよりも

$$
\text{Alpha Portfolio}
$$

の構築が中心課題になります。

---

## ③ Price × Volume interactionが非常に多い

単純なmomentum/reversalではなく、

$$
Price
\times
Volume
\times
Liquidity
\times
Volatility
$$

というinteractionが頻出します。

---

## ④ Cross-sectional transformが中心

単純に

$$
r_{i,t-5:t}
$$

を見るというより、

$$
Rank_i(\cdot)
$$

を大量に使っています。

そのため、

> 市場全体が上昇するか

ではなく、

> **どの株が他株より上がるか**

を予測する設計になっています。

---

# 24. 研究者としてこの論文を読むなら

この論文は「101個全部をそのまま運用するためのレシピ」というより、

$$
\boxed{
\text{primitive signals}
\rightarrow
\text{operators}
\rightarrow
\text{formulaic alpha}
\rightarrow
\text{alpha portfolio}
}
$$

という**alpha research languageのサンプル集**として読むのが適切です。

primitive signalは、

$$
Open,\ High,\ Low,\ Close,\ VWAP,\ Volume
$$

operatorは、

$$
Rank,\ Delta,\ Correlation,\ TsRank,
Decay,\ Neutralize
$$

です。

この組合せを変えることで膨大なalpha spaceが作れます。

著者が冒頭で述べる「数十万・数百万、さらにはそれ以上のalphaを自動生成する」という話とAppendix Aの式は、この点でつながっています。`101 Formulaic Alphas.pdf`

---

# 25. 論文全体を一枚で整理すると

$$
\boxed{\text{OHLCV / VWAP / ADV / Industry}}
$$

↓

$$
\boxed{
\text{Rank / Delta / Correlation /
TsRank / Decay / Neutralize}
}
$$

↓

$$
\boxed{\text{101 Alpha Signals}}
$$

↓

$$
\boxed{
\text{Mean Reversion}
+
\text{Momentum}
+
\text{Price-Volume Interaction}
}
$$

↓

多数の低相関alpha

$$
\bar{\rho}\approx15.9\%
$$

↓

$$
\boxed{\text{Mega-alpha / Alpha Portfolio}}
$$

という論文です。

また実証的には、

$$
\boxed{R\propto\sigma^{0.76}}
$$

が強く、

一方で

$$
\boxed{
R \not\propto Turnover
}
$$

かつ

$$
\boxed{
Correlation
\text{ is poorly explained by Turnover}
}
$$

というのが中心的な結論です。`101 Formulaic Alphas.pdf`

---

## この論文を実証研究に使う場合の重要点

特に日本株で再現するのであれば、**「101個すべてのSharpeを出す」ことよりも、各alphaについて**

$$
IC,\ ICIR,\ Decay,\ Turnover,
SectorExposure,\ SizeExposure,
VolatilityExposure
$$

を調べ、

さらに

$$
\text{Long contribution}
\quad vs\quad
\text{Short contribution}
$$

を分解する方が、現在のquant researchとしては有益です。

その中でも **Alpha #22** は構造が比較的明確で、

$$
\Delta Corr(High,Volume)
\times Volatility
$$

という経済的解釈が可能なので、単体で再現実験する題材としてかなり扱いやすい部類です。論文全体を理解したうえで見ると、#22は「101式のうちの一つ」というより、**price-volume interaction + short-term reversal + volatility scaling**というこの論文の典型的な設計思想を凝縮したalphaだと理解できます。

## Response:
2026/9/29 22:20:05 · gpt-5-6-thinking

> **調査方針を整理中**
>
> 筆者ページから連なるnoteをできるだけ網羅し、#22に関係する記述を特定します。そのうえで、添付資料の式を基準に、各アルファを統計的アービトラージの観点から整理していきます。
>
> **調査方針を整理した**
>
> 
>
> **調査範囲を確認中**
>
> 筆者ページと関連noteを一覧化し、各記事の主題を拾いながら、#22との直接的な関係と私自身の統計的アービトラージ解釈を分けて整理します。関連が薄い記事も、共通する価格構造の観点で位置づけます。
>
> **調査範囲を確認した**
>
> 
>
> **整理方法を設計中**
>
> 全noteを確認しつつ、各Alphaを「入力データ・変換・順位化・売買解釈・リスク・検証方法」に分解します。#22は特に、価格変化率と出来高変化率の順位相関として詳しく扱います。
>
> **設計方法を整理した**
>
> 
>
> **情報を突合中**
>
> 記事一覧を確定し、取得できる本文と紹介文を照合します。確認できない記事は推測で補わず、#22の数式分析では、資料に明記された内容と私の解釈を明確に分けて説明します。
>
> **情報を突合した**
>
> 
>
> **調査結果をまとめ中**
>
> 確認できたnote群を、基礎編・実践編・単独記事に分類し、#22を中心に、価格変化と出来高変化のクロスセクション順位相関、売買方向、モメンタムとの違い、実装上の注意点まで整理します。
>
> **調査結果を整理した**
>
> 
>
> **9件のウェブサイトを検索しました**
>
> 
>
> 4m 51s考えました

調査しました。結論から言うと、はなまる氏のnote群は **WorldQuant の「101 Formulaic Alphas」を直接解説したものではなく、ICT/SMCを「Liquidity → Price Delivery → Structure → Imbalance → Rebalancing」という流れで理解するための教材群**です。ただし、この「単一のチャート形状ではなく、価格・出来高・レンジ内位置・直前の状態変化を一連の状態遷移として読む」という発想は、101 Alphasを statistical arbitrage として経済的に解釈する際にかなり有用です。特に Alpha #22 はその枠組みと相性がよいです。

2026年9月29日時点で、プロフィールから確認できる体系は「基礎編12本」「実践編7本」に、独立記事の Hidden Order Block と Master Candle Range Theory を加えた **21本**です。プロフィール上でも2つのマガジンはそれぞれ12本・7本と表示されています。([note（ノート）](https://note.com/hanamaru_fx01/magazines))  
なお、基礎編 Episode 8 は現在本文が表示されず「販売されていません」となっているため、そこだけは前後の記事と最終章の総括から位置づけを確認しています。([note（ノート）](https://note.com/hanamaru_fx01/n/nde0c3d73ca47?hl=en&utm_source=chatgpt.com))

---

# 1. まず重要な整理：「SMCのLiquidity」と「stat arbのLiquidity」は同じではない

ここを混同しない方がよいです。

はなまる氏のnoteでいう Liquidity は主に、

$$
\text{Old High / Old Low / Equal High / Equal Low}
$$

などの周辺に存在すると想定される stop orders 等を含む「注文が集まりやすい価格帯」です。実践編では、価格が Liquidity を処理した後に Displacement、MSS、FVG がどう形成されたかを一連の Narrative として読むことが繰り返されています。([note（ノート）](https://note.com/hanamaru_fx01/n/n15947d4ca6e2?hl=en&utm_source=chatgpt.com))

一方、quantitative financeで通常いう liquidity は、

$$
Volume,\ ADV,\ Turnover,\ Spread,\ Depth,\ Amihud
$$

などで測る「取引容易性・市場インパクト・市場厚み」です。

したがって Alpha #22 の `volume` を「SMCのLiquidityそのもの」と呼ぶのは正確ではありません。より正確には、

> **Volume = participation / trading activity proxy**

と考えます。

101 Alphasの中では、

$$
\frac{Volume}{ADV20}
$$

やADVそのものを使うalphaの方が、stat-arb的な意味でのliquidity conditioningに近いです。

---

# 2. はなまる氏の21本をstat-arb研究に翻訳すると

以下の「Quantへの翻訳」はnote筆者自身の主張ではなく、**私が101 Formulaic Alphasを解釈する目的で対応付けたもの**です。

| Note | 原記事の中心テーマ | 101 Alphas / stat-arbへの翻訳 |
|---|---|---|
| 基礎1 Market is Engineered | Liquidityという視点 | priceは孤立した値ではなく、注文集中点との相対位置として扱う |
| 基礎2 Structure & Liquidity | Internal / External Liquidity | rolling high/low、range内位置、extremeからの距離 |
| 基礎3 Time & Price | PriceだけでなくTime | signal horizon、lookback、session/regime conditioning |
| 基礎4 Order Blocks | Price Deliveryの起点 | 強いprice moveの直前状態、lagged state variable |
| 基礎5 Simple Setups | Sweep→Displacement→Structure→FVG | 複数signalを順序付きconditionとして組み合わせる |
| 基礎6 Risk Management | expectancyとcapital preservation | volatility scaling、position sizing、drawdown制約 |
| 基礎7 Journaling | 感覚をデータ化 | IC/ICIR、decay、MAE/MFE、subsample分析 |
| 基礎8 Higher Timeframe | HTF Context→LTF Execution | long-horizon state × short-horizon alpha |
| 基礎9 Psychology | rule adherence | live/backtest乖離、execution slippage |
| 基礎10 Trading System | setupを固定する | specification固定、parameter mining抑制 |
| 基礎11 Holy Grail | Edgeを十分な標本で検証 | multiple testing / overfittingへの警戒 |
| 基礎12 Mastery | Pattern→Data Trader | hypothesis→backtest→reviewの研究プロセス |

Ep2では価格をInternal / External Liquidityの間の動きとして捉えています。Ep3では同じ価格でも「いつ到達したか」で意味が異なるとし、Price × Timeを強調しています。([note（ノート）](https://note.com/hanamaru_fx01/n/n670e7dd5cec9?hl=en&utm_source=chatgpt.com)) Ep4-5では単独のFVGやOBではなく、Liquidity event → Displacement → Structureという前後関係が重要だと整理されています。([note（ノート）](https://note.com/hanamaru_fx01/n/n9009aaa91ddb?utm_source=chatgpt.com))

後半はかなりquant researchに近い考え方になります。Ep7では、session・setup別集計、expectancy、MAE/MFE、サンプル数、仮説→検証→改善という考え方まで明示されています。([note（ノート）](https://note.com/hanamaru_fx01/n/n499a9a1779d6?utm_source=chatgpt.com)) Ep10-12も、ルールを頻繁に変更せず一つのedgeを多数回検証することを重視しています。([note（ノート）](https://note.com/hanamaru_fx01/n/n205b40236be7?utm_source=chatgpt.com))

実践編はより直接的です。

| Note | 中心テーマ | Quantへの翻訳 |
|---|---|---|
| 実践0 Introduction | PatternではなくNarrative | alphaを単一indicatorでなく状態遷移として説明 |
| 実践1 Elements | Liquidity + Imbalance | location variable + disequilibrium variable |
| 実践2 Internal Liquidity & MSS | Sweep後のDelivery Shift | event発生後のconditional response |
| 実践3 MSS & FVG | どこで発生したか | context-dependent signal |
| 実践4 Intraday Order Flow | Daily Range内の位置 | normalized range position |
| 実践5 Market Efficiency | Efficient / Inefficient Delivery | temporary price dislocation / rebalancing |
| 実践6 Daily Bias | What taken? Where now? Where next? | state → shock → conditional expectation |

実践編Introductionの「Where? → What happened? → Where next?」という整理は、101 Alphasを説明するテンプレートとして特に使えます。([note（ノート）](https://note.com/hanamaru_fx01/n/nbf82b12c6ea7?utm_source=chatgpt.com)) 実践2では、Liquidityを取ったこと自体ではなく、その後のDisplacementと内部構造変化を確認することが強調されています。([note（ノート）](https://note.com/hanamaru_fx01/n/n36aa7b88155a?utm_source=chatgpt.com))

実践5はさらに重要です。ここではFVGを単なる3-candle patternではなく、**一方向に急速に価格が移動し、十分な双方向取引が行われなかった “Inefficient Price Delivery” の痕跡**として説明しています。また、Institutional Order Flowは実注文を直接観測したものではなく、price actionから推測する概念だと明確に断っています。([note（ノート）](https://note.com/hanamaru_fx01/n/ne97f8602bb27?utm_source=chatgpt.com))

これはquant研究でも守るべき区別です。

> 「機関投資家が買ったから上がった」

ではなく、

> 「価格・出来高・レンジ・VWAP等に観測可能な非対称性が生じ、その後に統計的なconditional returnが存在するか」

と置き換えるべきです。

---

# 3. 独立2記事は特に重要

## Hidden Order Block

HOBの記事では、

$$
Balance
\rightarrow
Displacement
\rightarrow
FVG
\rightarrow
Retracement
\rightarrow
Acceptance/Rejection
$$

というAuctionの流れが強調されています。

単にFVGへタッチしたことではなく、**過去に取引が集中した価格帯へ戻ったあと、市場がそこを再受容するのか拒否するのか**を見るという考え方です。([note（ノート）](https://note.com/hanamaru_fx01/n/n759f62d83130?utm_source=chatgpt.com))

これをstat-arbに翻訳すると、

$$
\text{Historical equilibrium state}
\rightarrow
\text{price shock}
\rightarrow
\text{return to reference price}
\rightarrow
\text{persistence or reversion}
$$

です。

これはまさにmean-reversion研究の典型的な設計です。

---

## Master Candle Range Theory

MCRTではローソク足1本をauction rangeとみなし、

$$
Range\ breakout
\rightarrow
Price\ exploration
$$

の後、

$$
Acceptance
$$

なのか

$$
Rejection
$$

なのかを見る、と整理しています。

特に、

> rangeの外に出たことではなく、その価格帯に「留まれたか」

が重要だとしています。([note（ノート）](https://note.com/hanamaru_fx01/n/n7c2357d6454c?utm_source=chatgpt.com))

これは非常にquant化しやすい概念です。

例えば rolling high を突破した後、

$$
Close_t>High_{t-k:t-1}
$$

が翌日も継続すればacceptance、

一方、

$$
High_t>High_{t-k:t-1},
\qquad
Close_t<High_{t-k:t-1}
$$

ならrejection。

101 Alphasに頻出する

$$
High,\ Low,\ Close,\ VWAP,\ ts\_max,\ ts\_min
$$

の経済的説明に使えます。

---

# 4. この枠組みで Alpha #22 を読む

原論文の #22 は

$$
\boxed{
\alpha_{22,t}
=
-
\Delta_5
\left[
Corr_5(High,Volume)
\right]
\times
Rank
\left[
StdDev_{20}(Close)
\right]
}
$$

です。`101 Formulaic Alphas.pdf`

論文の定義上、

$$
delta(x,d)=x_t-x_{t-d},
$$

`rank` はcross-sectional rankです。`101 Formulaic Alphas.pdf`

変数を置くと、

$$
\rho_t
=
Corr
\left(
High_{t-4:t},
Volume_{t-4:t}
\right)
$$

$$
D_t=\rho_t-\rho_{t-5}
$$

$$
V_t=
Rank_{CS}
\left(
StdDev_{20}(Close)
\right)
$$

なので、

$$
\boxed{\alpha_{22,t}=-D_tV_t}
$$

です。

---

# 5. #22の最も重要なポイント：「相関」ではなく「相関の変化」

ここを強調すべきです。

#22は

$$
-Corr(High,Volume)
$$

ではありません。

$$
-\Delta Corr(High,Volume)
$$

です。

しかも、

$$
Corr_t
$$

が過去5日、

$$
Corr_{t-5}
$$

がそのさらに前の5日なので、概ね

$$
[t-9,t-5]
$$

と

$$
[t-4,t]
$$

という**隣接する2つの5営業日window**を比較しています。

つまり #22 の中心は、

> **High-Volume relationshipの短期的なregime shift**

です。

これは、単純なprice reversalより一段抽象度が高いsignalです。

---

# 6. 何を測っているのか

例えば直近5日で、

| Day | High | Volume |
|---|---:|---:|
| 1 | 100 | 1.0m |
| 2 | 102 | 1.2m |
| 3 | 104 | 1.5m |
| 4 | 106 | 1.8m |
| 5 | 108 | 2.2m |

のようなら、

$$
Corr(High,Volume)>0
$$

になります。

つまり、

> 高い価格が形成される日ほど参加量も増加している

状態です。

しかし #22 はこの水準だけでなく、

> 前の5日間より、この関係がどれだけ急激に強くなったか

を見ています。

---

# 7. #22はmean-reversion型である

もし

$$
D_t>0
$$

つまりprice-volume couplingが強まると、

$$
\alpha_{22}<0
$$

です。

したがってshort方向。

逆に、

$$
D_t<0
$$

なら

$$
\alpha_{22}>0
$$

でlong方向です。

したがって基本構造は、

$$
\boxed{
\text{change in price-volume coupling}
\rightarrow
\text{contrarian response}
}
$$

です。

これをstat-arb的に表現するなら、

> **短期的に価格形成と参加量の同期性が異常に強まった銘柄はoverextendedであり、その状態変化にはmean reversionが起きる**

という仮説と読むのが最も自然です。

ただしこれは**論文が明示した経済的説明ではなく、式から構成した解釈**です。

---

# 8. はなまる氏の用語に翻訳すると

実践編の

> Where?  
> What happened?  
> Where next?

に当てはめると非常に分かりやすくなります。

### Where?

$$
Rank(StdDev_{20}(Close))
$$

です。

つまり、

> 「どのような銘柄でこのeventを重視するか」

を決めています。

高volatility銘柄ほどweightを大きくします。

---

### What happened?

$$
\Delta Corr_5(High,Volume)
$$

です。

つまり、

> 「直近でprice formationとtrading activityの関係が急変したか」

です。

これはSMCの言葉でいうLiquidity EventやDisplacementそのものではありませんが、

> **market participationを伴うPrice Deliveryの状態変化**

に最も近い量です。

---

### Where next?

数式の先頭の

$$
-1
$$

です。

つまり、現在の変化方向を追随するのではなく、

$$
\boxed{\text{Reversion}}
$$

を仮定しています。

---

# 9. ただし「高値＋出来高＝強い上昇」と単純化してはいけない

これは #22 を説明するときの重要な注意点です。

例えば、

$$
\rho_{t-5}=-0.8,\qquad
\rho_t=-0.1
$$

でも

$$
\Delta\rho=+0.7
$$

です。

一方、

$$
\rho_{t-5}=0.1,\qquad
\rho_t=0.8
$$

も

$$
\Delta\rho=+0.7
$$

です。

どちらも同じshort signalになります。

しかし経済的な状態はかなり違います。

したがって #22 は、

> 「出来高を伴った上昇をshortするalpha」

ではありません。

より正確には、

> **High-Volume couplingが以前のregimeに比べてpositive方向へ変化した銘柄をshortする**

signalです。

さらに、`High`そのもののdirectionは数式には明示的に入っていません。

ここは実証で分解した方がよいです。

---

# 10. もう一つ重要な問題：5日相関は非常にnoisy

5 observationsだけで、

$$
Corr(High,Volume)
$$

を推定します。

そのため非常に不安定です。

しかしこれは欠点とは限りません。

このalphaの目的が、

$$
\text{stable structural correlation}
$$

ではなく、

$$
\text{short-lived local dislocation}
$$

なら、むしろ短いwindowが必要です。

つまり #22 は、

> 長期的なprice-volume relationを推定するfactor

ではなく、

> **price-volume relationの急激な局所変化をevent signalとして利用するalpha**

と理解した方が自然です。

---

# 11. Volatility Rankは符号を決めていない

$$
Rank(StdDev_{20}(Close))>0
$$

なので、これはsignalの方向を決めません。

方向は完全に

$$
-\Delta\rho
$$

から来ます。

Volatility Rankは

$$
\boxed{\text{signal amplitude conditioner}}
$$

です。

例えば、

$$
\Delta\rho=+0.8
$$

でも、

低vol銘柄なら

$$
V=0.2
\Rightarrow
\alpha=-0.16
$$

高vol銘柄なら

$$
V=0.9
\Rightarrow
\alpha=-0.72
$$

となります。

つまり、

> 同じprice-volume regime shiftでも、価格変動性の高い銘柄ほど強くbetする

構造です。

---

# 12. ただし `stddev(close,20)` には重要な問題がある

これは実装研究上かなり重要です。

原式は

$$
StdDev(Close,20)
$$

であって、

$$
StdDev(Return,20)
$$

ではありません。

したがって価格水準の影響を受けます。

例えば、

$$
\$500
$$

の銘柄と

$$
\$20
$$

の銘柄では、同じpercentage volatilityでもraw price standard deviationが異なります。

`rank()`を掛けても、このscale dependencyは完全には消えません。

したがって日本株で再現する場合、

**Original**

$$
Rank(\sigma(Close))
$$

を必ずbenchmarkとして残しつつ、

**Robustness**

$$
Rank(\sigma(Return))
$$

$$
Rank(ATR/Close)
$$

などを別versionとして比較する価値があります。

ただし後者は#22そのものではありません。

---

# 13. 実は#22単独より「Alpha 12-26のfamily」として読むと分かりやすい

原論文を見ると、#22の周辺にはprice-volume interactionが集中しています。

例えば、

$$
\alpha_{12}
=
sign(\Delta Volume)
\times
(-\Delta Close)
$$

`101 Formulaic Alphas.pdf`

これは非常に直接的な

$$
Volume\ conditioned\ reversal
$$

です。

また、

$$
\alpha_{13}
=
-Rank(Cov(Rank(Close),Rank(Volume)))
$$

$$
\alpha_{15}
=
-\sum Rank(Corr(Rank(High),Rank(Volume)))
$$

$$
\alpha_{16}
=
-Rank(Cov(Rank(High),Rank(Volume)))
$$

といったものがあります。`101 Formulaic Alphas.pdf`

さらに #26 は、

$$
-\max
Corr
\left(
TsRank(Volume),
TsRank(High)
\right)
$$

です。`101 Formulaic Alphas.pdf`

したがって#22は孤立した式というより、

$$
\boxed{
Price\text{-}Volume\ Interaction
+
Contrarian
}
$$

という一群の中に位置づけられます。

その中で#22だけは特に、

$$
\boxed{
\text{level of correlation}
\rightarrow
\text{change in correlation}
}
$$

へ一段進めたsignalです。

---

# 14. #22をSMC/Auction Market的に言い換えるなら

かなり慎重に表現すれば、

> 高値形成とmarket participationの結びつきが、直近の状態から急激に変化したことを「Price Delivery regimeの変化」とみなし、その変化が高volatility銘柄で過剰になった場合にreversionを期待する

alphaです。

はなまる氏の記事でいう

$$
Exploration
\rightarrow
Acceptance/Rejection
$$

という言葉を借りれば、

#22は直接Acceptance/Rejectionを測ってはいませんが、

$$
\Delta Corr(High,Volume)
$$

を

> 「新しい価格への探索に参加量がどの程度伴うようになったか」

という**proxy**として読むことはできます。

そして先頭のminus signは、

> その急激な状態変化が持続するより、短期的にはrevertする

というbetです。

MCRTの「breakした事実より、その後その価格に留まれるかを見る」という考え方とも相性があります。([note（ノート）](https://note.com/hanamaru_fx01/n/n7c2357d6454c?utm_source=chatgpt.com))

---

# 15. ただしSMCのNarrativeを#22の「原因」として扱わない

ここは研究として重要です。

例えば、

> 「Liquidity Sweepが起きたためHigh-Volume correlationが上昇し、機関がstopを取ったので反転する」

と説明すると、データから観測できていない因果を追加してしまいます。

より適切なのは、

$$
\boxed{
Observed:
High,\ Volume,\ Close
}
$$

から、

$$
\boxed{
Observed\ statistical\ state:
\Delta Corr(High,Volume)
}
$$

を作り、

$$
\boxed{
Hypothesis:
subsequent\ return\ mean\ reverts
}
$$

を検定することです。

SMC/Auctionの考え方は、

> **仮説を考えるためのeconomic narrative**

として利用し、

実証はOHLCVから独立に行う、という分離がよいです。

---

# 16. 全101 Alphaを説明するための共通テンプレート

今回のnote調査を踏まえると、各Alphaを次の6項目で統一して説明できます。

| 軸 | 質問 |
|---|---|
| ① State / Where | 現在どの価格・volatility・liquidity regimeにいるか |
| ② Event / What happened | 何が直近で変化したか |
| ③ Participation | Volume / ADVはその変化をどうconfirmしているか |
| ④ Relative location | VWAP、High/Low、rolling range、他銘柄との相対位置はどうか |
| ⑤ Expected response | MomentumかMean Reversionか |
| ⑥ Conditioning | volatility、industry、liquidity等でどの銘柄を強くbetするか |

例えば #22 なら、

$$
State
=
VolatilityRank
$$

$$
Event
=
\Delta Corr(High,Volume)
$$

$$
Participation
=
Volume
$$

$$
RelativeLocation
=
High
$$

$$
ExpectedResponse
=
MeanReversion
$$

$$
Conditioning
=
20d\ volatility
$$

となります。

この形式に統一すると、複雑な#60-#100もかなり解読しやすくなります。

---

# 17. #22で次に行うべき実証分解

#22を本当に理解するには、完成式だけバックテストするより**component attribution**を行うべきです。特に次の分解が重要です。

$$
X_1=-\Delta Corr_5(High,Volume)
$$

$$
X_2=Rank(StdDev_{20}(Close))
$$

$$
X_3=X_1X_2=\alpha_{22}
$$

について、各々の

$$
IC,\ ICIR,\ Decay,\ Turnover
$$

を見る。

さらに

$$
\Delta\rho
$$

をquintile、

$$
VolRank
$$

をquintileにして、

$$
5\times5
$$

portfolio sortを作れば、

> 「本当にhigh-volatility銘柄でprice-volume coupling shockの効果が強いのか」

を直接確認できます。

その次に、

$$
\Delta\rho>0
$$

を

$$
5d\ return>0
$$

と

$$
5d\ return<0
$$

に分割します。

これで、

> #22のshort legは本当に「出来高を伴った上昇のoverextension」なのか

それとも単に

> correlation regime changeそのもの

なのかが分かります。

これは#22の経済的意味を確定するうえで非常に重要です。

---

今回の21本のnote調査から得られる最も有用なポイントは、**101 Alphasを「式の翻訳」で終わらせず、“どの市場状態で → 何が変化し → その変化に対してmomentum/reversionのどちらをbetしているのか”というNarrativeで説明する**ことです。

特に#22は、

$$
\boxed{
\text{Price-Volume coupling regime shift}
\times
\text{Volatility conditioning}
\times
\text{Mean reversion}
}
$$

と位置づけるのが、現時点では最も精密な説明です。

次に進めるなら、**101個すべてをこの6軸で分類し、Alpha #1〜#101について「数式 → primitive signal → market microstructure/stat-arb解釈 → momentum/reversal → liquidity/relative-priceとの関係」の一覧表を作る**のがよいです。そのうえで #22 だけは上記component decompositionを使って、日本株で検証可能な仮説まで落とし込めます。

---

**Sources:**

- [はなまるのマガジン一覧｜note](https://note.com/hanamaru_fx01/magazines)

## Response:
2026/9/29 23:02:42 · gpt-5-6-thinking

> **精緻化している**
>
> 私は式の意味を、価格リターンではなく価格水準の標準偏差と相関変化の組み合わせとして整理している。高ボラティリティは水準であり、感情的な誤価格や反転を直接証明するものではない。
>
> **精緻化した**
>
> 
>
> **符号特性を確認している**
>
> 私は式ごとの符号と方向性を点検している。常に非正、0/1、または正値になる式もあり、未加工のアルファは対称なロング・ショート信号とは限らない。実運用では中立化や順位変換が方向性を補う可能性がある。
>
> **符号特性を確認した**
>
> 
>
> 4m 44s考えました

概ね整合的です。ただし、#22の経済的意味を厳密にするなら、提示された説明には **「数式が直接測っているもの」と「その背後に置く市場仮説」** が少し混ざっています。ここを分離すると、かなり説得力のある解釈になります。

## 1. Alpha #22：提示された解釈はどこまで妥当か

原式は

$$
\alpha_{22,t}
=
-\Delta_5\left[\operatorname{Corr}_5(High,Volume)\right]
\times
Rank_{CS}\left[\operatorname{Std}_{20}(Close)\right]
$$

です。`101 Formulaic Alphas.pdf`

論文の定義では `delta(x,d)` は $x_t-x_{t-d}$、`rank` はcross-sectional rank、`stddev(x,d)` は過去 $d$ 日の時系列標準偏差です。`101 Formulaic Alphas.pdf`

提示された説明のうち、

> 「量価構造の急変」と「高い価格変動性」の組み合わせを捉え、その状態に対して逆方向のポジションを取る

という部分は、これまでの検討とかなり整合的です。

ただし4点、修正した方がよいです。

### ① 「資金行動の転換点」は有力な仮説だが、直接観測してはいない

$$
\Delta Corr(High,Volume)
$$

から直接分かるのは、

> **HighとVolumeの短期的な連動構造が、直前の5日間から変化した**

ということだけです。

したがって、

> 「市場を主導する資金が切り替わった」

は economic narrative としては合理的ですが、式から直接識別された事実ではありません。

より精密には、

> **市場参加・価格形成メカニズムの局所的なregime shiftのproxy**

と表現するのがよいでしょう。

---

### ② 「元々安定していた量価構造が崩れた」とは限らない

#22には

$$
\operatorname{Var}(\rho)
$$

や「それまで相関が安定していたか」を測定する項はありません。

例えば、

$$
\rho_{t-5}=-0.8,\qquad \rho_t=-0.1
$$

でも、

$$
\Delta\rho=+0.7
$$

ですし、

$$
\rho_{t-5}=0.1,\qquad \rho_t=0.8
$$

でも同じです。

したがって、

> stable structure → breakdown

より、

$$
\boxed{\text{local price-volume coupling shift}}
$$

と呼ぶ方が式に忠実です。

---

### ③ 「ボラティリティの拡大」ではなく「現在のボラティリティ水準」

ここはかなり重要です。

式は

$$
\Delta Std(Close,20)
$$

ではなく、

$$
Rank\{Std(Close,20)\}
$$

です。

したがって測定しているのは、

> ボラティリティが最近拡大したか

ではなく、

> **現在、他銘柄に比べて20日終値dispersionが大きいか**

です。

さらに原式は

$$
Std(Return)
$$

ではなく

$$
Std(Close)
$$

なので、price-level effectも入ります。

この意味で、

> 「変動の拡大と量価構造の急変が共鳴」

より、

> **「量価構造の急変が、高dispersion銘柄で生じているときにsignalを増幅する」**

の方が正確です。

---

### ④ 「非合理的な誤価格」は仮説であり、数式そのものではない

先頭の

$$
-1
$$

から明確に分かるのは、

$$
\Delta Corr(High,Volume)>0
\Rightarrow
\alpha<0
$$

であり、逆に

$$
\Delta Corr(High,Volume)<0
\Rightarrow
\alpha>0
$$

ということです。

つまり、

$$
\boxed{
\text{price-volume coupling change に対する contrarian bet}
}
$$

です。

ただしこれは、

> 株価そのものが必ず反転する

とはまだ言っていません。

#22にはリターンの符号が直接入っていないからです。

したがって「短期反転」を確定するには、

$$
\Delta\rho>0,\quad Return_{past}>0
$$

と

$$
\Delta\rho>0,\quad Return_{past}<0
$$

を分けて、その後のreturnを調べる必要があります。

### 私なら#22を次のように表現します

> **Alpha #22は、HighとVolumeの局所的な結び付きが直近で急変した銘柄を検出し、その変化に対してcontrarianなポジションを取るprice-volume interaction alphaである。20日終値dispersionのcross-sectional rankによって、価格変動性の高い銘柄ほどsignalを増幅する。経済的には、参加量と価格形成の同期性が急激に変化した高volatility銘柄では、一時的なoverextensionやprice dislocationが発生しやすく、その後にmean reversionが起きる、という仮説として解釈できる。ただし、資金主体の交代・感情主導・mispricingそのものは数式から直接観測されるものではなく、検証すべきeconomic mechanismである。**

これが、これまで検討した

$$
\boxed{
Price\text{-}Volume\ Coupling\ Regime\ Shift
\times
Volatility\ Conditioning
\times
Contrarian
}
$$

という整理と最も整合的です。

---

# 2. 101 Alphasを読むための「6軸」

以下では全alphaを同じ枠組みで整理します。

**S = State / Where**：現在どの市場状態か  
**E = Event / What changed**：直近で何が変化したか  
**P = Participation / Liquidity**：Volume・ADV等の参加量  
**R = Relative Price / Location**：VWAP・High/Low・rolling range等との相対位置  
**X = Expected response**：MR = mean reversion、MOM = momentum、MIX = 混合、RV = relative-value/state signal  
**C = Conditioning**：volatility、industry neutralization、long horizon等

以下の経済的解釈は論文本文の説明ではなく、Appendix Aの数式から構成した **stat-arb interpretation** です。原論文自体は主として数式を提示しています。入力はOHLCV、VWAP、market cap、ADV、industry classification等です。`101 Formulaic Alphas.pdf`

また、正の値しか取らないalphaやbinary alphaもあります。実際のportfolio weightへの変換は論文に完全には開示されていないため、以下のMOM/MR分類は「signalの経済的な単調方向」を示すもので、最終ポジションそのものを保証するものではありません。

---

## Alpha #1-#20

式はAppendix Aの#1-#20に基づきます。`101 Formulaic Alphas.pdf`

| # | 数式・primitive signalの要約 | 6軸分類 | Stat-arb解釈 |
|---|---|---|---|
| 1 | 負return時は20d vol、それ以外はCloseを用いた5d extreme timing | S: return/vol regime; E: recent extreme timing; P:-; R: close/extreme; X:MIX; C:vol | 異なるregimeで定義を切替え、最近のextreme発生時点を相対評価するhybrid signal。経済的解釈は弱め。 |
| 2 | $-Corr_6[Rank(\Delta_2\log V),Rank((C-O)/O)]$ | S: intraday return; E: volume change; P:volume; R:O→C; X:MR; C:rank | volume changeとintraday returnの結合が強い状態に逆張り。price-volume coupling reversal。 |
| 3 | $-Corr_{10}[Rank(O),Rank(V)]$ | S:open level; E:coupling; P:volume; R:open; X:RV/MR; C:rank | Openと参加量の局所的連動を逆方向評価。 |
| 4 | $-TsRank_9[Rank(L)]$ | S:low relative strength; E:recent rank; P:-; R:Low; X:MR; C:time rank | Lowが最近相対的に高い銘柄を抑制。短期price-strength reversal。 |
| 5 | $Rank(O-MA_{10}VWAP)\times-|Rank(C-VWAP)|$ | S:opening dislocation; E:O-VWAP; P:VWAP; R:open/close vs VWAP; X:MR; C:magnitude | opening価格がVWAP基準から乖離した銘柄への逆張りを、当日VWAP乖離で増幅。 |
| 6 | $-Corr_{10}(O,V)$ | S:open; E:coupling; P:volume; R:open; X:MR/RV; C:- | #3のraw版。open-price/participation couplingへの逆張り。 |
| 7 | Volume>ADV20なら7d price moveに逆張り | S:large move; E:Δ7C; P:V/ADV20; R:close; X:MR; C:60d extremeness | unusual volume下での大きな7日価格変化をoverextensionとしてrevert。 |
| 8 | 5d Open×5d Return複合量の10d変化を逆rank | S:multi-day state; E:10d change; P:-; R:open+returns; X:MR; C:rank | price-level×return stateの急変へのcross-sectional contrarian。 |
| 9 | 5日連続同方向なら1d momentum、それ以外は1d reversal | S:trend consistency; E:Δ1C; P:-; R:close; X:MIX; C:5d condition | persistent trend時だけmomentum、通常時はreversalというregime-switching alpha。 |
| 10 | #9の4d判定＋cross-sectional rank | S:trend; E:Δ1C; P:-; R:close; X:MIX; C:rank | #9を横断的順位へ変換。 |
| 11 | VWAP-Closeの3d max/min × 3d volume change | S:VWAP dislocation; E:Δ3V; P:volume; R:C vs VWAP; X:MIX; C:rank | recent price-location imbalanceとparticipation shockのinteraction。 |
| 12 | $sign(\Delta V)\times(-\Delta C)$ | S:1d move; E:volume direction; P:volume; R:close; X:MR; C:- | price reversalをvolume changeの符号で条件付け。 |
| 13 | $-Rank[Cov_5(Rank(C),Rank(V))]$ | S:price-volume state; E:covariance; P:volume; R:close; X:MR; C:rank | price-volume couplingの強い銘柄をcontrarianに評価。 |
| 14 | $-Rank(\Delta_3 return)\times Corr_{10}(O,V)$ | S:return change; E:Δreturn; P:volume; R:open; X:MR/MIX; C:coupling | return acceleration reversalをopen-volume couplingでscale。 |
| 15 | 3d high-volume rank correlationを負方向累積 | S:coupling; E:ρ(H,V); P:volume; R:High; X:MR; C:rank | HighとVolumeの強い同期を一時的overextensionとして逆張り。 |
| 16 | $-Rank[Cov_5(Rank(H),Rank(V))]$ | S:coupling; E:covariance; P:volume; R:High; X:MR; C:rank | #15のcovariance版。 |
| 17 | recent Close rank × price acceleration × V/ADV rank | S:price strength; E:2nd diff; P:V/ADV20; R:close; X:MR; C:time rank | 高い価格位置＋加速＋高relative volumeの組み合わせをoverextensionとして扱う。 |
| 18 | intraday range-vol + C-O + Corr(C,O)を逆rank | S:intraday volatility; E:C-O; P:-; R:O/C; X:MR; C:5/10d | 大きなintraday move・volatilityに対するcross-sectional reversal。 |
| 19 | $-sign(\Delta_7C)$ × long-term return rank | S:7d move; E:Δ7C; P:-; R:close; X:MR; C:250d return | 短期7d reversalをlong-term winner/loser状態でscale。 |
| 20 | Openと前日High/Close/Lowとの差のrank積 | S:overnight gap; E:open gap; P:-; R:prior H/C/L; X:MR; C:rank | Openが前日range全体から上方乖離するほどshort。gap reversal。 |

---

## Alpha #21-#40

`101 Formulaic Alphas.pdf`

| # | 数式・primitive signal | 6軸分類 | Stat-arb解釈 |
|---|---|---|---|
| 21 | 2d meanと8d mean±σを比較、通常時はV/ADV20 | S:MA deviation; E:short-term displacement; P:V/ADV; R:close vs MA; X:MR; C:σ | 短期価格がbandを越えた際のmean reversion。中立帯ではparticipation stateで方向決定。 |
| **22** | $-\Delta_5 Corr_5(H,V)\times Rank[\sigma_{20}(C)]$ | S:high dispersion; E:price-volume coupling shift; P:volume; R:High; X:**MR**; C:20d dispersion rank | **High-Volume couplingの急変へのcontrarian signal。高dispersion銘柄で増幅。** |
| 23 | High>20d avg Highなら$-\Delta_2H$ | S:high breakout; E:Δ2H; P:-; R:High vs MA; X:MR; C:trigger | high breakout後の短期reversal。 |
| 24 | long-term trend弱ならClose-100d lowに逆張り、強ければ3d reversal | S:100d trend; E:price displacement; P:-; R:100d low; X:MR; C:regime | 長期regimeに応じてreversal定義を切替える。 |
| 25 | $(-Return)\times ADV20\times VWAP\times(H-C)$ rank | S:down move; E:return; P:ADV; R:C below H/VWAP; X:MR; C:liquidity | 下落＋closeがhighから遠い＋高liquidityな銘柄をlong。liquidity-weighted reversal。 |
| 26 | $-\max_3 Corr_5[TsRank(V),TsRank(H)]$ | S:coupling; E:max recent ρ; P:volume; R:High; X:MR; C:rank | recent strongest High-Volume couplingへのcontrarian。 |
| 27 | VWAP-Volume correlation rankが高ければ-1、低ければ+1 | S:coupling regime; E:ρ(V,VWAP); P:volume; R:VWAP; X:MR/RV; C:binary | 強いvolume-VWAP couplingをnegative stateとして扱うbinary alpha。 |
| 28 | Corr(ADV20,Low)+midprice-Close | S:range location; E:close displacement; P:ADV; R:mid/close/low; X:MR; C:scale | Closeがrange midpointより低いほどlong。liquidity-low relationで補正。 |
| 29 | nonlinear close-change reversal + delayed negative return rank | S:multi-horizon return; E:close change; P:-; R:close; X:MR; C:nonlinear ranks | 複数時間軸のreversalを強く非線形化したcomposite。 |
| 30 | 最近3日方向性のrankを反転 × 5d/20d volume ratio | S:streak; E:return-sign sequence; P:volume ratio; R:close; X:MR; C:participation | 直近の方向的streakへの逆張りをrecent volume intensityでscale。 |
| 31 | 10d/3d close reversal + Corr(ADV20,Low) sign | S:short/medium move; E:ΔC; P:ADV; R:Low; X:MR; C:decay | multi-horizon price reversalにliquidity-low stateを加える。 |
| 32 | 7d mean-Close + long-horizon Corr(VWAP,lag Close) | S:mean deviation; E:local dislocation; P:VWAP; R:C vs 7d mean; X:MR/MIX; C:230d correlation | short-term mean reversion＋長期price-structure bias。 |
| 33 | $Rank(Open/Close-1)$ | S:intraday move; E:O→C; P:-; R:O/C; X:MR; C:rank | 当日上昇銘柄をshort、下落をlongする純粋intraday reversal。 |
| 34 | 2d/5d return-vol ratio＋1d price changeを双方反転rank | S:vol regime; E:Δ1C; P:-; R:close; X:MR; C:vol ratio | 短期volatility低下＋直近下落銘柄を選ぶreversal。 |
| 35 | volume TsRank × low price-location score × low return TsRank | S:low-return state; E:return rank; P:volume; R:H/L/C geometry; X:MR; C:multi-horizon | high participation下の弱いprice actionからのreversalを狙う。 |
| 36 | price/volume correlation、O-C、lagged returns、VWAP/ADV、200d mean等 | S:multi-state; E:multiple; P:ADV/volume; R:O/C/VWAP; X:MIX; C:weighted sum | price-action、participation、long-horizon anchorを統合したensemble alpha。 |
| 37 | Corr(lag O-C, C,200)+Rank(O-C) | S:intraday loss; E:O-C; P:-; R:O/C; X:MR; C:200d relation | 当日下落をlongするintraday reversalを長期serial relationで補正。 |
| 38 | $-Rank(TsRank(C,10))\times Rank(C/O)$ | S:recent price strength; E:intraday move; P:-; R:C/O; X:MR; C:10d rank | recent winnerかつ当日上昇銘柄をshort。 |
| 39 | 7d ΔClose × inverse relative-volume strength × 250d return | S:7d move; E:Δ7C; P:V/ADV; R:close; X:MR; C:long-term return | volume supportの弱いprice moveほど反転しやすいという仮説。 |
| 40 | $-Rank[\sigma_{10}(High)]\times Corr_{10}(High,V)$ | S:high-vol state; E:H-V coupling; P:volume; R:High; X:MR; C:vol | #22に近い。High-Volume couplingへのcontrarianをHigh volatilityで増幅。 |

---

## Alpha #41-#60

`101 Formulaic Alphas.pdf`

| # | primitive signal | 6軸分類 | Stat-arb解釈 |
|---|---|---|---|
| 41 | $\sqrt{HL}-VWAP$ | S:intraday value; E:VWAP displacement; P:VWAP; R:range midpoint; X:RV/MR; C:- | VWAPがrange-derived fair-priceより低ければlong。intraday relative-value。 |
| 42 | $Rank(VWAP-C)/Rank(VWAP+C)$ | S:late-day dislocation; E:C-VWAP; P:VWAP; R:Close vs VWAP; X:MR; C:price-level denominator | 論文自身がdelay-0 mean-reversionとして説明。`101 Formulaic Alphas.pdf` |
| 43 | TsRank(V/ADV20) × TsRank(-Δ7C) | S:recent decline; E:Δ7C; P:relative volume; R:close; X:MR; C:rank | high relative volume下での7d loserをlong。 |
| 44 | $-Corr_5(H,Rank(V))$ | S:H-V state; E:coupling; P:volume; R:High; X:MR; C:rank | High-Volume couplingへの短期contrarian。 |
| 45 | long price rank × Corr(C,V,2) × multi-horizon close correlationを負方向 | S:trend/coupling; E:price-volume sync; P:volume; R:close; X:MR; C:multi-horizon | 複数価格trendがvolumeと同期した状態をoverextensionとして扱う。 |
| 46 | 10d slopeの変化をthreshold判定、通常は1d reversal | S:trend acceleration; E:slope change; P:-; R:close; X:MIX; C:threshold | trend acceleration/deceleration regimeでsignalを切替える。 |
| 47 | low-price rank×V/ADV×High-close geometry - 5d VWAP change | S:range position; E:VWAP change; P:relative volume; R:H/C/VWAP; X:MIX; C:price level | high participation下のintraday dislocationとVWAP momentumの競合。 |
| 48 | long-run return autocorrelation × current return / variance、subindustry neutral | S:serial-dependence regime; E:1d return; P:-; R:close; X:MIX; C:subindustry neutral | 過去の自己相関がpositiveならmomentum、negativeならreversal。adaptive serial-dependence alpha。 |
| 49 | trend-slope changeが大幅ならconstant long、通常は1d reversal | S:acceleration; E:slope change; P:-; R:close; X:MIX; C:threshold | #46 variant。 |
| 50 | $-\max_5 Rank[Corr_5(Rank(V),Rank(VWAP))]$ | S:coupling; E:max ρ; P:volume; R:VWAP; X:MR; C:rank | recent extreme volume-VWAP couplingへのreversal。 |
| 51 | #49のthreshold変更 | S:trend acceleration; E:slope change; P:-; R:close; X:MIX; C:threshold | #49の感応度違い。 |
| 52 | 5d low floor変化 × long-minus-short return rank × volume TsRank | S:new low/trend; E:rolling low change; P:volume; R:Low; X:MIX/MR; C:240/20d | new-low eventをlong-horizon trendとparticipationで条件付け。 |
| 53 | 9d change of Close-location-in-range metricを反転 | S:range position; E:location change; P:-; R:H/L/C; X:MR; C:9d | close locationの構造変化へのcontrarian。delay-0。 |
| 54 | nonlinear $O/C$ とrange-location | S:intraday geometry; E:O/C; P:-; R:H/L/O/C; X:asymmetric; C:5th power | 強い非線形かつshort-biasedなrange-shape signal。通常の対称MR/MOM分類には馴染みにくい。 |
| 55 | $-Corr_6[Rank(range-position),Rank(V)]$ | S:range position; E:position-volume coupling; P:volume; R:12d range; X:MR; C:rank | range内位置とvolumeの同期に逆張り。 |
| 56 | return-shape ratio × return×market-capを負方向 | S:return shape; E:return; P:cap; R:close; X:MR; C:size | recent returnの形状をmarket-cap weighted return intensityでscaleしたreversal。 |
| 57 | $-(C-VWAP)/Decay[Rank(argmax_{30}C)]$ | S:distance to VWAP; E:C-VWAP; P:VWAP; R:VWAP/30d high; X:MR; C:high recency | Close>VWAPならshort、Close<VWAPならlong。recent-high timingでscale。 |
| 58 | sector-neutral VWAP-Volume correlationのdecay/TsRankを負方向 | S:sector-relative coupling; E:ρ; P:volume; R:VWAP; X:MR; C:sector-neutral | sector effectを除いたprice-volume couplingのmean reversion。 |
| 59 | industry-neutral VWAP-Volume correlation variant | S:industry-relative coupling; E:ρ; P:volume; R:VWAP; X:MR; C:industry-neutral | #58のindustry/parameter variant。 |
| 60 | close-in-range×Volume と recent-close-max timingの差 | S:range pressure; E:close location; P:volume; R:H/L/C; X:MIX; C:scale/rank | volumeを伴うclose-location pressureとrecent high timingのrelative-value。 |

---

## Alpha #61-#80

`101 Formulaic Alphas.pdf` `101 Formulaic Alphas.pdf`

| # | primitive signal | 6軸分類 | Stat-arb解釈 |
|---|---|---|---|
| 61 | VWAP-16d min VWAP vs Corr(VWAP,ADV180) | S:VWAP location; E:distance from low; P:ADV180; R:VWAP; X:RV; C:binary | price extensionとlong-horizon liquidity couplingのrelative comparison。 |
| 62 | VWAP-ADV20 couplingとOpen/High/Low geometryの比較 | S:price/liquidity structure; E:relative rank; P:ADV; R:O/H/L/VWAP; X:RV; C:binary | liquidity structureとintraday price geometryの不整合をsignal化。 |
| 63 | industry-neutral ΔClose - price/ADV180 correlation | S:industry-relative momentum; E:ΔC; P:ADV180; R:C/VWAP/O; X:MR/RV; C:industry-neutral | price moveがliquidity supportを上回る状態をoverextensionとして評価。 |
| 64 | weighted O/LとADV120のcoupling vs weighted mid/VWAP change | S:liquidity support; E:price change; P:ADV120; R:O/L/mid/VWAP; X:MR; C:binary | price moveがliquidity relationより強い時に反対方向。 |
| 65 | O/VWAP-ADV60 correlation vs Open-recent-min | S:open extension; E:distance from low; P:ADV60; R:Open/VWAP; X:MR; C:binary | liquidity supportに比べOpenが上方に伸びすぎた状態をshort。 |
| 66 | ΔVWAP decay + intraday geometry TsRankを負方向 | S:VWAP momentum; E:ΔVWAP; P:VWAP; R:VWAP vs O/mid; X:MR; C:decay | VWAP momentumとintraday displacementへのreversal。 |
| 67 | High-recent-min High × sector-neutral VWAP/ADV couplingを負方向 | S:high extension; E:breakout; P:ADV20; R:High; X:MR; C:sector/subindustry neutral | breakout＋liquidity couplingが強いほどshort。 |
| 68 | High-ADV15 coupling vs weighted C/L change | S:price-liquidity state; E:price change; P:ADV15; R:H/C/L; X:MR; C:binary | price changeがparticipation confirmationを上回る場合のreversal。 |
| 69 | industry-neutral ΔVWAP extreme × price-ADV20 couplingを負方向 | S:VWAP extension; E:ΔVWAP; P:ADV20; R:VWAP/C; X:MR; C:industry neutral | industry-relative price shock＋liquidity couplingへのcontrarian。 |
| 70 | ΔVWAP × industry-neutral Close-ADV50 couplingを負方向 | S:VWAP momentum; E:ΔVWAP; P:ADV50; R:VWAP/C; X:MR; C:industry neutral | positive VWAP moveとliquidity couplingの組合せをoverextension視。 |
| 71 | price-ADV180 couplingと$Low+Open-2VWAP$^2の最大 | S:coupling/dislocation intensity; E:-; P:ADV180; R:O/L/VWAP; X:RV; C:decay | directional signalより「price-liquidity dislocationの強さ」を測るfactor。 |
| 72 | mid-ADV40 coupling / VWAP-Volume coupling | S:relative coupling; E:-; P:ADV/volume; R:mid/VWAP; X:RV; C:ratio | 異なるprice-liquidity relationshipsの相対強度。 |
| 73 | ΔVWAPとweighted O/L returnのmaxを負方向 | S:short price momentum; E:Δprice; P:VWAP; R:O/L/VWAP; X:MIX/MR; C:decay | 二つのshort-horizon displacementのうち強い方へ逆方向。 |
| 74 | Close-ADV30 coupling vs weighted H/VWAP-Volume coupling | S:coupling competition; E:-; P:ADV/volume; R:H/C/VWAP; X:RV/MR; C:binary | broad liquidity supportよりlocal price-volume couplingが強い状態をnegative評価。 |
| 75 | VWAP-Volume corr vs Low-ADV50 corr | S:coupling structure; E:-; P:volume/ADV; R:VWAP/Low; X:RV; C:binary | price-level別のliquidity relationshipを比較。 |
| 76 | ΔVWAP + sector-neutral Low-ADV81 couplingを負方向 | S:VWAP momentum; E:ΔVWAP; P:ADV81; R:VWAP/Low; X:MR; C:sector neutral | positive price displacementまたは強いliquidity couplingをcontrarianに扱う。 |
| 77 | mid-VWAP dislocationとmid-ADV40 correlationのmin | S:relative value; E:mid-VWAP; P:ADV40; R:mid/VWAP; X:MR/RV; C:decay | VWAPがrange midpointより低く、liquidity relationも強い銘柄をlong。 |
| 78 | weighted Low/VWAP-ADV40 coupling × VWAP-Volume coupling | S:coupling intensity; E:-; P:ADV/volume; R:Low/VWAP; X:RV; C:power | 複数price-volume/liquidity couplingが同時に強い状態を強調。 |
| 79 | sector-neutral Δ(C/O) vs VWAP-ADV150 coupling | S:sector-relative move; E:price change; P:ADV150; R:C/O/VWAP; X:MR/RV; C:sector neutral | price moveよりliquidity structureが優勢な銘柄をpositive評価。 |
| 80 | industry-neutral O/H change × H-ADV10 couplingを負方向 | S:industry-relative price move; E:ΔO/H; P:ADV10; R:O/H; X:MR; C:industry neutral | positive price shift＋strong liquidity confirmationへのcontrarian。 |

---

## Alpha #81-#101

`101 Formulaic Alphas.pdf` `101 Formulaic Alphas.pdf`

| # | primitive signal | 6軸分類 | Stat-arb解釈 |
|---|---|---|---|
| 81 | persistent VWAP-ADV10 relation vs immediate VWAP-Volume corr | S:coupling regime; E:local coupling jump; P:ADV/volume; R:VWAP; X:MR; C:binary | long-horizon liquidity relationを上回る急激なlocal couplingをtemporary distortionとみなす。 |
| 82 | ΔOpen + sector-neutral Volume-Open correlationを負方向 | S:open momentum; E:ΔOpen; P:volume; R:Open; X:MR; C:sector neutral | opening-price momentumがstrong participationと共存する時のcontrarian。 |
| 83 | delayed range size × volume / current range divided by VWAP-Close | S:intraday range; E:C-VWAP; P:volume; R:H/L/C/VWAP; X:MR; C:range scaling | 符号は概ねVWAP-Close。Close<VWAPならlong、Close>VWAPならshort。 |
| 84 | TsRank(VWAP-recent VWAP max)をΔCloseでSignedPower | S:distance from VWAP high; E:price change; P:VWAP; R:recent max; X:MIX/RV; C:nonlinear | recent VWAP extremeとprice changeを強く非線形結合。単純MOM/MR解釈は弱い。 |
| 85 | H/C-ADV30 coupling ^ mid-Volume coupling | S:coupling intensity; E:-; P:ADV/volume; R:H/C/mid; X:RV; C:power | price-liquidity couplingの複合強度factor。 |
| 86 | Close-ADV20 coupling vs Close-VWAP | S:VWAP dislocation; E:C-VWAP; P:ADV20; R:C/VWAP; X:MR; C:binary | liquidity supportに比べCloseがVWAPから上に乖離しすぎる場合short。 |
| 87 | Δ(C/VWAP) + $|Corr(ADV81,C)|$ を負方向 | S:price momentum; E:Δprice; P:ADV81; R:C/VWAP; X:MR; C:industry neutral | positive short-term displacementまたは強いliquidity couplingをoverextension視。 |
| 88 | O/L vs H/C rank geometry + Close-ADV60 coupling | S:intraday shape; E:price geometry; P:ADV60; R:O/H/L/C; X:MR/MIX; C:decay | 弱いintraday closing structureをliquidity confirmation下でreversalする設計。 |
| 89 | Low-ADV10 coupling - industry-neutral ΔVWAP | S:coupling vs momentum; E:ΔVWAP; P:ADV10; R:Low/VWAP; X:MR/RV; C:industry neutral | liquidity structureがprice momentumを上回る銘柄をlong側評価。 |
| 90 | Close-recent max Close × Low-ADV40 couplingを負方向 | S:near recent high; E:breakout location; P:ADV40; R:Close/Low; X:MR; C:subindustry neutral | recent high付近＋strong liquidity relationをshortするbreakout reversal。 |
| 91 | industry-neutral Close-Volume coupling vs VWAP-ADV30 coupling | S:coupling spread; E:-; P:volume/ADV; R:C/VWAP; X:RV; C:industry neutral | 二種類のprice-participation relationshipのrelative-value。 |
| 92 | bearish intraday geometry × Low-ADV30 coupling | S:weak price shape; E:range geometry; P:ADV30; R:O/H/L/C; X:MR; C:binary/decay | bearish price configurationが強いparticipation relationを伴う時のreversal候補。 |
| 93 | industry-neutral VWAP-ADV81 coupling / Δ(C/VWAP) | S:coupling vs momentum; E:price change; P:ADV81; R:C/VWAP; X:RV/MR; C:industry neutral | liquidity couplingが強くprice momentumが弱い銘柄を優先。 |
| 94 | VWAP-recent min VWAP × VWAP-ADV60 couplingを負方向 | S:VWAP extension; E:distance from low; P:ADV60; R:VWAP; X:MR; C:rank | VWAPがrecent lowから大きく上昇しparticipation relationも強い状態をshort。 |
| 95 | Open-recent min vs midpoint-ADV40 coupling | S:open location; E:distance from low; P:ADV40; R:Open/mid; X:RV; C:binary | price extensionが小さくliquidity couplingが強い銘柄をpositive評価。 |
| 96 | VWAP-Volume corrのrecent strength＋Close-ADV60 corr peak timingを負方向 | S:coupling extreme; E:coupling peak; P:volume/ADV; R:C/VWAP; X:MR; C:time rank | price-volume couplingの極端化またはrecent peakをcontrarianに取る。 |
| 97 | industry-neutral Δ(Low/VWAP) vs Low-ADV60 coupling | S:price change vs liquidity; E:Δprice; P:ADV60; R:Low/VWAP; X:MR/RV; C:industry neutral | liquidity supportに比べprice displacementが大きい状態をrevert。 |
| 98 | VWAP-ADV5 coupling - timing of minimum Open-ADV15 coupling | S:coupling regime; E:coupling-extreme timing; P:ADV; R:O/VWAP; X:RV; C:decay | current liquidity couplingと過去のcoupling lowの時点を比較するstate factor。 |
| 99 | midpoint-ADV60 coupling vs Low-Volume coupling | S:local vs broad coupling; E:-; P:volume/ADV; R:mid/Low; X:MR/RV; C:binary | local Low-Volume relationがbroader liquidity structureを上回る時にnegative。 |
| 100 | subindustry-neutral close-location×Volume - Close/ADV relation＋recent low timing、V/ADVでscale | S:range location; E:price/liquidity imbalance; P:volume/ADV; R:H/L/C; X:MR/RV; C:subindustry neutral | price pressure、liquidity relation、recent-low timingを統合したmicrostructure-style composite。 |
| 101 | $(C-O)/(H-L+0.001)$ | S:intraday directional efficiency; E:O→C move; P:-; R:range-normalized body; X:**MOM**; C:range normalization | intraday rangeに対して一方向に強く動いた銘柄の翌日continuation。論文自身がdelay-1 momentumと説明。`101 Formulaic Alphas.pdf` |

---

# 3. 101個を俯瞰すると、実は少数の「alpha family」にまとめられる

この一覧から重要なのは、101個が101種類の独立した経済仮説なのではなく、大半が以下のprimitiveを組み替えたものだという点です。

$$
\boxed{
Price\ Location
}
$$

- Close vs VWAP
- Open vs prior range
- Close in High-Low range
- distance from rolling high/low

と、

$$
\boxed{
Participation / Liquidity
}
$$

- Volume
- Volume / ADV
- price-volume correlation
- price-ADV correlation

と、

$$
\boxed{
State\ Change
}
$$

- delta
- correlation change
- rolling extrema
- TsRank
- decay

を組み合わせています。

そのうえで最終的には、

$$
\boxed{
Momentum
\quad\text{or}\quad
Mean\ Reversion
}
$$

へ変換しています。

特に **#2、#12-16、#22、#26、#40、#44、#50、#55、#58-59、#69-70、#81、#96、#99** は、広い意味で

$$
\boxed{\text{Price × Participation Interaction}}
$$

という同じfamilyに置けます。

その中でも#22は、

$$
Corr(H,V)
$$

そのものではなく、

$$
\boxed{\Delta Corr(H,V)}
$$

を使う点が特徴的です。

つまり単なる「出来高を伴った価格変化」ではなく、

> **price formationとmarket participationの結び付き方そのものが変わった瞬間**

をeventとして捉えています。

これが、短期statistical arbitrageとして#22を特に研究する価値がある理由です。

## #22を研究上もう一段厳密に分解するなら

次の3つを別々に検証するのが最も重要です。

$$
A_t=-\Delta Corr_5(H,V)
$$

$$
B_t=Rank[\sigma_{20}(C)]
$$

$$
\alpha_{22,t}=A_tB_t
$$

まず、

$$
IC(A),\quad IC(B),\quad IC(A\times B)
$$

を比較します。

次に、

$$
A\text{ quintile}\times B\text{ quintile}
$$

の **5×5 dependent sort** を作ります。

もし提示されたeconomic storyが正しいなら、

$$
\left|\Delta Corr(H,V)\right|\uparrow
$$

かつ

$$
VolRank\uparrow
$$

のcorner portfolioほど将来returnの反転が強くなるはずです。

さらに #22 の「量価構造急変 → overextension → reversal」という説明を本当に検証するには、

$$
\Delta\rho
\times
PastReturn
\times
VolRank
$$

まで分解する必要があります。

特に、

$$
\Delta\rho>0,\ PastReturn>0
$$

の翌期returnが有意に負であれば、

> **participationを伴って形成された上方price-pressureの急激な強まりが短期的overextensionを示す**

という解釈をかなり強く支持できます。

逆にここが出なければ、#22は「価格上昇の反転」ではなく、より抽象的な **price-volume coupling stateのcross-sectional anomaly** と理解すべきです。

この区別が、#22を単なるテクニカル指標からstatistical-arbitrage factorへ引き上げるうえで最も重要です。

## Response:
2026/9/29 23:22:28 · gpt-5-6-thinking

> **実装方針を整理**
>
> 私は、論文の式をそのまま再現できる最小構成を作る。株価・出来高から、2日・5日・20日リターン、出来高比、zスコア、順位、検証用リターンを計算する。
>
> **検証方法を整理**
>
> 私は、時点𝑡のシグナルを翌営業日のオープンからクローズまでのリターンと対応させる。符号付き逆相関と出来高順位の5×5分位表、日次IC、ICIRを計算し、 close-to-closeも比較する。
>
> **検証方法を整理した**
>
> 
>
> 1m 27s考えました

はい。#22については、まず **「原式そのものに予測力があるか」→「どのcomponentが効いているか」→「提示したeconomic narrativeと整合するか」** の3段階だけに絞れば、かなり簡潔なNotebookで検証できます。

原式は次です。

$$
\alpha_{22,t}
=
-\Delta_5 Corr_5(High,Volume)
\times
Rank_{CS}\left[Std_{20}(Close)\right]
$$

`101 Formulaic Alphas.pdf`

ここでは、

$$
A_t=-\Delta_5 Corr_5(High,Volume),\qquad
B_t=Rank_{CS}[Std_{20}(Close)]
$$

として、

$$
\alpha_{22}=A\times B
$$

に分解します。`rank` はcross-sectional rank、`delta(x,d)=x_t-x_{t-d}` です。`101 Formulaic Alphas.pdf`

---

## 最小構成の検証Notebook

日本株を `yfinance` から取得する想定です。実際にはcross-sectional rankを使うため、**少なくとも50～100銘柄、できればTOPIX500程度**まで広げる方がよいです。

```python
import numpy as np
import pandas as pd
import yfinance as yf

# ============================================================
# 0. Universe
# ============================================================

# まずは動作確認用。
# 本検証では100～500銘柄程度へ拡張してください。
TICKERS = [
    "7203.T", "6758.T", "9984.T", "8306.T", "6501.T",
    "8035.T", "6857.T", "4063.T", "6098.T", "9432.T",
    "8058.T", "8001.T", "8316.T", "8766.T", "7267.T",
    "4502.T", "4519.T", "4568.T", "6902.T", "6594.T",
]

START = "2020-01-01"
END   = None

raw = yf.download(
    TICKERS,
    start=START,
    end=END,
    auto_adjust=False,
    progress=False,
    group_by="column"
)

open_  = raw["Open"]
high   = raw["High"]
close  = raw["Close"]
volume = raw["Volume"]
```

---

# 1. Alpha #22を忠実に作る

これが最重要部分です。

```python
# ============================================================
# 1. Original Alpha #22
# ============================================================

# Corr(High, Volume, 5)
corr5 = high.rolling(5).corr(volume)

# DELTA(CORR(..., 5), 5)
delta_corr5 = corr5 - corr5.shift(5)

# STD(Close, 20)
std20_close = close.rolling(20).std()

# RANK = cross-sectional percentile rank
vol_rank = std20_close.rank(axis=1, pct=True)

# Component A
A = -delta_corr5

# Component B
B = vol_rank

# Alpha #22
alpha22 = A * B

alpha22.tail()
```

このコードの

```python
corr5 - corr5.shift(5)
```

が重要です。

概ね、

$$
Corr(H,V)_{t-4:t}
-
Corr(H,V)_{t-9:t-5}
$$

なので、**隣接する二つの5日windowでprice-volume couplingがどう変わったか**を見ています。

---

# 2. 翌日リターンを作る

#22は論文上delay-0 alphaではありません。論文ではdelay-0として明示されているのは #42, #48, #53, #54 なので、#22は翌日執行として扱うのが自然です。`101 Formulaic Alphas.pdf`

簡易検証では、

$$
t+1:\ Open\rightarrow Close
$$

を使うのが分かりやすいです。

```python
# ============================================================
# 2. Forward Return
# ============================================================

# signal at t close -> trade next day's open -> next day's close
fwd_ret_1d = close.shift(-1) / open_.shift(-1) - 1

# 参考：close-to-closeも比較可能
fwd_ret_cc = close.shift(-1) / close - 1
```

---

# 3. A、B、A×BのICを比較する

ここで、

$$
IC(A),\qquad IC(B),\qquad IC(A\times B)
$$

を比較します。

これによって、

> #22の予測力は本当にprice-volume coupling shiftから来ているのか、それとも単純にvolatility rankから来ているのか

を切り分けられます。

```python
# ============================================================
# 3. Cross-sectional IC / ICIR
# ============================================================

def calc_ic(signal, forward_return, min_obs=10):
    """
    Daily cross-sectional Spearman IC
    """
    s = signal.rank(axis=1, pct=True)
    r = forward_return.rank(axis=1, pct=True)

    ic = s.corrwith(r, axis=1)

    # small cross-section datesを除外
    n = signal.notna().mul(forward_return.notna()).sum(axis=1)
    ic = ic[n >= min_obs].dropna()

    return {
        "Mean IC": ic.mean(),
        "IC Std": ic.std(),
        "ICIR (ann.)": ic.mean() / ic.std() * np.sqrt(252),
        "Positive IC Ratio": (ic > 0).mean(),
        "N days": len(ic),
    }, ic

result_A, ic_A = calc_ic(A, fwd_ret_1d)
result_B, ic_B = calc_ic(B, fwd_ret_1d)
result_AB, ic_AB = calc_ic(alpha22, fwd_ret_1d)

ic_summary = pd.DataFrame({
    "A = -ΔCorr(H,V)": result_A,
    "B = VolRank": result_B,
    "Alpha22 = A×B": result_AB,
}).T

display(ic_summary)
```

見るべき比較は単純です。

| 結果 | 解釈 |
|---|---|
| IC(A) > 0 | price-volume coupling shift自体に予測力 |
| IC(B) ≈ 0 | volatility単独ではalphaでない |
| IC(A×B) > IC(A) | high-vol stateでAが強くなる |
| IC(A×B) ≈ IC(A) | volatility conditioningは不要かもしれない |
| IC(B)だけ強い | #22のeconomic storyに疑問 |

理想的には、

$$
IC(A\times B)>IC(A)>0
$$

で、

$$
IC(B)\approx0
$$

です。

そうなれば、

> 「高volatilityだから儲かる」のではなく、「price-volume coupling shockのpredictabilityがhigh-vol銘柄で増幅される」

という#22の構造を支持します。

---

# 4. 最重要：5×5 Portfolio Sort

次に

$$
A=-\Delta Corr(H,V)
$$

を5分位、

$$
B=VolRank
$$

を5分位にして、

$$
5\times5
$$

portfolioを作ります。

```python
# ============================================================
# 4. 5 x 5 Portfolio Sort
# ============================================================

def to_quintile(df):
    pct = df.rank(axis=1, pct=True)
    q = np.ceil(pct * 5)
    return q.clip(1, 5)

qA = to_quintile(A)
qB = to_quintile(B)

panel = pd.DataFrame({
    "A_quintile": qA.stack(),
    "B_quintile": qB.stack(),
    "fwd_ret": fwd_ret_1d.stack(),
}).dropna()

sort_5x5 = (
    panel
    .groupby(["A_quintile", "B_quintile"])["fwd_ret"]
    .mean()
    .unstack()
)

# basis points
sort_5x5_bps = sort_5x5 * 10_000

display(sort_5x5_bps.round(2))
```

ここで行が

$$
A=-\Delta\rho
$$

なので、

- A=1 → $\Delta\rho$ が大きくpositive → short側
- A=5 → $\Delta\rho$ が大きくnegative → long側

です。

#22が想定通りなら、高volatility列、

$$
B=5
$$

で、

$$
Return(A=5,B=5)
>
Return(A=1,B=5)
$$

というspreadが強くなるはずです。

---

## Volatility別のLong-Short spread

これをさらに簡単に数値化できます。

```python
ls_by_vol = (
    sort_5x5.loc[5]
    - sort_5x5.loc[1]
) * 10_000

ls_by_vol.name = "Long-Short spread (bps)"

display(ls_by_vol.to_frame())
```

期待する形は、

$$
Spread_{B=1}
<
Spread_{B=2}
<
\cdots
<
Spread_{B=5}
$$

です。

完全に単調である必要はありませんが、

> **High-volatility universeほど $-\Delta Corr(H,V)$ のspreadが大きい**

なら、#22のinteraction interpretationを強く支持します。

---

# 5. 本当に「overextension → reversal」なのかを検証する

ここが今回のeconomic narrativeに対する核心です。

まず過去5日returnを追加します。

```python
# ============================================================
# 5. Mechanism test
# ============================================================

past_ret_5d = close / close.shift(5) - 1

# |ΔCorr|のcross-sectional rank
event_rank = delta_corr5.abs().rank(axis=1, pct=True)

mechanism = pd.DataFrame({
    "delta_corr": delta_corr5.stack(),
    "past_ret_5d": past_ret_5d.stack(),
    "vol_rank": vol_rank.stack(),
    "event_rank": event_rank.stack(),
    "fwd_ret": fwd_ret_1d.stack(),
}).dropna()

# Strong regime shift + High volatilityだけを抽出
strong = mechanism[
    (mechanism["event_rank"] >= 0.8) &
    (mechanism["vol_rank"] >= 0.8)
].copy()

strong["corr_shift"] = np.where(
    strong["delta_corr"] > 0,
    "ΔCorr > 0",
    "ΔCorr < 0"
)

strong["past_direction"] = np.where(
    strong["past_ret_5d"] > 0,
    "Past Return > 0",
    "Past Return < 0"
)

mechanism_summary = (
    strong
    .groupby(["corr_shift", "past_direction"])["fwd_ret"]
    .agg(["mean", "std", "count"])
)

mechanism_summary["mean_bps"] = mechanism_summary["mean"] * 10_000

mechanism_summary["t_stat"] = (
    mechanism_summary["mean"]
    /
    (mechanism_summary["std"] /
     np.sqrt(mechanism_summary["count"]))
)

display(
    mechanism_summary[
        ["mean_bps", "t_stat", "count"]
    ].round(3)
)
```

この表が非常に重要です。

今回の仮説で特に見たいセルは、

$$
\boxed{
\Delta Corr>0
\quad\&\quad
PastReturn>0
}
$$

です。

もしこのセルで、

$$
E[R_{t+1}]<0
$$

かつ十分なt-statが出るなら、

> HighとVolumeのcouplingが急激にpositive方向へ強まり、かつ実際に価格も上昇していた銘柄では、翌日reversalしやすい

と言えます。

これはかなり直接的に、

$$
\text{Price-volume coupling shock}
\rightarrow
\text{Overextension}
\rightarrow
\text{Reversal}
$$

という説明を支持します。

---

# 6. Alpha #22そのもののLong-Short

最終的にはalpha scoreのtop/bottom quintileだけでも確認します。

```python
# ============================================================
# 6. Simple Long-Short Backtest
# ============================================================

pct_rank = alpha22.rank(axis=1, pct=True)

long_mask  = pct_rank >= 0.8
short_mask = pct_rank <= 0.2

# equal-weight long / short
long_w = long_mask.div(long_mask.sum(axis=1), axis=0)
short_w = short_mask.div(short_mask.sum(axis=1), axis=0)

weights = 0.5 * long_w - 0.5 * short_w

strategy_ret = (weights * fwd_ret_1d).sum(axis=1).dropna()

ann_ret = strategy_ret.mean() * 252
ann_vol = strategy_ret.std() * np.sqrt(252)
sharpe = ann_ret / ann_vol

cum = (1 + strategy_ret).cumprod()

print(f"Annualized Return : {ann_ret:.2%}")
print(f"Annualized Vol    : {ann_vol:.2%}")
print(f"Sharpe            : {sharpe:.2f}")
print(f"N days            : {len(strategy_ret)}")

cum.plot(
    figsize=(12, 5),
    title="Alpha #22 Long-Short cumulative return"
);
```

これはあくまで**signal validation用**です。

原論文のproduction implementationを再現しているわけではありません。論文はalpha formulaを公開していますが、完全なportfolio constructionやexecution methodologyまでは公開していません。

---

# 7. Turnoverも最低限見る

短期alphaなので、Sharpeだけでは危険です。

```python
# ============================================================
# 7. Turnover
# ============================================================

turnover = (
    weights
    .fillna(0)
    .diff()
    .abs()
    .sum(axis=1)
)

print("Average daily turnover:",
      turnover.mean())

print("Approx holding period:",
      1 / turnover.mean()
      if turnover.mean() > 0 else np.nan)
```

原論文自体でも101 alphaの平均保有期間は非常に短く、約0.6～6.4日です。`101 Formulaic Alphas.pdf`

したがってgross Sharpeが高くても、

$$
Turnover
\times
TransactionCost
$$

で消える可能性があります。

---

# 8. 私ならもう1つだけRobustnessを入れる

原式には少し気になる点があります。

$$
Std(Close,20)
$$

なのでprice level依存があります。

そこで原式を変更せずbenchmarkとして残した上で、

$$
Std(Return,20)
$$

版を比較します。

```python
# ============================================================
# 8. Robustness:
#    Close-volatility vs Return-volatility
# ============================================================

ret = close.pct_change()

return_vol20 = ret.rolling(20).std()

return_vol_rank = (
    return_vol20
    .rank(axis=1, pct=True)
)

alpha22_retvol = A * return_vol_rank

result_original, _ = calc_ic(
    alpha22,
    fwd_ret_1d
)

result_retvol, _ = calc_ic(
    alpha22_retvol,
    fwd_ret_1d
)

robustness = pd.DataFrame({
    "Original Std(Close)": result_original,
    "Std(Return)": result_retvol,
}).T

display(robustness)
```

もし

$$
Std(Return)
$$

版でも同じ現象が出れば、

> 単なる株価水準の違いではなく、本当にvolatility stateがprice-volume coupling signalを増幅している

という説明が強くなります。

---

# この簡易実験で何が分かるか

最終的には次の4点だけ確認すれば十分です。

| 検証 | 支持される仮説 |
|---|---|
| $IC(A)>0$ | $-\Delta Corr(H,V)$ 自体に情報がある |
| $IC(A\times B)>IC(A)$ | high-vol stateでsignalが強まる |
| 5×5でhigh-volほどAのspread拡大 | volatilityとのinteractionが存在 |
| $\Delta Corr>0,\ PastReturn>0$ の翌日return<0 | upward overextension → reversalというeconomic story |

特に最後が重要です。

**Alpha #22そのものが効くこと**と、

> 「量価構造の急変＋高volatility → 感情的overextension → mean reversion」

という**説明が正しいことは別問題**です。

したがって、単なるSharpeの確認で終わらず、

$$
\boxed{
\Delta Corr(H,V)
\times
PastReturn
\times
Volatility
}
$$

まで分解することで、先ほどのeconomic interpretationそのものを検証できます。

この程度のコードであれば、#22の「再現」ではなく**メカニズム検証の最小実験**として十分に機能します。実際の研究ではこの後、sector/size/volatility neutralization、IC decay、Long/Short別寄与、transaction cost、subperiod robustnessを追加する順序が自然です。

## Response:
2026/9/29 23:39:05 · gpt-6-pro

#22をHigh・Low・VWAPへ拡張し、突破後のrejection／acceptanceまで捉える設計を検討します。Liquidity sweep等は、OHLCVで作れる代理変数と約定・板データが必要な部分を分離します。

> **整えている情報源**
>
> 検索結果には無関係なものも多いので、まず主要な資料を軸に整理している。数学的な提案は自分の説明として示し、必要な事実だけを一次資料や学術的な文献で支える方針にしている。
>
> **設計を整理する**
>
> 私は、公式資料によるVWAP定義と基礎文献を分けて扱いながら、変数、正規化、イベント条件、時間粒度、データ制約を明確化していく。ATRや出来高比率も定義し、用語の混同を避ける。
>
> **情報源を整え設計を整理した**
>
> 
>
> **条件式を明確化**
>
> 私は、上下の拒否イベントを事前レンジ、終値、ヒゲ幅で定義し、窓開けや同日両方向突破は別扱いにする。方向スコアは複雑な積を避け、正規化した拒否幅を上下で差し引く形が扱いやすいと考えている。
>
> **条件式を明確化した**
>
> 
>
> **比較指標を設計**
>
> 私は、拒否イベントの強度、出来高、相関変化、状態遷移を組み合わせた候補を比較する。まずは単純な基本式を採用し、追加の出来高や順位調整は別仕様として、過適合を避けながら段階的に検証していく。
>
> **比較指標を設計した**
>
> 
>
> **20件のウェブサイトを検索しました**
>
> 
>
> **PDFスキルの確認**
>
>
> **PDFスキルを確認した**
>
> 
>
> **検証した日次ポートフォリオ統計と出来高指標**
>
> 
>
> **組み立てを確定する**
>
> 私は、VWAPなどの定義を一次資料で確認し、検証可能な最小モデルを中心に据える。説明は、観測可能性、正規化、候補指標、データ粒度、検証手順の順に整理する。
>
> **構成を固める**
>
> 私は、イベント定義、強度スコア、出来高やVWAP、価格形成レジーム、検証設計の順にまとめる。最終的には、解釈しやすく過適合しにくい中核要素を三つに絞って提案する。
>
> **組み立てと構成を確定した**
>
> 
>
> **19件のウェブサイトを検索しました**
>
> 
>
> 14m 40s考えました

**できます。ただし、HighをLowやVWAPに置き換えるだけでは、Liquidity sweepやprice deliveryの表現としては不十分です。** 有効な拡張は、#22を「価格と出来高の結び付きが急変したことを捉える部分」として残し、別途、**どの価格帯を試したか、その価格帯が拒否されたか、あるいは受容されたか**を識別する構造です。

具体的には、次の役割分担が適しています。

| 役割 | 使用する情報 | 表現したい状態 |
|---|---|---|
| 価格探索の場所 | High・Lowと過去の高安値 | 既知のレンジ境界を突破したか |
| 探索の結果 | Close、VWAP、突破した水準との位置関係 | レンジ内へ戻されたか、外側へ移行したか |
| 価格の偏り | Close-VWAP、High-VWAP、VWAP-Low | 当日の約定価格中心からどちらへ偏ったか |
| 価格形成の変化 | それらと出来高の相関変化 | 参加量と価格形成の関係が急変したか |
| 売買方向 | Rejection／Acceptanceの分類 | 反転仮説か、継続仮説か |

以下では、**原論文・noteの概念に由来する部分と、今回提案する定量化を区別**して整理します。提示する拡張式は研究仮説であり、有効性を確認した結果ではありません。

# 1. 最初に整理すべきこと：Sweep、imbalance、deliveryは別の情報

はなまる氏の実践編では、Sweepは「何が取られたか」、Market Structure Shiftは「deliveryが変化したか」を確認するものとして分けられています。また、MCRTの記事では、レンジ外へ出た後に定着することをAcceptance、戻されることをRejectionと説明しています。**したがって、Sweepらしい形が出たことだけを理由に、すべて逆張りにするのは、この枠組みとも整合しません。** ([note（ノート）](https://note.com/hanamaru_fx01/n/n36aa7b88155a))

この点は市場マイクロストラクチャーの研究とも矛盾しません。例えばOslerの為替市場研究では、ストップ注文は価格変化を加速させ、トレンドを伝播させる場合が示されています。ただし、これは為替市場に関する結果で、日本株の日次反転を直接裏付けるものではありません。([ニューヨーク連邦準備銀行](https://www.newyorkfed.org/research/staff_reports/sr150.html))

今回の研究では、次の区別を維持します。

| 概念 | 日次データで構成できる代理変数 | その変数だけでは識別できないもの |
|---|---|---|
| Liquidity sweep | 過去高安値の突破と、その後のレンジ内への回帰 | 実際にストップ注文が集中・発動したか |
| Price imbalance | VWAP乖離、終値位置、FVG形状 | 実際の買い主導・売り主導注文の不均衡 |
| Price delivery | 値動きの方向、実体の大きさ、VWAPの移動、価格帯の受容・拒否 | 注文主体の意図、日中の詳細なイベント順序 |

特に、**総出来高はorder-flow imbalanceではありません。** Cont・Kukanov・Stoikovは、米国株の短時間の価格変化について、最良気配での需給変化を捉えたorder-flow imbalanceとの関係を分析しており、単純な取引出来高との関係はそれより不安定と報告しています。OHLCVから作る指標は、この意味でのOFIとは区別すべきです。([arXiv](https://arxiv.org/abs/1011.6402))

---

# 2. #22の拡張を二段階に分ける

原式は、

$$
\alpha^{22}_{i,t}
=
-\Delta_5\operatorname{Corr}_5(H_i,V_i)_t
\cdot
\operatorname{Rank}_{CS}\!\left[\operatorname{Std}_{20}(C_i)_t\right]
$$

です。原論文の`rank`は銘柄間順位、`correlation`は時系列相関、`delta`は指定日数前との差です。`101 Formulaic Alphas.pdf` `101 Formulaic Alphas.pdf`

以下では、相関変化を

$$
\mathcal D_t(X,Y)
=
\operatorname{Corr}_5(X,Y)_t
-
\operatorname{Corr}_5(X,Y)_{t-5}
$$

と書きます。

## 第一段階：価格入力だけを変える

まずは、

$$
\alpha^{P}_t
=
-\mathcal D_t(P,V)\,B_t,
\qquad
P\in\{H,L,W\}
$$

を比較します。$W$はVWAP、$B_t$は原式の終値標準偏差の順位です。

| 入力 | 測っているもの |
|---|---|
| $H$ | 高値水準と出来高の結び付きの変化 |
| $L$ | 安値水準と出来高の結び付きの変化 |
| $W$ | 約定価格の加重平均と出来高の結び付きの変化 |

これは、**#22がHigh固有の情報を利用しているのか、単に価格系列全般と出来高の関係を利用しているのか**を調べる対照実験です。

ただし、Low版を自動的に「下方Sweepを買うシグナル」と解釈することはできません。Lowが上昇しながら出来高が増える場合にも正の相関は生じます。High版と同様、相関の変化だけでは、価格探索の方向や拒否・受容を特定できないためです。

## 第二段階：価格水準から「位置・形状・状態遷移」へ変える

今回の目的により近いのはこちらです。

$$
\boxed{
\text{価格水準と出来高の関係}
\quad\longrightarrow\quad
\text{価格の相対位置・探索結果と出来高の関係}
}
$$

以降では、この第二段階を具体化します。

# 3. 共通の正規化：株価水準の影響を外す

銘柄間で価格差を比較するため、価格単位の正規化量として、

$$
a_t=\operatorname{ATR}_{20,t-1}
$$

を使うことを提案します。ここではATRを、前日までの20日間のTrue Rangeの平均と定義します。分母を前日までで固定することで、当日の大きな変動が同時に分母を押し上げる影響を避けます。

参加量は、

$$
RVOL_t
=
\frac{V_t}
{\frac1{20}\sum_{j=1}^{20}V_{t-j}},
\qquad
q_t=\log RVOL_t
$$

で表します。

この分母は**株数出来高の平均**です。原論文の`adv`は平均日次売買代金と定義されているため、ここでは混同を避けて`RVOL`と呼びます。`101 Formulaic Alphas.pdf`

また、原式の

$$
B_t=\operatorname{Rank}_{CS}[\operatorname{Std}_{20}(C)]
$$

は価格水準の影響を受けるので、拡張版の初期実験では、**まず追加のボラティリティ倍率を掛けずに検証**するのがよいです。その後に、原式の$B_t$とリターン・ボラティリティ順位を別々に追加し、何が改善したかを切り分けます。

---

# 4. Liquidity sweep：High・Lowを「過去の境界」と比較する

## 4.1 事前に存在する高安値を定義する

過去 $K$ 日の高値・安値を、

$$
u_t=\max_{1\le j\le K}H_{t-j},
\qquad
\ell_t=\min_{1\le j\le K}L_{t-j}
$$

とします。

重要なのは、**当日を含めないこと**です。初期設定は例えば $K=20$ とし、後から結果に合わせて最適な期間を選ばないようにします。

これらは「ストップ注文の所在を観測した値」ではなく、**価格探索の基準として事前に定義した境界**です。

## 4.2 上方探索の拒否と、下方探索の拒否を分ける

上方の拒否候補は、

$$
I^U_t
=
\mathbf1\{H_t>u_t,\ C_t<u_t\}
$$

です。過去高値を上抜いたものの、終値ではその水準より下へ戻っています。

下方の拒否候補は、

$$
I^D_t
=
\mathbf1\{L_t<\ell_t,\ C_t>\ell_t\}
$$

です。

初版ではさらに、始値が旧レンジ内にある日だけに限定すると、寄り付きのギャップと、日中に境界を試した事象を分けやすくなります。両側を突破した日は別カテゴリーにし、機械的に売買方向を決めない方がよいです。

## 4.3 二値判定を「探索の深さ×拒否の強さ」に拡張する

例えば、

$$
S^U_t
=
I^U_t
\underbrace{\frac{H_t-u_t}{a_t}}_{\text{上方への突破幅}}
\underbrace{\frac{H_t-C_t}{H_t-L_t}}_{\text{高値からの押し戻し}}
$$

$$
S^D_t
=
I^D_t
\underbrace{\frac{\ell_t-L_t}{a_t}}_{\text{下方への突破幅}}
\underbrace{\frac{C_t-L_t}{H_t-L_t}}_{\text{安値からの回復}}
$$

とします。

反転仮説の基礎シグナルは、

$$
\boxed{
A^{sweep}_t=S^D_t-S^U_t
}
$$

です。

これは、下方探索が拒否された場合を買い方向、上方探索が拒否された場合を売り方向とする設計です。ただし、**当日すでに戻ったことを検出しているのであって、その後にも利益機会が残ることは別途検証が必要**です。

## 4.4 VWAPで回復・押し戻しを確認する

さらに、

$$
R_t
=
S^D_t\mathbf1\{C_t>W_t\}
-
S^U_t\mathbf1\{C_t<W_t\}
$$

とします。

この確認版では、下方探索後に当日の平均約定価格より上まで回復した場合、あるいは上方探索後に平均約定価格より下まで押し戻された場合を重視します。

ここでのVWAPは「公正価値」ではなく、**その日の実際の取引が形成した価格の加重平均**です。

## 4.5 #22の相関変化を組み込む

High・Lowそれぞれの量価関係の変化を、

$$
\Gamma_t
=
\frac{
|\mathcal D_t(H,V)|
+
|\mathcal D_t(L,V)|
}{2}
$$

とまとめ、例えば、

$$
\boxed{
A^{sweep22}_t
=
R_t(1+\Gamma_t)
}
$$

を提案します。

これは、

> **価格探索の拒否から売買方向を決め、その事象が量価関係の急変を伴う場合に強調する**

という設計です。

ただし重要な違いがあります。原式は$-\mathcal D(H,V)$が方向を決めますが、この拡張では**拒否された側が方向を決め、相関変化は強度を調整します**。したがって、原式の単なるパラメータ変更ではなく、#22の考え方を用いた別のアルファ仮説です。

---

# 5. Imbalance：VWAP乖離は有用だが、三つの概念を分ける

## 5.1 VWAP周りの価格形状

まず、次の変数が使えます。

| 変数 | 定義 | 観測しているもの |
|---|---|---|
| 上方への広がり | $\displaystyle e^U_t=\frac{H_t-W_t}{a_t}$ | 当日VWAPから高値までの距離 |
| 下方への広がり | $\displaystyle e^D_t=\frac{W_t-L_t}{a_t}$ | 当日VWAPから安値までの距離 |
| 引け時点の乖離 | $\displaystyle d_t=\frac{C_t-W_t}{a_t}$ | 終値が当日の約定価格中心からどちらへ偏ったか |
| レンジ内の終値位置 | $\displaystyle CLV_t=\frac{2C_t-H_t-L_t}{H_t-L_t}$ | 終値が高値側・安値側のどちらに位置するか |

これらは「価格の偏り」を表しますが、**どちらの側の成行注文が多かったかを直接表すものではありません。**

また、

$$
e^U_t+e^D_t=\frac{H_t-L_t}{a_t}
$$

なので、上方・下方への広がりを足したものは、単に正規化された値幅です。複数変数を投入する際には、このような重複を確認する必要があります。

## 5.2 VWAP乖離と出来高の相関変化

#22の形を直接引き継ぐなら、

$$
\boxed{
A^{dev22}_t
=
-\mathcal D_t(d,q)
}
$$

が候補です。

解釈は、

> **終値のVWAP乖離と異常出来高の結び付きが、直前の状態からどう変化したか**

です。

例えば、出来高の多い日に終値がVWAPより上へ位置する関係が急に強くなれば、負方向のシグナルになります。

ただし、ここでも「上方乖離が急に拡大した」とは限りません。負だった相関がゼロへ近づいた場合にも同じ符号になるため、**現在の$d_t$の符号・大きさを併せて見ることが必要**です。

経済的解釈を優先するなら、別案として、

$$
\boxed{
A^{dev\text{-}MR}_t
=
-d_t\left(1+|\mathcal D_t(d,q)|\right)
}
$$

を使えます。

こちらは、方向をVWAP乖離から決め、量価関係の急変を増幅要因にしています。ただし、これはあくまで**VWAP乖離が解消するという仮説**であり、後述する継続型との比較が欠かせません。

なお、VWAP乖離への逆張り自体は原論文にもあります。#42はVWAP-Closeの順位比、#57はClose-VWAPを用いた逆張りであり、#55はレンジ内の価格位置と出来高の相関を使います。したがって今回の研究で問うべき新しい点は、**VWAPを使ったことではなく、相関変化や拒否・受容の条件付けが追加的な情報を持つか**です。`101 Formulaic Alphas.pdf` `101 Formulaic Alphas.pdf`

## 5.3 FVGとしてのimbalance

はなまる氏の記事では、Bullish FVGは、3本のローソク足の1本目のHighと3本目のLowが重ならない形として説明されています。同時に、FVGは強い値動きの痕跡であって、必ず埋まるものではないとされています。([note（ノート）](https://note.com/hanamaru_fx01/n/ne97f8602bb27))

その幾何学的な部分は、

$$
FVG^+_t
=
\frac{(L_t-H_{t-2})_+}{a_t},
\qquad
FVG^-_t
=
\frac{(L_{t-2}-H_t)_+}{a_t}
$$

で表現できます。ここで$(x)_+=\max(x,0)$です。

ただし、**この形は「その価格帯で取引がなかった」ことを意味しません。中央の足ではその価格帯を取引している可能性があるからです。**

また、日足で計算すれば、日中の一方向の動きだけでなく、寄り付きギャップを含む3日間の形状になります。日中のICT/SMC概念と対応づけるなら、分足で計算する方が時間的な対応は明確です。

FVGは初期段階では売買方向を決める主因ではなく、

> Sweep候補の後に、反対方向の強い価格移動が実際に生じたか

を調べる補助変数として使う方が、解釈しやすいと考えます。

# 6. Price delivery：VWAPの「移動」と「そこからの乖離」を分解する

今回の拡張で、**Sweepと同程度に重要なのが、この分解です。**

## 6.1 過去の約定価格中心を定義する

前日までの5日間の出来高加重平均価格を、

$$
\bar W^-_{5,t}
=
\frac{\sum_{j=1}^{5}W_{t-j}V_{t-j}}
{\sum_{j=1}^{5}V_{t-j}}
$$

とします。

次に、

$$
m_t=\frac{W_t-\bar W^-_{5,t}}{a_t}
$$

を定義します。

これは、**当日の平均約定価格が、過去の平均約定価格からどちらへ移動したか**を表します。

先ほどの

$$
d_t=\frac{C_t-W_t}{a_t}
$$

と合わせると、

$$
\boxed{
\frac{C_t-\bar W^-_{5,t}}{a_t}
=
\underbrace{m_t}_{\text{約定価格中心の移動}}
+
\underbrace{d_t}_{\text{当日の中心から終値への乖離}}
}
$$

という正確な分解ができます。

## 6.2 この分解で何が分かるか

同じように終値が過去の価格水準から上昇していても、状態は異なります。

| 状態 | $m_t$ | $d_t$ | 検証したい仮説 |
|---|---:|---:|---|
| 取引価格全体が上方へ移行 | 大きく正 | 小さい | 上昇が継続するか |
| 約定価格中心はあまり変わらず、終値だけ上方へ乖離 | 小さい | 大きく正 | 引けの乖離が解消するか |
| 上方へ価格探索したが、引けでは当日VWAPを下回る | 正の場合もある | 負 | 上方探索の失敗後、下落が続くか |
| 下方へ価格探索したが、引けでは当日VWAPを回復 | 負の場合もある | 正 | 下方探索の失敗後、上昇が続くか |

もちろん、当日の平均約定価格が動いたことだけで「新しい価格が正しい」「情報が織り込まれた」とは言えません。しかし、**単純な終値変化より、継続と反転を分ける仮説を構成しやすくなります。**

## 6.3 Acceptanceの粗い日次代理変数

上方Acceptance候補を、

$$
J^U_t
=
\mathbf1\{C_t>u_t,\ W_t>u_t,\ C_t>O_t\}
$$

下方Acceptance候補を、

$$
J^D_t
=
\mathbf1\{C_t<\ell_t,\ W_t<\ell_t,\ C_t<O_t\}
$$

とします。

これは、終値だけでなく当日の平均約定価格も旧レンジの外側へ移行した場合を選びます。

ただし、VWAPが境界の外側にあることは、**出来高の過半が外側で成立したことや、十分な時間滞留したことまでは保証しません。** あくまで日次で作れる粗いAcceptance候補です。

継続型の候補は、

$$
\boxed{
A^{delivery}_t
=
(J^U_t-J^D_t)|m_t|
}
$$

で、#22の量価変化を加えるなら、

$$
A^{delivery22}_t
=
(J^U_t-J^D_t)|m_t|(1+\Gamma_t)
$$

です。

この場合は原式と異なり、**大きな量価関係の変化を、継続方向の重みとして使う**ことになります。

---

# 7. 同じHigh-Volume相関変化でも、正反対の仮説を作れる

数値例で考えると、拡張の意味が明確になります。

過去高値が100で、当日のHighが103だったとします。

| 項目 | 上方探索が拒否されたケース | 上方へ移行したケース |
|---|---:|---:|
| 過去高値 | 100 | 100 |
| 当日High | 103 | 103 |
| Close | 99.5 | 102.5 |
| VWAP | 100.5 | 101.5 |
| 判定 | 高値突破後、旧レンジ内へ回帰 | 終値・VWAPとも旧レンジ外 |
| 拡張版で検証する方向 | 下方向の継続／上方探索の反転 | 上方向の継続 |

HighとVolumeの履歴が同じなら、両ケースの

$$
\mathcal D(H,V)
$$

は同じです。#22の終値標準偏差による倍率は変わり得ますが、相関変化が正なら、どちらも負方向になります。

一方、Low・Close・VWAPを使えば、**高値を付けた後に何が起きたか**を分けられます。

したがって今回の拡張の中心は、

$$
\boxed{
\text{「量価関係が変わったから逆張り」から、}
\quad
\text{「量価関係の変化を伴う探索が拒否／受容されたか」へ}
}
$$

という変更です。

# 8. 最初に比較するアルファ群

最初からすべてを一つの式へ掛け合わせるより、次の比較に分けることを勧めます。

| 系列 | シグナル | 主な検証目的 |
|---|---|---|
| 原型 | $-\mathcal D(H,V)B$ | 元の#22の再現 |
| 入力置換 | $-\mathcal D(L,V)B,\ -\mathcal D(W,V)B$ | High固有の情報か |
| 相対価格版 | $-\mathcal D(d,q)$ | 価格水準よりVWAP乖離の量価関係が重要か |
| Sweep基礎版 | $R$ | 拒否形状だけで予測力があるか |
| Sweep＋#22 | $R(1+\Gamma)$ | 相関変化が拒否形状に追加情報を与えるか |
| VWAP乖離版 | $-d$ と $-d(1+|\mathcal D(d,q)|)$ | 単純なVWAP回帰を超える効果があるか |
| Delivery基礎版／拡張版 | $(J^U-J^D)|m|$、同じものに$(1+\Gamma)$を乗じる | 受容された価格移動には継続性があるか |

**最優先の比較は「Sweep基礎版」と「Sweep＋#22」です。**

拡張版の成績が原型より良くても、Sweep基礎版と変わらなければ、改善したのは価格形状であって、#22の相関変化ではありません。この比較を置くことで、#22を拡張する意味があるのかを判定できます。

同様に、price deliveryの継続版は、反転版に対する重要な対立仮説になります。反転を最初から正しいと決めずに検証できるためです。

---

# 9. 日中データがあると、概念への対応をさらに明確にできる

日次データでは、「上抜いて引けでは戻った」という終点の関係は分かっても、

> 境界突破 → 反対方向へのDisplacement → 構造変化 → FVG形成

という詳細な順序までは分かりません。

日中データでは、突破時刻を$\tau$、判定時刻を$s$として、次のような追加計測ができます。

## 9.1 突破後の外側での取引比率

上方突破なら、

$$
AcceptanceRatio^+_{\tau:s}
=
\frac{
\sum_{\tau\le j\le s}v_j\,\mathbf1\{p_j>u\}
}{
\sum_{\tau\le j\le s}v_j
}
$$

です。

これなら、単にVWAPが上にあるかではなく、**突破後の出来高のどの程度が旧レンジ外で成立したか**を測れます。判定時点までのデータだけで計算する必要があります。

## 9.2 突破後の方向性

例えば、

$$
PathDirection_{\tau:s}
=
\frac{p_s-p_\tau}
{\sum_{\tau<j\le s}|p_j-p_{j-1}|}
$$

とすれば、突破後に往復せず上へ進んだか、反対方向へ戻されたかを測れます。

これは経路の方向性を表す指標であり、noteでいう「双方向の価格交換としてのefficiency」や、効率的市場仮説とは別の概念です。

## 9.3 本当の注文不均衡

約定の売買主導側を識別できれば、

$$
TradeImbalance
=
\frac{\sum_j\epsilon_jv_j}{\sum_jv_j},
\qquad
\epsilon_j=
\begin{cases}
+1&\text{買い主導約定}\\
-1&\text{売り主導約定}
\end{cases}
$$

を計算できます。

さらに気配更新・取消しまであれば、約定出来高だけでなく板の需給変化を扱うOFIへ進めます。これはOHLCVから推測した「価格の偏り」とは異なる情報です。([arXiv](https://arxiv.org/abs/1011.6402))

したがって、日次版は**microstructure-inspiredな代理変数モデル**、約定・板データ版は**注文フローをより直接扱うモデル**と区別しておくのが適切です。

# 10. データ面で最も重要：疑似VWAPを使うと、検証内容が変わる

前回のOHLCVだけの取得コードに、

$$
W^{proxy}_t=\frac{H_t+L_t+C_t}{3}
$$

を追加しても、それは本来のVWAPではありません。

この疑似VWAPを使うと、値幅がゼロでない場合、

$$
\frac{C_t-W^{proxy}_t}{H_t-L_t}
=
\frac{2C_t-H_t-L_t}{3(H_t-L_t)}
=
\frac{CLV_t}{3}
$$

となります。

つまり、**「VWAP乖離」を追加したつもりでも、実際には終値のレンジ内位置を再表現しただけ**になります。今回の研究では、この違いは決定的です。

同じ取引範囲に対応した売買代金 $Q_t$ と株数出来高 $V_t$ があれば、

$$
W_t=\frac{Q_t}{V_t}
$$

として日次VWAPを計算できます。例えばJ-Quantsの公式仕様では、出来高と売買代金の項目が提供されています。利用するデータの市場範囲・時間帯・単位を一致させたうえで計算する設計が可能です。([J-Quants](https://jpx-jquants.com/ja/help/data))

調整済みOHLCを使う場合も、VWAPだけ未調整のまま混ぜないことが必要です。まず整合した未調整データで計算し、価格調整を行うならVWAPにもOHLCと同じ調整を適用します。

# 11. 検証は「形状があった」ではなく「執行後の残存リターンがあるか」

この研究では、特に次の点を重視します。

### 同じイベントで、#22の追加効果を比較する

Sweepイベントだけを対象に、

$$
R
\quad\text{対}\quad
R(1+\Gamma)
$$

を、同じ銘柄集合・同じ日・同じリスク量で比較します。

また、相関変化の強さ別に、

> 下方拒否後の買い方向リターン、上方拒否後の売り方向リターンが強くなるか

を確認します。

単純な過去リターン、VWAP乖離、RVOL、ボラティリティ、株価水準、規模、業種を統制した後にも差が残るかを見ることで、「ただの短期リバーサル」「高ボラティリティ効果」との区別ができます。

### 翌日執行と2営業日遅れを分ける

時点$t$の終値まででシグナルを作ったなら、当日すでに生じた回復を利益として数えてはいけません。

初期検証では、翌日寄り付きと2営業日後寄り付きについて、執行後の1・3・5営業日リターンを比較すると、情報の減衰を確認できます。日中で完結する価格拒否が日次運用でも利用可能かは、この検証で初めて分かります。

### 統計的有意性は銘柄×日を独立として計算しない

前回の簡易コードにあった、イベントをすべてプールして

$$
t=\frac{\bar r}{s/\sqrt N}
$$

とする方法は、今回の結論を出す用途には不十分です。同じ日の銘柄間依存や保有期間の重複を考慮する必要があります。

まず日別のイベント・ポートフォリオ収益を作り、その時系列に対してHAC標準誤差などを用いる設計に改めます。HACは異分散と自己相関を考慮するための推定法です。([JSTOR](https://www.jstor.org/stable/1913610?utm_source=chatgpt.com))

評価はIC・IC decayだけでなく、ロング／ショート別寄与、等ウェイト・ベンチマークとの差、コスト控除後収益まで確認します。寄り付きで建てて毎日引けに閉じる検証なら、コストは前日とのウェイト差ではなく、**毎日の建玉と手仕舞いの両方**から計算します。

---

## 結論：中心に据えるべきなのは「Sweep後の拒否」と「価格帯の受容」の分離

今回の拡張は、次の形に整理すると研究上の意味が明確になります。

$$
\boxed{
\text{既知の高安値への価格探索}
\;\rightarrow\;
\text{VWAP・終値による拒否／受容の判定}
\;\rightarrow\;
\text{量価関係の急変による条件付け}
}
$$

**High・Lowは「どこを試したか」、VWAPは「取引価格の中心がどこへ移ったか」、Close-VWAPは「終値がそこからどちらへ偏ったか」を担当させる**のが適切です。

最初の実験では、次の二つを独立した戦略として扱うことを勧めます。

**Sweep-rejection型**

$$
\boxed{
A^{sweep22}=R(1+\Gamma)
}
$$

価格探索が拒否された方向への戻りが、量価関係の急変を伴うときに強まるかを検証します。

**Acceptance-delivery型**

$$
\boxed{
A^{delivery22}
=
(J^U-J^D)|m|(1+\Gamma)
}
$$

取引価格の中心が旧レンジ外へ移行した場合には、同じ量価関係の急変がむしろ継続を示すかを検証します。

この二つを比較することで、#22を単に「HighからLow・VWAPへ広げる」のではなく、**同じ量価構造の変化が、どの状態では反転を、どの状態では継続を予測するのかを調べる条件付きアルファ**へ拡張できます。

---

**Sources:**

- [Episode ②：Internal Range Liquidity & Market Structure Shift～内部流動性と市場構造のシフト ～｜はなまる](https://note.com/hanamaru_fx01/n/n36aa7b88155a)
- [Stop-Loss Orders and Price Cascades in Currency Markets - FEDERAL RESERVE BANK of NEW YORK](https://www.newyorkfed.org/research/staff_reports/sr150.html)
- [[1011.6402] The Price Impact of Order Book Events](https://arxiv.org/abs/1011.6402)
- [データ内容・仕様 - J-Quants API Help](https://jpx-jquants.com/ja/help/data)
- [A Simple, Positive Semi-Definite, Heteroskedasticity and ...](https://www.jstor.org/stable/1913610?utm_source=chatgpt.com)



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)