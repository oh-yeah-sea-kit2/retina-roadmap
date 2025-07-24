# データフローとHTML表示改善の具体的実装計画

## 1. データフロー整理の具体的実装

### A. 統一データモデルの実装
**ファイル**: `src/models/clinical_program.py`

```python
@dataclass
class ClinicalProgram:
    # 識別情報
    program_id: str  # "MCO-010", "OCU400"など
    name: str
    company: str
    
    # 治療情報
    modality: str  # "gene_therapy", "cell_therapy", "drug"
    target_genes: List[str]  # ["NR2E3", "RPGR"]または["gene-agnostic"]
    mechanism: str
    
    # 臨床試験情報  
    trial_ids: List[str]  # ["NCT04945772", "NCT05203939"]
    current_phase: str  # "Phase 3", "Phase 2/3"
    trial_status: str  # "BLA submission", "Enrolling"
    
    # タイムライン
    key_dates: Dict[str, str]  # phase開始日、完了日、申請日など
    milestones: List[Dict]  # 達成済み・予定のマイルストーン
    
    # データソース追跡
    sources: Dict[str, Any]  # どこから来たデータか
    last_updated: Dict[str, datetime]  # ソースごとの更新日
    
    # 優先度情報
    priority_score: float  # 0-100
    confidence_level: str  # "high", "medium", "low"
```

### B. データ統合パイプライン
**ファイル**: `src/pipeline/data_integrator.py`

1. **ClinicalTrials.govデータの正規化**
   - NCT番号を基準にプログラムIDを推定
   - 企業名、治療名を統一フォーマットに変換
   
2. **知識ベースとのマージ**
   - プログラムIDでマッチング
   - 最新情報を優先してマージ
   - 競合がある場合は信頼度で判定

3. **重複除去ロジック**
   - 同一プログラムの複数試験を統合
   - 企業名の表記揺れを吸収（"Nanoscope" = "Nanoscope Therapeutics"）

### C. 優先度計算の具体的実装
```python
def calculate_priority_score(program: ClinicalProgram) -> float:
    score = 0.0
    
    # Phase による基礎スコア
    phase_scores = {
        "BLA submission": 100,
        "Phase 3": 80,
        "Phase 2/3": 60,
        "Phase 2": 40,
        "Phase 1/2": 30,
        "Phase 1": 20
    }
    score = phase_scores.get(program.current_phase, 0)
    
    # 規制優遇による加点
    if "FDA Fast Track" in program.regulatory:
        score += 10
    if "Orphan Drug" in program.regulatory:
        score += 5
    
    # 最近の更新による加点
    days_since_update = (datetime.now() - program.last_updated).days
    if days_since_update < 30:
        score += 5
    
    return min(score, 100)  # 最大100
```

## 2. HTML表示改善の具体的実装

### A. 新しいHTML構造
**ファイル**: `templates/index_template.html`

```html
<body>
    <!-- 1. ヒーローセクション（最重要情報） -->
    <section class="hero-section">
        <h1>網膜色素変性症の治療法はいつ？</h1>
        
        <div class="key-metrics">
            <div class="metric-card primary">
                <span class="metric-label">最速承認予測</span>
                <span class="metric-value">2026年</span>
                <span class="metric-detail">MCO-010（米国）</span>
            </div>
            
            <div class="metric-card secondary">
                <span class="metric-label">日本での承認</span>
                <span class="metric-value">2031年頃</span>
                <span class="metric-detail">FDA承認+5年</span>
            </div>
            
            <div class="metric-card tertiary">
                <span class="metric-label">開発中の治療</span>
                <span class="metric-value">15種類</span>
                <span class="metric-detail">Phase 2以上: 8</span>
            </div>
        </div>
    </section>
    
    <!-- 2. タイムライン（ビジュアル重視） -->
    <section class="timeline-section">
        <h2>承認予測タイムライン</h2>
        <div class="timeline-container">
            <!-- JavaScriptで動的に生成 -->
        </div>
    </section>
    
    <!-- 3. プログラムカード（上位5つ） -->
    <section class="programs-section">
        <h2>注目の治療プログラム TOP5</h2>
        <div class="program-grid">
            <!-- プログラムカードを動的生成 -->
        </div>
    </section>
    
    <!-- 4. 最新更新情報 -->
    <section class="updates-section">
        <h2>最新アップデート</h2>
        <div class="update-list">
            <!-- 更新情報を動的生成 -->
        </div>
    </section>
</body>
```

### B. プログラムカードのHTML生成
**ファイル**: `src/reporting/card_generator.py`

```python
def generate_program_card(program: ClinicalProgram) -> str:
    # 進捗度計算（0-100%）
    progress = calculate_phase_progress(program)
    
    # カードクラス決定
    card_class = "card-urgent" if program.priority_score > 80 else "card-normal"
    
    html = f'''
    <div class="program-card {card_class}" data-program-id="{program.program_id}">
        <div class="card-header">
            <h3>{program.name}</h3>
            <span class="company-badge">{program.company}</span>
        </div>
        
        <div class="progress-section">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progress}%"></div>
            </div>
            <span class="phase-label">{program.current_phase}</span>
        </div>
        
        <dl class="card-details">
            <dt>治療タイプ</dt>
            <dd>{translate_modality(program.modality)}</dd>
            
            <dt>対象</dt>
            <dd>{format_target_genes(program.target_genes)}</dd>
            
            <dt>予測承認</dt>
            <dd class="highlight">{format_approval_prediction(program)}</dd>
        </dl>
        
        <div class="card-footer">
            <a href="#{program.program_id}-details" class="detail-link">詳細を見る</a>
            <time class="update-time" datetime="{program.last_updated}">
                更新: {format_relative_time(program.last_updated)}
            </time>
        </div>
    </div>
    '''
    return html
```

### C. レスポンシブCSS実装
**ファイル**: `static/css/responsive.css`

```css
/* モバイルファースト設計 */

/* ベース（モバイル） */
.hero-section {
    padding: 20px;
    text-align: center;
}

.key-metrics {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.metric-card {
    background: white;
    padding: 16px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.program-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
}

/* タブレット（768px以上） */
@media (min-width: 768px) {
    .key-metrics {
        flex-direction: row;
        justify-content: center;
    }
    
    .program-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* デスクトップ（1024px以上） */
@media (min-width: 1024px) {
    .program-grid {
        grid-template-columns: repeat(3, 1fr);
    }
    
    .timeline-container {
        overflow-x: visible;
    }
}
```

## 3. データ更新フローの具体的実装

### A. 更新管理システム
**ファイル**: `src/update/update_manager.py`

```python
class UpdateManager:
    def __init__(self):
        self.update_history = []
        
    def check_for_updates(self) -> UpdateReport:
        """更新チェックを実行"""
        report = UpdateReport()
        
        # 各データソースの鮮度チェック
        ct_age = self.get_data_age('clinical_trials')
        kb_age = self.get_data_age('knowledge_base')
        
        if ct_age > 7:  # 7日以上古い
            report.add_needed('clinical_trials', 'データが7日以上古い')
        
        if kb_age > 30:  # 30日以上古い
            report.add_needed('knowledge_base', 'データが30日以上古い')
            
        return report
    
    def perform_smart_update(self):
        """必要な部分のみ更新"""
        report = self.check_for_updates()
        
        if report.needs_update('clinical_trials'):
            self.update_clinical_trials()
            
        if report.needs_update('knowledge_base'):
            self.update_knowledge_base()
            
        # 更新があった場合のみレポート再生成
        if report.has_updates():
            self.regenerate_reports()
```

### B. 差分検出と通知
**ファイル**: `src/update/diff_detector.py`

```python
class DiffDetector:
    def detect_changes(self, old_data: Dict, new_data: Dict) -> DiffReport:
        """変更を検出してレポート生成"""
        diff = DiffReport()
        
        # 新規プログラム
        new_ids = set(new_data.keys()) - set(old_data.keys())
        for pid in new_ids:
            diff.add_new(pid, new_data[pid])
        
        # 更新されたプログラム
        for pid in set(old_data.keys()) & set(new_data.keys()):
            changes = self.compare_programs(old_data[pid], new_data[pid])
            if changes:
                diff.add_updated(pid, changes)
        
        # 削除されたプログラム
        removed_ids = set(old_data.keys()) - set(new_data.keys())
        for pid in removed_ids:
            diff.add_removed(pid)
            
        return diff
```

### C. 更新通知のHTML生成
```python
def generate_update_notification(diff: DiffReport) -> str:
    """更新通知のHTMLを生成"""
    html = '<div class="update-notification">'
    
    if diff.new_programs:
        html += f'''
        <div class="update-new">
            <h3>🆕 新規プログラム（{len(diff.new_programs)}件）</h3>
            <ul>
                {''.join(f'<li>{p.name} - {p.company}</li>' for p in diff.new_programs)}
            </ul>
        </div>
        '''
    
    if diff.updated_programs:
        html += f'''
        <div class="update-changed">
            <h3>📝 更新されたプログラム（{len(diff.updated_programs)}件）</h3>
            <ul>
                {''.join(f'<li>{p.name}: {p.change_summary}</li>' for p in diff.updated_programs)}
            </ul>
        </div>
        '''
    
    html += '</div>'
    return html
```

## 4. 実装の優先順位と具体的なステップ

### Phase 1: データモデル統一（3-4日）
1. **Day 1**: `ClinicalProgram`クラスの実装とテスト
2. **Day 2**: データ統合スクリプトの作成
3. **Day 3**: 既存データの移行とバリデーション
4. **Day 4**: 統合テストと修正

### Phase 2: HTML表示改善（3-4日）
1. **Day 1**: HTMLテンプレートの作成
2. **Day 2**: カード生成ロジックの実装
3. **Day 3**: レスポンシブCSSの実装
4. **Day 4**: JavaScriptインタラクションの追加

### Phase 3: 更新フロー整備（2-3日）
1. **Day 1**: 更新チェックロジックの実装
2. **Day 2**: 差分検出と通知システム
3. **Day 3**: 統合テストとドキュメント作成

この実装により、データの一貫性が保たれ、ユーザーにとって分かりやすく、メンテナンスしやすいシステムが構築できます。