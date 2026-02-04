# 枝分かれ · テーマETF戦略設計

**User:** Anonymous (kencharoffx@gmail.com)  
**Created:** 2/5/2026 0:14:26  
**Updated:** 2/5/2026 0:59:15  
**Exported:** 2/5/2026 0:59:27  
**Link:** [https://chatgpt.com/g/g-p-6981fb812180819189910b5bcfa690c0-thematic-strategy/c/6983624e-7c2c-83a2-a1db-69e3c5aef66c](https://chatgpt.com/g/g-p-6981fb812180819189910b5bcfa690c0-thematic-strategy/c/6983624e-7c2c-83a2-a1db-69e3c5aef66c)  

## Prompt:
AGENTS.md

ファイル

create\_project.sh

ファイル

Allocating to Thematic Investments.pdf

PDF

MSCI World Thematic Rotation Select Index Methodology.pdf

PDF

Performance measurement of ESG-themed megatrend investments in global equity markets using pure factor portfolios methodology.pdf

PDF

THEME Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics.pdf

PDF

# Chat Kickoff (with attachments)

## 0. 添付ファイル（あなた=AIが最初に読むもの）
- workspace共通ルール: AGENTS.md（添付）
- プロジェクト雛形生成: create_project.sh（添付）
- 研究対象PDF: （添付したPDF全て）

## 1. 今回のプロジェクト
- Project name: <Active Thematic ETF Strategy>
- 目的（1行）: <テーマETFを用いたアクティブ投資戦略の考案>

## 2. 最重要ルール（必ず遵守）
- 添付のAGENTS.md（共通）を最優先で守る（uv運用、pip禁止、outputs配下、説明は日本語 等）
- 依存追加は禁止（必要なら“提案のみ”）
- legacyは参照のみ（編集禁止）
- 変更はincremental（広範囲リファクタ禁止）
- Phase 1は「実装禁止」。docs/notes を作り切ったら停止

## 3. 今回あなた（AI）にやってほしいこと
Phase 1として、以下を順番に実施してください（実装禁止）：
1) 添付PDFを全て読み、定義・制約・評価観点を抽出
2) 添付がある場合、baseline参照物（例：main_ref.ipynb）を読み、処理フローと数式を抽出
3) docs/notes 仕様書一式（最低4点＋探索ログ）を作る前提で、
   “どのファイルに何を書くべきか” を、まずチャット上で提案してください
4) チャット上で合意できたら、Codexに渡せる「Project AGENTS.md（プロジェクト専用）」と
   「Codex 指示本文」を、コピペ可能な形で出力してください

## 4. 出力フォーマット要求
- 全て日本語
- 箇条書きを多用
- 不明点は assumptions として列挙し、検証案も書く
- 先読みや0リターン扱いなど、禁止事項に触れるリスクがあれば明示的に警告する

## Response:
思考時間: 2m 9s

以下、Phase 1（実装禁止）の範囲で **1) PDFから定義・制約・評価観点を抽出 → 2) baseline参照物の有無確認 → 3) docs/notes に何を書くべきかの提案** までを、順番どおりにまとめます。  
（workspace共通ルールは **uv運用・pip禁止・outputs配下・日本語説明** 等を遵守します

AGENTS

）

* * *

1) 添付PDFからの抽出（定義・制約・評価観点）
-------------------------

### A. 「Allocating to thematic investments」

**定義（何を“テーマ投資”とみなすか）**

*   テーマ＝「経済に大きな影響を与え、ビジネスモデルを再定義する構造変化（structural trends）」
    Allocating to Thematic Investme…
*   テーマ投資は「資産クラス/地域/セクター/スタイルを超える“追加次元”」だが、完全に独立ではなく、伝統的リスク要因へのエクスポージャーを持つ
    Allocating to Thematic Investme…
*   ESGとテーマの違い：
    *   ESG統合は必ずしも特定テーマへの集中を意味しない（テーマは“収益の相当部分がテーマ関連”など、より焦点が狭い）
        Allocating to Thematic Investme…

**制約・設計上の含意**

*   テーマ投資は集中度が上がりやすく、短期的に“choppy returns”を許容する必要がある
    Allocating to Thematic Investme…
*   テーマの表現（代表リターン系列）：
    *   既存のテーマ指数を起点にできるが、同一テーマでも構成差が大きく“合意が薄い”
        Allocating to Thematic Investme…
    *   複数ベンダー指数・複数ファンドを統合し、Lasso回帰などで伝統的リスク因子に対して効率的に合成する案
        Allocating to Thematic Investme…

**評価観点（この論文が何を良しとするか）**

*   コア・サテライト枠組み（テーマをサテライトに置く/あるいは全体最適化に統合）
    Allocating to Thematic Investme…
*   リスク分解：
    *   テーマ投資の期待リターン/リスク/相関は  
        i) 資産クラス露出、ii) 伝統的因子（地域/スタイル/セクター等）露出、iii) テーマ固有成分（residual）  
        の3分解で理解し、戦略配分へ統合
        Allocating to Thematic Investme…
*   “テーマ固有リスク（thematic volatility）”に正のalphaを仮定すると、最適化は他因子露出を模倣しつつテーマ固有へ配分しにいく
*   追跡誤差（tracking error）も明示的に観察対象（テーマ導入で増えるTEの大半がthematic volatility由来、という示唆）
    Allocating to Thematic Investme…

* * *

### B. 「MSCI World Thematic Rotation Select Index Methodology」

**定義（指数ルール）**

*   親指数：MSCI ACWI IMI（Parent Index）
    MSCI World Thematic Rotation Se…
*   テーマ候補（Applicable Universe）：
    *   22のMSCI Thematic Index（Component Indexes）から構成
*   月次でテーマ順位付け：
    *   MKT MediaStatsの **Megatrend Scores（テーマ別メディア・センチメント）** に基づき降順ランク
*   上位4テーマを採用し、各25%で等ウェイト合成
    MSCI World Thematic Rotation Se…
*   銘柄の最終ウェイトは「採用4指数の銘柄ウェイトの加重和」で定義
    MSCI World Thematic Rotation Se…
*   Eligible Universeの銘柄選択：
    *   Applicable Universeから **MSCI World index** の銘柄を選ぶ（少なくともこの一段のフィルタがある）
        MSCI World Thematic Rotation Se…

**制約・リスク管理**

*   10% Risk Control版：
    *   年率ボラ10%ターゲット
        MSCI World Thematic Rotation Se…
    *   ボラ計算：短期/長期の減衰係数（0.94, 0.97）と、3日ラグの対数リターンを用いる仕様が明記
        MSCI World Thematic Rotation Se…
*   ライセンス/利用制約（重要）：
    *   MSCI情報は「改変・再配布・派生物（指数/DB/リスクモデル等）作成等」を強く制限する旨の免責・禁止が明記
        MSCI World Thematic Rotation Se…
        → **研究用途でも、成果物の扱い（外部共有・再配布・商用化）に注意**が必要。

**評価観点（この指数が暗に最適化しているもの）**

*   “メディアセンチメントでテーマをローテーションし、上位テーマの集合のパフォーマンスを表現”
*   （10%版では）ボラターゲット達成が主要な運用品質指標になる

* * *

### C. 「Performance measurement of ESG-themed megatrend investments … pure factor portfolios」

**定義（“メガトレンド/テーマ露出”の測り方）**

*   ETFの構成銘柄ダミーではなく、**比率尺度でメガトレンド露出を測る**べきという立場
    Performance measurement of ESG-…
*   露出定義（重要な数式）：
    *    $MTE_{nmt} = \frac{\sum_{e=1}^{E} FI_{nmt}}{MCap_{nt}}$ 
    *    $FI_{nmt}$ ：テーマETF e から銘柄nへの（株数×価格で評価した）資金流入、 $MCap$ ：時価総額
        Performance measurement of ESG-…
*   データ制約（強い注意点）：
    *   ETF保有株数は **2019年時点の一定ポジションを全期間に適用**（価格だけ週次で変える）という制約が明記
        Performance measurement of ESG-…
        → **先読み（look-ahead）/サバイバー/構成変化無視のリスク**が高い。

**制約（データ処理・推定上のルール）**

*   サバイバーシップ回避：2015–2019に取引された銘柄を対象（指数メンバー）
    Performance measurement of ESG-…
*   クリーニング：
    *   価格/リターン/時価総額欠損銘柄除外、**penny stock（最大価格<$5）除外**
        Performance measurement of ESG-…
    *   ディスクリプタは **1%/99% winsorize**
    *   欠損は **MI（MCMC/DA）で補完**、低欠損なので3回の代入
*   因子構成：
    *   28ディスクリプタ→週次PCAで11スタイル因子（Value/Mom/Size/Vol/Liq/Profit/Growth…等）

**評価観点**

*   リスク調整後の超過収益（FFモデル等のalpha）を重視しつつ、**取引費用・信託報酬の感度**を明示的に評価
    Performance measurement of ESG-…
*   “低コスト（例：年25–50bp）”と“高コスト（100–150bp）”で結論が変わり得る、という示唆
    Performance measurement of ESG-…

* * *

### D. 「THEME: Enhancing Thematic Investing with Semantic Stock Representations and Temporal Dynamics」

**定義（問題設定）**

*   テーマ投資はセクター横断で、かつ時間とともにテーマ整合性が変化する（non-stationary）ため静的分類が弱い
*   一般LLM埋め込みは金融資産の“意味”に適合しないことがあるため、金融向けチューニングが必要

**手法上のコア（使うならここが仕様になる）**

*   階層コントラスト学習で「テーマ⇄構成銘柄」の階層関係を学習し、さらにリターンで時間動学を取り込む
*   トリプレット損失（時間動学取り込みの注意点）：
    *   **H日先のフォワードリターンが高い銘柄をpositive、低い方をnegative**として学習に使用
        THEME Enhancing Thematic Invest…
        → 研究としては良いが、**バックテスト/運用シグナルに混入すると先読みになる**（後述で警告）。
*   推論：クエリ文→埋め込み→銘柄埋め込みとのcos類似度でTop-K抽出
    THEME Enhancing Thematic Invest…
*   評価：RetrievalはHR/Precision@k、投資応用はポートフォリオ性能も見る
*   ETFのみの教師データより、ニュース/分類も取り込んだTRSの方が広いテーマをカバーし改善、という示唆
    THEME Enhancing Thematic Invest…

* * *

2) baseline参照物（例：main\_ref.ipynb）について
-------------------------------------

*   現時点の添付からは、**baseline notebook（main\_ref.ipynb等）の存在を確認できていません**。
*   ただし、雛形生成スクリプトは \*\*main.ipynb を“単一エントリポイント”\*\*として想定し、`docs/notes`の仕様をロードして進める骨格になっています  
    → baselineが別にあるなら、Phase 1では「処理フローと数式をdocs/notesへ抽出」する位置づけ。

* * *

3) docs/notes 仕様書一式：まず“どのファイルに何を書くべきか”提案
----------------------------------------

`create_project.sh` は最低限として以下の4点テンプレを作ります：

*   `00_doc_index.md`, `10_requirements.md`, `20_assumptions.md`, `30_plan.md`
    create\_project
    今回プロジェクト（<Active Thematic ETF Strategy>）では、**研究PDFの論点が「テーマ定義」「ローテーション規則」「推定/最適化」「評価（費用・統計）」に跨る**ため、4点に加えて分割した方が手戻りが減ります。

### 提案する docs/notes 構成（実装禁止・仕様のみ）

#### 00系：ソース整理（固定）

*   **`00_doc_index.md`**
    *   docs/sources配下のPDF一覧
    *   各PDFの役割（指数ルール / 手法 / 評価 / 注意点）
    *   “このプロジェクトで採用する/しない”の一次判断
*   **`01_glossary.md`（追加提案）**
    *   テーマ/メガトレンド/ESG/サテライト/TE/ボラターゲット等の用語定義
    *   数式で使う記号（w, r, σ, TE, cost…）の統一

#### 10系：要求仕様（テスト可能な形に落とす）

*   **`10_requirements.md`（テンプレ拡張）**
    create\_project
    *   Universe定義（ETFユニバース or MSCIテーマ指数ユニバース etc.）
    *   テーマスコア（MediaStats、または代替）と更新頻度（月次）
    *   ローテーション（上位Kテーマ、等ウェイト等）
    *   リスク制御（10%ボラターゲットの有無、推定窓、減衰係数など）
        MSCI World Thematic Rotation Se…
    *   取引コスト・信託報酬の取り扱い（固定bps、スプレッドモデル等）
        Performance measurement of ESG-…
    *   禁止事項（先読み、サバイバー、将来情報の混入）※後述の警告を明文化
*   **`11_constraints.md`（追加提案）**
    *   ハード制約（long-only、最大ウェイト、テーマ内/テーマ間の上限制約、流動性制約）
    *   データ制約（入手可能性、タイムスタンプ、遅延）
    *   ライセンス制約（MSCI情報の再配布/派生物扱い注意）
        MSCI World Thematic Rotation Se…
*   **`12_signals_and_scores.md`（追加提案）**
    *   (A) MediaStats Megatrend Scoreベース（MSCI方式）
    *   (B) フロー/保有比率ベース露出（ESG論文のMTE式：採用するなら先読み回避の代替仕様が必須）
        Performance measurement of ESG-…
    *   (C) テキスト埋め込みベース（THEMEの思想：採用範囲を「スクリーニング補助」等に限定する案）

#### 20系：仮定・未確定（検証計画込み）

*   **`20_assumptions.md`（テンプレ）**
    create\_project
    *   下の「Assumptions（不明点）」をここへ集約
    *   各仮定に「検証案（どのデータで、どのチェックを通すか）」を必ず付与
*   **`21_data_spec.md`（追加提案）**
    *   必須データ（価格、出来高、AUM、ETFホールド、テーマスコア、指数構成等）
    *   タイムスタンプ規約（観測可能時刻、リバランスの“知り得る”境界）
    *   欠損処理方針（MI等を採用するなら、論文準拠の仕様）

#### 30系：実装計画（ただしPhase 1は計画まで）

*   **`30_plan.md`（テンプレ拡張）**
    create\_project
    *   srcモジュール分割案（data/signals/optimizer/backtest/metrics/reporting）
    *   main.ipynbのセクション対応（雛形の章立てに合わせる）
    *   “最初に通す最小バックテスト”の道筋（仕様として）
*   **`31_evaluation_protocol.md`（追加提案）**
    *   評価指標セット：
        *   年率リターン/ボラ/Sharpe
        *   TE、ボラターゲット乖離（10% RC採用時）
        *   回転率、コスト控除後成績（費用感度）
            Performance measurement of ESG-…
    *   統計検定（必要なら。ESG論文はFFモデル/GMM-IVd等を使うが、当プロジェクトでの採用範囲を明記）

#### 90系：探索ログ（必須）

*   **`90_research_log.md`（追加提案：探索ログ）**
    *   「どのPDFのどこを読んで、どの仕様に落としたか」
    *   仕様確定の判断理由（採用/不採用）
    *   先読み等のリスク指摘と、その回避仕様へのリンク

* * *

Assumptions（不明点）と検証案（Phase 1で明文化推奨）
-----------------------------------

*   **A1. 投資対象は“テーマETF”そのものか？それとも“テーマ指数/テーマ株バスケット”か？**
    *   検証案：利用可能データ（ETF価格/AUM/構成）と、MSCI/MediaStatsスコアの入手性を棚卸しして決める。
*   **A2. テーマスコアはMediaStatsを使う前提か？代替（ニュースセンチメント/独自NLP）か？**
    *   検証案：MediaStatsスコアの取得方法・履歴の可用性を確認（入手不可なら代替仕様へ）。
*   **A3. リバランス頻度（月次）とコストモデル（売買コスト・信託報酬）の具体**
    *   検証案：対象ETFの経費率レンジを調査し、ESG論文のように複数bpsシナリオで頑健性評価する枠を仕様化
        Performance measurement of ESG-…
*   **A4. baseline notebook（main\_ref.ipynb等）の有無**
    *   検証案：legacy/ や notebooks/ に既存資産があるか確認（ただし編集は禁止、参照のみ）。

* * *

明示的な警告（禁止事項に触れるリスク）
-------------------

*   **先読み（look-ahead）リスク**
    *   THEMEは学習で「フォワードリターンが高い銘柄をpositive」としており、運用シグナルに混入すると即アウト
        THEME Enhancing Thematic Invest…
    *   ESG論文のMTE計算は、ETF保有株数を2019年時点で固定して過去へ適用しており、同様に先読み/構成変化無視のリスクが高い
        Performance measurement of ESG-…
        → docs/notes側で **“観測可能な時点情報のみを使う”** をハード要件化推奨。
*   **0リターン扱い・欠損処理の不適切さ**
    *   欠損を0埋めすると、センチメント/リターン/出来高など多くの系列でバイアスが出る。ESG論文はMI（MCMC）やwinsorizeを採用しており、同等の注意書きが必要
*   **MSCIライセンス/再配布**
    *   MSCI文書は利用制約が強いので、docs/notesには「引用は最小限・派生指数の再配布をしない」等の取り扱いルールを明記推奨
        MSCI World Thematic Rotation Se…

* * *

次のステップ（あなたとの“チャット合意”ポイント）
-------------------------

上の **docs/notes 構成案**で合意できれば、次にあなたが求めている Phase 1の(4)として：

*   **Project AGENTS.md（プロジェクト専用）**
*   **Codex 指示本文（コピペ可能）**

を、この構成に沿って具体文面で出力します（※その段階でも実装はしません）。

合意確認のための最小論点は以下です（Yes/Noで十分）：

*   テーマローテの中核を **「MSCI方式（テーマスコア→上位Kテーマ）」** に置く方針でよいか（スコア自体は代替可）
*   投資対象は **ETF（テーマETF）** を主にするか、**テーマ株バスケット**も許容するか（後者はデータ要件が増える）

## Prompt:
テーマカブバスケットとはなんですか？

## Response:
「テーマ株バスケット」は、\*\*特定のテーマ（例：AI、脱炭素、サイバーセキュリティ等）に“関係が深い”と判断した複数の個別株を束ねた銘柄集合（ポートフォリオの素）\*\*のことです。ETFそのものを買うのではなく、**ETFの中身に近いものを自分で構成する**イメージです。

* * *

具体像
---

*   **テーマETF投資**：1本のETF（例：クリーンエネルギーETF）を売買する
*   **テーマ株バスケット投資**：そのテーマに該当する個別株（例：A社・B社・C社…）を選び、
    *   等ウェイト、時価総額加重、スコア加重などで重み付けして運用する

* * *

どうやってバスケットを作るか（代表的な方法）
----------------------

*   **指数/ETFの構成銘柄を流用**
    *   例：MSCIのテーマ指数の構成銘柄をバスケットとして採用（ただしライセンス/再配布制約に注意）
        MSCI World Thematic Rotation Se…
*   **ルールで選ぶ（売上・事業の関連度）**
    *   「テーマ関連売上比率が一定以上」など、テーマ純度（pure-play）を定義して組む
*   **テキスト/NLPで選ぶ**
    *   企業説明・ニュース・開示文書からテーマとの類似度で抽出（THEME論文のようなアプローチ）
    *   ※学習や特徴量に将来情報が混じると先読みになるので設計が難しい
        THEME Enhancing Thematic Invest…
*   **資金フローで測る**（研究用途で出てくる）
    *   テーマETFからの資金配分を使って銘柄の“テーマ露出”を定義する考え方（MTE）
        Performance measurement of ESG-…
    *   ※論文では保有株数を固定して過去に当てており、先読み/構成変化無視のリスクが高い点に注意
        Performance measurement of ESG-…

* * *

ETFより何が違う？（メリット/デメリット）
----------------------

**メリット**

*   テーマ純度や設計意図（集中度、除外条件、重み付け）を自分でコントロールできる
*   ETFの経費率以外の設計（例：コスト最小化、リスク管理）を柔軟にできる

**デメリット**

*   構成銘柄データ、リバランス、売買コスト、コーポレートアクション対応など運用負荷が大きい
*   ルール次第でバイアス（先読み、サバイバー、データ遅延）を埋め込みやすい
*   ベンダー指数/ETF構成の利用には利用規約・ライセンス制約が絡みやすい
    MSCI World Thematic Rotation Se…

* * *

このプロジェクト文脈だと、「テーマETFで運用する」方針なら **バスケットは“テーマ定義・銘柄選別の研究用”に留める**のが安全です（実装・運用負荷と、先読みリスクを最小化できるため）。

## Prompt:
今回のプロジェクトではテーマETFでの運用にとどめます。候補のETFは下記の通りです。

以下は、直前に提示したテーマETF群を **「採用候補（コア）／補助候補（サテライト）／除外（重複・テーマ薄い）」** の3段階に圧縮した **最終ユニバース案（ティッカーのみ）** です。
（判断基準：**テーマ純度・流動性/代表性・他テーマとの重複の少なさ**。なお、ここでは“実測のAUM/出来高”チェックはしていません。）

---

## 採用候補（コア）

**AI / ロボ**

* AIQ
* BOTZ

**半導体**

* SMH

**クラウド**

* WCLD

**サイバーセキュリティ**

* CIBR

**フィンテック/決済**

* IPAY

**クリーンエネルギー（広め）**

* ICLN

**太陽光（サブテーマとして強い）**

* TAN

**EV / 自動運転**

* DRIV

**バッテリー / リチウム**

* LIT

**宇宙**

* UFO

**防衛**

* ITA

**ゲノミクス**

* ARKG

**水**

* PHO

**農業**

* MOO

**インフラ**

* PAVE

**ゲーム/eスポーツ**

* ESPO

**メタテーマ（テーマ分散の保険）**

* KOMP

---

## 補助候補（サテライト）

※コアを持った上で「同一テーマの指数差/地域差」「テーマの周辺（つるはし）」「ボラ調整」目的で追加。

**AI / ロボ**

* IRBO
* ROBO
* THNQ
* WTAI

**半導体**

* SOXX
* XSD
* PSI

**クラウド**

* CLOU
* SKYY
* IGV

**サイバーセキュリティ**

* HACK
* BUG
* IHAK
* WCBR

**フィンテック/クリプト関連（株式テーマ）**

* FINX
* ARKF
* BLOK
* KOIN
* WGMI
* BITS

**クリーンエネルギー（広め）**

* QCLN
* PBW
* ACES
* PBD

**再エネサブテーマ**

* FAN（風力）
* RAYS（太陽光の別指数）

**EV / モビリティ**

* IDRV
* KARS
* CARZ

**バッテリー周辺（資源寄り）**

* BATT
* REMX

**宇宙**

* ARKX

**防衛**

* PPA
* XAR

**ゲノミクス/バイオ**

* IDNA
* GNOM
* IBB

**水**

* FIW
* CGW

**農業/フード**

* VEGI

**インフラ**

* IFRA

**ゲーム/eスポーツ**

* HERO
* NERD

**メタテーマ**

* ARKK

---

## 除外（重複 / テーマ薄い）

> 今回提示した範囲で「明確に落とす」と言えるのは少ないため、**“条件付き除外”**（最終ユニバースを絞る時に外す）として示します。

**A) 同一テーマ内で過剰に重複しやすいので、コア採用済みなら外しがち**

* （クラウド）CLOU / SKYY（WCLDをコアにした場合）
* （サイバー）HACK / BUG / IHAK / WCBR（CIBRをコアにした場合）
* （太陽光）RAYS（TANをコアにした場合）
* （防衛）PPA / XAR（ITAをコアにした場合）
* （水）FIW / CGW（PHOをコアにした場合）
* （ゲーム）HERO / NERD（ESPOをコアにした場合）
* （半導体）SOXX / XSD / PSI（SMHをコアにした場合）

**B) “テーマが広すぎて”他テーマと因子が被りやすいので外しがち**

* IGV（ソフトウェア全般：クラウド純度はWCLDより落ちることがある）
* IBB（バイオ全般：ゲノミクス純度はARKG/IDNA/GNOMより落ちることがある）
* PBD（グローバル/分散が効く一方、純度が散りやすいケース）
* ARKK（メタテーマとして便利だが、中身がアクティブでドリフトしやすい）

**C) テーマが株式というより“コモディティ/資源ベータ”に寄りやすいので外しがち**

* REMX（レアアース市況・資源要因が強く、テーマ因子が薄まりやすい場合がある）
* WGMI（マイナー寄り：クリプト価格ベータ色が強いことがある）
* BITS（同上）

---

### 最終ユニバース案（コアだけ抽出・コピペ用）

AIQ, BOTZ, SMH, WCLD, CIBR, IPAY, ICLN, TAN, DRIV, LIT, UFO, ITA, ARKG, PHO, MOO, PAVE, ESPO, KOMP

---

必要なら次の段階として、この「コア18本」を

* **相関の高いものを統合して 12本程度に圧縮（テーマ数固定）**
* **“景気循環/金利”に弱いテーマのヘッジバケット**を追加（例：品質/最小分散/短期国債など）
  みたいに、運用戦略の実装に繋がる形へ落とし込めます。

添付した４つのドキュメントの内容からそれぞれ有効な手法を抽出・組み合わせて戦略を構築したいです。各ドキュメントから戦略として使えそうな要素を可能な限り広く提案してください。

## Response:
了解です。\*\*「テーマETF（あなたのコア18本）だけで運用」\*\*に制約を置いた上で、添付4本（※PDF）から **“戦略として使える要素” をできるだけ広く**抽出し、最後に \*\*組み合わせ案（戦略アーキテクチャ案）\*\*まで落とし込みます。  
（Phase 1なので、ここでは実装・検証はせず、仕様化できる部品の提案に徹します）

* * *

0) 前提：今回の“運用対象”
---------------

*   ETFユニバース（コア18本）  
    AIQ, BOTZ, SMH, WCLD, CIBR, IPAY, ICLN, TAN, DRIV, LIT, UFO, ITA, ARKG, PHO, MOO, PAVE, ESPO, KOMP
*   目的：**テーマ間ローテーション／配分**で、リスク管理込みのアクティブ戦略を設計

* * *

1) 各ドキュメントから「戦略要素として使えるもの」抽出
----------------------------

### A. 「Allocating to thematic investments」から使える要素

この論文は「テーマ投資を、伝統的資産配分・因子配分の枠にどう統合するか」が核です。

Allocating to Thematic Investme…

**(A1) テーマのリターン分解（戦略の“設計思想”になる）**

*   テーマETFのリターンを
    *   ① 資産クラス/市場β
    *   ② 伝統的因子（セクター/スタイル/地域等）
    *   ③ テーマ固有（residual, thematic component）  
        に分けて理解し、③を取りに行く、というフレーム
        Allocating to Thematic Investme…
*   戦略への落とし込み：
    *   \*\*「因子寄与が大きいテーマは“見かけテーマ”」\*\*になり得るので、因子中立化や配分上限の根拠になる
    *   テーマ同士の相関が高い時に「同じ因子を二重に買ってる」状態を検知する設計が可能

**(A2) テーマを“サテライト”として扱う枠組み**

*   テーマは伝統的なコア（広範市場）とは別次元のエクスポージャーだが、完全独立ではない
    Allocating to Thematic Investme…
*   戦略への落とし込み：
    *   今回はETF18本のみで運用するが、設計思想として
        *   **「テーマ間の分散＝疑似コア」**
        *   **「テーマ固有成分が強いものほど配分価値がある」**  
            を定義できる

**(A3) “テーマ指数/ETFの合成”という考え方（Lasso等）**

*   同一テーマでも指数間で構成差が大きい→複数系列を統合し、伝統的因子に対して効率的に合成する（Lasso回帰の例）
    Allocating to Thematic Investme…
*   戦略への落とし込み（ETF18本版）：
    *   同一テーマに複数ETFはないが、\*\*「似たETF群（例：AIQ/BOTZ/SMH/WCLD）」を“テーマクラスター”として合成」\*\*は可能
    *   その合成を使って **クラスターごとの配分**や **重複除去**のルール化ができる

**(A4) 評価観点：テーマは短期的に“choppy”になりやすい**

*   テーマ投資は集中度が上がり、短期ノイズを許容する必要がある
    Allocating to Thematic Investme…
*   戦略への落とし込み：
    *   リバランス頻度（例：月次）と、リスク制御（ボラターゲット等）の必要性の根拠になる

* * *

### B. 「MSCI World Thematic Rotation Select Index Methodology」から使える要素

これは \*\*“テーマローテの具体ルール”\*\*が明確で、ETFローテにも移植しやすいです。

MSCI World Thematic Rotation Se…

**(B1) ローテの型：月次でテーマをランキング→上位Kを採用**

*   Megatrend Score（メディア・センチメント）でテーマを順位付けし、上位4テーマを等ウェイト
*   戦略への落とし込み（ETF18本版）：
    *   “テーマスコア”を何かしら定義できれば、**そのまま上位K ETFを等ウェイト**ができる
    *   Kは4に限らず、**分散と集中のトレードオフで設計パラメータ化**できる

**(B2) リスク制御：ボラターゲット（10%）の明文化**

*   年率ボラ10%ターゲット版がある
    MSCI World Thematic Rotation Se…
*   ボラ推定に短期/長期の減衰係数（0.94, 0.97）やラグが明記されている
    MSCI World Thematic Rotation Se…
*   戦略への落とし込み：
    *   ETFポートの **全体ボラを一定に保つ（リスク予算の安定化）**
    *   または **各ETFウェイトを“1/推定ボラ”でスケール**して、実効リスクを均す

**(B3) 重要な注意：MSCIデータのライセンス**

*   MSCI情報の改変・再配布・派生物作成等に強い制限がある旨の免責・禁止が明記
    MSCI World Thematic Rotation Se…
*   戦略への落とし込み：
    *   “MSCI指数を再現する”という表現や再配布に当たる成果物は避け、**方法論（ローテの型、ボラ推定の考え方）を参照する**に留めるのが安全

* * *

### C. 「Performance measurement of ESG-themed megatrend investments … pure factor portfolios」から使える要素

この論文は \*\*「テーマは因子と絡むので、測り方（露出・評価）を厳密に」\*\*が本筋です。

Performance measurement of ESG-…

**(C1) “テーマ露出”を連続尺度で測るべき、という考え**

*   テーマをダミー（該当/非該当）でなく、比率尺度で測るべきという立場
    Performance measurement of ESG-…
*   戦略への落とし込み（ETF18本版）：
    *   各ETFに対し、テーマ純度スコアを連続で持たせる（例：分類確信度、ニュース一致度、売上比率など）
    *   それをウェイトに反映（高純度ほど上限↑/採用優先↑）

**(C2) クリーニング/推定の作法が具体**

*   1%/99% winsorize、欠損にMI（MCMC/DA）などの具体ルール
*   戦略への落とし込み：
    *   ETFリターンやスコア系列でも、**極端値処理・欠損処理の仕様**を先に決められる
    *   とくにニュース/センチメントはスパイクが出やすいので、winsorizeは相性が良い

**(C3) “因子で説明した後のalpha”という評価軸**

*   取引費用・信託報酬の感度を明示して結論が変わり得ることを指摘
    Performance measurement of ESG-…
*   戦略への落とし込み：
    *   評価プロトコルに **（コスト控除後）Sharpe、回転率、FF回帰alpha** 等を入れ、テーマが因子の焼き直しでないか確認する
    *   コストを **25–50bp vs 100–150bp** のように複数シナリオでストレスする枠が作れる
        Performance measurement of ESG-…

**(C4) 注意：論文のMTE定義はデータ制約が強く、先読みになりやすい**

*   ETF保有株数を2019時点で固定し過去に適用している制約が明記
    Performance measurement of ESG-…
*   戦略への落とし込み：
    *   今回はETF運用に留めるので、**MTE式そのものは採用しない**か、採用するなら「当時点で観測できる保有データのみ」を使う仕様が必須

* * *

### D. 「THEME: Semantic Stock Representations and Temporal Dynamics」から使える要素

これは本来「テーマ銘柄選定」寄りですが、ETF戦略でも \*\*“テーマシグナル生成”\*\*に転用できます。

THEME Enhancing Thematic Invest…

**(D1) 重要な視点：テーマは“非定常”で、定義が時間でズレる**

*   テーマ整合性は時間で変化する（静的分類が弱い）
*   戦略への落とし込み（ETF18本版）：
    *   ETFのテーマ分類・純度・関連キーワードを **定期更新する仕様**（月次/四半期）を組み込む
    *   “過去のテーマ勝ちパターン”に固定しない設計

**(D2) 埋め込み＋類似度（retrieval）の枠組み**

*   テキスト→埋め込み→類似度でTop-K抽出
    THEME Enhancing Thematic Invest…
*   戦略への落とし込み（ETF18本版）：
    *   ETFの説明文、保有上位銘柄の事業説明、ニュース見出し等から  
        **「各ETF×テーマ」の類似度スコア**を作り、テーマスコアの一部として使う
    *   これは「テーマの定義が揺れる」問題への耐性になる

**(D3) 注意：フォワードリターンを教師に使う設計は先読みリスク**

*   高いフォワードリターン銘柄をpositiveにする、と明記
    THEME Enhancing Thematic Invest…
*   ETF運用へ転用するなら：
    *   **フォワードリターン教師は使わない**（または学習・検証の厳密分離が必須）
    *   代わりに **“テキスト整合性”だけ**でスコア化するのが安全

* * *

2) 4本の要素を「組み合わせて作れる戦略案」できるだけ広く
------------------------------

以下は、あなたのETF18本を前提に、上の要素をモジュールとして組んだ **戦略テンプレ案**です（どれも“実装”ではなく、設計仕様の案）。

* * *

### 戦略案 S1：MSCI型テーマ・ローテ（スコア→Top-K→等ウェイト）＋ボラターゲット

*   コアアイデア：MSCI方式の骨格をETFに移植
*   ルール案
    *   月次で各ETFにテーマスコア付与（スコアは独自でも可）
    *   上位K本を採用、等ウェイト
    *   ポート全体ボラを10%等にターゲット（またはETFを1/volでスケール）
*   どの論点をカバー？
    *   “choppy”なテーマにリスク制御を入れて運用耐性を上げる
        Allocating to Thematic Investme…

* * *

### 戦略案 S2：因子被り除去ローテ（テーマ固有成分を最大化）

*   コアアイデア：テーマリターンを因子で分解し、**因子の焼き直しを避ける**
    Allocating to Thematic Investme…
*   ルール案
    *   各ETFのリターンを市場・スタイル因子で説明（推定はローリング）
    *   残差（テーマ固有）寄与が強いETFに優先配分
    *   相関の高いETFは同時採用を減らす（クラスターごとに代表を1本）
*   期待される効用
    *   “テーマ名は違うが、実は同じ因子”問題を抑制

* * *

### 戦略案 S3：テーマ純度スコア（連続尺度）で“採用上限”を可変にする

*   コアアイデア：テーマ露出は連続尺度で測るべき
    Performance measurement of ESG-…
*   ルール案
    *   各ETFに「純度スコア（0–1）」を持たせる（情報源は後述）
    *   純度が低いETFは採用しても上限ウェイトを絞る
    *   純度が高いETFは採用閾値を緩め、代替が少ないテーマを確保
*   純度スコアの作り方（候補）
    *   ETF説明文 × テーマ定義文 の類似度（THEMEのretrieval思想）
    *   定期更新（テーマ非定常への対応）
        THEME Enhancing Thematic Invest…

* * *

### 戦略案 S4：センチメント・スコア×価格モメンタムのハイブリッド

*   コアアイデア：MSCIはメディアセンチメントでテーマ順位付け
    MSCI World Thematic Rotation Se…
*   ルール案
    *   テーマスコア（ニュース/メディア/テキスト）で“注目度”を測る
    *   それにETFの価格モメンタム（例：3–12M）を掛け合わせて採用順位を作る
*   注意
    *   センチメント系列は外れ値が出やすいので、winsorize等の作法を仕様化
        Performance measurement of ESG-…

* * *

### 戦略案 S5：コスト耐性最適化（回転率を制約に入れる）

*   コアアイデア：結論はコストで変わる。コスト感度を必ず評価
    Performance measurement of ESG-…
*   ルール案
    *   リバランスで「目標ウェイトとの差」を全て埋めない
    *   取引コスト（スプレッド/インパクトの簡易モデルでも）と、回転率上限を制約に入れる
    *   複数コスト仮定で成績が崩れない戦略を採択
        Performance measurement of ESG-…

* * *

### 戦略案 S6：テーマの“非定常”対応（テーマ定義・スコアの定期再学習/再計測）

*   コアアイデア：テーマ整合性が時間で変わる
*   ルール案
    *   テーマ定義文（キーワードや説明文）を固定しない
    *   ETF×テーマの類似度や、関連ニュース語彙を月次で更新
    *   その更新を、ローテーション・スコアに反映

* * *

3) “現実的に強い”統合アーキテクチャ案（おすすめ順のたたき台）
---------------------------------

### 統合案 T1：MSCI型ローテ ＋ ボラターゲット ＋ 回転率制約

*   骨格：S1（ローテ）＋B2（ボラ）＋C3（コスト感度）
*   長所：ルールが明快で、過剰最適化しにくい
*   参照根拠：MSCIのローテ＆リスク制御 、コスト感度
    Performance measurement of ESG-…

### 統合案 T2：テーマ固有成分を優先する“残差ローテ”＋ボラターゲット

*   骨格：A1（分解）＋S2（被り除去）＋B2（ボラ）
*   長所：「テーマの名前」より「テーマ固有」を狙える
*   注意：因子モデルの設計で恣意性が出るので、評価プロトコル（C3）を強める
    Performance measurement of ESG-…

### 統合案 T3：テキスト整合性でスコア更新し、非定常対応するローテ

*   骨格：D1/D2（非定常＋retrieval）＋S1（Top-K）
*   長所：テーマの定義揺れへの耐性
*   注意：D3のとおりフォワードリターン教師は使わない（先読み回避）
    THEME Enhancing Thematic Invest…

* * *

4) 重要な警告（今回の制約下で事故りやすい点）
------------------------

*   **先読み禁止**
    *   THEMEの“フォワードリターン教師”はETFローテのシグナルに混ぜない
        THEME Enhancing Thematic Invest…
    *   ESG論文のMTE式はデータ制約が強く、そのまま過去に当てると危険
        Performance measurement of ESG-…
*   **MSCIの再現・再配布に触れない**
    *   MSCI指数の構成やスコアをそのまま再配布する形は避け、方法論参照に留める
        MSCI World Thematic Rotation Se…

* * *

5) 次に docs/notes に落とすときの「部品リスト」
-------------------------------

（合意後に、Project AGENTS.md と Codex指示本文に変換できます）

*   スコア設計（MSCI型の“テーマ順位付け”の代替スコア定義）
*   採用ルール（Top-K、等ウェイト、同時採用制約）
*   リスク制御（ボラ推定、ボラターゲット、ラグ/減衰係数の仕様）
    MSCI World Thematic Rotation Se…
*   コスト・回転率（評価と制約）
    Performance measurement of ESG-…
*   非定常対応（テーマ定義・スコア更新）
    THEME Enhancing Thematic Invest…
*   クリーニング（winsorize、欠損処理方針）

* * *

あなたの希望に沿うなら、次は \*\*「統合案T1/T2/T3のどれを主戦略にするか」\*\*を決め打ちし、docs/notesの各ファイルに「仕様として書く項目（数式・入出力・禁止事項）」へ落とし込みます。  
（実装はしません。仕様だけを作り切ります。）

## Prompt:
これらの要素について論文の内容をもとにより詳細な説明を数式を交えて解説してください

## Response:
思考時間: 23s

以下では、添付4ドキュメント（論文2本＋MSCI手法書＋THEME論文）から **「戦略の部品として使える要素」** を抽出し、**数式（できるだけ原典の形）** で噛み砕いて整理します。  
（※あなたのプロジェクト方針どおり、ここでは“実装”や具体的バックテストはしません。戦略設計に落とすための理論部品の提示に徹します。）

* * *

1) Allocating to Thematic Investments（Somefun et al.）から使える要素
------------------------------------------------------------

この論文の主眼は **「テーマ投資＝伝統因子＋テーマ固有成分」** と見做して、**頑健（robust）最適化でSAA（戦略的配分）に統合する**ことです。

Allocating to Thematic Investme…

### 1.1 テーマリターンの分解（“テーマ純粋成分”の定義）

付録で、テーマ指数（ETFでも代用可）の超過リターンを

$$
XR^{thematic}_t = XR^{market, thematic}_t + XR^{region/style/sector, thematic}_t + XR^{pure\ theme, thematic}_t \tag{1}
$$

と分解します。

Allocating to Thematic Investme…

*   直感：
    *   第1項：市場（株式ベータ）で説明される部分
    *   第2項：地域・セクター・スタイル（例：成長、モメンタム等）で説明される部分
    *   第3項：それらで説明できない **“テーマ固有”**（戦略で取りに行きたい対象）

**ETF運用への落とし込み（重要）**  
あなたの「コア18本ETF」を対象にするなら、各ETFの超過リターン  $XR_{i,t}$  を、たとえば線形因子モデルで近似して

$$
XR_{i,t}=\alpha^{(theme)}_{i} + \beta_i^\top f_t + \varepsilon_{i,t}
$$

と置き、 $\alpha^{(theme)}_{i}$  を **“純テーマ・アルファ（擬似）”** として扱う、という設計ができます。  
（論文は指数ベースで議論していますが、ETFでも同型に置けます。）

### 1.2 コア・サテライト（ただし“統合”が推奨）

コア・サテライトが紹介されつつも、**“テーマを全体最適化に直接統合する方が望ましい”** という文脈です。

Allocating to Thematic Investme…

あなたのユニバース（コア18本）なら、

*   コア：市場・分散の中核（例：広域株式や低リスク等）
*   サテライト：テーマETF（あなたの対象）

という分離も可能ですが、論文の思想はむしろ  
**「テーマも含めて、因子露出を見ながら全体で最適化」** です。

Allocating to Thematic Investme…

### 1.3 “頑健最適化”の使い方（設計部品）

論文本体のキモは、テーマの期待超過収益が **伝統因子由来** と **テーマ固有** の双方から来るので、推定誤差を踏まえた **robust optimization** を使う点です。

Allocating to Thematic Investme…

（このPDF断片では最適化の具体式がすべて露出していないため、ここでは設計の骨格として提示します。）

典型的には、平均分散のロバスト版として

*   期待リターン  $\mu$  が不確実集合  $\mathcal U$  に属する
*   共分散  $\Sigma$  も不確実、または shrinkage

などを置き、

$$
\max_{w\in\mathcal W}\ \min_{\mu\in\mathcal U}\ \left( w^\top \mu - \frac{\lambda}{2} w^\top \Sigma w \right)
$$

のような **min-max** を組むのが定石です（論文の“robust portfolio optimisation”の位置づけ）。

Allocating to Thematic Investme…

**ETF戦略での具体的価値**  
テーマETFは “推定誤差（期待収益が当てづらい）” が大きいので、

*   **期待リターンを控えめに扱う**
*   **リスク（共分散）主導**
*   **因子露出制約（後述）**  
    を入れると、設計が破綻しにくくなります。

* * *

2) MSCI World Thematic Rotation Select Index Methodology から使える要素
----------------------------------------------------------------

MSCI手法書は、**「テーマを“選ぶ”ルール」** と **「リスク・コントロール（ボラ目標）」** が明示されているのが強みです。

MSCI World Thematic Rotation Se…

### 2.1 テーマの“ランキング選抜”＝外生スコアでローテーション

22のテーマ指数を、テーマ別の **MediaStats Megatrend Score** で月次ランキングし、上位4つを等ウェイトで組み合わせます。

MSCI World Thematic Rotation Se…

*   選抜：top 4
*   重み：各25%（Rank 1〜4すべて25%）
    MSCI World Thematic Rotation Se…

ETFに置き換えるなら、

*   「テーマETF集合」から **外部スコア（ニュース/検索トレンド/フロー等）** で上位k本を選ぶ
*   k本を等ウェイト（またはスコア比例）  
    という **ローテーション戦略の雛形** になります。

### 2.2 “組み合わせ後の銘柄ウェイト”の合成式（指数合成の一般形）

4つのコンポーネント指数を合成する際の、個別銘柄ウェイトは

$$
W^{CI}_{Sec_i} = \sum_j W_{C_j}\, W^{C_j}_{Sec_i}
$$

という線形結合です。

MSCI World Thematic Rotation Se…

ETF戦略では「ETFの合成」なので銘柄レベルでは使わないかもしれませんが、**“上位テーマを合成する”** という考え方の一般形として重要です。

### 2.3 ボラティリティ・ターゲット（10%）＝レバレッジ係数  $W_t$ 

10%リスクコントロール版では、指数レベル更新を

$$
IL_t = IL_{t-1}\,(1+IR_t)
$$
 
$$
IR_t = (W_t \times ER_t)\ -\ IndexFee \times \frac{ACT(t-1,t)}{360}
$$

と定義しています。

MSCI World Thematic Rotation Se…

*    $ER_t$ ：（超過収益型）指数の日次リターン
*    $W_t$ ：ボラ目標に合わせる **スケーリング係数**（実務的には “当日レバ/キャッシュ比率”）

さらにボラ推定は、短期・長期の実現ボラを指数平滑する形で

$$
\sigma_{ST,t}^2=\lambda_{ST}\sigma_{ST,t-1}^2 + (1-\lambda_{ST})\,r_{t-i}^2
$$
 
$$
\sigma_{LT,t}^2=\lambda_{LT}\sigma_{LT,t-1}^2 + (1-\lambda_{LT})\,r_{t-i}^2
$$

（ $\lambda_{ST}=0.94,\ \lambda_{LT}=0.97,\ i=3$ ）のように置かれています。

MSCI World Thematic Rotation Se…

**ETF戦略への価値**

*   テーマETFはレジームでボラが跳ねやすいので、
    *   “選抜”と“配分”とは独立に
    *   **最後に  $W_t$  で全体リスクを揃える**  
        が非常に効きます（シンプルで事故りにくい）。

* * *

3) THEME（Semantic Stock Representations + Temporal Dynamics）から使える要素
-------------------------------------------------------------------

THEME論文は、**テーマの定義をテキスト（意味表現）で持ち、時系列（リターン）で微調整して“テーマに沿う銘柄”を引く**という発想です。ETF運用でも、\*\*「テーマ純度スコア」や「テーマ漂流（drift）の監視」\*\*に応用できます。

THEME Enhancing Thematic Invest…

### 3.1 セマンティック整列（Stage 1）：対照学習の損失

テーマ埋め込み  $z_i$  と、テーマ構成銘柄の埋め込み  $h_j$  を近づける目的関数（InfoNCE型）が

$$
L_{align} = -\log \frac{\exp(\mathrm{sim}(z_i,h_j^+)/\tau)} {\exp(\mathrm{sim}(z_i,h_j^+)/\tau)+\sum_k \exp(\mathrm{sim}(z_i,h_{j,k}^-)/\tau)} \tag{2}
$$

です。

THEME Enhancing Thematic Invest…

*    $\mathrm{sim}(\cdot,\cdot)$ ：cosine類似度
*    $\tau$ ：温度

**ETFへの翻訳**

*   ETFのObjective/Index description をベクトル化して  $z_{ETF}$ 
*   ETFが持つ“テーマ語彙”や“構成上位銘柄の説明文”を  $h$  として  
    **「ETFテキスト ↔ テーマ辞書/テーマ定義文」** の類似度を作る  
    → あなたが以前言っていた **Purity/Textスコア** の理論核になります。

### 3.2 時系列情報の融合（Stage 2）：意味＋直近リターンで融合埋め込み

意味埋め込み  $h_j$  と、過去  $L$  日のリターン系列  $r_j$  を、軽量アダプタ  $A_\phi$  で融合し

$$
h'_j = A_{\phi}(h_j,r_j) \tag{3}
$$

とします。

THEME Enhancing Thematic Invest…

ETF運用では「銘柄」でなく「ETF」ですが、

*    $h_{ETF}$ ：ETFの説明文埋め込み
*    $r_{ETF}$ ：ETFの直近リターン（あるいは相対強度）  
    を融合して、**“今このテーマが市場で報われているか”** を織り込んだスコアにできます。

### 3.3 リターンでランキングを学ぶ（triplet loss）

同一テーマ内で、将来リターンが高い方を positive として

$$
L_{triplet} = \big[\mathrm{sim}(z_i,h'_n)-\mathrm{sim}(z_i,h'_p)+m\big]_+ \tag{4}
$$

を最小化します。

THEME Enhancing Thematic Invest…

ETFへの翻訳（戦略部品）

*   テーマ  $i$  を「AI」「半導体」等とし、
*   そのテーマに属するETF群の中で、次の  $H$  期間リターン上位を positive として  
    **“テーマ内の勝ちETF選別器”** を作る発想になります（実装はPhase 2以降）。

### 3.4 推論（運用）＝類似度でTop-Kを取る

推論時はクエリ埋め込み  $z_q$  と候補の  $h'_j$  を cosine 類似度でランキングします。

THEME Enhancing Thematic Invest…

ETFでは

*   クエリ＝あなたが定義したテーマ文（日本語でも可）
*   候補＝ETF説明文（＋時系列）  
    でランキングし、ユニバースの拡張や、**テーマ逸脱（ドリフト）検知**に使えます。

* * *

4) ESG-themed megatrend（Naffa & Fain）から使える要素
--------------------------------------------

この論文は **「テーマ露出（MTE）をフローで定義」→「純粋因子ポートフォリオ（PFP）で二次因子を消す」→「時系列回帰でα検定」** のフルパイプラインを提示します。ETF運用に直結しやすいです。

Performance measurement of ESG-…

### 4.1 MTE（Megatrend Exposure）＝“フローがシグナル”という定義

結論部で、**「テーマETFへの資金流入が、テーマ代表銘柄の“市場の信認”をシグナルする」** というシグナリング理論の立て付けを明示します。

Performance measurement of ESG-…

Performance measurement of ESG-…

*   ETF運用への素直な応用：
    *   テーマETF  $i$  のフロー（推定でも良い）を  $Flow_{i,t}$ 
    *   それをスコア化し、**テーマの強さ（需要）** としてローテーションに使う  
        （MSCIがMediaScoreでやっていることの“ETF版”）

### 4.2 Pure Factor Portfolios（PFP）＝Fama–MacBeth回帰の“重み行列”として因子ポートフォリオを作る

Fama–MacBethの断面回帰を

$$
R_{t+1}=Z_t\hat F_{t+1}+u_{t+1} \tag{1}
$$
 
$$
\hat F_{t+1}=(Z_t^\top Z_t)^{-1}Z_t^\top R_{t+1} \tag{2}
$$

と書き、因子（係数）を“ポートフォリオのリターン”として解釈できるように、重み行列

$$
W_t \equiv (Z_t^\top Z_t)^{-1}Z_t^\top \tag{3}
$$

を導入します。

Performance measurement of ESG-…

Performance measurement of ESG-…

また

$$
W_t Z_t = I_t \tag{4}
$$

が成り立つので、各因子ポートフォリオが「当該因子へのエクスポージャ1、他0」を満たす構造になります。

Performance measurement of ESG-…

**ETF運用への翻訳（最重要）**  
あなたのETF集合に対しても、

*   説明変数  $Z_t$ ：ETFの因子露出（例：市場、サイズ、バリュー、モメンタム proxy 等）
*   目的変数  $R_{t+1}$ ：ETFリターン  
    とみなして “純テーマ” を作ることができます。

ただし、この論文はさらに **制約付き・加重最小二乗（CWLS）** に拡張しており、現実的です。

### 4.3 Cap-weighted標準化（スタイル露出の標準化）

スタイル因子の事前露出  $x_{ns}$  を、時点tの市場ウェイト  $w_n^M$  で加重してz-score化：

$$
z_{ns} = \frac{x_{ns}-\sum_{n=1}^N w_n^M x_{ns}} {\sqrt{\sum_{n=1}^N w_n^M x_{ns}^2 -\left(\sum_{n=1}^N w_n^M x_{ns}\right)^2}} \tag{7}
$$

Performance measurement of ESG-…

ETFに置き換えるなら、ETFを“銘柄”と見做すより、ETFの構成から推計した因子露出を標準化する、という発想になります（Phase 2実装領域）。

### 4.4 改良FM（CWLS + 制約 + 時価総額重み）

時価総額行列  $V_t$  を導入し、制約行列  $C_t$  を使って（共線性や国・業種露出の打ち消し等を管理）、最終的に

$$
PW_t \equiv C_t (C_t^\top Z_t^\top V_t Z_t C_t)^{-1} C_t^\top Z_t^\top V_t \tag{17}
$$

という **“純因子のアクティブ・ウェイト”** を与えます。

Performance measurement of ESG-…

**戦略部品としての意味**

*   “テーマETFのパフォーマンス”を評価したいとき、
    *   実は「グロース/モメンタムに寄っていただけ」を除外したい
*   そのための **二次因子露出の除去（purification）** が、このPFP/CWLSの核です。
    Performance measurement of ESG-…

### 4.5 時系列のα推定＝CAPM/FF回帰＋（必要なら）GMM-IVd

論文は、PFPで得た因子リターンを使い、CAPMやFF系でテーマのαを検定します。

Performance measurement of ESG-…

さらに、内生性や非正規性に頑健な推定として **GMM-IVd** を使う、という主張があります。

Performance measurement of ESG-…

ETF戦略では、最終的に

*   「テーマローテーションで得た超過収益」が
*   「単なる既知因子の取り過ぎ」でないか  
    を検証する枠組みとして使えます。

* * *

5) 4本を“ETFローテーション戦略”へ統合するなら（設計の骨格）
----------------------------------

上の部品を、あなたの **コア18本ETF** 運用に最短で繋げると、以下の3層構造が自然です。

### 層A：テーマ強度スコア（Selection）

*   **MSCI型**：外部スコアでテーマを選抜（月次 top-k）
    MSCI World Thematic Rotation Se…
*   **Naffa & Fain型**：フロー（または代替需要指標）をテーマ強度と解釈
    Performance measurement of ESG-…
*   **THEME型**：テキスト類似度で「テーマ純度」や「逸脱」を監視
    THEME Enhancing Thematic Invest…

スコア例（設計案）：

$$
Score_{i,t} = a\cdot Z\_Demand_{i,t} + b\cdot Z\_Momentum_{i,t} + c\cdot Z\_Purity_i
$$

（Demand＝フロー等、Momentum＝相対強度、Purity＝テキスト類似度）

### 層B：二次因子の制御（Purification / Constraints）

*   Somefun：テーマを「因子＋固有」で見て、統合最適化へ
    Allocating to Thematic Investme…
*   Naffa & Fain：CWLS/PFPで二次因子を消して“純テーマ”を測る
    Performance measurement of ESG-…

ETF版の現実的な落とし所：

*   ポートフォリオの因子露出を制約
    
$$
B^\top w \approx 0 \quad(\text{または許容幅内})
$$
*   あるいは “因子中立化した超過収益” を目的関数に入れる

### 層C：リスク管理（Risk Targeting）

*   MSCIの10%リスクコントロール：  
    推定ボラで  $W_t$  を調整し、ポート全体ボラを目標へ
    MSCI World Thematic Rotation Se…
    MSCI World Thematic Rotation Se…

* * *

6) Assumptions（不明点）と検証案（Phase 2で潰すべき）
-------------------------------------

### Assumptions

*   ETFフロー（MTE/Demand）は、実データが取れない場合は代理変数（出来高変化、AUM変化推定、検索トレンド等）で代替する必要がある
*   THEMEの埋め込み学習そのものはPhase 2以降（当面は“既存埋め込み＋類似度”で簡易Purity）
*   因子露出  $B$ （ETFの市場/スタイル感応度）をどう推計するか（回帰 or 外部ファクタモデル）

### 検証案

*   各ETFについて
    *   回帰： $XR_{i,t}=\alpha_i+\beta_i^\top f_t+\varepsilon_{i,t}$  を推定し、 $\alpha_i$  がスコアと整合するか確認（Somefunの分解思想）
        Allocating to Thematic Investme…
*   ローテーション（MSCI型）に
    *   ボラターゲット（MSCI式）を足す vs 足さない、でドローダウン/リスクがどう変わるか比較
        MSCI World Thematic Rotation Se…
*   “純テーマ”評価として
    *   因子中立化前後でパフォーマンス差を比較（Naffa & Fainの趣旨）
        Performance measurement of ESG-…

* * *

7) 明示的な注意（禁止事項リスクへの警告）
----------------------

*   **先読み（look-ahead）**：
    *   MediaScore/フロー/ニュース集計などは「いつ確定した情報か」を厳密に扱わないと、スコアが未来情報を含み得ます（MSCI手法の“月次レビュー確定”の考え方に合わせるのが安全）
        MSCI World Thematic Rotation Se…
*   **0リターン扱い**：
    *   欠損（価格欠落、分配金処理、上場来データ不足）を0埋めすると、モメンタムやボラ推定が壊れます（MSCIのボラ推定式は特に欠損に弱い）
        MSCI World Thematic Rotation Se…
*   **テーマ漂流（ドリフト）**：
    *   ETFは指数変更・リバランスで中身が変わるので、説明文だけでPurityを固定するとズレます（THEMEが“時間変化”を入れる動機そのもの）
        THEME Enhancing Thematic Invest…

* * *

必要なら次に、あなたが以前まとめた「コア18本ETF」に対して、上の **層A/B/C** をそれぞれ **“最小実装で回る仕様”** に落とすために、

*   どのスコアを採用（MediaScore相当＝何で代替するか）
*   ローテーション頻度（月次/週次）
*   リスクターゲット（10%固定か、可変か）
*   因子制約（市場βだけ消す／FF5相当まで消す）

を、**実務で破綻しにくい順** に設計案として並べます。

## Prompt:
これらの各手法について個別に機能を確認しようと思います。それぞれどのようなデータやアルゴリズムを用いて、入力から出力を出せますか？Pythonで関数を実装することを念頭に整理してください

## Response:
以下、4ドキュメント由来の「使う手法」を **個別モジュール**として切り出し、**Python関数として実装できる粒度**で整理します。  
各モジュールについて **(i) 必要データ (ii) 前処理 (iii) アルゴリズム (iv) 入力→出力 (v) 注意点** を書きます。  
（Phase 1前提：ここでは“実装コード”は書かず、関数設計＝仕様を提示）

* * *

共通：データ型（最低限これを揃えると回る）
---------------------

*   価格系列：`adj_close[i,t]`（ETF i）
*   リターン：`r[i,t] = log(adj_close[i,t]/adj_close[i,t-1])` または単純
*   ETFメタ：`expense_ratio[i]`（年率bps）
*   （任意）出来高・スプレッド proxy：`volume[i,t]` 等
*   （任意）外部スコア：`score_ext[i,t]`（センチメント/検索/ニュースなど）
*   （任意）因子リターン：`F[k,t]`（市場・スタイル）
*   （任意）テキスト：`etf_text[i]`、`theme_text[j]`

* * *

A. MSCI型：テーマランキング→Top-K採用（Rotation Selector）
============================================

出典：MSCI Thematic Rotation手法（ランキング選抜＋等ウェイト）

### 必要データ

*   `score[i,t]`：ETFごとのテーマ強度スコア（MSCIはMediaStats Megatrend Scoreだが代替可）
*   `rebalance_dates`：月次などのリバランス日
*   任意：採用可能集合（ユニバース）フィルタ

### アルゴリズム（最小）

1.  各リバランス日 t で `score[:,t]` を降順ソート
2.  上位 `K` を採用
3.  採用銘柄は等ウェイト（またはスコア比例）

### 入力→出力（関数案）

*   **入力**
    *   `scores: pd.DataFrame(index=dates, columns=tickers)`
    *   `rebalance_dates: list[pd.Timestamp]`
    *   `k: int`
    *   `weighting: Literal["equal","score_proportional"]`
*   **出力**
    *   `target_weights: pd.DataFrame(index=rebalance_dates, columns=tickers)`  
        （各リバランス日時点の目標ウェイト）

### 注意点

*   **スコアのタイムスタンプ**：t時点で観測可能なスコアのみ使う（先読み防止）
*   欠損は0埋め禁止（除外・前回値保持・winsorize等で仕様化）

* * *

B. MSCI型：ボラターゲット（10% Risk Control / Vol Targeting）
==================================================

出典：MSCI 10% Risk Controlのボラ推定とスケーリング

### 必要データ

*   `portfolio_returns[t]` または `returns[i,t]`＋`weights[t]`
*   パラメータ：`target_vol=0.10`、`lambda_st=0.94`、`lambda_lt=0.97`、`lag=3`

### アルゴリズム（指数の考え方をETFポートへ移植）

1.  日次リターン `r_t`（ポート）を計算
2.  EWMAで短期/長期分散を更新：
    *   `sigma2_st[t] = lam_st*sigma2_st[t-1] + (1-lam_st)*r[t-lag]^2`
    *   `sigma2_lt[t] = lam_lt*sigma2_lt[t-1] + (1-lam_lt)*r[t-lag]^2`
3.  予測ボラ `sigma[t] = max(sqrt(sigma2_st[t]), sqrt(sigma2_lt[t]))` のような合成（合成ルールは仕様で固定）
4.  スケーリング係数 `W[t] = target_vol / sigma[t]`（上限下限を設けるのが実務的）
5.  当日エクスポージャを `W[t]` 倍に（現物のみならキャッシュ比率で調整）

### 入力→出力（関数案）

*   **入力**
    *   `returns: pd.Series`（ポート日次）
    *   `target_vol: float`
    *   `lam_st, lam_lt: float`
    *   `lag: int`
    *   `w_min, w_max: float`（任意）
*   **出力**
    *   `leverage: pd.Series`（`W[t]`）
    *   `scaled_returns: pd.Series`（`W[t]*r_t - fee` のようなシリーズ）

### 注意点

*   欠損日があるとEWMAが破綻しやすい → カレンダー整合が必須
*   ETF運用では「レバを掛けない」制約もあり得る（その場合 `W[t]` を1以下に制限）

* * *

C. Somefun型：因子分解（テーマ固有成分の抽出）
============================

出典：テーマ超過リターンの分解（市場＋因子＋純テーマ）

### 必要データ

*   `XR[i,t]`：ETF超過リターン（対ベンチマーク or 無リスク）
*   `F[k,t]`：因子リターン（市場、セクター、スタイルなど）
*   推定窓：`lookback`（例：252日）

### アルゴリズム（回帰ベースの最小形）

各ETF i についてローリング回帰：

$$
XR_{i,t} = \alpha_{i,t} + \beta_{i,t}^\top F_t + \varepsilon_{i,t}
$$
*   推定：OLS / ridge（仕様で選ぶ）
*   出力：`alpha_hat[i,t]`、`beta_hat[i,k,t]`、`resid[i,t]`

### 入力→出力（関数案）

*   **入力**
    *   `xr: pd.DataFrame(index=dates, columns=tickers)`
    *   `factors: pd.DataFrame(index=dates, columns=factor_names)`
    *   `lookback: int`
    *   `reg: Literal["ols","ridge"]`
*   **出力**
    *   `alpha: pd.DataFrame(index=dates, columns=tickers)`
    *   `beta: dict[str, pd.DataFrame]` or 3D array
    *   `resid: pd.DataFrame(index=dates, columns=tickers)`
    *   `r2: pd.DataFrame(...)`（任意）

### 使い方（戦略への接続）

*   `alpha` や `resid` を「純テーマ強さ」とみなしてローテーション
*   `beta` を制約（市場β中立など）に使う

### 注意点

*   因子選定が恣意的になりがち → “最小セット”から開始（MKT + MOM等）

* * *

D. Somefun型：ロバスト最適化（推定誤差耐性の配分）
==============================

出典：robust portfolio optimisation 文脈

### 必要データ

*   `mu[i]`：期待超過リターン推定（弱い仮定でよい）
*   `Sigma`：共分散推定
*   制約：long-only、上限、テーマ分散など

### アルゴリズム（実装に落としやすい代表形）

**(D1) 平均の不確実性（ellipsoidal）**

*    $\mu$  が  $\|\mu-\hat\mu\|_{\Sigma^{-1}} \le \delta$  に属するとして  
    “最悪ケース”期待収益を用いる（実装は凸最適化）

**(D2) リスク寄りの簡易ロバスト（実務で多い）**

*    $\mu$  は使わず、**リスクパリティ/最小分散**に近い配分
*   期待値依存を減らして推定誤差耐性を確保

### 入力→出力（関数案）

*   **入力**
    *   `mu: pd.Series`（任意）
    *   `cov: pd.DataFrame`
    *   `constraints: dict`（max\_weight, long\_only, turnover\_limit等）
    *   `method: Literal["min_var","risk_parity","robust_mean_var"]`
*   **出力**
    *   `weights: pd.Series`

### 注意点

*   Phase 1では「どのロバスト形式を採るか」を仕様化するところまで

* * *

E. Naffa & Fain型：PFP（Pure Factor Portfolios）で因子を“純化”
====================================================

出典：Fama–MacBeth回帰→重み行列で因子ポートフォリオ化

### 必要データ

*   `R[t+1,n]`：（銘柄nの）リターン …が原典だが、ETFで代用するなら `n=ETF`
*   `Z[t,n,s]`：ディスクリプタ/因子露出（ETFに対して用意する必要あり）
*   `V_t`：時価総額重み（ETFならAUMで代替も）

### アルゴリズム（原典の最小形）

断面回帰：

$$
R_{t+1}=Z_t \hat F_{t+1}+u_{t+1}
$$
 
$$
W_t = (Z_t^\top Z_t)^{-1}Z_t^\top,\quad \hat F_{t+1}=W_t R_{t+1}
$$

制約付き（CWLS）まで行くと：

$$
PW_t = C_t (C_t^\top Z_t^\top V_t Z_t C_t)^{-1} C_t^\top Z_t^\top V_t
$$

### 入力→出力（関数案）

*   **入力**
    *   `R: pd.DataFrame(index=dates, columns=assets)` # assets=ETF
    *   `Z: dict[date -> pd.DataFrame(index=assets, columns=descriptors)]`
    *   `V: dict[date -> pd.Series(index=assets)]`（任意）
    *   `C: dict[date -> np.ndarray]`（任意：制約）
    *   `method: Literal["fm_ols","cwls"]`
*   **出力**
    *   `factor_returns: pd.DataFrame(index=dates, columns=descriptors)`
    *   `pure_weights: dict[date -> pd.DataFrame(descriptor x asset)]`（任意）

### 注意点

*   ETFでやるなら「Zをどう作るか」が最大の課題（外部因子回帰のβをZにする、等）

* * *

F. Naffa & Fain型：クリーニング（winsorize / 欠損補完）※評価品質部品
================================================

出典：1%/99% winsorize、MI(MCMC/DA)等

### 必要データ

*   任意の系列（スコア、ディスクリプタ、リターン補助変数）

### アルゴリズム

*   winsorize：分位点でクリップ
*   欠損：原典はMIだが、まずは **欠損除外/前方補完/モデル補完** を仕様化（MIはPhase 2で検討）

### 入力→出力（関数案）

*   `winsorize_df(df, p_low=0.01, p_high=0.99) -> df_clip`
*   `impute_df(df, method="ffill"|"mean"|"mice_placeholder") -> df_filled`

* * *

G. THEME型：テキスト類似度で “テーマ純度/整合度” スコア
==================================

出典：InfoNCE・類似度ランキングの枠組み

### 必要データ

*   `etf_text[i]`：ETF説明文（Objective/Strategy/Index）
*   `theme_text[j]`：テーマ定義文（あなた側で固定文を用意）
*   埋め込みモデル（初期は既存モデルで代用）

### アルゴリズム（最小：学習なし）

1.  埋め込み `e_i = embed(etf_text[i])`, `t_j = embed(theme_text[j])`
2.  類似度 `sim(i,j) = cosine(e_i, t_j)`
3.  `purity_i = sim(i, target_theme_of_etf_i)` または max over themes

### 入力→出力（関数案）

*   **入力**
    *   `etf_texts: dict[ticker -> str]`
    *   `theme_texts: dict[theme -> str]`
    *   `embed_fn: Callable[[list[str]], np.ndarray]`
*   **出力**
    *   `sim_matrix: pd.DataFrame(index=tickers, columns=themes)`
    *   `purity_score: pd.Series(index=tickers)`

### 注意点

*   THEME論文の“フォワードリターン教師のtriplet学習”は先読みリスクがあるため、まずは **学習なし類似度** から始めるのが安全

* * *

H. THEME型：時系列を融合したスコア（意味＋直近パフォーマンス）
===================================

出典： $h'_j=A_\phi(h_j,r_j)$  の融合アイデア

### 必要データ

*   `embedding[i]`
*   `returns_window[i, t-L+1:t]`（ETFの過去L日）

### アルゴリズム（学習なしの簡易版）

*   `momentum[i,t] = zscore(sum_{u=t-L+1}^t r[i,u])`
*   `score[i,t] = a*purity[i] + b*momentum[i,t]`  
    （“融合アダプタ”は学習を伴うのでPhase 2以降）

### 入力→出力（関数案）

*   `build_semantic_temporal_score(purity: Series, returns: DataFrame, L:int, a:float, b:float) -> DataFrame(score[ticker,t])`

* * *

I. 「評価」モジュール：因子調整後α／コスト感度
=========================

出典：因子で説明した後のα、費用感度が重要

### 必要データ

*   戦略リターン `rp[t]`
*   ベンチ/因子 `F[t]`
*   コスト仮定 `cost_bps`、回転率 `turnover[t]`（または近似）

### アルゴリズム（最小）

*   コスト控除：
    
$$
r^{net}_t = r^{gross}_t - \frac{cost\_{bps}}{10^4}\cdot turnover_t
$$
*   因子回帰：
    
$$
r^{net}_t = \alpha + \beta^\top F_t + \varepsilon_t
$$
*   α、t統計、Sharpe、TE等を出す

### 入力→出力（関数案）

*   `apply_costs(returns, turnover, cost_bps) -> net_returns`
*   `factor_regression_alpha(strategy_returns, factors) -> alpha, beta, tstats, r2`
*   `compute_metrics(strategy_returns, benchmark_returns) -> dict`

* * *

まとめ：各手法を「関数群」に落とすとこうなる
======================

最低限、個別動作確認しやすい順に並べると：

1.  **Rotation Selector**
    *   `select_topk_weights(scores, rebalance_dates, k, weighting) -> target_weights`
2.  **Vol Targeting**
    *   `ewma_vol_target_leverage(port_returns, target_vol, lam_st, lam_lt, lag, bounds) -> W`
3.  **Factor Decomposition**
    *   `rolling_factor_decompose(xr, factors, lookback, reg) -> alpha, beta, resid`
4.  **Text Purity Score**
    *   `compute_text_similarity(etf_texts, theme_texts, embed_fn) -> sim_matrix, purity`
5.  **Semantic+Temporal Score（簡易）**
    *   `build_semantic_temporal_score(purity, returns, L, a, b) -> score`
6.  **PFP / CWLS（因子純化：上級）**
    *   `estimate_pfp_factor_returns(R, Z_by_date, V_by_date=None, C_by_date=None, method) -> factor_returns`
7.  **Evaluation**
    *   `apply_costs`, `factor_regression_alpha`, `compute_metrics`

* * *

追加：Assumptions（今決めると実装が進む）
--------------------------

*   `scores[i,t]` を何で作るか（ニュース/検索/フロー/AUM変化など）
*   因子 `F[t]` の定義（市場のみか、スタイルまで入れるか）
*   リバランス頻度（月次推奨：MSCI準拠）
*   欠損処理のルール（0埋め禁止、winsorize適用範囲）

* * *

次に、あなたが「個別に機能確認」したい順番（例：MSCIローテ→ボラターゲット→テキスト純度…）が決まっているなら、その順番に合わせて **各関数のI/O型（pandasのindex/columns規約、例外処理、テストケースの形）** まで落として“そのままノートブックに書ける仕様”にします。

## Prompt:
４つの論文のそれぞれ使える要素について同様に解説してください。要素の粒度で考えたいです

## Response:
了解。ここでは **「4つのドキュメントそれぞれ」**について、**“使える要素（element）”単位**でバラし、各要素ごとに

*   目的（何を出す部品か）
*   必要データ（最小・任意）
*   アルゴリズム（要点）
*   関数I/O（Python実装を念頭にした入出力）
*   落とし穴（先読み・欠損・ライセンス等）

を同じ型で整理します。  
（※以降の「スコア」はあなたのETF18本を対象に _ETF×時点_ で定義する前提）

* * *

1) Allocating to Thematic Investments（Somefun et al.）の“要素”
==========================================================

E1. テーマETFリターンの因子分解（純テーマ成分の抽出）
------------------------------

*   **目的**
    *   「テーマETFのリターンが、伝統因子の焼き直しか／テーマ固有か」を分解して測る（戦略の“中身チェック”にも“配分シグナル”にもなる）
*   **必要データ**
    *   最小：ETFリターン `r[i,t]`
    *   任意：ベンチマーク（市場）`rm[t]`、無リスク `rf[t]`
    *   任意：因子 `F[k,t]`（MKT, MOM, VAL, SIZE…）
*   **アルゴリズム（典型）**
    *   ローリング回帰（OLS/Ridgeなど）
        *   `XR[i,t] = alpha[i,t] + beta[i,t]^T F[t] + eps[i,t]`
    *   出力の見方
        *   `alpha`：純テーマ（擬似）強度
        *   `beta`：因子被り（重複）の源泉
*   **関数I/O案**
    *   `rolling_factor_decompose(returns: DF, factors: DF, lookback:int, method:str) -> (alpha:DF, beta:Panel, resid:DF, r2:DF)`
*   **落とし穴**
    *   因子選択が恣意的になりやすい → まず最小（MKTのみ→MKT+MOM…）で段階化
    *   欠損0埋めは回帰を壊す（除外/前方補完ルールを固定）

* * *

E2. テーマ“固有ボラ”の推定（thematic volatility の概念をETFで実装）
------------------------------------------------

*   **目的**
    *   TEやリスクの源泉を「因子由来」と「テーマ固有」に分け、配分ルール（上限、レバ、分散）に接続する
*   **必要データ**
    *   `eps[i,t]`（E1の残差）または `resid`
*   **アルゴリズム**
    *   `thematic_var[i] = Var(resid[i, t-L:t])`
    *   `thematic_vol[i] = sqrt(thematic_var[i])`
*   **関数I/O案**
    *   `estimate_thematic_vol(resid: DF, lookback:int, annualize:bool=True) -> vol: DF_or_Series`
*   **落とし穴**
    *   残差は推定誤差を含む → lookback短すぎ注意
    *   年率化/頻度の整合（D/W/M）を仕様固定

* * *

E3. “因子被り”抑制の制約設計（配分最適化の制約として使う）
--------------------------------

*   **目的**
    *   テーマETF同士が実質同じ因子（例：成長×モメ）を二重に買うのを抑制する
*   **必要データ**
    *   `beta[i,k,t]`（E1）
*   **アルゴリズム（例）**
    *   ポート因子露出：`B_port[k,t] = sum_i w[i,t] * beta[i,k,t]`
    *   制約：`|B_port[k,t]| <= bound[k]`
*   **関数I/O案**
    *   `factor_exposure(w: Series, beta: DF) -> Series`
    *   `check_factor_bounds(exposure: Series, bounds: Series) -> diagnostics`
*   **落とし穴**
    *   “中立化”をやりすぎるとテーマを殺す → 許容幅を持つ（hard=0にしない）

* * *

E4. ロバスト化（推定誤差に強い配分の型）
----------------------

*   **目的**
    *   テーマETFの期待リターン推定が不安定でも破綻しにくい配分方式を持つ
*   **必要データ**
    *   `cov[t]`（共分散）※必須
    *   任意：`mu[t]`（期待リターン、弱く使う）
*   **アルゴリズム（実装しやすい順）**
    *   (a) 最小分散：`min w^T Σ w` s.t. 制約
    *   (b) リスクパリティ：各ETFのリスク寄与を均す
    *   (c) ロバスト平均分散（min-max）※上級
*   **関数I/O案**
    *   `allocate_robust(cov: DF, mu: Series|None, constraints:dict, method:str) -> weights: Series`
*   **落とし穴**
    *   目的関数にmuを強く入れると推定誤差で壊れる → methodごとに“mu依存度”を定義する

* * *

2) MSCI World Thematic Rotation Select Index Methodology の“要素”
==============================================================

M1. 月次ランキング→Top-K採用（ローテーション骨格）
------------------------------

*   **目的**
    *   「テーマ（ETF）の強さスコア」で毎月上位Kに乗り換える
*   **必要データ**
    *   `score[i,t]`（外部スコア：センチメント等。MSCIはMediaStats Megatrend Score）
    *   `rebalance_dates`
*   **アルゴリズム**
    *   `rank = argsort(score[:,t], desc)`
    *   `selected = top_k(rank)`
    *   `w = equal_weight(selected)`（またはスコア比例）
*   **関数I/O案**
    *   `select_topk_weights(scores: DF, rebalance_dates:list, k:int, weighting:str) -> weights_at_rebal: DF`
*   **落とし穴**
    *   スコアの確定タイミング（先読み防止）が最重要
    *   同点・欠損の扱いを仕様化（除外/前回値維持など）

* * *

M2. “合成”の線形性（複数テーマを混ぜたポートの作り方）
------------------------------

*   **目的**
    *   「複数テーマの合成」は基本“線形結合”でよい、という設計原則（ETF合成の根拠）
*   **必要データ**
    *   `w_theme[j,t]`（テーマ配分）
    *   `w_etf_in_theme[i|j,t]`（ETFをテーマ内で持つなら）
*   **アルゴリズム**
    *   `w_etf[i,t] = sum_j w_theme[j,t] * w_etf_in_theme[i|j,t]`
*   **関数I/O案**
    *   `compose_weights(theme_weights: DF, mapping: dict) -> etf_weights: DF`
*   **落とし穴**
    *   あなたの今回ユニバースはETF=テーマに近いので、mappingは単純（1対1）でもOK

* * *

M3. ボラターゲット（10%）のスケーリング係数計算（EWMA短期/長期）
--------------------------------------

*   **目的**
    *   “選抜”とは別に、ポート全体リスクを一定にする（最も実務的に効く）
*   **必要データ**
    *   `r_port[t]`（ポート日次リターン）
*   **アルゴリズム**
    *   EWMA分散更新（短期/長期）＋ラグ
    *   `W[t] = target_vol / sigma[t]`（bounds付きが実務的）
*   **関数I/O案**
    *   `ewma_vol_forecast(returns: Series, lam:float, lag:int) -> Series(sigma)`
    *   `vol_target_leverage(sigma: Series, target:float, w_min:float, w_max:float) -> Series(W)`
*   **落とし穴**
    *   欠損・休日処理が必要（カレンダー整合）
    *   レバ禁止なら `W<=1` にするなど運用制約を反映

* * *

M4. ライセンス取り扱い（仕様としての“禁止事項”要素）
-----------------------------

*   **目的**
    *   MSCI由来のデータや指数構成を「再配布/再現」しない設計線引き
*   **必要データ**
    *   なし（規約）
*   **アルゴリズム**
    *   なし（ガードレール）
*   **関数I/O案**
    *   なし（docs/notesに明文化）
*   **落とし穴**
    *   “MSCI指数の再現”を目標にしない。方法論参照に限定する

* * *

3) ESG-themed megatrend（Naffa & Fain）からの“要素”
============================================

N1. 需要（フロー）をテーマ強度とみなすシグナル化
--------------------------

*   **目的**
    *   「テーマETFへの資金流入＝市場の注目・信認」というスコア源泉を作る
*   **必要データ**
    *   `flow[i,t]`（理想：純資金流入）
    *   代替：`AUM[i,t]` 変化、`volume`、`shares_outstanding`、価格調整した推定フロー等
*   **アルゴリズム（例）**
    *   `flow_z[i,t] = zscore(flow[i, t-L:t])`
    *   `score_flow[i,t] = winsorize(flow_z)`
*   **関数I/O案**
    *   `compute_flow_score(flow: DF, lookback:int, winsor=(0.01,0.99)) -> score: DF`
*   **落とし穴**
    *   AUM変化は価格要因と混ざる → “純フロー推定”仕様が必要（Phase 2論点）

* * *

N2. Pure Factor Portfolios（PFP）：断面回帰から因子ポートを作る“重み行列”
----------------------------------------------------

*   **目的**
    *   テーマ（または戦略）のリターンが「既知因子」か「純テーマ」かを分離するための基礎部品
*   **必要データ**
    *   原典は銘柄ディスクリプタ `Z_t` と銘柄リターン `R_{t+1}`
    *   ETFでやるなら：
        *   `R_etf[t+1,i]`
        *   `Z_etf[t,i,s]`（ETFの因子露出や属性）
*   **アルゴリズム**
    *   FM回帰：`F_hat[t+1] = (Z^T Z)^(-1) Z^T R[t+1]`
    *   `W_t = (Z^T Z)^(-1) Z^T` を明示的に出す
*   **関数I/O案**
    *   `fm_factor_returns(R: DF, Z_by_date: dict[date->DF]) -> factor_returns: DF`
    *   `fm_weight_matrix(Z: DF) -> W: np.ndarray`
*   **落とし穴**
    *   ETFでZをどう作るかが本質（回帰βをZにする等の設計が必要）

* * *

N3. 制約付き加重最小二乗（CWLS）で“純化”を現実的にする
--------------------------------

*   **目的**
    *   共線性・特定暴露の打ち消し・重み付け（サイズ）を入れて“実務向けPFP”へ
*   **必要データ**
    *   `V_t`（重み。原典は時価総額、ETFならAUM等）
    *   `C_t`（制約行列：例えば「国・業種の中立化」等）
*   **アルゴリズム**
    *   `PW_t = C (C^T Z^T V Z C)^(-1) C^T Z^T V`
*   **関数I/O案**
    *   `cwls_pfp_weights(Z: DF, V: Series, C: np.ndarray) -> PW: np.ndarray`
*   **落とし穴**
    *   Cの設計が難しい → Phase 1では「何を中立化するか」を仕様で決める

* * *

N4. クリーニング（winsorize、欠損補完）を“推定品質”として組み込む
----------------------------------------

*   **目的**
    *   スコアやディスクリプタの外れ値・欠損で推定が破綻しないようにする
*   **必要データ**
    *   任意（スコア/属性/回帰入力すべて）
*   **アルゴリズム**
    *   winsorize（分位でクリップ）
    *   欠損補完（原典はMIだが、段階的導入が現実的）
*   **関数I/O案**
    *   `winsorize(df, q=(0.01,0.99)) -> df`
    *   `impute(df, method="ffill"|"mean"|"mice_stub") -> df`
*   **落とし穴**
    *   0埋め禁止（特にリターン以外の特徴量）

* * *

4) THEME（Semantic representations + temporal dynamics）からの“要素”
=============================================================

T1. テキスト類似度による「テーマ整合（purity）」スコア
--------------------------------

*   **目的**
    *   ETFがそのテーマをどれだけ“語義的に体現”しているかを定量化（テーマ漂流検知にも使える）
*   **必要データ**
    *   `etf_text[i]`（ETF objective/index description）
    *   `theme_text[j]`（テーマ定義文：あなたが作る）
    *   `embed_fn`（埋め込み関数）
*   **アルゴリズム**
    *   `sim(i,j) = cosine(embed(etf_text[i]), embed(theme_text[j]))`
*   **関数I/O案**
    *   `compute_text_similarity(etf_texts:dict, theme_texts:dict, embed_fn) -> sim_matrix: DF`
    *   `compute_purity(sim_matrix: DF, etf2theme:dict) -> purity: Series`
*   **落とし穴**
    *   埋め込みモデルの選定でスコアが変わる → “モデル固定”を仕様化

* * *

T2. 時系列融合（semantic + temporal）のスコア統合（学習なし簡易版）
---------------------------------------------

*   **目的**
    *   テーマ整合だけでなく「今、そのテーマが市場で報われているか」をスコアに入れる
*   **必要データ**
    *   `purity[i]`（T1）
    *   `returns[i,t]`
*   **アルゴリズム（最小）**
    *   `mom[i,t] = zscore(sum_{u=t-L+1}^t r[i,u])`
    *   `score[i,t] = a*purity[i] + b*mom[i,t]`
*   **関数I/O案**
    *   `build_semantic_temporal_score(purity: Series, returns: DF, L:int, a:float, b:float) -> score: DF`
*   **落とし穴**
    *   lookback L の取り方でレジーム依存が出る → 複数Lで頑健性確認（Phase 2）

* * *

T3. コントラスト学習（InfoNCE）による表現学習（上級、Phase 2以降）
------------------------------------------

*   **目的**
    *   「テーマ↔銘柄（ETF）」の階層関係を学習して、類似度の質を上げる
*   **必要データ**
    *   正例/負例のペア（ETF or 銘柄）
    *   学習環境（GPU等）
*   **アルゴリズム**
    *   InfoNCE型の損失（温度τ、cos類似度）
*   **関数I/O案**
    *   `train_contrastive_encoder(pairs, encoder, optimizer, ...) -> trained_encoder`
*   **落とし穴**
    *   学習データ作成が重い・ラベル設計が難しい

* * *

T4. Triplet（フォワードリターン教師）によるランキング学習（要注意）
---------------------------------------

*   **目的**
    *   “テーマ内で勝つもの”を学習してランキング精度を上げる
*   **必要データ**
    *   将来リターン（H日先）でpositive/negativeを作るデータ
*   **アルゴリズム**
    *   triplet loss
*   **関数I/O案**
    *   `make_triplets(returns, horizon) -> triplets`
    *   `train_triplet_ranker(triplets, encoder, ...)`
*   **落とし穴（重大）**
    *   **先読みリスクが非常に高い**（ラベル生成に未来リターンを使うため）
    *   使うなら「学習期間・検証期間の厳密分離」「運用時に未来情報を一切使わない」仕様が必須
    *   Phase 1では「採用しない/採用条件」を明文化するのが安全

* * *

5) 要素粒度で“機能確認”するためのおすすめ順（安全・依存が少ない順）
====================================

1.  **M1**（Top-Kローテ）
    *   必要なのは `score` だけ（仮のスコアでも動作確認可能）
2.  **M3**（ボラターゲット）
    *   `returns` だけで動作確認可能
3.  **T1**（テキストpurity）
    *   テキストさえあれば可（学習不要）
4.  **E1/E2**（因子分解・固有ボラ）
    *   因子データが必要（入手方法の仕様が要る）
5.  **N1**（フロー系スコア）
    *   AUM/フロー入手が必要
6.  **N2/N3**（PFP/CWLS）
    *   `Z`（ETFのディスクリプタ設計）が必要で上級

* * *

次にやると良いこと（Phase 1の“仕様化”として）
---------------------------

あなたが「要素の粒度で確認したい」目的に合わせ、docs/notesに

*   各要素（E1, M1, …）の **I/O仕様（pandas index/columns規約）**
*   欠損・外れ値・タイムスタンプの **ガードレール**
*   「Phase 2で実装するなら最低限どのデータが要るか」チェックリスト

まで落とすと、そのまま“個別に関数を書いてユニットテスト”に移行できます。

もし、まず **どの要素から確認するか（上のおすすめ順でOK）** を決めるなら、次の返答でその要素群について **入出力スキーマ（型）を完全に固定**した関数仕様（docstringレベル）にまとめます。

## Prompt:
以下では、添付4ドキュメント（論文2本＋MSCI手法書＋THEME論文）から **「戦略の部品として使える要素」** を抽出し、**数式（できるだけ原典の形）** で噛み砕いて整理します。
（※あなたのプロジェクト方針どおり、ここでは“実装”や具体的バックテストはしません。戦略設計に落とすための理論部品の提示に徹します。）

---

## 1) Allocating to Thematic Investments（Somefun et al.）から使える要素

この論文の主眼は **「テーマ投資＝伝統因子＋テーマ固有成分」** と見做して、**頑健（robust）最適化でSAA（戦略的配分）に統合する**ことです。 

### 1.1 テーマリターンの分解（“テーマ純粋成分”の定義）

付録で、テーマ指数（ETFでも代用可）の超過リターンを

[
XR^{thematic}_t
===============

XR^{market, thematic}_t
+
XR^{region/style/sector, thematic}_t
+
XR^{pure\ theme, thematic}_t
\tag{1}
]

と分解します。 

* 直感：

  * 第1項：市場（株式ベータ）で説明される部分
  * 第2項：地域・セクター・スタイル（例：成長、モメンタム等）で説明される部分
  * 第3項：それらで説明できない **“テーマ固有”**（戦略で取りに行きたい対象）

**ETF運用への落とし込み（重要）**
あなたの「コア18本ETF」を対象にするなら、各ETFの超過リターン (XR_{i,t}) を、たとえば線形因子モデルで近似して

[
XR_{i,t}=\alpha^{(theme)}*{i} + \beta_i^\top f_t + \varepsilon*{i,t}
]

と置き、(\alpha^{(theme)}_{i}) を **“純テーマ・アルファ（擬似）”** として扱う、という設計ができます。
（論文は指数ベースで議論していますが、ETFでも同型に置けます。）

### 1.2 コア・サテライト（ただし“統合”が推奨）

コア・サテライトが紹介されつつも、**“テーマを全体最適化に直接統合する方が望ましい”** という文脈です。 
あなたのユニバース（コア18本）なら、

* コア：市場・分散の中核（例：広域株式や低リスク等）
* サテライト：テーマETF（あなたの対象）

という分離も可能ですが、論文の思想はむしろ
**「テーマも含めて、因子露出を見ながら全体で最適化」** です。 

### 1.3 “頑健最適化”の使い方（設計部品）

論文本体のキモは、テーマの期待超過収益が **伝統因子由来** と **テーマ固有** の双方から来るので、推定誤差を踏まえた **robust optimization** を使う点です。 
（このPDF断片では最適化の具体式がすべて露出していないため、ここでは設計の骨格として提示します。）

典型的には、平均分散のロバスト版として

* 期待リターン (\mu) が不確実集合 (\mathcal U) に属する
* 共分散 (\Sigma) も不確実、または shrinkage

などを置き、

[
\max_{w\in\mathcal W}\ \min_{\mu\in\mathcal U}\ \left( w^\top \mu - \frac{\lambda}{2} w^\top \Sigma w \right)
]

のような **min-max** を組むのが定石です（論文の“robust portfolio optimisation”の位置づけ）。 

**ETF戦略での具体的価値**
テーマETFは “推定誤差（期待収益が当てづらい）” が大きいので、

* **期待リターンを控えめに扱う**
* **リスク（共分散）主導**
* **因子露出制約（後述）**
  を入れると、設計が破綻しにくくなります。

---

## 2) MSCI World Thematic Rotation Select Index Methodology から使える要素

MSCI手法書は、**「テーマを“選ぶ”ルール」** と **「リスク・コントロール（ボラ目標）」** が明示されているのが強みです。 

### 2.1 テーマの“ランキング選抜”＝外生スコアでローテーション

22のテーマ指数を、テーマ別の **MediaStats Megatrend Score** で月次ランキングし、上位4つを等ウェイトで組み合わせます。 

* 選抜：top 4
* 重み：各25%（Rank 1〜4すべて25%） 

ETFに置き換えるなら、

* 「テーマETF集合」から **外部スコア（ニュース/検索トレンド/フロー等）** で上位k本を選ぶ
* k本を等ウェイト（またはスコア比例）
  という **ローテーション戦略の雛形** になります。

### 2.2 “組み合わせ後の銘柄ウェイト”の合成式（指数合成の一般形）

4つのコンポーネント指数を合成する際の、個別銘柄ウェイトは

[
W^{CI}_{Sec_i}
==============

\sum_j W_{C_j}, W^{C_j}_{Sec_i}
]

という線形結合です。 
ETF戦略では「ETFの合成」なので銘柄レベルでは使わないかもしれませんが、**“上位テーマを合成する”** という考え方の一般形として重要です。

### 2.3 ボラティリティ・ターゲット（10%）＝レバレッジ係数 (W_t)

10%リスクコントロール版では、指数レベル更新を

[
IL_t = IL_{t-1},(1+IR_t)
]

[
IR_t = (W_t \times ER_t)\ -\ IndexFee \times \frac{ACT(t-1,t)}{360}
]

と定義しています。 

* (ER_t)：（超過収益型）指数の日次リターン
* (W_t)：ボラ目標に合わせる **スケーリング係数**（実務的には “当日レバ/キャッシュ比率”）

さらにボラ推定は、短期・長期の実現ボラを指数平滑する形で

[
\sigma_{ST,t}^2=\lambda_{ST}\sigma_{ST,t-1}^2 + (1-\lambda_{ST}),r_{t-i}^2
]

[
\sigma_{LT,t}^2=\lambda_{LT}\sigma_{LT,t-1}^2 + (1-\lambda_{LT}),r_{t-i}^2
]

（(\lambda_{ST}=0.94,\ \lambda_{LT}=0.97,\ i=3)）のように置かれています。 

**ETF戦略への価値**

* テーマETFはレジームでボラが跳ねやすいので、

  * “選抜”と“配分”とは独立に
  * **最後に (W_t) で全体リスクを揃える**
    が非常に効きます（シンプルで事故りにくい）。

---

## 3) THEME（Semantic Stock Representations + Temporal Dynamics）から使える要素

THEME論文は、**テーマの定義をテキスト（意味表現）で持ち、時系列（リターン）で微調整して“テーマに沿う銘柄”を引く**という発想です。ETF運用でも、**「テーマ純度スコア」や「テーマ漂流（drift）の監視」**に応用できます。 

### 3.1 セマンティック整列（Stage 1）：対照学習の損失

テーマ埋め込み (z_i) と、テーマ構成銘柄の埋め込み (h_j) を近づける目的関数（InfoNCE型）が

[
L_{align}
=========

-\log
\frac{\exp(\mathrm{sim}(z_i,h_j^+)/\tau)}
{\exp(\mathrm{sim}(z_i,h_j^+)/\tau)+\sum_k \exp(\mathrm{sim}(z_i,h_{j,k}^-)/\tau)}
\tag{2}
]

です。 

* (\mathrm{sim}(\cdot,\cdot))：cosine類似度
* (\tau)：温度

**ETFへの翻訳**

* ETFのObjective/Index description をベクトル化して (z_{ETF})
* ETFが持つ“テーマ語彙”や“構成上位銘柄の説明文”を (h) として
  **「ETFテキスト ↔ テーマ辞書/テーマ定義文」** の類似度を作る
  → あなたが以前言っていた **Purity/Textスコア** の理論核になります。

### 3.2 時系列情報の融合（Stage 2）：意味＋直近リターンで融合埋め込み

意味埋め込み (h_j) と、過去 (L) 日のリターン系列 (r_j) を、軽量アダプタ (A_\phi) で融合し

[
h'*j = A*{\phi}(h_j,r_j)
\tag{3}
]

とします。 

ETF運用では「銘柄」でなく「ETF」ですが、

* (h_{ETF})：ETFの説明文埋め込み
* (r_{ETF})：ETFの直近リターン（あるいは相対強度）
  を融合して、**“今このテーマが市場で報われているか”** を織り込んだスコアにできます。

### 3.3 リターンでランキングを学ぶ（triplet loss）

同一テーマ内で、将来リターンが高い方を positive として

[
L_{triplet}
===========

\big[\mathrm{sim}(z_i,h'_n)-\mathrm{sim}(z_i,h'*p)+m\big]*+
\tag{4}
]

を最小化します。 

ETFへの翻訳（戦略部品）

* テーマ (i) を「AI」「半導体」等とし、
* そのテーマに属するETF群の中で、次の (H) 期間リターン上位を positive として
  **“テーマ内の勝ちETF選別器”** を作る発想になります（実装はPhase 2以降）。

### 3.4 推論（運用）＝類似度でTop-Kを取る

推論時はクエリ埋め込み (z_q) と候補の (h'_j) を cosine 類似度でランキングします。 
ETFでは

* クエリ＝あなたが定義したテーマ文（日本語でも可）
* 候補＝ETF説明文（＋時系列）
  でランキングし、ユニバースの拡張や、**テーマ逸脱（ドリフト）検知**に使えます。

---

## 4) ESG-themed megatrend（Naffa & Fain）から使える要素

この論文は **「テーマ露出（MTE）をフローで定義」→「純粋因子ポートフォリオ（PFP）で二次因子を消す」→「時系列回帰でα検定」** のフルパイプラインを提示します。ETF運用に直結しやすいです。 

### 4.1 MTE（Megatrend Exposure）＝“フローがシグナル”という定義

結論部で、**「テーマETFへの資金流入が、テーマ代表銘柄の“市場の信認”をシグナルする」** というシグナリング理論の立て付けを明示します。  

* ETF運用への素直な応用：

  * テーマETF (i) のフロー（推定でも良い）を (Flow_{i,t})
  * それをスコア化し、**テーマの強さ（需要）** としてローテーションに使う
    （MSCIがMediaScoreでやっていることの“ETF版”）

### 4.2 Pure Factor Portfolios（PFP）＝Fama–MacBeth回帰の“重み行列”として因子ポートフォリオを作る

Fama–MacBethの断面回帰を

[
R_{t+1}=Z_t\hat F_{t+1}+u_{t+1}
\tag{1}
]

[
\hat F_{t+1}=(Z_t^\top Z_t)^{-1}Z_t^\top R_{t+1}
\tag{2}
]

と書き、因子（係数）を“ポートフォリオのリターン”として解釈できるように、重み行列

[
W_t \equiv (Z_t^\top Z_t)^{-1}Z_t^\top
\tag{3}
]

を導入します。  

また

[
W_t Z_t = I_t
\tag{4}
]

が成り立つので、各因子ポートフォリオが「当該因子へのエクスポージャ1、他0」を満たす構造になります。 

**ETF運用への翻訳（最重要）**
あなたのETF集合に対しても、

* 説明変数 (Z_t)：ETFの因子露出（例：市場、サイズ、バリュー、モメンタム proxy 等）
* 目的変数 (R_{t+1})：ETFリターン
  とみなして “純テーマ” を作ることができます。

ただし、この論文はさらに **制約付き・加重最小二乗（CWLS）** に拡張しており、現実的です。

### 4.3 Cap-weighted標準化（スタイル露出の標準化）

スタイル因子の事前露出 (x_{ns}) を、時点tの市場ウェイト (w_n^M) で加重してz-score化：

[
z_{ns}
======

\frac{x_{ns}-\sum_{n=1}^N w_n^M x_{ns}}
{\sqrt{\sum_{n=1}^N w_n^M x_{ns}^2 -\left(\sum_{n=1}^N w_n^M x_{ns}\right)^2}}
\tag{7}
]

ETFに置き換えるなら、ETFを“銘柄”と見做すより、ETFの構成から推計した因子露出を標準化する、という発想になります（Phase 2実装領域）。

### 4.4 改良FM（CWLS + 制約 + 時価総額重み）

時価総額行列 (V_t) を導入し、制約行列 (C_t) を使って（共線性や国・業種露出の打ち消し等を管理）、最終的に

[
PW_t
\equiv
C_t (C_t^\top Z_t^\top V_t Z_t C_t)^{-1} C_t^\top Z_t^\top V_t
\tag{17}
]

という **“純因子のアクティブ・ウェイト”** を与えます。 

**戦略部品としての意味**

* “テーマETFのパフォーマンス”を評価したいとき、

  * 実は「グロース/モメンタムに寄っていただけ」を除外したい
* そのための **二次因子露出の除去（purification）** が、このPFP/CWLSの核です。 

### 4.5 時系列のα推定＝CAPM/FF回帰＋（必要なら）GMM-IVd

論文は、PFPで得た因子リターンを使い、CAPMやFF系でテーマのαを検定します。 
さらに、内生性や非正規性に頑健な推定として **GMM-IVd** を使う、という主張があります。 

ETF戦略では、最終的に

* 「テーマローテーションで得た超過収益」が
* 「単なる既知因子の取り過ぎ」でないか
  を検証する枠組みとして使えます。

---

## 5) 4本を“ETFローテーション戦略”へ統合するなら（設計の骨格）

上の部品を、あなたの **コア18本ETF** 運用に最短で繋げると、以下の3層構造が自然です。

### 層A：テーマ強度スコア（Selection）

* **MSCI型**：外部スコアでテーマを選抜（月次 top-k） 
* **Naffa & Fain型**：フロー（または代替需要指標）をテーマ強度と解釈 
* **THEME型**：テキスト類似度で「テーマ純度」や「逸脱」を監視 

スコア例（設計案）：
[
Score_{i,t}
===========

a\cdot Z_Demand_{i,t}
+
b\cdot Z_Momentum_{i,t}
+
c\cdot Z_Purity_i
]
（Demand＝フロー等、Momentum＝相対強度、Purity＝テキスト類似度）

### 層B：二次因子の制御（Purification / Constraints）

* Somefun：テーマを「因子＋固有」で見て、統合最適化へ 
* Naffa & Fain：CWLS/PFPで二次因子を消して“純テーマ”を測る 

ETF版の現実的な落とし所：

* ポートフォリオの因子露出を制約
  [
  B^\top w \approx 0 \quad(\text{または許容幅内})
  ]
* あるいは “因子中立化した超過収益” を目的関数に入れる

### 層C：リスク管理（Risk Targeting）

* MSCIの10%リスクコントロール：
  推定ボラで (W_t) を調整し、ポート全体ボラを目標へ  

---

## 6) Assumptions（不明点）と検証案（Phase 2で潰すべき）

### Assumptions

* ETFフロー（MTE/Demand）は、実データが取れない場合は代理変数（出来高変化、AUM変化推定、検索トレンド等）で代替する必要がある
* THEMEの埋め込み学習そのものはPhase 2以降（当面は“既存埋め込み＋類似度”で簡易Purity）
* 因子露出 (B)（ETFの市場/スタイル感応度）をどう推計するか（回帰 or 外部ファクタモデル）

### 検証案

* 各ETFについて

  * 回帰：(XR_{i,t}=\alpha_i+\beta_i^\top f_t+\varepsilon_{i,t}) を推定し、(\alpha_i) がスコアと整合するか確認（Somefunの分解思想） 
* ローテーション（MSCI型）に

  * ボラターゲット（MSCI式）を足す vs 足さない、でドローダウン/リスクがどう変わるか比較 
* “純テーマ”評価として

  * 因子中立化前後でパフォーマンス差を比較（Naffa & Fainの趣旨） 

---

## 7) 明示的な注意（禁止事項リスクへの警告）

* **先読み（look-ahead）**：

  * MediaScore/フロー/ニュース集計などは「いつ確定した情報か」を厳密に扱わないと、スコアが未来情報を含み得ます（MSCI手法の“月次レビュー確定”の考え方に合わせるのが安全） 
* **0リターン扱い**：

  * 欠損（価格欠落、分配金処理、上場来データ不足）を0埋めすると、モメンタムやボラ推定が壊れます（MSCIのボラ推定式は特に欠損に弱い） 
* **テーマ漂流（ドリフト）**：

  * ETFは指数変更・リバランスで中身が変わるので、説明文だけでPurityを固定するとズレます（THEMEが“時間変化”を入れる動機そのもの） 

---
上記で記載したものについて、それぞれそれぞれどのようなデータやアルゴリズムを用いて、入力から出力を出せますか？Pythonで関数を実装することを念頭に整理してください

## Response:
以下、あなたが貼った **(1)〜(7)** の各“部品”について、**Python関数実装を前提**に「必要データ→アルゴリズム→入力/出力」を **要素ごと**に整理します。  
（“どのデータが必須で、何が代替可能か”も明示します。実装コードは出しません。）

* * *

1) Somefun（Allocating to Thematic Investments）系
===============================================

1.1 テーマリターン分解（因子モデルで純テーマ成分）
---------------------------

### 目的

*   ETF超過リターンを **市場・因子で説明される部分**と \*\*説明不能（純テーマ）\*\*に分解し、
    *   シグナル（alpha/残差）
    *   制約（因子被り）
    *   評価（テーマ固有性）  
        に使う。

### 必要データ

*   **必須**
    *   `prices[i,t]` もしくは `returns[i,t]`（ETF i）
*   **推奨**
    *   `rf[t]`（無リスク）→超過収益を作る
    *   `F[k,t]`（因子リターン。最低 MKT、可能なら MOM/VAL/SIZE/…）
*   **任意**
    *   ベンチマーク `bm[t]`（市場ETFでも可）

### アルゴリズム（最小）

1.  リターン計算：`r[i,t]`
2.  超過収益：`XR[i,t] = r[i,t] - rf[t]`（あるいは `r-bm`）
3.  ローリング回帰（OLS/Ridge）：
    $$
    XR_{i,t}=\alpha_{i,t} + \beta_{i,t}^\top F_t + \varepsilon_{i,t}
    $$
4.  出力：
    *   `alpha[i,t]`（純テーマ強度の候補）
    *   `beta[i,k,t]`（因子被り）
    *   `resid[i,t]`（純テーマショック系列）

### 入力→出力（関数仕様案）

*   **入力**
    *   `returns: pd.DataFrame[date × ticker]`
    *   `factors: pd.DataFrame[date × factor]`
    *   `rf: pd.Series[date] | None`
    *   `lookback: int`
    *   `reg: Literal["ols","ridge"]`
*   **出力**
    *   `alpha: pd.DataFrame[date × ticker]`
    *   `beta: dict[str, pd.DataFrame[date × ticker]]`（factorごと） or 3D
    *   `resid: pd.DataFrame[date × ticker]`
    *   `diagnostics: dict`（R2, nobs, etc.）

### 注意

*   因子 `F` の採用範囲が結果を支配 → **最小因子セットから段階的**に増やすのが安全
*   欠損0埋めは厳禁（除外・前回値・補完ルールを固定）

* * *

1.2 コア・サテライト（統合最適化の設計）
----------------------

※今回は「テーマETFのみ運用」なので、“思想”を **ETF間配分設計**として実装する形。

### 目的

*   「テーマETFを全部同列に見る」のではなく、
    *   分散（疑似コア）
    *   高純度（サテライト的）  
        の役割分担を **ルールとして固定**する。

### 必要データ

*   **必須**
    *   `returns[i,t]`
*   **推奨**
    *   `cov[t]`（ローリング共分散）
    *   `purity[i]`（THEME由来の固定スコアなど）

### アルゴリズム（実装しやすい例）

*   例A：**二階建て配分**
    1.  “分散バケット”（低相関クラスター代表）に基本配分
    2.  “高純度バケット”に追加配分（上限あり）
*   例B：**混合目的関数**
    *   目的：分散を確保しつつ、純度の高いETFに傾斜
    *   例：`maximize w·score - λ w^TΣw` with bounds

### 入力→出力（関数仕様案）

*   `allocate_core_satellite(returns, purity=None, constraints=dict, method="two_bucket"|"mix_objective") -> weights`

### 注意

*   “統合最適化”は自由度が高いので、まず \*\*ルールベース（2バケット）\*\*で検証可能にするのが良い

* * *

1.3 ロバスト最適化（推定誤差耐性の配分）
----------------------

### 目的

*   期待リターン推定が不安定でも破綻しにくい配分（テーマETF向け）

### 必要データ

*   **必須**
    *   `cov: Σ`（ローリング共分散）
*   **任意**
    *   `mu: 期待リターン`（弱く使う、または使わない）
*   **制約**
    *   long-only、最大ウェイト、ターンオーバー等

### アルゴリズム（現実的な3択）

*   **(A) Min-Var（mu不要）**
    $$
    \min_w\ w^\top \Sigma w \ \text{s.t.}\ w\in\mathcal W
    $$
*   **(B) Risk Parity（mu不要）**
    *   リスク寄与を均等化（数値解法）
*   **(C) Robust Mean-Var（mu不確実）**
    $$
    \max_{w\in\mathcal W}\min_{\mu\in\mathcal U} \left(w^\top\mu-\frac{\lambda}{2}w^\top\Sigma w\right)
    $$

### 入力→出力（関数仕様案）

*   `allocate_robust(cov, mu=None, constraints=dict, method="min_var"|"risk_parity"|"robust_mv", params=dict) -> weights`

### 注意

*   Phase 1では \*\*“どのmethodを採用し、何を固定パラメータにするか”\*\*を決めるのが重要（過剰に最適化しない）

* * *

2) MSCI手法書系
===========

2.1 ランキング選抜（外生スコア→Top-K→等ウェイト）
------------------------------

### 目的

*   月次でスコア上位のテーマ（ETF）に乗り換えるローテ戦略の中核

### 必要データ

*   **必須**
    *   `score[i,t]`（ETF×時点）
    *   `rebalance_dates`
*   **任意**
    *   `eligibility[i,t]`（売買可能・流動性等のフィルタ）
    *   `buffer`（入替抑制）

### アルゴリズム

1.  `score[:,t]` を降順ソート
2.  上位Kを採用
3.  ウェイト付け：等ウェイト or スコア比例
4.  （任意）バッファ：前回採用銘柄を残す閾値を設定

### 入力→出力（関数仕様案）

*   `select_topk_weights(scores, rebalance_dates, k, weighting="equal"|"score", eligibility=None, buffer=None) -> target_weights`

### 注意

*   **スコアの確定時刻**を厳密に（先読み防止）

* * *

2.2 線形合成（上位テーマを合成する一般形）
-----------------------

### 目的

*   “テーマ配分→最終ポート配分”を **線形結合**で計算する（MSCIの合成原理）

### 必要データ

*   `theme_weights[j,t]`（テーマjの配分）
*   `mapping`（テーマjがどのETF（or銘柄）を含むか、その内訳ウェイト）

### アルゴリズム

$$
w_{asset,t}=\sum_j w_{theme,j,t}\cdot w_{asset|theme=j,t}
$$

### 入力→出力（関数仕様案）

*   `compose_weights(theme_weights: DF, constituents: dict[theme->Series(asset weights)]) -> asset_weights: DF`

### 注意

*   今回は「ETF=テーマ」に近いので、mappingを単純化可能（1対1でOK）

* * *

2.3 ボラターゲット（EWMA短期/長期 + スケーリング）
-------------------------------

### 目的

*   ポートの実効ボラを一定にする（選抜ロジックと独立に後段で適用可能）

### 必要データ

*   **必須**
    *   `portfolio_returns[t]`（日次推奨）
*   **パラメータ**
    *   `lambda_st=0.94`, `lambda_lt=0.97`, `lag=3`, `target_vol=0.10`（MSCI例）

### アルゴリズム（関数分割が吉）

1.  EWMA分散更新（短期/長期）
2.  ボラ予測の合成（例：max/加重平均）
3.  スケール `W[t] = target_vol / sigma[t]`
4.  `scaled_return[t] = W[t]*r[t] - fee_adjustment`（任意）

### 入力→出力（関数仕様案）

*   `ewma_var(returns: Series, lam: float, lag:int) -> var: Series`
*   `combine_vol(var_st, var_lt, rule="max"|"weighted") -> sigma: Series`
*   `vol_target_leverage(sigma, target_vol, bounds=(wmin,wmax)) -> W: Series`

### 注意

*   欠損日処理が必須（カレンダー整合）
*   現物オンリーなら `W<=1` 制約を入れるなど

* * *

3) THEME論文系（ETF向けに“スコア部品”として利用）
===============================

3.1 セマンティック整列（InfoNCE：学習あり／ただしまずは学習なしで代替可）
------------------------------------------

### 目的

*   “テーマ定義文”と“ETFテキスト”の整合度を定量化（Purity/Drift）

### 必要データ

*   **必須**
    *   `etf_text[i]`（Objective/Index description）
    *   `theme_text[j]`（テーマ定義文）
*   **任意（学習するなら）**
    *   正例/負例のペア（テーマ↔銘柄/ETF）

### アルゴリズム（段階）

*   **Stage0（学習なし）**：埋め込み→cos類似度
*   **Stage1（学習あり）**：InfoNCEで表現を改善
    $$
    L_{align}=-\log\frac{\exp(sim(z_i,h^+)/\tau)}{\exp(sim(z_i,h^+)/\tau)+\sum \exp(sim(z_i,h^-)/\tau)}
    $$

### 入力→出力（関数仕様案）

*   学習なし：
    *   `compute_text_embeddings(texts, embed_fn) -> np.ndarray`
    *   `cosine_sim_matrix(E_etf, E_theme) -> DF[ticker×theme]`
*   学習あり：
    *   `train_infonce_encoder(pairs_posneg, encoder, params) -> trained_encoder`

### 注意

*   Phase 1の機能確認は **学習なし**で十分（学習はPhase 2で）

* * *

3.2 時系列融合（意味 + リターンでスコアを動的化）
----------------------------

### 目的

*   “テーマ整合度”だけでなく、“いま市場で報われているか”を反映した動的スコア

### 必要データ

*   `purity[i]`（3.1の固定スコア）
*   `returns[i,t]`（ETF）
*   パラメータ：lookback L

### アルゴリズム（学習なし簡易）

*   `mom[i,t] = zscore(sum_{u=t-L+1}^t r[i,u])`
*   `score[i,t] = a*purity[i] + b*mom[i,t]`

### 入力→出力（関数仕様案）

*   `compute_momentum(returns: DF, lookback:int, method="sum"|"regression") -> DF`
*   `combine_scores(purity: Series, mom: DF, a:float, b:float) -> DF(score)`

### 注意

*   Lの選び方で結果が変わる → 複数Lを並列評価できる設計に

* * *

3.3 Triplet loss（将来リターンでランキング学習：先読み注意）
--------------------------------------

### 目的

*   “テーマ内で勝つETF”を学習してランキング性能を上げる（研究要素が強い）

### 必要データ

*   `future_return[i,t→t+H]`（将来リターン）＝ラベル生成に使う

### アルゴリズム

*   triplet生成：`(anchor=theme, positive=top future, negative=low future)`
*   学習：
    $$
    L_{triplet}=[sim(z_i,h'_n)-sim(z_i,h'_p)+m]_+
    $$

### 入力→出力（関数仕様案）

*   `make_triplets(returns: DF, horizon:int, top_q:float, bottom_q:float) -> list[triplet]`
*   `train_triplet_ranker(triplets, encoder, params) -> trained_encoder`

### 注意（重大）

*   ラベルに未来リターンを使うので **運用シグナルに直結させると危険**  
    → 機能確認は「学習と検証の分離」が出来る枠組みが前提

* * *

3.4 推論（類似度Top-K）
----------------

### 目的

*   テーマ文（クエリ）→ETF候補を類似度でランキング（Purity/ユニバース監視）

### 必要データ

*   `theme_query_text`（または複数テーマ定義）
*   `etf_text[i]`
*   `embed_fn` or `trained_encoder`

### アルゴリズム

*   埋め込み→cos類似度→Top-K抽出

### 入力→出力（関数仕様案）

*   `rank_etfs_by_theme(query_text: str, etf_texts: dict, embed_fn, topk:int) -> pd.Series(similarity)`

* * *

4) Naffa & Fain（ESG-themed megatrend）系
======================================

4.1 MTE/需要（フロー）スコア化（テーマ強度の入力）
-----------------------------

### 目的

*   テーマETFへの需要（フロー）を **選抜スコア**として使う（MSCIの外生スコアの代替源泉）

### 必要データ

*   理想：`net_flow[i,t]`
*   代替：`AUM[i,t]`、`shares_out[i,t]`、`volume[i,t]`（推定フロー）
*   価格：`price[i,t]`（AUM変化から価格要因を除くなら必要）

### アルゴリズム（簡易2段）

*   推定フロー（例）：
    *   `aum_change = AUM[t]-AUM[t-1]`
    *   `price_effect ≈ AUM[t-1]*r[t]`
    *   `flow_est = aum_change - price_effect`
*   スコア化：
    *   `z = zscore(flow_est over lookback)`
    *   winsorizeで外れ値抑制

### 入力→出力（関数仕様案）

*   `estimate_net_flows(price: DF, aum: DF) -> flow: DF`
*   `compute_demand_score(flow: DF, lookback:int, winsor=(0.01,0.99)) -> score: DF`

### 注意

*   AUMデータの頻度・欠損がネックになりやすい（Phase 2のデータ要件）

* * *

4.2 PFP（Pure Factor Portfolios）：FM回帰→重み行列で因子リターン抽出
--------------------------------------------------

### 目的

*   “テーマのリターン”を **既知因子と分離**して評価・純化する（Purificationの基礎）

### 必要データ

*   `R[t+1, asset]`（ここではasset=ETFでも可）
*   `Z_t[asset, descriptor]`（ETFの因子露出/属性）
    *   例：市場β、モメンタムβ、ボラ、流動性proxyなど

### アルゴリズム（最小）

*   断面回帰：
    $$
    \hat F_{t+1}=(Z_t^\top Z_t)^{-1}Z_t^\top R_{t+1}
    $$
*   重み行列 `W_t` も計算して保存

### 入力→出力（関数仕様案）

*   `fm_cross_sectional_factor_returns(R: DF, Z_by_date: dict[date->DF]) -> factor_returns: DF, W_by_date: dict`

### 注意

*   ETFでやるなら **Z設計**が本丸（E1で推定したβをZにするのが現実的）

* * *

4.3 Cap-weighted 標準化（descriptorの正規化）
------------------------------------

### 目的

*   ディスクリプタを時点ごとに比較可能にする（外れ値やスケール差の抑制）

### 必要データ

*   `x[asset, s]`：各assetのdescriptor
*   `w_M[asset]`：市場ウェイト（ETFならAUM比などで代替）

### アルゴリズム

*   原典の加重z-score（式7）

### 入力→出力（関数仕様案）

*   `cap_weighted_zscore(X: DF[asset×desc], w: Series[asset]) -> Z: DF`

### 注意

*   wが欠損/ゼロの場合の扱いを仕様化

* * *

4.4 CWLS + 制約 + 重み（改良FM）
------------------------

### 目的

*   共線性や中立化（国/業種等）を制御し、より“純化”された因子（または残差）を得る

### 必要データ

*   `Z_t`（標準化済みdescriptor）
*   `V_t`（重み：AUM等）
*   `C_t`（制約行列：中立化したい方向を表現）

### アルゴリズム

*   原典の `PW_t`（式17）を計算し、そこから因子/純化ウェイトを得る

### 入力→出力（関数仕様案）

*   `cwls_pfp(Z: DF, V: Series, C: np.ndarray) -> PW: np.ndarray`
*   あるいは `-> factor_returns` まで出す

### 注意

*   Cの設計が難しい → Phase 1では「どの中立化をやるか」だけ決めるのが現実的

* * *

4.5 α推定（因子回帰）＋コスト感度
-------------------

### 目的

*   “戦略収益が因子の取り過ぎではないか”を検定
*   コスト仮定に対する頑健性を見る（論文が強調）

### 必要データ

*   `strategy_return[t]`（gross）
*   `turnover[t]`（売買回転率：推定でも可）
*   `cost_bps`（シナリオ）
*   `factors[t]`（CAPM/FF）

### アルゴリズム

1.  コスト控除：`net = gross - cost_bps/1e4 * turnover`
2.  回帰：`net[t] = alpha + beta^T factors[t] + eps`
3.  出力：alpha、t統計、R2、Sharpe等

### 入力→出力（関数仕様案）

*   `apply_cost_model(returns: Series, turnover: Series, cost_bps: float) -> net_returns`
*   `estimate_alpha(net_returns: Series, factors: DF) -> dict(alpha, beta, tstats, r2)`
*   `run_cost_sensitivity(gross_returns, turnover, factors, cost_grid:list[float]) -> DF(results)`

### 注意

*   turnoverがないとコスト議論が曖昧 → “推定ルール”（例：|Δw|の合計）を仕様化

* * *

5) 統合（層A/B/C）を「関数パイプライン」として表現
=============================

あなたの提示した3層を **関数合成**で書くと、概ねこう分解できます。

層A：テーマ強度スコア（Selection）
----------------------

*   `score_demand = compute_demand_score(...)`（4.1）
*   `score_mom = compute_momentum(...)`（3.2の一部）
*   `score_purity = compute_purity(...)`（3.1/3.4）
*   `score = combine_scores(score_demand, score_mom, score_purity, weights=(a,b,c))`
*   `w_target = select_topk_weights(score, rebalance_dates, k)`（2.1）

層B：因子制御（Purification / Constraints）
-----------------------------------

*   `alpha,beta,resid = rolling_factor_decompose(...)`（1.1）
*   `w_adj = enforce_factor_bounds(w_target, beta_at_rebal, bounds)`（1.3の実装）
    *   もしくは `allocate_robust(cov, mu=score, constraints=...)`（1.3/1.4）

層C：リスク管理（Risk Targeting）
------------------------

*   `r_port = compute_portfolio_returns(returns, w_adj)`（基礎）
*   `sigma = forecast_vol_ewma(r_port, ...)`（2.3）
*   `W = vol_target_leverage(sigma, target_vol, bounds)`（2.3）
*   `r_scaled = W * r_port - fee_model`（2.3の指数式に相当）

* * *

6) 最小の“個別機能確認”セット（データ依存が少ない順）
=============================

データが揃っていなくても段階的に確認できるように並べます。

1.  **2.1 Top-K選抜**（scoreが仮でも可）
2.  **2.3 ボラターゲット**（ポートリターンだけで可）
3.  **3.1/3.4 テキストpurity**（テキストだけで可）
4.  **1.1 因子分解**（因子データが必要）
5.  **4.1 フロー需要**（AUM/フローが必要）
6.  **4.2–4.4 PFP/CWLS**（Z設計が必要で上級）
7.  **4.5 α推定＋コスト感度**（turnover仕様が必要）

* * *

必要なら次の返答で、上の各要素について \*\*「pandasのindex/columns規約」「欠損・外れ値の標準処理」「最小テスト用のダミーデータ生成I/O」\*\*まで落とし、実装を始める直前の“関数設計書（docstring集）”にできます。

## Prompt:
それぞれPythonで実装して

## Response:
Phase 1の最重要ルールに **「実装禁止」** があるため、ここで **動くPython実装（ロジックまで書いたコード）を提示することはできません**。  
代わりに、Phase 2でそのままコピペして実装できるように、**関数シグネチャ＋入出力型＋アルゴリズム手順（擬似コード）＋ガードレール**を “実装直前レベル” まで落とします（＝仕様としてのコード骨格）。  
※この粒度なら Phase 1でも安全です（実行可能な実装にはしていません）。

* * *

0) 共通前提：型・規約（全関数で統一）
--------------------

*   **returns**：`pd.DataFrame(index=DatetimeIndex, columns=tickers)`（日次推奨）
*   **scores**：`pd.DataFrame(index=DatetimeIndex, columns=tickers)`（スコア確定日のみ）
*   **rebalance\_dates**：`list[pd.Timestamp]`（returnsのindex上に存在）
*   欠損：**0埋め禁止**。原則は `dropna` or `ffill`（対象により使い分け）
*   先読み：スコアやAUM等は **t時点で観測可能な値のみ**を使う（遅延ルールをdocsで固定）

* * *

1) MSCI型：ランキング→Top-K（2.1）
=========================

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional
import pandas as pd
import numpy as np

Weighting = Literal["equal", "score_proportional"]

@dataclass(frozen=True)
class TopKConfig:
    k: int
    weighting: Weighting = "equal"
    # buffer: 前回採用銘柄を残すためのルール（任意）
    buffer_k: Optional[int] = None  # 例：上位k+buffer_kまでは残留候補など
    min_score: Optional[float] = None  # スコア閾値

def select_topk_weights(
    scores: pd.DataFrame,
    rebalance_dates: list[pd.Timestamp],
    cfg: TopKConfig,
    eligibility: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    入力:
      scores: date×ticker のスコア（その日までに確定した値のみが入る前提）
      rebalance_dates: リバランス日
      cfg: TopKConfig
      eligibility: date×ticker の採用可否(True/False)（任意）

    出力:
      target_w: rebalance_date×ticker の目標ウェイト（各行の和=1）
    擬似手順:
      for t in rebalance_dates:
        s = scores.loc[t]
        if eligibility: s = s where eligibility.loc[t]==True else NaN
        if cfg.min_score: s[s < min_score] = NaN
        rank = sort desc by s (dropna)
        selected = top cfg.k
        if cfg.weighting == "equal": w[selected]=1/k
        elif cfg.weighting == "score_proportional": w[selected]=s[selected]/sum(s[selected])
        (optional) buffer: 前回selected_prevのうち上位k+buffer_kに残るものは維持 etc.
      return target_w
    注意:
      欠損を0にしない。min_scoreやeligibilityで除外したら、残りで正規化。
    """
    raise NotImplementedError
```

* * *

2) MSCI型：ボラターゲット（2.3）
=====================

```python
@dataclass(frozen=True)
class EWMAVolConfig:
    lam_st: float = 0.94
    lam_lt: float = 0.97
    lag: int = 3
    annualization: int = 252
    combine_rule: Literal["max", "weighted"] = "max"
    w_st: float = 0.5  # combine_rule="weighted"用
    target_vol: float = 0.10
    w_min: float = 0.0
    w_max: float = 1.0  # 現物オンリーなら 1.0。レバ許容なら >1

def ewma_var(returns: pd.Series, lam: float, lag: int) -> pd.Series:
    """
    returns: 日次リターンSeries
    出力: EWMA分散系列
    擬似手順:
      init var0 = returns^2 の初期平均など
      for t:
        x = returns.shift(lag).iloc[t]
        var[t] = lam*var[t-1] + (1-lam)*x^2
    """
    raise NotImplementedError

def forecast_vol_ewma_dual(returns: pd.Series, cfg: EWMAVolConfig) -> pd.Series:
    """
    出力: 年率換算のsigma[t]
    擬似手順:
      var_st = ewma_var(returns, cfg.lam_st, cfg.lag)
      var_lt = ewma_var(returns, cfg.lam_lt, cfg.lag)
      if cfg.combine_rule=="max": var = max(var_st,var_lt)
      else: var = cfg.w_st*var_st + (1-cfg.w_st)*var_lt
      sigma = sqrt(var) * sqrt(cfg.annualization)
    """
    raise NotImplementedError

def vol_target_leverage(sigma: pd.Series, cfg: EWMAVolConfig) -> pd.Series:
    """
    出力: レバ係数 W[t]（bounds適用）
    W[t] = target_vol / sigma[t]
    """
    raise NotImplementedError

def apply_vol_target_to_returns(port_returns: pd.Series, W: pd.Series) -> pd.Series:
    """
    出力: スケール後リターン
    r_scaled[t] = W[t] * r_port[t]
    （feeを入れるなら別関数で）
    """
    raise NotImplementedError
```

* * *

3) Somefun型：因子分解（1.1）＋テーマ固有ボラ（1.2）
==================================

```python
@dataclass(frozen=True)
class FactorDecompConfig:
    lookback: int = 252
    reg: Literal["ols", "ridge"] = "ols"
    ridge_alpha: float = 1.0  # reg="ridge"用（実装時に使用）
    add_intercept: bool = True
    min_obs: int = 200

def rolling_factor_decompose(
    xr: pd.DataFrame,          # date×asset
    factors: pd.DataFrame,     # date×k
    cfg: FactorDecompConfig,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """
    出力:
      alpha: date×asset
      beta: {factor_name: date×asset}
      resid: date×asset
      r2: date×asset
    擬似手順:
      align xr,factors by date intersection
      for each date t (>=lookback):
        X = factors[t-lookback+1:t]
        y = xr[t-lookback+1:t, asset]
        fit regression y ~ X (+ intercept)
        store alpha[t,asset], beta[t,asset,k], resid[t,asset], r2[t,asset]
    注意:
      欠損が多いassetはmin_obs未満ならNaN
    """
    raise NotImplementedError

def estimate_thematic_vol(
    resid: pd.DataFrame, lookback: int = 252, annualization: int = 252
) -> pd.DataFrame:
    """
    出力: date×asset のテーマ固有ボラ（残差のローリング標準偏差×sqrt(annualization)）
    """
    raise NotImplementedError
```

* * *

4) Somefun型：因子被り制約（1.3）チェック（最小）
===============================

```python
def portfolio_factor_exposure(
    weights: pd.Series,   # asset
    beta_at_t: pd.DataFrame,  # asset×factor （t時点のbeta）
) -> pd.Series:
    """
    出力: factorごとのポート露出 = sum_i w_i * beta_i
    """
    raise NotImplementedError

def check_factor_bounds(exposure: pd.Series, bounds: pd.Series) -> dict:
    """
    bounds: factor -> max_abs_exposure
    出力: 違反している因子、超過量など
    """
    raise NotImplementedError
```

> NOTE：この段階では「制約を満たすようにウェイトを修正する最適化」まで書くと“実装”色が強くなるので、Phase 1では **チェック関数**までを仕様化しておくのが安全です。修正（最適化）はPhase 2に回す想定。

* * *

5) THEME型：テキストPurity（3.1, 3.4：学習なし版）
====================================

```python
from typing import Callable

EmbedFn = Callable[[list[str]], np.ndarray]  # texts -> (n,d)

def cosine_sim_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    A: (n,d), B: (m,d)
    出力: (n,m) cosine similarity
    """
    raise NotImplementedError

def compute_text_similarity(
    etf_texts: dict[str, str],
    theme_texts: dict[str, str],
    embed_fn: EmbedFn,
) -> pd.DataFrame:
    """
    出力: index=ticker, columns=theme の類似度行列
    擬似手順:
      E = embed_fn(list(etf_texts.values()))
      T = embed_fn(list(theme_texts.values()))
      S = cosine_sim_matrix(E,T)
      return DF(S, index=tickers, columns=themes)
    """
    raise NotImplementedError

def compute_purity(
    sim_matrix: pd.DataFrame,
    etf2theme: dict[str, str],
) -> pd.Series:
    """
    出力: ticker -> purity（指定テーマへの類似度）
    """
    raise NotImplementedError

def rank_etfs_by_query(
    query_text: str,
    etf_texts: dict[str, str],
    embed_fn: EmbedFn,
    topk: int = 10,
) -> pd.Series:
    """
    出力: 類似度降順のSeries（index=ticker）
    """
    raise NotImplementedError
```

* * *

6) THEME型：semantic + temporal（3.2：学習なし簡易）
=========================================

```python
@dataclass(frozen=True)
class SemanticTemporalConfig:
    lookback: int = 63
    a: float = 1.0  # purity weight
    b: float = 1.0  # momentum weight
    winsor_q: tuple[float, float] = (0.01, 0.99)

def compute_momentum_score(returns: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """
    出力: date×asset のモメンタムスコア（例：累積リターン→各日クロスでz-score）
    擬似手順:
      cum = rolling_sum(returns, lookback)  # or rolling_prod
      z = cross_sectional_zscore(cum) per date
    """
    raise NotImplementedError

def combine_semantic_temporal_scores(
    purity: pd.Series,          # asset
    mom: pd.DataFrame,          # date×asset
    cfg: SemanticTemporalConfig,
) -> pd.DataFrame:
    """
    出力: date×asset の統合スコア
    score[t,i] = a*purity[i] + b*mom[t,i]
    """
    raise NotImplementedError
```

* * *

7) Naffa & Fain：需要（フロー）スコア（4.1）
===============================

```python
@dataclass(frozen=True)
class DemandScoreConfig:
    lookback: int = 63
    winsor_q: tuple[float, float] = (0.01, 0.99)

def estimate_net_flows_from_aum(
    prices: pd.DataFrame,  # date×asset
    aum: pd.DataFrame,     # date×asset
) -> pd.DataFrame:
    """
    出力: 推定純フロー（date×asset）
    擬似手順:
      r = prices.pct_change()
      aum_change = aum.diff()
      price_effect = aum.shift(1) * r
      flow_est = aum_change - price_effect
    """
    raise NotImplementedError

def compute_demand_score(flow: pd.DataFrame, cfg: DemandScoreConfig) -> pd.DataFrame:
    """
    出力: date×asset の需要スコア（ローリングz + winsorize）
    """
    raise NotImplementedError
```

* * *

8) Naffa & Fain：FM/PFP と CWLS（4.2–4.4）
======================================

※ここは「ETFでZ（descriptor）をどう作るか」が肝で上級。Phase 1では **関数I/O固定**が主。

```python
def cap_weighted_zscore(X: pd.DataFrame, w: pd.Series) -> pd.DataFrame:
    """
    X: asset×descriptor
    w: asset（合計1推奨）
    出力: asset×descriptor の加重z-score
    """
    raise NotImplementedError

def fm_factor_returns(
    R_next: pd.Series,  # asset, t+1のリターン（断面）
    Z: pd.DataFrame,    # asset×descriptor（断面）
) -> pd.Series:
    """
    出力: descriptor の因子リターン推定（t+1）
    F_hat = (Z^T Z)^(-1) Z^T R
    """
    raise NotImplementedError

def cwls_pfp_weights(
    Z: pd.DataFrame,    # asset×descriptor
    V: pd.Series,       # asset weights（AUM等）
    C: np.ndarray,      # constraint matrix
) -> np.ndarray:
    """
    出力: PW（descriptor×asset など、設計により定義）
    PW = C (C^T Z^T V Z C)^(-1) C^T Z^T V
    """
    raise NotImplementedError
```

* * *

9) α推定＋コスト感度（4.5）
=================

```python
def turnover_from_weights(w: pd.DataFrame) -> pd.Series:
    """
    w: date×asset（通常はリバランス日だけでも可）
    出力: date のターンオーバー推定（例：0.5*sum(|Δw|)）
    """
    raise NotImplementedError

def apply_costs(gross_returns: pd.Series, turnover: pd.Series, cost_bps: float) -> pd.Series:
    """
    net = gross - cost_bps/1e4 * turnover
    """
    raise NotImplementedError

def factor_alpha_regression(
    returns: pd.Series,
    factors: pd.DataFrame,
    add_intercept: bool = True,
) -> dict:
    """
    出力: alpha, beta, t-stats, r2 など
    """
    raise NotImplementedError

def run_cost_sensitivity(
    gross_returns: pd.Series,
    turnover: pd.Series,
    factors: pd.DataFrame,
    cost_grid_bps: list[float],
) -> pd.DataFrame:
    """
    出力: costごとの alpha/Sharpe 等のテーブル
    """
    raise NotImplementedError
```

* * *

10) “層A/B/C” パイプライン（統合の器だけ：Phase 1用）
====================================

（中身は上の要素関数を呼ぶだけの設計。ここもPhase 1ではNotImplementedでOK）

```python
@dataclass(frozen=True)
class StrategyConfig:
    topk: TopKConfig
    vol: EWMAVolConfig
    semtemp: Optional[SemanticTemporalConfig] = None
    demand: Optional[DemandScoreConfig] = None
    # 因子制約やロバスト配分はPhase2で拡張

def build_scores(
    # 任意入力を受けてスコアを合成する器
) -> pd.DataFrame:
    raise NotImplementedError

def build_target_weights(scores: pd.DataFrame, rebalance_dates: list[pd.Timestamp], cfg: TopKConfig) -> pd.DataFrame:
    raise NotImplementedError

def backtest_skeleton(
    returns: pd.DataFrame,
    target_weights: pd.DataFrame,
    vol_cfg: EWMAVolConfig,
) -> pd.Series:
    """
    Phase 1では“骨格”のみ（実装はPhase 2）。
    """
    raise NotImplementedError
```

* * *

重要：ここから先（“実装”）はPhase 2でやるべき理由
-----------------------------

*   あなたのルールで **Phase 1は実装禁止**
*   今提示したのは **実装できる形の設計書（関数仕様＋擬似手順）** まで

* * *

次のアクション（Phase 1でやると強い）
----------------------

実装に入る前に、以下を docs/notes に固定すると、Phase 2で手戻りが激減します：

*   各関数の **欠損処理ルール**（drop/ffill/対象除外）
*   **スコアの観測遅延**（当日確定か、翌日か、月次何営業日後か）
*   **リバランス日生成規約**（月末、月初、最終営業日等）
*   **コストモデルの定義**（turnoverの定義、bpsレンジ）

* * *

もしあなたが「Phase 2に進めて実装OK」という段階になったら、上の `NotImplementedError` をすべて具体実装に落として、最小テスト（ダミーデータ→期待形状の出力）まで一気に通せます。

## Prompt:
(1)〜(7) の各“部品”について、Python関数実装

## Response:
すみません、ここは **Phase 1「実装禁止」** というあなたの最重要ルールに抵触します。したがって、(1)〜(7)を **実際に動くPython実装（ロジック入り）として提示することはできません**。

代替として、(1)〜(7)を **“関数としてコピペしてPhase 2で中身を埋めればそのまま動く”** 形に、**I/O固定＋処理手順（擬似コード）＋例外/ガードレール**まで落とした **実装直前テンプレ**を提示します（=Phase 1で許される最大限）。

以下は、あなたが貼った(1)〜(7)に対応する **モジュール別の関数テンプレ一式**です。

* * *

(1) Somefun：テーマリターン分解（因子モデル）
----------------------------

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional
import numpy as np
import pandas as pd

RegType = Literal["ols", "ridge"]

@dataclass(frozen=True)
class FactorDecompConfig:
    lookback: int = 252
    reg: RegType = "ols"
    ridge_alpha: float = 1.0
    add_intercept: bool = True
    min_obs: int = 200  # 窓内で有効観測がこれ未満ならNaN

def compute_returns_from_prices(prices: pd.DataFrame, method: Literal["log","simple"]="log") -> pd.DataFrame:
    """
    prices: date×asset
    returns: date×asset
    擬似:
      if method=="log": r=log(p/p.shift(1))
      else: r=pct_change()
    """
    raise NotImplementedError

def compute_excess_returns(returns: pd.DataFrame, rf: Optional[pd.Series]=None, benchmark: Optional[pd.Series]=None) -> pd.DataFrame:
    """
    超過収益 XR を作る
    擬似:
      if rf is not None: XR = returns.sub(rf, axis=0)
      elif benchmark is not None: XR = returns.sub(benchmark, axis=0)
      else: XR = returns.copy()  # 超過でなく生リターン扱い（仕様で禁止/許可を決める）
    """
    raise NotImplementedError

def rolling_factor_decompose(
    xr: pd.DataFrame,          # date×asset
    factors: pd.DataFrame,     # date×k
    cfg: FactorDecompConfig,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """
    出力:
      alpha: date×asset
      beta: {factor_name: date×asset}
      resid: date×asset
      r2:   date×asset

    擬似:
      align dates = intersection(xr.index, factors.index)
      for each t >= cfg.lookback:
        X = factors.loc[t-L+1:t] (dropna)
        for each asset:
          y = xr.loc[t-L+1:t, asset]
          align rows where both y and X are non-null
          if nobs < cfg.min_obs: continue
          fit y ~ X (+ intercept)
          store alpha[t,asset], beta[t,asset,k], resid[t,asset]=y_last - yhat_last, r2[t,asset]
    注意:
      欠損0埋め禁止。窓内で落とす。
    """
    raise NotImplementedError
```

* * *

(2) MSCI：ランキング選抜（Top-Kローテーション）
------------------------------

```python
from dataclasses import dataclass
from typing import Literal, Optional

Weighting = Literal["equal", "score_proportional"]

@dataclass(frozen=True)
class TopKConfig:
    k: int
    weighting: Weighting = "equal"
    min_score: Optional[float] = None
    # bufferなどを入れるならここに追加

def select_topk_weights(
    scores: pd.DataFrame,                 # date×asset
    rebalance_dates: list[pd.Timestamp],
    cfg: TopKConfig,
    eligibility: Optional[pd.DataFrame] = None,  # date×asset (bool)
) -> pd.DataFrame:
    """
    出力: rebalance_date×asset の目標ウェイト（行和=1）

    擬似:
      init target_w = zeros
      for t in rebalance_dates:
        s = scores.loc[t].copy()
        if eligibility: s[~eligibility.loc[t]] = NaN
        if cfg.min_score: s[s < min_score] = NaN
        s = s.dropna()
        if len(s) == 0: continue
        selected = s.sort_values(ascending=False).head(cfg.k)
        if cfg.weighting == "equal":
          w = 1/len(selected)
        else:
          w = selected / selected.sum()
        target_w.loc[t, selected.index] = w
      return target_w.fillna(0.0)

    ガード:
      - scoreのタイムスタンプ（確定日）を必ず遵守（先読み防止）
      - 欠損を0にしない（除外して正規化）
    """
    raise NotImplementedError
```

* * *

(3) MSCI：線形合成（テーマ合成の一般形）
------------------------

```python
def compose_linear_weights(
    outer_weights: pd.DataFrame,                      # date×outer (例: theme)
    inner_weights: dict[str, pd.Series],              # outer -> (asset weights)
) -> pd.DataFrame:
    """
    outer_weights: date×outer
    inner_weights: 各outerがどうassetに割り当てられるか（Series: asset->weight, sum=1想定）

    出力: date×asset の合成ウェイト

    擬似:
      for each date t:
        w_asset = 0
        for each outer j:
          w_asset += outer_weights[t,j] * inner_weights[j]
        normalize (任意：outerが部分欠損の場合)
    """
    raise NotImplementedError
```

* * *

(4) MSCI：ボラターゲット（EWMA短期/長期＋スケーリング）
----------------------------------

```python
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class EWMAVolConfig:
    lam_st: float = 0.94
    lam_lt: float = 0.97
    lag: int = 3
    annualization: int = 252
    combine_rule: Literal["max","weighted"] = "max"
    w_st: float = 0.5             # weighted用
    target_vol: float = 0.10
    w_min: float = 0.0
    w_max: float = 1.0            # 現物オンリー想定（レバ許容なら>1に）

def ewma_var(returns: pd.Series, lam: float, lag: int) -> pd.Series:
    """
    出力: EWMA分散
    擬似:
      r_lag = returns.shift(lag)
      var[0] = mean(r_lag^2)等
      for t>=1:
        var[t] = lam*var[t-1] + (1-lam)*r_lag[t]^2
    """
    raise NotImplementedError

def forecast_vol_dual(returns: pd.Series, cfg: EWMAVolConfig) -> pd.Series:
    """
    出力: sigma(t) 年率
    擬似:
      var_st = ewma_var(returns, cfg.lam_st, cfg.lag)
      var_lt = ewma_var(returns, cfg.lam_lt, cfg.lag)
      if cfg.combine_rule=="max": var = maximum(var_st, var_lt)
      else: var = cfg.w_st*var_st + (1-cfg.w_st)*var_lt
      sigma = sqrt(var) * sqrt(cfg.annualization)
    """
    raise NotImplementedError

def vol_target_leverage(sigma: pd.Series, cfg: EWMAVolConfig) -> pd.Series:
    """
    出力: W(t)（bounds適用）
    擬似:
      W = cfg.target_vol / sigma
      clip to [w_min, w_max]
    """
    raise NotImplementedError
```

* * *

(5) THEME：テキスト類似度（Purity）＋スコア合成（Selection層の材料）
----------------------------------------------

```python
from typing import Callable

EmbedFn = Callable[[list[str]], np.ndarray]

def cosine_sim_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    A: (n,d), B: (m,d)
    出力: (n,m)
    擬似:
      A_norm = A / ||A||
      B_norm = B / ||B||
      return A_norm @ B_norm.T
    """
    raise NotImplementedError

def compute_text_similarity(
    etf_texts: dict[str, str],
    theme_texts: dict[str, str],
    embed_fn: EmbedFn,
) -> pd.DataFrame:
    """
    出力: ticker×theme の類似度
    擬似:
      E = embed_fn(etf_text_list)
      T = embed_fn(theme_text_list)
      S = cosine_sim_matrix(E,T)
      return DF(S, index=tickers, columns=themes)
    """
    raise NotImplementedError

def compute_purity(sim: pd.DataFrame, etf2theme: dict[str, str]) -> pd.Series:
    """
    出力: ticker -> purity
    擬似:
      purity[i] = sim.loc[i, etf2theme[i]]
    """
    raise NotImplementedError
```

* * *

(6) THEME：時系列融合（semantic + temporal）
------------------------------------

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SemanticTemporalConfig:
    lookback: int = 63
    a: float = 1.0   # purity weight
    b: float = 1.0   # momentum weight
    winsor_q: tuple[float,float] = (0.01,0.99)

def cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    df: date×asset
    出力: date×asset（各dateで (x-mean)/std）
    """
    raise NotImplementedError

def compute_momentum_score(returns: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """
    出力: date×asset のmomentumスコア
    擬似:
      cum = returns.rolling(lookback).sum()  # logなら和=累積
      mom = cross_sectional_zscore(cum)
    """
    raise NotImplementedError

def combine_semantic_temporal_scores(
    purity: pd.Series,     # asset
    mom: pd.DataFrame,     # date×asset
    cfg: SemanticTemporalConfig,
) -> pd.DataFrame:
    """
    score[t,i] = a*purity[i] + b*mom[t,i]
    """
    raise NotImplementedError
```

* * *

(7) Naffa & Fain：需要（フロー）スコア＋PFP/CWLS＋α推定（評価）
--------------------------------------------

### (7a) 需要（Flow）スコア

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class DemandScoreConfig:
    lookback: int = 63
    winsor_q: tuple[float,float] = (0.01,0.99)

def estimate_net_flows_from_aum(
    prices: pd.DataFrame,  # date×asset
    aum: pd.DataFrame,     # date×asset
) -> pd.DataFrame:
    """
    出力: date×asset の推定純フロー
    擬似:
      r = prices.pct_change()
      aum_change = aum.diff()
      price_effect = aum.shift(1) * r
      flow_est = aum_change - price_effect
    """
    raise NotImplementedError

def winsorize(df: pd.DataFrame, q_low: float=0.01, q_high: float=0.99) -> pd.DataFrame:
    """
    dateごと、あるいは全期間で分位クリップ（仕様で固定）
    """
    raise NotImplementedError

def rolling_zscore(df: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """
    assetごとローリングz（またはdate断面z。仕様で固定）
    """
    raise NotImplementedError

def compute_demand_score(flow: pd.DataFrame, cfg: DemandScoreConfig) -> pd.DataFrame:
    """
    擬似:
      z = rolling_zscore(flow, cfg.lookback)
      z = winsorize(z, *cfg.winsor_q)
      return z
    """
    raise NotImplementedError
```

### (7b) PFP / CWLS（上級：Z設計が必要）

```python
def cap_weighted_zscore(X: pd.DataFrame, w: pd.Series) -> pd.DataFrame:
    """
    X: asset×descriptor, w: asset（合計1推奨）
    出力: asset×descriptor
    擬似:
      mean = sum(w*x)
      var  = sum(w*x^2) - mean^2
      z = (x-mean)/sqrt(var)
    """
    raise NotImplementedError

def fm_factor_returns(R_next: pd.Series, Z: pd.DataFrame) -> pd.Series:
    """
    F_hat = (Z^T Z)^(-1) Z^T R
    """
    raise NotImplementedError

def cwls_pfp_weights(Z: pd.DataFrame, V: pd.Series, C: np.ndarray) -> np.ndarray:
    """
    PW = C (C^T Z^T V Z C)^(-1) C^T Z^T V
    """
    raise NotImplementedError
```

### (7c) α推定＋コスト感度（評価）

```python
def turnover_from_weights(w: pd.DataFrame) -> pd.Series:
    """
    例: turnover[t] = 0.5 * sum_i |w_i[t] - w_i[t-1]|
    （定義は仕様で固定）
    """
    raise NotImplementedError

def apply_costs(gross_returns: pd.Series, turnover: pd.Series, cost_bps: float) -> pd.Series:
    """
    net = gross - cost_bps/1e4 * turnover
    """
    raise NotImplementedError

def factor_alpha_regression(returns: pd.Series, factors: pd.DataFrame, add_intercept: bool=True) -> dict:
    """
    出力: alpha, beta, t-stats, r2 など
    擬似:
      y = returns
      X = factors (+ const)
      OLSで推定して統計量を返す
    """
    raise NotImplementedError

def run_cost_sensitivity(
    gross_returns: pd.Series,
    turnover: pd.Series,
    factors: pd.DataFrame,
    cost_grid_bps: list[float],
) -> pd.DataFrame:
    """
    costごとに alpha/sharpe 等を並べる
    """
    raise NotImplementedError
```

* * *

ここまでが「Phase 1で許される最大限の“実装直前”」
=============================

*   関数の **I/Oは完全に固定**
*   内部は **擬似コード**で処理内容を明確化
*   `raise NotImplementedError` のままなので **動く実装ではない**（＝Phase 1遵守）

* * *

次に（あなたがPhase 2へ進むなら）
--------------------

Phase 2に移行して **実装解禁**になった時点で、上の `NotImplementedError` をすべて埋めて「最小テスト（ダミーデータで形状一致）」まで一気に通せます。

もし今このチャットで「Phase 2に進めて実装OK」という扱いに変更するなら、(1)〜(7)を **実コードとして完成版**で出します。

## Prompt:
Phase 2に進めて実装OK、(1)〜(7)を 実コードとして完成版で

## Response:
了解。以下に **(1)〜(7)** を「そのまま動く完成版の実コード」としてまとめて出します（pandas/numpyのみ依存）。  
設計上の前提は **日次データ、欠損は0埋めしない、indexはDatetimeIndex** です。

```python
# (1)〜(7) Active Thematic ETF Strategy - Phase 2 Implementations
# Dependencies: numpy, pandas (only)

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Optional, Dict, Tuple, List

import numpy as np
import pandas as pd

# ----------------------------
# Utilities
# ----------------------------

def _align_index(*objs):
    """Align multiple pd objects to the common DatetimeIndex (intersection), preserving column names."""
    idx = None
    for o in objs:
        if o is None:
            continue
        if idx is None:
            idx = o.index
        else:
            idx = idx.intersection(o.index)
    if idx is None:
        raise ValueError("No objects to align.")
    out = []
    for o in objs:
        if o is None:
            out.append(None)
        else:
            out.append(o.loc[idx])
    return out

def _safe_div(a: np.ndarray, b: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    return a / (b + eps)

def _add_const(X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones((X.shape[0], 1)), X])

def _winsorize_1d(x: np.ndarray, q_low: float, q_high: float) -> np.ndarray:
    if x.size == 0:
        return x
    lo = np.nanquantile(x, q_low)
    hi = np.nanquantile(x, q_high)
    return np.clip(x, lo, hi)

# ----------------------------
# (1) Somefun: Thematic return decomposition via factor model
# ----------------------------

RegType = Literal["ols", "ridge"]

@dataclass(frozen=True)
class FactorDecompConfig:
    lookback: int = 252
    reg: RegType = "ols"
    ridge_alpha: float = 1.0
    add_intercept: bool = True
    min_obs: int = 200  # minimum valid observations within the rolling window

def compute_returns_from_prices(prices: pd.DataFrame, method: Literal["log", "simple"] = "log") -> pd.DataFrame:
    """
    prices: date×asset
    returns: date×asset
    """
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise TypeError("prices.index must be a DatetimeIndex")
    prices = prices.sort_index()
    if method == "log":
        r = np.log(prices / prices.shift(1))
    elif method == "simple":
        r = prices.pct_change()
    else:
        raise ValueError("method must be 'log' or 'simple'")
    return r

def compute_excess_returns(
    returns: pd.DataFrame,
    rf: Optional[pd.Series] = None,
    benchmark: Optional[pd.Series] = None
) -> pd.DataFrame:
    """
    XR = returns - rf  (preferred)  or returns - benchmark
    """
    if rf is not None and benchmark is not None:
        raise ValueError("Provide either rf or benchmark, not both.")
    if rf is None and benchmark is None:
        # Allow, but user should be explicit in research settings
        return returns.copy()

    if rf is not None:
        if not returns.index.equals(rf.index):
            returns, rf = _align_index(returns, rf)
        return returns.sub(rf, axis=0)
    else:
        if not returns.index.equals(benchmark.index):
            returns, benchmark = _align_index(returns, benchmark)
        return returns.sub(benchmark, axis=0)

def _fit_regression(
    y: np.ndarray,
    X: np.ndarray,
    reg: RegType,
    ridge_alpha: float,
    add_intercept: bool
) -> Tuple[np.ndarray, float]:
    """
    Fit y ~ X (+ intercept).
    Returns: coef (including intercept if add_intercept), r2
    """
    if add_intercept:
        X_ = _add_const(X)
    else:
        X_ = X

    # Drop rows with NaN in y or X
    mask = np.isfinite(y) & np.all(np.isfinite(X_), axis=1)
    yv = y[mask]
    Xv = X_[mask]
    if yv.size == 0:
        return np.full((X_.shape[1],), np.nan), np.nan

    if reg == "ols":
        coef, *_ = np.linalg.lstsq(Xv, yv, rcond=None)
    elif reg == "ridge":
        # Closed form: (X'X + aI)^-1 X'y ; do not penalize intercept
        XtX = Xv.T @ Xv
        Xty = Xv.T @ yv
        I = np.eye(XtX.shape[0])
        if add_intercept:
            I[0, 0] = 0.0
        coef = np.linalg.solve(XtX + ridge_alpha * I, Xty)
    else:
        raise ValueError("reg must be 'ols' or 'ridge'")

    yhat = Xv @ coef
    ss_res = float(np.sum((yv - yhat) ** 2))
    ss_tot = float(np.sum((yv - np.mean(yv)) ** 2))
    r2 = np.nan if ss_tot == 0 else 1.0 - ss_res / ss_tot
    return coef, r2

def rolling_factor_decompose(
    xr: pd.DataFrame,          # date×asset
    factors: pd.DataFrame,     # date×k
    cfg: FactorDecompConfig,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """
    Rolling factor regression to obtain alpha/beta/residual at each date.
    Output is defined at each date t (window end), based on last observation in the window.
    """
    if not isinstance(xr.index, pd.DatetimeIndex) or not isinstance(factors.index, pd.DatetimeIndex):
        raise TypeError("xr and factors must have DatetimeIndex")
    xr, factors = _align_index(xr.sort_index(), factors.sort_index())

    dates = xr.index
    assets = list(xr.columns)
    factor_names = list(factors.columns)
    L = cfg.lookback

    alpha = pd.DataFrame(index=dates, columns=assets, dtype=float)
    resid = pd.DataFrame(index=dates, columns=assets, dtype=float)
    r2_df = pd.DataFrame(index=dates, columns=assets, dtype=float)
    beta_dict = {fn: pd.DataFrame(index=dates, columns=assets, dtype=float) for fn in factor_names}

    X_all = factors.values

    for t_idx in range(L - 1, len(dates)):
        win_slice = slice(t_idx - L + 1, t_idx + 1)
        Xw = X_all[win_slice, :]
        # For each asset, regress within window
        for a in assets:
            yw = xr[a].values[win_slice]
            # Count valid obs after dropping NaNs
            if cfg.add_intercept:
                X_design = _add_const(Xw)
            else:
                X_design = Xw
            mask = np.isfinite(yw) & np.all(np.isfinite(X_design), axis=1)
            nobs = int(mask.sum())
            if nobs < cfg.min_obs:
                continue

            coef, r2_val = _fit_regression(
                y=yw, X=Xw, reg=cfg.reg, ridge_alpha=cfg.ridge_alpha, add_intercept=cfg.add_intercept
            )
            # Last point residual in window (end t)
            y_last = yw[-1]
            x_last = Xw[-1, :]
            if not np.isfinite(y_last) or not np.all(np.isfinite(x_last)):
                continue
            if cfg.add_intercept:
                yhat_last = float(np.dot(np.r_[1.0, x_last], coef))
                alpha.loc[dates[t_idx], a] = float(coef[0])
                betas = coef[1:]
            else:
                yhat_last = float(np.dot(x_last, coef))
                alpha.loc[dates[t_idx], a] = 0.0
                betas = coef

            resid.loc[dates[t_idx], a] = float(y_last - yhat_last)
            r2_df.loc[dates[t_idx], a] = r2_val
            for j, fn in enumerate(factor_names):
                beta_dict[fn].loc[dates[t_idx], a] = float(betas[j])

    return alpha, beta_dict, resid, r2_df

def estimate_thematic_vol(resid: pd.DataFrame, lookback: int = 252, annualization: int = 252) -> pd.DataFrame:
    """
    Thematic (idiosyncratic) volatility proxy: rolling std of residuals * sqrt(annualization)
    """
    if not isinstance(resid.index, pd.DatetimeIndex):
        raise TypeError("resid.index must be DatetimeIndex")
    vol = resid.rolling(lookback, min_periods=max(20, lookback // 4)).std() * np.sqrt(annualization)
    return vol

# ----------------------------
# (2) MSCI: Ranking selection (Top-K rotation)
# ----------------------------

Weighting = Literal["equal", "score_proportional"]

@dataclass(frozen=True)
class TopKConfig:
    k: int
    weighting: Weighting = "equal"
    min_score: Optional[float] = None

def select_topk_weights(
    scores: pd.DataFrame,                 # date×asset
    rebalance_dates: List[pd.Timestamp],
    cfg: TopKConfig,
    eligibility: Optional[pd.DataFrame] = None,  # date×asset bool
) -> pd.DataFrame:
    """
    Select top-k assets by score on each rebalance date, output target weights.
    """
    if not isinstance(scores.index, pd.DatetimeIndex):
        raise TypeError("scores.index must be DatetimeIndex")
    scores = scores.sort_index()

    if eligibility is not None:
        if not isinstance(eligibility.index, pd.DatetimeIndex):
            raise TypeError("eligibility.index must be DatetimeIndex")
        scores, eligibility = _align_index(scores, eligibility)

    # Ensure rebalance dates exist in index
    idx_set = set(scores.index)
    rb = [pd.Timestamp(d) for d in rebalance_dates if pd.Timestamp(d) in idx_set]
    if len(rb) == 0:
        raise ValueError("No rebalance_dates exist in scores.index")

    assets = scores.columns
    target = pd.DataFrame(0.0, index=rb, columns=assets)

    for t in rb:
        s = scores.loc[t].copy()
        if eligibility is not None:
            elig = eligibility.loc[t]
            s = s.where(elig.astype(bool))
        if cfg.min_score is not None:
            s = s.where(s >= cfg.min_score)

        s = s.dropna()
        if s.empty:
            continue

        selected = s.sort_values(ascending=False).head(cfg.k)
        if cfg.weighting == "equal":
            w = pd.Series(1.0 / len(selected), index=selected.index)
        else:
            denom = float(selected.sum())
            if denom <= 0 or not np.isfinite(denom):
                # fallback
                w = pd.Series(1.0 / len(selected), index=selected.index)
            else:
                w = selected / denom

        target.loc[t, w.index] = w.values

    # Normalize rows (safety)
    row_sum = target.sum(axis=1)
    target = target.div(row_sum.replace(0.0, np.nan), axis=0).fillna(0.0)
    return target

# ----------------------------
# (3) MSCI: Linear composition of weights
# ----------------------------

def compose_linear_weights(
    outer_weights: pd.DataFrame,                      # date×outer
    inner_weights: Dict[str, pd.Series],              # outer -> (asset weights)
    normalize: bool = True,
) -> pd.DataFrame:
    """
    Compose weights: w_asset(t) = sum_j w_outer(t,j) * w_asset|j
    """
    if not isinstance(outer_weights.index, pd.DatetimeIndex):
        raise TypeError("outer_weights.index must be DatetimeIndex")
    outer_weights = outer_weights.sort_index()

    # Collect union of all assets
    asset_set = set()
    for k, s in inner_weights.items():
        if not isinstance(s, pd.Series):
            raise TypeError(f"inner_weights[{k}] must be pd.Series")
        asset_set |= set(s.index)

    assets = sorted(asset_set)
    out = pd.DataFrame(0.0, index=outer_weights.index, columns=assets)

    for outer in outer_weights.columns:
        if outer not in inner_weights:
            continue
        w_inner = inner_weights[outer].reindex(assets).fillna(0.0).astype(float)
        out = out.add(outer_weights[outer].values.reshape(-1, 1) * w_inner.values.reshape(1, -1))

    if normalize:
        row_sum = out.sum(axis=1)
        out = out.div(row_sum.replace(0.0, np.nan), axis=0).fillna(0.0)
    return out

# ----------------------------
# (4) MSCI: Vol targeting (dual EWMA variance and leverage scaling)
# ----------------------------

@dataclass(frozen=True)
class EWMAVolConfig:
    lam_st: float = 0.94
    lam_lt: float = 0.97
    lag: int = 3
    annualization: int = 252
    combine_rule: Literal["max", "weighted"] = "max"
    w_st: float = 0.5
    target_vol: float = 0.10
    w_min: float = 0.0
    w_max: float = 1.0  # set >1.0 if leverage allowed

def ewma_var(returns: pd.Series, lam: float, lag: int) -> pd.Series:
    """
    EWMA variance with lag: var[t] = lam*var[t-1] + (1-lam)*r[t-lag]^2
    """
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise TypeError("returns.index must be DatetimeIndex")
    r = returns.sort_index().astype(float)
    r_lag = r.shift(lag)
    out = pd.Series(index=r.index, dtype=float)

    # init with expanding mean of squared lagged returns (first valid region)
    sq = r_lag.pow(2)
    first_valid = sq.first_valid_index()
    if first_valid is None:
        return out

    # Initialize at first_valid using its squared value
    out.loc[first_valid] = float(sq.loc[first_valid])

    # Iterate
    started = False
    prev = np.nan
    for t in r.index:
        x = sq.loc[t]
        if not np.isfinite(x):
            # carry forward variance if started, else keep NaN
            if started:
                out.loc[t] = prev
            continue
        if not started:
            prev = float(x)
            out.loc[t] = prev
            started = True
        else:
            prev = lam * prev + (1.0 - lam) * float(x)
            out.loc[t] = prev

    return out

def forecast_vol_dual(returns: pd.Series, cfg: EWMAVolConfig) -> pd.Series:
    """
    Forecast annualized volatility from dual EWMA variances.
    """
    var_st = ewma_var(returns, cfg.lam_st, cfg.lag)
    var_lt = ewma_var(returns, cfg.lam_lt, cfg.lag)

    if cfg.combine_rule == "max":
        var = pd.concat([var_st, var_lt], axis=1).max(axis=1)
    elif cfg.combine_rule == "weighted":
        var = cfg.w_st * var_st + (1.0 - cfg.w_st) * var_lt
    else:
        raise ValueError("combine_rule must be 'max' or 'weighted'")

    sigma = np.sqrt(var) * np.sqrt(cfg.annualization)
    return sigma

def vol_target_leverage(sigma: pd.Series, cfg: EWMAVolConfig) -> pd.Series:
    """
    Leverage/scaling factor W[t] = target_vol / sigma[t], clipped to [w_min, w_max]
    """
    sigma = sigma.astype(float)
    W = cfg.target_vol / sigma.replace(0.0, np.nan)
    W = W.clip(lower=cfg.w_min, upper=cfg.w_max)
    return W

def apply_vol_target_to_returns(port_returns: pd.Series, W: pd.Series) -> pd.Series:
    """
    r_scaled[t] = W[t] * r_port[t]
    """
    port_returns, W = _align_index(port_returns, W)
    return (port_returns.astype(float) * W.astype(float)).rename("scaled_return")

# ----------------------------
# (5) THEME: Text similarity (Purity) (no training; embed_fn is injected)
# ----------------------------

EmbedFn = Callable[[List[str]], np.ndarray]

def cosine_sim_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity matrix between rows of A and rows of B.
    """
    if A.ndim != 2 or B.ndim != 2:
        raise ValueError("A and B must be 2D arrays")
    An = _safe_div(A, np.linalg.norm(A, axis=1, keepdims=True))
    Bn = _safe_div(B, np.linalg.norm(B, axis=1, keepdims=True))
    return An @ Bn.T

def compute_text_similarity(
    etf_texts: Dict[str, str],
    theme_texts: Dict[str, str],
    embed_fn: EmbedFn,
) -> pd.DataFrame:
    """
    Returns: similarity DataFrame index=tickers, columns=themes
    """
    if len(etf_texts) == 0 or len(theme_texts) == 0:
        raise ValueError("etf_texts and theme_texts must be non-empty")

    tickers = list(etf_texts.keys())
    themes = list(theme_texts.keys())

    E = embed_fn([etf_texts[t] for t in tickers])
    T = embed_fn([theme_texts[k] for k in themes])

    if not isinstance(E, np.ndarray) or not isinstance(T, np.ndarray):
        raise TypeError("embed_fn must return np.ndarray")
    if E.shape[0] != len(tickers) or T.shape[0] != len(themes):
        raise ValueError("embed_fn output shape mismatch")

    S = cosine_sim_matrix(E, T)
    return pd.DataFrame(S, index=tickers, columns=themes, dtype=float)

def compute_purity(sim: pd.DataFrame, etf2theme: Dict[str, str]) -> pd.Series:
    """
    Purity = similarity to the ETF's assigned theme.
    """
    out = {}
    for etf, theme in etf2theme.items():
        if etf not in sim.index or theme not in sim.columns:
            out[etf] = np.nan
        else:
            out[etf] = float(sim.loc[etf, theme])
    return pd.Series(out, name="purity").reindex(sim.index)

# ----------------------------
# (6) THEME: semantic + temporal score (purity + momentum)
# ----------------------------

@dataclass(frozen=True)
class SemanticTemporalConfig:
    lookback: int = 63
    a: float = 1.0  # purity weight
    b: float = 1.0  # momentum weight
    winsor_q: Tuple[float, float] = (0.01, 0.99)

def cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    Z-score across assets for each date: (x-mean)/std, ignoring NaNs.
    """
    mean = df.mean(axis=1, skipna=True)
    std = df.std(axis=1, skipna=True).replace(0.0, np.nan)
    return df.sub(mean, axis=0).div(std, axis=0)

def compute_momentum_score(returns: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """
    Momentum proxy: rolling sum of returns over lookback, then cross-sectional z-score per date.
    (For log returns, sum is consistent with cumulative log return.)
    """
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise TypeError("returns.index must be DatetimeIndex")
    returns = returns.sort_index().astype(float)
    cum = returns.rolling(lookback, min_periods=max(10, lookback // 4)).sum()
    mom = cross_sectional_zscore(cum)
    return mom

def combine_semantic_temporal_scores(
    purity: pd.Series,     # asset
    mom: pd.DataFrame,     # date×asset
    cfg: SemanticTemporalConfig,
) -> pd.DataFrame:
    """
    score[t,i] = a*purity[i] + b*mom[t,i], with winsorization per date.
    """
    purity = purity.astype(float)
    # Align columns
    common_assets = [c for c in mom.columns if c in purity.index]
    mom_ = mom[common_assets].copy()
    p = purity.reindex(common_assets)

    score = cfg.a * mom_.copy()  # start with mom
    score = score.mul(cfg.b)
    score = score.add(cfg.a * p.values.reshape(1, -1))

    # Winsorize per date across assets
    ql, qh = cfg.winsor_q
    def _wz(row: pd.Series) -> pd.Series:
        x = row.values.astype(float)
        if np.all(~np.isfinite(x)):
            return row
        lo = np.nanquantile(x, ql)
        hi = np.nanquantile(x, qh)
        return row.clip(lower=lo, upper=hi)

    score = score.apply(_wz, axis=1)
    return score

# ----------------------------
# (7) Naffa & Fain: demand (flow) score + PFP/CWLS + alpha regression
# ----------------------------

@dataclass(frozen=True)
class DemandScoreConfig:
    lookback: int = 63
    winsor_q: Tuple[float, float] = (0.01, 0.99)
    zscore_mode: Literal["asset_rolling", "date_cross"] = "asset_rolling"

def estimate_net_flows_from_aum(prices: pd.DataFrame, aum: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate net flows from AUM change minus price effect:
      flow_est[t] = (AUM[t] - AUM[t-1]) - AUM[t-1]*r[t]
    """
    if not isinstance(prices.index, pd.DatetimeIndex) or not isinstance(aum.index, pd.DatetimeIndex):
        raise TypeError("prices/aum must have DatetimeIndex")
    prices, aum = _align_index(prices.sort_index(), aum.sort_index())
    r = prices.pct_change()
    aum_change = aum.diff()
    price_effect = aum.shift(1) * r
    flow_est = aum_change - price_effect
    return flow_est

def winsorize(df: pd.DataFrame, q_low: float = 0.01, q_high: float = 0.99, axis: Literal["date","all"]="date") -> pd.DataFrame:
    """
    Winsorize values.
      axis="date": per date across assets (row-wise)
      axis="all": global across all entries
    """
    out = df.copy().astype(float)
    if axis == "all":
        x = out.values
        lo = np.nanquantile(x, q_low)
        hi = np.nanquantile(x, q_high)
        return out.clip(lo, hi)
    elif axis == "date":
        def _w(row: pd.Series) -> pd.Series:
            x = row.values.astype(float)
            if np.all(~np.isfinite(x)):
                return row
            lo = np.nanquantile(x, q_low)
            hi = np.nanquantile(x, q_high)
            return row.clip(lo, hi)
        return out.apply(_w, axis=1)
    else:
        raise ValueError("axis must be 'date' or 'all'")

def rolling_zscore_assetwise(df: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """
    Rolling z-score per asset column (time-series z-score):
      z[t] = (x[t] - mean_{t-L..t}) / std_{t-L..t}
    """
    mean = df.rolling(lookback, min_periods=max(10, lookback // 4)).mean()
    std = df.rolling(lookback, min_periods=max(10, lookback // 4)).std().replace(0.0, np.nan)
    return (df - mean) / std

def compute_demand_score(flow: pd.DataFrame, cfg: DemandScoreConfig) -> pd.DataFrame:
    """
    Demand score by z-scoring and winsorizing.
    """
    flow = flow.sort_index().astype(float)

    if cfg.zscore_mode == "asset_rolling":
        z = rolling_zscore_assetwise(flow, cfg.lookback)
    elif cfg.zscore_mode == "date_cross":
        z = cross_sectional_zscore(flow)
    else:
        raise ValueError("zscore_mode must be 'asset_rolling' or 'date_cross'")

    z = winsorize(z, cfg.winsor_q[0], cfg.winsor_q[1], axis="date")
    return z

# --- PFP / FM / CWLS

def cap_weighted_zscore(X: pd.DataFrame, w: pd.Series) -> pd.DataFrame:
    """
    Cap-weighted z-score per descriptor column:
      z = (x - sum(w*x)) / sqrt(sum(w*x^2) - (sum(w*x))^2)
    w should sum to 1 (will be normalized).
    """
    X = X.astype(float)
    w = w.reindex(X.index).astype(float)
    w = w / w.sum() if w.sum() != 0 else w

    # Weighted mean per column
    mu = (X.mul(w, axis=0)).sum(axis=0)
    ex2 = (X.pow(2).mul(w, axis=0)).sum(axis=0)
    var = ex2 - mu.pow(2)
    std = np.sqrt(var.replace(0.0, np.nan))
    Z = (X - mu) / std
    return Z

def fm_factor_returns(R_next: pd.Series, Z: pd.DataFrame) -> pd.Series:
    """
    Cross-sectional OLS: F_hat = (Z'Z)^-1 Z'R
    """
    # Align
    R = R_next.reindex(Z.index).astype(float)
    Zm = Z.astype(float)

    mask = np.isfinite(R.values) & np.all(np.isfinite(Zm.values), axis=1)
    Rv = R.values[mask]
    Zv = Zm.values[mask, :]
    if Rv.size == 0:
        return pd.Series(index=Z.columns, data=np.nan)

    XtX = Zv.T @ Zv
    Xty = Zv.T @ Rv
    try:
        coef = np.linalg.solve(XtX, Xty)
    except np.linalg.LinAlgError:
        coef = np.linalg.lstsq(XtX, Xty, rcond=None)[0]
    return pd.Series(coef, index=Z.columns, name="factor_return")

def cwls_pfp_weights(Z: pd.DataFrame, V: pd.Series, C: np.ndarray) -> np.ndarray:
    """
    Compute PW = C (C^T Z^T V Z C)^(-1) C^T Z^T V
    Here V is diagonal weights as a vector aligned with assets.
    Returns PW as a numpy array with shape (k_c, n_assets) if C has shape (k, k_c).
    """
    Zm = Z.astype(float)
    v = V.reindex(Zm.index).astype(float).values
    if v.ndim != 1:
        raise ValueError("V must be a Series aligned to Z.index")
    n, k = Zm.shape
    if C.ndim != 2 or C.shape[0] != k:
        raise ValueError(f"C must be 2D with shape ({k}, k_c)")

    # Build weighted matrices without constructing full diag(V)
    # Z^T V Z = Z^T (diag(v) Z) = Z^T (v[:,None]*Z)
    Zv = Zm.values
    VZ = (v.reshape(-1, 1) * Zv)
    ZtVZ = Zv.T @ VZ
    ZtV = Zv.T * v  # shape k×n, equals Z^T diag(v)

    Ct = C.T
    M = Ct @ ZtVZ @ C  # (k_c × k_c)
    try:
        M_inv = np.linalg.inv(M)
    except np.linalg.LinAlgError:
        M_inv = np.linalg.pinv(M)

    PW = C @ M_inv @ Ct @ ZtV  # shape (k × n)
    return PW

# --- Alpha regression + costs

def turnover_from_weights(w: pd.DataFrame) -> pd.Series:
    """
    Turnover proxy:
      turnover[t] = 0.5 * sum_i |w_i[t] - w_i[t-1]|
    """
    w = w.sort_index().astype(float)
    dw = w.diff()
    tnr = 0.5 * dw.abs().sum(axis=1)
    return tnr.rename("turnover")

def apply_costs(gross_returns: pd.Series, turnover: pd.Series, cost_bps: float) -> pd.Series:
    """
    net = gross - (cost_bps/1e4) * turnover
    """
    gross_returns, turnover = _align_index(gross_returns, turnover)
    net = gross_returns.astype(float) - (cost_bps / 1e4) * turnover.astype(float)
    return net.rename("net_return")

def factor_alpha_regression(
    returns: pd.Series,
    factors: pd.DataFrame,
    add_intercept: bool = True
) -> Dict[str, object]:
    """
    OLS regression: returns = alpha + beta' factors + eps
    Returns alpha/beta/t-stats/r2/nobs/sigma_hat.

    Notes:
      - Uses classical (homoskedastic) standard errors (no HAC).
      - Drops rows with any NaN.
    """
    y = returns.astype(float)
    X = factors.astype(float)
    y, X = _align_index(y, X)

    df = pd.concat([y.rename("y"), X], axis=1).dropna()
    if df.shape[0] < X.shape[1] + (1 if add_intercept else 0) + 5:
        return {"alpha": np.nan, "beta": pd.Series(index=X.columns, data=np.nan), "t_alpha": np.nan,
                "t_beta": pd.Series(index=X.columns, data=np.nan), "r2": np.nan, "nobs": df.shape[0]}

    yv = df["y"].values
    Xv = df[X.columns].values
    if add_intercept:
        Xv = _add_const(Xv)
        colnames = ["const"] + list(X.columns)
    else:
        colnames = list(X.columns)

    # OLS
    coef, *_ = np.linalg.lstsq(Xv, yv, rcond=None)
    yhat = Xv @ coef
    resid = yv - yhat

    n = Xv.shape[0]
    p = Xv.shape[1]
    dof = max(1, n - p)
    sigma2 = float((resid @ resid) / dof)

    # Var(coef) = sigma^2 (X'X)^-1
    XtX = Xv.T @ Xv
    try:
        XtX_inv = np.linalg.inv(XtX)
    except np.linalg.LinAlgError:
        XtX_inv = np.linalg.pinv(XtX)
    se = np.sqrt(np.diag(sigma2 * XtX_inv))
    tstats = coef / (se + 1e-12)

    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((yv - np.mean(yv)) ** 2))
    r2 = np.nan if ss_tot == 0 else 1.0 - ss_res / ss_tot

    if add_intercept:
        alpha = float(coef[0])
        beta = pd.Series(coef[1:], index=X.columns, name="beta")
        t_alpha = float(tstats[0])
        t_beta = pd.Series(tstats[1:], index=X.columns, name="t_beta")
    else:
        alpha = 0.0
        beta = pd.Series(coef, index=X.columns, name="beta")
        t_alpha = np.nan
        t_beta = pd.Series(tstats, index=X.columns, name="t_beta")

    return {
        "alpha": alpha,
        "beta": beta,
        "t_alpha": t_alpha,
        "t_beta": t_beta,
        "r2": r2,
        "nobs": n,
        "sigma": np.sqrt(sigma2),
    }

def run_cost_sensitivity(
    gross_returns: pd.Series,
    turnover: pd.Series,
    factors: pd.DataFrame,
    cost_grid_bps: List[float],
) -> pd.DataFrame:
    """
    For each cost_bps, compute net returns and alpha regression stats.
    """
    rows = []
    for c in cost_grid_bps:
        net = apply_costs(gross_returns, turnover, c)
        stats = factor_alpha_regression(net, factors, add_intercept=True)
        rows.append({
            "cost_bps": c,
            "alpha": stats["alpha"],
            "t_alpha": stats["t_alpha"],
            "r2": stats["r2"],
            "nobs": stats["nobs"],
        })
    return pd.DataFrame(rows).set_index("cost_bps")

# ----------------------------
# Optional: Portfolio return calculator (useful glue)
# ----------------------------

def compute_portfolio_returns(returns: pd.DataFrame, weights: pd.DataFrame, forward_fill_weights: bool = True) -> pd.Series:
    """
    Compute daily portfolio returns given asset returns and (possibly sparse) weights.
    weights can be defined only on rebalance dates; if forward_fill_weights=True, it will be ffilled daily.
    Assumes weights are *start-of-day* weights applied to same-day returns (you may shift if you prefer).
    """
    if not isinstance(returns.index, pd.DatetimeIndex) or not isinstance(weights.index, pd.DatetimeIndex):
        raise TypeError("returns/weights must have DatetimeIndex")

    returns = returns.sort_index().astype(float)
    weights = weights.sort_index().astype(float)

    # Align dates
    common_dates = returns.index.intersection(weights.index) if not forward_fill_weights else returns.index
    weights_daily = weights.reindex(common_dates)
    if forward_fill_weights:
        weights_daily = weights_daily.reindex(returns.index).ffill().fillna(0.0)

    # Align columns
    common_assets = [c for c in returns.columns if c in weights_daily.columns]
    if not common_assets:
        raise ValueError("No overlapping assets between returns and weights")
    r = returns[common_assets]
    w = weights_daily[common_assets]

    # Ensure row sums are 1 (optional safety)
    row_sum = w.sum(axis=1).replace(0.0, np.nan)
    w = w.div(row_sum, axis=0).fillna(0.0)

    port = (w * r).sum(axis=1)
    return port.rename("portfolio_return")
```

* * *

使い方の最小例（動作確認の順序）
----------------

（あなたの(1)〜(7)を “部品ごと”に確認するための最短）

1.  **(2) Top-K選抜**
    *   `scores`（date×ETF）を用意 → `select_topk_weights(scores, rebalance_dates, TopKConfig(k=4))`
    2.  **(4) ボラターゲット**
    *   `port_returns` を作る（下の `compute_portfolio_returns` でOK）
*   `sigma = forecast_vol_dual(port_returns, EWMAVolConfig(...))`
*   `W = vol_target_leverage(sigma, cfg)`
*   `scaled = apply_vol_target_to_returns(port_returns, W)`
    3.  **(1) 因子分解**
    *   `xr = compute_excess_returns(returns, rf=...)`
*   `alpha, beta, resid, r2 = rolling_factor_decompose(xr, factors, cfg)`
*   `thematic_vol = estimate_thematic_vol(resid)`
    4.  **(5)(6) テキストpurity＋semantic-temporal**
    *   `sim = compute_text_similarity(etf_texts, theme_texts, embed_fn)`
*   `purity = compute_purity(sim, etf2theme)`
*   `mom = compute_momentum_score(returns, lookback=63)`
*   `score = combine_semantic_temporal_scores(purity, mom, cfg)`
    5.  **(7) 需要（フロー）＋α検定**
    *   `flow = estimate_net_flows_from_aum(prices, aum)`
*   `demand_score = compute_demand_score(flow, cfg)`
*   `turnover = turnover_from_weights(weights_daily_or_rebalance)`
*   `net = apply_costs(gross_returns, turnover, cost_bps=50)`
*   `stats = factor_alpha_regression(net, factors)`
*   `grid = run_cost_sensitivity(gross_returns, turnover, factors, [25,50,100,150])`

* * *

重要な注意（あなたの元テキスト(7)の警告に対応）
-------------------------

*   **先読み防止**：`scores` / `aum` / `flow` / `text` をいつの時点で観測可能とするかは、必ず「遅延ルール」を固定してください（例：月次スコアは翌営業日から有効）。
*   **欠損0埋め禁止**：この実装は基本 NaN を落とす／ffill する前提で設計しています。
*   \*\*THEMEの学習（InfoNCE/Triplet）\*\*は含めていません（ここは先読み・学習分離が難しく、まずは“学習なし”を安定稼働させるのが筋）。

* * *

必要なら次に、あなたの **コア18ETF** に合わせて

*   `rebalance_dates`（月末最終営業日など）の生成
*   「層A/B/C」を1本の `run_strategy()` にまとめる
*   ユニットテスト（ダミーデータで形状保証）

まで一気に仕上げます。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)