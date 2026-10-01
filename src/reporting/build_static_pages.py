#!/usr/bin/env python3
"""従来の手書き公開4ページを、Markdown本文とPythonテンプレートから再生成する。

本文のHTMLは既存レイアウトを維持するためのMarkdown内HTML。
医療従事者のチェックリストはmedical/for_doctor_checklist.mdから組み込む。
"""
from pathlib import Path
from src.reporting.html_utils import convert_markdown_to_html, process_html_content
from src.reporting.site_metadata import update_public_html_metadata

PAGE_TEMPLATES = {
    'detailed_analysis': """<!DOCTYPE html>

<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>詳細分析データ - 網膜色素変性症治療予測</title>
<meta content="網膜色素変性症治療の詳細な予測データ、AI影響分析、開発ボトルネック、シミュレーション方法論。研究者・専門家向け。" name="description"/>
<!-- OGPタグ -->
<meta content="article" property="og:type"/>
<meta content="詳細分析 - RP治療予測データ" property="og:title"/>
<meta content="モンテカルロシミュレーションによる詳細な予測結果と分析" property="og:description"/>
<!-- CSS -->
<link href="css/common.css" rel="stylesheet"/>
<style>
        /* タブシステム用スタイル */
        .tab-container {
            margin: 30px 0;
        }

        .tabs {
            display: flex;
            border-bottom: 2px solid #ddd;
            margin-bottom: 0;
            flex-wrap: wrap;
        }

        .tab-btn {
            background: none;
            border: none;
            padding: 15px 25px;
            font-size: 1rem;
            cursor: pointer;
            position: relative;
            color: #666;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
        }

        .tab-btn:hover {
            color: var(--primary-color);
            background: #f0f0f0;
        }

        .tab-btn.active {
            color: var(--primary-color);
            font-weight: bold;
            border-bottom-color: var(--primary-color);
            background: white;
        }

        .tab-content {
            display: none;
            padding: 30px;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            animation: fadeIn 0.3s ease;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        /* 詳細データテーブル */
        .data-table {
            font-size: 0.9em;
            margin: 20px 0;
        }

        .data-table th {
            position: sticky;
            top: 0;
            background: var(--primary-color);
            z-index: 10;
        }

        /* 図表のキャプション */
        figure {
            margin: 30px 0;
            text-align: center;
        }

        figure img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }

        figcaption {
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }

        /* AI分析セクション */
        .ai-impact-box {
            background: #e8f4f8;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .scenario-card {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }

        /* ボトルネック分析 */
        .bottleneck-item {
            background: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid var(--accent-color);
        }

        .solution-box {
            background: #e7f3ff;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }

        /* 方法論セクション */
        .formula-box {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
        }

        .parameter-table {
            background: white;
            margin: 20px 0;
        }

        /* モバイル対応 */
        @media screen and (max-width: 768px) {
            .tabs {
                flex-direction: column;
            }

            .tab-btn {
                width: 100%;
                text-align: left;
                border-bottom: 1px solid #eee;
            }

            .tab-content {
                padding: 20px;
            }
        }

        /* ハイライト */
        .highlight {
            background: #ffeb3b;
            padding: 2px 5px;
            border-radius: 3px;
        }

        /* 統計情報ボックス */
        .stat-box {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin: 20px 0;
        }

        .stat-item {
            flex: 1;
            min-width: 200px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: var(--primary-color);
        }

        .stat-label {
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>{content}</body>
</html>""",
    'disclaimer': """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>免責事項 - 網膜色素変性症治療予測</title>
    <meta name="description" content="網膜色素変性症治療予測プロジェクトの免責事項。医学的助言ではないこと、予測の不確実性、個人差について。">

    <!-- OGPタグ -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="免責事項 - RP治療予測">
    <meta property="og:description" content="重要な免責事項と利用上の注意">

    <!-- CSS -->
    <link rel="stylesheet" href="css/common.css">
    <style>
        /* 免責事項専用スタイル */
        .disclaimer-content {
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.8;
        }

        .important-notice {
            background: #ffe4e1;
            border: 2px solid #ff0000;
            padding: 20px;
            border-radius: 10px;
            margin: 30px 0;
        }

        .important-notice h2 {
            color: #d00000;
            margin-top: 0;
        }

        .disclaimer-section {
            background: #f8f9fa;
            padding: 20px;
            border-left: 4px solid var(--accent-color);
            margin: 20px 0;
            border-radius: 0 5px 5px 0;
        }

        .disclaimer-section h3 {
            color: var(--accent-color);
            margin-top: 0;
        }

        .do-section {
            background: #d4edda;
            border-left: 4px solid var(--success-color);
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 5px 5px 0;
        }

        .do-section h3 {
            color: var(--success-color);
            margin-top: 0;
        }

        .dont-section {
            background: #f8d7da;
            border-left: 4px solid var(--accent-color);
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 5px 5px 0;
        }

        .dont-section h3 {
            color: var(--accent-color);
            margin-top: 0;
        }

        .contact-info {
            background: #e7f3ff;
            padding: 20px;
            border-radius: 8px;
            margin: 30px 0;
        }

        .disclaimer-content ul {
            margin: 15px 0;
            padding-left: 30px;
        }

        .disclaimer-content li {
            margin: 10px 0;
        }

        .emphasis {
            font-weight: bold;
            color: #d00000;
        }

        .update-date {
            text-align: right;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
        }
    </style>
</head>
<body>{content}</body>
</html>""",
    'medical_info': """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>医療従事者向け情報 - 網膜色素変性症治療予測</title>
    <meta name="description" content="網膜色素変性症（RP）治療開発の医学的エビデンスと予測根拠。モンテカルロシミュレーションによる統計的予測、臨床試験データ、信頼性評価。">

    <!-- OGPタグ -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="医療従事者向け - RP治療開発予測">
    <meta property="og:description" content="エビデンスに基づく網膜色素変性症治療の承認時期予測">

    <!-- CSS -->
    <link rel="stylesheet" href="css/common.css">
    <style>
        /* 医療従事者向け専用スタイル */
        .evidence-box {
            background: #f0f8ff;
            border: 2px solid var(--primary-color);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .reliability-rating {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 10px 0;
        }

        .stars {
            color: var(--warning-color);
            font-size: 1.2em;
        }

        .checklist {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .checklist h3 {
            margin-top: 0;
            color: var(--secondary-color);
        }

        .checklist ul {
            list-style-type: none;
            padding-left: 0;
        }

        .checklist li {
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }

        .checklist li:before {
            content: "☐ ";
            font-size: 1.2em;
            margin-right: 8px;
        }

        .clinical-significance {
            background: #e8f4f8;
            padding: 20px;
            border-left: 5px solid var(--primary-color);
            margin: 20px 0;
        }

        .data-source {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            font-size: 0.9em;
        }

        .limitation-box {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }

        .methodology-summary {
            background: #e7f3ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        table.evidence-table {
            width: 100%;
            margin: 20px 0;
        }

        table.evidence-table th {
            background-color: var(--primary-color);
            color: white;
        }

        .reference-list {
            font-size: 0.9em;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }

        .reference-list li {
            margin: 5px 0;
        }
    </style>
</head>
<body>{content}</body>
</html>""",
    'patient_guide': """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>患者・ご家族向けガイド - 網膜色素変性症の治療について</title>
    <meta name="description" content="網膜色素変性症（RP）の治療予測と今すぐできる5つのアクション。最速2027年の承認見込み、遺伝子検査の重要性、臨床試験への参加方法など。">

    <!-- OGPタグ -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="患者・ご家族向けガイド - 網膜色素変性症">
    <meta property="og:description" content="治療の見通しと今すぐできる具体的なアクション">

    <!-- CSS -->
    <link rel="stylesheet" href="css/common.css">
    <style>
        /* 患者ガイド専用スタイル */
        .quick-answers {
            background-color: #f0f8ff;
            padding: 30px;
            border-radius: 10px;
            margin: 30px 0;
        }

        .qa-card {
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .qa-card h3 {
            color: var(--primary-color);
            margin-top: 0;
        }

        .action-item {
            background: #e8f4f8;
            padding: 20px;
            margin: 20px 0;
            border-left: 5px solid var(--primary-color);
            border-radius: 0 8px 8px 0;
        }

        .action-item h3 {
            margin-top: 0;
            color: var(--secondary-color);
        }

        .program-card {
            border: 1px solid #ddd;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            background: #f9f9f9;
        }

        .program-card h4 {
            margin-top: 0;
            color: var(--primary-color);
        }

        .timeline-box {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        details {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 10px 15px;
            margin: 15px 0;
        }

        summary {
            cursor: pointer;
            font-weight: bold;
            color: var(--primary-color);
        }

        .cost-info {
            background: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }

        .important {
            background: #ffe4e1;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
        }
    </style>
</head>
<body>{content}</body>
</html>""",
}


def main():
    for name, template in PAGE_TEMPLATES.items():
        source = Path(f"docs/content/main/{name}.md").read_text()
        if name == "medical_info":
            checklist = Path("docs/content/medical/for_doctor_checklist.md").read_text()
            source = source.replace("{doctor_checklist}", convert_markdown_to_html(checklist).replace("<h1>", "<h2>").replace("</h1>", "</h2>"))
        if name == "detailed_analysis":
            content = '<div class="container"><main id="main-content">' + convert_markdown_to_html(source) + '</main></div>'
        else:
            # HTML本文のインデントをMarkdownのコードブロックに変換しない。
            content = source
        output = template.replace("{content}", process_html_content(content))
        output = '\n'.join(line.rstrip() for line in output.splitlines()) + '\n'
        Path(f"docs/public/{name}.html").write_text(output)
        print(f"Regenerated: {name}.html")

    update_public_html_metadata(Path("docs/public"))


if __name__ == "__main__":
    main()
