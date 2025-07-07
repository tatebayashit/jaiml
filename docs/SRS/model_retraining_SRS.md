### A. 統一記述セクション

#### A.1 概要

**仕様書名**: JAIML 分類器再学習仕様書 v1.0

**目的**: 人手アノテーションから得られた高品質教師データを用いて、迎合性分類器を再学習し、予測精度の向上と汎化性能の改善を実現する。

**学習方式**: XGBoostによる多出力回帰（4軸独立学習）とニューラルネットワークのアンサンブル。

#### A.2 モジュール構成と責務

```
src/model_retraining/
├── data/
│   ├── splitter.py           # 学習/検証/テスト分割
│   ├── balancer.py           # クラス不均衡対策
│   └── augmenter.py          # データ拡張
├── models/
│   ├── xgboost_trainer.py    # XGBoost学習
│   ├── neural_trainer.py     # NN学習
│   └── ensemble.py           # 複数モデルの予測統合と重み付き平均
├── evaluation/
│   ├── metrics.py            # 評価指標算出
│   ├── cross_validator.py    # 交差検証
│   └── ablation.py           # アブレーション研究
├── optimization/
│   ├── hyperparameter.py     # ハイパーパラメータ探索
│   └── feature_selection.py  # 特徴量選択
└── deployment/
    ├── model_export.py       # モデル出力
    └── version_control.py    # バージョン管理
```

#### A.3 入出力仕様

**入力形式（Feature CSV）**:
```csv
dialogue_id,semantic_congruence,...,self_promotion_intensity,label_social,label_avoidant,label_mechanical,label_self
dialogue_001,0.87,...,0.00,3.33,2.33,1.0,1.0
```

**出力形式**:
1. モデルファイル: `models/xgboost_v2.0.joblib`
2. 評価レポート: `reports/evaluation_v2.0.json`
3. 特徴重要度: `reports/feature_importance_v2.0.json`

#### A.4 パラメータ定義

**学習パラメータ**:
- `test_size`: 0.2（テストデータ比率）
- `validation_size`: 0.2（検証データ比率）
- `random_state`: 42（再現性確保）
- `cv_folds`: 5（交差検証数）

**XGBoostパラメータ**:
- `n_estimators`: 100
- `max_depth`: 6
- `learning_rate`: 0.1
- `objective`: "reg:squarederror"
- `eval_metric`: ["mae", "rmse"]

#### A.5 関連ファイル構成

```
models/
├── trained/
│   ├── xgboost_social_v2.0.joblib
│   ├── xgboost_avoidant_v2.0.joblib
│   ├── xgboost_mechanical_v2.0.joblib
│   └── xgboost_self_v2.0.joblib
├── baseline/
│   └── baseline_v1.0/            # 比較用旧モデル
└── experiments/
    └── ablation_results/         # アブレーション結果
```

#### A.6 使用例とコマンドライン

**基本学習**:
```bash
python model_retraining/train.py \
  --input features/extracted/train_features.csv \
  --model xgboost \
  --output models/trained/ \
  --cv-folds 5
```

**ハイパーパラメータ探索**:
```bash
python model_retraining/optimization/hyperparameter.py \
  --input features/extracted/train_features.csv \
  --trials 100 \
  --output reports/optuna_results.json
```

**モデル評価**:
```bash
python model_retraining/evaluation/evaluate.py \
  --model models/trained/xgboost_v2.0.joblib \
  --test features/extracted/test_features.csv \
  --output reports/evaluation_v2.0.json
```

#### A.7 CI検証項目

1. **精度向上検証**: 新モデルが旧モデルを上回ることの確認
2. **過学習検証**: 学習/検証誤差の乖離チェック
3. **再現性検証**: 同一データでの学習結果一致
4. **予測値域検証**: 出力が[0, 5]範囲内
5. **特徴重要度検証**: 極端な偏りの検出
6. **推論速度検証**: レイテンシ要件の充足

#### A.8 インターフェース定義（型注釈付き）

```python
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from sklearn.base import BaseEstimator

class ModelTrainer:
    def __init__(self, model_type: str = "xgboost"):
        """学習器の初期化"""
        self.model_type = model_type
        self.models = {}  # 4軸分のモデル格納
    
    def train(self, X: pd.DataFrame, y: pd.DataFrame) -> Dict[str, BaseEstimator]:
        """4軸独立学習"""
    
    def cross_validate(self, X: pd.DataFrame, y: pd.DataFrame, 
                      cv: int = 5) -> Dict[str, float]:
        """交差検証"""

class ModelEvaluator:
    def evaluate_regression(self, y_true: pd.Series, 
                          y_pred: pd.Series) -> Dict[str, float]:
        """回帰評価指標算出（MAE, RMSE, Spearman）"""
    
    def evaluate_ordinal(self, y_true: pd.Series, 
                        y_pred: pd.Series) -> Dict[str, float]:
        """順序尺度評価（Weighted-κ, Macro-F1）"""
```

#### A.9 既知の制約と注意事項

1. **ラベル分布偏り**: 極端な迎合（Level 5）の少なさ
2. **軸間相関**: 社会的/自己迎合の相関による学習困難
3. **計算資源**: グリッドサーチ時の計算時間
4. **汎化性**: 新規ドメインへの転移性能の限界
5. **解釈性**: XGBoostの決定過程の説明困難性

### B. 詳細仕様セクション

#### B.1 データ分割戦略

##### B.1.1 層化分割

```python
from sklearn.model_selection import train_test_split

def stratified_split(features_df: pd.DataFrame, 
                    test_size: float = 0.2,
                    val_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """迎合度分布を保持した層化分割"""
    # 各軸のラベルを離散化（5段階）
    y_stratify = pd.DataFrame()
    for axis in ['label_social', 'label_avoidant', 'label_mechanical', 'label_self']:
        y_stratify[axis] = pd.cut(features_df[axis], bins=5, labels=False)
    
    # 複合ラベルを作成
    stratify_label = y_stratify.apply(lambda x: '_'.join(x.astype(str)), axis=1)
    
    # 学習/一時データに分割
    X_temp, X_test, y_temp, y_test = train_test_split(
        features_df,
        features_df,
        test_size=test_size,
        stratify=stratify_label,
        random_state=42
    )
    
    # 学習/検証に分割
    val_ratio = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp,
        X_temp,
        test_size=val_ratio,
        stratify=stratify_label[X_temp.index],
        random_state=42
    )
    
    return X_train, X_val, X_test
```

##### B.1.2 時系列考慮分割

アノテーション時期を考慮し、将来データへの汎化を評価:
- Train: 最初の60%
- Val: 次の20%
- Test: 最後の20%

#### B.2 学習アルゴリズム詳細

##### B.2.1 XGBoost多出力回帰

```python
import xgboost as xgb
from sklearn.multioutput import MultiOutputRegressor

class XGBoostTrainer:
    def train_multioutput(self, X_train: pd.DataFrame, 
                         y_train: pd.DataFrame) -> Dict[str, xgb.XGBRegressor]:
        """4軸独立XGBoost学習"""
        models = {}
        
        for axis in ['social', 'avoidant', 'mechanical', 'self']:
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective='reg:squarederror',
                eval_metric=['mae', 'rmse'],
                random_state=42
            )
            
            y_axis = y_train[f'label_{axis}']
            model.fit(
                X_train,
                y_axis,
                eval_set=[(X_val, y_val[f'label_{axis}'])],
                early_stopping_rounds=10,
                verbose=False
            )
            
            models[axis] = model
        
        return models
```

##### B.2.2 順序回帰の考慮

```python
from sklearn.base import BaseEstimator, RegressorMixin

class OrdinalRegressor(BaseEstimator, RegressorMixin):
    """順序尺度を考慮した回帰器"""
    def __init__(self, base_regressor):
        self.base_regressor = base_regressor
        self.thresholds = None
    
    def fit(self, X, y):
        # 連続値として学習
        self.base_regressor.fit(X, y)
        
        # 閾値を最適化
        y_pred_continuous = self.base_regressor.predict(X)
        self.thresholds = self._optimize_thresholds(y, y_pred_continuous)
        
        return self
    
    def predict(self, X):
        # 連続値予測
        y_pred_continuous = self.base_regressor.predict(X)
        
        # 順序カテゴリに変換
        y_pred_ordinal = np.digitize(y_pred_continuous, self.thresholds) + 1
        
        return np.clip(y_pred_ordinal, 1, 5)
    
    def _optimize_thresholds(self, y_true, y_pred_continuous):
        """最適な閾値を探索"""
        from scipy.optimize import minimize
        
        def loss(thresholds):
            y_pred = np.digitize(y_pred_continuous, thresholds) + 1
            return -cohen_kappa_score(y_true, y_pred, weights='quadratic')
        
        # 初期閾値
        initial = [1.5, 2.5, 3.5, 4.5]
        
        result = minimize(loss, initial, bounds=[(1, 2), (2, 3), (3, 4), (4, 5)])
        return result.x
```

#### B.3 評価指標実装

##### B.3.1 Weighted-κ算出

```python
def calculate_metrics(y_true: pd.DataFrame, y_pred: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """全評価指標を算出"""
    metrics = {}
    
    for axis in ['social', 'avoidant', 'mechanical', 'self']:
        y_true_axis = y_true[f'label_{axis}']
        y_pred_axis = y_pred[f'{axis}_pred']
        
        # 順序尺度用のWeighted-κ
        kappa = cohen_kappa_score(
            y_true_axis.round().clip(1, 5),
            y_pred_axis.round().clip(1, 5),
            weights='quadratic'
        )
        
        # Macro-F1（5クラス）
        f1 = f1_score(
            y_true_axis.round().clip(1, 5),
            y_pred_axis.round().clip(1, 5),
            labels=[1, 2, 3, 4, 5],
            average='macro'
        )
        
        # 回帰指標
        mae = mean_absolute_error(y_true_axis, y_pred_axis)
        spearman = spearmanr(y_true_axis, y_pred_axis)[0]
        
        metrics[axis] = {
            'weighted_kappa': kappa,
            'macro_f1': f1,
            'mae': mae,
            'spearman': spearman
        }
    
    return metrics
```

#### B.4 アブレーション研究

##### B.4.1 特徴量重要度分析

```python
def feature_ablation_study(model: xgb.XGBRegressor, 
                          X_test: pd.DataFrame,
                          y_test: pd.Series) -> pd.DataFrame:
    """各特徴量を除外した際の性能低下を測定"""
    baseline_score = model.score(X_test, y_test)
    ablation_results = []
    
    for feature in X_test.columns:
        # 特徴量を除外
        X_ablated = X_test.drop(columns=[feature])
        
        # 再学習なしで予測（特徴量をゼロ化）
        X_zeroed = X_test.copy()
        X_zeroed[feature] = 0
        
        ablated_score = model.score(X_zeroed, y_test)
        importance = baseline_score - ablated_score
        
        ablation_results.append({
            'feature': feature,
            'importance': importance,
            'baseline_score': baseline_score,
            'ablated_score': ablated_score
        })
    
    return pd.DataFrame(ablation_results).sort_values('importance', ascending=False)
```

##### B.4.2 軸別学習 vs 統合学習

```python
def compare_learning_strategies(X_train, y_train, X_test, y_test):
    """独立学習とマルチタスク学習の比較"""
    # 戦略1: 軸別独立学習
    independent_models = {}
    independent_scores = {}
    
    for axis in ['social', 'avoidant', 'mechanical', 'self']:
        model = xgb.XGBRegressor()
        model.fit(X_train, y_train[f'label_{axis}'])
        pred = model.predict(X_test)
        independent_scores[axis] = mean_absolute_error(
            y_test[f'label_{axis}'], pred
        )
        independent_models[axis] = model
    
    # 戦略2: マルチタスク学習
    from sklearn.multioutput import MultiOutputRegressor
    multi_model = MultiOutputRegressor(xgb.XGBRegressor())
    multi_model.fit(X_train, y_train[['label_social', 'label_avoidant', 
                                     'label_mechanical', 'label_self']])
    multi_pred = multi_model.predict(X_test)
    
    multi_scores = {}
    for i, axis in enumerate(['social', 'avoidant', 'mechanical', 'self']):
        multi_scores[axis] = mean_absolute_error(
            y_test[f'label_{axis}'], multi_pred[:, i]
        )
    
    return {
        'independent': independent_scores,
        'multitask': multi_scores
    }
```