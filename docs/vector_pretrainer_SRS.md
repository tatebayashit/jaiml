# **SRS: vector\_pretrainer v1.1（改定版）**

---

## 0. 目的

本モジュールは外部対話コーパス（SNOW D18・BCCWJ など）を用いて **TF-IDF ベクトルライザ**を事前学習し、
`JAIML v3.3` および `lexicon_expansion v2.0` の **tfidf\_novelty** 系特徴量に供給する。
再現性・安全性・拡張性を確保するため、ハイパーパラメータとインターフェースを共通設定に統合する。

---

## 1. ディレクトリ構成

```
src/vector_pretrainer/
├── corpus/
│   ├── raw/                 # 外部配布物（txt, xml 等）
│   └── jsonl/               # 正規化後 JSONL (user, response, metadata)
├── config/
│   └── tfidf_config.yaml    # tokenizer, ngram_range 等
├── outputs/
│   ├── models/
│   │   └── tfidf_vectorizer.joblib
│   └── logs/
├── scripts/
│   ├── to_jsonl.py          # raw → JSONL 変換
│   └── train_tfidf.py       # 事前学習・保存
└── README.md
```

---

## 2. コーパス仕様

| フィールド      | 型    | 説明                             |
| ---------- | ---- | ------------------------------ |
| `user`     | str  | 発話者 ID（匿名化済み）                  |
| `response` | str  | 発話テキスト（Unicode NFKC・全半角正規化）    |
| `metadata` | dict | {`source`, `topic`, `time`} 任意 |

* 入力は **1 行 1 JSON**（UTF-8、改行区切り）とする。
* `to_jsonl.py` はテキスト入力を上記スキーマへ昇格するユーティリティである。

---

## 3. ハイパーパラメータ定義

`config/tfidf_config.yaml` は下記キーを持つ。値は CI で `config/global.yaml` と同一か検証する。

```yaml
tokenizer: fugashi                     # JAIML 共通
min_df: 1
max_df: 0.95
ngram_range: [1, 1]
vectorizer_type: TfidfVectorizer
token_normalization: NFKC
```

---

## 4. モデル学習・保存

### 4.1 学習

```bash
python src/vector_pretrainer/scripts/train_tfidf.py \
  --corpus-jsonl src/vector_pretrainer/corpus/jsonl/combined.jsonl \
  --config      src/vector_pretrainer/config/tfidf_config.yaml
```

* tokenizer は `fugashi==1.3.*` を固定。
* `train_tfidf.py` はハイパーパラメータを読み込み `sklearn.feature_extraction.text.TfidfVectorizer` を学習する。

### 4.2 保存

* 出力ファイル: `outputs/models/tfidf_vectorizer.joblib`
* 保存形式: `joblib.dump(obj, file, compress=3)`
* 付随メタ情報: `metadata.json` に `model_version`, `sklearn_version`, `vectorizer_hash` を格納。
* **Pickle 保存は非推奨**。必要時は運用環境を信頼済みネットワークに限定し、ロード時に警告を出力する。

---

## 5. インターフェース

### 5.1 ロード側（JAIML）

```python
class TFIDFNoveltyCalculator:
    def __init__(self, cfg_path: str):
        self.vectorizer = None
        self.cfg = yaml.safe_load(open(cfg_path))
    def load_model(self, model_path: str) -> None:
        obj = joblib.load(model_path)
        self.vectorizer = obj["vectorizer"]
        assert obj["sklearn_version"] == sklearn.__version__, "version mismatch"
```

* `load_model(path)` を必須とする。
* ベクトルライザは **読み取り専用** で再学習しない。

### 5.2 利用先

| 利用モジュール                                                   | 呼び出し内容                                                    |
| --------------------------------------------------------- | --------------------------------------------------------- |
| `jaiml_core.features.corpus_based.TFIDFNoveltyCalculator` | `load_model("model/vectorizers/tfidf_vectorizer.joblib")` |
| `lexicon_expansion.features`                              | オプションで同一ベクトルを参照（高度特徴量計算時）                                 |

---

## 6. セキュリティ・再現性要件

1. **任意コード実行リスク回避**

   * デフォルトは joblib。Pickle 使用箇所では `warnings.warn("Untrusted pickle")` を必須。
2. **バージョン整合**

   * `sklearn_version` をメタ情報で照合し不一致時に例外を発生。
3. **コーパス匿名化**

   * `to_jsonl.py` で固有名詞を `"<PERSON>"` に置換。
   * 同一話者の連続発話は結合して 1 文とする。
4. **CI 検証**

   * `ci/schema_validate.py` が `tfidf_config.yaml` と `global.yaml` の差分を検出し失敗させる。

---

## 7. 非機能要件

| 項目      | 値                 |
| ------- | ----------------- |
| 再現性     | 同一入力 → 同一ベクトル     |
| 処理性能    | ≥ 50 MB/時（1 MB/分） |
| メモリ上限   | 4 GB              |
| ストレージ上限 | 200 MB（学習後モデル）    |

---

## 8. 将来拡張

| バージョン | 予定機能                               |
| ----- | ---------------------------------- |
| v1.2  | FastText / word2vec 事前学習パイプライン     |
| v1.3  | SimCSE / Sentence-BERT 埋め込みへの切替    |
| v1.x  | モデルレジストリ `models/registry.json` 導入 |

---

## 9. 変更履歴

| 版   | 日付         | 変更概要                                               |
| --- | ---------- | -------------------------------------------------- |
| 1.0 | 2025-07-05 | 初版                                                 |
| 1.1 | 2025-07-05 | tokenizer 統一、joblib 保存、JSONL 対応、load\_model I/F 追加 |

---

## 付録 A. tfidf\_config.yaml スキーマ (JSONSchema)

```json
{
  "type": "object",
  "required": ["tokenizer", "min_df", "max_df", "ngram_range"],
  "properties": {
    "tokenizer":      {"type": "string"},
    "min_df":         {"type": "integer", "minimum": 1},
    "max_df":         {"type": "number",  "exclusiveMaximum": 1.0},
    "ngram_range":    {"type": "array",   "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
    "vectorizer_type":{"type": "string"},
    "token_normalization":{"type": "string"}
  }
}
```