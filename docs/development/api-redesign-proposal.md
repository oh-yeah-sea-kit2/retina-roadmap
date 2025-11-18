# 網膜色素変性症ページ API化・データベース設計提案

作成日: 2025-11-18

## 📋 目次

1. [現状分析](#現状分析)
2. [提案アーキテクチャ](#提案アーキテクチャ)
3. [データベース設計](#データベース設計)
4. [REST API設計](#rest-api設計)
5. [CMS選択肢](#cms選択肢)
6. [データ更新フロー](#データ更新フロー)
7. [iOSアプリ統合](#iOSアプリ統合)
8. [実装ロードマップ](#実装ロードマップ)

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

---

## 提案アーキテクチャ

### アーキテクチャ概要図

```
┌─────────────────────────────────────────────────────────────┐
│                     クライアント層                              │
├─────────────┬──────────────┬───────────────┬────────────────┤
│  Webブラウザ   │  iOSアプリ    │  Androidアプリ │  管理画面(CMS)  │
└─────────────┴──────────────┴───────────────┴────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   REST API        │
                    │   (FastAPI)       │
                    │   Port: 8000      │
                    └─────────┬─────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
        ┌───────▼──────┐ ┌───▼────┐ ┌─────▼─────┐
        │ビジネスロジック│ │キャッシュ│ │外部API統合 │
        │(Python)      │ │(Redis) │ │(CT.gov等) │
        └───────┬──────┘ └────────┘ └───────────┘
                │
        ┌───────▼──────┐
        │ データベース   │
        │ (PostgreSQL) │
        │ or SQLite    │
        └──────────────┘
```

### 技術スタック推奨

| 層 | 技術 | 理由 |
|---|------|------|
| **API** | FastAPI | 高速、型安全、自動ドキュメント生成 |
| **データベース** | PostgreSQL | 本番環境推奨、JSON型サポート |
| **開発DB** | SQLite | 軽量、ファイルベース、移行容易 |
| **キャッシュ** | Redis | 高速レスポンス、API rate limit管理 |
| **認証** | JWT | ステートレス、モバイルアプリ対応 |
| **ホスティング** | Railway/Render/Fly.io | 無料枠あり、自動デプロイ |
| **CMS** | 選択肢A: Strapi (Headless CMS) | 既製品、管理画面付き |
|         | 選択肢B: 自前FastAPI + React Admin | 完全制御、軽量 |

---

## データベース設計

### テーブル設計（PostgreSQL/SQLite共通）

#### 1. `clinical_programs` テーブル（治療プログラム）

```sql
CREATE TABLE clinical_programs (
    id SERIAL PRIMARY KEY,
    program_id VARCHAR(50) UNIQUE NOT NULL,  -- 'MCO-010', 'OCU400'など
    name VARCHAR(200) NOT NULL,
    company VARCHAR(200) NOT NULL,
    current_phase VARCHAR(50),               -- 'Phase 3', 'Phase 2/3'など
    status VARCHAR(100),                     -- 'Enrolling', 'BLA submitted'など
    modality VARCHAR(100),                   -- 'Gene therapy', 'Cell therapy'など
    target VARCHAR(200),                     -- 'Gene-agnostic', 'RPGR'など
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- JSON列（柔軟性確保）
    key_dates JSONB,                         -- {phase3_start: '2021-06', ...}
    regulatory JSONB,                        -- ['FDA Fast Track', ...]
    trial_ids JSONB,                         -- ['NCT04945772', ...]

    -- 検索インデックス
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(name, '') || ' ' ||
            coalesce(company, '') || ' ' ||
            coalesce(target, '')
        )
    ) STORED
);

CREATE INDEX idx_programs_search ON clinical_programs USING GIN(search_vector);
CREATE INDEX idx_programs_phase ON clinical_programs(current_phase);
CREATE INDEX idx_programs_company ON clinical_programs(company);
```

#### 2. `program_updates` テーブル（更新履歴）

```sql
CREATE TABLE program_updates (
    id SERIAL PRIMARY KEY,
    program_id VARCHAR(50) REFERENCES clinical_programs(program_id),
    update_date DATE NOT NULL,
    event_type VARCHAR(50),                  -- 'phase_transition', 'trial_result'など
    event TEXT NOT NULL,
    source VARCHAR(200),                     -- 'Company PR', 'Web Search'など
    importance_score INTEGER,                -- 0-100
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_updates_program ON program_updates(program_id, update_date DESC);
CREATE INDEX idx_updates_date ON program_updates(update_date DESC);
```

#### 3. `clinical_trials` テーブル（臨床試験）

```sql
CREATE TABLE clinical_trials (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) UNIQUE NOT NULL,      -- 'NCT04945772'
    program_id VARCHAR(50) REFERENCES clinical_programs(program_id),
    title TEXT,
    status VARCHAR(50),
    phase VARCHAR(50),
    enrollment INTEGER,
    start_date DATE,
    completion_date DATE,
    primary_outcome TEXT,
    sponsor VARCHAR(200),
    location VARCHAR(500),

    -- JSON列
    conditions JSONB,                        -- ['Retinitis Pigmentosa', ...]
    interventions JSONB,                     -- [{type: 'Gene Therapy', name: '...'}]
    raw_data JSONB,                          -- API全データ保存

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trials_nct ON clinical_trials(nct_id);
CREATE INDEX idx_trials_program ON clinical_trials(program_id);
CREATE INDEX idx_trials_status ON clinical_trials(status);
```

#### 4. `publications` テーブル（論文）

```sql
CREATE TABLE publications (
    id SERIAL PRIMARY KEY,
    pubmed_id VARCHAR(20) UNIQUE,
    program_id VARCHAR(50) REFERENCES clinical_programs(program_id),
    title TEXT NOT NULL,
    authors TEXT,
    journal VARCHAR(200),
    publication_date DATE,
    abstract TEXT,
    doi VARCHAR(100),
    url TEXT,
    keywords JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_publications_program ON publications(program_id);
CREATE INDEX idx_publications_date ON publications(publication_date DESC);
```

#### 5. `simulation_results` テーブル（予測結果）

```sql
CREATE TABLE simulation_results (
    id SERIAL PRIMARY KEY,
    program_id VARCHAR(50) REFERENCES clinical_programs(program_id),
    simulation_date DATE NOT NULL,

    -- 予測結果
    fda_approval_median INTEGER,             -- 承認予測年（中央値）
    fda_approval_ci_low INTEGER,             -- 90%信頼区間下限
    fda_approval_ci_high INTEGER,            -- 90%信頼区間上限
    japan_approval_median INTEGER,
    japan_approval_ci_low INTEGER,
    japan_approval_ci_high INTEGER,

    -- シミュレーションパラメータ
    success_probability NUMERIC(4, 3),       -- 成功確率
    phase_durations JSONB,                   -- {phase1: [12, 24], ...}
    confidence_level VARCHAR(20),            -- 'high', 'medium', 'low'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_simulations_program ON simulation_results(program_id, simulation_date DESC);
```

#### 6. `content_pages` テーブル（CMSコンテンツ）

```sql
CREATE TABLE content_pages (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,       -- 'patient-guide', 'faq'
    title VARCHAR(200) NOT NULL,
    content TEXT,                            -- Markdown形式
    page_type VARCHAR(50),                   -- 'guide', 'faq', 'analysis'
    target_audience VARCHAR(50),             -- 'patient', 'doctor', 'general'
    meta_description TEXT,
    published BOOLEAN DEFAULT false,

    -- バージョン管理
    version INTEGER DEFAULT 1,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pages_slug ON content_pages(slug);
CREATE INDEX idx_pages_published ON content_pages(published);
```

#### 7. `data_sources` テーブル（データソース管理）

```sql
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,        -- 'clinicaltrials_gov', 'pubmed', 'web_search'
    source_url TEXT,
    last_fetched_at TIMESTAMP,
    next_fetch_at TIMESTAMP,
    fetch_status VARCHAR(50),                -- 'success', 'failed', 'pending'
    error_message TEXT,
    fetch_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### データ移行スクリプト（既存JSON→DB）

```python
# scripts/migrate_to_db.py
import json
import sqlite3  # or psycopg2 for PostgreSQL
from datetime import datetime

def migrate_clinical_programs():
    """clinical_programs.json → clinical_programs テーブル"""
    with open('data/knowledge_base/clinical_programs.json') as f:
        data = json.load(f)

    conn = sqlite3.connect('retina_roadmap.db')
    cursor = conn.cursor()

    for program_id, program in data['programs'].items():
        cursor.execute("""
            INSERT INTO clinical_programs
            (program_id, name, company, current_phase, status,
             modality, target, notes, key_dates, regulatory, trial_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            program_id,
            program_id,  # nameも同じにするか別途設定
            program['company'],
            program['current_phase'],
            program['status'],
            program['modality'],
            program['target'],
            program.get('notes', ''),
            json.dumps(program.get('key_dates', {})),
            json.dumps(program.get('regulatory', [])),
            json.dumps(program.get('trial_ids', []))
        ))

        # 更新履歴も移行
        for update in program.get('recent_updates', []):
            cursor.execute("""
                INSERT INTO program_updates
                (program_id, update_date, event, source)
                VALUES (?, ?, ?, ?)
            """, (
                program_id,
                update['date'],
                update['event'],
                update['source']
            ))

    conn.commit()
    conn.close()
```

---

## REST API設計

### エンドポイント一覧

#### 公開エンドポイント（認証不要）

```
GET  /api/v1/programs                    # 全治療プログラム一覧
GET  /api/v1/programs/{program_id}       # 特定プログラム詳細
GET  /api/v1/programs/{program_id}/updates  # プログラム更新履歴
GET  /api/v1/programs/{program_id}/trials   # 関連臨床試験
GET  /api/v1/programs/search?q={query}   # プログラム検索
GET  /api/v1/programs/top-candidates     # 最有望候補（Top 5）

GET  /api/v1/trials                      # 臨床試験一覧
GET  /api/v1/trials/{nct_id}             # 特定試験詳細

GET  /api/v1/predictions                 # 最新予測結果
GET  /api/v1/predictions/{program_id}    # プログラム別予測

GET  /api/v1/content/{slug}              # コンテンツページ取得
GET  /api/v1/content/pages               # ページ一覧

GET  /api/v1/stats/summary               # 統計サマリー
GET  /api/v1/stats/timeline              # タイムライン統計
```

#### 管理エンドポイント（認証必要）

```
POST   /api/v1/admin/programs            # プログラム新規作成
PUT    /api/v1/admin/programs/{id}       # プログラム更新
DELETE /api/v1/admin/programs/{id}       # プログラム削除

POST   /api/v1/admin/content             # コンテンツ作成
PUT    /api/v1/admin/content/{id}        # コンテンツ更新

POST   /api/v1/admin/data/fetch          # データ手動取得トリガー
GET    /api/v1/admin/data/status         # 取得ステータス確認
```

### API実装例（FastAPI）

```python
# api/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
import sqlite3

app = FastAPI(
    title="Retina Roadmap API",
    description="網膜色素変性症治療開発ロードマップAPI",
    version="1.0.0"
)

# CORS設定（iOSアプリからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydanticモデル（レスポンススキーマ）
class ClinicalProgram(BaseModel):
    program_id: str
    name: str
    company: str
    current_phase: str
    status: str
    modality: str
    target: str
    notes: Optional[str]
    key_dates: dict
    regulatory: List[str]
    trial_ids: List[str]

class ProgramUpdate(BaseModel):
    update_date: date
    event: str
    source: str
    importance_score: Optional[int]

class PredictionResult(BaseModel):
    program_id: str
    fda_approval_median: int
    fda_approval_ci_low: int
    fda_approval_ci_high: int
    japan_approval_median: int
    japan_approval_ci_low: int
    japan_approval_ci_high: int
    confidence_level: str

# エンドポイント実装

@app.get("/api/v1/programs", response_model=List[ClinicalProgram])
def get_all_programs(
    phase: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=100)
):
    """全治療プログラム一覧を取得"""
    conn = sqlite3.connect('retina_roadmap.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM clinical_programs WHERE 1=1"
    params = []

    if phase:
        query += " AND current_phase = ?"
        params.append(phase)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += f" LIMIT {limit}"

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return [dict(row) for row in results]

@app.get("/api/v1/programs/{program_id}", response_model=ClinicalProgram)
def get_program(program_id: str):
    """特定プログラムの詳細を取得"""
    conn = sqlite3.connect('retina_roadmap.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM clinical_programs WHERE program_id = ?",
        (program_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Program not found")

    return dict(result)

@app.get("/api/v1/programs/{program_id}/updates", response_model=List[ProgramUpdate])
def get_program_updates(program_id: str, limit: int = 10):
    """プログラムの更新履歴を取得"""
    conn = sqlite3.connect('retina_roadmap.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT update_date, event, source, importance_score
        FROM program_updates
        WHERE program_id = ?
        ORDER BY update_date DESC
        LIMIT ?
    """, (program_id, limit))

    results = cursor.fetchall()
    conn.close()

    return [dict(row) for row in results]

@app.get("/api/v1/programs/search")
def search_programs(q: str):
    """プログラムを検索（会社名、治療名、ターゲット等）"""
    conn = sqlite3.connect('retina_roadmap.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 簡易検索（PostgreSQLの場合はtsvectorを使用）
    cursor.execute("""
        SELECT * FROM clinical_programs
        WHERE name LIKE ? OR company LIKE ? OR target LIKE ?
    """, (f'%{q}%', f'%{q}%', f'%{q}%'))

    results = cursor.fetchall()
    conn.close()

    return [dict(row) for row in results]

@app.get("/api/v1/programs/top-candidates", response_model=List[ClinicalProgram])
def get_top_candidates():
    """最有望候補Top 5を取得"""
    # シミュレーション結果と結合して最速承認予測順にソート
    conn = sqlite3.connect('retina_roadmap.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, s.fda_approval_median
        FROM clinical_programs p
        LEFT JOIN (
            SELECT program_id, fda_approval_median
            FROM simulation_results
            WHERE id IN (
                SELECT MAX(id) FROM simulation_results GROUP BY program_id
            )
        ) s ON p.program_id = s.program_id
        WHERE p.status NOT LIKE '%Failed%'
        ORDER BY s.fda_approval_median ASC
        LIMIT 5
    """)

    results = cursor.fetchall()
    conn.close()

    return [dict(row) for row in results]

@app.get("/api/v1/predictions/{program_id}", response_model=PredictionResult)
def get_prediction(program_id: str):
    """プログラム別の最新予測を取得"""
    conn = sqlite3.connect('retina_roadmap.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM simulation_results
        WHERE program_id = ?
        ORDER BY simulation_date DESC
        LIMIT 1
    """, (program_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return dict(result)

@app.get("/api/v1/stats/summary")
def get_summary_stats():
    """統計サマリーを取得"""
    conn = sqlite3.connect('retina_roadmap.db')
    cursor = conn.cursor()

    stats = {}

    # アクティブプログラム数
    cursor.execute("""
        SELECT COUNT(*) FROM clinical_programs
        WHERE status NOT LIKE '%Failed%' AND status NOT LIKE '%Discontinued%'
    """)
    stats['active_programs'] = cursor.fetchone()[0]

    # Phase別プログラム数
    cursor.execute("""
        SELECT current_phase, COUNT(*) as count
        FROM clinical_programs
        GROUP BY current_phase
    """)
    stats['programs_by_phase'] = dict(cursor.fetchall())

    # 最速承認予測
    cursor.execute("""
        SELECT MIN(fda_approval_median) FROM simulation_results
        WHERE id IN (SELECT MAX(id) FROM simulation_results GROUP BY program_id)
    """)
    stats['fastest_approval_year'] = cursor.fetchone()[0]

    conn.close()

    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### API自動ドキュメント

FastAPIは自動的にSwagger UIとReDocを生成：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## CMS選択肢

### 選択肢A: Headless CMS（Strapi）

**メリット:**
- 管理画面が最初から用意されている
- コンテンツのバージョン管理
- 多言語対応（日英切り替え）
- ユーザー権限管理
- メディアライブラリ

**デメリット:**
- 追加のサーバーリソース必要
- カスタマイズに限界
- 学習コスト

**実装例:**

```bash
# Strapiのインストール
npx create-strapi-app@latest retina-cms --quickstart

# コンテンツタイプ定義
# - Page (title, slug, content, target_audience)
# - FAQ (question, answer, category)
# - News Update (title, date, content, related_program)
```

### 選択肢B: 自前CMS（FastAPI + React Admin）

**メリット:**
- 完全制御
- 既存のFastAPI APIと統合
- 軽量
- 独自の要件に柔軟対応

**デメリット:**
- 開発工数が増える
- メンテナンス負担

**実装例:**

```python
# 管理画面エンドポイント追加
from fastapi_admin.app import app as admin_app
from fastapi_admin.resources import Model, Field

@app.mount("/admin", admin_app)

class ProgramResource(Model):
    model = ClinicalProgram
    fields = [
        Field("program_id", label="プログラムID"),
        Field("company", label="企業名"),
        Field("current_phase", label="現在のPhase"),
        # ...
    ]
```

### 推奨: 選択肢B（自前CMS）

理由:
1. 既存のPythonコードベースと統合しやすい
2. データベース設計を完全制御できる
3. iOSアプリとも同じAPI経由でアクセス可能
4. 将来的に機械学習モデル統合がしやすい

---

## データ更新フロー

### 自動更新パイプライン

```
┌──────────────────────────────────────────────────────────┐
│                  定期実行（GitHub Actions）                  │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  1. データ取得 (scripts/fetch_latest_data.py)            │
│     - ClinicalTrials.gov API                             │
│     - PubMed API                                         │
│     - Web検索（Gemini Search）                            │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  2. データ比較 (scripts/compare_and_update.py)            │
│     - 既存DBと比較                                        │
│     - 変更検出（新規/更新/変更なし）                        │
│     - 重要度スコアリング（0-100）                          │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  3. データベース更新                                       │
│     - clinical_programs テーブル更新                      │
│     - program_updates テーブルに履歴追加                  │
│     - simulation_results 再計算                          │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  4. キャッシュ無効化                                       │
│     - Redis キャッシュクリア                              │
│     - CDN キャッシュパージ                                │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  5. 通知送信                                              │
│     - Slack通知（重要度70以上）                           │
│     - プッシュ通知（iOSアプリ）                            │
└──────────────────────────────────────────────────────────┘
```

### GitHub Actions設定例

```yaml
# .github/workflows/update_data.yml
name: Auto Update Clinical Data

on:
  schedule:
    # 毎週月曜 9:00 JST (00:00 UTC)
    - cron: '0 0 * * 1'
  workflow_dispatch:  # 手動実行も可能

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
      run: |
        pip install -r requirements.txt

    - name: Fetch latest data
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: |
        python scripts/fetch_latest_data.py

    - name: Compare and update database
      run: |
        python scripts/compare_and_update.py

    - name: Run simulations
      run: |
        python src/sim/timeline_sim.py

    - name: Commit changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add data/
        git diff --quiet || git commit -m "Auto update: $(date +'%Y-%m-%d')"
        git push

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

### iOS アプリアーキテクチャ

```swift
// API Client (URLSession + Async/Await)
class RetinaRoadmapAPI {
    let baseURL = "https://api.retina-roadmap.com/api/v1"

    func fetchPrograms() async throws -> [ClinicalProgram] {
        let url = URL(string: "\(baseURL)/programs")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode([ClinicalProgram].self, from: data)
    }

    func fetchProgramDetail(id: String) async throws -> ClinicalProgram {
        let url = URL(string: "\(baseURL)/programs/\(id)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(ClinicalProgram.self, from: data)
    }

    func searchPrograms(query: String) async throws -> [ClinicalProgram] {
        var components = URLComponents(string: "\(baseURL)/programs/search")!
        components.queryItems = [URLQueryItem(name: "q", value: query)]
        let (data, _) = try await URLSession.shared.data(from: components.url!)
        return try JSONDecoder().decode([ClinicalProgram].self, from: data)
    }
}

// Data Models
struct ClinicalProgram: Codable, Identifiable {
    let id: String
    let programId: String
    let name: String
    let company: String
    let currentPhase: String
    let status: String
    let modality: String
    let target: String
    let notes: String?
    let keyDates: [String: String]
    let regulatory: [String]
    let trialIds: [String]

    enum CodingKeys: String, CodingKey {
        case id, name, company, status, modality, target, notes
        case programId = "program_id"
        case currentPhase = "current_phase"
        case keyDates = "key_dates"
        case regulatory
        case trialIds = "trial_ids"
    }
}

struct ProgramUpdate: Codable, Identifiable {
    let id: UUID = UUID()
    let updateDate: String
    let event: String
    let source: String
    let importanceScore: Int?

    enum CodingKeys: String, CodingKey {
        case updateDate = "update_date"
        case event, source
        case importanceScore = "importance_score"
    }
}

// SwiftUI Views
struct ProgramListView: View {
    @StateObject private var viewModel = ProgramListViewModel()

    var body: some View {
        NavigationView {
            List(viewModel.programs) { program in
                NavigationLink(destination: ProgramDetailView(programId: program.programId)) {
                    ProgramRowView(program: program)
                }
            }
            .navigationTitle("治療プログラム")
            .task {
                await viewModel.loadPrograms()
            }
            .refreshable {
                await viewModel.loadPrograms()
            }
        }
    }
}

struct ProgramDetailView: View {
    let programId: String
    @StateObject private var viewModel = ProgramDetailViewModel()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                if let program = viewModel.program {
                    ProgramInfoSection(program: program)
                    TimelineSection(programId: programId)
                    UpdateHistorySection(programId: programId)
                }
            }
            .padding()
        }
        .navigationTitle(programId)
        .task {
            await viewModel.loadProgram(id: programId)
        }
    }
}

// ViewModel
@MainActor
class ProgramListViewModel: ObservableObject {
    @Published var programs: [ClinicalProgram] = []
    @Published var isLoading = false
    @Published var error: Error?

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
}
```

### オフライン対応（Core Data）

```swift
// ローカルキャッシュ
class DataManager {
    static let shared = DataManager()
    private let container: NSPersistentContainer

    func savePrograms(_ programs: [ClinicalProgram]) {
        // Core Dataに保存
    }

    func loadCachedPrograms() -> [ClinicalProgram] {
        // オフライン時にキャッシュから読み込み
    }
}
```

### プッシュ通知

```swift
// 重要な更新時にプッシュ通知
struct NotificationPayload {
    let title: String
    let body: String
    let programId: String
    let importanceScore: Int
}

// アプリ側で受信
UNUserNotificationCenter.current().delegate = self

func userNotificationCenter(
    _ center: UNUserNotificationCenter,
    didReceive response: UNNotificationResponse
) async {
    let programId = response.notification.request.content.userInfo["programId"] as? String
    // プログラム詳細画面へ遷移
}
```

---

## 実装ロードマップ

### Phase 1: データベース構築（2週間）

- [ ] データベース設計最終化
- [ ] SQLiteでテーブル作成
- [ ] 既存JSONデータの移行スクリプト作成
- [ ] データ移行実行・検証

### Phase 2: API開発（3週間）

- [ ] FastAPIプロジェクトセットアップ
- [ ] 基本エンドポイント実装（GET /programs, /trials等）
- [ ] ページネーション・フィルタリング実装
- [ ] 検索機能実装
- [ ] API自動テスト作成

### Phase 3: データ更新自動化（2週間）

- [ ] fetch_latest_data.py をDB対応に修正
- [ ] compare_and_update.py 作成
- [ ] GitHub Actions設定
- [ ] Slack通知設定

### Phase 4: 管理画面（3週間）

- [ ] FastAPI Admin統合
- [ ] コンテンツ編集画面
- [ ] プログラム情報編集画面
- [ ] 認証機能（JWT）

### Phase 5: 既存HTMLの動的化（2週間）

- [ ] HTMLテンプレートをAPI経由に変更
- [ ] JavaScriptでの動的読み込み実装
- [ ] キャッシュ戦略実装

### Phase 6: iOSアプリ開発（6週間）

- [ ] Xcodeプロジェクト作成
- [ ] API Clientライブラリ実装
- [ ] 画面実装（リスト、詳細、検索）
- [ ] オフライン対応（Core Data）
- [ ] プッシュ通知実装
- [ ] App Store申請

### Phase 7: 本番デプロイ（1週間）

- [ ] PostgreSQL移行（Railway/Render）
- [ ] API本番デプロイ
- [ ] DNS設定
- [ ] SSL証明書設定
- [ ] モニタリング設定（Sentry等）

**総期間: 約19週間（約5ヶ月）**

---

## 次のステップ

1. **プロトタイプ作成**: まずSQLite + FastAPIで最小限のAPIを構築
2. **データ移行**: 既存JSONをDBに移行
3. **API動作確認**: Swagger UIでテスト
4. **iOSプロトタイプ**: 簡単なリスト表示アプリ作成
5. **フィードバック収集**: ユーザーテスト

---

## 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [PostgreSQL JSON型ガイド](https://www.postgresql.org/docs/current/datatype-json.html)
- [SwiftUI + Async/Await](https://developer.apple.com/documentation/swift/concurrency)
- [REST API設計ベストプラクティス](https://restfulapi.net/)
