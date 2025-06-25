#!/usr/bin/env python3
"""
シミュレーション手法説明のMarkdownをHTMLに変換
"""

import markdown
from pathlib import Path

def convert_to_html():
    """MarkdownファイルをHTMLに変換"""
    
    # ファイルパスを設定
    md_file = Path("docs/simulation_methodology.md")
    html_file = Path("docs/simulation_methodology.html")
    
    # Markdownファイルを読み込み
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # HTMLテンプレート
    html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>モンテカルロシミュレーションの詳細な計算方法と根拠 - RP治療開発</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
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
            border-left: 5px solid #e74c3c;
            padding-left: 15px;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 30px;
        }
        details {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 10px 15px;
            margin: 15px 0;
        }
        summary {
            cursor: pointer;
            font-weight: bold;
            color: #3498db;
            padding: 5px 0;
        }
        summary:hover {
            color: #2980b9;
        }
        details[open] summary {
            margin-bottom: 10px;
            border-bottom: 1px solid #dee2e6;
        }
        code {
            background-color: #f8f9fa;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        blockquote {
            background-color: #e8f6f3;
            border-left: 5px solid #16a085;
            padding: 15px;
            margin: 20px 0;
        }
        .back-link {
            margin: 20px 0;
            font-size: 16px;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        ul, ol {
            line-height: 2;
        }
        li {
            margin: 5px 0;
        }
        /* 信頼度の星 */
        .rating {
            font-size: 1.5em;
            color: #f39c12;
        }
        /* ハイライト */
        strong {
            color: #e74c3c;
        }
        /* 目次のスタイル */
        #目次 + ol {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 20px 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="back-link">
            <a href="reality_and_actions.html">← 予測の現実性と私たちにできることに戻る</a> | 
            <a href="index.html">メインレポートへ</a>
        </div>
        {content}
        <div class="back-link" style="margin-top: 50px; text-align: center;">
            <a href="reality_and_actions.html">← 予測の現実性と私たちにできることに戻る</a> | 
            <a href="index.html">メインレポートへ</a>
        </div>
    </div>
</body>
</html>"""
    
    # MarkdownをHTMLに変換
    md = markdown.Markdown(extensions=['extra', 'toc'])
    html_content = md.convert(md_content)
    
    # HTMLテンプレートに埋め込み
    full_html = html_template.replace("{content}", html_content)
    
    # HTMLファイルを保存
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(full_html)
    
    print(f"HTML file created: {html_file}")

if __name__ == "__main__":
    convert_to_html()