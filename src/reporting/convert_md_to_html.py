#!/usr/bin/env python3
"""
MarkdownファイルをHTMLに変換（ナビゲーション付き）
"""

import markdown
from pathlib import Path

def convert_with_nav(md_file, title):
    """Markdownファイルをナビゲーション付きHTMLに変換"""
    
    # Markdownファイルを読み込む
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # HTMLテンプレート
    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="網膜色素変性症の治療法開発予測プロジェクトの関連資料">
    
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 30px;
        }}
        nav {{
            background: #e8f4f8;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        nav h3 {{
            font-size: 1.2em;
            margin: 0 0 10px 0;
        }}
        nav ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        nav li {{
            margin: 5px 0;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- ナビゲーション -->
        <nav>
            <h3>関連ページ</h3>
            <ul>
                <li>📊 <a href="index.html">メインレポート</a> - 詳細な予測データ</li>
                <li>🎯 <a href="reality_and_actions.html">現実的なアクションガイド</a> - 今すぐできる5つの行動</li>
                <li>🔊 <a href="accessible_summary.html">音声読み上げ対応版</a> - スクリーンリーダー最適化</li>
                <li>🤖 <a href="ai_acceleration_impact.html">AI活用による開発加速予測</a> - 最大45%短縮の可能性</li>
                <li>📈 <a href="simulation_methodology.html">シミュレーション方法論</a> - 計算の詳細</li>
                <li>🏥 <a href="for_doctor_checklist.html">医師向けチェックリスト</a> - 信憑性確認用</li>
                <li>📄 <a href="executive_summary_for_doctor.html">医師向け要約</a> - 研究概要と根拠</li>
            </ul>
        </nav>
        
        <!-- Content will be inserted here -->
    </div>
</body>
</html>"""
    
    # Markdownを変換
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br', 'extra'])
    html_content = md.convert(md_content)
    
    # リンクを修正（.mdを.htmlに変換）
    html_content = html_content.replace('.md"', '.html"')
    html_content = html_content.replace('.md#', '.html#')
    
    # HTMLテンプレートに挿入
    final_html = html_template.replace("<!-- Content will be inserted here -->", html_content)
    
    # 出力ファイル名を生成
    output_file = md_file.with_suffix('.html')
    
    # HTMLファイルを保存
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"Converted: {md_file} -> {output_file}")

def main():
    """メイン処理"""
    docs_dir = Path("docs")
    
    # 変換するファイルのリスト
    files_to_convert = [
        ("ai_acceleration_impact.md", "AI活用による開発加速予測"),
        ("for_doctor_checklist.md", "医師向けチェックリスト"),
        ("executive_summary_for_doctor.md", "医師向け要約"),
        ("simulation_methodology.md", "シミュレーション方法論"),
        ("bottlenecks.md", "開発ボトルネック分析"),
        ("publication_disclaimer.md", "免責事項"),
        ("publication_checklist.md", "公開前チェックリスト"),
        ("current_status_facts.md", "網膜色素変性症治療開発の現状"),
        ("ai_predictions.md", "AI予測による治療承認時期の分析")
    ]
    
    for filename, title in files_to_convert:
        md_file = docs_dir / filename
        if md_file.exists():
            convert_with_nav(md_file, title)
        else:
            print(f"File not found: {md_file}")

if __name__ == "__main__":
    main()