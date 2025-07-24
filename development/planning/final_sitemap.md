# 最終サイトマップ確認書

## 新サイト構造（6ページ）

```
retina-roadmap/docs/public/
├── index.html              # ランディングページ（新規作成）
├── patient_guide.html      # 患者・家族向け統合ページ
├── medical_info.html       # 医療従事者向け統合ページ
├── detailed_analysis.html  # 詳細分析統合ページ（タブ形式）
├── faq.html               # よくある質問（新規作成）
├── disclaimer.html        # 免責事項（既存を簡潔に）
├── css/
│   ├── common.css         # 共通スタイル（新規）
│   └── print.css          # 印刷用スタイル（新規）
├── js/
│   └── common.js          # 共通JavaScript（新規）
└── images/
    ├── CDF.png
    ├── tornado.png
    └── waterfall.png
```

## 各ページの役割と内容

### 1. index.html（ランディングページ）
**目的**: 訪問者を適切なコンテンツへ誘導
**主要コンテンツ**:
- ヒーローセクション（インパクトのある見出し）
- 3つの重要数字（2027年、2032年、15種類）
- 3つの選択パス（患者向け、医療者向け、詳細分析）
- 最新更新情報（1-2行）

### 2. patient_guide.html（患者向け統合）
**統合元**:
- reality_and_actions.html（全内容）
- regional_approval_timeline.html（日本部分）
- accessible_summary.html（要点）
- index.html（TOP5プログラム）

**構成**:
1. クイックアンサー（FAQ形式の導入）
2. 最も期待される治療法TOP5（カード形式）
3. 今すぐできる5つのアクション（詳細手順付き）
4. 日本での承認時期予測
5. 関連リソースへのリンク

### 3. medical_info.html（医療従事者向け）
**統合元**:
- executive_summary_for_doctor.html（全内容）
- for_doctor_checklist.html（全内容）
- simulation_methodology.html（要約部分）

**構成**:
1. エグゼクティブサマリー（研究概要）
2. 臨床的重要情報（治療モダリティ別）
3. エビデンスチェックリスト（インタラクティブ）
4. 方法論の要約
5. 参考文献・臨床試験リンク

### 4. detailed_analysis.html（詳細分析）
**統合元**:
- 現index.html（詳細テーブル部分）
- ai_predictions.html（全内容）
- bottlenecks.html（全内容）
- ai_acceleration_impact.html（全内容）
- simulation_methodology.html（詳細部分）

**構成**（タブ形式）:
- タブ1: 予測結果（完全なデータテーブル）
- タブ2: 方法論（モンテカルロ詳細）
- タブ3: AI影響分析
- タブ4: 開発課題分析

### 5. faq.html（よくある質問）
**新規作成**
**構成**:
- 治療時期について（5-6問）
- 治療法について（5-6問）
- 参加方法について（3-4問）
- その他（3-4問）

### 6. disclaimer.html（免責事項）
**既存のpublication_disclaimer.htmlを簡潔に**
**構成**:
- 医学的助言でないことの明記
- 予測の不確実性
- 著作権情報
- 連絡先

## 削除されるページ（7ページ）

1. current_status_facts.html → 各ページに分散統合
2. accessible_summary.html → patient_guide.htmlに統合
3. publication_checklist.html → 開発ドキュメントへ移動
4. reality_and_actions.html → patient_guide.htmlに統合
5. executive_summary_for_doctor.html → medical_info.htmlに統合
6. for_doctor_checklist.html → medical_info.htmlに統合
7. simulation_methodology.html → 要約をmedical_info.html、詳細をdetailed_analysis.htmlへ

## URLリダイレクト計画

旧URLから新URLへのマッピング:
```
/reality_and_actions.html → /patient_guide.html
/accessible_summary.html → /patient_guide.html
/executive_summary_for_doctor.html → /medical_info.html
/for_doctor_checklist.html → /medical_info.html
/simulation_methodology.html → /detailed_analysis.html#methodology
/ai_predictions.html → /detailed_analysis.html#predictions
/bottlenecks.html → /detailed_analysis.html#bottlenecks
/ai_acceleration_impact.html → /detailed_analysis.html#ai-impact
```

## 実装の優先順位

1. **必須（Phase 1-2）**: index.html, patient_guide.html, 共通CSS/JS
2. **推奨（Phase 3）**: medical_info.html, detailed_analysis.html
3. **オプション（Phase 4）**: faq.html, disclaimer.html更新

## 確認事項

- [ ] ページ数の削減（13→6）は適切か
- [ ] 各ターゲット層への情報提供は十分か
- [ ] 重要情報へのアクセスは改善されるか
- [ ] モバイルユーザビリティは向上するか
- [ ] メンテナンス性は改善されるか