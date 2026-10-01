#!/usr/bin/env python3
"""Generate the screen-reader optimized summary page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.reporting.glossary import annotate_first_terms
from src.reporting.html_utils import convert_markdown_to_html, get_responsive_table_css
from src.reporting.site_metadata import load_build_metadata


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_PATH = PROJECT_ROOT / "docs" / "content" / "accessibility" / "accessible_summary.md"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "public" / "accessible_summary.html"


def generate_html(site_metadata: dict[str, Any] | None = None) -> str:
    """Build the full accessible summary HTML."""
    site_metadata = site_metadata or load_build_metadata()
    md_content = SOURCE_PATH.read_text(encoding="utf-8")
    html_content = convert_markdown_to_html(md_content)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>音声読み上げ対応版 - 網膜色素変性症治療ロードマップ</title>
    <meta name="description" content="網膜色素変性症治療ロードマップのスクリーンリーダー向け要約。2軸の治療分類、日本で今日からできる行動、主要プログラムを読みやすい順番で整理。">
    <link rel="stylesheet" href="css/common.css">
    <script src="js/mobile-nav.js" defer></script>
    <style>
        .accessible-content {{
            max-width: 920px;
            margin: 0 auto;
            font-size: 1.05rem;
            line-height: 1.9;
        }}
        .accessible-content h1 {{
            margin-top: 0;
        }}
        .accessible-content h2 {{
            margin-top: 42px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--primary-color);
        }}
        .accessible-content h3 {{
            margin-top: 28px;
        }}
        .accessible-content li {{
            margin-bottom: 0.35rem;
        }}
        .reader-note {{
            background: #f7fbf9;
            border-left: 6px solid var(--success-color);
            padding: 16px 18px;
            margin: 20px 0 28px;
        }}
{get_responsive_table_css()}
    </style>
</head>
<body>
    <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>

    <nav role="navigation" aria-label="サイト内ナビゲーション">
        <ul>
            <li><a href="index.html">ホーム</a></li>
            <li><a href="japan_action_guide.html">日本向け行動</a></li>
            <li><a href="faq.html">FAQ</a></li>
            <li><a href="report.html">詳細レポート</a></li>
            <li><a href="accessible_summary.html" aria-current="page">音声読み上げ対応版</a></li>
        </ul>
    </nav>

    <div class="container">
        <main id="main-content" class="accessible-content" role="main">
            <div class="reader-note">
                <strong>読み上げ用の構成:</strong> このページは、トップページと日本アクションガイドの要点を、見出し移動しやすい順番に並べ直しています。
            </div>
            {html_content}
        </main>
    </div>

    <nav class="bottom-nav" role="navigation" aria-label="モバイル用ナビゲーション">
        <ul>
            <li><a href="index.html"><span class="bottom-nav-icon">ホーム</span></a></li>
            <li><a href="japan_action_guide.html"><span class="bottom-nav-icon">日本向け</span></a></li>
            <li><a href="report.html"><span class="bottom-nav-icon">レポート</span></a></li>
            <li><a href="faq.html"><span class="bottom-nav-icon">FAQ</span></a></li>
        </ul>
    </nav>

    <footer role="contentinfo">
        <p>このサイトは研究・情報整理目的であり、医学的助言ではありません。</p>
        <p>改善提案は <a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues">GitHub</a> までお寄せください。</p>
    </footer>
</body>
</html>"""

    annotated = annotate_first_terms(html)
    return "\n".join(line.rstrip() for line in annotated.splitlines()) + "\n"


def build_accessible_summary(site_metadata: dict[str, Any] | None = None) -> Path:
    """Write docs/public/accessible_summary.html and return the path."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(generate_html(site_metadata), encoding="utf-8")
    return OUTPUT_PATH


def main() -> None:
    build_accessible_summary()


if __name__ == "__main__":
    main()
