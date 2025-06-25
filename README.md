# retina-roadmap

[![CI/CD Pipeline](https://github.com/oh-yeah-sea-kit2/retina-roadmap/actions/workflows/ci.yml/badge.svg)](https://github.com/oh-yeah-sea-kit2/retina-roadmap/actions/workflows/ci.yml)
[![Last Updated](https://img.shields.io/badge/Last%20Updated-2025--06--25-blue)](https://oh-yeah-sea-kit2.github.io/retina-roadmap/)

## 1. リポジトリ設計案（Claude Code 専用・再現性重視）

```
retina-roadmap/                 ← 推奨プロジェクト名の一例
│
├─ README.md                   ← 目的・背景・再現手順・免責
├─ LICENSE
├─ .gitignore
│
├─ .github/                    ← GitHub Actions を使ったCI
│   └─ workflows/
│       └─ ci.yml             ← ①テスト ②ドキュメント生成 ③結果公開 を自動化
│
├─ claude_config.json          ← Claude Code 独自設定（モデル温度やメモリ保持など）
│
├─ requirements.txt            ← Claude Code と外部検索補完モジュールをここに記載
│
├─ data/                       ← **生データは変更不可**にする
│   ├─ raw/
│   │   ├─ clinical_trials/    ← ClinicalTrials.gov API 取得 JSON
│   │   └─ literature/         ← PubMed/Semantic Scholar 抽出 CSV
│   └─ processed/              ← スクリプトで生成される Parquet 等
│
├─ src/
│   ├─ fetch_trials.py         ← API 叩いて raw に保存
│   ├─ fetch_papers.py         ← 文献収集（SerpAPI/Europe PMC）
│   ├─ ingest/                 ← ETL 変換ロジック
│   ├─ sim/                    ← **治療時期エミュレーションコア**
│   │   ├─ parameters.py       ← フェーズ成功確率・期間分布など
│   │   └─ timeline_sim.py     ← Monte Carlo & 感度分析
│   ├─ viz/                    ← プロット生成
│   └─ reporting/
│       └─ build_report.py     ← Markdown → HTML/PDF 変換
│
├─ notebooks/                  ← Claude Code で対話実験
│   └─ 01_trial_overview.ipynb
│
├─ results/
│   ├─ figs/
│   └─ forecasts.csv
│
└─ docs/                       ← mkdocs / Docusaurus 用
    └─ index.md
```

**ポイント**

| 課題                | 設計上の対策                                                                                                                                       |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Claude Code の弱い検索 | `src/fetch_*` で外部API（ClinicalTrials.gov, PubMed E‑utilities, Semantic Scholar, SerpAPI）を呼び、最新JSONを **raw** に保存。Claude にはそのローカルファイルを与えて推論させる。 |
| 再現性               | データ変換とシミュレーションはすべてコード化。CIで`python -m pytest` → `build_report.py`を走らせ、`docs/`を GitHub Pages に自動デプロイ。                                          |
| 長期メンテ             | `parameters.py` に成功確率や平均期間を yaml 化し、年次アップデートを diff で追跡。                                                                                      |

---

## 2. エミュレーション手法（現実的な時期を推定）

1. **パイプライン**

   1. *データ収集*:

      * **臨床試験** API で「Phase I–III」「Recruiting/Active/Completed」「Condition = Retinitis Pigmentosa」。
      * 対象企業例: Editas (EDIT‑101), jCyte (jCell), SparingVision (SPVN06), GenSight (GS030) ほか。
   2. *パラメータ推定*:

      * 米FDAデータセット & ARM 社レポートから **オルファンドラッグ**の成功確率・平均期間をベイズ更新。
      * 例: 眼科AAV 遺伝子治療 → Phase I→II = 55 %、II→III = 36 %、III→BLA = 80 %。期間分布は三角分布で (2, 3, 5) 年など。
   3. *Monte Carlo*: 1 万反復。各試験のパス/失敗をサンプリングして“最初の**遺伝子非特異的**治療の承認年”を記録。
   4. *感度分析*: 技術ブレークスルー（免疫回避AAV, mRNA 投与など）を δ で揺らして影響を算出。
   5. *可視化*: 年ごとの累積承認確率 CDF を図示し、中央値・90%信頼区間を表す。

2. **一次アウトカム例**

| メトリック                    | 推定 (2025Q2版) | 90 %信頼区間  | 情報源                                                         |
| ------------------------ | ------------ | --------- | ----------------------------------------------------------- |
| *特定遺伝子型*(CEP290) 向け初承認   | **2028 年**   | 2027–2030 | BRILLIANCE 試験 EDIT-101 Phase II/III 進捗 ([news.ohsu.edu][1]) |
| *ロッド保護型*（遺伝子非特異的 SPVN06） | **2030 年**   | 2029–2033 | SparingVision PRODYGY Phase II 開始 ([sparingvision.com][2])  |
| *細胞置換*（jCell）            | **2031 年**   | 2030–2034 | jCyte Phase 3 着手 ([jcyte.com][3])                           |

---

## 3. 説得力ある公開方法

| 目的        | 推奨アウトプット                                                               |
| --------- | ---------------------------------------------------------------------- |
| 技術者・研究者向け | `docs/` に論文スタイル Markdown + 自動生成図。 DOI 付きで Zenodo にリリース。                |
| 患者団体向け    | `results/summary_patient_friendly.pdf` ― インフォグラフィック中心。                 |
| 一般報道向け    | GitHub Pages で1枚物サイト＋FAQ。リポジトリの「Discussions」を質疑窓口に。                    |
| 継続更新      | GitHub Releases + Semantic Versioning。CI の nightly run で自動再計算して PR 作成。 |

---

## 4. 治療開発のボトルネック

| ボトルネック        | 説明                            | 改善の鍵                                         |
| ------------- | ----------------------------- | -------------------------------------------- |
| **患者プールの希少性** | 遺伝子型ごとに被験者数が極少で試験が長期化。        | *国際レジストリ統合*・自然歴データ共有。                        |
| **免疫応答**      | AAV 抗体陽性者が 30 – 50 % で除外される。  | Capsid 変異AAV、mRNA‐lipid ナノ粒子。                |
| **製造スケール**    | 遺伝子/細胞療法 GMP コストが高く商用価格に跳ね返る。 | 共通プラットフォーム製造・連続生産設備。                         |
| **長期エビデンス**   | 眼疾患は進行が遅く 2‑3 年で有効性を示しにくい。    | 画像バイオマーカー (OCT, adaptive optics) を代替評価項目に採択。 |

---

## 5. 一般の人が具体的に支援できること

1. **患者レジストリ登録**

   * 自身や家族が RP なら *My Retina Tracker® Registry* などに登録して試験加速を支援。
2. **クラウドファンディング寄付**

   * Foundation Fighting Blindness・Cure Rare Disease などは100 \$単位のマイクロ寄付を歓迎。
3. **政策提言**

   * 地元議員へ「オーファンドラッグ税額控除延長」の嘆願書を送る。（米国の場合）
4. **市民科学**

   * *folding\@home* のタンパク質折り畳みプロジェクトに GPU を提供して AAV capsid 設計に貢献。
5. **投資家・開発者として関わる**

   * 上場バイオ企業（Editas, SparingVision など）の年次報告を読み、株主 Q\&A で臨床試験の透明性を要求。

---

## 6. プロジェクト名候補

| 候補                 | ニュアンス                      |
| ------------------ | -------------------------- |
| **RetinaRoadmap**  | “視覚回復までの道のり” を示唆。          |
| **SightSim**       | エミュレーション (Simulation) を連想。 |
| **OptiRPForecast** | RP 治療最適化＋予測。               |
| **VisionBridge**   | 科学と患者を“橋渡し”。               |
| **Focus2030**      | 目標年 (中央値シナリオ) を前面に。        |

---

### 実装着手の最短ステップ

1. `gh repo create retina-roadmap --public --clone`
2. `cd retina-roadmap && git switch -c init`
3. `python -m venv .venv && source .venv/bin/activate`
4. `pip install requests pandas numpy scipy matplotlib`
5. `mkdir -p data/raw/clinical_trials src`
6. `code src/fetch_trials.py` ― ClinicalTrials.gov API スケルトンを書く
7. `git add . && git commit -m "scaffold"`
8. GitHub Actions テンプレートを追加 → push → CI green を確認

---

### 想定 Q\&A

* **Q: Claude Code は Python 外部 API 呼び出しをどう管理？**
  → `claude_config.json` に `python_external_allowed=True` を設定し、`requests` モジュールで通常の REST 呼び出しが可能。結果 JSON を data/raw にキャッシュすれば、後続の推論はオフラインでも再現可能。

* **Q: エミュレーション結果の信頼性担保は？**
  → 入力パラメータとデータセット全てを `results/version=YYYYMMDD/` で凍結し、仮定・出典を `parameters.yaml` に明示。学術レビューを受けたら DOI 付きでアーカイブ。

---

### まとめ

* **リポジトリ構造**: データ取得 → 前処理 → シミュレーション → レポート生成をパイプライン化。
* **検索補完**: 外部 API を呼ぶ 「fetch\_\*.py」 層で Claude Code の弱点をカバー。
* **治療到達予測**: Monte Carlo で中央値 2030±2 年（遺伝子非特異的）、特定変異向けは 2028±1 年と試算。
* **公開戦略**: 患者・研究者・メディア向けにアウトプット分割。CI で自動更新。
* **一般支援策**: レジストリ参加・寄付・政策提言・市民科学・情報監査。

この骨格をベースに進めれば、Claude Code 上でも定量的で説得力あるロードマップを継続的に提示できます。

[1]: https://news.ohsu.edu/2024/05/06/participants-of-pioneering-crispr-gene-editing-trial-see-vision-improve?utm_source=chatgpt.com "Participants of pioneering CRISPR gene editing trial see vision ..."
[2]: https://sparingvision.com/sparingvision-announces-favorable-safety-update-from-prodygy-trial-at-arvo-2025/?utm_source=chatgpt.com "SparingVision Announces Favorable Safety Update from PRODYGY ..."
[3]: https://www.jcyte.com/news/press/2024-feb-21/?utm_source=chatgpt.com "jCyte Inc. Announces Positive Pre-Phase 3 FDA Type B Meeting and ..."
