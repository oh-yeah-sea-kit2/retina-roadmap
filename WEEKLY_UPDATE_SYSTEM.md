# 週次更新チェックシステム

## 概要

このシステムは、網膜色素変性症の治療法開発に関する最新情報を週次で自動チェックし、Claude Codeを活用して分析・報告する仕組みです。

## システム構成

### 1. GitHub Actionsワークフロー
**ファイル**: `.github/workflows/weekly-update-check.yml`

実行タイミング：
- 毎週月曜日 午前9時（JST）
- 手動実行も可能（Actions画面から）

### 2. Claude Codeの自動実行
**仕組み**：
1. GitHub ActionsがIssueを自動作成
2. Issue内の`@claude`メンションでClaude Codeが起動
3. `/update_rp_info check`コマンドを実行
4. 結果をIssueにコメントとして報告

処理フロー：
1. 週次チェック用のIssueを作成（または既存Issueにリマインダー追加）
2. Claude Codeが自動的に反応して更新チェックを実行
3. 重要な更新があれば推奨アクションを提示

## Claude Codeによる判定

Claude Codeが以下の観点から重要度を判定します：

### 重要な更新の例
- BLA申請の開始
- Phase進行（特にPhase 3への移行）
- 試験の成功/失敗の発表
- 新規の有望な治療プログラムの追加
- 規制当局からの重要な発表

### 推奨アクション
Claude Codeが状況に応じて以下を提案：
- **完全更新（full）**: 重大な変更があった場合
- **部分更新（quick）**: 中程度の変更があった場合  
- **更新不要**: 軽微な変更のみの場合

## 使用方法

### 1. 自動実行
- 毎週月曜日に自動的にIssueが作成されます
- Claude Codeが自動的に`/update_rp_info check`を実行
- 結果がIssueにコメントとして投稿されます

### 2. 手動実行
```bash
# GitHubのActionsタブから手動実行可能
1. GitHubリポジトリの Actions タブを開く
2. "週次更新チェック" ワークフローを選択
3. "Run workflow" ボタンをクリック
```

### 3. Issueでの直接実行
既存のIssueでも以下のコメントでClaude Codeを呼び出し可能：
```
@claude /update_rp_info check
```

## システムの利点

1. **シンプル**: 複雑なPythonスクリプト不要
2. **柔軟性**: Claude Codeの判断力で詳細な分析
3. **対話的**: Issue内で追加質問や指示が可能
4. **自動化**: 週次での自動チェック
5. **透明性**: 全ての処理がIssue内で可視化

## 技術的詳細

### GitHub Actions実装
- **重複チェック**: 同じ週のIssueが既に存在する場合はリマインダーコメントを追加
- **日付管理**: Asia/Tokyo時間で月曜日の日付を自動取得
- **エラーハンドリング**: 日付取得の代替ロジックを実装

### YAMLファイルの構成
```yaml
# 実行タイミング
on:
  schedule:
    - cron: '0 0 * * 0'  # 毎週月曜日 9:00 JST
  workflow_dispatch:  # 手動実行

# メイン処理
jobs:
  create-check-issue:
    - 今週のIssue存在チェック
    - 新規Issue作成 or リマインダーコメント追加
```

## 注意事項

- **Claude Code設定**: OAuth Tokenが正しく設定されている必要があります
- **権限**: Issue作成/コメントにはGITHUB_TOKENの権限が必要です
- **言語設定**: 日本語での応答設定が`claude.yml`に含まれています
- **開発時**: YAMLファイル修正時は必ず`act --list`で構文チェックを実行

## トラブルシューティング

### Issue作成されない場合
1. Actions の権限確認（Settings > Actions > General）
2. "Workflow permissions" が "Read and write permissions" になっているか確認
3. `act --list`でワークフロー構文をチェック

### Claude Codeが反応しない場合
1. Claude Code OAuth Tokenの設定確認
2. `claude.yml`ファイルの設定確認
3. Issue内の`@claude`メンションが正しいか確認

### ワークフロー開発時
```bash
# YAMLファイル作成・修正後は必ずチェック
act --list

# エラーがある場合は修正して再チェック
# 正常ならワークフロー一覧が表示される
```