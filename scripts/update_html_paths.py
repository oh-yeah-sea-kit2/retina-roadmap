#!/usr/bin/env python3
"""
HTMLファイル内の画像パスとリンクを更新するスクリプト
"""

from pathlib import Path
import re

def update_html_paths():
    """HTMLファイル内のパスを新しい構造に合わせて更新"""
    public_dir = Path("docs/public")
    
    # 更新するパスのマッピング
    path_updates = {
        # 画像パス
        'src="figs/': 'src="images/',
        'href="figs/': 'href="images/',
        '../figs/': 'images/',
        './figs/': 'images/',
        
        # 相対リンクの更新（同じpublicディレクトリ内なので変更なし）
        # ただし、開発ドキュメントへのリンクがある場合は削除または更新が必要
    }
    
    updated_files = []
    
    # すべてのHTMLファイルを処理
    for html_file in public_dir.glob("*.html"):
        print(f"処理中: {html_file.name}")
        
        content = html_file.read_text(encoding='utf-8')
        original_content = content
        
        # パスを更新
        for old_path, new_path in path_updates.items():
            if old_path in content:
                content = content.replace(old_path, new_path)
                print(f"  - 更新: {old_path} → {new_path}")
        
        # ファイルが変更された場合のみ書き込み
        if content != original_content:
            html_file.write_text(content, encoding='utf-8')
            updated_files.append(html_file.name)
    
    # レポート生成スクリプトのパスも更新
    report_script = Path("src/reporting/build_report.py")
    if report_script.exists():
        print(f"\n処理中: {report_script}")
        content = report_script.read_text(encoding='utf-8')
        original_content = content
        
        # 出力パスを更新
        updates = {
            '"docs/': '"docs/public/',
            "'docs/": "'docs/public/",
            'docs/figs/': 'docs/public/images/',
            'figs/': 'images/',
        }
        
        for old_path, new_path in updates.items():
            if old_path in content:
                content = content.replace(old_path, new_path)
                print(f"  - 更新: {old_path} → {new_path}")
        
        if content != original_content:
            report_script.write_text(content, encoding='utf-8')
            updated_files.append(str(report_script))
    
    # 可視化スクリプトのパスも更新
    viz_scripts = list(Path("src/viz").glob("*.py"))
    for viz_script in viz_scripts:
        print(f"\n処理中: {viz_script}")
        content = viz_script.read_text(encoding='utf-8')
        original_content = content
        
        # 画像保存パスを更新
        updates = {
            'docs/figs/': 'docs/public/images/',
            'results/figs/': 'results/figs/',  # resultsは変更なし
        }
        
        for old_path, new_path in updates.items():
            if old_path in content:
                content = content.replace(old_path, new_path)
                print(f"  - 更新: {old_path} → {new_path}")
        
        if content != original_content:
            viz_script.write_text(content, encoding='utf-8')
            updated_files.append(str(viz_script))
    
    print(f"\n完了: {len(updated_files)}個のファイルを更新しました")
    if updated_files:
        print("更新されたファイル:")
        for file in updated_files:
            print(f"  - {file}")


if __name__ == "__main__":
    update_html_paths()