# 学生向けレビュー（S版）: Dimension reduction in quantum sampling of stochastic processes

## S0. この文書の目的
- 本文書は、論文 *Dimension reduction in quantum sampling of stochastic processes* を、輪読会で分野外の学生が理解できる形に再整理したレビュー。
- 根拠は `docs/sources/Dimension reduction in quantum sampling of stochastic processes.pdf` の本文・Methods・図表説明。
- 記述方針は「直感 → 最小限数式 → 意味」。

## S1. 論文情報
### S1.1 基本情報
- タイトル: *Dimension reduction in quantum sampling of stochastic processes*
- 著者: Chengran Yang, Marta Florido-Llinas, Mile Gu, Thomas J. Elliott
- 誌名: *npj Quantum Information* (2025) 11:34
- DOI: [10.1038/s41534-025-00978-2](https://doi.org/10.1038/s41534-025-00978-2)

### S1.2 一言でいうと
- 確率過程の量子サンプル（q-sample）を作るときのメモリ次元を、少しの誤差と引き換えに大幅削減する方法を示した研究。

## S2. 背景と問題設定
### S2.1 何が難しいか
- 複雑な確率過程では、長い将来にわたる相関を保持するためにメモリが大きくなりやすい。
- 量子計算で有望な q-sample でも、生成に必要なメモリ次元が実装の障壁になる。

### S2.2 この論文の狙い
- 「情報量そのもの（必要な内容）」に比べて「メモリ空間の箱（次元）」が大きすぎる場合に、次元を圧縮しても精度を保てることを示す。

## S3. 基本概念
### S3.1 確率過程と因果状態
- 過去列から未来分布を予測する最小古典モデルは epsilon-machine。
- 未来予測が同じ過去をまとめた状態が causal state。

### S3.2 q-sample
- 長さ `L` の出力列全体を重ね合わせた量子状態。
- 最小式:
\[
|P(X_{0:L}|j)\rangle = \sum_{x_{0:L}}\sqrt{P(x_{0:L}|j)}\,|x_{0:L}\rangle
\]
- 直感: 1本ずつサンプルする代わりに、全軌道を同時に持つ量子表現。

### S3.3 MPS/iMPS
- q-sample は1次元量子状態なので MPS として書ける。
- 無限長・平行移動不変の形を iMPS と呼び、本論文の解析基盤になる。

## S4. 主要な量
### S4.1 メモリ次元コスト
\[
D_q := \log_2 d
\]
- `d` はメモリHilbert空間の次元。

### S4.2 情報コスト
\[
C_q := S(\rho),\quad \rho=\sum_j P(j)|\sigma_j\rangle\langle\sigma_j|
\]
- 直感: `D_q` は箱の大きさ、`C_q` は実際に入っている情報量。
- 論文の核心は、しばしば `C_q << D_q` になる点。

## S5. 提案手法（何をしたか）
### S5.1 生成の基本更新
\[
U|\sigma_j\rangle|0\rangle
=\sum_x\sqrt{P(x|j)}e^{i\phi_{xj}}|x\rangle|\sigma_{\lambda(x,j)}\rangle
\tag{S-1}
\]
- 意味: 1ステップごとに出力とメモリ更新を同時に行う。

### S5.2 iMPS表現への写像
\[
A^x_{kj}=\sqrt{P(x|j)}\,\delta_{\lambda(x,j),k}
\tag{S-2}
\]
- 意味: q-sample 生成問題を iMPS 切り詰め問題へ変換する。

### S5.3 歪み指標（QFDR）
\[
R_F(|P\rangle,|P'\rangle)
:=-\lim_{L\to\infty}\frac{1}{2L}\log_2 F(|P_L\rangle,|P'_L\rangle)
\tag{S-3}
\]
- 意味: 長さを延ばしたときの fidelity 劣化速度。
- 小さいほど近い。

### S5.4 変分切り詰め
- `\tilde d` 次元の ansatz iMPS を置き、混合転送行列の主固有構造で更新を反復。
- 収束判定は
\[
\Delta := \left\|\frac{\tilde A_c}{\eta}-\tilde A_l\tilde C\right\| < \Delta_{\mathrm{thresh}}
\tag{S-4}
\]
- 収束後、左正準形からユニタリ `\tilde U` を合成して切り詰め q-sample を生成。

## S6. 理論保証（定理の読み方）
### S6.1 Theorem 1（捨てたSchmidt和で誤差制御）
- 捨てたSchmidt係数和 `\epsilon_{\tilde d}` が小さいと QFDR も小さく抑えられる。
- メッセージ: 「小さい成分を切る」ことの悪化幅を定量制御できる。

### S6.2 Theorem 2（情報量との接続）
- `\epsilon_{\tilde d}` は Schmidt分布エントロピー `H(\lambda)` と `\tilde d` で上から抑えられる。
- メッセージ: 情報量が低い過程では次元削減余地が大きい。

### S6.3 Corollary 1（設計指針）
\[
\epsilon_{\tilde d} \lesssim \frac{C_q}{\tilde D_q},\quad \tilde D_q=\log_2\tilde d
\tag{S-5}
\]
- メッセージ: 目安として `C_q/\tilde D_q` を見れば圧縮可能性を判断しやすい。

### S6.4 Corollary 2（統計モデル側への転用）
- q-sample 側の境界を、確率分布の統計FDR境界としても使える。

## S7. 実験結果
### S7.1 例1: cyclic random walk（Markov）
- 大きい状態数でも、低次元 `\tilde d_q` で低歪み再現を達成。
- 論文では一様/正規ステップ分布の両方で有効性を示す。

### S7.2 例2: Dyson-Ising chain（強非Markov）
- Markov order `L` が上がると古典側メモリ要求は急増。
- それでも `\tilde d_q=2`（1qubit）で高温域の低QFDRを実証。

### S7.3 古典縮約との比較
- 同メモリ次元の古典縮約モデルより、量子縮約モデルの歪みが小さい例を提示。
- KL率比較でも（Dyson-Ising で）量子側が有利。

## S8. Methods A-D の役割
### S8.1 Methods A（MPS Primer）
- 正準形、混合ゲージ、Kraus解釈を与える基礎章。

### S8.2 Methods B（Theorem 1証明）
- 有限長重なり境界から QFDR 境界へ接続。

### S8.3 Methods C（Theorem 2/Corollary 1証明）
- Schmidt係数を確率分布として扱い、エントロピー不等式で上界化。

### S8.4 Methods D（古典側下界）
- coarse-graining と pre-model により古典縮約歪みの下界を与える。

## S9. 限界と注意
### S9.1 研究上の限界
- 手法は lossy なので厳密再現ではない。
- 境界は有用だが常にタイトとは限らない。
- 指標によって比較しやすさが変わる（KLはゼロ確率に敏感）。

### S9.2 実装上の注意
- 変分反復は古典計算コストがある。
- `\tilde d` と `\Delta_{thresh}` の設定で結果が変わるため、要求精度ベースの探索が必要。

## S10. 用語集
- causal state: 未来分布の同値類としての内部状態。
- q-sample: 出力列重ね合わせ状態。
- iMPS: 無限長・平行移動不変MPS。
- Schmidt係数: 分割相関の強度スペクトル。
- QFDR: 量子状態列の fidelity 劣化率。
- 統計FDR: 確率分布列の fidelity 劣化率。
- KL率: 系列長あたりのKL divergence。

## S11. 5分発表の骨子
### S11.1 問題（1分）
- q-sample は有用だがメモリ次元が障壁。

### S11.2 アイデア（1分）
- q-sample を iMPS 化し、小Schmidt成分を変分切り詰め。

### S11.3 理論（1分）
- Theorem 1/2 + Corollary 1 で歪みと情報量の関係を境界化。

### S11.4 実験（1分）
- Markov/非Markovの両極で低歪み圧縮を確認。

### S11.5 意義（1分）
- 量子サンプリングの実装負荷を下げる現実的な道筋を示した。

## S12. 参照ガイド
- 背景: 論文 p.1
- 定義と理論: p.2-4
- 計算手法: p.4-5
- 実験: p.5-7
- Methods A-D: p.7-10
