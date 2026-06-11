# 網膜色素変性症（RP）治療開発ロードマップ

最終更新（HTML生成）: 2026年06月11日 22:12

データ取得: ClinicalTrials.gov 2026-06-11 / PubMed 2026-06-11

## エグゼクティブサマリー

本レポートは、網膜色素変性症（Retinitis Pigmentosa, RP）の治療法開発状況を定量的に分析し、効果的な治療法がいつ頃利用可能になるかを予測したものです。

### 3分でわかる

**網膜色素変性症の治療は「2種類」あります。**

1. **A: 進行を止める/遅らせる**
   視力を取り戻すものではないが、数年内に手が届きうる現実的な希望。神経保護・抗酸化・進行抑制を主に狙います。
2. **B: 失った視力を取り戻す/根治を目指す**
   10〜20年スパン。遺伝子補充・編集・細胞移植などで、対象遺伝子や病期が限られることが多いです。

OCU400や光遺伝学（MCO-010/RV-001など）は、進行抑制と機能改善、または視覚再建を狙う**中間**として扱います。根治や完全な視力回復とは分けて読む必要があります。

### まず今すぐできること

1. **遺伝子検査**で原因遺伝子を確定する
2. **自然経過レジストリ**に登録し、治験の声がかかる側に入る
3. **jRCT・難病治験ウェブ**で「網膜色素変性」を定点検索する

### 予測年の読み方（米国FDA承認基準）

- **早い候補の中央値**: 2027年（MCO-010を含む。視覚再建・中間分類の候補を含む）
- **全体の中央値**: 2037年（複数の治療法が利用可能になる時期）
- **現在アクティブな臨床試験**: 54件（重要な完了試験含む）
- **フェーズ平均の過去成功率**: Phase 1: 85.0%, Phase 2: 78.0%, Phase 3: 71.0%（表示・計算上限 85%）

⚠️ **重要**: 上記の予測は**米国FDA承認**を基準としています。
- **日本での承認**: 通常FDA承認の**3-7年後**（過去実績より）
- **欧州での承認**: 通常FDA承認の**1-2年後**
- 詳細は[地域別承認予測タイムライン](regional_approval_timeline.html)をご覧ください。

## 1. データソース概要

### 臨床試験データ
- **データソース**: ClinicalTrials.gov
- **総試験数**: 136件
- **アクティブな試験**: 51件
- **完了した試験**: 55件

### 文献データ
- **データソース**: PubMed
- **総論文数**: 881件
- **検索クエリ**: "retinitis pigmentosa" AND ("gene therapy" OR "cell therapy")
- **期間**: 1993-2026年

#### 年別論文数（直近5年）
| 年 | 論文数 |
|---|--------|
| 2026 | 37 |
| 2025 | 81 |
| 2024 | 63 |
| 2023 | 99 |
| 2022 | 67 |


## 2. モンテカルロシミュレーション結果

### 予測手法
- **シミュレーション回数**: 10000回/プログラム
- **分布**: 三角分布（最小値、中央値、最大値）
- **パラメータ**: フェーズ別ヒストリカル成功率、残フェーズの累積承認確率、開発期間

### 最も有望な治療プログラム（米国FDA承認予測年順）

| 試験ID | 治療法名 | 治療の読み方 | 対象 | フェーズ | スポンサー | フェーズ平均の過去成功率 | 累積承認確率（残フェーズ） | FDA承認予測（中央値） | 日本承認予測（中央値） | 90%信頼区間（FDA） |
|--------|----------|--------------|------|----------|------------|----------------------|---------------------------|---------------------|---------------------|------------------|
| NCT04945772 | Efficacy and Safety of MCO-010 Optogenet... | B寄り/中間（光遺伝学による視覚再建） | 型不問 | PHASE2 | Nanoscope Therapeutics Inc. | 78.0% | 49.8% | 2027年 | 2029年 | [2027, 2027] |
| NCT05203939 | Study to Assess the Safety and Efficacy ... | A/B中間（進行抑制＋低照度視機能改善） | 型不問 | PHASE1, PHASE2 | Ocugen | 85.0% | 42.4% | 2027年 | 2032年 | [2027, 2027] |
| NCT06388200 | A Phase 3 Study Of OCU400 Gene Therapy f... | A/B中間（進行抑制＋低照度視機能改善） | 型不問 | PHASE3 | Ocugen | 63.9% | 63.9% | 2027年 | 2032年 | [2027, 2027] |
| NCT04794101 | Follow-up Gene Therapy Trial for the Tre... | B（遺伝子補充） | 型特異 | PHASE3 | Janssen Research & Development, LLC | 63.9% | 50.0% | 2028年 | 2033年 | [2027, 2028] |
| NCT06646289 | A Follow-on Study for Second-Eye Treatme... | B（遺伝子補充） | 型特異 | PHASE2 | Janssen Research & Development, LLC | 78.0% | 50.0% | 2028年 | 2033年 | [2027, 2028] |
| NCT05926583 | A Study of AAV5-hRKp.RPGR for the Treatm... | B（遺伝子補充） | 型特異 | PHASE3 | Janssen Pharmaceutical K.K. | 63.9% | 50.0% | 2028年 | 2033年 | [2027, 2028] |
| NCT00999609 | Safety and Efficacy Study in Subjects Wi... | 分類未設定 | 未分類 | PHASE3 | Spark Therapeutics, Inc. | 71.0% | 71.0% | 2030年 | 2035年 | [2029, 2031] |
| NCT06333249 | A Study Comparing Two Doses of AGTC-501 ... | B（遺伝子補充） | 型特異 | PHASE2 | Beacon Therapeutics | 78.0% | 49.8% | 2030年 | 2035年 | [2030, 2030] |
| NCT04850118 | A Clinical Trial Evaluating the Safety a... | B（遺伝子補充） | 型特異 | PHASE2, PHASE3 | Beacon Therapeutics | 78.0% | 49.8% | 2030年 | 2035年 | [2030, 2030] |
| NCT05537220 | Oral N-acetylcysteine for Retinitis Pigm... | A（抗酸化・神経保護） | 型不問 | PHASE3 | Johns Hopkins University | 71.0% | 71.0% | 2030年 | 2035年 | [2028, 2031] |


### 日本での承認予測

過去の実績（Luxturna: FDA承認2017年→日本承認2023年、約5.5年の遅延）に基づく予測：

| 治療法 | FDA承認予測 | 日本承認予測（中央値） | 日本承認90%信頼区間 | 遅延期間（中央値） |
|--------|------------|---------------------|-------------------|---------------------|
| NCT04945772 | 2027年 | **2029年** | [2028, 2030] | +2.1年 |
| NCT05203939 | 2027年 | **2032年** | [2031, 2033] | +5.0年 |
| NCT06388200 | 2027年 | **2032年** | [2031, 2033] | +5.0年 |
| NCT04794101 | 2028年 | **2033年** | [2031, 2034] | +5.0年 |
| NCT06646289 | 2028年 | **2033年** | [2031, 2034] | +5.0年 |
| NCT05926583 | 2028年 | **2033年** | [2031, 2034] | +5.0年 |
| NCT00999609 | 2030年 | **2035年** | [2034, 2037] | +5.0年 |
| NCT06333249 | 2030年 | **2035年** | [2034, 2036] | +5.0年 |
| NCT04850118 | 2030年 | **2035年** | [2034, 2036] | +5.0年 |
| NCT05537220 | 2030年 | **2035年** | [2033, 2036] | +5.0年 |


詳細は[地域別承認予測タイムライン](regional_approval_timeline.html)をご覧ください。

### 治療モダリティ別の状況

#### 遺伝子治療
- **試験数**: 36件
- **主要なターゲット遺伝子**: RPGR, RPE65, PDE6A, USH2A
- **最速FDA承認予測**: 詳細表の再シミュレーション結果を参照

#### 細胞治療・再生医療（iPS細胞含む）
- **試験数**: 23件
- **主要プログラム**:
  - **DSP-3077（住友ファーマ/RACTHERA）**: 日本発の他家iPS細胞由来網膜シート。FDA Orphan Drug Designation取得（2026年3月）。米国Phase 1/2（NCT06891885）はRecruiting
  - **OpCT-001（BlueRock/Bayer）**: iPSC由来光受容体細胞。世界初のiPSC由来細胞治療。Phase 1/2a CLARICO試験進行中。FDA Fast Track + Orphan Drug指定
  - **jCells/ファムゼレトセル（jCyte）**: 網膜前駆細胞。Phase 2 JC02-88試験進行中。FDA RMAT指定
- **特徴**: 遺伝子変異に依存しない治療法。失われた網膜細胞を補う再生医療アプローチ
- **FDA承認予測**: 2030年代前半～中盤

#### 低分子薬
- **試験数**: 11件
- **メカニズム**: 神経保護、抗酸化、血流改善
- **主要プログラム**:
  - **NAC Attack（Johns Hopkins）**: NCT05537220。485名・31施設の組入れ目標到達、日本施設なし
  - **NPI-001（Nacuity）**: FDA Breakthrough Therapy Designation取得。Phase 1/2で光受容体喪失50%超抑制と会社発表
  - **SENTAN-PVS-NP（SENTAN Pharma/九州大学）**: jRCT2071260006。国内第1相医師主導治験、2026年7月開始予定
- **FDA承認予測**: 2029-2034年

## 3. 感度分析結果

パラメータの±20%変動が承認時期に与える影響：

![トルネード図](images/tornado.png)

### 主要な影響要因
- **PHASE2 duration** (increase 20%): +0.4年の影響
- **PHASE1 duration** (increase 20%): +0.2年の影響
- **PHASE3 duration** (increase 20%): +0.2年の影響


## 4. 予測の可視化

### 累積承認確率
![CDF図](images/CDF.png)

*図: 主要5プログラムの累積承認確率。横軸は年、縦軸は該当年までに承認される確率。*

### タイムライン予測
![ウォーターフォール図](images/waterfall.png)

*図: 上位20プログラムの承認予測タイムライン。エラーバーは10-90パーセンタイル範囲。*

## 5. 主要な知見と提言

### 患者・家族向け
1. **進行を遅らせる治療**: 視力を取り戻すものではないが、残っている視機能を守る現実的な希望
2. **視力再建・根治を目指す治療**: 10〜20年スパンで、原因遺伝子や病期により対象が限られる
3. **行動提案**:
   - 遺伝子検査を受けて原因遺伝子を特定
   - 患者レジストリへの登録
   - 臨床試験情報の定期的なチェック

📌 **[詳細な行動ガイドはこちら](reality_and_actions.html)** - 予測の現実性と、治療開発を加速するために私たちができる5つの具体的アクション

📊 **[モンテカルロシミュレーションの詳細な計算方法と根拠](simulation_methodology.html)** - 予測値がどのように計算されたか、なぜ信頼できるかの詳細説明

### 研究者向け
1. **成功率の高さ**: RP領域の成功率は他疾患より高い（Phase 3で71%）
2. **開発期間**: Phase 1から承認まで平均8-10年
3. **重点領域**: RPGR、USH2A、PDE6Bなどの主要原因遺伝子

### 政策立案者向け
1. **規制の迅速化**: 希少疾患用医薬品指定の積極活用
2. **研究支援**: 遺伝子治療の製造インフラ整備
3. **患者アクセス**: 高額な治療費への対応策

## 6. 制限事項と注意点

- 本分析は公開データに基づくものであり、企業の非公開パイプラインは含まれません
- 表の「フェーズ平均の過去成功率」は個別試験の成功率ではありません
- 「累積承認確率」は残フェーズ分を掛け合わせた推定値で、承認を保証するものではありません
- 技術革新により予測が大幅に変わる可能性があります
- 規制環境の変化は考慮していません

## 7. 根拠・参照資料

### データソース
- **ClinicalTrials.gov**: https://clinicaltrials.gov/
- **RP臨床試験検索**: https://clinicaltrials.gov/search?cond=Retinitis%20Pigmentosa
- **データ取得日**: 2026-06-11

### 主要試験の詳細
- **MCO-010（Nanoscope）**: https://clinicaltrials.gov/study/NCT04945772
- **OCU400（Ocugen）**: https://clinicaltrials.gov/study/NCT06388200
- **Botaretigene / bota-vec（MeiraGTx）**: https://investors.meiragtx.com/news-releases/news-release-details/meiragtx-announces-acquisition-botaretigene-sparoparvovec-bota
- **AGTC-501 / laru-zova（Beacon）**: https://clinicaltrials.gov/study/NCT04850118
- **NAC Attack（Johns Hopkins）**: https://clinicaltrials.gov/study/NCT05537220
- **NPI-001（Nacuity）**: https://clinicaltrials.gov/study/NCT04355689
- **DSP-3077（Sumitomo Pharma/RACTHERA）**: https://clinicaltrials.gov/study/NCT06891885
- **SPVN06（SparingVision）**: https://clinicaltrials.gov/study/NCT05748873
- **RV-001（Restore Vision）**: https://nanbyo-chiken.nibn.go.jp/detail/jRCT2033240611/
- **SENTAN-PVS-NP（SENTAN Pharma/九州大学）**: https://nanbyo-chiken.nibn.go.jp/detail/jRCT2071260006/
- **Prime editing前臨床**: https://www.nature.com/articles/s41467-025-57628-6
- **ソースコード**: https://github.com/oh-yeah-sea-kit2/retina-roadmap

## 8. 更新履歴

本レポートは自動的に生成・更新されます。最新版は以下でご確認ください：
https://oh-yeah-sea-kit2.github.io/retina-roadmap/

---
---

## ⚠️ 重要な免責事項

**本レポートは研究目的で作成されており、医学的助言ではありません。**

- 記載された承認時期はあくまで**予測**であり、保証するものではありません
- すべての患者に効果があるわけではありません（遺伝子型・病期により異なります）
- 治療に関する決定は**必ず医療専門家にご相談ください**
- 現在の治療を自己判断で中断しないでください

詳細は[免責事項](disclaimer.html)をご確認ください。
