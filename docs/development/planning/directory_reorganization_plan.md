# docsディレクトリ再編成計画

## 現状の課題
- 36個のファイルが同一階層に混在
- 目的別の分類がない
- 開発用ドキュメントと公開用ドキュメントが混在
- 同じ内容のMDとHTMLが混在

## 提案する新しい構造

```
docs/
├── public/                      # 公開用（GitHub Pages）
│   ├── index.html              # メインページ
│   ├── ai_predictions.html     # AI予測
│   ├── current_status_facts.html
│   ├── reality_and_actions.html
│   ├── regional_approval_timeline.html
│   ├── accessible_summary.html
│   ├── executive_summary_for_doctor.html
│   ├── for_doctor_checklist.html
│   ├── publication_disclaimer.html
│   ├── css/                    # スタイルシート
│   │   └── main.css
│   └── images/                 # 画像ファイル
│       ├── CDF.png
│       ├── tornado.png
│       └── waterfall.png
│
├── development/                # 開発用ドキュメント
│   ├── planning/              # 計画・提案
│   │   ├── information_flow_analysis.md
│   │   ├── data_flow_improvement_plan.md
│   │   ├── detailed_implementation_plan.md
│   │   ├── workflow_automation_proposal.md
│   │   ├── new_structure_proposal.md
│   │   └── directory_reorganization_plan.md
│   │
│   ├── technical/             # 技術文書
│   │   ├── simulation_methodology.md
│   │   ├── advanced_simulation_design.md
│   │   ├── advanced_simulation_proposal.md
│   │   └── advanced_simulation_results.md
│   │
│   └── analysis/              # 分析・レポート
│       ├── bottlenecks.md
│       └── ai_acceleration_impact.md
│
├── content/                    # コンテンツソース（Markdown）
│   ├── main/                  # メインコンテンツ
│   │   ├── index.md
│   │   ├── ai_predictions.md
│   │   ├── current_status_facts.md
│   │   └── reality_and_actions.md
│   │
│   ├── regional/              # 地域別情報
│   │   └── regional_approval_timeline.md
│   │
│   ├── accessibility/         # アクセシビリティ対応
│   │   └── accessible_summary.md
│   │
│   └── medical/               # 医療従事者向け
│       ├── executive_summary_for_doctor.md
│       └── for_doctor_checklist.md
│
└── checklists/                 # チェックリスト・ガイド
    ├── publication_checklist.md
    └── publication_disclaimer.md
```

## 移行手順

### 1. ディレクトリ作成
```bash
# 新しいディレクトリ構造を作成
mkdir -p docs/public/css docs/public/images
mkdir -p docs/development/planning docs/development/technical docs/development/analysis
mkdir -p docs/content/main docs/content/regional docs/content/accessibility docs/content/medical
mkdir -p docs/checklists
```

### 2. ファイル移動スクリプト
```python
# scripts/reorganize_docs.py
import shutil
from pathlib import Path

def reorganize_docs():
    docs_dir = Path("docs")
    
    # 公開用HTMLファイル
    public_files = [
        "index.html", "ai_predictions.html", "current_status_facts.html",
        "reality_and_actions.html", "regional_approval_timeline.html",
        "accessible_summary.html", "executive_summary_for_doctor.html",
        "for_doctor_checklist.html", "publication_disclaimer.html"
    ]
    
    for file in public_files:
        if (docs_dir / file).exists():
            shutil.move(str(docs_dir / file), str(docs_dir / "public" / file))
    
    # 画像ファイル
    if (docs_dir / "figs").exists():
        for img in (docs_dir / "figs").glob("*.png"):
            shutil.move(str(img), str(docs_dir / "public/images" / img.name))
    
    # 開発用ドキュメント
    planning_files = [
        "information_flow_analysis.md", "data_flow_improvement_plan.md",
        "detailed_implementation_plan.md", "workflow_automation_proposal.md",
        "new_structure_proposal.md", "directory_reorganization_plan.md"
    ]
    
    for file in planning_files:
        if (docs_dir / file).exists():
            shutil.move(str(docs_dir / file), str(docs_dir / "development/planning" / file))
    
    # 以下同様に他のファイルも移動
```

### 3. GitHub Pages設定の更新
`.github/workflows/ci.yml`を更新:
```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v4
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs/public  # 変更点
    publish_branch: gh-pages
```

### 4. HTMLファイル内のパス更新
```python
# scripts/update_html_paths.py
def update_html_paths():
    """HTMLファイル内の画像パスを更新"""
    public_dir = Path("docs/public")
    
    for html_file in public_dir.glob("*.html"):
        content = html_file.read_text()
        # 画像パスを更新
        content = content.replace('src="figs/', 'src="images/')
        content = content.replace('href="figs/', 'href="images/')
        html_file.write_text(content)
```

## メリット

1. **構造の明確化**
   - 用途別にファイルが整理される
   - 新規ファイルの配置場所が明確

2. **保守性の向上**
   - 公開用と開発用が分離
   - 関連ファイルがまとまっている

3. **CI/CDの簡素化**
   - 公開ディレクトリが明確
   - 不要なファイルが公開されない

4. **拡張性**
   - 新しいカテゴリの追加が容易
   - 多言語対応時の構造拡張が簡単

## 実装優先度

1. **高優先度**: public/とcontent/の分離（公開に直接影響）
2. **中優先度**: development/の整理（開発効率に影響）
3. **低優先度**: さらなる細分化（必要に応じて）