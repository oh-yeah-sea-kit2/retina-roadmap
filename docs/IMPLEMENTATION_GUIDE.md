# API実装ガイド

## 🎯 目的

このガイドでは、網膜色素変性症ロードマップのAPI化プロジェクトの実装手順を説明します。

---

## 📚 ドキュメント一覧

1. **[API設計提案書](API_REDESIGN_PROPOSAL.md)** - 全体設計とアーキテクチャ
2. **このガイド** - 実装手順とベストプラクティス
3. **[iOS SDK サンプル](ios-sdk-example/RetinaRoadmapAPI.swift)** - iOSアプリからの利用例

---

## ✅ 実装状況

### Phase 1: 基礎API構築 ✅ **完了**

- ✅ `/api/v1/programs.json` 生成
- ✅ `/api/v1/programs/{id}.json` 生成
- ✅ `/api/v1/timeline.json` 生成
- ✅ `/api/v1/statistics.json` 生成
- ✅ `/api/v1/meta.json` 生成
- ✅ GitHub Actions統合
- ✅ iOS SDK サンプルコード

### Phase 2: CMS統合 🔄 **次のステップ**

- ⏳ Strapi セットアップ
- ⏳ ニュース・FAQ管理
- ⏳ 自動デプロイ設定

### Phase 3: iOS アプリ開発 📱 **並行可能**

- ⏳ Swift SDK完成版
- ⏳ SwiftUI アプリUI
- ⏳ オフライン対応
- ⏳ プッシュ通知

---

## 🚀 クイックスタート

### 1. API生成

既存のデータからJSONAPIを生成します:

```bash
# API生成
python src/api_generator.py

# 生成されたファイルを確認
ls -la docs/public/api/v1/
```

**生成されるファイル:**
```
docs/public/api/v1/
├── programs.json          # 全治療プログラム一覧
├── programs/
│   ├── MCO-010.json      # 個別プログラム詳細
│   ├── OCU400.json
│   └── ...
├── timeline.json          # タイムライン予測
├── statistics.json        # 統計情報
└── meta.json             # APIメタ情報
```

### 2. ローカルで確認

```bash
# Python簡易サーバーで確認
cd docs/public
python -m http.server 8000

# ブラウザで確認
# http://localhost:8000/api/v1/meta.json
```

### 3. GitHub Pagesへデプロイ

```bash
# GitHub Actionsが自動実行
# または手動でコミット
git add docs/public/api/
git commit -m "Add JSON API endpoints"
git push origin main
```

**公開URL:**
```
https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/meta.json
```

---

## 📖 API使用例

### cURL

```bash
# 全プログラム取得
curl https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/programs.json

# 特定プログラム詳細
curl https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/programs/MCO-010.json

# タイムライン
curl https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/timeline.json
```

### JavaScript (Web)

```javascript
// 全プログラム取得
async function fetchPrograms() {
  const response = await fetch(
    'https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/programs.json'
  );
  const data = await response.json();

  console.log(`総プログラム数: ${data.metadata.total_count}`);

  data.programs.forEach(program => {
    console.log(`${program.name} (${program.company}): ${program.current_phase}`);
  });
}

// 特定プログラム詳細取得
async function fetchProgramDetail(programId) {
  const response = await fetch(
    `https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/programs/${programId}.json`
  );
  return await response.json();
}

// 使用例
fetchPrograms();

const mco010 = await fetchProgramDetail('MCO-010');
console.log(mco010);
```

### Swift (iOS)

詳細は [RetinaRoadmapAPI.swift](ios-sdk-example/RetinaRoadmapAPI.swift) を参照。

```swift
// プログラム一覧取得
let api = RetinaRoadmapAPI.shared
let programs = try await api.fetchPrograms()

// 特定プログラム詳細
let detail = try await api.fetchProgramDetail(id: "MCO-010")

// タイムライン予測
let timeline = try await api.fetchTimeline()
```

---

## 🔧 カスタマイズ

### 新しいエンドポイントの追加

`src/api_generator.py`に以下を追加:

```python
def generate_new_endpoint(self) -> None:
    """新しいエンドポイントを生成"""
    logger.info("Generating /api/v1/new_endpoint.json...")

    # データ構築
    data = {
        'metadata': {
            'generated_at': datetime.now().isoformat()
        },
        'content': {
            # あなたのデータ
        }
    }

    # ファイル書き込み
    self._write_json(self.api_dir / 'new_endpoint.json', data)
    logger.info("✓ Generated new_endpoint.json")

# generate_all()メソッドに追加
def generate_all(self) -> None:
    # ... 既存のコード
    self.generate_new_endpoint()  # 追加
```

### データ構造の拡張

`data/knowledge_base/clinical_programs.json`にフィールドを追加:

```json
{
  "programs": {
    "MCO-010": {
      // 既存フィールド
      "company": "Nanoscope Therapeutics",

      // 新しいフィールド
      "patient_population": {
        "target_size": 100000,
        "eligibility": "Advanced RP with some remaining vision"
      },
      "pricing": {
        "estimated_cost": "$850,000",
        "insurance_coverage": "TBD"
      }
    }
  }
}
```

対応するSwiftモデルも更新:

```swift
struct ClinicalProgram: Codable {
    // 既存フィールド
    let id: String
    let company: String

    // 新しいフィールド
    let patientPopulation: PatientPopulation?
    let pricing: Pricing?
}

struct PatientPopulation: Codable {
    let targetSize: Int
    let eligibility: String

    enum CodingKeys: String, CodingKey {
        case targetSize = "target_size"
        case eligibility
    }
}
```

---

## 🎨 WebサイトでAPIを使用

既存のHTMLページを動的化:

### Before (静的HTML)
```html
<div>
  <h2>MCO-010</h2>
  <p>Nanoscope Therapeutics</p>
  <p>Phase 3</p>
</div>
```

### After (動的JavaScript)
```html
<div id="programs-container"></div>

<script>
async function loadPrograms() {
  const response = await fetch('/api/v1/programs.json');
  const data = await response.json();

  const container = document.getElementById('programs-container');

  data.programs.forEach(program => {
    const div = document.createElement('div');
    div.innerHTML = `
      <h2>${program.name}</h2>
      <p>${program.company}</p>
      <p>${program.current_phase}</p>
      ${program.predicted_approval?.fda ?
        `<p>FDA予測: ${program.predicted_approval.fda}</p>` : ''}
    `;
    container.appendChild(div);
  });
}

loadPrograms();
</script>
```

---

## 🔄 Phase 2: CMS統合

### Strapiセットアップ

#### 1. Render.comでデプロイ

**無料プラン利用:**

1. [Render.com](https://render.com)にサインアップ
2. "New +" → "Web Service"
3. GitHub連携でStrapiリポジトリを選択
4. 設定:
   ```yaml
   Build Command: npm install && npm run build
   Start Command: npm start
   Environment: Node
   ```

#### 2. データベース設定

**PostgreSQL (Render.com無料プラン):**

1. "New +" → "PostgreSQL"
2. 無料プランを選択
3. Strapi環境変数に接続情報を設定:
   ```
   DATABASE_CLIENT=postgres
   DATABASE_HOST=<render-db-host>
   DATABASE_PORT=5432
   DATABASE_NAME=<db-name>
   DATABASE_USERNAME=<username>
   DATABASE_PASSWORD=<password>
   ```

#### 3. コレクション作成

**News (ニュース):**
```javascript
// Strapi管理画面で作成
{
  title: String (required),
  slug: UID (from title),
  date: Date (required),
  category: Enumeration ['regulatory', 'clinical', 'research', 'general'],
  summary: Text (required),
  content: RichText (Markdown),
  tags: JSON,
  related_programs: JSON,
  featured_image: Media,
  published: Boolean (default: false)
}
```

**FAQ:**
```javascript
{
  question: String (required),
  answer: RichText (Markdown, required),
  category: Enumeration ['treatment', 'clinical_trial', 'general', 'technical'],
  order: Number,
  related_programs: JSON,
  published: Boolean (default: false)
}
```

#### 4. GitHub Actions連携

`.github/workflows/cms-sync.yml`:

```yaml
name: Sync CMS Content

on:
  schedule:
    - cron: '0 */6 * * *'  # 6時間ごと
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Fetch Strapi Content
        run: |
          # ニュース取得
          curl https://your-strapi.onrender.com/api/news?populate=* \
            -H "Authorization: Bearer ${{ secrets.STRAPI_API_TOKEN }}" \
            > temp_news.json

          # FAQ取得
          curl https://your-strapi.onrender.com/api/faqs?populate=* \
            -H "Authorization: Bearer ${{ secrets.STRAPI_API_TOKEN }}" \
            > temp_faqs.json

      - name: Transform to API Format
        run: |
          python scripts/transform_cms_data.py

      - name: Commit Changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add docs/public/api/v1/news.json
          git add docs/public/api/v1/faq.json
          git commit -m "Update CMS content" || echo "No changes"
          git push
```

**データ変換スクリプト** (`scripts/transform_cms_data.py`):

```python
import json

def transform_strapi_news():
    """StrapiのニュースデータをAPI形式に変換"""
    with open('temp_news.json', 'r') as f:
        strapi_data = json.load(f)

    news = []
    for item in strapi_data.get('data', []):
        attrs = item['attributes']
        news.append({
            'id': f"news-{item['id']}",
            'title': attrs['title'],
            'date': attrs['date'],
            'category': attrs['category'],
            'summary': attrs['summary'],
            'content': attrs['content'],
            'tags': attrs.get('tags', []),
            'related_programs': attrs.get('related_programs', [])
        })

    api_data = {
        'metadata': {
            'total': len(news),
            'last_updated': datetime.now().isoformat()
        },
        'news': news
    }

    with open('docs/public/api/v1/news.json', 'w') as f:
        json.dump(api_data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    transform_strapi_news()
```

---

## 📱 Phase 3: iOS アプリ実装

### プロジェクト構成

```
RetinaRoadmapApp/
├── RetinaRoadmapApp/
│   ├── API/
│   │   └── RetinaRoadmapAPI.swift     # API クライアント
│   ├── Models/
│   │   ├── ClinicalProgram.swift
│   │   ├── Timeline.swift
│   │   └── Statistics.swift
│   ├── Views/
│   │   ├── ProgramsListView.swift
│   │   ├── ProgramDetailView.swift
│   │   ├── TimelineView.swift
│   │   └── NewsView.swift
│   └── RetinaRoadmapApp.swift
└── Tests/
```

### 主要機能

1. **治療プログラム一覧**
   - フェーズ別フィルタ
   - 優先度ソート
   - 検索機能

2. **タイムライン表示**
   - 地域別予測
   - グラフ表示
   - 確率分布

3. **ニュースフィード**
   - 最新情報表示
   - プッシュ通知

4. **オフライン対応**
   - ローカルキャッシュ
   - CoreData保存

### プッシュ通知設定

**重要な更新時に通知:**

```swift
import UserNotifications

func checkForUpdates() async {
    let api = RetinaRoadmapAPI.shared

    // 最新データ取得
    let programs = try? await api.fetchPrograms()

    // 前回のデータと比較
    let previousData = loadCachedData()

    // 重要な更新を検出
    if let newBLASubmission = detectNewBLASubmission(programs, previous: previousData) {
        // 通知送信
        sendNotification(
            title: "重要な進展",
            body: "\(newBLASubmission.name)がFDAへBLA申請を開始しました"
        )
    }
}

func sendNotification(title: String, body: String) {
    let content = UNMutableNotificationContent()
    content.title = title
    content.body = body
    content.sound = .default

    let request = UNNotificationRequest(
        identifier: UUID().uuidString,
        content: content,
        trigger: nil
    )

    UNUserNotificationCenter.current().add(request)
}
```

---

## 🔒 セキュリティ

### CORS設定

GitHub Pagesはデフォルトで全オリジン許可しています。
特定ドメインのみに制限する場合は、Cloudflare Workersを使用:

```javascript
// Cloudflare Workers
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const allowedOrigins = [
    'https://oh-yeah-sea-kit2.github.io',
    'https://your-ios-app.com'
  ]

  const origin = request.headers.get('Origin')

  if (!allowedOrigins.includes(origin)) {
    return new Response('Forbidden', { status: 403 })
  }

  const response = await fetch(request)
  const newResponse = new Response(response.body, response)

  newResponse.headers.set('Access-Control-Allow-Origin', origin)
  newResponse.headers.set('Access-Control-Allow-Methods', 'GET, OPTIONS')

  return newResponse
}
```

### レート制限

Cloudflare Workersで実装:

```javascript
const RATE_LIMIT = 100 // リクエスト/分
const requests = new Map()

async function handleRequest(request) {
  const ip = request.headers.get('CF-Connecting-IP')
  const now = Date.now()
  const windowMs = 60000 // 1分

  // レート制限チェック
  const userRequests = requests.get(ip) || []
  const recentRequests = userRequests.filter(time => now - time < windowMs)

  if (recentRequests.length >= RATE_LIMIT) {
    return new Response('Too Many Requests', { status: 429 })
  }

  recentRequests.push(now)
  requests.set(ip, recentRequests)

  // リクエスト処理
  return await fetch(request)
}
```

---

## 📊 モニタリング

### Google Analytics 4

```html
<!-- docs/public/index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');

  // API利用状況追跡
  gtag('event', 'api_request', {
    'endpoint': '/api/v1/programs.json',
    'user_agent': navigator.userAgent
  });
</script>
```

### エラー追跡

**Sentry統合:**

```javascript
// iOS
import Sentry

SentrySDK.start { options in
    options.dsn = "https://your-sentry-dsn"
    options.environment = "production"
}

// API エラーを記録
do {
    try await api.fetchPrograms()
} catch {
    SentrySDK.capture(error: error)
}
```

---

## 🧪 テスト

### APIテスト

```python
# tests/test_api_generator.py
import pytest
from src.api_generator import APIGenerator

def test_generate_programs_api():
    """プログラムAPI生成テスト"""
    generator = APIGenerator()
    generator.generate_all()

    # ファイルが生成されているか確認
    assert (generator.api_dir / 'programs.json').exists()
    assert (generator.api_dir / 'timeline.json').exists()

    # JSONが正しいか確認
    with open(generator.api_dir / 'programs.json', 'r') as f:
        data = json.load(f)
        assert 'metadata' in data
        assert 'programs' in data
        assert len(data['programs']) > 0
```

### iOS SDKテスト

```swift
// Tests/RetinaRoadmapAPITests.swift
import XCTest
@testable import RetinaRoadmapApp

class RetinaRoadmapAPITests: XCTestCase {

    func testFetchPrograms() async throws {
        let api = RetinaRoadmapAPI.shared
        let programs = try await api.fetchPrograms()

        XCTAssertGreaterThan(programs.count, 0)
        XCTAssertNotNil(programs.first?.company)
    }

    func testFetchProgramDetail() async throws {
        let api = RetinaRoadmapAPI.shared
        let detail = try await api.fetchProgramDetail(id: "MCO-010")

        XCTAssertEqual(detail.id, "MCO-010")
        XCTAssertEqual(detail.company, "Nanoscope Therapeutics")
    }
}
```

---

## 🚀 デプロイ

### 本番環境チェックリスト

- [ ] API生成が正常に動作
- [ ] GitHub Actionsが成功
- [ ] 全エンドポイントがアクセス可能
- [ ] iOS SDKでデータ取得可能
- [ ] CORS設定確認
- [ ] ドキュメント更新
- [ ] テスト実行
- [ ] パフォーマンス確認

### デプロイ手順

```bash
# 1. 全てのテストを実行
pytest tests/

# 2. API生成
python src/api_generator.py

# 3. ローカル確認
cd docs/public && python -m http.server 8000

# 4. コミット
git add .
git commit -m "Add JSON API endpoints"

# 5. プッシュ (GitHub Actionsが自動デプロイ)
git push origin main

# 6. デプロイ確認
curl https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/meta.json
```

---

## 📚 参考資料

- [API設計提案書](API_REDESIGN_PROPOSAL.md)
- [GitHub Pages公式ドキュメント](https://docs.github.com/pages)
- [Strapi公式ドキュメント](https://docs.strapi.io)
- [SwiftUI公式チュートリアル](https://developer.apple.com/tutorials/swiftui)

---

## 💬 サポート

質問や問題がある場合:

1. [GitHub Issues](https://github.com/oh-yeah-sea-kit2/retina-roadmap/issues)
2. [GitHub Discussions](https://github.com/oh-yeah-sea-kit2/retina-roadmap/discussions)

---

**作成日**: 2025-11-18
**バージョン**: 1.0
**担当**: Claude (Sonnet 4.5)
