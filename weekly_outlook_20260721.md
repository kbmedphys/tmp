# 週次セクターGamma見通し — 2026年7月第4週

**更新日時:** 2026-07-21 00:02 JST（2026-07-20 11:02 ET）  
**観測済み期間:** 2026-07-20米国市場の午前まで  
**主な見通し対象:** 2026-07-21〜2026-07-24  
**対象:** S&P 500 11セクターETF

> **重要:** 本版は7月20日の米国市場が取引中の時点で取得した価格・オプションチェーンによる日中スナップショットであり、米国引け後の確定版ではない。価格、GEX、Gamma Flip、Wall、IV、Vanna/Charmは引けまでに変化しうる。以下はモデルに基づく調査資料であり、投資助言ではない。

## 1. データ時点と読み方

### 確認できた事実

- 11 ETFすべてのオプションチェーンを取得し、Notebookは上から例外なく完走した。
- 前週検証は2026-07-10終値から7月17日終値までの配当調整済みETF価格で計算した。
- 今週の価格・オプション指標は2026-07-20 11:02 ET前後の日中値である。
- IVレンジは各ETFのATM IVから計算した**7日、1標準偏差**の予想変動であり、7月24日までの残存日数だけに縮尺したレンジではない。

### モデル判断のルール

- 総合スコアは価格モメンタム、Gamma、オプション需要、リスク制御を統合する。
- IV調整スコアは高IVや主要Gamma水準のレンジ内包を反映して順位を補正する。
- Hard RuleでOverweight不可となったセクターには、総合順位が高くても積極配分を行わない。
- 提案配分は既存ルールを変更せず、Benchmark WeightにActive Weightを加えたもの。合計は100%、Active Weight合計は0%である。

## 2. 先週の結果：7月10日終値から7月17日終値

### ポートフォリオ実績

| 指標 | 実績 |
|---|---:|
| 前回提案ポートフォリオ | **-1.836%** |
| ベンチマーク | **-1.759%** |
| 超過収益 | **-0.076%（-7.63bp）** |

前回提案はベンチマークを7.63bp下回った。大きな敗因はXLEのUnderweightで、XLFのOverweightとXLCのUnderweightによる利益を打ち消した。比較用のセクター指数でも、前週はEnergyが最上位、TechnologyとCommunication Servicesが弱かったことを[LPLの前週レビュー](https://www.lpl.com/research/blog/weekly-market-performance-july-17-2026.html)で確認できる。ただし、本表の実績値はニュース記事ではなくETFの配当調整済み終値から算出している。

| セクター | 前回判断 | 実現騰落率 | Active Weight | Active寄与 | 評価 |
|---|---:|---:|---:|---:|---|
| XLF 金融 | Overweight | +0.987% | +2.00% | **+1.97bp** | 銀行株の底堅さを捉え、提案に寄与した。 |
| XLC コミュニケーション | Underweight | -0.887% | -1.17% | **+1.03bp** | 下落を抑制し、方向は適切だった。 |
| XLP 生活必需品 | Underweight | +1.272% | -0.78% | **-0.99bp** | ディフェンシブ回帰に逆行した。 |
| XLY 一般消費財 | Overweight | -1.535% | +1.50% | **-2.30bp** | リスクオフと成長株調整に対して過大配分だった。 |
| XLE エネルギー | Underweight | +4.720% | -1.56% | **-7.34bp** | Iran・Hormuzを巡る原油上昇への反応が遅れ、最大のマイナス寄与となった。 |

その他のActive Weightは実質ゼロだった。XLREは+2.182%、XLVは+0.155%と上昇した一方、XLIは-1.380%、XLKは-5.485%だった。

### XLKの警戒シナリオ検証

前回のXLKはNeutralだったが、Gamma Flip 180.98割れを下方向のレジーム転換リスクとして監視していた。実際には7月10日の185.78から7月17日の175.59へ**-5.49%**下落し、Gamma Flipを割り、前回7日IVレンジ下限175.86もわずかに下回った。

これは警戒水準自体の有効性を示す一方、前回配分がNeutralだったため超過収益としては獲得できなかった。今週は「警告の記載」だけで終えず、XLKを明示的なUnderweightへ変更している。

### 先週からのモデル上の教訓

- **有効だった点:** XLFとXLCの相対方向、XLKのGamma Flip割れ警戒。
- **改善が必要な点:** 地政学ショックによる原油の非線形上昇は、遅行的な価格モメンタムだけでは捕捉しにくい。
- **今週への反映:** XLEは現在、正のNet GEXかつGamma Flip上へ移行したためOverweight。ただし高IV・High Charmであり、原油反落時の巻き戻しも同時に管理する。

## 3. 今週の総論

### 確認できた事実

7月20日午前の米国市場はAI・半導体株の反発でNasdaq優位だった一方、原油高と長期金利上昇が続いている。[APの当日市場報道](https://apnews.com/article/stocks-market-ai-oil-iran-war-15939a01f378bcec5eec2868e8100ca9)では、10:15 ET時点でS&P 500が約+0.3%、Nasdaqが約+0.5%、Dowが約-0.2%、Brentが約88.17ドル、米10年債利回りが約4.58%と報じられた。NvidiaとAMDの反発はXLK、今週のAlphabet決算はXLC、Tesla決算はXLY、Intel決算はXLKの主要カタリストになる。

経済指標は比較的少なく、7月23日の新規失業保険申請件数、7月24日の速報PMIと新築住宅販売が中心である。[今週の経済カレンダー](https://www.kiplinger.com/investing/economy/this-weeks-economic-calendar)によれば、翌週7月28〜29日のFOMCを控える。FRBの[ブラックアウト期間規則](https://www.federalreserve.gov/monetarypolicy/files/fomc-blackout-period-calendar.pdf)からみて、今週はFRB高官発言より企業決算・原油・金利・経済統計が価格形成を主導しやすい、というのが本レポートの推論である。

### モデルの結論

今週は**XLF・XLV・XLEをOverweight、XLI・XLK・XLYをUnderweight**とする。XLREは総合3位だがHard RuleでOverweight不可、XLPもOverweight可能ではあるものの負のGammaかつGamma Flip下であるためNeutralを維持する。

中心的な組み合わせは次の通り。

- **守りながら取る:** XLF、XLV。正のNet GEXと高順位を優先する。
- **地政学ヘッジ:** XLE。原油高の恩恵を取り込むが、IVが高くGamma Flip 56.35を割れば縮小候補。
- **イベント前のリスク削減:** XLK、XLY。AI反発を追いかけず、決算通過とGamma水準回復を確認する。
- **景気循環の選別:** XLIをUnderweight。総合9位、負のNet GEXで、決算・PMIに対する値幅拡大を警戒する。

## 4. 更新配分

| 順位 | ETF | セクター | 総合 / IV調整スコア | Benchmark | Active | Proposed | 判断 |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | XLF | 金融 | 1.575 / 1.475 | 12.59% | **+2.00%** | **14.59%** | Overweight |
| 2 | XLV | ヘルスケア | 1.500 / 1.550 | 9.49% | **+1.50%** | **10.99%** | Overweight |
| 3 | XLRE | 不動産 | 1.275 / 1.175 | 2.00% | 0.00% | 2.00% | Neutral / Hard Rule |
| 4 | XLE | エネルギー | 1.225 / 0.925 | 4.00% | **+1.00%** | **5.00%** | Overweight |
| 5 | XLU | 公益 | 0.600 / 0.250 | 2.50% | 0.00% | 2.50% | Neutral / Hard Rule |
| 6 | XLP | 生活必需品 | 0.275 / 0.175 | 5.29% | 0.00% | 5.29% | Neutral |
| 7 | XLC | コミュニケーション | -0.525 / -0.525 | 10.29% | 0.00% | 10.29% | Neutral / Hard Rule |
| 8 | XLB | 素材 | -1.075 / -1.025 | 2.10% | 0.00% | 2.10% | Neutral / Hard Rule |
| 9 | XLI | 資本財 | -1.125 / -1.225 | 8.99% | **-1.00%** | **7.99%** | Underweight |
| 10 | XLK | 情報技術 | -1.325 / -1.625 | 32.87% | **-1.50%** | **31.37%** | Underweight |
| 11 | XLY | 一般消費財 | -1.575 / -1.575 | 9.89% | **-2.00%** | **7.89%** | Underweight |

**整合性:** Proposed Weight合計100.00%、Active Weight合計0.00%。総合順位とIV調整順位が異なるのはXLVが1位、XLFが2位、XLKが11位、XLYが10位となる点である。

## 5. 全11セクターの読み

| ETF | Spot | Net GEX | Gamma Flip | Call / Put Wall | 7日1σ IVレンジ | Vanna / Charm | モデル解釈 |
|---|---:|---:|---:|---:|---:|---|---|
| XLF | 56.12 | +137.82m | 53.92 | 56 / 50 | 54.84–57.39 | 通常 / **High** | 正のGammaと首位スコア。ただしCall Wall 56付近で上値が抑えられやすく、決算後のCharmに注意。 |
| XLV | 160.28 | +45.65m | 151.74 | 165 / 155 | 156.19–164.37 | **High / High** | IV調整後首位。正のGammaで相対的に安定だが、決算後IV低下時のVanna/Charmフローは大きい。 |
| XLRE | 45.32 | +1.69m | 41.66 | 46 / 35 | 43.80–46.84 | 通常 / 通常 | 総合3位でもHard RuleによりNeutral。金利低下なら46を試しやすいが、金利上昇では追わない。 |
| XLE | 58.08 | +44.33m | 56.35 | 60 / 55 | 55.76–60.39 | 通常 / **High** | 原油高、正のGamma、Flip上を評価。60は上値抵抗。高IVとCharmのため56.35割れで守勢へ。 |
| XLU | 45.35 | +6.40m | 45.05 | 45 / 45 | 44.22–46.47 | 通常 / **High** | Spot、Flip、両Wallが密集。方向感より45近辺のピン留めと、金利変化による離脱を監視。 |
| XLP | 85.07 | -26.11m | 88.52 | 85 / 78 | 83.17–86.97 | 通常 / **High** | 前週は強かったが負のGamma・Flip下。Hard Rule上はOW可能でも、85近辺のWallと上値余地を考えNeutral。 |
| XLC | 111.18 | -47.79m | 127.11 | 115 / 104 | 107.87–114.49 | 通常 / 通常 | Alphabet決算前。負のGammaで値幅拡大リスクがあるが、前回UWからNeutralへ。115回復が改善の第一条件。 |
| XLB | 50.17 | +9.94m | 48.71 | 55 / 47.5 | 48.72–51.61 | 通常 / 通常 | 正のGammaだがスコア8位。PMIや鉱業決算待ちで、48.71維持なら下値は比較的抑制的。 |
| XLI | 178.57 | -98.72m | 193.71 | 180 / 165 | 172.20–184.94 | 通常 / 通常 | 負のGammaが最大級でFlipから遠い。180近辺の決算反応を上抜けられなければUW継続。 |
| XLK | 176.20 | -13.99m | 180.69 | 200 / 170 | 167.62–184.78 | 通常 / **High** | AI反発は確認できるが、Flip下・高IV・IV調整最下位。180.69回復まではUW、170割れは下方加速警戒。 |
| XLY | 114.85 | -73.50m | 137.82 | 120 / 107.5 | 110.79–118.91 | 通常 / 通常 | 総合最下位でFlipから約20%下。Tesla決算を控え、120を回復するまでUWを維持。 |

### 5.1 マクロ前提

各セクター判断に共通して使う現時点のマクロ環境は次の通り。

- **成長:** FRBの[2026年7月金融政策報告](https://www.federalreserve.gov/monetarypolicy/2026-07-mpr-summary.htm)は、1–3月期の実質GDPを緩やかな成長、企業設備投資を大幅増、家計消費を小幅増と整理している。6月ISMは製造業53.3、サービス業54.0で、ともに活動拡大圏にある一方、6月雇用者増は+5.7万人、失業率は4.2%にとどまり、成長の中身にはばらつきがある。
- **インフレ:** [BLSの6月CPI](https://www.bls.gov/news.release/cpi.htm?lv=true)は総合が前月比-0.4%、前年比+3.5%、コアが前月比横ばい、前年比+2.6%。6月のエネルギー価格低下が総合を押し下げたが、7月の原油反発により、この改善をそのまま先行きへ延長できない。
- **金利・信用:** 原油上昇を受け10年債利回りは7月20日午前に約4.58%。高金利は金融の利鞘には部分的な追い風だが、不動産、公益、一般消費財、長期成長株の割引率には逆風となる。FRBの[4月SLOOS](https://www.federalreserve.gov/data/sloos/sloos-202604.htm)ではC&Iローンの融資基準が引き締まり、需要は概ね横ばいだった。
- **消費:** [6月小売売上高](https://www.census.gov/retail/sales.html)は前月比+0.2%、前年比+6.7%。名目消費は崩れていないが、雇用増の鈍化、原油、金利が今後の実質購買力を圧迫するリスクがある。
- **住宅:** 直近公表済みの5月新築住宅販売は年率58.0万戸、前月比-7.3%、在庫月数10.3カ月。[6月分は7月24日公表予定](https://www.census.gov/construction/soc/schedule.html)で、住宅建設・REIT・銀行・建材・耐久消費財を横断する重要材料となる。
- **原油:** 7月20日午前のBrentは約88ドル。一方、EIAは[7月見通し](https://www.eia.gov/pressroom/releases/press590.php)で、Hormuzの輸送正常化を前提に7–9月期平均を74ドルと予想している。足元価格には大きな地政学プレミアムがあり、XLEには追い風だが、正常化時の下落余地も大きい。

### 5.2 XLF 金融 — Overweight +2.0%

**マクロ:** 高めの長期金利と景気拡大は純金利収益、資本市場収益、運用残高に追い風。一方、弱い雇用増、C&I融資基準の引き締まり、消費者信用の悪化リスクは貸出数量と与信費用の逆風である。したがって「金利高だけで金融全面強気」ではなく、預金調達力と信用力のある大手を優先する環境とみる。

**ボトムアップ:** Charles Schwabでは預かり資産、現金選好、利鞘、取引収益、Capital OneとAmerican Expressではカード利用額、延滞率、貸倒引当、地方銀行では預金ベータと商業不動産エクスポージャーが焦点。良好な収益でも、金利上昇が債券評価損や信用コストを増やす場合は相殺される。

**モデルとの統合:** モメンタム+2.50、Gamma +1.75、正のNet GEX +137.82mで総合1位。Spot 56.12はCall Wall 56にほぼ到達しており、方向は強いが短期上値は57.39まで限定されやすい。High Charmもあるため決算通過後のピン留めを想定する。

**結論:** 最も確度の高いOW。ただし追い上がりではなく、56近辺の保ち合いを利用する。54.84割れで縮小を検討し、Gamma Flip 53.92割れでNeutralへ戻す。

### 5.3 XLV ヘルスケア — Overweight +1.5%

**マクロ:** 雇用全体が鈍化するなかでも6月はヘルスケア雇用が増加し、需要の景気耐性を示す。医療CPIは前月比-0.1%、前年比+2.0%で、価格決定力の加速は見えないが、人件費・調達コストが安定すればプロバイダーの採算にはプラス。景気減速時のディフェンシブ性も評価する。

**ボトムアップ:** DanaherとThermo Fisherではバイオ医薬品顧客の在庫調整終了、機器受注、消耗品の継続収益を確認する。HCAとTenetでは患者数、手術ミックス、賃金・外注費、保険者との価格交渉が重要。製薬・バイオの個別治験リスクより、今週はライフサイエンスツールと病院の業績幅を重視する。

**モデルとの統合:** モメンタム+2.50、Gamma +1.50、正のNet GEX +45.65m。総合2位、IV調整後1位で、156.19–164.37のレンジに主要Flipが入らず構造は安定的。ただし唯一のHigh VannaかつHigh Charmで、決算後のIV低下に伴うフロー変化は大きい。

**結論:** XLFより上値抵抗が遠く、分散効果もあるためOW。155のPut Wallを終値で割ればOWを解消し、165近辺では利益確定を優先する。

### 5.4 XLRE 不動産 — Neutral

**マクロ:** 高い長期金利と住宅在庫の積み上がりは、資本コスト、物件評価、住宅関連需要に逆風。反対に、雇用やインフレの鈍化で金利が低下すれば、長期契約キャッシュフローの現在価値が上がるため反応は大きい。7月24日の新築住宅販売は方向を分ける材料になる。

**ボトムアップ:** D.R. HortonやPulteGroupはXLREの主要構成銘柄ではないが、住宅需要、住宅ローン金利への感応度、値引き・モーゲージバイダウンの先行指標になる。REITではオフィスと住宅の弱さ、データセンター・通信・物流施設の需要、借換期限、FFO、増資余力の差をみる必要があり、セクター一括OWには不向き。

**モデルとの統合:** モメンタム+2.50、正のNet GEXで総合3位だが、Call Wall 46に近くHard RuleでOW不可。強い価格トレンドと金利リスクが衝突している。

**結論:** Neutralが妥当。46を明確に上抜け、かつ長期金利が低下する場合にのみOW候補。43.80割れなら金利・資金調達懸念を優先する。

### 5.5 XLE エネルギー — Overweight +1.0%

**マクロ:** Iran・Hormuzを巡る供給不安は原油・LNG価格を押し上げ、上流企業のキャッシュフローに直接寄与する。反面、EIAの74ドル見通しと足元約88ドルの差は地政学プレミアムを示し、航行正常化や供給回復で急反落する余地がある。原油高はXLEにプラスでも、広範なインフレと金利上昇を通じて市場全体にはマイナスになりうる。

**ボトムアップ:** HalliburtonとSLBでは国際掘削、サービス価格、受注、顧客の設備投資計画、EQTやRange Resourcesでは天然ガス価格、ヘッジ、輸送制約、増産方針を確認する。統合石油大手では上流利益だけでなく、精製マージンと化学事業の悪化が相殺要因となる。

**モデルとの統合:** モメンタム+1.75、Gamma +1.75、正のNet GEX +44.33mでSpotはFlip 56.35上。ただしオプション需要-0.25、IVリスク-1.50、High Charmで、イベントプレミアムは相応に織り込まれている。

**結論:** 前週の機会損失を修正する**戦術的OW**であり、恒久的強気ではない。56.35上で維持、60–60.39で利益管理、56.35割れでNeutralへ戻す。

### 5.6 XLU 公益 — Neutral

**マクロ:** 電力需要と規制資産への投資は中期追い風だが、債券代替としての公益は4.5%台の長期金利に弱い。燃料価格上昇も、料金転嫁に時間差がある事業者には運転資金・規制リスクとなる。景気鈍化だけを理由に買うには金利水準が高い。

**ボトムアップ:** NextEra Energyでは規制公益のレートベース成長、再エネ案件の採算・資金調達、設備投資と株式発行余力を確認する。AI・データセンター向け電力需要は追い風だが、送電投資、規制承認、金利負担を差し引いて評価する必要がある。

**モデルとの統合:** 正のNet GEXだが、Spot 45.35、Flip 45.05、Call/Put Wall 45が密集。リスク制御-1.0、IVリスク-1.75、Hard RuleでOW不可。High Charmにより45付近のピン留めも起こりやすい。

**結論:** Neutral。45.05を維持して46.47方向へ離脱し、同時に金利が低下すれば改善。44.22割れはUnderweight検討水準。

### 5.7 XLP 生活必需品 — Neutral

**マクロ:** 雇用の鈍化や金利高はディフェンシブ需要を支える一方、食料品CPIは前月比+0.2%、前年比+2.7%で、企業側は価格引き上げと数量維持の両立を問われる。原油高は包装・物流コストを再び押し上げる可能性がある。

**ボトムアップ:** Philip Morrisでは販売数量、値上げ、無煙製品の成長、為替を確認する。食品・飲料・日用品では値上げ後の数量、プライベートブランドへのシフト、販促費、原材料・輸送コストが重要。前週の強さが実需なのか単なるリスク回避フローなのかを分ける。

**モデルとの統合:** モメンタム+1.75に対しGamma -1.75、Net GEX -26.11mでFlip 88.52下。総合6位でOWは可能だが、SpotがCall Wall 85近辺、High Charmでもあり、上値追随の効率が低い。

**結論:** 前週UnderweightからNeutralへ引き上げたが、OWにはしない。88.52回復と業績での数量維持を確認できればOW候補、83.17割れなら再び弱気。

### 5.8 XLC コミュニケーション・サービス — Neutral

**マクロ:** サービス業PMI 54.0と名目小売の前年比増加は広告・デジタル消費を支える。一方、雇用鈍化と高金利は広告主予算と高成長株のバリュエーションに逆風。通信は景気耐性があるが、資本集約度と価格競争の影響を受ける。

**ボトムアップ:** Alphabetは検索・YouTube広告、Cloud成長、AI検索の収益化、AIインフラ投資による減価償却とマージンが核心。AT&T、Comcast、T-Mobile、Verizon、Charterは純増、解約率、ARPU、端末販促、ブロードバンド競争、設備投資を確認する。同じXLCでも広告プラットフォームと通信では利益要因が異なる。

**モデルとの統合:** モメンタム+0.25、Gamma -1.75、オプション需要-0.50、Net GEX -47.79mでFlip 127.11を大幅に下回る。総合7位、Hard RuleでOW不可。ただし前回UWが利益寄与し、足元ではXLCが日中反発しているためNeutralまで戻した。

**結論:** 決算前に方向を追加しない。Alphabet決算後に115を明確に超えれば改善、107.87割れならUWへ戻す。通信株の安定だけでXLC全体を強気にしない。

### 5.9 XLB 素材 — Neutral

**マクロ:** 製造業PMI 53.3は需要面の追い風だが、Prices Paid 73.0は原料・輸送コスト圧力を示す。原油・海運費上昇は化学のマージンを圧迫し、鉱業は中国・世界需要、ドル、金属価格に左右される。景気拡大とコストインフレが同居している。

**ボトムアップ:** Dowでは販売数量、稼働率、原料ナフサ・ガスと製品価格のスプレッド、Freeport-McMoRanとTeckでは銅価格、生産量、品位、単位コスト、プロジェクト投資を確認する。金属価格上昇だけでなく、コストと出荷量を合わせて判断する。

**モデルとの統合:** 正のNet GEX +9.94m、Flip 48.71上は下値抑制要因。一方、モメンタム-2.00、オプション需要-1.00、リスク制御-1.50で総合8位、Hard RuleによりOW不可。

**結論:** Neutral。51.61突破と決算での数量・マージン改善がそろえば上方修正。48.71割れなら正のGammaの支えが失われるためUW候補。

### 5.10 XLI 資本財 — Underweight -1.0%

**マクロ:** 製造業拡大と企業設備投資は明確な追い風で、防衛・電力インフラ・航空宇宙の受注も中期的には強い。一方、原油高は航空・物流の燃料費を押し上げ、雇用鈍化は広範な需要の減速リスクを示す。マクロだけならNeutral寄りだが、イベント密度と市場構造が弱い。

**ボトムアップ:** 3M、Honeywell、GE Vernovaでは受注、バックログ、価格・数量、マージン、RTX・Lockheed Martinでは防衛受注とサプライチェーン、Union Pacific・Norfolk Southernでは輸送量、運賃、燃料費、生産性を確認する。好材料が防衛・電力設備に集中し、運輸や一般資本財へ広がるかが鍵。

**モデルとの統合:** モメンタム-0.50、Gamma -2.75、リスク制御-1.0、Net GEX -98.72mで総合9位。SpotはFlip 193.71を8%以上下回り、Call Wall 180に近い。好決算でも180で止まる可能性がある一方、失望時は負のGammaで下落が増幅しやすい。

**結論:** ファンダメンタルズ全否定ではなく、**イベント週の戦術的UW**。180を明確に上抜け、複数業種でガイダンス改善が確認できればNeutral。172.20割れでUWを維持・拡大する。

### 5.11 XLK 情報技術 — Underweight -1.5%

**マクロ:** 企業設備投資とAIインフラ需要は構造的追い風。一方、長期金利上昇、原油由来のインフレ再燃、AI投資回収への疑念は高バリュエーション銘柄の逆風となる。6月製造業ではComputer & Electronic Productsの生産拡大が示されたが、短期の株価は業績の良さより期待値との差に左右される。

**ボトムアップ:** Texas Instrumentsはアナログ半導体の在庫・産業需要、IBMとServiceNowは企業IT支出、契約残高、AI案件の収益化、Intelは製品ロードマップ、Foundry損益、設備投資、粗利率を確認する。AI関連では売上成長だけでなく、GPU・データセンター投資に対する回収期間とフリーキャッシュフローが重要。

**モデルとの統合:** モメンタム-1.00、Gamma -2.25、リスク制御-2.50、IVリスク-1.50、Net GEX -13.99m。総合10位、IV調整後11位でFlip 180.69下、7日レンジは±4.87%と最大。High Charmにより決算後IV低下時のヘッジ調整も大きい。

**結論:** AIの長期成長を否定する判断ではなく、価格・期待値・オプション構造に基づく短期UW。180.69回復をUW縮小、184.78超えをNeutral化の条件とし、170割れではリスクをさらに削減する。

### 5.12 XLY 一般消費財 — Underweight -2.0%

**マクロ:** 小売売上は名目ベースで維持されているが、雇用増+5.7万人、原油高、住宅ローン・自動車ローン金利は裁量支出に逆風。消費全体の崩壊ではなく、高所得層と低所得層、サービスと耐久財の二極化を想定する。

**ボトムアップ:** Teslaでは自動車粗利、値引き、納車見通し、ロボタクシー投資と規制、GMでは価格・販売奨励金、在庫、EV損益、D.R. HortonとPulteGroupでは受注、キャンセル、粗利、住宅ローン優遇を確認する。住宅会社は金利を下げるための販売費用増が数量を支える一方、利益率を圧迫しうる。

**モデルとの統合:** モメンタム-2.00、Gamma -1.75、オプション需要-0.50、リスク制御-1.50、Net GEX -73.50mで総合最下位。Flip 137.82は約20%上で、短期改善の現実的な第一関門は120。Tesla決算を前に、下方ショックを吸収しにくい。

**結論:** 最大UW。118.91–120を決算後に回復すればUWを縮小し、110.79割れ、特に107.5のPut Wall割れでは下方加速に備える。

### 5.13 判断の比較

| 判断 | セクター | マクロ評価 | ボトムアップ評価 | オプション構造が加えた最終調整 |
|---|---|---|---|---|
| OW | XLF | 成長・金利は追い風、信用は要監視 | 預金・利鞘・カード与信を選別 | 正のGamma・首位のため+2.0% |
| OW | XLV | 景気耐性、雇用増 | ツール受注と病院採算 | IV調整首位、ただしVanna/Charmを考慮し+1.5% |
| OW | XLE | 地政学・原油が追い風、正常化は逆風 | 掘削・ガス・上流CFを確認 | Flip上だが高IVのため+1.0%に抑制 |
| Neutral | XLRE/XLP/XLU | 金利・防御性が拮抗 | 業種内格差が大きい | Wall/Hard Ruleにより見送り |
| Neutral | XLC/XLB | 活動は拡大、イベント不確実性 | 広告・通信、化学・鉱業を個別確認 | 負のGammaまたは弱い需要スコアで見送り |
| UW | XLI | 設備投資は強いが原油・景気に敏感 | 決算の業種間分散が大きい | 最大級の負のGEXで-1.0% |
| UW | XLK | AI追い風と金利逆風が衝突 | 期待値と投資回収を確認 | Flip下・高IVで-1.5% |
| UW | XLY | 名目消費維持も金利・雇用が逆風 | 自動車・住宅の採算リスク | 最下位・負のGammaで-2.0% |

## 6. 7月20日午前の初日反応

以下は7月17日終値から7月20日11:02 ET前後までの**途中経過**であり、日次確定値ではない。

| 上昇側 | 途中騰落率 | 下落側 | 途中騰落率 |
|---|---:|---|---:|
| XLE | +0.68% | XLB | -0.78% |
| XLC | +0.44% | XLY | -0.52% |
| XLU | +0.37% | XLV | -0.49% |
| XLK | +0.35% | XLI | -0.48% |

AI・半導体の反発はXLKを押し上げているが、現時点ではGamma Flip 180.69を回復していないため、モデル上は「反転確認」ではなく「負のGamma領域内の自律反発」と扱う。XLEの上昇は原油・地政学リスクと整合する。XLB、XLY、XLIの弱さは、金利・景気・決算感応度を抑える今週の配分と整合的である。

## 7. 日別イベント対応

決算日程は[Kiplingerの週間決算カレンダー](https://www.kiplinger.com/investing/stocks/17494/next-week-earnings-calendar-stocks)と各社IRで照合した。以下の「対応」は、発表内容そのものではなく、イベントをどのETFとGamma水準で管理するかを示すモデル推論である。

### 7月21日（火）：金融・住宅・資本財・エネルギー

**事実:** Charles Schwab、Capital Oneや地方銀行、D.R. Horton、3M、GM、Halliburton、EQTなどの決算が予定される。

**対応:** 

- **XLF:** 56のCall Wall近辺から57.39が上側レンジ。好決算でも56付近に抑えられるなら利幅は限定的。53.92のFlipを割らない限りOW継続。
- **XLRE/XLB:** 住宅販売・住宅建設のガイダンスは住宅需要、住宅ローン金利、建材へ波及。XLREは46、XLBは48.71を確認する。
- **XLI/XLY:** 3MやGMの需要・コスト見通しを景気循環の確認材料とする。XLIは180、XLYは120が戻りの壁。
- **XLE:** 油田サービスと天然ガス企業の見通しを、原油価格だけでなく掘削・設備投資へ接続。56.35〜60の範囲を基本シナリオとする。

### 7月22日（水）：Alphabet、Teslaと大型テクノロジー

**事実:** Alphabet、Tesla、Texas Instruments、IBM、ServiceNowのほか、AT&T、PulteGroupなどの決算が予定される。

**対応:**

- **XLC / Alphabet:** 115は7日レンジ上限114.49のすぐ上。好決算で115を明確に上抜ければNeutralから改善、107.87割れなら負のGammaによる下振れを警戒する。
- **XLY / Tesla:** XLYは総合最下位。118.91〜120を上抜けるまではUWを維持し、110.79、次いで107.5を下値監視とする。
- **XLK / TXN・IBM・NOW:** 半導体需要と企業IT支出を確認。180.69のFlip回復はUW縮小条件、170のPut Wall割れはリスク削減条件。
- **XLRE / PulteGroup:** 金利と受注の組み合わせを重視し、単独の好決算だけでHard Ruleを解除しない。

### 7月23日（木）：失業保険、Intel、資本財・素材

**事実:** 新規失業保険申請件数に加え、Blackstone、Comcast、Dow、Freeport-McMoRan、Honeywell、Lockheed Martin、Norfolk Southern、RTX、Thermo Fisher、Union Pacificなどが予定され、Intelは引け後に発表する。Intelの発表日は[同社IR](https://newsroom.intel.com/corporate/intel-to-report-second-quarter-2026-financial-results)でも確認した。

**対応:**

- **金利経路:** 雇用の強さが金利上昇を招けばXLRE・XLU・XLYに逆風。弱すぎる雇用は景気敏感のXLI・XLBへ逆風となる。
- **XLK / Intel:** 180.69未満では負のGammaレジーム。ガイダンスが半導体全体へ波及するため、170〜180.69のどちらを先に抜けるかを重視する。
- **XLI:** 180のCall Wallを超えられるかを、航空宇宙・鉄道・複合企業の決算で確認。負のNet GEX -98.72mのため、失望時の値幅拡大に注意する。
- **XLB:** 鉱山・化学の需要見通しと商品価格を48.71のFlipへ接続。維持ならNeutral、割れれば弱気へ。
- **XLV:** Thermo Fisherを含むヘルスケア決算を確認。156.19〜164.37内ならOW維持、155割れで再評価する。

### 7月24日（金）：PMI、新築住宅販売、主要決算

**事実:** 速報製造業・サービス業PMI、新築住宅販売が予定される。American Express、Charter Communications、HCA Healthcare、NextEra Energy、SLB、Verizonなどの決算も予定される。

**対応:**

- **PMI:** XLI・XLB・XLKの需要見通しに直結。強いPMIでも金利が急騰する場合はXLY・XLREに必ずしも好材料ではない。
- **新築住宅販売:** XLREだけでなく、住宅ローンのXLF、建材のXLB、耐久消費財のXLYへ波及する。
- **決算:** AXPはXLFと消費、HCAはXLV、NextEraはXLU、SLBはXLE、CharterとVerizonはXLCの確認材料とする。
- **週末リスク:** Iran・Hormuz関連のヘッドラインをまたぐため、XLEの利益追随と広範なインフレ・金利リスクを別々に評価する。

## 8. Vanna / Charmオーバーレイ

### フラグ

- **High Vanna:** XLVのみ。
- **High Charm:** XLF、XLV、XLE、XLU、XLP、XLK。
- **両方High:** XLV。
- **いずれも通常:** XLRE、XLC、XLB、XLI、XLY。

### モデル推論

- **XLV:** 決算後にIVが低下すると、VannaとCharmの双方を通じたディーラーヘッジ調整が価格方向を増幅しうる。正のNet GEXでも「常に低変動」とは限らない。
- **XLK:** High Charmと高ATM IVの組み合わせ。大型決算を通過するにつれて短期オプションの時間価値が急減し、180.69または170への接近時にヘッジフローが変わりやすい。
- **XLF/XLE/XLP/XLU:** 主要Wall付近での時間経過がピン留めを促す可能性がある一方、Wall離脱時はフロー方向の反転に注意する。
- これらは方向予測ではなく、**同じニュースでも値動きの出方が変わる条件**として使う。

## 9. シナリオ

### 強気シナリオ

AI・半導体決算が需要の持続を示し、原油が安定または反落、長期金利が落ち着く。XLKが180.69を回復、XLCが115を上抜け、XLYが120へ接近する。この場合、XLK・XLYのUWを段階的に縮小し、XLF・XLVのOWを維持する。XLEは60付近で一部利益確定を検討する。

### 中立シナリオ

決算はまちまちで、主要ETFは7日IVレンジ内。XLFは56近辺、XLEは56.35〜60、XLUは45近辺でピン留めされる。現行のXLF・XLV・XLE OW、XLI・XLK・XLY UWを維持し、Wall突破を待つ。これを基本シナリオとする。

### 弱気シナリオ

Iran・Hormuzを巡る緊張で原油・インフレ・金利が上昇する、または大型テクノロジー決算が失望を招く。XLEには相対的な追い風でも、XLY・XLRE・XLUと広範な株式バリュエーションには逆風となる。XLKが170、XLYが110.79、XLIが172.20を割れば負のGamma下の下方加速を想定し、グロスリスクを落とす。XLEも56.35を割れば「原油高＝無条件のOW」という前提を撤回する。

## 10. 監視水準

| ETF | 上方向の確認 | 下方向の確認 | 行動の目安 |
|---|---|---|---|
| XLF | 56、57.39 | 54.84、53.92 | Flip維持でOW。53.92割れで縮小。 |
| XLV | 164.37、165 | 156.19、155 | 155維持でOW。165到達は利幅管理。 |
| XLRE | 46、46.84 | 43.80、41.66 | Hard Rule継続。46突破と金利低下を同時確認。 |
| XLE | 60、60.39 | 56.35、55.76、55 | 56.35上でOW。60付近は利食い・反落警戒。 |
| XLU | 45.05、46.47 | 45、44.22 | 45密集帯からの離脱方向を確認。 |
| XLP | 86.97、88.52 | 83.17、78 | 88.52回復までNeutral。 |
| XLC | 114.49、115 | 107.87、104 | 115突破で改善、107.87割れで弱気。 |
| XLB | 51.61、55 | 48.72、48.71、47.5 | Flip維持でNeutral、割れで警戒。 |
| XLI | 180、184.94 | 172.20、165 | 180未満でUW、Flip 193.71は遠い。 |
| XLK | 180.69、184.78 | 170、167.62 | Flip回復までUW。170割れで削減。 |
| XLY | 118.91、120 | 110.79、107.5 | 120回復までUW。 |

## 11. 今週の運用方針

1. 現時点ではXLF +2.0%、XLV +1.5%、XLE +1.0%、XLI -1.0%、XLK -1.5%、XLY -2.0%を採用する。
2. 7月22日のAlphabet/Tesla、7月23日のIntelを通過するまでは、負のGammaであるXLK・XLY・XLCの値動きを追いかけない。
3. XLEは前週の反省からOWへ変更するが、56.35のGamma Flipを明確な撤退判断に使う。
4. 原油上昇をXLEの利益要因と、XLRE・XLU・XLYに波及するインフレ・金利要因へ分解して判断する。
5. 米国引け後に価格と全11チェーンを再取得し、Gamma Flip・Wall・IVレンジ・Vanna/Charmフラグが変わった場合は確定版へ差し替える。

## 12. 外部参照

- [LPL Financial — Weekly Market Performance, July 17, 2026](https://www.lpl.com/research/blog/weekly-market-performance-july-17-2026.html)
- [Kiplinger — This Week's Economic Calendar](https://www.kiplinger.com/investing/economy/this-weeks-economic-calendar)
- [Kiplinger — Next Week's Earnings Calendar](https://www.kiplinger.com/investing/stocks/17494/next-week-earnings-calendar-stocks)
- [Federal Reserve — FOMC Blackout Period Calendar](https://www.federalreserve.gov/monetarypolicy/files/fomc-blackout-period-calendar.pdf)
- [Federal Reserve — Monetary Policy Report, July 2026](https://www.federalreserve.gov/monetarypolicy/2026-07-mpr-summary.htm)
- [Federal Reserve — April 2026 Senior Loan Officer Opinion Survey](https://www.federalreserve.gov/data/sloos/sloos-202604.htm)
- [BLS — Consumer Price Index, June 2026](https://www.bls.gov/news.release/cpi.htm?lv=true)
- [BLS — Employment Situation, June 2026](https://www.bls.gov/news.release/empsit.htm)
- [U.S. Census Bureau — Advance Monthly Retail Sales, June 2026](https://www.census.gov/retail/sales.html)
- [U.S. Census Bureau — New Residential Sales and Release Schedule](https://www.census.gov/construction/nrs/current/index.html)
- [EIA — July 2026 oil production and price forecast](https://www.eia.gov/pressroom/releases/press590.php)
- [ISM — June 2026 Manufacturing PMI](https://www.ismworld.org/supply-management-news-and-reports/reports/ism-pmi-reports/pmi/june/)
- [ISM — June 2026 Services PMI](https://www.ismworld.org/supply-management-news-and-reports/reports/ism-pmi-reports/services/june/)
- [Alphabet Investor Relations — Q2 2026 results date](https://alphabet2025ir.q4web.com/investor/news/news-details/2026/Alphabet-Announces-Date-of-Second-Quarter-2026-Financial-Results-Conference-Call-2026-2h_R0kzZHY/default.aspx)
- [Tesla Investor Relations — Q2 2026 earnings date](https://ir.tesla.com/)
- [Intel Newsroom — Second-quarter 2026 financial results schedule](https://newsroom.intel.com/corporate/intel-to-report-second-quarter-2026-financial-results)
- [AP — July 20 market update on AI shares, oil and Iran-related risk](https://apnews.com/article/stocks-market-ai-oil-iran-war-15939a01f378bcec5eec2868e8100ca9)

## 13. 内部成果物

- 実行済みNotebook: `outputs/executed/main_20260721_executed.ipynb`
- ダッシュボード: `outputs/dashboard/sector_gamma_dashboard.html`
- 更新配分: `outputs/tables/proposed_portfolio.csv`
- GEX判断表: `outputs/tables/gex_decision_table.csv`
- IV予想変動表: `outputs/tables/iv_expected_move_table.csv`
- Vanna/Charm表: `outputs/tables/second_order_greeks_table.csv`
- 前週寄与度: `outputs/tables/weekly_attribution.csv`

---

**次回更新条件:** 2026-07-20米国引け後の確定データで再実行し、日中スナップショットとの差分を確認する。
