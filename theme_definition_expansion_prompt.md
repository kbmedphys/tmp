# Theme Definition 拡張指示書
## Broad News + Revenue Driver Based Theme Rotation 用

以下をそのまま ChatGPT / Codex / LLM に貼って使ってください。

---

あなたは日本株テーマ投資、金融ニュース分類、自然言語処理、クオンツ運用に詳しいリサーチャーです。

以下の既存テーマ定義を、LSEG / Refinitiv ニュースを用いた Broad News + Revenue Driver Based Theme Rotation 戦略で利用できるように拡張してください。

# 目的

拡張後のテーマ定義は、以下に使います。

1. Broadニュース本文との embedding 類似度計算
2. 収益ドライバー単位の embedding 類似度計算
3. ニュースからテーマへの多ラベル帰属
4. Keyword Match による補正
5. Tone 判定
6. DriverBreadth の計算
7. EntityBreadth の補助計算
8. ThemeScore の算出

# 入力

以下の情報を与えます。

- theme_id
- theme_name_en
- theme_name_ja
- theme_description_en
- theme_description_ja
- 必要に応じて、構成銘柄情報
- 必要に応じて、既存の catalysts / revenue drivers / keywords

# 出力形式

必ず以下の YAML 形式のみで出力してください。

```yaml
themes:
  - theme_id: ""
    theme_name_en: ""
    theme_name_ja: ""
    theme_type: ""

    description_en: ""
    description_ja: ""

    profile_summary_en: ""
    profile_summary_ja: ""

    revenue_drivers:
      - driver_id: ""
        driver_name_en: ""
        driver_name_ja: ""
        driver_type: ""
        driver_description_en: ""
        driver_description_ja: ""
        driver_embedding_text: ""
        driver_keywords_en:
          - ""
        driver_keywords_ja:
          - ""
        positive_driver_events_en:
          - ""
        positive_driver_events_ja:
          - ""
        negative_driver_events_en:
          - ""
        negative_driver_events_ja:
          - ""

    catalysts_en:
      - ""
    catalysts_ja:
      - ""

    positive_events_en:
      - ""
    positive_events_ja:
      - ""

    negative_events_en:
      - ""
    negative_events_ja:
      - ""

    related_macro_factors_en:
      - ""
    related_macro_factors_ja:
      - ""

    related_policy_factors_en:
      - ""
    related_policy_factors_ja:
      - ""

    related_industries:
      gics_sectors:
        - ""
      gics_industries:
        - ""
      trbc_industries:
        - ""

    keyword_match_terms_en:
      - ""
    keyword_match_terms_ja:
      - ""

    embedding_text: ""

    entity_linking_terms:
      rics:
        - ""
      company_names_en:
        - ""
      company_names_ja:
        - ""
      aliases_en:
        - ""
      aliases_ja:
        - ""

    notes_for_classification: ""
```

# 作成ルール

## theme_id

入力の theme_id をそのまま使ってください。変更しないでください。

## theme_name_en / theme_name_ja

入力を尊重してください。日本語名がない場合のみ自然に補完してください。

## theme_type

以下から1つ選んでください。

- industry_theme
- style_theme
- policy_theme
- macro_theme
- event_theme
- industry_policy_theme
- macro_style_theme

判断基準:

| theme_type | 判断基準 | 例 |
|---|---|---|
| industry_theme | 産業、業種、技術、サプライチェーンが主軸 | 半導体、AI、電力インフラ、医療機器 |
| style_theme | バリュエーション、財務特性、株主還元が主軸 | 低PBR、高配当、クオリティ |
| policy_theme | 政策、規制、政府支出、補助金が主軸 | 防衛、GX、国土強靭化 |
| macro_theme | 金利、為替、資源価格、景気が主軸 | 円安メリット、資源高、インフレ |
| event_theme | M&A、自社株買い、決算、承認などが主軸 | TOB、自社株買い、薬事承認 |
| industry_policy_theme | 産業テーマと政策テーマの両方 | 防衛、半導体国内生産、電力網 |
| macro_style_theme | マクロ環境とスタイル特性の両方 | 地銀・金利上昇メリット、インフレ耐性高配当 |

## description_en / description_ja

3〜6文で、テーマの投資対象、収益ドライバー、ニュース分類で検出すべき論点を説明してください。

必ず以下を含めてください。

- 投資対象の概要
- 主な収益ドライバー
- ニュースで検出すべき論点
- 構成銘柄情報がある場合は、その実態
- テーマが反応しやすいマクロ・政策・産業イベント

悪い例:

```yaml
description_ja: "AI関連企業に投資するテーマ。"
```

良い例:

```yaml
description_ja: >
  このテーマは、生成AI、AI半導体、データセンター、クラウド基盤、
  産業用AIソフトウェア、電子部品、半導体製造装置に関連する日本株を対象とする。
  主な収益ドライバーは、AIサーバー需要、データセンター投資、
  半導体設備投資、企業のDX投資、クラウド利用拡大である。
  ニュース分類では、GPU需要、AI設備投資、半導体受注、データセンター増設、
  ハイパースケーラーの投資計画などを重視する。
```

## profile_summary_en / profile_summary_ja

1〜2文で、何にエクスポージャーを取るテーマかを簡潔にまとめてください。

## revenue_drivers

各テーマにつき5〜12個作成してください。

テーマを「収益ドライバーの集合」として分解してください。

各 driver には以下を必ず含めてください。

- driver_id
- driver_name_en
- driver_name_ja
- driver_type
- driver_description_en
- driver_description_ja
- driver_embedding_text
- driver_keywords_en
- driver_keywords_ja
- positive_driver_events_en
- positive_driver_events_ja
- negative_driver_events_en
- negative_driver_events_ja

## driver_id

以下の形式で作成してください。

```yaml
driver_id: "<theme_id>__driver_001"
```

例:

```yaml
driver_id: "semiconductor_equipment_jp__driver_001"
```

## driver_type

以下から1つ選んでください。

- demand_driver
- supply_driver
- capex_driver
- policy_driver
- macro_driver
- valuation_driver
- shareholder_return_driver
- earnings_driver
- technology_driver
- regulatory_driver
- event_driver

判断基準:

| driver_type | 内容 |
|---|---|
| demand_driver | 最終需要、販売量、利用拡大 |
| supply_driver | 供給制約、在庫、サプライチェーン |
| capex_driver | 設備投資、建設投資、投資サイクル |
| policy_driver | 政策支援、補助金、政府支出 |
| macro_driver | 金利、為替、資源価格、景気 |
| valuation_driver | PBR、PER、資本効率、割安修正 |
| shareholder_return_driver | 自社株買い、増配、配当方針 |
| earnings_driver | 業績修正、受注、利益率、決算 |
| technology_driver | 技術革新、製品サイクル |
| regulatory_driver | 規制、承認、輸出管理 |
| event_driver | M&A、TOB、訴訟、災害、事故 |

## driver_embedding_text

ニュース本文との embedding 類似度に直接使います。

日本語と英語を両方含め、ニュースに出やすい表現を入れてください。

例:

```yaml
driver_embedding_text: >
  Semiconductor capital expenditure cycle. 半導体設備投資サイクル。
  Wafer fab investment, foundry capex, AI semiconductor investment,
  memory capacity expansion, semiconductor equipment orders,
  半導体製造装置受注、ファウンドリー投資、AI半導体設備投資。
```

## driver_keywords_en / driver_keywords_ja

各 driver について、ニュース見出し・本文に出やすい具体的な語句を作成してください。

目安:

- 各 driver につき英語5〜15語
- 各 driver につき日本語5〜15語
- 名詞句中心
- 抽象語を避ける

## positive_driver_events / negative_driver_events

各 driver に対して、ポジティブ・ネガティブに解釈されやすいイベントを作成してください。

例:

```yaml
positive_driver_events_ja:
  - 設備投資増額
  - 受注回復
  - ファウンドリー投資拡大
  - メモリ価格回復

negative_driver_events_ja:
  - 設備投資削減
  - 受注減少
  - 投資延期
  - 輸出規制
```

## catalysts_en / catalysts_ja

各言語10〜30個作成してください。

ニュース見出し・本文に出やすい名詞句を中心にしてください。

テーマ名そのものだけに依存しないでください。

抽象語を避け、具体的な語句にしてください。

悪い例:

```yaml
catalysts_ja:
  - 成長
  - 市場
  - 需要
  - 投資
```

良い例:

```yaml
catalysts_ja:
  - 半導体設備投資
  - 半導体製造装置受注
  - AI半導体
  - ファウンドリー投資
  - メモリ市況
  - 輸出規制
  - データセンター投資
```

## positive_events_en / positive_events_ja

テーマ全体に対してポジティブと解釈されやすいイベントを5〜15個作成してください。

例:

```yaml
positive_events_ja:
  - 上方修正
  - 受注増加
  - 設備投資増額
  - 自社株買い発表
  - 増配
  - 補助金採択
  - 規制承認
  - 価格上昇
```

## negative_events_en / negative_events_ja

テーマ全体に対してネガティブと解釈されやすいイベントを5〜15個作成してください。

例:

```yaml
negative_events_ja:
  - 下方修正
  - 受注減少
  - 設備投資延期
  - 減配
  - 公募増資
  - 輸出規制
  - 行政処分
  - 訴訟
  - コスト増
```

## related_macro_factors_en / related_macro_factors_ja

テーマに影響するマクロ要因を列挙してください。

例:

```yaml
related_macro_factors_ja:
  - 国内金利
  - 長期金利
  - 米ドル円
  - 半導体サイクル
  - 設備投資サイクル
  - 原油価格
  - 電力価格
```

関係が薄い場合は空リストで構いません。

```yaml
related_macro_factors_ja: []
related_macro_factors_en: []
```

## related_policy_factors_en / related_policy_factors_ja

政策・規制・政府支出・補助金・制度改革に関係する要因を列挙してください。

例:

```yaml
related_policy_factors_ja:
  - 防衛予算
  - 半導体補助金
  - GX政策
  - 電力系統投資
  - 東証による資本効率改善要請
  - 経済安全保障
```

関係が薄い場合は空リストで構いません。

## related_industries

構成銘柄情報がある場合、GICS / TRBC を集約してください。

```yaml
related_industries:
  gics_sectors:
    - "Information Technology"
    - "Industrials"
  gics_industries:
    - "Semiconductors & Semiconductor Equipment"
    - "Electronic Equipment, Instruments & Components"
  trbc_industries:
    - "Semiconductor Equipment"
    - "Electronic Equipment & Parts"
```

ルール:

- 重複を除去する
- ウェイト上位または出現頻度が高いものを優先
- 最大10個程度に抑える
- 入力データにある表記を尊重する

## keyword_match_terms_en / keyword_match_terms_ja

ニュースのキーワード一致スコアに使う語句です。

以下を統合してください。

- catalysts
- revenue driver keywords
- positive events
- negative events
- macro factors
- policy factors
- 業界用語
- 表記ゆれ

各言語20〜50語を目安にしてください。

単体では広すぎる語は避けてください。

避けるべき例:

```text
成長
市場
需要
投資
企業
事業
株価
材料
```

使うなら具体化してください。

```text
AI需要
データセンター投資
半導体設備投資
防衛予算
資本効率改善
自社株買い発表
```

## embedding_text

テーマ全体の embedding に使う文章です。

必ず以下を含めてください。

- theme_name_en
- theme_name_ja
- description_en
- description_ja
- profile_summary_en
- profile_summary_ja
- revenue drivers の要約
- catalysts の要約
- related macro / policy factors
- 構成銘柄がある場合は、主要構成銘柄の特徴

作成ルール:

- 日本語と英語を両方含める
- ニュース本文に近い語彙を含める
- 長すぎないようにする
- 構成銘柄説明を入れる場合は、上位30社または累積80%まで
- 一企業だけに過度に寄せない

## entity_linking_terms

構成銘柄情報がある場合のみ作成してください。

```yaml
entity_linking_terms:
  rics:
    - "8035.T"
    - "6857.T"
  company_names_en:
    - "Tokyo Electron"
    - "Advantest"
  company_names_ja:
    - "東京エレクトロン"
    - "アドバンテスト"
  aliases_en:
    - "TEL"
  aliases_ja:
    - "東エレク"
```

ルール:

- RIC は入力値を変更しない
- 企業名は入力値を尊重する
- aliases は、明らかに一般的な略称のみ追加する
- 勝手に企業を追加しない
- 入力にない RIC を作らない

## notes_for_classification

ニュース分類時の注意点を短く記載してください。

例:

```yaml
notes_for_classification: >
  このテーマでは、個別企業名が出ないニュースでも、半導体設備投資、
  ファウンドリー投資、AI半導体需要、輸出規制に関するニュースは関連度を高く評価する。
  一方、一般的なテクノロジー株ニュースや米国大型テック企業の決算だけの記事は、
  日本の半導体製造装置需要との接続が弱い場合、関連度を低くする。
```

# 禁止事項

以下を守ってください。

- 入力データにない銘柄を追加しない
- RIC を変更しない
- ウェイトを変更しない
- theme_id を変更しない
- 企業説明にない事業を断定しない
- 投資推奨文にしない
- 「必ず上昇する」「恩恵を受ける」と断定しない
- 抽象的すぎる keyword を大量に入れない
- 一般語だけで catalyst を作らない
- ニュース分類に使えない美文にしない
- 事実ではなく期待だけで説明を膨らませない

# 許可される補完

以下は許可します。

- テーマ説明をニュース分類に適した形へ補強する
- 英語説明から自然な日本語表現を作る
- 日本語説明から自然な英語表現を作る
- 企業説明・業種分類から収益ドライバーを推定する
- 表記ゆれ・同義語を keyword に追加する
- 重要なマクロ・政策要因を合理的に補完する
- テーマが反応しやすい positive / negative event を定義する
- 収益ドライバー単位に分解する

# 品質基準

出力後、以下を満たしているか確認してください。

## テーマ説明

- テーマ名の言い換えだけになっていない
- 収益ドライバーが明確
- ニュース分類に使える語彙が含まれている
- 日本語・英語が整合している

## Revenue Drivers

- 5〜12個程度ある
- 各 driver が具体的
- driver_type が適切
- driver_embedding_text がニュース本文との意味類似に使える
- driver_keywords が具体的

## Catalysts / Keywords

- 抽象語が多すぎない
- ニュース見出しに出やすい語が多い
- 日本語・英語の表記ゆれが含まれる
- テーマ名だけに依存していない

## Events

- positive / negative events がテーマごとに妥当
- マクロや政策の方向性が逆になるテーマでは注意されている
  例: 金利上昇は銀行にはポジティブ、不動産にはネガティブ

## Entity Linking

- RIC が変更されていない
- 企業名が入力と整合している
- aliases が過剰に追加されていない

# 分割実行する場合

テーマ数が多い場合は、10〜20テーマずつ分割してください。

その場合、以下のように対象テーマを明示します。

```markdown
テーマ数が多いため、今回の対象は以下の theme_id のみです。

対象 theme_id:
- xxx
- yyy
- zzz

対象外のテーマは出力しないでください。
```

# 出力

解説文は不要です。

YAML のみを出力してください。
