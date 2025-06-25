#!/usr/bin/env python3
"""
PubMedから網膜色素変性症に関する文献メタデータを取得する。
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import pandas as pd
import time
import json


def search_pubmed(query, max_results=1000):
    """PubMed E-utilities esearchを使って文献IDを検索"""
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "usehistory": "y"
    }
    
    print(f"Searching PubMed with query: {query}")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        result = data.get("esearchresult", {})
        count = int(result.get("count", 0))
        id_list = result.get("idlist", [])
        webenv = result.get("webenv", "")
        query_key = result.get("querykey", "")
        
        print(f"Found {count} articles, retrieved {len(id_list)} IDs")
        
        return {
            "count": count,
            "ids": id_list,
            "webenv": webenv,
            "query_key": query_key
        }
        
    except Exception as e:
        print(f"Error searching PubMed: {e}")
        return None


def fetch_pubmed_details(search_result):
    """PubMed efetchを使って文献の詳細情報を取得"""
    
    if not search_result or not search_result["ids"]:
        return []
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    # WebEnvとquery_keyを使用（推奨される方法）
    params = {
        "db": "pubmed",
        "WebEnv": search_result["webenv"],
        "query_key": search_result["query_key"],
        "retmode": "xml",
        "retmax": len(search_result["ids"])
    }
    
    print(f"Fetching details for {len(search_result['ids'])} articles...")
    
    try:
        # APIレート制限を考慮
        time.sleep(0.5)
        
        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()
        
        # XMLをパース
        root = ET.fromstring(response.content)
        
        articles = []
        for article in root.findall(".//PubmedArticle"):
            try:
                # PMID
                pmid = article.find(".//PMID").text
                
                # タイトル
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else ""
                
                # ジャーナル名
                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else ""
                
                # 発行年
                year_elem = article.find(".//PubDate/Year")
                if year_elem is None:
                    # MedlineDate形式の場合
                    medline_date = article.find(".//PubDate/MedlineDate")
                    if medline_date is not None:
                        # 年だけ抽出
                        year = medline_date.text[:4] if medline_date.text else ""
                    else:
                        year = ""
                else:
                    year = year_elem.text
                
                articles.append({
                    "PMID": pmid,
                    "Year": year,
                    "Title": title,
                    "Journal": journal
                })
                
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue
        
        print(f"Successfully parsed {len(articles)} articles")
        return articles
        
    except Exception as e:
        print(f"Error fetching article details: {e}")
        return []


def fetch_papers():
    """メイン関数：PubMedから文献データを取得して保存"""
    
    # 検索クエリ
    query = '("retinitis pigmentosa"[MeSH Terms] OR "retinitis pigmentosa"[Title/Abstract]) AND ("gene therapy"[MeSH Terms] OR "gene therapy"[Title/Abstract] OR "cell therapy"[MeSH Terms] OR "cell therapy"[Title/Abstract])'
    
    # 検索実行
    search_result = search_pubmed(query, max_results=2000)
    
    if not search_result:
        print("Search failed")
        return None
    
    # 詳細情報を取得
    articles = fetch_pubmed_details(search_result)
    
    if not articles:
        print("No articles fetched")
        return None
    
    # DataFrameに変換
    df = pd.DataFrame(articles)
    
    # Yearを整数に変換（可能な場合）
    df["Year"] = pd.to_numeric(df["Year"], errors='coerce')
    
    # 年でソート（新しい順）
    df = df.sort_values("Year", ascending=False).reset_index(drop=True)
    
    # 生データをJSON形式で保存
    raw_dir = Path("data/raw/literature")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    raw_file = raw_dir / f"pubmed_{timestamp}.json"
    
    raw_data = {
        "query": query,
        "search_result": search_result,
        "articles": articles,
        "timestamp": timestamp
    }
    
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)
    
    print(f"Raw data saved to: {raw_file}")
    
    # 処理済みデータをCSVで保存
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_dir / "papers.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")
    
    print(f"Processed data saved to: {output_file}")
    print(f"Total papers: {len(df)}")
    
    # 年ごとの論文数を表示
    year_counts = df["Year"].value_counts().sort_index(ascending=False)
    print("\nPapers by year (recent 10 years):")
    print(year_counts.head(10))
    
    return df


if __name__ == "__main__":
    df = fetch_papers()
    if df is not None:
        print("\nSample data (first 5 rows):")
        print(df.head())