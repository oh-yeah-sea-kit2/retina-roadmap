#!/usr/bin/env python3
"""
データ比較ユーティリティ
Web検索結果と既存の知識ベースを比較し、新規・更新・変更なしを分類
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any


def load_knowledge_base() -> Dict[str, Any]:
    """知識ベースを読み込む"""
    kb_path = Path("data/knowledge_base/clinical_programs.json")
    if kb_path.exists():
        with open(kb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"programs": {}}


def extract_program_info_from_text(text: str) -> Dict[str, Any]:
    """テキストから治療プログラム情報を抽出"""
    info = {
        "programs_mentioned": [],
        "phase_updates": {},
        "regulatory_updates": {},
        "key_events": []
    }
    
    # 治療プログラム名の抽出
    program_patterns = [
        r"MCO-010",
        r"OCU400",
        r"VP-001",
        r"AGTC-501",
        r"OpCT-001",
        r"NPI-001",
        r"Botaretigene|bota-vec"
    ]
    
    for pattern in program_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            program_name = pattern.split("|")[0]  # 最初の名前を使用
            info["programs_mentioned"].append(program_name)
    
    # Phase情報の抽出
    phase_patterns = [
        (r"(MCO-010).*?Phase\s*(\d)", "MCO-010"),
        (r"(OCU400).*?Phase\s*(\d)", "OCU400"),
        (r"(VP-001).*?Phase\s*(\d)", "VP-001")
    ]
    
    for pattern, program in phase_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info["phase_updates"][program] = f"Phase {match.group(2)}"
    
    # BLA/FDA申請情報の抽出
    bla_patterns = [
        (r"(MCO-010).*?(BLA|submission|申請).*?(initiated|started|開始)", "BLA submission initiated"),
        (r"(OCU400).*?(BLA|MAA).*?(2026)", "BLA/MAA planned 2026"),
        (r"(VP-001).*?Phase\s*2/3.*?(2025)", "Phase 2/3 planned 2025")
    ]
    
    for pattern, event in bla_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            program = re.search(pattern, text, re.IGNORECASE).group(1)
            info["key_events"].append({
                "program": program,
                "event": event,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
    
    return info


def compare_clinical_programs(new_data: Dict[str, Any], existing_kb: Dict[str, Any]) -> Dict[str, Any]:
    """新旧データを比較し、差分を検出"""
    comparison = {
        "new_programs": [],
        "updated_programs": {},
        "unchanged_programs": [],
        "important_updates": []
    }
    
    existing_programs = existing_kb.get("programs", {})
    
    # 新規プログラムの検出
    for program in new_data.get("programs_mentioned", []):
        if program not in existing_programs:
            comparison["new_programs"].append(program)
    
    # 更新の検出
    for program, phase in new_data.get("phase_updates", {}).items():
        if program in existing_programs:
            existing_phase = existing_programs[program].get("current_phase", "")
            if phase != existing_phase:
                comparison["updated_programs"][program] = {
                    "old_phase": existing_phase,
                    "new_phase": phase
                }
                comparison["important_updates"].append(
                    f"{program}: Phase更新 {existing_phase} → {phase}"
                )
    
    # 重要なイベントの検出
    for event in new_data.get("key_events", []):
        program = event["program"]
        if program in existing_programs:
            # 既存の更新履歴と比較
            recent_updates = existing_programs[program].get("recent_updates", [])
            is_new = True
            for update in recent_updates:
                if update.get("event", "").lower() in event["event"].lower():
                    is_new = False
                    break
            
            if is_new:
                comparison["important_updates"].append(
                    f"{program}: {event['event']}"
                )
    
    # 変更なしのプログラム
    for program in new_data.get("programs_mentioned", []):
        if (program in existing_programs and 
            program not in comparison["new_programs"] and 
            program not in comparison["updated_programs"]):
            comparison["unchanged_programs"].append(program)
    
    return comparison


def calculate_importance_score(update: str) -> int:
    """更新の重要度スコアを計算（0-100）"""
    score = 50  # 基本スコア
    
    # キーワードによるスコアリング
    high_importance_keywords = [
        ("BLA", 30), ("FDA", 25), ("承認", 30), ("approval", 30),
        ("Phase 3", 20), ("primary endpoint", 25), ("failed", -20),
        ("initiated", 15), ("completed", 20)
    ]
    
    for keyword, points in high_importance_keywords:
        if keyword.lower() in update.lower():
            score += points
    
    return min(max(score, 0), 100)  # 0-100の範囲に制限


def format_comparison_report(comparison: Dict[str, Any]) -> str:
    """比較結果を見やすい形式でフォーマット"""
    report = []
    
    # サマリー
    report.append("## 📊 更新チェック結果サマリー\n")
    report.append(f"- 新規プログラム: {len(comparison['new_programs'])}件")
    report.append(f"- 更新されたプログラム: {len(comparison['updated_programs'])}件")
    report.append(f"- 変更なし: {len(comparison['unchanged_programs'])}件")
    report.append(f"- 重要な更新: {len(comparison['important_updates'])}件\n")
    
    # 重要な更新
    if comparison['important_updates']:
        report.append("### 🚨 重要な更新")
        for update in sorted(comparison['important_updates'], 
                           key=lambda x: calculate_importance_score(x), 
                           reverse=True):
            score = calculate_importance_score(update)
            if score >= 70:
                report.append(f"- **{update}** (重要度: {score}/100)")
            else:
                report.append(f"- {update} (重要度: {score}/100)")
        report.append("")
    
    # 新規プログラム
    if comparison['new_programs']:
        report.append("### 🆕 新規プログラム")
        for program in comparison['new_programs']:
            report.append(f"- {program}")
        report.append("")
    
    # 更新されたプログラム
    if comparison['updated_programs']:
        report.append("### 🔄 更新されたプログラム")
        for program, changes in comparison['updated_programs'].items():
            report.append(f"- {program}: {changes['old_phase']} → {changes['new_phase']}")
        report.append("")
    
    # 変更なし
    if comparison['unchanged_programs']:
        report.append("### ✅ 変更なし（既知の情報）")
        report.append(f"- {', '.join(comparison['unchanged_programs'])}")
    
    return "\n".join(report)


def save_check_results(comparison: Dict[str, Any], sources: List[str]) -> None:
    """チェック結果を保存"""
    check_file = Path("data/knowledge_base/last_check.json")
    
    check_data = {
        "last_check_date": datetime.now().isoformat(),
        "check_type": "web_search",
        "programs_checked": (
            comparison.get("new_programs", []) + 
            list(comparison.get("updated_programs", {}).keys()) + 
            comparison.get("unchanged_programs", [])
        ),
        "sources_queried": sources,
        "new_findings": comparison.get("new_programs", []),
        "updates_found": comparison.get("important_updates", [])
    }
    
    with open(check_file, "w", encoding="utf-8") as f:
        json.dump(check_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # テスト実行
    kb = load_knowledge_base()
    print(f"Loaded {len(kb.get('programs', {}))} programs from knowledge base")
    
    # サンプルテキストでテスト
    sample_text = """
    MCO-010 has initiated BLA submission to FDA in July 2025.
    OCU400 Phase 3 trial is progressing well.
    VP-001 will start Phase 2/3 in late 2025.
    """
    
    extracted = extract_program_info_from_text(sample_text)
    print("\nExtracted info:", json.dumps(extracted, indent=2))
    
    comparison = compare_clinical_programs(extracted, kb)
    report = format_comparison_report(comparison)
    print("\n" + report)