# ✅ CI仕様 v1.0：JAIML統合CIパイプライン設計

## 🔧 目的

| カテゴリ          | 目的内容                                                    |
| ------------- | ------------------------------------------------------- |
| **再現性の保証**    | ハイパーパラメータ・トークナイザ等がすべてのモジュールで一致していることを検証                 |
| **安全性の担保**    | Pickle依存の危険性やscikit-learnのバージョン不一致などを事前に検出              |
| **構成ミス防止**    | YAML構文の不備・未定義パス・不要ファイルなど、設計と実装の差分を検知                    |
| **CI/CD統合準備** | github actions等のCI環境で自動的にユニットテストと構成検証を行い、ビルドエラーを早期検出可能に |

---

## 🧪 チェック項目と実装案

### 1. tfidf_config.yaml 検証（再現性）

| 項目             | 検証内容                                                        |
| -------------- | ----------------------------------------------------------- |
| YAMLスキーマ構文検証   | `ci/schema_validate.py` により `tfidf_config_schema.yaml` と照合  |
| グローバル設定との整合性確認 | `config/global.yaml` に記載された `min_df`, `ngram_range` 等と一致を確認 |
| 禁止値チェック        | `min_df=0` や `ngram_range=(0,0)` のような無効値を検知                 |

**使用技術案**：

```bash
pip install jsonschema
python ci/schema_validate.py
```

---

### 2. Pickle使用の静的警告（安全性）

| 項目              | 検証内容                                                             |
| --------------- | ---------------------------------------------------------------- |
| Pickleのimport検出 | `pickle.load` 使用箇所を grepし、警告コメントが付いているかをチェック                     |
| 推奨方式との差分        | `joblib.dump(..., compress=3)` が使用されていることを確認                     |
| metadata存在確認    | `vectorizers/metadata.json` が `tfidf_vectorizer.joblib` に付属しているか |

**使用技術案**：

```bash
grep -nr "pickle.load" src/
# 各箇所に「信頼済み環境でのみ使用」コメントがあるか確認
```

---

### 3. sklearn バージョン整合性チェック

| 項目          | 検証内容                                                   |
| ----------- | ------------------------------------------------------ |
| 保存時のバージョン記録 | `metadata.json` に `sklearn_version` が記載されているか          |
| 実行時の一致確認    | `corpus_based.py` にて `joblib` ロード後、バージョンが一致しているか検証する処理 |

```json
// metadata.json の例
{
  "model_version": "v1.0",
  "sklearn_version": "1.7.0"
}
```

---

### 4. JSONLフォーマット検査（入力形式）

| 項目        | 検証内容                                                                             |
| --------- | -------------------------------------------------------------------------------- |
| JSONパース検証 | `vector_pretrainer/corpus/jsonl/*.jsonl` が各行で `user`, `response`, `metadata` を持つ |
| 改行の存在     | 最終行に改行があることを確認（jsonlines仕様上の互換性確保）                                               |

**使用技術案**（擬似コード）：

```python
with open("sample.jsonl") as f:
    for i, line in enumerate(f):
        obj = json.loads(line)
        assert 'user' in obj and 'response' in obj
```

---

### 5. 統合ユニットテスト（CI/CD用）

| テスト内容                             | 実行ファイル                                             |
| --------------------------------- | -------------------------------------------------- |
| TF-IDFスコアが正常に出力されるか               | `tests/test_features.py`                           |
| load_model が vectorizer を正常に読込むか | `test_features.py::test_load_model_consistency`    |
| tokenizer が fugashi で統一されているか     | `test_tokenize.py` で `assert tokenizer=="fugashi"` |

---

## 🧩 CI導入例（GitHub Actions）

```yaml
# .github/workflows/ci.yaml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run YAML schema validation
        run: python src/ci/schema_validate.py
      - name: Run unit tests
        run: pytest src/model/jaiml_v3_3/tests
```

---

## 📌 今後の拡張案

| 項目                | 概要                                                        |
| ----------------- | --------------------------------------------------------- |
| YAML config 差分 CI | `tfidf_config.yaml` の改訂が `global.yaml` を変更せずに行われた場合にCIで検知 |
| Pickle 禁止 Linter  | flake8 + plugin で `pickle.load` 使用箇所を lint 時に警告           |
| データライセンス検査        | コーパス使用時に LICENSE ファイル存在と遵守項目をチェック                         |

---

## ✅ 結論

この CI 設計により、**ベクトル事前学習・特徴抽出・推論モジュールが全て構成的に同期され、安全・再現可能な分析環境が保証**される。開発者は CI で失敗を早期発見し、設計ドリフトを抑止できる。