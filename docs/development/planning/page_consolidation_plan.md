# ページ統合計画書

## 1. 新しいサイト構造

### 現在：13ページ → 提案：6ページ

```
旧構造（13ページ）                    新構造（6ページ）
├── index.html                      ├── index.html（ランディング）
├── reality_and_actions.html        ├── patient_guide.html（患者向け統合）
├── current_status_facts.html       ├── medical_info.html（医療者向け統合）
├── ai_predictions.html             ├── detailed_analysis.html（詳細分析統合）
├── regional_approval_timeline.html ├── faq.html（よくある質問）
├── accessible_summary.html         └── disclaimer.html（免責事項）
├── executive_summary_for_doctor.html
├── for_doctor_checklist.html
├── simulation_methodology.html
├── bottlenecks.html
├── ai_acceleration_impact.html
├── publication_disclaimer.html
└── publication_checklist.html
```

## 2. 各ページの詳細設計

### 2.1 index.html - ランディングページ

#### 目的
訪問者を適切なコンテンツへ誘導する入口

#### 構成
```html
<body>
    <!-- ヒーローセクション -->
    <section class="hero">
        <h1>網膜色素変性症の治療はいつ？</h1>
        
        <!-- 3つの重要数字 -->
        <div class="key-numbers">
            <div class="number-card">
                <span class="big-number">2027年</span>
                <span class="label">最速承認予測（米国）</span>
            </div>
            <div class="number-card">
                <span class="big-number">2032年</span>
                <span class="label">日本での承認予測</span>
            </div>
            <div class="number-card">
                <span class="big-number">15種類</span>
                <span class="label">開発中の治療法</span>
            </div>
        </div>
    </section>
    
    <!-- 3つの選択パス -->
    <section class="paths">
        <div class="path-card patient">
            <h2>患者・ご家族の方へ</h2>
            <p>治療の見通しと今できることを分かりやすく</p>
            <a href="patient_guide.html" class="btn-primary">詳しく見る</a>
        </div>
        
        <div class="path-card medical">
            <h2>医療従事者の方へ</h2>
            <p>エビデンスと臨床情報</p>
            <a href="medical_info.html" class="btn-secondary">詳しく見る</a>
        </div>
        
        <div class="path-card researcher">
            <h2>詳細データを見る</h2>
            <p>予測の根拠と分析結果</p>
            <a href="detailed_analysis.html" class="btn-tertiary">詳しく見る</a>
        </div>
    </section>
</body>
```

### 2.2 patient_guide.html - 患者向け統合ページ

#### 統合元
- reality_and_actions.html（メイン）
- regional_approval_timeline.html（日本部分）
- accessible_summary.html（要約）
- index.html（TOP5プログラム）

#### 構成
```html
<body>
    <h1>患者・ご家族向けガイド</h1>
    
    <!-- クイックアンサー -->
    <section class="quick-answers">
        <h2>よくあるご質問</h2>
        <div class="qa-card">
            <h3>Q: 治療はいつ頃受けられますか？</h3>
            <p>A: 最も早い治療法は2032年頃に日本で承認される見込みです。</p>
        </div>
    </section>
    
    <!-- 注目の治療法TOP5 -->
    <section class="top-treatments">
        <h2>最も期待される治療法</h2>
        <!-- プログラムカード形式で表示 -->
    </section>
    
    <!-- 今できる5つのアクション -->
    <section class="actions">
        <h2>今すぐできること</h2>
        <!-- reality_and_actionsの内容を整理 -->
    </section>
    
    <!-- 日本での承認時期 -->
    <section class="japan-timeline">
        <h2>日本での承認予測</h2>
        <!-- regional_approval_timelineから抽出 -->
    </section>
</body>
```

### 2.3 medical_info.html - 医療従事者向け統合

#### 統合元
- executive_summary_for_doctor.html
- for_doctor_checklist.html
- simulation_methodology.html（要約）

#### 構成
```html
<body>
    <h1>医療従事者向け情報</h1>
    
    <!-- エグゼクティブサマリー -->
    <section class="executive-summary">
        <h2>研究概要</h2>
        <!-- エビデンスレベル、信頼性など -->
    </section>
    
    <!-- 臨床的に重要な情報 -->
    <section class="clinical-info">
        <h2>臨床情報</h2>
        <!-- 治療モダリティ、対象患者など -->
    </section>
    
    <!-- 信頼性チェックリスト -->
    <section class="checklist">
        <h2>エビデンスチェックリスト</h2>
        <!-- インタラクティブなチェックリスト -->
    </section>
    
    <!-- 参考文献・リソース -->
    <section class="resources">
        <h2>参考資料</h2>
        <!-- 論文、臨床試験へのリンク -->
    </section>
</body>
```

### 2.4 detailed_analysis.html - 詳細分析統合

#### 統合元
- 現在のindex.html（詳細部分）
- ai_predictions.html
- bottlenecks.html
- ai_acceleration_impact.html
- simulation_methodology.html

#### 構成
```html
<body>
    <h1>詳細分析とデータ</h1>
    
    <!-- タブ形式で切り替え -->
    <div class="tab-container">
        <nav class="tabs">
            <button class="tab-btn active" data-tab="prediction">予測結果</button>
            <button class="tab-btn" data-tab="methodology">方法論</button>
            <button class="tab-btn" data-tab="ai-impact">AI影響</button>
            <button class="tab-btn" data-tab="bottlenecks">課題分析</button>
        </nav>
        
        <div class="tab-content">
            <!-- 各タブの内容 -->
        </div>
    </div>
</body>
```

### 2.5 faq.html - よくある質問（新規）

#### 目的
散在している質問と回答を集約

#### 構成
```html
<body>
    <h1>よくある質問</h1>
    
    <div class="faq-container">
        <section class="faq-category">
            <h2>治療時期について</h2>
            <details>
                <summary>いつ頃治療を受けられますか？</summary>
                <p>回答内容...</p>
            </details>
        </section>
        
        <section class="faq-category">
            <h2>治療法について</h2>
            <!-- 質問と回答 -->
        </section>
        
        <section class="faq-category">
            <h2>参加方法について</h2>
            <!-- 質問と回答 -->
        </section>
    </div>
</body>
```

## 3. コンテンツ移行マッピング

### 削除されるコンテンツ
- publication_checklist.html → 開発ドキュメントへ
- current_status_facts.html → 各ページに分散統合

### 移行マッピング表

| 旧ページ | 新ページ | 移行内容 |
|---------|---------|---------|
| reality_and_actions.html | patient_guide.html | 全内容 |
| regional_approval_timeline.html | patient_guide.html | 日本部分のみ |
| accessible_summary.html | patient_guide.html | 要約として統合 |
| executive_summary_for_doctor.html | medical_info.html | 全内容 |
| for_doctor_checklist.html | medical_info.html | 全内容 |
| ai_predictions.html | detailed_analysis.html | 全内容 |
| bottlenecks.html | detailed_analysis.html | 全内容 |
| simulation_methodology.html | detailed_analysis.html | 全内容 |
| ai_acceleration_impact.html | detailed_analysis.html | 全内容 |

## 4. 実装手順

### Step 1: テンプレート作成
1. 新しいHTMLテンプレートを作成
2. 共通のCSS/JSを準備
3. レスポンシブデザインの実装

### Step 2: コンテンツ移行
1. 移行スクリプトの作成
2. コンテンツの抽出と再構成
3. 重複の削除

### Step 3: ナビゲーション更新
1. シンプルな3-4項目のメニュー
2. パンくずリストの追加
3. 関連ページの提示

### Step 4: テストと最適化
1. モバイル対応の確認
2. アクセシビリティチェック
3. パフォーマンス最適化

## 5. 期待される効果

### ユーザビリティの向上
- 情報を見つけやすくなる（13→6ページ）
- ターゲット別の明確な分離
- モバイルでの使いやすさ

### メンテナンスの簡素化
- 重複コンテンツの削除
- 更新箇所の削減
- 一貫性の向上

### エンゲージメントの向上
- 直帰率の低下
- 滞在時間の増加
- 目的達成率の向上