#!/usr/bin/env python3
"""
reality_and_actions.mdをHTMLに変換
"""

import markdown
from pathlib import Path
from src.reporting.html_utils import convert_markdown_to_html, get_responsive_table_css


def convert_action_guide():
    """アクションガイドをHTMLに変換"""
    
    # Markdownファイルを読み込む
    md_file = Path("docs/content/main/reality_and_actions.md")
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # HTMLテンプレート
    html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>予測の現実性と私たちにできること - RP治療開発</title>
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/reality_and_actions.html">
    <meta property="og:title" content="予測の現実性と私たちにできること - 網膜色素変性症治療開発">
    <meta property="og:description" content="網膜色素変性症の治療法開発を加速するために今すぐできる5つのアクション。遺伝子検査、患者レジストリ登録、研究支援など具体的な行動指針を提供。">
    <meta property="og:image" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/figs/waterfall.png">
    <meta property="og:locale" content="ja_JP">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/reality_and_actions.html">
    <meta property="twitter:title" content="予測の現実性と私たちにできること - 網膜色素変性症治療開発">
    <meta property="twitter:description" content="網膜色素変性症の治療法開発を加速するために今すぐできる5つのアクション。遺伝子検査、患者レジストリ登録、研究支援など具体的な行動指針を提供。">
    <meta property="twitter:image" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/figs/waterfall.png">
    
    <!-- Additional Meta Tags -->
    <meta name="description" content="網膜色素変性症の治療法開発を加速するために今すぐできる5つのアクション。遺伝子検査、患者レジストリ登録、研究支援など具体的な行動指針を提供。">
    <meta name="keywords" content="網膜色素変性症,RP,遺伝子検査,患者レジストリ,JRPS,臨床試験参加,行動指針">
    <meta name="author" content="網膜色素変性症治療開発予測プロジェクト">
    <!-- ナビゲーション -->
    
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
        /* フォーカス時の視認性向上 */
        a:focus, button:focus, input:focus, select:focus, textarea:focus {
            outline: 3px solid #ff6600;
            outline-offset: 2px;
        }
        /* スキップリンク */
        .skip-link {
            position: absolute;
            left: -9999px;
            top: 0;
            z-index: 999;
        }
        .skip-link:focus {
            left: 0;
            background: #000;
            color: #fff;
            padding: 10px;
            text-decoration: none;
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
        {get_responsive_table_css()}
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
    <!-- スキップリンク -->
    <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>
    
    <div class="container">
        <!-- ナビゲーション -->
        <nav role="navigation" aria-label="サイト内ナビゲーション" style="background: #e8f4f8; padding: 15px; margin-bottom: 20px; border-radius: 5px;">
            <h3 style="font-size: 1.2em; margin: 0 0 10px 0;">関連ページ</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="margin: 5px 0;">🏠 <a href="index.html">トップページ</a></li>
                <li style="margin: 5px 0;">📊 <a href="report.html">詳細レポート</a> - シミュレーション結果</li>
                <li style="margin: 5px 0;">🎯 <a href="reality_and_actions.html">現実的なアクションガイド（このページ）</a></li>
                <li style="margin: 5px 0;">🇯🇵 <a href="japan_action_guide.html">日本の読者向けアクションガイド</a> - 遺伝子検査・国内レジストリ・jRCTの手順</li>
                <li style="margin: 5px 0;">🔊 <a href="accessible_summary.html">音声読み上げ対応版</a> - スクリーンリーダー最適化</li>
                <li style="margin: 5px 0;">📈 <a href="simulation_methodology.html">シミュレーション方法論</a></li>
                <li style="margin: 5px 0;">👨‍⚕️ <a href="medical_info.html">医療従事者向け情報</a></li>
                <li style="margin: 5px 0;">👥 <a href="patient_guide.html">患者・家族向けガイド</a></li>
            </ul>
        </nav>
        
        <main id="main-content" role="main">
            <div class="back-link">
                <a href="index.html">← メインレポートに戻る</a>
            </div>
            {content}
        <div class="back-link" style="margin-top: 50px; text-align: center;">
            <a href="index.html">← トップページに戻る</a> |
            <a href="japan_action_guide.html">日本向け手順を見る</a> |
            <a href="patient_guide.html">患者・家族向けガイド →</a>
        </div>
        </main>
    </div>
    
    <footer role="contentinfo" style="margin-top: 50px; padding: 20px; background: #f0f0f0; text-align: center;">
        <p>アクセシビリティについて：このサイトは網膜色素変性症の方々にも利用しやすいよう配慮して作成されています。</p>
        <p>改善提案は <a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues">GitHub</a> までお寄せください。</p>
    </footer>
</body>
</html>"""
    
    # Markdownを変換（URLリンク化とレスポンシブテーブル対応を含む）
    html_content = convert_markdown_to_html(md_content)
    
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
    html_file = Path("docs/public/reality_and_actions.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"HTML file created: {html_file}")


if __name__ == "__main__":
    convert_action_guide()
