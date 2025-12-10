# 専門家向け解説

**User:** Anonymous (kbmedphys@gmail.com)  
**Created:** 12/10/2025 17:26:39  
**Updated:** 12/10/2025 19:36:20  
**Exported:** 12/10/2025 19:47:42  
**Link:** [https://chatgpt.com/c/69392ebd-ce80-8332-a9a4-c35cddea77ab](https://chatgpt.com/c/69392ebd-ce80-8332-a9a4-c35cddea77ab)  

## Response:
思考時間: 1m 3s

以下では、3つのドキュメント（本稿 Guo (2025, RFS)「Earnings Extrapolation and Predictable Stock Market Returns」、そのオンライン付録、Guo & Wachter (2025)「Correlation neglect in asset prices」）を相互に関連づけながら、実証事実と数理モデルの両面から専門家向けに整理します。

* * *

1\. 全体像と3文献の位置づけ
----------------

3本はいずれも「四半期決算サイクル」と「月次株式リターンの系列相関」に焦点を当てています。

*   コアの実証事実  
    企業決算が集中する「newsy month」（四半期の第1月：1,4,7,10月）と、それに続く月（第2・第3月）のリターンには、\*\*継続（momentum）→反転（reversal）\*\*という特異なパターンがある。
*   Guo (RFS) 本文  
    主に「**earnings extrapolation + parameter compression（パラメータ圧縮）**」という行動仮説で、このパターン全体（複数期にわたる継続・反転）を説明する。
*   オンライン付録  
    そのうち特に「第2月リターンが次の第1月リターンを負に予測する」部分が、**correlation neglect** によっても自然に説明できることを示し、両メカニズムを識別する補助実証を与える。さらにカレンダー・ラグやグローバル・クロスセクション、定量的 “newsyness” 指標などのロバストネスチェックを整理している。
*   Guo & Wachter (2025, SSRN)  
    別稿として correlation neglect に特化したシンプルな**3期ベイズモデル**を構築し、その上で aggregate / industry / survey のデータで continuation & reversal を検証する。ここでは「第1月 → 第2月（継続）」および「第2月 → 次の第1月（反転）」の2本のレッグにフォーカスしている。

したがって、

*   RFS論文：\*\*パラメータ圧縮に基づく「ファンダメンタルの誤った外挿」\*\*がメインストーリー
*   付録＋別稿：\*\*correlation neglect（繰り返しシグナルの誤認）\*\*も、決算サイクルの中で独立に観測されることを示し、両者は「別々の認知バイアスだが、同じデータ上で共存している」ことを強調

という構図になっています。

* * *

2\. 実証の出発点：決算サイクルと「newsy / non-newsy」月
--------------------------------------

### 2.1 決算サイクルの構造

*   米国企業の多くは四半期末をカレンダーの月末（3,6,9,12月）に揃えている。
    ssrn-5268329
*   しかし決算発表日は企業ごとにばらつきがあり、**四半期終了後3か月以内に分散して発表**される。
*   統計的には、四半期内の発表は概ね以下のように配分される：
    *   第1月（newsy month）：約45%
    *   第2月（repetitive month）：約48%
    *   第3月：残り少数（約8%）
        ssrn-5268329

この結果、

*   第1月：前四半期の集計的な業績（aggregate earnings）について「初めて」まとまった情報が出る → **newsy（月次のアグレゲートな新情報）**
*   第2月：同じ四半期の決算が追加で出るものの、**既に第1月で分かった情報の薄い繰り返し**（同じ四半期の earnings に基づくため） → **repetitive**
*   第3月：on-cycle 発表は少なく、news は弱い

という、情報到着の構造的な非一様性が生じます。

### 2.2 基本的なリターン予測パターン

RFS論文では、月次の市場超過リターン  $mkt_t$  について、  
「直近の new/repetitive 月のリターン  $mkt_{nr(t)}$  が、次月以降のリターンをどう予測するか」を時系列回帰で調べています。

ssrn-5268329

簡略化すると、例えば

*   **第2月（repetitive）を被説明変数に取る回帰：**
    
$$
mkt_t = \alpha + \beta \, mkt_{nr(t)} + \varepsilon_t,\quad t\text{ がrepetitive月}
$$

ここで  $nr(t)$  は直前の newsy 月（第1月）で、実証では  
 $\beta \approx 0.279 >0$ （newsy→repetitive の**正の継続**）。

ssrn-5268329

*   **第1月（newsy）を被説明変数に取る回帰：**
    
$$
mkt_t = \alpha + \beta \, mkt_{nr(t)} + \varepsilon_t,\quad t\text{ がnewsy月}
$$

ここで  $nr(t)$  は直前の repetitive 月（第2月）で、  
 $\beta \approx -0.279 <0$ （repetitive→次のnewsy の**負の反転**）。

ssrn-5268329

*   両者を統合した回帰：
    
$$
mkt_t = \alpha + \beta_1 mkt_{nr(t)} + \beta_2 mkt_{nr(t)}\cdot I_t^n + \gamma I_t^n + \varepsilon_t \tag{2}
$$

ここで  $I_t^n=1$  は newsy 月ダミー。  
 $\beta_2 \approx -0.557$  は「newsy 月と non-newsy 月での自己相関の差」を表し、  
この係数が大きく負で統計的に有意（t ≈ -4.35）であることが、本論文のキーレザルトになっています。

ssrn-5268329

さらに、このパターンは前半・後半・戦後サンプルいずれでも生じ、長期にわたる安定した現象であることが確認されています。

* * *

3\. Guo (RFS) のメインメカニズム：パラメータ圧縮による earnings extrapolation
---------------------------------------------------------

### 3.1 直感：Figure 4 の step function vs 線形近似

オンライン付録の Appendix B を含めた実証により、\*\*「あるニュース月 (0E) の earnings が、将来のニュース月 (E) と non-news 月 (L) の earnings に与える予測力」\*\*は、以下のような特徴を持つことが示されます。

*   実際の回帰係数（青丸）は、時間方向に**階段（step）状**に減衰する。
    *   E 期（newsy）で急激に落ちる
    *   L 期（non-newsy）間ではほぼフラット

これに対して、投資家は

*   認知・注意の制約から、  
    「**減衰速度は一定（線形に減衰）**」と考え、青丸に対して直線近似（赤×）を行う。
*   すなわち、E期とL期で異なる decay speed を、**平均的な速度**に「圧縮」してしまう（parameter compression）。

結果として、

*   平均的には「predictive power が時間とともに減る」という理解は合っているが、
*   \*\*newsy 月に対しては過大に extrapolate（overreaction）、non-newsy 月に対しては過小に extrapolate（underreaction）\*\*する。

これが、

*   newsy→repetitive（月）では underreaction の解消として**正の継続**、
*   repetitive→次の newsy（月）では overreaction の解消として**負の反転**

というパターンを同一メカニズムから生成する、というのが直感的なストーリーです。

### 3.2 数理モデルの構造

RFS論文のモデル部分では、上記の直感を以下のような形式で定式化しています。

1.  経済と配当
    *   離散時間  $t = 0,1,2,\dots$ 、無限期間経済。
    *   配当  $D_t$ 、その対数  $d_t = \log D_t$ 。
    *    $t$  が奇数のとき E（newsy）、偶数のとき L（non-newsy）とする。
        hhaf020
2.  キャッシュフローショック
    *   earnings（or cash flow）のイノベーションを  $u_t$ （平均0, 分散  $\sigma_u^2$  の i.i.d. 正規）とする。
    *   真の「有効な state」 $x_{t}^{act}$  は、過去の  $u_{t-j}$  の指数加重平均であり、ただし E/L に応じてウェイトが交互に変化する：
        
$$
x_t^{act} = \begin{cases} \displaystyle\sum_{j=0}^{\infty} e^{(2j)\delta} u_{t-2j}, & t \text{ odd (E)}\\ \displaystyle\sum_{j=0}^{\infty} e^{(2j+2)\delta} u_{t-(2j+1)}, & t \text{ even (L)} \end{cases} \tag{3}
$$
*   ここで  $\delta < 0$  は減衰パラメータ。E/L で指数のオフセットがズレることで、**E期に step down が集中**する構造が埋め込まれている。
    hhaf020
    3.  投資家の belief（パラメータ圧縮）
    *   投資家は指数減衰の速度を一定  $\delta$  とみなし、「期待 state」 $x_t^{exp}$  を
        
$$
x_t^{exp} = \sum_{j=0}^{\infty} e^{j\delta} u_{t-j}
$$

と想定する。

*   真の state は、実は
    
$$
x_t^{act} = e^{\mp 0.5\delta} x_t^{exp}
$$

と E/L 期でスケールが異なる（式(3) の再表記）。奇数（E）期で  $e^{-0.5\delta} > 1$ 、偶数（L）期で  $e^{0.5\delta} < 1$  となる。

hhaf020

4.  実際の配当成長
    *   対数配当成長  $db_{t+1} = d_{t+1} - \rho d_t$ （ $\rho$  は persistence）を
        
$$
db_{t+1} = x_t^{act} + u_{t+1}
$$

と置くと、E/Lで

$$
db_{t+1}= \begin{cases} e^{-0.5\delta} x_t^{exp} + u_{t+1}, & t \text{ odd (E)}\\ e^{0.5\delta} x_t^{exp} + u_{t+1}, & t \text{ even (L)} \end{cases} \tag{4}
$$

となる。

hhaf020

5.  価格付けと valuation ratio
    *   リスク中立の代表的投資家、割引因子  $r$ 。
    *    $n$  期先に期限を持つ「equity strip」の価格  $P_t^n$ 、valuation ratio を
        
$$
F_n(x_t) = \frac{P_t^n}{D_t}
$$

と定義。

*   無裁定条件
    
$$
P_t^n = E_t[r P_{t+1}^{n-1}] \quad\Rightarrow\quad F_n(x_t) = E_t\left[r F_{n-1}(x_{t+1})\frac{D_{t+1}}{D_t}\right] \tag{5}
$$
*   ここで  $x_t^{exp}, db_t$  と E/L 状態に依存する指数線形の形
    
$$
\frac{P_t^n}{D_t} = \begin{cases} \exp\left(a_1^n + b_1^n x_t^{exp} + c_1^n db_t\right), & t\text{ odd (E)}\\ \exp\left(a_0^n + b_0^n x_t^{exp} + c_0^n db_t\right), & t\text{ even (L)} \end{cases}
$$

を仮定すると、再帰式(5)から係数  $(a_i^n,b_i^n,c_i^n)$  の漸化式が得られ、閉形式で解ける（特に  $b_0^n=b_1^n=(1-\rho)(1-e^{n\delta})/(1-e^\delta)>0$ ）。

6.  リターンの分解と予測可能成分
    *   strip の1期リターン  $R_{n,t+1}$  の対数は
        
$$
\log(1+R_{n,t+1}) = \begin{cases} a_0^{n-1}-a_1^n + (e^{-0.5\delta}-1)(1-\rho)x_t^{exp} + (1-\rho)u_{t+1}, & t\text{ odd (E)}\\[4pt] a_1^{n-1}-a_0^n + (e^{0.5\delta}-1)(1-\rho)x_t^{exp} + (b_1^{n-1}e^\delta +1-\rho)u_{t+1}, & t\text{ even (L)} \end{cases}
$$

となる。

hhaf020

*   ここで  $u_{t+1}$  が\*\*予測不能成分（ショック）\*\*で、リターン変動の大部分を占める。
*   一方、 $x_t^{exp}$  に比例した項が**予測可能成分**であり、
    *    $e^{-0.5\delta}-1>0$ （E→L）
    *    $e^{0.5\delta}-1<0$ （L→E）  
        となるため、E/L をまたぐ1期リターンの自己相関は**符号が交互に変わる**。

この符号反転が、実証で観測される

*   newsy→repetitive（第1→第2月）の**正**の自己相関、
*   repetitive→newsy（第2→次の第1月）の**負**の自己相関

に対応します。つまり、

> 「投資家が earnings の decay パラメータを E/L で区別せずに平均化（圧縮）して extrapolate しているため、E期には overreaction、L期には underreaction が系統的に生じる」

という行動仮説を、明示的なキャッシュフロー・価格付けモデルとして定式化しているわけです。

* * *

4\. オンライン付録：correlation neglect・カレンダーラグ・グローバル・newsyness の検証
-----------------------------------------------------------

### 4.1 correlation neglect の補助的証拠

付録Aでは、**correlation neglect** による別種の予測パターンを検証しています。

ssrn-4316030

*   理論的な prediction：
    *   ある四半期の第1月と第2月の earnings は本質的に同じ四半期 earnings に基づくため高い相関を持つ。
    *   correlation neglect を持つ投資家は、この**高い相関を無視し、2本の signal を独立とみなして二重にカウント**する。
    *   その結果、第2月で過剰反応し、その過剰分が次の第1月で反転する。
*   これをリターンに翻訳すると
    1.  第1月リターンは第2月リターンを**正**に予測（継続）
    2.  第2月リターンは次四半期の第1月リターンを**負**に予測（反転）

付録では、具体的に

$$
mkt_t = \alpha + \beta_2 mkt_{t-2} + \beta_5 mkt_{t-5} + \beta_8 mkt_{t-8} + \beta_{11} mkt_{t-11} + \varepsilon_t,
$$

というような回帰を、被説明変数  $t$  を newsy 月（1,4,7,10月）に限定して推定し、  
第2月（四半期内で2か月前）リターンの係数  $\beta_2$  が大きく負（-0.275, t=-3.05）であることを示しています。

ssrn-4316030

同様の構造を industry excess returns に対しても確認し、correlation neglect が aggregate だけでなくクロスセクションにも現れていることを示します。

ssrn-4316030

一方で、付録は明示的に

*   correlation neglect は「第2月→次の第1月」の反転を説明するが、
*   RFS本論文で重要な「第1月→第2月・第3月・さらに先の月までの継続・反転パターン全体」は説明しない

と指摘し、**自分のメインストーリー（parameter compression）とは別のメカニズム**であることを強調しています。

### 4.2 カレンダー・ラグとAR(1) シミュレーション

付録Bでは、「たまたまカレンダー月ラグ（t-1〜t-12）ごとの自己相関構造が非均一だから、newsy/non-newsy の区別をしているように見えるのでは？」という懸念に応えています。

ssrn-4316030

*   12ラグの自己回帰を推定すると、係数はほぼフラットで、ラグと自己相関の間に明確な傾きはない（傾き ≈ -0.00062）。唯一、ラグ1の係数が約0.11で有意。
    ssrn-4316030
*   そこで、AR(1) プロセス（自己相関0.11）のシミュレーションを10,000回行い、そのデータに対してRFS本文の Table 3 と同じ回帰をかけると、  
    実際のデータでは interaction term が  $-0.232$  で有意なのに対し、シミュレーションでは  $-0.019$  程度で有意性もない。
    ssrn-4316030
    → 単純な AR(1) 構造やカレンダーラグの違いだけでは説明できないことを確認。

### 4.3 グローバル・クロスセクションと定量的「newsyness」

付録Cでは、Compustat Global を用いて各国×業種の excess returns を構築し、US と同様に

*   non-newsy 月では momentum が強い
*   newsy 月では reversal が強い

というパターンがグローバルにも成立することを示します。

付録Dでは、これまで binary だった “newsy / non-newsy” を、**半減期 HL を持つ指数重み**

$$
\text{unit\_newsy}(x) = 0.5^{x/HL}
$$

を用いて「報告ラグ x 日」に応じて連続的に測り、月ごとの newsyness を

*   四半期内で合計1になるよう正規化したうえで、
*   月次リターン回帰のダミー  $I_t^{nm}$  や過去4 new 月の和  $\sum_{j=1}^4 exret_{i,nm(t,j)}$  の代わりに使用する

という拡張を行っています。

結果として、

*   continuation 項の係数  $\beta_1$ 、reversal 項  $\beta_2$  のいずれも、binary 指標より統計的に強くなる（t値が大きくなる）。
*   Q1（特に1月）のように「実は newsyness がやや低い」ケースをうまく補正でき、パターンがより鮮明に現れる。

* * *

5\. Guo & Wachter (2025)「Correlation neglect in asset prices」のモデル
-----------------------------------------------------------------

この別稿では、correlation neglect を独立の行動仮説として扱い、極めてミニマルな 3 期間モデルで

*   **第1月 → 第2月の継続（E\[R₂R₁\] > 0）**
*   **第2月 → 第3月の反転（E\[R₃R₂\] < 0）**

を導出します。

### 5.1 経済の基本構造

1.  生産性状態
    *   経済は高・低の2状態。高状態なら市場価値  $=1$ 、低状態なら  $=0$ 。
    *   高状態の確率  $p$  は未知で、事前分布は Beta。投資家の事前期待は  $p^*$ 、事前サンプルサイズは  $\tau=1$  と固定。
        ssrn-5268329
2.  シグナル構造（3期間モデル）
    *   期間1（newsy 月）：シグナル  $\hat{s}_1 = s_1$ 、 $s_1 \sim \text{Bernoulli}(p)$ （例えば  $s_1=1$  は良い earnings）。
        ssrn-5268329
    *   期間2（repetitive 月）：シグナル  $\hat{s}_2$  は
        *   確率  $p_x$  で **繰り返し**（ $x=1$  のとき  $\hat{s}_2 = s_1$ ）
        *   確率  $1-p_x$  で **独立な新シグナル**（ $x=0$  のとき  $\hat{s}_2 = s_2$ ,  $s_2\sim Bernoulli(p)$ ）
    *   期間3（次の newsy 月）：新たな独立シグナル  $\hat{s}_3$  等を通じて true state が最終的に明らかになる、という構図。
3.  価格とリターン
    *   価格  $P_t$  は「経済が高状態である確率」の事後期待に比例すると仮定。
    *   1期リターン  $R_t = P_t - P_{t-1}$ （割引率は1に正規化）。
        ssrn-5268329

### 5.2 ベンチマーク：合理的投資家

*   投資家が  $x$  を観測し、「今見ているシグナルが繰り返しなのか（x=1）、独立なのか（x=0）」を知っているなら、
    *    $x=1$  のとき  $\hat{s}_2$  は新情報を含まず、 $P_2 = P_1$ 
    *    $x=0$  のとき  $\hat{s}_2$  は新情報だが、ベイズ更新の martingale 性質により  $E[P_2|s_1,x=0]=P_1$ 
*   したがって、
    $$
    E[R_2] = E[E[P_2 - P_1|s_1]] = 0, \quad E[R_2R_1] = 0,\quad E[R_3R_2]=0
    $$
    となり、継続も反転も生じないことが示されます。
    ssrn-5268329

### 5.3 correlation neglect 投資家

これに対し、correlation neglect を持つ投資家は

> 「シグナル間の相関を無視し、すべて独立なシグナルとして平均を取る」

ような updating を行うと仮定します。

簡単化された価格式の一例：

$$
P_1 = \frac{s_1 + p^* + 1}{3},\quad P_2 = \frac{\hat{s}_1 + \hat{s}_2 + p^* + 1}{5},
$$

など、観測シグナルと事前  $p^*$  を平均する線形規則で表されます（Beta–Binomial からの近似）。

このとき、

1.  **継続  $E[R_2R_1]>0$ **
    *    $x=1$  すなわちシグナルが繰り返されると、
        *   実際には新情報はないのに、投資家は「2つのシグナル」として数え、 $P_2$  を過大に動かす。
    *   形式的には、
        $$
        E[R_2 R_1] = E\left[ E[R_2 R_1 | s_1, x] \right] = E\left[ E[R_2 R_1 | s_1, x=1] \right]p_x \propto E\Big[\Big(3s_1 - p^* -1\Big)^2\Big]p_x > 0, \tag{5}
        $$
        となり、 $p_x>0$  の限り正になります。
        ssrn-5268329
2.  **反転  $E[R_3R_2]<0$ **
    *   期間3で真の状態がより精密に判明し、期間2の過剰反応が修正される。
    *   数式としては、
        *   期間2での誤った反応に対し、期間3での価格変化は平均的にその「取り消し」となることから、
        $$
        E[R_3 + R_2 | x=1,\hat{s}_1,\hat{s}_2] = 0
        $$
        が成り立ち、
        $$
        E[R_3 R_2] = -E[R_2^2]p_x < 0 \tag{6}
        $$
        となります。

ここから、

*   continuation（第1→第2月）と reversal（第2→第3月）の両方が  $p_x$ （繰り返し頻度）の関数として強くなる、というテスト可能な含意が出てきます。
*   実証では、earnings announcement の「繰り返し度合い」「類似度」「ネットワーク的結び付け」などを proxy に、  
    continuation/reversal の強さがこれら proxy に応じて変化することを示し、correlation neglect が実際に資産価格に効いていることを示しています。
    ssrn-5268329

* * *

6\. 3文献の関係：パラメータ圧縮 vs correlation neglect
-----------------------------------------

最後に、3つの文献の理論的関係をまとめます。

1.  **共通の実証パターン**
    *   どちらの枠組みも、決算サイクルに沿った「継続→反転」構造を説明する。
    *   ただし、RFS論文のパターンはよりリッチで、
        *   0E→0L の継続
        *   0L→1E の反転
        *   1E→1L の継続
        *   1L→2E の反転  
            ・・・といった**複数期にわたる交互の継続・反転**を含む。
2.  **メカニズムの違い**
    *   **パラメータ圧縮**
        *   投資家は、earnings の「将来への影響度」が E/L で step 状に変化することを十分区別せず、**単一の平均的な decay パラメータ**を用いる。
        *   結果として、E期への予想は過大（overextrapolation）、L期への予想は過小（underextrapolation）になり、  
            キャッシュフロー・ショックを通じて valuation とリターンの予測可能成分が交互に符号を変える。
        *   数理的には「状態変数の遷移行列のパラメータをグルーピングして平均化してしまう」ミス。
    *   **correlation neglect**
        *   投資家は、**シグナル同士の相関（特に繰り返しシグナル）を無視し、独立な情報として二重カウント**する。
        *   結果として、第2月で過剰反応し、第3月でそれが修正される。
        *   数理的には「シグナルの共分散構造を誤認し、独立と仮定したベイズ更新を行う」ミス。
3.  **RFS本文 vs オンライン付録 vs 別稿の役割分担**
    *   RFS本文：
        *   「earnings extrapolation + parameter compression」を主メカニズムとし、  
            newsy / non-newsy 構造に基づく広範な predictability と高い OOS  $R^2$  を説明。
    *   オンライン付録：
        *   「第2月→次の第1月」の反転に関して、correlation neglect も理論的に予測し得ることを示し、  
            実際にその予測がデータで確認できることを示す。
        *   しかし、correlation neglect は「第1月→第2・第3月の継続」など、本文で示されたすべてのパターンを説明しないことも明示。
    *   Guo & Wachter 別稿：
        *   correlation neglect を単独で取り出し、シンプルな3期モデルでその含意（E\[R₂R₁\]>0, E\[R₃R₂\]<0）を厳密に導出。
        *   aggregate、industry、survey expectations を通じて、「**高度にインセンティブを持つ投資家・アナリストでさえ correlation neglect を犯している**」ことを示す。
4.  **理論的・実務的含意**
    *   パラメータ圧縮と correlation neglect は、いずれも「有限の注意・計算能力を持つ投資家が、複雑な時系列・共分散構造を単純化して処理する」際に自然に生じるバイアス。
    *   RFS論文は、四半期 earnings サイクルに埋め込まれた「step 型の predictive structure」が十分に理解されていないことから生じる価格パターンを強調。
    *   別稿は、「繰り返しニュース」の誤解というより一般的なメカニズムを強調し、金融市場以外の文脈（政治、マクロ叙述など）で議論されてきた correlation neglect を、**aggregate 資産価格の月次レベルでも確認できる**ことを示す。

* * *

7\. まとめ
-------

*   3つのドキュメントは、決算サイクルという同じ舞台装置の上に
    *   「**パラメータ圧縮**による外挿の歪み」
    *   「**correlation neglect** による繰り返しニュースの二重カウント」  
        という2種類の行動メカニズムを載せ、それぞれが生み出す継続・反転パターンを数理モデル + 実証で示しています。
*   RFS論文のモデルは、log配当・状態変数・strip価格の指数線形構造を通じて、E/L期ごとに符号が反転する予測可能成分を導出し、同じメカニズムのもとで under-/overreaction を統合的に説明します。
*   別稿のモデルは、3期の Bernoulli シグナルと Beta 事前を用いたベイズ更新のずれとして correlation neglect を定式化し、E\[R₂R₁\]>0, E\[R₃R₂\]<0 を解析的に示します。

もし次のステップとして、

*   これら2つのメカニズムを**統合したモデル**を作りたい、
*   あるいはご自身のデータで「どちらのメカニズムがどの程度寄与しているか」を識別したい、

といった方向に進めるのであれば、そのための識別戦略や推定方針も整理できますので、そこにフォーカスした議論も続けて行えます。

## Response:
思考時間: 1m 28s

了解しました。ここでは、これまでやり取りしてきた戦略を整理する形で、

*   Method 1〜6 を「どの予測子を、どう推定し、どうポートフォリオに落とすか」
*   特に Method 6（nr + P4 の 2変数オンライン版 z\*\_t 戦略）

を数理的にまとめて解説します。以下は、Guo 系の論文で出てくる構造と、これまでご一緒に組んできた実装を対応づけた整理だと思ってください。

* * *

0\. 共通の前提と記法
------------

*   月次の市場超過リターン：
    $$
    r_t \equiv \text{MKT excess return at month }t
    $$
*   「newsy 月」（決算情報が集中的に出る月）を示すダミー：
    $$
    I_t^n = \begin{cases} 1 & t\text{ が newsy 月（1,4,7,10など）}\\ 0 & \text{それ以外} \end{cases}
    $$
*   Guo & Wachter 型の「news-based predictor」：  
    直近の newsy 月のリターン  $r_{nr(t)}$ 、あるいは過去4つの newsy 月のリターンをまとめた P4 など。

これらを使って、

1.  「リターンの予測」：
    $$
    \hat r_{t+1} = f_t(Z_t) 
    $$
2.  「ポジション（ウェイト）の決定」：
    $$
    w_{t} = g_t(\hat r_{t+1}, \hat\sigma_{t+1}) 
    $$

をどう設計するかが、各 Method の違いです。

* * *

1\. Method 1：単純な unconditional equity premium（ベンチマーク）
-----------------------------------------------------

### 1.1 数式

最もベーシックな比較対象として、

$$
\hat r_{t+1}^{(1)} = \bar r
$$
*    $\bar r$ ：全サンプル（もしくは直近 T 年）の平均市場超過リターン

という一定の期待リターンを仮定する方法です。

ポートフォリオウェイトは、ターゲットボラティリティ  $\sigma^\*$  を指定すると

$$
w_t^{(1)} = \frac{\bar r}{\hat\sigma_t^2} \sigma^\*
$$

のような Kelly 的ロジック（mean/variance 比例）でスケーリングすることが多いです。

### 1.2 解釈

*   予測子を一切使わないので「構造変化に鈍感」ですが、
*   タイミング誤差も生まれにくいベースライン。
*   実証的には「buy-and-hold + vol targeting」と同じような挙動になります。

* * *

2\. Method 2：Newsy / non-newsy を区別しない単一 AR(1) 予測
------------------------------------------------

### 2.1 数式

ここでは、最も単純に「直近の market return だけ」を使う AR(1) 型予測です。

$$
r_t = \alpha + \phi r_{t-1} + \varepsilon_t
$$
*   全サンプル（expanding）や rolling window で OLS により  $\hat\alpha, \hat\phi$  を求める。
*   予測は
    $$
    \hat r_{t+1}^{(2)} = \hat\alpha_t + \hat\phi_t r_t
    $$

### 2.2 解釈

*   Newsy / non-newsy の違いを無視し、「カレンダー月ラグ構造のみ」で predict する手法。
*   Guo 論文の付録Bでやっている AR(1) シミュレーションに近い世界観で、「こういう単純な AR(1) では決算サイクルのパターンは説明できない」という比較対象になっています。

* * *

3\. Method 3：Newsy / non-newsy の interaction 付き単一ラグ回帰（Guo eq.(2) 型）
-------------------------------------------------------------------

### 3.1 数式

ここから Guo の本論に近づきます。  
「直近の『情報のある月』（newsy / non-newsy）のリターン」を  $r_{nr(t)}$  とし、newsy 月ダミーとの interaction をとった回帰：

$$
r_t = \alpha + \beta_1 r_{nr(t)} + \beta_2 r_{nr(t)} I_t^n + \gamma I_t^n + \varepsilon_t \tag{M3}
$$
*    $I_t^n$ ：t が newsy 月かどうか
*    $\beta_1$ ：non-newsy 月での自己相関
*    $\beta_1+\beta_2$ ：newsy 月での自己相関

これを expanding OLS で推定していきます（Guo の baseline）。

### 3.2 予測とウェイト

予測は

$$
\hat r_{t+1}^{(3)} = \hat\alpha_t + \hat\beta_{1,t} r_{nr(t+1)} + \hat\beta_{2,t} r_{nr(t+1)} I_{t+1}^n + \hat\gamma_t I_{t+1}^n
$$

ボラターゲティングまで踏み込むなら、

$$
w_t^{(3)} = \frac{\hat r_{t+1}^{(3)}}{\hat\sigma_t^2} \sigma^\*
$$

のように「predictable Sharpe」に比例させます。

### 3.3 解釈

*   パラメータ圧縮の理論では、「本来は E/L で decay の仕方が違うのに、それを平均化して１本の  $\delta$  で近似してしまう」と説明していますが、
*   実証的には (M3) のような interaction 付き回帰が、その結果として生じる「E/L で符号が反転する自己相関構造」をキャッチしています。
*   Method 3 は、まさに Guo の equation (2) をそのまま予測に使うものと対応します。

* * *

4\. Method 4：P4 型 multi-lag predictor（Guo & Wachter の z\_t に近い）
---------------------------------------------------------------

### 4.1 P4 の定義

Guo & Wachter / オンライン付録で出てくる「過去4つの newsy 月」をまとめた予測子を、ここでは P4 と書きます：

*   四半期ごとに newsy 月を  $n_1, n_2, n_3, \dots$  と並べる。
*   時点 t の直近 4 newsy 月を  $(n_{k-3}, n_{k-2}, n_{k-1}, n_k)$  とすると、
    
$$
P4_t \equiv \sum_{j=0}^{3} \omega_j r_{n_{k-j}}
$$
*    $\omega_j$ ：単純平均  $\frac{1}{4}$  でもよいし、
*   Guo & Wachter の理論から導かれる係数（例えば「news の繰り返し度合い」に応じて重みを変える）を使うこともできます。

### 4.2 単一変数予測：z\_t

P4 がそのまま予測子になる：

$$
\hat r_{t+1}^{(4)} = \alpha_t + \beta_t P4_t
$$

もしくは、標準化して

$$
z_t = \frac{P4_t - \mu_t}{\sigma_t},\quad \hat r_{t+1}^{(4)} = \tilde\alpha_t + \tilde\beta_t z_t
$$

のような z-score ベースのシグナルとみなすものが Method 4 的な設計です。

### 4.3 解釈

*   Guo & Wachter の correlation neglect モデルでは、「同じ四半期 earnings に対する繰り返しニュース」がキーポイントになるので、P4 はその「累積ニュース量」を proxy にしたものと解釈できます。
*   z\_t は、P4 の水準を時変平均・分散から標準化したもので、「今が過去に比べてどれだけ極端な news 環境か」を測る指標です。

* * *

5\. Method 5：rolling OLS 版 z\*\_t（1変数 online 20年ウィンドウ）
------------------------------------------------------

ここから、ユーザーの実装と最も近い話になります。

### 5.1 z\*\_t の基本アイデア

z\*\_t は、

*   予測子として P4\_t（もしくは z\_t）を使い、
*   その「リターンに対する影響度」を rolling window で再推定し、
*   さらにその推定された係数を使って「normalized signal」に変換したもの

と整理できます。

具体的には、

1.  rolling window（例：直近20年 = 240ヶ月）で
    
$$
r_{t}^{(newsy)} = \alpha + \beta P4_{t-1} + \varepsilon_t
$$

を newsy 月だけ抜き出して OLS。  
2\.  $\hat\beta_t$  を用いて、信号を

$$
z_t^\* = \hat\beta_t P4_t
$$

のように「その時点のベスト線形予測子」に変換（必要なら平均・分散で標準化）。

### 5.2 Method 5 の特徴

*   **rolling OLS**：サンプルの最初からの expanding ではなく、「直近20年のみ」で推定するため、構造変化に敏感。
*   予測子は1変数（P4 や z\_t）なので、実装が比較的シンプルで、推定の分散も比較的抑えやすい。

### 5.3 経済的解釈

*   Guo の理論上の係数は固定ですが、実務的には「news の情報量・市場構造」は時期によって変化する可能性がある。
*   rolling OLS によって、  
    「P4\_t が newsy 月リターンをどの程度動かしてきたか」という係数  $\beta_t$  をオンラインで学習し、その都度 z\*\_t をアップデートしていくイメージです。

* * *

6\. Method 6：nr + P4 の 2変数オンライン版 z\*\_t ＋ ボラティリティターゲッティング
---------------------------------------------------------

ようやく本丸です。Method 6 は、上記 Method 5 を拡張して、

1.  「newsy 月かどうか」を明示的に組み込んだ 2変数回帰
2.  rolling 20年 window を「真の window」とせず、**RLS（recursive least squares）や忘却係数付きオンライン更新**で近似
3.  さらに出てきたシグナルをボラターゲティングでスケール

という構成になっていると整理できます。

### 6.1 2変数回帰の仕様

被説明変数を「newsy 月リターン」に絞るとします（Guo eq.(2) の newsy 部分に対応）。

*   説明変数ベクトル：
    
$$
X_t = \begin{pmatrix} P4_t\\ P4_t \cdot I_t^n \end{pmatrix} \in \mathbb{R}^2,
$$
*   係数ベクトル：
    
$$
\theta_t = \begin{pmatrix} \beta_{1,t}\\ \beta_{2,t} \end{pmatrix}
$$
*   モデル：
    
$$
r_t = \alpha_t + \beta_{1,t} P4_{t-1} + \beta_{2,t} P4_{t-1}I_t^n + \varepsilon_t \tag{M6-reg}
$$

ここで、

*    $\beta_{1,t}$ ：non-newsy 月での P4 の効果
*    $\beta_{1,t} + \beta_{2,t}$ ：newsy 月での P4 の効果

という構造になっており、Guo eq.(2) の  $\beta_1,\beta_2$  を rolling/online 推定していると解釈できます。

### 6.2 オンライン推定（RLS with forgetting）

rolling window を明示的に取り直す代わりに、**忘却係数  $\lambda \in (0,1)$ ** を使った RLS で  $\theta_t$  をアップデートします。

*   推定したいのは
    
$$
\min_{\theta_t} \sum_{s\le t} \lambda^{t-s} (r_s - \alpha_s - X_s^\top\theta_t)^2
$$

の解に相当する  $\theta_t$ 。

*   RLS の標準形：
    1.  prediction error
        $$
        e_t = r_t - \alpha_{t-1} - X_t^\top \theta_{t-1}
        $$
    2.  gain
        $$
        K_t = \frac{P_{t-1}X_t}{\lambda + X_t^\top P_{t-1}X_t}
        $$
    3.  係数更新
        $$
        \theta_t = \theta_{t-1} + K_t e_t
        $$
    4.  分散行列更新
        $$
        P_t = \lambda^{-1}\Big( P_{t-1} - K_t X_t^\top P_{t-1}\Big)
        $$
*    $\lambda$  を「20年 ≒ 240ヶ月の有効 window」に対応させるなら、例えば
    $$
    \lambda = \exp(-1/240)
    $$
    といった設定が自然です（半減期ベースで決めることもできます）。

これにより、 $\theta_t$  が「直近20年くらいの情報」を主に反映した推定値としてオンラインで更新されていきます。

### 6.3 z\*\_t（Method 6 版）の構成

Method 6 では、  
この時変係数  $\theta_t$  と予測対象月  $t+1$  の説明変数  $X_{t+1}$  を組み合わせて、

$$
\hat r_{t+1}^{(6)} = \hat\alpha_t + \hat\theta_t^\top X_{t+1}
$$
 
$$
z_{t+1}^{\*(6)} = \frac{\hat\theta_t^\top X_{t+1}}{\hat\sigma_t} \quad\text{（あるいは標準化した値）}
$$

のような形で normalized signal を定義します。

*    $X_{t+1}$  は、newsy 月かどうか  $I_{t+1}^n$  によって
    *   non-newsy →  $\hat\theta_t^\top X_{t+1} \approx \hat\beta_{1,t} P4_{t+1}$ 
    *   newsy →  $\hat\theta_t^\top X_{t+1} \approx (\hat\beta_{1,t} + \hat\beta_{2,t}) P4_{t+1}$ 

となるので、「同じ P4 でも、newsy / non-newsy で効き方が違う」ことを自動で反映します。

### 6.4 ボラティリティターゲッティング

ボラターゲティングまで含めた完全形は、例えば

1.  過去 Lヶ月の realized vol から  $\hat\sigma_t$  を推定  
    （例：EWMA や rolling 標準偏差）
2.  ターゲットボラ  $\sigma^\*$  を設定（例えば 10% 年率 → 月次に換算）
3.  Kelly 的な mean/variance ロジックで
    
$$
w_t^{(6)} = \kappa \frac{\hat r_{t+1}^{(6)}}{\hat\sigma_t^2} = \kappa \frac{\hat\theta_t^\top X_{t+1}}{\hat\sigma_t^2}
$$

などとする（ $\kappa$  はレバレッジ上限・リスク制約を反映した縮小係数）。

*   実務的には  $|w_t^{(6)}| \le w_{\max}$  のクリッピング、
*    $\hat r_{t+1}^{(6)}$  が小さい場合にノーポジに近づける dead-band を設定することも多いです。

### 6.5 Method 5 との違い

*   Method 5：
    *   1変数（P4 or z\_t）を rolling OLS で推定 → z\*\_t を構成
    *   「E/L の違い」は implicit（定数係数の中に吸収）
*   Method 6：
    *   2変数（P4, P4×I^n）を online（RLS）で推定
    *   「newsy / non-newsy の差」を明示的に学習し、 $\beta_{1,t}$  と  $\beta_{2,t}$  を別々に更新
    *   rolling window の明示的取り直しを避けて計算効率を上げつつ、忘却係数で有効 window を調整
    *   さらにボラターゲティングを標準装備

という点で、より「Guo の構造に忠実で、かつ構造変化に敏感な実装」と言えます。

* * *

7\. Method 1〜6 のまとめ（概念比較）
-------------------------

最後に、各 Method をざっくり並べると以下のイメージです。

*   **Method 1**：
    *   予測子：なし（定数）
    *   推定：全期間平均
    *   役割：完全なベンチマーク
*   **Method 2**：
    *   予測子：直近の r\_{t-1}（newsy / non-newsy 無視）
    *   推定：AR(1)（expanding / rolling）
    *   役割：カレンダー自己相関だけで決算サイクルが説明できるかの検証用
*   **Method 3**：
    *   予測子： $r_{nr(t)}$  + newsy ダミー × interaction
    *   推定：expanding OLS（Guo eq.(2)）
    *   役割：パラメータ圧縮から生じる E/L の自己相関構造を直接キャプチャ
*   **Method 4**：
    *   予測子：P4（過去4 newsy 月）から作る単一 z\_t
    *   推定：単変量回帰（expanding / rolling）
    *   役割：correlation neglect 型の「累積ニュース」指標としての位置づけ
*   **Method 5**：
    *   予測子：P4 or z\_t（1変数）
    *   推定：rolling（例：20年）OLS → z\*\_t
    *   役割：時変の予測力を rolling で追いかけ、構造変化に対応
*   **Method 6**：
    *   予測子： $X_t=(P4_t, P4_t I_t^n)$ （2変数）
    *   推定：忘却係数付き RLS（20年相当）
    *   シグナル： $\hat r_{t+1}^{(6)}=\hat\theta_t^\top X_{t+1}$ 、z\*\_t^{(6)}
    *   実装：ボラターゲティング込みでウェイト決定
    *   役割：Guo eq.(2) の構造（E/L の違い）を online で学習しつつ、相場環境の変化に適応する“本命”戦略

* * *

もしよろしければ次のステップとして、

*   各 Method の OOS R² や Sharpe、最大 DD を比較する分析コード
*   Method 6 の RLS 部だけを丁寧に数式→Python コードに落とした解説
*   newsy 月 / non-newsy 月・Newsy quartile（R/N/3）別のパフォーマンス分解

などもまとめてお出しできます。

## Response:
思考時間: 1m 35s

了解しました。ここでは、添付ドキュメントの記述だけに基づいて、Method 6 を数式レベルで整理して説明します。必要最小限の範囲で他の Method との位置付けも触れますが、全てドキュメント中に出てくる定義に限定します。

* * *

1\. 予測問題の枠組みとシグナルの定義
--------------------

論文のベースになっているのは、  
「**ニュース性のある月（newsy month）とそうでない月（non-newsy month）で、過去リターンの予測力が大きく異なる**」  
という時間系列のパターンです。月次の米国株式市場超過リターンを

*    $mkt_t$ ：月  $t$  の市場超過リターン（リスクフリー控除後）

とすると、代表的な回帰は

$$
mkt_t = \alpha + \beta \, mkt_{nr(t)} + \varepsilon_t,
$$

ここで  $nr(t)$  は「月  $t$  の直前の newsy 月」のインデックスです。実証結果では、

*   予測される月  $t$  が **newsy** か **non-newsy** かで  $\beta$  の符号が反転することが示されています。
    ssrn-5268329

この構造を踏まえて、**ニュース性に基づく単一の時系列シグナル**が定義されます。

### 1.1 OOS  $R^2$  用のシグナル  $x_t$ 

ワーキングペーパーでは、アウト・オブ・サンプルの予測力を評価する際のシグナルとして、次のような  $x_t$ （論文では predictor）が使われます：

ssrn-5268329

*    $\bar mkt_{t-1}$ ：月  $t-1$  までの市場リターンの「拡張窓平均（expanding window mean）」。
*    $mkt_{nr(t)}$ ：月  $t$  の直前の newsy 月のリターン。

このとき

$$
x_t = \begin{cases} mkt_{nr(t)} - \bar mkt_{t-1}, & t \text{ が non-newsy 月のとき} \\ -(mkt_{nr(t)} - \bar mkt_{t-1}), & t \text{ が newsy 月のとき} \\ 0, & \text{それ以外の場合} \end{cases}
$$

として、「**newsy 月では符号を反転させた、平均からの乖離**」が predictor になります。これに対して、拡張窓 OLS を逐次的に回すことで、様々な Method（1–3,5–7）の OOS 予測が構成されます。

* * *

2\. Method 1–3 と Method 5–7 の位置づけ
---------------------------------

### 2.1 Method 1–3（基本形）

ワーキングペーパーでは、各月  $t$  について、次のような**拡張窓 OLS 回帰**を行います：

ssrn-5268329

$$
mkt_t = \alpha_t + \beta_t x_{t-1} + \varepsilon_t.
$$

ここで  $\alpha_t, \beta_t$  は「月  $t$  時点で利用可能な過去データだけ」で推定した係数です（逐次更新される expanding-window 推定）。

そのうえで次のように予測  $\hat r_t$  を構成します：

ssrn-5268329

*   **Method 1**
    $$
    \hat r_t^{(1)} = \hat \alpha_t + \hat \beta_t x_{t-1}.
    $$
*   **Method 2**  
    定数項を推定値の代わりに、過去リターンの拡張窓平均  $\bar mkt_{t-1}$  に置き換える：
    $$
    \hat r_t^{(2)} = \bar mkt_{t-1} + \hat \beta_t x_{t-1}.
    $$
*   **Method 3**  
    定数項を、Campbell & Thompson (2008) に倣い、配当利回り・E/P・B/M から抽出した「平均」指標（ドキュメントでは “an average extracted from dividend/price, earnings/price, and book-to-market”）で置き換える：
    $$
    \hat r_t^{(3)} = c^{CT}_t + \hat \beta_t x_{t-1},
    $$
    ここで  $c^{CT}_t$  はこれら 3 つのバリュエーション指標から構築された水準です。
    ssrn-5268329

これらに対し、OOS  $R^2$  は

$$
R^2_{\text{OOS}} = 1 - \frac{\sum_{t=1}^n (mkt_t - \hat r_t)^2}{\sum_{t=1}^n (mkt_t - \bar mkt_t)^2}
$$

として計算され、Method 1–3 は 4% 台という「従来の文献に比べて桁違いに大きい」  $R^2$  を達成することが示されています。

ssrn-5268329

### 2.2 Method 5–7（係数推定の仕方の違い）

最終版論文では、Appendix において次のように述べられています：

> “Methods 5–7 are methods 2–4 with the coefficients estimated on the combined sample of newsy and non-newsy months.”
> 
> hhaf020

つまり、

*   **Method 2–4**：元々は「newsy 月」と「non-newsy 月」を分けて推定していたバージョン。
*   **Method 5–7**：それと同じ定数構造（Method 2–4 それぞれ）を用いつつ、  
    係数推定は **newsy／non-newsy を統合した単一のサンプルで行う**バージョン。

このうち、\*\*Method 6 は「Method 3 の構造 + combined sample 推定」**と読み取ることができますが、Method 6 についてはさらに A.3 節で**トレーディング戦略に対応した「より具体的な実装形」\*\*が詳しく書かれています。以下では、この A.3 節の記述を中心に Method 6 を整理します。

* * *

3\. Method 6 の具体的な構成
--------------------

### 3.1 データ変換：4つの newsy 月リターンからのシグナル

Appendix A.3「Time-Series Strategy」では、まず**過去 4 回の newsy 月のリターンを集約したシグナル**が定義されます：

hhaf020

1.  各月末  $t-1$  時点で、
    *   直近 4 回の newsy 月（1,4,7,10 月）の「**トータルリターン**」を合計した値を計算する。
2.  そのトータルリターンの「拡張窓平均」（サンプル開始から  $t-1$  までの平均）を計算する。
    hhaf020
3.  トータルリターンからその平均を引き、さらに
    *   **予測対象の月  $t$  が newsy 月であれば符号を反転させる**ことで、demeaned signal  $x_{t-1}$  を得る。
        hhaf020

直観的には、

*   「直近 4 回分の『決算シーズン』リターンが、歴史的な平均と比べてどれだけ高い／低いか」
*   そして「その情報は、次の月が newsy か non-newsy かによって期待リターンの符号が反転する」

という構造を、**1 本のスカラーシグナル  $x_{t-1}$ ** に圧縮している、という理解になります。

### 3.2 制約付き時系列回帰（Method 6 の心臓部）

次に、このシグナルを用いて以下のような**制約付き時系列回帰**を行います：

hhaf020

$$
mkt_t = \beta \, x_{t-1} + 1 \cdot \bar mkt_{t-1} + \varepsilon_t,
$$
*    $mkt_t$ ：月  $t$  の市場超過リターン
*    $x_{t-1}$ ：上述の demeaned signal
*    $\bar mkt_{t-1}$ ：月  $t-1$  までの市場リターンの拡張窓平均
*   係数  $\bar mkt_{t-1}$  の前の係数は **1 に固定される**（制約付き回帰）

論文はこれを

> “The coefficient before mktt−1 is constrained to be 1. Denote the estimated coefficient β as c\_t.”
> 
> hhaf020

と記述しています（ここで mktt−1 と表記されていますが、実質的には拡張窓平均と同じ役割を果たす水準項と解釈できます）。

この制約付き回帰は、 algebra 的には

$$
mkt_t - \bar mkt_{t-1} = \beta \, x_{t-1} + \varepsilon_t
$$

という 1 変量回帰と同値です。つまり、

*   左辺：**「その月のリターン − 歴史的平均」**
*   右辺：シグナル  $x_{t-1}$ 

として、**平均からの超過部分を  $x_{t-1}$  だけで説明する構造**になっています。

この回帰を拡張窓で逐次的に推定し、月  $t$  時点までのデータのみで推定した  $\hat \beta_t$  を

$$
c_t := \hat\beta_t
$$

と定義します。

hhaf020

### 3.3 予測式：Method 6 の期待リターン

この制約付き回帰から、月  $t$  の終わりに「翌月  $t+1$  の予想リターン」を構成すると、

$$
\hat r_{t+1|t}^{(6)} = c_t \, x_t + \bar mkt_t,
$$

となる、と論文は明示しています：

hhaf020

> “The forecasted market return at the end of month t for month t+1 is then  $c_t x_t + \bar mkt_t$ . This is the forecast from method 6 of Table 4.”

ここで重要なのは、予測値が

*   **長期平均リターン**  $\bar mkt_t$ 
*   **ニュース性シグナルから得られる「上振れ／下振れ」部分**  $c_t x_t$ 

に分解されている点です。

*    $c_t x_t > 0$  のとき：  
    過去の newsy 月リターンが「平均より高く」、かつ「次の月が non-newsy」であるといった状況に対応し、平均より高い期待リターンとなる。
*    $c_t x_t < 0$  のとき：  
    過去の newsy 月リターンが高く、次の月が newsy である、などの状況に対応し、平均より低い期待リターンになる。

このように、**newsy / non-newsy の非対称な自己相関構造**を、1 本のシグナル  $x_t$  と係数  $c_t$  を通じて期待リターンにマッピングしているのが Method 6 のコアです。

* * *

4\. Method 6 とトレーディング戦略（ボラティリティ・ターゲティング）
----------------------------------------

Method 6 は単に期待リターンを予測するだけでなく、そのまま**リアルタイムで実装可能なマーケット・タイミング戦略**に落とし込まれています。

### 4.1 ポジション・サイズ： $w_t = c_t x_t$ 

論文は、Method 6 の予測式を用いて次のようなポートフォリオのウェイトを構成します：

hhaf020

> “The portfolio weight in my strategy is  $c_t x_t$ , which roughly has a mean of zero over time.”

つまり、

*   月  $t$  の前月末（すなわち取引前の情報）で、  
    市場に対するウェイトを
    $$
    w_t = c_t x_t
    $$
    と設定する。
*    $x_t$  が正ならロング、負ならショート、ゼロなら中立に近いポジション。

この  $w_t$  はシグナルの対称性から時間平均でほぼ 0 になりやすく、**純粋なロング／ショートのビューを表す成分**になっていると解釈できます。

### 4.2 ボラティリティ・スケーリング

さらにこのポートフォリオは、一定のボラティリティになるようスケーリングされます：

hhaf020

> “Finally, the portfolio is scaled by a constant so that it has the same volatility as the aggregate market, which is 5.34% per month.”

つまり、ある定数  $k$  を選んで

$$
\tilde w_t = k \, c_t x_t
$$

とし、結果として得られる戦略リターン

$$
R^{\text{TS}}_t = \tilde w_{t-1} \cdot mkt_t
$$

の標準偏差が、サンプル上で市場ポートフォリオの月次ボラティリティ（約 5.34%）と一致するように  $k$  を選びます。これにより、

*   Method 6 ベースの戦略と
*   パッシブな市場ポートフォリオ

の Sharpe 比や平均リターンを**同一ボラ水準で比較可能**にしています。

Appendix では、こうして構成された Time-Series Portfolio が、

*   年率約 10% に相当する月次平均 0.8% 強のリターン
*   市場と同程度の Sharpe 比

を持つことなどが示されており、Method 6 に基づくシグナルが実際のトレーディング戦略としても十分に強力であることが強調されています。

hhaf020

* * *

5\. Method 6 の経済的・数理的含意（ドキュメント内の議論に限定）
--------------------------------------

### 5.1 期待リターンの高頻度変動とリスクベース・モデルへのチャレンジ

Method 6 を用いて構築した OOS 期待リターン系列（図 2 の青線）は、以下の特徴を持ちます：

hhaf020

*   月次オートコリレーションは約 −0.20 と負。
*   期待リターンが **T-bill レートを下回る月が 3 ヶ月に 1 回、期待リターン自体が負になるのが 5 ヶ月に 1 回**程度の頻度で出現。

これは

$$
\hat r_{t+1|t}^{(6)} = \bar mkt_t + c_t x_t
$$

の  $c_t x_t$  成分が、newsy / non-newsy の切り替わりと過去ニュース強度によって、かなり高頻度に符号を変えていることを反映しています。

著者は、こうしたパターンを理由に、標準的なリスクベース・モデル（サープラス消費比モデルなど）が、この種の「高頻度の期待リターン変動」かつ「株の方が T-bill よりしばしば安全になる」状況を説明するのは難しい、と指摘しています。

hhaf020

### 5.2 Method 6 の数理構造のポイント

Method 6 の数理的なポイントをまとめると：

1.  **線形予測構造**
    $$
    E[mkt_{t+1} \mid \mathcal F_t] \approx \bar mkt_t + c_t x_t
    $$
    という、長期平均 + シグナル×係数の線形モデル。
2.  **係数の時間変動性**（拡張窓 OLS による逐次推定）
    *    $c_t$  は、時点  $t$  までのデータのみから推定されるため、  
        論文の用語では「look-ahead bias を除いた out-of-sample 予測」になっている。
3.  **シグナルの符号反転ロジック**
    *   newy / non-newsy に応じて  $x_t$  の符号を反転させることで、  
        1 本の線形モデルでも「newsy ではリバーサル」「non-newsy ではモメンタム」という二面性を表現できる。
4.  **制約付き回帰により定数項を平均に固定**
    *    $\bar mkt_t$  に係数 1 を与え、定数項を明示的なパラメータとして推定しないことにより、  
        予測の「水準部分」を長期平均に委ね、  
         $c_t x_t$  を純粋な「超過分」として解釈しやすくしている。
        hhaf020

* * *

まとめ
---

ドキュメントに基づく限り、**Method 6**は以下のように整理できます。

*   newsy / non-newsy 構造から導かれるシグナル  $x_t$  を用いて、
*   「平均リターンからの乖離」を説明する制約付き線形モデル
    $$
    mkt_t - \bar mkt_{t-1} = c_t x_{t-1} + \varepsilon_t
    $$
    を拡張窓 OLS で逐次推定し、
*   期待リターンを
    $$
    \hat r_{t+1|t}^{(6)} = \bar mkt_t + c_t x_t
    $$
    として構成し、
*   その超過部分  $c_t x_t$  をそのまま市場ウェイトとする時系列戦略（ボラティリティを市場と同程度にスケーリング）に接続している。

これにより、**高い OOS  $R^2$  と実務的に意味のある Sharpe 比を同時に実現する予測・トレーディング・フレームワーク**として Method 6 が位置付けられています。

もし次のステップとして、

*   20 年ローリング窓版（オンライン 20Y）との理論的な違い、
*   2 変数拡張（例： $x_t$  + P4）の Method 6 版、
*   ボラティリティ・ターゲティングの数式仕様（目標ボラを任意に変えた場合）

などを、論文の枠組みからどこまで「自然に一般化できるか」を整理したい場合は、その点だけ切り出して続けて掘り下げましょう。

## Response:
以下、Method 6 の内容（「直近4回の決算シーズンリターン」「newsy / non-newsy で符号反転」「平均からの乖離 × 制約付き回帰」「ボラティリティ・ターゲティング」）に沿って、名称候補をいくつか出します。和名＋英語名セットで書いておきます。

* * *

### 1\. 決算サイクルの“非対称モメンタム”を強調する名前

1.  **「決算サイクル非対称モメンタム戦略」  
    Asymmetric Earnings-Cycle Momentum (AECM)**
    *   決算ニュースに対する continuation / reversal の非対称性を前面に出した名前。
    *   学術的な説明にもそのまま使いやすいです。
2.  **「Newsy–Non-Newsy 切替モメンタム戦略」  
    Newsy–Non-Newsy Switch Momentum (NNSM)**
    *   シグナルの符号が「newsy / non-newsy」でスイッチすることをそのまま表現。
    *   コード名としても短くて扱いやすいと思います。

* * *

### 2\. “4つの決算シーズン”シグナル（P4 / z\*\_t）を強調する名前

3.  **「四半期ニュース累積シグナル戦略」  
    Quarterly News-Stack Strategy (QNSS)**
    *   “直近4回の newsy 月リターンを積み上げる”という構造をそのまま表現。
    *   「ニュースをスタックしてタイミングを取る」イメージ。
4.  **「P4 決算ニュースタイミング戦略」  
    P4 Earnings-News Timing Strategy (P4-ENTS)**
    *   論文・コード上の P4 という記号をそのまま名称に反映。
    *   ご自身のコードベースとの対応も明快になります。

* * *

### 3\. 「平均からの乖離×制約付き回帰」を強調する名前

5.  **「平均乖離決算シグナル戦略」  
    Mean-Shift Earnings Signal Strategy (MSESS)**
    *    $\bar mkt_t + c_t x_t$  という “長期平均＋乖離成分” の構造を強調。
    *   「期待リターンの平均からのシフトを決算情報で測る」戦略という意味づけです。
6.  **「決算ベース期待リターンシフト戦略」  
    Earnings-Based Expected-Return Shift (EBERS)**
    *   期待リターンそのものを“shift”させる、というイメージを前面に。
    *   プレゼンテーションで「この戦略は expected return shift を明示的に推定する」と説明しやすいです。

* * *

### 4\. 「パラメータ圧縮・誤った外挿」を意識した名前

7.  **「外挿ミス補正決算サイクル戦略」  
    Extrapolation-Error Corrected Earnings-Cycle Strategy (EECS)**
    *   Guo のメインストーリー（earnings extrapolation の誤り）を“補正”するタイミング戦略という解釈。
    *   「市場の外挿ミスに乗る」ニュアンスを名前に込めています。
8.  **「圧縮パラメータ反転モメンタム」  
    Compressed-Parameter Reversal–Momentum Strategy (CPRM)**
    *   パラメータ圧縮（parameter compression）から生じる「newsy で reversal / non-newsy で momentum」の組み合わせを直接表現。
    *   理論セクションとのリンクを強くしたい場合に向きます。

* * *

### 5\. 実務・コードで使いやすい短いラベル

9.  **「E-Cycle TS 戦略」  
    Earnings-Cycle TS Strategy (E-Cycle TS)**
    *   Time-Series (TS) で決算サイクルを取る、という意味のシンプルなラベル。
    *   論文中の “Time-Series Strategy based on Method 6” とも整合的です。
10.  **「z\*\_E 戦略」  
    z\*\_E Strategy (z-star Earnings Strategy)**
    *   z\*\_t を「earnings-based z-star」と解釈して、そのままラベルにしてしまう案。
    *   研究ノートやコード上で “run\_zstar\_E\_strategy(method=6)” のように書けて扱いやすいです。

* * *

### おすすめの絞り込み案

*   学術的な論文タイトル・スライドに載せるなら：  
    → **Asymmetric Earnings-Cycle Momentum (決算サイクル非対称モメンタム戦略)**
*   コードや内部メモで使う“短い識別子”としては：  
    → **Newsy–Non-Newsy Switch Momentum (NNSM)**  
    → もしくは **Earnings-Cycle TS Strategy (E-Cycle TS)**

もし、

*   「correlation neglect との対比も名称に入れたい」
*   「将来 cross-section 版も作る前提で、time-series と cross-sectional を並べられる命名体系にしたい」  
    といった要望があれば、その前提でペアになる名前セット（TS 用／CS 用）も作ります。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)