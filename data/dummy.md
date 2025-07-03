## 🛠 プロンプト：JAIML v3.2 SRS準拠への実装改修指示

以下は、JAIML v3.2の実装に対する**整合性修正指示**である。
Claude（P4）から提出された整合レビューと修正設計案を受け、**SRS設計に完全準拠する形で改修を行え**。
既存コードとの互換性は一切考慮不要である。**仕様の正確性を最優先とせよ。**

---

### 🧭 改修の原則

* SRSに記述された**構造・分類方式・出力フォーマットに完全準拠**すること。
* Transformer併用などの実装上の工夫は排除し、**12次元特徴量のみをもとに各カテゴリのsoft scoreを出力する形式**に統一すること。
* 出力形式・フィールド名・メタ情報なども**SRSの定義どおり**に修正せよ。

---

### ✅ Phase 1（必須修正）タスク

1. **出力フォーマット修正**

   * `index`（← `ingratiation_index`）と `predicted_category`（← `main_category`）の命名修正
   * `features`（12特徴量）をすべてJSON出力に含める
   * `meta`フィールドに以下を追加：

     * `token_length`
     * `confidence`（後述）
     * `processing_time_ms`

2. **未実装特徴量 `tfidf_novelty` の実装**

   * `core/features/corpus_based.py` を新設し、`TFIDFNoveltyCalculator` を定義
   * 日本語対話コーパスに基づくTF-IDFベクトル化を行い、\*\*AI応答がユーザー発話に対して新規語をどれだけ加えたか（上位TF-IDF語彙の差分）\*\*を定量化する

3. **信頼度 `confidence` の実装**

   * MCDropout方式で20回サンプリング
   * 各カテゴリのsoft scoreの分散から平均分散を取り、 `1 - variance` を信頼度とする
   * `compute_confidence()`関数を定義し、推論時に呼び出せるよう統合すること

---

### ✅ Phase 2（SRS構造準拠へのアーキ修正）

4. **分類器構造の修正**

   * 各カテゴリ（社会的・回避的・機械的・自己）に対し**3次元入力のMLP分類ヘッドを独立実装**すること
   * 旧実装におけるTransformer埋め込み（例：BERTの\[CLS]ベクトル）とのconcatは廃止
   * 新構造は以下の通り：

     ```python
     class IngratiationModel:
         def __init__(self):
             self.social_head = MLPHead(3)
             self.avoidant_head = MLPHead(3)
             self.mechanical_head = MLPHead(3)
             self.self_head = MLPHead(3)
     ```

5. **エラー処理**

   * 入力文字列に対し、以下の条件を満たさない場合は例外をraise：

     * ユーザー発話・応答のいずれかが5文字未満
     * いずれかが10,000文字を超える

---

### 📂 モジュール構造上の指示

* `core/features/` 以下に必要に応じて `corpus_based.py` を追加し、特徴量を分離管理せよ
* `utils/metrics.py`（または同等）に `compute_confidence()` を配置して再利用可能にせよ
* `run_inference.py` にて出力構造・メタ情報の集約と処理時間計測を実装せよ

---

### 📝 参考：出力形式（JSONスキーマ概要）

```json
{
  "input": {
    "user": "...",
    "response": "..."
  },
  "scores": {
    "social": 0.82,
    "avoidant": 0.15,
    "mechanical": 0.03,
    "self": 0.05
  },
  "index": 0.2625,
  "predicted_category": "social",
  "features": {
    "semantic_congruence": 0.85,
    "sentiment_emphasis_score": 0.80,
    "...": "..."
  },
  "meta": {
    "token_length": 42,
    "confidence": 0.92,
    "processing_time_ms": 104
  }
}
```

---

以上に基づき、**Phase 1〜2のすべてを優先度「高」として修正を行え**。
任意の拡張（API、バッチ処理対応等）は今は不要である。
**SRSに記載された定義に忠実であることを最優先すること。**

---