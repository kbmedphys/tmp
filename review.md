# Phase A review: Narrative Momentum と MKT Multi-Asset Rotation

## 1. 対象文献と位置づけ

### 主文献

- ファイル: `docs/sources/ssrn-4912496.pdf`
- タイトル: Narrative Momentum
- 著者: Hojoon Lee, Xiaoxia Lou, Gideon Ozik, Ronnie Sadka
- 日付: 2025-07-23
- 位置づけ: 本プロジェクトの再現実装における主仕様。株式を対象に、経済ナラティブへのメディア注目が上昇したナラティブの mimicking portfolio が、その後も低下ナラティブをアウトパフォームするという "narrative momentum" を検証する。

### 補助文献

- ファイル: `docs/sources/MKT Multi Asset Rotation Documentation_web.pdf`
- タイトル: MKT Multi-Asset Rotation Documentation
- 日付: 2025-08-12
- 位置づけ: 主文献の考え方をマルチアセット・ローテーションへ拡張した実務的仕様の補足資料。主文献の再現実装ではなく、後続のマルチアセット実装時に参照する。

## 2. 研究目的と主要仮説

主文献の目的は、投資家が経済ナラティブへのメディア注目の変化に過小反応するかを、ナラティブ感応度の高い株式ポートフォリオを通じて検証すること。

中心仮説は以下。

- 経済ナラティブへの注目度が上昇した場合、そのナラティブに正の beta を持つ株式群は、その後も相対的に高いリターンを出す。
- 注目度が低下したナラティブの mimicking portfolio は相対的に低いリターンを出す。
- この効果は通常の株価モメンタムや factor momentum では説明しきれない。
- アナリスト予想誤差やナラティブ特性別の分析から、投資家またはアナリストの過小反応と整合する。

## 3. データ仕様

### メディアデータ

- データ提供元: MKT MediaStats, LLC
- 収集期間: 2012-2023
- 収集方法: point-in-time に日次で Web 記事を収集・解析。アーカイブベンダーデータではないため、削除記事や事後修正による back-fill bias を避ける意図がある。
- 規模: 約 23,000 の digital media sources、合計 13.27 million articles、平均 3,899 items/day、約 27,000 articles/week。
- WSJ と NYT はそれぞれ平均 164 items/day、82 items/day 程度だが、全体の 4% と 2% にすぎない。
- ナラティブ数: 主分析は 347 narratives。
- narrative library の由来: Reuters、IPTC、Bloomberg macroeconomic announcement news tags、analyst interest など。
- evergreen narratives: 主文献では JEL 分類と交差させた 53 narratives。MKT資料では 55 evergreen narratives が提示されており、文献間で数が異なるため Phase B で対象リストを固定する必要がある。

### 株式・ファクター・会計データ

- 株式リターン・特性: CRSP と Compustat。
- アナリスト予想: I/B/E/S summary history。
- Fama-French factors、12/30/49 industry returns: Kenneth R. French Data Library。
- factor momentum 用 factor returns: Hou, Xue, Zhang の q-factor website。
- 産業分類の一部: MSCI GICS 25 industry groups。

### 株式ユニバース

- 各月で CRSP firms の時価総額上位 3,000 社。
- 株価が 1 USD 超。
- narrative beta 推定には最低 26 週間のリターンが必要。
- baseline の narrative-mimicking portfolio は各ナラティブにつき高 beta 25 銘柄を long、低 beta 25 銘柄を short。

## 4. ナラティブ強度の定義

### 日次強度

各ナラティブについて、negative または positive media-coverage intensity を定義する。

- negative intensity: 当該ナラティブに該当し、かつ Loughran and McDonald (2011) ベースで negative sentiment と判定された記事数を、全体の議論量で割った比率。
- positive intensity: 同様に positive sentiment 記事で計算。
- 値域は [0, 1]。
- baseline は negative intensity を使用。

### 月次強度

- 月次強度は、その月の日次強度の平均。
- Table 1 は 347 narratives のうち、サンプル期間平均の月次 negative intensity が 0.01 を超える 180 narratives について、最大強度月を示す。
- 例: COVID-19 は 2020-03 に最大 0.51、Inflation は 2022-06 に最大 0.25。

### 週次強度

stock-level narrative beta の推定では週次強度を使う。

- 週 w の強度は、前週木曜日から当週水曜日までの日次強度の平均。
- 週次リターンも水曜終値から翌水曜終値で計算。
- 週次強度変化は `Intensity_n,w - Intensity_n,w-1`。

## 5. Stock-level narrative beta

各株式 i、ナラティブ n、週 w について、以下の週次回帰で beta を推定する。

```text
r_i,w = alpha_i + beta_m,i * r_m,w + beta_n,i * DeltaIntensity_n,w + e_i,w
```

- `r_i,w`: 株式 i の週次超過リターン。
- `r_m,w`: market excess return。Kenneth French の `MKT-RF`。
- `DeltaIntensity_n,w`: ナラティブ n の週次 negative intensity 変化。
- `beta_n,i`: 株式 i のナラティブ n に対する narrative beta。

推定ルール:

- 月 t の beta は、月 t-1 の最後の週で推定された beta を使う。
- rolling window は直近 52 週。
- 最低 26 週の利用可能リターンが必要。
- beta 推定期間と月末の間に少なくとも 1 日の separation を置く。
- 2012-12 と 2013-01 は 52 週未満のデータで例外的に推定される。

解釈:

- positive beta: negative narrative news が増えたときに相対的に上がる銘柄。
- negative beta: negative narrative news が増えたときに相対的に下がる銘柄。
- この方法は、企業が直接メディアに言及されているかではなく、ナラティブ強度変化へのリターン感応度で exposure を測る点が重要。

## 6. Narrative-mimicking portfolio

各ナラティブ n について、月次で long-short mimicking portfolio を構築する。

- formation timing: 月 t の初めに、月 t-1 末までに利用可能な beta を使う。
- long leg: ナラティブ n の beta が最も高い 25 銘柄。
- short leg: ナラティブ n の beta が最も低い 25 銘柄。
- baseline は各 leg 内を value-weighted。
- portfolio は月次でリバランス。
- 対象は時価総額上位 3,000 社、株価 1 USD 超。
- narrative-mimicking portfolio returns は 2013-01 から利用可能。

再現時の注意:

- 月 t の銘柄選択に月 t のリターンや月 t 末の beta を使わない。
- beta 推定に使う週次強度・週次リターンは、formation date で実際に利用可能な情報に限定する。
- 企業メディア言及ベースの代替ポートフォリオは robustness test であり、baseline ではない。

## 7. Narrative momentum strategy

### ナラティブ強度変化シグナル

月 t の初めに、各ナラティブの J-month intensity change を計算する。

```text
Signal_n,t(J) =
  average monthly intensity over [t-J, t-1]
  - average monthly intensity over [t-2J, t-J-1]
```

例: `J=6` の場合、月 t の初めに `[t-6, t-1]` の平均強度から `[t-12, t-7]` の平均強度を引く。

重要な時点整合:

- signal 計算時には月 t-1 の最終日を除外する。
- 月 t の初めに決定した signal は、月 t 以降の保有リターンにのみ使う。
- `t` までの情報で特徴量を作り、`t+1` 以降のリターン予測に使うという本プロジェクトの制約に合わせる場合、formation close と適用開始日を明示し、同一日・同一月内の未来情報混入を避ける。

### ナラティブのソート

J は 1, 3, 6, 9, 12 か月。

- rising narratives: intensity change が最大の top 10 narratives。
- declining narratives: intensity change が最小の bottom 10 narratives。
- middle: その他。

### 保有期間とラダー

K は 1, 3, 6, 9 か月。

- top 10 の narrative-mimicking portfolios を equal-weight して long。
- bottom 10 の narrative-mimicking portfolios を equal-weight して short。
- long-short narrative spread portfolio は、gross leverage を 2 に保つため returns を 2 で割る。
- K が 1 か月超の場合は Jegadeesh and Titman (1993) 型の laddered overlapping portfolio を使う。
- 例: `K=6` では、過去 6 か月に形成された 6 本のサブポートフォリオの当月リターンを equal-weight する。
- 保有期間中、選ばれたナラティブ集合は固定するが、各 narrative-mimicking portfolio の構成銘柄は月次でリバランスされる。

## 8. 評価指標

主文献の評価は以下。

- 年率リターン。
- monthly returns に基づく t-statistics。
- Fama-French 6-factor alpha。
- factor momentum control では FF6 に 1-month factor momentum と 12-month factor momentum を追加。
- cumulative returns。
- event-time cumulative returns。
- アナリスト予想誤差。
- Fama-MacBeth cross-sectional regression。
- tag decomposition と industry decomposition。

Factor momentum の構築:

- Hou et al. (2020) の 122 factors を使う。
- 各月末に factor 自身の過去 1 か月または 12 か月リターンで decile sort。
- top decile long、bottom decile short。
- 月次リバランス。

## 9. 主結果

### Baseline narrative momentum

Table 3 の主要結果:

- `J=6`, `K=6`:
  - rising narratives return: 13.30% 年率、t-stat 2.35。
  - declining narratives return: -3.54% 年率、t-stat -0.71。
  - long-short spread return: 8.42% 年率、t-stat 2.79。
  - FF6 alpha: 7.30% 年率、t-stat 2.42。
- `J=6` の `K=1, 3, 6, 9` はいずれも spread return が 7% から 9% 程度で有意。
- `J=12`, `K=1` も spread return 8.84%、FF6 alpha 9.16% と強い。
- `J=1` は弱く、短期の一時的変化よりも数か月単位の注目変化が重要。

解釈:

- 注目が増加したナラティブの mimicking portfolio が、その後も注目低下ナラティブをアウトパフォームする。
- long leg の寄与が大きく、declining leg は符号は概ね負だが有意性は弱い。

### Price momentum control

Table 4 と Table 5 は、narrative portfolio 自身の過去リターンで price momentum を制御しても narrative intensity momentum が残ることを示す。

- `M=6`, `J=6`, `K=6` の double sort:
  - portfolio-level momentum control の average spread return は 4.20%、t-stat 2.22、FF6 alpha 4.04%、t-stat 2.12。
  - stock-level momentum control の average spread return は 4.25%、t-stat 2.41、FF6 alpha 3.86%、t-stat 2.16。
- narrative portfolio の過去リターンそのものには強い price momentum は確認されない。

### Factor momentum control

Table 6 は FF6 に factor momentum を追加しても効果が残ることを示す。

- `J=6`, `K=6`: return 8.42%、t-stat 2.79、alpha 7.03%、t-stat 2.29。
- narrative momentum は factor momentum だけでは説明されない。

## 10. 過小反応仮説の検証

### アナリスト予想誤差

Table 7 は、`J=6` でソートした top 10、bottom 10、spread について、formation 後 1 から 12 か月の earnings forecast error を計算する。

定義:

```text
(ActualEPS_t-1+k+tau - ForecastedEPS_t-1) / Price_t-1
```

- `ForecastedEPS_t-1`: 月 t-1 末時点で記録された、同じ fiscal year-end に対する median analyst forecast。
- `ActualEPS`: 月 t-1+k 以後に発表された最初の annual EPS。
- winsorize: 1% と 99%。
- stock-level forecast errors は value-weight で narrative portfolio へ集計し、その後 top 10 と bottom 10 内で equal-weight。

主結果:

- spread の forecast error は概ね formation 後 9 か月程度まで正。
- top 10 側の予想誤差が正で有意になりやすく、効果は rising narratives 側で強い。
- アナリストが rising narratives に感応する銘柄の将来 earnings を過小評価している可能性と整合する。

### 情報の連続性

Table 8 は information discreteness を検証する。

- smoothness = `abs(average weekly intensity changes) / std(weekly intensity changes)`。
- J=1,3,6,9,12 に対して 9, 26, 52, 78, 104 週の過去 intensity changes を使う。
- above-median smoothness は、少量で連続的に届く情報を表す。
- `J=6`, `K=6` では below-median smoothness の return 4.59% に対し、above-median smoothness は 6.51%。
- `J=9`, `K=6` では 4.82% に対し 7.93%。
- frog-in-the-pan 仮説、つまり連続的な小さい情報ほど過小反応されやすいという説明と整合する。

### Quarter-life

Table 9 は narrative intensity の持続性を検証する。

- 各ナラティブに AR(12) を当て、unit impulse response が 0.25 未満に減衰するまでの月数を quarter-life とする。
- 平均 5.10、中央値 3、10th percentile 1、90th percentile 12。
- above-median quarter-life narratives の方が narrative spread return が高い。
- `J=6`, `K=6`: below-median 4.13%、above-median 7.01%。
- 持続的なナラティブほど過小反応が強い可能性がある。

### Prior intensity level

Table 10 は、月 t-7 時点の過去 6 か月平均強度でナラティブを分割する。

- `J=6`, `K=6`: low prior intensity は 2.27%、high prior intensity は 7.80%。
- すでに長く注目されているナラティブでは、追加的な注目変化が見落とされやすいという解釈。

## 11. 追加分析と robustness

### Narrative tag decomposition

- 347 narratives を 14 narrative tags に分類。
- `J=6`, `K=6` の spread return 8.42% の内訳:
  - excess tag return: 6.03%、t-stat 2.25。
  - average tag return: 2.38%、t-stat 2.63。
- 大部分は tag 内の個別ナラティブ効果だが、tag-level momentum も存在する。

### Industry decomposition

- Fama-French の 12/30/49 industries で stock returns を industry return と excess industry return に分解。
- 12 industries での `J=6`, `K=6` spread:
  - excess industry return: 7.39%、t-stat 2.50。
  - average industry return: 1.02%、t-stat 2.08。
- 主効果は industry 間ではなく intra-industry の寄与が大きい。

### Fama-MacBeth regressions

- 各株式について、top 10 rising narratives と bottom 10 declining narratives に対する `6-month intensity change * narrative beta` を合計し、6 か月平均を説明変数にする。
- 被説明変数は将来 1 か月リターン。
- controls: log(B/M)、log(market cap)、過去 1 か月・12 か月リターン、investment、profitability。
- OLS と market-cap weighted WLS を実施。
- OLS column (3): Top 10 rising coefficient 0.05、t-stat 3.08。
- WLS column (6): Top 10 rising coefficient 0.07、t-stat 2.39。Bottom 10 declining coefficient 0.07、t-stat 1.96。
- stock-level exposure でも narrative signal が将来リターンを説明する。

### Media reservoirs

メディア記事は以下の reservoirs に分類される。

- General
- Corporate
- FX
- Country Equity
- Aggregate: 上記の平均。collection ramp-up 期間では利用不可 reservoir を missing として扱う。

Table 14 は beta 推定に使う reservoir と attention signal に使う reservoir の 5 x 5 組み合わせを比較する。

- `J=6`, `K=6` の Aggregate/Aggregate は 8.42%。
- 25 組み合わせ平均は `J=6`, `K=6` で 3.85%、t-stat 2.08。
- `J=12`, `K=1` では平均 5.17%、t-stat 2.35。
- FX reservoir が相対的に強い。

### Different narrative sets

Table 15 は narrative selection bias を検証する。

- 347 MKT narratives
- 53 evergreen narratives
- 294 non-evergreen narratives
- Bybee et al. (2024) ベースの 137 economics/politics business news narratives

主結果:

- evergreen と non-evergreen でも positive return が確認される。
- Bybee ベース narratives は全体に弱いが、`J=12`, `K=1` の momentum-neutral は 2.27%、t-stat 2.43。
- 新規 narrative 導入前後 3 か月を落としても主結果は大きく変わらないとされる。

### Other robustness

Table 16 の baseline は `J=6`, `K=6`。

- Baseline: return 8.42%、alpha 7.30%。
- narrative weights を intensity level や intensity difference で変えても return は 8% 台。
- positive intensity でも効果は残るが、negative intensity よりやや弱い。
- positive + negative の overall intensity でも return 7.71%、alpha 6.59%。
- beta t-stat で銘柄選択すると return は弱いが alpha は一部有意。
- firm-level media coverage で long-only portfolio を作ると弱く、beta による directionality の重要性を示す。
- top/bottom 5 narratives は return 9.44%、top/bottom 20 は 5.17%。
- 682 sub-narratives、subperiod、PCA first 50 components、skip one month、equal-weight stock legs でも方向性は概ね維持。

## 12. MKT Multi-Asset Rotation 資料の整理

MKT資料は、主文献の narrative momentum を株式以外の資産クラスへ拡張する設計資料である。大別して以下の 2 系統がある。

- Direct Media Coverage: 資産そのものをナラティブとして扱い、当該資産の明示的メディア coverage から attention と sentiment を作る。
- Narrative-Beta Exposure: trending evergreen narratives への beta exposure を使い、複数ナラティブを同時に追跡する mimicking portfolio を作る。

### 資産クラス別仕様

#### Safe Asset Rotation

- Universe: 3 safe assets。MSCI excess-return forward indexes on USD、Gold、US Treasury。
- Signal: short-term media sentiment。
- Selection: sentiment signal 上位 2 assets を equal-weight。

#### Individual Stock Rotation

- Universe: MKT large cap universe と MSCI USA universe の交差。
- Signals:
  - Narrative-beta exposure: stock-narrative betas と trending narrative attention shocks を組み合わせた long-term stock expected return。
  - Conditional media sentiment: stock-specific conditional media sentiment。price momentum と log market cap に直交化。
- Short leg から除外: rolling 30 calendar days の maximum borrow cost が 1.5% 超の銘柄。
- 各 signal で top 20 long、bottom 20 short を equal-weight。
- 2 signal portfolios を equal-weight し、重複 position を netting/re-weighting。
- position weight cap: 3%。
- long/short gross exposures を rescale して cash neutral。

#### US Sector Rotation

- Universe: 10 MSCI sectors。Real Estate は size/liquidity 理由で除外。
- Signals:
  - Narrative-beta exposure top-down。
  - Conditional media sentiment bottom-up。stock-level conditional media sentiment を market cap で value-weight。
- Narrative-beta exposure: top/bottom 4 sectors を sector aggregate market cap で value-weight、6-month ladder。
- Conditional media sentiment: top/bottom 4 sectors を value-weight、3-month ladder。
- 2 signal portfolios を equal-weight。
- weight cap: 30%。
- cash neutral に rescale。

#### MSCI Factor Rotation

- Universe: 7 MSCI factors。Enhanced Value、Equal Weighting、Growth Target、High Dividend Yield、Minimum Volatility、Momentum、Quality。
- Signal: Narrative-beta exposure。factor-narrative betas と trending narrative attention shocks から long-term factor expected return を推定し、factor price momentum に直交化。
- Selection: top/bottom 3 factors を equal-weight、12-month ladder。
- weight cap: 40%。
- cash neutral に rescale。

#### Commodity Rotation

- Universe: 14 commodities。Aluminium、Cattle、Copper、Corn、Gold、Lean Hog、Natural Gas、Nickel、Oil、Silver、Soybean、Sugar、Wheat、Zinc。
- Signals:
  - Attention: medium-term positive attention growth minus short-term negative attention growth。12-month price returns に直交化。positive predictor。
  - Sentiment: long-term sentiment change。12-month price returns に直交化。positive predictor。
  - Reversal: 12-month price returns。negative predictor。
- Attention と Sentiment は top 5 long、bottom 5 short。
- Reversal は bottom 5 long、top 5 short。
- 3 signal portfolios を equal-weight。
- weight caps: Cattle、Lean Hog、Silver、Sugar、Wheat は 10%、その他は 30%。
- cash neutral に rescale。

#### Currency Rotation

- Universe: developed market currencies 9 通貨 AUD、CAD、CHF、EUR、GBP、JPY、NOK、NZD、SEK と emerging market currencies 2 通貨 MXN、ZAR。各通貨は USD 建て。
- Signals:
  - Long-term expected return: currency-narrative betas と trending narrative attention shocks の組み合わせ。
  - Media sentiment tone: monetary policy coverage 由来の media signal。
- 各 signal で top/bottom 4 currencies を equal-weight。
- 2 signal portfolios を equal-weight。
- weight caps: MXN 9%、ZAR 18%、その他 27%。
- cash neutral に rescale。

### Multi-Asset allocation

MKT資料の selection section では以下の配分。

- Safe Asset rotation: 20%
- Commodity rotation: 8%
- Individual Stocks、US Sectors、MSCI Factors、Currencies: 各 18%

この配分は合計 100% になる。一方、本文の empirical evaluation には Safe Assets 18% と読める記述があるため、Phase B でマルチアセット実装に進む場合は 20% を暫定採用しつつ、原資料の記述揺れとして明示する。

### MKT資料の時点整合

- Signal construction: 対象 asset class の business month end の 3 business days before。
- Table B2 の予測回帰では、signals は rank-transform され `[-0.5, 0.5]` に収められる。
- future returns は next month asset returns。
- 後続実装では、3 business days before business month end で signal を確定し、翌月または次の有効リバランス期間に適用する必要がある。

### MKT資料の 55 evergreen narratives

MKT資料 Appendix A の Table A2 は以下の 55 topics を evergreen narratives として示す。

- Macroeconomics: Budget Deficit、GDP Growth、Federal Reserve、Inflation、Interest Rates、Manufacturing、Money Supply、Recession。
- Asset Class Investing: Bond Investing、Commodity Investing、Currency Investing、Derivatives Investing、ETF Investing、Money Market Investing、Retail Investing、Stock Market Investing。
- Investment Strategies: Carry Investing、ESG Investing、Momentum Investing、Passive Investing、Quality Investing、Size Factor Investing、Smart Beta Investing、Value Investing。
- Corporate & Industry Topics: Corporate Bankruptcies、Corporate Capex、Corporate Profitability、Corporate Financing、Corporate Governance、Corporate Competition、Fund Management Industry、Investment Banking。
- Social Issues & Public Policy: Civil Unrest、Immigration、Natural Disasters、Political Elections、Privacy Concerns、Public Health、Racism、Social Inequality、The Environment、Violent Crime。
- Global Affairs & Trade: Globalization、International Conflicts、International Organizations、Trade Tensions。
- Consumer & Household Economics: Consumer Credit、Employment Concerns、Healthcare、Housing Market、Personal Consumption、Personal Finances。
- Market Psychology & Risks: Investor Sentiment、Liquidity Concerns、Risk and Uncertainty。

### MKT資料の実証結果

Table B1 の sample period は 2013-03 から 2025-03。

- Safe Assets: mean 4.84%、t-Mean 3.04、vol 6.16%、SR 0.79、drawdown -10.21%。
- Stocks: mean 9.20%、t-Mean 3.47、vol 9.25%、SR 0.99、drawdown -13.32%。
- Sectors: mean 6.36%、t-Mean 3.08、vol 6.64%、SR 0.96、drawdown -10.72%。
- Factors: mean 4.46%、t-Mean 3.40、vol 4.59%、SR 0.97、drawdown -6.50%。
- Commodities: mean 11.47%、t-Mean 2.98、vol 13.35%、SR 0.86、drawdown -22.93%。
- Currencies: mean 2.73%、t-Mean 2.71、vol 4.14%、SR 0.66、drawdown -6.14%。
- Multi-Asset: mean 5.98%、t-Mean 6.21、vol 3.18%、SR 1.88、drawdown -5.02%。

Table B2 の predictive regressions:

- cross-sectional regression of next month asset returns onto signals。
- slopes と R2 を時系列平均し、slopes の t-stat を評価。
- Stocks の long-term expected return slope は 5.79%、t-stat 1.97。
- Sectors の long-term expected return slope は 9.85%、t-stat 2.25。
- Factors の long-term expected return slope は 7.74%、t-stat 3.19。
- Currencies の media coverage slope は 4.38%、t-stat 2.11。

## 13. Phase B 再現実装に向けた仕様メモ

### 優先して再現する baseline

最初の再現対象は、主文献 Table 3 の `J=6`, `K=6` baseline が妥当。

理由:

- 論文中の代表的な結果。
- signal、holding、alpha、robustness の中心。
- MKT資料の Narrative-Beta Exposure とも対応しやすい。

### 必須入力データ

再現には以下が必要。

- 日次 article-level または narrative-level intensity data。
- negative intensity の日次系列。
- 株式日次または週次価格、月次リターン、時価総額、株価。
- risk-free rate と market factor。
- Fama-French 6 factors。
- 必要に応じて Compustat、I/B/E/S、industry classification、q-factor data。

注意:

- MKT MediaStats の article/narrative data は proprietary の可能性が高い。データがない場合、厳密再現ではなく代替データによる構造再現に切り替える必要がある。
- その場合も、時点整合、rolling beta、monthly formation、laddered holding の仕様は維持する。

### 厳守すべき時点整合

- 日次メディアデータは publication date で point-in-time に扱う。
- 月 t の signal は、月 t のリターン開始前に利用可能な情報だけで作る。
- intensity change では月 t-1 の最終日を除外するという論文仕様を反映する。
- beta 推定では月末との separation を最低 1 日確保する。
- 月 t に形成した portfolio return は月 t 以降だけを使う。
- K か月保有では、各 formation cohort の return を重ねるが、cohort ごとの formation 情報は固定する。
- 週次リバランスや日次適用に拡張する場合は、「週末または signal 確定時点で決めた weight を翌営業日から適用」と明示し、同日終値を使った look-ahead を避ける。

### 実装上の推奨データフロー

1. 日次 narrative intensity を作成する。
2. 週次 intensity と weekly DeltaIntensity を作成する。
3. 水曜終値ベースの週次 stock excess returns を作成する。
4. rolling 52-week regression で stock-narrative beta を推定する。
5. 月 t の formation 用 beta snapshot を月 t-1 末時点で作る。
6. 各 narrative の high-beta 25 / low-beta 25 stocks で monthly mimicking returns を作る。
7. 月次 negative intensity から J-month intensity change を作る。
8. 月 t の top 10 / bottom 10 narratives を選ぶ。
9. K-month laddered strategy returns を計算する。
10. FF6 alpha、t-stat、cumulative returns を計算する。

### Acceptance criteria for Phase B

- `J=6`, `K=6` の signal construction が論文式と一致している。
- month t の portfolio に month t 末以降の情報が混入していない。
- narrative-mimicking portfolio と narrative momentum portfolio の 2 段階構造が分離されている。
- long/short spread の leverage scaling が明示されている。
- Table 3 の 20 combinations を再計算できる設計になっている。
- データ制約で完全再現できない場合は、代替データ・非再現部分・比較不能部分を notebook 内で明示する。

## 14. 未解決事項

- MKT MediaStats の 347 narrative intensity data がプロジェクト内に存在しない。
- CRSP、Compustat、I/B/E/S のアクセス可否が未確認。
- evergreen narratives は主文献 53、MKT資料 55 と差があるため、使用リストを固定する必要がある。
- MKT資料の Multi-Asset allocation は Safe Assets 20% と 18% の記述揺れがある。合計 100% になる 20% を暫定優先候補とする。
- Fama-French 6-factor alpha の具体的な factor set と t-stat 標準誤差仕様は、Phase B で使用データに合わせて明記する必要がある。

## 15. Phase A の範囲確認

この review は文献レビューと再現実装仕様の整理であり、以下は行っていない。

- `.ipynb` の作成。
- バックテスト実装。
- データ取得スクリプト作成。
- 原本 PDF の変更。
- 既存ファイルの削除・上書き。
