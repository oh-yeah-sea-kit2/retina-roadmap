#!/usr/bin/env python3
"""
機械学習による臨床試験成功予測モデル
複数の特徴量を使用して、より精密な予測を実現
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import joblib
from typing import Dict, List, Tuple
import requests
from datetime import datetime
from pathlib import Path


class ClinicalTrialFeatureExtractor:
    """臨床試験の特徴量を抽出"""
    
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_names = []
    
    def extract_features(self, trials_df: pd.DataFrame) -> pd.DataFrame:
        """
        試験データから機械学習用の特徴量を抽出
        
        Args:
            trials_df: 臨床試験データ
            
        Returns:
            特徴量データフレーム
        """
        features = pd.DataFrame()
        
        # 基本的な試験特性
        features['phase_numeric'] = trials_df['Phase'].map({
            'PHASE1': 1, 'PHASE2': 2, 'PHASE3': 3,
            'PHASE1, PHASE2': 1.5, 'PHASE2, PHASE3': 2.5
        }).fillna(1)
        
        # 治療タイプの特定（タイトルから推測）
        features['is_gene_therapy'] = trials_df['BriefTitle'].str.contains(
            'gene|AAV|lentivir|CRISPR', case=False, na=False
        ).astype(int)
        
        features['is_cell_therapy'] = trials_df['BriefTitle'].str.contains(
            'cell|stem|transplant', case=False, na=False
        ).astype(int)
        
        features['is_small_molecule'] = (~(features['is_gene_therapy'] | features['is_cell_therapy'])).astype(int)
        
        # スポンサー特性
        sponsor_counts = trials_df['SponsorName'].value_counts()
        features['sponsor_trial_count'] = trials_df['SponsorName'].map(sponsor_counts)
        features['is_big_pharma'] = trials_df['SponsorName'].str.contains(
            'Janssen|Roche|Novartis|Pfizer|Merck', case=False, na=False
        ).astype(int)
        
        # 対象遺伝子（タイトルから抽出）
        common_genes = ['RPGR', 'USH2A', 'PDE6B', 'ABCA4', 'CEP290']
        for gene in common_genes:
            features[f'targets_{gene}'] = trials_df['BriefTitle'].str.contains(
                gene, case=False, na=False
            ).astype(int)
        
        # 試験の経過時間（既に開始している場合）
        if 'StartDate' in trials_df.columns:
            features['years_since_start'] = (
                pd.Timestamp.now() - pd.to_datetime(trials_df['StartDate'])
            ).dt.days / 365.25
            features['years_since_start'] = features['years_since_start'].fillna(0).clip(lower=0)
        
        # 試験デザインの複雑さ（複数フェーズは複雑）
        features['is_multi_phase'] = trials_df['Phase'].str.contains(',', na=False).astype(int)
        
        self.feature_names = features.columns.tolist()
        return features
    
    def prepare_training_data(self, historical_trials: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        過去の試験データから訓練データを準備
        
        Args:
            historical_trials: 結果が判明している過去の試験
            
        Returns:
            (特徴量, ラベル)のタプル
        """
        # 特徴量抽出
        X = self.extract_features(historical_trials)
        
        # ラベル（成功/失敗）
        y = (historical_trials['Status'] == 'COMPLETED').astype(int)
        
        # 欠損値の処理
        X = X.fillna(0)
        
        return X, y


class MLTrialPredictor:
    """機械学習による試験成功予測"""
    
    def __init__(self):
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            ),
            'gradient_boost': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        }
        self.feature_extractor = ClinicalTrialFeatureExtractor()
        self.is_trained = False
        self.feature_importance = {}
    
    def train(self, historical_trials: pd.DataFrame):
        """
        過去のデータでモデルを訓練
        
        Args:
            historical_trials: 訓練用データ
        """
        # 訓練データの準備
        X, y = self.feature_extractor.prepare_training_data(historical_trials)
        
        # データ分割
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 各モデルの訓練と評価
        for name, model in self.models.items():
            print(f"\n訓練中: {name}")
            
            # 訓練
            model.fit(X_train, y_train)
            
            # 評価
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_test, y_pred, average='binary'
            )
            
            print(f"精度: {accuracy:.3f}")
            print(f"適合率: {precision:.3f}")
            print(f"再現率: {recall:.3f}")
            print(f"F1スコア: {f1:.3f}")
            
            # 特徴量重要度
            if hasattr(model, 'feature_importances_'):
                importance_df = pd.DataFrame({
                    'feature': self.feature_extractor.feature_names,
                    'importance': model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                self.feature_importance[name] = importance_df
                print("\n重要な特徴量トップ5:")
                print(importance_df.head())
        
        self.is_trained = True
    
    def predict_success_probability(self, trial: pd.Series) -> Dict[str, float]:
        """
        個別の試験の成功確率を予測
        
        Args:
            trial: 試験データ
            
        Returns:
            各モデルの予測確率
        """
        if not self.is_trained:
            raise ValueError("モデルが訓練されていません")
        
        # 特徴量抽出
        trial_df = pd.DataFrame([trial])
        X = self.feature_extractor.extract_features(trial_df)
        X = X.fillna(0)
        
        # 各モデルで予測
        predictions = {}
        for name, model in self.models.items():
            prob = model.predict_proba(X)[0, 1]  # 成功確率
            predictions[name] = prob
        
        # アンサンブル予測（平均）
        predictions['ensemble'] = np.mean(list(predictions.values()))
        
        return predictions
    
    def predict_timeline_with_ml(self, trial: pd.Series, base_timeline: float) -> Dict[str, float]:
        """
        機械学習で調整した承認タイムラインを予測
        
        Args:
            trial: 試験データ
            base_timeline: ベースとなるタイムライン（年）
            
        Returns:
            調整されたタイムライン
        """
        # 成功確率を取得
        success_probs = self.predict_success_probability(trial)
        
        # 成功確率に基づいてタイムラインを調整
        # 成功確率が高い→早期承認の可能性
        # 成功確率が低い→遅延または失敗の可能性
        adjusted_timelines = {}
        
        for model_name, prob in success_probs.items():
            if prob > 0.8:
                # 高確率→10%短縮
                adjustment = 0.9
            elif prob > 0.6:
                # 中確率→変更なし
                adjustment = 1.0
            elif prob > 0.4:
                # 低確率→20%延長
                adjustment = 1.2
            else:
                # 非常に低い→50%延長
                adjustment = 1.5
            
            adjusted_timelines[model_name] = base_timeline * adjustment
        
        return adjusted_timelines
    
    def get_risk_factors(self, trial: pd.Series) -> List[str]:
        """
        試験のリスク要因を特定
        
        Args:
            trial: 試験データ
            
        Returns:
            リスク要因のリスト
        """
        risk_factors = []
        
        # 特徴量抽出
        trial_df = pd.DataFrame([trial])
        features = self.feature_extractor.extract_features(trial_df).iloc[0]
        
        # リスク要因の判定
        if features.get('is_gene_therapy', 0) and features.get('phase_numeric', 0) == 1:
            risk_factors.append("初期段階の遺伝子治療（技術リスク高）")
        
        if features.get('sponsor_trial_count', 0) < 3:
            risk_factors.append("スポンサーの経験不足")
        
        if features.get('years_since_start', 0) > 5:
            risk_factors.append("長期化している試験（問題の可能性）")
        
        if features.get('is_multi_phase', 0):
            risk_factors.append("複数フェーズの複雑な試験デザイン")
        
        if not any(features.get(f'targets_{gene}', 0) for gene in ['RPGR', 'USH2A', 'PDE6B']):
            risk_factors.append("一般的でない標的遺伝子")
        
        return risk_factors
    
    def save_models(self, directory: str):
        """モデルを保存"""
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        
        for name, model in self.models.items():
            joblib.dump(model, dir_path / f"{name}_model.pkl")
        
        joblib.dump(self.feature_extractor, dir_path / "feature_extractor.pkl")
        joblib.dump(self.feature_importance, dir_path / "feature_importance.pkl")
    
    def load_models(self, directory: str):
        """モデルを読み込み"""
        dir_path = Path(directory)
        
        for name in self.models.keys():
            model_path = dir_path / f"{name}_model.pkl"
            if model_path.exists():
                self.models[name] = joblib.load(model_path)
        
        extractor_path = dir_path / "feature_extractor.pkl"
        if extractor_path.exists():
            self.feature_extractor = joblib.load(extractor_path)
        
        importance_path = dir_path / "feature_importance.pkl"
        if importance_path.exists():
            self.feature_importance = joblib.load(importance_path)
        
        self.is_trained = True


def demo_ml_prediction():
    """機械学習予測のデモンストレーション"""
    
    # 仮想的な訓練データ
    np.random.seed(42)
    n_trials = 200
    
    historical_trials = pd.DataFrame({
        'BriefTitle': [
            f"{'Gene therapy' if np.random.random() > 0.5 else 'Small molecule'} for "
            f"{np.random.choice(['RPGR', 'USH2A', 'PDE6B', 'Other'], p=[0.3, 0.2, 0.2, 0.3])}"
            for _ in range(n_trials)
        ],
        'Phase': np.random.choice(
            ['PHASE1', 'PHASE2', 'PHASE3'], 
            size=n_trials,
            p=[0.3, 0.4, 0.3]
        ),
        'SponsorName': np.random.choice(
            ['Janssen', 'Novartis', 'Small Biotech', 'University'],
            size=n_trials,
            p=[0.2, 0.2, 0.4, 0.2]
        ),
        'StartDate': pd.date_range(
            start='2015-01-01',
            end='2023-01-01',
            periods=n_trials
        ),
        'Status': np.random.choice(
            ['COMPLETED', 'TERMINATED'],
            size=n_trials,
            p=[0.7, 0.3]  # 70%成功率
        )
    })
    
    # モデルの訓練
    predictor = MLTrialPredictor()
    predictor.train(historical_trials)
    
    # テスト試験での予測
    test_trial = pd.Series({
        'BriefTitle': 'Gene therapy for RPGR-associated retinitis pigmentosa',
        'Phase': 'PHASE3',
        'SponsorName': 'Janssen',
        'StartDate': pd.Timestamp('2021-01-01')
    })
    
    print("\n\nテスト試験の予測:")
    print(f"試験: {test_trial['BriefTitle']}")
    
    # 成功確率予測
    success_probs = predictor.predict_success_probability(test_trial)
    print("\n成功確率:")
    for model, prob in success_probs.items():
        print(f"  {model}: {prob:.1%}")
    
    # リスク要因
    risk_factors = predictor.get_risk_factors(test_trial)
    if risk_factors:
        print("\nリスク要因:")
        for factor in risk_factors:
            print(f"  - {factor}")
    else:
        print("\n特筆すべきリスク要因なし")
    
    # タイムライン調整
    base_timeline = 3.0  # 基本3年
    adjusted_timelines = predictor.predict_timeline_with_ml(test_trial, base_timeline)
    print(f"\n承認までの予測期間（基本: {base_timeline}年）:")
    for model, timeline in adjusted_timelines.items():
        print(f"  {model}: {timeline:.1f}年")


if __name__ == "__main__":
    demo_ml_prediction()