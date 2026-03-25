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
        r"DSP-3077",
        r"Botaretigene|bota-vec"
    ]
    
    for pattern in program_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            program_name = pattern.split("|")[0]  # 最初の名前を使用
            info["programs_mentioned"].append(program_name)
    
    # Phase情報の抽出
    # 各プログラム名の近傍に出現するPhase番号を収集する。
    # 誤検知を防ぐため以下のフィルタを適用:
    # 1. 将来の計画を示すキーワード（planned, design等）の近傍は除外
    # 2. 他のプログラム名がPhase言及とプログラム名の間にある場合は除外
    # 3. プログラム名から最も近いPhase言及を優先
    phase_programs = ["MCO-010", "OCU400", "VP-001", "AGTC-501", "OpCT-001", "NPI-001", "DSP-3077"]
    all_program_names = phase_programs + ["Botaretigene", "bota-vec", "SPVN06", "SPVN20",
                                          "Ultevursen", "ZM-02", "jCells", "DSP-3077",
                                          "VG901", "GS030", "4D-125"]
    # 将来の計画を示すキーワード（Phase言及の前後50文字に出現する場合は除外）
    future_keywords = re.compile(
        r"planned|design|expected|will\s+start|to\s+start|initiat\w+\s+in|"
        r"proposed|upcoming|目指|予定|計画|開始予定|finalize",
        re.IGNORECASE,
    )

    for program in phase_programs:
        phases_with_distance = []  # (distance, phase_number) のリスト
        for match in re.finditer(re.escape(program), text, re.IGNORECASE):
            prog_pos = match.start()
            # プログラム名の前後100文字の範囲でPhase番号を探す
            start = max(0, prog_pos - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            prog_offset = prog_pos - start  # context内でのプログラム名の位置
            # "Phase 2/3" や "Phase 1/2a" のような複合表記にも対応
            # 注意: "Phase 2/3" は「Phase 2からPhase 3へ向かう試験」を意味し、
            # まだPhase 3に到達したわけではないため、低い方の番号（2）を採用する
            for phase_match in re.finditer(r"Phase\s*(\d)(?:\s*/\s*(\d))?", context, re.IGNORECASE):
                # Phase言及の前後50文字に将来を示すキーワードがあれば除外
                pm_start = max(0, phase_match.start() - 50)
                pm_end = min(len(context), phase_match.end() + 50)
                surrounding = context[pm_start:pm_end]
                if future_keywords.search(surrounding):
                    continue
                # プログラム名とPhase言及の間に別のプログラム名があれば除外
                between_start = min(prog_offset + len(program), phase_match.start())
                between_end = max(prog_offset, phase_match.end())
                between_text = context[between_start:between_end]
                has_other_program = False
                for other in all_program_names:
                    if other != program and re.search(re.escape(other), between_text, re.IGNORECASE):
                        has_other_program = True
                        break
                if has_other_program:
                    continue
                distance = abs(phase_match.start() - prog_offset)
                # 複合Phase（例: "Phase 2/3"）は低い方の番号を採用
                # "Phase 2/3" = Phase 2からPhase 3を目指す試験であり、Phase 3到達ではない
                phase_num = int(phase_match.group(1))
                phases_with_distance.append((distance, phase_num))
        if phases_with_distance:
            # 最も近いPhase言及を優先（距離30文字以内のものだけ集めて最大値）
            # 近いものがなければ全体から最大値
            close_phases = [p for d, p in phases_with_distance if d <= 30]
            if close_phases:
                max_phase = max(close_phases)
            else:
                max_phase = max(p for _, p in phases_with_distance)
            info["phase_updates"][program] = f"Phase {max_phase}"
    
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


def _extract_max_phase_number(phase_str: str) -> int:
    """Phase文字列から現在のPhase番号を抽出する。
    複合Phase表記は低い方の番号を採用する（試験の開始Phase）。
    "Phase 2/3" → 2, "Phase 1/2a" → 1, "Phase 1/2" → 1,
    "Phase 3" → 3, "Phase 2b" → 2, "BLA" → 4
    """
    if not phase_str:
        return 0
    if "BLA" in phase_str.upper() or "NDA" in phase_str.upper():
        return 4  # BLA/NDAはPhase 3より進んだ段階
    # "Phase X/Y" の形式を検出し、Xを採用（複合Phaseの低い方）
    compound = re.search(r"(\d)\s*/\s*(\d)", phase_str)
    if compound:
        return int(compound.group(1))
    # 単独Phase（"Phase 3" など）
    numbers = re.findall(r"\d", phase_str)
    return max(int(n) for n in numbers) if numbers else 0


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

    # 更新の検出（Phase番号を正規化して比較）
    # Phase番号が上がった場合 → 進捗として報告
    # Phase番号が下がった場合 → 検索結果の情報不足の可能性が高いため無視
    #   （本当の後退・中止は _detect_new_keywords で "discontinued" 等から検出）
    for program, phase in new_data.get("phase_updates", {}).items():
        if program in existing_programs:
            existing_phase = existing_programs[program].get("current_phase", "")
            new_max = _extract_max_phase_number(phase)
            existing_max = _extract_max_phase_number(existing_phase)
            if new_max > existing_max:
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