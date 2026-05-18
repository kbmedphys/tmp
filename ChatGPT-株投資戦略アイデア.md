# 株投資戦略アイデア

**User:** Anonymous  
**Created:** 5/18/2026 23:53:37  
**Updated:** 5/19/2026 0:38:35  
**Exported:** 5/19/2026 0:39:36  
**Link:** [https://chatgpt.com/c/6a0b27f0-55ac-8324-9135-a1489c765826](https://chatgpt.com/c/6a0b27f0-55ac-8324-9135-a1489c765826)  

## Response:
2026/5/18 23:53:37

Reddit上の個別銘柄推奨をそのまま採用せず、「頻出テーマ→投資仮説→検証指標→実装候補」の形で抽出します。直近投稿を重視して確認します。

## Response:
2026/5/18 23:53:41

現時点では「AIそのもの」より、電力・送配電・冷却・光通信・メモリ・データセンター建設・防衛ドローンなど、AIの制約条件に賭ける二次テーマが目立ちます。

## Response:
2026/5/18 23:59:31

Redditを単なる銘柄頻度ではなく、テーマ性・語彙・感情・価格反応を結びつけた時系列シグナルとして扱います。まず検出指標から検定、ポートフォリオ化までの設計に絞って整理します。

## Response:
2026/5/19 0:02:41

狙いは、Reddit上の「言及量が多いテーマ」ではなく、**通常時のベースラインから統計的に逸脱し、かつ投資対象に写像できるテーマ**を検出することです。単純な mention count だと、NVDA/AI/TSLA のような常時ノイズに負けるので、私は以下のような多段階設計にします。

## 1. まず「テーマの盛り上がり」を定義する

テーマ $k$ の時点 $t$ における盛り上がりを、単なる投稿数ではなく、次の合成スコアで見るのがよいです。

$$
ThemeHeat_{k,t}
= 
w_1 Burst_{k,t}
+ w_2 Breadth_{k,t}
+ w_3 Engagement_{k,t}
+ w_4 Novelty_{k,t}
+ w_5 CrossSource_{k,t}
+ w_6 FundamentalConfirm_{k,t}
- w_7 Crowding_{k,t}
- w_8 Spam/Meme_{k,t}
$$

ポイントは、**増えているか、広がっているか、新しいか、投資可能か、すでに混みすぎていないか**を分けて測ることです。

---

## 2. データ単位は「投稿」より「テーマ × 日次」に落とす

Redditからは最低限、以下を取ります。

| フィールド | 用途 |
|---|---|
| timestamp | 日次・週次集計 |
| subreddit | 情報源の質・拡散範囲 |
| title / body / comments | テーマ抽出 |
| score / upvote ratio | エンゲージメント |
| comment count | 議論の深さ |
| author id hash | ユニーク投稿者数、集中度 |
| mentioned tickers | 投資対象への写像 |
| permalink/thread id | 同一スレッド内の重複除去 |

Reddit公式のData APIは無料アクセス利用者に対してOAuth client idあたり100 queries per minuteの制限を示しており、商用利用や制限超過の研究利用などには別途契約が必要になり得ます。データ保持・削除・利用条件も制約があるため、本番運用ではAPI利用規約に沿った設計が必要です。([Reddit Help](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki))

---

## 3. テーマ抽出は3系統を併用する

### A. Seed dictionary方式

最初は人間がテーマ辞書を作ります。

例：

```text
AI power:
  data center power, grid, transformer, substation, utility, nuclear, SMR, gas turbine, electricity demand

CPO / photonics:
  co-packaged optics, silicon photonics, optical interconnect, 800G, 1.6T, transceiver

GLP-1:
  obesity drug, weight loss drug, GLP-1, Ozempic, Wegovy, Zepbound
```

メリットはバックテストしやすいことです。デメリットは未知テーマを拾えないことです。

### B. Embedding + clustering方式

各投稿・コメントを sentence embedding に変換し、UMAP/HDBSCAN/BERTopic などでクラスタリングします。BERTopicはtransformer embeddingsとc-TF-IDFを使って解釈可能なトピックを作る手法で、dynamic / online / hierarchical topic modelingにも対応しています。([maartengr.github.io](https://maartengr.github.io/BERTopic/index.html))

この方式は、辞書にない新しいテーマを拾えます。

例：

```text
Cluster 17:
  top terms = "power, grid, data center, transformer, nuclear, utility"
  label = AI power infrastructure

Cluster 23:
  top terms = "optical, CPO, silicon photonics, 1.6T, transceiver"
  label = AI networking bottleneck
```

### C. Graph community方式

ticker、企業名、技術語、サブレディットをノードにして、共起グラフを作ります。

```text
nodes = tickers + companies + keywords + subreddits
edges = co-mention frequency
community detection = Louvain / Leiden
```

この方法は、テーマと銘柄群の対応を作るのに強いです。

例：

```text
{VRT, ETN, PWR, GEV, CEG, transformer, substation, data center power}
→ AI power / electrical infrastructure community
```

---

## 4. 盛り上がり指標の中身

### 4.1 Burst：通常時からの急増

単純な件数ではなく、総投稿量で正規化します。

$$
x_{k,t} = \frac{mentions_{k,t}}{total\_posts_t}
$$

$$
Burst_{k,t}
=
\frac{\log(1+x_{k,t}) - EWMA_{60d}(\log(1+x_{k,t}))}
{EWMAStd_{60d}(\log(1+x_{k,t}))}
$$

より厳密には、Kleinbergのburst detectionを使えます。Kleinbergの手法は、連続する文書ストリーム内で、ある特徴語やトピックが急激に強度を増す「burst」を状態遷移として検出するための古典的手法です。([cs.cornell.edu](https://www.cs.cornell.edu/home/kleinber/bhs.pdf))

実務的には、まずは rolling z-score / Poisson CUSUM / Bayesian change point detection で十分です。

---

### 4.2 Breadth：一部の人だけで騒いでいないか

盛り上がりが本物なら、言及は複数の投稿者・サブレディット・銘柄に広がります。

見るべき指標：

$$
UniqueAuthors_{k,t}
$$

$$
SubredditEntropy_{k,t}
=
-\sum_s p_{s,k,t}\log p_{s,k,t}
$$

$$
AuthorHHI_{k,t}
=
\sum_a p_{a,k,t}^2
$$

良いシグナルは、

```text
mentions ↑
unique authors ↑
subreddit entropy ↑
author HHI ↓
```

です。

逆に、mention countだけ増えて author HHI が高い場合、少数アカウントの連投やキャンペーンの可能性があります。

---

### 4.3 Engagement：読まれているか、議論されているか

Redditでは投稿数より、コメントの伸びのほうが有効な場合があります。

$$
Engagement_{k,t}
=
z(score)
+
z(comment\_count)
+
z(reply\_depth)
+
z(comment\_velocity)
$$

ただし、wallstreetbets系では engagement が meme/mania を拾いやすいので、情報源ごとに重みを変えます。

例：

```text
r/SecurityAnalysis: quality weight high
r/investing: medium-high
r/stocks: medium
r/wallstreetbets: momentum signal high, quality weight low
```

---

### 4.4 Novelty：既存テーマの焼き直しではないか

新規性は重要です。すでに何年も語られているAI/EV/cryptoではなく、そこから派生した新しい制約テーマを見たい。

方法は複数あります。

#### 方法1：過去クラスタとのcosine distance

$$
Novelty_{k,t}
=
1 - \max_{j \in historical\ topics}
cosine(c_{k,t}, c_j)
$$

ここで $c_{k,t}$ は現在テーマクラスタのembedding centroidです。

#### 方法2：Jensen-Shannon divergence

過去90日と直近7日のトピック分布の差を見る。

$$
JSD(P_{topics,t-7:t}, P_{topics,t-90:t})
$$

JSDが高いテーマは、話題構造が変わっている可能性があります。

#### 方法3：新規n-gram比率

```text
new_terms = 直近7日で急増したbi-gram / tri-gram
```

例：

```text
"AI power"
"co-packaged optics"
"data center gas turbine"
"grid bottleneck"
"oral GLP-1"
```

---

### 4.5 CrossSource confirmation：Redditだけの話か

Redditだけで盛り上がっているテーマは、alphaの源泉にもなりますが、ノイズも多いです。投資戦略にするなら、外部ソースで確認します。

候補：

| ソース | 確認するもの |
|---|---|
| Google Trends | 一般関心 |
| News API / GDELT | メディア露出 |
| Earnings call transcripts | 経営陣の言及 |
| SEC filings / 10-K | 事業セグメントとの対応 |
| Analyst revisions | 業績期待 |
| Options data | 投機的混雑 |
| Price/volume | 価格反応 |
| ETF flows | テーマ資金流入 |

理想的なパターンは、

```text
Redditで初期バースト
→ ニュースで確認
→ earnings callで企業側も言及
→ アナリストリビジョン改善
→ まだ株価は過熱していない
```

です。

---

## 5. 「盛り上がり」と「投資妙味」を分ける

テーマ検出と投資判断を混ぜないほうがよいです。

### Step 1：Theme Heat

Reddit上で盛り上がっているか。

### Step 2：Investability

そのテーマに投資できるか。

$$
Investability_{i,k}
=
RevenueExposure_{i,k}
+
PurePlayScore_{i,k}
+
LiquidityScore_i
+
BalanceSheetQuality_i
+
RevisionScore_i
-
ValuationPenalty_i
-
DilutionRisk_i
$$

例えば「AI電力」が盛り上がっていても、テーマへの売上エクスポージャーが低い大型公益を買ってもalphaが薄いかもしれません。一方、純粋すぎる小型株は希薄化やバリュエーションで負けます。

---

## 6. テーマのライフサイクル分類

盛り上がっているテーマを、以下の4段階に分類すると使いやすいです。

| 段階 | 特徴 | 売買インプリケーション |
|---|---|---|
| Incubation | 技術系・専門系サブレで少数言及。Novelty高い | 監視リスト化 |
| Breakout | Burst高い、投稿者数増加、複数サブレへ拡散 | ロング候補 |
| Consensus | ニュース・アナリスト・個人投資家に広く拡散 | モメンタム継続か警戒 |
| Mania/Fade | WSB比率上昇、オプション過熱、同じミーム反復 | 利確/ショート/除外候補 |

重要なのは、**高いTheme Heatは必ずしも買いではない**ことです。初期のHeatはalphaになりやすいですが、後期のHeatはcrowdingや逆張りシグナルになります。

---

## 7. 実務で使うスコア例

私なら最初にこのようなスコアを作ります。

$$
EarlyThemeScore_{k,t}
=
0.30 \cdot Burst_{k,t}
+
0.20 \cdot Breadth_{k,t}
+
0.15 \cdot Novelty_{k,t}
+
0.15 \cdot CrossSource_{k,t}
+
0.10 \cdot QualitySubredditShare_{k,t}
+
0.10 \cdot TickerMapQuality_{k,t}
-
0.20 \cdot Crowding_{k,t}
-
0.15 \cdot SpamRisk_{k,t}
$$

Crowdingは以下で測ります。

$$
Crowding_{k,t}
=
z(Return_{basket,20d})
+
z(OptionsCallVolume_{basket})
+
z(WSBShare_{k,t})
+
z(MemeLexiconShare_{k,t})
+
z(ValuationExpansion_{basket})
$$

良いテーマは、

```text
EarlyThemeScore 高い
Crowding まだ低い
TickerMapQuality 高い
FundamentalConfirm 改善中
```

です。

---

## 8. バックテスト設計

テーマ検出は、必ず event study に落とします。

### イベント定義

```text
Event_{k,t} = 1 if EarlyThemeScore_{k,t} > 95th percentile
```

または、

```text
Event_{k,t} = 1 if Burst > 2.5 and Breadth > 1.5 and Crowding < 1.0
```

### テーマバスケット

テーマ $k$ に属する銘柄 $i$ のウェイト：

$$
w_{i,k,t}
\propto
ThemeExposure_{i,k,t}
\times LiquidityScore_i
\times RevisionScore_i
$$

ただし、以下で中立化します。

```text
market beta
sector beta
size
value/growth
momentum
country
```

### 評価期間

```text
1 week
1 month
3 months
6 months
12 months
```

Reddit由来のテーマは短期モメンタムと中期反転が混在するので、複数ホライズンで見たほうがよいです。

### 検定

重複リターンが多くなるので、

```text
Newey-West t-stat
block bootstrap
Fama-MacBeth
White reality check / deflated Sharpe
```

あたりを使います。

特に多数のテーマ・多数のパラメータを試すと、見かけのSharpeが出やすいので、multiple testing補正は必須です。

---

## 9. 実装イメージ

日次で次のようなテーブルを作ります。

```text
theme_daily
- date
- theme_id
- theme_label
- mentions
- normalized_mentions
- unique_authors
- subreddit_entropy
- avg_score
- comment_velocity
- burst_z
- novelty_score
- reddit_quality_score
- cross_source_score
- crowding_score
- early_theme_score
```

銘柄側は別テーブルにします。

```text
theme_stock_map
- date
- theme_id
- ticker
- company
- exposure_score
- pure_play_score
- liquidity_score
- revision_score
- valuation_score
- dilution_risk
```

最終的なランキングはこうです。

```text
ranked_themes
- date
- theme_label
- early_theme_score
- crowding_score
- investability_score
- suggested_stage
- top_terms
- top_tickers
```

---

## 10. LLMの使いどころ

LLMは「シグナルそのもの」ではなく、以下に限定して使うのが安全です。

1. クラスタのラベル付け  
2. 類義語辞書の拡張  
3. ticker/company/technologyの曖昧性解消  
4. スパム・meme・低品質投稿の分類  
5. テーマ説明文の生成

売買シグナルは、LLMの主観ではなく、**固定された数値特徴量**から作るべきです。

例えば：

```text
LLM:
  "このクラスタはAI power infrastructureです"

Quant model:
  Burst, Breadth, Novelty, CrossSource, Crowdingを計算してスコア化
```

この分離が重要です。

---

## 11. ありがちな落とし穴

一番危険なのは、**Redditで盛り上がっている = 買い**と解釈することです。

よくある失敗：

```text
mention countだけを見る
ticker抽出で $AI のような曖昧語を誤認する
同一スレッド内コメントを独立サンプル扱いする
bot/連投/低カルマアカウントを除外しない
WSB由来のmemeをfundamental signal扱いする
株価上昇後の言及増を先行シグナルと誤認する
バックテストで将来のテーマ辞書を使う
```

特に最後の look-ahead bias は深刻です。テーマ辞書・クラスタラベル・銘柄マッピングは、必ずその時点までの情報だけで作る必要があります。

---

## 私なら最初に作るMVP

最初から高度なtopic modelに行くより、以下の順が現実的です。

### MVP 1：Seed辞書 + burst score

```text
対象:
  r/stocks
  r/investing
  r/wallstreetbets
  r/SecurityAnalysis
  r/ValueInvesting

頻度:
  daily

指標:
  normalized mentions
  unique authors
  subreddit entropy
  rolling z-score
  price crowding
```

これで、まずテーマランキングを作る。

### MVP 2：Embedding clusteringで未知テーマ検出

Seed辞書で拾えない投稿をクラスタリングし、新しいテーマ候補を出す。

### MVP 3：テーマ × 銘柄バスケットのevent study

ThemeHeatが閾値を超えた日をイベントにして、その後のrisk-adjusted returnを見る。

---

結論としては、**Redditテーマ検出は「バースト検出 × 拡散度 × 新規性 × 投資可能性 × 混雑度ペナルティ」の問題**として設計するのがよいです。最も使えるシグナルは、単純な話題量ではなく、  
**“まだ価格に完全には織り込まれていないが、複数コミュニティに広がり始めた新規テーマ”**  
を捕まえるスコアです。

---

**Sources:**

- [Reddit Data API Wiki – Reddit Help](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki)
- [BERTopic](https://maartengr.github.io/BERTopic/index.html)
- [](https://www.cs.cornell.edu/home/kleinber/bhs.pdf)

## Response:
2026/5/19 0:05:43

前回の3分類を、投資文脈から切り離して任意コーパス向けのテーマ抽出パイプラインとして整理します。辞書・埋め込みクラスタ・共起グラフは、それぞれ異なる仮定に基づく手法です。

## Response:
2026/5/19 0:05:47

学術的には、辞書法を概念の操作化、埋め込み法を分散表現＋クラスタリング、グラフ法をco-word analysis／community detectionとして位置づけます。実務では既知テーマの捕捉、未知テーマの発見、概念構造の可視化に役割分担します。

## Response:
2026/5/19 0:10:19

以下では、前回の3手法を投資文脈に限定せず、**任意のテキストコーパスからテーマを抽出する汎用手法**として整理します。

対象コーパスを

$$
D=\{d_1,\dots,d_N\}
$$

とし、各文書 $d_i$ から「意味的にまとまった話題単位」すなわちテーマ

$$
T_k
$$

を抽出する問題として定式化します。

---

# 全体像

3手法は、テーマを何として定義するかが違います。

| 手法 | テーマの定義 | 学術的系譜 | 向いている用途 |
|---|---|---|---|
| 1. Seed dictionary / keyword-assisted | 事前に定義した語彙集合に近い文書群 | 辞書法、情報検索、keyword-assisted topic model | 既知テーマの監視 |
| 2. Embedding + clustering | 意味ベクトル空間上で近い文書クラスタ | LDA、sentence embedding、BERTopic、HDBSCAN | 未知テーマの探索 |
| 3. Graph community | 語・文書・主体・エンティティの共起ネットワーク上のコミュニティ | co-word analysis、ネットワーク科学、Louvain/Leiden | テーマ間関係・銘柄/主体マッピング |

実務的には、これらは競合手法ではなく、**相補的に使う**べきです。辞書法は解釈性と安定性が高い。embedding clusteringは発見力が高い。graph communityは、テーマとエンティティ群の構造を捉えるのに強いです。

---

# 1. Seed dictionary / keyword-assisted approach

## 1.1 発想

人間が事前にテーマ語彙を定義し、その語彙に基づいて文書をテーマに割り当てる方法です。

例えば一般化すると、テーマ $k$ に対して seed word set を

$$
S_k = \{s_{k1}, s_{k2}, \dots, s_{km}\}
$$

として定義します。

文書 $d_i$ のテーマスコアは、単純には

$$
Score(d_i, k)
=
\sum_{w \in d_i} \mathbf{1}(w \in S_k)
$$

ですが、実務では重み付きにします。

$$
Score(d_i, k)
=
\sum_{w \in d_i} \alpha_{k,w} \cdot tfidf(w,d_i)
$$

ここで $\alpha_{k,w}$ は、その語がテーマ $k$ をどれだけ代表するかを表す重みです。

TF-IDFは、文書内頻度とコーパス内での希少性を組み合わせて語の重要度を測る古典的な情報検索手法です。Salton and Buckleyのterm weightingや、Manning, Raghavan, Schützeの情報検索体系で標準的に扱われています。([サイエンスダイレクト](https://www.sciencedirect.com/science/article/abs/pii/0306457388900210/))

---

## 1.2 学術的な位置づけ

この方法は、古典的には**辞書法 dictionary-based content analysis**です。政治テキスト分析などでは、事前に語彙辞書を作り、文書の立場・感情・争点・政策領域を測定する方法として使われてきました。

ただし、完全な手作業辞書には限界があります。Grimmer and Stewartは、テキスト分析モデルは大規模文書分析を可能にする一方、問題固有の検証が不可欠であり、機械的分類は慎重に検証すべきだと論じています。([Cambridge University Press & Assessment](https://www.cambridge.org/core/journals/political-analysis/article/text-as-data-the-promise-and-pitfalls-of-automatic-content-analysis-methods-for-political-texts/F7AAC8B2909441603FEB25C156448F20))

より近年の発展としては、**keyword-assisted topic model**があります。Eshima, Imai, SasakiのkeyATMは、少数のキーワードを使ってトピックモデルを誘導し、標準的な教師なしトピックモデルより解釈性や分類性能を改善することを狙う手法です。([arXiv](https://arxiv.org/abs/2004.05964))

また、Jagarlamudi, Daumé, Udupaのlexical priorsを使うトピックモデルも、seed wordsを事前情報としてトピック学習を誘導する代表的な研究です。([ACL Anthology](https://aclanthology.org/E12-1021/))

---

## 1.3 汎用アルゴリズム

手順は以下です。

```text
Input:
  文書集合 D
  テーマ集合 K
  各テーマのseed words S_k

Step 1:
  文書を正規化する
  - lower case
  - lemmatization / stemming
  - stopword除去
  - n-gram抽出

Step 2:
  各テーマ辞書 S_k を作る

Step 3:
  各文書 d_i について Score(d_i, k) を計算する

Step 4:
  文書を最大スコアのテーマに割り当てる
  または複数テーマへのsoft assignmentにする

Step 5:
  seed wordsを定期的に拡張・修正する
```

soft assignmentにするなら、

$$
P(k \mid d_i)
=
\frac{\exp(Score(d_i,k))}
{\sum_{l} \exp(Score(d_i,l))}
$$

のように確率化できます。

---

## 1.4 辞書拡張

seed dictionaryは固定すると陳腐化します。したがって、以下のように拡張します。

### 共起ベース

seed wordと頻繁に共起する語を追加候補にする。

$$
Assoc(w, S_k)
=
PMI(w, S_k)
=
\log \frac{P(w, S_k)}{P(w)P(S_k)}
$$

### embedding近傍ベース

seed wordのembeddingに近い語を追加する。

$$
sim(w, S_k)
=
\max_{s \in S_k} cosine(e_w, e_s)
$$

### log-odds ratio

テーマ内と非テーマ内で語の出現率がどれだけ違うかを見る。Monroe, Colaresi, Quinnは、単純な頻度差ではなく、informative Dirichlet priorを使ったlog-oddsにより、語の識別力を安定的に評価する方法を提示しています。([IDEAS/RePEc](https://ideas.repec.org/a/cup/polals/v16y2008i04p372-403_00.html))

---

## 1.5 長所と短所

**長所**

解釈性が高い。テーマ定義が明示的。バックテストや監査がしやすい。特定テーマの時系列監視に向いている。

**短所**

未知テーマを発見しにくい。同義語・隠語・新語に弱い。辞書設計者のバイアスが入る。文脈依存の語義曖昧性に弱い。

---

# 2. Embedding + clustering approach

## 2.1 発想

文書を意味ベクトルに変換し、意味的に近い文書群をクラスタとして抽出します。

文書 $d_i$ をembedding model $f(\cdot)$ でベクトル化します。

$$
x_i = f(d_i) \in \mathbb{R}^p
$$

その後、クラスタリングによって

$$
C_1, C_2, \dots, C_K
$$

を得ます。各クラスタ $C_k$ がテーマ候補です。

---

## 2.2 学術的な位置づけ

古典的なトピックモデルの代表はLDAです。Blei, Ng, JordanのLatent Dirichlet Allocationは、文書を複数トピックの混合、各トピックを語分布として表現する確率的生成モデルです。([jmlr.csail.mit.edu](https://jmlr.csail.mit.edu/papers/v3/blei03a.html))

一方、近年の実務的なテーマ抽出では、BERT系embeddingを用いる方法が主流です。Sentence-BERTは、文や段落を比較しやすい密ベクトルに変換するためのSiamese network構造を提案し、semantic textual similarityなどで効率的な文ベクトル比較を可能にしました。([ACL Anthology](https://aclanthology.org/D19-1410/))

BERTopicは、transformer embedding、次元削減、クラスタリング、class-based TF-IDFを組み合わせて、解釈可能なトピック表現を作る手法です。Grootendorstは、BERTopicを「document embeddingsをクラスタリングし、c-TF-IDFでトピック語を表現する」neural topic modelingとして整理しています。([arXiv](https://arxiv.org/abs/2203.05794))

このパイプラインでは、次元削減にUMAP、クラスタリングにHDBSCANがよく使われます。UMAPは多様体学習に基づく次元削減手法で、t-SNEと比較される可視化・次元削減手法です。HDBSCANは密度ベースの階層的クラスタリングで、クラスタ数を事前指定しなくてもノイズ点を扱える点が実務上有用です。([arXiv](https://arxiv.org/abs/1802.03426))

---

## 2.3 汎用アルゴリズム

```text
Input:
  文書集合 D

Step 1:
  各文書 d_i をembeddingに変換する
  x_i = f(d_i)

Step 2:
  必要なら次元削減する
  z_i = UMAP(x_i)

Step 3:
  z_i または x_i をクラスタリングする
  C_1, ..., C_K = HDBSCAN(z_i)

Step 4:
  各クラスタ C_k の代表語を抽出する
  - c-TF-IDF
  - log-odds
  - keyphrase extraction
  - representative documents

Step 5:
  クラスタにテーマラベルを付ける

Step 6:
  各文書をテーマに割り当てる
```

---

## 2.4 c-TF-IDFによるクラスタ説明

BERTopicで使われる考え方に近い形で、クラスタ $C_k$ に含まれる文書を1つの巨大文書とみなし、語 $w$ の代表度を測ります。

$$
cTFIDF(w,k)
=
tf(w,C_k)
\cdot
\log \frac{K}{|\{j: w \in C_j\}|}
$$

通常のTF-IDFが「文書内の語の重要度」を測るのに対して、c-TF-IDFは「クラスタを特徴づける語」を測ります。

---

## 2.5 クラスタのテーマ化

embedding clusteringでは、クラスタそのものは単なる文書群です。テーマとして使うには、以下を出す必要があります。

```text
theme_id
theme_label
top_terms
representative_documents
cluster_size
cluster_coherence
time_series
```

クラスタラベルは人間が付けてもよいし、LLMで補助してもよいです。ただし、ラベル付けは説明用であり、クラスタ生成そのものは固定された数値手法で行うほうが再現性が高いです。

---

## 2.6 長所と短所

**長所**

未知テーマを発見しやすい。同義語や言い換えに強い。短文・口語・新語にも比較的対応しやすい。事前辞書に依存しない。

**短所**

クラスタの安定性が低い場合がある。embedding modelに依存する。パラメータ感応度がある。クラスタに意味のあるラベルを付ける工程が必要。時系列比較では、昨日のクラスタと今日のクラスタをどう対応させるかが問題になる。

---

# 3. Graph community approach

## 3.1 発想

語、文書、エンティティ、ユーザー、組織、銘柄、商品、技術語などをノードにし、共起・引用・類似・同時出現をエッジにしたグラフを作ります。

$$
G = (V, E)
$$

ここで、ノード $V$ は例えば

```text
terms
documents
named entities
companies
authors
subreddits
hashtags
tickers
```

であり、エッジ $E$ は

```text
同じ文書内で共起
同じ時間窓で共起
同じ投稿者が言及
同じクラスタに所属
embedding類似度が高い
```

などで定義します。

このグラフ上のコミュニティ

$$
M_1, M_2, \dots, M_K
$$

をテーマ候補と見なします。

---

## 3.2 学術的な位置づけ

この方法の古典的系譜は**co-word analysis**です。co-word analysisは、語の共起関係を使って科学技術分野や研究領域の構造・変化を可視化する方法として発展しました。Callonらの科学技術マッピングの文脈や、その後のbibliometrics / scientometricsで広く使われています。([スプリンガーリンク](https://link.springer.com/chapter/10.1007/978-1-4757-5182-6_4))

ネットワークのコミュニティ検出では、Louvain法とLeiden法が代表的です。Louvain法はmodularity最適化に基づく大規模ネットワーク向けの高速コミュニティ検出手法です。Leiden法はLouvain法の欠点、特に接続性の悪いコミュニティが生じ得る問題を改善し、より良い分割と接続性保証を与える手法として提案されています。([arXiv](https://arxiv.org/abs/0803.0476))

---

## 3.3 汎用アルゴリズム

```text
Input:
  文書集合 D
  抽出対象ノードの種類 V_type

Step 1:
  文書からノードを抽出する
  - keywords
  - named entities
  - noun phrases
  - authors
  - organizations
  - tickers
  - hashtags

Step 2:
  共起ルールを定義する
  - 同一文書内
  - 同一段落内
  - 同一スレッド内
  - 同一時間窓内

Step 3:
  エッジ重みを計算する

Step 4:
  低頻度・低情報量ノードを除去する

Step 5:
  Louvain / Leiden などでcommunity detectionを行う

Step 6:
  各communityをテーマとして解釈する
```

---

## 3.4 エッジ重みの設計

最も単純には共起回数です。

$$
w_{ab}
=
count(a,b)
$$

ただし、頻出語に引っ張られるため、実務では正規化します。

### PMI

$$
PMI(a,b)
=
\log
\frac{P(a,b)}{P(a)P(b)}
$$

### Jaccard係数

$$
Jaccard(a,b)
=
\frac{|D_a \cap D_b|}
{|D_a \cup D_b|}
$$

### Cosine similarity

$$
cosine(a,b)
=
\frac{x_a^\top x_b}{\|x_a\|\|x_b\|}
$$

### 条件付き確率

$$
P(b \mid a)
=
\frac{count(a,b)}{count(a)}
$$

実務上は、PMIだけだと低頻度語ペアが過大評価されやすいので、最低出現回数を設定するか、正則化PMIを使うほうが安定します。

---

## 3.5 グラフの型

グラフ方式は、何をノードにするかで大きく変わります。

### Term-term graph

語同士の共起グラフです。

```text
node = term
edge = same document / same sentence co-occurrence
```

これは古典的なco-word analysisに近いです。

### Entity-entity graph

企業、人名、地名、商品名、技術名などの共起グラフです。

```text
node = named entity
edge = co-mention
```

投資テーマ、産業テーマ、政策テーマ、技術テーマの抽出に向いています。

### Document-term bipartite graph

文書と語の二部グラフです。

```text
node type 1 = document
node type 2 = term
edge = term appears in document
```

この場合、二部グラフのcommunity detectionにより、文書群と語群を同時に抽出できます。

### Heterogeneous graph

複数タイプのノードを持つグラフです。

```text
node = document, term, entity, author, source, timestamp
edge = mention, co-mention, authored-by, appears-in
```

最も情報量は多いですが、設計が複雑になります。

---

## 3.6 長所と短所

**長所**

テーマとエンティティの関係を明示的に表現できる。テーマ同士の近さ、重なり、階層構造を見やすい。複数種類のデータ、例えば文書・企業・投稿者・媒体・時間を統合しやすい。

**短所**

共起の定義に強く依存する。頻出ノードがハブ化しやすい。閾値設定で結果が変わる。語義曖昧性を処理しないと、無関係なノードが同じコミュニティに入る。小さなテーマは大テーマに吸収されやすい。

---

# 3手法の比較

| 観点 | Seed dictionary | Embedding + clustering | Graph community |
|---|---:|---:|---:|
| 解釈性 | 高い | 中程度 | 高い |
| 未知テーマ発見 | 低い | 高い | 中〜高 |
| 再現性 | 高い | 中程度 | 中程度 |
| 時系列監視 | 高い | 中程度 | 高い |
| 語義曖昧性への強さ | 低い | 高い | 中程度 |
| 関係構造の表現 | 低い | 中程度 | 高い |
| 実装容易性 | 高い | 中程度 | 中程度 |
| 人間の事前知識 | 多い | 少ない | 中程度 |

---

# 汎用パイプラインとしての統合

実務では、以下のように統合するのが最も安定します。

## Step 1: corpus construction

```text
D = 文書集合
metadata = timestamp, source, author, location, category, engagementなど
```

## Step 2: preprocessing

```text
正規化
tokenization
lemmatization
n-gram抽出
固有表現抽出
重複除去
低品質文書除去
```

## Step 3: candidate theme extraction

3手法を並列に走らせます。

```text
A. Seed dictionary
  既知テーマを測定

B. Embedding clustering
  未知テーマを探索

C. Graph community
  語・主体・エンティティの関係構造を抽出
```

## Step 4: theme representation

各テーマを共通フォーマットに変換します。

```text
theme_id
theme_label
top_terms
representative_documents
related_entities
source_distribution
time_series
confidence_score
```

## Step 5: theme consolidation

3手法で得られたテーマ候補を統合します。

例えば、テーマ $a$ とテーマ $b$ の類似度を

$$
Sim(a,b)
=
\lambda_1 cosine(e_a,e_b)
+
\lambda_2 Jaccard(TopTerms_a,TopTerms_b)
+
\lambda_3 Jaccard(Entities_a,Entities_b)
$$

として、近いテーマをマージします。

## Step 6: validation

テーマ抽出では、精度よりも**妥当性検証**が重要です。

見るべき観点は以下です。

```text
coherence:
  上位語が意味的に一貫しているか

stability:
  サンプルや期間を変えても似たテーマが出るか

distinctiveness:
  他テーマと十分に区別できるか

coverage:
  重要文書を取りこぼしていないか

human validity:
  人間が読んで納得できるか

predictive validity:
  後続の行動・価格・ニュース・検索量などを説明できるか
```

Grimmer and Stewartが強調するように、テキスト分析モデルは「正しいテーマ」を自動で保証するものではなく、研究目的に応じた検証が必要です。([Cambridge University Press & Assessment](https://www.cambridge.org/core/journals/political-analysis/article/text-as-data-the-promise-and-pitfalls-of-automatic-content-analysis-methods-for-political-texts/F7AAC8B2909441603FEB25C156448F20))

---

# 実装上の推奨構成

汎用システムとしては、次の3層に分けるとよいです。

```text
Layer 1: Measurement layer
  seed dictionaryで既知テーマを安定的に測定

Layer 2: Discovery layer
  embedding clusteringで未知テーマを発見

Layer 3: Structure layer
  graph communityでテーマ間・主体間の関係を可視化
```

最終的なテーマ候補は、例えば以下のようにスコア化します。

$$
ThemeQuality_k
=
w_1 Coherence_k
+
w_2 Stability_k
+
w_3 Distinctiveness_k
+
w_4 Coverage_k
+
w_5 Novelty_k
+
w_6 Interpretability_k
$$

さらに時系列で使うなら、

$$
ThemeHeat_{k,t}
=
z(Mentions_{k,t})
+
z(UniqueSources_{k,t})
+
z(Engagement_{k,t})
+
z(GrowthRate_{k,t})
$$

のように、抽出されたテーマを日次・週次で計測対象にします。

---

# まとめ

3手法は、次のように使い分けるのが最も自然です。

**Seed dictionary / keyword-assisted approach**は、既知テーマを精密に測る方法です。人間の事前知識を入れられるため、解釈性・再現性・監査性が高い。一方、未知テーマの発見には弱いです。

**Embedding + clustering approach**は、未知テーマを探索する方法です。Sentence-BERTやBERTopicのような手法により、表層語が違っても意味的に近い文書をまとめられます。ただし、クラスタの解釈・安定性検証が必要です。

**Graph community approach**は、テーマを「語や主体の関係構造」として捉える方法です。co-word analysisやLouvain/Leiden型のcommunity detectionに基づき、テーマと関連エンティティのネットワークを抽出できます。テーマ間の重なりや周辺構造を見るのに強いです。

したがって、汎用的なテーマ抽出では、

$$
\text{辞書で測る}
+
\text{embeddingで発見する}
+
\text{グラフで構造化する}
$$

という三層構造にするのが堅牢です。

## Response:
2026/5/19 0:17:17

添付ノートブックの構造と実装差分を確認し、既存のテーマ抽出・投資適用ロジックを保ったままReuters取得部分を組み込む完成版に仕上げます。まず関数、依存関係、入出力形式を特定します。

## Response:
2026/5/19 0:17:20

実運用に近い2本目のE5/MiniLM切替版をベースにし、Reuters/LSEG APIを主経路、RSS/CSVを代替経路として `news_df` に正規化します。

## Response:
2026/5/19 0:21:47

> **RSS解析と重複除去処理**
>
> RSSフィードを処理する際、`requests.get`を使い、`ElementTree`で解析します。重複を避けるため、`external_id`や`url`、またはヘッドラインのハッシュを使って、`news_id`を生成します。検索クエリは単純なORクエリで、APIの仕様が不明な場合には適用します。
>
> **エラーハンドリングと依存関係の確認**
>
> 実際のモードで結果が得られなかった場合、エラーメッセージを表示してデモモードにフォールバックすることを検討します。また、インターネット接続がない場合でもデモモードで動作させるため、`requests`がインストールされていない場合のエラーハンドリングが重要です。URLリクエストの処理には代替手段として`urllib`を使います。
>
> **最終的なノートブックと必要な調整**
>
> 完成したノートブックは、出力をクリアしてサイズを減らすことができるかも。READMEの作成は必要なさそうだけど、最終版として提供する「完成したノートブック」と「アダプタモジュール」を準備した方がお互いに便利かも。`sentence_transformers`が使えない場合は、`tfidf`のフォールバック処理を入れるよ。
>
> **考慮しているノートブックのアプローチ**
>
> もし`SentenceTransformer`がインストールされていない場合、`TF-IDF`を使って代替する方法が便利かもしれない。2つのノートブックを提供することで、どちらの環境でも使えるようにするのがいいかな。1つは`TF-IDF`用、もう1つは`E5/MiniLM`用、どちらでも動作するようにする。
>
> **最終調整と推奨アプローチ**
>
> E5を推奨し、両方のファイルをリンクして説明するのが良さそう。非文章セルの異なる関数を使っているところを確認し、同様のセルを追加できるかも。最後に、共通モジュールと単独の`reuters_adapter.py`を作成することで再利用可能なコードに仕上げるべきだと思う。
>
> **Creating Reuters news ingestion adapter**
>
>
> **修正が必要なスタンドアロンコード**
>
> スタンドアロンのコードでOptional、Dict、Anyが定義されていない問題が発生するかもしれません。これらはノートブック内のインポートセルでは問題ないのですが、スタンドアロンコードでは不足しています。解決策として、「from typing import Any, Dict, List, Optional, Mapping, Sequence」を追加する必要がありそうです。
>
> **Updating type imports in standalone script**
>
>
> **ノートブック内でのテスト実行**
>
> ノートブックのセルを順番に実行する必要があり、特にセル8後の`news_df`の再設定を確認したいです。デフォルトはデモモードで動作するべきなので、セル1, 3, 4, 7, 8 の後、アダプターを実行すると良さそうです。
>
> **実行順序でノートブックセルを実行**
>
>
> **ノートブックにアダプター組み込み**
>
> `news_df`の形状はデフォルトデモで確認。CSVやRSS、APIの場合、追加のカラムが含まれるが既存の分類器には問題ないはずです。ノートブックにアダプターを挿入するには、`nbformat`を使ってセル8後にコードとマークダウンを追加。出力をクリアして、`reuters_adapter_code.py`は最終実行なしでスタンドアロンモジュールとして提供すべきです。
>
> **アダプターの独立性と実行制御**
>
> 全体の分類パイプラインはまだ完成していないけれ
>
> **更新ノートブックと最終アダプター化**
>
> `reuters_news_adapter.py`は個別に使えるヘルパーとして別途用意したい。最終版には「推奨はE5/Minilm版」の記載を追加し、ノートブックも更新。`theme_basket_news_investing.ipynb`の最初のセルは`TfidfVectorizer`をインポートし、アダプターは必要なすべてを持ち込んでいます。
>
> **Updating notebooks with Reuters adapter and instructions**
>
>
> **ノートブックの検証とテスト**
>
> ノートブックのASTを確認し、アダプタが挿入されるまで実行を行いたい。TFIDFノートブックのセルインデックスは、1, 3, 4, 7, 8, 10が変更された。E5は同様で、アダプタのテストはすでに実施済みだが、挿入後にも改めてテストを実行する予定です。
>
> **検証ノートブックのAST実行**
>
>
> **アダプタの設計と実装**
>
> アダプタファイル（`reuters_news_adapter.py`）を作成することが有用かもしれません。最終的な実行コードはなく、フォールバック関数を提供したいと考えています。ただ、最終的にはノートブックにリンクするだけでも良いかもしれません。もし標準的なプログラムを提供するなら、`.py`形式のスクリプトを作成し、ノートブックのコードを使って出力する方法もありますが、もう少し検討が必要です。
>
> **TFIDFノートブックの検証**
>
> TFIDFノートブックのコードセルを実行して、エラーがないか確認する必要があります。プロットや他の出力も含まれる可能性があるので、問題ないか確認します。また、`sentence_transformers`が必須でないデモをデフォルトにしておく方が良いかもしれません。Jupyter環境で動作する点を考慮して、最後にREADMEも追加すると良さそうです。
>
> **全コードセルの実行と確認**
>
>
> **TFIDFの完了と問題確認**
>
> TFIDFノートブックは正常に実行されたようです。出力ファイルは`/theme_model_outputs`に書き込まれたので、問題ないと思います。ただ、e5ノートブックが実行できない原因は、`sentence-transformers`が不足していることかもしれません。確認が必要です。
>
> **確認 sentence-transformers のインストール状況**
>
>
> **E5ノートブックのインストールとフォールバック案**
>
> E5ノートブックが動作しない可能性があるため、ユーザーにインストール手順を案内する必要があります。`sentence-transformers`がない場合、"tfidf"にフォールバックする設定を考えるべきですが、E5ノートブックではsemanticな処理が優先されているので、2バージョン提供が理想かもしれません。
>
> **スタンドアロンな`reuters_news_adapter.py`作成**
>
> `reuters_news_adapter.py`を構築し、`make_demo_news`なしで、ReutersのAPI、RSS、CSV接続機能を持つ形にします。テーマデータとドライバーデータを使用したAPIクエリをサポートするが、前のノートブック依存なしでフォールバック関数を追加します。
>
> **Creating standalone Reuters news adapter module**
>
>
> **アダプターの重複チェックとインポートテスト**
>
> アダプターで重複した`safe_list`の確認が必要かもしれないですね。テストとしてインポートの確認もしておいた方が良さそうです。
>
> **テストインポートとアダプター検査**
>
>
> **インポートの修正**
>
> おっと、スタンドアロンのコードに`pandas`、`numpy`、`re`が再インポートされていないですね。元のノートブックのインポートが削除されてしまったようです。`re`、`numpy`（np）、`pandas`（pd）をコードの最初に追加して修正しましょう。
>
> **パッチ適用：pandas, numpy, re インポート追加**
>
>
> **テスト用CSVの作成と関数確認**
>
> 最終的にスタンドアロンのヘルパーモジュールを挿入した方が良さそうですね。CSVサンプルを作成して`load_reuters_news_csv`をテストするのもいいかもしれませんが、必須ではないです。とりあえず、ダミーデータでテストして確認してみようと思います。
>
> **テスト用CSVデータの読み込み**
>
>
> **ダミーデータ削除の検討**
>
> ダミーデータを削除すべきかもしれませんね。テストが終わった後、不要なら削除した方がよさそうです。ただ、それを削除するタイミングをちょっと考えておきたいです。
>
> **ファイル削除とリスト表示**
>
>
> **README作成とコードの整理**
>
> READMEに使用方法を記載するべきかもしれませんね。最終的に説明を加えると良いかも。ノートブックにスタンドアロンコードを追加する必要があるかもしれませんが、既にそうなっているので問題なし。ノートブックのインポート部分で型関連のインポートが一部不足している可能性があり、修正が必要な点があります。
>
> 思考時間: 12m 22s

## Response:
2026/5/19 0:29:39

完成版を作成しました。Reuters.comのHTMLスクレイピングは入れていません。Reutersの利用条件では、自動スクレイピング、データマイニング、コンテンツの商用利用・再配布・ML/AI開発利用などが制限されているため、**LSEG Data Libraryの正規セッション**または**ライセンス済みCSV**から取得する設計にしています。([Reuters](https://www.reuters.com/info-pages/terms-of-use/))

作成したファイルはこちらです。

- [Reuters対応・TF-IDF版ノートブック](sandbox:/mnt/data/theme_basket_news_investing_reuters_tfidf_completed.ipynb)
- [Reuters対応・E5/MiniLM版ノートブック](sandbox:/mnt/data/theme_basket_news_investing_reuters_completed.ipynb)
- [Reuters/LSEGニュース取得アダプタ単体](sandbox:/mnt/data/reuters_news_theme_adapter.py)

今回追加した主な内容は以下です。

1. `NEWS_SOURCE_MODE = "lseg" | "csv" | "demo"` の切替  
2. LSEG Data Library経由のReuters headlines取得  
3. テーマ定義YAMLと構成銘柄RICからReuters検索クエリを自動生成  
4. Reuters/LSEGの取得データを既存モデルの `news_df` スキーマに正規化  
5. `news_df → テーマ・ドライバー分類 → 日次特徴量 → 魅力度スコア → 配分最適化` へ接続  
6. LSEGが使えない環境ではデモニュースに自動フォールバック  
7. Workspace等から出力したReuters CSVを読む `csv` モード  
8. オプションで `get_story()` による本文取得  

LSEG Data Libraryは、ニュース、価格、ファンダメンタル、ESGなどにアクセスできるPythonライブラリで、ニュース見出し取得には `ld.news.get_headlines()` が使えます。LSEG側の説明では、headlineサービスはニュース見出し・ニュース本文・Top Newsを扱え、`ld.news.get_headlines` はニュースクエリからDataFrameを返します。([developers.lseg.com](https://developers.lseg.com/en/article-catalog/article/lseg-data-library-for-python--news-pagination)) また、Desktop SessionにはWorkspace/Eikon Desktopが必要で、Platform Sessionには対応ライセンスが必要です。([developers.lseg.com](https://developers.lseg.com/en/api-catalog/lseg-data-platform/lseg-data-library-for-python/documentation))

使う場合は、ノートブック内のReutersアダプタセルで以下を設定してください。

```python
NEWS_SOURCE_MODE = "lseg"
REUTERS_START_DATE = "2025-01-01"
REUTERS_END_DATE = None
REUTERS_FETCH_STORY_BODY = False
```

CSVで使う場合は、次のようにします。

```python
NEWS_SOURCE_MODE = "csv"
REUTERS_CSV_PATH = Path("reuters_news.csv")
```

CSVの最小列は以下です。

```text
date または published_at
headline
```

任意列として、以下も使えます。

```text
body
story_id
url
source_type
provider
```

この環境ではLSEG認証情報と `lseg-data` がないため、実際のReuters取得までは実行していません。一方、**TF-IDF版ノートブックは、この環境でデモニュースへのフォールバック込みで最後まで実行確認済み**です。E5/MiniLM版は、実行環境で以下が必要です。

```python
%pip install -U sentence-transformers lseg-data
```

実運用では、まずTF-IDF版でReuters接続と日次パイプラインを安定化し、その後E5/MiniLM版へ切り替えるのが安全です。

## Response:
2026/5/19 0:31:34

まず生成済みノートブックとアダプタの構造を確認し、処理フロー、主要関数、設定項目、実運用時の使い方と注意点に分けて解説します。

## Response:
2026/5/19 0:31:51

完成版は2本のノートブックとアダプタ単体で構成され、Reuters取得・正規化を既存パイプライン前段に差し込む設計です。

## Response:
2026/5/19 0:35:37

> **プログラムの詳細な説明**
>
> プログラムはReutersニュースを取得し、テーマバスケット投資モデルに適用します。説明は日本語で、流れや係数、数式、関数の役割、出力列、設定などを含めます。2つのノートブックとアダプターを区別し、TF-IDF版とE5/MiniLM版を明確に記述。引用としてファイルリンクを示すことは可能ですが、ウェブの引用は不要です。
>
> 思考時間: 7m 0s

## Response:
2026/5/19 0:38:35

対象は主に以下の3ファイルです。

- [TF-IDF版ノートブック](sandbox:/mnt/data/theme_basket_news_investing_reuters_tfidf_completed.ipynb)
- [E5/MiniLM版ノートブック](sandbox:/mnt/data/theme_basket_news_investing_reuters_completed.ipynb)
- [Reuters/LSEGニュース取得アダプタ単体](sandbox:/mnt/data/reuters_news_theme_adapter.py)

全体としては、**Reutersニュースを取得し、テーマ定義YAMLに基づいてニュースをテーマ・収益ドライバーへ分類し、日次特徴量化し、テーマ魅力度スコアとテーマ配分を作るプログラム**です。

---

# 1. プログラム全体の構造

大きく見ると、処理は次の順序です。

```text
1. テーマ定義YAMLを読み込む
2. テーマ・収益ドライバーを DataFrame 化する
3. テーマ構成銘柄 holdings_df を作る
4. Reuters / LSEG または CSV からニュース news_df を作る
5. ニュースをテーマ・ドライバーに分類する
6. 分類結果を日次テーマ特徴量に集約する
7. テーマリターンをファクターで残差化する
8. ニュース特徴量 + 価格特徴量から魅力度スコアを作る
9. 魅力度スコアを使ってテーマ配分を最適化する
10. バックテスト、ランキング、CSV出力を行う
```

ノートブック内の主要DataFrameは次のような関係です。

```text
theme_config
   ↓
theme_df, driver_df
   ↓
holdings_df

Reuters/LSEG or CSV
   ↓
news_df
   ↓
article_driver_scores
   ↓
article_theme_scores
   ↓
daily_features
   ↓
panel
   ↓
score_panel
   ↓
weights_df, backtest_df, latest_report
```

---

# 2. 2本のノートブックの違い

2本の完成版ノートブックは、ニュース分類エンジンだけが違います。

| ファイル | 分類エンジン | 特徴 |
|---|---|---|
| `theme_basket_news_investing_reuters_tfidf_completed.ipynb` | char n-gram TF-IDF + cosine類似度 | 軽量。外部モデル不要。まず動かす本番MVP向き |
| `theme_basket_news_investing_reuters_completed.ipynb` | SentenceTransformer, E5 / MiniLM | 意味類似度が強い。表現揺れに強い。モデルインストールが必要 |

それ以外の流れ、つまりReuters取得、日次特徴量化、スコアリング、配分最適化、バックテストは基本的に共通です。

---

# 3. テーマ定義YAMLの読み込み

最初の中核入力は、テーマ定義YAMLです。

ノートブックでは、同じディレクトリに外部YAMLがあればそれを使い、なければノートブック内に埋め込まれたデモYAMLを使います。

デモYAMLには、例として次の2テーマが入っています。

```text
semiconductor_equipment_jp
  半導体製造装置

low_pbr_reform_jp
  低PBR・資本効率改革
```

それぞれのテーマには、以下が定義されています。

```text
theme_id
theme_name_en / theme_name_ja
theme_type
description
profile_summary
revenue_drivers
catalysts
positive_events
negative_events
keyword_match_terms
entity_linking_terms
embedding_text
```

特に重要なのは `revenue_drivers` です。テーマを単なるキーワード集合として扱うのではなく、**何がそのテーマの収益・バリュエーションを動かすのか**というドライバー単位に分解しています。

例：

```text
半導体製造装置
  - 半導体設備投資サイクル
  - AI半導体需要

低PBR・資本効率改革
  - 資本効率改革
  - 株主還元強化
```

---

# 4. `parse_theme_profiles()` の役割

YAMLはそのままでは扱いにくいので、`parse_theme_profiles()` が2つの表に変換します。

## `theme_df`

テーマ単位のDataFrameです。

主な列は以下です。

```text
theme_id
theme_name_en
theme_name_ja
theme_type
description_en / description_ja
profile_summary_en / profile_summary_ja
embedding_text
theme_keywords
positive_events
negative_events
entity_terms
rics
company_names_en
company_names_ja
aliases_en
aliases_ja
theme_corpus
```

`theme_corpus` は、テーマ名、説明文、概要、埋め込み用テキスト、キーワードを連結した分類用テキストです。

```python
theme_df["theme_corpus"]
```

が、後続のTF-IDFまたはSentenceTransformerでニュースと比較されます。

## `driver_df`

収益ドライバー単位のDataFrameです。

主な列は以下です。

```text
theme_id
driver_id
driver_name_en
driver_name_ja
driver_type
driver_description_en
driver_description_ja
driver_embedding_text
driver_keywords
positive_driver_events
negative_driver_events
driver_corpus
```

`driver_corpus` は、ドライバー名、説明文、埋め込み用テキスト、キーワードを連結した分類用テキストです。

この設計により、ニュースを

```text
テーマに関連しているか
どの収益ドライバーに関連しているか
そのニュースはポジティブかネガティブか
```

まで分解できます。

---

# 5. `holdings_df` の作成

`build_holdings_from_yaml()` は、YAML内の `entity_linking_terms` からテーマ構成銘柄テーブルを作ります。

主な列は以下です。

```text
theme_id
ticker
weight
company_name_en
company_name_ja
aliases
source
```

例えば半導体製造装置テーマでは、

```text
8035.T  東京エレクトロン
6857.T  アドバンテスト
```

のような構成銘柄が入ります。

デモでは、低PBRテーマにYAML上の構成銘柄がないため、サンプルとして以下が追加されています。

```text
8306.T  三菱UFJ
8058.T  三菱商事
7203.T  トヨタ自動車
5401.T  日本製鉄
```

本番では、この部分は必ず実際の point-in-time なテーマ構成銘柄に差し替える必要があります。

---

# 6. Reuters / LSEGニュース取得アダプタ

今回追加した最も重要な部分が、Reuters / LSEGニュース取得アダプタです。

ノートブック内にも同じコードが埋め込まれており、単体ファイルとしても

```python
reuters_news_theme_adapter.py
```

を作っています。

## 6.1 モード切替

ニュース取得は以下の3モードです。

```python
NEWS_SOURCE_MODE = "lseg"  # LSEG Data LibraryからReutersニュースを取得
NEWS_SOURCE_MODE = "csv"   # ライセンス済みCSVから読み込み
NEWS_SOURCE_MODE = "demo"  # デモニュースを使う
```

重要なのは、`reuters.com` のHTMLスクレイピングは行わない設計にしている点です。Reutersニュースは、LSEG Data Libraryまたはライセンス済みCSVから取り込む前提です。

---

## 6.2 主要設定

```python
NEWS_SOURCE_MODE = "lseg"
FALLBACK_TO_DEMO_IF_REUTERS_UNAVAILABLE = True

REUTERS_START_DATE = "2025-01-01"
REUTERS_END_DATE = None
REUTERS_CHUNK_DAYS = 30
REUTERS_MAX_HEADLINES_PER_REQUEST = 100
REUTERS_MAX_PAGES_PER_QUERY = 20
REUTERS_FETCH_STORY_BODY = False
REUTERS_REQUEST_SLEEP_SEC = 0.15

REUTERS_CSV_PATH = Path("reuters_news.csv")

LSEG_APP_KEY = None
LSEG_CONFIG_NAME = None
```

意味は以下です。

| 変数 | 意味 |
|---|---|
| `NEWS_SOURCE_MODE` | ニュース取得方法 |
| `FALLBACK_TO_DEMO_IF_REUTERS_UNAVAILABLE` | LSEGが使えない場合にデモへ落とすか |
| `REUTERS_START_DATE` | Reuters取得開始日 |
| `REUTERS_END_DATE` | 終了日。`None`なら今日まで |
| `REUTERS_CHUNK_DAYS` | 日付範囲を何日単位で分割するか |
| `REUTERS_MAX_HEADLINES_PER_REQUEST` | 1リクエストあたり取得件数 |
| `REUTERS_MAX_PAGES_PER_QUERY` | ページネーション上限 |
| `REUTERS_FETCH_STORY_BODY` | 本文取得を行うか |
| `REUTERS_CSV_PATH` | CSVモードの入力ファイル |

本文取得は `False` がデフォルトです。見出しだけで十分に動くようにしつつ、権限がある場合のみ `get_story()` で本文も取得できる設計です。

---

# 7. Reutersニュースの正規化

LSEGやCSVから得られる列名は環境によって異なります。そこで、`standardize_news_df()` が任意のニュース表を、ノートブック共通の `news_df` 形式に変換します。

出力列は以下です。

```text
news_id
date
published_at
headline
body
source_type
provider
story_id
url
theme_query_id
lseg_query
news_text
```

最低限必要なのは、

```text
date または published_at
headline
```

です。

CSVモードの場合、以下のような列があれば動きます。

```text
published_at, headline, body, story_id, url
```

`standardize_news_df()` は内部で以下を行います。

```text
1. headline / title / subject などの列名を自動認識
2. published_at / versionCreated / timestamp / date などの日付列を自動認識
3. HTMLタグを除去
4. published_at を timezone なしdatetimeへ変換
5. date を日次に丸める
6. story_id があれば story_id で重複除去
7. なければ date + headline で重複除去
8. headline + body から news_text を作る
```

`news_text` は後続の分類で使われる本文です。

```python
news_text = headline + "。" + body
```

---

# 8. LSEGクエリの自動生成

`build_reuters_lseg_queries()` は、テーマ定義と構成銘柄からReuters検索クエリを自動生成します。

例えば、半導体製造装置テーマなら、概念的には以下のようなクエリになります。

```text
(
  R:8035.T
  OR R:6857.T
  OR "Japanese Semiconductor Equipment"
  OR "semiconductor capex"
  OR "wafer fab"
  OR "foundry capex"
  OR "AI semiconductor"
  OR "export controls"
)
AND Language:LEN
AND Source:RTRS
```

ここで、

```text
R:<RIC>
```

はLSEG上の銘柄識別子検索です。

クエリには以下が含まれます。

```text
1. holdings_df の ticker から R:<RIC>
2. theme_name_en
3. theme_keywords の英語キーワード
4. Language:LEN
5. Source:RTRS
```

日本語キーワードはReuters Englishニュース検索ではノイズになる可能性が高いため、LSEGクエリ生成時には英語・RICらしい語を優先しています。

---

# 9. LSEG取得処理

Reuters取得の中核は `fetch_reuters_news_from_lseg()` です。

処理は以下です。

```text
1. LSEGセッションを開く
2. テーマごとにReuters検索クエリを作る
3. 期間を REUTERS_CHUNK_DAYS ごとに分割する
4. 各テーマ × 各期間で見出しを取得する
5. ページネーションがあれば cursor を使って追加取得する
6. 取得結果に theme_query_id と lseg_query を付与する
7. standardize_news_df() で news_df に正規化する
8. 必要なら story_id ごとに本文を取得する
```

内部では2種類の取得関数を用意しています。

```python
_fetch_lseg_headlines_paginated()
_fetch_lseg_headlines_access_layer()
```

前者は、LSEG content layer の `news.headlines.Definition` を使い、cursorページネーションに対応しています。後者は、簡易な `ld.news.get_headlines()` ラッパーです。

最終的に、ReutersニュースもデモニュースもCSVニュースも、すべて同じ `news_df` スキーマにそろえられます。

---

# 10. ニュース分類エンジン：共通部分

ニュース分類の出力は、

```python
article_driver_scores
news_scored_df
```

です。

分類では、1本のニュースに対して、全テーマ・全ドライバーとの関連度を計算します。

評価する要素は以下です。

```text
theme_semantic_sim
driver_semantic_sim
theme_keyword_score
driver_keyword_score
entity_score
pos_score
neg_score
impact
risk_score
evidence
novelty
source_quality
relevance
```

このうち、特に重要なのは `relevance` と `impact` です。

---

## 10.1 phrase score

キーワード一致は `phrase_score()` で計算されます。

```python
phrase_score = min(1, log1p(hit_count) / log1p(saturation))
```

単純なヒット数ではなく、対数で飽和させています。これにより、同じキーワードが何度も出てもスコアが過剰に大きくなりません。

---

## 10.2 ポジティブ・ネガティブ判定

汎用ポジティブ語と汎用ネガティブ語があります。

ポジティブ語の例：

```text
increase
expansion
recovery
upgrade
buyback
dividend hike
受注回復
上方修正
自社株買い
増配
```

ネガティブ語の例：

```text
decline
cut
delay
restriction
downgrade
equity offering
輸出規制
下方修正
公募増資
不祥事
懸念
```

さらに、YAML内のテーマ固有・ドライバー固有の

```text
positive_events
negative_events
positive_driver_events
negative_driver_events
```

も使います。

最終的なインパクトは以下で計算されます。

```python
impact = tanh(1.75 * (pos_score - neg_score))
```

つまり、

```text
impact > 0 ならポジティブ
impact < 0 ならネガティブ
impact ≈ 0 なら中立
```

です。

---

## 10.3 evidence

`evidence` は、ニュースに実際の材料らしい語が含まれているかを見ます。

```text
announcement
confirmed
guidance
order
capex
filing
disclosure
発表
開示
受注
設備投資
上方修正
決算
```

スコアは以下です。

```python
evidence = 0.60 + 0.40 * phrase_score(EVIDENCE_TERMS)
```

最低でも0.60を与え、明確な根拠語がある場合に最大1.00へ近づけます。

---

## 10.4 source quality

ニュースソースの信頼度・材料性も係数化しています。

```python
SOURCE_QUALITY = {
    "company_disclosure": 1.20,
    "exchange": 1.15,
    "regulator": 1.15,
    "major_media": 1.00,
    "wire": 0.95,
    "blog": 0.60,
    "social": 0.40,
}
```

Reutersから入るニュースは通常 `wire` 扱いで、係数は0.95です。会社開示や取引所開示を別途入れる場合は、より高く評価されます。

---

# 11. TF-IDF版の分類ロジック

TF-IDF版では、以下を使います。

```python
TfidfVectorizer(
    analyzer="char",
    ngram_range=(2, 5),
    max_features=50000,
    sublinear_tf=True,
    norm="l2",
)
```

日本語と英語が混在するため、単語分割ではなく **文字n-gram** を使っています。これにより、形態素解析なしでも日本語・英語混在テキストを扱えます。

処理は以下です。

```text
1. news_text をTF-IDFベクトル化
2. theme_corpus をTF-IDFベクトル化
3. driver_corpus をTF-IDFベクトル化
4. ニュース × テーマの cosine類似度を計算
5. ニュース × ドライバーの cosine類似度を計算
6. 類似度を robust min-max で 0〜1 に正規化
```

TF-IDF版の長所は、

```text
外部モデル不要
高速
再現性が高い
環境依存が小さい
```

です。

一方、同義語や言い換えにはE5/MiniLM版ほど強くありません。

---

# 12. E5/MiniLM版の分類ロジック

E5/MiniLM版では、`SentenceTransformer` を使います。

設定は以下です。

```python
EMBEDDING_PRESET = "e5-base"
# EMBEDDING_PRESET = "e5-small"
# EMBEDDING_PRESET = "minilm"
```

対応プリセットは以下です。

| preset | model | 特徴 |
|---|---|---|
| `e5-base` | `intfloat/multilingual-e5-base` | 精度寄り |
| `e5-small` | `intfloat/multilingual-e5-small` | 軽量 |
| `minilm` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | さらに軽量 |

E5系では、

```text
テーマ・ドライバー側: query:
ニュース側: passage:
```

のprefixが自動付与されます。

```python
query_prefix = "query: "
passage_prefix = "passage: "
```

MiniLMではprefixは付けません。

E5/MiniLM版では、ニュース、テーマ、ドライバーをすべて同じ意味ベクトル空間に写像します。

```text
X_news
X_theme
X_driver
```

その後、L2正規化済みembeddingの内積をcosine類似度として使います。

```python
semantic_similarity = X_news @ X_theme.T
```

この版の長所は、

```text
表現揺れに強い
キーワードが完全一致しなくても意味的に近いニュースを拾える
英日混在でも比較的扱いやすい
```

です。

短所は、

```text
sentence-transformers のインストールが必要
モデルロードに時間がかかる
大量ニュースではGPUまたはバッチ処理設計が必要
```

です。

---

# 13. relevance の計算

TF-IDF版でもE5/MiniLM版でも、最終的な関連度 `relevance` は同じ設計です。

```python
weights = [0.42, 0.23, 0.18, 0.10, 0.07]

components = [
    driver_semantic_sim,
    theme_semantic_sim,
    driver_keyword_score,
    theme_keyword_score,
    entity_score,
]
```

つまり、

```text
42% ドライバー意味類似度
23% テーマ意味類似度
18% ドライバーキーワード一致
10% テーマキーワード一致
 7% 銘柄・企業名一致
```

です。

式で書くと、

$$
relevance =
0.42 \cdot driver\_sim
+ 0.23 \cdot theme\_sim
+ 0.18 \cdot driver\_kw
+ 0.10 \cdot theme\_kw
+ 0.07 \cdot entity\_score
$$

に近い設計です。

この設計の意図は、ニュースが単にテーマ名に似ているかではなく、**どの収益ドライバーに効くニュースか**を重視することです。

---

# 14. novelty の計算

ニュースの新規性 `novelty` も計算しています。

TF-IDF版では、直近50本のニュースとのTF-IDF cosine類似度を見ます。

E5/MiniLM版では、直近50本のニュースembeddingとのcosine類似度を見ます。

考え方は同じです。

```python
novelty = 1 - max_similarity_to_recent_articles
```

つまり、直近ニュースと似ていないほど新規性が高くなります。

---

# 15. `article_driver_scores`

ニュース分類の最初の出力が `article_driver_scores` です。

これは、ニュース × テーマ × ドライバー単位の表です。

主な列は以下です。

```text
news_id
date
theme_id
driver_id
driver_name_ja
source_type
source_quality
theme_semantic_sim
driver_semantic_sim
theme_keyword_score
driver_keyword_score
entity_score
relevance
pos_score
neg_score
impact
risk_score
evidence
novelty
headline
```

E5/MiniLM版ではさらに、

```text
embedding_preset
embedding_model_name
theme_semantic_sim_raw
driver_semantic_sim_raw
```

も出ます。

この表を見ると、

```text
どのニュースが
どのテーマの
どの収益ドライバーに
どれだけ関連し
ポジティブかネガティブか
```

を確認できます。

---

# 16. 日次テーマ特徴量への集約

次に `aggregate_daily_theme_features()` が、ニュース単位の分類結果を日次テーマ特徴量へ変換します。

まず、ドライバー単位のスコアから、ニュース×テーマ単位のスコアを作ります。

```python
signed_signal =
    relevance
  * impact
  * evidence
  * source_quality
  * (0.60 + 0.40 * novelty)
```

この `signed_signal` が、そのニュースがテーマに与える方向付きインパクトです。

ポジティブ成分、ネガティブ成分、リスク成分も別に作っています。

```python
positive_signal_component =
    relevance * max(impact, 0) * evidence * source_quality

negative_signal_component =
    relevance * max(-impact, 0) * evidence * source_quality

risk_component =
    relevance * risk_score * source_quality
```

---

# 17. `daily_features`

日次テーマ特徴量 `daily_features` の主な列は以下です。

```text
date
theme_id
attention
n_relevant_articles
driver_signal
positive_signal
negative_signal
risk_signal
novelty
entity_breadth
article_breadth_proxy
breadth
matched_tickers
attention_z
driver_signal_z
positive_signal_z
negative_signal_z
risk_signal_z
novelty_z
breadth_z
driver_signal_ewm
driver_signal_ewm_z
breadth_ewm
breadth_ewm_z
```

意味は以下です。

| 列 | 意味 |
|---|---|
| `attention` | 関連ニュース量。relevanceの合計 |
| `n_relevant_articles` | relevanceが0.20を超える記事数 |
| `driver_signal` | ニュースが示す方向付きテーマ材料 |
| `positive_signal` | ポジティブ材料 |
| `negative_signal` | ネガティブ材料 |
| `risk_signal` | リスク材料 |
| `novelty` | 関連ニュースの新規性 |
| `breadth` | 銘柄・記事の広がり |
| `driver_signal_ewm_z` | ドライバーシグナルの平滑化・標準化値 |
| `breadth_ewm_z` | breadthの平滑化・標準化値 |

標準化は、テーマごとのrolling z-scoreです。

```python
rolling_z(window=60, min_periods=20)
```

これにより、テーマ間でニュース量の水準が違っても、通常時からの変化として比較できます。

---

# 18. breadth の考え方

`breadth` は、テーマ内でどの程度広がりがあるかを見ます。

銘柄名・RIC・aliasがニュース本文に出た場合は、構成銘柄ベースの広がりを見ます。

```python
entity_breadth = matched_ticker_count / number_of_theme_holdings
```

銘柄名が出ないテーマニュースもあるため、記事数ベースのproxyも使います。

```python
article_breadth_proxy = min(1.0, relevant_article_count / 5.0)
```

最終的には、

```python
breadth = max(entity_breadth, 0.50 * article_breadth_proxy)
```

です。

つまり、特定銘柄だけのニュースより、複数銘柄・複数記事へ広がるテーマを高く評価します。

---

# 19. 価格・リターン側の特徴量

ニュースだけでなく、価格にどの程度織り込まれているかも見ます。

デモでは `make_demo_market_data()` が以下を生成しています。

```text
theme_returns_df
factor_returns_df
constituent_returns_df
valuation_df
```

本番では、ここを実データに差し替えます。

必要なデータは以下です。

```text
theme_returns_df:
  date, theme_id, ret

factor_returns_df:
  date, MKT_JP, VALUE, GROWTH, USDJPY, GLOBAL_CAPEX など

constituent_returns_df:
  date, theme_id, ticker, ret

valuation_df:
  date, theme_id, valuation_penalty, crowding_penalty
```

---

# 20. テーマリターンの残差化

`rolling_residualize_returns()` は、テーマリターンをファクターでrolling回帰し、残差リターンを作ります。

概念的には、

$$
r_{k,t}
=
\alpha_{k,t}
+
\beta_{k,t}^{\top} f_t
+
\epsilon_{k,t}
$$

です。

ここで、

```text
r_{k,t}: テーマ k のリターン
f_t: 市場、バリュー、グロース、為替、設備投資サイクルなどのファクター
epsilon_{k,t}: ファクターで説明されないテーマ固有リターン
```

コードでは、

```python
lookback = 90
min_obs = 40
```

のrolling回帰です。

出力される主な列は、

```text
pred_ret
resid_ret
```

です。

この `resid_ret` を使うことで、市場全体やスタイル要因ではなく、テーマ固有の価格反応を見ます。

---

# 21. coherence

`calc_theme_coherence()` は、テーマ構成銘柄のリターン相関からテーマの一体性を測ります。

処理は以下です。

```text
1. テーマごとに構成銘柄リターンをwide化
2. rolling 60日で銘柄間相関を計算
3. 上三角の平均相関を取る
4. [-1, 1] を [0, 1] に変換
```

テーマ内の銘柄が同じ方向に動くほど、テーマとしての市場認識が強いと解釈します。

---

# 22. underreaction

`add_price_and_risk_features()` では、ニュースシグナルと価格反応の差から `underreaction` を作ります。

```python
underreaction = driver_signal_ewm_z - 0.60 * resid_mom_5_z
```

意味は、

```text
ニュース材料は強い
しかし短期の残差モメンタムはまだ強くない
```

という状態を高く評価することです。

つまり、ニュースに対して価格がまだ十分に反応していない可能性を狙います。

---

# 23. 魅力度スコア

`add_rule_score()` がルールベースのテーマ魅力度を計算します。

式は以下です。

```python
rule_score_raw =
    0.25 * driver_signal_ewm_z
  + 0.15 * attention_z
  + 0.15 * breadth_ewm_z
  + 0.10 * novelty_z
  + 0.15 * underreaction
  + 0.10 * coherence_z
  - 0.10 * valuation_crowding_penalty_z
  - 0.10 * risk_penalty_z
```

意味は以下です。

| 項目 | 符号 | 意味 |
|---|---:|---|
| `driver_signal_ewm_z` | + | 収益ドライバーに沿った好材料 |
| `attention_z` | + | 通常比でニュース量が増えている |
| `breadth_ewm_z` | + | テーマの広がりがある |
| `novelty_z` | + | 新規性がある |
| `underreaction` | + | 価格がまだ十分に反応していない可能性 |
| `coherence_z` | + | 構成銘柄がテーマとして動いている |
| `valuation_crowding_penalty_z` | - | バリュエーション・混雑が高い |
| `risk_penalty_z` | - | リスクニュースが多い |

その後、同じ日付内でテーマ間比較できるように、

```python
rule_score_cs = cross_sectional_z(rule_score_raw)
```

を作ります。

---

# 24. Walk-forward MLスコア

`walkforward_ml_score()` は、過去データだけを使って、将来20営業日の残差リターンを予測します。

ターゲットは、

```python
target_fwd_20d_resid
```

です。

特徴量は以下です。

```python
feature_cols = [
    "driver_signal_ewm_z",
    "attention_z",
    "breadth_ewm_z",
    "novelty_z",
    "underreaction",
    "coherence_z",
    "valuation_penalty_z",
    "crowding_penalty_z",
    "risk_signal_z",
    "resid_mom_5_z",
    "resid_mom_20_z",
    "resid_vol_20_z",
]
```

モデルは、

```python
StandardScaler()
Ridge(alpha=10.0)
```

のシンプルなRidge回帰です。

リーケージを避けるため、

```python
embargo_bdays = 20
```

を置いています。つまり、ある日付の予測を作る際に、将来20営業日のターゲットが重なる直近データを学習から除外します。

最終スコアは、

```python
final_score = 0.70 * rule_score_cs + 0.30 * ml_score_cs
```

です。

ルールスコアを主、MLを補助として扱う設計です。

---

# 25. テーマ配分最適化

`build_portfolio_weights()` がテーマスコアから配分を作ります。

最適化問題は概念的には以下です。

$$
\max_w
\quad
\mu^\top w
-
\lambda w^\top \Sigma w
-
c \|w-w_{prev}\|_1
$$

制約は、

```text
long-only
sum(w) = 1
0 <= w_i <= max_weight
```

です。

コードの主なパラメータは以下です。

```python
max_weight = 0.70
risk_aversion = 8.0
turnover_cost = 0.0015
score_scale = 0.0030
lookback_cov = 60
```

`mu` は `final_score` をスケール変換したものです。

```python
mu = score_scale * scores
```

共分散は、テーマリターンの過去60日から推定します。

```python
estimate_covariance_for_date()
```

さらに、テーマ間の構成銘柄重複も見ています。

```python
holdings_overlap_matrix()
```

同じ銘柄を多く含むテーマ同士に過度に配分しないよう、重複を共分散に上乗せしています。

---

# 26. バックテスト

`run_backtest()` は、日次で決めたテーマウェイトを翌営業日のリターンに適用します。

```python
strategy_return_t = weight_t * return_{t+1}
```

つまり、当日終値時点でシグナルを作り、翌日のリターンで評価する形です。

比較対象は等ウェイトです。

出力されるものは、

```text
backtest_df
perf_df
```

です。

`perf_df` には以下が入ります。

```text
ann_return
ann_vol
sharpe
max_drawdown
avg_daily_turnover
```

---

# 27. 日次レポート

`latest_theme_report()` は、最新日のテーマランキングと配分を出します。

主な列は以下です。

```text
date
theme_id
theme_name_ja
theme_type
rank
weight
final_score
rule_score_cs
ml_score_cs
driver_signal_ewm_z
attention_z
breadth_ewm_z
novelty_z
underreaction
coherence_z
valuation_crowding_penalty_z
risk_penalty_z
resid_mom_5_z
resid_vol_20_z
```

また、直近10営業日の重要ニュースとして、

```python
recent_news_report
```

も作っています。

これは、テーマスコアの根拠となるニュースを監査するための表です。

---

# 28. CSV出力

最後に、以下のCSVを出力します。

```text
theme_model_outputs/theme_score_panel.csv
theme_model_outputs/theme_weights.csv
theme_model_outputs/theme_backtest.csv
theme_model_outputs/latest_theme_report.csv
theme_model_outputs/recent_news_report.csv
```

それぞれの意味は以下です。

| ファイル | 内容 |
|---|---|
| `theme_score_panel.csv` | 全日付・全テーマの特徴量とスコア |
| `theme_weights.csv` | 日次テーマ配分 |
| `theme_backtest.csv` | 戦略リターン、等ウェイトリターン、ターンオーバー |
| `latest_theme_report.csv` | 最新日のテーマランキング |
| `recent_news_report.csv` | 直近ニュース根拠 |

---

# 29. 本番投入時に差し替えるべき部分

デモとして生成している部分は、本番では必ず差し替えます。

## 差し替え1：ニュース

LSEGを使う場合：

```python
NEWS_SOURCE_MODE = "lseg"
REUTERS_START_DATE = "2025-01-01"
REUTERS_END_DATE = None
REUTERS_FETCH_STORY_BODY = False
```

CSVを使う場合：

```python
NEWS_SOURCE_MODE = "csv"
REUTERS_CSV_PATH = Path("reuters_news.csv")
```

CSVの最小列：

```text
date または published_at
headline
```

推奨列：

```text
body
story_id
url
source_type
provider
```

## 差し替え2：構成銘柄

```python
holdings_df = pd.read_csv("theme_holdings.csv")
```

必須列：

```text
theme_id
ticker
weight
```

推奨列：

```text
company_name_ja
company_name_en
aliases
```

## 差し替え3：テーマリターン

```python
theme_returns_df = pd.read_csv("theme_returns.csv", parse_dates=["date"])
```

必須列：

```text
date
theme_id
ret
```

## 差し替え4：ファクターリターン

```python
factor_returns_df = pd.read_csv("factor_returns.csv", parse_dates=["date"])
```

必須列：

```text
date
任意のfactor columns
```

## 差し替え5：バリュエーション・混雑度

```python
valuation_df = pd.read_csv("theme_valuation_crowding.csv", parse_dates=["date"])
```

必須列：

```text
date
theme_id
valuation_penalty
crowding_penalty
```

---

# 30. 実務上の重要な注意点

このプログラムは、テーマ投資戦略のプロトタイプとして使える形にしていますが、本番運用では以下が重要です。

第一に、ニュース・テーマ定義・構成銘柄・価格データはすべて **point-in-time** にする必要があります。将来のテーマ定義や将来の構成銘柄を過去に使うと、look-ahead biasになります。

第二に、Reutersニュースの時刻と取引時刻の整合が必要です。現在の実装では日次 `date` に丸めていますが、本番では東京市場引け前・引け後、米国時間、休日の扱いを明示する必要があります。

第三に、`final_score` は投資判断の候補ランキングであって、単独の売買シグナルとしては不十分です。ポートフォリオ制約、流動性、コスト、テーマ間相関、個別銘柄のイベントリスクを別途見るべきです。

第四に、E5/MiniLM版ではembeddingモデルに依存するため、モデル変更時にはスコア分布が変わります。モデル間比較では、`theme_semantic_sim_raw` と `driver_semantic_sim_raw` の分布確認が必要です。

---

# 31. 一言でいうと

このプログラムは、Reutersニュースを以下の形でテーマ投資に変換するパイプラインです。

```text
Reuters headline / body
   ↓
theme / revenue driver relevance
   ↓
positive / negative / risk impact
   ↓
daily theme attention, novelty, breadth, driver signal
   ↓
price underreaction, coherence, valuation/crowding penalty
   ↓
relative theme attractiveness score
   ↓
long-only theme allocation
   ↓
backtest and daily report
```

TF-IDF版は軽量で本番MVP向き、E5/MiniLM版は意味類似度を強化した上位版です。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)