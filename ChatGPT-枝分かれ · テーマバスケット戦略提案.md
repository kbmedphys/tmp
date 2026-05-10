# 枝分かれ · テーマバスケット戦略提案

**User:** Anonymous  
**Created:** 5/11/2026 0:56:50  
**Updated:** 5/11/2026 1:28:36  
**Exported:** 5/11/2026 1:29:56  
**Link:** [https://chatgpt.com/c/6a00aac1-ab48-8324-8abb-ae4e1925ec61](https://chatgpt.com/c/6a00aac1-ab48-8324-8abb-ae4e1925ec61)  

## Response:
2026/5/11 0:09:58

利用可能データを活かし、テーマを投資家が同時売買する銘柄群・ナラティブとして扱う複合戦略に整理します。学術・実務根拠と日本市場制度を踏まえ、検証可能な設計に絞ります。

## Response:
2026/5/11 0:10:22

中核は、テーマリターンをファクター分解し、残差・ニュース・混雑度を別々に測ることです。仮説はモメンタムの発生と過度な話題化後の反転です。

## Response:
2026/5/11 0:14:16

> **Proposing a unified theme basket strategy**
>
> I’m thinking about presenting this as one coherent strategy rather than many separate ones. Perhaps I could build a multi-signal approach with modules. I'll need to outline the universe and theme categories, pulling in broker-provided Japanese equity theme baskets. Should I use equal or provider-weighted baskets, and how would I handle factor exposures? Including equations between factors like market beta, sector weights, and returns is key for clarity.
>
> Thought for 6m 43s

## Response:
2026/5/11 0:16:42

以下の設計が最も筋が良いです。**テーマを単なるラベルではなく、銘柄リターンの残差相関・ニュース・需給・ファンダメンタルを持つ“中間資産”として扱い、統計的に実在するテーマだけを売買対象にする**、という方針です。

## 1. 中核戦略：Theme Coherence Momentum

まず、証券会社が任意に作ったテーマバスケットをそのまま信じない方がよいです。テーマ名はマーケティング色が強く、同じ「AI」でも、半導体装置、データセンター、SaaS、ロボット、電力設備などが混在します。したがって、最初にやるべきことは、各テーマが本当に共通リスクを持つかを検定することです。

近年のテーマ投資研究では、テーマを「標準的なファクターでは説明できない一時的な残差相関を持つ銘柄群」と定義し、平均ペアワイズ残差相関をブートストラップで検定するアプローチが提案されています。重要なのは、統計的に有意な残差相関を持つテーマはトレンド性も示しやすい一方、有意でないテーマは平均的にはトレンドしにくい、という実務的に使える示唆です。([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5336504&utm_source=chatgpt.com))

### 実装

各銘柄リターンを、少なくとも以下で残差化します。

$$
r_{i,t}
=
\beta_{i}^{M}M_t
+\beta_{i}^{Size}Size_t
+\beta_{i}^{Value}Value_t
+\beta_{i}^{Mom}Mom_t
+\beta_{i}^{Sector}Sector_t
+\epsilon_{i,t}
$$

日本株なら、TOPIX、サイズ、バリュー、モメンタム、業種、場合によっては為替感応度、金利感応度、半導体グローバル指数、銀行なら金利スプレッドなども候補です。標準的なファクター分解の出発点として、Fama-French 型の市場・サイズ・バリュー要因は有用です。([サイエンスダイレクト](https://www.sciencedirect.com/science/article/pii/0304405X93900235?utm_source=chatgpt.com))

テーマ $k$ について、構成銘柄の残差 $\epsilon_{i,t}$ から平均ペアワイズ残差相関を計算します。

$$
APC_{k,t}
=
\frac{2}{n_k(n_k-1)}
\sum_{i<j \in k}
corr(\epsilon_{i}, \epsilon_{j})
$$

この $APC$ が有意なテーマだけを「本物のテーマ候補」とします。次に、そのテーマの過去 3か月、6か月、12か月リターンを使い、1か月スキップのモメンタムを作ります。

$$
Signal^{mom}_{k,t}
=
z\left(
\frac{R_{k,t-252:t-21}}{\sigma_{k,t}}
\right)
$$

月次または隔週で、上位テーマをロング、下位テーマまたはTOPIXをショートします。ロングオンリー運用なら、上位テーマをオーバーウェイト、下位テーマをアンダーウェイトにします。

この設計は、個別株モメンタムよりもテーマ・業種単位の共通リターンを狙うものです。業種モメンタムが個別株モメンタムの大きな部分を説明するという古典的結果、および 1〜12か月程度の時系列モメンタムの実証結果と整合的です。([Wiley Online Library](https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00146?utm_source=chatgpt.com))

---

## 2. ニュース確認型テーマ・モメンタム

次に、Reuters ニュースを使って、テーマモメンタムを確認します。ニュースを全件取得できないという制約はむしろ自然です。全ニュースを読むのではなく、**テーマの状態変化を測るためのサンプリング設計**にするべきです。LSEG Data Library はニュースヘッドラインのページング取得などをサポートしており、ニュースをプログラムで取得するワークフロー自体は構築可能です。([developers.lseg.com](https://developers.lseg.com/en/article-catalog/article/lseg-data-library-for-python--news-pagination?utm_source=chatgpt.com))

### 推奨するニュース取得設計

ニュース取得は三層に分けます。

第一層は、**短期・広範囲サンプル**です。過去 5〜10営業日の日本関連ニュースを広めに取り、全テーマに対するニュース量の変化を測ります。これは「どのテーマに市場の注意が向いているか」を見るためです。

第二層は、**候補テーマへの深掘り**です。Theme Coherence Momentum で上位または下位に来たテーマだけについて、30〜90日程度のニュースを深く取りに行きます。AI、半導体、防衛、造船、銀行、低PBR、TOB、配当、自社株買いなど、テーマごとにキーワード・トピックコード・構成銘柄RICを組み合わせます。

第三層は、**イベント型クエリ**です。決算、受注、政策、補助金、TOB、親子上場解消、自社株買い、増配、アクティビスト、資本政策、設備投資など、価格形成に直結しやすいイベントだけを狙います。

### ニュース特徴量

テーマ $k$ に対して、以下を作ります。

$$
NewsSurprise_{k,t}
=
\log(1+Count_{k,t})
-
EMA(\log(1+Count_{k,t}))
$$

さらに、以下を加えます。

| 特徴量 | 意味 |
|---|---|
| ニュース件数サプライズ | 通常時よりニュースが増えているか |
| ニュース・ブレッドス | テーマ内の何銘柄にニュースが出ているか |
| センチメント | ヘッドライン・リード文のポジティブ/ネガティブ |
| ノベルティ | 同じニュースの再配信ではなく新規情報か |
| イベントタイプ | 受注、政策、決算、資本政策、M&Aなど |
| 構成銘柄ウェイト加重 | 大型構成銘柄のニュースか、周辺銘柄だけか |

ニュースを単独シグナルにするよりも、**価格モメンタムの確認フィルター**として使う方が堅いです。

$$
Score_{k,t}
=
0.45 \cdot Momentum_{k,t}
+
0.25 \cdot Coherence_{k,t}
+
0.20 \cdot NewsConfirmation_{k,t}
-
0.10 \cdot Crowding_{k,t}
$$

ニュースやメディアのトーンが株価・出来高・投資家行動に影響することは、Tetlock、Barber-Odean、Loughran-McDonald 以降の文献と整合的です。特に、個人投資家はニュースや異常出来高など注意を引く銘柄を買いやすいこと、金融テキストでは一般的な辞書より金融文脈に適した語彙が重要であることが示されています。([OUP Academic](https://academic.oup.com/rfs/article-abstract/21/2/785/1607197?utm_source=chatgpt.com))

---

## 3. 日本株固有の高確度スリーブ：PBR・ガバナンス・資本効率リレーティング

日本株で特に実務的な期待値があるのは、低PBR、ガバナンス、高配当、上場子会社、親子上場解消、政策保有株削減、自社株買い、ROE改善などのテーマです。これは単なるバリュー投資ではなく、東京証券取引所の要請を背景にした**資本効率改善イベント・ドリブン**として設計すべきです。

TSE は 2023年3月31日にプライム市場・スタンダード市場の全上場会社に対して「資本コストや株価を意識した経営」の実現に向けた対応を要請し、2026年4月28日にも投資家期待や経営資源配分に関するポイントを更新しています。また、開示済み企業リストを月次更新しており、企業が「開示済み」「検討中」などの状態にあるかを確認できます。([日本取引所グループ](https://www.jpx.co.jp/english/equities/follow-up/02.html))

### 銘柄スコア

低PBRテーマやガバナンステーマを、単純にロングするのは危険です。低PBRにはバリュートラップが多いからです。以下のようなスコアに分解します。

$$
PBRReformScore_i
=
Cheapness_i
+
CapitalEfficiency_i
+
BalanceSheetOptionality_i
+
GovernanceCatalyst_i
+
ShareholderReturn_i
-
ValueTrapRisk_i
$$

具体的には、

| 要素 | 指標例 |
|---|---|
| Cheapness | PBR、PER、EV/EBITDA、セクター内相対バリュエーション |
| Capital Efficiency | ROE、ROIC、ROE改善率、ROIC-WACCスプレッド |
| Balance Sheet Optionality | ネットキャッシュ、政策保有株、遊休資産 |
| Governance Catalyst | TSE開示状況、CG報告書更新、英文開示、取締役会構成 |
| Shareholder Return | 自社株買い、増配、総還元性向、DOE導入 |
| Value Trap Risk | 低ROE固定化、赤字継続、資本効率改善策なし、流動性低下 |

テーマバスケットのスコアは構成銘柄のウェイト加重平均で作ります。

$$
ThemePBRScore_k
=
\sum_{i \in k}
w_{i,k}
PBRReformScore_i
$$

### 売買方針

このスリーブでは、以下をロング候補にします。

低PBRかつROE改善余地があり、TSE対応開示・自社株買い・増配・政策保有株削減・親子上場解消などのカタリストがあるテーマ。

ショートまたはアンダーウェイト候補は、低PBRだが資本効率改善の兆候がなく、低成長・低ROE・低流動性・ガバナンス改善なしのテーマです。

対象としては、**低PBR、ガバナンス、高配当、上場子会社、親子上場、政策保有株、メガバンク、地銀、商社、資本政策改善期待**などが有力です。これは 3〜18か月程度の中期スリーブとして扱うのが自然です。

---

## 4. Crowding Reversal：過熱テーマの逆張り・ヘッジ

AI、半導体、防衛、造船、宇宙、データセンター、未黒字企業のようなテーマは、トレンドが出る一方で、ニュース・出来高・証券会社レポート・個人投資家関心が集中すると、短期的に過熱しやすいです。

ここではロング戦略のリスク管理として、**過熱後のリバーサル検出**を入れます。

$$
Crowding_{k,t}
=
z(Turnover_{k,t})
+
z(VolumeSurprise_{k,t})
+
z(NewsSurprise_{k,t})
+
z(ResidualCorrJump_{k,t})
+
z(ReturnAcceleration_{k,t})
$$

次の条件を満たしたら、テーマウェイトを削減します。

$$
Crowding_{k,t} > threshold
\quad \text{and} \quad
MomentumShortTerm_{k,t} < 0
$$

つまり、ニュースも出来高も価格も過熱しているが、短期モメンタムが折れ始めた局面です。これは、テーマバスケットのショートというより、既存ロングの利確・ヘッジ・リスク削減に使う方が実務的です。

特に未黒字企業テーマは、ファンダメンタルのアンカーが弱く、バリュエーションが主観的で裁定しにくいため、センチメント影響を受けやすい領域です。投資家センチメントは、主観的評価が大きく裁定困難な銘柄群により強く影響しやすいという文献とも整合的です。([IDEAS/RePEc](https://ideas.repec.org/a/bla/jfinan/v61y2006i4p1645-1680.html?utm_source=chatgpt.com))

---

## 5. セマンティック純度戦略：テーマらしい銘柄だけを抽出する

Refinitive から会社概要説明文や業種コードが取れるなら、これはかなり有用です。証券会社のテーマバスケットには、「名前だけ入っている銘柄」「主力事業ではないがテーマに関連する銘柄」「業種ベータだけの銘柄」が混じります。

そこで、テーマ定義文と会社概要文の類似度を使って、テーマ純度を作ります。

$$
SemanticPurity_{i,k}
=
Similarity(ThemeDescription_k, CompanyDescription_i)
$$

さらに、TRBCや業種コード、売上セグメント、ニュース内でのテーマ語出現、複数証券会社バスケットへの採用有無を加えます。

$$
ThemePurity_{i,k}
=
0.35 \cdot SemanticSimilarity
+
0.25 \cdot NewsRelevance
+
0.20 \cdot IndustryFit
+
0.20 \cdot BrokerConsensus
$$

使い方は二つあります。

一つ目は、テーマバスケットをそのまま売買せず、**高純度銘柄だけで再構成する**ことです。AIなら、本業がAI・半導体・データセンター・生成AIソフトウェアに近い銘柄を残し、単に周辺扱いで入っている低純度銘柄を落とします。

二つ目は、**高純度銘柄ロング、低純度銘柄ショート**です。テーマが本当に買われる局面では、高純度銘柄の方がニュース・資金流入・アナリスト注目を受けやすい可能性があります。

---

## 6. テーマ間リード・ラグ戦略

テーマは独立ではありません。半導体、AI、データセンター、電力設備、電子部品、製造装置、素材、商社は連鎖します。防衛、造船、重工、電子部品、サイバーセキュリティもつながります。銀行、保険、証券、高配当、低PBRも重なります。

この構造を使い、テーマ間のリード・ラグを推定します。

$$
\hat{R}_{k,t+h}
=
\alpha_k
+
\sum_{\ell \neq k}
\beta_{k,\ell}R_{\ell,t}
+
\sum_{\ell \neq k}
\gamma_{k,\ell}News_{\ell,t}
+
u_{k,t}
$$

ただし、全テーマで無制約 VAR を組むと過学習します。制約として、以下のどれかを満たすテーマ間だけにエッジを張るべきです。

| エッジ条件 | 例 |
|---|---|
| 構成銘柄の重複 | AIと半導体、低PBRと高配当 |
| 業種・TRBCの近接 | 造船と重工、防衛と電子部品 |
| 会社説明文の近接 | データセンターと電力設備 |
| ニュース共起 | 同一ニュース内で複数テーマが言及される |
| 価格残差の先行相関 | あるテーマの残差リターンが別テーマを先行 |

経済的につながった企業群では、投資家の注意制約によりニュースやリターンの反映が遅れ、予測可能性が生じるという研究があります。テーマ間リード・ラグは、この考え方をテーマバスケットに拡張したものです。([IDEAS/RePEc](https://ideas.repec.org/a/bla/jfinan/v63y2008i4p1977-2011.html?utm_source=chatgpt.com))

---

## 推奨ポートフォリオ構成

実務で使うなら、単一モデルではなく、以下の 3 スリーブ構成がよいです。

| スリーブ | 役割 | 期間 | 対象テーマ |
|---|---:|---:|---|
| Coherent Theme Momentum | 主力アルファ | 1〜6か月 | AI、半導体、防衛、造船、銀行、データセンターなど |
| PBR/Governance Re-rating | 日本株固有アルファ | 3〜18か月 | 低PBR、ガバナンス、高配当、上場子会社、親子上場 |
| Crowding/Reversal Hedge | ドローダウン抑制 | 数日〜2か月 | 未黒字企業、急騰テーマ、ニュース過熱テーマ |

配分例は、リスクベースで以下です。

$$
Portfolio
=
60\% \cdot ThemeMomentum
+
30\% \cdot PBRGovernance
+
10\% \cdot CrowdingHedge
$$

資本配分ではなく、**リスク寄与ベース**で管理する方がよいです。AIや半導体のような高ボラテーマは、名目配分を抑えてもリスク寄与が大きくなります。

---

## 実装上の重要ポイント

最終的な売買は、テーマ単位ではなく銘柄単位に落とすべきです。複数テーマに同じ銘柄が入るため、テーマウェイトを単純に足すと、東京エレクトロン、アドバンテスト、三菱重工、川崎重工、メガバンク、大手商社などに意図せぬ集中が起きます。

テーマ配分 $a_{k,t}$ が決まったら、銘柄ウェイトは次のように集約します。

$$
x_{i,t}
=
\sum_k
a_{k,t}w_{i,k,t}
$$

その後、制約付き最適化をかけます。

$$
\max_x
\quad
s_t'x
-
\lambda x'\Sigma x
-
Cost(x-x_{t-1})
$$

制約は、TOPIXベータ、業種、個別銘柄上限、ADV参加率、売買回転率、空売り可否、流動性、借株コスト、テーマ上限を入れます。

---

## バックテスト設計

この案件で一番危険なのは、テーマ数・窓・ニュース条件・業種調整・ウェイト方式を何度も試して、偶然当たったものを選ぶことです。データスヌーピングは、同じデータを繰り返し使ってモデル選択すると、見かけ上よい結果が偶然生じる問題として古くから指摘されています。また、Deflated Sharpe Ratio は、選択バイアス、非正規性、バックテスト過学習を補正する実務的な評価指標として使えます。([Social Science Computing Core](https://www.ssc.wisc.edu/~bhansen/718/White2000.pdf?utm_source=chatgpt.com))

最低限、以下を守るべきです。

1. **Point-in-time データ**  
   テーマ構成、ウェイト、TSE開示状況、ニュース、会社概要、業種コードは、利用可能日ベースで管理します。

2. **テーマ誕生日の扱い**  
   証券会社が後から作ったテーマを過去に遡ってバックフィルすると危険です。バックフィル版とローンチ後版を分けて評価します。

3. **ウォークフォワード検証**  
   2016-2020年で設計、2021-2023年で検証、2024年以降でアウトオブサンプル、のように期間を分けます。

4. **コスト控除後で評価**  
   Bloomberg の出来高、スプレッド、回転率、ADVを使い、売買コストとマーケットインパクトを入れます。

5. **重複銘柄を必ず見る**  
   テーマ別の見かけ上の分散ではなく、銘柄レベルの実質エクスポージャーでリスクを見ます。

6. **ファクター寄与を分解**  
   アルファが単なるバリュー、サイズ、業種、TOPIXベータ、円安感応度、金利感応度ではないかを確認します。

---

## テーマ別の使い分け

| テーマ群 | 有効な戦略 | 注意点 |
|---|---|---|
| AI・半導体 | Coherence Momentum + News Confirmation | 過熱・重複集中・米国半導体指数依存 |
| 造船・防衛 | ニュース確認型モメンタム + 政策/受注イベント | 受注ニュースと実収益化のラグ |
| メガバンク | 金利・資本政策・高配当・低PBRスリーブ | TOPIXバリュー/金利ベータの分解が必要 |
| 低PBR | PBR改革スコア | 低PBRだけではバリュートラップ |
| ガバナンス | TSE開示・資本政策イベント | 開示済みでも中身が弱い企業を除外 |
| 高配当 | バリュー/金利/減配リスク調整 | 利回りだけで買わない |
| 上場子会社 | 親子上場解消・TOB期待 | 流動性とイベント待ち期間 |
| 未黒字企業 | 原則は過熱検知・選別ロング | ニュース過熱後の反落リスクが大きい |

---

## 最も推奨する最小構成

最初に作るべき MVP は、以下です。

**月次リバランスのロング・ショートまたはロング・アンダーウェイト戦略**として、

$$
FinalScore_k
=
0.35 \cdot ResidualMomentum_k
+
0.25 \cdot ThemeCoherence_k
+
0.20 \cdot NewsConfirmation_k
+
0.20 \cdot PBRGovernanceCatalyst_k
-
0.15 \cdot CrowdingRisk_k
$$

上位テーマをロング、下位テーマまたはTOPIXをショートします。PBR/Governance 系テーマは中期保有、AI/半導体/防衛/造船系はモメンタムとニュース確認、未黒字・急騰テーマはクラウディング抑制を強めます。

この戦略の肝は、**テーマ名を買うのではなく、統計的にまとまりがあり、価格トレンドがあり、ニュースで裏付けられ、過度に混雑していないテーマだけを買う**ことです。日本株ではさらに、TSE改革を背景にした低PBR・ガバナンス・資本政策テーマを独立スリーブとして持つのが、学術的にも実務的にも最も納得感があります。

---

**Sources:**

- [Thematic Investing: A Risk-based Perspective](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5336504&utm_source=chatgpt.com)
- [Common risk factors in the returns on stocks and bonds](https://www.sciencedirect.com/science/article/pii/0304405X93900235?utm_source=chatgpt.com)
- [Do Industries Explain Momentum? - Moskowitz - 1999](https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00146?utm_source=chatgpt.com)
- [LSEG Data Library for Python: News Pagination | Devportal](https://developers.lseg.com/en/article-catalog/article/lseg-data-library-for-python--news-pagination?utm_source=chatgpt.com)
- [That Glitters: The Effect of Attention and News on the Buying ...](https://academic.oup.com/rfs/article-abstract/21/2/785/1607197?utm_source=chatgpt.com)
- [Action to Implement Management that is Conscious of Cost of Capital and Stock Price (Prime and Standard Markets) | Japan Exchange Group](https://www.jpx.co.jp/english/equities/follow-up/02.html)
- [Investor Sentiment and the Cross‐Section of Stock Returns](https://ideas.repec.org/a/bla/jfinan/v61y2006i4p1645-1680.html?utm_source=chatgpt.com)
- [A REALITY CHECK FOR DATA SNOOPING ...](https://www.ssc.wisc.edu/~bhansen/718/White2000.pdf?utm_source=chatgpt.com)

## Response:
2026/5/11 0:21:37

本提案の中核を、運用実装に耐える「テーマ・コヒーレンス付きモメンタム＋ニュース確認＋クラウディング制御」として整理します。根拠、データ設計、推定、最適化、検証まで一体化します。

## Response:
2026/5/11 0:21:53

差別化点は、テーマを所与の分類でなく、残差相関で検定された中間リスク・プレミアムとして再定義することです。日本株固有のPBR・ガバナンス改革も重ねます。

## Response:
2026/5/11 0:27:35

## 提案手法：CGNM-GCO  
**Coherence-Gated Narrative Momentum with Governance Catalyst Overlay**

最良案は、テーマバスケットをそのまま売買するのではなく、まず**統計的に“テーマとして実在する”バスケットだけを選別**し、そのうえで、**残差モメンタム、Reuters ニュースによるナラティブ確認、日本株固有の資本効率・ガバナンス・PBR 改革カタリスト**を合成して配分する手法です。

中核思想は以下です。

$$
\textbf{テーマ名を買うのではなく、}
\quad
\textbf{残差相関・価格トレンド・ニュース確認・資本政策カタリストを持つテーマだけを買う。}
$$

テーマ投資の学術的整理としては、近年、テーマを「共通ファクターでは説明しきれない一時的な残差相関を持つ銘柄群」と定義し、テーマ内の平均ペアワイズ残差相関をブートストラップで検定する考え方が提示されています。この研究では、統計的に有意な平均残差相関を持つテーマバスケットはトレンド性を示す一方、有意でないテーマは平均的にはトレンドしない、という本戦略に直接関係する示唆が示されています。([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5336504))

---

# 1. 戦略の全体像

本手法は、4 層構造にします。

| 層 | 役割 | 目的 |
|---|---|---|
| Layer 1 | Theme Coherence Gate | 任意に作られたテーマのうち、本当に共通リスクを持つものだけを選ぶ |
| Layer 2 | Residual Theme Momentum | 市場・業種・スタイルを除いたテーマ固有トレンドを取る |
| Layer 3 | News / Narrative Confirmation | Reuters ニュースでテーマへの注意・材料・拡散を確認する |
| Layer 4 | Governance / PBR Catalyst Overlay | 日本株固有の資本効率改善テーマを中期アルファとして加える |

補助的に、過熱テーマを減額する **Crowding Reversal Control** を入れます。

最終的なテーマスコアは、概念的には次の形です。

$$
Score_{k,t}
=
G(C_{k,t},P_{k,t})
\cdot
\left[
0.45M_{k,t}
+
0.20N_{k,t}
+
0.20Q_{k,t}
+
0.15V_{k,t}
\right]
-
0.25H_{k,t}
$$

ここで、

| 記号 | 意味 |
|---|---|
| $C_{k,t}$ | テーマ $k$ の残差相関上の実在性、coherence |
| $P_{k,t}$ | テーマ純度、semantic / industry purity |
| $M_{k,t}$ | 残差テーマ・モメンタム |
| $N_{k,t}$ | ニュース確認シグナル |
| $Q_{k,t}$ | PBR・ガバナンス・資本政策カタリスト |
| $V_{k,t}$ | バリュエーション・ファンダメンタル補助シグナル |
| $H_{k,t}$ | 過熱・クラウディング・反転リスク |
| $G(C,P)$ | coherence と purity によるゲート関数 |

重要なのは、**coherence と purity は加点項ではなく、原則としてゲート**にすることです。つまり、テーマとして統計的にまとまりがないものは、たとえ過去リターンが良くても主力ロング対象から外します。

---

# 2. 投資仮説

## 2.1 テーマバスケットはノイズを含む

証券会社が作るテーマバスケットは、実務上有用ですが、構成ルールはマーケティング的・裁量的です。AI、半導体、防衛、造船、低 PBR、ガバナンス、高配当、上場子会社のようなテーマは、投資家の注意や資金フローを集める一方、実際には次のようなノイズを含みます。

| ノイズ | 例 |
|---|---|
| 業種ベータの混入 | AI テーマが実質的には半導体装置ベータ |
| 周辺銘柄の混入 | 主力事業ではないが、テーマ名に関連しているだけの銘柄 |
| 大型株集中 | 複数テーマに同じ大型株が重複 |
| 後付けテーマ | 過去に上がった銘柄を後からテーマ化 |
| スタイル混入 | 高配当、低 PBR、銀行、バリューが同一リスクとして重複 |

したがって、テーマ名・構成銘柄・ウェイトをそのまま使うのではなく、まず**テーマとしての統計的実在性**を検定します。

## 2.2 価格トレンドはテーマ単位で生じやすい

モメンタムについては、個別株で過去の勝者を買い敗者を売る戦略が 3〜12か月程度の保有期間で正のリターンを生むという古典的実証があります。([EconPapers](https://econpapers.repec.org/RePEc%3Abla%3Ajfinan%3Av%3A48%3Ay%3A1993%3Ai%3A1%3Ap%3A65-91)) また、個別株モメンタムのかなりの部分は業種モメンタムによって説明されるという結果もあり、テーマバスケット戦略はこの「業種より細かく、個別株より粗い」中間粒度を狙う戦略として自然です。([AQRキャピタルマネジメント](https://www.aqr.com/Insights/Research/Journal-Article/Do-Industries-Explain-Momentum))

さらに、1〜12か月の時系列モメンタムが株価指数、通貨、商品、債券先物など複数資産で観測されるという研究もあり、テーマバスケットの時系列トレンドを使う設計と整合的です。([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463))

## 2.3 ニュースは「単独アルファ」ではなく「確認フィルター」として使う

ニュースはノイズが多く、単純なセンチメント売買は不安定です。しかし、テーマモメンタムにニュース確認を重ねると、投資家の注意、材料の拡散、ナラティブの強度を測れます。

個人投資家は、ニュースに出た銘柄、異常出来高の銘柄、大きく動いた銘柄のような「注意を引く銘柄」を買いやすいことが示されています。([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=460660)) また、金融テキストでは一般的な辞書のネガティブ語が金融文脈で誤分類されやすく、金融専用辞書・文脈処理が必要であることも示されています。([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1331573))

このため、Reuters ニュースは、  
**価格がすでに示しているテーマトレンドが、ニュースフローによって裏付けられているか**  
を確認する用途に限定するのが堅いです。

## 2.4 日本株では PBR・ガバナンス・資本政策が独立した構造アルファになり得る

日本株固有の強い材料は、TSE の「資本コストや株価を意識した経営」に関する要請です。TSE は 2023年3月31日にプライム市場・スタンダード市場の全上場会社に対応を要請し、2026年4月28日にも投資家期待や経営資源配分に関するポイントを更新しています。また、開示済み企業リストを月次で更新しており、開示状況、更新日、英文開示の有無、CG 報告書での記載内容などを確認できます。([日本取引所グループ](https://www.jpx.co.jp/english/equities/follow-up/02.html))

したがって、低 PBR、ガバナンス、高配当、上場子会社、親子上場解消、政策保有株削減、自社株買い、増配、ROE 改善といったテーマは、単なるバリュー・ファクターではなく、**資本効率改善イベント・ドリブン**として扱うべきです。

---

# 3. データ設計

## 3.1 必要データ

| データ | 取得元 | 用途 |
|---|---|---|
| テーマ定義 | 証券会社 | テーマ名、説明文、分類 |
| テーマ構成銘柄 | 証券会社 | 銘柄リスト、ウェイト、構成変更 |
| 株価・リターン | Bloomberg | 日次・週次・月次リターン |
| 出来高・売買代金 | Bloomberg | 流動性、回転率、クラウディング |
| ファクター | Bloomberg / 内製 | TOPIX、業種、サイズ、バリュー、モメンタム等 |
| 会社概要文 | Refinitive | semantic purity |
| 業種コード | Refinitive | TRBC / 業種近接度 |
| Reuters ニュース | lseg.data | ニュース件数、イベント、センチメント |
| TSE 対応状況 | JPX / TSE | PBR・ガバナンス・資本効率カタリスト |

LSEG Data Library for Python ではニュースヘッドライン取得が可能で、ニュースヘッドラインサービスは 1 リクエスト 100 件、過去 15か月分の履歴、カーソルベースのページネーションに対応しています。`ld.news.get_headlines` はヘッドライン取得に使えますが、カーソルページネーションを使うには content layer の `news.headlines.Definition` を使う必要があります。([LSEG Developers](https://developers.lseg.com/en/article-catalog/article/lseg-data-library-for-python--news-pagination))

---

# 4. Layer 1：Theme Coherence Gate

## 4.1 個別株リターンの残差化

まず個別株リターンを共通リスクで残差化します。

$$
r_{i,t}
=
\beta_i^\top F_t
+
\epsilon_{i,t}
$$

$F_t$ には、最低限以下を入れます。

| ファクター | 目的 |
|---|---|
| TOPIX / 市場リターン | 市場ベータ除去 |
| 業種ファクター | 業種ベータ除去 |
| サイズ | 小型株効果除去 |
| バリュー | PBR / PER / BTM 効果除去 |
| モメンタム | 汎用モメンタム効果除去 |
| クオリティ | ROE、利益率、財務健全性 |
| 低ボラ | ディフェンシブ効果除去 |
| 為替 | 輸出・輸入感応度 |
| 金利 | 銀行、保険、不動産等の金利感応度 |
| グローバル半導体 / SOX | 半導体テーマの外部ベータ |
| 原油・海運・防衛関連指数 | テーマ固有マクロ感応度 |

市場、サイズ、バリューなどの共通リスクファクターを使ってリターンを説明する発想は、Fama-French 型の多因子モデルと整合的です。([サイエンスダイレクト](https://www.sciencedirect.com/science/article/pii/0304405X93900235?utm_source=chatgpt.com))

推定は、日次なら 252〜504 営業日の rolling OLS / WLS を基本にします。ただし、日本株では小型株・低流動性株が混じるため、以下を推奨します。

$$
\hat{\beta}_{i,t}
=
\arg\min_\beta
\sum_{\tau=t-L}^{t}
\omega_{\tau}
\left(
r_{i,\tau}
-
\beta^\top F_\tau
\right)^2
+
\lambda \|\beta\|_2^2
$$

つまり、**指数減衰ウェイト付き ridge regression** です。  
小型株で推定が不安定な場合、業種平均ベータへの shrinkage を入れます。

---

## 4.2 テーマ内残差相関

テーマ $k$ の構成銘柄集合を $B_{k,t}$、構成ウェイトを $w_{i,k,t}$ とします。  
テーマ内の平均ペアワイズ残差相関を計算します。

$$
APC_{k,t}
=
\frac{2}{n_k(n_k-1)}
\sum_{i<j,\,i,j\in B_{k,t}}
corr(\epsilon_i,\epsilon_j)
$$

ウェイト付きにするなら、

$$
WAPC_{k,t}
=
\sum_{i<j}
\tilde{w}_{i,k,t}
\tilde{w}_{j,k,t}
corr(\epsilon_i,\epsilon_j)
$$

ただし、大型株 1〜2銘柄で支配されるテーマを避けるため、coherence 判定には equal-weighted と weighted の両方を使います。

## 4.3 ブートストラップ検定

テーマが本当にまとまっているかを、以下の帰無仮説で検定します。

$$
H_0:
\text{テーマ構成銘柄の残差相関は、同等の業種・サイズ・流動性を持つランダム銘柄群と変わらない}
$$

実務上は、次の 2 種類の null を併用します。

### Null A：Matched Random Basket

各テーマについて、構成銘柄と同じような業種、時価総額、流動性、PBR、ボラティリティを持つ銘柄からランダムバスケットを多数生成します。

$$
APC^{null,b}_{k,t},\quad b=1,\dots,B
$$

$$
p_{k,t}
=
\Pr
\left(
APC^{null,b}_{k,t}
\geq
APC_{k,t}
\right)
$$

### Null B：Residual Block Bootstrap

銘柄の時系列自己相関をある程度維持しながら、残差系列を block bootstrap します。  
特にニュースやイベントで相関が出るテーマでは、iid bootstrap ではなく block bootstrap の方が自然です。

---

## 4.4 Coherence Score

テーマ実在性を以下のように定義します。

$$
C_{k,t}
=
z(APC_{k,t})
+
z(\lambda_{1,k,t})
+
z(BreadthCorr_{k,t})
-
z(Instability_{k,t})
$$

| 指標 | 意味 |
|---|---|
| $APC$ | 平均ペアワイズ残差相関 |
| $\lambda_1$ | テーマ内残差共分散の第1固有値寄与 |
| BreadthCorr | 相関が一部銘柄だけでなく広く存在するか |
| Instability | 構成変更・相関構造の不安定性 |

採用基準の例は以下です。

$$
p_{k,t}<0.10
$$

$$
APC_{k,t}>0
$$

$$
n^{eff}_{k,t}
=
\frac{1}{\sum_i w_{i,k,t}^2}
\geq 8
$$

$$
\lambda_{1,k,t}
/
\sum_j \lambda_{j,k,t}
>
\theta_\lambda
$$

この条件を満たさないテーマは、たとえテーマ名が魅力的でも主力ロング候補から除外します。

---

# 5. Layer 2：Residual Theme Momentum

## 5.1 テーマ残差リターン

テーマの生リターンではなく、構成銘柄の残差リターンからテーマ固有リターンを作ります。

$$
U_{k,t}
=
\sum_{i\in B_{k,t}}
\tilde{w}_{i,k,t}
\epsilon_{i,t}
$$

ここで $\tilde{w}$ は、元の証券会社ウェイトをそのまま使うのではなく、流動性、テーマ純度、上限ウェイトを反映して調整したウェイトです。

$$
\tilde{w}_{i,k,t}
\propto
w_{i,k,t}
\cdot
LiquidityAdj_{i,t}
\cdot
Purity_{i,k,t}
$$

## 5.2 モメンタムシグナル

3、6、12か月の residual theme return を使い、1か月スキップを入れます。

$$
M_{k,t}
=
z
\left[
0.50
\frac{\sum_{\tau=t-252}^{t-21}U_{k,\tau}}
{\sigma(U_{k,t-252:t-21})}
+
0.30
\frac{\sum_{\tau=t-126}^{t-21}U_{k,\tau}}
{\sigma(U_{k,t-126:t-21})}
+
0.20
\frac{\sum_{\tau=t-63}^{t-21}U_{k,\tau}}
{\sigma(U_{k,t-63:t-21})}
\right]
$$

1か月スキップを入れる理由は、短期反転・イベント後の過剰反応・リバランスノイズを避けるためです。

補助的に、テーマ内の勝率 breadth も見ます。

$$
MomentumBreadth_{k,t}
=
\sum_{i\in B_{k,t}}
\tilde{w}_{i,k,t}
1
\left[
\sum_{\tau=t-126}^{t-21}\epsilon_{i,\tau}>0
\right]
$$

テーマ全体が上がっているのか、一部の主力銘柄だけで上がっているのかを分けます。

---

# 6. Layer 3：News / Narrative Confirmation

## 6.1 ニュース取得の基本方針

Reuters ニュースは API リミットがあるため、全ニュースを取るのではなく、**value of information が高いテーマにニュース予算を配分**します。

ニュース取得は 3 段階にします。

## Stage A：広範囲・短期間スキャン

直近 5〜10 営業日の日本株関連ニュースを広く取得します。

目的は、全テーマのうちどこにニュースフローが集中しているかを見ることです。

$$
BroadNews_{t}
=
\{\text{Japan equities related headlines over recent short window}\}
$$

テーマ別に、構成銘柄 RIC、会社名、テーマキーワード、業種語でマッピングします。

## Stage B：候補テーマ深掘り

Coherence Gate を通過し、かつ residual momentum が高いテーマだけ、30〜90日程度深掘りします。

ニュース取得予算を次のように割り当てます。

$$
Budget_{k,t}
\propto
|M_{k,t}|
\cdot
C_{k,t}
\cdot
Capacity_{k,t}
\cdot
Uncertainty_{k,t}
$$

つまり、  
「強いモメンタムがあり、統計的にまとまりがあり、運用可能容量があり、ニュース確認の価値が高いテーマ」  
から優先的にニュースを取ります。

## Stage C：イベント型クエリ

イベント型テーマでは、トピックコードやキーワードを限定します。

| テーマ | 優先イベント |
|---|---|
| 半導体 | 受注、設備投資、輸出規制、米国半導体株、生成 AI 投資 |
| AI | 生成 AI、データセンター、クラウド、GPU、ソフトウェア導入 |
| 造船 | 受注、船価、LNG船、防衛艦、為替、鋼材価格 |
| 防衛 | 防衛予算、装備品、ミサイル、防衛省契約、地政学 |
| メガバンク | 金利、日銀、増配、自社株買い、政策保有株 |
| 低 PBR | TSE 対応、ROE、資本政策、自社株買い、増配 |
| 上場子会社 | TOB、親子上場、完全子会社化、アクティビスト |
| 高配当 | 増配、減配リスク、業績修正、DOE、還元方針 |
| 未黒字企業 | 資金調達、赤字縮小、提携、希薄化、業績未達 |

---

## 6.2 ニュース特徴量

テーマ $k$ のニュース件数を、単純件数ではなく、構成ウェイト・ニュースの新規性・対象銘柄の重みで加重します。

$$
Count_{k,t}
=
\sum_{i\in B_{k,t}}
\tilde{w}_{i,k,t}
\cdot
NewsCount_{i,t}
$$

ニュースサプライズは、

$$
NS_{k,t}
=
\log(1+Count_{k,t})
-
EMA_{60}
\left[
\log(1+Count_{k,t})
\right]
$$

テーマ内のニュース breadth は、

$$
NBreadth_{k,t}
=
\sum_{i\in B_{k,t}}
\tilde{w}_{i,k,t}
1[NewsCount_{i,t}>0]
$$

センチメントは、金融文脈対応の辞書または日本語・英語金融 BERT 系モデルを使います。ただし、ニュースセンチメントはそのまま使うのではなく、イベント分類と組み合わせます。

$$
Sent_{k,t}
=
\sum_{i\in B_{k,t}}
\tilde{w}_{i,k,t}
\cdot
Sentiment_{i,t}
\cdot
Novelty_{i,t}
$$

## 6.3 イベント分類

ニュースは次のように分類します。

| 分類 | 価格インパクト |
|---|---|
| Earnings / Guidance | 業績修正、決算、コンセンサス差 |
| Orders / Capex | 受注、設備投資、工場建設 |
| Policy / Regulation | 政策、補助金、規制、輸出管理 |
| Capital Allocation | 自社株買い、増配、DOE、配当方針 |
| Governance | 取締役会、政策保有株、親子上場、英文開示 |
| M&A / TOB | 完全子会社化、買収、防衛策 |
| Financing | 増資、CB、希薄化、借入 |
| Litigation / Scandal | 不祥事、調査、訴訟 |
| Macro Link | 金利、為替、商品価格、地政学 |

最終的なニュース確認スコアは、

$$
N_{k,t}
=
z(NS_{k,t})
+
z(NBreadth_{k,t})
+
z(Sent_{k,t})
+
z(EventQuality_{k,t})
-
z(Repetition_{k,t})
$$

ここで $Repetition$ は、同じニュースの再配信・要約・続報ばかりで新規情報が少ない場合の減点です。

---

# 7. Layer 4：Governance / PBR Catalyst Overlay

## 7.1 対象テーマ

この overlay は全テーマに一律適用するのではなく、以下のテーマ群に強く適用します。

| テーマ | 主要カタリスト |
|---|---|
| 低 PBR | TSE 対応、ROE 改善、資本政策 |
| ガバナンス | CG 報告書、独立社外取締役、英文開示 |
| 高配当 | 増配、DOE、総還元性向 |
| 上場子会社 | 親子上場解消、TOB、完全子会社化 |
| メガバンク | 金利上昇、増配、自社株買い、政策保有株削減 |
| 地銀 | 再編、PBR 改善、還元強化 |
| 商社 | 資本効率、還元、事業ポートフォリオ |
| 政策保有株削減 | 保有株売却、資本効率改善 |

TSE の取り組みは、単に自社株買いや増配を求めるものではなく、資本コスト・資本収益性・市場評価を把握し、取締役会で分析し、改善計画を開示し、投資家との対話を通じて進捗を更新する継続的な対応を求めるものです。([日本取引所グループ](https://www.jpx.co.jp/english/equities/follow-up/02.html))

## 7.2 銘柄レベルの PBR 改革スコア

銘柄 $i$ について、

$$
Q_{i,t}
=
Cheapness_{i,t}
+
EfficiencyGap_{i,t}
+
BalanceSheetOption_{i,t}
+
GovernanceAction_{i,t}
+
ShareholderReturn_{i,t}
+
EventOptionality_{i,t}
-
ValueTrapRisk_{i,t}
$$

と定義します。

| 項目 | 指標 |
|---|---|
| Cheapness | PBR、PER、EV/EBITDA、セクター内相対 PBR |
| EfficiencyGap | ROE、ROIC、ROE 改善余地、ROIC-WACC |
| BalanceSheetOption | ネットキャッシュ、政策保有株、遊休資産 |
| GovernanceAction | TSE 開示済み、更新日、英文開示、CG 報告書記載 |
| ShareholderReturn | 自社株買い、増配、DOE、総還元性向 |
| EventOptionality | 親子上場、TOB 可能性、アクティビスト、事業再編 |
| ValueTrapRisk | 低 ROE 固定化、赤字、低成長、流動性不足、還元余地なし |

テーマスコアは、

$$
Q_{k,t}
=
\sum_{i\in B_{k,t}}
\tilde{w}_{i,k,t}
Q_{i,t}
$$

です。

## 7.3 低 PBR テーマで避けるべき罠

低 PBR テーマを単純ロングするのは不十分です。  
買うべきは、

$$
\text{低 PBR}
+
\text{資本効率改善余地}
+
\text{具体的カタリスト}
$$

を持つ銘柄です。

避けるべきは、

$$
\text{低 PBR}
+
\text{低 ROE 固定化}
+
\text{資本政策なし}
+
\text{低流動性}
$$

です。

したがって、低 PBR テーマは以下の 4 分類に分けます。

| 分類 | 投資判断 |
|---|---|
| 低 PBR + 改革開示 + 還元強化 | 強いロング候補 |
| 低 PBR + 改革開示なし + 政策保有株多い | イベント待ち候補 |
| 低 PBR + 低 ROE + 改善策なし | 除外またはショート候補 |
| 低 PBR + 業績悪化 + 減配リスク | 除外 |

---

# 8. Semantic Purity：テーマ純度補正

Refinitive の会社概要文と業種コードを使えるなら、テーマ純度を必ず作るべきです。

テーマ定義文を $D_k$、会社概要文を $D_i$ とします。

$$
SemanticSim_{i,k}
=
cos
\left(
Embedding(D_i),
Embedding(D_k)
\right)
$$

さらに、TRBC 業種適合度、ニュース中のテーマ語出現、複数証券会社での採用有無を加えます。

$$
P_{i,k,t}
=
0.35SemanticSim_{i,k}
+
0.25IndustryFit_{i,k}
+
0.20NewsRelevance_{i,k,t}
+
0.20BrokerConsensus_{i,k,t}
$$

この $P_{i,k,t}$ を構成ウェイトに反映します。

$$
\tilde{w}_{i,k,t}
\propto
w_{i,k,t}
\cdot
P_{i,k,t}
\cdot
LiquidityAdj_{i,t}
$$

これにより、たとえば AI テーマにおいて、実態が半導体装置、電子部品、データセンター、SaaS、ロボット、電力設備のどこにあるのかを分解できます。

実務上は、以下の 2 種類のポートフォリオを比較検証します。

| ポートフォリオ | 内容 |
|---|---|
| Broker Basket | 証券会社定義そのまま |
| Purified Basket | テーマ純度で再ウェイト |

Purified Basket が Broker Basket をコスト控除後で上回るなら、テーマ純度補正は採用価値があります。

---

# 9. Crowding Reversal Control

テーマ投資の最大リスクは、価格・ニュース・出来高が同時に過熱し、短期モメンタムが折れた後の急反落です。特に AI、半導体、防衛、造船、未黒字企業、小型成長株テーマでは重要です。

クラウディング指標を次のように作ります。

$$
H_{k,t}
=
z(TurnoverSurprise_{k,t})
+
z(VolumeSurprise_{k,t})
+
z(NewsSurprise_{k,t})
+
z(ReturnAcceleration_{k,t})
+
z(ResidualCorrJump_{k,t})
+
z(RetailAttention_{k,t})
$$

ここで、

$$
TurnoverSurprise_{k,t}
=
\log(1+Turnover_{k,t})
-
EMA_{60}
[
\log(1+Turnover_{k,t})
]
$$

$$
ReturnAcceleration_{k,t}
=
R_{k,t-21:t}
-
R_{k,t-63:t-21}
$$

減額条件は、

$$
H_{k,t}>h^*
\quad
\text{and}
\quad
R_{k,t-10:t}<0
$$

または、

$$
H_{k,t}>h^*
\quad
\text{and}
\quad
\Delta M_{k,t}<0
$$

です。

つまり、  
**ニュース・出来高・価格が過熱しているにもかかわらず、短期リターンが崩れ始めた局面**  
でウェイトを落とします。

未黒字企業や高ボラ成長株では、投資家センチメントの影響が特に大きくなりやすいです。Baker and Wurgler は、投資家センチメントが、評価が主観的で裁定しにくい銘柄群により大きな影響を与えるという仮説と実証結果を示しています。([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=464843))

---

# 10. テーマ間リード・ラグ

テーマは独立ではありません。  
たとえば、

$$
AI
\rightarrow
半導体
\rightarrow
電子部品
\rightarrow
データセンター
\rightarrow
電力設備
$$

あるいは、

$$
防衛
\rightarrow
重工
\rightarrow
造船
\rightarrow
電子部品
\rightarrow
サイバーセキュリティ
$$

という情報伝播があります。

したがって、テーマ間グラフを作ります。

$$
A_{k,l}
=
f
\left(
Overlap_{k,l},
TRBCSim_{k,l},
TextSim_{k,l},
NewsCoMention_{k,l},
LeadLagCorr_{k,l}
\right)
$$

そのうえで、テーマ $l$ のニュースやリターンがテーマ $k$ を先行するかを推定します。

$$
\hat{U}_{k,t+h}
=
\alpha_k
+
\sum_l
\beta_{k,l}U_{l,t}
+
\sum_l
\gamma_{k,l}N_{l,t}
+
\eta_k Q_{k,t}
+
e_{k,t+h}
$$

ただし、全テーマ間で VAR を組むと過学習します。  
エッジは以下の条件を満たす場合だけ許可します。

| 条件 | 内容 |
|---|---|
| 構成銘柄重複 | 同じ銘柄が複数テーマに入る |
| 業種近接 | TRBC / 東証業種が近い |
| テキスト近接 | 会社概要・テーマ説明が近い |
| ニュース共起 | 同一ニュースで複数テーマが言及される |
| 経済的因果 | 半導体 → 電子部品、金利 → 銀行など |

業種内で情報が緩やかに拡散し、大型株のリターンが小型株を先行するという lead-lag 効果は、情報拡散の遅れとして研究されています。([OUP Academic](https://academic.oup.com/rfs/article-abstract/20/4/1113/1615954))

この要素は主力シグナルではなく、**補助的なタイミング調整**として使います。

---

# 11. 最終スコア設計

実装上は、最終スコアを次のようにするのが扱いやすいです。

$$
S_{k,t}
=
\mathbb{1}
[
C_{k,t}>c^*
]
\cdot
\mathbb{1}
[
P_{k,t}>p^*
]
\cdot
\left(
0.45M_{k,t}
+
0.20N_{k,t}
+
0.20Q_{k,t}
+
0.10L_{k,t}
+
0.05V_{k,t}
\right)
-
0.25H_{k,t}
$$

| 項目 | 推奨ウェイト | 備考 |
|---|---:|---|
| Residual Momentum $M$ | 45% | 主力アルファ |
| News Confirmation $N$ | 20% | 単独売買ではなく確認 |
| Governance / PBR Catalyst $Q$ | 20% | 日本株固有アルファ |
| Lead-Lag $L$ | 10% | 補助タイミング |
| Valuation $V$ | 5% | 過熱・割安補正 |
| Crowding $H$ | 減点 | リスク管理 |

ここで、$C$ と $P$ はゲートです。  
つまり、coherence がないテーマや、テーマ純度が低いテーマは、スコア以前に対象外にします。

---

# 12. テーマ配分

## 12.1 ロング・ショート版

月次または隔週で、テーマスコアに基づき配分します。

$$
a_{k,t}
=
\frac{
\max(S_{k,t},0)
}{
\sum_j \max(S_{j,t},0)
}
$$

ロング・ショートの場合は、

$$
a^L_{k,t}
\propto
\max(S_{k,t},0)
$$

$$
a^S_{k,t}
\propto
\max(-S_{k,t},0)
$$

ただし、ショートは以下の条件を満たすテーマに限定します。

| 条件 | 理由 |
|---|---|
| 流動性が十分 | 実装可能性 |
| 借株可能 | ショートコスト管理 |
| テーマ純度が高い | 何をショートしているか明確 |
| クラウディングが剥落 | 反転狙い |
| ファクター中立化可能 | 意図しない市場・業種ショートを避ける |

現実的には、テーマショートよりも、**TOPIX・業種 ETF・先物・高相関大型株でのヘッジ**を使う方が安定しやすいです。

## 12.2 ロングオンリー版

ロングオンリー運用では、ベンチマーク対比の active weight として実装します。

$$
x_{i,t}
=
x^{bench}_{i,t}
+
\Delta x_{i,t}
$$

$$
\Delta x_{i,t}
=
\sum_k
a_{k,t}
\tilde{w}_{i,k,t}
-
HedgeAdjustment_{i,t}
$$

下位テーマを必ずショートするのではなく、アンダーウェイトにします。

---

# 13. テーマ配分から銘柄ウェイトへの変換

テーマ配分 $a_{k,t}$ を銘柄ウェイトに展開します。

$$
\alpha_{i,t}
=
\sum_k
a_{k,t}
\tilde{w}_{i,k,t}
$$

複数テーマに同じ銘柄が入るため、ここで重複が顕在化します。  
たとえば、東京エレクトロン、アドバンテスト、三菱重工、川崎重工、三菱 UFJ、三井住友、大手商社などは複数テーマに重なりやすいです。

したがって、最終的には銘柄レベルで最適化します。

$$
\max_x
\quad
\alpha_t^\top x
-
\lambda x^\top \Sigma_t x
-
TC(x-x_{t-1})
-
\phi \|B^\top x - b^*\|^2
$$

制約は以下です。

| 制約 | 内容 |
|---|---|
| Gross / Net | ロングショートなら gross、net 管理 |
| Beta | TOPIX ベータを所定範囲に |
| Sector | 業種偏り制約 |
| Style | サイズ、バリュー、モメンタム、クオリティ |
| Single Name | 個別銘柄上限 |
| Theme | 同一テーマ・類似テーマの上限 |
| Liquidity | ADV 参加率、売買代金 |
| Turnover | 月次・日次回転率 |
| Borrow | ショート銘柄の借株可否・コスト |
| Event | 決算前後、TOB、売買停止リスク |

---

# 14. バックテスト設計

この戦略で最も重要なのは、**バックテスト過学習を徹底的に避けること**です。テーマ数、期間、ニュース条件、窓幅、トピックコード、ウェイト、残差モデルを多数試すと、偶然よく見える戦略を選びやすくなります。Deflated Sharpe Ratio は、複数検定による選択バイアスと非正規リターンを補正する指標として提案されています。([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551))

## 14.1 Point-in-time 管理

以下はすべて point-in-time 化します。

| データ | 注意点 |
|---|---|
| テーマ構成 | 後から作られたテーマを過去に遡らない |
| テーマウェイト | 構成変更日を厳密に管理 |
| 会社概要 | 最新文言の過去利用を避ける |
| 業種コード | 変更履歴を管理 |
| ニュース | 配信時刻ベース |
| TSE 開示状況 | 月次更新日ベース |
| 自社株買い・増配 | 公表時刻ベース |
| 流動性 | 当日終値後に利用可能な情報のみ |

## 14.2 テーマ誕生日問題

証券会社テーマには、後から作られたテーマが多い可能性があります。  
したがって、2 種類のテストを分けます。

| テスト | 内容 |
|---|---|
| Backfilled Theme Test | テーマを過去に遡って構成したテスト |
| Live-since-launch Test | テーマ公表後のみを使ったテスト |

本採用判断では、Live-since-launch Test を重視します。

## 14.3 Out-of-sample 検証

例として、

| 期間 | 用途 |
|---|---|
| 2016-2020 | モデル設計 |
| 2021-2023 | パラメータ検証 |
| 2024-2026 | 完全 out-of-sample |

とします。

ただし、Reuters ニュース履歴の利用可能期間や LSEG 側の履歴制約により、ニュース特徴量は別枠で短期 OOS を設計します。LSEG のニュースヘッドラインサービスは、少なくとも当該ドキュメント時点で過去 15か月の履歴深度と説明されています。([LSEG Developers](https://developers.lseg.com/en/article-catalog/article/lseg-data-library-for-python--news-pagination))

## 14.4 Placebo Test

必須の placebo test は以下です。

| テスト | 目的 |
|---|---|
| Random Basket | テーマと同じサイズ・業種・流動性のランダムバスケットと比較 |
| Shuffled Theme Label | テーマ名を入れ替えて semantic/news 効果を確認 |
| Delayed News | ニュースを数日遅らせてリーケージ確認 |
| Future Constituents Ban | 将来構成銘柄の混入を検出 |
| Sector-Neutral Null | 業種効果だけで説明できないか確認 |
| Mega-cap Exclusion | 大型株数銘柄だけの効果でないか確認 |
| Cost Stress | コストを 2倍、3倍にして頑健性確認 |

---

# 15. パフォーマンス評価指標

単純な Sharpe だけでは不十分です。以下を評価します。

| 指標 | 目的 |
|---|---|
| Annualized Return | 総収益 |
| Volatility | リスク |
| Sharpe / Sortino | リスク調整後収益 |
| Information Ratio | ベンチマーク対比 |
| Max Drawdown | 損失耐性 |
| Calmar | DD 対比収益 |
| Hit Rate | 月次勝率 |
| Skew / Kurtosis | テール形状 |
| Turnover | 実装コスト |
| Capacity | 運用可能額 |
| Factor Alpha | ファクター控除後 α |
| Theme Contribution | テーマ別寄与 |
| Name Concentration | 銘柄集中度 |
| Crowding Loss | 過熱局面の損失 |
| DSR | 過学習補正後の有意性 |

特に重要なのは、

$$
r^{strategy}_t
=
\alpha
+
\beta^\top F_t
+
e_t
$$

の $\alpha$ が、コスト控除後で残るかです。

---

# 16. テーマ別の実装方針

| テーマ | 主シグナル | 補助シグナル | 注意点 |
|---|---|---|---|
| AI | Residual Momentum | News, Semantic Purity | 実態が半導体かソフトウェアか分解 |
| 半導体 | Momentum | SOX 調整、受注ニュース | 米国半導体ベータ控除が必須 |
| 防衛 | News + Momentum | 政策、受注、防衛予算 | 材料の実収益化ラグ |
| 造船 | Momentum + Orders | 船価、為替、鋼材 | 周期性と受注確認 |
| メガバンク | PBR/Governance | 金利、還元、政策保有株 | 金利ベータとバリューを分解 |
| 低 PBR | Governance Catalyst | ROE、還元、TSE 開示 | バリュートラップ除去 |
| ガバナンス | TSE / CG Event | 英文開示、取締役会 | 開示内容の質を評価 |
| 高配当 | Capital Return | 減配リスク、業績 | 単純利回り買いを避ける |
| 上場子会社 | Event Optionality | TOB、親子上場解消 | 待ち期間と流動性 |
| 未黒字企業 | Crowding Control | Sentiment | 主力ロングより過熱管理向き |

---

# 17. 推奨する運用仕様

## 17.1 リバランス

| 項目 | 推奨 |
|---|---|
| コアリバランス | 月次 |
| ニュース反映 | 日次または週次 |
| クラウディング減額 | 日次 |
| PBR/Governance overlay | 月次 |
| テーマ coherence 再推定 | 月次 |
| ファクターモデル更新 | 日次または週次 |

## 17.2 保有期間

| スリーブ | 保有期間 |
|---|---:|
| Theme Momentum | 1〜6か月 |
| News Confirmation | 数日〜3か月 |
| Governance / PBR | 3〜18か月 |
| Crowding Hedge | 数日〜1か月 |
| Lead-Lag | 数日〜1か月 |

## 17.3 リスク配分

リスク寄与ベースで、

$$
PortfolioRisk
=
60\% \cdot ThemeMomentum
+
30\% \cdot GovernancePBR
+
10\% \cdot CrowdingControl
$$

を初期値にします。

資本配分ではなく、リスク配分で管理します。AI・半導体・未黒字企業テーマは名目配分が小さくてもリスク寄与が大きくなりやすいためです。

---

# 18. 実装ロードマップ

## Phase 1：テーマデータ基盤

最初に作るべきものは、モデルではなくデータ基盤です。

| 作業 | 内容 |
|---|---|
| Theme Master | テーマ ID、名称、定義、提供会社 |
| Constituents PIT | 構成銘柄、ウェイト、開始日、終了日 |
| Security Master | TSE code、RIC、Bloomberg ticker、ISIN |
| Corporate Text | 会社概要、TRBC、業種 |
| Price Panel | 日次価格、配当込みリターン |
| Liquidity Panel | 売買代金、出来高、スプレッド proxy |
| News Panel | headline、storyId、RIC、topic、timestamp |
| TSE Reform Panel | 開示状況、更新日、英文開示、CG 報告書項目 |

## Phase 2：Coherence + Momentum MVP

最初の MVP はニュースなしで十分です。

$$
S^{MVP}_{k,t}
=
\mathbb{1}[C_{k,t}>c^*]
\cdot
M_{k,t}
$$

これで、テーマ coherence が本当にモメンタムの予測力を改善するかを検証します。

採用基準は、

| 条件 | 目安 |
|---|---|
| ランダムバスケット対比 | 有意に上回る |
| 業種中立後 α | 正 |
| コスト控除後 IR | 正 |
| DSR | 十分高い |
| Max DD | 許容範囲 |

## Phase 3：News Confirmation 追加

次に、ニュースを価格シグナルの確認に使います。

$$
S^{News}_{k,t}
=
S^{MVP}_{k,t}
+
0.20N_{k,t}
-
0.10H_{k,t}
$$

検証ポイントは、ニュース追加によって、

| 期待効果 | 確認方法 |
|---|---|
| 勝率改善 | 上位テーマの hit rate |
| DD 改善 | 過熱後の減額効果 |
| 回転率悪化なし | コスト控除後 IR |
| ニュースリーケージなし | delayed news test |

## Phase 4：Governance / PBR Overlay 追加

最後に、日本株固有 overlay を加えます。

$$
S^{Final}_{k,t}
=
S^{News}_{k,t}
+
0.20Q_{k,t}
$$

低 PBR、ガバナンス、高配当、上場子会社、メガバンクなどのテーマで、3〜18か月の寄与を検証します。

---

# 19. なぜこの手法が最良か

この手法が最良と考える理由は、単一のアイデアに依存していないにもかかわらず、各コンポーネントに明確な役割があるからです。

| 問題 | 解決策 |
|---|---|
| テーマ定義が任意 | 残差相関の coherence gate |
| テーマが業種ベータに過ぎない | 残差リターン化 |
| 後付けテーマが混じる | point-in-time と launch-date 検証 |
| テーマがニュースで動く | Reuters による narrative confirmation |
| ニュース API に制約 | 候補テーマにニュース予算を集中 |
| 日本株固有材料を取りたい | PBR/Governance overlay |
| 過熱テーマで損をする | Crowding reversal control |
| 銘柄重複で集中する | 銘柄レベル最適化 |
| バックテスト過学習 | placebo、OOS、DSR |

特に重要なのは、**coherence gate** です。  
これを入れないと、テーマ戦略は「名前のついた業種ローテーション」または「証券会社が作った話題株リストのモメンタム」になりやすいです。

---

# 20. 最終提案の要約

本戦略の正式仕様は、以下です。

$$
\boxed{
\text{Coherence-Gated Narrative Momentum with Governance Catalyst Overlay}
}
$$

運用プロセスは、

1. 証券会社テーマバスケットを point-in-time で管理する。  
2. 個別株リターンを市場・業種・スタイル・マクロで残差化する。  
3. テーマ内の平均ペアワイズ残差相関と第1固有値で、テーマの実在性を検定する。  
4. Coherence が有意なテーマだけを投資対象にする。  
5. 残差テーマリターンの 3〜12か月モメンタムを作る。  
6. Reuters ニュースで、ニュース件数、breadth、novelty、event quality、sentiment を確認する。  
7. 低 PBR・ガバナンス・高配当・上場子会社・メガバンクには、TSE 改革を背景にした資本効率改善スコアを加える。  
8. 出来高、ニュース、短期リターン加速、残差相関ジャンプでクラウディングを検出し、過熱後の反転局面で減額する。  
9. テーマ配分を銘柄レベルに展開し、リスク・流動性・ファクター・重複制約付きで最適化する。  
10. ランダムバスケット、業種中立、ローンチ後検証、ニュース遅延テスト、Deflated Sharpe Ratio で過学習を抑制する。

最も小さく始めるなら、まずは以下の MVP です。

$$
\boxed{
S^{MVP}_{k,t}
=
\mathbb{1}
[
C_{k,t}>c^*
]
\cdot
M_{k,t}
}
$$

その後、

$$
\boxed{
S^{Final}_{k,t}
=
\mathbb{1}
[
C_{k,t}>c^*
]
\mathbb{1}
[
P_{k,t}>p^*
]
\left(
0.45M_{k,t}
+
0.20N_{k,t}
+
0.20Q_{k,t}
+
0.10L_{k,t}
+
0.05V_{k,t}
\right)
-
0.25H_{k,t}
}
$$

へ拡張するのが、研究リスクと実装リスクのバランスが最も良いです。

---

**Sources:**

- [Thematic Investing: A Risk-based Perspective by Emmanuel Candes, Trevor Hastie, Ked Hogan, Ronald Kahn, Robert Luo, Asher Spector :: SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5336504)
- [EconPapers: Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency](https://econpapers.repec.org/RePEc%3Abla%3Ajfinan%3Av%3A48%3Ay%3A1993%3Ai%3A1%3Ap%3A65-91)
- [Do Industries Explain Momentum?](https://www.aqr.com/Insights/Research/Journal-Article/Do-Industries-Explain-Momentum)
- [Action to Implement Management that is Conscious of Cost of Capital and Stock Price (Prime and Standard Markets) | Japan Exchange Group](https://www.jpx.co.jp/english/equities/follow-up/02.html)
- [LSEG Data Library for Python: News Pagination | Devportal](https://developers.lseg.com/en/article-catalog/article/lseg-data-library-for-python--news-pagination)
- [Common risk factors in the returns on stocks and bonds](https://www.sciencedirect.com/science/article/pii/0304405X93900235?utm_source=chatgpt.com)
- [](https://academic.oup.com/rfs/article-abstract/20/4/1113/1615954)

## Response:
2026/5/11 0:35:39

まず価格CSVだけで動くMVPを実装し、残差モメンタム、クラウディング抑制、月次リバランスまで走らせます。追加データは任意入力として完全版で使える設計にします。

## Response:
2026/5/11 0:36:22

MVPはコスト控除後バックテストまで含め、完全版では構成銘柄と個別株リターンがあればcoherence gateを有効化します。価格CSVだけでは純度・PBR・ニュース確認は未計算です。

## Response:
2026/5/11 0:39:06

> **Creating a notebook and final docs**
>
> I’m thinking it could be useful to also create a notebook alongside the Python files and README. But I’ll keep the final product compact, summarizing usage, data requirements, and providing essential code snippets. I’ll link files and mention dependencies like pandas and numpy. I'll ensure the final version makes sense without needing citations.
>
> **Considering optimization and design for production-level performance**
>
> I’m spotting possible issues, like turnover costs being charged early and `score_gated` misbeh
>
> **Improving residualization efficiency**
>
> The current approach uses 0 stocks over 2500 days, which is quite heavy. We don’t need full residualization on a daily basis, but we can residualize returns at rebalance dates using a cross-sectional risk model. To speed it up, I’ll precompute betas for assets across dates and handle missing data carefully, possibly treating it as zeros. I’ll aim for a vectorized, masked approach for efficiency.
>
> **Simplifying residualization with rolling covariances**
>
> To simplify residualization, I’m considering using cross-sectional factor exposures but the factors' returns matter too. I can try a "pooled rolling residualize" using rolling covariances and betas. For multiple factors, I'll compute covariance matrices at each date. I’ll also fill missing values carefully, using masks when necessary. For liquid assets, I’ll focus on non-missing data.
>
> **Updating CLI for residualization control**
>
> It seems the CLI doesn’t currently allow disabling residualization for stocks. I’ll add flags like `--no_residualize_themes` and `--no_residualize_stocks`, which will allow for residual returns via the stock CSV. I’ll also support precomputed residuals with `--stock_input_kind return` and update the README to reflect these changes.
>
> **Updating CLI arguments for stock residualization**
>
>
> **Updating README**
>
> I need to update the README. It’s important to make sure all recent changes, like CLI flag additions and options like `--no_residualize_stocks` or `--stock_input_kind return`, are fully documented. This will help users understand how to use these features effectively.
>
> **Patching README with additional instructions**
>
>
> **Deciding on file inclusion**
>
> I’m wondering whether to create a zip file or just link individual files. Should I include a `sample_theme_prices.csv`? It might be helpful, but I don’t think it’s necessary. I’ll focus on linking the Python file and the README. I need to check the syntax after patching the file.
>
> **Running theme strategy analysis with CSV input**
>
>
> **Considering a zip file**
>
> Before finalizing, I’m thinking maybe I should create a zip file for convenience. It could help organize everything. I could just use `zip` to bundle the files, making things more streamlined instead of linking them individually. Let’s see if that adds value before the final version.
>
> **Creating a zip file of strategy package**
>
>
> Thought for 9m 4s

## Response:
2026/5/11 0:44:43

実装ファイルを作成しました。

- [Python実装: theme_basket_strategy.py](sandbox:/mnt/data/theme_basket_strategy.py)
- [README: theme_basket_strategy_README_ja.md](sandbox:/mnt/data/theme_basket_strategy_README_ja.md)
- [一式ZIP](sandbox:/mnt/data/theme_basket_strategy_package.zip)

## 実装内容

この実装は、以下の4段階で動きます。

| レベル | 必要データ | 実装される内容 |
|---|---|---|
| MVP | テーマ価格CSVのみ | テーマ・モメンタム、過熱減額、月次リバランス、バックテスト |
| Factor-adjusted | テーマ価格CSV + ファクターCSV | TOPIX・スタイル等で残差化したテーマ・モメンタム |
| Coherence-gated | 上記 + 構成銘柄 + 個別株価格/リターン | テーマ内平均ペアワイズ残差相関、固有値、effective N による coherence gate |
| Overlay版 | 上記 + ニュース/ガバナンス特徴量 | Reuters ニュース確認、PBR/ガバナンス・カタリスト、回転率ベースのcrowding control |

## 最小実行例

テーマバスケット価格CSVだけで走らせる場合です。

```bash
python theme_basket_strategy.py \
  --theme_csv theme_prices.csv \
  --theme_input_kind price \
  --mode long_only \
  --top_n 5 \
  --output_dir output_mvp \
  --disable_coherence_gate \
  --disable_news \
  --disable_governance
```

ロング・ショート版は以下です。

```bash
python theme_basket_strategy.py \
  --theme_csv theme_prices.csv \
  --theme_input_kind price \
  --mode long_short \
  --top_n 5 \
  --bottom_n 5 \
  --output_dir output_ls \
  --disable_coherence_gate \
  --disable_news \
  --disable_governance
```

## 推奨実行例

ファクター調整付きのテーマ残差モメンタムです。

```bash
python theme_basket_strategy.py \
  --theme_csv theme_prices.csv \
  --factor_csv factor_returns.csv \
  --theme_input_kind price \
  --mode long_only \
  --top_n 5 \
  --output_dir output_factor_adjusted \
  --disable_coherence_gate
```

完全版は以下です。

```bash
python theme_basket_strategy.py \
  --theme_csv theme_prices.csv \
  --factor_csv factor_returns.csv \
  --constituents_csv constituents.csv \
  --stock_csv stock_prices.csv \
  --theme_input_kind price \
  --stock_input_kind price \
  --mode long_only \
  --top_n 5 \
  --output_dir output_full
```

## テーマ価格CSVの想定形式

ワイド形式であればそのまま読めます。

```text
date,AI,Semiconductor,Defense,LowPBR,Governance
2021-01-04,100.0,100.0,100.0,100.0,100.0
2021-01-05,101.2,99.8,100.5,100.3,100.1
```

ロング形式も対応しています。

```text
date,theme,price
2021-01-04,AI,100.0
2021-01-04,Semiconductor,100.0
```

リターンCSVの場合は、`--theme_input_kind return` を指定してください。

## 追加で必要なデータ

テーマ価格CSVだけでもMVPは動きます。ただし、提案した「最良手法」をきちんと実装するには、以下が必要です。

| 優先度 | データ | 用途 |
|---:|---|---|
| 必須 | テーマバスケット価格/リターン | テーマ・モメンタム |
| 強く推奨 | TOPIX、業種、サイズ、バリュー、モメンタム等のファクターリターン | 残差テーマ・モメンタム |
| 強く推奨 | テーマ構成銘柄、ウェイト、有効日 | point-in-time のテーマ定義 |
| 強く推奨 | 構成銘柄の日次価格/リターン | coherence gate |
| 推奨 | 会社概要文、TRBC/業種コード | semantic purity 作成 |
| 推奨 | Reuters/LSEG ニュース特徴量 | narrative confirmation |
| 推奨 | TSE対応状況、自社株買い、増配、DOE、親子上場等 | PBR/Governance overlay |
| 推奨 | 出来高、売買代金、回転率 | crowding control、容量・コスト推定 |
| 推奨 | セキュリティマスター | Bloomberg ticker、RIC、TSE code、ISIN の紐付け |

## Coherence gate 用の構成銘柄CSV

```text
date,theme,ticker,weight,purity,liquidity_adj
2023-01-31,AI,6758.T,0.08,0.75,1.00
2023-01-31,AI,6501.T,0.07,0.60,1.00
2023-01-31,Semiconductor,8035.T,0.12,0.95,1.00
```

必須列は `theme`, `ticker`, `weight` です。  
`date` がない場合は静的構成として扱います。`purity` と `liquidity_adj` は任意です。

## 出力

`output_dir` に以下が保存されます。

```text
theme_returns.csv
theme_residual_returns.csv
momentum_score.csv
coherence_apc.csv
coherence_eigenshare.csv
coherence_effective_n.csv
coherence_gate.csv
news_score.csv
governance_score.csv
crowding_score.csv
final_score.csv
final_score_gated.csv
theme_weights_rebalance.csv
theme_weights_daily.csv
strategy_returns.csv
backtest_details.csv
metrics.csv
config.json
```

## 注意点

coherence gate は、テーマ価格CSVだけでは計算できません。構成銘柄と個別株リターンが必要です。大量の個別株で rolling OLS が重い場合は、個別株の残差リターンを外部で前計算して、以下のように渡してください。

```bash
python theme_basket_strategy.py \
  --theme_csv theme_prices.csv \
  --factor_csv factor_returns.csv \
  --constituents_csv constituents.csv \
  --stock_csv stock_residual_returns.csv \
  --stock_input_kind return \
  --no_residualize_stocks \
  --output_dir output_full_fast
```

この実装は研究・検証用のベースです。実運用に載せる場合は、個別銘柄ウェイトへの展開、借株制約、銘柄別ADV制約、ファクター中立化、銘柄重複制御を別途 optimizer に接続するのが次の工程です。

## Response:
2026/5/11 0:56:51

Jupyter Notebook版を作成します。既存Python実装を呼び出し、MVP、ファクター調整、coherence gate、overlay版を独立セルに分けます。

## Response:
2026/5/11 0:57:15

ノートブック単体ではなく、再利用しやすいヘルパーモジュールも同梱します。現在、ノートブックの実行検証まで含めて整えています。

## Response:
2026/5/11 1:01:01

> **Building out core components**
>
> I should focus on implementing the core features like `prices_to_returns`, `rolling_residualize`, `zscore`, `rolling_momentum`, and `coherence features`. The `Strategy` class will compute the results and save them, but a concise version may not need charts. I'll ensure there are no syntax errors before testing the notebook with sample data.
>
> **Implementing theme basket strategy and backtest**
>
>
> **Creating sample data for testing**
>
> It seems like the previous sample data is no longer available. I’ll need to recreate it and then run the notebook to test things out. Once the sample data is ready, I can execute the notebook to ensure everything functions properly. Hopefully, that will help verify everything works as expected.
>
> **Generating sample data and executing notebook**
>
>
> **Fixing string formatting issue in notebook**
>
> In the generated notebook, the `print("\nOptional files")` is incorrectly interpreted, as `\n` becomes an actual newline in the string. This happens because the string in the `create_nb.py` script isn't using raw strings. To fix it, I can patch the notebook to use escaped `\\n` or use raw strings in the helper code.
>
> **Editing `create_nb.py` to fix string formatting**
>
> Since the outer file uses raw strings, Chinese characters and docstrings should be fine. I can replace all instances of `new_code_cell('''` with `new_code_cell(r'''` for consistency. Markdown content isn't problematic. I'll edit `create_nb.py` by using `sed` to replace those strings and then regenerate the notebook.
>
> **Fixing newline handling in notebook code cells**
>
>
> **Re-executing due to odd output**
>
> The printed condition looks strange, but the source code itself seems fine. I should try executing it again to see if that clears things up or if the issue persists. Let's give it another go and see what happens.
>
> **Re-executing Jupyter notebook with error handling**
>
>
> **Considering package update and README**
>
> I need to update the package zip with the notebook and `.py` file, maybe even a README. Not sure if the README is absolutely necessary—though it's probably a good idea to include it. The current directory doesn't have one. It might be useful to list this out before proceeding.
>
> **Listing files in /mnt/data**
>
>
> **Considering README and package creation**
>
> It seems like there are .json files generated from running the notebook, possibly due to matplotlib exports. It’s in the `/mnt/data` folder, but that’s not really important. I should create a README, though—not sure if a full one is needed. Maybe just a small README for the notebook and include it in the package with the notebook and .py file.
>
> **Creating README and packaging notebook files**
>
>
> Thought for 13m 55s

## Response:
2026/5/11 1:10:46

作成しました。Notebookでは、各実行レベルを個別セルに分けています。

- [Jupyter Notebook本体](sandbox:/mnt/data/theme_basket_strategy_notebook.ipynb)
- [Notebook用ヘルパーモジュール](sandbox:/mnt/data/theme_basket_strategy.py)
- [README](sandbox:/mnt/data/theme_basket_strategy_notebook_README_ja.md)
- [一式ZIP](sandbox:/mnt/data/theme_basket_strategy_notebook_package.zip)

Notebookの構成は以下です。

| セル | 内容 |
|---|---|
| 0 | imports |
| 1 | CSVパス設定 |
| 2 | サンプルデータ生成 |
| 3 | 共通データロード |
| Level 1 | MVP：テーマ価格時系列のみ |
| Level 2 | Factor-adjusted：テーマ価格 + ファクターリターン |
| Level 3 | Coherence-gated：構成銘柄 + 個別株価格/リターン |
| Level 4 | Full overlay：ニュース、ガバナンス/PBR、回転率crowding |
| 5 | 各レベルのパフォーマンス比較 |
| 6 | NAVプロット |
| 7 | 最終ウェイト・シグナル確認 |

初回は `USE_SAMPLE_DATA = True` のまま上から実行すれば、サンプルデータで全レベルが動きます。実データで使う場合は、Notebookの「1. パス設定」セルで `USE_SAMPLE_DATA = False` にし、保有しているテーマバスケットCSVのパスを指定してください。

注意点として、Notebookは `theme_basket_strategy.py` を読み込む形式です。Notebookと `.py` ファイルは同じフォルダに置いて実行してください。ZIPには両方入っています。

## Response:
2026/5/11 1:12:52

ファクターは既製指数で作る実装可能プロキシと、個別株から内製する横断スタイルファクターを分け、まずBloomberg中心の最小構成から始めるのが実務的です。

## Response:
2026/5/11 1:12:54

> **Searching sources for factor returns and indices**
>
> [TOPIX (TPX) | Japan Exchange Group](https://www.jpx.co.jp/english/markets/indices/topix/)
> [Kenneth R. French - Description of Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/details_japanese.html)
> [Bloomberg Equity Indices | Bloomberg Professional Services](https://www.bloomberg.com/professional/products/indices/equity/)
> [【JPX総研】TOPIXを区分して見る（業種編）](https://money-bu-jpx.com/news/article059375/)
> [CARF Working Paper](https://www.carf.e.u-tokyo.ac.jp/pdf/workingpaper/fseries/212.pdf)
> [Bloomberg Equity Indices](https://assets.bbhub.io/professional/sites/27/Bloomberg-PAB-Japan-Index-Fact-Sheet.pdf)
> [iShares Core TOPIX ETF - BlackRock](https://www.blackrock.com/jp/individual-en/en/products/279438/ishares-core-topix-etf)
> [33-sector code and name](https://jpx-jquants.com/en/spec/eq-master/sector33code)
> [A six‐factor asset pricing model: The Japanese evidence](https://onlinelibrary.wiley.com/doi/10.1002/cfp2.1109)
> [japan stock index: Guide to Japan's benchmark equity ...](https://www.bitget.com/wiki/japan-stock-index)
> [Stefano Marmi - Data Library](https://homepage.sns.it/marmi/Data_Library.html)
> [Japan Equity Monthly Review](https://www.nam.co.jp/english/news/npdf/jeo201506.pdf)
> [The Impact of Japanese ETF Providers and Foreign ...](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2024-Lisbon/papers/ImpactOfJapaneseETFsAndForeignPIIsOnCOE.pdf)
> [Japan's Nikkei jumps 6%, rebounds from rout on market recovery hopes](https://www.reuters.com/markets/asia/japans-nikkei-jumps-6-rebounds-1-12-year-low-us-tech-boost-2025-04-08/)
> [Japanese stocks surge to year-end record](https://www.ft.com/content/1eef8dfd-34e9-4630-ad6a-6ec6823dae3a)
>
> **Providing sources for financial data**
>
> I need to make sure I'm offering the right financial information from reputable sources. Since the user has access to Bloomberg, I can recommend using Bloomberg and JPX data directly. I'll mention key indices like the TOPIX, which offers both price and total return versions. I'll also provide specific details and categories with citations where necessary. I'll cross-check everything for accuracy.
>
> **Browsing for JPX TOPIX and related indices information**
>
> [TOPIX (TPX) | Japan Exchange Group](https://www.jpx.co.jp/english/markets/indices/topix/)
> [JPX-Nikkei Index 400](https://indexes.nikkei.co.jp/en/nkave/index/profile?idx=jpxnk400)
> [Stock price index - historical - TOPIX Growth － Monthly Chart](https://quote.jpx.co.jp/jpxhp/main/index.aspx?F=e_hist_index&qcode=212)
> [External Evaluations and Index Inclusion](https://www.nipponpaint-holdings.com/en/ir/evaluation/)
> [TOPIX Growth Index Today (TOPXG)](https://www.investing.com/indices/topix-growth)
> [QUICK Data Factory – Japanese Alternative ...](https://corporate.quick.co.jp/data-factory/en/)
> [Tokyo Stock Exchange Index Guidebook](https://www.wisdomtree.eu/-/media/eu-media-files/other-documents/index/boost/topix-index-methodology.pdf?sc_lang=en-gb)
> [Evaluation | SUSTAINABILITY | DENTSU SOKEN](https://www.dentsusoken.com/english/sustainability/evaluation.html)
> [Governance through shame and aspiration: Index creation ...](https://www.sciencedirect.com/science/article/abs/pii/S0304405X19301783)
> [The Effects of the Bank of Japan's ETF Purchases on Risk ...](https://www.boj.or.jp/en/research/wps_rev/wps_2021/data/wp21e03.pdf)
> [https://site2.sbisec.co.jp/ETGate/?_ControlID=WPLE...](https://site2.sbisec.co.jp/ETGate/?_ActionID=DefaultAID&_ControlID=WPLETmgR001Control&_DataStoreID=DSWPLETmgR001Control&_PageID=WPLETmgR001Mdtl20&burl=iris_indexDetail&cat1=market&cat2=index&dir=tl1-idxdtl%7Ctl2-.TOPX%7Ctl5-jpn&file=index.html&getFlg=on)
> [iShares JPX-Nikkei 400 ETF - BlackRock](https://www.blackrock.com/jp/individual-en/en/products/270795/ishares-jpx-nikkei-400-etf)
> [What is Growth Strategy and Future Prospects of Japan ...](https://matrixbcg.com/blogs/growth-strategy/jpx)
> [Japanese stocks surge to year-end record](https://www.ft.com/content/1eef8dfd-34e9-4630-ad6a-6ec6823dae3a)
> [Japan's Topix tops 3,000 for first time on tariff clarity; SoftBank soars](https://www.reuters.com/markets/asia/japans-topix-tops-3000-first-time-tariff-clarity-softbank-soars-2025-08-08/)
>
> **Providing factor data and sources**
>
> I should provide citation sources for each factor set to give a complete, practical answer. For example, using Bloomberg tickers or specifying exact codes like "PX_LAST" for daily returns might be useful, but I'll stick to general terms for flexibility. I'll include a sample factor set with specific indices like TOPIX and JPX-Nikkei 400 for various factors like size, value, and momentum.
>
> Thought for 2m 56s

## Response:
2026/5/11 1:15:49

結論として、最初は **JPX/TOPIX 系の指数リターンを Bloomberg から取得してファクター化**するのが一番実務的です。Kenneth French の日本ファクターは研究用ベンチマークとして使えますが、本番戦略では、ユニバース・配当込み・時点管理・日本株テーマとの整合性を考えると、**自前で日本株ファクターを構成する**か、**JPX/MSCI/S&P/FTSE の日本株ファクター指数を Bloomberg 経由で取る**のがよいです。

---

## 1. まず取得すべき最小ファクター

Notebook の `factor_returns.csv` には、まず以下を入れてください。

```text
date,MKT,SIZE,VALUE,MOMENTUM,LOWVOL,QUALITY,YIELD,USDJPY,JGB10Y,SOX
2024-01-04,0.0031,-0.0012,0.0020,0.0015,-0.0004,0.0008,0.0011,0.0040,0.0003,0.0120
```

最小構成は以下です。

| ファクター | 推奨定義 | 取得元 |
|---|---|---|
| `MKT` | TOPIX Total Return | Bloomberg / JPX |
| `SIZE` | TOPIX Small TR - TOPIX 100 TR、または Small - Large | Bloomberg / JPX |
| `VALUE` | TOPIX Value TR - TOPIX Growth TR | Bloomberg / JPX |
| `SECTOR_*` | TOPIX-17 または TOPIX 33業種 TR - TOPIX TR | Bloomberg / JPX |
| `MOMENTUM` | 自前の 12か月-1か月モメンタム long-short、または MSCI/S&P Momentum Japan - 親指数 | 自前 / MSCI / S&P |
| `LOWVOL` | MSCI Japan Minimum Volatility TR - MSCI Japan TR、または S&P Japan Low Vol - 親指数 | MSCI / S&P / Bloomberg |
| `QUALITY` | JPX-Nikkei 400 TR - TOPIX TR、JPX Prime 150 TR - TOPIX TR、または自前クオリティ | JPX / Nikkei / Bloomberg |
| `YIELD` | 高配当指数 TR - TOPIX TR、または自前配当利回り long-short | Bloomberg / 自前 |
| `USDJPY` | USDJPY リターン、または変化率 | Bloomberg |
| `JGB10Y` | 10年国債利回り変化 | Bloomberg |
| `SOX` | Philadelphia Semiconductor Index 等のリターン | Bloomberg |

このうち、**必須は `MKT`, `SIZE`, `VALUE`, `SECTOR`** です。  
`MOMENTUM`, `LOWVOL`, `QUALITY`, `YIELD` は推奨です。  
`USDJPY`, `JGB10Y`, `SOX` はテーマ依存の補助ファクターです。

---

## 2. Bloomberg から取るべき JPX/TOPIX 系指数

### 2.1 市場ファクター

まず `MKT` は TOPIX Total Return を使ってください。価格指数ではなく、**配当込み Total Return** を推奨します。

TOPIX は日本株市場全体を代表する free-float adjusted market capitalization weighted index として JPX が説明しており、日本株テーマの市場ベータ控除に最も自然です。([日本取引所グループ](https://www.jpx.co.jp/english/markets/indices/topix/?utm_source=chatgpt.com))

```text
MKT = TOPIX Total Return の日次リターン
```

Bloomberg では TOPIX 価格指数の代表コードは `TPX Index` として確認できます。Total Return 版は Bloomberg 端末または JPX factsheet の vendor code で確認してください。([ブルームバーグ](https://www.bloomberg.com/quote/TPX%3AIND?utm_source=chatgpt.com))

---

### 2.2 サイズファクター

`SIZE` は、TOPIX の規模別指数を使って作るのが簡単です。JPX は TOPIX Core30、Large70、TOPIX100、Mid400、TOPIX500、TOPIX Small、TOPIX1000、TOPIX Small500、TOPIX Micro Cap などの規模別指数を算出しています。([日本取引所グループ](https://www.jpx.co.jp/english/markets/indices/line-up/files/e_cal2_12_size.pdf))

推奨定義は以下です。

```text
SIZE = return(TOPIX Small Total Return) - return(TOPIX 100 Total Return)
```

または、

```text
SIZE = return(TOPIX Small Total Return) - return(TOPIX Core30 + Large70 Total Return)
```

テーマバスケットには中小型のテーマ株が多く混ざるので、サイズファクターは必須です。特に未黒字企業、AI周辺、防衛小型株、造船周辺、上場子会社テーマでは、サイズ効果を除かないとテーマアルファを過大評価しやすいです。

---

### 2.3 バリュー/グロースファクター

`VALUE` は TOPIX Value と TOPIX Growth の差で作ります。

```text
VALUE = return(TOPIX Value Total Return) - return(TOPIX Growth Total Return)
```

JPX の TOPIX Style Index Series は、TOPIX Value、TOPIX Growth、TOPIX500 Value/Growth、TOPIX Small Value/Growth などを含み、構成銘柄は consolidated PBR などに基づいて分類されます。また、価格指数、Total Return Index、Net Total Return Index が計算されています。([日本取引所グループ](https://www.jpx.co.jp/english/markets/indices/topix/tvdivq00000030ne-att/e_cal2_14_style_rev.pdf))

低PBR、高配当、銀行、商社、保険、ガバナンス系テーマでは、`VALUE` を入れないとテーマ固有の寄与とバリューファクター寄与が混ざります。

---

### 2.4 業種ファクター

テーマ戦略では、業種ファクターが最重要です。  
TOPIX-17 または TOPIX 33業種を使ってください。

JPX は TOPIX Sector Indices として TOPIX 構成銘柄を33業種に分類した指数、および33業種を17分類に再編した TOPIX-17 Series を算出しています。([日本取引所グループ](https://www.jpx.co.jp/english/markets/indices/factsheets/index.html))

推奨は、まず TOPIX-17 です。

```text
SECTOR_BANKS       = return(TOPIX-17 Banks TR) - return(TOPIX TR)
SECTOR_MACHINERY   = return(TOPIX-17 Machinery TR) - return(TOPIX TR)
SECTOR_ELEC_PREC   = return(TOPIX-17 Electric Appliances & Precision Instruments TR) - return(TOPIX TR)
...
```

TOPIX 33業種を全部入れてもよいですが、テーマ数や観測期間が短い場合は、回帰が不安定になります。Notebook の実装は ridge regression を使っているのである程度耐えますが、最初は **TOPIX-17 の excess return** で十分です。

---

## 3. スタイルファクターの取得候補

### 3.1 Momentum

選択肢は2つです。

第一候補は、**自前で日本株モメンタムファクターを作る**ことです。

```text
MOMENTUM = 過去12か月 - 直近1か月リターン上位群
         - 過去12か月 - 直近1か月リターン下位群
```

できれば業種中立・サイズ中立で作ります。  
テーマバスケット自体が momentum 戦略なので、テーマの residual momentum が単なる一般モメンタムではないかを確認するために、このファクターは重要です。

外部指数を使うなら、S&P Momentum Japan LargeMidCap などがあります。同指数は、日本市場で相対パフォーマンスの持続性を示す銘柄を測る指数として S&P が説明しています。([S&P Global](https://www.spglobal.com/spdji/en/indices/dividends-factors/sp-momentum-japan-largemidcap-index/))

```text
MOMENTUM = return(S&P Momentum Japan LargeMidCap TR)
         - return(S&P Japan LargeMidCap Parent TR)
```

MSCI Japan Momentum Index が Bloomberg/Refinitiv で使えるなら、それでも構いません。

---

### 3.2 Low Volatility

低ボラは、MSCI Japan Minimum Volatility、S&P Japan 500 Low Volatility などを使えます。

MSCI Japan Minimum Volatility Index は、MSCI Japan Index を親指数として、日本株大型・中型株ユニバースに minimum variance strategy を適用する指数です。([MSCI](https://www.msci.com/indexes/index/700488?utm_source=chatgpt.com))

```text
LOWVOL = return(MSCI Japan Minimum Volatility TR)
       - return(MSCI Japan TR)
```

または、

```text
LOWVOL = return(S&P Japan 500 Low Volatility TR)
       - return(S&P Japan 500 TR)
```

S&P Japan 500 Low Volatility Index は、S&P Japan 500 の中でボラティリティが低い100銘柄のパフォーマンスを測る指数です。([S&P Global](https://www.spglobal.com/spdji/en/indices/dividends-factors/sp-japan-500-low-volatility-index/?utm_source=chatgpt.com))

---

### 3.3 Quality / Governance

`QUALITY` は、実務上は3通りあります。

一つ目は、JPX-Nikkei 400 を使う方法です。  
JPX-Nikkei 400 は、資本の効率的活用や投資者を意識した経営など、グローバル投資基準を満たす魅力ある会社で構成される指数として説明されています。([日本取引所グループ](https://www.jpx.co.jp/english/markets/indices/jpx-nikkei400/?utm_source=chatgpt.com))

```text
QUALITY = return(JPX-Nikkei 400 TR) - return(TOPIX TR)
```

二つ目は、JPX Prime 150 を使う方法です。  
JPX Prime 150 は、価値創造が推定される日本企業を見える化する指数で、ROE が株主資本コストを上回るか、PBR が1倍を上回るかといった観点を用いています。Total Return Index も利用可能です。([日本取引所グループ](https://www.jpx.co.jp/english/markets/indices/jpx-prime150/))

```text
QUALITY_OR_VALUE_CREATION = return(JPX Prime 150 TR) - return(TOPIX TR)
```

三つ目は、自前で ROE、ROIC、営業利益率、財務レバレッジ、利益安定性から long-short を作る方法です。  
本格実装ではこれが最も望ましいです。

---

### 3.4 Yield

`YIELD` は、高配当指数が Bloomberg で取れるならそれを使います。

```text
YIELD = return(Japan High Dividend TR) - return(TOPIX TR)
```

ただし、高配当テーマはバリュー、銀行、保険、商社、低PBRと重複しやすいので、`VALUE` と `SECTOR_BANKS` を同時に入れたうえで、`YIELD` の寄与を見るべきです。

自前で作るなら、

```text
YIELD = 配当利回り上位群 - 配当利回り下位群
```

よりも、

```text
YIELD = 総還元利回り上位群 - 総還元利回り下位群
```

の方が日本株では実務的です。自社株買いも入るためです。

---

## 4. 外部ベンダーの factor index を使う場合

Bloomberg や Refinitiv でライセンスがあるなら、以下の外部指数も候補です。

| ベンダー | 使える指数例 | 用途 |
|---|---|---|
| MSCI | MSCI Japan Value, Momentum, Quality, Minimum Volatility, High Dividend Yield | スタイルファクター |
| FTSE Russell | FTSE Japan Comprehensive Factor Index 等 | 複合ファクター |
| S&P DJI | S&P Momentum Japan LargeMidCap, S&P Japan Low Volatility | Momentum / LowVol |
| JPX | TOPIX Value/Growth, Size indices, Sector indices, JPX Prime150, JPX-Nikkei400 | 日本株市場・業種・サイズ・PBR/Quality proxy |

FTSE Japan Comprehensive Factor Index は、Quality、Value、Momentum、Low Volatility、Size の5ファクターへのエクスポージャーを捉える指数として説明されています。([FTSE Russell Research Portal](https://research.ftserussell.com/Analytics/Factsheets/Home/DownloadSingleIssue?IsManual=false&issueName=FJACPF&utm_source=chatgpt.com))

ただし、外部ファクター指数は多くの場合 **long-only factor tilt index** です。純粋な long-short factor ではありません。したがって、回帰に入れるときは基本的に、

```text
factor_excess = return(factor_index_total_return) - return(parent_index_total_return)
```

として使ってください。

---

## 5. 無料の研究用データ：Kenneth French Data Library

研究用・検証用なら Kenneth French Data Library の Japanese factors が使えます。French のページでは、Japanese factors and portfolios は日本のみを含むと説明されています。([タックビジネススクール](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/details_japanese.html))

取得できる代表的なものは、Fama-French 型の以下です。

```text
Mkt-RF
SMB
HML
RMW
CMA
MOM
RF
```

使い方は以下です。

```text
theme_excess_return = theme_return - RF

theme_excess_return
  ~ Mkt-RF + SMB + HML + RMW + CMA + MOM
```

ただし、私はこれを本番用の第一候補にはしません。理由は、あなたのテーマバスケットの実際のユニバース、時価総額範囲、流動性制約、TSE改革テーマ、Bloomberg/Refinitive上の point-in-time 構成と必ずしも一致しないからです。

使いどころは以下です。

| 用途 | 適性 |
|---|---|
| 学術的な sanity check | 高い |
| 初期検証 | 高い |
| 本番リスクモデル | 中程度 |
| テーマ構成銘柄の residualization | 自前ファクターの方が望ましい |

---

## 6. 最終的に最も望ましい構成：自前ファクター

本番では、Bloomberg/Refinitive から個別株データを取って、**自前で日本株 factor-mimicking portfolio** を作るのが最良です。

### 6.1 ユニバース

```text
TSE Prime + Standard のうち、
流動性、時価総額、売買停止、上場後期間を満たす銘柄
```

推奨条件：

```text
時価総額 >= 300億円
過去60日平均売買代金 >= 1億円
上場後6か月以上
金融商品、REIT、ETF、優先株等は除外
```

テーマバスケットの中小型株を評価したい場合は、時価総額条件を緩めてもよいですが、ファクター側は安定性を優先してください。

### 6.2 自前ファクター定義

| ファクター | 定義例 |
|---|---|
| `MKT` | TOPIX TR |
| `SIZE` | 小型上位 - 大型上位 |
| `VALUE` | 低PBR/低PER/高BPR 上位 - 高PBR/高PER 下位 |
| `MOMENTUM` | 過去12か月-直近1か月リターン上位 - 下位 |
| `QUALITY` | ROE、ROIC、営業利益率、利益安定性上位 - 下位 |
| `LOWVOL` | 低β/低ボラ上位 - 高β/高ボラ下位 |
| `YIELD` | 配当利回り + 自社株買い利回り上位 - 下位 |
| `INVESTMENT` | 総資産成長率低位 - 高位 |
| `PBR_REFORM` | 低PBR + 改革開示/還元強化 - 低PBR value trap |

### 6.3 構成方法

月次でリバランスし、日次リターンを出します。

```text
1. 各月末に特徴量を計算
2. 業種内で z-score 化
3. 時価総額または売買代金で最低流動性を制限
4. 上位20%をロング、下位20%をショート
5. 各レッグを等ウェイトまたはボラ逆数ウェイト
6. 業種中立、サイズ中立に近づける
7. 翌月の日次 long-short return を factor return とする
```

ファクターリターンCSVは次のような形になります。

```text
date,MKT,SIZE,VALUE,MOMENTUM,QUALITY,LOWVOL,YIELD,PBR_REFORM
2024-01-04,0.0031,-0.0010,0.0022,0.0014,0.0003,-0.0006,0.0011,0.0008
2024-01-05,-0.0020,0.0004,-0.0015,0.0002,0.0001,0.0007,-0.0003,0.0010
```

---

## 7. どれを採用すべきか

私は以下の順で推奨します。

## Phase 1：すぐ動かす

Bloomberg から以下を取得してください。

```text
TOPIX TR
TOPIX Small TR
TOPIX 100 TR
TOPIX Value TR
TOPIX Growth TR
TOPIX-17 Sector TR
USDJPY
JGB10Y
SOX
```

作るファクターは以下です。

```text
MKT        = TOPIX_TR
SIZE       = TOPIX_Small_TR - TOPIX100_TR
VALUE      = TOPIX_Value_TR - TOPIX_Growth_TR
SECTOR_x   = TOPIX17_x_TR - TOPIX_TR
USDJPY     = USDJPY return
JGB10Y     = JGB10Y yield change
SOX        = SOX return
```

この構成だけで、テーマバスケットの「市場・サイズ・バリュー・業種・外部半導体ベータ」はかなり除去できます。

## Phase 2：スタイルを追加

Bloomberg/Refinitiv で取得できるなら以下を追加します。

```text
MOMENTUM = MSCI/S&P Japan Momentum TR - parent TR
LOWVOL   = MSCI/S&P Japan LowVol TR - parent TR
QUALITY  = MSCI Japan Quality TR - MSCI Japan TR
YIELD    = Japan High Dividend TR - parent TR
```

JPX系を使う場合は、

```text
QUALITY_PROXY = JPX-Nikkei400_TR - TOPIX_TR
VALUE_CREATION = JPX_Prime150_TR - TOPIX_TR
```

JPX Prime 150 の Bloomberg vendor code は JPX factsheet 上で価格指数 `JPXP150 Index`、Total Return `JPXP150T Index` と記載されています。([日本取引所グループ](https://www.jpx.co.jp/english/markets/indices/factsheets/files/e_200_fac2_jpx150.pdf?utm_source=chatgpt.com))

## Phase 3：本番用に自前ファクター化

最終的には以下を自前で作るべきです。

```text
SIZE
VALUE
MOMENTUM
QUALITY
LOWVOL
YIELD
PBR_REFORM
```

特に `MOMENTUM` と `PBR_REFORM` は自前構成を推奨します。外部指数では、あなたのテーマバスケットの投資ユニバースやリバランス条件と一致しにくいからです。

---

## 8. Notebook 用の推奨 `factor_returns.csv`

まずはこの列構成で十分です。

```text
date,MKT,SIZE,VALUE,SECTOR_BANKS,SECTOR_ELEC_PREC,SECTOR_MACHINERY,SECTOR_AUTOS,SECTOR_IT_SERVICES,SECTOR_REAL_ESTATE,SECTOR_TRADING,SECTOR_RETAIL,MOMENTUM,LOWVOL,QUALITY,YIELD,USDJPY,JGB10Y,SOX
```

ただし、全 TOPIX-17 を入れるなら以下のようにしてください。

```text
date,
MKT,
SIZE,
VALUE,
SECTOR_FOODS,
SECTOR_ENERGY,
SECTOR_CONSTRUCTION_MATERIALS,
SECTOR_RAW_MATERIALS_CHEMICALS,
SECTOR_PHARMA,
SECTOR_AUTOS_TRANSPORT_EQUIP,
SECTOR_STEEL_NONFERROUS,
SECTOR_MACHINERY,
SECTOR_ELEC_PRECISION,
SECTOR_IT_SERVICES_OTHERS,
SECTOR_ELECTRIC_POWER_GAS,
SECTOR_TRANSPORT_LOGISTICS,
SECTOR_COMMERCIAL_WHOLESALE,
SECTOR_RETAIL,
SECTOR_BANKS,
SECTOR_FINANCIALS_EX_BANKS,
SECTOR_REAL_ESTATE,
MOMENTUM,
LOWVOL,
QUALITY,
YIELD,
USDJPY,
JGB10Y,
SOX
```

---

## 9. Pythonでの作成イメージ

Bloomberg から指数水準を取った後、以下のように `factor_returns.csv` を作ります。

```python
import pandas as pd

# index_prices: Bloombergから取得した指数水準
# columns例:
# TOPIX_TR, TOPIX_SMALL_TR, TOPIX100_TR,
# TOPIX_VALUE_TR, TOPIX_GROWTH_TR,
# TOPIX17_BANKS_TR, TOPIX17_MACHINERY_TR, ...
# USDJPY, JGB10Y, SOX

ret = index_prices.pct_change()

factors = pd.DataFrame(index=index_prices.index)

factors["MKT"] = ret["TOPIX_TR"]

factors["SIZE"] = (
    ret["TOPIX_SMALL_TR"]
    - ret["TOPIX100_TR"]
)

factors["VALUE"] = (
    ret["TOPIX_VALUE_TR"]
    - ret["TOPIX_GROWTH_TR"]
)

sector_cols = [
    "TOPIX17_BANKS_TR",
    "TOPIX17_MACHINERY_TR",
    "TOPIX17_ELEC_PRECISION_TR",
    "TOPIX17_IT_SERVICES_TR",
    "TOPIX17_REAL_ESTATE_TR",
]

for col in sector_cols:
    factor_name = "SECTOR_" + col.replace("TOPIX17_", "").replace("_TR", "")
    factors[factor_name] = ret[col] - ret["TOPIX_TR"]

# Macro / external factors
factors["USDJPY"] = ret["USDJPY"]
factors["JGB10Y"] = index_prices["JGB10Y"].diff()  # yieldはリターンではなく変化幅
factors["SOX"] = ret["SOX"]

factors = factors.dropna()
factors.to_csv("factor_returns.csv", index_label="date")
```

---

## 10. 実務上の注意

`factor_returns.csv` は、価格ではなく**リターン**で渡してください。  
Total Return 指数が取れる場合は、価格指数ではなく Total Return を使ってください。  
金利はリターンではなく、利回り変化で構いません。

また、業種ファクターを入れる場合は、以下のどちらかにしてください。

```text
方法A: MKT + SECTOR excess returns
方法B: SECTOR raw returns only
```

私は **方法A** を推奨します。

```text
MKT = TOPIX_TR
SECTOR_BANKS = TOPIX17_BANKS_TR - TOPIX_TR
SECTOR_MACHINERY = TOPIX17_MACHINERY_TR - TOPIX_TR
...
```

これにより、市場全体の動きと業種固有の動きを分けやすくなります。

まずは、

```text
MKT
SIZE
VALUE
TOPIX-17 sector excess returns
USDJPY
JGB10Y
SOX
```

で開始するのが最もよいです。その後、Momentum、LowVol、Quality、Yield、PBR_REFORM を追加してください。

---

**Sources:**

- [TOPIX (TPX) | Japan Exchange Group](https://www.jpx.co.jp/english/markets/indices/topix/?utm_source=chatgpt.com)
- [Tokyo Stock Exchange Tokyo Stock Price Index TOPIX](https://www.bloomberg.com/quote/TPX%3AIND?utm_source=chatgpt.com)
- [S&P Momentum Japan LargeMidCap Index | S&P Dow Jones Indices](https://www.spglobal.com/spdji/en/indices/dividends-factors/sp-momentum-japan-largemidcap-index/)
- [MSCI Japan Minimum Volatility Index (JPY)](https://www.msci.com/indexes/index/700488?utm_source=chatgpt.com)
- [FTSE Japan Comprehensive Factor Index](https://research.ftserussell.com/Analytics/Factsheets/Home/DownloadSingleIssue?IsManual=false&issueName=FJACPF&utm_source=chatgpt.com)
- [Kenneth R. French - Description of Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/details_japanese.html)

## Response:
2026/5/11 1:20:32

まず、データを「LSEGで取れる指数水準」と「構成銘柄の価格・属性」に分け、TickerではなくRIC/PermID/ISINを検索・検証して取得する形で整理します。

## Response:
2026/5/11 1:20:41

JPXファクトシート記載のベンダーコードをRIC候補にし、TOPIX系指数は「候補リスト→lseg.data疎通確認→取得可能なものだけ採用」の流れで実装します。

## Response:
2026/5/11 1:24:25

> **Clarifying JGB yields and data formats for notebook**
>
> I need to figure out the right field for JGB yield, possibly fields like `TR.BIDYIELD`, `TR.MIDYIELD`, or just `get_history('JP10YT=RR')`. I'll explain the data formats for the existing notebook: `factor_returns.csv` has dates and returns, `stock_prices.csv` includes dates and RICs, and `constituents.csv` might need broker mapping. I want to make sure to use official documentation for fields and cite sources like LSEG and JPX.
>
> Thought for 8m 3s

## Response:
2026/5/11 1:28:35

以下では、Refinitiv/LSEG 上の **Ticker は原則として RIC** として扱います。日本株個別銘柄なら通常 `7203.T`、`8035.T` のような形式、指数なら `.TOPXDV` のような形式です。Bloomberg ticker や証券コードだけを持っている場合は、後述のコードで RIC に変換・検証してください。

`lseg.data` では、価格時系列は `ld.get_history()`、銘柄属性や TRBC などの参照データは `ld.get_data()`、検索は `ld.discovery.search()` や content layer の `search.Definition()` を使います。LSEG の公式ドキュメントでも、`get_history` は pricing history と fundamental/reference history を取得する関数として説明されており、`universe`, `fields`, `interval`, `start`, `end` などを指定できます。([Refinitiv](https://cdn.refinitiv.com/public/lseg-lib-python-doc/2.0.0.2/book/en/sections/access-layer/access/get-history-function.html)) また、Quick Reference では `ld.discovery.search()`、`ld.get_history()`、TRBC 参照フィールドの利用例が示されています。([LSEG Developers](https://developers.lseg.com/en/article-catalog/article/the-data-library-for-python-quick-reference-guide-access-layer))

---

# 1. Factor-adjusted で取得すべきデータ

Factor-adjusted で必要なのは、テーマ価格時系列を残差化するための **ファクターリターンCSV** です。Refinitiv/LSEG からは、まず以下のインデックス水準を取得し、Python側で日次リターンに変換します。

## 1.1 推奨ファクターと RIC

### コア指数

| 用途 | ファクター名 | 取得する RIC | 作成方法 |
|---|---|---:|---|
| 市場 | `MKT` | `.TOPXDV` | TOPIX Total Return の日次リターン |
| サイズ | `SIZE` | `.TOPXSDV`, `.TOPX100DV` | TOPIX Small TR - TOPIX100 TR |
| バリュー | `VALUE` | `.TOPXVTR`, `.TOPXGTR` | TOPIX Value TR - TOPIX Growth TR |
| 高配当 | `YIELD` | `.TPXHY40TR`, `.TOPXDV` | TOPIX High Dividend Yield 40 TR - TOPIX TR |

JPX の factsheet では、TOPIX の Refinitiv コードとして価格指数 `.TOPX`、配当込み指数 `.TOPXDV` が記載されています。TOPIX Growth は `.TOPXG` / `.TOPXGTR`、TOPIX Small は `.TOPXS` / `.TOPXSDV`、TOPIX100 は `.TOPX100` / `.TOPX100DV`、TOPIX Value は `.TOPXV` / `.TOPXVTR`、TOPIX High Dividend Yield 40 は `.TPXHY40` / `.TPXHY40TR` と記載されています。([日本取引所グループ](https://www.jpx.co.jp/english/markets/indices/factsheets/files/e_001_fac2_TOPIX.pdf))

---

## 1.2 TOPIX-17 業種ファクター

テーマバスケット戦略では、業種ファクターはかなり重要です。まずは TOPIX-17 の配当込み指数を取得し、各業種の TOPIX 対比 excess return を作ってください。

```text
SECTOR_BANKS = return(.BANK17TR) - return(.TOPXDV)
SECTOR_MACHINERY = return(.MACH17TR) - return(.TOPXDV)
...
```

| TOPIX-17 業種 | RIC, Price Return | RIC, Total Return | factor列名例 |
|---|---:|---:|---|
| Foods | `.FOOD17.T` | `.FOOD17TR` | `SECTOR_FOODS` |
| Energy Resources | `.ENGY17.T` | `.ENGY17TR` | `SECTOR_ENERGY` |
| Construction & Materials | `.CNST17.T` | `.CNST17TR` | `SECTOR_CONSTRUCTION_MATERIALS` |
| Raw Materials & Chemicals | `.CHEM17.T` | `.CHEM17TR` | `SECTOR_RAW_MATERIALS_CHEMICALS` |
| Pharmaceutical | `.PHAM17.T` | `.PHAM17TR` | `SECTOR_PHARMA` |
| Automobiles & Transportation Equipment | `.ATMO17.T` | `.ATMO17TR` | `SECTOR_AUTOS_TRANSPORT_EQUIP` |
| Steel & Nonferrous Metals | `.STEL17.T` | `.STEL17TR` | `SECTOR_STEEL_NONFERROUS` |
| Machinery | `.MACH17.T` | `.MACH17TR` | `SECTOR_MACHINERY` |
| Electric Appliances & Precision Instruments | `.ELEC17.T` | `.ELEC17TR` | `SECTOR_ELEC_PRECISION` |
| IT & Services, Others | `.ITSV17.T` | `.ITSV17TR` | `SECTOR_IT_SERVICES_OTHERS` |
| Electric Power & Gas | `.PWGA17.T` | `.PWGA17TR` | `SECTOR_POWER_GAS` |
| Transportation & Logistics | `.TRAN17.T` | `.TRAN17TR` | `SECTOR_TRANSPORT_LOGISTICS` |
| Commercial & Wholesale Trade | `.TRAD17.T` | `.TRAD17TR` | `SECTOR_COMMERCIAL_WHOLESALE` |
| Retail Trade | `.RETL17.T` | `.RETL17TR` | `SECTOR_RETAIL` |
| Banks | `.BANK17.T` | `.BANK17TR` | `SECTOR_BANKS` |
| Financials ex Banks | `.FNCL17.T` | `.FNCL17TR` | `SECTOR_FINANCIALS_EX_BANKS` |
| Real Estate | `.RLTY17.T` | `.RLTY17TR` | `SECTOR_REAL_ESTATE` |

JPX の TOPIX-17 factsheet では、TOPIX-17 が東証33業種を17分類に集約した指数であること、また Refinitiv の価格指数・配当込み指数コードが掲載されています。たとえば Banks は `.BANK17.T` / `.BANK17TR`、Electric Appliances & Precision Instruments は `.ELEC17.T` / `.ELEC17TR`、Automobiles & Transportation Equipment は `.ATMO17.T` / `.ATMO17TR` と記載されています。([日本取引所グループ](https://www.jpx.co.jp/english/markets/indices/factsheets/files/e_003_2_15_fac2_17sector_BANKS.pdf?utm_source=chatgpt.com))

---

## 1.3 テーマ固有の外部ファクター

| 用途 | RIC候補 | 作成方法 | 備考 |
|---|---:|---|---|
| 半導体外部ベータ | `.SOX` | 日次リターン、原則1営業日ラグ | 半導体、AI、データセンター向け |
| 為替 | `JPY=` または `USDJPY=X` | USDJPY の日次変化率 | 環境によって RIC 表記が異なるため検証推奨 |
| 金利 | `JP10YTN=JBTC` | 10年JGB利回り変化 | 銀行、保険、不動産、低PBR向け |

Reuters の quote page では Philadelphia SE Semiconductor Index が `.SOX` として表示されます。USD/JPY は Reuters 上で `USDJPY=X` として表示されますが、LSEG Workspace/Eikon のデスクトップ RIC では `JPY=` が使われる環境もあるため、後述の `validate_rics()` で確認してください。10年最長期国債利回りについては Reuters 記事中で `<JP10YTN=JBTC>` と表記されています。([Reuters](https://www.reuters.com/markets/quote/.SOX/))

---

# 2. Factor-adjusted 用：lseg.data 取得プログラム

以下をそのまま Notebook のセルに入れて使えます。

```python
# ============================================================
# Factor-adjusted: Refinitiv/LSEG からファクター用指数を取得
# ============================================================

import pandas as pd
import numpy as np
import lseg.data as ld

# Workspace / Eikon / Platform の接続設定に応じて open_session してください。
# Desktop session の場合は Workspace/Eikon を起動した状態で実行します。
ld.open_session()
```

## 2.1 RIC一覧

```python
# ------------------------------------------------------------
# 1. ファクター作成に使う RIC
# ------------------------------------------------------------

CORE_RICS = {
    # Market
    "TOPIX_TR": ".TOPXDV",

    # Size
    "TOPIX_SMALL_TR": ".TOPXSDV",
    "TOPIX100_TR": ".TOPX100DV",

    # Style
    "TOPIX_VALUE_TR": ".TOPXVTR",
    "TOPIX_GROWTH_TR": ".TOPXGTR",

    # Dividend / yield proxy
    "TOPIX_HIGH_DIV40_TR": ".TPXHY40TR",
}

TOPIX17_TR_RICS = {
    "FOODS": ".FOOD17TR",
    "ENERGY": ".ENGY17TR",
    "CONSTRUCTION_MATERIALS": ".CNST17TR",
    "RAW_MATERIALS_CHEMICALS": ".CHEM17TR",
    "PHARMA": ".PHAM17TR",
    "AUTOS_TRANSPORT_EQUIP": ".ATMO17TR",
    "STEEL_NONFERROUS": ".STEL17TR",
    "MACHINERY": ".MACH17TR",
    "ELEC_PRECISION": ".ELEC17TR",
    "IT_SERVICES_OTHERS": ".ITSV17TR",
    "POWER_GAS": ".PWGA17TR",
    "TRANSPORT_LOGISTICS": ".TRAN17TR",
    "COMMERCIAL_WHOLESALE": ".TRAD17TR",
    "RETAIL": ".RETL17TR",
    "BANKS": ".BANK17TR",
    "FINANCIALS_EX_BANKS": ".FNCL17TR",
    "REAL_ESTATE": ".RLTY17TR",
}

EXTERNAL_RICS = {
    "SOX": ".SOX",

    # FX は環境によって RIC が異なることがあるため候補として扱う
    # まず JPY= を試し、取れなければ USDJPY=X を検索・検証
    "USDJPY": "JPY=",

    # 10Y JGB yield
    "JGB10Y": "JP10YTN=JBTC",
}

ALL_RICS = {}
ALL_RICS.update(CORE_RICS)
ALL_RICS.update(TOPIX17_TR_RICS)
ALL_RICS.update(EXTERNAL_RICS)

ALL_RICS
```

## 2.2 RIC 検証関数

LSEG の entitlement や環境によって、一部の RIC が取れない場合があります。まず検証します。

```python
# ------------------------------------------------------------
# 2. RIC が取得可能か確認する関数
# ------------------------------------------------------------

def validate_rics(rics, start="2024-01-01", end="2024-01-10"):
    """
    各 RIC について get_history が成功するか確認する。
    取得できない RIC をリストアップする。
    """
    ok = []
    ng = []

    for ric in rics:
        try:
            df = ld.get_history(
                universe=[ric],
                fields=["TRDPRC_1"],
                interval="daily",
                start=start,
                end=end,
            )
            if df is not None and len(df) > 0:
                ok.append(ric)
            else:
                ng.append(ric)
        except Exception as e:
            ng.append(ric)
            print(f"[NG] {ric}: {e}")

    return ok, ng

ok_rics, ng_rics = validate_rics(list(ALL_RICS.values()))
print("OK:", ok_rics)
print("NG:", ng_rics)
```

`JPY=` が取れない場合は、`USDJPY=X` を試してください。

```python
# USDJPY RIC の代替候補を確認
if "JPY=" in ng_rics:
    ok_alt, ng_alt = validate_rics(["USDJPY=X"])
    print("USDJPY alternative OK:", ok_alt)
    print("USDJPY alternative NG:", ng_alt)
```

---

## 2.3 検索で RIC を探す関数

RICが不明な場合は、LSEG Search を使って候補を探します。

```python
# ------------------------------------------------------------
# 3. RIC 検索
# ------------------------------------------------------------

from lseg.data.content import search

def search_lseg(query, top=20):
    """
    LSEG Search で RIC 候補を検索する。
    """
    response = search.Definition(
        query=query,
        top=top
    ).get_data()

    return response.data.df

# 例
# search_lseg("TOPIX Total Return", top=10)
# search_lseg("TOPIX Value Total Return", top=10)
# search_lseg("USD JPY spot", top=10)
# search_lseg("Japan 10 year government bond yield", top=10)
```

---

## 2.4 価格・指数水準を取得する関数

`get_history()` は返り値の列形式が環境・フィールド指定によって変わることがあるため、以下では MultiIndex にも対応します。

```python
# ------------------------------------------------------------
# 4. get_history の返り値を wide matrix に整形
# ------------------------------------------------------------

def _extract_field_from_history(df, rics, field="TRDPRC_1"):
    """
    ld.get_history の返り値から、指定 field の wide DataFrame を作る。
    columns = RIC に揃える。
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()

    out = df.copy()

    if isinstance(out.columns, pd.MultiIndex):
        # field がどの level にあるか探す
        for level in range(out.columns.nlevels):
            labels = set(out.columns.get_level_values(level))
            if field in labels:
                out = out.xs(field, axis=1, level=level)
                break

        # xs 後も MultiIndex が残る場合は平坦化
        if isinstance(out.columns, pd.MultiIndex):
            out.columns = [
                tuple([x for x in col if x != field])[-1]
                for col in out.columns
            ]

    else:
        # 単一RIC・単一フィールドの場合、列名が field になることがある
        if len(rics) == 1 and out.shape[1] == 1:
            out.columns = [rics[0]]

    # 列名を文字列化
    out.columns = [str(c) for c in out.columns]

    return out

def get_history_matrix(
    rics,
    start,
    end,
    field="TRDPRC_1",
    interval="daily",
    batch_size=50,
):
    """
    複数 RIC の日次時系列を取得し、wide DataFrame にする。
    """
    rics = list(dict.fromkeys(rics))  # unique preserve order
    parts = []

    for i in range(0, len(rics), batch_size):
        batch = rics[i:i + batch_size]

        try:
            raw = ld.get_history(
                universe=batch,
                fields=[field],
                interval=interval,
                start=start,
                end=end,
            )
            mat = _extract_field_from_history(raw, batch, field=field)

        except Exception as e:
            print(f"[WARN] field={field} failed for batch {i}: {e}")
            print("       Trying default fields...")
            raw = ld.get_history(
                universe=batch,
                interval=interval,
                start=start,
                end=end,
            )
            mat = raw.copy()
            if isinstance(mat.columns, pd.MultiIndex):
                # 返ってきた最初の numeric-like field を使う
                mat = mat.select_dtypes(include=[np.number])

        parts.append(mat)

    out = pd.concat(parts, axis=1)
    out = out.loc[:, ~out.columns.duplicated()]
    out = out.sort_index()
    out.index = pd.to_datetime(out.index)

    return out
```

---

## 2.5 factor_returns.csv を作成

```python
# ------------------------------------------------------------
# 5. Refinitiv/LSEG から指数水準を取得して factor_returns.csv を作成
# ------------------------------------------------------------

START = "2016-01-01"
END = None  # None にすると現在まで。必要に応じて "2026-05-10" など。

ric_to_name = {v: k for k, v in ALL_RICS.items()}

index_levels_ric = get_history_matrix(
    rics=list(ALL_RICS.values()),
    start=START,
    end=END,
    field="TRDPRC_1",
    interval="daily",
    batch_size=40,
)

# RIC列名を論理名に変換
index_levels = index_levels_ric.rename(columns=ric_to_name)

# 価格・指数水準として保存
index_levels.to_csv("lseg_index_levels.csv", index_label="date")

# 日次リターン
ret = index_levels.ffill().pct_change()

factors = pd.DataFrame(index=index_levels.index)

# Market
factors["MKT"] = ret["TOPIX_TR"]

# Size
factors["SIZE"] = (
    ret["TOPIX_SMALL_TR"]
    - ret["TOPIX100_TR"]
)

# Value
factors["VALUE"] = (
    ret["TOPIX_VALUE_TR"]
    - ret["TOPIX_GROWTH_TR"]
)

# Yield
if "TOPIX_HIGH_DIV40_TR" in ret.columns:
    factors["YIELD"] = (
        ret["TOPIX_HIGH_DIV40_TR"]
        - ret["TOPIX_TR"]
    )

# TOPIX-17 sectors: sector excess return
for sector_name in TOPIX17_TR_RICS.keys():
    if sector_name in ret.columns:
        factors[f"SECTOR_{sector_name}"] = (
            ret[sector_name]
            - ret["TOPIX_TR"]
        )

# External factors
# 注意：日本株の日中・終値ベースのバックテストでは、米国指数は原則1営業日ラグ推奨。
if "SOX" in ret.columns:
    factors["SOX_LAG1"] = ret["SOX"].shift(1)

# USDJPY
# JPY= が取れた場合。USDJPY=Xを使った場合は列名を合わせてください。
if "USDJPY" in ret.columns:
    factors["USDJPY"] = ret["USDJPY"]

# JGB10Yは利回りなので pct_change ではなく diff を使う。
# LSEG上の単位が%表示なら /100 して小数化する。回帰用途なら diff のままでも可。
if "JGB10Y" in index_levels.columns:
    factors["JGB10Y"] = index_levels["JGB10Y"].diff() / 100.0

# 欠損処理
factors = factors.replace([np.inf, -np.inf], np.nan)
factors = factors.dropna(how="all")

# 初期欠損が多い列を必要に応じて削除
# 例: 70%以上欠損なら削除
min_non_na = int(len(factors) * 0.70)
factors = factors.dropna(axis=1, thresh=min_non_na)

# 回帰用には欠損を過度に埋めない方がよいが、
# 指数リターンの単発欠損は0埋めまたは前後確認。
factors = factors.fillna(0.0)

factors.to_csv("factor_returns_lseg.csv", index_label="date")

factors.tail()
```

この `factor_returns_lseg.csv` を、以前作成した strategy notebook / script の `factor_csv` に渡してください。

```bash
python theme_basket_strategy.py \
  --theme_csv theme_prices.csv \
  --factor_csv factor_returns_lseg.csv \
  --theme_input_kind price \
  --mode long_only \
  --top_n 5 \
  --output_dir output_factor_adjusted \
  --disable_coherence_gate
```

---

# 3. Coherence-gated で取得すべきデータ

Coherence-gated では、テーマ内の構成銘柄について、平均ペアワイズ残差相関や固有値を計算します。必要なのは以下です。

| データ | 取得元 | 形式 |
|---|---|---|
| テーマ構成銘柄・ウェイト | 証券会社から取得済みの想定 | `date, theme, ticker/ric, weight` |
| 個別株価格/リターン | LSEG / Refinitiv | `date, 7203.T, 8035.T, ...` |
| ファクターリターン | 上記 Factor-adjusted で作成 | `factor_returns_lseg.csv` |
| 銘柄属性 | LSEG / Refinitiv | `TR.CommonName`, TRBC, market cap 等 |
| 会社概要文 | LSEG / Refinitiv | 利用可能フィールドは Data Item Browser で確認 |

TRBC については、LSEG Quick Reference で `TR.CommonName`, `TR.TRBCEconomicSector`, `TR.TRBCBusinessSector`, `TR.TRBCIndustryGroup`, `TR.TRBCIndustry`, `TR.TRBCActivity` および対応する code fields の例が示されています。([LSEG Developers](https://developers.lseg.com/en/article-catalog/article/the-data-library-for-python-quick-reference-guide-access-layer))

---

# 4. Coherence-gated 用：個別株価格を取得するプログラム

前提として、証券会社から取得した構成銘柄CSVがあるとします。

```text
date,theme,ticker,weight
2024-01-31,AI,6758,0.08
2024-01-31,AI,6501,0.07
2024-01-31,Semiconductor,8035,0.12
2024-01-31,Semiconductor,6857,0.10
```

または、すでに RIC 形式で、

```text
date,theme,ric,weight
2024-01-31,AI,6758.T,0.08
2024-01-31,AI,6501.T,0.07
```

でも構いません。

---

## 4.1 構成銘柄の RIC 正規化

```python
# ============================================================
# Coherence-gated: 構成銘柄を RIC 化し、個別株価格を取得
# ============================================================

import re
import pandas as pd
import numpy as np
import lseg.data as ld

ld.open_session()

def normalize_japan_equity_ric(x):
    """
    日本株の証券コード/Bloomberg風表記/RICを、可能な範囲で RIC に正規化する。
    例:
      7203      -> 7203.T
      '7203'    -> 7203.T
      '7203 JT Equity' -> 7203.T
      '7203.T'  -> 7203.T
    """
    if pd.isna(x):
        return np.nan

    s = str(x).strip()

    # すでに RIC らしい場合
    if s.endswith(".T"):
        return s

    # Bloomberg風: "7203 JT Equity"
    m = re.match(r"^(\d{4})\s+JT\s+Equity$", s, flags=re.IGNORECASE)
    if m:
        return f"{m.group(1)}.T"

    # 4桁証券コード
    m = re.match(r"^(\d{4})$", s)
    if m:
        return f"{m.group(1)}.T"

    # その他はそのまま返す。あとで search / validate で確認。
    return s

const = pd.read_csv("constituents.csv")

# 列名を吸収
cols_lower = {c.lower(): c for c in const.columns}

theme_col = cols_lower.get("theme")
weight_col = cols_lower.get("weight")
date_col = cols_lower.get("date") or cols_lower.get("effective_date")
ric_col = cols_lower.get("ric")
ticker_col = cols_lower.get("ticker") or cols_lower.get("symbol") or cols_lower.get("code")

if ric_col is not None:
    const["ric"] = const[ric_col].map(normalize_japan_equity_ric)
elif ticker_col is not None:
    const["ric"] = const[ticker_col].map(normalize_japan_equity_ric)
else:
    raise ValueError("constituents.csv には ric, ticker, symbol, code のいずれかが必要です。")

const["theme"] = const[theme_col].astype(str)
const["weight"] = pd.to_numeric(const[weight_col], errors="coerce")

if date_col is not None:
    const["date"] = pd.to_datetime(const[date_col])
else:
    const["date"] = pd.Timestamp("1900-01-01")

# 欠損・重複除去
const = const.dropna(subset=["date", "theme", "ric", "weight"])
const = const[const["weight"] > 0].copy()

# strategy script が読む形式に合わせる
const_for_strategy = const[["date", "theme", "ric", "weight"]].rename(columns={"ric": "ticker"})
const_for_strategy.to_csv("constituents_ric.csv", index=False)

stock_rics = sorted(const["ric"].unique().tolist())
len(stock_rics), stock_rics[:10]
```

---

## 4.2 個別株 RIC の検証

```python
# 先ほど定義した validate_rics を再利用
ok_stock_rics, ng_stock_rics = validate_rics(stock_rics, start="2024-01-01", end="2024-01-10")

print("OK stocks:", len(ok_stock_rics))
print("NG stocks:", len(ng_stock_rics))
print("NG sample:", ng_stock_rics[:20])
```

RIC が取れない場合は、Search で探します。

```python
# 例: 取れない銘柄を検索
for bad in ng_stock_rics[:5]:
    print("====", bad, "====")
    try:
        print(search_lseg(bad.replace(".T", ""), top=10)[["RIC", "DocumentTitle"]].head())
    except Exception as e:
        print(e)
```

---

## 4.3 個別株価格を取得

個別株価格は `TRDPRC_1` を使います。配当調整済み・total return 系のフィールドが利用可能な契約であれば、そちらの方がより望ましいです。ただし coherence gate の目的は主にテーマ内の残差相関を見ることなので、まずは終値系列から始めて構いません。

```python
# ------------------------------------------------------------
# 個別株価格の取得
# ------------------------------------------------------------

START = "2016-01-01"
END = None

stock_prices = get_history_matrix(
    rics=ok_stock_rics,
    start=START,
    end=END,
    field="TRDPRC_1",
    interval="daily",
    batch_size=80,
)

# 列名は RIC のままにする
stock_prices = stock_prices.sort_index()
stock_prices.to_csv("stock_prices_lseg.csv", index_label="date")

stock_prices.tail()
```

これで `coherence-gated` 用の `stock_prices_lseg.csv` ができます。

```bash
python theme_basket_strategy.py \
  --theme_csv theme_prices.csv \
  --factor_csv factor_returns_lseg.csv \
  --constituents_csv constituents_ric.csv \
  --stock_csv stock_prices_lseg.csv \
  --theme_input_kind price \
  --stock_input_kind price \
  --mode long_only \
  --top_n 5 \
  --output_dir output_coherence_gated
```

---

# 5. Coherence-gated 用：銘柄属性・TRBCを取得するプログラム

これは coherence gate そのものには必須ではありませんが、テーマ純度、業種制約、後続の semantic purity に使います。

```python
# ------------------------------------------------------------
# 銘柄属性・TRBC の取得
# ------------------------------------------------------------

def get_data_chunked(rics, fields, batch_size=100):
    parts = []

    for i in range(0, len(rics), batch_size):
        batch = rics[i:i + batch_size]
        try:
            df = ld.get_data(
                universe=batch,
                fields=fields,
            )
            parts.append(df)
        except Exception as e:
            print(f"[WARN] get_data failed for batch {i}: {e}")

    if not parts:
        return pd.DataFrame()

    out = pd.concat(parts, axis=0)
    return out

ref_fields = [
    "TR.RIC",
    "TR.CommonName",

    # TRBC names
    "TR.TRBCEconomicSector",
    "TR.TRBCBusinessSector",
    "TR.TRBCIndustryGroup",
    "TR.TRBCIndustry",
    "TR.TRBCActivity",

    # TRBC codes
    "TR.TRBCEconSectorCode",
    "TR.TRBCBusinessSectorCode",
    "TR.TRBCIndustryGroupCode",
    "TR.TRBCIndustryCode",
    "TR.TRBCActivityCode",

    # Size / liquidity / basic descriptors
    "TR.CompanyMarketCap",
    "TR.FreeFloatPct",
    "TR.PriceClose",
]

security_master = get_data_chunked(
    rics=ok_stock_rics,
    fields=ref_fields,
    batch_size=100,
)

security_master.to_csv("security_master_lseg.csv", index=False)
security_master.head()
```

---

# 6. 会社概要文・テーマ純度用データ

Refinitiv/LSEG で会社概要文を取る場合、利用可能フィールド名は契約・Workspace環境で差が出ることがあります。Data Item Browser で確認しながら、以下の候補を試してください。

候補フィールド名：

```text
TR.BusinessSummary
TR.CompanyDescription
TR.BusinessDescription
TR.OrganizationSummary
TR.CompanyProfile
```

以下は、候補フィールドを順番に試して、取れたものを保存するコードです。

```python
# ------------------------------------------------------------
# 会社概要文フィールド候補を試す
# ------------------------------------------------------------

text_field_candidates = [
    "TR.BusinessSummary",
    "TR.CompanyDescription",
    "TR.BusinessDescription",
    "TR.OrganizationSummary",
    "TR.CompanyProfile",
]

available_text = {}

for fld in text_field_candidates:
    try:
        tmp = get_data_chunked(
            rics=ok_stock_rics[:20],
            fields=["TR.RIC", "TR.CommonName", fld],
            batch_size=20,
        )
        non_null_count = tmp[fld].notna().sum() if fld in tmp.columns else 0
        print(fld, "non-null sample:", non_null_count)

        if non_null_count > 0:
            available_text[fld] = non_null_count

    except Exception as e:
        print("[NG]", fld, e)

available_text
```

取れるフィールドが分かったら、全銘柄で取得します。

```python
# 例: 利用可能だった最初のフィールドを使う
if available_text:
    best_text_field = list(available_text.keys())[0]

    company_text = get_data_chunked(
        rics=ok_stock_rics,
        fields=["TR.RIC", "TR.CommonName", best_text_field],
        batch_size=100,
    )

    company_text.to_csv("company_text_lseg.csv", index=False)
    print("Saved:", best_text_field)

else:
    print("会社概要文フィールドが取得できませんでした。Data Item Browserでフィールド名を確認してください。")
```

---

# 7. Factor-adjusted と Coherence-gated の入力ファイル対応

最終的に、以前の strategy notebook / script には以下を渡します。

| 戦略レベル | 入力ファイル | 作成方法 |
|---|---|---|
| Factor-adjusted | `theme_prices.csv` | 既に保有しているテーマバスケット価格 |
| Factor-adjusted | `factor_returns_lseg.csv` | 上記の LSEG 指数から作成 |
| Coherence-gated | `constituents_ric.csv` | 証券会社の構成銘柄を RIC 化 |
| Coherence-gated | `stock_prices_lseg.csv` | LSEG から個別株価格を取得 |
| Coherence-gated 補助 | `security_master_lseg.csv` | TRBC、時価総額、会社名等 |
| Coherence-gated 補助 | `company_text_lseg.csv` | semantic purity 用 |

実行コマンドは以下です。

```bash
python theme_basket_strategy.py \
  --theme_csv theme_prices.csv \
  --factor_csv factor_returns_lseg.csv \
  --constituents_csv constituents_ric.csv \
  --stock_csv stock_prices_lseg.csv \
  --theme_input_kind price \
  --stock_input_kind price \
  --mode long_only \
  --top_n 5 \
  --output_dir output_coherence_gated
```

---

# 8. Notebook用に分けるなら、この順番のセルが良いです

## Cell A：LSEG session

```python
import pandas as pd
import numpy as np
import lseg.data as ld

ld.open_session()
```

## Cell B：RIC辞書

```python
CORE_RICS = {
    "TOPIX_TR": ".TOPXDV",
    "TOPIX_SMALL_TR": ".TOPXSDV",
    "TOPIX100_TR": ".TOPX100DV",
    "TOPIX_VALUE_TR": ".TOPXVTR",
    "TOPIX_GROWTH_TR": ".TOPXGTR",
    "TOPIX_HIGH_DIV40_TR": ".TPXHY40TR",
}

TOPIX17_TR_RICS = {
    "FOODS": ".FOOD17TR",
    "ENERGY": ".ENGY17TR",
    "CONSTRUCTION_MATERIALS": ".CNST17TR",
    "RAW_MATERIALS_CHEMICALS": ".CHEM17TR",
    "PHARMA": ".PHAM17TR",
    "AUTOS_TRANSPORT_EQUIP": ".ATMO17TR",
    "STEEL_NONFERROUS": ".STEL17TR",
    "MACHINERY": ".MACH17TR",
    "ELEC_PRECISION": ".ELEC17TR",
    "IT_SERVICES_OTHERS": ".ITSV17TR",
    "POWER_GAS": ".PWGA17TR",
    "TRANSPORT_LOGISTICS": ".TRAN17TR",
    "COMMERCIAL_WHOLESALE": ".TRAD17TR",
    "RETAIL": ".RETL17TR",
    "BANKS": ".BANK17TR",
    "FINANCIALS_EX_BANKS": ".FNCL17TR",
    "REAL_ESTATE": ".RLTY17TR",
}

EXTERNAL_RICS = {
    "SOX": ".SOX",
    "USDJPY": "JPY=",
    "JGB10Y": "JP10YTN=JBTC",
}
```

## Cell C：factor_returns 作成

```python
ALL_RICS = {}
ALL_RICS.update(CORE_RICS)
ALL_RICS.update(TOPIX17_TR_RICS)
ALL_RICS.update(EXTERNAL_RICS)

ric_to_name = {v: k for k, v in ALL_RICS.items()}

index_levels_ric = get_history_matrix(
    rics=list(ALL_RICS.values()),
    start="2016-01-01",
    end=None,
    field="TRDPRC_1",
    interval="daily",
    batch_size=40,
)

index_levels = index_levels_ric.rename(columns=ric_to_name)
ret = index_levels.ffill().pct_change()

factors = pd.DataFrame(index=index_levels.index)

factors["MKT"] = ret["TOPIX_TR"]
factors["SIZE"] = ret["TOPIX_SMALL_TR"] - ret["TOPIX100_TR"]
factors["VALUE"] = ret["TOPIX_VALUE_TR"] - ret["TOPIX_GROWTH_TR"]
factors["YIELD"] = ret["TOPIX_HIGH_DIV40_TR"] - ret["TOPIX_TR"]

for sector_name in TOPIX17_TR_RICS.keys():
    if sector_name in ret.columns:
        factors[f"SECTOR_{sector_name}"] = ret[sector_name] - ret["TOPIX_TR"]

if "SOX" in ret.columns:
    factors["SOX_LAG1"] = ret["SOX"].shift(1)

if "USDJPY" in ret.columns:
    factors["USDJPY"] = ret["USDJPY"]

if "JGB10Y" in index_levels.columns:
    factors["JGB10Y"] = index_levels["JGB10Y"].diff() / 100.0

factors = factors.replace([np.inf, -np.inf], np.nan)
factors = factors.fillna(0.0)

factors.to_csv("factor_returns_lseg.csv", index_label="date")
factors.tail()
```

## Cell D：構成銘柄を RIC 化

```python
const = pd.read_csv("constituents.csv")

# 例: ticker列が証券コードまたはRICの場合
const["ric"] = const["ticker"].map(normalize_japan_equity_ric)

const_for_strategy = const.rename(columns={"ric": "ticker"})
const_for_strategy = const_for_strategy[["date", "theme", "ticker", "weight"]]
const_for_strategy.to_csv("constituents_ric.csv", index=False)

stock_rics = sorted(const["ric"].dropna().unique().tolist())
len(stock_rics)
```

## Cell E：個別株価格を取得

```python
ok_stock_rics, ng_stock_rics = validate_rics(
    stock_rics,
    start="2024-01-01",
    end="2024-01-10",
)

print("OK:", len(ok_stock_rics))
print("NG:", len(ng_stock_rics), ng_stock_rics[:20])

stock_prices = get_history_matrix(
    rics=ok_stock_rics,
    start="2016-01-01",
    end=None,
    field="TRDPRC_1",
    interval="daily",
    batch_size=80,
)

stock_prices.to_csv("stock_prices_lseg.csv", index_label="date")
stock_prices.tail()
```

---

# 9. 実務上の注意点

一番重要なのは、**Total Return 指数を優先すること**です。ファクター側では `.TOPX` ではなく `.TOPXDV`、`.TOPXS` ではなく `.TOPXSDV`、`.TOPXV` ではなく `.TOPXVTR` のように、配当込み指数を使ってください。個別株側は `TRDPRC_1` の終値で開始して構いませんが、配当落ちの影響が気になる場合は、LSEG の調整済み価格・total return 系フィールドを Data Item Browser で確認して置き換えてください。

また、日本株の終値ベースでテーマバスケットを評価する場合、`.SOX` など米国指数は同日ではなく **1営業日ラグ** を推奨します。同日 `.SOX` を使うと、日本時間の東証終値後に確定する米国市場情報を混入させる可能性があります。

まずは以下の構成で始めるのが良いです。

```text
MKT
SIZE
VALUE
TOPIX-17 sector excess returns
YIELD
USDJPY
JGB10Y
SOX_LAG1
```

その後、Refinitiv 上で MSCI/S&P/FTSE の Japan Momentum, Quality, Low Volatility 系指数にアクセスできるなら、追加で `MOMENTUM`, `QUALITY`, `LOWVOL` を作ってください。銘柄ユニバースとリバランスルールを完全に合わせたい場合は、最終的には Refinitiv の個別株データから自前の long-short ファクターを作るのが最も望ましいです。

---

**Sources:**

- [get_history](https://cdn.refinitiv.com/public/lseg-lib-python-doc/2.0.0.2/book/en/sections/access-layer/access/get-history-function.html)
- [The Data Library for Python  - Quick Reference Guide (Access layer) | Devportal](https://developers.lseg.com/en/article-catalog/article/the-data-library-for-python-quick-reference-guide-access-layer)
- [jpx.co.jp](https://www.jpx.co.jp/english/markets/indices/factsheets/files/e_001_fac2_TOPIX.pdf)
- [ (.SOX) | Stock Price & Latest News | Reuters](https://www.reuters.com/markets/quote/.SOX/)



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)