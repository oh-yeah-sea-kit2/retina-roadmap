#!/usr/bin/env python3
"""
GitHub Actions用の簡易週次チェックスクリプト
"""

import json
from datetime import datetime
from pathlib import Path


def main():
    """簡易的な週次チェック"""
    
    # 知識ベースの読み込み
    kb_path = Path("data/knowledge_base/clinical_programs.json")
    if not kb_path.exists():
        print("エラー: 知識ベースファイルが見つかりません")
        return
    
    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)
    
    # 最終チェック日の確認
    last_check_path = Path("data/knowledge_base/last_check.json")
    if last_check_path.exists():
        with open(last_check_path, "r", encoding="utf-8") as f:
            last_check = json.load(f)
            last_date = last_check.get("last_check_date", "不明")
    else:
        last_date = "初回チェック"
    
    # 重要なプログラムの状況確認
    programs = kb.get("programs", {})
    key_programs = ["MCO-010", "OCU400", "VP-001"]
    
    print("## 📊 更新チェック結果サマリー\n")
    print(f"- チェック日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"- 前回チェック: {last_date}")
    print(f"- 登録プログラム数: {len(programs)}件")
    print(f"- 重要な更新: 0件（自動チェック未実行）")
    print("")
    
    print("### 主要プログラムの状況\n")
    for prog_id in key_programs:
        if prog_id in programs:
            prog = programs[prog_id]
            phase = prog.get("current_phase", "不明")
            status = prog.get("status", "不明")
            print(f"- **{prog_id}**: {phase}, {status}")
        else:
            print(f"- **{prog_id}**: データなし")
    
    print("\n### 推奨アクション\n")
    print("手動で最新情報を確認することをお勧めします：")
    print("```bash")
    print("python scripts/update_latest_info.py check")
    print("```")
    
    # 最終チェック日を更新
    check_data = {
        "last_check_date": datetime.now().isoformat(),
        "check_type": "github_actions_simple",
        "note": "WebSearchが利用できないため簡易チェックのみ実行"
    }
    
    with open(last_check_path, "w", encoding="utf-8") as f:
        json.dump(check_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()