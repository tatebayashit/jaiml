### A. 統一記述セクション

#### A.1 概要

**仕様書名**: JAIML アノテーション品質検査・信頼度フィルタ仕様書 v1.0

**目的**: 収集されたアノテーションデータから統計的信頼性の高いデータのみを抽出し、後続の機械学習プロセスに供給する高品質データセットを構築する。

**処理方式**: Weighted-κ基準による評価者間一致率フィルタリングと、統計的外れ値除去の2段階処理。

#### A.2 モジュール構成と責務

```
src/filtering/
├── metrics/
│   ├── kappa_matrix.py        # 評価者ペア間のκ行列生成
│   ├── agreement_score.py     # 総合一致度スコア算出
│   └── confidence_estimator.py # 信頼度推定
├── filters/
│   ├── kappa_filter.py        # κ閾値フィルタ
│   ├── outlier_filter.py      # 統計的外れ値除去
│   └── consistency_filter.py  # 論理一貫性フィルタ
├── merging/
│   ├── weighted_merge.py      # 重み付き平均統合
│   └── majority_vote.py       # 多数決統合
└── reporting/
    ├── quality_report.py      # 品質統計レポート生成
    └── rejection_log.py       # 除外データ記録
```

#### A.3 入出力仕様

**入力形式（Raw Annotation CSV）**:
```csv
dialogue_id,annotator_id,social,avoidant,mechanical,self,timestamp
dialogue_001,ann_001,3,2,1,1,2025-01-01T10:00:00Z
dialogue_001,ann_002,4,2,1,1,2025-01-01T10:05:00Z
dialogue_001,ann_003,3,3,1,1,2025-01-01T10:10:00Z
```

**出力形式（Filtered JSONL）**:
```json
{
  "dialogue_id": "dialogue_001",
  "aggregated_scores": {
    "social": 3.33,
    "avoidant": 2.33,
    "mechanical": 1.0,
    "self": 1.0
  },
  "quality_metrics": {
    "kappa": 0.82,
    "n_annotators": 3,
    "agreement_variance": 0.22
  }
}
```

#### A.4 パラメータ定義

**フィルタリング基準**:
- `kappa_threshold`: 0.60（最小一致率）
- `min_annotators`: 3（最小評価者数）
- `outlier_z_score`: 3.0（外れ値判定Z値）
- `confidence_threshold`: 0.70（最小信頼度）

**統合方式**:
- `merge_method`: "weighted_kappa"（κ重み付き平均）
- `tie_breaking`: "conservative"（保守的判定）

#### A.5 関連ファイル構成

```
filtered_data/
├── high_quality/           # 高品質データ
│   └── filtered.jsonl
├── low_agreement/          # 低一致率データ
│   └── for_reannotation.jsonl
├── outliers/              # 外れ値データ
│   └── statistical_outliers.jsonl
└── reports/               # 品質レポート
    ├── kappa_distribution.json
    └── filtering_summary.json
```

#### A.6 使用例とコマンドライン

**基本フィルタリング**:
```bash
python filtering/run_filter.py \
  --input data/raw_annotations.csv \
  --output filtered_data/high_quality/filtered.jsonl \
  --kappa-threshold 0.60 \
  --method weighted_kappa
```

**品質レポート生成**:
```bash
python filtering/reporting/quality_report.py \
  --input data/raw_annotations.csv \
  --output reports/quality_summary.json
```

**再アノテーション対象抽出**:
```bash
python filtering/extract_low_agreement.py \
  --input data/raw_annotations.csv \
  --output filtered_data/low_agreement/for_reannotation.jsonl \
  --kappa-threshold 0.60
```

#### A.7 CI検証項目

1. **κ閾値検証**: 全データのκ≥0.60確認
2. **欠損値処理**: NaN値の適切な処理確認
3. **評価者数検証**: min_annotators以上の確認
4. **外れ値記録**: 除外データの正確な記録
5. **統合一貫性**: 入力と出力の対話ID整合性
6. **統計的妥当性**: フィルタ後の分布正規性検証

#### A.8 インターフェース定義（型注釈付き）

```python
from typing import List, Dict, Tuple, Optional
import pandas as pd

class KappaCalculator:
    def calculate_pairwise_kappa(self, df: pd.DataFrame) -> pd.DataFrame:
        """評価者ペア間のκ行列を算出"""
    
    def get_average_kappa(self, kappa_matrix: pd.DataFrame) -> float:
        """平均κを算出"""

class AnnotationFilter:
    def __init__(self, kappa_threshold: float = 0.60):
        self.kappa_threshold = kappa_threshold
    
    def filter_by_agreement(self, annotations: pd.DataFrame) -> pd.DataFrame:
        """一致率基準でフィルタリング"""
    
    def detect_outliers(self, annotations: pd.DataFrame, 
                       z_threshold: float = 3.0) -> List[str]:
        """統計的外れ値を検出"""

class AnnotationMerger:
    def merge_weighted(self, annotations: pd.DataFrame, 
                      kappa_scores: Dict[str, float]) -> pd.DataFrame:
        """κ重み付き平均で統合"""
    
    def merge_majority(self, annotations: pd.DataFrame) -> pd.DataFrame:
        """多数決で統合"""
```

#### A.9 既知の制約と注意事項

1. **評価者プール偏り**: 特定の評価者グループの系統的バイアス
2. **少数ラベル除外**: 稀な迎合パターンの過小評価リスク
3. **κの限界**: 順序尺度での偶然一致の過大評価
4. **欠損値処理**: 部分的評価の扱いによる歪み
5. **時系列依存**: 評価時期による品質変動

### B. 詳細仕様セクション

#### B.1 Weighted-κ算出詳細

##### B.1.1 Quadratic Weights定義

```python
def create_quadratic_weights(n_categories: int = 5) -> np.ndarray:
    """順序尺度用の二次重み行列生成"""
    weights = np.zeros((n_categories, n_categories))
    for i in range(n_categories):
        for j in range(n_categories):
            weights[i, j] = ((i - j) ** 2) / ((n_categories - 1) ** 2)
    return weights
```

##### B.1.2 軸別κ算出

各軸（社会的・回避的・機械的・自己）について独立にκを計算:
- κ_social ≥ 0.60
- κ_avoidant ≥ 0.60
- κ_mechanical ≥ 0.60
- κ_self ≥ 0.60

全軸が基準を満たす対話ペアのみを採用。

#### B.2 外れ値検出アルゴリズム

##### B.2.1 評価者内一貫性

```python
def detect_inconsistent_annotator(annotations: pd.DataFrame, 
                                 annotator_id: str) -> bool:
    """同一評価者の応答パターン一貫性を検証"""
    annotator_data = annotations[annotations['annotator_id'] == annotator_id]
    
    # 極端な分散を示す評価者を検出
    variance_per_axis = annotator_data[['social', 'avoidant', 'mechanical', 'self']].var()
    
    # 全軸で常に同じ値を付ける評価者も問題
    unique_counts = annotator_data[['social', 'avoidant', 'mechanical', 'self']].nunique()
    
    return (variance_per_axis > 2.0).any() or (unique_counts == 1).any()
```

##### B.2.2 対話別外れ値

```python
def detect_dialogue_outliers(annotations: pd.DataFrame, 
                           dialogue_id: str, 
                           z_threshold: float = 3.0) -> List[str]:
    """特定対話に対する外れ値評価を検出"""
    dialogue_data = annotations[annotations['dialogue_id'] == dialogue_id]
    outlier_annotators = []
    
    for axis in ['social', 'avoidant', 'mechanical', 'self']:
        values = dialogue_data[axis].values
        mean = np.mean(values)
        std = np.std(values)
        
        if std > 0:
            z_scores = np.abs((values - mean) / std)
            outlier_indices = np.where(z_scores > z_threshold)[0]
            outlier_annotators.extend(
                dialogue_data.iloc[outlier_indices]['annotator_id'].tolist()
            )
    
    return list(set(outlier_annotators))
```

#### B.3 統合アルゴリズム

##### B.3.1 κ重み付き平均

```python
def weighted_average_merge(annotations: pd.DataFrame, 
                          kappa_scores: Dict[Tuple[str, str], float]) -> pd.DataFrame:
    """評価者の信頼度（κ）で重み付けした平均"""
    results = []
    
    for dialogue_id in annotations['dialogue_id'].unique():
        dialogue_data = annotations[annotations['dialogue_id'] == dialogue_id]
        annotators = dialogue_data['annotator_id'].unique()
        
        # 各評価者の平均κを算出
        annotator_weights = {}
        for ann in annotators:
            kappa_sum = sum(kappa_scores.get((ann, other), 0) 
                          for other in annotators if other != ann)
            annotator_weights[ann] = kappa_sum / (len(annotators) - 1)
        
        # 重み付き平均を計算
        weighted_scores = {}
        for axis in ['social', 'avoidant', 'mechanical', 'self']:
            values = dialogue_data[axis].values
            weights = [annotator_weights[ann] for ann in dialogue_data['annotator_id']]
            weighted_scores[axis] = np.average(values, weights=weights)
        
        results.append({
            'dialogue_id': dialogue_id,
            'aggregated_scores': weighted_scores,
            'quality_metrics': {
                'average_kappa': np.mean(list(annotator_weights.values())),
                'n_annotators': len(annotators)
            }
        })
    
    return pd.DataFrame(results)
```

#### B.4 再アノテーションフロー

##### B.4.1 優先順位付け

低一致率データの再アノテーション優先順位:
1. 0.40 ≤ κ < 0.60: 高優先度（改善可能性高）
2. 0.20 ≤ κ < 0.40: 中優先度（大幅な不一致）
3. κ < 0.20: 低優先度（根本的な問題の可能性）

##### B.4.2 再アノテーション戦略

- 高優先度: 既存評価者による再評価
- 中優先度: 新規評価者追加
- 低優先度: 対話ペア自体の見直し