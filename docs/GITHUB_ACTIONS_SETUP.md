# GitHub Actions セットアップガイド

## ⚠️ 重要: Workflows 権限について

このブランチからGitHub Actionsワークフローファイル (`.github/workflows/ci.yml`) を直接プッシュすることができません。これはGitHub Appに`workflows`権限が付与されていないためです。

## 🔧 API自動生成を有効にする方法

### オプション1: パッチファイルを適用 (推奨)

同梱の`github-actions-api-generation.patch`を適用してください:

```bash
# パッチを適用
git apply docs/github-actions-api-generation.patch

# 変更を確認
git diff .github/workflows/ci.yml

# コミット
git add .github/workflows/ci.yml
git commit -m "Add API generation to CI/CD pipeline"
git push
```

### オプション2: 手動で編集

`.github/workflows/ci.yml`の`Generate report`ステップの後に以下を追加:

```yaml
    - name: Generate report
      run: |
        python src/reporting/build_report.py

    - name: Generate JSON API
      run: |
        python src/api_generator.py

    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: results
        path: |
          results/
          docs/
```

## 📝 変更内容

追加されるステップ:
- **Generate JSON API**: `src/api_generator.py`を実行してJSON APIファイルを生成
- 既存のデプロイステップで`docs/public/api/v1/`も自動的にGitHub Pagesにデプロイされます

## ✅ 動作確認

変更後、以下を確認してください:

1. GitHub Actionsが正常に実行される
2. API生成ステップが成功する
3. GitHub PagesにAPIファイルがデプロイされる
4. エンドポイントにアクセス可能:
   - `https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/meta.json`
   - `https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/programs.json`

## 🔍 トラブルシューティング

### エラー: `workflows` permission required

GitHub App設定で`workflows`権限を有効にする必要があります:

1. リポジトリの Settings → Actions → General
2. Workflow permissions で "Read and write permissions" を選択
3. "Allow GitHub Actions to create and approve pull requests" をチェック

または、リポジトリ管理者に権限変更を依頼してください。

### API生成ステップが失敗する

```bash
# ローカルでテスト
python src/api_generator.py

# 依存関係を確認
pip install -r requirements.txt
```

---

**作成日**: 2025-11-18
**関連**: API_REDESIGN_PROPOSAL.md, IMPLEMENTATION_GUIDE.md
