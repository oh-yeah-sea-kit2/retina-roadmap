# HTMLファイル コンテンツ量分析レポート

## 1. 各ファイルのサイズ分析

### 文字数ランキング（大きい順）
1. **reality_and_actions.html**: 31,636文字（577行）
2. **index.html**: 19,437文字（463行）+ 画像3枚
3. **current_status_facts.html**: 18,160文字（478行）
4. **ai_predictions.html**: 17,406文字（472行）
5. **accessible_summary.html**: 17,222文字（393行）
6. **simulation_methodology.html**: 16,388文字（418行）
7. **ai_acceleration_impact.html**: 14,674文字（399行）
8. **executive_summary_for_doctor.html**: 12,917文字（293行）
9. **bottlenecks.html**: 12,850文字（370行）
10. **regional_approval_timeline.html**: 11,843文字（362行）
11. **publication_disclaimer.html**: 10,330文字（263行）
12. **publication_checklist.html**: 10,046文字（286行）
13. **for_doctor_checklist.html**: 9,267文字（272行）

**合計**: 202,176文字（5,046行）

### 画像の使用状況
- **index.html**: 3枚（CDF.png, tornado.png, waterfall.png）
- その他のファイル: 0枚

## 2. 重複コンテンツの詳細分析

### 2.1 最速承認予測（OCU400/2027年）の重複

以下のファイルで同じ情報が繰り返されている：

1. **index.html**
   - 行129: 最速の承認予測: 2026年（MCO-010）
   - 行213,223,324,331: OCU400 - 2027年承認予測
   - 行365: 最速FDA承認予測: 2026年

2. **ai_predictions.html**
   - 行190: 最速2027年が2025-2026年に前倒し可能性
   - 行216,239,278-279: OCU400 - 2027年承認
   - 行307-308: 2026年MCO-010、2027年OCU400

3. **reality_and_actions.html**
   - 行201: 最速2025-2026年の承認が現実的
   - 行203: MCO-010 - 2025年後半〜2026年
   - 行209: OCU400 - 2026年BLA/MAA申請

4. **regional_approval_timeline.html**
   - 行209,214,259-260: OCU400 - 2027年
   - 行320,325,330: OCU400日本承認時期

5. **accessible_summary.html**
   - 行166: 最速で2025年後半から2026年
   - 行197-199: 2026-2027年 OCU400

6. **current_status_facts.html**
   - 行250,336,387,394-395,398: OCU400関連情報

7. **executive_summary_for_doctor.html**
   - 行201,213,215: OCU400 - 2026〜2027年承認

8. **for_doctor_checklist.html**
   - 行202: OCU400の2026-2027年承認予測

### 2.2 5つのアクションの重複

**reality_and_actions.html**に詳細版があり、以下で要約版が重複：
- **index.html**: 簡易版として言及
- **accessible_summary.html**: 音声読み上げ版として同内容

### 2.3 日本承認時期の重複

**regional_approval_timeline.html**がメインだが、以下でも言及：
- **index.html**: 各プログラムの日本承認列
- **ai_predictions.html**: 日本承認の遅延について
- **reality_and_actions.html**: 日本での承認時期

### 2.4 研究方法論の重複

**simulation_methodology.html**に詳細があるが、要約が以下に存在：
- **index.html**: 方法論の簡単な説明
- **executive_summary_for_doctor.html**: 医師向け要約
- **ai_predictions.html**: シミュレーション手法の言及

## 3. 統合の優先順位

### 高優先度（重複が多く、統合効果が高い）
1. **予測結果の統合**
   - index.html、ai_predictions.html、current_status_facts.htmlの予測部分
   - 削減可能: 約30%のコンテンツ

2. **患者向け情報の統合**
   - reality_and_actions.html、accessible_summary.html、regional_approval_timeline.html（日本部分）
   - 削減可能: 約25%のコンテンツ

3. **医療従事者向けの統合**
   - executive_summary_for_doctor.html、for_doctor_checklist.html、simulation_methodology.html（要約）
   - 削減可能: 約20%のコンテンツ

### 中優先度
4. **技術詳細の統合**
   - simulation_methodology.html、bottlenecks.html、ai_acceleration_impact.html
   - タブ形式での整理が効果的

### 低優先度
5. **メタ情報**
   - publication_disclaimer.html、publication_checklist.html
   - 独立したページとして残すか、フッターに統合

## 4. 推定作業量

### コンテンツ移行作業
- **高複雑度**: reality_and_actions.html（31,636文字）→ 4-6時間
- **中複雑度**: index.html、ai_predictions.html等 → 各2-3時間
- **低複雑度**: チェックリスト、免責事項等 → 各1時間

### 新規作成作業
- **新index.html**: デザイン含めて4-6時間
- **統合ページ**: 各3-4時間
- **共通コンポーネント**: 4-6時間

**総作業時間見積もり**: 40-60時間