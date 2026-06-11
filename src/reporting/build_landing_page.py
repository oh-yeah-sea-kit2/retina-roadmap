#!/usr/bin/env python3
"""Generate the public landing page from structured sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.reporting.glossary import annotate_first_terms
from src.reporting.message_design import (
    classification_badges,
    definition_block,
    escape_html,
    load_clinical_programs,
)
from src.reporting.site_metadata import load_build_metadata
from src.reporting.timeline_visualization import render_timeline


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


LANDING_PROGRAMS = [
    "SPVN06",
    "NAC Attack",
    "NPI-001",
    "SENTAN-PVS-NP",
    "OCU400",
    "MCO-010",
    "RV-001",
    "Botaretigene sparoparvovec",
    "AGTC-501",
    "DSP-3077",
]


def program_table(kb: dict[str, Any]) -> str:
    """Render patient-facing classification table for the landing page."""
    rows = []
    programs = kb.get("programs", {})
    for program_id in LANDING_PROGRAMS:
        program = programs.get(program_id)
        if not program:
            continue
        design = program.get("message_design", {})
        milestone = design.get("landing_milestone") or program.get("status", "")
        rows.append(f"""
            <tr>
                <td><strong>{escape_html(program_id)}</strong></td>
                <td>{classification_badges(program)}</td>
                <td>{escape_html(milestone)}</td>
                <td>{escape_html(design.get("patient_summary", ""))}</td>
            </tr>""")
    return "\n".join(rows)


def generate_html(site_metadata: dict[str, Any] | None = None) -> str:
    """Build the full landing HTML."""
    kb = load_clinical_programs()
    site_metadata = site_metadata or load_build_metadata()
    site_last_updated = site_metadata.get("site_last_updated", "")
    data_date = site_metadata.get("clinical_trials_snapshot_date", "")

    table_rows = program_table(kb)
    timeline_html = render_timeline(kb)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>網膜色素変性症の治療はいつ？ - RPトリートメントロードマップ</title>
    <meta name="description" content="網膜色素変性症（RP）の治療を、進行を遅らせる治療と視力再建・根治を目指す治療に分けて整理。今すぐできる行動と最新の開発状況をまとめます。">

    <meta property="og:type" content="website">
    <meta property="og:url" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/">
    <meta property="og:title" content="網膜色素変性症の治療はいつ？">
    <meta property="og:description" content="治療を2種類に分け、今すぐできる行動から順に整理したRP治療ロードマップ。">
    <meta property="og:image" content="https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/public/images/CDF.png">

    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:title" content="網膜色素変性症の治療はいつ？">
    <meta property="twitter:description" content="進行を遅らせる治療と視力再建・根治を目指す治療を分けて整理。">

    <link rel="stylesheet" href="css/common.css">
    <script src="js/mobile-nav.js" defer></script>
    <style>
        .hero {{
            padding: 42px 24px;
            background: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            margin-bottom: 24px;
        }}
        .hero h1 {{
            font-size: 2.4rem;
            margin-bottom: 12px;
            border-bottom: none;
            padding-bottom: 0;
        }}
        .hero .lead {{
            max-width: 820px;
            color: var(--text-secondary);
            font-size: 1.15rem;
            margin-bottom: 0;
        }}
        .update-info {{
            color: var(--text-secondary);
            font-size: 0.92rem;
            margin-bottom: 24px;
        }}
        .quick-summary {{
            border-left: 6px solid var(--success-color);
        }}
        .quick-summary h2, .action-first h2, .axis-forecast h2 {{
            margin-top: 0;
        }}
        .axis-definitions {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .axis-definitions div {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            background: #fbfcfd;
        }}
        .axis-definitions dt {{
            font-weight: 700;
            color: var(--secondary-color);
            margin-bottom: 8px;
        }}
        .axis-definitions dd {{
            margin: 0;
            color: var(--text-primary);
        }}
        .action-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin: 18px 0;
        }}
        .action-item {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            background: #ffffff;
        }}
        .action-item strong {{
            display: block;
            margin-bottom: 6px;
        }}
        .axis-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .axis-card {{
            border-radius: 8px;
            padding: 18px;
            border: 1px solid var(--border-color);
            background: #ffffff;
        }}
        .axis-card.a {{
            border-top: 5px solid var(--success-color);
        }}
        .axis-card.mid {{
            border-top: 5px solid var(--warning-color);
        }}
        .axis-card.b {{
            border-top: 5px solid var(--primary-color);
        }}
        .axis-card h3 {{
            margin-top: 0;
            font-size: 1.2rem;
        }}
        .timeline-section h2 {{
            margin-top: 0;
        }}
        .timeline-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px 20px;
            margin: 18px 0;
            color: var(--text-secondary);
            font-size: 1rem;
        }}
        .timeline-legend span {{
            display: inline-flex;
            align-items: center;
            min-height: 44px;
        }}
        .timeline-legend i {{
            display: inline-block;
            width: 18px;
            height: 10px;
            border-radius: 999px;
            margin-right: 8px;
        }}
        .legend-a {{
            background: #2f80c4;
        }}
        .legend-b {{
            background: #d97918;
        }}
        .timeline-scroll {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 10px;
        }}
        .timeline-chart {{
            min-width: 760px;
            padding: 18px 0 8px;
        }}
        .timeline-scale {{
            position: relative;
            height: 30px;
            margin-left: 210px;
            border-bottom: 1px solid var(--border-color);
        }}
        .timeline-tick {{
            position: absolute;
            transform: translateX(-50%);
            color: var(--text-secondary);
            font-size: 1rem;
            white-space: nowrap;
        }}
        .timeline-chart h3 {{
            margin: 18px 0 8px;
            font-size: 1rem;
            color: var(--secondary-color);
        }}
        .timeline-row {{
            display: grid;
            grid-template-columns: 200px minmax(520px, 1fr);
            gap: 10px;
            align-items: center;
            margin: 8px 0;
        }}
        .timeline-label {{
            min-height: 44px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            font-size: 1rem;
        }}
        .timeline-label span {{
            color: var(--text-secondary);
            font-size: 1rem;
            line-height: 1.35;
        }}
        .timeline-track {{
            position: relative;
            height: 44px;
            border-radius: 8px;
            background:
                repeating-linear-gradient(
                    90deg,
                    #f3f6f8 0,
                    #f3f6f8 calc((100% / 14) - 1px),
                    #dfe7ed calc((100% / 14) - 1px),
                    #dfe7ed calc(100% / 14)
                );
            border: 1px solid #dfe7ed;
        }}
        .timeline-bar {{
            position: absolute;
            left: var(--bar-left);
            width: var(--bar-width);
            top: 5px;
            min-height: 34px;
            border-radius: 7px;
            color: #ffffff;
            padding: 5px 9px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: hidden;
            white-space: nowrap;
            box-shadow: 0 2px 6px rgba(0,0,0,0.16);
        }}
        .timeline-bar span {{
            font-weight: 700;
            font-size: 1rem;
            line-height: 1.1;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .timeline-bar small {{
            font-size: 1rem;
            line-height: 1.1;
            opacity: 0.95;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .timeline-a {{
            background: #2f80c4;
        }}
        .timeline-b {{
            background: #d97918;
        }}
        .timeline-mid {{
            background: linear-gradient(90deg, #2f80c4 0%, #d97918 100%);
        }}
        .timeline-note {{
            color: var(--text-secondary);
            font-size: 1rem;
            margin-top: 16px;
        }}
        .program-table td:nth-child(2) {{
            min-width: 210px;
        }}
        .tag {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            margin: 2px 4px 2px 0;
            color: #1f2933;
            background: #eef2f7;
        }}
        .axis-a {{
            background: #dff3e8;
            color: #145a32;
        }}
        .axis-b {{
            background: #e2f0fb;
            color: #1b4f72;
        }}
        .axis-mid {{
            background: #fff0d6;
            color: #7a4a00;
        }}
        .scope-agnostic {{
            background: #e8f4f8;
            color: #1f5f75;
        }}
        .scope-specific, .scope-limited {{
            background: #f3e8ff;
            color: #5b2c6f;
        }}
        .scope-preclinical {{
            background: #f2f2f2;
            color: #555;
        }}
        .paths {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 20px;
            margin: 28px 0;
        }}
        .path-card {{
            padding: 24px;
            background: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }}
        .disclaimer {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px 20px;
            border-radius: 5px;
            margin: 32px 0;
        }}
        @media screen and (max-width: 768px) {{
            .hero {{
                padding: 28px 18px;
            }}
            .hero h1 {{
                font-size: 1.9rem;
            }}
        }}
    </style>
</head>
<body>
    <a href="#main-content" class="skip-link">メインコンテンツへスキップ</a>

    <div class="container">
        <main id="main-content" role="main">
            <section class="hero">
                <h1>網膜色素変性症の治療はいつ？</h1>
                <p class="lead">答えは一つの年ではなく、「進行を遅らせる治療」と「失った視力を取り戻す・根治を目指す治療」で分けて考える必要があります。</p>
            </section>

            <div class="update-info">
                最終更新: {escape_html(site_last_updated)} | データソース: ClinicalTrials.gov, PubMed | データ取得: {escape_html(data_date)} |
                <a href="updates.html">更新履歴を見る</a>
            </div>

            <section class="content-wrapper quick-summary">
                <h2>3分でわかる</h2>
                <p><strong>網膜色素変性症の治療は「2種類」あります。</strong></p>
                {definition_block(kb)}
                <p><strong>だから「いつ治る？」の答えは人によって違います。</strong> 原因遺伝子、残っている視機能、病期によって、現実的な候補が変わります。</p>
            </section>

            <section class="content-wrapper action-first">
                <h2>あなたが今すぐできること</h2>
                <div class="action-list">
                    <div class="action-item">
                        <strong>1. 遺伝子検査で原因を確定</strong>
                        <p>型特異の治療は、原因遺伝子が合うかで対象が決まります。</p>
                    </div>
                    <div class="action-item">
                        <strong>2. 自然経過レジストリに登録</strong>
                        <p>治験の声がかかる側に入るための準備です。</p>
                    </div>
                    <div class="action-item">
                        <strong>3. 国内治験DBを定点チェック</strong>
                        <p><a href="https://jrct.mhlw.go.jp/" target="_blank" rel="noopener noreferrer">jRCT</a> と <a href="https://nanbyo-chiken.nibn.go.jp/" target="_blank" rel="noopener noreferrer">難病治験ウェブ</a> で「網膜色素変性」を定期検索します。</p>
                    </div>
                </div>
                <p>
                    <a class="btn btn-primary" href="japan_action_guide.html">日本で今日から動く手順を見る</a>
                    <a class="btn btn-secondary" href="reality_and_actions.html">全体の行動ガイドを見る</a>
                </p>
            </section>

            <section class="content-wrapper axis-forecast">
                <h2>2軸で見る治療の見通し</h2>
                <div class="axis-grid">
                    <div class="axis-card a">
                        <h3>A: 進行を遅らせる</h3>
                        <p>神経保護・抗酸化など。視力を戻すものではありませんが、残っている視機能を守る現実的な希望です。</p>
                        <p><strong>代表例:</strong> SPVN06、NAC Attack、NPI-001、SENTAN-PVS-NP</p>
                    </div>
                    <div class="axis-card mid">
                        <h3>中間: 機能改善・視覚再建</h3>
                        <p>OCU400や光遺伝学は、進行抑制や視覚再建を狙います。ただし根治や完全な視力回復とは分けて読む必要があります。</p>
                        <p><strong>代表例:</strong> OCU400、MCO-010、RV-001</p>
                    </div>
                    <div class="axis-card b">
                        <h3>B: 取り戻す/根治を目指す</h3>
                        <p>遺伝子補充、細胞移植、編集。10〜20年スパンで、原因遺伝子や病期が合う人に限られることがあります。</p>
                        <p><strong>代表例:</strong> AGTC-501、bota-vec、DSP-3077、prime editing</p>
                    </div>
                </div>
            </section>

            {timeline_html}

            <section class="content-wrapper">
                <h2>主なプログラムの読み方</h2>
                <p>トップでは登録番号や統計の細部より、「何を期待する治療か」「自分が対象になりうるか」を先に見ます。詳細な登録番号と一次ソースは更新履歴と詳細レポートに格納しています。</p>
                <table class="program-table card-layout">
                    <thead>
                        <tr>
                            <th>プログラム</th>
                            <th>分類</th>
                            <th>次の節目</th>
                            <th>患者向けの読み方</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </section>

            <section class="paths" role="navigation" aria-label="情報カテゴリ">
                <div class="path-card">
                    <h2>患者・ご家族の方へ</h2>
                    <p>治療の見通しと、今できる準備をまとめています。</p>
                    <a href="patient_guide.html" class="btn btn-primary">詳しく見る</a>
                </div>
                <div class="path-card">
                    <h2>日本で今動く</h2>
                    <p>遺伝子検査、国内レジストリ、jRCT、難病治験ウェブの使い方。</p>
                    <a href="japan_action_guide.html" class="btn btn-primary">手順を見る</a>
                </div>
                <div class="path-card">
                    <h2>医療従事者の方へ</h2>
                    <p>エビデンスに基づく臨床情報と信頼性チェックリスト。</p>
                    <a href="medical_info.html" class="btn btn-secondary">詳しく見る</a>
                </div>
                <div class="path-card">
                    <h2>詳細データを見る</h2>
                    <p>予測の根拠、登録番号、一次ソース、シミュレーション結果。</p>
                    <a href="report.html" class="btn btn-tertiary">詳しく見る</a>
                </div>
            </section>

            <div class="disclaimer">
                <p><strong>重要:</strong> このサイトの情報は医学的助言ではありません。治療に関する決定は必ず専門医にご相談ください。現在の治療を自己判断で中断しないでください。 <a href="disclaimer.html">詳しい免責事項</a></p>
            </div>

            <section class="content-wrapper">
                <h2>その他の情報</h2>
                <ul>
                    <li><a href="updates.html">更新履歴</a></li>
                    <li><a href="faq.html">よくある質問</a></li>
                    <li><a href="japan_action_guide.html">日本の読者向けアクションガイド</a></li>
                    <li><a href="regional_approval_timeline.html">地域別承認予測</a></li>
                    <li><a href="simulation_methodology.html">シミュレーション方法論</a></li>
                    <li><a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap" target="_blank" rel="noopener noreferrer">ソースコード（GitHub）</a></li>
                </ul>
            </section>
        </main>

        <footer>
            <p>&copy; 2025 網膜色素変性症治療予測プロジェクト |
            <a href="disclaimer.html">免責事項</a> |
            <a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues" target="_blank" rel="noopener noreferrer">フィードバック</a>
            </p>
        </footer>
    </div>

    <nav class="bottom-nav" role="navigation" aria-label="モバイル用ナビゲーション">
        <ul>
            <li><a href="index.html"><span class="bottom-nav-icon">🏠</span><span>ホーム</span></a></li>
            <li><a href="report.html"><span class="bottom-nav-icon">📊</span><span>レポート</span></a></li>
            <li><a href="patient_guide.html"><span class="bottom-nav-icon">👥</span><span>患者向け</span></a></li>
            <li><a href="faq.html"><span class="bottom-nav-icon">❓</span><span>FAQ</span></a></li>
        </ul>
    </nav>

    <script src="js/common.js"></script>
</body>
</html>"""

    return annotate_first_terms(html)


def build_landing_page(site_metadata: dict[str, Any] | None = None) -> Path:
    """Write docs/public/index.html and return the path."""
    output_path = PROJECT_ROOT / "docs" / "public" / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generate_html(site_metadata), encoding="utf-8")
    return output_path


def main() -> None:
    build_landing_page()


if __name__ == "__main__":
    main()
