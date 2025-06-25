#!/usr/bin/env python3
"""
reality_and_actions.mdをHTMLに変換
"""

import markdown
from pathlib import Path


def convert_action_guide():
    """アクションガイドをHTMLに変換"""
    
    # Markdownファイルを読み込む
    md_file = Path("docs/reality_and_actions.md")
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # HTMLテンプレート
    html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>予測の現実性と私たちにできること - RP治療開発</title>
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
            border-bottom: 3px solid #e74c3c;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 40px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 30px;
        }
        .action-item {
            background-color: #e8f6f3;
            border-left: 5px solid #16a085;
            padding: 15px;
            margin: 20px 0;
        }
        strong {
            color: #e74c3c;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .back-link {
            margin: 20px 0;
            font-size: 16px;
        }
        ul, ol {
            line-height: 2;
            margin: 15px 0;
            padding-left: 30px;
        }
        li {
            margin: 8px 0;
        }
        /* 番号付きリストの改善 */
        ol li {
            margin-bottom: 10px;
        }
        /* ネストされたリスト */
        li ul, li ol {
            margin-top: 10px;
            margin-bottom: 10px;
        }
        /* ステップごとの強調表示 */
        p strong:first-child {
            display: inline-block;
            margin-top: 20px;
            font-size: 1.1em;
        }
        /* 絵文字を少し大きく */
        h3 {
            font-size: 1.3em;
        }
        /* ハイライト */
        .highlight {
            background-color: #fff3cd;
            padding: 2px 5px;
            border-radius: 3px;
        }
        /* タイムラインセクション */
        .timeline {
            background-color: #f0f8ff;
            border: 1px solid #b0d4ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        /* details要素のスタイル */
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
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="back-link">
            <a href="index.html">← メインレポートに戻る</a>
        </div>
        {content}
        <div class="back-link" style="margin-top: 50px; text-align: center;">
            <a href="index.html">← メインレポートに戻る</a> | 
            <a href="bottlenecks.md">開発ボトルネック分析 →</a>
        </div>
    </div>
</body>
</html>"""
    
    # Markdownを変換（改行を適切に処理する拡張機能を追加）
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br', 'extra'])
    html_content = md.convert(md_content)
    
    # リストの不適切な処理を修正
    # 番号付きリストが分割されている場合の修正
    import re
    # <ol>タグ内の不要な<p>タグを削除
    html_content = re.sub(r'</li>\s*</ol>\s*<ol>\s*<li>', '</li>\n<li>', html_content)
    # コードブロック内の不要な<br>を<pre>に変換
    html_content = re.sub(r'<code>([^<]+)<br />([^<]+)</code>', r'<pre><code>\1\n\2</code></pre>', html_content, flags=re.DOTALL)
    
    # アクション項目にスタイルを適用
    html_content = html_content.replace('<h3>1. 🧬', '<h3 class="action-item">1. 🧬')
    html_content = html_content.replace('<h3>2. 📊', '<h3 class="action-item">2. 📊')
    html_content = html_content.replace('<h3>3. 💰', '<h3 class="action-item">3. 💰')
    html_content = html_content.replace('<h3>4. 🏛️', '<h3 class="action-item">4. 🏛️')
    html_content = html_content.replace('<h3>5. 🔬', '<h3 class="action-item">5. 🔬')
    
    # タイムラインセクションにスタイルを適用
    html_content = html_content.replace('<h3>ベストケース', '<div class="timeline"><h3>ベストケース')
    html_content = html_content.replace('<h3>現実的ケース', '</div><div class="timeline"><h3>現実的ケース')
    html_content = html_content.replace('<h3>最悪ケース', '</div><div class="timeline"><h3>最悪ケース')
    html_content = html_content.replace('<h2>まとめ', '</div><h2>まとめ')
    
    # HTMLテンプレートに挿入
    final_html = html_template.replace("{content}", html_content)
    
    # ファイルに保存
    html_file = Path("docs/reality_and_actions.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"HTML file created: {html_file}")


if __name__ == "__main__":
    convert_action_guide()