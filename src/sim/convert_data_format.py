#!/usr/bin/env python3
"""
既存のparquetデータをJSON形式に変換して統合シミュレーションで使用可能にする
"""

import pandas as pd
import json
from pathlib import Path
import numpy as np
from datetime import datetime

def convert_parquet_to_json():
    """parquetファイルをJSON形式に変換"""
    data_dir = Path(__file__).parent.parent.parent / "data"
    
    # parquetファイルを読み込み
    parquet_path = data_dir / "processed" / "clinical_trials.parquet"
    df = pd.read_parquet(parquet_path)
    
    print(f"データ読み込み完了: {len(df)}件の試験")
    
    # データの前処理
    # NaN値を適切な値に置換
    df = df.fillna({
        'SponsorName': 'Unknown',
        'StartDate': '',
        'Phase': 'Unknown'
    })
    
    # 日付を文字列に変換
    date_columns = ['StartDate', 'CompletionDate', 'PrimaryCompletionDate', 'StudyFirstPostDate']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df[col] = df[col].dt.strftime('%Y-%m-%d').fillna('')
    
    # 特徴量を追加（簡易版）
    df['is_gene_therapy'] = df['BriefTitle'].str.contains(
        'gene|AAV|lentivir|CRISPR', case=False, na=False
    ).astype(int)
    
    df['is_cell_therapy'] = df['BriefTitle'].str.contains(
        'cell|stem|transplant', case=False, na=False
    ).astype(int)
    
    # JSON形式で保存
    output_data = {
        'metadata': {
            'source': 'ClinicalTrials.gov',
            'update_date': datetime.now().isoformat(),
            'total_trials': len(df),
            'active_trials': len(df[df['Status'].isin(['RECRUITING', 'ACTIVE_NOT_RECRUITING'])])
        },
        'trials': df.to_dict('records')
    }
    
    output_path = data_dir / "processed" / "trials_with_features.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"データ変換完了: {output_path}")
    
    # サマリー表示
    print("\nデータサマリー:")
    print(f"- 総試験数: {len(df)}")
    print(f"- 進行中: {len(df[df['Status'].isin(['RECRUITING', 'ACTIVE_NOT_RECRUITING'])])}件")
    print(f"- Phase別:")
    print(df['Phase'].value_counts())
    print(f"\n- 遺伝子治療: {df['is_gene_therapy'].sum()}件")
    print(f"- 細胞治療: {df['is_cell_therapy'].sum()}件")

if __name__ == "__main__":
    convert_parquet_to_json()