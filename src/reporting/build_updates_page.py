#!/usr/bin/env python3
"""
更新履歴ページを生成する。
clinical_programs.jsonの各プログラムのrecent_updatesと
last_check.jsonの情報から、時系列の更新履歴HTMLを生成。
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def load_data():
    """知識ベースのデータを読み込む"""
    kb_path = Path("data/knowledge_base/clinical_programs.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)

    last_check_path = Path("data/knowledge_base/last_check.json")
    with open(last_check_path, "r", encoding="utf-8") as f:
        last_check = json.load(f)

    return kb, last_check


def collect_updates_by_date(kb):
    """各プログラムのrecent_updatesを日付ごとにグループ化"""
    updates_by_date = defaultdict(list)

    for program_id, program in kb.get("programs", {}).items():
        company = program.get("company", "")
        phase = program.get("current_phase", "")
        for update in program.get("recent_updates", []):
            date = update.get("date", "")
            event = update.get("event", "")
            source = update.get("source", "")
            updates_by_date[date].append({
                "program_id": program_id,
                "company": company,
                "phase": phase,
                "event": event,
                "source": source,
            })

    return updates_by_date


def classify_importance(event_text):
    """イベントの重要度を判定"""
    high_keywords = ["FDA", "承認", "approval", "BLA", "NDA", "Orphan Drug",
                     "Breakthrough", "RMAT", "先駆け", "Sakigake", "Phase 3",
                     "登録完了", "enrollment completed", "primary endpoint"]
    medium_keywords = ["Phase 2", "試験開始", "trial start", "初患者",
                       "first patient", "データ", "data", "論文", "paper",
                       "特許", "patent", "指定", "designation"]

    text_lower = event_text.lower()
    for kw in high_keywords:
        if kw.lower() in text_lower:
            return "high"
    for kw in medium_keywords:
        if kw.lower() in text_lower:
            return "medium"
    return "low"


def escape_html(text):
    """HTMLエスケープ"""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def generate_html(kb, last_check):
    """更新履歴HTMLを生成"""
    updates_by_date = collect_updates_by_date(kb)
    sorted_dates = sorted(updates_by_date.keys(), reverse=True)

    last_updated = kb.get("last_updated", "")
    last_check_date = last_check.get("last_check_date", "")[:10]
    check_type = last_check.get("check_type", "")

    # 更新一覧のHTML生成
    timeline_html = ""
    for date in sorted_dates:
        items = updates_by_date[date]
        # 日付ヘッダー
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            date_display = dt.strftime("%Y年%m月%d日")
        except ValueError:
            date_display = date

        cards_html = ""
        for item in items:
            importance = classify_importance(item["event"])
            if importance == "high":
                badge = '<span class="badge badge-high">重要</span>'
            elif importance == "medium":
                badge = '<span class="badge badge-medium">更新</span>'
            else:
                badge = '<span class="badge badge-low">情報</span>'

            event_escaped = escape_html(item["event"])
            source_escaped = escape_html(item["source"])

            cards_html += f"""
                <div class="update-card importance-{importance}">
                    <div class="update-card-header">
                        {badge}
                        <strong>{escape_html(item["program_id"])}</strong>
                        <span class="company">({escape_html(item["company"])})</span>
                        <span class="phase-tag">{escape_html(item["phase"])}</span>
                    </div>
                    <div class="update-card-body">
                        <p>{event_escaped}</p>
                    </div>
                    <div class="update-card-footer">
                        <span class="source">出典: {source_escaped}</span>
                    </div>
                </div>"""

        timeline_html += f"""
            <section class="date-section">
                <h3 class="date-header">{date_display}</h3>
                <div class="update-cards">
                    {cards_html}
                </div>
            </section>"""

    # 現在のプログラム一覧テーブル
    programs_table_rows = ""
    for pid, prog in sorted(kb.get("programs", {}).items(),
                            key=lambda x: x[1].get("current_phase", ""),
                            reverse=True):
        status = prog.get("status", "")
        phase = prog.get("current_phase", "")
        company = prog.get("company", "")
        updates = prog.get("recent_updates", [])
        last_update_date = updates[0]["date"] if updates else "-"

        programs_table_rows += f"""
                    <tr>
                        <td><strong>{escape_html(pid)}</strong></td>
                        <td>{escape_html(company)}</td>
                        <td>{escape_html(phase)}</td>
                        <td>{escape_html(status)}</td>
                        <td>{escape_html(last_update_date)}</td>
                    </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>更新履歴 - RPトリートメントロードマップ</title>
    <meta name="description" content="網膜色素変性症（RP）治療法の最新情報更新履歴。各プログラムの進捗をタイムラインで確認。">
    <link rel="stylesheet" href="css/common.css">
    <style>
        .update-meta {{
            text-align: center;
            color: var(--text-secondary);
            margin-bottom: 30px;
            font-size: 0.9rem;
        }}
        .update-meta strong {{
            color: var(--text-primary);
        }}

        /* フィルタ */
        .filter-bar {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 30px;
            padding: 15px;
            background: var(--bg-light);
            border-radius: var(--radius);
        }}
        .filter-bar label {{
            font-weight: bold;
            margin-right: 5px;
        }}
        .filter-bar select {{
            padding: 6px 12px;
            border: 1px solid var(--border-color);
            border-radius: 5px;
            font-size: 0.9rem;
        }}

        /* タイムライン */
        .date-section {{
            margin-bottom: 40px;
        }}
        .date-header {{
            font-size: 1.3rem;
            color: var(--secondary-color);
            border-left: 4px solid var(--primary-color);
            padding-left: 12px;
            margin-bottom: 15px;
        }}
        .update-cards {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        /* カード */
        .update-card {{
            background: white;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            border-left: 4px solid var(--border-color);
            transition: var(--transition);
        }}
        .update-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}
        .update-card.importance-high {{
            border-left-color: var(--accent-color);
        }}
        .update-card.importance-medium {{
            border-left-color: var(--primary-color);
        }}
        .update-card.importance-low {{
            border-left-color: var(--border-color);
        }}

        .update-card-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 8px;
        }}
        .update-card-header strong {{
            font-size: 1.05rem;
        }}
        .company {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .phase-tag {{
            background: var(--bg-light);
            color: var(--primary-color);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }}

        .badge {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: bold;
            color: white;
        }}
        .badge-high {{
            background: var(--accent-color);
        }}
        .badge-medium {{
            background: var(--primary-color);
        }}
        .badge-low {{
            background: var(--text-light);
        }}

        .update-card-body p {{
            margin: 0;
            line-height: 1.7;
            color: var(--text-primary);
        }}
        .update-card-footer {{
            margin-top: 8px;
        }}
        .source {{
            font-size: 0.8rem;
            color: var(--text-light);
        }}

        /* プログラム一覧テーブル */
        .programs-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .programs-table th, .programs-table td {{
            border: 1px solid var(--border-color);
            padding: 10px 12px;
            text-align: left;
        }}
        .programs-table th {{
            background: var(--primary-color);
            color: white;
        }}
        .programs-table tr:nth-child(even) {{
            background: #f9f9f9;
        }}

        /* スマホ対応 */
        @media screen and (max-width: 768px) {{
            .filter-bar {{
                flex-direction: column;
            }}
            .update-card-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .programs-table {{
                display: block;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                font-size: 0.85rem;
            }}
            .programs-table th, .programs-table td {{
                padding: 8px;
                min-width: 100px;
            }}
            .programs-table tbody tr td:first-child,
            .programs-table thead tr th:first-child {{
                position: sticky;
                left: 0;
                background-color: white;
                z-index: 1;
                border-right: 2px solid var(--primary-color);
            }}
            .programs-table thead tr th:first-child {{
                background-color: var(--primary-color);
            }}
            .programs-table tbody tr:nth-child(even) td:first-child {{
                background-color: #f9f9f9;
            }}
        }}
    </style>
</head>
<body>
    <a href="#main" class="skip-link">メインコンテンツへスキップ</a>

    <div class="container">
        <nav aria-label="メインナビゲーション">
            <a href="index.html">トップ</a> |
            <a href="patient_guide.html">患者向け</a> |
            <a href="medical_info.html">医療従事者向け</a> |
            <a href="detailed_analysis.html">詳細分析</a> |
            <a href="report.html">レポート</a> |
            <strong>更新履歴</strong>
        </nav>

        <main id="main">
            <h1>更新履歴</h1>

            <div class="update-meta">
                最終更新: <strong>{last_updated}</strong> |
                最終チェック: <strong>{last_check_date}</strong> |
                チェック方法: {escape_html(check_type)}
            </div>

            <section class="content-wrapper">
                <h2>現在のプログラム一覧</h2>
                <table class="programs-table">
                    <thead>
                        <tr>
                            <th>プログラム</th>
                            <th>企業</th>
                            <th>Phase</th>
                            <th>ステータス</th>
                            <th>最終更新</th>
                        </tr>
                    </thead>
                    <tbody>
                        {programs_table_rows}
                    </tbody>
                </table>
            </section>

            <section class="content-wrapper">
                <h2>更新タイムライン</h2>

                <div class="filter-bar">
                    <div>
                        <label for="filter-importance">重要度:</label>
                        <select id="filter-importance" onchange="filterUpdates()">
                            <option value="all">すべて</option>
                            <option value="high">重要のみ</option>
                            <option value="medium">更新以上</option>
                        </select>
                    </div>
                    <div>
                        <label for="filter-program">プログラム:</label>
                        <select id="filter-program" onchange="filterUpdates()">
                            <option value="all">すべて</option>
                        </select>
                    </div>
                </div>

                <div id="timeline">
                    {timeline_html}
                </div>
            </section>
        </main>

        <footer>
            <p>&copy; 2025 網膜色素変性症治療予測プロジェクト |
            <a href="disclaimer.html">免責事項</a> |
            <a href="https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues" target="_blank" rel="noopener noreferrer">フィードバック</a>
            </p>
        </footer>
    </div>

    <script src="js/common.js"></script>
    <script>
        // プログラムフィルタの選択肢を動的生成
        (function() {{
            const cards = document.querySelectorAll('.update-card');
            const programs = new Set();
            cards.forEach(card => {{
                const name = card.querySelector('.update-card-header strong');
                if (name) programs.add(name.textContent);
            }});
            const sel = document.getElementById('filter-program');
            Array.from(programs).sort().forEach(p => {{
                const opt = document.createElement('option');
                opt.value = p;
                opt.textContent = p;
                sel.appendChild(opt);
            }});
        }})();

        function filterUpdates() {{
            const importance = document.getElementById('filter-importance').value;
            const program = document.getElementById('filter-program').value;
            const cards = document.querySelectorAll('.update-card');
            const sections = document.querySelectorAll('.date-section');

            cards.forEach(card => {{
                let show = true;
                if (importance === 'high' && !card.classList.contains('importance-high')) show = false;
                if (importance === 'medium' && card.classList.contains('importance-low')) show = false;
                if (program !== 'all') {{
                    const name = card.querySelector('.update-card-header strong');
                    if (name && name.textContent !== program) show = false;
                }}
                card.style.display = show ? '' : 'none';
            }});

            // 表示カードがない日付セクションを非表示
            sections.forEach(section => {{
                const visibleCards = section.querySelectorAll('.update-card:not([style*="display: none"])');
                section.style.display = visibleCards.length > 0 ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>"""

    return html


def main():
    logging.basicConfig(level=logging.INFO)

    kb, last_check = load_data()
    html = generate_html(kb, last_check)

    output_path = Path("docs/public/updates.html")
    output_path.write_text(html, encoding="utf-8")
    logger.info(f"Updates page saved to: {output_path}")


if __name__ == "__main__":
    main()
