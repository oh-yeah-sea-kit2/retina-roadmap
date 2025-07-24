# 高度なシミュレーション手法の設計書

最終更新: 2025年6月25日

## 1. 概要

現在のモンテカルロシミュレーションは有用ですが、静的な確率モデルに留まっています。本設計書では、より動的で現実的な予測を可能にする高度なシミュレーション手法を提案します。

## 2. 現在の手法の限界

### 2.1 現状の問題点
- **静的な確率**: 過去データの平均値のみ使用
- **単純な独立性仮定**: 試験間の相互作用を無視
- **更新不可**: 新しい情報が反映されない
- **説明性の欠如**: なぜその予測になったか不明

### 2.2 改善の必要性
- リアルタイムでの予測更新
- 試験間の相互影響の考慮
- 予測の根拠の明確化
- 不確実性のより正確な定量化

## 3. 提案する高度な手法

### 3.1 ベイズ階層モデル

#### 概要
事前分布と事後分布を使用して、新しいデータで予測を動的に更新

#### 数式表現
```
P(成功|データ) = P(データ|成功) × P(成功) / P(データ)

事前分布: Beta(α, β) ← 過去のRP試験データから推定
尤度: Binomial(n, p) ← 現在進行中の試験結果
事後分布: Beta(α + 成功数, β + 失敗数)
```

#### 実装例
```python
class BayesianTrialPredictor:
    def __init__(self, prior_alpha, prior_beta):
        self.alpha = prior_alpha  # 過去の成功数 + 1
        self.beta = prior_beta    # 過去の失敗数 + 1
    
    def update(self, successes, failures):
        """新しい試験結果で更新"""
        self.alpha += successes
        self.beta += failures
    
    def predict_success_rate(self):
        """更新された成功率を予測"""
        return self.alpha / (self.alpha + self.beta)
    
    def confidence_interval(self, confidence=0.95):
        """信頼区間を計算"""
        from scipy import stats
        return stats.beta.interval(confidence, self.alpha, self.beta)
```

### 3.2 機械学習アンサンブルモデル

#### 特徴量設計
```python
features = {
    # 試験特性
    'phase': 'カテゴリカル（1, 2, 3）',
    'treatment_type': 'カテゴリカル（遺伝子治療、細胞治療、低分子）',
    'target_gene': 'カテゴリカル（RPGR, USH2A, etc）',
    'patient_count': '連続値',
    'trial_duration_planned': '連続値',
    
    # 企業特性
    'sponsor_market_cap': '連続値（億円）',
    'sponsor_previous_approvals': '整数',
    'sponsor_rp_experience': 'ブール値',
    
    # 技術成熟度
    'related_publications_count': '整数',
    'patent_citations': '整数',
    'years_since_first_publication': '連続値',
    
    # 競合環境
    'competing_trials_same_target': '整数',
    'competing_trials_same_phase': '整数',
    
    # 規制環境
    'regulatory_designation': 'カテゴリカル（希少疾患指定等）',
    'country': 'カテゴリカル',
}
```

#### モデル構成
```python
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.ensemble import VotingRegressor

# 個別モデル
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
elastic_model = ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42)

# アンサンブル
ensemble = VotingRegressor([
    ('rf', rf_model),
    ('gb', gb_model),
    ('elastic', elastic_model)
])
```

### 3.3 エージェントベースモデル（ABM）

#### エージェント定義
```python
class PharmaCompanyAgent:
    def __init__(self, name, capital, risk_tolerance):
        self.name = name
        self.capital = capital
        self.risk_tolerance = risk_tolerance
        self.active_trials = []
    
    def decide_investment(self, market_state):
        """市場状況に基づいて投資判断"""
        if self.capital > threshold and market_state.success_rate > self.risk_tolerance:
            return True
        return False

class RegulatoryAgent:
    def __init__(self, base_review_time):
        self.base_review_time = base_review_time
        self.safety_concerns = 0
    
    def adjust_review_time(self, safety_events):
        """安全性イベントに基づいて審査期間を調整"""
        return self.base_review_time * (1 + 0.1 * safety_events)

class PatientPoolAgent:
    def __init__(self, total_patients, participation_rate):
        self.total_patients = total_patients
        self.participation_rate = participation_rate
    
    def available_patients(self, competing_trials):
        """競合試験を考慮して利用可能な患者数を計算"""
        return self.total_patients * self.participation_rate / (1 + competing_trials)
```

### 3.4 生存時間分析

#### Cox比例ハザードモデル
```python
from lifelines import CoxPHFitter

# データ準備
survival_data = pd.DataFrame({
    'duration': trial_durations,  # 試験開始から承認/中止までの時間
    'event': trial_success,        # 1=承認, 0=中止または継続中
    'phase': phases,
    'treatment_type': treatment_types,
    'sponsor_size': sponsor_sizes
})

# モデル適合
cph = CoxPHFitter()
cph.fit(survival_data, duration_col='duration', event_col='event')

# ハザード比の解釈
# 例: 遺伝子治療は低分子薬より承認確率が1.5倍高い
```

## 4. データソース拡張計画

### 4.1 必要な追加データ

| データソース | 取得方法 | 用途 | 優先度 |
|------------|---------|------|--------|
| FDA Orange Book | API | 過去の承認パターン | 高 |
| SEC EDGAR | API | 企業財務情報 | 高 |
| Google Scholar | API | 研究活動指標 | 中 |
| PatentsView | API | 技術成熟度 | 中 |
| NewsAPI | API | センチメント分析 | 低 |

### 4.2 データ統合アーキテクチャ
```python
class DataIntegrator:
    def __init__(self):
        self.sources = {
            'clinical_trials': ClinicalTrialsAPI(),
            'fda': FDAOrangeBookAPI(),
            'sec': SECEdgarAPI(),
            'scholar': GoogleScholarAPI(),
            'patents': PatentsViewAPI()
        }
    
    def fetch_all_data(self, trial_id):
        """全データソースから関連情報を取得"""
        data = {}
        for source_name, api in self.sources.items():
            try:
                data[source_name] = api.fetch(trial_id)
            except Exception as e:
                logger.warning(f"Failed to fetch from {source_name}: {e}")
        return data
```

## 5. 実装ロードマップ

### Phase 1: 基礎実装（2週間）
- [ ] ベイズ更新モジュールの実装
- [ ] 基本的な特徴量エンジニアリング
- [ ] 簡易版機械学習モデル

### Phase 2: データ拡張（1ヶ月）
- [ ] 追加APIの統合
- [ ] データパイプラインの構築
- [ ] 特徴量の拡充

### Phase 3: 高度なモデル（2ヶ月）
- [ ] エージェントベースモデルの実装
- [ ] 生存時間分析の統合
- [ ] アンサンブルモデルの最適化

### Phase 4: 検証と改善（1ヶ月）
- [ ] バックテストによる精度検証
- [ ] パラメータチューニング
- [ ] 可視化とレポート機能

## 6. 評価指標

### 6.1 予測精度
- **MAE (Mean Absolute Error)**: 予測年と実際の承認年の差
- **Calibration**: 予測確率と実際の成功率の一致度
- **Brier Score**: 確率予測の精度

### 6.2 モデル比較
```python
def evaluate_models(models, test_data):
    results = {}
    for name, model in models.items():
        predictions = model.predict(test_data)
        results[name] = {
            'mae': mean_absolute_error(test_data.actual, predictions),
            'rmse': np.sqrt(mean_squared_error(test_data.actual, predictions)),
            'r2': r2_score(test_data.actual, predictions)
        }
    return pd.DataFrame(results).T
```

## 7. 期待される成果

### 7.1 予測精度の向上
- 現在: ±3年の誤差
- 目標: ±1.5年の誤差
- 特に短期予測（2-3年先）の精度向上

### 7.2 説明可能性
- 各予測に対する要因分解
- 重要な特徴量の可視化
- シナリオ分析による感度分析

### 7.3 動的更新
- 月次での予測更新
- 新しい試験結果の自動反映
- リアルタイムダッシュボード

## 8. 次のステップ

1. **プロトタイプ実装**: ベイズモデルの基本版
2. **データ収集**: FDA Orange BookとSEC EDGARの統合
3. **初期検証**: 過去5年のデータでバックテスト
4. **段階的改善**: フィードバックに基づく調整

---

*この設計書は、より精度の高い治療開発予測を実現するための技術的ロードマップです。*