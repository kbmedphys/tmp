# Gideon Ozik ナラティブ分析

**User:** Anonymous  
**Created:** 7/23/2026 17:57:34  
**Updated:** 7/23/2026 18:08:59  
**Exported:** 7/24/2026 7:41:32  
**Link:** [https://chatgpt.com/c/6a61d77c-1c38-83e8-8f80-946184369f20](https://chatgpt.com/c/6a61d77c-1c38-83e8-8f80-946184369f20)  

## Response:
2026/7/23 17:57:34

論文本文・補足資料・著者の講演資料・実装に言及する二次資料を突き合わせ、`narrative intensity` の定義、入力データ、正規化、集計頻度まで再現可能な形に落とします。公開情報だけでは一意に確定しない箇所は、推定部分と明示します。

中核定義は確認できました。日次 intensity は「当該ナラティブかつ所定センチメントの記事数」を、その日の当該メディア区分の**全記事数**で割る比率で、月次・週次はその日次系列の単純平均です。次に、記事分類・センチメント補正の公開範囲と非公開部分を切り分けます。

> **ウェブ検索で『Narrative Momentum』に関する論文を調査**
>
> [Narrative Momentum](https://papers.ssrn.com/sol3/Delivery.cfm/4912496.pdf?abstractid=4912496)
> [Global metrics](https://arxiv.org/html/2603.19225v2)
> [Narrative Attention Pricing](https://wp.lancs.ac.uk/fofi2024/files/2024/04/FoFI-2024-128-Hojoon-Lee.pdf)
> [Quantifying Narratives and their Impact on Financial Markets](https://www.statestreet.com/web/insights/articles/documents/ssa-quantifying-narratives-and-their-financial-impact_4862467.1.2.GBL.pdf)
> [Gideon OZIK | PhD | EDHEC Business School, Roubaix](https://www.researchgate.net/profile/Gideon-Ozik)
> [Gideon Ozik](https://scholar.google.com/citations?hl=en&user=qQUmjKAAAAAJ)
> [https://researchmap.jp/media-eng/published_papers/...](https://researchmap.jp/media-eng/published_papers/27100828?lang=en)
> [NOVEL RISKS AND SOURCES OF VOLATILITY:](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/428b4323-e4f3-4376-b2d4-0fe590d40582/jpm_the_power_of_narrative_attention.pdf)
> [Loading...](https://portal.wfsi-data.org/view/doi%3A10.60594/W43K5F)
> [Ronnie Sadka, PhD](https://sites.google.com/bc.edu/ronnie-sadka/home)
> [New Perspectives in Forecasting the Cross Section of ...](https://www.aeaweb.org/conference/2025/program/1842?q=eNqrVipOLS7OzM8LqSxIVbKqhnGVrJQMlWp1lJITS1LT84sqgXwlHaXE4uL8ZAizJLUoF8JKSYTKlmTmpkJYZZmp5SDDigoKgAKmBiCTChLTQbImSrVcMFnkXCJj)
> [https://digital.lib.washington.edu/researchworks/i...](https://digital.lib.washington.edu/researchworks/items/6c10a35f-043f-45a7-b2dd-fc0139dc09b6/full)
> [Hojoon Lee](https://hojoonlee300.github.io/documents/Lee_CV.pdf)
>
> **13 件のウェブサイトを検索しました**
>
> 
>
> **ダウンロードファイルの取得**
>
>
> **取得したダウンロードファイル**
>
> 
>
> **ウェブを検索中**
>
>
> **www.ei-navi.jp を検索**
>
> 
>
> **検索してナラティブモメンタムを分析**
>
> 
>
> **Searching for Narrative Momentum and related research**
>
> [Narrative Momentum](https://papers.ssrn.com/sol3/Delivery.cfm/4912496.pdf?abstractid=4912496)
> [Narrative](https://en.wikipedia.org/wiki/Narrative)
> [Narrative Attention Pricing](https://wp.lancs.ac.uk/fofi2024/files/2024/04/FoFI-2024-128-Hojoon-Lee.pdf)
> [「narrative」の意味・使い方・表現・読み方](https://eow.alc.co.jp/search?q=narrative)
> [How do media narratives influence the financial markets?](https://www.edhec.edu/en/research-and-faculty/edhec-vox/how-do-media-narratives-influence-financial-markets)
> [narrative Inc.](https://narratives.co.jp/)
> [NARRATIVE Definition & Meaning](https://www.merriam-webster.com/dictionary/narrative)
> [QUANTIFYING | English meaning - Cambridge Dictionary](https://dictionary.cambridge.org/dictionary/english/quantifying)
> [From Headlines to Forecasts: Narrative Econometrics in ...](https://www.mdpi.com/1911-8074/18/9/524)
> [Quantifying Narratives and their Impact on Financial Markets](https://www.statestreet.com/web/insights/articles/documents/ssa-quantifying-narratives-and-their-financial-impact_4862467.1.2.GBL.pdf)
> [CESifo Working Paper No. 12204](https://www.ifo.de/DocDL/cesifo1_wp12204.pdf)
> [narrative inc.](https://nrtv.co.jp/)
> [QUANTIFICATION](https://www.mcgill.ca/sociology/files/sociology/2008_--_qunatification.pdf)
> [Best Presentation Storytelling Techniques That Make Ideas ...](https://highbridgeacademy.com/presentation-storytelling-techniques-that-transform-data-into-decisions/)
> [Narrative: Why It's Important, and How It Works - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6701731/)
> [Telling a Good Story](https://www.lasanozfinance.com/telling-a-good-story)
> [Narrative - an overview | ScienceDirect Topics](https://www.sciencedirect.com/topics/social-sciences/narrative)
> [[Quantifying Qualitative Variables] Quantification II and its ...](https://www.youtube.com/watch?v=gqrrsAxM3r0)
> [An Analysis of Activist Short Sellers' Rhetoric* | Request PDF](https://www.researchgate.net/publication/346484649_Deploying_Narrative_Economics_To_Understand_Financial_Market_Dynamics_An_Analysis_of_Activist_Short_Sellers%27_Rhetoric)
> [Narrative-Driven Paper-to-Slide Generation via ArcDeck](https://arxiv.org/abs/2604.11969)
> [Quantifying in | Synthese | Springer Nature Link](https://link.springer.com/article/10.1007/BF00568057)
>
> **21 件のウェブサイトを検索しました**
>
> 
>
> **解析し、PDFのページのスクリーンショットを取得しました**
>
> 
>
> **ウェブを検索中**
>
> [How do media narratives influence the financial markets? | EDHEC BUSINESS SCHOOL](https://www.edhec.edu/en/research-and-faculty/edhec-vox/how-do-media-narratives-influence-financial-markets)
>
> **1件のウェブサイトを検索しました**
>
> 
>
> **調査したナラティブタグと関連事項**
>
> 
>
> **ウェブを検索中**
>
> [globalmarkets.statestreet.com](https://globalmarkets.statestreet.com/research/dam/public/docs/Product_Descriptions_Indicators.pdf)
>
> **1件のウェブサイトを検索しました**
>
> 
>
> 8m 21s考えました

# 調査結果

Gideon Ozikらの **Narrative Momentum** について、2025年7月23日版の論文、先行する *Quantifying Narratives and Their Impact on Financial Markets*、State Street Mediastatsの仕様書、Ozikのインタビューを突き合わせました。

結論として、

> **Narrative intensity の集計式、分母、時間集計、media reservoir の統合方法、Narrative Momentumで使用する変化率は再現可能です。**  
> 一方、記事をナラティブへ分類するルールと、記事センチメントを決定する最終アルゴリズムが proprietary であるため、MKT MediaStatsと完全に同一の系列を公開情報だけで再現することはできません。

ただし、公開情報に基づく **経済的・統計的に同等な proxy series** は十分構築できます。

---

## 1. Narrative Momentum の位置づけ

最新版では、2012～2023年に point-in-time で収集された約2.3万のデジタルメディアソース、1,327万件の記事、日平均3,899件を利用し、記事を347のナラティブに分類しています。記事を後からアーカイブから取得するのではなく、その時点で収集・解析することで、削除記事や事後修正によるバックフィル・バイアスを抑えています。`Narrative Momentum.pdf`

347ナラティブのライブラリは、Reuters、IPTC、Bloombergのマクロニュースタグ、アナリストの関心テーマなどをもとに構築されています。このうち53テーマはJEL分類と対応する evergreen narratives として定義されています。`Narrative Momentum.pdf`

2023年の先行研究では、当時の73ナラティブについて、

- JEL分類
- アナリストへのインタビュー
- キーワード検索
- 文脈条件、近接条件などの textual conditions

を組み合わせた proprietary classifier を使用したと説明されています。73ナラティブの名称自体は付録で公開されています。([State Street Markets](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf))

したがって、2025年論文の347分類は73分類を拡張したものですが、完全な347テーマの判定辞書までは公開されていません。

---

# 2. Narrative intensity の正確な定義

## 2.1 記号

日付を $d$、media reservoirを $r$、ナラティブを $n$、記事を $a$ とします。

$$
\mathcal A_{r,d}
=
\{\text{日 }d\text{ に reservoir }r\text{ で収集された全記事}\}
$$

$$
N_{r,d}=|\mathcal A_{r,d}|
$$

記事がナラティブ $n$ に関連する場合、

$$
T_{a,n}=1
$$

それ以外は0とします。

記事のセンチメントについて、

$$
S_a^-=
\begin{cases}
1 & \text{記事 }a\text{ が negative}\\
0 & \text{otherwise}
\end{cases}
$$

$$
S_a^+=
\begin{cases}
1 & \text{記事 }a\text{ が positive}\\
0 & \text{otherwise}
\end{cases}
$$

とします。

---

## 2.2 通常の intensity

日次の通常 intensity は、

$$
\boxed{
I_{n,r,d}
=
\frac{
\sum_{a\in\mathcal A_{r,d}}T_{a,n}
}{
N_{r,d}
}
}
$$

です。

つまり、

> その日にそのmedia reservoirで収集された全記事のうち、ナラティブ $n$ に関連する記事の割合

です。

分母は、

- ナラティブ $n$ に関連する記事数
- 全ナラティブ記事数
- negative記事数

ではなく、**当該日・当該reservoirの全記事数**です。2023年論文とState Streetの仕様書の双方でこの点が明記されています。([State Street Markets](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf))

---

## 2.3 Negative intensity

Narrative Momentumのベースラインで使われるのは negative intensity です。

$$
\boxed{
I^-_{n,r,d}
=
\frac{
\sum_{a\in\mathcal A_{r,d}}
T_{a,n}S_a^-
}{
N_{r,d}
}
}
$$

すなわち、

> 当該ナラティブに関連し、かつnegativeと分類された記事数を、同日の全記事数で割った値

です。

重要なのは、分母がnegative記事数ではないことです。そのためこれは、

$$
P(\text{Narrative }n \cap \text{Negative})
$$

に相当し、

$$
P(\text{Negative}\mid\text{Narrative }n)
$$

ではありません。

最新版論文は、negativeおよびpositive intensityを「当該センチメントかつ当該ナラティブの記事がoverall discussionに占める割合」と定義し、値域を $[0,1]$ としています。`Narrative Momentum.pdf`

---

## 2.4 Positive intensity

同様に、

$$
\boxed{
I^+_{n,r,d}
=
\frac{
\sum_{a\in\mathcal A_{r,d}}
T_{a,n}S_a^+
}{
N_{r,d}
}
}
$$

です。

記事のセンチメント分類が positive、negative、neutral の相互排他的分類なら、

$$
I^-_{n,r,d}+I^+_{n,r,d}\le I_{n,r,d}
$$

となります。

論文の主仕様はnegative intensityですが、positive intensityを使ってもNarrative Momentumは観測されます。ただしリターンはやや弱く、positiveとnegativeの和を使った仕様でも結果は残っています。`Narrative Momentum.pdf`

---

# 3. Media reservoir

最新版では記事を次の4reservoirに分類しています。

| Reservoir | 内容 |
|---|---|
| General | CNN、Fox、NY Timesなど主要一般報道 |
| Corporate | 個別企業に関する記事 |
| FX | 通貨・外国為替に関する記事 |
| Country Equity | 国別株価指数・国別株式市場に関する記事 |

日次記事数の平均構成はGeneral 40.7%、Corporate 33.3%、FX 11.4%、Country Equity 14.7%です。`Narrative Momentum.pdf`

## Aggregate intensity

論文のメイン分析で使われるAggregateは、記事をすべてプールしてから比率を計算するのではなく、**各reservoirで計算したintensityの平均**です。

$$
\boxed{
I^{-,\mathrm{Agg}}_{n,d}
=
\frac{1}{|\mathcal R_d|}
\sum_{r\in\mathcal R_d}
I^-_{n,r,d}
}
$$

ここで $\mathcal R_d$ は日 $d$ にデータが利用可能なreservoir集合です。

収集開始日はreservoirごとに異なり、

- Corporate、Country Equity：2012年2月1日
- FX：2012年6月1日
- General：2015年9月15日

です。収集開始前のreservoirは0ではなくmissingとして扱い、Aggregateの平均から除外されます。`Narrative Momentum.pdf`

### 注意点

Aggregateは概念的に、

$$
\frac14
\left(
I_{\mathrm{General}}
+I_{\mathrm{Corporate}}
+I_{\mathrm{FX}}
+I_{\mathrm{Country}}
\right)
$$

という **reservoir equal-weight** です。

全記事をプールして計算する

$$
\frac{\sum_r N^-_{n,r,d}}{\sum_r N_{r,d}}
$$

とは異なります。後者はGeneralやCorporateの記事量に大きく左右されます。

---

# 4. 時間集計

## 4.1 月次 intensity

月 $m$ の日次intensityの単純平均です。

$$
\boxed{
I^-_{n,m}
=
\frac{1}{D_m}
\sum_{d\in m}I^-_{n,d}
}
$$

ここで $D_m$ は、その月に利用可能な日数です。

記事数を月間で合計してから分母で割る

$$
\frac{\sum_d N^-_{n,d}}{\sum_d N_d}
$$

ではありません。

したがって、記事量の多い日と少ない日は月次集計において同じ1日として扱われます。最新版論文はmonthly intensityを「当月の日次intensityの平均」と明記しています。`Narrative Momentum.pdf`

---

## 4.2 1か月の intensity change

初期の市場回帰等で用いる月次変化は、

$$
\boxed{
\Delta I^-_{n,m}
=
I^-_{n,m}-I^-_{n,m-1}
}
$$

です。`Narrative Momentum.pdf`

---

## 4.3 週次 intensity

Narrative beta推定では、水曜終値から翌水曜終値までのリターンと整合させるため、木曜から翌水曜までの日次intensityを平均します。

$$
\boxed{
I^-_{n,w}
=
\frac17
\sum_{d=\mathrm{Thu}(w-1)}^{\mathrm{Wed}(w)}
I^-_{n,d}
}
$$

$$
\boxed{
\Delta I^-_{n,w}
=
I^-_{n,w}-I^-_{n,w-1}
}
$$

週末の記事も含まれます。`Narrative Momentum.pdf`

2023年研究でも、直近7暦日の平均をweekly intensityとし、その7日前との差をweekly changeとしています。([State Street Markets](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf))

---

# 5. Narrative Momentumで用いる intensity signal

形成月を $t$、look-back期間を $J$ か月とします。

論文のNarrative Momentum signalは、単なる $J$ か月変化ではなく、**最近の $J$ か月平均と、その直前の $J$ か月平均との差**です。

$$
\boxed{
M^{(J)}_{n,t}
=
\frac1J\sum_{j=1}^{J}I^-_{n,t-j}
-
\frac1J\sum_{j=J+1}^{2J}I^-_{n,t-j}
}
$$

例えば $J=6$ なら、

$$
M^{(6)}_{n,t}
=
\operatorname{Avg}
\left(
I^-_{n,t-6},\ldots,I^-_{n,t-1}
\right)
-
\operatorname{Avg}
\left(
I^-_{n,t-12},\ldots,I^-_{n,t-7}
\right)
$$

です。

look-backは、

$$
J\in\{1,3,6,9,12\}\text{か月}
$$

です。

さらに、情報利用可能性を確保するため、**形成月 $t$ の直前月 $t-1$ の最終日をintensity計算から除外**します。`Narrative Momentum.pdf`

毎月、

- $M^{(J)}$ が最大の10ナラティブ：rising narratives
- $M^{(J)}$ が最小の10ナラティブ：declining narratives

に分類します。`Narrative Momentum.pdf`

ベースラインは、

$$
J=6,\qquad K=6
$$

すなわち6か月形成・6か月保有です。

---

# 6. センチメント分類で分かっていること

## 公開されている部分

最新版は、negative/positive sentimentをLoughran-McDonaldの金融センチメント分類に従うとしています。`Narrative Momentum.pdf`

2023年論文はさらに、

> 各記事のセンチメントスコアを、その記事が属するreservoirの当日のoverall toneで調整する

ことを明記しています。([State Street Markets](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf))

したがって概念的には、

$$
s^{\mathrm{adj}}_a
=
s^{\mathrm{raw}}_a
-
\operatorname{Tone}_{r,d}
$$

のような、日次・reservoir別のセンタリングまたは残差化が行われています。

## 公開されていない部分

次の仕様は確認できませんでした。

1. Loughran-McDonald単語数の正規化方法  
2. headlineと本文のウェイト  
3. negation処理  
4. daily tone調整が平均、中央値、回帰残差のいずれか  
5. positive／negative判定閾値  
6. 中立記事の定義  
7. 他言語記事の翻訳・辞書処理  
8. 重複記事・通信社転載記事の処理  
9. ソースごとのウェイト  
10. classifier更新時の過去データ再計算の有無  

したがって、この部分は完全再現ではなくproxy実装になります。

---

# 7. 公開情報に基づくセンチメントproxy

最も自然な再現仕様は以下です。

記事 $a$ のLoughran-McDonald positive／negative単語数を $P_a,N_a$、総単語数を $L_a$ とします。

## Raw tone

$$
s^{\mathrm{raw}}_a
=
\frac{P_a-N_a}{L_a}
$$

または、文書長への感応度を抑えるなら、

$$
s^{\mathrm{raw}}_a
=
\frac{P_a-N_a}{P_a+N_a+\epsilon}
$$

とします。

## Reservoir/day adjustment

$$
s^{\mathrm{adj}}_a
=
s^{\mathrm{raw}}_a
-
\operatorname{median}
\{s^{\mathrm{raw}}_j:j\in\mathcal A_{r,d}\}
$$

平均よりmedianのほうが極端な記事に対して頑健です。ただし、これは公開仕様ではなく推奨proxyです。

## 分類

$$
S_a^-=\mathbf 1(s^{\mathrm{adj}}_a<-\tau)
$$

$$
S_a^+=\mathbf 1(s^{\mathrm{adj}}_a>\tau)
$$

$$
S_a^0=\mathbf 1(|s^{\mathrm{adj}}_a|\le\tau)
$$

初期値は $\tau=0$ とし、人手ラベルデータを用いて $\tau$ を調整するのが自然です。

より頑健には、

- LM辞書のみ
- FinBERT
- LM＋FinBERT ensemble

の3仕様でintensityを計算し、rank correlationとNarrative Momentumの再現性を確認します。

---

# 8. ナラティブ分類の再現方法

2023年の公開説明から、単純なtopic modelよりも、**dictionary＋textual conditions型のmulti-label classifier** が原手法に近いと考えられます。([State Street Markets](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf))

例えばMarket Crashなら、論文中に次のような判定例があります。

- equity marketを示す語
- crash、bear、meltdown等の語
- 両者が近い位置に出現

という近接条件です。([State Street Markets](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf))

実装辞書は次の形式が適切です。

```yaml
narrative: market_crash

required_any:
  - stock market
  - equity market
  - s&p 500
  - nasdaq
  - nyse

event_any:
  - crash
  - meltdown
  - bear market
  - market collapse
  - selloff
  - correction

proximity:
  max_tokens: 30

exclude_any:
  - car crash
  - airplane crash
  - software crash
```

記事が複数ナラティブに該当することを許容するmulti-label方式にします。分母は全記事数であるため、ナラティブ間でintensityを足して1になる必要はありません。

公開された73テーマには、Inflation、Recession、Market Crash、Global Growth、Trade War、Federal Reserve、Labor Market、Liquidity、Housing Market、International Conflictなどが含まれています。([State Street Markets](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf))

---

# 9. 必要な記事データ

最低限、以下のpoint-in-timeテーブルが必要です。

| 列 | 内容 |
|---|---|
| `article_id` | 記事の一意ID |
| `published_at` | 公開日時 |
| `ingested_at` | 実際に取得した日時 |
| `source_id` | メディアソース |
| `title` | タイトル |
| `body` | 本文 |
| `language` | 言語 |
| `reservoir` | General / Corporate / FX / Country |
| `duplicate_cluster_id` | 転載・重複クラスタ |
| `narrative_tags` | 該当ナラティブのリスト |
| `sentiment_score` | 調整前または調整後スコア |
| `sentiment_label` | positive / negative / neutral |

特に `ingested_at` が重要です。バックテストでは、

$$
\mathrm{ingested\_at}\le\mathrm{signal\ cutoff}
$$

を満たす記事だけを使用しなければなりません。

---

# 10. intensity計算の参照実装

以下は、記事にreservoir、ナラティブタグ、センチメントラベルが付与済みであることを前提とします。

```python
from __future__ import annotations

import numpy as np
import pandas as pd

def calculate_narrative_intensity(
    articles: pd.DataFrame,
    narrative_universe: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    MKT/Ozik型の日次 narrative intensity を計算する。

    Required columns
    ----------------
    article_id       : 記事ID
    published_at     : 公開日時
    reservoir        : General / Corporate / FX / Country
    narrative_tags   : list[str]
    sentiment_label  : negative / positive / neutral

    Returns
    -------
    reservoir_daily:
        date × reservoir × narrative の日次intensity

    aggregate_daily:
        date × narrative のreservoir等ウェイト平均
    """
    required = {
        "article_id",
        "published_at",
        "reservoir",
        "narrative_tags",
        "sentiment_label",
    }
    missing = required.difference(articles.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    x = articles.copy()

    x["published_at"] = pd.to_datetime(
        x["published_at"], utc=True, errors="coerce"
    )
    x = x.dropna(
        subset=["article_id", "published_at", "reservoir"]
    )

    # 実務ではduplicate_cluster_id単位で重複除去することが望ましい
    x = x.drop_duplicates(
        subset=["article_id", "reservoir"]
    )

    # midnight-to-midnightの日付。
    # 本番では採用タイムゾーンを明示する。
    x["date"] = x["published_at"].dt.floor("D").dt.tz_localize(None)

    # 分母：当日・reservoir内の全記事数
    denominator = (
        x.groupby(["date", "reservoir"], observed=True)["article_id"]
        .nunique()
        .rename("n_total")
        .reset_index()
    )

    # multi-label narrativeを縦持ち化
    tagged = x.explode("narrative_tags").rename(
        columns={"narrative_tags": "narrative"}
    )
    tagged = tagged[
        tagged["narrative"].isin(narrative_universe)
    ].copy()

    tagged["negative_article_id"] = tagged["article_id"].where(
        tagged["sentiment_label"].eq("negative")
    )
    tagged["positive_article_id"] = tagged["article_id"].where(
        tagged["sentiment_label"].eq("positive")
    )

    numerator = (
        tagged.groupby(
            ["date", "reservoir", "narrative"],
            observed=True,
        )
        .agg(
            n_narrative=("article_id", "nunique"),
            n_negative=("negative_article_id", "nunique"),
            n_positive=("positive_article_id", "nunique"),
        )
        .reset_index()
    )

    # 利用可能なdate-reservoirについて全ナラティブのグリッドを作る。
    # 該当記事がゼロのナラティブを0として扱うために必要。
    available = denominator[["date", "reservoir"]].drop_duplicates()
    narratives = pd.DataFrame({"narrative": narrative_universe})

    grid = available.merge(narratives, how="cross")

    reservoir_daily = (
        grid.merge(
            numerator,
            on=["date", "reservoir", "narrative"],
            how="left",
        )
        .merge(
            denominator,
            on=["date", "reservoir"],
            how="left",
        )
    )

    count_cols = ["n_narrative", "n_negative", "n_positive"]
    reservoir_daily[count_cols] = (
        reservoir_daily[count_cols].fillna(0)
    )

    reservoir_daily["intensity"] = (
        reservoir_daily["n_narrative"]
        / reservoir_daily["n_total"]
    )
    reservoir_daily["negative_intensity"] = (
        reservoir_daily["n_negative"]
        / reservoir_daily["n_total"]
    )
    reservoir_daily["positive_intensity"] = (
        reservoir_daily["n_positive"]
        / reservoir_daily["n_total"]
    )

    # MKT論文のAggregate：
    # 利用可能なreservoirのintensityを等ウェイト平均
    intensity_cols = [
        "intensity",
        "negative_intensity",
        "positive_intensity",
    ]

    aggregate_daily = (
        reservoir_daily
        .groupby(["date", "narrative"], observed=True)[intensity_cols]
        .mean()
        .reset_index()
    )

    return reservoir_daily, aggregate_daily
```

---

# 11. 月次・週次系列

```python
def aggregate_monthly(
    aggregate_daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    月次 intensity = 日次 intensity の単純平均。
    """
    x = aggregate_daily.copy()
    x["month"] = x["date"].dt.to_period("M")

    cols = [
        "intensity",
        "negative_intensity",
        "positive_intensity",
    ]

    return (
        x.groupby(["month", "narrative"], observed=True)[cols]
        .mean()
        .reset_index()
    )

def aggregate_thursday_to_wednesday(
    aggregate_daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    木曜から翌水曜までの7暦日平均。
    """
    x = aggregate_daily.copy()

    # Monday=0, Tuesday=1, Wednesday=2
    days_to_wednesday = (2 - x["date"].dt.weekday) % 7

    x["week_end"] = (
        x["date"]
        + pd.to_timedelta(days_to_wednesday, unit="D")
    )

    cols = [
        "intensity",
        "negative_intensity",
        "positive_intensity",
    ]

    weekly = (
        x.groupby(["week_end", "narrative"], observed=True)[cols]
        .mean()
        .reset_index()
        .sort_values(["narrative", "week_end"])
    )

    weekly["delta_negative_intensity"] = (
        weekly.groupby("narrative", observed=True)[
            "negative_intensity"
        ].diff()
    )

    return weekly
```

---

# 12. Narrative Momentum signal

```python
def calculate_narrative_momentum(
    aggregate_daily: pd.DataFrame,
    lookback_months: int = 6,
) -> pd.DataFrame:
    """
    Narrative Momentum signal:

    最近Jか月の平均negative intensity
    - その直前Jか月の平均negative intensity

    各月末最終日は除外する。
    """
    if lookback_months <= 0:
        raise ValueError("lookback_months must be positive.")

    x = aggregate_daily.copy()
    x["date"] = pd.to_datetime(x["date"])

    # 論文仕様：
    # 形成月直前月の最終日を除外。
    # 毎月シグナルを形成する場合、全月の月末日を除外すればよい。
    x = x[
        x["date"]
        != x["date"] + pd.offsets.MonthEnd(0)
    ].copy()

    x["month"] = x["date"].dt.to_period("M")

    monthly = (
        x.groupby(["month", "narrative"], observed=True)[
            "negative_intensity"
        ]
        .mean()
        .unstack("narrative")
        .sort_index()
    )

    recent_average = monthly.rolling(
        window=lookback_months,
        min_periods=lookback_months,
    ).mean()

    previous_average = recent_average.shift(lookback_months)

    signal = recent_average - previous_average

    # 月mまでのデータから、翌月m+1初に形成するシグナル
    signal.index = signal.index + 1
    signal.index.name = "formation_month"

    long_form = (
        signal.stack(dropna=False)
        .rename("narrative_momentum")
        .reset_index()
    )

    long_form["rank_descending"] = (
        long_form.groupby("formation_month")[
            "narrative_momentum"
        ]
        .rank(method="first", ascending=False)
    )

    long_form["rank_ascending"] = (
        long_form.groupby("formation_month")[
            "narrative_momentum"
        ]
        .rank(method="first", ascending=True)
    )

    long_form["group"] = "middle"
    long_form.loc[
        long_form["rank_descending"] <= 10, "group"
    ] = "rising"
    long_form.loc[
        long_form["rank_ascending"] <= 10, "group"
    ] = "declining"

    return long_form
```

---

# 13. Raw intensityとZ-scoreを混同しないこと

Narrative Momentum論文が用いるintensityは、基本的には $[0,1]$ の**記事比率そのもの**です。

一方、State Streetの会社・通貨・国別Media Indicatorsは、クロスセクションまたは履歴に対するz-scoreとして提供されることがあります。([State Street Markets](https://globalmarkets.statestreet.com/research/dam/public/docs/Product_Descriptions_Indicators.pdf))

また2023年研究のMarket Crash予測戦略では、別途、

$$
Z_{n,d}
=
\frac{
I^-_{n,d}-\mu_{n,d}^{(60)}
}{
\sigma_{n,d}^{(60)}
}
$$

という60日rolling z-scoreを使用しています。これはNarrative Momentumの6か月変化シグナルとは別仕様です。([State Street Markets](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf))

したがってベースライン再現では、最初からintensityをz-score化しないほうがよいです。

---

# 14. 完全再現に対する識別状況

| 要素 | 再現可能性 | 状況 |
|---|---:|---|
| 日次intensityの式 | 高 | 完全公開 |
| negative/positive intensityの分母 | 高 | 全記事数と判明 |
| 月次集計 | 高 | 日次単純平均 |
| 週次集計 | 高 | 木曜～水曜平均 |
| Aggregate reservoir | 高 | 利用可能reservoirの平均 |
| Momentum signal | 高 | 直近Jか月平均－その前Jか月平均 |
| 月末最終日の除外 | 高 | 明記あり |
| 73テーマ名称 | 高 | 2023年付録に公開 |
| 347テーマ名称 | 中～低 | 一部は表から取得可能、全辞書は未公開 |
| テーマ判定ロジック | 低 | keyword＋textual conditionのみ公開 |
| LMセンチメント | 中 | 辞書は公開、正規化・閾値は非公開 |
| daily tone adjustment | 低 | 調整の存在のみ公開 |
| 重複記事処理 | 低 | 非公開 |
| ソース選択・ウェイト | 低 | 非公開 |
| MKT系列との数値完全一致 | 不可能 | proprietary部分が必要 |

---

## 最終的な推奨再現仕様

論文に最も忠実な公開実装は次の仕様です。

1. point-in-timeで記事を保存  
2. 重複・転載をクラスタ単位で除去  
3. General、Corporate、FX、Country Equityへ分類  
4. 公開73テーマを起点にmulti-label rule-based classifierを構築  
5. Loughran-McDonald＋reservoir/day調整でセンチメントを分類  
6. 日次の分母をreservoir内全記事数とする  
7. reservoirごとにnegative intensityを計算  
8. 利用可能reservoirを等ウェイト平均  
9. 日次系列を単純平均して月次化  
10. 各月末最終日を除き、直近6か月平均－その前6か月平均を計算  
11. rising上位10、declining下位10を選択  
12. LM、FinBERT、辞書条件、重複処理について感応度分析を行う  

この構成なら、MKT固有の数値との完全一致ではなくとも、**Narrative Momentum論文の経済的仮説とシグナル生成過程を検証できる再現実装**になります。

---

**Sources:**

- [https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf](https://globalmarkets.statestreet.com/research/service/public/v1/article/insights/pdf/v2/12452810-757d-4ce5-83a7-921292651788/jpm_quantifying_narratives.pdf)



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)