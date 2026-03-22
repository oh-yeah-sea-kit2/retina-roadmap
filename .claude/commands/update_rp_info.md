---
description: 網膜色素変性症の最新情報を収集し、プロジェクトのデータとドキュメントを更新
argument-hint: '[full|quick|check]'
allowed-tools: WebSearch, Bash(python3:*), Bash(git:*), Bash(gemini:*), Read, Write, Task
---

## Context
- Mode: ${ARGUMENTS:-full}

## Task

網膜色素変性症治療法の最新情報を更新します。モード: **${ARGUMENTS:-full}**

### モード別処理

#### checkモード（最新情報の確認と既存データとの比較）
🔍 最新情報の確認と既存データとの比較を実行します
- 既存の知識ベースを読み込み
- Web検索で最新情報を収集
- 既存データと比較してレポート生成

#### quickモード（レポート再生成のみ）
📝 既存データでレポートを再生成します
- レポート再生成: python3 src/reporting/build_report.py

#### fullモード（完全更新）
🚀 完全な更新を実行します（デフォルト）
- 全ての処理を実行

### 実行手順

1. **Gemini検索で最新情報を収集**（checkモードとfullモードで実行）
                        ```bash
   # Gemini Searchを使用（より包括的な情報収集が可能）
   gemini --prompt "WebSearch: MCO-010 Nanoscope Therapeutics retinitis pigmentosa 2025 latest update Phase 3"
   gemini --prompt "WebSearch: OCU400 Ocugen retinitis pigmentosa 2025 latest update Phase 3"
   gemini --prompt "WebSearch: Botaretigene sparoparvovec Janssen (J&J) retinitis pigmentosa 2025 latest update Phase 3"
   gemini --prompt "WebSearch: AGTC-501 Beacon Therapeutics retinitis pigmentosa 2025 latest update Phase 2/3"
   gemini --prompt "WebSearch: jCells jCyte retinitis pigmentosa 2025 latest update Phase 2"
   gemini --prompt "WebSearch: Ultevursen Sepul Bio / Théa retinitis pigmentosa 2025 latest update Phase 2b"
   gemini --prompt "WebSearch: VP-001 PYC Therapeutics retinitis pigmentosa 2025 latest update Phase 1/2"
   gemini --prompt "WebSearch: retinitis pigmentosa gene therapy 2025 FDA approval new treatments"
   gemini --prompt "WebSearch: 網膜色素変性症 遺伝子治療 2025 最新 日本 承認"
   ```
   
   注: gemini-searchが利用できない場合は、通常のWebSearchツールを使用

2. **既存データとの比較**（checkモードで実行）
   ```python
   # Web検索結果を既存の知識ベースと比較
   import sys
   sys.path.append('.')
   from scripts.utils.data_comparison import (
       load_knowledge_base, 
       extract_program_info_from_text,
       compare_clinical_programs,
       format_comparison_report
   )
   
   # 知識ベースを読み込み
   kb = load_knowledge_base()
   
   # Web検索結果から情報を抽出（実際にはWeb検索結果を使用）
   # extracted_info = extract_program_info_from_text(web_search_results)
   
   # 比較実行
   # comparison = compare_clinical_programs(extracted_info, kb)
   
   # レポート生成
   # print(format_comparison_report(comparison))
   ```

3. **更新スクリプトの実行**（fullモードのみ）
   ```bash
   python3 scripts/update_latest_info.py
   ```

4. **データ処理**（fullモードのみ）
   ```bash
   python3 src/ingest/parameters.py
   ```

5. **シミュレーション実行**（fullモードのみ）
   ```bash
   python3 src/sim/timeline_sim.py
   ```

6. **レポート生成**（quickモードとfullモードで実行）
   ```bash
   python3 src/reporting/build_report.py
   ```

7. **結果確認**
   ```bash
   open docs/index.html
   ```

8. **変更内容の確認**
   ```bash
   git status --short
   ```

### チェック結果の見方（checkモード）

- 🆕 **新規プログラム**: 完全に新しい治療法や企業
- 🔄 **更新されたプログラム**: Phase進行、規制承認など
- ✅ **変更なし**: 既に把握している情報
- 🚨 **重要な更新**: FDA申請、Phase移行、承認など（重要度スコア付き）

### 更新頻度の推奨

- **週次**: `/update_rp_info check` → 新情報の確認
- **月次**: `/update_rp_info full` → 重要な更新があれば完全更新
- **四半期**: `/update_rp_info full` → 定期的な包括更新

### 注意事項

1. checkモードは情報収集と比較のみ（データ更新なし）
2. 重要度スコア70以上の更新は要注意
3. fullモード実行前にcheckモードで確認推奨

## 知識ベースの現在の状態
@data/knowledge_base/clinical_programs.json