#!/usr/bin/env python3
"""
docsディレクトリを再編成するスクリプト
"""

import shutil
from pathlib import Path
import os

def reorganize_docs():
    """docsディレクトリのファイルを新しい構造に移動"""
    docs_dir = Path("docs")
    
    # 移動計画
    moves = {
        # 公開用HTMLファイル
        "public": [
            "index.html",
            "ai_predictions.html",
            "current_status_facts.html",
            "reality_and_actions.html",
            "regional_approval_timeline.html",
            "accessible_summary.html",
            "executive_summary_for_doctor.html",
            "for_doctor_checklist.html",
            "publication_disclaimer.html",
            "bottlenecks.html",
            "simulation_methodology.html",
            "ai_acceleration_impact.html",
            "publication_checklist.html"
        ],
        
        # 開発計画文書
        "development/planning": [
            "information_flow_analysis.md",
            "data_flow_improvement_plan.md",
            "detailed_implementation_plan.md",
            "workflow_automation_proposal.md",
            "new_structure_proposal.md",
            "directory_reorganization_plan.md"
        ],
        
        # 技術文書
        "development/technical": [
            "simulation_methodology.md",
            "advanced_simulation_design.md",
            "advanced_simulation_proposal.md",
            "advanced_simulation_results.md"
        ],
        
        # 分析文書
        "development/analysis": [
            "bottlenecks.md",
            "ai_acceleration_impact.md"
        ],
        
        # メインコンテンツのMarkdown
        "content/main": [
            "index.md",
            "ai_predictions.md",
            "current_status_facts.md",
            "reality_and_actions.md"
        ],
        
        # 地域別情報
        "content/regional": [
            "regional_approval_timeline.md"
        ],
        
        # アクセシビリティ対応
        "content/accessibility": [
            "accessible_summary.md"
        ],
        
        # 医療従事者向け
        "content/medical": [
            "executive_summary_for_doctor.md",
            "for_doctor_checklist.md"
        ],
        
        # チェックリスト
        "checklists": [
            "publication_checklist.md",
            "publication_disclaimer.md"
        ]
    }
    
    # ファイルを移動
    moved_count = 0
    for dest_dir, files in moves.items():
        dest_path = docs_dir / dest_dir
        for file in files:
            src_file = docs_dir / file
            if src_file.exists():
                dest_file = dest_path / file
                print(f"移動: {file} → {dest_dir}/")
                shutil.move(str(src_file), str(dest_file))
                moved_count += 1
            else:
                print(f"警告: {file} が見つかりません")
    
    # 画像ファイルの移動
    figs_dir = docs_dir / "figs"
    if figs_dir.exists():
        images_dir = docs_dir / "public" / "images"
        for img_file in figs_dir.glob("*.png"):
            print(f"移動: figs/{img_file.name} → public/images/")
            shutil.move(str(img_file), str(images_dir / img_file.name))
            moved_count += 1
        
        # 空のfigsディレクトリを削除
        if not list(figs_dir.iterdir()):
            figs_dir.rmdir()
            print("削除: 空のfigs/ディレクトリ")
    
    print(f"\n完了: {moved_count}個のファイルを移動しました")
    
    # 移動後の構造を表示
    print("\n新しいディレクトリ構造:")
    os.system("tree docs -I '__pycache__' | head -50")


if __name__ == "__main__":
    reorganize_docs()