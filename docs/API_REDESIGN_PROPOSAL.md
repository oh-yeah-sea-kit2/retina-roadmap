# 網膜色素変性症サイト API再設計提案書

## 📋 目次
1. [現状分析](#現状分析)
2. [設計アプローチの比較](#設計アプローチの比較)
3. [推奨設計: ハイブリッドアプローチ](#推奨設計-ハイブリッドアプローチ)
4. [API エンドポイント設計](#api-エンドポイント設計)
5. [データベーススキーマ](#データベーススキーマ)
6. [CMS選択肢](#cms選択肢)
7. [実装ロードマップ](#実装ロードマップ)

---

## 現状分析

### 既存の構成
```
現在: データ → Python処理 → 静的HTML → GitHub Pages
課題:
  - HTMLに情報が埋め込まれている
  - アプリからの再利用が困難
  - 更新のたびにHTMLを再生成
```

### データ資産
- ✅ `clinical_programs.json` - 15+の治療プログラム情報
- ✅ `parameters.yaml` - シミュレーションパラメータ
- ✅ 臨床試験データ (129試験)
- ✅ 学術論文データ (826論文)
- ✅ 予測シミュレーション結果

---

## 設計アプローチの比較

### アプローチ1: 完全動的API (FastAPI + PostgreSQL)

```
構成:
  Web/App → FastAPI → PostgreSQL
  管理画面: Admin Dashboard (React/Vue)
```

**メリット:**
- ✅ リアルタイム更新
- ✅ 高度な検索・フィルタリング
- ✅ ユーザー認証・権限管理
- ✅ アクセス分析

**デメリット:**
- ❌ サーバー維持コスト (月額$20-100)
- ❌ インフラ管理の複雑さ
- ❌ 既存のGitHub Pagesワークフローを捨てる
- ❌ スケーリング対応が必要

**適している場合:**
- ユーザー投稿機能が必要
- リアルタイム更新が必須
- 複雑な検索・分析機能が必要

---

### アプローチ2: 完全静的API (JSON API + CDN)

```
構成:
  データ → Python処理 → JSON API + HTML → GitHub Pages/Netlify
  Web/App → CDN → 静的JSON
```

**メリット:**
- ✅ **無料** (GitHub Pages)
- ✅ 超高速 (CDN配信)
- ✅ スケーラブル (無制限)
- ✅ シンプルな構成
- ✅ 既存のCI/CDを活用

**デメリット:**
- ❌ リアルタイム更新不可
- ❌ 複雑な検索はクライアント側で実装
- ❌ 更新にはGitプッシュが必要

**適している場合:**
- 更新頻度が低い (日次〜週次)
- 予算重視
- シンプルな構成を維持したい

---

### アプローチ3: ハイブリッド (推奨) 🌟

```
構成:
  データ → Python処理 → JSON API + HTML → GitHub Pages
  ┌─────────────────┐
  │ 頻繁に更新される│ → Headless CMS (月額$0-50)
  │ コンテンツのみ  │
  └─────────────────┘
  Web/App → CDN (静的JSON) + CMS API
```

**メリット:**
- ✅ **ほぼ無料** (CMSの無料プランで十分)
- ✅ 静的データは超高速配信
- ✅ 動的コンテンツはCMSで管理
- ✅ 既存ワークフローを活用
- ✅ 将来的な拡張性

**デメリット:**
- 🔶 2つのデータソース管理

**適している場合:**
- 本プロジェクトに最適 👈

---

## 推奨設計: ハイブリッドアプローチ

### アーキテクチャ図

```
┌─────────────────────────────────────────────────────────┐
│                     データソース層                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐    ┌──────────────────┐         │
│  │ 静的データ        │    │ Headless CMS     │         │
│  │ (GitHub)         │    │ (Strapi/Payload) │         │
│  ├──────────────────┤    ├──────────────────┤         │
│  │• 臨床試験データ   │    │• ニュース記事    │         │
│  │• 治療プログラム   │    │• FAQ             │         │
│  │• シミュレーション │    │• 用語集          │         │
│  │• 学術論文        │    │• ブログ記事       │         │
│  └──────────────────┘    └──────────────────┘         │
│           │                        │                   │
│           ▼                        ▼                   │
├─────────────────────────────────────────────────────────┤
│                     API生成層                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────────────────────────────────┐            │
│  │ Python ビルドパイプライン                │            │
│  │ (GitHub Actions)                      │            │
│  ├────────────────────────────────────────┤            │
│  │ 1. データ収集・処理                     │            │
│  │ 2. JSON API生成                        │            │
│  │ 3. HTML生成                            │            │
│  │ 4. GitHub Pagesデプロイ                │            │
│  └────────────────────────────────────────┘            │
│           │                                             │
│           ▼                                             │
├─────────────────────────────────────────────────────────┤
│                  配信層 (GitHub Pages)                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  /api/v1/                                              │
│  ├── programs.json          ← 全治療プログラム         │
│  ├── programs/{id}.json     ← 個別プログラム詳細       │
│  ├── trials.json            ← 臨床試験一覧             │
│  ├── timeline.json          ← 予測タイムライン         │
│  ├── statistics.json        ← 統計データ               │
│  ├── papers.json            ← 学術論文リスト           │
│  ├── news.json              ← CMSから生成              │
│  └── meta.json              ← APIメタ情報              │
│                                                         │
└─────────────────────────────────────────────────────────┘
           │                        │
           ▼                        ▼
    ┌──────────┐           ┌──────────────┐
    │ Webサイト │           │ iOSアプリ    │
    └──────────┘           └──────────────┘
```

---

## API エンドポイント設計

### 基本URL
```
https://oh-yeah-sea-kit2.github.io/retina-roadmap/api/v1/
```

### エンドポイント一覧

#### 1. 治療プログラム関連

```http
GET /api/v1/programs.json
```
**説明**: 全治療プログラム一覧
**レスポンス例**:
```json
{
  "metadata": {
    "last_updated": "2025-11-07T00:00:00Z",
    "total_count": 15,
    "api_version": "1.0.0"
  },
  "programs": [
    {
      "id": "MCO-010",
      "name": "MCO-010",
      "company": "Nanoscope Therapeutics",
      "current_phase": "Phase 3",
      "status": "BLA submission initiated",
      "modality": "Gene therapy (optogenetics)",
      "target": "Gene-agnostic",
      "predicted_approval": {
        "fda": "2026-Q1",
        "japan": "2032-Q2",
        "europe": "2027-Q3"
      },
      "summary": "遺伝子非依存型の光遺伝学治療",
      "priority": 1
    }
  ]
}
```

```http
GET /api/v1/programs/{program_id}.json
```
**説明**: 個別プログラムの詳細情報
**例**: `/api/v1/programs/MCO-010.json`
**レスポンス例**:
```json
{
  "id": "MCO-010",
  "company": "Nanoscope Therapeutics",
  "current_phase": "Phase 3",
  "status": "BLA submission initiated",
  "key_dates": {
    "phase3_start": "2021-06-01",
    "phase3_completion": "2024-03-01",
    "bla_submission_start": "2025-07-14",
    "expected_bla_completion": "2026-02-01"
  },
  "trial_ids": ["NCT04945772"],
  "modality": "Gene therapy (optogenetics)",
  "target": "Gene-agnostic",
  "regulatory": [
    "FDA Fast Track",
    "Orphan Drug Designation"
  ],
  "recent_updates": [
    {
      "date": "2025-11-07",
      "event": "5-year safety data and 3-year efficacy data show sustained vision gains",
      "source": "Web Search",
      "importance": "high"
    }
  ],
  "clinical_data": {
    "efficacy": {
      "endpoint": "Visual acuity improvement",
      "result": "Statistically significant",
      "p_value": "<0.05"
    },
    "safety": {
      "serious_adverse_events": 0,
      "follow_up_years": 5
    }
  },
  "notes": "First gene-agnostic gene therapy for RP...",
  "links": {
    "company_website": "https://nanostherapeutics.com",
    "clinicaltrials_gov": "https://clinicaltrials.gov/study/NCT04945772"
  }
}
```

#### 2. タイムライン・予測関連

```http
GET /api/v1/timeline.json
```
**説明**: 治療承認予測タイムライン
**レスポンス例**:
```json
{
  "metadata": {
    "simulation_date": "2025-11-07",
    "method": "Monte Carlo (10,000 iterations)",
    "confidence_interval": 0.90
  },
  "predictions": {
    "first_approval": {
      "program": "MCO-010",
      "median_date": "2026-Q1",
      "confidence_90": {
        "lower": "2025-Q4",
        "upper": "2027-Q2"
      },
      "probability_by_year": {
        "2025": 0.05,
        "2026": 0.65,
        "2027": 0.25,
        "2028": 0.05
      }
    },
    "by_region": {
      "FDA": {
        "median_approval_year": 2026,
        "programs": ["MCO-010", "OCU400"]
      },
      "Japan": {
        "median_approval_year": 2032,
        "delay_years": 6,
        "programs": ["MCO-010"]
      },
      "Europe": {
        "median_approval_year": 2027,
        "delay_years": 1,
        "programs": ["MCO-010", "AGTC-501"]
      }
    }
  }
}
```

```http
GET /api/v1/timeline/{region}.json
```
**説明**: 地域別タイムライン
**例**: `/api/v1/timeline/japan.json`

#### 3. 臨床試験関連

```http
GET /api/v1/trials.json
```
**説明**: 臨床試験一覧
**クエリパラメータ** (将来的にクライアント側フィルタリング用):
- `phase`: Phase 1, Phase 2, Phase 3
- `status`: Active, Completed, Recruiting
- `modality`: Gene therapy, Cell therapy, etc.

**レスポンス例**:
```json
{
  "metadata": {
    "total_trials": 129,
    "active_trials": 54,
    "last_updated": "2025-11-07"
  },
  "trials": [
    {
      "nct_id": "NCT04945772",
      "title": "RESTORE Phase 3 Study",
      "phase": "Phase 3",
      "status": "Completed",
      "enrollment": 42,
      "sponsor": "Nanoscope Therapeutics",
      "program_id": "MCO-010",
      "start_date": "2021-06",
      "completion_date": "2024-03",
      "primary_endpoint": "Visual acuity improvement",
      "results_available": true
    }
  ]
}
```

#### 4. 統計・分析関連

```http
GET /api/v1/statistics.json
```
**説明**: プロジェクト全体の統計情報
**レスポンス例**:
```json
{
  "overview": {
    "total_programs": 15,
    "active_programs": 12,
    "phase_distribution": {
      "Phase 1": 3,
      "Phase 2": 4,
      "Phase 3": 5
    }
  },
  "success_rates": {
    "phase1": 0.867,
    "phase2": 0.784,
    "phase3": 0.714
  },
  "modality_breakdown": {
    "Gene therapy": 10,
    "Cell therapy": 3,
    "RNA therapy": 2
  },
  "regional_status": {
    "fda_approved": 0,
    "fda_under_review": 1,
    "japan_approved": 0
  }
}
```

#### 5. 学術論文関連

```http
GET /api/v1/papers.json
```
**説明**: 学術論文リスト
**レスポンス例**:
```json
{
  "metadata": {
    "total_papers": 826,
    "date_range": {
      "start": "1993-01-01",
      "end": "2025-11-07"
    }
  },
  "papers": [
    {
      "pmid": "12345678",
      "title": "Gene therapy for retinitis pigmentosa",
      "authors": ["Smith J", "Doe A"],
      "journal": "Nature Medicine",
      "year": 2024,
      "doi": "10.1038/...",
      "abstract": "...",
      "related_programs": ["MCO-010"]
    }
  ],
  "trends": {
    "publications_by_year": {
      "2020": 45,
      "2021": 52,
      "2022": 68,
      "2023": 89,
      "2024": 102
    }
  }
}
```

#### 6. コンテンツ関連 (CMSから配信)

```http
GET /api/v1/news.json
```
**説明**: ニュース記事一覧
**レスポンス例**:
```json
{
  "news": [
    {
      "id": "news-001",
      "title": "MCO-010がBLA申請を開始",
      "date": "2025-07-14",
      "category": "regulatory",
      "summary": "Nanoscope TherapeuticsがFDAへBLA申請を開始...",
      "content": "...",
      "tags": ["MCO-010", "FDA", "BLA"],
      "related_programs": ["MCO-010"]
    }
  ]
}
```

```http
GET /api/v1/faq.json
```
**説明**: よくある質問

```http
GET /api/v1/glossary.json
```
**説明**: 医学用語集

#### 7. メタ情報

```http
GET /api/v1/meta.json
```
**説明**: API全体のメタ情報
**レスポンス例**:
```json
{
  "api_version": "1.0.0",
  "last_updated": "2025-11-07T05:45:18Z",
  "endpoints": [
    "/programs.json",
    "/programs/{id}.json",
    "/timeline.json",
    "/trials.json",
    "/statistics.json",
    "/papers.json",
    "/news.json",
    "/faq.json",
    "/glossary.json"
  ],
  "data_sources": {
    "clinical_trials": "ClinicalTrials.gov",
    "papers": "PubMed",
    "programs": "Manual curation + Web search"
  },
  "update_frequency": {
    "programs": "weekly",
    "trials": "weekly",
    "papers": "monthly",
    "news": "as_needed"
  }
}
```

---

## データベーススキーマ

### CMSデータ構造 (Headless CMS用)

#### コレクション1: News (ニュース)
```typescript
interface News {
  id: string;
  title: string;
  slug: string;
  date: Date;
  category: 'regulatory' | 'clinical' | 'research' | 'general';
  summary: string;
  content: string; // Markdown
  tags: string[];
  related_programs: string[]; // program IDs
  featured_image?: string;
  author?: string;
  published: boolean;
  created_at: Date;
  updated_at: Date;
}
```

#### コレクション2: FAQ
```typescript
interface FAQ {
  id: string;
  question: string;
  answer: string; // Markdown
  category: 'treatment' | 'clinical_trial' | 'general' | 'technical';
  order: number;
  related_programs?: string[];
  published: boolean;
  created_at: Date;
  updated_at: Date;
}
```

#### コレクション3: Glossary (用語集)
```typescript
interface GlossaryTerm {
  id: string;
  term: string;
  reading?: string; // 読み仮名
  definition: string; // Markdown
  category: 'medical' | 'regulatory' | 'scientific';
  related_terms?: string[];
  published: boolean;
}
```

### 静的データ構造 (JSON)

既存の`clinical_programs.json`を拡張:

```typescript
interface ClinicalProgram {
  id: string;
  company: string;
  current_phase: string;
  status: string;
  key_dates: {
    phase1_start?: string;
    phase2_start?: string;
    phase3_start?: string;
    bla_submission_start?: string;
    expected_approval?: string;
  };
  trial_ids: string[];
  modality: string;
  target: string;
  regulatory: string[];
  recent_updates: Update[];
  notes: string;

  // 追加フィールド
  predicted_approval?: {
    fda?: string;
    japan?: string;
    europe?: string;
  };
  clinical_data?: {
    efficacy?: any;
    safety?: any;
  };
  links?: {
    company_website?: string;
    clinicaltrials_gov?: string;
  };
  priority?: number; // 1-5 (1が最重要)
}

interface Update {
  date: string;
  event: string;
  source: string;
  importance?: 'low' | 'medium' | 'high';
}
```

---

## CMS選択肢

### 推奨: Strapi (Headless CMS) 🌟

**理由:**
- ✅ 完全無料 (セルフホスト)
- ✅ REST & GraphQL API自動生成
- ✅ 日本語対応
- ✅ 使いやすい管理画面
- ✅ GitHub Actionsと連携可能
- ✅ Markdown対応

**構成:**
```
Strapi (Render.com無料プラン) → REST API
     ↓
GitHub Actions (定期実行)
     ↓
JSON生成 → GitHub Pages
```

### 代替案1: Payload CMS

**理由:**
- ✅ モダンなUI
- ✅ TypeScript製
- ✅ 開発者フレンドリー

**デメリット:**
- 🔶 Strapiより新しい (安定性)

### 代替案2: 完全Gitベース (Markdown + Front Matter)

```
docs/content/news/
├── 2025-11-07-mco010-bla.md
├── 2025-10-22-ocu400-update.md
└── ...
```

**メリット:**
- ✅ 完全無料
- ✅ Git管理
- ✅ シンプル

**デメリット:**
- ❌ 非技術者には編集が難しい

---

## 実装ロードマップ

### Phase 1: 基礎API構築 (1-2週間)

**目標**: 既存データをJSON APIとして公開

**タスク:**
1. ✅ `/api/v1/programs.json` 生成スクリプト作成
2. ✅ `/api/v1/timeline.json` 生成
3. ✅ `/api/v1/statistics.json` 生成
4. ✅ GitHub Actions更新 (JSON生成を追加)
5. ✅ API仕様書作成 (OpenAPI/Swagger)

**成果物:**
- 基本的なJSON API
- iOSアプリが利用可能

---

### Phase 2: CMS統合 (2-3週間)

**目標**: ニュース・FAQをCMSで管理

**タスク:**
1. ✅ Strapi セットアップ (Render.com)
2. ✅ コレクション設計 (News, FAQ, Glossary)
3. ✅ GitHub Actions連携
   - Strapi API → JSON取得 → GitHub Pages配信
4. ✅ 管理画面カスタマイズ (日本語化)

**成果物:**
- ニュース・FAQの簡単更新
- `/api/v1/news.json` 配信

---

### Phase 3: iOS アプリ対応 (並行開発可能)

**目標**: iOS アプリからAPIを利用

**タスク:**
1. ✅ Swift SDK作成 (APIクライアント)
2. ✅ データモデル定義
3. ✅ オフライン対応 (ローカルキャッシュ)
4. ✅ プッシュ通知 (新情報更新時)

**iOS アプリ機能例:**
- 治療プログラム一覧
- タイムライン表示
- ニュースフィード
- FAQ検索
- 論文ブラウザ

---

### Phase 4: 高度な機能 (将来的)

**タスク:**
1. ✅ ユーザー認証 (患者レジストリ連携)
2. ✅ パーソナライズ (遺伝子型別情報)
3. ✅ 通知機能 (臨床試験募集アラート)
4. ✅ 多言語対応 (英語・中国語)
5. ✅ 検索機能強化 (Algolia統合)

---

## コスト試算

### 推奨構成 (ハイブリッド)

| 項目 | サービス | 月額 | 年額 |
|------|----------|------|------|
| 静的ホスティング | GitHub Pages | $0 | $0 |
| CMS | Strapi (Render.com) | $0 | $0 |
| データベース | Render.com PostgreSQL | $0 | $0 |
| CDN | GitHub Pages | $0 | $0 |
| ドメイン | 既存 | $0 | $0 |
| **合計** | | **$0** | **$0** |

※ 無料枠で十分運用可能

### 将来的なアップグレード (オプション)

| 項目 | サービス | 月額 |
|------|----------|------|
| プロフェッショナルCMS | Strapi Cloud | $29 |
| 高速CDN | Cloudflare Pro | $20 |
| 検索API | Algolia | $0-49 |
| 分析 | Google Analytics | $0 |

---

## 技術スタック

### バックエンド (ビルド)
- **言語**: Python 3.11
- **フレームワーク**: なし (スタンドアロンスクリプト)
- **データ処理**: pandas, NumPy
- **JSON生成**: json, pyyaml

### CMS
- **Platform**: Strapi v4
- **Database**: PostgreSQL (Render.com)
- **API**: REST + GraphQL

### フロントエンド (既存)
- **Web**: 静的HTML + vanilla JS
- **iOS**: Swift + SwiftUI (新規)

### インフラ
- **Hosting**: GitHub Pages
- **CI/CD**: GitHub Actions
- **CDN**: GitHub Pages CDN

---

## セキュリティ考慮事項

1. **API Rate Limiting**
   - GitHub Pagesは静的配信なので問題なし
   - 将来的にCDN追加でDDoS対策

2. **データバリデーション**
   - CMSからのデータは取り込み時にバリデーション

3. **CORS設定**
   - GitHub Pagesは全オリジン許可
   - 特定ドメインのみ許可する場合はCloudflare Workers使用

4. **認証 (将来的)**
   - OAuth 2.0 (Google/Apple Sign-in)
   - JWT トークン

---

## まとめ

### 推奨アプローチ: ハイブリッド

**理由:**
1. ✅ **コストゼロ** - 既存のGitHub Pagesを活用
2. ✅ **シンプル** - 既存のCI/CDパイプラインを維持
3. ✅ **拡張性** - CMSで動的コンテンツ管理
4. ✅ **iOSアプリ対応** - JSON APIで簡単に連携
5. ✅ **定期更新容易** - CMS管理画面で非技術者も編集可能

### 次のステップ

1. **Phase 1 実装開始**: JSON API生成スクリプト作成
2. **API仕様確定**: エンドポイント詳細設計
3. **CMS選定**: Strapi vs Gitベース
4. **iOS開発着手**: Swift SDKプロトタイプ

---

**作成日**: 2025-11-18
**バージョン**: 1.0
**担当**: Claude (Sonnet 4.5)
