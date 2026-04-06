# 論文解説 クラウディング分析

**User:** Kentaro Baba (kencharoffx@gmail.com)  
**Created:** 4/6/2026 20:35:11  
**Updated:** 4/6/2026 21:05:33  
**Exported:** 4/6/2026 23:06:52  
**Link:** [https://chatgpt.com/c/69d39a5c-ed34-83ab-9825-4c02ecb79f2e](https://chatgpt.com/c/69d39a5c-ed34-83ab-9825-4c02ecb79f2e)  

## Response:
2026/4/6 20:35:10

> 思考時間: 8s

この論文は、**「クラウディング（crowded trades）」を利用して、セクターローテーションやファクタータイミングに活かせないか**を検証したものです。結論からいうと、著者たちは

*   **どの資産群に資金が集中しているか**を示す指標として **centrality**
*   **その集中が割高な局面かどうか**を示す指標として **relative value**

を組み合わせることで、**バブルの上昇局面と崩壊局面をある程度識別できる**と主張しています。さらに、その考え方を使ったバックテストでは、米国株の**セクターローテーション**でも**ファクタータイミング**でも、静的な保有や市場指数対比で良好な成績が得られた、と報告しています。

jpm\_crowded\_trades

論文の問題意識
-------

論文の出発点は、**価格上昇そのものだけではバブルかどうか分からない**という点です。ファンダメンタルズの改善で価格が上がることもあれば、投資家心理や流行で資金が一方向に集中して価格が上がることもあります。後者がいわゆるバブルに近い現象であり、これを早めに見つけて、しかも崩壊前に抜けられれば収益機会になる、という発想です。著者は、**centralityだけでも不十分、relative valueだけでも不十分で、両方を併用すべき**だと述べています。

jpm\_crowded\_trades

centrality とは何か
---------------

この論文の中心概念が **asset centrality** です。考え方としては、あるセクターやファクターが、**市場全体の共分散構造の中でどれだけ中心的な位置を占めているか**を測ります。具体的には、

1.  セクター群の共分散行列を作る
2.  主成分分析を行う
3.  上位の固有ベクトルが全体の分散をどれだけ吸収するかを見る
4.  各セクターがその主要固有ベクトルにどれだけ強く載っているかを重み付きで合成する

ことで centrality を定義しています。論文ではまず **absorption ratio** を定義し、その上で各資産群の寄与を使って centrality を作っています。

jpm\_crowded\_trades

直感的には、**資金が集中しているセクターは、ボラティリティが上がり、他セクターとの連関も強まり、市場全体の値動きに対して“中心的”になる**、というロジックです。論文では、テックバブル期にはテクノロジー、金融危機前後には金融やREITs、エネルギー価格変動時にはエネルギーの centrality が高かったことを、ヒートマップで示しています。これは6ページの Exhibit 1 にあります。

jpm\_crowded\_trades

なぜ centrality だけではダメか
---------------------

重要なのは、**centrality はバブル上昇時にも下落時にも高くなる**ことです。実際、論文では、テックバブルでも住宅バブルでも、**centrality は上昇局面で上がるだけでなく、崩壊局面ではむしろさらに急上昇する**と示しています。つまり、

*   centrality が高い  
    → 「人が集まっている」ことは分かる  
    → しかし、それが**これから上がる crowdedness** なのか、**投げ売りの crowdedness** なのかは分からない

という問題があります。

jpm\_crowded\_trades

relative value の役割
------------------

そこで導入されるのが **relative value** です。論文ではセクターについて、まず各セクターの **PBR（price-to-book ratio）** を計算し、それを

*   自セクターの過去10年平均で正規化し
*   さらに他セクター平均と比較する

ことで、**相対的に割高か割安か**を測っています。

jpm\_crowded\_trades

著者の考え方はこうです。

*   **centrality が高いが、relative value はまだ過度に高くない**  
    → crowding は起きているが、まだ上昇余地がある  
    → **bubble run-up（バブル上昇局面）**
*   **centrality が高く、relative value も高い**  
    → crowding も評価過熱も起きている  
    → 崩壊に入りやすい、あるいは sell-off 局面  
    → **bubble sell-off**

という整理です。relative value は、centrality が示す「集中」が、**上昇中の集中なのか、崩壊中の集中なのかを切り分ける補助指標**という位置づけです。

jpm\_crowded\_trades

有名バブルでの挙動
---------

論文ではまず、既知のバブル事例でこの2指標がどう動くかを見ています。

### 1\. テックバブル

7ページの Exhibit 2 では、

*   Panel A: テック株価格は大きく上昇してから急落
*   Panel B: centrality は上昇局面で上がり、崩壊局面でさらに跳ねる
*   Panel C: relative value は価格と似た形で上昇後に低下

となっています。つまり、**centrality がバブルの存在を示唆し、relative value が山の位置を示す**という読み方です。

jpm\_crowded\_trades

### 2\. 住宅バブル

同じく7ページの Exhibit 3 でも、REIT セクターで同様のパターンが示されています。住宅価格・REIT価格の上昇局面では centrality と relative value がともに上がり、崩壊局面では relative value が崩れ、centrality は高止まりまたはさらに上昇します。

jpm\_crowded\_trades

セクターローテーションへの応用
---------------

論文の実証パートでは、米国11セクターを対象に以下のようなルールを作っています。

*   centrality の「水準」ではなく、**過去3年平均との差を標準化した shift** を用いる
*   relative value もクロスセクションで比較する
*   各日、セクターを crowding と overvaluation でランク付けする
*   特定条件を満たすセクター群を翌日から保有する

特に条件付きパフォーマンスでは、セクターを4群に分けています。

1.  crowded でも overvalued でもない
2.  overvalued だが crowded ではない
3.  **crowded で、overvalued ではなく、さらに過去1年上昇している**  
    → bubble run-up
4.  **crowded かつ overvalued**  
    → bubble sell-off

その結果、1985–2017 の米国株セクターでは、

*   **crowded だが overvalued でない群**が最も高い超過収益
*   **crowded かつ overvalued 群**が最も低い超過収益

となり、run-up と sell-off の識別が有効だったと述べています。これは9ページの Exhibit 4 に示されています。

jpm\_crowded\_trades

さらに簡単な mean-variance 最適化ルールでポートフォリオを組むと、Exhibit 5 では

*   S&P500: 年率 11.3%、リスク 17.3%、比率 0.66
*   Sector Rotation Strategy: 年率 15.5%、リスク 15.6%、比率 1.00

と報告されています。つまり、**市場より高リターンかつ低リスク**だったというのが論文の主張です。

jpm\_crowded\_trades

ファクタータイミングへの応用
--------------

この方法はセクターだけでなく、**size, value, quality, low volatility** の4ファクターにも適用されています。著者は momentum を除外しています。その理由は、

*   モメンタムポートフォリオの銘柄入替が頻繁で crowding と価格の関係が追いにくい
*   momentum 自体が他ファクターの crowding の結果である可能性がある

ためです。

jpm\_crowded\_trades

各ファクターについて、S&P500ユニバースを10分位に分け、上位2デシルをそのファクターのエクスポージャーとみなしています。そして、

*   デシル間リターンの共分散構造から factor centrality を計算
*   各デシルの PBR 系列から factor relative value を計算

しています。方法論はセクター版の延長です。

jpm\_crowded\_trades

その結果、12ページの Exhibit 8 では、

*   **run-up と判定されたファクター群**は S&P500 対比で年率 **11.4%**
*   **sell-off と判定されたファクター群**は同 **2.4%**

となり、差は年率 9.0% です。さらに Exhibit 9 では、1995–2017 の期間で

*   S&P500: 8.6%
*   Static Factors: 11.6%
*   Factor Timing: 14.9%

とされており、**静的ファクター保有よりもタイミング戦略の方が高い成績**だったと報告されています。

jpm\_crowded\_trades

この論文の本質
-------

この論文の本質は、単なる「割高・割安」でもなく、単なる「ボラ高」でもなく、**市場の共分散構造の変化から crowding を読み取る**点にあります。かなり面白いのは、crowding をフローやポジションデータで直接測るのではなく、**価格系列から間接的に推定している**ことです。そこが実務的には扱いやすい一方で、後述の限界にもつながります。

jpm\_crowded\_trades

論文の強み
-----

強みは3つあります。

まず、**バブルの「存在」と「位相」を分けて考えている**ことです。centrality は存在、relative value は位相、という役割分担が明確です。

jpm\_crowded\_trades

次に、**セクターとファクターの両方に同じ考え方を適用している**ことです。単一事例の説明で終わらず、横展開できる枠組みにしています。

jpm\_crowded\_trades

最後に、**実装が比較的明瞭**です。PCA、過去窓、指数減衰、PBR 正規化、クロスセクションランクという構造なので、再現性があります。

jpm\_crowded\_trades

限界と注意点
------

一方で、実務で読むといくつか注意点があります。

第一に、**centrality は crowding の直接観測ではない**ことです。論文でもフローデータを直接使わず、価格挙動から crowding を推定していると明言しています。したがって、centrality 上昇が本当に crowding なのか、それとも単なるマクロショックやレジーム変化なのかは切り分けが必要です。

jpm\_crowded\_trades

第二に、**relative value として PBR を使っている点**です。セクターやファクターによっては、PBR が本質的なバリュエーション指標として弱い場合があります。特に quality や low vol では、PBR だけで過熱を測るのはやや粗いです。これは論文の簡潔さの代償です。

jpm\_crowded\_trades

第三に、**バックテストはかなり設計依存**です。上位3セクター、上位2ファクター、5年共分散、3年 z-score、1日ラグなど、パラメータ選択が結果に効いている可能性があります。論文は proof of concept としては説得的ですが、そのまま運用実装に落とすにはロバストネス確認が必要です。

jpm\_crowded\_trades

実務・研究上の読み替え
-----------

クオンツ的には、この論文は

*   **クラウディング指標**
*   **バリュエーション指標**
*   **クロスセクション・ローテーション**
*   **バブルの相転移検知**

を統合したものと読めます。

特に重要なのは、著者が「バブル」を壮大な歴史的大事件に限定せず、**ファンダメンタルズと釣り合わない有意な価格上昇・下落の反復現象**として広く捉えていることです。つまりこれは、伝統的なバブル予測論文というより、**crowding を使った横断面アロケーションモデル**に近いです。

jpm\_crowded\_trades

一言でまとめると
--------

この論文は、  
**「どこに資金が集まっているか」を centrality で、  
「その集中が過熱かどうか」を relative value で測り、  
両者の組み合わせでセクターやファクターの上昇局面と崩壊局面を識別しようとする研究**です。  
その結果、**crowded だがまだ過度に割高でない領域を買い、crowded かつ割高な領域を避ける**ことで、セクターローテーションとファクタータイミングの両方で有望な成績が得られた、というのが主張です。

jpm\_crowded\_trades

必要であれば次に、**この論文の数式を整理して、実装可能な形で順に分解**します。

## Response:
2026/4/6 20:46:14

> 思考時間: 5s

結論として、**その4系列だけでも「かなり近いもの」は実装できますが、論文そのものを厳密には再現できません**。可否を分けると次の通りです。

jpm\_crowded\_trades

何がそのまま適用できるか
------------

### 1\. centrality 側はかなり適用可能

論文の centrality は、セクター群の**リターン共分散行列**に対して PCA を行い、上位固有ベクトルへの寄与から計算します。したがって、**各セクターETFの total return 系列**があれば、少なくとも

*   共分散行列の推定
*   PCA
*   absorption ratio
*   centrality
*   centrality shift の z-score 化

は実装できます。さらに論文では、セクターの重要度を反映するために、**市場規模で重み付けしたリターン**を使っていますので、**market\_cap** が取得できるならこの点もかなり近く再現できます。

jpm\_crowded\_trades

ただし注意点として、論文の market weight は本来「セクターそのものの市場規模」です。ETFで代用する場合の market\_cap は多くの場合 **ETFのAUMやETF自体の時価総額** に近く、**基礎となるセクター全体の規模**とは違います。したがって、

*   厳密な論文再現ではない
*   ただし「市場参加者がどこに資金を集めているか」の proxy としては、むしろETFのAUM系は実務的に意味がある

という整理になります。

何が不足するか
-------

### 2\. relative value 側はそのままでは難しい

論文の relative value は、**price-to-book ratio（PBR）** を使って作っています。具体的には、

*   各セクターの PBR
*   それを自セクターの長期平均で正規化
*   さらに他セクターとの相対比較

という構造です。つまり必要なのは **価格だけでなく book value 側の情報** です。**px\_last だけでは PBR は作れない**ので、論文の relative value はそのままでは実装できません。

jpm\_crowded\_trades

したがって、あなたが持っている

*   total\_return
*   px\_last
*   market\_cap
*   turnover

だけだと、**centrality は可能、relative value は不足**です。

では「適応」はできるか
-----------

はい、できます。ただしそれは

*   **論文の厳密再現**  
    ではなく
*   **論文の思想をETFデータに合わせて再設計したバージョン**

になります。

### 適応の考え方

論文の本質は、

*   **centrality** で「資金集中・crowding」を捉える
*   **relative value** で「その crowding が上昇局面か、崩壊局面か」を切り分ける

ことです。

jpm\_crowded\_trades

このうち second leg の「relative value」を、ETFで取得可能な別指標に置き換えればよい、という考え方です。

あなたの保有データで作れる現実的な代替案
--------------------

### 案1: centrality + price extension

最も簡単なのは、relative value の代わりに **価格の行き過ぎ** を使う方法です。たとえば

*   価格の長期移動平均からの乖離
*   12M-1M などの累積超過上昇
*   rolling z-score of log price
*   52週高値からの距離

などです。

これは「valuation」ではなく**price extension**なので、論文の relative value とは別物です。ただし、  
**crowding が高く、かつ価格が過度に伸びているものは late stage の可能性が高い**  
という実務的な解釈はできます。

### 案2: centrality + turnover

**turnover** はかなり有用です。論文は crowding を価格構造から間接推定していますが、turnover が取れるなら、これは crowding のより直接的な proxy になります。

jpm\_crowded\_trades

たとえば、

*   centrality 高
*   turnover 高騰
*   価格も長期トレンドから大きく乖離

なら、**「過熱した crowded trade」** とみなしやすいです。逆に

*   centrality 高
*   turnover は中程度
*   price trend は強いが極端ではない

なら、**run-up 初期〜中期** と解釈しやすいです。

この場合は、relative value の代わりに  
**overextension / trading-intensity 指標**  
を使う設計になります。

### 案3: centrality + ETF premium/discount か NAV 系

もし sector ETF で **NAV** や premium/discount to NAV が取れるなら、これはかなり良い代替です。ETF市場での需給過熱を直接見られるからです。ただし、今挙げられた4変数には含まれていないので、現時点では使えません。

実務上の判定
------

厳密に言うと次の通りです。

### 適用可能な部分

*   **total\_return**: centrality 計算に必要
*   **market\_cap**: 論文の市場規模調整の代替に使える
*   **turnover**: 論文にはないが crowding proxy として有益
*   **px\_last**: price extension や trend filter には使える

### 適用困難な部分

*   **PBRベースの relative value**
*   したがって **論文の bubble run-up / sell-off の定義そのもの**

どの程度まで論文らしさを保てるか
----------------

3段階で言うと、

### A. 論文そのまま

必要:

*   total return
*   market cap
*   **book value あるいは PBR**

→ **現状の4変数だけでは不可**

### B. 論文にかなり近い実務版

必要:

*   total return
*   market cap
*   turnover
*   price extension 指標

→ **可能**

この場合は、

*   centrality = 論文準拠
*   relative value = valuation の代わりに price/turnover ベース proxy

になります。

### C. ETF需給版として再定義

必要:

*   total return
*   ETF AUM/market cap
*   turnover
*   premium/discount, flows, creation/redemption があればなお良い

→ むしろ**ETFの crowding 検知モデル**としては強いです。  
ただし論文の「ファンダメンタルズ対比のバブル」ではなく、**ETF需給の過熱検知**になります。

私の推奨
----

あなたのデータなら、まずは次の構成が最も自然です。

*   **centrality**: total\_return × market\_cap で論文準拠に近く構築
*   **overheating leg**: turnover z-score
*   **extension leg**: px\_last の長期乖離 or 12M-1M
*   **phase classification**:
    *   centrality 高 × extension 中程度 × turnover 中程度 → run-up
    *   centrality 高 × extension 高 × turnover 高 → overheating / sell-off risk
    *   centrality 低 → no bubble / neutral

この形なら、論文の「crowding と位相の切り分け」という思想を保ちながら、ETFデータで実装できます。

端的な答え
-----

*   **はい、適応はできます。**
*   ただし **total\_return + market\_cap で centrality は構築可能**でも、**px\_last だけでは論文の relative value は作れない**ので、**厳密再現ではありません**。
    jpm\_crowded\_trades
*   **turnover を使って crowding/過熱 proxy を補強し、px\_last から price extension を作る**のが現実的です。
*   その場合は、\*\*「論文のETF版アダプテーション」\*\*としては十分成立します。

必要なら次に、**この4変数だけで動く具体的な数式設計**を、run-up / sell-off 判定まで含めて提示します。

## Response:
2026/4/6 20:52:13

足りないのは、**book value 側の情報**です。

この論文の relative value は、単なる価格水準ではなく、各セクターの **price-to-book ratio（PBR）** を使って定義されています。手順は概ね、

1.  各セクターの PBR を計算する
2.  それを自セクターの過去10年平均で正規化する
3.  他セクター平均と比較して相対割高・割安を出す

というものです。したがって、**px\_last だけでは不十分**で、少なくとも **book value per share** か **PBRそのもの** が必要です。

jpm\_crowded\_trades

実務的には、次のいずれかがあれば計算できます。

*   **PBR 時系列そのもの**
*   **price と book value per share の時系列**
*   **price と aggregate book equity と shares outstanding**
*   セクターETFではなく基礎ユニバースから作るなら、**構成銘柄ごとの book value とウェイト**

逆に、今ある

*   total\_return
*   px\_last
*   market\_cap
*   turnover

だけでは、**relative value ではなく price-based 指標**しか作れません。market\_cap があっても、book equity がなければ **market-to-book** は出せません。

補足すると、ETFについて relative value をどう定義するかで必要データは少し変わります。

*   **論文に近い定義**をしたい  
    → セクターの **PBR** が必要
*   **ETF自体の需給過熱**を見たい  
    → NAV、premium/discount、flows などでも代替可能
*   **価格の行き過ぎ**だけ見たい  
    → px\_last だけで可。ただしこれは relative value ではありません

要するに、\*\*relative value のために足りないのは「簿価情報」またはそれに基づく valuation 指標」\*\*です。

jpm\_crowded\_trades

必要なら次に、**ETFしかない場合に PBR の代替として何を使うべきか**を、優先順位付きで整理します。

## Response:
2026/4/6 20:54:57

**Book equity** は、企業会計上の **純資産（株主資本に近い概念）** です。かなり大雑把に言うと、

**総資産 − 総負債 = book equity**

です。

株式評価の文脈では、企業の「帳簿上の持分価値」を表します。市場で付いている時価ではなく、**貸借対照表ベースの会計上の自己資本**です。

直感
--

ある会社について

*   資産が 1,000
*   負債が 700

なら、

*   純資産 = 300

で、この 300 が book equity に相当します。

market cap との違い
---------------

混同しやすいのは **market cap（時価総額）** との違いです。

*   **book equity**  
    → 会計帳簿上の株主価値
*   **market cap**  
    → 株価 × 発行株式数で決まる市場評価

たとえば、

*   book equity = 300
*   market cap = 900

なら、市場は帳簿価値の3倍で評価しているので、

*   **P/B = 900 / 300 = 3.0**

です。

PBRとの関係
-------

PBR は通常、

**Price / Book Value per Share**

ですが、同値的に

**Market Cap / Book Equity**

でも表せます。

したがって relative value を PBR ベースで作りたいなら、最低限どちらかが必要です。

*   株価と 1株当たり簿価
*   時価総額と book equity

ETF文脈での注意
---------

セクターETFに対して「book equity」というと、通常は**ETF自身の純資産**ではなく、**ETFの保有銘柄群の簿価ベース純資産を集計したもの**を意味するはずです。

つまり論文的に欲しいのは

*   ETFのAUMのような値ではなく
*   **基礎となるセクター企業群の簿価情報**

です。

ここが重要です。ETF自体にも純資産はありますが、それは投資信託・ETFビークルの純資産であって、**セクターのバリュエーション指標としての book equity とは別物**です。

実務上どう取るか
--------

実務では book equity は、企業ごとの財務データから取ります。セクター単位なら、

*   構成銘柄ごとの book equity を集計する
*   あるいはベンダー提供のセクター P/B をそのまま使う

のが普通です。

一言でいうと、\*\*book equity は「会社の帳簿上の自己資本」\*\*です。  
relative value を論文どおりに作るには、この情報か、それを要約した **PBR 時系列** が必要です。

## Response:
2026/4/6 20:56:04

> 思考時間: 2 ～ 3 秒

はい。  
**必要データが取得できるなら、この論文の手法はかなり素直に再現できます。**  
以下では、**論文の定義にできるだけ忠実**に、**セクター版**を中心に、必要なら**ファクター版**へ拡張できる形で、実装手順を順番に整理します。

jpm\_crowded\_trades

* * *

1\. 論文の再現で何を作るのか
================

論文の骨格は非常に明確で、やることは大きく4段階です。

1.  **Centrality を計算する**  
    → 「どのセクターに crowding が起きているか」を測る。
    jpm\_crowded\_trades
2.  **Relative Value を計算する**  
    → その crowding が、まだ上昇局面なのか、すでに過熱・崩壊局面なのかを切り分ける。
    jpm\_crowded\_trades
3.  **Bubble run-up / sell-off を分類する**  
    → crowded かつ割高でないものを run-up、crowded かつ割高なものを sell-off とみなす。
    jpm\_crowded\_trades
4.  **分類結果を使ってポートフォリオを組む**  
    → セクターローテーション、あるいはファクタータイミング戦略を作る。
    jpm\_crowded\_trades

* * *

2\. 必要データ
=========

セクター版で必要なもの
-----------

論文に忠実に再現するなら、各セクターについて日次または各時点で少なくとも以下が必要です。

*   **total return series**
*   **market capitalization**
*   **price-to-book ratio（PBR）**  
    もしくは PBR を作れるだけの
    *   price
    *   book value per share  
        あるいは
    *   market cap
    *   book equity

です。

jpm\_crowded\_trades

### データの意味

*   **total return**  
    → centrality 計算用のリターン系列
*   **market cap**  
    → セクター規模を反映するため、リターンに重みを掛ける
*   **PBR**  
    → relative value の計算に使う

セクターETFで代用する場合
--------------

論文は本来「セクター指数」ベースですが、セクターETFでもかなり近い再現は可能です。  
ただし、その場合は

*   total return: ETFトータルリターン
*   market cap: ETFのAUMやETF時価総額ではなく、できれば**基礎セクター全体の市場規模**
*   PBR: ETF保有銘柄ベースの aggregate PBR

が望ましいです。

ETFしかない場合でも再現はできますが、**論文再現**というより**ETF実務版アダプテーション**になります。

* * *

3\. Centrality の再現方法
====================

論文の centrality は、**共分散構造の中で、そのセクターがどれだけ中心的か**を測る指標です。ベースは PCA です。

jpm\_crowded\_trades

3.1 まず吸収比率 Absorption Ratio
---------------------------

論文ではまず absorption ratio を定義しています。  
セクター数を  $N$ 、上位で使う固有ベクトル数を  $n$  とすると、

$$
AR = \frac{\sum_{i=1}^{n}\sigma^2_{E_i}}{\sum_{j=1}^{N}\sigma^2_{A_j}}
$$

です。ここで

*    $\sigma^2_{E_i}$ : 第  $i$  主成分の分散
*    $\sigma^2_{A_j}$ : 第  $j$  セクターの分散

です。これは「市場全体の分散のうち、主要な共通因子がどれだけ吸収しているか」です。

jpm\_crowded\_trades

3.2 Centrality の定義
------------------

各セクター  $i$  の centrality  $C_i$  は、上位  $n$  本の固有ベクトルに対する当該セクターの絶対荷重を、各固有ベクトルの重要度で重み付けして合成したものです。論文の式の趣旨は次です。

jpm\_crowded\_trades

$$
C_i = \sum_{j=1}^{n} \left( \frac{AR_j}{\sum_{k=1}^{n} AR_k} \right) |EV_{i,j}|
$$

ここで

*    $EV_{i,j}$ : 第  $j$  固有ベクトルにおけるセクター  $i$  の荷重の絶対値
*    $AR_j$ : 第  $j$  固有ベクトルが説明する分散寄与

です。

直感としては、**主要な共通変動を作っている固有モードに強く載っているセクターほど centrality が高い**、ということです。

* * *

4\. Centrality の具体的な計算フロー
=========================

論文の sector centrality の計算手順はかなり具体的です。ほぼそのまま実装できます。

jpm\_crowded\_trades

Step 1: 2年分の日次リターンを用意
---------------------

各日  $t$  で、直近2年のセクター日次 total return を取ります。  
セクター数を  $N$ 、窓長を  $L$  日とすると、行列は

$$
R_t \in \mathbb{R}^{L \times N}
$$

です。

Step 2: 市場規模で重み付け
-----------------

論文では、各セクターの重要度を反映するために、**前日の market-cap weight の平方根**を各セクターのリターンに掛けています。

jpm\_crowded\_trades

$$
\tilde r_{s,i} = r_{s,i} \cdot \sqrt{w_{s-1,i}}
$$

ここで  $w_{s-1,i}$  は前日時点の市場規模ウェイトです。

論文が平方根を使う理由は、**大きいセクターほどつながりやすいが、その効果は線形ではなく飽和すると考えるから**です。

jpm\_crowded\_trades

Step 3: 指数減衰を掛ける
----------------

直近データを重視するため、**半減期1年**の指数ウェイトを使います。

jpm\_crowded\_trades

たとえば過去  $k$  日前の観測に対し、

$$
\omega_k = 2^{-k/H}
$$

で、 $H$  は半減期（約252営業日）です。

Step 4: 共分散行列を推定
----------------

加重済みリターンから加重共分散行列を推定します。

$$
\Sigma_t = \mathrm{Cov}_\omega(\tilde R_t)
$$

Step 5: PCA
-----------

 $\Sigma_t$  を固有分解します。

$$
\Sigma_t = Q_t \Lambda_t Q_t^\top
$$
*    $Q_t$ : 固有ベクトル
*    $\Lambda_t$ : 固有値対角行列

Step 6: 上位  $n=2$  本で centrality を作る
------------------------------------

論文の sector 実装では、**上位2本の固有ベクトル**を使っています。

jpm\_crowded\_trades

したがって、各日  $t$  で各セクター  $i$  に centrality  $C_{t,i}$  が付きます。

* * *

5\. Centrality Shift の作り方
=========================

論文は centrality の「水準」をそのまま使っていません。  
代わりに、**過去3年平均との差の標準化**を使っています。これがかなり重要です。

jpm\_crowded\_trades

$$
Z^{(C)}_{t,i} = \frac{ C_{t,i} - \mu^{(3Y)}_{t-1,i} }{ \sigma^{(3Y)}_{t-1,i} }
$$

ここで

*    $\mu^{(3Y)}_{t-1,i}$ : セクター  $i$  の過去3年平均 centrality
*    $\sigma^{(3Y)}_{t-1,i}$ : セクター  $i$  の過去3年標準偏差

です。

この  $Z^{(C)}$  が、論文でいう **standardized shift of centrality** です。  
以後、これを **crowding score** とみなします。

jpm\_crowded\_trades

* * *

6\. Relative Value の再現方法
========================

論文の relative value は、**PBR の相対比較**です。これもそのまま作れます。

jpm\_crowded\_trades

Step 1: 各セクターの PBR を取得
----------------------

各日  $t$  で、各セクター  $i$  の price-to-book ratio  $PB_{t,i}$  を用意します。

Step 2: 自セクターの長期平均で正規化
----------------------

各セクターは構造的に PBR 水準が異なるので、そのまま比較しません。  
各セクターごとに、過去10年平均で割ります。論文では初期部分は5年からスタートして10年に伸ばしています。

jpm\_crowded\_trades

$$
\widetilde{PB}_{t,i} = \frac{PB_{t,i}}{\overline{PB}^{(10Y)}_{t-1,i}}
$$

Step 3: 他セクター平均と比較
------------------

その上で、他セクターの平均 normalized PB と比べます。

$$
RV_{t,i} = \frac{ \widetilde{PB}_{t,i} }{ \frac{1}{N-1}\sum_{j\neq i}\widetilde{PB}_{t,j} }
$$

これが relative value です。  
 $RV_{t,i} > 1$  なら、相対的に割高寄りです。

jpm\_crowded\_trades

* * *

7\. セクター分類の再現
=============

論文は毎日、各セクターを **crowding** と **relative value** でランク付けして分類します。

jpm\_crowded\_trades

Step 1: 横断面ランク
--------------

各日  $t$  に、

*    $Z^{(C)}_{t,i}$  の高い順
*    $RV_{t,i}$  の高い順

でセクターを並べます。

Step 2: top 3 を定義
-----------------

米国11セクターなら、論文は **上位3セクター**を crowded / overvalued と定義しています。

jpm\_crowded\_trades

*   crowded: centrality shift が上位3位以内
*   overvalued: relative value が上位3位以内

Step 3: 4分類
-----------

論文では以下の4群に分けます。

jpm\_crowded\_trades

### (a) no bubble

*   not top 3 crowded
*   not top 3 overvalued

### (b) no bubble

*   not top 3 crowded
*   top 3 overvalued

### (c) bubble run-up

*   top 3 crowded
*   not top 3 overvalued
*   **過去1年価格上昇**あり

この「過去1年上昇」は、run-up と late sell-off を切り分けるための補助条件です。

jpm\_crowded\_trades

### (d) bubble sell-off

*   top 3 crowded
*   top 3 overvalued

* * *

8\. Conditional Performance の再現
===============================

まず論文は、この分類が本当に意味を持つかを見るために、条件付きパフォーマンスを計算しています。

jpm\_crowded\_trades

やることは単純で、各日  $t$  に各分類に該当するセクターを等ウェイトで持ち、**1日ラグを置いて翌日リターン**を見ます。

実装イメージ
------

各群  $g$  について、日  $t$  の対象セクター集合を  $S_t^{(g)}$  とすると、

$$
w_{t,i}^{(g)} = \begin{cases} 1/|S_t^{(g)}| & i \in S_t^{(g)} \\ 0 & \text{otherwise} \end{cases}
$$

そして翌日リターンは

$$
r_{t+1}^{(g)} = \sum_i w_{t,i}^{(g)} r_{t+1,i}
$$

です。

論文ではこの結果として、

*   crowded だが overvalued でないセクター群
*   crowded かつ overvalued なセクター群

の間に大きな差が出ると示しています。

jpm\_crowded\_trades

* * *

9\. セクターローテーション戦略の再現
====================

条件付きパフォーマンスが確認できたら、次は実際のポートフォリオです。

論文の trading rule は、見た目以上にシンプルです。

jpm\_crowded\_trades

Step 1: 期待リターンをルールベースで付与
------------------------

各日  $t$ 、各セクター  $i$  に対し

$$
\mu_{t,i} = \begin{cases} +5\% & \text{run-up に分類} \\ -5\% & \text{sell-off に分類} \\ 0 & \text{otherwise} \end{cases}
$$

という**仮の expected return**を置きます。

jpm\_crowded\_trades

これは予測モデルではなく、分類結果を mean-variance 最適化に入れるためのルール化です。

Step 2: 共分散行列を推定
----------------

過去5年の日次リターンから annualized covariance を推定します。

jpm\_crowded\_trades

$$
\Sigma^{(5Y)}_t
$$

Step 3: Long-only mean-variance 最適化
-----------------------------------

リスク回避係数  $\lambda = 1$  として、たとえば

$$
\max_w \quad \mu_t^\top w - \frac{\lambda}{2} w^\top \Sigma_t w
$$

subject to

$$
w_i \ge 0,\quad \sum_i w_i = 1
$$

を解きます。

jpm\_crowded\_trades

Step 4: 売買回転を抑えるため四半期平均
-----------------------

論文では turnover 抑制のため、**過去1四半期の最適ウェイト平均**を実際の保有ウェイトにしています。

jpm\_crowded\_trades

$$
\bar w_t = \frac{1}{Q}\sum_{s=t-Q+1}^{t} w_s^\star
$$

Step 5: 1日ラグで翌日リターン
-------------------

実運用可能性のため、**1日 implementation lag** を置いて翌日収益を計上します。

jpm\_crowded\_trades

$$
r_{t+1}^{port} = \bar w_t^\top r_{t+1}
$$

* * *

10\. バックテスト実装での注意点
==================

再現で重要なのは、**見た目の式より時系列アラインメント**です。

10.1 ルックアヘッド禁止
--------------

各日  $t$  の判定に使うものは、すべて  $t$  までに観測済みの情報だけにします。

*   centrality:  $t$  までの過去2年
*   centrality shift の平均・標準偏差:  $t-1$  まで
*   relative value の10年平均:  $t-1$  まで
*   過去1年上昇判定:  $t$  時点までの価格

そして実際の保有は ** $t+1$ ** です。

jpm\_crowded\_trades

10.2 初期期間の欠損
------------

必要窓が長いので、再現開始にはかなりの履歴が必要です。

*   centrality: 2年
*   centrality shift: さらに3年
*   relative value: 最大10年

したがって full fidelity でやるなら、**少なくとも10年以上の事前履歴**が必要です。

10.3 セクター数
----------

論文は米国11セクターを使っています。ETF版で 9～12 本程度でも動きますが、あまり少ないと PCA 構造が不安定になります。

10.4 market cap の意味
-------------------

論文の market cap は、セクターそのものの市場規模です。ETFのAUMで代用すると、「市場規模」ではなく「投資資金の集中」をより強く反映します。これは悪くありませんが、厳密再現ではありません。

* * *

11\. 数式ベースでの実装全体像
=================

まとめると、各日  $t$  で以下を順に行います。

Input
-----

*   セクター total return  $r_{t,i}$ 
*   セクター market cap  $MC_{t,i}$ 
*   セクター PBR  $PB_{t,i}$ 

11.1 重み付きリターン
-------------

$$
w^{MC}_{t,i} = \frac{MC_{t,i}}{\sum_j MC_{t,j}}
$$
 
$$
\tilde r_{s,i} = r_{s,i}\sqrt{w^{MC}_{s-1,i}}
$$

11.2 Covariance and PCA
-----------------------

$$
\Sigma_t = \mathrm{Cov}_\omega(\tilde R_t)
$$
 
$$
\Sigma_t = Q_t \Lambda_t Q_t^\top
$$

11.3 Centrality
---------------

$$
C_{t,i} = \sum_{j=1}^{2} \left( \frac{\lambda_{t,j}}{\lambda_{t,1}+\lambda_{t,2}} \right) |q_{t,i,j}|
$$

11.4 Centrality Shift
---------------------

$$
Z^{(C)}_{t,i} = \frac{ C_{t,i} - \mu^{(3Y)}_{t-1,i} }{ \sigma^{(3Y)}_{t-1,i} }
$$

11.5 Relative Value
-------------------

$$
\widetilde{PB}_{t,i} = \frac{PB_{t,i}}{\overline{PB}^{(10Y)}_{t-1,i}}
$$
 
$$
RV_{t,i} = \frac{ \widetilde{PB}_{t,i} }{ \frac{1}{N-1}\sum_{j\neq i}\widetilde{PB}_{t,j} }
$$

11.6 分類
-------

*   crowded:  $Z^{(C)}$  上位3
*   overvalued:  $RV$  上位3
*   run-up: crowded かつ not overvalued かつ 1年上昇
*   sell-off: crowded かつ overvalued

11.7 Expected return mapping
----------------------------

$$
\mu_{t,i} = \begin{cases} +0.05 & run\text{-}up \\ -0.05 & sell\text{-}off \\ 0 & otherwise \end{cases}
$$

11.8 Mean-variance portfolio
----------------------------

$$
\max_w \mu_t^\top w - \frac{1}{2} w^\top \Sigma^{(5Y)}_t w
$$

s.t.

$$
w_i \ge 0,\quad \sum_i w_i = 1
$$

11.9 Smoothing and lag
----------------------

$$
\bar w_t = \text{quarter-average of } w_t^\star
$$
 
$$
r_{t+1}^{port} = \bar w_t^\top r_{t+1}
$$

これで論文の sector rotation はほぼ再現できます。

jpm\_crowded\_trades

* * *

12\. ファクター版を再現するには
==================

論文後半は、これをファクターにも適用しています。基本思想は同じです。

jpm\_crowded\_trades

対象ファクター
-------

*   size
*   value
*   quality
*   low volatility

momentum は除外です。

jpm\_crowded\_trades

ファクター定義
-------

S&P500 の各銘柄を属性で10分位に分け、**上位2デシルの時価総額加重平均**をそのファクターとします。

jpm\_crowded\_trades

Factor centrality
-----------------

各ファクターごとに、10デシルポートフォリオの過去2年日次リターンから PCA をかけ、上位2固有ベクトルを使います。  
セクター版と違い、**市場規模重みは掛けません**。

jpm\_crowded\_trades

Factor relative value
---------------------

各デシルの PBR を出し、過去10年平均で正規化し、他デシルとの相対比較をします。  
その後、**上位2デシルの時価総額加重平均**で factor-level relative value を作ります。

jpm\_crowded\_trades

分類
--

4ファクターの中で

*   crowded 上位2
*   overvalued 上位2

を使って run-up / sell-off を判定します。

jpm\_crowded\_trades

* * *

13\. 再現時にまず確認すべきこと
==================

再現を始める前に、次の3点を決めると実装がぶれません。

13.1 セクター単位か ETF単位か
-------------------

*   論文忠実再現ならセクター指数
*   実務実装なら sector ETF

13.2 PBRの定義
-----------

*   ベンダー提供の sector P/B を使うか
*   保有銘柄から集計するか

13.3 market cap の定義
-------------------

*   セクター全体時価総額
*   ETF AUM
*   ETF market cap

この3つで「論文再現」か「実務版」かが決まります。

* * *

14\. 実務的な解釈
===========

この手法は、見方を変えると

*   **centrality** = 共分散構造から見た crowding
*   **relative value** = バリュエーション過熱度
*   **cross-sectional ranking** = 相対比較による regime classification
*   **mean-variance optimizer** = シグナルのポートフォリオ化

です。

つまり、単なるバブル検知というより、  
**“crowding × valuation” による横断面ローテーション戦略**  
として理解すると実装しやすいです。

jpm\_crowded\_trades

* * *

15\. 端的な実装レシピ
=============

最短で書くと、再現手順は以下です。

1.  11セクターの daily total return を並べる
2.  各日の sector market cap weight を作る
3.  リターンに  $\sqrt{\text{market cap weight}}$  を掛ける
4.  2年窓・半減期1年で加重共分散を作る
5.  PCA して上位2PCから centrality を作る
6.  過去3年平均・標準偏差で centrality shift を z-score 化する
7.  各セクターの PBR を過去10年平均で正規化する
8.  他セクター平均で割って relative value を作る
9.  crowded 上位3、overvalued 上位3を決める
10.  crowded かつ not overvalued かつ 1年上昇 → run-up
11.  crowded かつ overvalued → sell-off
12.  run-up に +5%、sell-off に -5%、それ以外 0% の expected return を付与
13.  過去5年共分散で long-only mean-variance 最適化
14.  ウェイトを四半期平均して 1日ラグでバックテスト

これで論文の中核は再現できます。

jpm\_crowded\_trades

* * *

次に必要なら、**この論文をそのまま Python/pandas で実装するための疑似コード**を、関数単位で分解して示します。

## Response:
2026/4/6 21:02:54

> 思考時間: 2 ～ 3 秒

では、**論文手法をそのまま Python / pandas で実装できる粒度**まで落として、  
**セクター版の疑似コードと実装設計**を示します。  
論文の流れに沿って、**データ → centrality → relative value → run-up / sell-off 判定 → 最適化 → バックテスト**の順で書きます。

jpm\_crowded\_trades

* * *

全体設計
====

最小構成なら、処理は次の関数に分けるのが自然です。

```
load_inputs()
compute_market_cap_weights()
compute_weighted_returns()
compute_ewm_cov()
compute_centrality()
compute_centrality_shift()
compute_relative_value()
classify_states()
build_expected_returns()
solve_mvo_weights()
smooth_weights()
run_backtest()
evaluate_results()
```

入出力は基本的に **DataFrame を時系列 index × セクター columns** で統一すると扱いやすいです。

* * *

1\. 入力データの形
===========

最低限、次の 3 つを用意します。

```
ret_tr      # daily total return, shape=(T, N)
market_cap  # daily market cap,   shape=(T, N)
pb_ratio    # daily price-to-book ratio, shape=(T, N)
```

例:

```
import pandas as pd
import numpy as np

# index: daily datetime
# columns: ["XLB", "XLE", ..., "XLU"] など
ret_tr = pd.DataFrame(...)
market_cap = pd.DataFrame(...)
pb_ratio = pd.DataFrame(...)
```

想定:

*   `ret_tr` は日次リターン（小数）
*   `market_cap` は各日のセクター時価総額
*   `pb_ratio` は各日のセクターPBR

* * *

2\. market cap weight の計算
=========================

論文では、リターンに **前日の market-cap weight の平方根**を掛けます。

jpm\_crowded\_trades

```
def compute_market_cap_weights(market_cap: pd.DataFrame) -> pd.DataFrame:
    w = market_cap.div(market_cap.sum(axis=1), axis=0)
    return w
```

* * *

3\. centrality 用の weighted return
=================================

```
def compute_weighted_returns(
    ret_tr: pd.DataFrame,
    market_cap_weights: pd.DataFrame
) -> pd.DataFrame:
    # 前日の market-cap weight を使用
    sqrt_w = np.sqrt(market_cap_weights.shift(1))
    ret_w = ret_tr * sqrt_w
    return ret_w
```

* * *

4\. 指数減衰付き共分散の計算
================

論文は

*   **2年窓**
*   **半減期1年**  
    で共分散を作っています。
    jpm\_crowded\_trades

pandas の標準機能だけで厳密再現しにくいので、ここは関数化して rolling で回すのが分かりやすいです。

4.1 補助: 指数ウェイト
--------------

```
def make_exp_weights(window: int, half_life: int) -> np.ndarray:
    # 古い順 -> 新しい順
    k = np.arange(window)[::-1]
    w = 0.5 ** (k / half_life)
    w = w / w.sum()
    return w
```

4.2 加重共分散
---------

```
def weighted_cov(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    """
    x: shape=(L, N)
    w: shape=(L,)
    """
    w = w / w.sum()
    mu = np.sum(x * w[:, None], axis=0)
    xc = x - mu
    cov = (xc * w[:, None]).T @ xc
    return cov
```

* * *

5\. centrality の計算
==================

論文の centrality は、PCA の上位2固有ベクトルに対する絶対荷重を、各固有値で重み付けして作ります。

jpm\_crowded\_trades

```
def compute_centrality_from_cov(cov: np.ndarray, n_top: int = 2) -> np.ndarray:
    """
    cov: shape=(N, N)
    return: centrality vector shape=(N,)
    """
    eigvals, eigvecs = np.linalg.eigh(cov)

    # 昇順で返るので降順へ
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]

    top_vals = eigvals[:n_top]
    top_vecs = eigvecs[:, :n_top]

    # 論文の趣旨に沿って、上位固有ベクトルの寄与率で重み付け
    weights_pc = top_vals / top_vals.sum()

    # 各セクターの絶対荷重の重み付き和
    centrality = np.sum(np.abs(top_vecs) * weights_pc[None, :], axis=1)
    return centrality
```

* * *

6\. 日次の centrality series を作る
=============================

ここが main loop の第一段階です。

```
def compute_centrality_series(
    ret_w: pd.DataFrame,
    lookback_days: int = 252 * 2,
    half_life_days: int = 252,
    n_top: int = 2
) -> pd.DataFrame:
    dates = ret_w.index
    cols = ret_w.columns
    out = pd.DataFrame(index=dates, columns=cols, dtype=float)

    exp_w = make_exp_weights(lookback_days, half_life_days)

    for t in range(lookback_days - 1, len(dates)):
        x = ret_w.iloc[t - lookback_days + 1:t + 1].values

        # 欠損がある場合は単純に skip でもよい
        if np.isnan(x).any():
            continue

        cov = weighted_cov(x, exp_w)
        c = compute_centrality_from_cov(cov, n_top=n_top)
        out.iloc[t] = c

    return out
```

* * *

7\. centrality shift の計算
========================

論文では centrality の level ではなく、**過去3年平均との差の z-score** を使います。

jpm\_crowded\_trades

```
def compute_centrality_shift(
    centrality: pd.DataFrame,
    lookback_days: int = 252 * 3
) -> pd.DataFrame:
    mean_ = centrality.shift(1).rolling(lookback_days, min_periods=lookback_days).mean()
    std_ = centrality.shift(1).rolling(lookback_days, min_periods=lookback_days).std()
    z = (centrality - mean_) / std_
    return z
```

* * *

8\. relative value の計算
======================

論文の定義は次です。

jpm\_crowded\_trades

1.  各セクターの PBR
2.  自セクターの過去10年平均で割る
3.  他セクター平均で割る

```
def compute_relative_value(
    pb_ratio: pd.DataFrame,
    lookback_days: int = 252 * 10,
    min_periods: int = 252 * 5
) -> pd.DataFrame:
    # 自セクターの長期平均で正規化
    pb_mean = pb_ratio.shift(1).rolling(lookback_days, min_periods=min_periods).mean()
    pb_norm = pb_ratio / pb_mean

    # 他セクター平均で割る
    cross_sum = pb_norm.sum(axis=1)
    n = pb_norm.shape[1]
    others_mean = pd.DataFrame(
        {
            col: (cross_sum - pb_norm[col]) / (n - 1)
            for col in pb_norm.columns
        },
        index=pb_norm.index
    )
    rv = pb_norm / others_mean
    return rv
```

* * *

9\. 過去1年上昇条件
============

論文の run-up 判定では、  
**crowded かつ not overvalued** に加えて **過去1年上昇** を条件にしています。

jpm\_crowded\_trades

price level が必要なので、トータルリターン指数を作るのが自然です。

```
def build_total_return_index(ret_tr: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    tri = base * (1.0 + ret_tr).cumprod()
    return tri
```

```
def compute_trailing_1y_return(tri: pd.DataFrame, lookback_days: int = 252) -> pd.DataFrame:
    mom_1y = tri / tri.shift(lookback_days) - 1.0
    return mom_1y
```

* * *

10\. crowded / overvalued の横断面判定
================================

論文の米国セクター版では **top 3** を使っています。

jpm\_crowded\_trades

```
def top_k_mask(df: pd.DataFrame, k: int) -> pd.DataFrame:
    """
    各日ごとに上位k列をTrueにする
    """
    out = pd.DataFrame(False, index=df.index, columns=df.columns)
    for dt in df.index:
        row = df.loc[dt]
        row = row.dropna()
        if len(row) < k:
            continue
        top_cols = row.nlargest(k).index
        out.loc[dt, top_cols] = True
    return out
```

* * *

11\. state classification
=========================

論文定義に沿って 4 分類します。

jpm\_crowded\_trades

```
def classify_states(
    centrality_shift: pd.DataFrame,
    relative_value: pd.DataFrame,
    trailing_1y_return: pd.DataFrame,
    top_k: int = 3
):
    crowded = top_k_mask(centrality_shift, k=top_k)
    overvalued = top_k_mask(relative_value, k=top_k)
    up_1y = trailing_1y_return > 0.0

    bubble_runup = crowded & (~overvalued) & up_1y
    bubble_selloff = crowded & overvalued

    no_bubble_1 = (~crowded) & (~overvalued)
    no_bubble_2 = (~crowded) & overvalued

    return {
        "crowded": crowded,
        "overvalued": overvalued,
        "bubble_runup": bubble_runup,
        "bubble_selloff": bubble_selloff,
        "no_bubble_1": no_bubble_1,
        "no_bubble_2": no_bubble_2,
    }
```

* * *

12\. 条件付きパフォーマンスの計算
===================

まずは論文 Exhibit 4 相当の検証です。

jpm\_crowded\_trades

```
def equal_weight_returns_from_mask(
    ret_tr: pd.DataFrame,
    mask: pd.DataFrame,
    lag: int = 1
) -> pd.Series:
    """
    mask[t]で選ばれたセクターを、t+lag のリターンで評価
    """
    w = mask.astype(float)
    w = w.div(w.sum(axis=1), axis=0)
    w = w.fillna(0.0)

    port_ret = (w.shift(lag) * ret_tr).sum(axis=1)
    return port_ret
```

使用例:

```
states = classify_states(cs_z, rv, mom_1y, top_k=3)

ret_runup = equal_weight_returns_from_mask(ret_tr, states["bubble_runup"], lag=1)
ret_selloff = equal_weight_returns_from_mask(ret_tr, states["bubble_selloff"], lag=1)
```

* * *

13\. expected return の構築
========================

論文の trading rule では、

*   run-up → +5%
*   sell-off → -5%
*   それ以外 → 0%

を expected return として与えます。

jpm\_crowded\_trades

```
def build_expected_returns(
    bubble_runup: pd.DataFrame,
    bubble_selloff: pd.DataFrame,
    pos_mu: float = 0.05,
    neg_mu: float = -0.05
) -> pd.DataFrame:
    mu = pd.DataFrame(0.0, index=bubble_runup.index, columns=bubble_runup.columns)
    mu[bubble_runup] = pos_mu
    mu[bubble_selloff] = neg_mu
    return mu
```

* * *

14\. mean-variance optimization
===============================

論文は long-only, risk aversion = 1.0 です。

jpm\_crowded\_trades

最も簡単には `scipy.optimize.minimize` を使います。

```
from scipy.optimize import minimize

def solve_long_only_mvo(mu: np.ndarray, cov: np.ndarray, risk_aversion: float = 1.0) -> np.ndarray:
    n = len(mu)

    def objective(w):
        return -(mu @ w - 0.5 * risk_aversion * (w @ cov @ w))

    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, 1.0) for _ in range(n)]
    x0 = np.repeat(1.0 / n, n)

    res = minimize(objective, x0=x0, method="SLSQP", bounds=bounds, constraints=cons)
    if not res.success:
        return x0
    return res.x
```

* * *

15\. 5年共分散で最適ウェイトを日次計算
======================

```
def compute_mvo_weights_series(
    ret_tr: pd.DataFrame,
    mu_df: pd.DataFrame,
    cov_lookback_days: int = 252 * 5,
    risk_aversion: float = 1.0
) -> pd.DataFrame:
    dates = ret_tr.index
    cols = ret_tr.columns
    w_opt = pd.DataFrame(index=dates, columns=cols, dtype=float)

    for t in range(cov_lookback_days - 1, len(dates)):
        hist = ret_tr.iloc[t - cov_lookback_days + 1:t + 1]
        if hist.isna().any().any():
            continue

        cov = hist.cov().values * 252.0  # annualized
        mu = mu_df.iloc[t].values

        w = solve_long_only_mvo(mu=mu, cov=cov, risk_aversion=risk_aversion)
        w_opt.iloc[t] = w

    return w_opt
```

* * *

16\. 四半期平均でウェイト平滑化
==================

論文では turnover 抑制のため、**過去1四半期の平均ウェイト**を使います。

jpm\_crowded\_trades

```
def smooth_weights(
    w_opt: pd.DataFrame,
    window_days: int = 63
) -> pd.DataFrame:
    w_sm = w_opt.rolling(window_days, min_periods=1).mean()
    return w_sm
```

* * *

17\. バックテスト本体
=============

ここまでそろえば、日次 for ループで一連を流せます。  
ただし計算量を考えると、まずは各コンポーネントを作って最後に結合する方が見通しは良いです。

17.1 一括実行版
----------

```
def run_sector_rotation_pipeline(
    ret_tr: pd.DataFrame,
    market_cap: pd.DataFrame,
    pb_ratio: pd.DataFrame,
):
    # 1) market-cap weight
    mc_w = compute_market_cap_weights(market_cap)

    # 2) centrality
    ret_w = compute_weighted_returns(ret_tr, mc_w)
    centrality = compute_centrality_series(
        ret_w=ret_w,
        lookback_days=252 * 2,
        half_life_days=252,
        n_top=2,
    )
    cs_z = compute_centrality_shift(centrality, lookback_days=252 * 3)

    # 3) relative value
    rv = compute_relative_value(
        pb_ratio=pb_ratio,
        lookback_days=252 * 10,
        min_periods=252 * 5,
    )

    # 4) past-1y up condition
    tri = build_total_return_index(ret_tr)
    mom_1y = compute_trailing_1y_return(tri, lookback_days=252)

    # 5) state classification
    states = classify_states(
        centrality_shift=cs_z,
        relative_value=rv,
        trailing_1y_return=mom_1y,
        top_k=3,
    )

    # 6) conditional returns
    ret_runup = equal_weight_returns_from_mask(ret_tr, states["bubble_runup"], lag=1)
    ret_selloff = equal_weight_returns_from_mask(ret_tr, states["bubble_selloff"], lag=1)

    # 7) expected returns
    mu_df = build_expected_returns(
        bubble_runup=states["bubble_runup"],
        bubble_selloff=states["bubble_selloff"],
        pos_mu=0.05,
        neg_mu=-0.05,
    )

    # 8) MVO weights
    w_opt = compute_mvo_weights_series(
        ret_tr=ret_tr,
        mu_df=mu_df,
        cov_lookback_days=252 * 5,
        risk_aversion=1.0,
    )

    # 9) smooth
    w_hold = smooth_weights(w_opt, window_days=63)

    # 10) portfolio return with 1-day lag
    port_ret = (w_hold.shift(1) * ret_tr).sum(axis=1)

    return {
        "market_cap_weights": mc_w,
        "centrality": centrality,
        "centrality_shift": cs_z,
        "relative_value": rv,
        "tri": tri,
        "mom_1y": mom_1y,
        "states": states,
        "ret_runup": ret_runup,
        "ret_selloff": ret_selloff,
        "mu_df": mu_df,
        "w_opt": w_opt,
        "w_hold": w_hold,
        "port_ret": port_ret,
    }
```

* * *

18\. ウォークフォワードとして見ると何を毎日更新しているか
===============================

あなたの関心に合わせて、これを **for ループのウォークフォワード** として言い換えると、各日  $t$  でやることは次です。

```
for t in dates:
    # A. t までの過去2年で centrality
    # B. t までの過去3年履歴で centrality shift
    # C. t までの過去10年履歴で relative value
    # D. t 時点で crowded / overvalued / run-up / sell-off 判定
    # E. その判定を +5 / -5 / 0 に写像
    # F. t までの過去5年共分散で MVO
    # G. 過去63営業日の最適ウェイト平均を保有ウェイトとする
    # H. t+1 の日次リターンを記録
```

つまり、**完全に leakage-free な日次ウォークフォワード**で再現できます。

jpm\_crowded\_trades

* * *

19\. 評価指標
=========

最低限、次を出せば論文の主張に対応しやすいです。

```
def performance_summary(ret: pd.Series, ann_factor: int = 252) -> pd.Series:
    ret = ret.dropna()
    if len(ret) == 0:
        return pd.Series(dtype=float)

    nav = (1 + ret).cumprod()
    years = len(ret) / ann_factor
    cagr = nav.iloc[-1] ** (1 / years) - 1 if years > 0 else np.nan
    vol = ret.std() * np.sqrt(ann_factor)
    sharpe = ret.mean() / ret.std() * np.sqrt(ann_factor) if ret.std() > 0 else np.nan
    dd = nav / nav.cummax() - 1
    maxdd = dd.min()

    return pd.Series({
        "CAGR": cagr,
        "AnnVol": vol,
        "Sharpe": sharpe,
        "MaxDD": maxdd,
    })
```

比較例:

```
summary_port = performance_summary(results["port_ret"])
summary_runup = performance_summary(results["ret_runup"])
summary_selloff = performance_summary(results["ret_selloff"])
```

* * *

20\. 実装上の重要注意点
==============

20.1 初期欠損が非常に長い
---------------

論文に忠実だと必要履歴は長いです。

*   centrality: 2年
*   centrality shift: さらに3年
*   relative value: 最大10年
*   MVO covariance: 5年

したがって、まともに動き出すのはかなり後ろになります。

jpm\_crowded\_trades

20.2 PB の頻度
-----------

PBR は日次で取れないことがあります。その場合は

*   月次・週次更新値を forward fill
*   ただし未来値で埋めない

で良いです。

20.3 欠損処理
---------

セクターの途中追加やデータ欠損があると PCA が不安定になります。  
まずは **全セクターがそろった期間に限定**して動かすのが無難です。

20.4 ETF版との違い
-------------

このコードは「論文のセクター指数版」に近い設計です。  
ETFでやる場合は、

*   `market_cap` が ETF AUM なのかセクター総額なのか
*   `pb_ratio` が ETF aggregate P/B なのか

で意味が変わります。

* * *

21\. 最小限の実装順序
=============

いきなり全部作るより、次の順で検証すると壊れにくいです。

### 段階1

*   centrality series を作る
*   特定局面で tech / financials / energy が高くなるか確認

### 段階2

*   relative value を作る
*   centrality 高 × relative value 高 がバブル終盤っぽく見えるか確認

### 段階3

*   run-up / sell-off の条件付きリターンを作る
*   run-up > sell-off になるか検証

### 段階4

*   MVO ポートフォリオ化
*   index 対比の超過収益を見る

この順なら、論文の Exhibit 1 → 4 → 5 の流れに近く確認できます。

jpm\_crowded\_trades

* * *

22\. かなりそのまま使える関数一覧
===================

最後に、実装ファイルの骨子だけまとめるとこうです。

```
# inputs
compute_market_cap_weights()
compute_weighted_returns()

# centrality
make_exp_weights()
weighted_cov()
compute_centrality_from_cov()
compute_centrality_series()
compute_centrality_shift()

# valuation
build_total_return_index()
compute_trailing_1y_return()
compute_relative_value()

# classification
top_k_mask()
classify_states()
equal_weight_returns_from_mask()
build_expected_returns()

# portfolio
solve_long_only_mvo()
compute_mvo_weights_series()
smooth_weights()

# backtest
run_sector_rotation_pipeline()
performance_summary()
```

* * *

必要であれば次に、**この疑似コードをそのままフルの Python コードにして、関数定義まで完成形で出します。**



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)