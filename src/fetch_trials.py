#!/usr/bin/env python3
"""
臨床試験データを ClinicalTrials.gov API から取得し、ローカルに保存する。
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import pandas as pd
import time


def fetch_clinical_trials():
    """ClinicalTrials.gov APIから網膜色素変性症の臨床試験データを取得"""
    
    # 新しいAPIエンドポイント (v2)
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    # クエリパラメータ
    params = {
        "query.cond": "Retinitis Pigmentosa",
        "query.term": "AREA[StudyType]Interventional",
        "fields": "NCTId|BriefTitle|Phase|StartDate|CompletionDate|OverallStatus|LeadSponsorName",
        "pageSize": 1000,
        "format": "json"
    }
    
    print(f"Fetching clinical trials data from ClinicalTrials.gov...")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # 生データを保存
        raw_dir = Path("data/raw/clinical_trials")
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        raw_file = raw_dir / f"{timestamp}.json"
        
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Raw data saved to: {raw_file}")
        
        # データを処理してDataFrameに変換
        studies = data.get("studies", [])
        
        if not studies:
            print("No studies found.")
            return
        
        # 各研究のデータを整形
        processed_data = []
        for study in studies:
            protocol_section = study.get("protocolSection", {})
            
            # 識別情報
            identification = protocol_section.get("identificationModule", {})
            nct_id = identification.get("nctId", "")
            brief_title = identification.get("briefTitle", "")
            
            # ステータス情報
            status_module = protocol_section.get("statusModule", {})
            overall_status = status_module.get("overallStatus", "")
            start_date_struct = status_module.get("startDateStruct", {})
            completion_date_struct = status_module.get("completionDateStruct", {})
            
            # フェーズ情報
            design_module = protocol_section.get("designModule", {})
            phases = design_module.get("phases", [])
            phase = ", ".join(phases) if phases else ""
            
            # スポンサー情報
            sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
            lead_sponsor = sponsor_module.get("leadSponsor", {})
            sponsor_name = lead_sponsor.get("name", "")
            
            # フェーズのフィルタリング（Phase 1, 2, 3のみ）
            if phase and any(p in phase for p in ["PHASE1", "PHASE2", "PHASE3"]):
                processed_data.append({
                    "NCTId": nct_id,
                    "BriefTitle": brief_title,
                    "Phase": phase,
                    "StartDate": start_date_struct.get("date", ""),
                    "CompletionDate": completion_date_struct.get("date", ""),
                    "Status": overall_status,
                    "SponsorName": sponsor_name
                })
        
        # DataFrameに変換してParquet形式で保存
        df = pd.DataFrame(processed_data)
        
        # 日付をパース（エラーを無視）
        for date_col in ["StartDate", "CompletionDate"]:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # 処理済みデータを保存
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = processed_dir / "clinical_trials.parquet"
        df.to_parquet(output_file, index=False)
        
        print(f"Processed data saved to: {output_file}")
        print(f"Total trials found: {len(df)}")
        print(f"Phase distribution:\n{df['Phase'].value_counts()}")
        print(f"Status distribution:\n{df['Status'].value_counts()}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


if __name__ == "__main__":
    df = fetch_clinical_trials()
    if df is not None:
        print("\nSample data (first 5 rows):")
        print(df.head())