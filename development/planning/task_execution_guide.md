# タスク実行ガイド

このガイドは、ページ統合プロジェクトを効率的に実行するための参照ドキュメントです。

## 1. 現在のディレクトリ構造

```
/Users/kyohei/workspace/retina-roadmap/
├── docs/
│   ├── public/                    # 公開HTMLファイル（作業対象）
│   │   ├── index.html            # 現在のメインページ
│   │   ├── reality_and_actions.html
│   │   ├── regional_approval_timeline.html
│   │   ├── ai_predictions.html
│   │   ├── (他9ファイル)
│   │   └── images/               # 画像ファイル
│   ├── content/                  # Markdownソース
│   │   ├── main/
│   │   ├── medical/
│   │   └── regional/
│   └── development/              # 開発ドキュメント
│       └── planning/             # 計画書類（ここ）
├── src/
│   └── reporting/
│       └── build_report.py       # レポート生成スクリプト
└── data/
    └── knowledge_base/           # 臨床プログラムデータ
```

## 2. タスク別必要ファイル一覧

### Phase 0: 準備・分析

#### タスク 0.1: 現状把握
**必要ファイル:**
- `docs/public/*.html` (全13ファイル)
- `docs/content/**/*.md` (参考用)

**実行コマンド:**
```bash
# 各ファイルの行数・文字数カウント
wc -l docs/public/*.html

# 画像ファイルのリスト
ls -la docs/public/images/

# 重複コンテンツ検索例
grep -n "最速の承認予測" docs/public/*.html
```

#### タスク 0.2: バックアップ
**実行コマンド:**
```bash
# バックアップディレクトリ作成
mkdir -p docs/public_backup_$(date +%Y%m%d)

# ファイルコピー
cp -r docs/public/* docs/public_backup_$(date +%Y%m%d)/

# Gitタグ作成
git tag -a "before-page-consolidation" -m "Backup before page consolidation"
```

### Phase 1: 共通コンポーネント作成

#### タスク 1.1: CSS作成
**作成場所:** `docs/public/css/common.css`

**参考にする既存スタイル:**
- `docs/public/index.html` 内の`<style>`タグ
- レスポンシブテーブルCSS関数: `get_responsive_table_css()`

**基本構造:**
```css
/* カラーパレット */
:root {
  --primary-color: #3498db;
  --secondary-color: #2c3e50;
  --accent-color: #e74c3c;
  --bg-color: #f5f5f5;
  --text-color: #333;
}

/* タイポグラフィ */
body { font-family: -apple-system, BlinkMacSystemFont... }

/* レスポンシブグリッド */
.container { max-width: 1200px; margin: 0 auto; }

/* カードコンポーネント */
.card { background: white; border-radius: 10px; }
```

#### タスク 1.2: JavaScript作成
**作成場所:** `docs/public/js/common.js`

**実装する機能:**
1. タブ切り替え
2. アコーディオン
3. スムーススクロール
4. モバイルメニュー

### Phase 2: 新規ページ作成

#### 新index.html作成時の参照データ
**データソース:**
- 最速承認: `data/knowledge_base/clinical_programs.json` → OCU400
- 日本承認: FDA承認 + 5年（計算済み）
- プログラム数: 知識ベースのカウント

**必要な要素:**
```html
<!-- ヒーローセクション -->
<div class="hero">
  <h1>網膜色素変性症の治療はいつ？</h1>
  <div class="key-numbers">
    <div>2027年 - 最速承認（米国）</div>
    <div>2032年 - 日本での承認</div>
    <div>15種類 - 開発中の治療</div>
  </div>
</div>
```

#### patient_guide.html作成時の移行元
1. **reality_and_actions.html から:**
   - 「今すぐできること」セクション全体
   - 5つのアクションの詳細

2. **regional_approval_timeline.html から:**
   - 「日本での承認プロセス」セクション
   - Luxturnaの事例

3. **index.html から:**
   - 「最も有望な治療プログラム」テーブルの上位5行

## 3. 作業効率化のためのスニペット

### HTMLテンプレート
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><!-- ページタイトル --></title>
    <link rel="stylesheet" href="css/common.css">
    <!-- ページ固有CSS -->
</head>
<body>
    <!-- スキップリンク -->
    <a href="#main" class="skip-link">メインコンテンツへ</a>
    
    <!-- ヘッダー -->
    <header>
        <nav>
            <a href="index.html">ホーム</a>
            <a href="patient_guide.html">患者ガイド</a>
            <a href="medical_info.html">医療情報</a>
        </nav>
    </header>
    
    <!-- メインコンテンツ -->
    <main id="main">
        <!-- ページ内容 -->
    </main>
    
    <!-- フッター -->
    <footer>
        <p>&copy; 2025 網膜色素変性症治療予測プロジェクト</p>
    </footer>
    
    <script src="js/common.js"></script>
</body>
</html>
```

### コンテンツ抽出用コマンド
```bash
# 特定のセクションを抽出（例：h2タグで囲まれた部分）
awk '/<h2>今すぐできること<\/h2>/,/<h2>/' docs/public/reality_and_actions.html

# テーブルの特定行を抽出
grep -A 5 "NCT" docs/public/index.html | head -20
```

### リンク更新用sed
```bash
# 旧リンクを新リンクに一括置換
sed -i '' 's/reality_and_actions\.html/patient_guide.html/g' docs/public/*.html
```

## 4. チェックポイント

### 各フェーズ完了時の確認項目

**Phase 0 完了:**
- [ ] バックアップディレクトリが存在する
- [ ] Gitタグが作成されている
- [ ] 重複コンテンツリストが文書化されている

**Phase 1 完了:**
- [ ] common.cssが作成され、基本スタイルが定義されている
- [ ] common.jsが作成され、基本機能が実装されている
- [ ] HTMLテンプレートが利用可能

**Phase 2 各ページ完了:**
- [ ] 正しいHTMLバリデーション
- [ ] モバイルでの表示確認
- [ ] 内部リンクの動作確認

## 5. トラブルシューティング

### よくある問題と解決法

**問題:** CSSが適用されない
**解決:** パスを確認 `href="css/common.css"` vs `href="../css/common.css"`

**問題:** 日本語が文字化け
**解決:** UTF-8エンコーディングを確認、`<meta charset="UTF-8">`

**問題:** モバイルで横スクロール
**解決:** `max-width: 100%` と `overflow-x: auto` を適用

## 6. 次のステップ判断フロー

```
現在のタスク完了
    ↓
同じPhase内に未完了タスクがある？
    Yes → 次のタスクへ
    No  → 次のPhaseへ
        ↓
    Phase 2の場合：最優先ページから作成
    1. index.html
    2. patient_guide.html
    3. その他は優先度順
```