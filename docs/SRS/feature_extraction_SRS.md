### A. 統一記述セクション

#### A.1 概要

**仕様書名**: JAIML 特徴量抽出再定義仕様書 v1.0

**目的**: フィルタリング済みアノテーションデータから、JAIML v3.3の12次元特徴量体系に準拠した特徴ベクトルを抽出し、教師あり学習用のデータセットを構築する。

**処理内容**: 語彙的・統語的・意味的・コーパス依存の4系統特徴量を算出し、アノテーションラベルと結合。

#### A.2 モジュール構成と責務

```
src/feature_extraction/
├── lexical/
│   ├── emotion_scorer.py      # 感情強調スコア
│   ├── repetition_ratio.py    # ユーザー語彙反復率
│   └── diversity_inverse.py   # 語彙多様性逆数
├── syntactic/
│   ├── modal_ratio.py         # 推量構文率
│   ├── ai_subject_ratio.py    # AI主語構文率
│   └── assertiveness.py       # 決定性スコア
├── semantic/
│   ├── congruence.py         # 意味的同調度
│   └── dependency.py         # 応答依存度
├── corpus_based/
│   ├── tfidf_novelty.py      # TF-IDF新規性
│   ├── template_match.py     # テンプレートマッチ率
│   └── self_promotion.py     # 自己呈示強度
└── integration/
    ├── feature_combiner.py   # 特徴量統合
    └── normalizer.py         # 正規化処理
```

#### A.3 入出力仕様

**入力形式（Annotated JSONL）**:
```json
{
  "dialogue_id": "dialogue_001",
  "user": "ユーザー発話",
  "response": "AI応答",
  "aggregated_scores": {
    "social": 3.33,
    "avoidant": 2.33,
    "mechanical": 1.0,
    "self": 1.0
  }
}
```

**出力形式（Feature CSV）**:
```csv
dialogue_id,semantic_congruence,sentiment_emphasis_score,...,self_promotion_intensity,label_social,label_avoidant,label_mechanical,label_self
dialogue_001,0.87,0.92,...,0.00,3.33,2.33,1.0,1.0
```

#### A.4 パラメータ定義

**特徴量算出パラメータ**:
- `window_ttr`: 50（TTR計算窓サイズ）
- `tfidf_vectorizer_path`: "model/vectorizers/tfidf_vectorizer.joblib"
- `lexicon_path`: "lexicons/jaiml_lexicons.yaml"
- `normalization`: "minmax"（各特徴量0-1、self_promotionは0-2→÷2）

**SimCSE設定**:
- `model_name`: "cl-tohoku/bert-base-japanese"
- `similarity_metric`: "cosine"

#### A.5 関連ファイル構成

```
features/
├── extracted/
│   ├── train_features.csv    # 学習用特徴量
│   └── test_features.csv     # 評価用特徴量
├── metadata/
│   ├── feature_stats.json    # 特徴量統計
│   └── extraction_log.json   # 抽出ログ
└── cache/
    └── embeddings/           # SimCSE埋め込みキャッシュ
```

#### A.6 使用例とコマンドライン

**特徴量抽出実行**:
```bash
python feature_extraction/extract_all.py \
  --input filtered_data/high_quality/filtered.jsonl \
  --output features/extracted/train_features.csv \
  --lexicon lexicons/jaiml_lexicons.yaml \
  --vectorizer model/vectorizers/tfidf_vectorizer.joblib
```

**特徴量統計レポート**:
```bash
python feature_extraction/analyze_features.py \
  --input features/extracted/train_features.csv \
  --output features/metadata/feature_stats.json
```

#### A.7 CI検証項目

1. **次元数検証**: 12特徴量すべての存在確認
2. **値域検証**: 各特徴量の値域チェック
3. **欠損値検証**: NaN/Inf値の不在確認
4. **相関検証**: 特徴量間の病的相関検出
5. **ラベル整合性**: アノテーションラベルとの対応確認
6. **再現性検証**: 同一入力からの同一出力確認

#### A.8 インターフェース定義（型注釈付き）

```python
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

class FeatureExtractor:
    def __init__(self, lexicon_path: str, vectorizer_path: str):
        """特徴抽出器の初期化"""
        self.lexicon_matcher = LexiconMatcher(lexicon_path)
        self.tfidf_calculator = TFIDFNoveltyCalculator()
        self.tfidf_calculator.load_model(vectorizer_path)
    
    def extract_features(self, user: str, response: str) -> Dict[str, float]:
        """12次元特徴量を抽出"""
    
    def extract_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """バッチ処理で特徴量抽出"""

class FeatureNormalizer:
    def fit_transform(self, features: pd.DataFrame) -> pd.DataFrame:
        """特徴量の正規化（学習時）"""
    
    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        """特徴量の正規化（推論時）"""
```

#### A.9 既知の制約と注意事項

1. **計算コスト**: SimCSE埋め込みがボトルネック（GPU推奨）
2. **辞書依存性**: 語彙辞書の更新時は再抽出必要
3. **文長依存**: 短文（<10文字）での特徴量不安定性
4. **言語制約**: 日本語単言語、コードスイッチング非対応
5. **メモリ制約**: 大規模バッチ処理時の埋め込みキャッシュ

### B. 詳細仕様セクション

#### B.1 特徴量算出詳細

##### B.1.1 意味的同調度（semantic_congruence）

```python
def semantic_congruence(user_text: str, response_text: str, 
                       model_name: str = "cl-tohoku/bert-base-japanese") -> float:
    """SimCSEによる文埋め込みコサイン類似度"""
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer(model_name)
    user_emb = model.encode(user_text)
    resp_emb = model.encode(response_text)
    
    # コサイン類似度を[0, 1]に正規化
    similarity = np.dot(user_emb, resp_emb) / (np.linalg.norm(user_emb) * np.linalg.norm(resp_emb))
    return (similarity + 1.0) / 2.0
```

##### B.1.2 感情強調スコア（sentiment_emphasis_score）

```python
def sentiment_emphasis_score(response_text: str, lexicon_matcher: LexiconMatcher) -> float:
    """肯定語と強調副詞の相乗効果を測定"""
    matches = lexicon_matcher.match(response_text)
    pos_words = matches.get('positive_emotion_words', [])
    intensifiers = matches.get('intensifiers', [])
    
    # 文分割
    sentences = response_text.split('。')
    n_sent = len([s for s in sentences if s.strip()])
    
    if pos_words and intensifiers:
        # 共起時は1.5倍の相乗効果
        score = (len(pos_words) * len(intensifiers) * 1.5) / n_sent
    else:
        score = (len(pos_words) + len(intensifiers)) / n_sent
    
    return min(score, 3.0)  # 上限3.0
```

##### B.1.3 自己呈示強度（self_promotion_intensity）

```python
def self_promotion_intensity(response_text: str, lexicon_matcher: LexiconMatcher) -> float:
    """4パターンの自己呈示を統合評価"""
    sentences = response_text.split('。')
    
    direct_boast = 0      # 直接的自慢
    comparative = 0       # 比較優位
    humble_brag = 0      # 謙遜装い自慢
    achievement = 0      # 実績列挙
    
    for sent in sentences:
        sent_matches = lexicon_matcher.match(sent)
        
        # パターン1: 自己参照＋評価語
        if (sent_matches.get('self_reference_words') and 
            sent_matches.get('evaluative_adjectives')):
            direct_boast += 1
        
        # パターン2: 比較語＋評価語
        if (sent_matches.get('comparative_terms') and 
            sent_matches.get('evaluative_adjectives')):
            comparative += 1
        
        # パターン3: 謙遜語＋逆接＋肯定評価
        if (sent_matches.get('humble_phrases') and 
            sent_matches.get('contrastive_conjunctions')):
            humble_brag += 1
        
        # パターン4: 自己参照＋実績語
        if (sent_matches.get('self_reference_words') and 
            (sent_matches.get('achievement_nouns') or 
             sent_matches.get('achievement_verbs'))):
            achievement += 1
    
    # 重み付け統合
    n_sent = len([s for s in sentences if s.strip()])
    score = (direct_boast * 1.5 + comparative * 0.8 + 
             humble_brag * 0.6 + achievement * 0.4) / n_sent
    
    return min(score, 2.0)  # 上限2.0
```

#### B.2 特徴量間相関と多重共線性対策

##### B.2.1 相関行列分析

```python
def analyze_feature_correlations(features_df: pd.DataFrame) -> Dict[str, float]:
    """特徴量間の相関を分析し、問題のあるペアを検出"""
    feature_cols = [col for col in features_df.columns 
                   if not col.startswith('label_') and col != 'dialogue_id']
    
    corr_matrix = features_df[feature_cols].corr()
    high_corr_pairs = []
    
    for i in range(len(feature_cols)):
        for j in range(i+1, len(feature_cols)):
            if abs(corr_matrix.iloc[i, j]) > 0.9:
                high_corr_pairs.append({
                    'feature1': feature_cols[i],
                    'feature2': feature_cols[j],
                    'correlation': corr_matrix.iloc[i, j]
                })
    
    return high_corr_pairs
```

##### B.2.2 VIF（分散拡大係数）チェック

```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

def calculate_vif(features_df: pd.DataFrame) -> pd.DataFrame:
    """多重共線性の診断"""
    feature_cols = [col for col in features_df.columns 
                   if not col.startswith('label_') and col != 'dialogue_id']
    
    vif_data = pd.DataFrame()
    vif_data["feature"] = feature_cols
    vif_data["VIF"] = [variance_inflation_factor(features_df[feature_cols].values, i) 
                       for i in range(len(feature_cols))]
    
    # VIF > 10 は多重共線性の可能性
    return vif_data[vif_data["VIF"] > 10]
```

#### B.3 正規化戦略

##### B.3.1 特徴量別正規化方式

| 特徴量 | 値域 | 正規化方式 |
|--------|------|------------|
| semantic_congruence | [0, 1] | なし（既に正規化済み） |
| sentiment_emphasis_score | [0, 3] | x/3 |
| user_repetition_ratio | [0, 1] | なし |
| modal_expression_ratio | [0, 1] | なし |
| response_dependency | [0, 1] | なし |
| assertiveness_score | [0, 1] | なし |
| lexical_diversity_inverse | [0, 1] | なし |
| template_match_rate | [0, 1] | なし |
| tfidf_novelty | [0, 1] | なし |
| self_ref_pos_score | [0, 1] | なし |
| ai_subject_ratio | [0, 1] | なし |
| self_promotion_intensity | [0, 2] | x/2 |

##### B.3.2 外れ値処理

```python
def clip_outliers(features_df: pd.DataFrame, percentile: float = 99) -> pd.DataFrame:
    """極端な外れ値をクリッピング"""
    feature_cols = [col for col in features_df.columns 
                   if not col.startswith('label_') and col != 'dialogue_id']
    
    for col in feature_cols:
        upper_bound = np.percentile(features_df[col], percentile)
        lower_bound = np.percentile(features_df[col], 100 - percentile)
        features_df[col] = features_df[col].clip(lower=lower_bound, upper=upper_bound)
    
    return features_df
```