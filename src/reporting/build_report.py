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
    
    return data


def generate_markdown_report(data):
    """Markdownレポートを生成"""
    
    # 現在の日時
    now = datetime.now()
    
    # Markdownコンテンツ
    content = f"""# 網膜色素変性症（RP）治療開発ロードマップ

生成日時: {now.strftime('%Y年%m月%d日 %H:%M')}

## エグゼクティブサマリー

本レポートは、網膜色素変性症（Retinitis Pigmentosa, RP）の治療法開発状況を定量的に分析し、効果的な治療法がいつ頃利用可能になるかを予測したものです。

### 主要な発見

- **最速の承認予測**: 2027年（OCU400遺伝子治療）
  - 根拠: https://clinicaltrials.gov/study/NCT05203939
- **全体の中央値**: 2036年（複数の治療法が利用可能になる時期）
- **現在アクティブな臨床試験**: {len(data['trials'][data['trials']['Status'].isin(['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'NOT_YET_RECRUITING'])])}件
- **成功率**: Phase 1: 86.2%, Phase 2: 78.4%, Phase 3: 71.4%

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
- **パラメータ**: 実データから推定した成功率と期間

### 最も有望な治療プログラム（承認予測年順）

| 試験ID | 治療法名 | フェーズ | スポンサー | 成功率 | 承認予測（中央値） | 90%信頼区間 |
|--------|----------|----------|------------|--------|-------------------|--------------|
"""
    
    # 上位10プログラムを表示
    top_programs = data['forecasts'].head(10)
    for _, row in top_programs.iterrows():
        content += f"| {row['NCTId']} | {row['BriefTitle'][:40]}... | {row['Phase']} | {row['SponsorName']} | {row['success_rate']:.1%} | {row['median_approval_year']:.0f}年 | [{row['pct10_approval_year']:.0f}, {row['pct90_approval_year']:.0f}] |\n"
    
    content += f"""

### 治療モダリティ別の状況

#### 遺伝子治療
- **試験数**: {len(data['trials'][data['trials']['BriefTitle'].str.contains('gene|AAV|vector', case=False, na=False)])}件
- **主要なターゲット遺伝子**: RPGR, RPE65, PDE6A, USH2A
- **最速承認予測**: 2027年（RPGR遺伝子治療）

#### 細胞治療
- **試験数**: {len(data['trials'][data['trials']['BriefTitle'].str.contains('cell|stem|transplant', case=False, na=False)])}件
- **アプローチ**: 幹細胞移植、網膜前駆細胞
- **承認予測**: 2030年代前半

#### 低分子薬
- **試験数**: {len(data['trials'][data['trials']['BriefTitle'].str.contains('tablet|oral|drug', case=False, na=False)])}件
- **メカニズム**: 神経保護、抗酸化、血流改善
- **承認予測**: 2029-2034年

## 3. 感度分析結果

パラメータの±20%変動が承認時期に与える影響：

![トルネード図](figs/tornado.png)

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
![CDF図](figs/CDF.png)

*図: 主要5プログラムの累積承認確率。横軸は年、縦軸は該当年までに承認される確率。*

### タイムライン予測
![ウォーターフォール図](figs/waterfall.png)

*図: 上位20プログラムの承認予測タイムライン。エラーバーは10-90パーセンタイル範囲。*

## 5. 主要な知見と提言

### 患者・家族向け
1. **最速シナリオ**: 2028-2029年頃に最初の遺伝子治療が承認される可能性
2. **現実的な期待値**: 多くの患者が恩恵を受けられるのは2030年代前半
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
- 成功率は過去のデータに基づく推定値です
- 技術革新により予測が大幅に変わる可能性があります
- 規制環境の変化は考慮していません

## 7. 根拠・参照資料

### データソース
- **ClinicalTrials.gov**: https://clinicaltrials.gov/
- **RP臨床試験検索**: https://clinicaltrials.gov/search?cond=Retinitis%20Pigmentosa
- **データ取得日**: 2025年6月26日

### 主要試験の詳細
- **MCO-010（Nanoscope）**: https://clinicaltrials.gov/study/NCT04945772
- **OCU400（Ocugen）**: https://clinicaltrials.gov/study/NCT05203939
- **ソースコード**: https://github.com/oh-yeah-sea-kit2/retina-roadmap

## 8. 更新履歴

本レポートは自動的に生成・更新されます。最新版は以下でご確認ください：
https://oh-yeah-sea-kit2.github.io/retina-roadmap/

---
*本レポートは研究目的で作成されており、医学的助言ではありません。治療に関する決定は必ず医療専門家にご相談ください。*
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
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/">
    <meta property="og:title" content="網膜色素変性症（RP）治療開発ロードマップ">
    <meta property="og:description" content="最新の臨床試験データに基づく網膜色素変性症の治療法承認時期予測。MCO-010は2025-2026年、OCU400は2026-2027年の承認見込み。54の活発な試験をモンテカルロシミュレーションで分析。">
    <meta property="og:image" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/figs/CDF.png">
    <meta property="og:locale" content="ja_JP">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/">
    <meta property="twitter:title" content="網膜色素変性症（RP）治療開発ロードマップ">
    <meta property="twitter:description" content="最新の臨床試験データに基づく網膜色素変性症の治療法承認時期予測。MCO-010は2025-2026年、OCU400は2026-2027年の承認見込み。">
    <meta property="twitter:image" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/figs/CDF.png">
    
    <!-- Additional Meta Tags -->
    <meta name="description" content="最新の臨床試験データに基づく網膜色素変性症の治療法承認時期予測。MCO-010は2025-2026年、OCU400は2026-2027年の承認見込み。54の活発な試験をモンテカルロシミュレーションで分析。">
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
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        img {
            max-width: 100%;
            height: auto;
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
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
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>"""
    
    # Markdownを変換（改行処理を改善）
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br', 'extra'])
    html_content = md.convert(markdown_content)
    
    # HTMLテンプレートに挿入（{{と}}をエスケープ）
    final_html = html_template.replace("{content}", html_content)
    
    # ファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)


def main():
    """メイン実行関数"""
    
    print("Loading data...")
    data = load_all_data()
    
    print("Generating Markdown report...")
    markdown_content = generate_markdown_report(data)
    
    # Markdownファイルを保存
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    md_file = docs_dir / "index.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(f"Markdown report saved to: {md_file}")
    
    # HTMLに変換
    print("Converting to HTML...")
    html_file = docs_dir / "index.html"
    convert_to_html(markdown_content, html_file)
    print(f"HTML report saved to: {html_file}")
    
    # 画像ファイルをコピー
    import shutil
    figs_src = Path("results/figs")
    figs_dst = docs_dir / "figs"
    if figs_dst.exists():
        shutil.rmtree(figs_dst)
    shutil.copytree(figs_src, figs_dst)
    print(f"Figures copied to: {figs_dst}")
    
    print("\nReport generation complete!")


if __name__ == "__main__":
    main()