# Pythonについて

**User:** Anonymous (kencharoffx@gmail.com)  
**Created:** 3/21/2026 15:24:47  
**Updated:** 3/21/2026 18:48:31  
**Exported:** 4/2/2026 7:16:51  
**Link:** [https://chatgpt.com/c/69be39ab-e29c-83a7-bbb9-d8be3d4d154a](https://chatgpt.com/c/69be39ab-e29c-83a7-bbb9-d8be3d4d154a)  

## Prompt:
python

## Response:
思考時間: 2 ～ 3 秒

Pythonですね。何をしたいかを書いてもらえれば、そのまま使える形で出します。

たと

## Prompt:
etfや暗号資産の投資戦略の開発をしたいです。統一的なバックエスト環境を構築したいが一般的にはどのようなライブラリや設計がされているか調査してください。最終的には自前で実装することが目的です。時系列データをわたし、戦略部分だけそれぞれオーバーライドして構築することを目指しています。

## Response:
主要なOSSと、それらに共通する設計パターンを先に押さえます。最後に「自前実装するならこう切る」という形で、ETF/暗号資産の両方に載せやすい最小アーキテクチャまで落とします。

かなり見えてきました。OSSは大きく、`ベクトル化で大量試行`、`イベント駆動で約定を真面目に再現`、`暗号資産の実運用寄り`の3系統に分かれます。自前実装が目的なら、最初はこの3つを混ぜずに層分離して設計するのが重要です。

思考時間: 41s

ETFと暗号資産を同じ枠組みで扱うバックテスト環境は、実務上かなりよくある設計です。結論からいうと、一般的なOSSは **「研究用のベクトル化エンジン」** と **「約定再現を重視するイベント駆動エンジン」** と **「暗号資産の実運用寄りフレームワーク」** に分かれます。自前実装が最終目的なら、最初から全部入りにせず、**研究層・シミュレーション層・分析層を分離**して作るのが最も失敗しにくいです。[Freqtrade+3VectorBT+3Zipline+3](https://vectorbt.dev/getting-started/features/?utm_source=chatgpt.com)

まず、主要ライブラリをどう見るべきかです。

**vectorbt** は pandas / NumPy ベースで、Numba により高速に大量のパラメータや戦略を回すタイプです。公式には、ポートフォリオモデリング、取引コスト、ドローダウン等を扱え、さらに **vectorized backtesting** と **event-driven backtesting using callbacks** の両モードを持つとされています。したがって、シグナル探索・パラメータスイープ・ETF/crypto 横断の研究基盤として非常に相性がよいです。反面、マイクロストラクチャや複雑な約定制御を厳密に再現する用途では、自前の執行層を別に持ちたくなります。[VectorBT+3VectorBT+3VectorBT+3](https://vectorbt.dev/?utm_source=chatgpt.com)

**backtrader** は典型的なイベント駆動です。`Cerebro` が Data Feed, Strategy, Observers, Analyzers を束ねる中央ハブになっていて、`Strategy` にライフサイクルがある構造です。つまり、「時系列を1本流し、その都度シグナル・注文・約定・評価を処理する」というバックテスタの古典的設計をかなりそのまま学べます。自前実装の参照元としてはとても良いですが、最近の大規模研究や大量スイープにはやや重い場面があります。[Backtrader+3Backtrader+3Backtrader+3](https://www.backtrader.com/docu/cerebro/?utm_source=chatgpt.com)

**backtesting.py** はさらに軽量で、`Backtest(data, strategy, ...)` という非常に小さいAPIに整理されています。シンプルなルールベース戦略を素早く試すには良い一方、ETFと暗号資産を統一した多資産・多口座・多通貨・複雑約定まで育てる土台としては、最終的には自前の設計のほうが拡張しやすいです。[Kernc+2Kernc+2](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html?utm_source=chatgpt.com)

**Zipline / Zipline Reloaded** はイベント駆動で、公式にも「stream-based」「look-ahead bias を避けやすい」「slippage, transaction costs, order delays を扱う」と明示されています。設計思想としては非常に教科書的です。ただしエコシステムの継続性やデータバンドル前提の癖があるので、2026年時点で新規に自前基盤を作るための“思想の参考”としては有用でも、そのまま主軸にする優先度は高くありません。[Zipline+2Zipline+2](https://zipline.ml4trading.io/?utm_source=chatgpt.com)

ETF寄りで参考になるのは **QSTrader** です。公式に、長短の systematic trading、特に cash equities / ETFs、日次〜低頻度のリバランス、そして **portfolio construction と risk management を重視**すると書かれています。これはまさに ETF バックテストの設計に近く、**シグナル生成** と **ポートフォリオ構築** を明確に分ける設計の参考になります。[quantstart.com+1](https://www.quantstart.com/qstrader/introduction/?utm_source=chatgpt.com)

暗号資産寄りでは **Freqtrade** と **NautilusTrader** が対照的です。Freqtrade は strategy customization, stoploss, order types, backtesting などがよく整理されていて、実運用ボットの文脈で「戦略だけ差し替える」設計が明快です。たとえば `order_types` で entry/exit/stoploss を market/limit で分けられ、stoploss を取引所に置く設定もあります。暗号資産特有の実務要件に近いです。[Freqtrade+4Freqtrade+4Freqtrade+4](https://www.freqtrade.io/en/stable/strategy-customization/?utm_source=chatgpt.com)

NautilusTrader はさらに本格的で、公式に **BacktestEngine, Cache, MessageBus, Portfolio, Actors, Strategies, Execution Algorithms** から成ると説明され、Rust core / Python edge を掲げています。これは「研究・バックテスト・ライブを同じエンジンで」という思想が強く、約定モデルや execution algorithm を重視する高精度側の設計見本です。自前実装でここまでやると重いですが、モジュール分割の思想は非常に参考になります。[NautilusTrader+3NautilusTrader+3NautilusTrader+3](https://nautilustrader.io/docs/latest/concepts/backtesting/?utm_source=chatgpt.com)

Hummingbot は CEX/DEX を跨ぐ crypto 自動売買フレームワークで、`Clock` と `TimeIterator` を中心に major components を動かす構造が公開されています。これは「時間が全ての駆動源」というイベント設計の見本です。ただし Hummingbot は暗号資産の実運用・接続寄りで、ETFとの統一研究環境を作る直接の土台というより、**ライブ実装を見据えた clock-driven 設計**の参考先です。[hummingbot.org+2hummingbot.org+2](https://hummingbot.org/docs/?utm_source=chatgpt.com)

ここから見える一般的な設計パターンは次の通りです。

1つ目は **ベクトル化研究層** です。価格やリターン、シグナル、ウェイトを配列で持ち、一括でP&Lを計算します。大量のハイパーパラメータ探索、リバランス頻度比較、特徴量実験には最適です。vectorbt がこの代表です。ETFのような日次・低頻度戦略ではまずここから始めるのが合理的です。[VectorBT+1](https://vectorbt.dev/getting-started/features/?utm_source=chatgpt.com)

2つ目は **イベント駆動シミュレーション層** です。バーやティックごとに `on_bar` / `on_tick` が呼ばれ、注文、約定、ポジション、キャッシュが逐次更新されます。backtrader, Zipline, NautilusTrader がこの系譜です。注文種別、部分約定、遅延、スリッページ、ストップ注文、出来高制約を真面目に扱いたいならこちらが必要です。[Zipline+2NautilusTrader+2](https://zipline.ml4trading.io/beginner-tutorial?utm_source=chatgpt.com)

3つ目は **ポートフォリオ構築を独立層に切り出す設計** です。QSTrader や PyPortfolioOpt / Riskfolio-Lib / skfolio が象徴的で、期待リターン推定・リスクモデル・制約付き最適化・再バランスを “戦略ロジック” とは別物として扱います。ETFのクロスセクション戦略では、この分離が非常に効きます。[skfolio+3quantstart.com+3pyportfolioopt.readthedocs.io+3](https://www.quantstart.com/qstrader/introduction/?utm_source=chatgpt.com)

したがって、あなたの目標である「時系列データを渡し、戦略だけオーバーライドする」設計なら、最も良い抽象化は **Strategy = target weights generator** です。つまり戦略は「この時点で各資産を何%持ちたいか」を返すだけにし、約定・手数料・資金管理・リスク制約・評価はエンジン側が処理します。これは ETF にも crypto にも共通化しやすく、vectorbt 的な研究層にも、QSTrader 的な portfolio construction 層にも自然に繋がります。[VectorBT+2quantstart.com+2](https://vectorbt.dev/api/portfolio/base/?utm_source=chatgpt.com)

自前実装するなら、私は次の層に切るのを勧めます。

**Data layer**  
OHLCV, funding, borrow, benchmark, macro, universe metadata を統一フォーマットで保持します。ETFでは取引カレンダーが重要で、`pandas_market_calendars` や `exchange_calendars` のようなカレンダーライブラリが一般に使われています。これにより祝日、早引け、複数市場の営業日差を吸収できます。暗号資産は 24/7 なので、ここだけ別 calendar adapter にします。[GitHub+3Pandas Market Calendars+3Pandas Market Calendars+3](https://pandas-market-calendars.readthedocs.io/?utm_source=chatgpt.com)

**Feature / signal layer**  
インジケータ、alpha、予測モデルはここで計算します。ここではまだ注文を出さず、あくまで `signal` か `score` を返します。vectorbt の indicator factory のように、「入力系列 -> 出力特徴量」の関数群として独立させると拡張しやすいです。[VectorBT](https://vectorbt.dev/api/indicators/factory/?utm_source=chatgpt.com)

**Portfolio construction layer**  
score を target weights に変換します。等ウェイト、ボラ逆数、max Sharpe、HRP、CVaR、制約付き最適化などをここに置きます。PyPortfolioOpt は efficient frontier / Black-Litterman / HRP、Riskfolio-Lib は多様な risk measures と階層型ポートフォリオ、skfolio は scikit-learn 風の model selection / validation / stress test を提供しており、この層の部品設計の参考になります。[skfolio+6pyportfolioopt.readthedocs.io+6pyportfolioopt.readthedocs.io+6](https://pyportfolioopt.readthedocs.io/?utm_source=chatgpt.com)

**Execution / broker simulator layer**  
target weights を実際の注文に変換します。ここで rebalance threshold、発注単位、成行/指値、maker/taker fee、スリッページ、volume cap、部分約定を扱います。Freqtrade の order type / stoploss、NautilusTrader の fee model や execution system は、この層の設計見本です。ETFだけなら簡素化できますが、crypto を含めるならここを別モジュールにしないとすぐ破綻します。[NautilusTrader+3Freqtrade+3Freqtrade+3](https://www.freqtrade.io/en/stable/configuration/?utm_source=chatgpt.com)

**Accounting layer**  
cash, positions, cost basis, realized/unrealized PnL, FX換算, funding, borrow cost を持ちます。ETFと暗号資産を統一するには、この層の台帳をしっかり持つことが重要です。特に crypto は quote currency や perpetual の funding が絡むため、「単なるリターン系列の積み上げ」では足りません。これは多くのイベント駆動系フレームワークが portfolio / account を独立させている理由です。[NautilusTrader+1](https://nautilustrader.io/docs/latest/concepts/backtesting/?utm_source=chatgpt.com)

**Analytics layer**  
returns series, turnover, hit ratio, drawdown, exposure, attribution, factor exposure を算出します。Empyrical は基本統計、Pyfolio は tear sheet、QuantStats は stats / plots / reports を提供していて、分析層の切り出し方の参考になります。[GitHub+4empyrical.ml4trading.io+4pyfolio.ml4trading.io+4](https://empyrical.ml4trading.io/?utm_source=chatgpt.com)

設計上、ETFと暗号資産を同居させるときに最重要なのは、**Strategy API を市場非依存に保つ** ことです。たとえば次の責務分離がよいです。

*   `Strategy.generate_targets(state) -> target_weights`
*   `PortfolioConstructor.transform(signals, risk_model) -> target_weights`
*   `ExecutionModel.create_orders(current_positions, target_weights, market_state) -> orders`
*   `BrokerSimulator.fill(orders, bar/tick, fee_model, slippage_model) -> fills`
*   `Account.apply(fills) -> new_state`
*   `Evaluator.compute(history) -> report`

この切り方なら、戦略は ETF でも BTC/ETH でも同じです。違いは Data, Calendar, FeeModel, ExecutionModel に押し込めます。これは vectorbt 的な「signals/arrays を渡す」世界と、Nautilus / backtrader 的な「engine に strategy を差し込む」世界の中間で、もっとも自前実装向きです。[VectorBT+2NautilusTrader+2](https://vectorbt.dev/getting-started/features/?utm_source=chatgpt.com)

実装方針としては、最初から完全イベント駆動にせず、**二層構成** が現実的です。

**Phase 1: research engine**  
日次またはバー単位で、`prices + target_weights -> portfolio returns` をベクトル化で回す。ここで戦略検証、特徴量、パラメータ探索、ウォークフォワードを整えます。ETF戦略の多くはまずこれで十分です。[VectorBT+1](https://vectorbt.dev/?utm_source=chatgpt.com)

**Phase 2: execution simulator**  
勝ち残った戦略だけをイベント駆動エンジンに通し、約定遅延・部分約定・スプレッド・maker/taker fee・stop order を検証します。暗号資産は最終的にこちらが必要です。[Zipline+2Freqtrade+2](https://zipline.ml4trading.io/beginner-tutorial?utm_source=chatgpt.com)

この二層構成にすると、研究速度と執行精度を両立できます。逆に、最初からイベント駆動だけで全部やろうとすると開発コストが跳ねますし、最初からベクトル化だけで済ませると暗号資産の実運用差分を取り逃します。[VectorBT+1](https://vectorbt.dev/getting-started/features/?utm_source=chatgpt.com)

自前実装で最低限入れるべき仕様を挙げると、次です。

*   入力は `DataBundle` として統一し、`prices`, `returns`, `volume`, `metadata`, `calendar`, `funding/borrow` を持たせる。ETFでは営業日、crypto では 24/7 を calendar adapter で吸収します。[Pandas Market Calendars+1](https://pandas-market-calendars.readthedocs.io/en/latest/pandas_market_calendars.html?utm_source=chatgpt.com)
*   戦略は直接売買せず、`score` または `target_weights` を返すだけにする。[pmorissette.github.io+1](https://pmorissette.github.io/bt/?utm_source=chatgpt.com)
*   リスクと最適化は strategy の外に出す。PyPortfolioOpt / Riskfolio-Lib / skfolio のように別モジュール化する。[pyportfolioopt.readthedocs.io+2riskfolio-lib.readthedocs.io+2](https://pyportfolioopt.readthedocs.io/?utm_source=chatgpt.com)
*   約定は `BrokerSimulator` に集約し、fee/slippage/order-type を asset class / venue ごとに差し替え可能にする。[Freqtrade+1](https://www.freqtrade.io/en/stable/configuration/?utm_source=chatgpt.com)
*   成績評価は Empyrical / QuantStats / Pyfolio 的に、returns から再計算可能な純粋関数群として分離する。[empyrical.ml4trading.io+2pyfolio.ml4trading.io+2](https://empyrical.ml4trading.io/?utm_source=chatgpt.com)

逆に、初期版でやらなくてよいものは、板レベルシミュレーション、複数口座、複数戦略配分、リアルタイム接続、超高頻度のorder book replayです。NautilusTrader や Hummingbot はこの先の世界として参考にしつつ、最初は daily/hourly bar ベースの設計に留めるのが良いです。[NautilusTrader+1](https://nautilustrader.io/docs/latest/concepts/backtesting/?utm_source=chatgpt.com)

総合すると、あなたの用途に最も相性が良い参照元はこうです。

*   **研究エンジンの思想**: vectorbt
*   **イベント駆動の骨格**: backtrader / Zipline
*   **ETFの portfolio construction**: QSTrader + PyPortfolioOpt / Riskfolio-Lib / skfolio
*   **暗号資産の execution / venue 差分**: Freqtrade
*   **将来の高精度化の参照先**: NautilusTrader

この組み合わせを抽象化して、自前では  
**Data → Signal → Portfolio Construction → Execution → Accounting → Analytics**  
に分けるのが最も筋が良いです。[NautilusTrader+3VectorBT+3quantstart.com+3](https://vectorbt.dev/getting-started/features/?utm_source=chatgpt.com)

必要なら次に、あなたの用途向けに  
**Pythonでの自前バックテスト基盤のクラス設計案**  
を、`BaseStrategy` と `BacktestEngine` のインターフェースまで落として具体的に書きます。

## Prompt:
research engine を想定します。ただし、ハイパラ探索は不要で、リークなしに戦略を試し比較しやすいようにしたいです。また、etfや暗号資産の時系列はどのように取得するのが一般的ですか？高品質なものを無料で使用したいです。株式分割や配当などの影響をきちんと考慮するためにトータルリターンを取得できるものが望ましい

## Response:
研究エンジン前提なら、設計の焦点は「速さ」より「時点整合性」と「比較可能性」です。データ取得元も含めて、ETFは配当・分割調整、暗号資産は取引所差と funding の扱いで分けて整理します。

データ面では、ETFは「無料で実務上いちばん使われがちなのは Yahoo 系」、暗号資産は「CCXT で取引所から直接」が中心です。研究用途ならこれで十分ですが、ETFは corporate actions、暗号資産は取引所差と funding を別管理にしておくのが肝です。

思考時間: 34s

research engine 前提なら、設計の主眼は **高速化** ではなく **時点整合性・比較容易性・再現性** です。  
つまり、「同じデータ束を渡して、戦略ごとに signal / target weight だけ差し替え、必ず同じ評価系を通す」構成が最もよいです。

ETF と暗号資産については、一般的な取得方法もかなり違います。

*   **ETF**: Yahoo Finance 系を `yfinance` などで取る運用が広く使われます。Yahoo 系では historical に dividends / splits / capital gains イベントが取得でき、adjusted close は配当や分割を反映する前提で使われます。Alpha Vantage も `TIME_SERIES_DAILY_ADJUSTED` で adjusted close, dividend, split を返します。[GitHub+1](https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/history.py?utm_source=chatgpt.com)
*   **暗号資産**: 取引所 API を直接叩くか、`ccxt` で統一的に取るのが一般的です。`ccxt` は `fetchOHLCV` を共通APIとして提供し、さらに funding rate 系のAPIも仕様に含みます。集約系としては CoinGecko があり、historical market chart API を提供しています。[CoinGecko API+4CCXT Documentation+4CCXT Documentation+4](https://docs.ccxt.com/?utm_source=chatgpt.com)

ただし、あなたの要件だと重要なのは「どこで取るか」よりも、**研究エンジンの基準価格を何にするか** です。  
ETF は **トータルリターン相当の系列** を明示的に使わないと、配当込み戦略の比較が崩れます。一方、暗号資産スポットは通常、分割や配当の概念がないので、基本は価格系列で足りますが、先物・perpetual を扱うなら **funding を別途加算/控除** しないと総収益になりません。[アルファバンテージ+1](https://www.alphavantage.co/documentation/?utm_source=chatgpt.com)

research engine の設計方針
---------------------

あなたの要件に合うのは、イベント駆動ではなく、**時点 t までの情報だけで t+1 以降のポジションを決める配列ベースの研究エンジン** です。  
設計としては次の切り分けが最も安定します。

### 1\. DataBundle

戦略共通の入力を束ねます。

```
@dataclass
class DataBundle:
    prices: pd.DataFrame          # 基準価格（ETFはTR相当、cryptoはclose等）
    open_: pd.DataFrame | None
    high: pd.DataFrame | None
    low: pd.DataFrame | None
    volume: pd.DataFrame | None
    returns: pd.DataFrame         # prices から計算するか、外部供給
    funding: pd.DataFrame | None  # perpetual用
    borrow_cost: pd.DataFrame | None
    metadata: pd.DataFrame | None
    calendar: pd.DatetimeIndex
```

ここで重要なのは、**戦略が直接データ取得しない**ことです。  
必ず `DataBundle` を介して渡すと、戦略比較時の条件差を防げます。

### 2\. Strategy

戦略は **signal か target weight を返すだけ** にします。

```
class BaseStrategy(ABC):
    @abstractmethod
    def generate_signals(self, data: DataBundle) -> pd.DataFrame:
        ...

    def generate_target_weights(self, data: DataBundle) -> pd.DataFrame:
        signals = self.generate_signals(data)
        return signals
```

ここでは注文も約定も扱いません。  
研究エンジンでは「何を持ちたいか」だけ返せば十分です。

### 3\. Portfolio construction

signal をウェイトに変換する層を戦略から分離します。

```
class BaseAllocator(ABC):
    @abstractmethod
    def allocate(self, signals: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        ...
```

これを分けると、

*   同じ signal で equal weight と vol scaling を比較する
*   同じ alpha で long-only 制約だけ変える
*   ETF と crypto で同じ alpha を別アロケータに流す

といった比較がきれいにできます。

### 4\. Simulator

研究エンジン側でリターンを計算します。

```
class ResearchBacktester:
    def run(self, data, weights, fee_bps=0.0):
        w = weights.shift(1)  # t時点の情報で t+1 を持つ
        asset_ret = data.returns.copy()

        if data.funding is not None:
            asset_ret = asset_ret.add(data.funding, fill_value=0.0)

        turnover = (w - w.shift(1)).abs().sum(axis=1).fillna(0.0)
        fee = turnover * fee_bps / 1e4

        port_ret = (w * asset_ret).sum(axis=1) - fee
        equity = (1.0 + port_ret.fillna(0.0)).cumprod()

        return {
            "weights": w,
            "turnover": turnover,
            "returns": port_ret,
            "equity": equity,
        }
```

この `weights.shift(1)` がリーク防止の基本です。  
signal を当日終値で作ったなら、その signal は **翌バーからしか使えない** ように固定します。

* * *

リークなしで比較しやすくするための実務ルール
----------------------

research engine で本当に大事なのはここです。

### 1\. 特徴量は必ず過去情報だけ

rolling mean, rolling vol, momentum などは、計算自体は t 時点まででよいですが、  
**実際に売買に使うのは t+1** に固定します。

つまり原則は、

*   特徴量: `feature_t = f(price_<=t)`
*   ポジション: `weight_{t+1} = g(feature_t)`

です。

### 2\. forward return は評価専用

クロスセクションで signal の有効性を見るとき、`future_return = return.shift(-1)` を使うことがありますが、これは **評価用テーブルだけ** に限定します。  
戦略生成ロジックに混ぜないことが重要です。

### 3\. ユニバース決定も時点整合

ETF でありがちな漏れはこれです。  
今存在している ETF の一覧を過去全期間に使うと survivorship bias が入ります。  
理想は **当時上場していた銘柄のみ** をその日時点でユニバースに含めることです。

無料データだけでこれを厳密にやるのは難しいので、初期版では

*   研究対象 ETF を事前固定
*   上場前は NaN
*   一定の有効履歴長がある銘柄だけ売買対象化

という運用が現実的です。

### 4\. データ前処理と戦略を分離

欠損補完、営業日合わせ、価格調整、リターン計算はエンジン側で統一し、  
戦略側ではそれを一切やらないのがよいです。

### 5\. 比較は同一 evaluator を通す

全戦略を同じ評価指標で並べます。

最低限:

*   CAGR
*   Volatility
*   Sharpe
*   Max Drawdown
*   Calmar
*   Turnover
*   Hit ratio
*   Exposure / average gross exposure

* * *

ETF データは何を使うべきか
---------------

あなたの条件だと、無料かつ実用的な第一候補は **Yahoo Finance 系** です。  
理由は、historical prices に加えて dividends / stock splits / capital gains イベントが取得できるためです。`yfinance` の実装でも ETF / MUTUALFUND に対して capital gains イベント取得を含むコードパスがあります。[GitHub+1](https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/history.py?utm_source=chatgpt.com)

ただし、注意点があります。

*   Yahoo 系で一般に使うのは **Adjusted Close ベースのリターン** です。これは splits と dividends、場合によっては capital gains distributions を反映した価格系列として扱われます。[GitHub+2GitHub+2](https://github.com/ranaroussi/yfinance/issues/1749?utm_source=chatgpt.com)
*   ただし **OHLC 全部が完全な total return 系列になるわけではありません**。研究エンジンで必要なのが日次リターン比較なら、まずは `Adj Close` からリターンを計算するのが定石です。[アルファバンテージ+1](https://www.alphavantage.co/documentation/?utm_source=chatgpt.com)
*   無料データなので、稀に corporate actions や欠損に癖があります。したがって、分配金が大きい ETF では `Dividends` 列と整合チェックをかけるのが安全です。[GitHub+1](https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/history.py?utm_source=chatgpt.com)

**実務的な推奨** はこうです。

*   **研究の基準価格**: `Adj Close`
*   **検算用**: `Close`, `Dividends`, `Stock Splits`, `Capital Gains`
*   **OHLC が必要な場合**: 売買価格は raw OHLC を使い、評価リターンは adjusted close ベースで別管理

これは少し不格好に見えますが、無料データでは一番壊れにくいです。

Alpha Vantage も無料枠があり、`TIME_SERIES_DAILY_ADJUSTED` が split/dividend-adjusted data と historical split/dividend events を返します。  
ただし、無料枠のレート制限は Yahoo 系より扱いづらい場面があります。[アルファバンテージ+1](https://www.alphavantage.co/documentation/?utm_source=chatgpt.com)

### ETF についての結論

無料・高品質・Python で扱いやすい、という条件なら

1.  **第一候補: Yahoo Finance + yfinance**
2.  **補助候補: Alpha Vantage**
3.  **研究エンジンの基準は Adj Close ベース**

が最も一般的です。[アルファバンテージ+1](https://www.alphavantage.co/documentation/?utm_source=chatgpt.com)

* * *

暗号資産データは何を使うべきか
---------------

暗号資産は ETF と違い、「トータルリターン」の意味が商品タイプで変わります。

### spot

BTC/USDT のような現物なら、通常は **価格リターン = 総収益の基礎** です。  
配当や分割がないので、OHLCV が取れれば足ります。

この用途なら、一般的には **CCXT で取引所 API を統一的に使う** のが王道です。  
CCXT は `fetchOHLCV` を共通APIとして持ち、複数取引所を同一コードで扱えます。[CCXT Documentation+1](https://docs.ccxt.com/?utm_source=chatgpt.com)

### perpetual futures

perp では **funding** があるため、単純な価格リターンだけでは総収益になりません。  
CCXT の base spec には funding rate 関連のメソッドが定義されています。したがって perp を研究対象にするなら、  
`close-to-close return + realized funding`  
を総収益とみなす設計が必要です。[CCXT Documentation+1](https://docs.ccxt.com/baseSpec?utm_source=chatgpt.com)

### CoinGecko の位置づけ

CoinGecko は無料で historical market chart を提供するので、**集約価格で広い universe を雑に見る研究** には便利です。  
ただし execution-grade というよりは aggregator なので、戦略バックテストの基準価格としては、実際に売買を想定する venue の OHLCV の方が自然です。[CoinGecko API+2CoinGecko API+2](https://docs.coingecko.com/?utm_source=chatgpt.com)

### 暗号資産についての結論

*   **spot の研究**: CCXT + 代表取引所（Binance, Coinbase, OKX など）OHLCV
*   **perp の研究**: CCXT の OHLCV + funding 系列
*   **広く横断的に見る一次調査**: CoinGecko

* * *

あなた向けの現実的なデータ運用案
----------------

一番壊れにくいのは次です。

### ETF

*   ソース: `yfinance`
*   主系列: `Adj Close`
*   補助列: `Close`, `Dividends`, `Stock Splits`, `Capital Gains`
*   リターン: `Adj Close.pct_change()`
*   売買価格が必要なら raw `Open` / `Close` を別持ち

### Crypto spot

*   ソース: `ccxt` で特定取引所の OHLCV
*   主系列: `Close`
*   リターン: `Close.pct_change()`
*   取引所は固定する。研究中に venue を混ぜない

### Crypto perp

*   ソース: `ccxt`
*   主系列: `Close`
*   追加系列: `Funding`
*   リターン: `Close return + funding contribution`

この切り方なら、最終的に両者とも

```
returns[t, asset]
weights[t, asset]
```

の共通形式に落ちます。

* * *

research engine の最小インターフェース
---------------------------

あなたの用途なら、これで十分です。

```
class BaseStrategy:
    def prepare_features(self, data: DataBundle) -> dict[str, pd.DataFrame]:
        return {}

    def generate_scores(self, data: DataBundle, features: dict[str, pd.DataFrame]) -> pd.DataFrame:
        raise NotImplementedError

class BaseAllocator:
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        raise NotImplementedError

class ResearchBacktester:
    def run(self, strategy, allocator, data: DataBundle) -> BacktestResult:
        feats = strategy.prepare_features(data)
        scores = strategy.generate_scores(data, feats)
        weights = allocator.allocate(scores, data)
        return self.simulate(weights, data)
```

これにしておくと、戦略比較は

*   Strategy だけ差し替え
*   Allocator だけ差し替え
*   同じ DataBundle と Evaluator を共通利用

で完結します。

* * *

実装上の重要な注意
---------

ETF の「トータルリターン」について、無料データで**厳密な指数ベンダー級TR** を常に保証するのは難しいです。  
無料で現実的に最も近いのは **Adjusted Close ベース** です。これで日次研究はかなり実用になりますが、厳密なベンダーTR指数と完全一致するとは限りません。[アルファバンテージ+2GitHub+2](https://www.alphavantage.co/documentation/?utm_source=chatgpt.com)

暗号資産についても、取引所間で価格・出来高・上場時期が異なるため、**取引所をまたいだ series の混合** は避けた方が安全です。集約データは universe survey 用、バックテスト本体は venue 固定が無難です。これは CoinGecko のような aggregator と、CCXT を通じた venue-direct data の使い分けとして理解すると整理しやすいです。[CoinGecko API+2CoinGecko API+2](https://docs.coingecko.com/?utm_source=chatgpt.com)

必要なら次に、  
**この方針に沿った Python の research engine の雛形** を、`BaseStrategy / BaseAllocator / ResearchBacktester / DataLoader(yfinance+ccxt)` まで含めて、そのまま動く形で出します。

## Prompt:
この方針に沿った Python の research engine の雛形 を、BaseStrategy / BaseAllocator / ResearchBacktester / DataLoader(yfinance+ccxt) まで含めて、そのまま動く形で出して

## Response:
研究用に割り切って、リーク防止・比較容易性・データ取得の統一に焦点を当てた最小構成でまとめます。ETF は `yfinance` の `Adj Close` を基準、暗号資産は `ccxt` の OHLCV を基準にして、両方とも `DataBundle -> Strategy -> Allocator -> Backtester` に落とします。

思考時間: 4s

以下は、そのまま動くことを意識した **research engine の最小雛形** です。  
目的は次の4点です。

*   ETF / crypto を同じ `DataBundle` 形式に統一
*   戦略は `BaseStrategy` を継承して差し替えるだけ
*   アロケーションは `BaseAllocator` を差し替えるだけ
*   `ResearchBacktester` が **リークなし** で評価する

初期版なので、イベント駆動や複雑約定は入れていません。  
その代わり、研究用途で重要な

*   `weights.shift(1)` による時点整合
*   `Adj Close` ベースの ETF リターン
*   crypto の funding 加算余地
*   共通 evaluator

をきちんと入れています。

* * *

依存関係
----

```
pip install pandas numpy yfinance ccxt
```

* * *

フルコード
-----

```
from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd
import yfinance as yf
import ccxt

# ============================================================
# Data container
# ============================================================

@dataclass
class DataBundle:
    prices: pd.DataFrame                  # 基準価格（ETF: Adj Close, Crypto: Close）
    returns: pd.DataFrame                 # 基準価格からのリターン
    open_: Optional[pd.DataFrame] = None
    high: Optional[pd.DataFrame] = None
    low: Optional[pd.DataFrame] = None
    close: Optional[pd.DataFrame] = None
    volume: Optional[pd.DataFrame] = None
    funding: Optional[pd.DataFrame] = None
    borrow_cost: Optional[pd.DataFrame] = None
    metadata: Optional[pd.DataFrame] = None
    asset_class: str = "unknown"          # "etf" / "crypto"
    frequency: str = "1d"

    @property
    def calendar(self) -> pd.DatetimeIndex:
        return self.prices.index

# ============================================================
# Utilities
# ============================================================

def ensure_2d_frame(df: pd.DataFrame | pd.Series, name: str) -> pd.DataFrame:
    if isinstance(df, pd.Series):
        return df.to_frame(name=name)
    return df.copy()

def sanitize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.sort_index().copy()
    prices = prices.replace([np.inf, -np.inf], np.nan)
    return prices

def compute_returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = sanitize_prices(prices)
    rets = prices.pct_change()
    rets = rets.replace([np.inf, -np.inf], np.nan)
    return rets

def align_like(df: Optional[pd.DataFrame], index: pd.Index, columns: pd.Index) -> Optional[pd.DataFrame]:
    if df is None:
        return None
    return df.reindex(index=index, columns=columns)

def annualization_factor(frequency: str) -> int:
    mapping = {
        "1d": 252,
        "1h": 24 * 365,
        "4h": 6 * 365,
        "1w": 52,
        "1m": 12,
    }
    return mapping.get(frequency, 252)

# ============================================================
# Data Loader
# ============================================================

class DataLoader:
    """
    ETF は yfinance、crypto は ccxt から取得して DataBundle に統一する。
    """

    @staticmethod
    def load_etf_yfinance(
        tickers: list[str],
        start: str,
        end: Optional[str] = None,
        auto_adjust: bool = False,
        progress: bool = False,
    ) -> DataBundle:
        """
        ETF 用。
        - prices は Adj Close を基準系列に使う
        - returns は Adj Close から計算
        - open/high/low/close/volume も保持
        """
        if len(tickers) == 0:
            raise ValueError("tickers must not be empty.")

        raw = yf.download(
            tickers=tickers,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
            progress=progress,
            group_by="column",
            actions=True,
            threads=True,
        )

        if raw.empty:
            raise ValueError("No data downloaded from yfinance.")

        # 単一銘柄と複数銘柄で列構造が違うため吸収
        def _extract_field(field: str) -> Optional[pd.DataFrame]:
            if isinstance(raw.columns, pd.MultiIndex):
                if field in raw.columns.get_level_values(0):
                    out = raw[field].copy()
                    if isinstance(out, pd.Series):
                        out = out.to_frame()
                    out = out.reindex(columns=tickers)
                    return out
                return None
            else:
                if field in raw.columns:
                    out = raw[[field]].copy()
                    out.columns = tickers[:1]
                    return out
                return None

        open_ = _extract_field("Open")
        high = _extract_field("High")
        low = _extract_field("Low")
        close = _extract_field("Close")
        adj_close = _extract_field("Adj Close")
        volume = _extract_field("Volume")

        if adj_close is None:
            # 念のため fallback
            if close is None:
                raise ValueError("Neither Adj Close nor Close is available from yfinance.")
            prices = close.copy()
        else:
            prices = adj_close.copy()

        prices = sanitize_prices(prices)
        returns = compute_returns_from_prices(prices)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            funding=None,
            borrow_cost=None,
            metadata=None,
            asset_class="etf",
            frequency="1d",
        )

    @staticmethod
    def load_crypto_ccxt(
        exchange_name: str,
        symbols: list[str],
        timeframe: str = "1d",
        since: Optional[str] = None,
        limit: int = 1000,
        funding_rate_fn=None,
    ) -> DataBundle:
        """
        Crypto 用。
        - prices は Close
        - returns は Close から計算
        - funding_rate_fn(exchange, symbol, index) -> pd.Series を渡せば funding を追加可能
        """
        if len(symbols) == 0:
            raise ValueError("symbols must not be empty.")

        exchange_cls = getattr(ccxt, exchange_name, None)
        if exchange_cls is None:
            raise ValueError(f"Unknown ccxt exchange: {exchange_name}")

        exchange = exchange_cls({"enableRateLimit": True})

        since_ms = None
        if since is not None:
            since_ms = int(pd.Timestamp(since, tz="UTC").timestamp() * 1000)

        opens = {}
        highs = {}
        lows = {}
        closes = {}
        volumes = {}
        funding_map = {}

        for symbol in symbols:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if not ohlcv:
                raise ValueError(f"No OHLCV data returned for {symbol} from {exchange_name}.")

            df = pd.DataFrame(
                ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
            df = df.set_index("timestamp").sort_index()

            opens[symbol] = df["open"]
            highs[symbol] = df["high"]
            lows[symbol] = df["low"]
            closes[symbol] = df["close"]
            volumes[symbol] = df["volume"]

            if funding_rate_fn is not None:
                f = funding_rate_fn(exchange, symbol, df.index)
                if f is not None:
                    funding_map[symbol] = f.reindex(df.index)

        open_df = pd.DataFrame(opens).sort_index()
        high_df = pd.DataFrame(highs).sort_index()
        low_df = pd.DataFrame(lows).sort_index()
        close_df = pd.DataFrame(closes).sort_index()
        volume_df = pd.DataFrame(volumes).sort_index()

        prices = sanitize_prices(close_df)
        returns = compute_returns_from_prices(prices)

        funding_df = None
        if len(funding_map) > 0:
            funding_df = pd.DataFrame(funding_map).sort_index().reindex_like(prices)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_df,
            high=high_df,
            low=low_df,
            close=close_df,
            volume=volume_df,
            funding=funding_df,
            borrow_cost=None,
            metadata=None,
            asset_class="crypto",
            frequency=timeframe,
        )

# ============================================================
# Strategy base
# ============================================================

class BaseStrategy(ABC):
    """
    戦略は DataBundle を受けて scores を返す。
    scores は各時点・各資産の相対的な魅力度。
    最終的なウェイトへの変換は Allocator に任せる。
    """

    def prepare_features(self, data: DataBundle) -> Dict[str, pd.DataFrame]:
        return {}

    @abstractmethod
    def generate_scores(
        self,
        data: DataBundle,
        features: Dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        raise NotImplementedError

class BuyAndHoldStrategy(BaseStrategy):
    """
    常に全資産を等しく好むスコアを返す。
    """
    def generate_scores(self, data: DataBundle, features: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        scores = pd.DataFrame(1.0, index=data.calendar, columns=data.prices.columns)
        scores = scores.where(data.prices.notna())
        return scores

class CrossSectionalMomentumStrategy(BaseStrategy):
    """
    単純なクロスセクション・モメンタム。
    - lookback 日の累積リターンで順位付け
    - 直近 skip 日を除外
    - 返すのはスコアのみ
    """
    def __init__(self, lookback: int = 126, skip: int = 21, min_history: Optional[int] = None):
        self.lookback = lookback
        self.skip = skip
        self.min_history = min_history if min_history is not None else lookback + skip

    def prepare_features(self, data: DataBundle) -> Dict[str, pd.DataFrame]:
        px = data.prices.copy()

        # t 時点で使うシグナルとして、
        # [t-lookback-skip+1, ..., t-skip] の価格変化を見る
        past = px.shift(self.skip)
        mom = past / past.shift(self.lookback) - 1.0

        valid_hist = px.notna().rolling(self.min_history).sum() >= self.min_history
        mom = mom.where(valid_hist)

        return {"momentum": mom}

    def generate_scores(
        self,
        data: DataBundle,
        features: Dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        scores = features["momentum"].copy()
        scores = scores.where(data.prices.notna())
        return scores

# ============================================================
# Allocator base
# ============================================================

class BaseAllocator(ABC):
    @abstractmethod
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        raise NotImplementedError

class EqualWeightAllocator(BaseAllocator):
    """
    有効資産に等ウェイト。
    スコアの大きさではなく、有効かどうかだけを見る。
    """
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        valid = scores.notna() & data.prices.notna()
        denom = valid.sum(axis=1).replace(0, np.nan)
        weights = valid.astype(float).div(denom, axis=0)
        return weights.fillna(0.0)

class TopKLongOnlyAllocator(BaseAllocator):
    """
    各時点でスコア上位 k 銘柄を等ウェイトで保有。
    """
    def __init__(self, k: int = 3):
        if k <= 0:
            raise ValueError("k must be positive.")
        self.k = k

    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        scores = scores.where(data.prices.notna())

        ranks = scores.rank(axis=1, ascending=False, method="first")
        selected = ranks <= self.k

        denom = selected.sum(axis=1).replace(0, np.nan)
        weights = selected.astype(float).div(denom, axis=0)
        return weights.fillna(0.0)

class ScoreProportionalLongOnlyAllocator(BaseAllocator):
    """
    正のスコアのみを使って長期保有ウェイトにする。
    """
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        s = scores.clip(lower=0.0)
        s = s.where(data.prices.notna())

        denom = s.sum(axis=1).replace(0, np.nan)
        weights = s.div(denom, axis=0)
        return weights.fillna(0.0)

# ============================================================
# Result container
# ============================================================

@dataclass
class BacktestResult:
    weights_raw: pd.DataFrame             # allocator が返した元のウェイト
    weights_executed: pd.DataFrame        # shift 後の実際保有ウェイト
    asset_returns_gross: pd.DataFrame     # funding 等込みの資産リターン
    portfolio_returns: pd.Series
    equity_curve: pd.Series
    turnover: pd.Series
    fees: pd.Series
    stats: pd.Series

# ============================================================
# Backtester
# ============================================================

class ResearchBacktester:
    """
    research engine:
    - t 時点の情報から weights_raw[t] を出す
    - 実際の保有は weights_executed[t] = weights_raw[t-1]
    - これにより look-ahead を防ぐ
    """

    def __init__(
        self,
        fee_bps: float = 0.0,
        annualization: Optional[int] = None,
    ):
        self.fee_bps = fee_bps
        self.annualization = annualization

    def run(
        self,
        strategy: BaseStrategy,
        allocator: BaseAllocator,
        data: DataBundle,
    ) -> BacktestResult:
        features = strategy.prepare_features(data)
        scores = strategy.generate_scores(data, features)

        scores = scores.reindex(index=data.calendar, columns=data.prices.columns)
        weights_raw = allocator.allocate(scores, data)
        weights_raw = weights_raw.reindex(index=data.calendar, columns=data.prices.columns).fillna(0.0)

        # リーク防止: t 時点で決めたウェイトは t+1 に保有開始
        weights_executed = weights_raw.shift(1).fillna(0.0)

        asset_returns_gross = data.returns.copy()
        if data.funding is not None:
            asset_returns_gross = asset_returns_gross.add(
                data.funding.reindex_like(asset_returns_gross).fillna(0.0),
                fill_value=0.0
            )

        if data.borrow_cost is not None:
            asset_returns_gross = asset_returns_gross.sub(
                data.borrow_cost.reindex_like(asset_returns_gross).fillna(0.0),
                fill_value=0.0
            )

        turnover = (weights_executed - weights_executed.shift(1).fillna(0.0)).abs().sum(axis=1)
        fees = turnover * (self.fee_bps / 1e4)

        portfolio_returns = (weights_executed * asset_returns_gross.fillna(0.0)).sum(axis=1) - fees
        equity_curve = (1.0 + portfolio_returns.fillna(0.0)).cumprod()

        stats = self.compute_stats(
            portfolio_returns=portfolio_returns,
            equity_curve=equity_curve,
            turnover=turnover,
            frequency=data.frequency,
        )

        return BacktestResult(
            weights_raw=weights_raw,
            weights_executed=weights_executed,
            asset_returns_gross=asset_returns_gross,
            portfolio_returns=portfolio_returns,
            equity_curve=equity_curve,
            turnover=turnover,
            fees=fees,
            stats=stats,
        )

    def compute_stats(
        self,
        portfolio_returns: pd.Series,
        equity_curve: pd.Series,
        turnover: pd.Series,
        frequency: str,
    ) -> pd.Series:
        r = portfolio_returns.dropna()
        if len(r) == 0:
            return pd.Series(dtype=float)

        ann = self.annualization if self.annualization is not None else annualization_factor(frequency)

        mean_ret = r.mean()
        vol = r.std(ddof=0)
        ann_ret = (1.0 + r).prod() ** (ann / max(len(r), 1)) - 1.0
        ann_vol = vol * np.sqrt(ann) if pd.notna(vol) else np.nan
        sharpe = (mean_ret / vol) * np.sqrt(ann) if vol not in [0, np.nan] and vol > 0 else np.nan

        running_max = equity_curve.cummax()
        drawdown = equity_curve / running_max - 1.0
        max_dd = drawdown.min()

        calmar = ann_ret / abs(max_dd) if pd.notna(max_dd) and max_dd < 0 else np.nan
        hit_ratio = (r > 0).mean()
        avg_turnover = turnover.mean()

        out = pd.Series(
            {
                "total_return": equity_curve.iloc[-1] - 1.0,
                "annual_return": ann_ret,
                "annual_volatility": ann_vol,
                "sharpe": sharpe,
                "max_drawdown": max_dd,
                "calmar": calmar,
                "hit_ratio": hit_ratio,
                "average_turnover": avg_turnover,
                "num_periods": len(r),
            }
        )
        return out

# ============================================================
# Example usage
# ============================================================

def example_etf():
    tickers = ["SPY", "QQQ", "IWM", "TLT", "GLD"]

    data = DataLoader.load_etf_yfinance(
        tickers=tickers,
        start="2018-01-01",
        end=None,
        auto_adjust=False,   # Adj Close を明示利用するため False のまま
        progress=False,
    )

    strategy = CrossSectionalMomentumStrategy(
        lookback=126,
        skip=21,
        min_history=147,
    )
    allocator = TopKLongOnlyAllocator(k=2)
    bt = ResearchBacktester(fee_bps=5.0)

    result = bt.run(strategy, allocator, data)

    print("=== ETF Stats ===")
    print(result.stats.round(4))
    print()
    print("Equity tail:")
    print(result.equity_curve.tail())
    print()
    print("Executed weights tail:")
    print(result.weights_executed.tail())

def example_crypto():
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    data = DataLoader.load_crypto_ccxt(
        exchange_name="binance",
        symbols=symbols,
        timeframe="1d",
        since="2022-01-01",
        limit=1000,
        funding_rate_fn=None,   # perp 用ならここに関数を渡す
    )

    strategy = CrossSectionalMomentumStrategy(
        lookback=60,
        skip=7,
        min_history=67,
    )
    allocator = TopKLongOnlyAllocator(k=1)
    bt = ResearchBacktester(fee_bps=10.0)

    result = bt.run(strategy, allocator, data)

    print("=== Crypto Stats ===")
    print(result.stats.round(4))
    print()
    print("Equity tail:")
    print(result.equity_curve.tail())
    print()
    print("Executed weights tail:")
    print(result.weights_executed.tail())

if __name__ == "__main__":
    # ETF 例
    example_etf()

    # Crypto 例
    # 取引所APIの制限や接続環境によっては時間がかかることがあります
    # example_crypto()
```

* * *

この雛形のポイント
---------

### 1\. リーク防止

ここが一番重要です。

```
weights_executed = weights_raw.shift(1).fillna(0.0)
```

これにより、時点 `t` までの情報で作ったシグナルは、必ず `t+1` 以降の保有にしか使われません。  
research engine ではこれを固定ルールにするのが安全です。

* * *

### 2\. ETF は `Adj Close` を基準価格にしている

`yfinance` で取得した `Adj Close` を `prices` に使っています。

```
prices = adj_close.copy()
returns = compute_returns_from_prices(prices)
```

これにより、少なくとも日次研究用途としては、分割・配当の影響をある程度反映した系列で比較できます。  
一方で、`Open/High/Low/Close` も別で保持しているので、将来的に

*   翌日寄りで約定
*   Close-to-Close ではなく Open-to-Close で評価
*   gap を考慮

といった拡張もしやすいです。

* * *

### 3\. crypto は `ccxt` で統一

crypto は取引所ごとの差が大きいので、研究時点では **取引所固定** が基本です。

```
data = DataLoader.load_crypto_ccxt(
    exchange_name="binance",
    symbols=["BTC/USDT", "ETH/USDT"],
    timeframe="1d",
    since="2022-01-01",
)
```

こうすると、ETF 側と同様に `DataBundle` に統一されます。

* * *

### 4\. funding を後付けできる

perpetual を将来扱うために、`funding` 列を差し込める形にしています。

```
if data.funding is not None:
    asset_returns_gross = asset_returns_gross.add(data.funding, fill_value=0.0)
```

つまり、

*   spot: `returns` のみ
*   perp: `returns + funding`

という整理で統一できます。

* * *

### 5\. 戦略とアロケータを分離

戦略はスコアだけ返し、ウェイト変換は allocator 側に寄せています。

そのため、

*   同じモメンタム戦略を TopK と ScoreProportional で比較
*   同じ allocator で別の alpha を比較

が簡単です。

* * *

まず追加したい拡張
---------

この最小版の次に、実務上ほぼ確実に欲しくなるのは次です。

### A. リバランス頻度制御

現状は毎バーでウェイト更新です。  
月次・週次に限定したいなら、`rebalance_mask` を持たせて、その日だけ `weights_raw` を更新する設計にします。

### B. 유니バース制御

ETF の上場前データや履歴不足を考慮して、

*   最低観測日数
*   最低売買代金
*   欠損率フィルタ

を入れるとかなり安定します。

### C. ベンチマーク比較

`SPY` や `BTC/USDT` を benchmark として別保持し、  
active return / information ratio まで出すと比較しやすくなります。

### D. walk-forward / train-test split

research engine では必須に近いです。  
ただし今回は「雛形をそのまま動く形で」という目的に絞って入れていません。

* * *

このままだと未対応な点
-----------

正直に言うと、この雛形は **研究用の最小版** です。未対応なのは次です。

*   intraday の厳密な約定
*   maker/taker 区別
*   部分約定
*   crypto perp の funding 自動取得実装
*   survivorship bias の厳密除去
*   ベンダー級 total return index の完全再現
*   multi-currency のFX換算

ただし、あなたが今目指している  
「時系列データを渡し、戦略だけオーバーライドして比較する」  
という目的には十分な骨格になっています。

* * *

次にやるなら、これをベースに  
**月次/週次リバランス対応、benchmark 比較、walk-forward 評価、signal/weight の可視化**  
まで拡張すると、かなり使える研究基盤になります。

## Prompt:
お願いします

## Response:
月次/週次リバランス、benchmark 比較、walk-forward をまとめて載せます。研究用途でそのまま回せるよう、前回の骨格を保ったまま拡張します。

思考時間: 数秒

以下は前回の雛形を拡張して、

*   月次 / 週次 / 日次リバランス
*   benchmark 比較
*   walk-forward 評価
*   signal / weight / equity の可視化

まで含めた **research engine の実用版テンプレート** です。

設計方針は前回と同じで、戦略は `BaseStrategy`、配分は `BaseAllocator` を差し替えるだけです。  
今回の追加点は、`ResearchBacktester` に

*   `rebalance_rule`
*   `benchmark_returns`
*   `walk_forward`

を入れたことです。

* * *

依存関係
----

```
pip install pandas numpy matplotlib yfinance ccxt
```

* * *

フルコード
-----

```
from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import ccxt

# ============================================================
# Data container
# ============================================================

@dataclass
class DataBundle:
    prices: pd.DataFrame
    returns: pd.DataFrame
    open_: Optional[pd.DataFrame] = None
    high: Optional[pd.DataFrame] = None
    low: Optional[pd.DataFrame] = None
    close: Optional[pd.DataFrame] = None
    volume: Optional[pd.DataFrame] = None
    funding: Optional[pd.DataFrame] = None
    borrow_cost: Optional[pd.DataFrame] = None
    metadata: Optional[pd.DataFrame] = None
    benchmark_returns: Optional[pd.Series] = None
    asset_class: str = "unknown"
    frequency: str = "1d"

    @property
    def calendar(self) -> pd.DatetimeIndex:
        return self.prices.index

# ============================================================
# Result containers
# ============================================================

@dataclass
class BacktestResult:
    scores: pd.DataFrame
    weights_raw: pd.DataFrame
    weights_executed: pd.DataFrame
    asset_returns_gross: pd.DataFrame
    portfolio_returns: pd.Series
    benchmark_returns: Optional[pd.Series]
    active_returns: Optional[pd.Series]
    equity_curve: pd.Series
    benchmark_equity_curve: Optional[pd.Series]
    active_equity_curve: Optional[pd.Series]
    turnover: pd.Series
    fees: pd.Series
    rebalance_mask: pd.Series
    stats: pd.Series

@dataclass
class WalkForwardSliceResult:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    result: BacktestResult

@dataclass
class WalkForwardResult:
    slices: List[WalkForwardSliceResult]
    stitched_returns: pd.Series
    stitched_equity_curve: pd.Series
    stitched_benchmark_returns: Optional[pd.Series]
    stitched_active_returns: Optional[pd.Series]
    stats: pd.Series

# ============================================================
# Utilities
# ============================================================

def sanitize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy().sort_index()
    prices = prices.replace([np.inf, -np.inf], np.nan)
    return prices

def compute_returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = sanitize_prices(prices)
    returns = prices.pct_change()
    returns = returns.replace([np.inf, -np.inf], np.nan)
    return returns

def annualization_factor(frequency: str) -> int:
    mapping = {
        "1d": 252,
        "1h": 24 * 365,
        "4h": 6 * 365,
        "1w": 52,
        "1m": 12,
    }
    return mapping.get(frequency, 252)

def _normalize_columns(df: pd.DataFrame, expected_cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    out = out.reindex(columns=expected_cols)
    return out

def make_rebalance_mask(index: pd.DatetimeIndex, rule: str = "D") -> pd.Series:
    """
    rule:
      - 'D'      : 毎バー
      - 'W-FRI'  : 週次（金曜）
      - 'M'      : 月末営業日
      - 'Q'      : 四半期末
    """
    idx = pd.DatetimeIndex(index)
    mask = pd.Series(False, index=idx)

    if rule == "D":
        mask[:] = True
        return mask

    if rule.startswith("W-"):
        grp = idx.to_series().dt.to_period("W-" + rule.split("-")[1])
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    if rule == "M":
        grp = idx.to_series().dt.to_period("M")
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    if rule == "Q":
        grp = idx.to_series().dt.to_period("Q")
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    raise ValueError("Unsupported rebalance rule. Use 'D', 'W-FRI', 'M', or 'Q'.")

def apply_rebalance_rule(weights_raw: pd.DataFrame, rebalance_mask: pd.Series) -> pd.DataFrame:
    """
    リバランス日だけ新しい weights_raw を採用し、それ以外は前回値を維持。
    """
    weights_raw = weights_raw.copy()
    rebalance_mask = rebalance_mask.reindex(weights_raw.index).fillna(False)

    out = pd.DataFrame(index=weights_raw.index, columns=weights_raw.columns, dtype=float)

    prev = pd.Series(0.0, index=weights_raw.columns)
    for dt in weights_raw.index:
        if rebalance_mask.loc[dt]:
            w = weights_raw.loc[dt].fillna(0.0)
            s = w.sum()
            if s > 0:
                prev = w / s
            else:
                prev = pd.Series(0.0, index=weights_raw.columns)
        out.loc[dt] = prev

    return out.fillna(0.0)

def compute_drawdown(equity_curve: pd.Series) -> pd.Series:
    running_max = equity_curve.cummax()
    return equity_curve / running_max - 1.0

# ============================================================
# Data loaders
# ============================================================

class DataLoader:
    @staticmethod
    def load_etf_yfinance(
        tickers: list[str],
        start: str,
        end: Optional[str] = None,
        benchmark_ticker: Optional[str] = None,
        auto_adjust: bool = False,
        progress: bool = False,
    ) -> DataBundle:
        if len(tickers) == 0:
            raise ValueError("tickers must not be empty")

        raw = yf.download(
            tickers=tickers,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
            progress=progress,
            group_by="column",
            actions=True,
            threads=True,
        )

        if raw.empty:
            raise ValueError("No ETF data downloaded.")

        def _extract_field(field: str) -> Optional[pd.DataFrame]:
            if isinstance(raw.columns, pd.MultiIndex):
                if field in raw.columns.get_level_values(0):
                    out = raw[field].copy()
                    if isinstance(out, pd.Series):
                        out = out.to_frame()
                    out = out.reindex(columns=tickers)
                    return out
                return None
            else:
                if field in raw.columns:
                    out = raw[[field]].copy()
                    out.columns = tickers[:1]
                    return out
                return None

        open_ = _extract_field("Open")
        high = _extract_field("High")
        low = _extract_field("Low")
        close = _extract_field("Close")
        adj_close = _extract_field("Adj Close")
        volume = _extract_field("Volume")

        prices = adj_close.copy() if adj_close is not None else close.copy()
        prices = sanitize_prices(prices)
        returns = compute_returns_from_prices(prices)

        benchmark_returns = None
        if benchmark_ticker is not None:
            bench = yf.download(
                tickers=benchmark_ticker,
                start=start,
                end=end,
                auto_adjust=auto_adjust,
                progress=progress,
                group_by="column",
                actions=True,
                threads=True,
            )
            if not bench.empty:
                if isinstance(bench.columns, pd.MultiIndex):
                    if "Adj Close" in bench.columns.get_level_values(0):
                        bench_px = bench["Adj Close"].iloc[:, 0]
                    else:
                        bench_px = bench["Close"].iloc[:, 0]
                else:
                    bench_px = bench["Adj Close"] if "Adj Close" in bench.columns else bench["Close"]
                benchmark_returns = bench_px.sort_index().pct_change().reindex(prices.index)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            funding=None,
            borrow_cost=None,
            metadata=None,
            benchmark_returns=benchmark_returns,
            asset_class="etf",
            frequency="1d",
        )

    @staticmethod
    def load_crypto_ccxt(
        exchange_name: str,
        symbols: list[str],
        timeframe: str = "1d",
        since: Optional[str] = None,
        limit: int = 1000,
        benchmark_symbol: Optional[str] = None,
        funding_rate_fn=None,
    ) -> DataBundle:
        if len(symbols) == 0:
            raise ValueError("symbols must not be empty")

        exchange_cls = getattr(ccxt, exchange_name, None)
        if exchange_cls is None:
            raise ValueError(f"Unknown ccxt exchange: {exchange_name}")

        exchange = exchange_cls({"enableRateLimit": True})

        since_ms = None
        if since is not None:
            since_ms = int(pd.Timestamp(since, tz="UTC").timestamp() * 1000)

        opens, highs, lows, closes, volumes = {}, {}, {}, {}, {}
        funding_map = {}

        for symbol in symbols:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if not ohlcv:
                raise ValueError(f"No OHLCV data for {symbol}")

            df = pd.DataFrame(
                ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
            df = df.set_index("timestamp").sort_index()

            opens[symbol] = df["open"]
            highs[symbol] = df["high"]
            lows[symbol] = df["low"]
            closes[symbol] = df["close"]
            volumes[symbol] = df["volume"]

            if funding_rate_fn is not None:
                f = funding_rate_fn(exchange, symbol, df.index)
                if f is not None:
                    funding_map[symbol] = f.reindex(df.index)

        open_df = pd.DataFrame(opens).sort_index()
        high_df = pd.DataFrame(highs).sort_index()
        low_df = pd.DataFrame(lows).sort_index()
        close_df = pd.DataFrame(closes).sort_index()
        volume_df = pd.DataFrame(volumes).sort_index()

        prices = sanitize_prices(close_df)
        returns = compute_returns_from_prices(prices)

        funding_df = None
        if len(funding_map) > 0:
            funding_df = pd.DataFrame(funding_map).sort_index().reindex_like(prices)

        benchmark_returns = None
        if benchmark_symbol is not None:
            bench_ohlcv = exchange.fetch_ohlcv(benchmark_symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if bench_ohlcv:
                bench_df = pd.DataFrame(
                    bench_ohlcv,
                    columns=["timestamp", "open", "high", "low", "close", "volume"]
                )
                bench_df["timestamp"] = pd.to_datetime(bench_df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
                bench_df = bench_df.set_index("timestamp").sort_index()
                benchmark_returns = bench_df["close"].pct_change().reindex(prices.index)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_df,
            high=high_df,
            low=low_df,
            close=close_df,
            volume=volume_df,
            funding=funding_df,
            borrow_cost=None,
            metadata=None,
            benchmark_returns=benchmark_returns,
            asset_class="crypto",
            frequency=timeframe,
        )

# ============================================================
# Strategy base
# ============================================================

class BaseStrategy(ABC):
    def fit(self, train_data: DataBundle) -> None:
        """
        walk-forward 用。学習不要なら何もしない。
        """
        return

    def prepare_features(self, data: DataBundle) -> Dict[str, pd.DataFrame]:
        return {}

    @abstractmethod
    def generate_scores(
        self,
        data: DataBundle,
        features: Dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        raise NotImplementedError

class BuyAndHoldStrategy(BaseStrategy):
    def generate_scores(self, data: DataBundle, features: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        scores = pd.DataFrame(1.0, index=data.calendar, columns=data.prices.columns)
        scores = scores.where(data.prices.notna())
        return scores

class CrossSectionalMomentumStrategy(BaseStrategy):
    def __init__(self, lookback: int = 126, skip: int = 21, min_history: Optional[int] = None):
        self.lookback = lookback
        self.skip = skip
        self.min_history = min_history if min_history is not None else lookback + skip

    def prepare_features(self, data: DataBundle) -> Dict[str, pd.DataFrame]:
        px = data.prices.copy()

        past = px.shift(self.skip)
        mom = past / past.shift(self.lookback) - 1.0

        valid_hist = px.notna().rolling(self.min_history).sum() >= self.min_history
        mom = mom.where(valid_hist)

        return {"momentum": mom}

    def generate_scores(self, data: DataBundle, features: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        scores = features["momentum"].copy()
        scores = scores.where(data.prices.notna())
        return scores

class RollingZScoreMeanReversionStrategy(BaseStrategy):
    def __init__(self, lookback: int = 20, min_history: Optional[int] = None):
        self.lookback = lookback
        self.min_history = min_history if min_history is not None else lookback

    def prepare_features(self, data: DataBundle) -> Dict[str, pd.DataFrame]:
        ret = data.returns.copy()
        mean = ret.rolling(self.lookback).mean()
        std = ret.rolling(self.lookback).std(ddof=0)
        z = (ret - mean) / std.replace(0.0, np.nan)

        valid_hist = data.prices.notna().rolling(self.min_history).sum() >= self.min_history
        z = z.where(valid_hist)

        return {"zscore": z}

    def generate_scores(self, data: DataBundle, features: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        # 逆張りなのでマイナスをつける
        scores = -features["zscore"]
        scores = scores.where(data.prices.notna())
        return scores

# ============================================================
# Allocator base
# ============================================================

class BaseAllocator(ABC):
    def fit(self, train_data: DataBundle, train_scores: pd.DataFrame) -> None:
        return

    @abstractmethod
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        raise NotImplementedError

class EqualWeightAllocator(BaseAllocator):
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        valid = scores.notna() & data.prices.notna()
        denom = valid.sum(axis=1).replace(0, np.nan)
        w = valid.astype(float).div(denom, axis=0)
        return w.fillna(0.0)

class TopKLongOnlyAllocator(BaseAllocator):
    def __init__(self, k: int = 3):
        if k <= 0:
            raise ValueError("k must be positive.")
        self.k = k

    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        s = scores.where(data.prices.notna())
        ranks = s.rank(axis=1, ascending=False, method="first")
        selected = ranks <= self.k
        denom = selected.sum(axis=1).replace(0, np.nan)
        w = selected.astype(float).div(denom, axis=0)
        return w.fillna(0.0)

class ScoreProportionalLongOnlyAllocator(BaseAllocator):
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        s = scores.clip(lower=0.0).where(data.prices.notna())
        denom = s.sum(axis=1).replace(0, np.nan)
        w = s.div(denom, axis=0)
        return w.fillna(0.0)

class VolTargetAllocator(BaseAllocator):
    """
    正のスコアを使いつつ、単純な逆ボラ調整もかける。
    """
    def __init__(self, vol_lookback: int = 20):
        self.vol_lookback = vol_lookback

    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        s = scores.clip(lower=0.0).where(data.prices.notna())

        vol = data.returns.rolling(self.vol_lookback).std(ddof=0)
        inv_vol = 1.0 / vol.replace(0.0, np.nan)

        raw = s * inv_vol
        denom = raw.sum(axis=1).replace(0, np.nan)
        w = raw.div(denom, axis=0)
        return w.fillna(0.0)

# ============================================================
# Backtester
# ============================================================

class ResearchBacktester:
    def __init__(
        self,
        fee_bps: float = 0.0,
        rebalance_rule: str = "D",
        annualization: Optional[int] = None,
    ):
        self.fee_bps = fee_bps
        self.rebalance_rule = rebalance_rule
        self.annualization = annualization

    def run(
        self,
        strategy: BaseStrategy,
        allocator: BaseAllocator,
        data: DataBundle,
    ) -> BacktestResult:
        features = strategy.prepare_features(data)
        scores = strategy.generate_scores(data, features)
        scores = scores.reindex(index=data.calendar, columns=data.prices.columns)

        weights_raw = allocator.allocate(scores, data)
        weights_raw = weights_raw.reindex(index=data.calendar, columns=data.prices.columns).fillna(0.0)

        rebalance_mask = make_rebalance_mask(data.calendar, self.rebalance_rule)
        weights_rebalanced = apply_rebalance_rule(weights_raw, rebalance_mask)

        # t の終わりで決めて t+1 に保有開始
        weights_executed = weights_rebalanced.shift(1).fillna(0.0)

        asset_returns_gross = data.returns.copy()
        if data.funding is not None:
            asset_returns_gross = asset_returns_gross.add(
                data.funding.reindex_like(asset_returns_gross).fillna(0.0),
                fill_value=0.0,
            )

        if data.borrow_cost is not None:
            asset_returns_gross = asset_returns_gross.sub(
                data.borrow_cost.reindex_like(asset_returns_gross).fillna(0.0),
                fill_value=0.0,
            )

        turnover = (weights_executed - weights_executed.shift(1).fillna(0.0)).abs().sum(axis=1)
        fees = turnover * (self.fee_bps / 1e4)

        portfolio_returns = (weights_executed * asset_returns_gross.fillna(0.0)).sum(axis=1) - fees
        equity_curve = (1.0 + portfolio_returns.fillna(0.0)).cumprod()

        benchmark_returns = None
        benchmark_equity_curve = None
        active_returns = None
        active_equity_curve = None

        if data.benchmark_returns is not None:
            benchmark_returns = data.benchmark_returns.reindex(portfolio_returns.index).fillna(0.0)
            benchmark_equity_curve = (1.0 + benchmark_returns).cumprod()
            active_returns = portfolio_returns - benchmark_returns
            active_equity_curve = (1.0 + active_returns.fillna(0.0)).cumprod()

        stats = self.compute_stats(
            portfolio_returns=portfolio_returns,
            equity_curve=equity_curve,
            turnover=turnover,
            frequency=data.frequency,
            benchmark_returns=benchmark_returns,
            active_returns=active_returns,
        )

        return BacktestResult(
            scores=scores,
            weights_raw=weights_raw,
            weights_executed=weights_executed,
            asset_returns_gross=asset_returns_gross,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            active_returns=active_returns,
            equity_curve=equity_curve,
            benchmark_equity_curve=benchmark_equity_curve,
            active_equity_curve=active_equity_curve,
            turnover=turnover,
            fees=fees,
            rebalance_mask=rebalance_mask,
            stats=stats,
        )

    def compute_stats(
        self,
        portfolio_returns: pd.Series,
        equity_curve: pd.Series,
        turnover: pd.Series,
        frequency: str,
        benchmark_returns: Optional[pd.Series] = None,
        active_returns: Optional[pd.Series] = None,
    ) -> pd.Series:
        r = portfolio_returns.dropna()
        if len(r) == 0:
            return pd.Series(dtype=float)

        ann = self.annualization if self.annualization is not None else annualization_factor(frequency)

        mean_ret = r.mean()
        vol = r.std(ddof=0)
        ann_ret = (1.0 + r).prod() ** (ann / max(len(r), 1)) - 1.0
        ann_vol = vol * np.sqrt(ann) if pd.notna(vol) else np.nan
        sharpe = (mean_ret / vol) * np.sqrt(ann) if (pd.notna(vol) and vol > 0) else np.nan

        dd = compute_drawdown(equity_curve)
        max_dd = dd.min()
        calmar = ann_ret / abs(max_dd) if pd.notna(max_dd) and max_dd < 0 else np.nan

        out = {
            "total_return": equity_curve.iloc[-1] - 1.0,
            "annual_return": ann_ret,
            "annual_volatility": ann_vol,
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "calmar": calmar,
            "hit_ratio": (r > 0).mean(),
            "average_turnover": turnover.mean(),
            "num_periods": len(r),
        }

        if benchmark_returns is not None:
            b = benchmark_returns.reindex(r.index).dropna()
            if len(b) > 0:
                bench_eq = (1.0 + b).cumprod()
                bench_dd = compute_drawdown(bench_eq)

                b_mean = b.mean()
                b_vol = b.std(ddof=0)
                b_ann_ret = (1.0 + b).prod() ** (ann / max(len(b), 1)) - 1.0
                b_ann_vol = b_vol * np.sqrt(ann) if pd.notna(b_vol) else np.nan

                out["benchmark_annual_return"] = b_ann_ret
                out["benchmark_annual_volatility"] = b_ann_vol
                out["benchmark_max_drawdown"] = bench_dd.min()

        if active_returns is not None:
            a = active_returns.reindex(r.index).dropna()
            if len(a) > 0:
                te = a.std(ddof=0) * np.sqrt(ann)
                ir = (a.mean() / a.std(ddof=0)) * np.sqrt(ann) if a.std(ddof=0) > 0 else np.nan
                out["tracking_error"] = te
                out["information_ratio"] = ir
                out["active_return_annual"] = (1.0 + a).prod() ** (ann / max(len(a), 1)) - 1.0

        return pd.Series(out)

    def walk_forward(
        self,
        strategy: BaseStrategy,
        allocator: BaseAllocator,
        data: DataBundle,
        train_periods: int,
        test_periods: int,
        step_periods: Optional[int] = None,
        warmup_bars: int = 0,
    ) -> WalkForwardResult:
        """
        配列ベースの walk-forward。
        - train 期間で fit
        - test 期間で out-of-sample 評価
        """
        idx = data.calendar
        if step_periods is None:
            step_periods = test_periods

        slices: List[WalkForwardSliceResult] = []
        stitched_returns = []
        stitched_bench = []
        stitched_active = []

        start_i = max(warmup_bars, train_periods)
        while True:
            train_start_i = start_i - train_periods
            train_end_i = start_i - 1
            test_start_i = start_i
            test_end_i = min(start_i + test_periods - 1, len(idx) - 1)

            if test_start_i >= len(idx):
                break

            train_index = idx[train_start_i: train_end_i + 1]
            test_index = idx[test_start_i: test_end_i + 1]

            train_data = self.slice_data(data, train_index)
            test_data = self.slice_data(data, test_index)

            strategy.fit(train_data)

            train_features = strategy.prepare_features(train_data)
            train_scores = strategy.generate_scores(train_data, train_features)
            allocator.fit(train_data, train_scores)

            result = self.run(strategy, allocator, test_data)

            slices.append(
                WalkForwardSliceResult(
                    train_start=train_index[0],
                    train_end=train_index[-1],
                    test_start=test_index[0],
                    test_end=test_index[-1],
                    result=result,
                )
            )

            stitched_returns.append(result.portfolio_returns)
            if result.benchmark_returns is not None:
                stitched_bench.append(result.benchmark_returns)
            if result.active_returns is not None:
                stitched_active.append(result.active_returns)

            if test_end_i == len(idx) - 1:
                break

            start_i += step_periods

        stitched_returns_s = pd.concat(stitched_returns).sort_index()
        stitched_returns_s = stitched_returns_s[~stitched_returns_s.index.duplicated(keep="first")]
        stitched_equity = (1.0 + stitched_returns_s.fillna(0.0)).cumprod()

        stitched_bench_s = None
        if len(stitched_bench) > 0:
            stitched_bench_s = pd.concat(stitched_bench).sort_index()
            stitched_bench_s = stitched_bench_s[~stitched_bench_s.index.duplicated(keep="first")]

        stitched_active_s = None
        if len(stitched_active) > 0:
            stitched_active_s = pd.concat(stitched_active).sort_index()
            stitched_active_s = stitched_active_s[~stitched_active_s.index.duplicated(keep="first")]

        stats = self.compute_stats(
            portfolio_returns=stitched_returns_s,
            equity_curve=stitched_equity,
            turnover=pd.Series(0.0, index=stitched_returns_s.index),
            frequency=data.frequency,
            benchmark_returns=stitched_bench_s,
            active_returns=stitched_active_s,
        )

        return WalkForwardResult(
            slices=slices,
            stitched_returns=stitched_returns_s,
            stitched_equity_curve=stitched_equity,
            stitched_benchmark_returns=stitched_bench_s,
            stitched_active_returns=stitched_active_s,
            stats=stats,
        )

    @staticmethod
    def slice_data(data: DataBundle, index: pd.Index) -> DataBundle:
        return DataBundle(
            prices=data.prices.reindex(index),
            returns=data.returns.reindex(index),
            open_=None if data.open_ is None else data.open_.reindex(index),
            high=None if data.high is None else data.high.reindex(index),
            low=None if data.low is None else data.low.reindex(index),
            close=None if data.close is None else data.close.reindex(index),
            volume=None if data.volume is None else data.volume.reindex(index),
            funding=None if data.funding is None else data.funding.reindex(index),
            borrow_cost=None if data.borrow_cost is None else data.borrow_cost.reindex(index),
            metadata=data.metadata,
            benchmark_returns=None if data.benchmark_returns is None else data.benchmark_returns.reindex(index),
            asset_class=data.asset_class,
            frequency=data.frequency,
        )

# ============================================================
# Visualization
# ============================================================

def plot_equity(result: BacktestResult, title: str = "Equity Curve") -> None:
    plt.figure(figsize=(12, 4))
    result.equity_curve.plot(label="Strategy")
    if result.benchmark_equity_curve is not None:
        result.benchmark_equity_curve.plot(label="Benchmark")
    plt.title(title)
    plt.ylabel("Cumulative value")
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_drawdown(result: BacktestResult, title: str = "Drawdown") -> None:
    dd = compute_drawdown(result.equity_curve)
    plt.figure(figsize=(12, 4))
    dd.plot()
    plt.title(title)
    plt.ylabel("Drawdown")
    plt.tight_layout()
    plt.show()

def plot_weights(result: BacktestResult, last_n: int = 100, title: str = "Executed Weights") -> None:
    plt.figure(figsize=(12, 5))
    result.weights_executed.tail(last_n).plot.area(figsize=(12, 5))
    plt.title(title)
    plt.ylabel("Weight")
    plt.tight_layout()
    plt.show()

def plot_scores(result: BacktestResult, asset: str, last_n: int = 200, title: Optional[str] = None) -> None:
    if asset not in result.scores.columns:
        raise ValueError(f"{asset} not found in scores columns.")
    plt.figure(figsize=(12, 4))
    result.scores[asset].tail(last_n).plot()
    plt.title(title or f"Score: {asset}")
    plt.tight_layout()
    plt.show()

# ============================================================
# Example usage
# ============================================================

def example_etf_monthly():
    tickers = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
    data = DataLoader.load_etf_yfinance(
        tickers=tickers,
        start="2015-01-01",
        benchmark_ticker="SPY",
        auto_adjust=False,
        progress=False,
    )

    strategy = CrossSectionalMomentumStrategy(lookback=126, skip=21, min_history=147)
    allocator = TopKLongOnlyAllocator(k=2)

    bt = ResearchBacktester(
        fee_bps=5.0,
        rebalance_rule="M",
    )

    result = bt.run(strategy, allocator, data)

    print("=== ETF monthly rebalance ===")
    print(result.stats.round(4))
    print(result.weights_executed.tail())

    plot_equity(result, title="ETF Strategy vs Benchmark")
    plot_drawdown(result, title="ETF Strategy Drawdown")
    plot_weights(result, last_n=120, title="ETF Executed Weights")
    plot_scores(result, asset="QQQ", last_n=300, title="QQQ Momentum Score")

def example_crypto_weekly():
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    data = DataLoader.load_crypto_ccxt(
        exchange_name="binance",
        symbols=symbols,
        timeframe="1d",
        since="2022-01-01",
        limit=1000,
        benchmark_symbol="BTC/USDT",
        funding_rate_fn=None,
    )

    strategy = CrossSectionalMomentumStrategy(lookback=60, skip=7, min_history=67)
    allocator = TopKLongOnlyAllocator(k=1)

    bt = ResearchBacktester(
        fee_bps=10.0,
        rebalance_rule="W-FRI",
    )

    result = bt.run(strategy, allocator, data)

    print("=== Crypto weekly rebalance ===")
    print(result.stats.round(4))
    plot_equity(result, title="Crypto Strategy vs BTC Benchmark")
    plot_drawdown(result, title="Crypto Strategy Drawdown")
    plot_weights(result, last_n=120, title="Crypto Executed Weights")

def example_etf_walk_forward():
    tickers = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
    data = DataLoader.load_etf_yfinance(
        tickers=tickers,
        start="2012-01-01",
        benchmark_ticker="SPY",
        auto_adjust=False,
        progress=False,
    )

    strategy = CrossSectionalMomentumStrategy(lookback=126, skip=21, min_history=147)
    allocator = TopKLongOnlyAllocator(k=2)

    bt = ResearchBacktester(
        fee_bps=5.0,
        rebalance_rule="M",
    )

    wf = bt.walk_forward(
        strategy=strategy,
        allocator=allocator,
        data=data,
        train_periods=252 * 3,
        test_periods=252,
        step_periods=252,
        warmup_bars=147,
    )

    print("=== ETF walk-forward ===")
    print(wf.stats.round(4))

    plt.figure(figsize=(12, 4))
    wf.stitched_equity_curve.plot(label="Walk-forward OOS")
    plt.title("Walk-forward Out-of-Sample Equity")
    plt.legend()
    plt.tight_layout()
    plt.show()

    if wf.stitched_benchmark_returns is not None:
        bench_eq = (1.0 + wf.stitched_benchmark_returns.fillna(0.0)).cumprod()
        plt.figure(figsize=(12, 4))
        wf.stitched_equity_curve.plot(label="Walk-forward OOS")
        bench_eq.plot(label="Benchmark")
        plt.title("Walk-forward OOS vs Benchmark")
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    example_etf_monthly()
    # example_crypto_weekly()
    # example_etf_walk_forward()
```

* * *

追加した部分の要点
---------

### 1\. 月次・週次リバランス

`rebalance_rule` を追加しています。

```
bt = ResearchBacktester(
    fee_bps=5.0,
    rebalance_rule="M",
)
```

対応しているのは次です。

*   `"D"` 毎バー
*   `"W-FRI"` 週次
*   `"M"` 月末
*   `"Q"` 四半期末

内部では `make_rebalance_mask` を作って、リバランス日だけウェイトを更新し、それ以外は前回ウェイトを維持しています。

重要なのは、ここでもなお

```
weights_executed = weights_rebalanced.shift(1).fillna(0.0)
```

としていることです。  
つまり、**月末に観測した signal に基づく売買は翌営業日以降にしか反映されません**。この点がリーク防止の中核です。

* * *

### 2\. benchmark 比較

`DataBundle` に `benchmark_returns` を持たせています。

ETF なら例えば SPY、crypto なら BTC を benchmark にできます。

```
data = DataLoader.load_etf_yfinance(
    tickers=tickers,
    start="2015-01-01",
    benchmark_ticker="SPY",
)
```

結果として以下を自動計算します。

*   `benchmark_equity_curve`
*   `active_returns`
*   `tracking_error`
*   `information_ratio`

戦略比較のとき、単に Sharpe だけでなく、  
**benchmark に対して何を付加したのか** を見られるようにしています。

* * *

### 3\. walk-forward

`walk_forward()` を追加しています。

```
wf = bt.walk_forward(
    strategy=strategy,
    allocator=allocator,
    data=data,
    train_periods=252 * 3,
    test_periods=252,
    step_periods=252,
    warmup_bars=147,
)
```

これは以下の流れです。

*   train window を切る
*   `strategy.fit(train_data)` を呼ぶ
*   `allocator.fit(train_data, train_scores)` を呼ぶ
*   test window を OOS で backtest
*   それを順次つなぐ

今の `CrossSectionalMomentumStrategy` や `TopKLongOnlyAllocator` は学習不要なので `fit()` は空ですが、将来的に

*   rolling PCA
*   Ridge 回帰
*   レジーム分類
*   リスクモデル推定

などを入れるとき、そのまま拡張できます。

* * *

### 4\. 可視化

最低限の可視化を入れています。

*   `plot_equity`
*   `plot_drawdown`
*   `plot_weights`
*   `plot_scores`

研究用途では、統計量だけでなく

*   どの局面で勝ったか
*   ウェイトが暴れていないか
*   signal が直感に合っているか

を必ず見た方がよいです。

* * *

この設計で重要な思想
----------

### Strategy は score を返すだけ

たとえばモメンタム、逆張り、PCA スコア、機械学習予測など、戦略の違いは `generate_scores()` に閉じ込めます。

### Allocator は weights に変換するだけ

Top-K、等ウェイト、逆ボラ、将来的には mean-variance や risk parity もここに入れます。

### Backtester は評価だけ

約定・PnL・benchmark 比較・walk-forward はここに集約します。

この分離により、

*   同じ signal に対して allocator だけ比較
*   同じ allocator に対して strategy だけ比較
*   同じ data bundle, fee, rebalance rule で公平比較

ができます。

* * *

すぐに足したくなる拡張
-----------

このテンプレートの次に入れるなら、優先度は次です。

### A. `universe_filter`

ETF や crypto の銘柄ごとに

*   最低観測履歴
*   最低売買代金
*   最低出来高
*   欠損率

を満たしたものだけ売買対象にする層です。  
これはかなり重要です。

### B. `TransactionCostModel`

今は `fee_bps` のみです。  
将来的には

*   固定 fee
*   spread cost
*   market impact の近似
*   asset ごとの fee

をクラスに分けると良いです。

### C. `BenchmarkSet`

単一 benchmark だけでなく

*   SPY
*   60/40
*   equal-weight universe
*   BTC buy-and-hold

など複数 benchmark に対する relative performance を出せるようにすると便利です。

### D. `ResultExporter`

結果を csv / parquet / pickle で保存する仕組みです。  
戦略比較が多くなると必要になります。

* * *

実務的な注意
------

この `walk_forward()` は **配列ベースの research engine 向け** です。  
train/test を分ける骨格としては十分ですが、現状は各窓の test に対して独立に `run()` を回しているので、test 窓の境界で前窓の保有状態を持ち越していません。研究用途では多くの場合これで十分ですが、完全に連続した live-like な持ち越しを再現したいなら、walk-forward でも state carry-over を入れる必要があります。

もう1点、ETF の benchmark も `Adj Close` ベースで取っています。  
したがって benchmark 側も配当込みに近い比較になります。これは research engine としては妥当です。

* * *

次にやるなら、これをさらに  
**universe filter・TransactionCostModel・結果保存・設定ファイル駆動**  
まで拡張して、戦略を差し替えるだけで回せるプロジェクト構成に落とすのが良いです。

## Prompt:
どのようなディレクトリ構造で実装すると良いか

## Response:
思考時間: 2 ～ 3 秒

research engine を長く育てる前提なら、**「戦略コード」「共通基盤」「実験設定」「出力結果」** を明確に分けるのがよいです。  
特にあなたの用途では、**戦略だけ差し替えて公平比較する**ことが重要なので、`strategies/` と `engine/` を強く分離した構造が向いています。

私なら、最初は次のように切ります。

```
project_root/
├─ README.md
├─ pyproject.toml
├─ requirements.txt
├─ .gitignore
│
├─ configs/
│  ├─ data/
│  │  ├─ etf_daily.yaml
│  │  └─ crypto_daily.yaml
│  ├─ backtest/
│  │  ├─ monthly.yaml
│  │  ├─ weekly.yaml
│  │  └─ daily.yaml
│  ├─ strategy/
│  │  ├─ buy_and_hold.yaml
│  │  ├─ cs_momentum.yaml
│  │  └─ mean_reversion.yaml
│  └─ experiment/
│     ├─ etf_mom_monthly.yaml
│     └─ crypto_mom_weekly.yaml
│
├─ data/
│  ├─ raw/
│  │  ├─ etf/
│  │  └─ crypto/
│  ├─ interim/
│  │  ├─ aligned/
│  │  └─ cleaned/
│  └─ processed/
│     ├─ bundles/
│     └─ benchmarks/
│
├─ notebooks/
│  ├─ 00_data_check.ipynb
│  ├─ 01_signal_sanity_check.ipynb
│  └─ 02_result_review.ipynb
│
├─ reports/
│  ├─ figures/
│  ├─ tables/
│  └─ logs/
│
├─ results/
│  ├─ backtests/
│  ├─ walkforward/
│  └─ cache/
│
├─ scripts/
│  ├─ download_etf_data.py
│  ├─ download_crypto_data.py
│  ├─ build_bundle.py
│  ├─ run_backtest.py
│  ├─ run_walkforward.py
│  └─ summarize_results.py
│
├─ src/
│  └─ research_engine/
│     ├─ __init__.py
│     │
│     ├─ core/
│     │  ├─ datatypes.py
│     │  ├─ strategy.py
│     │  ├─ allocator.py
│     │  ├─ backtester.py
│     │  ├─ walkforward.py
│     │  ├─ calendar.py
│     │  └─ exceptions.py
│     │
│     ├─ data/
│     │  ├─ base.py
│     │  ├─ yfinance_loader.py
│     │  ├─ ccxt_loader.py
│     │  ├─ bundle_builder.py
│     │  ├─ cleaning.py
│     │  ├─ alignment.py
│     │  ├─ benchmark.py
│     │  └─ cache.py
│     │
│     ├─ features/
│     │  ├─ returns.py
│     │  ├─ momentum.py
│     │  ├─ volatility.py
│     │  ├─ rolling.py
│     │  └─ utils.py
│     │
│     ├─ strategies/
│     │  ├─ buy_and_hold.py
│     │  ├─ cross_sectional_momentum.py
│     │  ├─ mean_reversion.py
│     │  └─ base.py
│     │
│     ├─ allocators/
│     │  ├─ equal_weight.py
│     │  ├─ topk.py
│     │  ├─ score_proportional.py
│     │  ├─ vol_target.py
│     │  └─ base.py
│     │
│     ├─ costs/
│     │  ├─ fee.py
│     │  ├─ slippage.py
│     │  └─ turnover.py
│     │
│     ├─ analytics/
│     │  ├─ metrics.py
│     │  ├─ drawdown.py
│     │  ├─ benchmark.py
│     │  ├─ attribution.py
│     │  └─ summary.py
│     │
│     ├─ visualization/
│     │  ├─ equity.py
│     │  ├─ weights.py
│     │  ├─ scores.py
│     │  └─ tables.py
│     │
│     └─ utils/
│        ├─ io.py
│        ├─ config.py
│        ├─ logging.py
│        └─ misc.py
│
└─ tests/
   ├─ test_data_loader.py
   ├─ test_bundle_builder.py
   ├─ test_strategy_no_leak.py
   ├─ test_allocator.py
   ├─ test_backtester.py
   └─ test_walkforward.py
```

この構造の意図はかなり明確です。

1\. `src/research_engine/core/` を最小の中核にする
-----------------------------------------

ここには依存の少ない抽象だけを置きます。

*   `DataBundle`
*   `BaseStrategy`
*   `BaseAllocator`
*   `ResearchBacktester`
*   `WalkForwardRunner`

この層は、なるべく `yfinance` や `ccxt` を直接知らない方がよいです。  
そうすると、後でデータ取得元を変えても中核が壊れません。

たとえば、責務はこうです。

*   `core/datatypes.py`: `DataBundle`, `BacktestResult`
*   `core/strategy.py`: `BaseStrategy`
*   `core/allocator.py`: `BaseAllocator`
*   `core/backtester.py`: PnL, turnover, fee, benchmark 比較
*   `core/walkforward.py`: train/test 分割と stitched OOS

ここは **研究エンジンの心臓部** です。

* * *

2\. `data/` は取得と整形を分ける
----------------------

データ層でよく失敗するのは、  
**取得・クリーニング・bundle化が1ファイルに混ざること** です。

なので少なくとも次は分けた方がよいです。

*   `yfinance_loader.py`: Yahoo から生データ取得
*   `ccxt_loader.py`: CCXT から生データ取得
*   `cleaning.py`: 欠損、重複、異常値の処理
*   `alignment.py`: 日付合わせ、列合わせ
*   `bundle_builder.py`: `DataBundle` を作る
*   `benchmark.py`: benchmark 系列の生成
*   `cache.py`: parquet 保存 / 読み出し

特に ETF と crypto を同じ研究環境で扱うなら、  
**「取得」と「共通形式への変換」** を絶対に分けた方がよいです。

* * *

3\. `features/` と `strategies/` を分ける
------------------------------------

ここはかなり重要です。

ありがちな悪い設計は、戦略ファイルの中に rolling mean や momentum 計算を全部書いてしまうことです。  
そうすると再利用できません。

だから、

*   `features/`: 純粋な特徴量計算
*   `strategies/`: 特徴量をどう組み合わせて score にするか

に分けるのがよいです。

たとえば、

*   `features/momentum.py`: 12-1 モメンタム、1m リターン、6m リターン
*   `features/volatility.py`: rolling vol, downside vol
*   `strategies/cross_sectional_momentum.py`: それらを使って score を作る

にしておくと、同じ特徴量を別戦略でも使えます。

* * *

4\. `allocators/` を独立させる
------------------------

戦略と配分を分ける設計を採るなら、ここは独立ディレクトリにするべきです。

*   `equal_weight.py`
*   `topk.py`
*   `score_proportional.py`
*   `vol_target.py`

この分離により、

*   同じ signal で配分だけ比較
*   同じ allocator に別 signal を流す

が可能になります。

これは研究の比較可能性にかなり効きます。

* * *

5\. `analytics/` と `visualization/` を分ける
----------------------------------------

これも地味ですが重要です。

*   `analytics/`: 数値計算
*   `visualization/`: 図表作成

たとえば `Sharpe`, `drawdown`, `IR`, `tracking error` は `analytics/metrics.py`。  
equity curve や weights の area chart は `visualization/` に置きます。

こうすると、レポート自動生成や notebook での再利用がしやすいです。

* * *

6\. `configs/` を最初から入れる
-----------------------

研究が進むと、コードの差より **設定差** が増えます。  
そのため、最初から YAML などで分けた方がよいです。

おすすめは3層です。

*   `configs/data/`: データ取得条件
*   `configs/backtest/`: fee, rebalance, benchmark
*   `configs/strategy/`: lookback, skip, topk
*   `configs/experiment/`: 上3つを束ねる実験定義

たとえば `configs/experiment/etf_mom_monthly.yaml` はこういうイメージです。

```
data_config: etf_daily
backtest_config: monthly
strategy_config: cs_momentum

universe:
  tickers: [SPY, QQQ, IWM, TLT, GLD]

benchmark:
  ticker: SPY
```

これを `run_backtest.py --config configs/experiment/etf_mom_monthly.yaml` のように呼びます。

こうしておくと、戦略比較が「コード編集」ではなく「実験設定の差分」になります。

* * *

7\. `scripts/` はCLI入口だけにする
--------------------------

`scripts/` には本体ロジックを書かず、  
**設定を読み込んで `src/` の関数を呼ぶだけ** にします。

良い役割分担はこうです。

*   `download_etf_data.py`: raw データ取得
*   `download_crypto_data.py`: raw データ取得
*   `build_bundle.py`: processed bundle 作成
*   `run_backtest.py`: 単発バックテスト
*   `run_walkforward.py`: walk-forward 実行
*   `summarize_results.py`: 集計

これで再現性が高くなります。

* * *

8\. `data/` と `results/` の物理ディレクトリを分ける
--------------------------------------

これは運用上かなり大事です。

*   `data/`: 入力データ
*   `results/`: 実験出力
*   `reports/`: 図表や最終レポート

この3つを分けると、  
「データ更新」と「実験出力」が混ざらず、管理しやすいです。

おすすめの意味づけは次です。

### `data/raw/`

取得したそのままの CSV / parquet / pickle

### `data/interim/`

クリーニング途中、営業日合わせ途中

### `data/processed/`

最終的に backtest にそのまま渡せる bundle

### `results/backtests/`

各 run の returns, weights, stats

### `results/walkforward/`

walk-forward の stitched OOS 結果

### `reports/`

会議資料・確認用の図表

* * *

9\. `tests/` は最初から作る
--------------------

研究用コードでも、最低限のテストは必須です。  
特にこの手の基盤は、**リークがないか** のテストが重要です。

最低限入れるべきなのは次です。

*   `test_data_loader.py`
    *   取得データの index が昇順か
    *   列名が期待通りか
*   `test_bundle_builder.py`
    *   `prices` と `returns` の shape 整合
*   `test_strategy_no_leak.py`
    *   将来値を混ぜたら失敗するようなテスト
*   `test_allocator.py`
    *   long-only ならウェイト合計が 1 か
*   `test_backtester.py`
    *   `weights.shift(1)` が効いているか
*   `test_walkforward.py`
    *   OOS stitching の index 重複がないか

とくに `weights.shift(1)` は、この基盤の最重要仕様なのでテストしておくべきです。

* * *

10\. あなたの用途なら notebook は補助に留める
------------------------------

notebook は便利ですが、  
エンジン本体まで notebook に寄せると再現性が下がります。

使い方としては、

*   `src/`: 本体
*   `scripts/`: 実行
*   `notebooks/`: 点検・可視化・仮説確認

に限定するのがよいです。

* * *

最小版ならここまで削ってよい
--------------

最初から全部は重いので、最小構成ならこうです。

```
project_root/
├─ configs/
├─ data/
├─ results/
├─ scripts/
├─ src/
│  └─ research_engine/
│     ├─ core/
│     ├─ data/
│     ├─ strategies/
│     ├─ allocators/
│     ├─ analytics/
│     └─ visualization/
└─ tests/
```

これだけでも十分始められます。

* * *

実務上いちばんおすすめの設計原則
----------------

一番大事なのは、ディレクトリ名そのものよりも、次の3原則です。

### 1\. Strategy は `src/research_engine/strategies/` に閉じ込める

戦略差分をここに限定する。

### 2\. `DataBundle` を唯一の共通入出力にする

ETF でも crypto でも、backtester が見るのは `DataBundle` だけにする。

### 3\. 実験条件は `configs/experiment/` に閉じ込める

コード差分ではなく設定差分で比較する。

この3つが守れていれば、かなり綺麗に育ちます。

* * *

あなたのケースだと、次の2段階で進めるのがよいです。

**第1段階**  
まずは

*   `core`
*   `data`
*   `strategies`
*   `allocators`
*   `analytics`
*   `scripts`
*   `configs`

だけで始める。

**第2段階**  
使いながら

*   `costs`
*   `visualization`
*   `walkforward`
*   `cache`
*   `tests`

を厚くする。

* * *

必要なら次に、上の構造に合わせて  
**`project_root` 以下の具体的なファイル雛形一式**  
`pyproject.toml`, `run_backtest.py`, `config.yaml`, `BaseStrategy`, `Backtester` の配置まで含めて、そのまま作れる形で出します。

## Prompt:
codexによる戦略の開発も別途行います。これはディレクトリを破壊的に変更する可能性があるため、ディレクトリを工夫して非破壊的にしたいです。高度な分離は可読性を損なうため最小構成で

## Response:
思考時間: 1 秒

その条件なら、**基盤と Codex 作業領域を物理的に分ける**のが最小で強いです。  
細かく層を増やすより、**「壊してよい場所」と「壊してはいけない場所」をトップレベルで分離**する方が実用的です。

おすすめは次です。

```
project_root/
├─ README.md
├─ pyproject.toml
├─ requirements.txt
├─ .gitignore
│
├─ configs/
│  ├─ etf_mom_monthly.yaml
│  └─ crypto_mom_weekly.yaml
│
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ cache/
│
├─ results/
│  ├─ backtests/
│  ├─ walkforward/
│  └─ figures/
│
├─ scripts/
│  ├─ run_backtest.py
│  ├─ run_walkforward.py
│  └─ build_data_bundle.py
│
├─ src/
│  └─ engine/
│     ├─ __init__.py
│     ├─ data.py
│     ├─ strategy.py
│     ├─ allocator.py
│     ├─ backtester.py
│     ├─ analytics.py
│     └─ plotting.py
│
├─ strategies/
│  ├─ __init__.py
│  ├─ buy_and_hold.py
│  ├─ cross_sectional_momentum.py
│  └─ mean_reversion.py
│
├─ codex/
│  ├─ README.md
│  ├─ prompts/
│  ├─ specs/
│  ├─ patches/
│  ├─ experiments/
│  │  ├─ exp_001/
│  │  ├─ exp_002/
│  │  └─ scratch/
│  └─ staging/
│
└─ tests/
   ├─ test_backtester.py
   ├─ test_strategy.py
   └─ test_data.py
```

この構造のポイントはかなり単純です。

1\. `src/engine/` は固定資産にする
--------------------------

ここは**研究基盤の本体**です。  
Codex に自由に触らせない前提にします。

含めるのは最小限で十分です。

*   `data.py`: `DataBundle`, loader, 前処理
*   `strategy.py`: `BaseStrategy`
*   `allocator.py`: `BaseAllocator`
*   `backtester.py`: `ResearchBacktester`, walk-forward
*   `analytics.py`: 指標計算
*   `plotting.py`: 可視化

つまり、前に提案した細分化をかなり潰して、**engine 1ディレクトリ**に寄せます。  
可読性を落とさず、しかも壊されにくいです。

* * *

2\. `strategies/` を engine から分離する
---------------------------------

ここが重要です。

Codex に触らせたいのは基本的にここです。  
戦略の追加・変更は `strategies/` 配下だけで完結するようにします。

例えば、

*   `strategies/cross_sectional_momentum.py`
*   `strategies/pca_rotation.py`
*   `strategies/rl_overlay.py`

のように置きます。

`src/engine/strategy.py` には `BaseStrategy` だけ置き、個別戦略は置かない方が安全です。  
こうすると Codex が戦略開発しても、基盤を壊しにくいです。

* * *

3\. `codex/` を完全に隔離した作業場にする
---------------------------

これが今回の主眼です。

Codex はしばしば、

*   ファイルを大量追加する
*   ディレクトリ構成を作り替える
*   中途半端な試作コードを残す

ので、これを本体と混ぜない方がよいです。

`codex/` の役割は次です。

*   `prompts/`: Codex に渡すプロンプト
*   `specs/`: 実装仕様
*   `patches/`: diff や修正版メモ
*   `experiments/`: 壊してよい実験コード
*   `staging/`: 一時的に生成された戦略候補

つまり **Codex の生成物を一度ここに受けて、採用するものだけ `strategies/` に移植** します。

これが最小かつ非破壊的な運用です。

* * *

4\. 運用ルールを明確にする
---------------

構造以上に大事なのはルールです。  
最低限、次のルールにすると安定します。

### ルールA

`src/engine/` は手作業でしか編集しない。

### ルールB

Codex は原則 `codex/` と `strategies/` だけ触る。

### ルールC

Codex の出力は一度 `codex/staging/` か `codex/experiments/` に置く。

### ルールD

採用が決まったものだけ `strategies/` に移す。

この4つでかなり事故が減ります。

* * *

5\. 最小構成での責務分担
--------------

この構成なら、責務はこう整理できます。

### `src/engine/`

共通基盤。壊したくない場所。

### `strategies/`

本採用の戦略置き場。差し替え対象。

### `codex/`

壊してよい生成・試作・検討の場所。

### `scripts/`

実行入口。設定を読み、engine と strategy を呼ぶだけ。

### `configs/`

実験条件。コードではなく設定差分で管理。

これ以上細かく分けなくても十分回ります。

* * *

6\. `scripts/` は strategy 名を文字列で受ける形がよい
---------------------------------------

Codex 連携を考えると、実行側はこういう設計がよいです。

```
# scripts/run_backtest.py のイメージ
from importlib import import_module

def load_strategy(strategy_name: str, **kwargs):
    mod = import_module(f"strategies.{strategy_name}")
    return mod.build_strategy(**kwargs)
```

これにより、

*   `strategies/cross_sectional_momentum.py`
*   `strategies/pca_rotation.py`

を増やしても、engine 側は変えずに済みます。

Codex にも「`strategies/` 配下に新規追加せよ」と指示しやすいです。

* * *

7\. Codex 用には `strategies/` のテンプレートを1つ置く
----------------------------------------

かなり有効です。

例えば `strategies/_template.py` を置いておきます。

```
from src.engine.strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def fit(self, train_data):
        return

    def prepare_features(self, data):
        return {}

    def generate_scores(self, data, features):
        raise NotImplementedError

def build_strategy(**kwargs):
    return MyStrategy(**kwargs)
```

Codex には「この形式に従え」と言えばよいです。  
これだけで余計な構造改変がかなり減ります。

* * *

8\. さらに非破壊にしたいなら `vendor/` 的発想もあり
---------------------------------

Codex が出したものをすぐ採用せず、一段置きたいなら次の形もあります。

```
strategies/
├─ approved/
│  ├─ cross_sectional_momentum.py
│  └─ mean_reversion.py
└─ experimental/
   ├─ pca_rotation_v1.py
   └─ codex_trial_001.py
```

ただし、これは少し階層が増えます。  
あなたは最小構成を望んでいるので、まずは

*   `strategies/` = 採用済み
*   `codex/experiments/` = 未採用

で十分です。

* * *

9\. いちばんおすすめの最小版
----------------

本当に最小まで削るなら、私はこれを勧めます。

```
project_root/
├─ configs/
├─ data/
├─ results/
├─ scripts/
├─ src/
│  └─ engine/
│     ├─ data.py
│     ├─ strategy.py
│     ├─ allocator.py
│     ├─ backtester.py
│     ├─ analytics.py
│     └─ plotting.py
├─ strategies/
├─ codex/
│  ├─ prompts/
│  ├─ specs/
│  ├─ staging/
│  └─ experiments/
└─ tests/
```

これならシンプルですし、意味も明快です。

*   `src/engine/` は固定
*   `strategies/` は本採用
*   `codex/` は破壊OK

この3分割だけで十分に非破壊的です。

* * *

10\. 追加でやると良い小さな工夫
------------------

大げさな分離ではなく、小さな工夫でかなり安全になります。

### `.gitignore`

`codex/experiments/` や `results/` の一部を ignore する。

### `README.md`

トップに「Codex が編集してよい場所」を明記する。

### `tests/`

最低限、`src/engine/` の仕様を守るテストだけ置く。  
Codex が壊してもすぐ分かります。

* * *

結論
--

あなたの条件なら、最小で強い構成はこれです。

*   **`src/engine/`**: 壊したくない共通基盤
*   **`strategies/`**: 本採用戦略
*   **`codex/`**: 壊してよい作業場

細かい階層分割より、このトップレベル分離の方が効果が大きいです。  
可読性もほとんど落ちません。

必要なら次に、この最小構成に合わせて  
**各ファイルの中身の雛形一式**  
`src/engine/*.py`, `strategies/_template.py`, `scripts/run_backtest.py` までまとめて出します。

## Prompt:
workspaceディレクトリ以下に、envs, projectsとディレクトリを配置している。ここに付け加える形で作りたい。projectsの中身は投資戦略以外でも日常の研究でさまざまなものを作る予定なため、相互で干渉しないようにsたい

## Response:
思考時間: 1 秒

その前提なら、`workspace/` 直下は増やしすぎず、**`projects/` の中で project ごとに完全分離**するのがよいです。  
つまり、投資戦略エンジン専用の1プロジェクトを `projects/` 配下に独立させ、他の研究プロジェクトとは **ディレクトリ・設定・依存・実行入口** を分けます。

おすすめはこうです。

```
workspace/
├─ envs/
│  ├─ research-base/
│  ├─ trading-research/
│  └─ <other-envs>/
│
└─ projects/
   ├─ trading_research/
   │  ├─ README.md
   │  ├─ pyproject.toml
   │  ├─ requirements.txt
   │  ├─ .gitignore
   │  │
   │  ├─ configs/
   │  ├─ data/
   │  ├─ results/
   │  ├─ scripts/
   │  ├─ src/
   │  │  └─ engine/
   │  ├─ strategies/
   │  ├─ codex/
   │  └─ tests/
   │
   ├─ <other_project_1>/
   ├─ <other_project_2>/
   └─ <other_project_3>/
```

これが一番素直で、相互干渉も起きにくいです。

1\. 干渉を防ぐ単位は `projects/<project_name>/`
---------------------------------------

他の研究も `projects/` の下に増やす予定なら、  
**project ごとに self-contained にする**のが最も重要です。

つまり `trading_research/` の中に

*   コード
*   設定
*   データ
*   結果
*   Codex 用作業場
*   テスト

を全部閉じ込めます。

こうすると、

*   他プロジェクトの `configs/` を読んでしまう
*   結果ファイルを書き潰す
*   Codex が別プロジェクトに触る

といった事故を避けやすいです。

* * *

2\. `envs/` も project 単位で対応付ける
------------------------------

依存衝突を避けるには、ディレクトリ分離だけでなく環境分離も重要です。  
そのため、`envs/` 側も project と対応づけるのがよいです。

例えば、

```
workspace/envs/trading-research/
```

をこの project 専用環境にします。

命名も合わせると分かりやすいです。

*   `projects/trading_research/`
*   `envs/trading-research/`

完全に1対1でなくてもよいですが、少なくとも投資戦略系は専用 env にした方がよいです。  
`ccxt`, `yfinance`, `matplotlib`, `pandas` あたりは他研究でも使うかもしれませんが、将来的に `numba`, `cvxpy`, `torch`, `stable-baselines3` などが入ると依存が重くなりやすいです。

* * *

3\. `projects/trading_research/` の最小構成
--------------------------------------

前の方針をそのまま `projects/` 配下に入れるなら、最小でこれです。

```
workspace/
└─ projects/
   └─ trading_research/
      ├─ README.md
      ├─ pyproject.toml
      ├─ requirements.txt
      ├─ .gitignore
      │
      ├─ configs/
      │  ├─ etf_mom_monthly.yaml
      │  └─ crypto_mom_weekly.yaml
      │
      ├─ data/
      │  ├─ raw/
      │  ├─ processed/
      │  └─ cache/
      │
      ├─ results/
      │  ├─ backtests/
      │  ├─ walkforward/
      │  └─ figures/
      │
      ├─ scripts/
      │  ├─ build_data_bundle.py
      │  ├─ run_backtest.py
      │  └─ run_walkforward.py
      │
      ├─ src/
      │  └─ engine/
      │     ├─ __init__.py
      │     ├─ data.py
      │     ├─ strategy.py
      │     ├─ allocator.py
      │     ├─ backtester.py
      │     ├─ analytics.py
      │     └─ plotting.py
      │
      ├─ strategies/
      │  ├─ __init__.py
      │  ├─ _template.py
      │  ├─ buy_and_hold.py
      │  └─ cross_sectional_momentum.py
      │
      ├─ codex/
      │  ├─ prompts/
      │  ├─ specs/
      │  ├─ staging/
      │  └─ experiments/
      │
      └─ tests/
         ├─ test_data.py
         ├─ test_strategy.py
         └─ test_backtester.py
```

これはかなり小さいですが、必要な分離はできています。

* * *

4\. 他プロジェクトと干渉しないための実務ルール
-------------------------

ディレクトリ構造だけでなく、運用ルールも少し決めた方がよいです。

### ルールA: project 内相対パスで閉じる

`trading_research/` のスクリプトは、  
**必ず project 直下を基準にパス解決** するようにします。

例えば `workspace/projects/other_project/data` を見に行かないようにします。

#### 良い例

```
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
CONFIG_DIR = PROJECT_ROOT / "configs"
```

このように project root 基準で閉じると安全です。

* * *

### ルールB: 絶対 import は project 内 package のみ

`src/engine/` を package 化し、  
他 project の `src/` を import しない運用にします。

例えばこの project では

```
from engine.backtester import ResearchBacktester
```

のように、自 project のみを見る形にします。

より安全にするなら package 名を固有にして

```
from trading_research.engine.backtester import ResearchBacktester
```

でもよいです。  
ただし最小構成を重視するなら `src/engine/` のままでも十分です。

* * *

### ルールC: データと結果は project 内完結

共通の `workspace/data` のような共有置き場は作らない方がよいです。  
便利ですが、他案件と混ざりやすくなります。

なので、

*   `projects/trading_research/data/`
*   `projects/trading_research/results/`

に閉じます。

共通化したくなっても、最初はやらない方が安全です。

* * *

### ルールD: Codex の作業領域も project 内完結

Codex 用の `codex/` も project ごとに持ちます。  
全 project 共通の `workspace/codex/` は作らない方がよいです。

理由は単純で、Codex の生成物は project 依存が強いからです。

* * *

5\. `projects/` 直下にカテゴリを切る案はどうか
-------------------------------

例えばこんな構造も考えられます。

```
workspace/
└─ projects/
   ├─ finance/
   │  └─ trading_research/
   ├─ ml/
   └─ misc/
```

これは将来的に project 数がかなり増えるなら有効です。  
ただ、今の段階では階層を1つ増やすだけなので、最小構成重視ならまだ不要です。

つまり今は

```
workspace/projects/trading_research/
```

で十分です。

* * *

6\. package 名だけは少し工夫するとさらに安全
----------------------------

相互干渉をさらに減らすなら、`src/engine/` よりも

```
src/trading_research/
```

の方が安全です。

例えばこうです。

```
workspace/projects/trading_research/
├─ src/
│  └─ trading_research/
│     ├─ __init__.py
│     ├─ data.py
│     ├─ strategy.py
│     ├─ allocator.py
│     ├─ backtester.py
│     ├─ analytics.py
│     └─ plotting.py
```

これなら import も

```
from trading_research.backtester import ResearchBacktester
from trading_research.strategy import BaseStrategy
```

となり、他 project と名前衝突しにくいです。

**可読性はほぼ落ちず、安全性は上がる** ので、実はこれが一番おすすめです。

つまり最小構成を保ちつつ少しだけ改善するなら、最終的にはこうです。

```
workspace/
├─ envs/
│  └─ trading-research/
└─ projects/
   └─ trading_research/
      ├─ configs/
      ├─ data/
      ├─ results/
      ├─ scripts/
      ├─ src/
      │  └─ trading_research/
      │     ├─ __init__.py
      │     ├─ data.py
      │     ├─ strategy.py
      │     ├─ allocator.py
      │     ├─ backtester.py
      │     ├─ analytics.py
      │     └─ plotting.py
      ├─ strategies/
      ├─ codex/
      └─ tests/
```

* * *

7\. あなたのケースでのおすすめ結論
-------------------

条件を整理すると、

*   `workspace/` 直下にはすでに `envs/`, `projects/` がある
*   `projects/` には投資戦略以外も増える
*   相互干渉を避けたい
*   可読性を落とす高度分離は不要
*   Codex の破壊的変更から守りたい

なので、最適解はこれです。

### 採用案

*   `workspace/projects/trading_research/` を1つ切る
*   その中に `src`, `strategies`, `codex`, `configs`, `data`, `results`, `scripts`, `tests`
*   Python package は `src/trading_research/`
*   専用環境は `workspace/envs/trading-research/`

これで十分シンプルで、しかも干渉しにくいです。

* * *

8\. 具体名のおすすめ
------------

命名はかなり大事です。  
私は次を勧めます。

*   project: `trading_research`
*   env: `trading-research`
*   package: `trading_research`

統一すると迷いません。

* * *

必要なら次に、この構成を前提に  
**`workspace/projects/trading_research/` の各ファイルの初期雛形**  
`pyproject.toml`, `run_backtest.py`, `src/trading_research/*.py`, `strategies/_template.py` までまとめて出します。

## Prompt:
projects直下にカテゴリを切った場合の構造にして

## Response:
思考時間: 1 秒

はい。その場合は `projects/` 直下に **カテゴリ** を置き、その下に **project を完全分離**する形が素直です。  
あなたの要件だと、投資戦略系は 1 カテゴリにまとめ、各案件はその下で self-contained にするのがよいです。

最小構成でおすすめなのは次です。

```
workspace/
├─ envs/
│  ├─ trading-research/
│  ├─ ml-research/
│  └─ <other-envs>/
│
└─ projects/
   ├─ finance/
   │  └─ trading_research/
   │     ├─ README.md
   │     ├─ pyproject.toml
   │     ├─ requirements.txt
   │     ├─ .gitignore
   │     │
   │     ├─ configs/
   │     │  ├─ etf_mom_monthly.yaml
   │     │  └─ crypto_mom_weekly.yaml
   │     │
   │     ├─ data/
   │     │  ├─ raw/
   │     │  ├─ processed/
   │     │  └─ cache/
   │     │
   │     ├─ results/
   │     │  ├─ backtests/
   │     │  ├─ walkforward/
   │     │  └─ figures/
   │     │
   │     ├─ scripts/
   │     │  ├─ build_data_bundle.py
   │     │  ├─ run_backtest.py
   │     │  └─ run_walkforward.py
   │     │
   │     ├─ src/
   │     │  └─ trading_research/
   │     │     ├─ __init__.py
   │     │     ├─ data.py
   │     │     ├─ strategy.py
   │     │     ├─ allocator.py
   │     │     ├─ backtester.py
   │     │     ├─ analytics.py
   │     │     └─ plotting.py
   │     │
   │     ├─ strategies/
   │     │  ├─ __init__.py
   │     │  ├─ _template.py
   │     │  ├─ buy_and_hold.py
   │     │  └─ cross_sectional_momentum.py
   │     │
   │     ├─ codex/
   │     │  ├─ prompts/
   │     │  ├─ specs/
   │     │  ├─ staging/
   │     │  └─ experiments/
   │     │
   │     └─ tests/
   │        ├─ test_data.py
   │        ├─ test_strategy.py
   │        └─ test_backtester.py
   │
   ├─ ml/
   │  ├─ feature_lab/
   │  └─ regime_models/
   │
   ├─ research/
   │  ├─ notebook_sandbox/
   │  └─ topic_experiments/
   │
   └─ misc/
      └─ utilities/
```

この形のメリットは明確です。

1\. `projects/finance/` 配下だけを金融研究の作業場にできる
-----------------------------------------

投資戦略系の project は `finance/` に寄せるので、他カテゴリと混ざりません。

たとえば今後、

*   `projects/finance/trading_research`
*   `projects/finance/portfolio_tools`
*   `projects/finance/risk_dashboard`

のように増やしても、金融系だけまとまります。

* * *

2\. 干渉回避の単位は `projects/<category>/<project>/`
---------------------------------------------

カテゴリを切っても、実際に隔離の単位は **project 単位** です。  
つまり、

```
projects/finance/trading_research/
```

の中だけで完結するようにします。

ここに

*   code
*   config
*   data
*   results
*   tests
*   codex workspace

を全部閉じ込めるのが重要です。

* * *

3\. package 名は `trading_research` のままでよい
----------------------------------------

ディレクトリが `projects/finance/trading_research/` でも、Python package は

```
src/trading_research/
```

で問題ありません。

つまり import は

```
from trading_research.backtester import ResearchBacktester
from trading_research.strategy import BaseStrategy
```

で統一できます。

カテゴリ名の `finance` を package 名にまで含めて

```
src/finance_trading_research/
```

としてもよいですが、少し長いです。  
最小構成を優先するなら `trading_research` で十分です。

* * *

4\. Codex の破壊的変更も project 内に閉じ込められる
-----------------------------------

今回の要件ではここが重要です。

Codex 用の作業場を

```
projects/finance/trading_research/codex/
```

に置くことで、他カテゴリや他 project には影響しません。

運用としてはこうです。

*   `src/trading_research/` は共通基盤
*   `strategies/` は採用済み戦略
*   `codex/experiments/` は壊してよい試作
*   `codex/staging/` は候補の一時置き場

これでかなり安全です。

* * *

5\. env もカテゴリ単位ではなく project 単位がよい
---------------------------------

カテゴリを切ると `envs/finance/` のようにしたくなるかもしれませんが、  
依存衝突を避けるなら環境は project 単位の方がよいです。

おすすめはそのまま

```
workspace/envs/trading-research/
```

です。

対応関係としては、

*   project: `workspace/projects/finance/trading_research/`
*   env: `workspace/envs/trading-research/`

とします。

これが一番分かりやすいです。

* * *

6\. finance カテゴリ配下でさらに共通基盤を作るのは、最初はやらない方がよい
-------------------------------------------

たとえば次のような構造は、今はまだ避けた方がよいです。

```
projects/
└─ finance/
   ├─ shared/
   ├─ trading_research/
   └─ risk_dashboard/
```

一見きれいですが、`shared/` を作ると project 間依存が生まれます。  
そうすると、相互干渉を避けたいという今回の目的とぶつかります。

なので最初は **project ごとに完全独立** がよいです。  
共通化は、本当に重複が増えてからで十分です。

* * *

7\. さらに最小化した版
-------------

かなり削るなら、`trading_research/` の中身はこれでも回ります。

```
workspace/
└─ projects/
   └─ finance/
      └─ trading_research/
         ├─ configs/
         ├─ data/
         ├─ results/
         ├─ scripts/
         ├─ src/
         │  └─ trading_research/
         │     ├─ data.py
         │     ├─ strategy.py
         │     ├─ allocator.py
         │     ├─ backtester.py
         │     ├─ analytics.py
         │     └─ plotting.py
         ├─ strategies/
         ├─ codex/
         └─ tests/
```

これが、可読性を落とさずに non-destructive に運用する最小ラインです。

* * *

8\. おすすめの命名
-----------

カテゴリを切るなら、命名は次のように揃えると運用しやすいです。

*   category: `finance`
*   project: `trading_research`
*   env: `trading-research`
*   package: `trading_research`

つまり実体はこうです。

```
workspace/projects/finance/trading_research/
workspace/envs/trading-research/
```

これで十分整っています。

* * *

結論
--

カテゴリを切る場合のおすすめは、

```
workspace/projects/finance/trading_research/
```

を独立プロジェクトにし、その中に

*   `src/trading_research/`
*   `strategies/`
*   `codex/`
*   `configs/`
*   `data/`
*   `results/`
*   `scripts/`
*   `tests/`

を置く形です。

これなら

*   他カテゴリの project と干渉しない
*   Codex の破壊的変更を project 内に閉じ込められる
*   構造がシンプル
*   将来 `finance` 配下に別案件を増やしやすい

というバランスが取れます。

次に必要なら、この構造前提で  
**初期ディレクトリ一式を `mkdir` できるコマンド** と、  
**各ファイルの最小雛形** をまとめて出します。

## Prompt:
命名規則はgithubno形式に合わせたい

## Response:
思考時間: 2 ～ 3 秒

了解です。  
その場合は **GitHub で一般的な命名** に寄せて、**リポジトリ名・ディレクトリ名は kebab-case**、Python の **package 名だけ snake\_case** にするのが一番自然です。

つまり方針は次です。

*   **repo / project directory / scripts / data dirs**: `kebab-case`
*   **Python package / module**: `snake_case`
*   **class 名**: `PascalCase`
*   **config ファイル名**: `kebab-case`
*   **strategy 実装ファイル名**: `snake_case` でもよいが、GitHub 上の見た目を揃えるなら `kebab-case` を避けて Python 側は `snake_case`

Python は import の都合があるので、**ディレクトリ名と package 名を完全一致させない**のがポイントです。

おすすめ構造
------

```
workspace/
├─ envs/
│  ├─ trading-research/
│  ├─ ml-research/
│  └─ other-env/
│
└─ projects/
   ├─ finance/
   │  └─ trading-research/
   │     ├─ README.md
   │     ├─ pyproject.toml
   │     ├─ requirements.txt
   │     ├─ .gitignore
   │     │
   │     ├─ configs/
   │     │  ├─ etf-momentum-monthly.yaml
   │     │  └─ crypto-momentum-weekly.yaml
   │     │
   │     ├─ data/
   │     │  ├─ raw/
   │     │  ├─ processed/
   │     │  └─ cache/
   │     │
   │     ├─ results/
   │     │  ├─ backtests/
   │     │  ├─ walkforward/
   │     │  └─ figures/
   │     │
   │     ├─ scripts/
   │     │  ├─ build-data-bundle.py
   │     │  ├─ run-backtest.py
   │     │  └─ run-walkforward.py
   │     │
   │     ├─ src/
   │     │  └─ trading_research/
   │     │     ├─ __init__.py
   │     │     ├─ data.py
   │     │     ├─ strategy.py
   │     │     ├─ allocator.py
   │     │     ├─ backtester.py
   │     │     ├─ analytics.py
   │     │     └─ plotting.py
   │     │
   │     ├─ strategies/
   │     │  ├─ __init__.py
   │     │  ├─ template_strategy.py
   │     │  ├─ buy_and_hold.py
   │     │  └─ cross_sectional_momentum.py
   │     │
   │     ├─ codex/
   │     │  ├─ prompts/
   │     │  ├─ specs/
   │     │  ├─ staging/
   │     │  └─ experiments/
   │     │
   │     └─ tests/
   │        ├─ test_data.py
   │        ├─ test_strategy.py
   │        └─ test_backtester.py
   │
   ├─ ml/
   ├─ research/
   └─ misc/
```

命名ルールの整理
--------

### 1\. project / repo 名

GitHub に合わせるならこれです。

*   `trading-research`
*   `portfolio-tools`
*   `regime-models`

つまり **kebab-case** です。

今回なら:

*   project directory: `projects/finance/trading-research/`
*   env name: `envs/trading-research/`

が自然です。

### 2\. Python package 名

Python 側は `-` が使えないので、ここだけ `snake_case` にします。

*   `src/trading_research/`

import はこうなります。

```
from trading_research.backtester import ResearchBacktester
from trading_research.strategy import BaseStrategy
```

これはかなり標準的です。

### 3\. strategy ファイル名

Python module なので `snake_case` が無難です。

*   `buy_and_hold.py`
*   `cross_sectional_momentum.py`
*   `mean_reversion.py`

ここを GitHub 見た目に合わせて `buy-and-hold.py` にすると import が面倒になるので、**Python ファイルは snake\_case を優先**した方がよいです。

### 4\. script 名

CLI 的に使うなら GitHub っぽく `kebab-case` が見やすいです。

*   `run-backtest.py`
*   `run-walkforward.py`
*   `build-data-bundle.py`

ただし `python -m` 運用に寄せるなら scripts 自体を薄くしてもよいです。

### 5\. config 名

GitHub でも CLI でも見やすいので `kebab-case` がよいです。

*   `etf-momentum-monthly.yaml`
*   `crypto-momentum-weekly.yaml`

### 6\. テスト名

Python の慣習で `snake_case` が自然です。

*   `test_backtester.py`
*   `test_strategy.py`

* * *

最小構成でのおすすめ最終形
-------------

あなたの条件を全部満たす形としては、これが一番よいです。

*   カテゴリあり: `projects/finance/`
*   project 名は GitHub 風: `trading-research`
*   Python package は Python 風: `trading_research`
*   Codex は project 内に隔離: `codex/`

つまり実体はこれです。

```
workspace/
├─ envs/
│  └─ trading-research/
└─ projects/
   └─ finance/
      └─ trading-research/
         ├─ configs/
         ├─ data/
         ├─ results/
         ├─ scripts/
         ├─ src/
         │  └─ trading_research/
         ├─ strategies/
         ├─ codex/
         └─ tests/
```

運用上の小さな注意
---------

`strategies/` を Python import 対象にするなら、ここも package にしておくのが安全です。

```
strategies/
├─ __init__.py
├─ buy_and_hold.py
└─ cross_sectional_momentum.py
```

そして `run-backtest.py` では文字列で読み込むと扱いやすいです。

```
from importlib import import_module

def load_strategy(name: str):
    mod = import_module(f"strategies.{name}")
    return mod.build_strategy()
```

この場合、指定名は `cross_sectional_momentum` のように **snake\_case** にします。

* * *

命名規則の結論
-------

今回のケースでは、次の統一が最も自然です。

*   **workspace/envs**: `trading-research`
*   **workspace/projects/finance**: `trading-research`
*   **Python package**: `trading_research`
*   **strategy modules**: `cross_sectional_momentum.py`
*   **scripts**: `run-backtest.py`
*   **configs**: `etf-momentum-monthly.yaml`

これで GitHub っぽさと Python らしさを両立できます。

必要なら次に、この命名規則に合わせて  
**`mkdir` 用コマンド一式** と **各ファイルの最小雛形** をまとめて出します。

## Prompt:
バックテストなどプログラムを再出力して

## Response:
思考時間: 2 ～ 3 秒

以下は、直近まで決めた方針に合わせて整理し直した **バックテスト用プログラム一式の再出力** です。

前提は次です。

*   配置先は `workspace/projects/finance/trading-research/`
*   GitHub 風に **project / dir / config / script 名は kebab-case**
*   Python package は **snake\_case** なので `src/trading_research/`
*   戦略は `strategies/` に分離
*   Codex の破壊的変更は `codex/` に隔離
*   research engine 前提
*   ETF は `yfinance`、crypto は `ccxt`
*   リーク防止のため `weights.shift(1)` を固定

* * *

ディレクトリ構造
========

```
workspace/
└─ projects/
   └─ finance/
      └─ trading-research/
         ├─ pyproject.toml
         ├─ requirements.txt
         ├─ README.md
         ├─ configs/
         │  ├─ etf-momentum-monthly.yaml
         │  └─ crypto-momentum-weekly.yaml
         ├─ data/
         │  ├─ raw/
         │  ├─ processed/
         │  └─ cache/
         ├─ results/
         │  ├─ backtests/
         │  ├─ walkforward/
         │  └─ figures/
         ├─ scripts/
         │  ├─ run-backtest.py
         │  └─ run-walkforward.py
         ├─ src/
         │  └─ trading_research/
         │     ├─ __init__.py
         │     ├─ data.py
         │     ├─ strategy.py
         │     ├─ allocator.py
         │     ├─ analytics.py
         │     ├─ backtester.py
         │     ├─ plotting.py
         │     └─ config.py
         ├─ strategies/
         │  ├─ __init__.py
         │  ├─ buy_and_hold.py
         │  └─ cross_sectional_momentum.py
         ├─ tests/
         │  └─ test_backtester.py
         └─ codex/
            ├─ prompts/
            ├─ specs/
            ├─ staging/
            └─ experiments/
```

* * *

1\. `requirements.txt`
======================

```
pandas>=2.2
numpy>=1.26
matplotlib>=3.8
PyYAML>=6.0
yfinance>=0.2.54
ccxt>=4.4
```

* * *

2\. `pyproject.toml`
====================

```
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "trading-research"
version = "0.1.0"
description = "Research backtesting engine for ETF and crypto strategies"
requires-python = ">=3.10"
dependencies = [
  "pandas>=2.2",
  "numpy>=1.26",
  "matplotlib>=3.8",
  "PyYAML>=6.0",
  "yfinance>=0.2.54",
  "ccxt>=4.4",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

* * *

3\. `src/trading_research/__init__.py`
======================================

```
from trading_research.data import DataBundle, DataLoader
from trading_research.strategy import BaseStrategy
from trading_research.allocator import BaseAllocator
from trading_research.backtester import ResearchBacktester, BacktestResult, WalkForwardResult

__all__ = [
    "DataBundle",
    "DataLoader",
    "BaseStrategy",
    "BaseAllocator",
    "ResearchBacktester",
    "BacktestResult",
    "WalkForwardResult",
]
```

* * *

4\. `src/trading_research/data.py`
==================================

```
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
import ccxt

@dataclass
class DataBundle:
    prices: pd.DataFrame
    returns: pd.DataFrame
    open_: Optional[pd.DataFrame] = None
    high: Optional[pd.DataFrame] = None
    low: Optional[pd.DataFrame] = None
    close: Optional[pd.DataFrame] = None
    volume: Optional[pd.DataFrame] = None
    funding: Optional[pd.DataFrame] = None
    borrow_cost: Optional[pd.DataFrame] = None
    metadata: Optional[pd.DataFrame] = None
    benchmark_returns: Optional[pd.Series] = None
    asset_class: str = "unknown"
    frequency: str = "1d"

    @property
    def calendar(self) -> pd.DatetimeIndex:
        return self.prices.index

def sanitize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy().sort_index()
    prices = prices.replace([np.inf, -np.inf], np.nan)
    return prices

def compute_returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = sanitize_prices(prices)
    returns = prices.pct_change()
    returns = returns.replace([np.inf, -np.inf], np.nan)
    return returns

class DataLoader:
    @staticmethod
    def load_etf_yfinance(
        tickers: list[str],
        start: str,
        end: Optional[str] = None,
        benchmark_ticker: Optional[str] = None,
        auto_adjust: bool = False,
        progress: bool = False,
    ) -> DataBundle:
        if not tickers:
            raise ValueError("tickers must not be empty")

        raw = yf.download(
            tickers=tickers,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
            progress=progress,
            group_by="column",
            actions=True,
            threads=True,
        )

        if raw.empty:
            raise ValueError("No ETF data downloaded from yfinance.")

        def extract_field(field: str) -> Optional[pd.DataFrame]:
            if isinstance(raw.columns, pd.MultiIndex):
                if field not in raw.columns.get_level_values(0):
                    return None
                out = raw[field].copy()
                if isinstance(out, pd.Series):
                    out = out.to_frame()
                return out.reindex(columns=tickers)
            else:
                if field not in raw.columns:
                    return None
                out = raw[[field]].copy()
                out.columns = tickers[:1]
                return out

        open_ = extract_field("Open")
        high = extract_field("High")
        low = extract_field("Low")
        close = extract_field("Close")
        adj_close = extract_field("Adj Close")
        volume = extract_field("Volume")

        prices = adj_close.copy() if adj_close is not None else close.copy()
        prices = sanitize_prices(prices)
        returns = compute_returns_from_prices(prices)

        benchmark_returns = None
        if benchmark_ticker is not None:
            bench = yf.download(
                tickers=benchmark_ticker,
                start=start,
                end=end,
                auto_adjust=auto_adjust,
                progress=progress,
                group_by="column",
                actions=True,
                threads=True,
            )
            if not bench.empty:
                if isinstance(bench.columns, pd.MultiIndex):
                    if "Adj Close" in bench.columns.get_level_values(0):
                        bench_px = bench["Adj Close"].iloc[:, 0]
                    else:
                        bench_px = bench["Close"].iloc[:, 0]
                else:
                    bench_px = bench["Adj Close"] if "Adj Close" in bench.columns else bench["Close"]
                benchmark_returns = bench_px.sort_index().pct_change().reindex(prices.index)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            benchmark_returns=benchmark_returns,
            asset_class="etf",
            frequency="1d",
        )

    @staticmethod
    def load_crypto_ccxt(
        exchange_name: str,
        symbols: list[str],
        timeframe: str = "1d",
        since: Optional[str] = None,
        limit: int = 1000,
        benchmark_symbol: Optional[str] = None,
        funding_rate_fn=None,
    ) -> DataBundle:
        if not symbols:
            raise ValueError("symbols must not be empty")

        exchange_cls = getattr(ccxt, exchange_name, None)
        if exchange_cls is None:
            raise ValueError(f"Unknown ccxt exchange: {exchange_name}")

        exchange = exchange_cls({"enableRateLimit": True})

        since_ms = None
        if since is not None:
            since_ms = int(pd.Timestamp(since, tz="UTC").timestamp() * 1000)

        opens, highs, lows, closes, volumes = {}, {}, {}, {}, {}
        funding_map = {}

        for symbol in symbols:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if not ohlcv:
                raise ValueError(f"No OHLCV data for {symbol}")

            df = pd.DataFrame(
                ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
            df = df.set_index("timestamp").sort_index()

            opens[symbol] = df["open"]
            highs[symbol] = df["high"]
            lows[symbol] = df["low"]
            closes[symbol] = df["close"]
            volumes[symbol] = df["volume"]

            if funding_rate_fn is not None:
                f = funding_rate_fn(exchange, symbol, df.index)
                if f is not None:
                    funding_map[symbol] = f.reindex(df.index)

        open_df = pd.DataFrame(opens).sort_index()
        high_df = pd.DataFrame(highs).sort_index()
        low_df = pd.DataFrame(lows).sort_index()
        close_df = pd.DataFrame(closes).sort_index()
        volume_df = pd.DataFrame(volumes).sort_index()

        prices = sanitize_prices(close_df)
        returns = compute_returns_from_prices(prices)

        funding_df = None
        if funding_map:
            funding_df = pd.DataFrame(funding_map).sort_index().reindex_like(prices)

        benchmark_returns = None
        if benchmark_symbol is not None:
            bench_ohlcv = exchange.fetch_ohlcv(benchmark_symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if bench_ohlcv:
                bench_df = pd.DataFrame(
                    bench_ohlcv,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )
                bench_df["timestamp"] = pd.to_datetime(bench_df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
                bench_df = bench_df.set_index("timestamp").sort_index()
                benchmark_returns = bench_df["close"].pct_change().reindex(prices.index)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_df,
            high=high_df,
            low=low_df,
            close=close_df,
            volume=volume_df,
            funding=funding_df,
            benchmark_returns=benchmark_returns,
            asset_class="crypto",
            frequency=timeframe,
        )
```

* * *

5\. `src/trading_research/strategy.py`
======================================

```
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

from trading_research.data import DataBundle

class BaseStrategy(ABC):
    def fit(self, train_data: DataBundle) -> None:
        return

    def prepare_features(self, data: DataBundle) -> Dict[str, pd.DataFrame]:
        return {}

    @abstractmethod
    def generate_scores(
        self,
        data: DataBundle,
        features: Dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        raise NotImplementedError
```

* * *

6\. `src/trading_research/allocator.py`
=======================================

```
from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd

from trading_research.data import DataBundle

class BaseAllocator(ABC):
    def fit(self, train_data: DataBundle, train_scores: pd.DataFrame) -> None:
        return

    @abstractmethod
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        raise NotImplementedError

class EqualWeightAllocator(BaseAllocator):
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        valid = scores.notna() & data.prices.notna()
        denom = valid.sum(axis=1).replace(0, np.nan)
        w = valid.astype(float).div(denom, axis=0)
        return w.fillna(0.0)

class TopKLongOnlyAllocator(BaseAllocator):
    def __init__(self, k: int = 3):
        if k <= 0:
            raise ValueError("k must be positive")
        self.k = k

    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        s = scores.where(data.prices.notna())
        ranks = s.rank(axis=1, ascending=False, method="first")
        selected = ranks <= self.k
        denom = selected.sum(axis=1).replace(0, np.nan)
        w = selected.astype(float).div(denom, axis=0)
        return w.fillna(0.0)
```

* * *

7\. `src/trading_research/analytics.py`
=======================================

```
from __future__ import annotations

import numpy as np
import pandas as pd

def annualization_factor(frequency: str) -> int:
    mapping = {
        "1d": 252,
        "1h": 24 * 365,
        "4h": 6 * 365,
        "1w": 52,
        "1m": 12,
    }
    return mapping.get(frequency, 252)

def compute_drawdown(equity_curve: pd.Series) -> pd.Series:
    running_max = equity_curve.cummax()
    return equity_curve / running_max - 1.0

def compute_stats(
    portfolio_returns: pd.Series,
    equity_curve: pd.Series,
    turnover: pd.Series,
    frequency: str,
    benchmark_returns: pd.Series | None = None,
    active_returns: pd.Series | None = None,
    annualization: int | None = None,
) -> pd.Series:
    r = portfolio_returns.dropna()
    if len(r) == 0:
        return pd.Series(dtype=float)

    ann = annualization if annualization is not None else annualization_factor(frequency)

    mean_ret = r.mean()
    vol = r.std(ddof=0)
    ann_ret = (1.0 + r).prod() ** (ann / max(len(r), 1)) - 1.0
    ann_vol = vol * np.sqrt(ann) if pd.notna(vol) else np.nan
    sharpe = (mean_ret / vol) * np.sqrt(ann) if (pd.notna(vol) and vol > 0) else np.nan

    dd = compute_drawdown(equity_curve)
    max_dd = dd.min()
    calmar = ann_ret / abs(max_dd) if pd.notna(max_dd) and max_dd < 0 else np.nan

    out = {
        "total_return": equity_curve.iloc[-1] - 1.0,
        "annual_return": ann_ret,
        "annual_volatility": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "hit_ratio": (r > 0).mean(),
        "average_turnover": turnover.mean(),
        "num_periods": len(r),
    }

    if benchmark_returns is not None:
        b = benchmark_returns.reindex(r.index).dropna()
        if len(b) > 0:
            out["benchmark_annual_return"] = (1.0 + b).prod() ** (ann / max(len(b), 1)) - 1.0
            out["benchmark_annual_volatility"] = b.std(ddof=0) * np.sqrt(ann)

    if active_returns is not None:
        a = active_returns.reindex(r.index).dropna()
        if len(a) > 0:
            te = a.std(ddof=0) * np.sqrt(ann)
            ir = (a.mean() / a.std(ddof=0)) * np.sqrt(ann) if a.std(ddof=0) > 0 else np.nan
            out["tracking_error"] = te
            out["information_ratio"] = ir
            out["active_return_annual"] = (1.0 + a).prod() ** (ann / max(len(a), 1)) - 1.0

    return pd.Series(out)
```

* * *

8\. `src/trading_research/backtester.py`
========================================

```
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

import pandas as pd

from trading_research.data import DataBundle
from trading_research.strategy import BaseStrategy
from trading_research.allocator import BaseAllocator
from trading_research.analytics import compute_stats

@dataclass
class BacktestResult:
    scores: pd.DataFrame
    weights_raw: pd.DataFrame
    weights_executed: pd.DataFrame
    asset_returns_gross: pd.DataFrame
    portfolio_returns: pd.Series
    benchmark_returns: Optional[pd.Series]
    active_returns: Optional[pd.Series]
    equity_curve: pd.Series
    benchmark_equity_curve: Optional[pd.Series]
    active_equity_curve: Optional[pd.Series]
    turnover: pd.Series
    fees: pd.Series
    rebalance_mask: pd.Series
    stats: pd.Series

@dataclass
class WalkForwardSliceResult:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    result: BacktestResult

@dataclass
class WalkForwardResult:
    slices: List[WalkForwardSliceResult]
    stitched_returns: pd.Series
    stitched_equity_curve: pd.Series
    stitched_benchmark_returns: Optional[pd.Series]
    stitched_active_returns: Optional[pd.Series]
    stats: pd.Series

def make_rebalance_mask(index: pd.DatetimeIndex, rule: str = "D") -> pd.Series:
    idx = pd.DatetimeIndex(index)
    mask = pd.Series(False, index=idx)

    if rule == "D":
        mask[:] = True
        return mask

    if rule.startswith("W-"):
        grp = idx.to_series().dt.to_period("W-" + rule.split("-")[1])
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    if rule == "M":
        grp = idx.to_series().dt.to_period("M")
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    if rule == "Q":
        grp = idx.to_series().dt.to_period("Q")
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    raise ValueError("Unsupported rebalance rule. Use 'D', 'W-FRI', 'M', or 'Q'.")

def apply_rebalance_rule(weights_raw: pd.DataFrame, rebalance_mask: pd.Series) -> pd.DataFrame:
    weights_raw = weights_raw.copy()
    rebalance_mask = rebalance_mask.reindex(weights_raw.index).fillna(False)

    out = pd.DataFrame(index=weights_raw.index, columns=weights_raw.columns, dtype=float)
    prev = pd.Series(0.0, index=weights_raw.columns)

    for dt in weights_raw.index:
        if rebalance_mask.loc[dt]:
            w = weights_raw.loc[dt].fillna(0.0)
            s = w.sum()
            prev = (w / s) if s > 0 else pd.Series(0.0, index=weights_raw.columns)
        out.loc[dt] = prev

    return out.fillna(0.0)

class ResearchBacktester:
    def __init__(
        self,
        fee_bps: float = 0.0,
        rebalance_rule: str = "D",
        annualization: int | None = None,
    ):
        self.fee_bps = fee_bps
        self.rebalance_rule = rebalance_rule
        self.annualization = annualization

    def run(
        self,
        strategy: BaseStrategy,
        allocator: BaseAllocator,
        data: DataBundle,
    ) -> BacktestResult:
        features = strategy.prepare_features(data)
        scores = strategy.generate_scores(data, features)
        scores = scores.reindex(index=data.calendar, columns=data.prices.columns)

        weights_raw = allocator.allocate(scores, data)
        weights_raw = weights_raw.reindex(index=data.calendar, columns=data.prices.columns).fillna(0.0)

        rebalance_mask = make_rebalance_mask(data.calendar, self.rebalance_rule)
        weights_rebalanced = apply_rebalance_rule(weights_raw, rebalance_mask)

        # リーク防止
        weights_executed = weights_rebalanced.shift(1).fillna(0.0)

        asset_returns_gross = data.returns.copy()
        if data.funding is not None:
            asset_returns_gross = asset_returns_gross.add(
                data.funding.reindex_like(asset_returns_gross).fillna(0.0),
                fill_value=0.0,
            )

        if data.borrow_cost is not None:
            asset_returns_gross = asset_returns_gross.sub(
                data.borrow_cost.reindex_like(asset_returns_gross).fillna(0.0),
                fill_value=0.0,
            )

        turnover = (weights_executed - weights_executed.shift(1).fillna(0.0)).abs().sum(axis=1)
        fees = turnover * (self.fee_bps / 1e4)

        portfolio_returns = (weights_executed * asset_returns_gross.fillna(0.0)).sum(axis=1) - fees
        equity_curve = (1.0 + portfolio_returns.fillna(0.0)).cumprod()

        benchmark_returns = None
        benchmark_equity_curve = None
        active_returns = None
        active_equity_curve = None

        if data.benchmark_returns is not None:
            benchmark_returns = data.benchmark_returns.reindex(portfolio_returns.index).fillna(0.0)
            benchmark_equity_curve = (1.0 + benchmark_returns).cumprod()
            active_returns = portfolio_returns - benchmark_returns
            active_equity_curve = (1.0 + active_returns.fillna(0.0)).cumprod()

        stats = compute_stats(
            portfolio_returns=portfolio_returns,
            equity_curve=equity_curve,
            turnover=turnover,
            frequency=data.frequency,
            benchmark_returns=benchmark_returns,
            active_returns=active_returns,
            annualization=self.annualization,
        )

        return BacktestResult(
            scores=scores,
            weights_raw=weights_raw,
            weights_executed=weights_executed,
            asset_returns_gross=asset_returns_gross,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            active_returns=active_returns,
            equity_curve=equity_curve,
            benchmark_equity_curve=benchmark_equity_curve,
            active_equity_curve=active_equity_curve,
            turnover=turnover,
            fees=fees,
            rebalance_mask=rebalance_mask,
            stats=stats,
        )

    def walk_forward(
        self,
        strategy: BaseStrategy,
        allocator: BaseAllocator,
        data: DataBundle,
        train_periods: int,
        test_periods: int,
        step_periods: int | None = None,
        warmup_bars: int = 0,
    ) -> WalkForwardResult:
        idx = data.calendar
        if step_periods is None:
            step_periods = test_periods

        slices: list[WalkForwardSliceResult] = []
        stitched_returns = []
        stitched_bench = []
        stitched_active = []

        start_i = max(warmup_bars, train_periods)
        while True:
            train_start_i = start_i - train_periods
            train_end_i = start_i - 1
            test_start_i = start_i
            test_end_i = min(start_i + test_periods - 1, len(idx) - 1)

            if test_start_i >= len(idx):
                break

            train_index = idx[train_start_i: train_end_i + 1]
            test_index = idx[test_start_i: test_end_i + 1]

            train_data = self.slice_data(data, train_index)
            test_data = self.slice_data(data, test_index)

            strategy.fit(train_data)
            train_features = strategy.prepare_features(train_data)
            train_scores = strategy.generate_scores(train_data, train_features)
            allocator.fit(train_data, train_scores)

            result = self.run(strategy, allocator, test_data)

            slices.append(
                WalkForwardSliceResult(
                    train_start=train_index[0],
                    train_end=train_index[-1],
                    test_start=test_index[0],
                    test_end=test_index[-1],
                    result=result,
                )
            )

            stitched_returns.append(result.portfolio_returns)
            if result.benchmark_returns is not None:
                stitched_bench.append(result.benchmark_returns)
            if result.active_returns is not None:
                stitched_active.append(result.active_returns)

            if test_end_i == len(idx) - 1:
                break

            start_i += step_periods

        stitched_returns_s = pd.concat(stitched_returns).sort_index()
        stitched_returns_s = stitched_returns_s[~stitched_returns_s.index.duplicated(keep="first")]
        stitched_equity = (1.0 + stitched_returns_s.fillna(0.0)).cumprod()

        stitched_bench_s = None
        if stitched_bench:
            stitched_bench_s = pd.concat(stitched_bench).sort_index()
            stitched_bench_s = stitched_bench_s[~stitched_bench_s.index.duplicated(keep="first")]

        stitched_active_s = None
        if stitched_active:
            stitched_active_s = pd.concat(stitched_active).sort_index()
            stitched_active_s = stitched_active_s[~stitched_active_s.index.duplicated(keep="first")]

        stats = compute_stats(
            portfolio_returns=stitched_returns_s,
            equity_curve=stitched_equity,
            turnover=pd.Series(0.0, index=stitched_returns_s.index),
            frequency=data.frequency,
            benchmark_returns=stitched_bench_s,
            active_returns=stitched_active_s,
            annualization=self.annualization,
        )

        return WalkForwardResult(
            slices=slices,
            stitched_returns=stitched_returns_s,
            stitched_equity_curve=stitched_equity,
            stitched_benchmark_returns=stitched_bench_s,
            stitched_active_returns=stitched_active_s,
            stats=stats,
        )

    @staticmethod
    def slice_data(data: DataBundle, index: pd.Index) -> DataBundle:
        return DataBundle(
            prices=data.prices.reindex(index),
            returns=data.returns.reindex(index),
            open_=None if data.open_ is None else data.open_.reindex(index),
            high=None if data.high is None else data.high.reindex(index),
            low=None if data.low is None else data.low.reindex(index),
            close=None if data.close is None else data.close.reindex(index),
            volume=None if data.volume is None else data.volume.reindex(index),
            funding=None if data.funding is None else data.funding.reindex(index),
            borrow_cost=None if data.borrow_cost is None else data.borrow_cost.reindex(index),
            metadata=data.metadata,
            benchmark_returns=None if data.benchmark_returns is None else data.benchmark_returns.reindex(index),
            asset_class=data.asset_class,
            frequency=data.frequency,
        )
```

* * *

9\. `src/trading_research/plotting.py`
======================================

```
from __future__ import annotations

import matplotlib.pyplot as plt

from trading_research.analytics import compute_drawdown
from trading_research.backtester import BacktestResult

def plot_equity(result: BacktestResult, title: str = "Equity Curve") -> None:
    plt.figure(figsize=(12, 4))
    result.equity_curve.plot(label="Strategy")
    if result.benchmark_equity_curve is not None:
        result.benchmark_equity_curve.plot(label="Benchmark")
    plt.title(title)
    plt.ylabel("Cumulative value")
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_drawdown(result: BacktestResult, title: str = "Drawdown") -> None:
    dd = compute_drawdown(result.equity_curve)
    plt.figure(figsize=(12, 4))
    dd.plot()
    plt.title(title)
    plt.ylabel("Drawdown")
    plt.tight_layout()
    plt.show()

def plot_weights(result: BacktestResult, last_n: int = 100, title: str = "Executed Weights") -> None:
    result.weights_executed.tail(last_n).plot.area(figsize=(12, 5))
    plt.title(title)
    plt.ylabel("Weight")
    plt.tight_layout()
    plt.show()
```

* * *

10\. `src/trading_research/config.py`
=====================================

```
from __future__ import annotations

from pathlib import Path
import yaml

def load_yaml(path: str | Path) -> dict:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
```

* * *

11\. `strategies/__init__.py`
=============================

```
# empty
```

* * *

12\. `strategies/buy_and_hold.py`
=================================

```
from __future__ import annotations

import pandas as pd

from trading_research.strategy import BaseStrategy
from trading_research.data import DataBundle

class BuyAndHoldStrategy(BaseStrategy):
    def generate_scores(self, data: DataBundle, features: dict[str, pd.DataFrame]) -> pd.DataFrame:
        scores = pd.DataFrame(1.0, index=data.calendar, columns=data.prices.columns)
        scores = scores.where(data.prices.notna())
        return scores

def build_strategy(**kwargs) -> BuyAndHoldStrategy:
    return BuyAndHoldStrategy()
```

* * *

13\. `strategies/cross_sectional_momentum.py`
=============================================

```
from __future__ import annotations

import pandas as pd

from trading_research.strategy import BaseStrategy
from trading_research.data import DataBundle

class CrossSectionalMomentumStrategy(BaseStrategy):
    def __init__(self, lookback: int = 126, skip: int = 21, min_history: int | None = None):
        self.lookback = lookback
        self.skip = skip
        self.min_history = min_history if min_history is not None else lookback + skip

    def prepare_features(self, data: DataBundle) -> dict[str, pd.DataFrame]:
        px = data.prices.copy()
        past = px.shift(self.skip)
        mom = past / past.shift(self.lookback) - 1.0
        valid_hist = px.notna().rolling(self.min_history).sum() >= self.min_history
        mom = mom.where(valid_hist)
        return {"momentum": mom}

    def generate_scores(self, data: DataBundle, features: dict[str, pd.DataFrame]) -> pd.DataFrame:
        scores = features["momentum"].copy()
        scores = scores.where(data.prices.notna())
        return scores

def build_strategy(
    lookback: int = 126,
    skip: int = 21,
    min_history: int | None = None,
    **kwargs,
) -> CrossSectionalMomentumStrategy:
    return CrossSectionalMomentumStrategy(
        lookback=lookback,
        skip=skip,
        min_history=min_history,
    )
```

* * *

14\. `scripts/run-backtest.py`
==============================

```
from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path

import pandas as pd

from trading_research.config import load_yaml
from trading_research.data import DataLoader
from trading_research.allocator import EqualWeightAllocator, TopKLongOnlyAllocator
from trading_research.backtester import ResearchBacktester
from trading_research.plotting import plot_equity, plot_drawdown, plot_weights

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "backtests"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures"

def load_strategy(strategy_name: str, strategy_params: dict):
    mod = import_module(f"strategies.{strategy_name}")
    return mod.build_strategy(**strategy_params)

def build_allocator(cfg: dict):
    name = cfg["name"]
    params = cfg.get("params", {})

    if name == "equal_weight":
        return EqualWeightAllocator()
    if name == "top_k_long_only":
        return TopKLongOnlyAllocator(**params)

    raise ValueError(f"Unknown allocator: {name}")

def build_data(cfg: dict):
    source = cfg["source"]

    if source == "yfinance":
        return DataLoader.load_etf_yfinance(
            tickers=cfg["tickers"],
            start=cfg["start"],
            end=cfg.get("end"),
            benchmark_ticker=cfg.get("benchmark_ticker"),
            auto_adjust=cfg.get("auto_adjust", False),
            progress=cfg.get("progress", False),
        )

    if source == "ccxt":
        return DataLoader.load_crypto_ccxt(
            exchange_name=cfg["exchange_name"],
            symbols=cfg["symbols"],
            timeframe=cfg.get("timeframe", "1d"),
            since=cfg.get("since"),
            limit=cfg.get("limit", 1000),
            benchmark_symbol=cfg.get("benchmark_symbol"),
        )

    raise ValueError(f"Unknown data source: {source}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to yaml config")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()

    cfg = load_yaml(args.config)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    data = build_data(cfg["data"])
    strategy = load_strategy(cfg["strategy"]["name"], cfg["strategy"].get("params", {}))
    allocator = build_allocator(cfg["allocator"])
    backtester = ResearchBacktester(
        fee_bps=cfg["backtest"].get("fee_bps", 0.0),
        rebalance_rule=cfg["backtest"].get("rebalance_rule", "D"),
        annualization=cfg["backtest"].get("annualization"),
    )

    result = backtester.run(strategy, allocator, data)

    print(result.stats.round(4))

    run_name = cfg.get("run_name", Path(args.config).stem)

    result.portfolio_returns.to_csv(RESULTS_DIR / f"{run_name}-returns.csv", header=["portfolio_return"])
    result.weights_executed.to_csv(RESULTS_DIR / f"{run_name}-weights.csv")
    result.stats.to_csv(RESULTS_DIR / f"{run_name}-stats.csv", header=["value"])

    if not args.no_plot:
        plot_equity(result, title=run_name)
        plot_drawdown(result, title=f"{run_name} drawdown")
        plot_weights(result, title=f"{run_name} weights")

if __name__ == "__main__":
    main()
```

* * *

15\. `scripts/run-walkforward.py`
=================================

```
from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path

import matplotlib.pyplot as plt

from trading_research.config import load_yaml
from trading_research.data import DataLoader
from trading_research.allocator import EqualWeightAllocator, TopKLongOnlyAllocator
from trading_research.backtester import ResearchBacktester

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "walkforward"

def load_strategy(strategy_name: str, strategy_params: dict):
    mod = import_module(f"strategies.{strategy_name}")
    return mod.build_strategy(**strategy_params)

def build_allocator(cfg: dict):
    name = cfg["name"]
    params = cfg.get("params", {})

    if name == "equal_weight":
        return EqualWeightAllocator()
    if name == "top_k_long_only":
        return TopKLongOnlyAllocator(**params)

    raise ValueError(f"Unknown allocator: {name}")

def build_data(cfg: dict):
    source = cfg["source"]

    if source == "yfinance":
        return DataLoader.load_etf_yfinance(
            tickers=cfg["tickers"],
            start=cfg["start"],
            end=cfg.get("end"),
            benchmark_ticker=cfg.get("benchmark_ticker"),
            auto_adjust=cfg.get("auto_adjust", False),
            progress=cfg.get("progress", False),
        )

    if source == "ccxt":
        return DataLoader.load_crypto_ccxt(
            exchange_name=cfg["exchange_name"],
            symbols=cfg["symbols"],
            timeframe=cfg.get("timeframe", "1d"),
            since=cfg.get("since"),
            limit=cfg.get("limit", 1000),
            benchmark_symbol=cfg.get("benchmark_symbol"),
        )

    raise ValueError(f"Unknown data source: {source}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to yaml config")
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    data = build_data(cfg["data"])
    strategy = load_strategy(cfg["strategy"]["name"], cfg["strategy"].get("params", {}))
    allocator = build_allocator(cfg["allocator"])

    backtester = ResearchBacktester(
        fee_bps=cfg["backtest"].get("fee_bps", 0.0),
        rebalance_rule=cfg["backtest"].get("rebalance_rule", "D"),
        annualization=cfg["backtest"].get("annualization"),
    )

    wf_cfg = cfg["walkforward"]
    wf = backtester.walk_forward(
        strategy=strategy,
        allocator=allocator,
        data=data,
        train_periods=wf_cfg["train_periods"],
        test_periods=wf_cfg["test_periods"],
        step_periods=wf_cfg.get("step_periods"),
        warmup_bars=wf_cfg.get("warmup_bars", 0),
    )

    print(wf.stats.round(4))

    run_name = cfg.get("run_name", Path(args.config).stem)
    wf.stitched_returns.to_csv(RESULTS_DIR / f"{run_name}-wf-returns.csv", header=["portfolio_return"])
    wf.stats.to_csv(RESULTS_DIR / f"{run_name}-wf-stats.csv", header=["value"])

    plt.figure(figsize=(12, 4))
    wf.stitched_equity_curve.plot(label="walk-forward")
    plt.title(run_name)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
```

* * *

16\. `configs/etf-momentum-monthly.yaml`
========================================

```
run_name: etf-momentum-monthly

data:
  source: yfinance
  tickers: [SPY, QQQ, IWM, TLT, GLD]
  start: "2015-01-01"
  benchmark_ticker: SPY
  auto_adjust: false
  progress: false

strategy:
  name: cross_sectional_momentum
  params:
    lookback: 126
    skip: 21
    min_history: 147

allocator:
  name: top_k_long_only
  params:
    k: 2

backtest:
  fee_bps: 5.0
  rebalance_rule: M
  annualization: 252

walkforward:
  train_periods: 756
  test_periods: 252
  step_periods: 252
  warmup_bars: 147
```

* * *

17\. `configs/crypto-momentum-weekly.yaml`
==========================================

```
run_name: crypto-momentum-weekly

data:
  source: ccxt
  exchange_name: binance
  symbols: [BTC/USDT, ETH/USDT, SOL/USDT]
  timeframe: 1d
  since: "2022-01-01"
  limit: 1000
  benchmark_symbol: BTC/USDT

strategy:
  name: cross_sectional_momentum
  params:
    lookback: 60
    skip: 7
    min_history: 67

allocator:
  name: top_k_long_only
  params:
    k: 1

backtest:
  fee_bps: 10.0
  rebalance_rule: W-FRI
  annualization: 252

walkforward:
  train_periods: 365
  test_periods: 90
  step_periods: 90
  warmup_bars: 67
```

* * *

18\. 実行方法
=========

project 直下で:

```
pip install -r requirements.txt
pip install -e .
```

単発バックテスト:

```
python scripts/run-backtest.py --config configs/etf-momentum-monthly.yaml
python scripts/run-backtest.py --config configs/crypto-momentum-weekly.yaml
```

walk-forward:

```
python scripts/run-walkforward.py --config configs/etf-momentum-monthly.yaml
```

* * *

19\. この再出力版での要点
===============

今回の構成では、以前の説明をそのまま project 構成に落としています。

*   `src/trading_research/`  
    共通基盤。壊したくない場所です。
*   `strategies/`  
    戦略差分だけを置きます。Codex に触らせるならまずここです。
*   `codex/`  
    壊してよい作業場です。本採用前の試作やパッチはここに置きます。
*   `configs/`  
    実験条件をコードではなく yaml で管理します。
*   `scripts/`  
    実行入口だけに限定しています。

* * *

20\. 最初に確認しておきたい注意点
===================

このままでも研究用途には十分動きますが、いくつか仕様上の前提があります。

ETF 側は `Adj Close` を基準価格に使っています。  
したがって、**配当込みに近い日次比較**には向きますが、ベンダー級の厳密な total return index と完全一致する保証はありません。

crypto 側は venue 固定です。  
`ccxt` で Binance を指定しているので、**他取引所と価格を混ぜない**前提です。

walk-forward は OOS 評価用としては十分ですが、test 窓ごとの連続保有 state を厳密に引き継いではいません。  
research engine としては妥当ですが、live-like にさらに寄せたくなった段階で拡張対象になります。

* * *

必要なら次に、これをそのまま一括生成できる **`mkdir` / `cat` ベースのシェルスクリプト** にして出します。

## Prompt:
スクリプトは不要、最小構成で実装し、実行は適宜ノートブックで行うものとする

## Response:
思考時間: 数秒

了解です。  
その条件なら、**scripts と configs を外し、ノートブックから直接 import して使う最小構成**に寄せるのがよいです。

目的は次の3つです。

*   共通基盤は最小限
*   戦略だけ差し替え可能
*   Codex の作業領域を分離しつつ、普段は notebook から実行

* * *

最小構成
----

`projects` 直下にカテゴリを切る前提で、最小ならこれです。

```
workspace/
├─ envs/
│  └─ trading-research/
└─ projects/
   └─ finance/
      └─ trading-research/
         ├─ README.md
         ├─ pyproject.toml
         ├─ requirements.txt
         ├─ data/
         │  ├─ raw/
         │  ├─ processed/
         │  └─ cache/
         ├─ results/
         │  ├─ backtests/
         │  ├─ walkforward/
         │  └─ figures/
         ├─ notebooks/
         │  ├─ 00-data-check.ipynb
         │  ├─ 10-etf-backtest.ipynb
         │  └─ 20-crypto-backtest.ipynb
         ├─ src/
         │  └─ trading_research/
         │     ├─ __init__.py
         │     ├─ data.py
         │     ├─ strategy.py
         │     ├─ allocator.py
         │     ├─ analytics.py
         │     ├─ backtester.py
         │     └─ plotting.py
         ├─ strategies/
         │  ├─ __init__.py
         │  ├─ buy_and_hold.py
         │  └─ cross_sectional_momentum.py
         ├─ tests/
         │  └─ test_backtester.py
         └─ codex/
            ├─ prompts/
            ├─ specs/
            ├─ staging/
            └─ experiments/
```

これで十分です。

*   `src/trading_research/`: 壊したくない共通基盤
*   `strategies/`: 採用済み戦略
*   `notebooks/`: 実行入口
*   `codex/`: 壊してよい作業場

`scripts/` と `configs/` は不要です。

* * *

再整理したコード一式
----------

### `requirements.txt`

```
pandas>=2.2
numpy>=1.26
matplotlib>=3.8
yfinance>=0.2.54
ccxt>=4.4
```

### `pyproject.toml`

```
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "trading-research"
version = "0.1.0"
description = "Research backtesting engine for ETF and crypto strategies"
requires-python = ">=3.10"
dependencies = [
  "pandas>=2.2",
  "numpy>=1.26",
  "matplotlib>=3.8",
  "yfinance>=0.2.54",
  "ccxt>=4.4",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

### `src/trading_research/__init__.py`

```
from trading_research.data import DataBundle, DataLoader
from trading_research.strategy import BaseStrategy
from trading_research.allocator import BaseAllocator, EqualWeightAllocator, TopKLongOnlyAllocator
from trading_research.backtester import ResearchBacktester, BacktestResult, WalkForwardResult

__all__ = [
    "DataBundle",
    "DataLoader",
    "BaseStrategy",
    "BaseAllocator",
    "EqualWeightAllocator",
    "TopKLongOnlyAllocator",
    "ResearchBacktester",
    "BacktestResult",
    "WalkForwardResult",
]
```

### `src/trading_research/data.py`

```
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
import ccxt

@dataclass
class DataBundle:
    prices: pd.DataFrame
    returns: pd.DataFrame
    open_: Optional[pd.DataFrame] = None
    high: Optional[pd.DataFrame] = None
    low: Optional[pd.DataFrame] = None
    close: Optional[pd.DataFrame] = None
    volume: Optional[pd.DataFrame] = None
    funding: Optional[pd.DataFrame] = None
    borrow_cost: Optional[pd.DataFrame] = None
    benchmark_returns: Optional[pd.Series] = None
    asset_class: str = "unknown"
    frequency: str = "1d"

    @property
    def calendar(self) -> pd.DatetimeIndex:
        return self.prices.index

def sanitize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy().sort_index()
    prices = prices.replace([np.inf, -np.inf], np.nan)
    return prices

def compute_returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = sanitize_prices(prices)
    returns = prices.pct_change()
    returns = returns.replace([np.inf, -np.inf], np.nan)
    return returns

class DataLoader:
    @staticmethod
    def load_etf_yfinance(
        tickers: list[str],
        start: str,
        end: Optional[str] = None,
        benchmark_ticker: Optional[str] = None,
        auto_adjust: bool = False,
        progress: bool = False,
    ) -> DataBundle:
        if not tickers:
            raise ValueError("tickers must not be empty")

        raw = yf.download(
            tickers=tickers,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
            progress=progress,
            group_by="column",
            actions=True,
            threads=True,
        )
        if raw.empty:
            raise ValueError("No ETF data downloaded from yfinance.")

        def extract_field(field: str) -> Optional[pd.DataFrame]:
            if isinstance(raw.columns, pd.MultiIndex):
                if field not in raw.columns.get_level_values(0):
                    return None
                out = raw[field].copy()
                if isinstance(out, pd.Series):
                    out = out.to_frame()
                return out.reindex(columns=tickers)
            else:
                if field not in raw.columns:
                    return None
                out = raw[[field]].copy()
                out.columns = tickers[:1]
                return out

        open_ = extract_field("Open")
        high = extract_field("High")
        low = extract_field("Low")
        close = extract_field("Close")
        adj_close = extract_field("Adj Close")
        volume = extract_field("Volume")

        prices = adj_close.copy() if adj_close is not None else close.copy()
        prices = sanitize_prices(prices)
        returns = compute_returns_from_prices(prices)

        benchmark_returns = None
        if benchmark_ticker is not None:
            bench = yf.download(
                tickers=benchmark_ticker,
                start=start,
                end=end,
                auto_adjust=auto_adjust,
                progress=progress,
                group_by="column",
                actions=True,
                threads=True,
            )
            if not bench.empty:
                if isinstance(bench.columns, pd.MultiIndex):
                    if "Adj Close" in bench.columns.get_level_values(0):
                        bench_px = bench["Adj Close"].iloc[:, 0]
                    else:
                        bench_px = bench["Close"].iloc[:, 0]
                else:
                    bench_px = bench["Adj Close"] if "Adj Close" in bench.columns else bench["Close"]
                benchmark_returns = bench_px.sort_index().pct_change().reindex(prices.index)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            benchmark_returns=benchmark_returns,
            asset_class="etf",
            frequency="1d",
        )

    @staticmethod
    def load_crypto_ccxt(
        exchange_name: str,
        symbols: list[str],
        timeframe: str = "1d",
        since: Optional[str] = None,
        limit: int = 1000,
        benchmark_symbol: Optional[str] = None,
        funding_rate_fn=None,
    ) -> DataBundle:
        if not symbols:
            raise ValueError("symbols must not be empty")

        exchange_cls = getattr(ccxt, exchange_name, None)
        if exchange_cls is None:
            raise ValueError(f"Unknown ccxt exchange: {exchange_name}")

        exchange = exchange_cls({"enableRateLimit": True})

        since_ms = None
        if since is not None:
            since_ms = int(pd.Timestamp(since, tz="UTC").timestamp() * 1000)

        opens, highs, lows, closes, volumes = {}, {}, {}, {}, {}
        funding_map = {}

        for symbol in symbols:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if not ohlcv:
                raise ValueError(f"No OHLCV data for {symbol}")

            df = pd.DataFrame(
                ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
            df = df.set_index("timestamp").sort_index()

            opens[symbol] = df["open"]
            highs[symbol] = df["high"]
            lows[symbol] = df["low"]
            closes[symbol] = df["close"]
            volumes[symbol] = df["volume"]

            if funding_rate_fn is not None:
                f = funding_rate_fn(exchange, symbol, df.index)
                if f is not None:
                    funding_map[symbol] = f.reindex(df.index)

        open_df = pd.DataFrame(opens).sort_index()
        high_df = pd.DataFrame(highs).sort_index()
        low_df = pd.DataFrame(lows).sort_index()
        close_df = pd.DataFrame(closes).sort_index()
        volume_df = pd.DataFrame(volumes).sort_index()

        prices = sanitize_prices(close_df)
        returns = compute_returns_from_prices(prices)

        funding_df = None
        if funding_map:
            funding_df = pd.DataFrame(funding_map).sort_index().reindex_like(prices)

        benchmark_returns = None
        if benchmark_symbol is not None:
            bench_ohlcv = exchange.fetch_ohlcv(benchmark_symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if bench_ohlcv:
                bench_df = pd.DataFrame(
                    bench_ohlcv,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )
                bench_df["timestamp"] = pd.to_datetime(bench_df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
                bench_df = bench_df.set_index("timestamp").sort_index()
                benchmark_returns = bench_df["close"].pct_change().reindex(prices.index)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_df,
            high=high_df,
            low=low_df,
            close=close_df,
            volume=volume_df,
            funding=funding_df,
            benchmark_returns=benchmark_returns,
            asset_class="crypto",
            frequency=timeframe,
        )
```

### `src/trading_research/strategy.py`

```
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

from trading_research.data import DataBundle

class BaseStrategy(ABC):
    def fit(self, train_data: DataBundle) -> None:
        return

    def prepare_features(self, data: DataBundle) -> Dict[str, pd.DataFrame]:
        return {}

    @abstractmethod
    def generate_scores(
        self,
        data: DataBundle,
        features: Dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        raise NotImplementedError
```

### `src/trading_research/allocator.py`

```
from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd

from trading_research.data import DataBundle

class BaseAllocator(ABC):
    def fit(self, train_data: DataBundle, train_scores: pd.DataFrame) -> None:
        return

    @abstractmethod
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        raise NotImplementedError

class EqualWeightAllocator(BaseAllocator):
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        valid = scores.notna() & data.prices.notna()
        denom = valid.sum(axis=1).replace(0, np.nan)
        w = valid.astype(float).div(denom, axis=0)
        return w.fillna(0.0)

class TopKLongOnlyAllocator(BaseAllocator):
    def __init__(self, k: int = 3):
        if k <= 0:
            raise ValueError("k must be positive")
        self.k = k

    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        s = scores.where(data.prices.notna())
        ranks = s.rank(axis=1, ascending=False, method="first")
        selected = ranks <= self.k
        denom = selected.sum(axis=1).replace(0, np.nan)
        w = selected.astype(float).div(denom, axis=0)
        return w.fillna(0.0)
```

### `src/trading_research/analytics.py`

```
from __future__ import annotations

import numpy as np
import pandas as pd

def annualization_factor(frequency: str) -> int:
    mapping = {
        "1d": 252,
        "1h": 24 * 365,
        "4h": 6 * 365,
        "1w": 52,
        "1m": 12,
    }
    return mapping.get(frequency, 252)

def compute_drawdown(equity_curve: pd.Series) -> pd.Series:
    running_max = equity_curve.cummax()
    return equity_curve / running_max - 1.0

def compute_stats(
    portfolio_returns: pd.Series,
    equity_curve: pd.Series,
    turnover: pd.Series,
    frequency: str,
    benchmark_returns: pd.Series | None = None,
    active_returns: pd.Series | None = None,
    annualization: int | None = None,
) -> pd.Series:
    r = portfolio_returns.dropna()
    if len(r) == 0:
        return pd.Series(dtype=float)

    ann = annualization if annualization is not None else annualization_factor(frequency)

    mean_ret = r.mean()
    vol = r.std(ddof=0)
    ann_ret = (1.0 + r).prod() ** (ann / max(len(r), 1)) - 1.0
    ann_vol = vol * np.sqrt(ann) if pd.notna(vol) else np.nan
    sharpe = (mean_ret / vol) * np.sqrt(ann) if (pd.notna(vol) and vol > 0) else np.nan

    dd = compute_drawdown(equity_curve)
    max_dd = dd.min()
    calmar = ann_ret / abs(max_dd) if pd.notna(max_dd) and max_dd < 0 else np.nan

    out = {
        "total_return": equity_curve.iloc[-1] - 1.0,
        "annual_return": ann_ret,
        "annual_volatility": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "hit_ratio": (r > 0).mean(),
        "average_turnover": turnover.mean(),
        "num_periods": len(r),
    }

    if benchmark_returns is not None:
        b = benchmark_returns.reindex(r.index).dropna()
        if len(b) > 0:
            out["benchmark_annual_return"] = (1.0 + b).prod() ** (ann / max(len(b), 1)) - 1.0
            out["benchmark_annual_volatility"] = b.std(ddof=0) * np.sqrt(ann)

    if active_returns is not None:
        a = active_returns.reindex(r.index).dropna()
        if len(a) > 0:
            te = a.std(ddof=0) * np.sqrt(ann)
            ir = (a.mean() / a.std(ddof=0)) * np.sqrt(ann) if a.std(ddof=0) > 0 else np.nan
            out["tracking_error"] = te
            out["information_ratio"] = ir
            out["active_return_annual"] = (1.0 + a).prod() ** (ann / max(len(a), 1)) - 1.0

    return pd.Series(out)
```

### `src/trading_research/backtester.py`

```
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

import pandas as pd

from trading_research.data import DataBundle
from trading_research.strategy import BaseStrategy
from trading_research.allocator import BaseAllocator
from trading_research.analytics import compute_stats

@dataclass
class BacktestResult:
    scores: pd.DataFrame
    weights_raw: pd.DataFrame
    weights_executed: pd.DataFrame
    asset_returns_gross: pd.DataFrame
    portfolio_returns: pd.Series
    benchmark_returns: Optional[pd.Series]
    active_returns: Optional[pd.Series]
    equity_curve: pd.Series
    benchmark_equity_curve: Optional[pd.Series]
    active_equity_curve: Optional[pd.Series]
    turnover: pd.Series
    fees: pd.Series
    rebalance_mask: pd.Series
    stats: pd.Series

@dataclass
class WalkForwardSliceResult:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    result: BacktestResult

@dataclass
class WalkForwardResult:
    slices: List[WalkForwardSliceResult]
    stitched_returns: pd.Series
    stitched_equity_curve: pd.Series
    stitched_benchmark_returns: Optional[pd.Series]
    stitched_active_returns: Optional[pd.Series]
    stats: pd.Series

def make_rebalance_mask(index: pd.DatetimeIndex, rule: str = "D") -> pd.Series:
    idx = pd.DatetimeIndex(index)
    mask = pd.Series(False, index=idx)

    if rule == "D":
        mask[:] = True
        return mask

    if rule.startswith("W-"):
        grp = idx.to_series().dt.to_period("W-" + rule.split("-")[1])
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    if rule == "M":
        grp = idx.to_series().dt.to_period("M")
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    if rule == "Q":
        grp = idx.to_series().dt.to_period("Q")
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    raise ValueError("Unsupported rebalance rule. Use 'D', 'W-FRI', 'M', or 'Q'.")

def apply_rebalance_rule(weights_raw: pd.DataFrame, rebalance_mask: pd.Series) -> pd.DataFrame:
    weights_raw = weights_raw.copy()
    rebalance_mask = rebalance_mask.reindex(weights_raw.index).fillna(False)

    out = pd.DataFrame(index=weights_raw.index, columns=weights_raw.columns, dtype=float)
    prev = pd.Series(0.0, index=weights_raw.columns)

    for dt in weights_raw.index:
        if rebalance_mask.loc[dt]:
            w = weights_raw.loc[dt].fillna(0.0)
            s = w.sum()
            prev = (w / s) if s > 0 else pd.Series(0.0, index=weights_raw.columns)
        out.loc[dt] = prev

    return out.fillna(0.0)

class ResearchBacktester:
    def __init__(
        self,
        fee_bps: float = 0.0,
        rebalance_rule: str = "D",
        annualization: int | None = None,
    ):
        self.fee_bps = fee_bps
        self.rebalance_rule = rebalance_rule
        self.annualization = annualization

    def run(
        self,
        strategy: BaseStrategy,
        allocator: BaseAllocator,
        data: DataBundle,
    ) -> BacktestResult:
        features = strategy.prepare_features(data)
        scores = strategy.generate_scores(data, features)
        scores = scores.reindex(index=data.calendar, columns=data.prices.columns)

        weights_raw = allocator.allocate(scores, data)
        weights_raw = weights_raw.reindex(index=data.calendar, columns=data.prices.columns).fillna(0.0)

        rebalance_mask = make_rebalance_mask(data.calendar, self.rebalance_rule)
        weights_rebalanced = apply_rebalance_rule(weights_raw, rebalance_mask)

        weights_executed = weights_rebalanced.shift(1).fillna(0.0)

        asset_returns_gross = data.returns.copy()
        if data.funding is not None:
            asset_returns_gross = asset_returns_gross.add(
                data.funding.reindex_like(asset_returns_gross).fillna(0.0),
                fill_value=0.0,
            )

        if data.borrow_cost is not None:
            asset_returns_gross = asset_returns_gross.sub(
                data.borrow_cost.reindex_like(asset_returns_gross).fillna(0.0),
                fill_value=0.0,
            )

        turnover = (weights_executed - weights_executed.shift(1).fillna(0.0)).abs().sum(axis=1)
        fees = turnover * (self.fee_bps / 1e4)

        portfolio_returns = (weights_executed * asset_returns_gross.fillna(0.0)).sum(axis=1) - fees
        equity_curve = (1.0 + portfolio_returns.fillna(0.0)).cumprod()

        benchmark_returns = None
        benchmark_equity_curve = None
        active_returns = None
        active_equity_curve = None

        if data.benchmark_returns is not None:
            benchmark_returns = data.benchmark_returns.reindex(portfolio_returns.index).fillna(0.0)
            benchmark_equity_curve = (1.0 + benchmark_returns).cumprod()
            active_returns = portfolio_returns - benchmark_returns
            active_equity_curve = (1.0 + active_returns.fillna(0.0)).cumprod()

        stats = compute_stats(
            portfolio_returns=portfolio_returns,
            equity_curve=equity_curve,
            turnover=turnover,
            frequency=data.frequency,
            benchmark_returns=benchmark_returns,
            active_returns=active_returns,
            annualization=self.annualization,
        )

        return BacktestResult(
            scores=scores,
            weights_raw=weights_raw,
            weights_executed=weights_executed,
            asset_returns_gross=asset_returns_gross,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            active_returns=active_returns,
            equity_curve=equity_curve,
            benchmark_equity_curve=benchmark_equity_curve,
            active_equity_curve=active_equity_curve,
            turnover=turnover,
            fees=fees,
            rebalance_mask=rebalance_mask,
            stats=stats,
        )

    def walk_forward(
        self,
        strategy: BaseStrategy,
        allocator: BaseAllocator,
        data: DataBundle,
        train_periods: int,
        test_periods: int,
        step_periods: int | None = None,
        warmup_bars: int = 0,
    ) -> WalkForwardResult:
        idx = data.calendar
        if step_periods is None:
            step_periods = test_periods

        slices: list[WalkForwardSliceResult] = []
        stitched_returns = []
        stitched_bench = []
        stitched_active = []

        start_i = max(warmup_bars, train_periods)
        while True:
            train_start_i = start_i - train_periods
            train_end_i = start_i - 1
            test_start_i = start_i
            test_end_i = min(start_i + test_periods - 1, len(idx) - 1)

            if test_start_i >= len(idx):
                break

            train_index = idx[train_start_i: train_end_i + 1]
            test_index = idx[test_start_i: test_end_i + 1]

            train_data = self.slice_data(data, train_index)
            test_data = self.slice_data(data, test_index)

            strategy.fit(train_data)
            train_features = strategy.prepare_features(train_data)
            train_scores = strategy.generate_scores(train_data, train_features)
            allocator.fit(train_data, train_scores)

            result = self.run(strategy, allocator, test_data)

            slices.append(
                WalkForwardSliceResult(
                    train_start=train_index[0],
                    train_end=train_index[-1],
                    test_start=test_index[0],
                    test_end=test_index[-1],
                    result=result,
                )
            )

            stitched_returns.append(result.portfolio_returns)
            if result.benchmark_returns is not None:
                stitched_bench.append(result.benchmark_returns)
            if result.active_returns is not None:
                stitched_active.append(result.active_returns)

            if test_end_i == len(idx) - 1:
                break

            start_i += step_periods

        stitched_returns_s = pd.concat(stitched_returns).sort_index()
        stitched_returns_s = stitched_returns_s[~stitched_returns_s.index.duplicated(keep="first")]
        stitched_equity = (1.0 + stitched_returns_s.fillna(0.0)).cumprod()

        stitched_bench_s = None
        if stitched_bench:
            stitched_bench_s = pd.concat(stitched_bench).sort_index()
            stitched_bench_s = stitched_bench_s[~stitched_bench_s.index.duplicated(keep="first")]

        stitched_active_s = None
        if stitched_active:
            stitched_active_s = pd.concat(stitched_active).sort_index()
            stitched_active_s = stitched_active_s[~stitched_active_s.index.duplicated(keep="first")]

        stats = compute_stats(
            portfolio_returns=stitched_returns_s,
            equity_curve=stitched_equity,
            turnover=pd.Series(0.0, index=stitched_returns_s.index),
            frequency=data.frequency,
            benchmark_returns=stitched_bench_s,
            active_returns=stitched_active_s,
            annualization=self.annualization,
        )

        return WalkForwardResult(
            slices=slices,
            stitched_returns=stitched_returns_s,
            stitched_equity_curve=stitched_equity,
            stitched_benchmark_returns=stitched_bench_s,
            stitched_active_returns=stitched_active_s,
            stats=stats,
        )

    @staticmethod
    def slice_data(data: DataBundle, index: pd.Index) -> DataBundle:
        return DataBundle(
            prices=data.prices.reindex(index),
            returns=data.returns.reindex(index),
            open_=None if data.open_ is None else data.open_.reindex(index),
            high=None if data.high is None else data.high.reindex(index),
            low=None if data.low is None else data.low.reindex(index),
            close=None if data.close is None else data.close.reindex(index),
            volume=None if data.volume is None else data.volume.reindex(index),
            funding=None if data.funding is None else data.funding.reindex(index),
            borrow_cost=None if data.borrow_cost is None else data.borrow_cost.reindex(index),
            benchmark_returns=None if data.benchmark_returns is None else data.benchmark_returns.reindex(index),
            asset_class=data.asset_class,
            frequency=data.frequency,
        )
```

### `src/trading_research/plotting.py`

```
from __future__ import annotations

import matplotlib.pyplot as plt

from trading_research.analytics import compute_drawdown
from trading_research.backtester import BacktestResult

def plot_equity(result: BacktestResult, title: str = "Equity Curve") -> None:
    plt.figure(figsize=(12, 4))
    result.equity_curve.plot(label="Strategy")
    if result.benchmark_equity_curve is not None:
        result.benchmark_equity_curve.plot(label="Benchmark")
    plt.title(title)
    plt.ylabel("Cumulative value")
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_drawdown(result: BacktestResult, title: str = "Drawdown") -> None:
    dd = compute_drawdown(result.equity_curve)
    plt.figure(figsize=(12, 4))
    dd.plot()
    plt.title(title)
    plt.ylabel("Drawdown")
    plt.tight_layout()
    plt.show()

def plot_weights(result: BacktestResult, last_n: int = 100, title: str = "Executed Weights") -> None:
    result.weights_executed.tail(last_n).plot.area(figsize=(12, 5))
    plt.title(title)
    plt.ylabel("Weight")
    plt.tight_layout()
    plt.show()
```

### `strategies/__init__.py`

```
# empty
```

### `strategies/buy_and_hold.py`

```
from __future__ import annotations

import pandas as pd

from trading_research.strategy import BaseStrategy
from trading_research.data import DataBundle

class BuyAndHoldStrategy(BaseStrategy):
    def generate_scores(self, data: DataBundle, features: dict[str, pd.DataFrame]) -> pd.DataFrame:
        scores = pd.DataFrame(1.0, index=data.calendar, columns=data.prices.columns)
        scores = scores.where(data.prices.notna())
        return scores

def build_strategy(**kwargs) -> BuyAndHoldStrategy:
    return BuyAndHoldStrategy()
```

### `strategies/cross_sectional_momentum.py`

```
from __future__ import annotations

import pandas as pd

from trading_research.strategy import BaseStrategy
from trading_research.data import DataBundle

class CrossSectionalMomentumStrategy(BaseStrategy):
    def __init__(self, lookback: int = 126, skip: int = 21, min_history: int | None = None):
        self.lookback = lookback
        self.skip = skip
        self.min_history = min_history if min_history is not None else lookback + skip

    def prepare_features(self, data: DataBundle) -> dict[str, pd.DataFrame]:
        px = data.prices.copy()
        past = px.shift(self.skip)
        mom = past / past.shift(self.lookback) - 1.0
        valid_hist = px.notna().rolling(self.min_history).sum() >= self.min_history
        mom = mom.where(valid_hist)
        return {"momentum": mom}

    def generate_scores(self, data: DataBundle, features: dict[str, pd.DataFrame]) -> pd.DataFrame:
        scores = features["momentum"].copy()
        scores = scores.where(data.prices.notna())
        return scores

def build_strategy(
    lookback: int = 126,
    skip: int = 21,
    min_history: int | None = None,
    **kwargs,
) -> CrossSectionalMomentumStrategy:
    return CrossSectionalMomentumStrategy(
        lookback=lookback,
        skip=skip,
        min_history=min_history,
    )
```

* * *

notebook での最小実行例
----------------

### ETF の単発バックテスト

```
from importlib import import_module

from trading_research.data import DataLoader
from trading_research.allocator import TopKLongOnlyAllocator
from trading_research.backtester import ResearchBacktester
from trading_research.plotting import plot_equity, plot_drawdown, plot_weights

data = DataLoader.load_etf_yfinance(
    tickers=["SPY", "QQQ", "IWM", "TLT", "GLD"],
    start="2015-01-01",
    benchmark_ticker="SPY",
)

strategy_mod = import_module("strategies.cross_sectional_momentum")
strategy = strategy_mod.build_strategy(
    lookback=126,
    skip=21,
    min_history=147,
)

allocator = TopKLongOnlyAllocator(k=2)

bt = ResearchBacktester(
    fee_bps=5.0,
    rebalance_rule="M",
    annualization=252,
)

result = bt.run(strategy, allocator, data)

print(result.stats.round(4))
plot_equity(result, title="ETF momentum monthly")
plot_drawdown(result, title="ETF momentum drawdown")
plot_weights(result, title="ETF momentum weights")
```

### crypto の単発バックテスト

```
from importlib import import_module

from trading_research.data import DataLoader
from trading_research.allocator import TopKLongOnlyAllocator
from trading_research.backtester import ResearchBacktester
from trading_research.plotting import plot_equity

data = DataLoader.load_crypto_ccxt(
    exchange_name="binance",
    symbols=["BTC/USDT", "ETH/USDT", "SOL/USDT"],
    timeframe="1d",
    since="2022-01-01",
    limit=1000,
    benchmark_symbol="BTC/USDT",
)

strategy_mod = import_module("strategies.cross_sectional_momentum")
strategy = strategy_mod.build_strategy(
    lookback=60,
    skip=7,
    min_history=67,
)

allocator = TopKLongOnlyAllocator(k=1)

bt = ResearchBacktester(
    fee_bps=10.0,
    rebalance_rule="W-FRI",
    annualization=252,
)

result = bt.run(strategy, allocator, data)

print(result.stats.round(4))
plot_equity(result, title="Crypto momentum weekly")
```

### walk-forward

```
wf = bt.walk_forward(
    strategy=strategy,
    allocator=allocator,
    data=data,
    train_periods=365,
    test_periods=90,
    step_periods=90,
    warmup_bars=67,
)

print(wf.stats.round(4))
wf.stitched_equity_curve.plot(figsize=(12, 4), title="Walk-forward OOS")
```

* * *

この形にした理由
--------

今回の要件だと、`scripts/` と `configs/` は確かに不要です。  
ノートブック実行なら、設定はセル上で直接与えた方が速いです。

その代わり、壊したくない部分はちゃんと分離しています。

*   `src/trading_research/` は基盤
*   `strategies/` は採用戦略
*   `codex/` は破壊OK

この3分割が最小で一番効きます。

必要なら次に、これをさらに削って  
**`src/trading_research/` を 4 ファイル程度まで圧縮した超最小版**  
にもできます。

## Prompt:
実装を基本の最小構成にして

## Response:
思考時間: 2 ～ 3 秒

はい。  
この要件なら、**本当に必要なものだけ**に絞った「基本の最小構成」は次です。

ディレクトリ構造
--------

```
workspace/
├─ envs/
│  └─ trading-research/
└─ projects/
   └─ finance/
      └─ trading-research/
         ├─ pyproject.toml
         ├─ requirements.txt
         ├─ notebooks/
         ├─ src/
         │  └─ trading_research/
         │     ├─ __init__.py
         │     ├─ core.py
         │     └─ plotting.py
         ├─ strategies/
         │  ├─ __init__.py
         │  ├─ buy_and_hold.py
         │  └─ cross_sectional_momentum.py
         └─ codex/
            ├─ staging/
            └─ experiments/
```

これが最小です。

*   `src/trading_research/core.py` に基盤を集約
*   `src/trading_research/plotting.py` に可視化だけ分離
*   `strategies/` に戦略
*   `notebooks/` から実行
*   `codex/` は隔離作業場

`data/`, `results/`, `tests/` も後から追加できますが、最初はなくても始められます。

* * *

`requirements.txt`
------------------

```
pandas>=2.2
numpy>=1.26
matplotlib>=3.8
yfinance>=0.2.54
ccxt>=4.4
```

* * *

`pyproject.toml`
----------------

```
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "trading-research"
version = "0.1.0"
description = "Minimal research backtesting engine for ETF and crypto strategies"
requires-python = ">=3.10"
dependencies = [
  "pandas>=2.2",
  "numpy>=1.26",
  "matplotlib>=3.8",
  "yfinance>=0.2.54",
  "ccxt>=4.4",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

* * *

`src/trading_research/__init__.py`
----------------------------------

```
from trading_research.core import (
    DataBundle,
    DataLoader,
    BaseStrategy,
    BaseAllocator,
    EqualWeightAllocator,
    TopKLongOnlyAllocator,
    BacktestResult,
    WalkForwardResult,
    ResearchBacktester,
)

__all__ = [
    "DataBundle",
    "DataLoader",
    "BaseStrategy",
    "BaseAllocator",
    "EqualWeightAllocator",
    "TopKLongOnlyAllocator",
    "BacktestResult",
    "WalkForwardResult",
    "ResearchBacktester",
]
```

* * *

`src/trading_research/core.py`
------------------------------

```
from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, Dict, List

import numpy as np
import pandas as pd
import yfinance as yf
import ccxt

# ============================================================
# Data
# ============================================================

@dataclass
class DataBundle:
    prices: pd.DataFrame
    returns: pd.DataFrame
    open_: Optional[pd.DataFrame] = None
    high: Optional[pd.DataFrame] = None
    low: Optional[pd.DataFrame] = None
    close: Optional[pd.DataFrame] = None
    volume: Optional[pd.DataFrame] = None
    funding: Optional[pd.DataFrame] = None
    benchmark_returns: Optional[pd.Series] = None
    asset_class: str = "unknown"
    frequency: str = "1d"

    @property
    def calendar(self) -> pd.DatetimeIndex:
        return self.prices.index

def sanitize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy().sort_index()
    prices = prices.replace([np.inf, -np.inf], np.nan)
    return prices

def compute_returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    prices = sanitize_prices(prices)
    returns = prices.pct_change()
    returns = returns.replace([np.inf, -np.inf], np.nan)
    return returns

class DataLoader:
    @staticmethod
    def load_etf_yfinance(
        tickers: list[str],
        start: str,
        end: Optional[str] = None,
        benchmark_ticker: Optional[str] = None,
        auto_adjust: bool = False,
        progress: bool = False,
    ) -> DataBundle:
        if not tickers:
            raise ValueError("tickers must not be empty")

        raw = yf.download(
            tickers=tickers,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
            progress=progress,
            group_by="column",
            actions=True,
            threads=True,
        )
        if raw.empty:
            raise ValueError("No ETF data downloaded from yfinance.")

        def extract_field(field: str) -> Optional[pd.DataFrame]:
            if isinstance(raw.columns, pd.MultiIndex):
                if field not in raw.columns.get_level_values(0):
                    return None
                out = raw[field].copy()
                if isinstance(out, pd.Series):
                    out = out.to_frame()
                return out.reindex(columns=tickers)
            else:
                if field not in raw.columns:
                    return None
                out = raw[[field]].copy()
                out.columns = tickers[:1]
                return out

        open_ = extract_field("Open")
        high = extract_field("High")
        low = extract_field("Low")
        close = extract_field("Close")
        adj_close = extract_field("Adj Close")
        volume = extract_field("Volume")

        prices = adj_close.copy() if adj_close is not None else close.copy()
        prices = sanitize_prices(prices)
        returns = compute_returns_from_prices(prices)

        benchmark_returns = None
        if benchmark_ticker is not None:
            bench = yf.download(
                tickers=benchmark_ticker,
                start=start,
                end=end,
                auto_adjust=auto_adjust,
                progress=progress,
                group_by="column",
                actions=True,
                threads=True,
            )
            if not bench.empty:
                if isinstance(bench.columns, pd.MultiIndex):
                    if "Adj Close" in bench.columns.get_level_values(0):
                        bench_px = bench["Adj Close"].iloc[:, 0]
                    else:
                        bench_px = bench["Close"].iloc[:, 0]
                else:
                    bench_px = bench["Adj Close"] if "Adj Close" in bench.columns else bench["Close"]
                benchmark_returns = bench_px.sort_index().pct_change().reindex(prices.index)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            benchmark_returns=benchmark_returns,
            asset_class="etf",
            frequency="1d",
        )

    @staticmethod
    def load_crypto_ccxt(
        exchange_name: str,
        symbols: list[str],
        timeframe: str = "1d",
        since: Optional[str] = None,
        limit: int = 1000,
        benchmark_symbol: Optional[str] = None,
        funding_rate_fn=None,
    ) -> DataBundle:
        if not symbols:
            raise ValueError("symbols must not be empty")

        exchange_cls = getattr(ccxt, exchange_name, None)
        if exchange_cls is None:
            raise ValueError(f"Unknown ccxt exchange: {exchange_name}")

        exchange = exchange_cls({"enableRateLimit": True})

        since_ms = None
        if since is not None:
            since_ms = int(pd.Timestamp(since, tz="UTC").timestamp() * 1000)

        opens, highs, lows, closes, volumes = {}, {}, {}, {}, {}
        funding_map = {}

        for symbol in symbols:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if not ohlcv:
                raise ValueError(f"No OHLCV data for {symbol}")

            df = pd.DataFrame(
                ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
            df = df.set_index("timestamp").sort_index()

            opens[symbol] = df["open"]
            highs[symbol] = df["high"]
            lows[symbol] = df["low"]
            closes[symbol] = df["close"]
            volumes[symbol] = df["volume"]

            if funding_rate_fn is not None:
                f = funding_rate_fn(exchange, symbol, df.index)
                if f is not None:
                    funding_map[symbol] = f.reindex(df.index)

        open_df = pd.DataFrame(opens).sort_index()
        high_df = pd.DataFrame(highs).sort_index()
        low_df = pd.DataFrame(lows).sort_index()
        close_df = pd.DataFrame(closes).sort_index()
        volume_df = pd.DataFrame(volumes).sort_index()

        prices = sanitize_prices(close_df)
        returns = compute_returns_from_prices(prices)

        funding_df = None
        if funding_map:
            funding_df = pd.DataFrame(funding_map).sort_index().reindex_like(prices)

        benchmark_returns = None
        if benchmark_symbol is not None:
            bench_ohlcv = exchange.fetch_ohlcv(benchmark_symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if bench_ohlcv:
                bench_df = pd.DataFrame(
                    bench_ohlcv,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )
                bench_df["timestamp"] = pd.to_datetime(bench_df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
                bench_df = bench_df.set_index("timestamp").sort_index()
                benchmark_returns = bench_df["close"].pct_change().reindex(prices.index)

        return DataBundle(
            prices=prices,
            returns=returns,
            open_=open_df,
            high=high_df,
            low=low_df,
            close=close_df,
            volume=volume_df,
            funding=funding_df,
            benchmark_returns=benchmark_returns,
            asset_class="crypto",
            frequency=timeframe,
        )

# ============================================================
# Strategy / Allocator
# ============================================================

class BaseStrategy(ABC):
    def fit(self, train_data: DataBundle) -> None:
        return

    def prepare_features(self, data: DataBundle) -> Dict[str, pd.DataFrame]:
        return {}

    @abstractmethod
    def generate_scores(
        self,
        data: DataBundle,
        features: Dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        raise NotImplementedError

class BaseAllocator(ABC):
    def fit(self, train_data: DataBundle, train_scores: pd.DataFrame) -> None:
        return

    @abstractmethod
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        raise NotImplementedError

class EqualWeightAllocator(BaseAllocator):
    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        valid = scores.notna() & data.prices.notna()
        denom = valid.sum(axis=1).replace(0, np.nan)
        w = valid.astype(float).div(denom, axis=0)
        return w.fillna(0.0)

class TopKLongOnlyAllocator(BaseAllocator):
    def __init__(self, k: int = 3):
        if k <= 0:
            raise ValueError("k must be positive")
        self.k = k

    def allocate(self, scores: pd.DataFrame, data: DataBundle) -> pd.DataFrame:
        s = scores.where(data.prices.notna())
        ranks = s.rank(axis=1, ascending=False, method="first")
        selected = ranks <= self.k
        denom = selected.sum(axis=1).replace(0, np.nan)
        w = selected.astype(float).div(denom, axis=0)
        return w.fillna(0.0)

# ============================================================
# Analytics
# ============================================================

def annualization_factor(frequency: str) -> int:
    mapping = {
        "1d": 252,
        "1h": 24 * 365,
        "4h": 6 * 365,
        "1w": 52,
        "1m": 12,
    }
    return mapping.get(frequency, 252)

def compute_drawdown(equity_curve: pd.Series) -> pd.Series:
    running_max = equity_curve.cummax()
    return equity_curve / running_max - 1.0

def compute_stats(
    portfolio_returns: pd.Series,
    equity_curve: pd.Series,
    turnover: pd.Series,
    frequency: str,
    benchmark_returns: pd.Series | None = None,
    active_returns: pd.Series | None = None,
    annualization: int | None = None,
) -> pd.Series:
    r = portfolio_returns.dropna()
    if len(r) == 0:
        return pd.Series(dtype=float)

    ann = annualization if annualization is not None else annualization_factor(frequency)

    mean_ret = r.mean()
    vol = r.std(ddof=0)
    ann_ret = (1.0 + r).prod() ** (ann / max(len(r), 1)) - 1.0
    ann_vol = vol * np.sqrt(ann) if pd.notna(vol) else np.nan
    sharpe = (mean_ret / vol) * np.sqrt(ann) if (pd.notna(vol) and vol > 0) else np.nan

    dd = compute_drawdown(equity_curve)
    max_dd = dd.min()
    calmar = ann_ret / abs(max_dd) if pd.notna(max_dd) and max_dd < 0 else np.nan

    out = {
        "total_return": equity_curve.iloc[-1] - 1.0,
        "annual_return": ann_ret,
        "annual_volatility": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "hit_ratio": (r > 0).mean(),
        "average_turnover": turnover.mean(),
        "num_periods": len(r),
    }

    if benchmark_returns is not None:
        b = benchmark_returns.reindex(r.index).dropna()
        if len(b) > 0:
            out["benchmark_annual_return"] = (1.0 + b).prod() ** (ann / max(len(b), 1)) - 1.0
            out["benchmark_annual_volatility"] = b.std(ddof=0) * np.sqrt(ann)

    if active_returns is not None:
        a = active_returns.reindex(r.index).dropna()
        if len(a) > 0:
            te = a.std(ddof=0) * np.sqrt(ann)
            ir = (a.mean() / a.std(ddof=0)) * np.sqrt(ann) if a.std(ddof=0) > 0 else np.nan
            out["tracking_error"] = te
            out["information_ratio"] = ir
            out["active_return_annual"] = (1.0 + a).prod() ** (ann / max(len(a), 1)) - 1.0

    return pd.Series(out)

# ============================================================
# Backtester
# ============================================================

@dataclass
class BacktestResult:
    scores: pd.DataFrame
    weights_raw: pd.DataFrame
    weights_executed: pd.DataFrame
    portfolio_returns: pd.Series
    equity_curve: pd.Series
    benchmark_returns: Optional[pd.Series]
    benchmark_equity_curve: Optional[pd.Series]
    active_returns: Optional[pd.Series]
    turnover: pd.Series
    fees: pd.Series
    stats: pd.Series

@dataclass
class WalkForwardSliceResult:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    result: BacktestResult

@dataclass
class WalkForwardResult:
    slices: List[WalkForwardSliceResult]
    stitched_returns: pd.Series
    stitched_equity_curve: pd.Series
    stats: pd.Series

def make_rebalance_mask(index: pd.DatetimeIndex, rule: str = "D") -> pd.Series:
    idx = pd.DatetimeIndex(index)
    mask = pd.Series(False, index=idx)

    if rule == "D":
        mask[:] = True
        return mask

    if rule.startswith("W-"):
        grp = idx.to_series().dt.to_period("W-" + rule.split("-")[1])
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    if rule == "M":
        grp = idx.to_series().dt.to_period("M")
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    if rule == "Q":
        grp = idx.to_series().dt.to_period("Q")
        last_dates = grp.groupby(grp).apply(lambda x: x.index.max())
        mask.loc[last_dates.values] = True
        return mask

    raise ValueError("Unsupported rebalance rule. Use 'D', 'W-FRI', 'M', or 'Q'.")

def apply_rebalance_rule(weights_raw: pd.DataFrame, rebalance_mask: pd.Series) -> pd.DataFrame:
    weights_raw = weights_raw.copy()
    rebalance_mask = rebalance_mask.reindex(weights_raw.index).fillna(False)

    out = pd.DataFrame(index=weights_raw.index, columns=weights_raw.columns, dtype=float)
    prev = pd.Series(0.0, index=weights_raw.columns)

    for dt in weights_raw.index:
        if rebalance_mask.loc[dt]:
            w = weights_raw.loc[dt].fillna(0.0)
            s = w.sum()
            prev = (w / s) if s > 0 else pd.Series(0.0, index=weights_raw.columns)
        out.loc[dt] = prev

    return out.fillna(0.0)

class ResearchBacktester:
    def __init__(
        self,
        fee_bps: float = 0.0,
        rebalance_rule: str = "D",
        annualization: int | None = None,
    ):
        self.fee_bps = fee_bps
        self.rebalance_rule = rebalance_rule
        self.annualization = annualization

    def run(
        self,
        strategy: BaseStrategy,
        allocator: BaseAllocator,
        data: DataBundle,
    ) -> BacktestResult:
        features = strategy.prepare_features(data)
        scores = strategy.generate_scores(data, features)
        scores = scores.reindex(index=data.calendar, columns=data.prices.columns)

        weights_raw = allocator.allocate(scores, data)
        weights_raw = weights_raw.reindex(index=data.calendar, columns=data.prices.columns).fillna(0.0)

        rebalance_mask = make_rebalance_mask(data.calendar, self.rebalance_rule)
        weights_rebalanced = apply_rebalance_rule(weights_raw, rebalance_mask)

        # leak防止
        weights_executed = weights_rebalanced.shift(1).fillna(0.0)

        asset_returns = data.returns.copy()
        if data.funding is not None:
            asset_returns = asset_returns.add(
                data.funding.reindex_like(asset_returns).fillna(0.0),
                fill_value=0.0,
            )

        turnover = (weights_executed - weights_executed.shift(1).fillna(0.0)).abs().sum(axis=1)
        fees = turnover * (self.fee_bps / 1e4)

        portfolio_returns = (weights_executed * asset_returns.fillna(0.0)).sum(axis=1) - fees
        equity_curve = (1.0 + portfolio_returns.fillna(0.0)).cumprod()

        benchmark_returns = None
        benchmark_equity_curve = None
        active_returns = None

        if data.benchmark_returns is not None:
            benchmark_returns = data.benchmark_returns.reindex(portfolio_returns.index).fillna(0.0)
            benchmark_equity_curve = (1.0 + benchmark_returns).cumprod()
            active_returns = portfolio_returns - benchmark_returns

        stats = compute_stats(
            portfolio_returns=portfolio_returns,
            equity_curve=equity_curve,
            turnover=turnover,
            frequency=data.frequency,
            benchmark_returns=benchmark_returns,
            active_returns=active_returns,
            annualization=self.annualization,
        )

        return BacktestResult(
            scores=scores,
            weights_raw=weights_raw,
            weights_executed=weights_executed,
            portfolio_returns=portfolio_returns,
            equity_curve=equity_curve,
            benchmark_returns=benchmark_returns,
            benchmark_equity_curve=benchmark_equity_curve,
            active_returns=active_returns,
            turnover=turnover,
            fees=fees,
            stats=stats,
        )

    def walk_forward(
        self,
        strategy: BaseStrategy,
        allocator: BaseAllocator,
        data: DataBundle,
        train_periods: int,
        test_periods: int,
        step_periods: int | None = None,
        warmup_bars: int = 0,
    ) -> WalkForwardResult:
        idx = data.calendar
        if step_periods is None:
            step_periods = test_periods

        slices: list[WalkForwardSliceResult] = []
        stitched_returns = []

        start_i = max(warmup_bars, train_periods)
        while True:
            train_start_i = start_i - train_periods
            train_end_i = start_i - 1
            test_start_i = start_i
            test_end_i = min(start_i + test_periods - 1, len(idx) - 1)

            if test_start_i >= len(idx):
                break

            train_index = idx[train_start_i: train_end_i + 1]
            test_index = idx[test_start_i: test_end_i + 1]

            train_data = self.slice_data(data, train_index)
            test_data = self.slice_data(data, test_index)

            strategy.fit(train_data)
            train_features = strategy.prepare_features(train_data)
            train_scores = strategy.generate_scores(train_data, train_features)
            allocator.fit(train_data, train_scores)

            result = self.run(strategy, allocator, test_data)
            slices.append(
                WalkForwardSliceResult(
                    train_start=train_index[0],
                    train_end=train_index[-1],
                    test_start=test_index[0],
                    test_end=test_index[-1],
                    result=result,
                )
            )
            stitched_returns.append(result.portfolio_returns)

            if test_end_i == len(idx) - 1:
                break

            start_i += step_periods

        stitched_returns_s = pd.concat(stitched_returns).sort_index()
        stitched_returns_s = stitched_returns_s[~stitched_returns_s.index.duplicated(keep="first")]
        stitched_equity = (1.0 + stitched_returns_s.fillna(0.0)).cumprod()

        stats = compute_stats(
            portfolio_returns=stitched_returns_s,
            equity_curve=stitched_equity,
            turnover=pd.Series(0.0, index=stitched_returns_s.index),
            frequency=data.frequency,
            annualization=self.annualization,
        )

        return WalkForwardResult(
            slices=slices,
            stitched_returns=stitched_returns_s,
            stitched_equity_curve=stitched_equity,
            stats=stats,
        )

    @staticmethod
    def slice_data(data: DataBundle, index: pd.Index) -> DataBundle:
        return DataBundle(
            prices=data.prices.reindex(index),
            returns=data.returns.reindex(index),
            open_=None if data.open_ is None else data.open_.reindex(index),
            high=None if data.high is None else data.high.reindex(index),
            low=None if data.low is None else data.low.reindex(index),
            close=None if data.close is None else data.close.reindex(index),
            volume=None if data.volume is None else data.volume.reindex(index),
            funding=None if data.funding is None else data.funding.reindex(index),
            benchmark_returns=None if data.benchmark_returns is None else data.benchmark_returns.reindex(index),
            asset_class=data.asset_class,
            frequency=data.frequency,
        )
```

* * *

`src/trading_research/plotting.py`
----------------------------------

```
from __future__ import annotations

import matplotlib.pyplot as plt

from trading_research.core import BacktestResult, compute_drawdown

def plot_equity(result: BacktestResult, title: str = "Equity Curve") -> None:
    plt.figure(figsize=(12, 4))
    result.equity_curve.plot(label="Strategy")
    if result.benchmark_equity_curve is not None:
        result.benchmark_equity_curve.plot(label="Benchmark")
    plt.title(title)
    plt.ylabel("Cumulative value")
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_drawdown(result: BacktestResult, title: str = "Drawdown") -> None:
    dd = compute_drawdown(result.equity_curve)
    plt.figure(figsize=(12, 4))
    dd.plot()
    plt.title(title)
    plt.ylabel("Drawdown")
    plt.tight_layout()
    plt.show()

def plot_weights(result: BacktestResult, last_n: int = 100, title: str = "Executed Weights") -> None:
    result.weights_executed.tail(last_n).plot.area(figsize=(12, 5))
    plt.title(title)
    plt.ylabel("Weight")
    plt.tight_layout()
    plt.show()
```

* * *

`strategies/__init__.py`
------------------------

```
# empty
```

* * *

`strategies/buy_and_hold.py`
----------------------------

```
from __future__ import annotations

import pandas as pd

from trading_research.core import BaseStrategy, DataBundle

class BuyAndHoldStrategy(BaseStrategy):
    def generate_scores(self, data: DataBundle, features: dict[str, pd.DataFrame]) -> pd.DataFrame:
        scores = pd.DataFrame(1.0, index=data.calendar, columns=data.prices.columns)
        scores = scores.where(data.prices.notna())
        return scores

def build_strategy(**kwargs) -> BuyAndHoldStrategy:
    return BuyAndHoldStrategy()
```

* * *

`strategies/cross_sectional_momentum.py`
----------------------------------------

```
from __future__ import annotations

import pandas as pd

from trading_research.core import BaseStrategy, DataBundle

class CrossSectionalMomentumStrategy(BaseStrategy):
    def __init__(self, lookback: int = 126, skip: int = 21, min_history: int | None = None):
        self.lookback = lookback
        self.skip = skip
        self.min_history = min_history if min_history is not None else lookback + skip

    def prepare_features(self, data: DataBundle) -> dict[str, pd.DataFrame]:
        px = data.prices.copy()
        past = px.shift(self.skip)
        mom = past / past.shift(self.lookback) - 1.0
        valid_hist = px.notna().rolling(self.min_history).sum() >= self.min_history
        mom = mom.where(valid_hist)
        return {"momentum": mom}

    def generate_scores(self, data: DataBundle, features: dict[str, pd.DataFrame]) -> pd.DataFrame:
        scores = features["momentum"].copy()
        scores = scores.where(data.prices.notna())
        return scores

def build_strategy(
    lookback: int = 126,
    skip: int = 21,
    min_history: int | None = None,
    **kwargs,
) -> CrossSectionalMomentumStrategy:
    return CrossSectionalMomentumStrategy(
        lookback=lookback,
        skip=skip,
        min_history=min_history,
    )
```

* * *

notebook での最小実行例
----------------

### ETF

```
from importlib import import_module

from trading_research.core import DataLoader, TopKLongOnlyAllocator, ResearchBacktester
from trading_research.plotting import plot_equity, plot_drawdown, plot_weights

data = DataLoader.load_etf_yfinance(
    tickers=["SPY", "QQQ", "IWM", "TLT", "GLD"],
    start="2015-01-01",
    benchmark_ticker="SPY",
)

strategy_mod = import_module("strategies.cross_sectional_momentum")
strategy = strategy_mod.build_strategy(
    lookback=126,
    skip=21,
    min_history=147,
)

allocator = TopKLongOnlyAllocator(k=2)

bt = ResearchBacktester(
    fee_bps=5.0,
    rebalance_rule="M",
    annualization=252,
)

result = bt.run(strategy, allocator, data)
print(result.stats.round(4))

plot_equity(result, title="ETF momentum monthly")
plot_drawdown(result, title="ETF momentum drawdown")
plot_weights(result, title="ETF momentum weights")
```

### crypto

```
from importlib import import_module

from trading_research.core import DataLoader, TopKLongOnlyAllocator, ResearchBacktester
from trading_research.plotting import plot_equity

data = DataLoader.load_crypto_ccxt(
    exchange_name="binance",
    symbols=["BTC/USDT", "ETH/USDT", "SOL/USDT"],
    timeframe="1d",
    since="2022-01-01",
    limit=1000,
    benchmark_symbol="BTC/USDT",
)

strategy_mod = import_module("strategies.cross_sectional_momentum")
strategy = strategy_mod.build_strategy(
    lookback=60,
    skip=7,
    min_history=67,
)

allocator = TopKLongOnlyAllocator(k=1)

bt = ResearchBacktester(
    fee_bps=10.0,
    rebalance_rule="W-FRI",
    annualization=252,
)

result = bt.run(strategy, allocator, data)
print(result.stats.round(4))

plot_equity(result, title="Crypto momentum weekly")
```

### walk-forward

```
wf = bt.walk_forward(
    strategy=strategy,
    allocator=allocator,
    data=data,
    train_periods=365,
    test_periods=90,
    step_periods=90,
    warmup_bars=67,
)

print(wf.stats.round(4))
wf.stitched_equity_curve.plot(figsize=(12, 4), title="Walk-forward OOS")
```

* * *

この形なら、かなりシンプルです。  
次に増やすとしても、まずは `tests/` か `data/processed/` くらいで十分です。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)