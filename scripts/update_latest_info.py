#!/usr/bin/env python3
"""
網膜色素変性症の最新情報を収集し、データベースを更新するスクリプト

使用方法:
    python scripts/update_latest_info.py
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
import subprocess
import re

# プロジェクトルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetch_trials import fetch_clinical_trials
from src.fetch_papers import fetch_papers
from scripts.utils.data_comparison import (
    load_knowledge_base,
    extract_program_info_from_text,
    compare_clinical_programs,
    format_comparison_report,
    save_check_results
)


def generate_search_queries():
    """知識ベースから動的に検索クエリを生成"""
    kb = load_knowledge_base()
    programs = kb.get('programs', {})
    
    # 重要なプログラムを優先度順にソート
    priority_programs = []
    for name, info in programs.items():
        priority_score = 0
        # BLA申請中は最優先
        if 'BLA' in info.get('status', ''):
            priority_score = 100
        # Phase 3は高優先
        elif 'Phase 3' in info.get('current_phase', ''):
            priority_score = 80
        # Phase 2/3は中優先
        elif 'Phase 2/3' in info.get('current_phase', '') or 'Phase 2' in info.get('current_phase', ''):
            priority_score = 60
        # FDA Fast Trackなど規制優遇がある場合は+10
        if any('FDA' in r or 'Fast Track' in r for r in info.get('regulatory', [])):
            priority_score += 10
        
        if priority_score > 0:
            priority_programs.append((name, info, priority_score))
    
    # スコア順にソート
    priority_programs.sort(key=lambda x: x[2], reverse=True)
    
    # 上位プログラムから検索クエリを生成
    queries = []
    for name, info, _ in priority_programs[:7]:  # 上位7個まで
        company = info.get('company', '')
        phase = info.get('current_phase', '')
        query = f"{name} {company} retinitis pigmentosa 2025 latest update {phase}"
        queries.append(query.strip())
    
    # 一般的な検索クエリも追加
    queries.extend([
        "retinitis pigmentosa gene therapy 2025 FDA approval new treatments",
        "網膜色素変性症 遺伝子治療 2025 最新 日本 承認"
    ])
    
    return queries


def update_command_search_queries(queries):
    """update_rp_info.mdの検索クエリセクションを更新"""
    command_path = Path(__file__).parent.parent / ".claude" / "commands" / "update_rp_info.md"
    
    if not command_path.exists():
        print("警告: update_rp_info.mdが見つかりません")
        return
    
    with open(command_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 検索クエリセクションを生成
    query_section = "   ```bash\n   # Gemini Searchを使用（より包括的な情報収集が可能）\n"
    for query in queries:
        query_section += f'   gemini --prompt "WebSearch: {query}"\n'
    query_section += "   ```"
    
    # 既存の検索クエリセクションを探して置換
    pattern = r'(```bash\n   # Gemini Searchを使用.*?\n)(.*?)(   ```)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        new_content = content[:match.start()] + query_section + content[match.end():]
        
        with open(command_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print("update_rp_info.mdの検索クエリを更新しました")
    else:
        print("警告: 検索クエリセクションが見つかりません")


def web_search_retina_updates():
    """Web検索で最新の網膜色素変性症治療情報を収集"""
    
    print("\n=== Web検索で最新情報を収集中 ===")
    
    # 動的に検索クエリを生成
    search_queries = generate_search_queries()
    
    # update_rp_info.mdも更新
    update_command_search_queries(search_queries)
    
    updates = []
    
    for query in search_queries:
        print(f"\n検索中: {query[:50]}...")
        # 注: 実際のClaude Code環境ではWebSearchツールが使用される
        # ここではプレースホルダーとして実装
        update = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": f"[検索結果: {query}]"
        }
        updates.append(update)
    
    return updates


def extract_key_updates(web_results, existing_kb):
    """Web検索結果から重要な更新情報を抽出し、既存データと比較"""
    
    # 全てのWeb検索結果を結合
    all_text = "\n".join([result.get("results", "") for result in web_results])
    
    # 情報を抽出
    extracted_info = extract_program_info_from_text(all_text)
    
    # 既存データと比較
    comparison = compare_clinical_programs(extracted_info, existing_kb)
    
    # key_updates形式に変換
    key_updates = {
        "comparison": comparison,
        "extracted_info": extracted_info,
        "report": format_comparison_report(comparison)
    }
    
    return key_updates


def update_knowledge_base(key_updates, existing_kb):
    """知識ベースを更新"""
    
    kb_file = Path("data/knowledge_base/clinical_programs.json")
    comparison = key_updates.get("comparison", {})
    
    # 更新があった場合のみ処理
    if comparison.get("important_updates") or comparison.get("new_programs"):
        # 既存の知識ベースをコピー
        updated_kb = json.loads(json.dumps(existing_kb))
        updated_kb["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        
        # 新規プログラムの追加
        for program in comparison.get("new_programs", []):
            updated_kb["programs"][program] = {
                "company": "TBD",
                "current_phase": "TBD",
                "status": "New",
                "key_dates": {},
                "trial_ids": [],
                "modality": "TBD",
                "target": "TBD",
                "regulatory": [],
                "recent_updates": [{
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "event": "Newly identified program",
                    "source": "Web search"
                }],
                "notes": "Automatically added - needs manual verification"
            }
        
        # 更新履歴の追加
        update_history_file = Path("data/knowledge_base/update_history.json")
        with open(update_history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
        
        history["updates"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "automatic_update",
            "summary": f"Found {len(comparison.get('new_programs', []))} new programs, {len(comparison.get('important_updates', []))} important updates",
            "changes": {
                "new_programs": comparison.get("new_programs", []),
                "updated_programs": list(comparison.get("updated_programs", {}).keys()),
                "key_events": comparison.get("important_updates", [])
            }
        })
        
        # 保存
        with open(kb_file, "w", encoding="utf-8") as f:
            json.dump(updated_kb, f, indent=2, ensure_ascii=False)
        
        with open(update_history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        return updated_kb
    
    return existing_kb


def update_simulation_parameters(key_updates):
    """重要な更新に基づいてシミュレーションパラメータを更新"""
    
    params_file = Path("data/processed/simulation_params.json")
    
    if params_file.exists():
        with open(params_file, "r", encoding="utf-8") as f:
            params = json.load(f)
    else:
        params = {}
    
    # 更新日時を記録
    params["last_updated"] = datetime.now().isoformat()
    
    # 保存
    with open(params_file, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2, ensure_ascii=False)
    
    return params


def generate_update_summary(key_updates):
    """更新内容のサマリーを生成"""
    
    # 比較レポートを使用
    report = key_updates.get("report", "")
    
    summary = f"""
## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: {datetime.now().strftime('%Y年%m月%d日')}

{report}
"""
    
    return summary


def update_documentation(summary, key_updates):
    """ドキュメントファイルの更新"""
    
    # CLAUDE.mdの更新履歴に追記
    claude_md_path = Path("CLAUDE.md")
    
    with open(claude_md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 更新履歴セクションを探す
    update_section_start = content.find("## 最近の更新履歴")
    
    if update_section_start != -1:
        # 新しい更新エントリを作成
        new_entry = f"""
### {datetime.now().strftime('%Y年%m月%d日')}（自動更新）
- **update_latest_info.pyによる自動更新**
{summary}
"""
        
        # 更新履歴の直後に挿入
        next_section = content.find("\n##", update_section_start + 1)
        if next_section == -1:
            next_section = len(content)
        
        # 最初の###を探す
        first_entry = content.find("\n###", update_section_start)
        if first_entry != -1 and first_entry < next_section:
            # 既存のエントリの前に挿入
            updated_content = (
                content[:first_entry] + 
                new_entry + 
                content[first_entry:]
            )
        else:
            # エントリがない場合は末尾に追加
            updated_content = (
                content[:next_section] + 
                new_entry + 
                content[next_section:]
            )
        
        with open(claude_md_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        print("CLAUDE.mdを更新しました")


def main():
    """メイン処理"""
    
    print("網膜色素変性症の最新情報更新を開始します...")
    
    # 1. 既存データの読み込み
    existing_kb = load_knowledge_base()
    print(f"\n既存の知識ベース: {len(existing_kb.get('programs', {}))}個のプログラム")
    
    # 2. Web検索で最新情報を収集
    web_results = web_search_retina_updates()
    
    # 3. ClinicalTrials.govから最新データを取得
    print("\n=== ClinicalTrials.govから最新データ取得 ===")
    try:
        fetch_clinical_trials()
    except Exception as e:
        print(f"警告: 臨床試験データの取得でエラー: {e}")
    
    # 4. PubMedから最新論文を取得
    print("\n=== PubMedから最新論文取得 ===")
    try:
        fetch_papers()
    except Exception as e:
        print(f"警告: 論文データの取得でエラー: {e}")
    
    # 5. 重要な更新を抽出（既存データと比較）
    key_updates = extract_key_updates(web_results, existing_kb)
    
    # 6. 知識ベースを更新
    comparison = key_updates.get("comparison", {})
    if comparison.get("important_updates") or comparison.get("new_programs"):
        print("\n=== 知識ベースを更新 ===")
        updated_kb = update_knowledge_base(key_updates, existing_kb)
        print(f"更新後: {len(updated_kb.get('programs', {}))}個のプログラム")
    
    # 7. シミュレーションパラメータを更新
    if comparison.get("important_updates"):
        print("\n=== シミュレーションパラメータを更新 ===")
        update_simulation_parameters(key_updates)
    
    # 8. 更新サマリーを生成
    summary = generate_update_summary(key_updates)
    print("\n=== 更新サマリー ===")
    print(summary)
    
    # 9. ドキュメントを更新
    if comparison.get("important_updates"):
        update_documentation(summary, key_updates)
    
    # 10. チェック結果を保存
    sources = [q["query"] for q in web_results]
    save_check_results(comparison, sources)
    
    # 11. 更新ログを保存
    log_dir = Path("data/update_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "web_results": web_results,
            "key_updates": key_updates,
            "summary": summary
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n更新ログを保存しました: {log_file}")
    print("\n更新処理が完了しました！")
    
    # 次のステップを案内
    if comparison.get("important_updates"):
        print("\n=== 次のステップ ===")
        print("1. シミュレーションを再実行:")
        print("   python src/sim/timeline_sim.py")
        print("\n2. レポートを再生成:")
        print("   python src/reporting/build_report.py")
        print("\n3. 変更内容を確認してコミット:")
        print("   git status")
        print("   git diff")
    else:
        print("\n重要な更新はありませんでした。")


if __name__ == "__main__":
    main()