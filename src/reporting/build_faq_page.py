#!/usr/bin/env python3
"""Generate the FAQ page from docs/content/main/faq.md."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.reporting.glossary import annotate_first_terms
from src.reporting.html_utils import convert_markdown_to_html
from src.reporting.site_metadata import load_build_metadata


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_PATH = PROJECT_ROOT / "docs" / "content" / "main" / "faq.md"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "public" / "faq.html"


def generate_html(site_metadata: dict[str, Any] | None = None) -> str:
    """Build the full FAQ HTML."""
    site_metadata = site_metadata or load_build_metadata()
    site_last_updated = site_metadata.get("site_last_updated", "")
    md_content = SOURCE_PATH.read_text(encoding="utf-8")
    html_content = convert_markdown_to_html(md_content)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>よくある質問 - 網膜色素変性症治療予測</title>
    <meta name="description" content="網膜色素変性症の治療時期、2種類の治療、今すぐできる行動、治験参加、予測の読み方に関するFAQ。">

    <meta property="og:type" content="website">
    <meta property="og:title" content="FAQ - 網膜色素変性症治療予測">
    <meta property="og:description" content="治療を2軸に分け、いつ治るのかを誠実に答えるFAQ。">

    <link rel="stylesheet" href="css/common.css">
    <script src="js/mobile-nav.js" defer></script>
    <style>
        .faq-container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .faq-meta {{
            color: var(--text-secondary);
            font-size: 0.92rem;
            margin-bottom: 20px;
        }}
        details {{
            background: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin: 14px 0;
            overflow: hidden;
        }}
        details[open] {{
            border-color: var(--primary-color);
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        summary {{
            cursor: pointer;
            padding: 18px 52px 18px 20px;
            font-weight: 700;
            color: var(--secondary-color);
            position: relative;
            list-style: none;
        }}
        summary::-webkit-details-marker {{
            display: none;
        }}
        summary::after {{
            content: "+";
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--primary-color);
            font-size: 1.4rem;
            line-height: 1;
        }}
        details[open] summary::after {{
            content: "×";
        }}
        details > div {{
            padding: 0 20px 18px 20px;
        }}
        details p, details ul, details ol {{
            margin-bottom: 12px;
        }}
        h2 {{
            margin-top: 40px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--primary-color);
        }}
        .category-nav {{
            background: var(--bg-light);
            border-radius: var(--radius);
            padding: 18px;
            margin-bottom: 28px;
        }}
        .category-nav ul {{
            margin-bottom: 0;
        }}
        @media screen and (max-width: 768px) {{
            summary {{
                padding-right: 44px;
            }}
        }}
    </style>
</head>
<body>
    <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>

    <nav role="navigation" aria-label="サイト内ナビゲーション">
        <ul>
            <li><a href="index.html">ホーム</a></li>
            <li><a href="patient_guide.html">患者ガイド</a></li>
            <li><a href="medical_info.html">医療従事者向け</a></li>
            <li><a href="report.html">詳細レポート</a></li>
            <li><a href="updates.html">更新履歴</a></li>
            <li><a href="faq.html" aria-current="page">FAQ</a></li>
        </ul>
    </nav>

    <div class="container">
        <main id="main-content" class="content-wrapper faq-container">
            <div class="faq-meta">最終更新: {site_last_updated}</div>
            <div class="category-nav">
                <strong>読む順番:</strong>
                <ul>
                    <li>まず「いつ治るのですか？」で2軸の考え方を確認</li>
                    <li>次に「今、何をすべきですか？」で具体行動を確認</li>
                    <li>最後に詳細レポートで登録番号・一次ソースを確認</li>
                </ul>
            </div>
            {html_content}
        </main>
    </div>

    <nav class="bottom-nav" role="navigation" aria-label="モバイル用ナビゲーション">
        <ul>
            <li><a href="index.html"><span class="bottom-nav-icon">🏠</span><span>ホーム</span></a></li>
            <li><a href="report.html"><span class="bottom-nav-icon">📊</span><span>レポート</span></a></li>
            <li><a href="patient_guide.html"><span class="bottom-nav-icon">👥</span><span>患者向け</span></a></li>
            <li><a href="faq.html"><span class="bottom-nav-icon">❓</span><span>FAQ</span></a></li>
        </ul>
    </nav>

    <footer role="contentinfo">
        <p>このサイトは研究・情報整理目的であり、医学的助言ではありません。</p>
        <p>改善提案は <a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues">GitHub</a> までお寄せください。</p>
    </footer>
</body>
</html>"""

    return annotate_first_terms(html)


def build_faq_page(site_metadata: dict[str, Any] | None = None) -> Path:
    """Write docs/public/faq.html and return the path."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(generate_html(site_metadata), encoding="utf-8")
    return OUTPUT_PATH


def main() -> None:
    build_faq_page()


if __name__ == "__main__":
    main()
