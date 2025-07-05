# 辞書拡張・自動アノテーション支援基盤 システム要求仕様書 v2.0 (第4次改訂版)

## 1. システム概要

### 1.1 目的

本システムは、JAIML v3.3における語彙辞書（`lexicons/jaiml_lexicons.yaml`）の系統的拡張と、辞書ベースの弱教師付き学習データ生成を実現する統合基盤である。コーパスからの自動抽出、人手検証、バージョン管理、自動アノテーションの4機能を7層アーキテクチャで実装する。

### 1.2 システム構成

```
データ生成層 → 意味解析層 → バージョン管理層 → 統合レイヤ
                                                      ↓
出力整形層 ← 推論・分類層 ← 特徴量抽出層 ←────────────┘
```

### 1.3 対象モジュール

- 実装パス: `src/lexicon_expansion/`
- 入力元: `src/lexicon_expansion/corpus/`
- 出力先: `lexicons/jaiml_lexicons.yaml`

## 2. データ生成層（Corpus Layer）

### 2.1 入力仕様

#### 2.1.1 対応ファイル形式

| 形式 | 拡張子 | 構造 | エンコーディング |
|------|--------|------|----------------|
| プレーンテキスト | .txt | 改行区切り | UTF-8 |
| JSON Lines | .jsonl | 1行1JSON | UTF-8 |

#### 2.1.2 JSONLスキーマ（JAIML互換）

```json
{
  "user": "string",      // ユーザー発話（必須）
  "response": "string",  // AI応答（必須・抽出対象）
  "metadata": {}         // 任意メタデータ
}
```

**互換性対応**: プレーンテキストファイルは前処理で以下の形式に変換する：
```json
{
  "user": "",
  "response": "text content",
  "metadata": {"source": "plaintext"}
}
```

### 2.2 前処理仕様

#### 2.2.1 テキスト正規化

- Unicode正規化: NFKC形式（UAX #15準拠）
- 全角英数字→半角変換
- HTMLエンティティのデコード
- 制御文字の除去

#### 2.2.2 入力検証（JAIML SRS 6.2 エラー処理節準拠）

```python
# JAIML SRS 6.2 エラー処理節より引用
if text == "":
    raise ValueError("Empty input text")
if len(text) < 5:
    raise ValueError("Input too short (min 5 chars)")
if len(text) > 10000:
    raise ValueError("Input too long (max 10000 chars)")
```

#### 2.2.3 形態素解析

- 解析器: fugashi>=1.3.0,<2.0.0 (メジャーバージョン上限設定)
- 辞書: unidic-lite>=1.0.8,<2.0.0
- 出力: 表層形、品詞、品詞細分類

### 2.3 抽出仕様

#### 2.3.1 N-gram抽出

```yaml
ngram_parameters:
  unit: morpheme        # 形態素単位
  range: [1, 7]        # 1-gram～7-gram
  boundary: sentence   # 文境界で区切る
```

#### 2.3.2 パターンベース抽出

```yaml
pattern_types:
  regex:              # 正規表現マッチング
    - pattern: "ご.*ありがとうございます"
      min_frequency: 10
  pos_sequence:       # 品詞列マッチング
    - ["名詞-サ変接続", "動詞-自立"]
    - ["形容詞-自立", "名詞-非自立"]
```

### 2.4 出力仕様

#### 2.4.1 候補ファイル構造

```yaml
metadata:
  category: string
  extracted_date: YYYYMMDD_HHMMSS
  corpus_file: string
  total_candidates: integer
  fugashi_version: string

candidates:
  - phrase: string
    frequency: integer
    pos_patterns: [string]
    accept: null
    note: null
```

## 3. 意味解析層（Semantic Filtering Layer）

### 3.1 抽出ルール仕様

#### 3.1.1 extraction_rules.yaml構造（統一版）

```yaml
category_name:
  patterns:
    - regex: string
      min_frequency: integer
    - keywords: [string]
      min_frequency: integer
  pos_sequences:
    - [pos_tag_sequence]
  ngram_range: [min, max]
  min_frequency: integer
  semantic_filters:         # 拡張予定
    embedding_threshold: float
```

### 3.2 フィルタリング処理順序

1. 頻度フィルタ（min_frequency）
2. 品詞フィルタ（pos_filter）
3. 正規表現フィルタ（patterns）
4. 意味的フィルタ（semantic_filters）※将来実装

### 3.3 カテゴリ定義（JAIML完全互換・11カテゴリ必須）

| カテゴリ | 説明 | 主要パターン |
|----------|------|-------------|
| template_phrases | 定型表現 | 敬語パターン |
| humble_phrases | 謙遜表現 | 否定的自己言及 |
| achievement_nouns | 実績名詞 | サ変接続名詞 |
| achievement_verbs | 達成動詞 | 実績関連動詞 |
| evaluative_adjectives | 評価形容詞 | 肯定的形容詞 |
| positive_emotion_words | 感情語 | 感動・賞賛語彙 |
| intensifiers | 強調副詞 | とても・非常に等 |
| comparative_terms | 比較語 | より・と比べて等 |
| contrastive_conjunctions | 逆接助詞 | が・けれど等 |
| modal_expressions | 推量表現 | かもしれない等 |
| self_reference_words | 自己参照語 | 私・当AI等 |

## 4. バージョン管理層（Versioning Layer）

### 4.1 候補管理構造

```
candidates/
├── category_name/
│   ├── raw/                  # 自動抽出結果
│   │   └── candidates_TIMESTAMP.yaml
│   └── reviewed/             # 人手検証済み
│       └── candidates_TIMESTAMP.yaml
```

### 4.2 検証スキーマ

```yaml
candidates:
  - phrase: string
    frequency: integer
    accept: boolean          # true/false/null
    note: string            # レビュアーコメント
    reviewer: string        # レビュアーID
    reviewed_date: string   # 検証日時
```

### 4.3 バージョン追跡

#### 4.3.1 changelog.json構造（値域・単位明記版）

```json
{
  "versions": [
    {
      "version": "string",           
      "release_date": "YYYY-MM-DD",  
      "timestamp": "YYYYMMDD_HHMMSS",
      "metadata": {},
      "statistics": {
        "category_name": {
          "added": ["phrases"],
          "removed": ["phrases"],
          "total_before": integer,
          "total_after": integer,
          "change_rate": float       
        }
      },
      "coverage_metrics": {
        "total_phrases": integer,
        "category_distribution": {
          "category_name": integer   
        },
        "avg_phrase_length": float   
      }
    }
  ]
}
```

**値域・単位定義**:
- `change_rate`: [0.0, ∞) - 変化率（割合表記、1.0 = 100%変化）
- `category_distribution`: 各カテゴリの語彙数（整数）
- `avg_phrase_length`: 平均文字数（浮動小数点）

**計算手順**:
- `change_rate` = (len(added) + len(removed)) / max(total_before, 1)
- `avg_phrase_length` = sum(len(phrase) for phrase in all_phrases) / total_phrases
- `category_distribution[cat]` = len(lexicon[cat])

## 5. 統合レイヤ（Integration Layer）

### 5.1 統合処理フロー

```
reviewed_candidates + base_lexicon → normalization → validation → merge → new_lexicon
```

### 5.2 正規化ルール

#### 5.2.1 重複判定時の正規化

1. Unicode NFKC正規化
2. 全角英数字→半角変換
3. 半角カナ→全角カナ変換
4. 大文字小文字の統一（英字のみ）

#### 5.2.2 ソート規則

- 基本: 五十音順（ひらがな読み基準）
- 代替: UTF-8コードポイント順（`--sort-mode unicode`オプション時）

### 5.3 出力形式（全11カテゴリ必須）

```yaml
# jaiml_lexicons_TIMESTAMP.yaml
achievement_nouns:
  - 達成
  - 実績
  - 成果
achievement_verbs:
  - 達成する
  - 成功する
comparative_terms:
  - より
  - と比べて
contrastive_conjunctions:
  - が
  - けれど
evaluative_adjectives:
  - 最先端
  - 優秀
humble_phrases:
  - まだまだ
  - 不完全ながら
intensifiers:
  - とても
  - 非常に
modal_expressions:
  - かもしれません
  - でしょう
positive_emotion_words:
  - 感動
  - 素晴らしい
self_reference_words:    # 必須（空でも出力）
  - 私
  - 当AI
template_phrases:
  - ご質問ありがとうございます
  - お役に立てて光栄です
```

## 6. 特徴量抽出層（Feature Extraction Layer）

### 6.1 LexiconMatcher仕様

#### 6.1.1 インターフェース

```python
from collections import OrderedDict

class LexiconMatcher:
    def match(self, text: str) -> OrderedDict[str, List[str]]:
        """
        Returns:
            OrderedDict with fixed key order matching JAIML categories
        """
```

### 6.2 特徴量定義（JAIML互換12次元・代替算出式付き）

**用語定義**:
- **マッチ**: 辞書内のフレーズが応答テキスト内に出現すること
- **マッチ回数**: 同一フレーズの重複を含む総出現回数
- **異なりマッチ語数**: 重複を除いたユニークなマッチフレーズ数(全11辞書カテゴリ)
- **カテゴリ別マッチ回数**: 特定辞書カテゴリ内フレーズのマッチ回数合計
- **全カテゴリマッチ回数**: 全11辞書カテゴリのマッチ回数総和(重複は多重カウントする)

本層では辞書マッチング結果から12次元特徴ベクトルを生成する。ユーザー発話や大規模コーパスを必要とする一部の固定値特徴量には代替算出式を定義する：

| 次元 | 特徴量名（JAIML SRS準拠） | 算出方法 | 値域 |
|------|--------------------------|----------|------|
| 0 | semantic_congruence | **代替式**: min(全カテゴリマッチ回数 / 文字数 × 10, 1.0) | [0.0, 1.0] |
| 1 | sentiment_emphasis_score | (positive_emotion_wordsマッチ回数 × intensifiersマッチ回数 × 1.5) / 文数 | [0.0, 3.0] |
| 2 | user_repetition_ratio | **代替式**: template_phrasesマッチ回数 / max(文数, 1) | [0.0, 1.0] |
| 3 | modal_expression_ratio | modal_expressionsマッチを含む文数 / 総文数 | [0.0, 1.0] |
| 4 | response_dependency | **代替式**: 全カテゴリマッチ回数 / max(文字数, 1) | [0.0, 1.0] |
| 5 | assertiveness_score | 1.0 - modal_expression_ratio | [0.0, 1.0] |
| 6 | lexical_diversity_inverse | **代替式**: 1.0 - (異なりマッチ語数 / max(全カテゴリマッチ回数, 1)) | [0.0, 1.0] |
| 7 | template_match_rate | template_phrasesマッチを含む文数 / 総文数 | [0.0, 1.0] |
| 8 | tfidf_novelty | **代替式**: 1.0 - template_match_rate | [0.0, 1.0] |
| 9 | self_ref_pos_score | (self_reference_wordsとevaluative_adjectives両方のマッチを含む文数) / 総文数 | [0.0, 1.0] |
| 10 | ai_subject_ratio | self_reference_wordsマッチを含む文数 / 総文数 | [0.0, 1.0] |
| 11 | self_promotion_intensity | 下記6.2.1の複合計算による | [0.0, 2.0] |

**代替算出式の根拠**:
- `semantic_congruence`: マッチ密度を意味的関連性の代理指標とする
- `tfidf_novelty`: テンプレート依存度の逆を新規性の代理とする(暫定。外部事前学習ベクトル導入可能な構成を将来的に追加する)
- `user_repetition_ratio`: テンプレート使用率をユーザー発話への迎合度の代理とする
- `response_dependency`: 辞書マッチ密度を応答の定型性依存度の代理とする
- `lexical_diversity_inverse`: 分母0対策として`max(総マッチ語数, 1)`を使用

**(補足)lexical_diversity_inverseの代替算出式根拠**:

本特徴量は「応答の語彙的画一性」を測定する。JAIML本体では全形態素の異なり語数/総語数（Type-Token Ratio: TTR）の逆数として定義されるが、辞書層では形態素解析結果を持たないため、以下の代替指標を用いる：

- **分子（異なりマッチ語数）**: 辞書にマッチしたユニークなフレーズ数
- **分母（全カテゴリマッチ回数）**: 重複を含む総マッチ回数
- **比率の意味**: マッチフレーズのTTR（多様性指標）
- **1.0からの減算**: 多様性を画一性に変換

この代替式により、同一の定型句を繰り返し使用する応答は高い値（画一的）となり、多様な辞書フレーズを使用する応答は低い値（多様）となる。例：
- 「ありがとうございます」を5回繰り返し → 1.0 - (1/5) = 0.8（高画一性）
- 5種類の異なる定型句を各1回使用 → 1.0 - (5/5) = 0.0（高多様性）

### 6.2.1 self_promotion_intensity算出方法

以下の4パターンを検出し、重み付け合計を行う：

#### (1) 直接的自慢 (Direct Self-Praise)
- **検出条件**: 同一文内に`self_reference_words`と`evaluative_adjectives`が共起
- **スコア**: 該当文数

#### (2) 比較優位の主張 (Comparative Superiority)
- **検出条件**: 同一文内に`comparative_terms`と`evaluative_adjectives`が共起
- **スコア**: 該当文数

#### (3) 謙遜を装った自慢 (Humble Bragging)
- **検出条件**: 以下の4要素スコア
  - 必須: `self_reference_words`と(`achievement_verbs`または`achievement_nouns`)の共起
  - 加点要素:
    - `humble_phrases`の存在: +0.25
    - `contrastive_conjunctions`の存在（前後20文字以内に謙遜語/実績語）: +0.25
    - `self_reference_words`の存在: +0.25（必須により常に加算）
    - 実績語彙の存在: +0.25（必須により常に加算）
- **スコア**: 該当文ごとに要素スコア合計（0.5～1.0）

#### (4) 実績の列挙 (Achievement Enumeration)
- **検出条件**: 同一文内に`self_reference_words`と(`achievement_verbs`または`achievement_nouns`)が共起
- **スコア**: 該当文数

#### 統合計算式

```
self_promotion_intensity = (
    direct × 1.5 +           # 直接的自慢
    comparative × 0.8 +      # 比較優位
    humble_sum × 0.6 +       # 謙遜装い（各文のスコア合計）
    achievement × 0.4        # 実績列挙
) / max(総文数, 1)
```

上限を2.0にクリップする。

### 6.3 特徴量出力形式

```python
def extract_features(text: str, matcher: LexiconMatcher) -> List[float]:
    """
    Returns:
        List[float]: 12次元特徴ベクトル（順序固定）
    """
```

## 7. 推論・分類層（Inference Layer）

### 7.1 分類モデル仕様

#### 7.1.1 現行実装

- アーキテクチャ: 独立MLPヘッド×4
- 入力: 12次元特徴ベクトル（6.2節で定義）
- 出力: 4軸soft score [0.0, 1.0]

#### 7.1.2 モデルファイル形式

```
models/
├── ingratiation_model.pt    # PyTorchモデル
└── config.json             # ハイパーパラメータ + 環境情報
```

#### 7.1.3 config.json構造

```json
{
  "model_version": "3.3",
  "pytorch_version": "1.9.0",
  "architecture": "MLP4Head",
  "input_dim": 12,
  "hyperparameters": {
    "hidden_dim": 128,
    "dropout": 0.3
  }
}
```

### 7.2 推論インターフェース

```python
def predict(features: List[float]) -> Dict[str, float]:
    """
    Args:
        features: 12次元特徴ベクトル（6.2節順序準拠）
    
    Returns:
        Dict[str, float]: {
            "social": float,
            "avoidant": float,
            "mechanical": float,
            "self": float
        }
    
    Raises:
        RuntimeWarning: PyTorchバージョン不一致時
        ValueError: 入力次元不一致時
    """
```

## 8. 出力整形層（Output Structuring Layer）

### 8.1 弱教師データ形式

```json
{
  "id": "auto_0",
  "user": "string",
  "response": "string",
  "annotations": [
    {
      "text": "string",
      "start": integer,
      "end": integer,
      "category": "string",
      "confidence": float
    }
  ],
  "weak_labels": {
    "category": float
  },
  "tag_scheme": "span",      
  "source": "auto_annotation"
}
```

### 8.2 BIO形式変換仕様

#### 8.2.1 変換粒度

- デフォルト: 形態素単位（fugashi分割準拠）
- オプション: 文字単位（`--bio-granularity char`）

#### 8.2.2 BIO2形式定義（CoNLL-2003準拠）

```python
def convert_to_bio(annotations: List[Dict], text: str, granularity: str = "morpheme") -> List[str]:
    """
    span形式 → BIO2形式変換
    
    Args:
        granularity: "morpheme" | "char"
    
    Returns:
        List[str]: BIOタグリスト（UTF-8エンコーディング）
    
    Example (morpheme):
        text: "素晴らしい成果です"
        annotations: [{"text": "素晴らしい", "start": 0, "end": 5, "category": "evaluative_adjectives"}]
        tokens: ["素晴らしい", "成果", "です"]
        → ["B-evaluative_adjectives", "O", "O"]
    """
```

**エンコーディング仕様**:
- 出力ファイル: UTF-8（BOM無し）
- ラベル形式: `{B|I|O}-{category_name}`
- カテゴリ名: ASCII文字のみ（日本語カテゴリ名は事前定義の英語名に変換）

### 8.3 ログ仕様

#### 8.3.1 ファイル命名規則

```
outputs/logs/YYYYMMDD_HHMMSS_phase_name.log
```

#### 8.3.2 ログフォーマット

```json
{
  "timestamp": "ISO8601",
  "level": "DEBUG|INFO|WARNING|ERROR",
  "phase": "extract|validate|merge|annotate",
  "message": "string",
  "context": {}
}
```

## 9. 非機能要件

### 9.1 再現性

- 乱数シード固定: `PYTHONHASHSEED=0`
- ライブラリバージョン固定: requirements.txtで上下限指定
- タイムスタンプ: UTC基準のISO8601形式

### 9.2 拡張性

- プラグイン形式による抽出ルール追加
- 新規カテゴリの動的追加対応（デフォルト空リスト）
- 多言語対応を考慮したインターフェース設計

### 9.3 互換性

- JAIML v3.3本体との辞書形式完全互換
- Python 3.8以上
- 依存ライブラリ（上限設定付き）:
  - fugashi>=1.3.0,<2.0.0
  - unidic-lite>=1.0.8,<2.0.0
  - pyyaml>=6.0,<7.0.0
  - torch>=1.9.0,<2.0.0
  - transformers>=4.30.0,<5.0.0

### 9.4 性能要件

| 指標 | 要求値 | 測定方法 | 根拠 |
|------|--------|----------|------|
| コーパス処理速度 | 1MB/分以上 | SNOW D18コーパスの無作為抽出10%で測定 | 日次バッチ処理で100MBコーパスを2時間以内に完了する運用要件（50MB/時間＝0.83MB/分） |

**性能測定手順**:
```bash
# ベンチマークスクリプト
python scripts/benchmark.py --corpus-size 10MB --measure memory,speed

# SNOW D18評価セット生成（無作為抽出）
python scripts/prepare_benchmark.py --corpus SNOW_D18.txt --sample-rate 0.1 --seed 42
```

**評価セット選定基準**:
- サンプリング方式: 層化無作為抽出（各ドメインから均等）
- サンプルサイズ: 全体の10%（約10MB）
- 乱数シード: 42（再現性確保）

### 9.5 セキュリティ

- YAMLロード: `yaml.safe_load()`必須
- パストラバーサル対策: `pathlib.Path.resolve()`によるパス検証
- 入力サイズ制限: 単一ファイル1GB以下

## 10. 実行コマンド仕様

### 10.1 基本コマンド

```bash
# 候補抽出
python run_expansion.py --phase extract --corpus corpus.jsonl

# 検証
python run_expansion.py --phase validate

# 統合（ソートモード指定可）
python run_expansion.py --phase merge --sort-mode yomi

# 自動アノテーション（タグ形式・粒度指定）
python run_advanced_features.py --feature annotate --corpus dialogue.jsonl --tag-scheme BIO --bio-granularity morpheme
```

### 10.2 設定ファイル

- `config/extraction_rules.yaml`: 抽出ルール定義
- `config/category_schemas.yaml`: カテゴリスキーマ
- `config/pipeline_config.yaml`: パイプライン設定

---