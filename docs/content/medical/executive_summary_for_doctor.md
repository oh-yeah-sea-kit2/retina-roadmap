# 網膜色素変性症治療開発予測：医療従事者向け要約

## 研究概要

### 目的
網膜色素変性症（RP）の治療法がいつ頃利用可能になるかを、公開データに基づいて統計的に予測

### 方法
- **データソース**: ClinicalTrials.gov（{{ clinical_trials_snapshot_date }}時点）
  - 検索URL: https://clinicaltrials.gov/search?cond=Retinitis%20Pigmentosa&aggFilters=status:rec%20act
- **対象試験数**: 127試験（アクティブ54試験）
- **予測手法**: モンテカルロシミュレーション（10,000回/試験）
- **パラメータ**: 過去の臨床試験データから推定した成功率と開発期間

## 主要な予測結果

### 最速承認候補（高確度）

1. **MCO-010（Nanoscope Therapeutics）**
   - 承認予測：最新の再シミュレーション結果を参照
   - 根拠：RESTORE試験で統計的有意性達成。申請・審査状況により時期は変動
   - 特徴：変異非特異的、外部デバイス不要の光遺伝学的アプローチ
   - **臨床試験登録**: https://clinicaltrials.gov/study/NCT04945772
   - **企業プレスリリース**: https://nanostherapeutics.com/2024/03/nanoscope-therapeutics-announces-positive-topline-results/
   - **FDA Fast Track指定**: https://nanostherapeutics.com/2023/08/fda-fast-track-designation/

2. **OCU400（Ocugen）**
   - 承認予測：2027年以降（トップラインPhase 3データは2027年Q1予定）
   - 根拠：Phase 3 liMeliGhT（NCT06388200）は140名の組入れ完了、rolling BLAは2026年Q3計画
   - 特徴：遺伝子非依存型、マスター遺伝子調節
   - **Phase 3試験**: https://clinicaltrials.gov/study/NCT06388200
   - **組入れ完了発表**: https://ir.ocugen.com/news-releases/news-release-details/ocugen-announces-phase-3-limelight-enrollment-completion-ocu400
   - **EAP方針**: https://ocugen.com/expanded-access-policy/（NCT06574997はClinicalTrials.gov上でNO_LONGER_AVAILABLE）
   - **FDA RMAT指定**: https://ir.ocugen.com/news-releases/news-release-details/ocugen-receives-fda-regenerative-medicine-advanced-therapy

### 中期的展望（2029-2035年）
- 複数の遺伝子特異的治療が承認見込み
- RPGR、USH2A、PDE6Aなどの主要変異に対する治療法

### 全体の中央値：2036年
- 多様な治療オプションが揃う時期
- 初期段階の試験が成熟

## 予測の信頼性と限界

### 強み
- 公的データベースに基づく透明性
- 統計的手法による不確実性の定量化
- 最新の試験情報を反映（データ取得: {{ clinical_trials_snapshot_date }}）

### 限界
1. **外的要因を考慮できない**
   - 予期せぬ安全性問題
   - パンデミック等の社会的影響
   - 規制要件の変更

2. **データの制約**
   - 成功率は限定的なサンプルに基づく
   - 企業の内部情報は反映されない
   - 日本での承認時期は別途考慮必要

3. **技術的前提**
   - 製造スケールアップの成功を仮定
   - 規制当局との標準的な協議を前提

## 臨床的意義

### 患者カウンセリングへの活用
- エビデンスに基づく期待値の設定
- 遺伝子検査の重要性の説明
- 治験参加の検討材料

### 注意事項
- 個々の患者への適用は遺伝子型に依存
- 病期による治療効果の差異
- 高額医療費（推定1-3億円）への準備

## データ更新情報

- **Botaretigene sparoparvovec / bota-vec**：LUMEOSは主要評価項目未達だが、MeiraGTxが2026年4月にJ&Jから取得し、米国・EU・日本で申請を進める方針
  - MeiraGTx発表: https://investors.meiragtx.com/news-releases/news-release-details/meiragtx-announces-acquisition-botaretigene-sparoparvovec-bota
  - LUMEOS: https://clinicaltrials.gov/study/NCT04671433
- **AGTC-501 / laru-zova**：VISTA（NCT04850118）は85名の組入れ完了。12ヶ月トップラインは2026年後半予定
  - Beacon発表: https://www.beacontx.com/news-and-events/beacon-therapeutics-completes-enrollment-in-registrational-phase-2-3-vista-trial-of-laru-zova-for-patients-with-xlrp/
- **NAC Attack**：NCT05537220は485名・31施設の組入れ目標に到達。日本施設は掲載なし
  - Johns Hopkins: https://www.hopkinsmedicine.org/wilmer/research/nac-attack
- **NPI-001**：FDA Breakthrough Therapy指定（2025年10月）、SLO-RP Phase 1/2で光受容体喪失50%超抑制と会社発表
  - Nacuity発表: https://www.nacuity.com/news/nacuity-pharmaceuticals-granted-u-s-fda-breakthrough-therapy-designation-for-npi-001-n-acetylcysteine-amide-tablets-for-the-treatment-of-retinitis-pigmentosa/
- **DSP-3077**：FDA Orphan Drug Designation取得（2026年3月）、米Phase 1/2（NCT06891885）はRecruiting
  - Sumitomo Pharma America: https://news.us.sumitomo-pharma.com/press-release-details/2026/Sumitomo-Pharma-America-Announces-that-its-Investigational-Therapy-DSP-3077-Has-Received-FDA-Orphan-Drug-Designation-for-the-Treatment-of-Retinitis-Pigmentosa/default.aspx
- **Biogen BIIB112**：開発中断
  - 開発中止発表: https://investors.biogen.com/news-releases/news-release-details/biogen-announces-topline-results-phase-3-gene-therapy-study
- 最新情報チェック日: {{ data_check_date }}

---

**免責事項**: 本予測は研究目的であり、医学的助言ではありません。治療に関する決定は必ず専門医の判断に基づいて行ってください。

**問い合わせ先**: プロジェクトGitHub: https://github.com/oh-yeah-sea-kit2/retina-roadmap
