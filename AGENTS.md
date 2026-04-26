# Project Rules: p01_short-term_momentum

このファイルは workspace/AGENTS.md に次ぐ優先度で適用される。
最初に必ず workspace/AGENTS.md を読み、すべて遵守すること。
このプロジェクトの Prefer explicit python path は 
- envs/base/.venv/bin/python

---

## Source of truth
- docs/sources/*.pdf : authoritative documents
- docs/notes/*.md    : extracted specification
- *.ipynb            : single source of execution & inspection
  
---

## 0. 目的
本プロジェクトは文献に基づきレビュー・再現実装する。
### 原本
- docs/sources
  
---

## 1. 進め方
### Phase A: 文献レビューのみ（実装禁止）
- docs/sources/ に原本（PDF）を置く
- docs/notes/ に論文を精読し、再現実装に必要な情報を日本語で1本のMarkdownに整理した review.md を作成

### Phase B: 論文ごとに再現実装
- 実装は対象論文１つにつき、それぞれ１つのipynbファイルで完結させること

---

## 2. 注意（リーク防止）
- 特徴量は t までの情報で計算し、t+1 のリターン予測に使う
- 月次リバランスなら「月末で決めたwを翌営業日から適用」など実装上の時点整合を厳密化
