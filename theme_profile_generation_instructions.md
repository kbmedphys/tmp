# テーマプロファイル作成指示書

## 0. 目的

この指示書は、既存の2つの入力データから、ニュース分類・テーマスコアリングに使う **テーマプロファイル YAML** を ChatGPT / Codex / LLM に作成させるためのものです。

目的は、単なるテーマ説明の整形ではなく、後続の処理で利用できる構造化プロファイルを作成することです。

```text
ニュース取得
  ↓
テーマプロファイル embedding
  ↓
ニュース多ラベル帰属
  ↓
Buzz / Tone / Breadth
  ↓
上位テーマ選択
```

作成するテーマプロファイルは、以下の用途で使います。

- lseg.data で取得したニュース本文との embedding 類似度計算
- ニュースのテーマへの多ラベル帰属
- キーワード一致による補正
- RIC・企業名による entity linking
- Buzz / Tone / Breadth の算出
- 上位テーマ選択

---

## 1. 入力データ

以下の2つのデータが与えられる前提です。

### 1.1 テーマバスケット一覧

各行は1つのテーマを表します。

| カラム | 内容 |
|---|---|
| `theme_id` | テーマID |
| `theme_name_en` | テーマ名 英語 |
| `theme_description_en` | テーマ説明 英語 |
| `theme_description_ja` | テーマ説明 日本語 |

### 1.2 個別企業リスト

各行は、あるテーマに含まれる1企業を表します。

| カラム | 内容 |
|---|---|
| `company_id` | 個別企業ID |
| `theme_id` | 所属テーマID |
| `weight` | テーマ内ウェイト |
| `ric` | Refinitiv RIC |
| `company_name_en` | 企業名 英語 |
| `company_description_en` | 企業説明 英語 |
| `gics_sector` | GICS Sector |
| `gics_industry` | GICS Industry |
| `trbc_industry` | TRBC Industry |
| `company_name_ja` | 企業名 日本語 |

---

## 2. 作成する成果物

各 `theme_id` ごとに、以下の形式の YAML を作成してください。

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

    revenue_drivers_en:
      - ""
    revenue_drivers_ja:
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

    profile_text_en: ""
    profile_text_ja: ""

    embedding_text: ""

    keyword_match_terms_en:
      - ""
    keyword_match_terms_ja:
      - ""

    entity_linking_terms:
      rics:
        - ""
      company_names_en:
        - ""
      company_names_ja:
        - ""

    top_constituents:
      - company_id: ""
        ric: ""
        company_name_en: ""
        company_name_ja: ""
        weight: 0.0
        company_description_en: ""
        gics_sector: ""
        gics_industry: ""
        trbc_industry: ""
```

---

## 3. 各項目の作成ルール

### 3.1 `theme_id`

入力テーマ一覧の `theme_id` をそのまま使ってください。

変更しないでください。

---

### 3.2 `theme_name_en`

入力テーマ一覧の `theme_name_en` をそのまま使ってください。

---

### 3.3 `theme_name_ja`

入力に日本語テーマ名がない場合は、`theme_description_ja` を参考に、自然な日本語テーマ名を作成してください。

例：

```yaml
theme_name_en: "Low PBR Reform"
theme_name_ja: "低PBR・資本効率改革"
```

ただし、過度に意訳しないでください。

---

### 3.4 `theme_type`

テーマの性質を以下から1つ選んでください。

```yaml
industry_theme
style_theme
policy_theme
macro_theme
event_theme
industry_policy_theme
macro_style_theme
```

判断基準は以下です。

| theme_type | 判断基準 | 例 |
|---|---|---|
| `industry_theme` | 業種・産業・技術・サプライチェーンで括られる | AI、半導体、医療機器、電力インフラ |
| `style_theme` | バリュエーション、財務特性、株主還元などで括られる | 低PBR、高配当、クオリティ、小型成長 |
| `policy_theme` | 政策、規制、政府支出、補助金が主ドライバー | 防衛、GX、国土強靭化、半導体補助金 |
| `macro_theme` | 金利、為替、資源価格、景気などが主ドライバー | 円安メリット、金利上昇、資源高 |
| `event_theme` | M&A、自社株買い、決算、承認などイベントが主軸 | 自社株買い、M&A候補 |
| `industry_policy_theme` | 産業テーマと政策テーマの両方 | 防衛、電力網、半導体国内生産 |
| `macro_style_theme` | マクロ環境とスタイル特性の両方 | 地銀・金利上昇メリット、インフレ耐性高配当 |

判断が曖昧な場合は、より実務上のニュース検出に有用な分類を選んでください。

---

### 3.5 `description_en` / `description_ja`

入力のテーマ説明をベースに、後続処理で使いやすいように補強してください。

#### 要件

- 3〜6文程度。
- テーマ名の言い換えだけにしない。
- 収益ドライバーを明示する。
- 構成銘柄の実態を反映する。
- ニュース本文に出やすい表現を含める。
- ただし、入力データにない事実を断定しない。

#### 悪い例

```yaml
description_ja: "AI関連企業に投資するテーマ。"
```

#### 良い例

```yaml
description_ja: >
  人工知能、生成AI、GPU、データセンター、クラウド基盤、半導体、
  AIソフトウェア、機械学習プラットフォームに関連する日本株テーマ。
  構成銘柄は、AI需要の拡大、データセンター投資、半導体投資、
  企業のDX投資、クラウド利用拡大などの影響を受ける。
```

---

### 3.6 `profile_summary_en` / `profile_summary_ja`

テーマの投資上の要点を短くまとめてください。

#### 要件

- 1〜2文。
- ポートフォリオマネージャーが見て、何に賭けているテーマか分かる内容にする。
- ニュース分類にも使えるよう、重要語を含める。

例：

```yaml
profile_summary_ja: >
  データセンター投資、AI半導体需要、クラウド基盤拡大に連動するテーマ。
  半導体、電子部品、ITサービス、電力関連企業を含む場合がある。
```

---

## 4. 収益ドライバー・カタリストの作成

### 4.1 `revenue_drivers_en` / `revenue_drivers_ja`

テーマの中長期的な収益源泉を列挙してください。

#### 目安

- 5〜12個。
- 企業説明、GICS、TRBC、テーマ説明から推定する。
- ニュースキーワードではなく、経済的ドライバーを書く。

例：

```yaml
revenue_drivers_ja:
  - データセンター向け設備投資の拡大
  - AI半導体・GPU需要の増加
  - クラウドサービス利用の拡大
  - 企業のDX投資
  - 高性能電子部品・半導体材料需要
```

---

### 4.2 `catalysts_en` / `catalysts_ja`

ニュースで出現しやすく、テーマの盛り上がり検出に使える語句を列挙してください。

#### 要件

- 10〜30個。
- 名詞句中心。
- ニュース見出しに出やすい語を優先。
- 英語・日本語の両方で作る。
- 同義語、表記ゆれを含める。
- テーマ名そのものだけに依存しない。

#### 例：低PBRテーマ

```yaml
catalysts_ja:
  - PBR1倍割れ
  - 資本効率
  - 資本コスト
  - 株価を意識した経営
  - 自社株買い
  - 増配
  - 株主還元
  - 政策保有株
  - 政策保有株縮減
  - アクティビスト
  - ROE改善
  - 東証要請
  - ガバナンス改革

catalysts_en:
  - price to book
  - PBR below one
  - capital efficiency
  - cost of capital
  - share buyback
  - dividend increase
  - shareholder return
  - cross shareholding
  - activist investor
  - governance reform
  - return on equity
  - Tokyo Stock Exchange reform
```

---

### 4.3 `positive_events_en` / `positive_events_ja`

テーマに対してポジティブと解釈されやすいニュースイベントを列挙してください。

#### 要件

- 5〜15個。
- テーマ固有の好材料を入れる。
- 汎用的すぎる語だけにしない。

例：

```yaml
positive_events_ja:
  - 上方修正
  - 受注増加
  - 受注残拡大
  - 設備投資計画の増額
  - 自社株買い発表
  - 増配
  - 補助金採択
  - 規制承認
```

---

### 4.4 `negative_events_en` / `negative_events_ja`

テーマに対してネガティブと解釈されやすいニュースイベントを列挙してください。

例：

```yaml
negative_events_ja:
  - 下方修正
  - 受注減少
  - 設備投資計画の延期
  - 輸出規制
  - 行政処分
  - 訴訟
  - 減配
  - 公募増資
  - コスト増
  - 需要減速
```

---

## 5. マクロ・政策ファクターの作成

### 5.1 `related_macro_factors_en` / `related_macro_factors_ja`

テーマが影響を受けやすいマクロ変数を列挙してください。

例：

```yaml
related_macro_factors_ja:
  - 国内金利
  - 長期金利
  - 為替レート
  - 米ドル円
  - 設備投資サイクル
  - 半導体サイクル
  - 原油価格
  - 電力価格
```

不要な場合は空リストでも構いません。

```yaml
related_macro_factors_ja: []
related_macro_factors_en: []
```

---

### 5.2 `related_policy_factors_en` / `related_policy_factors_ja`

政策・規制・補助金・政府支出に関係するテーマの場合に記載してください。

例：

```yaml
related_policy_factors_ja:
  - 防衛予算
  - 経済安全保障
  - 半導体補助金
  - GX政策
  - 電力系統投資
  - 東証による資本効率改善要請
```

---

## 6. 関連業種の集約

### 6.1 `related_industries`

個別企業リストから、そのテーマに含まれる企業の業種を集約してください。

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

### ルール

- 重複は除去する。
- 原則として、ウェイト上位または出現頻度の高い業種を優先する。
- 最大10個程度までに抑える。
- 入力にある表記をできるだけ維持する。
- 明らかな typo は修正してよいが、勝手に分類を作り直さない。

---

## 7. `profile_text_en` / `profile_text_ja`

embedding 用の中核テキストを作成してください。

### 7.1 `profile_text_en`

以下を自然な英文で統合してください。

- テーマ名
- テーマ説明
- 収益ドライバー
- カタリスト
- 主要構成銘柄の説明
- 関連業種
- 関連マクロ・政策要因

例：

```yaml
profile_text_en: >
  Theme: AI Infrastructure. This theme covers Japanese equities exposed to
  artificial intelligence infrastructure, semiconductors, data centers,
  cloud computing, electronic components, and AI-related capital expenditure.
  Key revenue drivers include data center investment, semiconductor equipment
  demand, AI server demand, enterprise digital transformation, and cloud adoption.
  Important catalysts include generative AI, GPU demand, data center capex,
  semiconductor cycle, and hyperscaler investment. Major constituents include
  companies involved in semiconductor equipment, electronic components,
  IT services, and industrial automation.
```

### 7.2 `profile_text_ja`

同じ内容を日本語で作成してください。

例：

```yaml
profile_text_ja: >
  このテーマは、人工知能インフラ、半導体、データセンター、
  クラウド基盤、電子部品、AI関連設備投資に関連する日本株を対象とする。
  主な収益ドライバーは、データセンター投資、半導体製造装置需要、
  AIサーバー需要、企業のDX投資、クラウド利用拡大である。
  重要なニュースカタリストは、生成AI、GPU需要、データセンター投資、
  半導体サイクル、ハイパースケーラーの設備投資である。
```

---

## 8. `embedding_text`

`embedding_text` は、ニュース本文との cosine similarity に直接使うテキストです。

### 8.1 作成ルール

`embedding_text` には以下を含めてください。

1. `theme_name_en`
2. `theme_name_ja`
3. `description_en`
4. `description_ja`
5. `profile_summary_en`
6. `profile_summary_ja`
7. `revenue_drivers_en`
8. `revenue_drivers_ja`
9. `catalysts_en`
10. `catalysts_ja`
11. 上位構成銘柄の企業説明

### 8.2 注意点

- 長すぎると embedding の焦点がぼやけるため、上位構成銘柄は原則として **累積ウェイト80%まで** または **上位30社まで**。
- 企業説明はそのまま全部貼るのではなく、必要に応じて短く要約する。
- 1つの企業だけが過度に支配しないようにする。
- ニュースに出やすい語句を適度に含める。
- 日本語と英語を両方含める。

---

## 9. `keyword_match_terms_en` / `keyword_match_terms_ja`

これは keyword score に使う語句です。

### 9.1 作成ルール

以下を統合して作ってください。

- catalysts
- positive_events
- negative_events
- revenue drivers の重要語
- テーマ名の表記ゆれ
- 業界用語
- 政策用語
- マクロ用語

### 9.2 目安

- 各言語 20〜50語。
- 短い名詞句を中心にする。
- 過度に一般的な語を避ける。

#### 避ける語の例

```text
成長
市場
企業
需要
投資
技術
```

単体では広すぎるため、使うなら以下のように具体化してください。

```text
AI需要
データセンター投資
半導体設備投資
電力需要
防衛予算
```

---

## 10. `entity_linking_terms`

個別企業リストから作成してください。

```yaml
entity_linking_terms:
  rics:
    - "6501.T"
    - "8035.T"
  company_names_en:
    - "Hitachi"
    - "Tokyo Electron"
  company_names_ja:
    - "日立製作所"
    - "東京エレクトロン"
```

### ルール

- 対象テーマに含まれる全企業を入れる。
- RIC は入力値をそのまま使う。
- 企業名は英語・日本語両方を入れる。
- 表記ゆれは、明らかに重要なものだけ追加してよい。
  - 例：`三菱UFJフィナンシャル・グループ`, `MUFG`
- ただし、入力にない略称を大量に作らない。

---

## 11. `top_constituents`

個別企業リストから作成してください。

### 11.1 選定ルール

- 原則としてウェイト降順。
- 上位30社まで、または累積ウェイト80%まで。
- テーマが少数銘柄なら全銘柄。
- `weight` は元データの値を使う。
- 欠損は空文字または `null` にする。

```yaml
top_constituents:
  - company_id: "C001"
    ric: "8035.T"
    company_name_en: "Tokyo Electron"
    company_name_ja: "東京エレクトロン"
    weight: 0.12
    company_description_en: >
      Tokyo Electron is a Japanese semiconductor production equipment company
      exposed to wafer fabrication equipment demand and semiconductor capital expenditure.
    gics_sector: "Information Technology"
    gics_industry: "Semiconductors & Semiconductor Equipment"
    trbc_industry: "Semiconductor Equipment"
```

---

## 12. 出力品質に関する制約

### 12.1 してはいけないこと

- 入力データにない銘柄を勝手に追加しない。
- RIC を変更しない。
- ウェイトを変更しない。
- テーマIDを変更しない。
- テーマ説明を過度に美化しない。
- 投資推奨文にしない。
- 「必ず上昇する」「恩恵を受ける」と断定しない。
- ニュース分類に使えない抽象語だけにしない。
- 一般語を keyword に大量投入しない。
- 企業説明から読み取れない事業を勝手に追加しない。

### 12.2 してよいこと

- テーマ説明をニュース分類に適した形に補強する。
- 英語説明から自然な日本語表現を作る。
- 日本語説明から自然な英語表現を作る。
- 企業説明と業種から revenue driver を推定する。
- 業種情報から関連産業を集約する。
- 重要な政策・マクロ要因を、テーマ説明と企業群から合理的に推定する。
- 明らかな同義語・表記ゆれを catalyst に追加する。

---

## 13. LLMに渡す実行プロンプト

以下をそのまま ChatGPT / Codex に渡してください。

````markdown
あなたは日本株テーマ投資、金融ニュース分類、NLP特徴量設計に詳しいクオンツリサーチャーです。

以下の2つの入力データをもとに、ニュース分類・テーマスコアリングに使うテーマプロファイル YAML を作成してください。

# 入力データ

1. テーマバスケット一覧

カラム:
- theme_id
- theme_name_en
- theme_description_en
- theme_description_ja

2. 個別企業リスト

カラム:
- company_id
- theme_id
- weight
- ric
- company_name_en
- company_description_en
- gics_sector
- gics_industry
- trbc_industry
- company_name_ja

# 目的

このテーマプロファイルは、以下の処理で使用します。

- lseg.data で取得したニュース本文との embedding 類似度計算
- ニュースのテーマへの多ラベル帰属
- キーワード一致による補正
- RIC・企業名による entity linking
- Buzz / Tone / Breadth の算出
- 上位テーマ選択

したがって、テーマ名の単なる翻訳や要約ではなく、ニュース本文に出現しやすい語句、収益ドライバー、ポジティブ/ネガティブイベント、構成銘柄の実態を反映したプロファイルにしてください。

# 出力形式

次の YAML 形式で出力してください。

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

    revenue_drivers_en:
      - ""
    revenue_drivers_ja:
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

    profile_text_en: ""
    profile_text_ja: ""

    embedding_text: ""

    keyword_match_terms_en:
      - ""
    keyword_match_terms_ja:
      - ""

    entity_linking_terms:
      rics:
        - ""
      company_names_en:
        - ""
      company_names_ja:
        - ""

    top_constituents:
      - company_id: ""
        ric: ""
        company_name_en: ""
        company_name_ja: ""
        weight: 0.0
        company_description_en: ""
        gics_sector: ""
        gics_industry: ""
        trbc_industry: ""
```

# 作成ルール

## theme_id
入力の theme_id をそのまま使ってください。変更しないでください。

## theme_name_en
入力の theme_name_en をそのまま使ってください。

## theme_name_ja
入力に日本語テーマ名がない場合、theme_description_ja から自然な日本語テーマ名を作成してください。

## theme_type
次から1つ選んでください。

- industry_theme
- style_theme
- policy_theme
- macro_theme
- event_theme
- industry_policy_theme
- macro_style_theme

判断基準:
- 業種、産業、技術、サプライチェーン中心なら industry_theme
- 低PBR、高配当、クオリティなど財務・バリュエーション中心なら style_theme
- 政策、規制、政府支出、補助金中心なら policy_theme
- 金利、為替、資源価格、景気中心なら macro_theme
- M&A、自社株買い、承認、決算などイベント中心なら event_theme
- 産業と政策の両方なら industry_policy_theme
- マクロとスタイルの両方なら macro_style_theme

## description_en / description_ja
入力テーマ説明をベースに、3〜6文で補強してください。
以下を含めてください。

- テーマの投資対象
- 主な収益ドライバー
- 構成銘柄の実態
- ニュースで検出すべき論点

ただし、入力データにない事実を断定しないでください。

## profile_summary_en / profile_summary_ja
1〜2文で、投資テーマとして何にエクスポージャーを取っているかを要約してください。

## revenue_drivers_en / revenue_drivers_ja
5〜12個作成してください。
ニュースキーワードではなく、テーマの中長期的な収益源泉を書いてください。

## catalysts_en / catalysts_ja
10〜30個作成してください。
ニュース見出し・本文に出やすい名詞句を中心にしてください。
テーマ名そのものだけに依存しないでください。
英語・日本語の表記ゆれを含めてください。

## positive_events_en / positive_events_ja
テーマに対してポジティブと解釈されやすいイベントを5〜15個作成してください。

## negative_events_en / negative_events_ja
テーマに対してネガティブと解釈されやすいイベントを5〜15個作成してください。

## related_macro_factors_en / related_macro_factors_ja
金利、為替、資源価格、景気、設備投資サイクルなど、テーマに関係するマクロ要因を列挙してください。
関係が薄い場合は空リストにしてください。

## related_policy_factors_en / related_policy_factors_ja
政策、規制、補助金、政府支出、制度改革などに関係する場合に列挙してください。
関係が薄い場合は空リストにしてください。

## related_industries
個別企業リストに含まれる GICS sector, GICS industry, TRBC industry をテーマごとに集約してください。
重複は除去してください。
ウェイトが大きい業種、または出現頻度が高い業種を優先してください。
最大10個程度に抑えてください。

## profile_text_en / profile_text_ja
embedding 用の中核テキストとして、テーマ名、説明、収益ドライバー、カタリスト、関連業種、主要構成銘柄の特徴を自然文で統合してください。

## embedding_text
ニュース本文との意味類似に直接使うテキストです。
日本語と英語を両方含めてください。
以下を含めてください。

- theme_name_en
- theme_name_ja
- description_en
- description_ja
- profile_summary_en
- profile_summary_ja
- revenue_drivers_en
- revenue_drivers_ja
- catalysts_en
- catalysts_ja
- 主要構成銘柄の企業説明

ただし、長くなりすぎないようにしてください。
構成銘柄は上位30社、または累積ウェイト80%までを目安にしてください。

## keyword_match_terms_en / keyword_match_terms_ja
ニュースのキーワード一致に使う語句です。
catalysts、positive_events、negative_events、revenue_drivers、業界用語、政策用語、マクロ用語を統合してください。
各言語20〜50語を目安にしてください。
「成長」「市場」「企業」「需要」「投資」など、単体では広すぎる語は避けてください。
使う場合は「AI需要」「データセンター投資」「半導体設備投資」のように具体化してください。

## entity_linking_terms
個別企業リストから作ってください。

- rics: 対象テーマの全RIC
- company_names_en: 対象テーマの全英語企業名
- company_names_ja: 対象テーマの全日本語企業名

RIC、企業名は入力値を尊重してください。
勝手に変更しないでください。

## top_constituents
個別企業リストから作ってください。
ウェイト降順で、上位30社または累積ウェイト80%までを含めてください。
少数銘柄テーマの場合は全銘柄を含めてください。

# 禁止事項

- 入力データにない銘柄を追加しない。
- RIC を変更しない。
- weight を変更しない。
- theme_id を変更しない。
- 企業説明にない事業を断定しない。
- テーマ説明を投資推奨文にしない。
- 「必ず上昇する」「恩恵を受ける」と断定しない。
- 抽象的すぎる keyword を大量に入れない。
- 出力に解説文を混ぜず、YAML のみを出力する。

# 品質基準

作成されたテーマプロファイルは、以下の用途で使える必要があります。

1. ニュース本文との embedding 類似度計算
2. 英語・日本語ニュースのキーワード一致
3. RIC・企業名による entity linking
4. テーマ内 Breadth の計算
5. Buzz / Tone / Breadth によるテーマスコアリング
6. ポートフォリオマネージャーが読んで理解できる説明性

では、入力データをもとに YAML を作成してください。
````

---

## 14. 分割実行する場合のプロンプト

テーマ数が多い場合、一括で作らせると品質が落ちます。推奨は **10〜20テーマずつ分割**です。

その場合は、以下を実行プロンプトに追加してください。

```markdown
テーマ数が多いため、今回の出力対象は以下の theme_id のみです。

対象 theme_id:
- xxx
- yyy
- zzz

対象外のテーマは出力しないでください。
```

---

## 15. 品質チェック用プロンプト

作成後に別の LLM / ChatGPT に品質チェックさせる場合は、以下を使ってください。

```markdown
以下のテーマプロファイル YAML をレビューしてください。

観点:
1. theme_id, RIC, weight が入力データから改変されていないか
2. theme_type は妥当か
3. description はテーマ名の言い換えに留まっていないか
4. revenue_drivers は経済的な収益源泉になっているか
5. catalysts はニュース本文に出やすい語句になっているか
6. keyword_match_terms に抽象語が多すぎないか
7. positive_events / negative_events はテーマごとに妥当か
8. related_macro_factors / related_policy_factors は過剰に入っていないか
9. embedding_text はニュース類似度計算に使える内容か
10. top_constituents はウェイト上位または累積80%ルールに沿っているか

問題があれば、修正案を YAML patch 形式で示してください。
```

---

## 16. 最終的な運用イメージ

この指示書で作成されたテーマプロファイルは、後続処理では次のように使います。

| プロファイル項目 | 用途 |
|---|---|
| `embedding_text` | ニュース本文との embedding 類似度 |
| `keyword_match_terms_ja/en` | キーワード一致スコア |
| `entity_linking_terms` | RIC・企業名一致 |
| `positive_events_ja/en` | Tone のポジティブ辞書 |
| `negative_events_ja/en` | Tone のネガティブ辞書 |
| `top_constituents` | Breadth 計算、説明、デバッグ |
| `related_industries` | セクター偏り確認 |
| `theme_type` | relevance score の重み変更 |

この形式にしておくと、日本株テーマバスケットに対して、**ニュースの意味類似、構成銘柄リンク、テーマ内広がり、ニュースイベント方向性**を一貫して扱えるようになります。
