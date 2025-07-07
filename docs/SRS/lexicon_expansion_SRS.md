## 📚 lexicon_expansion v2.0 システム要求仕様書 - 改訂版

### A. 統一記述セクション

#### A.1 概要

**モジュール名**: lexicon_expansion v2.0

**目的**: JAIML v3.3における語彙辞書（`lexicons/jaiml_lexicons.yaml`）の系統的拡張と、辞書ベースの弱教師付き学習データ生成を実現する統合基盤。コーパスからの自動抽出、人手検証、バージョン管理、自動アノテーションの4機能を提供する。

#### A.2 モジュール構成と責務

```
src/lexicon_expansion/
├── config/
│   ├── extraction_rules.yaml     # 抽出ルール定義
│   └── category_schemas.yaml     # カテゴリスキーマ
├── corpus/                       # 入力コーパス
├── scripts/
│   ├── run_expansion.py          # メイン実行スクリプト
│   ├── extract_candidates.py     # 候補抽出
│   ├── merge_lexicons.py         # 辞書統合
│   └── validate_yaml.py          # 検証
├── annotation/
│   ├── auto_annotator.py         # 自動アノテーション
│   ├── tfidf_novelty_calc.py     # TF-IDF新規性計算
│   └── snippet_generator.py      # スニペット生成
├── clustering/
│   ├── semantic_clustering.py    # 意味的クラスタリング
│   └── overexpression_detector.py # 過剰表現検出
├── version_control/
│   ├── version_manager.py        # バージョン管理
│   └── trend_analyzer.py         # トレンド分析
└── outputs/
    ├── candidates/               # 抽出候補
    ├── reports/                  # レポート
    │   └── cluster_metrics.json  # クラスタリング評価指標
    └── snippets/                 # アノテーション結果
```

**責務**:
- コーパスからの語彙候補自動抽出
- 人手検証プロセスの支援
- 辞書のバージョン管理と差分追跡
- 弱教師付き学習データの生成

#### A.3 入出力仕様

**入力形式**:
1. コーパス（JSONL/プレーンテキスト）
2. 既存辞書（`jaiml_lexicons.yaml`）
3. 抽出ルール（`extraction_rules.yaml`）

**出力形式**:
1. 拡張辞書（`jaiml_lexicons_TIMESTAMP.yaml`）
2. 弱教師データ（JSONL形式）
3. 変更ログ（`changelog.json`）
4. クラスタリング評価レポート（`cluster_metrics.json`）

#### A.4 パラメータ定義

**共通パラメータ（config/global.yamlから継承）**:
- `tokenizer`: "fugashi"
- `encoding`: "utf-8"
- `lexicon_path`: "lexicons/jaiml_lexicons.yaml"

**辞書拡張専用パラメータ**:
- `min_frequency`: 5（最小出現頻度）
- `ngram_range`: [1, 7]（N-gram範囲）
- `context_window`: 50（アノテーション文脈窓）
- `novelty_top_k`: 0.2（TF-IDF新規性上位20%閾値）
- `context_window_unit`: "morphemes"（形態素数単位、値域[10, 200]

#### A.5 関連ファイル構成

```
lexicons/
├── jaiml_lexicons.yaml          # マスター辞書（11カテゴリ必須）
└── versions/                    # バージョン履歴
    ├── jaiml_lexicons_TIMESTAMP.yaml
    └── changelog.json

config/
├── global.yaml                  # 共通設定
├── category_schemas.yaml        # カテゴリスキーマ定義
├── extraction_rules.yaml        # 抽出ルール
```

#### A.6 使用例とコマンドライン

**候補抽出**:
```bash
python run_expansion.py \
  --phase extract \
  --corpus corpus.jsonl \
  --categories template_phrases humble_phrases
```

**検証と統合**:
```bash
# 候補の検証
python run_expansion.py --phase validate

# 辞書への統合
python run_expansion.py --phase merge --output lexicons/
```

**自動アノテーション**:
```bash
python run_advanced_features.py \
  --feature annotate \
  --corpus dialogue.jsonl \
  --output outputs/weak_supervised.jsonl
```

#### A.7 CI検証項目

1. **辞書完全性**: 11カテゴリすべてが存在すること
2. **YAML妥当性**: `yaml.safe_load()`でエラーが発生しないこと
3. **重複検査**: 各カテゴリ内に重複エントリがないこと
4. **正規化一貫性**: Unicode NFKC正規化が適用されていること
5. **バージョン整合性**: changelogと実際の差分が一致すること
6. **canonical_key整合性**: 全エントリのcanonical_keyが正規化ルールに従っていること

#### A.8 インターフェース定義（型注釈付き）

```python
from typing import Dict, List, Set, Optional, Tuple
from collections import OrderedDict

class CandidateExtractor:
    def __init__(self, config_path: str):
        """
        Args:
            config_path: extraction_rules.yamlのパス
        """
    
    def extract_category(self, corpus_path: str, category: str) -> Dict[str, Dict]:
        """
        特定カテゴリの候補を抽出
        
        Returns:
            Dict[str, Dict]: {
                "phrase": {
                    "frequency": int,
                    "pos_patterns": List[str]
                }
            }
        """

class LexiconMatcher:
    def __init__(self, lexicon_path: str):
        """辞書の読み込み"""
    
    def match(self, text: str) -> OrderedDict[str, List[str]]:
        """
        テキストに対する辞書マッチング
        
        Returns:
            OrderedDict: カテゴリ順序固定の辞書
        """

class AutoAnnotator:
    def __init__(self, lexicon_path: str):
        """自動アノテーターの初期化"""
        self.lexicon_matcher = LexiconMatcher(lexicon_path)
        self.novelty_calculator = TFIDFNoveltyCalculator()
     
    def calculate_novelty_score(self, user: str, response: str) -> float:
        """
        TF-IDF新規性スコアの計算
        
        Args:
            user: ユーザー発話
            response: AI応答
        Returns:
            float: 新規性スコア（0.0-1.0）
        """
    
    def annotate_text(self, text: str, context_window: int = 50) -> List[Dict]:
        """
        テキストの自動アノテーション
        
        Returns:
            List[Dict]: アノテーション候補リスト
        """
```

#### A.9 既知の制約と注意事項

1. **メモリ使用量**: 大規模辞書（>10万語）使用時は2GB以上必要
2. **処理時間**: 100万文書の処理に約2時間
3. **カテゴリ数**: 必須11カテゴリ + 拡張カテゴリは最大20まで
4. **ファイルサイズ**: 単一辞書ファイルは10MB以下を推奨
5. **文字エンコーディング**: UTF-8のみ対応（BOM無し）

### B. 詳細仕様セクション

#### B.1 必須11カテゴリ定義

| カテゴリ名 | 変数名 | 用途 | パターン例 |
|-----------|--------|------|-----------|
| 定型表現 | template_phrases | 慣用的定型句の検出 | ご質問ありがとうございます |
| 謙遜表現 | humble_phrases | 自己卑下表現の検出 | まだまだ、不完全ながら |
| 実績名詞 | achievement_nouns | 成果関連名詞の検出 | 成果、実績、達成 |
| 達成動詞 | achievement_verbs | 実績動詞の検出 | 達成する、成功する |
| 評価形容詞 | evaluative_adjectives | 肯定的評価語の検出 | 素晴らしい、優秀な |
| 感情語 | positive_emotion_words | 肯定的感情表現の検出 | 嬉しい、感動 |
| 強調副詞 | intensifiers | 強調表現の検出 | とても、非常に |
| 比較語 | comparative_terms | 比較表現の検出 | より、と比べて |
| 逆接助詞 | contrastive_conjunctions | 逆接表現の検出 | が、けれど |
| 推量表現 | modal_expressions | 非断定表現の検出 | かもしれません、でしょう |
| 自己参照語 | self_reference_words | AI自己言及の検出 | 私、当AI |

#### B.2 抽出ルール仕様

##### B.2.1 extraction_rules.yaml構造

```yaml
# カテゴリ拡張可能性設定
categories:
  template_phrases:
    extendable: false  # 11既定カテゴリは拡張不可
    patterns:
      - regex: "正規表現パターン"
        min_frequency: 10
      - keywords: ["キーワード1", "キーワード2"]
        min_frequency: 5
  custom_category_1:
    extendable: true   # カスタムカテゴリは拡張可能
    # ...

# 抽出ルール定義
category_name:
  patterns:
    - regex: "正規表現パターン"
      min_frequency: 10
    - keywords: ["キーワード1", "キーワード2"]
      min_frequency: 5
  pos_sequences:
    - ["品詞1", "品詞2", "品詞3"]
  ngram_range: [最小, 最大]
  min_frequency: 5
  pos_filter: ["名詞", "動詞", "形容詞"]
  semantic_filters:
    embedding_threshold: 0.8
```

##### B.2.2 品詞列パターンマッチング

```python
def extract_pos_sequences(text: str, patterns: List[List[str]]) -> List[Tuple[str, str]]:
    """品詞列パターンに基づく抽出"""
    tagger = Tagger()
    tokens = []
    pos_tags = []
    
    for word in tagger(text):
        if word.surface:
            tokens.append(word.surface)
            features = word.pos.split(',')
            pos = features[0]
            if len(features) > 1 and features[1] != '*':
                pos += f'-{features[1]}'
            pos_tags.append(pos)
    
    matches = []
    for pattern in patterns:
        pattern_len = len(pattern)
        for i in range(len(pos_tags) - pattern_len + 1):
            if match_pos_pattern(pos_tags[i:i+pattern_len], pattern):
                surface = ''.join(tokens[i:i+pattern_len])
                pos_seq = '|'.join(pos_tags[i:i+pattern_len])
                matches.append((surface, pos_seq))
    
    return matches
```

#### B.3 弱教師データ生成仕様

##### B.3.1 アノテーション形式

```json
{
  "id": "auto_0",
  "user": "ユーザー発話",
  "response": "AI応答",
  "annotations": [
    {
      "text": "素晴らしい",
      "start": 10,
      "end": 15,
      "category": "evaluative_adjectives",
      "confidence": 0.95
    }
  ],
  "weak_labels": {
    "social": 0.8,
    "avoidant": 0.1,
    "mechanical": 0.05,
    "self": 0.05
  },
  "novelty_features": {
    "tfidf_novelty": 0.65
  },
  "source": "auto_annotation"
}
```

##### B.3.2 信頼度計算

```python
def calculate_confidence(phrase: str, text: str, start: int, end: int) -> float:
    """アノテーション信頼度の計算"""
    # 基本信頼度：フレーズ長に基づく
    base_confidence = min(len(phrase) / 20, 1.0)
    
    # 文境界での出現は信頼度を下げる
    if start == 0 or end == len(text):
        base_confidence *= 0.8
    
    # 句読点に隣接している場合は信頼度を上げる
    if (start > 0 and text[start-1] in '、。') or \
       (end < len(text) and text[end] in '、。'):
        base_confidence *= 1.1
    
    return min(base_confidence, 1.0)
```

#### B.4 バージョン管理仕様

##### B.4.1 changelog.json構造

```json
{
  "versions": [
    {
      "timestamp": "20250705_120000",
      "file_hash": "sha256:a1b2c3d4e5f6...",
      "metadata": {
        "action": "merge",
        "source": "corpus_extraction",
        "extendable_categories": ["custom_category_1"]
      },
      "statistics": {
        "template_phrases": {
          "extendable": false,
          "added": ["新規フレーズ1", "新規フレーズ2"],
          "removed": ["削除フレーズ1"],
          "total_before": 100,
          "total_after": 101,
          "change_rate": 0.03
        }
      },
      "coverage_metrics": {
        "total_phrases": 1500,
        "category_distribution": {
          "template_phrases": 101,
          "humble_phrases": 50
        },
        "avg_phrase_length": 12.5
      }
    }
  ]
}
```

##### B.4.2 差分計算アルゴリズム

```python
def calculate_diff(prev_data: Dict, curr_data: Dict) -> Dict:
    """バージョン間差分の計算"""
    diff_stats = {}
    all_categories = set(list(prev_data.keys()) + list(curr_data.keys()))
    
    for category in all_categories:
        prev_items = set(prev_data.get(category, []))
        curr_items = set(curr_data.get(category, []))
        
        added = list(curr_items - prev_items)
        removed = list(prev_items - curr_items)
        
        diff_stats[category] = {
            "added": sorted(added),
            "removed": sorted(removed),
            "total_before": len(prev_items),
            "total_after": len(curr_items),
            "change_rate": (len(added) + len(removed)) / max(len(prev_items), 1)
        }
    
    return diff_stats
```

#### B.5 クラスタリング評価仕様

##### B.5.1 Silhouette Score計算

```python
from sklearn.metrics import silhouette_score
import numpy as np

class ClusteringEvaluator:
    def evaluate_clustering(self, embeddings: np.ndarray, labels: np.ndarray) -> Dict[str, Any]:
        """クラスタリング結果の評価"""
        score = silhouette_score(embeddings, labels)
        
        metrics = {
            "algorithm": "KMeans",
            "n_clusters": len(np.unique(labels)),
            "silhouette_score": float(score),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
        # スコアが低い場合は警告
        if score < 0.25:
            metrics["warning"] = "Low silhouette score indicates poor clustering quality"
        
        return metrics
```

##### B.5.2 評価レポート出力

```python
def save_cluster_metrics(metrics: Dict[str, Any], output_dir: str) -> None:
    """クラスタリング評価指標の保存"""
    output_path = os.path.join(output_dir, "reports", "cluster_metrics.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
```

#### B.6 辞書エントリ仕様

##### B.6.1 canonical_key正規化ルール

```python
def generate_canonical_key(phrase: str) -> str:
    """正規化キーの生成"""
    # 1. Unicode NFKC正規化
    normalized = unicodedata.normalize('NFKC', phrase)
    
    # 2. 小文字化（ひらがな・カタカナは対象外）
    normalized = normalized.lower()
    
    # 3. 全角→半角変換（英数字のみ）
    import mojimoji
    normalized = mojimoji.zen_to_han(normalized, kana=False)
    
    return normalized
```

##### B.6.2 辞書エントリ形式

```yaml
template_phrases:
  - phrase: "ご質問ありがとうございます"
    canonical_key: "ご質問ありがとうございます"
  - phrase: "ご質問ありがとうございます。"
    canonical_key: "ご質問ありがとうございます。"

positive_emotion_words:
  - phrase: "素晴らしい"
    canonical_key: "素晴らしい"
  - phrase: "すばらしい"  
    canonical_key: "すばらしい"
```

#### B.7 TF-IDF新規性計算仕様

##### B.7.1 novelty_top_k算出

```python
def calculate_tfidf_novelty_with_threshold(user_text: str, response_text: str, 
                                         vectorizer_path: str, 
                                         top_k: float = 0.2) -> float:
    """
    TF-IDF新規性スコアの計算（上位k%閾値付き）
    
    Args:
        user_text: ユーザー発話
        response_text: AI応答
        vectorizer_path: TF-IDFベクトライザーのパス
        top_k: 上位何%を新規とみなすか（0.2 = 上位20%）
    
    Returns:
        float: 新規性スコア（0.0-1.0）
    """
    calc = TFIDFNoveltyCalculator()
    calc.load_model(vectorizer_path)
    
    # ベースの新規性スコアを計算
    base_score = calc.compute(user_text, response_text)
    
    # 上位k%判定
    if base_score >= (1.0 - top_k):
        return 1.0  # 高新規性
    else:
        return base_score / (1.0 - top_k)  # 線形スケーリング
```

#### B.8 レポート出力仕様

##### B.8.1 レポートファイル一覧

| ファイル名 | 形式 | 内容 |
|-----------|------|------|
| `extraction_summary.json` | JSON | 抽出候補の統計情報 |
| `cluster_metrics.json` | JSON | クラスタリング評価指標 |
| `coverage_report.json` | JSON | 辞書カバレッジ分析 |
| `annotation_stats.json` | JSON | アノテーション統計 |

##### B.8.2 JSONスキーマ定義

```json
// cluster_metrics.json
{
  "algorithm": "string",
  "n_clusters": "integer",
  "silhouette_score": "number",
  "timestamp": "string (ISO8601)",
  "warning": "string (optional)"
}

// extraction_summary.json
{
  "timestamp": "string",
  "corpus_size": "integer",
  "categories": {
    "category_name": {
      "candidates": "integer",
      "min_frequency": "integer",
      "avg_length": "number"
    }
  }
}
```