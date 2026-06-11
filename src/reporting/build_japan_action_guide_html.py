#!/usr/bin/env python3
"""Generate the Japan action guide from docs/content/regional/japan_action_guide.md."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.reporting.glossary import annotate_first_terms
from src.reporting.html_utils import convert_markdown_to_html, get_responsive_table_css
from src.reporting.site_metadata import load_build_metadata


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_PATH = PROJECT_ROOT / "docs" / "content" / "regional" / "japan_action_guide.md"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "public" / "japan_action_guide.html"


def generate_html(site_metadata: dict[str, Any] | None = None) -> str:
    """Build the full Japan action guide HTML."""
    site_metadata = site_metadata or load_build_metadata()
    site_last_updated = site_metadata.get("site_last_updated", "")
    data_date = site_metadata.get("clinical_trials_snapshot_date", "")
    md_content = SOURCE_PATH.read_text(encoding="utf-8")
    html_content = convert_markdown_to_html(md_content)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日本の読者向けアクションガイド - 網膜色素変性症治療予測</title>
    <meta name="description" content="網膜色素変性症の患者・家族が日本で今日からできる行動。遺伝子検査、自然経過レジストリ、jRCT、難病治験ウェブ、JRPSを公式ソース付きで整理。">

    <meta property="og:type" content="article">
    <meta property="og:title" content="日本の読者向けアクションガイド">
    <meta property="og:description" content="遺伝子検査、自然経過レジストリ、国内治験検索、患者会につながるための日本向け手順。">

    <link rel="stylesheet" href="css/common.css">
    <script src="js/mobile-nav.js" defer></script>
    <style>
        .guide-hero {{
            background: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 30px 24px;
            margin-bottom: 22px;
        }}
        .guide-hero h1 {{
            margin-top: 0;
            border-bottom: none;
            padding-bottom: 0;
        }}
        .guide-meta {{
            color: var(--text-secondary);
            font-size: 0.92rem;
            margin-bottom: 24px;
        }}
        .guide-content {{
            max-width: 980px;
            margin: 0 auto;
        }}
        .guide-content h2 {{
            margin-top: 42px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--primary-color);
        }}
        .guide-content h3 {{
            margin-top: 28px;
            color: var(--secondary-color);
        }}
        .guide-content blockquote {{
            border-left: 5px solid var(--primary-color);
            background: var(--bg-light);
            margin: 18px 0;
            padding: 14px 18px;
        }}
        .guide-callout {{
            border-left: 6px solid var(--success-color);
            background: #f7fbf9;
            padding: 16px 18px;
            margin: 20px 0;
        }}
        .guide-content table td:first-child {{
            font-weight: 700;
        }}
        .source-note {{
            color: var(--text-secondary);
            font-size: 0.92rem;
        }}
{get_responsive_table_css()}
    </style>
</head>
<body>
    <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>

    <nav role="navigation" aria-label="サイト内ナビゲーション">
        <ul>
            <li><a href="index.html">ホーム</a></li>
            <li><a href="japan_action_guide.html" aria-current="page">日本向け行動</a></li>
            <li><a href="reality_and_actions.html">行動ガイド</a></li>
            <li><a href="regional_approval_timeline.html">地域別承認予測</a></li>
            <li><a href="faq.html">FAQ</a></li>
            <li><a href="updates.html">更新履歴</a></li>
        </ul>
    </nav>

    <div class="container">
        <main id="main-content" class="guide-content">
            <section class="guide-hero">
                <h1>日本の読者向けアクションガイド</h1>
                <p>遺伝子検査、自然経過レジストリ、国内治験検索、患者会につながる手順を、日本の公式窓口に絞って整理します。</p>
            </section>
            <div class="guide-meta">最終更新: {site_last_updated} | データ取得: {data_date}</div>
            <div class="guide-callout">
                <strong>最初にやること:</strong> かかりつけ眼科に紹介状と検査資料を相談し、jRCTと難病治験ウェブを月1回確認してください。
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

    return annotate_first_terms(html)


def build_japan_action_guide(site_metadata: dict[str, Any] | None = None) -> Path:
    """Write docs/public/japan_action_guide.html and return the path."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(generate_html(site_metadata), encoding="utf-8")
    return OUTPUT_PATH


def main() -> None:
    build_japan_action_guide()


if __name__ == "__main__":
    main()
