#!/usr/bin/env python3
"""
HTML生成のための共通ユーティリティ関数
"""

import re
import markdown
from src.reporting.site_metadata import render_metadata_placeholders


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
    """テーブルをレスポンシブ対応にする（カード型レイアウト用のdata-label追加）"""
    from bs4 import BeautifulSoup
    
    # BeautifulSoupでHTMLをパース
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # すべてのテーブルを処理
    for table in soup.find_all('table'):
        # カード型レイアウトクラスを追加
        if 'class' in table.attrs:
            table['class'].append('card-layout')
        else:
            table['class'] = ['card-layout']
        
        # ヘッダー行を取得
        headers = []
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        # 各データ行にdata-label属性を追加
        tbody = table.find('tbody')
        if tbody and headers:
            for row in tbody.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                for i, cell in enumerate(cells):
                    if i < len(headers) and i > 0:  # 最初のセルはラベル不要
                        cell['data-label'] = headers[i]
    
    return str(soup)


def get_responsive_table_css():
    """レスポンシブテーブル用のCSSを返す"""
    return """
        /* テーブルスタイル */
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
            font-weight: bold;
        }
        
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        
        /* スマホ対応 - 横スクロール */
        @media screen and (max-width: 768px) {
            /* テーブルコンテナ */
            table {
                display: block;
                overflow-x: auto;
                white-space: nowrap;
                -webkit-overflow-scrolling: touch;
                font-size: 14px;
            }
            
            th, td {
                padding: 8px;
                min-width: 100px;
            }
            
            /* 最初の列を固定 */
            tbody tr td:first-child,
            thead tr th:first-child {
                position: sticky;
                left: 0;
                background-color: white;
                z-index: 1;
                border-right: 2px solid #3498db;
            }
            
            thead tr th:first-child {
                background-color: #3498db;
            }
            
            tbody tr:nth-child(even) td:first-child {
                background-color: #f2f2f2;
            }
        }
        
        /* より小さい画面用の調整 */
        @media screen and (max-width: 480px) {
            table {
                font-size: 12px;
            }
            
            th, td {
                padding: 6px;
                min-width: 80px;
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

    md_content = render_metadata_placeholders(md_content)
    
    md = markdown.Markdown(extensions=extensions)
    html_content = md.convert(md_content)
    
    # 処理を適用
    html_content = process_html_content(html_content)
    
    # .mdリンクを.htmlに変換
    html_content = re.sub(r'\.md(?=["#])', '.html', html_content)
    
    return html_content
