#!/usr/bin/env python3
"""
HTML生成のための共通ユーティリティ関数
"""

import re
import markdown


def auto_link_urls(text):
    """テキスト内のURLを自動的にリンクに変換"""
    # URLパターン（http://またはhttps://で始まる）
    url_pattern = r'(?<!href=")(?<!src=")(https?://[^\s<>"{}|\\^`\[\]]+)'
    
    def replace_url(match):
        url = match.group(0)
        # 既にリンクタグ内にある場合はそのまま返す
        if '<a' in match.string[max(0, match.start()-10):match.start()]:
            return url
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'
    
    return re.sub(url_pattern, replace_url, text)


def make_tables_responsive(html_content):
    """テーブルをレスポンシブ対応にする"""
    # テーブルをラッパーで囲む
    table_pattern = r'<table[^>]*>.*?</table>'
    
    def wrap_table(match):
        table_html = match.group(0)
        return f'<div class="table-wrapper">{table_html}</div>'
    
    # テーブルをラップ
    html_content = re.sub(table_pattern, wrap_table, html_content, flags=re.DOTALL)
    
    return html_content


def get_responsive_table_css():
    """レスポンシブテーブル用のCSSを返す"""
    return """
        /* レスポンシブテーブル */
        .table-wrapper {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin: 20px 0;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            min-width: 600px;
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
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        
        /* スマホ対応 */
        @media screen and (max-width: 768px) {
            .table-wrapper {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            
            table {
                font-size: 14px;
            }
            
            th, td {
                padding: 8px;
            }
            
            /* 横スクロール可能であることを示す */
            .table-wrapper::after {
                content: "← スクロール可能 →";
                display: block;
                text-align: center;
                color: #666;
                font-size: 12px;
                padding: 5px;
            }
        }
        
        /* より小さい画面用の調整 */
        @media screen and (max-width: 480px) {
            table {
                font-size: 12px;
            }
            
            th, td {
                padding: 6px;
            }
        }
    """


def process_html_content(html_content):
    """HTMLコンテンツを処理（URLリンク化、テーブルレスポンシブ化）"""
    # URLを自動リンク化
    html_content = auto_link_urls(html_content)
    
    # テーブルをレスポンシブ対応
    html_content = make_tables_responsive(html_content)
    
    return html_content


def convert_markdown_to_html(md_content, extensions=None):
    """Markdownをより良いHTMLに変換"""
    if extensions is None:
        extensions = ['tables', 'fenced_code', 'nl2br', 'extra', 'attr_list']
    
    md = markdown.Markdown(extensions=extensions)
    html_content = md.convert(md_content)
    
    # 処理を適用
    html_content = process_html_content(html_content)
    
    # .mdリンクを.htmlに変換
    html_content = re.sub(r'\.md(?=["#])', '.html', html_content)
    
    return html_content