# 網膜色素変性症ページ API化・データベース設計提案（Next.js版）

作成日: 2025-11-18
更新日: 2025-11-18（Next.js版に改訂）

## 📋 目次

1. [現状分析](#現状分析)
2. [Next.js採用の理由](#nextjs採用の理由)
3. [提案アーキテクチャ](#提案アーキテクチャ)
4. [データベース設計](#データベース設計)
5. [API Routes設計](#api-routes設計)
6. [フロントエンド設計](#フロントエンド設計)
7. [データ更新フロー](#データ更新フロー)
8. [iOSアプリ統合](#iOSアプリ統合)
9. [実装ロードマップ](#実装ロードマップ)

---

## 現状分析

### 現在のデータ構造

```
data/
├── knowledge_base/
│   ├── clinical_programs.json      # 14プログラムの詳細情報
│   ├── update_history.json         # 更新履歴
│   └── last_check.json            # 最終チェック日時
├── raw/
│   ├── clinical_trials/           # ClinicalTrials.gov生データ
│   └── literature/                # PubMed論文データ
└── processed/
    ├── clinical_trials.parquet    # 処理済み臨床試験データ
    ├── papers.csv                 # 処理済み論文データ
    └── simulation_params.json     # シミュレーションパラメータ
```

### 現在の公開ページ（18ページ）

```
docs/public/
├── index.html                          # メインページ
├── current_status_facts.html           # 現状の事実
├── ai_predictions.html                 # AI予測
├── patient_guide.html                  # 患者ガイド
├── medical_info.html                   # 医療情報
├── for_doctor_checklist.html           # 医師向けチェックリスト
├── regional_approval_timeline.html     # 地域別承認タイムライン
├── detailed_analysis.html              # 詳細分析
└── ... (その他10ページ)
```

### 現在の課題

1. **データの重複**: JSON、Parquet、CSVに同じデータが散在
2. **更新の手動性**: Web検索 → 手動更新 → レポート再生成
3. **静的HTML**: 動的なフィルタリングや検索が不可能
4. **API不在**: 外部アプリ（iOS等）からのデータアクセス不可
5. **バージョン管理**: データ変更履歴の追跡が困難
6. **デプロイの複雑さ**: GitHub Pages静的ホスティングのみ

---

## Next.js採用の理由

### FastAPI vs Next.js 比較表

| 項目 | FastAPI (Python) | Next.js (TypeScript) | 判定 |
|------|------------------|----------------------|------|
| **デプロイの簡単さ** | Railway/Render必要 | Vercel自動デプロイ | ✅ Next.js |
| **既存コード活用** | Python処理コード活用可 | TypeScript書き直し必要 | FastAPI |
| **フロント統合** | 別途React等必要 | App Router統合済み | ✅ Next.js |
| **静的ページ移行** | 困難 | 段階的移行容易 | ✅ Next.js |
| **API Routes** | 要実装 | 組み込み済み | ✅ Next.js |
| **型安全性** | Pydantic | TypeScript | ✅ Next.js |
| **iOSアプリ連携** | REST API | REST API | 同等 |
| **無料枠** | 制限あり | Vercel Hobby充実 | ✅ Next.js |
| **データ更新** | GitHub Actions | Vercel Cron Jobs | ✅ Next.js |
| **学習コスト** | 低（既存知識） | 中程度 | FastAPI |

### Next.js採用のメリット

1. **Vercelデプロイが超簡単**: GitHub連携だけで自動デプロイ、プレビューURL自動生成
2. **既存HTMLの段階的移行**: 静的ページから徐々に動的化可能
3. **ISR（Incremental Static Regeneration）**: 高速表示とデータ更新を両立
4. **App Router**: サーバーコンポーネントでSEO最適化
5. **API Routes**: `/api/*` でREST APIを簡単に構築
6. **TypeScript**: 型安全でiOSアプリとの連携も楽
7. **Vercel Cron Jobs**: 定期的なデータ更新を簡単に設定
8. **エッジファンクション**: グローバル配信で高速レスポンス

### Pythonコードの扱い

既存のPythonコード（データ取得、シミュレーション）は引き続き活用：

```
retina-roadmap/
├── python-scripts/          # 既存Pythonスクリプト（維持）
│   ├── fetch_trials.py
│   ├── fetch_papers.py
│   └── timeline_sim.py
├── app/                     # Next.js App Router
│   ├── api/                # API Routes
│   └── (pages)/            # ページコンポーネント
└── lib/                     # TypeScript共通ロジック
    └── db/                 # データベースアクセス
```

**運用フロー:**
1. PythonスクリプトでCronJobs実行（週次）
2. 結果をDBに保存
3. Next.jsがDBから取得して表示

---

## 提案アーキテクチャ

### システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                     クライアント層                              │
├─────────────┬──────────────┬───────────────┬────────────────┤
│  Webブラウザ   │  iOSアプリ    │  Androidアプリ │  管理者         │
└─────────────┴──────────────┴───────────────┴────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Next.js App     │
                    │   (Vercel)        │
                    └─────────┬─────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
        ┌───────▼──────┐ ┌───▼────┐ ┌─────▼─────┐
        │ Server       │ │API     │ │Static     │
        │ Components   │ │Routes  │ │Pages (ISR)│
        └───────┬──────┘ └───┬────┘ └─────┬─────┘
                │            │            │
        ┌───────▼────────────▼────────────▼─────┐
        │       Vercel Postgres / Supabase      │
        │       (PostgreSQL互換)                 │
        └───────────────┬───────────────────────┘
                        │
        ┌───────────────▼───────────────┐
        │  Vercel Cron Jobs             │
        │  ├─ fetch_latest_data.py      │
        │  ├─ run_simulations.py        │
        │  └─ update_database.py        │
        └───────────────────────────────┘
```

### 技術スタック

| 層 | 技術 | 理由 |
|---|------|------|
| **フレームワーク** | Next.js 14+ (App Router) | SSG/ISR/SSR統合、API Routes |
| **言語** | TypeScript | 型安全性、iOSアプリと型共有 |
| **データベース** | Vercel Postgres / Supabase | PostgreSQL互換、無料枠あり |
| **ORM** | Drizzle ORM | 軽量、TypeScript完全対応 |
| **デプロイ** | Vercel | 自動デプロイ、プレビューURL |
| **スタイリング** | Tailwind CSS | ユーティリティファースト |
| **データ取得** | Server Actions / API Routes | RSC対応 |
| **認証** | NextAuth.js | Google/GitHub OAuth |
| **Python実行** | Vercel Cron Jobs | 定期実行 |
| **モニタリング** | Vercel Analytics | パフォーマンス監視 |

---

## データベース設計

### Drizzle ORM スキーマ定義

```typescript
// lib/db/schema.ts
import { pgTable, serial, varchar, text, timestamp, integer, jsonb, boolean, date } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

// 1. clinical_programs テーブル
export const clinicalPrograms = pgTable('clinical_programs', {
  id: serial('id').primaryKey(),
  programId: varchar('program_id', { length: 50 }).unique().notNull(),
  name: varchar('name', { length: 200 }).notNull(),
  company: varchar('company', { length: 200 }).notNull(),
  currentPhase: varchar('current_phase', { length: 50 }),
  status: varchar('status', { length: 100 }),
  modality: varchar('modality', { length: 100 }),
  target: varchar('target', { length: 200 }),
  notes: text('notes'),

  // JSON列
  keyDates: jsonb('key_dates').$type<Record<string, string>>(),
  regulatory: jsonb('regulatory').$type<string[]>(),
  trialIds: jsonb('trial_ids').$type<string[]>(),

  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

// 2. program_updates テーブル
export const programUpdates = pgTable('program_updates', {
  id: serial('id').primaryKey(),
  programId: varchar('program_id', { length: 50 }).references(() => clinicalPrograms.programId),
  updateDate: date('update_date').notNull(),
  eventType: varchar('event_type', { length: 50 }),
  event: text('event').notNull(),
  source: varchar('source', { length: 200 }),
  importanceScore: integer('importance_score'),
  createdAt: timestamp('created_at').defaultNow(),
});

// 3. clinical_trials テーブル
export const clinicalTrials = pgTable('clinical_trials', {
  id: serial('id').primaryKey(),
  nctId: varchar('nct_id', { length: 20 }).unique().notNull(),
  programId: varchar('program_id', { length: 50 }).references(() => clinicalPrograms.programId),
  title: text('title'),
  status: varchar('status', { length: 50 }),
  phase: varchar('phase', { length: 50 }),
  enrollment: integer('enrollment'),
  startDate: date('start_date'),
  completionDate: date('completion_date'),
  primaryOutcome: text('primary_outcome'),
  sponsor: varchar('sponsor', { length: 200 }),
  location: varchar('location', { length: 500 }),

  // JSON列
  conditions: jsonb('conditions').$type<string[]>(),
  interventions: jsonb('interventions').$type<any[]>(),
  rawData: jsonb('raw_data'),

  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

// 4. simulation_results テーブル
export const simulationResults = pgTable('simulation_results', {
  id: serial('id').primaryKey(),
  programId: varchar('program_id', { length: 50 }).references(() => clinicalPrograms.programId),
  simulationDate: date('simulation_date').notNull(),

  // 予測結果
  fdaApprovalMedian: integer('fda_approval_median'),
  fdaApprovalCiLow: integer('fda_approval_ci_low'),
  fdaApprovalCiHigh: integer('fda_approval_ci_high'),
  japanApprovalMedian: integer('japan_approval_median'),
  japanApprovalCiLow: integer('japan_approval_ci_low'),
  japanApprovalCiHigh: integer('japan_approval_ci_high'),

  // パラメータ
  successProbability: integer('success_probability'), // 0-1000 (0.001精度)
  phaseDurations: jsonb('phase_durations'),
  confidenceLevel: varchar('confidence_level', { length: 20 }),

  createdAt: timestamp('created_at').defaultNow(),
});

// 5. content_pages テーブル (CMS)
export const contentPages = pgTable('content_pages', {
  id: serial('id').primaryKey(),
  slug: varchar('slug', { length: 100 }).unique().notNull(),
  title: varchar('title', { length: 200 }).notNull(),
  content: text('content'), // Markdown
  pageType: varchar('page_type', { length: 50 }),
  targetAudience: varchar('target_audience', { length: 50 }),
  metaDescription: text('meta_description'),
  published: boolean('published').default(false),

  // バージョン管理
  version: integer('version').default(1),
  createdBy: varchar('created_by', { length: 100 }),
  updatedBy: varchar('updated_by', { length: 100 }),

  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

// リレーション定義
export const programsRelations = relations(clinicalPrograms, ({ many }) => ({
  updates: many(programUpdates),
  trials: many(clinicalTrials),
  predictions: many(simulationResults),
}));

export const updatesRelations = relations(programUpdates, ({ one }) => ({
  program: one(clinicalPrograms, {
    fields: [programUpdates.programId],
    references: [clinicalPrograms.programId],
  }),
}));
```

### データベース接続設定

```typescript
// lib/db/index.ts
import { drizzle } from 'drizzle-orm/vercel-postgres';
import { sql } from '@vercel/postgres';
import * as schema from './schema';

export const db = drizzle(sql, { schema });
```

### 環境変数設定

```bash
# .env.local
POSTGRES_URL="postgres://..."          # Vercel Postgresから取得
POSTGRES_PRISMA_URL="postgres://..."   # Prisma用
POSTGRES_URL_NON_POOLING="postgres://..."

# または Supabase
DATABASE_URL="postgresql://..."
```

---

## API Routes設計

### エンドポイント一覧

```
app/api/
├── programs/
│   ├── route.ts                    # GET /api/programs (全プログラム)
│   ├── [id]/
│   │   ├── route.ts               # GET /api/programs/[id]
│   │   ├── updates/route.ts       # GET /api/programs/[id]/updates
│   │   └── trials/route.ts        # GET /api/programs/[id]/trials
│   ├── search/route.ts             # GET /api/programs/search?q=...
│   └── top-candidates/route.ts     # GET /api/programs/top-candidates
├── trials/
│   ├── route.ts                    # GET /api/trials
│   └── [nctId]/route.ts           # GET /api/trials/[nctId]
├── predictions/
│   ├── route.ts                    # GET /api/predictions
│   └── [programId]/route.ts       # GET /api/predictions/[programId]
├── stats/
│   ├── summary/route.ts            # GET /api/stats/summary
│   └── timeline/route.ts           # GET /api/stats/timeline
└── content/
    ├── route.ts                    # GET /api/content/pages
    └── [slug]/route.ts            # GET /api/content/[slug]
```

### API実装例

#### 全プログラム取得

```typescript
// app/api/programs/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { clinicalPrograms } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

export const runtime = 'edge'; // エッジランタイムで高速化

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const phase = searchParams.get('phase');
  const status = searchParams.get('status');
  const limit = parseInt(searchParams.get('limit') || '100');

  try {
    let query = db.select().from(clinicalPrograms);

    if (phase) {
      query = query.where(eq(clinicalPrograms.currentPhase, phase)) as any;
    }

    if (status) {
      query = query.where(eq(clinicalPrograms.status, status)) as any;
    }

    const programs = await query.limit(limit);

    return NextResponse.json(programs, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    console.error('Error fetching programs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch programs' },
      { status: 500 }
    );
  }
}
```

#### 特定プログラム詳細

```typescript
// app/api/programs/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { clinicalPrograms, programUpdates, clinicalTrials } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

export const runtime = 'edge';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // プログラム本体
    const program = await db.query.clinicalPrograms.findFirst({
      where: eq(clinicalPrograms.programId, params.id),
      with: {
        updates: {
          limit: 10,
          orderBy: (updates, { desc }) => [desc(updates.updateDate)],
        },
        trials: true,
        predictions: {
          limit: 1,
          orderBy: (predictions, { desc }) => [desc(predictions.simulationDate)],
        },
      },
    });

    if (!program) {
      return NextResponse.json(
        { error: 'Program not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(program, {
      headers: {
        'Cache-Control': 'public, s-maxage=1800, stale-while-revalidate=3600',
      },
    });
  } catch (error) {
    console.error('Error fetching program:', error);
    return NextResponse.json(
      { error: 'Failed to fetch program' },
      { status: 500 }
    );
  }
}
```

#### 検索API

```typescript
// app/api/programs/search/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { clinicalPrograms } from '@/lib/db/schema';
import { sql } from 'drizzle-orm';

export const runtime = 'edge';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');

  if (!query || query.length < 2) {
    return NextResponse.json(
      { error: 'Query parameter "q" must be at least 2 characters' },
      { status: 400 }
    );
  }

  try {
    // PostgreSQL全文検索
    const results = await db
      .select()
      .from(clinicalPrograms)
      .where(
        sql`
          to_tsvector('english', ${clinicalPrograms.name} || ' ' ||
                                 ${clinicalPrograms.company} || ' ' ||
                                 ${clinicalPrograms.target})
          @@ plainto_tsquery('english', ${query})
        `
      )
      .limit(20);

    return NextResponse.json(results, {
      headers: {
        'Cache-Control': 'public, s-maxage=600, stale-while-revalidate=1800',
      },
    });
  } catch (error) {
    console.error('Error searching programs:', error);
    return NextResponse.json(
      { error: 'Failed to search programs' },
      { status: 500 }
    );
  }
}
```

#### 統計サマリー

```typescript
// app/api/stats/summary/route.ts
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { clinicalPrograms, simulationResults } from '@/lib/db/schema';
import { sql, not, like, min } from 'drizzle-orm';

export const runtime = 'edge';
export const revalidate = 3600; // 1時間キャッシュ

export async function GET() {
  try {
    // アクティブプログラム数
    const [{ count: activeCount }] = await db
      .select({ count: sql<number>`count(*)` })
      .from(clinicalPrograms)
      .where(
        not(
          like(clinicalPrograms.status, '%Failed%')
        )
      );

    // Phase別プログラム数
    const programsByPhase = await db
      .select({
        phase: clinicalPrograms.currentPhase,
        count: sql<number>`count(*)`,
      })
      .from(clinicalPrograms)
      .groupBy(clinicalPrograms.currentPhase);

    // 最速承認予測
    const [{ fastest }] = await db
      .select({ fastest: min(simulationResults.fdaApprovalMedian) })
      .from(simulationResults);

    return NextResponse.json({
      activePrograms: activeCount,
      programsByPhase: Object.fromEntries(
        programsByPhase.map(p => [p.phase, p.count])
      ),
      fastestApprovalYear: fastest,
      lastUpdated: new Date().toISOString(),
    }, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=7200',
      },
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch stats' },
      { status: 500 }
    );
  }
}
```

---

## フロントエンド設計

### ディレクトリ構造

```
app/
├── layout.tsx                      # ルートレイアウト
├── page.tsx                        # トップページ
├── programs/
│   ├── page.tsx                   # プログラム一覧
│   └── [id]/
│       └── page.tsx               # プログラム詳細
├── trials/
│   ├── page.tsx                   # 臨床試験一覧
│   └── [nctId]/page.tsx          # 試験詳細
├── predictions/
│   └── page.tsx                   # 予測タイムライン
├── patient-guide/
│   └── page.tsx                   # 患者ガイド
├── for-doctors/
│   └── page.tsx                   # 医師向け情報
└── api/                           # API Routes
    └── ...

components/
├── ui/                            # Shadcn/ui コンポーネント
│   ├── button.tsx
│   ├── card.tsx
│   └── ...
├── programs/
│   ├── ProgramCard.tsx
│   ├── ProgramList.tsx
│   ├── ProgramDetail.tsx
│   └── ProgramSearch.tsx
├── charts/
│   ├── TimelineChart.tsx
│   └── CDFChart.tsx
└── layout/
    ├── Header.tsx
    ├── Footer.tsx
    └── Navigation.tsx

lib/
├── db/
│   ├── index.ts                   # DB接続
│   └── schema.ts                  # Drizzleスキーマ
├── api/
│   └── client.ts                  # クライアント側API呼び出し
└── utils/
    └── format.ts                  # ユーティリティ関数
```

### ページ実装例

#### トップページ（Server Component）

```typescript
// app/page.tsx
import { db } from '@/lib/db';
import { clinicalPrograms, simulationResults } from '@/lib/db/schema';
import { desc } from 'drizzle-orm';
import ProgramCard from '@/components/programs/ProgramCard';
import StatsOverview from '@/components/stats/StatsOverview';

export const revalidate = 3600; // ISR: 1時間ごとに再生成

export default async function HomePage() {
  // トップ候補取得（Server Componentで直接DBアクセス）
  const topPrograms = await db.query.clinicalPrograms.findMany({
    with: {
      predictions: {
        limit: 1,
        orderBy: [desc(simulationResults.simulationDate)],
      },
    },
    limit: 5,
  });

  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">
        網膜色素変性症 治療開発ロードマップ
      </h1>

      <StatsOverview />

      <section className="mt-12">
        <h2 className="text-2xl font-semibold mb-4">最有望候補</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {topPrograms.map(program => (
            <ProgramCard key={program.id} program={program} />
          ))}
        </div>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold mb-4">最新情報</h2>
        {/* ... */}
      </section>
    </main>
  );
}
```

#### プログラム一覧ページ（検索機能付き）

```typescript
// app/programs/page.tsx
'use client';

import { useState, useEffect } from 'react';
import ProgramCard from '@/components/programs/ProgramCard';
import SearchBar from '@/components/programs/SearchBar';
import FilterPanel from '@/components/programs/FilterPanel';

export default function ProgramsPage() {
  const [programs, setPrograms] = useState([]);
  const [filters, setFilters] = useState({
    phase: null,
    status: null,
    search: '',
  });

  useEffect(() => {
    const fetchPrograms = async () => {
      const params = new URLSearchParams();
      if (filters.phase) params.set('phase', filters.phase);
      if (filters.status) params.set('status', filters.status);

      const res = await fetch(`/api/programs?${params}`);
      const data = await res.json();
      setPrograms(data);
    };

    fetchPrograms();
  }, [filters]);

  const handleSearch = async (query: string) => {
    if (query.length < 2) return;

    const res = await fetch(`/api/programs/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    setPrograms(data);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">治療プログラム一覧</h1>

      <div className="flex gap-6">
        <aside className="w-64">
          <FilterPanel filters={filters} onChange={setFilters} />
        </aside>

        <main className="flex-1">
          <SearchBar onSearch={handleSearch} />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            {programs.map(program => (
              <ProgramCard key={program.id} program={program} />
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
```

#### プログラム詳細ページ（Server Component + Client Component混在）

```typescript
// app/programs/[id]/page.tsx
import { db } from '@/lib/db';
import { clinicalPrograms } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import { notFound } from 'next/navigation';
import ProgramHeader from '@/components/programs/ProgramHeader';
import UpdateTimeline from '@/components/programs/UpdateTimeline';
import RelatedTrials from '@/components/programs/RelatedTrials';
import PredictionChart from '@/components/programs/PredictionChart';

export const revalidate = 1800; // ISR: 30分ごとに再生成

interface Props {
  params: { id: string };
}

export default async function ProgramDetailPage({ params }: Props) {
  const program = await db.query.clinicalPrograms.findFirst({
    where: eq(clinicalPrograms.programId, params.id),
    with: {
      updates: {
        limit: 20,
        orderBy: (updates, { desc }) => [desc(updates.updateDate)],
      },
      trials: true,
      predictions: {
        limit: 1,
        orderBy: (predictions, { desc }) => [desc(predictions.simulationDate)],
      },
    },
  });

  if (!program) {
    notFound();
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <ProgramHeader program={program} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
        <div className="lg:col-span-2">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">承認予測</h2>
            <PredictionChart prediction={program.predictions[0]} />
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">更新履歴</h2>
            <UpdateTimeline updates={program.updates} />
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">関連臨床試験</h2>
            <RelatedTrials trials={program.trials} />
          </section>
        </div>

        <aside>
          <div className="sticky top-4">
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-semibold mb-4">基本情報</h3>
              <dl className="space-y-2">
                <div>
                  <dt className="text-sm text-gray-600">企業</dt>
                  <dd className="font-medium">{program.company}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-600">Phase</dt>
                  <dd className="font-medium">{program.currentPhase}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-600">ステータス</dt>
                  <dd className="font-medium">{program.status}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-600">治療法</dt>
                  <dd className="font-medium">{program.modality}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-600">ターゲット</dt>
                  <dd className="font-medium">{program.target}</dd>
                </div>
              </dl>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

// 静的生成用のパス生成
export async function generateStaticParams() {
  const programs = await db.select({ programId: clinicalPrograms.programId })
    .from(clinicalPrograms);

  return programs.map(program => ({
    id: program.programId,
  }));
}
```

---

## データ更新フロー

### Vercel Cron Jobsによる自動更新

```typescript
// app/api/cron/update-data/route.ts
import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export const runtime = 'nodejs';
export const maxDuration = 300; // 5分タイムアウト

export async function GET(request: Request) {
  // Vercel Cronからのリクエストか検証
  const authHeader = request.headers.get('authorization');
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    // Pythonスクリプトを実行
    const { stdout: fetchOutput } = await execAsync('python3 python-scripts/fetch_latest_data.py');
    console.log('Fetch completed:', fetchOutput);

    const { stdout: updateOutput } = await execAsync('python3 python-scripts/update_database.py');
    console.log('Update completed:', updateOutput);

    const { stdout: simOutput } = await execAsync('python3 python-scripts/run_simulations.py');
    console.log('Simulation completed:', simOutput);

    // ISRキャッシュを無効化
    await fetch(`${process.env.NEXT_PUBLIC_BASE_URL}/api/revalidate?secret=${process.env.REVALIDATE_SECRET}`);

    return NextResponse.json({
      success: true,
      timestamp: new Date().toISOString(),
      output: { fetchOutput, updateOutput, simOutput },
    });
  } catch (error) {
    console.error('Cron job failed:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}
```

### Vercel設定（vercel.json）

```json
{
  "crons": [
    {
      "path": "/api/cron/update-data",
      "schedule": "0 0 * * 1"
    }
  ]
}
```

### キャッシュ無効化API

```typescript
// app/api/revalidate/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { revalidatePath, revalidateTag } from 'next/cache';

export async function GET(request: NextRequest) {
  const secret = request.nextUrl.searchParams.get('secret');

  if (secret !== process.env.REVALIDATE_SECRET) {
    return NextResponse.json({ error: 'Invalid secret' }, { status: 401 });
  }

  // すべてのページを再生成
  revalidatePath('/', 'layout');
  revalidateTag('programs');
  revalidateTag('predictions');

  return NextResponse.json({ revalidated: true, timestamp: Date.now() });
}
```

### GitHub Actions（週次データ更新）

```yaml
# .github/workflows/update-data.yml
name: Weekly Data Update

on:
  schedule:
    - cron: '0 0 * * 1'  # 毎週月曜 9:00 JST
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Trigger Vercel Cron Job
      run: |
        curl -X GET "${{ secrets.VERCEL_CRON_URL }}" \
          -H "Authorization: Bearer ${{ secrets.CRON_SECRET }}"

    - name: Notify Slack
      if: success()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'データ更新完了'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## iOSアプリ統合

### Swift API Client

```swift
// API/RetinaRoadmapAPI.swift
import Foundation

actor RetinaRoadmapAPI {
    let baseURL = URL(string: "https://retina-roadmap.vercel.app/api")!

    func fetchPrograms(phase: String? = nil, status: String? = nil) async throws -> [ClinicalProgram] {
        var components = URLComponents(url: baseURL.appendingPathComponent("programs"), resolvingAgainstBaseURL: false)!
        var queryItems: [URLQueryItem] = []
        if let phase { queryItems.append(URLQueryItem(name: "phase", value: phase)) }
        if let status { queryItems.append(URLQueryItem(name: "status", value: status)) }
        components.queryItems = queryItems.isEmpty ? nil : queryItems

        let (data, _) = try await URLSession.shared.data(from: components.url!)
        return try JSONDecoder().decode([ClinicalProgram].self, from: data)
    }

    func fetchProgramDetail(id: String) async throws -> ProgramDetail {
        let url = baseURL.appendingPathComponent("programs/\(id)")
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(ProgramDetail.self, from: data)
    }

    func searchPrograms(query: String) async throws -> [ClinicalProgram] {
        var components = URLComponents(url: baseURL.appendingPathComponent("programs/search"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "q", value: query)]
        let (data, _) = try await URLSession.shared.data(from: components.url!)
        return try JSONDecoder().decode([ClinicalProgram].self, from: data)
    }

    func fetchStatsSummary() async throws -> StatsSummary {
        let url = baseURL.appendingPathComponent("stats/summary")
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(StatsSummary.self, from: data)
    }
}

// Models/ClinicalProgram.swift
struct ClinicalProgram: Codable, Identifiable {
    let id: Int
    let programId: String
    let name: String
    let company: String
    let currentPhase: String
    let status: String
    let modality: String
    let target: String
    let notes: String?
    let keyDates: [String: String]?
    let regulatory: [String]?
    let trialIds: [String]?

    enum CodingKeys: String, CodingKey {
        case id, name, company, status, modality, target, notes
        case programId = "program_id"
        case currentPhase = "current_phase"
        case keyDates = "key_dates"
        case regulatory
        case trialIds = "trial_ids"
    }
}

struct ProgramDetail: Codable {
    let program: ClinicalProgram
    let updates: [ProgramUpdate]
    let trials: [ClinicalTrial]
    let prediction: PredictionResult?
}

struct ProgramUpdate: Codable, Identifiable {
    let id: Int
    let updateDate: String
    let event: String
    let source: String
    let importanceScore: Int?

    enum CodingKeys: String, CodingKey {
        case id, event, source
        case updateDate = "update_date"
        case importanceScore = "importance_score"
    }
}
```

### SwiftUI Views

```swift
// Views/ProgramListView.swift
import SwiftUI

struct ProgramListView: View {
    @StateObject private var viewModel = ProgramListViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading {
                    ProgressView("読み込み中...")
                } else if let error = viewModel.error {
                    ErrorView(error: error, retry: viewModel.loadPrograms)
                } else {
                    List(viewModel.programs) { program in
                        NavigationLink(value: program) {
                            ProgramRowView(program: program)
                        }
                    }
                }
            }
            .navigationTitle("治療プログラム")
            .navigationDestination(for: ClinicalProgram.self) { program in
                ProgramDetailView(programId: program.programId)
            }
            .task {
                await viewModel.loadPrograms()
            }
            .refreshable {
                await viewModel.loadPrograms()
            }
            .searchable(text: $viewModel.searchQuery)
        }
    }
}

// ViewModels/ProgramListViewModel.swift
@MainActor
class ProgramListViewModel: ObservableObject {
    @Published var programs: [ClinicalProgram] = []
    @Published var isLoading = false
    @Published var error: Error?
    @Published var searchQuery = ""

    private let api = RetinaRoadmapAPI()

    func loadPrograms() async {
        isLoading = true
        defer { isLoading = false }

        do {
            programs = try await api.fetchPrograms()
        } catch {
            self.error = error
        }
    }

    func search() async {
        guard !searchQuery.isEmpty else {
            await loadPrograms()
            return
        }

        do {
            programs = try await api.searchPrograms(query: searchQuery)
        } catch {
            self.error = error
        }
    }
}
```

---

## 実装ロードマップ

### Phase 1: プロジェクトセットアップ（1週間）

- [ ] Next.jsプロジェクト作成 (`npx create-next-app@latest`)
- [ ] Tailwind CSS + Shadcn/ui セットアップ
- [ ] Vercel Postgres / Supabase セットアップ
- [ ] Drizzle ORM セットアップ
- [ ] 環境変数設定

```bash
# プロジェクト作成
npx create-next-app@latest retina-roadmap-next --typescript --tailwind --app --src-dir

# Drizzle ORM
npm install drizzle-orm @vercel/postgres
npm install -D drizzle-kit

# Shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input table
```

### Phase 2: データベース構築（1週間）

- [ ] Drizzleスキーマ定義
- [ ] マイグレーションファイル生成
- [ ] Vercel Postgresにテーブル作成
- [ ] 既存JSONデータの移行スクリプト作成（TypeScript）
- [ ] データ移行実行・検証

```typescript
// scripts/migrate-data.ts
import { db } from '@/lib/db';
import { clinicalPrograms, programUpdates } from '@/lib/db/schema';
import programsData from '../data/knowledge_base/clinical_programs.json';

async function migrateData() {
  for (const [programId, program] of Object.entries(programsData.programs)) {
    await db.insert(clinicalPrograms).values({
      programId,
      name: programId,
      company: program.company,
      currentPhase: program.current_phase,
      status: program.status,
      modality: program.modality,
      target: program.target,
      notes: program.notes,
      keyDates: program.key_dates,
      regulatory: program.regulatory,
      trialIds: program.trial_ids,
    });

    // 更新履歴も移行
    for (const update of program.recent_updates) {
      await db.insert(programUpdates).values({
        programId,
        updateDate: update.date,
        event: update.event,
        source: update.source,
      });
    }
  }
}
```

### Phase 3: API Routes開発（2週間）

- [ ] 基本エンドポイント実装（GET /api/programs等）
- [ ] フィルタリング・ページネーション
- [ ] 検索API（PostgreSQL全文検索）
- [ ] エラーハンドリング
- [ ] APIテスト作成

### Phase 4: フロントエンド開発（3週間）

- [ ] レイアウト・ヘッダー・フッター
- [ ] トップページ（ISR）
- [ ] プログラム一覧ページ（Client Component）
- [ ] プログラム詳細ページ（ISR）
- [ ] 検索機能
- [ ] 予測タイムラインページ
- [ ] レスポンシブデザイン

### Phase 5: 既存ページ移行（2週間）

- [ ] 患者ガイドページ移行
- [ ] 医師向けページ移行
- [ ] FAQページ移行
- [ ] 免責事項ページ移行
- [ ] ナビゲーション統合

### Phase 6: データ更新自動化（1週間）

- [ ] Pythonスクリプト整理（fetch/update/simulate分離）
- [ ] Vercel Cron Job実装
- [ ] キャッシュ無効化API
- [ ] Slack通知設定

### Phase 7: iOSアプリ開発（4週間）

- [ ] Xcodeプロジェクト作成
- [ ] API Clientライブラリ実装
- [ ] 画面実装（リスト、詳細、検索）
- [ ] オフライン対応（Core Data）
- [ ] プッシュ通知実装
- [ ] App Store申請

### Phase 8: 本番デプロイ・最適化（1週間）

- [ ] Vercel本番デプロイ
- [ ] カスタムドメイン設定
- [ ] OGP画像生成
- [ ] パフォーマンス最適化
- [ ] モニタリング設定（Vercel Analytics/Sentry）
- [ ] ドキュメント整備

**総期間: 約15週間（約3.5ヶ月）**

---

## 次のステップ

### 即座に開始できる項目

1. **Next.jsプロジェクト作成**
   ```bash
   npx create-next-app@latest retina-roadmap-next \
     --typescript \
     --tailwind \
     --app \
     --src-dir \
     --import-alias "@/*"
   ```

2. **Vercel Postgres セットアップ**
   - Vercelプロジェクト作成
   - Storage → Postgres → Create Database
   - 環境変数を `.env.local` にコピー

3. **Drizzleスキーマ作成**
   - `lib/db/schema.ts` を作成
   - `drizzle.config.ts` を設定
   - `drizzle-kit generate:pg` でマイグレーション生成

4. **データ移行スクリプト実行**
   - `scripts/migrate-data.ts` を作成
   - `npm run migrate` で実行

5. **最初のページ実装**
   - `app/page.tsx` でトップページ
   - `app/api/programs/route.ts` で最初のAPI

### プロトタイプ作成を支援しましょうか？

以下のいずれかをすぐに作成できます：

1. **完全なプロジェクトセットアップスクリプト**
2. **Drizzleスキーマ + マイグレーション完全版**
3. **データ移行スクリプト（JSON→DB）**
4. **最初のページ（トップ + プログラム一覧）のフルコード**
5. **Vercelデプロイ設定一式**

どこから始めますか？
