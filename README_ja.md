# Tri-Brain System — RDAC実装

> **RDACフレームワークの公式実装**  
> 複数のAIエージェントが構造的に異なる役割で並列議論し、人間の思考を深化させるシステム。

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18859272.svg)](https://doi.org/10.5281/zenodo.18859272)
[![License: AGPLv3 + Commons Clause](https://img.shields.io/badge/License-AGPLv3%20%2B%20Commons%20Clause-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)

[English README is here](README.md)

---

## これは何か

**Tri-Brain System**は、**RDACモデル**（Role-Density-Architecture-Convergence）に基づいた、Human-in-the-Loopの複数AIエージェント対話フレームワークです。

3つのAIエージェントが構造的に異なる役割で問いに答え、4つ目のエージェント（Diff AI）が衝突の核心・隠れた前提・次の問いを抽出します。人間がその選択に参加しながら、思考が本当の収束に達するまで議論を深化させます。

**チャットボットではありません。思考の深化エンジンです。**

---

## 作った経緯

コンビニ店長として働きながら、12年間の読書と20年以上の即興ダンスを通じて培った「思考の構造化」への関心から生まれました。

AIを使って問いを深化させるとき、複数のAIに同じ問いを同じ形で渡すと、どのモデルも似た答えを返してくる——**同期バイアス（Synchrony Bias）**という現象に気づきました。

この問題を解決するために設計したのがRDACモデルです。役割（V）と情報密度（D）を独立して制御することで、AIの収束を防ぎ、本物の衝突と深化を生み出します。

論文はZenodoに公開しています（英語）：  
[https://doi.org/10.5281/zenodo.18859272](https://doi.org/10.5281/zenodo.18859272)

---

## RDACモデルの4次元

| 次元                   | 説明                                                           |
| ---------------------- | -------------------------------------------------------------- |
| **R** — 役割差異化     | Logic（構造脳）/ Emotion（情動脳）/ Meta-View（俯瞰脳）の3役割 |
| **D** — 情報密度       | 同じ問いを密度の異なる形で各脳に渡す                           |
| **A** — アーキテクチャ | 3脳 + Diff AI + Human-in-the-Loop = 5層構造                    |
| **C** — 収束検出       | 議論が本当の深さに達したことを自動検出                         |

> **核心的な発見：VとDは独立して制御しなければならない。**  
> 同じ密度で渡すと、役割が違っても収束してしまう。

---

## セッションの流れ

```
初期問い（あなたが入力）
      │
      ▼
3つの脳が並列で答える
  Logic Brain    [情報密度：高]
  Emotion Brain  [情報密度：低]
  Meta-View Brain[情報密度：中]
      │
      ▼
Diff AIが分析する
  ・Brain Summary（各脳の主張を1文で）
  ・Core Conflict（LogicとEmotionの衝突を断定）
  ・The Cost（各選択で永久に失うもの）
  ・Hidden Assumption（3脳が共有する盲点）
  ・Cognitive Hook（問いに直結した具体的シーン）
  ・Reframed Question + A/B（次の問い）
      │
      ▼
あなたが選択する
  A / B / C（独自の立場）/ Q（終了）
      │
      ▼
  （収束が検出されるまで繰り返す）
      │
      ▼
最終リフレクション
  L0：最初の問いへの直接回答
  Q1：最も印象に残った気づき
  Q2：一致・不一致とその理由
```

ブラウザで `http://127.0.0.1:7331/tri_brain_live.html` を開くとリアルタイムで議論を確認できます。

---

## ファイル構成

```
tri_brain_v2/
├── config.py        # 定数・モデル名・ラウンド上限
├── prompts_ja.py    # 日本語プロンプト（全プロンプトを関数化）
├── prompts_en.py    # 英語プロンプト（1行変更で切り替え可能）
├── classifier.py    # 選択肢分類・問いの型判定
├── core.py          # 3脳実行・Diff AI・収束チェック
├── renderer.py      # HTMLアーカイブ・ライブサイドバー生成
└── main.py          # セッションループ（エントリポイント）
```

**英語セッションへの切り替えは2行だけ：**

```python
# core.py と main.py のimport行を変更するだけ
from prompts_en import ...  # prompts_ja → prompts_en
```

---

## 必要なもの

- Python 3.10以上
- OpenAI Python SDK（`pip install openai`）
- OpenAI APIキー

---

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/phantomodysseyai-rgb/tri-brain-rdac.git
cd tri-brain-rdac/tri_brain_v2

# 依存関係をインストール
pip install openai

# APIキーを環境変数に設定
# Windows PowerShell:
$env:OPENAI_API_KEY = "your-api-key-here"

# macOS / Linux:
export OPENAI_API_KEY="your-api-key-here"

# 実行
python main.py
```

---

## 実際の出力例

```
⚔️ Core Conflict
Logicは「実験で証拠を積めば判断できる」と言い、
Emotionは「感じる可能性があるなら今すぐ保護せよ」と言っている。
これらは両立しない。

👁️ Hidden Assumption
外から測れる指標で「感じているか」を確実に判断できると
三者全員が無自覚に前提にしている。

🔁 Reframed Question
Step1: 証拠主義で判断する立場
Step2: 観測可能性と存在を同一視している盲点
問い: 観測できないものは存在しないとみなしてよいか？
A: 観測できないなら存在を主張できないとみなす
B: 観測できなくても存在可能性は残るとみなす
```

---

## 収束検出の仕組み

Round 4以降、以下の3条件で収束を自動判定します。

| 条件         | 説明                                       |
| ------------ | ------------------------------------------ |
| **軸固定**   | 同じ次元の衝突が2ラウンド連続する          |
| **前提枯渇** | 新しい隠れた前提が問題構造を変えない       |
| **政策枯渇** | 新しい選択肢が前ラウンドの焼き直しに留まる |

（軸固定 AND 前提枯渇）または（軸固定 AND 政策枯渇）で収束判定。

---

## 引用

学術研究でこのシステムを使用する場合は以下を引用してください：

```bibtex
@misc{ishikawa2026rdac,
  author    = {Masanao Ishikawa},
  title     = {RDAC: Relational Density, Diversity, Stability, and Closure},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.18859272},
  url       = {https://doi.org/10.5281/zenodo.18859272}
}
```

---

## ライセンス

GNU AGPLv3 + Commons Clause

- ✔ 個人利用・学習：自由に使用可
- ✔ 学術研究・引用：自由に使用可
- ✔ 改変・再配布（ソース公開前提）：AGPLv3の範囲で許可
- ✗ 商用利用（SaaS・製品・有償サービス）：許可なく禁止

**商用ライセンスについて**  
商用での利用を検討している場合は、別途有償ライセンスの発行が可能です。  
X（旧Twitter）のDMからお問い合わせください。

---

## サポート

このプロジェクトが役に立った場合、開発継続のためにサポートをお願いします：

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-PhantomOdysseyAI-ea4aaa?logo=github-sponsors)](https://github.com/sponsors/phantomodysseyai-rgb)

機関資金なしの独立研究として続けています。  
少額でも大きな励みになります。

---

## 作者

**石川 昌直（Phantom Odyssey AI）**  
独立研究者・クリエイター  
コンビニ店長として働きながら、哲学・AI・創作を探求しています。

X: [@PhantysseyAI](https://x.com/PhantysseyAI)  
Zenodo論文: [https://doi.org/10.5281/zenodo.18859272](https://doi.org/10.5281/zenodo.18859272)  
GitHub Sponsors: [https://github.com/sponsors/phantomodysseyai-rgb](https://github.com/sponsors/phantomodysseyai-rgb)
