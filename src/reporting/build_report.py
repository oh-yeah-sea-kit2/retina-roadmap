#!/usr/bin/env python3
"""
分析結果を統合してMarkdownレポートを生成し、HTMLに変換する。
"""

import pandas as pd
import markdown
from pathlib import Path
from datetime import datetime
import json
import yaml
import logging
from src.reporting.html_utils import convert_markdown_to_html, get_responsive_table_css
from src.reporting.message_design import (
    build_trial_program_index,
    get_message_design,
    load_clinical_programs,
    program_for_forecast_row,
)
from src.reporting.site_metadata import (
    create_build_metadata,
    load_build_metadata,
    update_public_html_metadata,
    update_readme_badge,
)

logger = logging.getLogger(__name__)


def load_all_data():
    """全ての分析結果を読み込む"""
    data = {}

    # 臨床試験データ
    data['trials'] = pd.read_parquet("data/processed/clinical_trials.parquet")

    # 文献データ
    data['papers'] = pd.read_csv("data/processed/papers.csv")

    # パラメータ
    with open("data/processed/parameters.yaml", "r") as f:
        data['parameters'] = yaml.safe_load(f)

    # 予測結果
    data['forecasts'] = pd.read_csv("results/forecasts.csv")

    # 感度分析
    data['sensitivity'] = pd.read_csv("results/sensitivity_analysis.csv")

    # サイト共通メタデータ
    data['site_metadata'] = load_build_metadata()

    # 治療の患者向け分類
    data['clinical_programs_kb'] = load_clinical_programs()

    return data


def generate_markdown_report(data):
    """Markdownレポートを生成"""

    site_metadata = data.get('site_metadata', {})
    build_datetime = site_metadata.get('site_last_updated_datetime', "")
    clinical_snapshot = site_metadata.get('clinical_trials_snapshot_date', "")

    phase_rates = data['parameters']['phase_success_rates']
    phase_rate_summary = ", ".join(
        f"{phase.replace('PHASE', 'Phase ')}: {stats['success_rate']:.1%}"
        for phase, stats in phase_rates.items()
        if phase in ["PHASE1", "PHASE2", "PHASE3"]
    )
    kb = data.get('clinical_programs_kb', {})
    programs = kb.get("programs", {})
    trial_index = build_trial_program_index(programs)
    forecasts_by_year = data['forecasts'].sort_values("median_approval_year")
    earliest = forecasts_by_year.iloc[0] if len(forecasts_by_year) else None
    earliest_year = (
        f"{earliest['median_approval_year']:.0f}年"
        if earliest is not None else "未算出"
    )
    earliest_program = (
        program_for_forecast_row(earliest.to_dict(), programs, trial_index)
        if earliest is not None else None
    )
    earliest_label = earliest_program or (
        earliest["BriefTitle"][:40] + "..." if earliest is not None else "未算出"
    )

    # アクティブな試験を抽出
    active_status = ["RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION"]
    active_trials = data['trials'][data['trials']['Status'].isin(active_status)]

    # Markdownコンテンツ
    content = f"""# 網膜色素変性症（RP）治療開発ロードマップ

最終更新（HTML生成）: {build_datetime}

データ取得: ClinicalTrials.gov {clinical_snapshot} / PubMed {site_metadata.get('pubmed_snapshot_date', clinical_snapshot)}

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

- **早い候補の中央値**: {earliest_year}（{earliest_label}を含む。視覚再建・中間分類の候補を含む）
- **全体の中央値**: 2037年（複数の治療法が利用可能になる時期）
- **現在アクティブな臨床試験**: {len(active_trials)}件（重要な完了試験含む）
- **フェーズ平均の過去成功率**: {phase_rate_summary}（表示・計算上限 {data['parameters'].get('success_rate_policy', {}).get('display_cap', 0.85):.0%}）

⚠️ **重要**: 上記の予測は**米国FDA承認**を基準としています。
- **日本での承認**: 通常FDA承認の**3-7年後**（過去実績より）
- **欧州での承認**: 通常FDA承認の**1-2年後**
- 詳細は[地域別承認予測タイムライン](regional_approval_timeline.html)をご覧ください。

## 1. データソース概要

### 臨床試験データ
- **データソース**: ClinicalTrials.gov
- **総試験数**: {len(data['trials'])}件
- **アクティブな試験**: {len(data['trials'][data['trials']['Status'].isin(['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'NOT_YET_RECRUITING'])])}件
- **完了した試験**: {len(data['trials'][data['trials']['Status'] == 'COMPLETED'])}件

### 文献データ
- **データソース**: PubMed
- **総論文数**: {len(data['papers'])}件
- **検索クエリ**: "retinitis pigmentosa" AND ("gene therapy" OR "cell therapy")
- **期間**: {data['papers']['Year'].min():.0f}-{data['papers']['Year'].max():.0f}年

#### 年別論文数（直近5年）
| 年 | 論文数 |
|---|--------|
"""

    # 年別論文数を追加
    recent_papers = data['papers'][data['papers']['Year'] >= 2020]
    year_counts = recent_papers['Year'].value_counts().sort_index(ascending=False)
    for year, count in year_counts.head(5).items():
        content += f"| {year:.0f} | {count} |\n"

    content += f"""

## 2. モンテカルロシミュレーション結果

### 予測手法
- **シミュレーション回数**: {data['parameters']['simulation_parameters']['n_simulations']}回/プログラム
- **分布**: 三角分布（最小値、中央値、最大値）
- **パラメータ**: フェーズ別ヒストリカル成功率、残フェーズの累積承認確率、開発期間

### 最も有望な治療プログラム（米国FDA承認予測年順）

| 試験ID | 治療法名 | 治療の読み方 | 対象 | フェーズ | スポンサー | フェーズ平均の過去成功率 | 累積承認確率（残フェーズ） | FDA承認予測（中央値） | 日本承認予測（中央値） | 90%信頼区間（FDA） |
|--------|----------|--------------|------|----------|------------|----------------------|---------------------------|---------------------|---------------------|------------------|
"""

    # 上位10プログラムを表示
    top_programs = data['forecasts'].head(10)
    for _, row in top_programs.iterrows():
        # 日本承認予測があるかチェック
        if 'japan_median_approval_year' in row:
            japan_approval = f"{row['japan_median_approval_year']:.0f}年"
        else:
            japan_approval = "N/A"
        phase_rate = row.get('phase_historical_success_rate', row['success_rate'])
        cumulative_probability = row.get('cumulative_approval_probability', row['success_rate'])
        program_id = program_for_forecast_row(row.to_dict(), programs, trial_index)
        design = get_message_design(programs.get(program_id, {})) if program_id else {
            "axis_label": "分類未設定",
            "genotype_scope": "未分類",
        }
        content += f"| {row['NCTId']} | {row['BriefTitle'][:40]}... | {design['axis_label']} | {design['genotype_scope']} | {row['Phase']} | {row['SponsorName']} | {phase_rate:.1%} | {cumulative_probability:.1%} | {row['median_approval_year']:.0f}年 | {japan_approval} | [{row['pct10_approval_year']:.0f}, {row['pct90_approval_year']:.0f}] |\n"

    content += f"""

### 日本での承認予測

過去の実績（Luxturna: FDA承認2017年→日本承認2023年、約5.5年の遅延）に基づく予測：

"""
    # 上位10プログラムの日本承認予測を詳細表示
    top10_programs = data['forecasts'].head(10)
    if len(top10_programs) > 0 and 'japan_median_approval_year' in top10_programs.columns:
        content += """| 治療法 | FDA承認予測 | 日本承認予測（中央値） | 日本承認90%信頼区間 | 遅延期間（中央値） |
|--------|------------|---------------------|-------------------|---------------------|
"""
        for _, row in top10_programs.iterrows():
            if 'japan_median_approval_year' in row:
                japan_ci = f"[{row.get('japan_pct10_approval_year', 'N/A'):.0f}, {row.get('japan_pct90_approval_year', 'N/A'):.0f}]"
                delay_years = row.get('japan_median_delay_years', 5.0)
                content += f"| {row['NCTId']} | {row['median_approval_year']:.0f}年 | **{row['japan_median_approval_year']:.0f}年** | {japan_ci} | +{delay_years:.1f}年 |\n"
    else:
        # フォールバック（日本承認データがない場合）
        content += """| 治療法 | FDA承認予測 | 日本承認予測（楽観的） | 日本承認予測（標準） | 日本承認予測（保守的） |
|--------|------------|---------------------|-------------------|---------------------|
| MCO-010 | 2026年 | **2029年**（+3年） | **2031年**（+5年） | **2033年**（+7年） |
| OCU400 | 2027年 | **2030年**（+3年） | **2032年**（+5年） | **2034年**（+7年） |"""

    content += f"""

詳細は[地域別承認予測タイムライン](regional_approval_timeline.html)をご覧ください。

### 治療モダリティ別の状況

#### 遺伝子治療
- **試験数**: {len(data['trials'][data['trials']['BriefTitle'].str.contains('gene|AAV|vector', case=False, na=False)])}件
- **主要なターゲット遺伝子**: RPGR, RPE65, PDE6A, USH2A
- **最速FDA承認予測**: 詳細表の再シミュレーション結果を参照

#### 細胞治療・再生医療（iPS細胞含む）
- **試験数**: {len(data['trials'][data['trials']['BriefTitle'].str.contains('cell|stem|transplant|iPSC|iPS', case=False, na=False)])}件
- **主要プログラム**:
  - **DSP-3077（住友ファーマ/RACTHERA）**: 日本発の他家iPS細胞由来網膜シート。FDA Orphan Drug Designation取得（2026年3月）。米国Phase 1/2（NCT06891885）はRecruiting
  - **OpCT-001（BlueRock/Bayer）**: iPSC由来光受容体細胞。世界初のiPSC由来細胞治療。Phase 1/2a CLARICO試験進行中。FDA Fast Track + Orphan Drug指定
  - **jCells/ファムゼレトセル（jCyte）**: 網膜前駆細胞。Phase 2 JC02-88試験進行中。FDA RMAT指定
- **特徴**: 遺伝子変異に依存しない治療法。失われた網膜細胞を補う再生医療アプローチ
- **FDA承認予測**: 2030年代前半～中盤

#### 低分子薬
- **試験数**: {len(data['trials'][data['trials']['BriefTitle'].str.contains('tablet|oral|drug', case=False, na=False)])}件
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
"""

    # 感度分析の上位要因
    top_sensitivity = data['sensitivity'].nlargest(5, 'impact_years', keep='all')
    for _, row in top_sensitivity.iterrows():
        if abs(row['impact_years']) > 0:
            content += f"- **{row['parameter']}** ({row['change']}): {row['impact_years']:+.1f}年の影響\n"

    content += f"""

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
- **データ取得日**: {clinical_snapshot}

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
"""

    return content


def convert_to_html(markdown_content, output_file):
    """MarkdownをHTMLに変換"""

    # HTML テンプレート
    html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>網膜色素変性症（RP）治療開発ロードマップ</title>
    <meta name="description" content="網膜色素変性症の治療法承認時期予測。公開データとモンテカルロシミュレーションに基づく研究用ロードマップ。音声読み上げ対応版もあります。">


    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/">
    <meta property="og:title" content="網膜色素変性症（RP）治療開発ロードマップ">
    <meta property="og:description" content="最新の臨床試験データに基づく網膜色素変性症の治療法承認時期予測。フェーズ別ヒストリカル成功率と残フェーズの累積承認確率を分けて表示。">
    <meta property="og:image" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/public/images/CDF.png">
    <meta property="og:locale" content="ja_JP">

    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/">
    <meta property="twitter:title" content="網膜色素変性症（RP）治療開発ロードマップ">
    <meta property="twitter:description" content="最新の臨床試験データに基づく網膜色素変性症の治療法承認時期予測。">
    <meta property="twitter:image" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/public/images/CDF.png">

    <!-- Additional Meta Tags -->
    <meta name="description" content="最新の臨床試験データに基づく網膜色素変性症の治療法承認時期予測。フェーズ別ヒストリカル成功率と残フェーズの累積承認確率を分けて表示。">
    <meta name="keywords" content="網膜色素変性症,RP,Retinitis Pigmentosa,遺伝子治療,臨床試験,MCO-010,OCU400,承認予測">
    <meta name="author" content="網膜色素変性症治療開発予測プロジェクト">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 40px;
        }
        h3 {
            color: #7f8c8d;
        }
{get_responsive_table_css()}
        img {
            max-width: 100%;
            height: auto;
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            /* 画像にキャプションを正しく設定 */
            display: block;
        }
        .summary-box {
            background-color: #e8f4f8;
            border-left: 5px solid #3498db;
            padding: 20px;
            margin: 20px 0;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
        }
        strong {
            color: #2c3e50;
        }
        /* フォーカス時の視認性向上 */
        a:focus, button:focus, input:focus, select:focus, textarea:focus {
            outline: 3px solid #ff6600;
            outline-offset: 2px;
        }
        /* スキップリンクのスタイル */
        .skip-link:focus {
            position: static;
            background: #000;
            color: #fff;
            padding: 10px;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <!-- アクセシビリティ向上のためのスキップリンク -->
    <a href="#main-content" class="skip-link" style="position: absolute; left: -9999px; top: 0; z-index: 999;">メインコンテンツへスキップ</a>

    <!-- アクセシビリティ案内 -->
    <div class="accessibility-notice" style="background: #f0f0f0; padding: 10px; margin-bottom: 20px; text-align: center;">
        <p>このページは音声読み上げソフトに対応しています。
        <a href="accessible_summary.html">より詳しい音声読み上げ対応版はこちら</a></p>
    </div>

    <div class="container" id="main-content" role="main">
        <!-- ナビゲーション -->
        <nav role="navigation" aria-label="サイト内ナビゲーション" style="background: #e8f4f8; padding: 15px; margin-bottom: 20px; border-radius: 5px;">
            <h2 style="font-size: 1.2em; margin: 0 0 10px 0;">関連ページ</h2>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="margin: 5px 0;">📊 <a href="index.html">トップページ</a></li>
                <li style="margin: 5px 0;">🌍 <a href="regional_approval_timeline.html">地域別承認予測</a> - 日本・米国・欧州の違い</li>
                <li style="margin: 5px 0;">🎯 <a href="reality_and_actions.html">現実的なアクションガイド</a> - 今すぐできる5つの行動</li>
                <li style="margin: 5px 0;">🔊 <a href="accessible_summary.html">音声読み上げ対応版</a> - スクリーンリーダー最適化</li>
                <li style="margin: 5px 0;">📈 <a href="simulation_methodology.html">シミュレーション方法論</a> - 計算の詳細</li>
                <li style="margin: 5px 0;">👨‍⚕️ <a href="medical_info.html">医療従事者向け情報</a> - 専門家向け詳細</li>
                <li style="margin: 5px 0;">👥 <a href="patient_guide.html">患者・家族向けガイド</a> - わかりやすい解説</li>
            </ul>
        </nav>

        {content}
    </div>

    <!-- フッターにアクセシビリティ情報を追加 -->
    <footer style="margin-top: 50px; padding: 20px; background: #f0f0f0; text-align: center;" role="contentinfo">
        <p>アクセシビリティについて：このサイトは網膜色素変性症の方々にも利用しやすいよう配慮して作成されています。</p>
        <p>改善提案は <a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues">GitHub</a> までお寄せください。</p>
    </footer>
</body>
</html>"""

    # Markdownを変換（URLリンク化とレスポンシブテーブル対応を含む）
    html_content = convert_markdown_to_html(markdown_content)

    # HTMLテンプレートに挿入
    final_html = html_template.replace("{content}", html_content)
    final_html = final_html.replace("{get_responsive_table_css()}", get_responsive_table_css())

    # ファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)


def main():
    """メイン実行関数"""

    site_metadata = create_build_metadata()

    logger.info("Loading data...")
    data = load_all_data()

    logger.info("Generating Markdown report...")
    markdown_content = generate_markdown_report(data)

    # Markdownファイルを保存
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    content_dir = docs_dir / "content" / "main"
    content_dir.mkdir(parents=True, exist_ok=True)
    public_dir = docs_dir / "public"
    public_dir.mkdir(exist_ok=True)

    md_file = content_dir / "index.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    logger.info("Markdown report saved to: %s", md_file)

    # HTMLに変換
    logger.info("Converting to HTML...")
    html_file = public_dir / "report.html"
    convert_to_html(markdown_content, html_file)
    logger.info("HTML report saved to: %s", html_file)

    # トップページとFAQも生成元から再生成
    from src.reporting.build_landing_page import build_landing_page
    from src.reporting.build_faq_page import build_faq_page
    from src.reporting.build_japan_action_guide_html import build_japan_action_guide
    build_landing_page(site_metadata)
    build_faq_page(site_metadata)
    build_japan_action_guide(site_metadata)
    logger.info("Landing page, FAQ, and Japan action guide regenerated")

    # 画像ファイルをコピー
    import shutil
    figs_src = Path("results/figs")
    images_dst = public_dir / "images"
    images_dst.mkdir(exist_ok=True)

    # 既存の画像を削除してから新しい画像をコピー
    for old_img in images_dst.glob("*.png"):
        old_img.unlink()

    for img_file in figs_src.glob("*.png"):
        shutil.copy2(img_file, images_dst / img_file.name)
    logger.info("Figures copied to: %s", images_dst)

    # 生成済みページとREADMEのメタデータをSSOTに揃える
    update_landing_page_date(public_dir, site_metadata)
    update_public_html_metadata(public_dir, site_metadata)
    update_readme_badge(site_metadata)

    logger.info("Report generation complete!")


def update_landing_page_date(public_dir: Path, site_metadata=None):
    """ランディングページ（index.html）の最終更新日をビルドメタデータに揃える"""
    import re

    index_file = public_dir / "index.html"
    if not index_file.exists():
        logger.warning("Landing page not found at %s", index_file)
        return

    site_metadata = site_metadata or load_build_metadata()
    site_date = site_metadata.get("site_last_updated", "")
    data_date = site_metadata.get("clinical_trials_snapshot_date", "")

    content = index_file.read_text(encoding='utf-8')

    # 最終更新日のパターンを探して置換
    pattern = r'最終更新: \d{4}年\d{1,2}月\d{1,2}日'
    replacement = f'最終更新: {site_date}'

    new_content = re.sub(pattern, replacement, content)
    if "データ取得:" not in new_content:
        new_content = new_content.replace(
            "データソース: ClinicalTrials.gov, PubMed |",
            f"データソース: ClinicalTrials.gov, PubMed | データ取得: {data_date} |",
        )

    if new_content != content:
        index_file.write_text(new_content, encoding='utf-8')
        logger.info("Landing page date updated to: %s", site_date)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
