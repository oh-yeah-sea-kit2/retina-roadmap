#!/usr/bin/env python3
"""
GitHub Actions用の月次更新チェックスクリプト
DuckDuckGoを使用してWeb検索を行い、知識ベースとの差分を検出する
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, ".")

from scripts.utils.data_comparison import (
    load_knowledge_base,
    extract_program_info_from_text,
    compare_clinical_programs,
    format_comparison_report,
    calculate_importance_score,
    save_check_results,
)


def search_program_updates(program_id: str, program_name: str, company: str) -> str:
    """DuckDuckGoで治療プログラムの最新情報を検索"""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print("警告: duckduckgo-search がインストールされていません")
        print("pip install duckduckgo-search でインストールしてください")
        return ""

    queries = [
        f"{program_id} {company} retinitis pigmentosa 2026 latest update",
        f"{program_name} {company} FDA approval clinical trial 2026",
    ]

    results_text = []
    with DDGS() as ddgs:
        for query in queries:
            try:
                results = list(ddgs.text(query, max_results=5))
                for r in results:
                    results_text.append(f"{r.get('title', '')} - {r.get('body', '')}")
                time.sleep(1)  # レート制限対策
            except Exception as e:
                print(f"  検索エラー ({query}): {e}")
                continue

    return "\n".join(results_text)


def main():
    """月次更新チェック（Web検索付き）"""

    print("=" * 60)
    print("🔍 月次更新チェック（Web検索付き）")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 知識ベースの読み込み
    kb = load_knowledge_base()
    programs = kb.get("programs", {})

    if not programs:
        print("エラー: 知識ベースにプログラムが見つかりません")
        return

    print(f"\n登録プログラム数: {len(programs)}件")

    # 主要プログラムの検索
    key_programs = {
        "MCO-010": {"name": "MCO-010", "company": "Nanoscope Therapeutics"},
        "OCU400": {"name": "OCU400", "company": "Ocugen"},
        "VP-001": {"name": "VP-001", "company": "PYC Therapeutics"},
        "AGTC-501": {"name": "laru-zova AGTC-501", "company": "Beacon Therapeutics"},
        "OpCT-001": {"name": "OpCT-001", "company": "BlueRock Therapeutics"},
        "NPI-001": {"name": "NPI-001 N-acetylcysteine amide", "company": "Nacuity Pharmaceuticals"},
        "SPVN06": {"name": "SPVN06 RdCVF", "company": "SparingVision"},
        "Ultevursen": {"name": "Ultevursen", "company": "Sepul Bio"},
    }

    # 一般的なRP治療ニュースも検索
    general_queries = [
        ("retinitis pigmentosa gene therapy 2026 FDA approval new treatments", "一般RP遺伝子治療"),
        ("retinitis pigmentosa clinical trial 2026 new results Phase 3", "一般RP臨床試験"),
    ]

    all_search_text = []
    sources_queried = []

    # 各プログラムの検索
    print("\n--- Web検索実行中 ---\n")
    for prog_id, info in key_programs.items():
        if prog_id in programs:
            print(f"🔎 {prog_id} ({info['company']}) を検索中...")
            text = search_program_updates(prog_id, info["name"], info["company"])
            if text:
                all_search_text.append(text)
                sources_queried.append(f"DuckDuckGo: {prog_id}")
                print(f"  ✅ {len(text)}文字の情報を取得")
            else:
                print(f"  ⚠️ 情報取得失敗")

    # 一般検索
    for query, label in general_queries:
        print(f"🔎 {label} を検索中...")
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                text = "\n".join(
                    f"{r.get('title', '')} - {r.get('body', '')}" for r in results
                )
                if text:
                    all_search_text.append(text)
                    sources_queried.append(f"DuckDuckGo: {label}")
                    print(f"  ✅ {len(text)}文字の情報を取得")
                time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ 検索エラー: {e}")

    # 検索結果の分析
    print("\n--- 検索結果の分析 ---\n")
    combined_text = "\n".join(all_search_text)

    if not combined_text:
        print("⚠️ Web検索結果が取得できませんでした")
        print("手動で /update_rp_info check を実行してください")
        # 最終チェック日だけ更新
        _save_minimal_check()
        return

    # data_comparison.pyのユーティリティで分析
    extracted = extract_program_info_from_text(combined_text)
    comparison = compare_clinical_programs(extracted, kb)

    # 検索結果から追加の新規キーワードを検出
    new_findings = _detect_new_keywords(combined_text, programs)
    if new_findings:
        for finding in new_findings:
            if finding not in comparison["important_updates"]:
                comparison["important_updates"].append(finding)

    # レポート出力
    report = format_comparison_report(comparison)
    print(report)

    # 重要な更新の有無を判定
    has_important = any(
        calculate_importance_score(u) >= 70
        for u in comparison.get("important_updates", [])
    )

    # 推奨アクション
    print("\n### 🎯 推奨アクション\n")
    if has_important:
        print("重要な更新が見つかりました！")
        print("```bash")
        print("python scripts/update_latest_info.py full")
        print("```")
    elif comparison.get("important_updates"):
        print("軽微な更新が見つかりました。")
        print("```bash")
        print("python scripts/update_latest_info.py quick")
        print("```")
    else:
        print("重要な更新はありませんでした。")

    # 検索結果の詳細を表示
    print("\n### 🔍 検索結果の詳細\n")
    print(f"- 検索クエリ数: {len(sources_queried)}")
    print(f"- 取得テキスト量: {len(combined_text)}文字")
    print(f"- 検出プログラム: {', '.join(extracted.get('programs_mentioned', []))}")

    # 結果を保存
    save_check_results(comparison, sources_queried)
    print(f"\n✅ チェック結果を保存しました")


def _detect_new_keywords(text: str, existing_programs: dict) -> list:
    """検索結果から新しいキーワードやイベントを検出

    キーワードとプログラム名が同じ文（ピリオドまたは改行で区切られた単位）内に
    出現する場合のみ検出する。
    """
    import re
    findings = []

    # テキストを文単位に分割
    sentences = re.split(r'[.\n]', text.lower())

    # 重要なイベントキーワード（高確度のもののみ）
    event_keywords = {
        "fda approved": "FDA承認済み",
        "bla submitted": "BLA提出",
        "bla accepted": "BLA受理",
        "phase 3 completed": "Phase 3完了",
        "primary endpoint met": "主要評価項目達成",
        "primary endpoint not met": "主要評価項目未達成",
        "complete response letter": "Complete Response Letter",
        "clinical hold": "Clinical Hold",
        "discontinued": "開発中止",
    }

    for sentence in sentences:
        for keyword, description in event_keywords.items():
            if keyword in sentence:
                for prog_id in existing_programs:
                    if prog_id.lower() in sentence:
                        finding = f"{prog_id}: {description}の可能性"
                        if finding not in findings:
                            findings.append(finding)

    return findings


def _save_minimal_check():
    """最小限のチェック結果を保存（検索失敗時）"""
    check_file = Path("data/knowledge_base/last_check.json")
    check_data = {
        "last_check_date": datetime.now().isoformat(),
        "check_type": "monthly_web_search_failed",
        "note": "Web検索結果が取得できなかったため、簡易チェックのみ実行",
    }
    with open(check_file, "w", encoding="utf-8") as f:
        json.dump(check_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
