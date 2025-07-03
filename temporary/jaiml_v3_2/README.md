# JAIML v3.2

JAIML (Judgment-based AI Ingratiation Measurement & Labeling) は、AI対話システムにおける迎合的応答を分類・定量化するための評価モジュール群です。本リポジトリは、v3.2仕様に基づく特徴量抽出器・分類器・辞書処理系・推論スクリプトを含みます。

---

## 🔧 構成概要

```

jaiml_v3_2/
├── core/           # 特徴量抽出・分類器本体
├── lexicons/       # 辞書定義とマッチャー
├── data/           # 学習・検証用データ
├── scripts/        # 実行用スクリプト
├── outputs/        # 出力ファイル保存先
└── tests/          # ユニットテスト群

````

---

## 🧮 特徴量分類（12種）

- semantic.py：意味的特徴（類似度・応答依存など）
- lexical.py：語彙的特徴（肯定語・反復率など）
- syntactic.py：構文的特徴（推量構文・主語構文など）

---

## 🚀 推論実行

```bash
python scripts/run_inference.py --input data/dev.jsonl --output outputs/sample_output.json
````

---

## 📚 辞書定義

`lexicons/jaiml_lexicons.yaml` に全特徴量で使用する語彙辞書を記載。辞書ベース照合は `LexiconMatcher` クラスで処理。

---

## 📦 インストールと依存関係

```bash
pip install -r requirements.txt
```

推奨環境：

* Python 3.11 以上
* PyTorch + Transformers
* scikit-learn + sentence-transformers

---

## 📊 テスト実行

```bash
pytest tests/
```

---