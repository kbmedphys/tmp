# 残差モメンタムの誤解

**User:** Kentaro Baba (kencharoffx@gmail.com)  
**Created:** 4/6/2026 21:37:00  
**Updated:** 4/6/2026 21:38:51  
**Exported:** 4/6/2026 23:05:04  
**Link:** [https://chatgpt.com/c/69d3a8db-0300-83a5-b7b9-844c9c0f3a7b](https://chatgpt.com/c/69d3a8db-0300-83a5-b7b9-844c9c0f3a7b)  

## Response:
2026/4/6 21:36:58

要点を押さえて整理します。まず論文の主張・問題設定・提案手法・実務含意を拾って、その後に数式 intuition まで噛み砕いて説明します。

> 思考時間: 33s

はい。この論文 **“What Does Residual Momentum Tell Us About Firm-Specific Momentum?”** は、かなり重要な整理をしています。結論から言うと、

**「残差モメンタムが儲かる ＝ 個別銘柄固有のモメンタムが強い」ではない**  
というのが中心主張です。著者は、従来の residual momentum は

1.  真の firm-specific momentum
2.  見落とした factor momentum
3.  betting-against-beta（BAB）的なベータ賭け  
    を混ぜてしまっている、と論じています。
    WhatDoesResidualMomentumTellUsA…

以下、順に整理します。  
参照論文:

WhatDoesResidualMomentumTellUsA…

1\. この論文の問題意識
-------------

従来のモメンタム研究では、株式の過去リターンではなく、CAPM や Fama-French モデルで説明したあとの**残差**で銘柄を並べてモメンタム戦略を作ると、普通の total return momentum より高い alpha が出ることがあるため、

*   「モメンタムの源泉は共通因子ではなく、企業固有成分にあるのではないか」

と解釈されがちでした。  
しかし著者は、その解釈はそのままでは正しくない、と言います。理由は、**残差でソートした瞬間に、実は beta に逆張りするポジションまで一緒に入ってしまう**からです。特に security factor line が十分に急でない世界では、高 beta 資産が低 alpha、低 beta 資産が高 alpha になり、残差ソートがそのまま BAB 戦略を含んでしまいます。

WhatDoesResidualMomentumTellUsA…

2\. 論文の核心
---------

論文の核心は、

**Residual momentum の alpha は、真の firm-specific momentum の純粋な測度ではない**

という点です。  
著者は、残差モメンタムの利益は次の3つの混合物だと整理します。

*   firm-specific momentum
*   omitted factor momentum
*   betting-against-beta 効果

つまり、残差戦略が儲かっていても、それは「個別銘柄固有の持続性」だけで説明してはいけない、ということです。

3\. なぜ残差モメンタムは誤解を生むのか
---------------------

論文は、残差モメンタムに次の“おかしな性質”があることを示します。

### (a) 因子を多く取り除くほど、むしろその因子群との共変動が強くなる

直感的には、因子をたくさん除去した残差ほど“純粋に idiosyncratic”になりそうです。  
ところが実証では逆で、**より多くの因子を取り除いて作った residual momentum のほうが、回帰で高い  $R^2$  を持ち、因子との関係も強くなる**。著者はこれを、「因子を消しているようで、実際にはその beta に対する賭けを強めているから」と説明します。

WhatDoesResidualMomentumTellUsA…

### (b) 平均リターンは下がるのに alpha は上がる

これも直感に反します。真に firm-specific な戦略なら、因子 loading は小さくなり、alpha と平均リターンの乖離も不自然にはならないはずです。  
しかし residual momentum では、**平均リターンは低下する一方で回帰 alpha は上昇する**。これは beta 賭けが回帰 alpha を押し上げている兆候だ、と著者は述べます。

WhatDoesResidualMomentumTellUsA…

4\. 著者の理論的分解
------------

論文では、観測された residual momentum を

*   真の firm-specific momentum
*   ベータに対する賭け（BAB補正項）

に分解できることを示します。  
要するに、残差ソート戦略は「本来取りたい企業固有モメンタム」だけではなく、**低 beta を買い、高 beta を売る構造**を必然的に持ちうる、ということです。結果として、因子回帰した alpha は上方に歪みます。

WhatDoesResidualMomentumTellUsA…

さらにモデルが不完全で、真の因子の一部を落としている場合には、そこに**omitted factor momentum**も混入します。したがって、残差モメンタムの収益はより一層「何の源泉か分からない混合物」になります。

WhatDoesResidualMomentumTellUsA…

5\. 論文の提案: beta-neutral residual momentum（iRMOM）
------------------------------------------------

この問題を解くために、著者は **iRMOM** を提案します。  
これは、通常の residual momentum（RMOM）から **beta bets / long-run intercept bets** を取り除いた戦略です。論文の4段階手順は概ね次です。

1.  直近期間の時系列回帰で各銘柄の residual を推定
2.  より長い窓で各銘柄の long-run intercept を推定
3.  residual を long-run intercept でクロスセクション回帰し、その残差を取る
4.  その“beta-neutralized residual”でモメンタムポートフォリオを組む

こうして、beta 賭けをなるべく除去した residual momentum を作ります。

WhatDoesResidualMomentumTellUsA…

6\. 実証結果で何が分かったか
----------------

著者は、firm-specific momentum が本当にあるなら次の3つが観察されるはずだとします。

1.  **iRMOM のほうが RMOM より平均分散効率が高いこと**
2.  **iRMOM 同士の地域間相関が RMOM より低いこと**
3.  **iRMOM が factor momentum とあまり共変動しないこと**
    WhatDoesResidualMomentumTellUsA…

実際に論文はその3つを確認しています。

*   米国では FF ベースの標準 RMOM の Sharpe が **0.59**
*   対応する beta-neutral 版 iRMOM の Sharpe が **1.23**

と大きく改善します。

WhatDoesResidualMomentumTellUsA…

また、地域間相関も

*   RMOM 平均相関: **0.40**
*   iRMOM 平均相関: **0.24**

に低下し、factor momentum との相関も

*   RMOM: **0.36**
*   iRMOM: **0.19**

へ低下します。  
これは、iRMOM のほうがより「systematic ではなく firm-specific」に近いことを示唆します。

WhatDoesResidualMomentumTellUsA…

さらに、beta bets を取り除くと、iRMOM は factor momentum への loading が小さくなりつつ、なお有意な intercept を持つため、**単なる factor momentum では説明しきれない**と結論づけています。

WhatDoesResidualMomentumTellUsA…

7\. 一番重要な含意
-----------

この論文の実務・研究上の重要点はかなり明確です。

### 従来の residual momentum をそのまま「個別銘柄固有のモメンタム」と読んではいけない

これはこの論文の最大のメッセージです。  
残差ソート戦略の alpha が高いからといって、すぐに

*   「企業固有情報の遅延反映がある」
*   「idiosyncratic underreaction が主因だ」  
    と解釈するのは危険です。

### それでも firm-specific momentum 自体は存在する

著者は逆に、きちんと beta 賭けを除いたあとでも強いモメンタムが残ることを示しており、**firm-specific momentum は実在する**と主張しています。

### ただし、その強さは時期によって変わる

要約部分では、**firm-specific momentum は 2002 年までは強かったが、その後はほぼ裁定され尽くした**とも述べています。

WhatDoesResidualMomentumTellUsA…

8\. クオンツ実務の観点での読み方
------------------

あなたの文脈でかなり大事なのは次です。

*   残差モメンタムをシグナルに使うなら、**alpha の源泉分解**が必要
*   FF5 で残差化しただけでは不十分
*   beta-neutralization をしない residual momentum は、実際には
    *   BAB
    *   omitted factor momentum
    *   firm-specific momentum  
        の混合ポートフォリオになっている可能性が高い

したがって、戦略研究としては

1.  raw momentum
2.  RMOM
3.  iRMOM
4.  factor momentum
5.  BAB

を並べて、相関・回帰・シャープ・クラッシュ特性を比較するのが自然です。これは論文の発想と整合的です。

9\. ひとことでまとめると
--------------

この論文は、

**「Residual momentum は firm-specific momentum の証拠ではあるかもしれないが、そのままでは証拠として不純すぎる。beta と omitted factors を除去したうえで見直すべきだ」**

という論文です。  
そして、著者の答えは

**「除去した後でもなお強い成分が残るので、firm-specific momentum は本当にある。ただし従来の residual momentum 解釈は雑すぎた」**

です。

必要なら次に、  
**(1) 数式ベースでこの論文を丁寧に解説する**  
または  
**(2) あなたの戦略研究向けに、RMOM / iRMOM / FMOM / BAB の実装手順へ落とし込む**  
形で続けます。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)