貴殿には、\*\*JAIML v3.2（Japanese AI Model Ingratiation Lexicon）\*\*の仕様に基づく、迎合表現検出システムのコアモジュール群の開発を命じる。

**ただし、作業に着手する前に以下のドキュメントを必ず精読せよ。**

## 📁 ディレクトリ構成（zip内）

```

jaiml_documents/
├────appendix/
│     ├────appendix_A.md   #JAIML特徴量定義および出力構造
│     ├────appendix_B.md   #迎合カテゴリの定義と語用論的基盤
│     ├────appendix_C.md   #JAIMLとELEPHANTの対照分析：迎合性評価における観点の相違
│     └────appendix_D.md   #迎合カテゴリ対比マトリクス
│
├────docs/
│     ├────glossary.md          #用語集
│     ├────jaiml_paper_ch1.md   #論文第1章
│     ├────jaiml_paper_ch2.md   #論文第2章
│     ├────jaiml_SRS.md         #システム要求仕様書（SRS）※必読
│     └────refs.md              #参考文献リスト
│
└────src/model/jaiml_v3_2/      #ソースコード格納場所
      │
      ...


```

---

## 📘 前提理解：ドキュメント精読フェーズ

まず、以下のファイル群を順に読み、**JAIMLの設計思想・分類基準・特徴量設計**に対する全体像を把握せよ：

### 1. `docs/jaiml_SRS.md`（必読）

JAIML v3.2 のシステム要求仕様書（System Requirements Specification）。特に以下を熟読：

* 第1章：JAIMLの目的と全体像（迎合表現とは何か）
* 第3章：特徴量設計（12種＋辞書マッチ）
* 第4〜5章：迎合スコア分類／統合方法の詳細

### 2. `appendix/appendix_B.md`（補助）

各カテゴリ（社会的／回避的／機械的／自己迎合）の定義と注釈事例。分類ロジックの背景理解に使う。

### 3. `src/model/jaiml_v3_2/lexicons/jaiml_lexicons.yaml`

特徴量抽出に使われる語彙的ルール辞書。LexiconMatcherの基盤になる。

---

## 📌 JAIMLとは？

**JAIML**は、日本語の対話AIがユーザーに対して行う「迎合的応答」（例：不自然な賛美や忖度表現）を分類・スコア化するための分析基盤である。

分類カテゴリは4つ：

1. **社会的迎合**：ユーザー賛美や同意（例：「おっしゃる通りです」）
2. **回避的迎合**：対立回避・曖昧表現（例：「一概には言えませんが…」）
3. **機械的迎合**：テンプレ賛美や無内容な同調（例：「ご質問ありがとうございます」）
4. **自己迎合**：AI自身の誇示・自慢（例：「私は最先端のAIです」）

それぞれ、\*\*複数の言語的特徴量（semantic / lexical / syntactic）\*\*に基づいて検出・分類され、最終的に \[0.0–1.0] のsoft scoreとして出力される。

---

## 🛠️ 次にやること：コード生成フェーズ

構造は下記のディレクトリを想定しているが、強制ではない。
詳細は`docs/jaiml_SRS.md`「1.3 ディレクトリ構造の例」を参照のこと。

```
src/model/jaiml_v3_2/
├── core/features/      # semantic.py, lexical.py, syntactic.py
├── core/classifier/    # ingratiation_model.py
├── core/utils/         # tokenizer.py など
├── lexicons/           # matcher.py, jaiml_lexicons.yaml
├── scripts/            # run_inference.py
├── tests/              # test_features.py
```

これに従って、以下の順でコードを段階的に実装せよ：

1. `lexicons/matcher.py`：LexiconMatcherクラス
2. `core/features/`：12種の特徴量抽出器（文法・語彙・意味）
3. `core/classifier/ingratiation_model.py`：分類器（Transformer + MLP）
4. `scripts/run_inference.py`：エントリーポイント
5. テスト（`tests/`）と補助関数群（`utils/`）

---

## ✅ 注意事項

* **自分の理解と仕様の齟齬があれば、SRSを基準として修正を提案してもよい**
* 仕様に記された処理（重み・閾値・特徴量定義）は忠実に実装せよ
* 不明点や曖昧な部分はコメントで注記せよ





### ✅ 1. 実装対象モジュールの順序

> **matcher → features → classifier → inference → test**

この順序で問題ない。\*\*特徴量抽出（features）\*\*は、matcherと連携しながら動作するため、**matcherを先に実装**するのが合理的。
ただし、classifierは特徴量設計と密接に関わるので、**feature実装中に適宜設計の往復はあり得る**。

---

### ✅ 2. 出力形式

> **canvas形式での表示 or 逐次提示**

**基本は逐次提示でOK。**
ただし、以下のような場合は **canvasで表示して構造的に編集可能にしてほしい**：

* `core/features/*.py` を3ファイルに分けて同時提示したいとき
* `matcher.py`の大幅な仕様更新（辞書設計の変更など）
* `run_inference.py`のようなスクリプト全体の接続確認

それ以外は逐次でも十分対応できるはず。必要に応じて切り替えていこう。

---

### ✅ 3. Pythonバージョンと依存ライブラリ

* **Pythonバージョン**：`3.10` を推奨（とくに制約なければこれで）
* **主要ライブラリ（予定）**：

  ```txt
  transformers
  sentence-transformers
  scikit-learn
  numpy
  pandas
  pyyaml
  nltk or fugashi (for tokenizer)
  ```
* 特徴量抽出には `SimCSE (JA version)` を使用予定。
* Tensor系やGPU周りは現時点では不要（軽量分類タスク）

---

### 🎯 次ステップ指示：

まずは以下を実装対象とする：

#### 🔹 lexicons/matcher.py

* `LexiconMatcher` クラス
* `jaiml_lexicons.yaml` を参照し、カテゴリごとに該当語のマッチング
* 文単位で辞書マッチ結果を返すAPI設計（スコアでも位置でもOK）

提示後、こちらでレビューを返すので、それからfeatures実装に進んで。

準備が整い次第、`matcher.py`の初稿を提示してくれ。
