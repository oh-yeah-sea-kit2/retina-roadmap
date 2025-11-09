---
title: "【追加】ネクストビジョンを情報源として追加"
labels: enhancement, documentation, high-priority
---

## 📋 問題の概要

患者・ご家族向けページに、視覚障害や眼科関連のイベント・啓発活動を行っているネクストビジョン（https://nextvision.or.jp）の情報が含まれていません。

患者・ご家族からのフィードバックで、有益なリソースとして追加の要望がありました。

## 🎯 追加内容

### 追加対象ファイル
- `docs/content/main/reality_and_actions.md`

### 追加場所
「根拠資料とリンク集」セクションの「日本での情報源」部分（現在383-386行目付近）

### 追加案

**現在の記載:**
```markdown
### 日本での情報源
- **JRPS（日本網膜色素変性症協会）**: https://jrps.org/
- **jRCT（臨床研究等提出・公開システム）**: https://jrct.niph.go.jp/
- **PMDA（医薬品医療機器総合機構）**: https://www.pmda.go.jp/
```

**修正後:**
```markdown
### 日本での情報源
- **JRPS（日本網膜色素変性症協会）**: https://jrps.org/
  - 年会費5,000円で治験情報、医療講演会、患者交流会に参加可能
- **ネクストビジョン**: https://nextvision.or.jp
  - 視覚障害・眼科関連のイベント、啓発活動
  - 最新の研究動向、患者支援プログラム情報
  - 無料で閲覧可能
- **jRCT（臨床研究等提出・公開システム）**: https://jrct.niph.go.jp/
- **PMDA（医薬品医療機器総合機構）**: https://www.pmda.go.jp/
```

## ✅ チェックリスト

- [ ] `reality_and_actions.md`にネクストビジョンを追加
- [ ] HTMLを再生成（`python src/reporting/build_report.py`）
- [ ] 生成されたHTMLでリンクがクリッカブルになっているか確認
- [ ] コミット & プッシュ

## 📌 優先度

**高**: 患者・ご家族にとって有益な情報源のため、早めの追加が望ましい

## 🔗 関連情報

- ネクストビジョン: https://nextvision.or.jp
- 患者・ご家族からのLINEフィードバックに基づく改善
