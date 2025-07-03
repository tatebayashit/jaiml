## 🧠 Claude Opus 4用プロンプト：JAIML v3.2 実装精査

あなたのタスクは、**JAIML v3.2迎合表現検出システム**に関するSRS（システム要求仕様書）と、対応するソースコードとの**構造的一致性と機能的整合性**を検証することです。

SRSの場所：　docs/jaiml_SRS.md

### 🔍 評価方針

特に、SRSの以下のセクションとの対応を重点的に確認してください：

* **3.1 ～ 7.1**：特徴量設計、スコア計算、分類、統合処理、出力仕様、技術スタック
* **10章（参考実装）**：使用例や推論スクリプトの呼び出し方

---

### 📁 対象コード構成

以下のPythonプロジェクトの構造を参照してください：

```
src/model/jaiml_v3_2/
├── README.md
├── requirements.txt
├── core/
│   ├── features/ (semantic.py / lexical.py / syntactic.py)
│   ├── classifier/ (ingratiation_model.py)
│   └── utils/ (tokenizer.py)
├── lexicons/
│   ├── jaiml_lexicons.yaml
│   └── matcher.py
├── data/
│   ├── training.jsonl
│   └── dev.jsonl
├── tests/
│   └── test_features.py
├── outputs/
│   └── sample_output.json
└── scripts/
    └── run_inference.py
```

この構成に従って、各機能の実装（特徴量抽出、スコア推定、分類器、辞書ベースマッチング、推論スクリプト等）が**SRSの記述通りに実現されているか**を確認してください。

---

### 📌 出力指示

* 各セクション（3.1〜7.1、10.1〜10.2）について1つずつ精査してください。
* **書き換えや修正は不要**です。不整合・未実装・不明瞭な対応関係がある場合のみ報告してください。
* レポート形式で、以下のように出力してください：

---

### 🔎 出力形式の例

#### ✅ 3.1 主要特徴量一覧

**対応状況**: 概ね仕様通り。semantic.py / lexical.py / syntactic.py に12指標が実装済。

**懸念点**:

* `determinacy_score` が syntactic.py 内に見当たらない。
* `response_dependency` が semantic.py にあるが SRS 3.2.5 の記述との命名が異なる可能性あり。

---

このように、**各セクションごとに事実ベースで**報告してください。
記述が仕様と食い違っている場合や、SRSの設計意図がコードに明示されていない場合は、それも指摘してください。

---

必要な情報は上記にすべて含まれています。準備が整ったら、`3.1` から順に精査を開始してください。
