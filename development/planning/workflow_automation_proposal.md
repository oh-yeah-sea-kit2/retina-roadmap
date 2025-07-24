# ワークフロー自動化の具体的改善提案

## 1. GitHub Actionsによる自動更新システム

### 1.1 現状の課題
- `/update_rp_info`はClaude Code専用コマンドでGitHub Actionsでは実行不可
- Gemini SearchもClaude Code環境専用
- 手動での定期更新が必要

### 1.2 解決策：GitHub Actions対応版の実装

#### A. 新規スクリプトの作成
```python
# scripts/github_update_workflow.py
import os
import json
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

class GitHubUpdateWorkflow:
    """GitHub Actions環境で動作する更新ワークフロー"""
    
    def __init__(self):
        self.clinicaltrials_api = "https://clinicaltrials.gov/api/v2/"
        self.pubmed_api = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        
    def search_web_fallback(self, query):
        """Web検索の代替実装（Google Custom Search API使用）"""
        api_key = os.environ.get('GOOGLE_API_KEY')
        cx = os.environ.get('GOOGLE_CX')
        if not api_key or not cx:
            return []
        
        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={query}"
        response = requests.get(url)
        # 結果を処理
        
    def update_clinical_trials(self):
        """ClinicalTrials.govから最新データを取得"""
        # 既存のfetch_trials.pyを活用
        
    def update_knowledge_base(self):
        """知識ベースを更新"""
        # Web検索の代わりにRSSフィードやAPIを活用
```

#### B. GitHub Actions ワークフロー設定
```yaml
# .github/workflows/auto-update.yml
name: Auto Update RP Information

on:
  schedule:
    # 毎週月曜日 9:00 JST（日曜日 24:00 UTC）
    - cron: '0 0 * * 0'
    # 毎月1日 9:00 JST
    - cron: '0 0 1 * *'
  workflow_dispatch:
    inputs:
      update_mode:
        description: 'Update mode'
        required: true
        default: 'check'
        type: choice
        options:
          - check
          - quick
          - full

jobs:
  update-information:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
      with:
        token: ${{ secrets.PAT_TOKEN }}  # 書き込み権限のあるトークン
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install beautifulsoup4 feedparser
    
    - name: Run update workflow
      env:
        UPDATE_MODE: ${{ inputs.update_mode || 'check' }}
        GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        GOOGLE_CX: ${{ secrets.GOOGLE_CX }}
      run: |
        python scripts/github_update_workflow.py --mode $UPDATE_MODE
    
    - name: Check for changes
      id: check_changes
      run: |
        git diff --exit-code || echo "changes=true" >> $GITHUB_OUTPUT
    
    - name: Create Pull Request
      if: steps.check_changes.outputs.changes == 'true'
      uses: peter-evans/create-pull-request@v5
      with:
        token: ${{ secrets.PAT_TOKEN }}
        commit-message: 'chore: 最新情報の自動更新'
        title: '🔄 RP治療情報の自動更新 - ${{ env.UPDATE_DATE }}'
        body: |
          ## 自動更新の内容
          
          更新日時: ${{ env.UPDATE_DATE }}
          更新モード: ${{ env.UPDATE_MODE }}
          
          ### 更新内容
          ${{ env.UPDATE_SUMMARY }}
          
          ### 変更ファイル
          - data/knowledge_base/clinical_programs.json
          - data/processed/parameters.yaml
          - docs/index.html
          
          このPRは自動生成されました。内容を確認してマージしてください。
        branch: auto-update/${{ env.UPDATE_DATE }}
        delete-branch: true
```

## 2. データ取得の具体的改善

### 2.1 RSSフィードとAPIの活用
```python
# scripts/utils/rss_monitor.py
import feedparser
from datetime import datetime, timedelta

class ClinicalTrialsRSSMonitor:
    """ClinicalTrials.govのRSSフィードを監視"""
    
    RSS_FEEDS = {
        'retinitis_pigmentosa': 'https://clinicaltrials.gov/ct2/results/rss.xml?cond=Retinitis+Pigmentosa&count=50',
        'gene_therapy': 'https://clinicaltrials.gov/ct2/results/rss.xml?cond=Retinitis+Pigmentosa&intr=gene+therapy&count=50'
    }
    
    def get_recent_updates(self, days=7):
        """過去N日間の更新を取得"""
        updates = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for feed_name, feed_url in self.RSS_FEEDS.items():
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')
                if pub_date > cutoff_date:
                    updates.append({
                        'nct_id': self.extract_nct_id(entry.link),
                        'title': entry.title,
                        'updated': pub_date.isoformat(),
                        'feed': feed_name
                    })
        
        return updates
```

### 2.2 企業ニュースAPIの統合
```python
# scripts/utils/news_aggregator.py
class NewsAggregator:
    """企業プレスリリースを収集"""
    
    COMPANY_RSS_FEEDS = {
        'Nanoscope': 'https://www.nanoscopetx.com/feed/',
        'Ocugen': 'https://ir.ocugen.com/rss/news-releases.xml',
        # 他の企業のRSSフィード
    }
    
    def check_company_updates(self):
        """各企業の最新ニュースをチェック"""
        # RSSフィードから最新情報を取得
        # キーワードフィルタリング（RP、retinitis pigmentosa等）
```

## 3. HTML生成の具体的改善

### 3.1 テンプレートエンジンの実装
```python
# src/reporting/template_engine.py
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import markdown

class ReportTemplateEngine:
    """Jinja2ベースのレポート生成エンジン"""
    
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader('templates/'),
            autoescape=True
        )
        self.env.filters['markdown'] = self.markdown_filter
        self.env.filters['autolink'] = self.autolink_filter
        
    def markdown_filter(self, text):
        """MarkdownをHTMLに変換"""
        return markdown.markdown(text, extensions=['extra', 'tables'])
    
    def autolink_filter(self, text):
        """URLを自動的にリンクに変換"""
        import re
        url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
        return re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)
    
    def generate_report(self, data):
        """データからHTMLレポートを生成"""
        template = self.env.get_template('main_report.html')
        return template.render(
            data=data,
            generated_at=datetime.now(),
            version=self.get_version()
        )
```

### 3.2 レスポンシブテンプレート
```html
<!-- templates/main_report.html -->
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>網膜色素変性症治療予測レポート</title>
    <style>
        /* モバイル優先のレスポンシブデザイン */
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        @media (max-width: 768px) {
            table { font-size: 14px; }
            .chart-container { overflow-x: auto; }
        }
        
        /* 自動テーブルレスポンシブ */
        .table-responsive {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        /* プログレスバー */
        .update-progress {
            background: #f0f0f0;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-bar {
            background: #4CAF50;
            height: 100%;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>網膜色素変性症（RP）治療法予測</h1>
            <p class="update-info">最終更新: {{ generated_at|date('Y年m月d日 H:i') }}</p>
        </header>
        
        <!-- 自動生成される内容 -->
        {% for program in data.programs %}
        <div class="program-card">
            <h3>{{ program.name }}</h3>
            <div class="update-progress">
                <div class="progress-bar" style="width: {{ program.progress }}%"></div>
            </div>
            <p>{{ program.description|markdown|autolink|safe }}</p>
        </div>
        {% endfor %}
    </div>
</body>
</html>
```

## 4. 通知システムの実装

### 4.1 Slack通知
```python
# scripts/utils/notifier.py
import requests
import json

class SlackNotifier:
    """Slack通知を送信"""
    
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_update_summary(self, summary):
        """更新サマリーを送信"""
        payload = {
            "text": "🔄 RP治療情報の自動更新",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*更新日時:* {summary['date']}\n*モード:* {summary['mode']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*新規プログラム:* {summary['new_count']}\n*更新:* {summary['updated_count']}"
                    }
                }
            ]
        }
        
        requests.post(self.webhook_url, json=payload)
```

### 4.2 メール通知
```yaml
# GitHub Actions内でのメール通知
- name: Send email notification
  if: steps.check_changes.outputs.changes == 'true'
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: RP治療情報の自動更新 - ${{ env.UPDATE_DATE }}
    to: recipient@example.com
    from: RP Update Bot
    body: |
      自動更新が完了しました。
      
      更新内容：
      ${{ env.UPDATE_SUMMARY }}
      
      詳細はGitHubのPRを確認してください。
```

## 5. エラーハンドリングとモニタリング

### 5.1 ヘルスチェック
```python
# scripts/utils/health_check.py
class SystemHealthCheck:
    """システムの健全性をチェック"""
    
    def check_data_freshness(self):
        """データの鮮度をチェック"""
        checks = {
            'clinical_trials': self.check_file_age('data/raw/clinical_trials/', max_days=7),
            'knowledge_base': self.check_file_age('data/knowledge_base/', max_days=30),
            'reports': self.check_file_age('docs/', max_days=7)
        }
        return checks
    
    def check_api_availability(self):
        """外部APIの可用性をチェック"""
        apis = {
            'clinicaltrials': 'https://clinicaltrials.gov/api/v2/studies',
            'pubmed': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
        }
        # 各APIにテストリクエストを送信
```

### 5.2 エラー回復機能
```python
class ErrorRecovery:
    """エラーからの自動回復"""
    
    def with_retry(self, func, max_attempts=3, delay=5):
        """リトライ機能付き実行"""
        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(delay * (attempt + 1))
                else:
                    self.log_error(e)
                    raise
```

これらの実装により、手動作業を大幅に削減し、常に最新の情報を提供できるシステムを構築できます。