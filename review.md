# 輪読レビュー: Dimension reduction in quantum sampling of stochastic processes

## 0. このレビューの位置づけ
- 本レビューは `docs/sources/Dimension reduction in quantum sampling of stochastic processes.pdf` の内容を、輪読会向けに日本語で再整理したもの。
- 事実の根拠は論文本文の `Results`, `Discussion`, `Methods A-F` と式番号 `(1) - (39)`。
- 本文中では、できるだけ **事実（論文記載）** と **解釈（理解しやすくする補足）** を分けて書く。

## 1. 論文情報
- タイトル: *Dimension reduction in quantum sampling of stochastic processes*
- 著者: Chengran Yang, Marta Florido-Llinas, Mile Gu, Thomas J. Elliott
- 誌名: *npj Quantum Information*
- DOI: [10.1038/s41534-025-00978-2](https://doi.org/10.1038/s41534-025-00978-2)
- 掲載情報: 2025年, Volume 11, Article 34
- 受付/採択: 2024-05-05 受付, 2025-02-06 採択（論文末尾記載）

## 2. まず全体像（短く）
### 事実（論文記載）
- 論文の目的は、確率過程の量子サンプリングで必要なメモリ次元を、少しの歪みを許して圧縮すること。
- 提案法は MPS（行列積状態）切り詰めを土台にした **lossy quantum dimension reduction**。
- Markov的な過程と、強い非Markov過程の両方で低歪み圧縮を示す。
- 圧縮後の量子モデルは、同じメモリ次元の古典モデルより歪みが小さい例を示す。

### 解釈（輪読会向け）
- 「情報量はそこまで多くないのに、実装上のメモリ箱だけ大きい」状況を狙い撃ちしている。
- その箱（次元）を小さくしても、出力統計があまり壊れないなら実用上有利。

## 3. イントロ整理: 何が課題で、なぜ重要か
### 事実（論文記載）
- 複雑な確率過程の解析は、時間とともに軌道数が指数的に増えやすい。
- Monte Carlo は有力だが、時間相関を保持するメモリが大きくなる欠点がある。
- 量子情報処理では q-sample（全軌道の重ね合わせ状態）を準備でき、解析・サンプリングの高速化可能性がある。
- ただし q-sample 構成にも「過去未来相関を運ぶメモリ」が必要で、これがボトルネックになる。

### 解釈（輪読会向け）
- 論文は「量子が速いか」より一段手前で、**そもそも量子状態を作るためのメモリ負担をどう減らすか** を扱う。
- ここが軽くなると、将来の量子デバイス上で実行可能な範囲が広がる。

## 4. 前提知識（初学者向け）
### 4.1 確率過程・因果状態
- 確率過程: 時刻ごとの出力列が確率分布で決まる対象。
- 未来予測に同じ情報を持つ過去同士をまとめた状態が causal state（因果状態）。
- 古典最小モデル（epsilon-machine）は、この因果状態を使って最小メモリで正確再現する。

### 4.2 q-sample
- 長さ `L` の出力列 `x_{0:L}` を確率振幅 `sqrt(P(x_{0:L}))` で重ね合わせた量子状態。
- 1本ずつサンプルする代わりに、全軌道情報を1つの量子状態に載せるイメージ。

### 4.3 MPS / iMPS
- MPS: 1次元量子状態をサイトごとのテンソル積で圧縮表現する方法。
- iMPS: 無限長・平行移動不変の MPS。
- 本論文は「q-sample を iMPS と見なして切り詰める」点が核。

### 4.4 メモリ次元と情報コスト
- メモリ次元コスト:
  \[
  D_q := \log_2 d
  \]
  `d` はメモリHilbert空間次元。
- 情報コスト:
  \[
  C_q := S(\rho), \quad \rho := \sum_j P(j)\,|\sigma_j\rangle\langle\sigma_j|
  \]
- 論文の重要観察は、しばしば `C_q << D_q` となること（Results, Framework and tools）。

## 5. 数理コア（式の再掲と解説）

## 5.1 q-sample生成の基本式
### 式(1): 量子更新ユニタリ
\[
U|\sigma_j\rangle|0\rangle
= \sum_x \sqrt{P(x|j)}\,e^{i\phi_{xj}}\,|x\rangle|\sigma_{\lambda(x,j)}\rangle
\tag{1}
\]
- 式の意味: 現在メモリ状態 `|sigma_j>` と空ancilla `|0>` から、次出力 `x` と次メモリ状態を同時生成。
- 変数の意味: `P(x|j)` は条件付き出力確率、`lambda(x,j)` は遷移先ラベル、`phi_{xj}` は位相自由度。
- 直感: 古典HMMの「出力＋状態遷移」を量子チャネル化した式。

### 式(2): Lステップ q-sample
\[
|P(X_{0:L}|j)\rangle
:= \sum_{x_{0:L}} \sqrt{P(x_{0:L}|j)}\,|x_{0:L}\rangle
\tag{2}
\]
- 式の意味: 長さ `L` の列全体を重ね合わせた状態。
- 直感: 1本ずつのサンプルではなく、全列をまとめて保持する。

### 式(3): q-sampleのMPSサイト行列
\[
A^x_{kj}=\sqrt{P(x|j)}\,\delta_{\lambda(x,j),k}
\tag{3}
\]
- 式の意味: q-sampleを iMPS に落とす具体式。
- 直感: `delta` が「遷移規則」を、`sqrt(P)` が「振幅」を担う。

## 5.2 歪み指標: QFDR
### 式(4): Quantum Fidelity Divergence Rate
\[
R_F\big(|P\rangle,|P'\rangle\big)
:= -\lim_{L\to\infty}\frac{1}{2L}\log_2 F\big(|P_L\rangle,|P'_L\rangle\big)
\tag{4}
\]
- 式の意味: 無限鎖で fidelity がどの速度で落ちるかを 1ステップ当たりで測る。
- 変数の意味: `F` は状態忠実度、`|P_L>` は長さ `L` 部分 q-sample。
- 直感: 値が小さいほど「1ステップごとの劣化が遅い」。

## 5.3 切り詰め誤差の理論保証
### 式(5): Theorem 1 の主要境界
\[
R_F\big(|P\rangle,|\tilde P\rangle\big)
\le
\frac{\epsilon_{\tilde d}}{2(1-L\epsilon_{\tilde d})\ln 2}
+ O\!\left(\frac{1}{L}\right),
\quad
\epsilon_{\tilde d}:=\sum_{k=\tilde d+1}^{d}\lambda_k
\tag{5}
\]
- 式の意味: 捨てたSchmidt係数和 `epsilon_tilde{d}` が小さければ QFDR も小さい。
- 直感: 「小さい成分を捨てる」操作の歪みが線形オーダーで制御できる。

### 式(6): Theorem 2（`epsilon_tilde{d}` と情報量の関係）
\[
\epsilon_{\tilde d}
\le
\frac{H(\lambda)}{\frac{\tilde d-2}{d-\tilde d}\log_2(d-\tilde d)+\log_2(\tilde d)}
\tag{6}
\]
- 式の意味: 捨てるSchmidt和に、エントロピー `H(lambda)` と切り詰め次元 `tilde d` で上界が付く。
- 直感: 情報量 `H(lambda)` が小さい系では、次元削減しても捨て損が大きくなりにくい。

### 式(7): Corollary 1
\[
\epsilon_{\tilde d}
\le
\frac{C_q}{\tilde D_q},
\quad
\tilde D_q:=\log_2(\tilde d)
\tag{7}
\]
- 式の意味: `C_q` が固定なら、`tilde D_q` を増やすほど捨て誤差上界が下がる。
- 直感: 必要情報量 `C_q` に対し、確保した次元 `tilde D_q` が十分なら圧縮しやすい。

### 式(8): Corollary 1 + Theorem 1 からのQFDR評価
\[
R_F\big(|P\rangle,|\tilde P\rangle\big)
\le O\!\left(\frac{C_q}{\tilde D_q}\right)
\tag{8}
\]
- 式の意味: 歪み率は「情報量 / 圧縮後メモリビット数」で抑えられる。
- 直感: `C_q << D_q` のとき、かなりの次元削減余地がある。

## 5.4 変分切り詰めアルゴリズムの数式
### 式(9): 混合転送行列
\[
\tilde E_l=\sum_x (A_l^x)^*\,\tilde A_l^x,
\qquad
\tilde E_r=\sum_x (A_r^x)^*\,\tilde A_r^x
\tag{9}
\]
- 式の意味: ターゲット iMPS と近似 iMPS の整合を左右ゲージで比較。

### 式(10): ansatz更新
\[
\tilde A_c\leftarrow G_l A_c G_r,
\qquad
\tilde C\leftarrow G_l C G_r
\tag{10}
\]
- 式の意味: 主要固有ベクトル `G_l, G_r` で近似テンソルを更新。

### 式(11): 反復停止に使う誤差
\[
\Delta := \left\|\frac{\tilde A_c}{\eta}-\tilde A_l\tilde C\right\|
\tag{11}
\]
- 式の意味: 混合ゲージ条件からのずれを測る。
- 直感: `Delta < Delta_thresh` で収束判定。

### 式(12): 切り詰め後ユニタリの列構成
\[
\tilde U|j\rangle|0\rangle
=\sum_x (\tilde A_l^x|j\rangle)|x\rangle
\tag{12}
\]
- 式の意味: 左正準形テンソルから生成回路ユニタリ `tilde U` を作る。

### 切り詰め後エンコード写像（本文中記述）
\[
\tilde f_q(x_{-L:0})
\propto
\tilde A_{x_{-L:0}}^l\,\rho\,(\tilde A_{x_{-L:0}}^l)^\dagger
\]
- 式の意味: 過去列に条件づけた初期メモリ状態を決める。

## 5.5 実験で使う過程の式
### 式(13): cyclic random walk
\[
y_{t+1}=\mathrm{Frac}(y_t+x)
\tag{13}
\]
- `x` は分布 `Q(X)` からサンプル。

### 式(14): Dyson-Ising ハミルトニアン
\[
H_{DI}=-\sum_{j,k}J(j,k)\sigma_j\sigma_k
\tag{14}
\]

### 式(15): 熱平衡分布
\[
P(\boldsymbol\sigma)=\frac{1}{Z}\exp\!\left(-\frac{H_{DI}^{(L)}}{T}\right)
\tag{15}
\]

### 式(16): 統計FDR
\[
R_F^{(S)}(P,P')
:= -\lim_{L\to\infty}\frac{1}{L}
\log F^{(S)}(P_L,P'_L)
\tag{16}
\]
- 直感: 量子版QFDRの「確率分布版」。

### 式(17): Corollary 2（量子モデルの歪み境界）
\[
R_F^{(S)}(P,P')\le O(\epsilon_{\tilde d}),
\qquad
R_F^{(S)}(P,P')\le O\!\left(\frac{C_q}{\tilde D_q}\right)
\tag{17}
\]
- 直感: q-sampleで得た境界が、そのまま量子確率モデルにも効く。

## 5.6 Methodsで追加される主要式
### MPS基礎（Methods A）
\[
E=\sum_x A^x\otimes (A^x)^* \tag{18}
\]
\[
A_c:=W_l A W_r,\quad C:=W_lW_r \tag{20}
\]
\[
A_l=\lambda\Gamma,\quad A_r=\Gamma\lambda \tag{21}
\]
\[
\sum_x (A_l^x)^\dagger A_l^x=I,
\quad
\sum_x A_r^x(A_r^x)^\dagger=I \tag{22}
\]

### Theorem 1証明の骨格（Methods B, 式(23)-(30)）
\[
|1-\langle\psi_d^L|\psi_{\tilde d}^L\rangle|
\le\sum_{l=1}^{L}\epsilon_{\tilde d}^{[l]} \tag{23}
\]
\[
\langle\psi_d^L|\psi_{\tilde d}^L\rangle
\ge 1-L\epsilon_{\tilde d} \tag{25}
\]
\[
\tilde E_r=\sum_j \mu_j|r_j\rangle\langle l_j| \tag{26}
\]
\[
\langle\psi_d^L|\psi_{\tilde d}^L\rangle
=\sum_j\mu_j^L\langle\Lambda|r_j\rangle\langle l_j|I\rangle \tag{27}
\]
\[
R_F=-\frac{1}{2}\log_2|\mu_0|
\le
-\frac{1}{2L}\log_2(1-L\epsilon_{\tilde d})+O(1/L)
\tag{30}
\]
- 解釈: 「固有値の支配」と「重なり下界」を結び、式(5)を導く。

### Theorem 2証明の骨格（Methods C, 式(31)-(35)）
\[
\mathcal P(\tilde d,\epsilon_{\tilde d},h)
:=\left\{p_j\,\middle|\,\sum_{k=\tilde d+1}^{\infty}p_k=\epsilon_{\tilde d},\ p_{\tilde d}=h\right\}
\tag{31}
\]
\[
\frac{\epsilon_{\tilde d}}{d-\tilde d}
\le h
\le \frac{1-\epsilon_{\tilde d}}{\tilde d}
\tag{33}
\]
\[
\epsilon_{\tilde d}
\le
\frac{H(\lambda)}{\frac{\tilde d-2}{d-\tilde d}\log_2(d-\tilde d)+\log_2(\tilde d)}
\tag{35}
\]
- 解釈: Schmidt係数を確率分布と見なし、エントロピーのSchur凹性で上界化する。

### 古典圧縮モデル比較（Methods D, 式(36)(37)）
\[
\tilde S_j=
\begin{cases}
\{S_{j(K+1)},\dots,S_{(j+1)(K+1)-1}\}, & j<r \\
\{S_{jK+r},\dots,S_{(j+1)K+r-1}\}, & j\ge r
\end{cases}
\tag{36}
\]
\[
P(y|\tilde S_j)
=\frac{\sum_{S_k\in\tilde S_j}P(y|S_k)P(S_k)}{\sum_{S_k\in\tilde S_j}P(S_k)}
\tag{37}
\]
- 解釈: 古典側は coarse-graining に基づく下界評価で比較。

### KL指標（Methods E, 式(38)(39)）
\[
D_{KL}(P\|Q)=\sum_x P(x)\log_2\frac{P(x)}{Q(x)} \tag{38}
\]
\[
R_{KL}(P\|Q):=\lim_{L\to\infty}\frac{1}{L}
D_{KL}(P(x_{0:L})\|Q(x_{0:L})) \tag{39}
\]

## 6. 定理・系の要点（保証、条件、実用含意）
### Theorem 1
- 保証: 切り詰め誤差和 `epsilon_tilde{d}` で QFDR を上から抑えられる。
- 条件: iMPS 表現でSchmidt係数が降順に取れること、切り詰め次元 `tilde d` を選ぶこと。
- 実用含意: 「どれだけ捨てるか」を直接 QFDR と結びつけられるため、設計指標になる。

### Theorem 2
- 保証: `epsilon_tilde{d}` を `H(lambda)` と `d, tilde d` で上界化。
- 条件: 非ゼロSchmidt係数が `d >= 3`, 切り詰め後 `tilde d >= 3`。
- 実用含意: 情報量が小さいプロセスほど、次元削減余地が理論的に大きい。

### Corollary 1
- 保証: `epsilon_tilde{d} <= C_q / tilde D_q`。
- 条件: q-sample の iMPS 表現と `C_q=H(lambda)` の同一視。
- 実用含意: 実装では `C_q` を見積もるだけで削減可能性の目安が立つ。

### Corollary 2
- 保証: 量子確率モデルの統計FDRも `O(epsilon_tilde{d})` と `O(C_q/tilde D_q)` で境界化。
- 条件: 元過程が量子モデルで正確生成可能であること。
- 実用含意: q-sample 圧縮結果をそのまま「モデル圧縮」の性能保証に転用できる。

## 7. 計算手法（Computational Approach）の手順化
### 7.1 入力
- `P`: 対象確率過程
- `tilde d`: 目標メモリ次元
- `Delta_thresh`: 収束閾値

### 7.2 出力
- `tilde U`: 切り詰め後 q-sample を生成するユニタリ
- `tilde f_q`: 過去列から切り詰めメモリ状態への写像

### 7.3 反復アルゴリズム（論文の box を再構成）
1. Eq. (3) でターゲット q-sample の iMPS を作り、左右正準形を計算。
2. 次元 `tilde d` の ansatz iMPS をランダム初期化。
3. Eq. (9) で混合転送行列を作り、主固有値 `eta` と固有ベクトル `G_l,G_r` を得る。
4. Eq. (10) で `tilde A_c, tilde C` を更新。
5. Eq. (11) で誤差 `Delta` を評価。
6. `Delta < Delta_thresh` まで 3-5 を反復。
7. 収束後、Eq. (12) と Gram-Schmidt で `tilde U` を完成。
8. 固定点 `rho` を使って `tilde f_q` を構成。

### 7.4 停止条件とトレードオフ
- 停止条件: `Delta < Delta_thresh`。
- トレードオフ: `tilde d` を小さくするとメモリ節約が増えるが、QFDRは悪化しやすい。
- 計算コスト（本文）: 変分切り詰めの古典計算コストは概ね `O(d tilde d^2 |X| + d^2 |X|^2)`。

## 8. 実験・結果の整理
### 8.1 例1: cyclic random walk（Markov過程）
### 事実
- 力学: Eq. (13)。
- 離散化で古典最小モデルは `N` 状態、情報コストは `log_2 N`。
- 一方、量子では `N -> infinity` でも `C_q` が有限にとどまる分布族がある。
- 一様分布ケース: `Q(X)=Uniform[-0.1,0.1]`、`tilde d_q in {3,5,7}` を評価。
- 論文記述では `N -> infinity` で `C_q ≈ 3.4`、`tilde D_q <= C_q` でも歪み `O(10^{-2})`。
- 正規分布ケース（平均0, 幅0.1）では `N=256` でも `tilde d_q=7` で `10^{-6}` 未満の歪みを報告。

### 解釈
- 大きなアルファベットを持つMarkov過程でも、必要な「情報」は低次元に圧縮可能。

### 8.2 例2: Dyson-Ising chain（強非Markov過程）
### 事実
- ハミルトニアン Eq. (14)、熱分布 Eq. (15)。
- Markov order は `L`、古典最小モデルは `2^L` 状態。
- 既報として `C_q <= 1 qubit` が知られるが、メモリ空間次元は大きい。
- 本研究では `tilde d_q=2`（1qubit）で圧縮し、高温側で `QFDR < 10^{-3}` を報告。

### 解釈
- 強い時間相関がある非Markov過程でも、低次元量子メモリで高忠実再現が可能な領域がある。

### 8.3 量子モデル vs 古典モデル比較
### 事実
- Proposition 1: 古典モデルで可能な歪み `R` は同次元量子モデルでも実現可能（古典は量子の部分集合）。
- Corollary 2 と Methods D により、同次元比較で量子側の優位（複数桁）を図示。
- KL率比較（Methods E）でも Dyson-Ising で量子優位。

### 解釈
- 「同じメモリ次元なら量子が常に勝つ」と一般断定はしていない。
- ただし本論文の2例では、量子圧縮が古典圧縮より顕著に良いことを示した。

### 8.4 改善点と代償（表）
| 観点 | 従来（無圧縮の量子生成） | 提案法（lossy圧縮） | 代償 |
|---|---|---|---|
| メモリ次元 | 大きい（`d`） | 小さい（`tilde d`） | 近似誤差が入る |
| 歪み | 0（理想生成） | 小さい非ゼロ（QFDR/FDR） | `tilde d` を下げすぎると増加 |
| 理論保証 | 限定的 | Theorem 1/2, Corollary 1/2 で上界あり | 上界は十分条件で最適値ではない |
| 実験確認 | なし | Markov/非Markovの2極で実証 | 問題依存で有効度が変わる |
| 古典比較 | 比較外 | 同次元古典より良い例を提示 | 一般最適性の完全証明ではない |

## 9. Methods A-D の要点と本文との接続
### A. MPS Primer
- 役割: MPS/iMPS、正準形、混合ゲージの定義を与える。
- 本文接続: Eq. (9)-(12) の変分更新と回路合成の基礎。

### B. Proof of Theorem 1
- 役割: 切り詰め重なり下界から QFDR 境界（式(30)）へ。
- 本文接続: `epsilon_tilde{d}` による歪み制御の正当化。

### C. Proof of Theorem 2 and Corollary 1
- 役割: Schmidt分布のエントロピー境界から式(35)を導出。
- 本文接続: `C_q << D_q` のとき圧縮余地が大きいという主張を理論化。

### D. Reduced dimension classical models
- 役割: 古典側の縮約モデル歪み下界を与える比較枠組み。
- 本文接続: 量子圧縮優位を「同次元比較」で示す根拠。

## 10. 限界・注意点
### 事実（論文記載）
- 提案法は **lossy** なので、厳密再現ではなく歪みとのトレードオフ。
- 変分切り詰めの古典前処理コストは無視できない。
- 上界は有用な指針だが、常にタイトな最適境界であるとは限らない。
- KL率は確率ゼロ近傍に敏感で、cyclic random walk では有効比較が難しいと明記。

### 解釈（輪読会向け）
- 実務では「要求精度を満たす最小 `tilde d` を探索」する設計問題として使うのが自然。
- 定理は“安全側”の見積もりと捉えるのが良い。

## 11. 用語集（初学者向け）
- 確率過程: 時系列データを確率で記述する対象。
- causal state: 未来予測に関して同値な過去をまとめた状態。
- q-sample: 出力列全体を重ね合わせで表す量子状態。
- MPS/iMPS: 1次元量子状態の圧縮表現（無限長版が iMPS）。
- Schmidt係数: 量子状態を2分割したときの相関強度スペクトル。
- QFDR: 無限長状態の fidelity 劣化率。
- FDR（統計）: 確率分布列の fidelity 劣化率。
- KL率: KLダイバージェンスを系列長で正規化した極限率。
- injective iMPS: 転送行列の主固有値が非縮退な iMPS（本文定義）。

## 12. 想定質問と回答（輪読会）
### Q1. なぜ `C_q << D_q` だと圧縮できるのか？
A. `D_q` は「箱の大きさ」、`C_q` は「実際に詰まっている情報量」。箱が大きすぎるなら、Schmidt小成分を切っても影響が小さい可能性が高い。式(7)(8)がこの直観を定量化している。

### Q2. QFDR が小さいと何がうれしい？
A. 長い系列を作るほど fidelity は下がるが、QFDRが小さいとその低下速度が遅い。つまり長系列でも統計再現が壊れにくい。

### Q3. これは古典モデルを常に上回るのか？
A. 論文は一般定理として「常に上回る」とは主張していない。だが提示した2例では同次元古典より明確に良い。

### Q4. 実装で最初に決めるべきハイパーパラメータは？
A. `tilde d` と `Delta_thresh`。実運用では要求歪み（許容QFDR）を先に決め、満たす最小 `tilde d` を探索するのが現実的。

### Q5. Methods D の古典比較はなぜ下界になる？
A. まずより広いクラス（pre-model）で最適化し、その最小歪みを計算する。uniﬁlar古典モデルはその部分集合なので、uniﬁlar最適値はそれ以上になる。

## 13. 5分説明用サマリー（短縮版）
1. 問題設定（1分）
- q-sample は有用だが、生成メモリ次元が大きい。
- 論文は「少し誤差を許してメモリ次元を下げる」方法を提案。

2. 中核アイデア（1分）
- q-sample を iMPS で表し、Schmidt小成分を変分法で切り詰める。
- 指標は QFDR（式(4)）。

3. 理論保証（1分）
- Theorem 1: QFDRは捨てたSchmidt和 `epsilon_tilde{d}` で上界化。
- Theorem 2/Corollary 1: `epsilon_tilde{d}` は `C_q` と `tilde D_q` で抑えられる。
- 結果として `R_F = O(C_q/tilde D_q)`（式(8)）。

4. 実験結果（1分）
- cyclic random walk（Markov）と Dyson-Ising（非Markov）で有効。
- 同次元古典圧縮より低歪みを達成する例を示す。

5. 意義と限界（1分）
- 意義: 量子サンプリングの実装負荷（メモリ）を大幅に下げうる。
- 限界: lossy法なので誤差ゼロにはならない。上界は設計指針であり最適値保証そのものではない。

## 14. 参照箇所メモ（輪読準備用）
- イントロと問題意識: p.1
- Framework and tools（定義）: p.2-3
- 理論境界 Theorem 1/2, Corollary 1: p.3-4
- Computational Approach と algorithm box: p.4-5
- 実験（2例）: p.5-6
- 量子モデル比較 Corollary 2: p.7
- Discussion: p.7
- Methods A-D: p.7-10
- KL指標と数値境界: Methods E-F, p.10
