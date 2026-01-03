#!/usr/bin/env python3
"""
MarkdownファイルをHTMLに変換（ナビゲーション付き）
"""

import markdown
from pathlib import Path
from html_utils import convert_markdown_to_html, get_responsive_table_css

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
        /* フォーカス時の視認性向上 */
        a:focus, button:focus, input:focus, select:focus, textarea:focus {{
            outline: 3px solid #ff6600;
            outline-offset: 2px;
        }}
        /* スキップリンク */
        .skip-link {{
            position: absolute;
            left: -9999px;
            top: 0;
            z-index: 999;
        }}
        .skip-link:focus {{
            left: 0;
            background: #000;
            color: #fff;
            padding: 10px;
            text-decoration: none;
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
        {get_responsive_table_css()}
    </style>
</head>
<body>
    <!-- スキップリンク -->
    <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>
    
    <div class="container">
        <!-- ナビゲーション -->
        <nav role="navigation" aria-label="サイト内ナビゲーション">
            <h3>関連ページ</h3>
            <ul>
                <li>🏠 <a href="index.html">トップページ</a></li>
                <li>📊 <a href="report.html">詳細レポート</a> - シミュレーション結果</li>
                <li>🎯 <a href="reality_and_actions.html">現実的なアクションガイド</a> - 今すぐできる5つの行動</li>
                <li>🔊 <a href="accessible_summary.html">音声読み上げ対応版</a> - スクリーンリーダー最適化</li>
                <li>📈 <a href="simulation_methodology.html">シミュレーション方法論</a> - 計算の詳細</li>
                <li>👨‍⚕️ <a href="medical_info.html">医療従事者向け情報</a></li>
                <li>👥 <a href="patient_guide.html">患者・家族向けガイド</a></li>
            </ul>
        </nav>
        
        <main id="main-content" role="main">
            <!-- Content will be inserted here -->
        </main>
    </div>
    
    <footer role="contentinfo" style="margin-top: 50px; padding: 20px; background: #f0f0f0; text-align: center;">
        <p>アクセシビリティについて：このサイトは網膜色素変性症の方々にも利用しやすいよう配慮して作成されています。</p>
        <p>改善提案は <a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues">GitHub</a> までお寄せください。</p>
    </footer>
</body>
</html>"""
    
    # Markdownを変換（HTML処理も含む）
    html_content = convert_markdown_to_html(md_content)
    
    # HTMLテンプレートに挿入
    final_html = html_template.replace("<!-- Content will be inserted here -->", html_content)
    
    # 見出しにaria-labelを追加（必要に応じて）
    final_html = final_html.replace('<h1>', '<h1 role="heading" aria-level="1">')
    final_html = final_html.replace('<h2>', '<h2 role="heading" aria-level="2">')
    final_html = final_html.replace('<h3>', '<h3 role="heading" aria-level="3">')
    
    # 出力ファイル名を生成
    output_file = md_file.with_suffix('.html')
    
    # HTMLファイルを保存
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"Converted: {md_file} -> {output_file}")

def main():
    """メイン処理"""
    docs_dir = Path("docs")
    
    # 変換するファイルのリスト（削除されたファイルは除外）
    files_to_convert = [
        ("simulation_methodology.md", "シミュレーション方法論"),
        ("regional_approval_timeline.md", "地域別承認予測タイムライン")
    ]
    
    for filename, title in files_to_convert:
        md_file = docs_dir / filename
        if md_file.exists():
            convert_with_nav(md_file, title)
        else:
            print(f"File not found: {md_file}")

if __name__ == "__main__":
    main()