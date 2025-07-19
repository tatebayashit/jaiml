## 🔧 CI_SRS v1.0 システム要求仕様書 - 改訂版

### A. 統一記述セクション

#### A.1 概要

**システム名**: JAIML継続的インテグレーション（CI）システム

**目的**: JAIMLプロジェクトの3モジュール（JAIML本体、lexicon_expansion、vector_pretrainer）間の仕様整合性、再現性、セキュリティを自動検証し、品質を保証する。

#### A.2 モジュール構成と責務

```
src/ci/
├── schema_validate.py           # YAML設定検証
├── check_tokenizer.py           # tokenizer統一性検査
├── check_versions.py            # バージョン整合性検査
├── check_security.py            # セキュリティ検査
├── check_jsonl.py               # JSONL形式検証
├── check_anonymization.py       # 匿名化処理検証
├── check_cluster_quality.py     # クラスタリング品質検証
├── check_annotation_metrics.py  # アノテーション品質メトリクス検証
└── run_all_checks.py            # 統合実行スクリプト

.github/workflows/
├── validate.yml                 # 設定検証ワークフロー
├── tests.yml                    # ユニットテストワークフロー
└── security.yml                 # セキュリティ検査ワークフロー
```

**責務**:
- 設定ファイルの構文・値の整合性検証
- モジュール間インターフェースの一貫性確認
- セキュリティリスクの自動検出
- テストカバレッジの監視

#### A.3 入出力仕様

**入力**:
- 各種設定ファイル（YAML形式）
- ソースコード（Python）
- テストスイート

**出力**:
- 検証レポート（JSON/Markdown形式）
- エラーログ
- カバレッジレポート

#### A.4 パラメータ定義

**CI設定パラメータ**:
- `python_version`: "3.11"
- `test_coverage_threshold`: 80  # 全モジュール共通のカバレッジ閾値（%）
- `max_complexity`: 10（循環的複雑度）
- `allowed_licenses`: ["MIT", "Apache-2.0", "BSD"]
- `min_silhouette_score`: 0.25  # クラスタリング品質閾値

#### A.5 関連ファイル構成

```
config/
├── global.yaml                  # 検証対象
└── tfidf_config.yaml           # 検証対象

ci/
├── schemas/
│   ├── global_schema.yaml      # global.yamlのスキーマ
│   └── tfidf_schema.yaml       # tfidf_config.yamlのスキーマ
└── reports/                    # 検証レポート出力先
```

#### A.6 使用例とコマンドライン

**個別検証**:
```bash
# YAML設定検証
python ci/schema_validate.py

# tokenizer統一性検査
python ci/check_tokenizer.py

# セキュリティ検査
python ci/check_security.py

# 匿名化検証
python ci/check_anonymization.py --corpus-dir corpus/jsonl/

# クラスタリング品質検証
python ci/check_cluster_quality.py --metrics-file outputs/reports/cluster_metrics.json
```

**統合検証**:
```bash
python ci/run_all_checks.py --output-format json
```

#### A.7 CI検証項目

1. **設定ファイル整合性**: 全モジュールの設定値一致
2. **依存関係整合性**: requirements.txtのバージョン範囲
3. **コード品質**: flake8、mypy、black準拠
4. **テストカバレッジ**: 80%以上
5. **セキュリティ**: bandit、safety検査
6. **Annotation Metrics Check**: アノテーション品質の定期監視
   - κ と Macro-F1 を nightly job で計算
   - κ<0.60 or Macro-F1<0.60 で Warning
7. **人手確認フラグ**: 匿名化データの人手確認状態
8. **クラスタリング品質**: Silhouette score ≥ 0.25
9. **辞書ハッシュ整合性**: changelog記載のハッシュと実ファイルの一致
10. **TF-IDF再現性**: 同一入力から同一noveltyスコア
11. **匿名化処理**: 個人情報の適切なマスキング
12. **アノテーションログ整合性**: JSONスキーマ準拠とタイムスタンプ論理性
13. **UI仕様整合性**: アノテーション定義との表示要素の一致
14. **アノテーション品質**: Weighted-κ ≥ 0.60, Macro-F1 ≥ 0.60

#### A.8 インターフェース定義（型注釈付き）

```python
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """検証結果を表すデータクラス"""
    passed: bool
    errors: List[str]
    warnings: List[str]
    info: Dict[str, any]

class ConfigValidator:
    def validate_yaml(self, config_path: str, schema_path: str) -> ValidationResult:
        """YAML設定ファイルの検証"""

class ConsistencyChecker:
    def check_tokenizer_consistency(self) -> ValidationResult:
        """全モジュールのtokenizer設定一貫性を検証"""
    
    def check_parameter_consistency(self, param_name: str) -> ValidationResult:
        """特定パラメータの一貫性を検証"""

class SecurityAuditor:
    def scan_for_pickle_usage(self) -> ValidationResult:
        """Pickle使用箇所の検出"""
    
    def check_dependencies(self) -> ValidationResult:
        """依存ライブラリの脆弱性検査"""
def check_dependencies(self) -> ValidationResult:
         """依存ライブラリの脆弱性検査"""

class AnonymizationChecker:
    def check_anonymization_flags(self, corpus_dir: str) -> ValidationResult:
        """匿名化フラグの検証"""
    
    def scan_unmasked_patterns(self, corpus_dir: str) -> ValidationResult:
        """未マスク個人情報パターンの検出"""

class LexiconValidator:
    def check_canonical_keys(self, lexicon_path: str) -> ValidationResult:
        """canonical_keyの正規化ルール準拠を検証"""

class AnnotationQualityChecker:
    def check_annotation_metrics(self, annotation_file: str) -> ValidationResult:
        """アノテーション品質メトリクスの検証"""
    
    def validate_annotation_logs(self, log_dir: str) -> ValidationResult:
        """アノテーションログのスキーマ準拠性検証"""
    
    def check_ui_consistency(self, snapshot_file: str) -> ValidationResult:
        """UI仕様とアノテーション定義の整合性検証"""      
```

#### A.9 既知の制約と注意事項

1. **実行環境**: Ubuntu 20.04/22.04のみ完全サポート
2. **Python版**: 3.8〜3.11のみ対応
3. **実行時間**: 全検証完了まで最大10分
4. **並列実行**: 一部の検証は排他制御が必要
5. **外部依存**: GitHub APIレート制限に注意

### B. 詳細仕様セクション

#### B.1 検証項目詳細

##### B.1.1 YAML設定検証

```python
def validate_yaml_config(config_path: str, schema_path: str) -> ValidationResult:
    """JSONSchemaによるYAML検証"""
    import yaml
    import jsonschema
    
    # 設定読み込み
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # スキーマ読み込み
    with open(schema_path) as f:
        schema = yaml.safe_load(f)
    
    # 検証実行
    try:
        jsonschema.validate(config, schema)
        
        # 追加の整合性チェック
        errors = []
        
        # global.yamlとの整合性
        if 'tokenizer' in config and config['tokenizer'] != 'fugashi':
            errors.append(f"tokenizer must be 'fugashi', got '{config['tokenizer']}'")
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=[],
            info={'config_path': config_path}
        )
        
    except jsonschema.ValidationError as e:
        return ValidationResult(
            passed=False,
            errors=[str(e)],
            warnings=[],
            info={'config_path': config_path}
        )
```

##### B.1.2 tokenizer統一性検査

```python
def check_tokenizer_consistency() -> ValidationResult:
    """全モジュールでfugashiが使用されているか検証"""
    errors = []
    checked_files = []
    
    # 検査対象ファイル
    target_patterns = [
        'src/model/jaiml_v3_3/core/utils/tokenize.py',
        'src/vector_pretrainer/scripts/train_tfidf.py',
        'src/lexicon_expansion/scripts/extract_candidates.py'
    ]
    
    for pattern in target_patterns:
        for filepath in glob.glob(pattern, recursive=True):
            with open(filepath) as f:
                content = f.read()
            
            # fugashi以外のトークナイザー使用を検出
            if 'MeCab' in content and 'fugashi' not in content:
                errors.append(f"{filepath}: MeCab used without fugashi wrapper")
            
            if 'janome' in content or 'sudachi' in content:
                errors.append(f"{filepath}: Non-fugashi tokenizer detected")
            
            checked_files.append(filepath)
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=[],
        info={'checked_files': checked_files}
    )
```

##### B.1.3 バージョン整合性検査

```python
def check_version_consistency() -> ValidationResult:
    """sklearn等のバージョン整合性を検証"""
    errors = []
    warnings = []
    
    # metadata.jsonの確認
    metadata_path = 'model/vectorizers/metadata.json'
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        # 現在のsklearnバージョンと比較
        import sklearn
        if metadata.get('sklearn_version') != sklearn.__version__:
            warnings.append(
                f"sklearn version mismatch: "
                f"model={metadata.get('sklearn_version')}, "
                f"current={sklearn.__version__}"
            )
    
    # requirements.txtとの整合性
    requirements_path = 'src/requirements.txt'
    if os.path.exists(requirements_path):
        with open(requirements_path) as f:
            for line in f:
                if 'sklearn' in line:
                    # バージョン指定の解析
                    if 'sklearn==1.7.*' not in line:
                        errors.append(
                            f"sklearn version not properly constrained in requirements.txt"
                        )
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info={}
    )
```

##### B.1.4 匿名化処理検証

```python
def check_anonymization_flags(corpus_dir: str) -> ValidationResult:
    """JSONLファイルの匿名化メタデータを検証"""
    errors = []
    warnings = []
    processed_files = []
    
    for jsonl_file in glob.glob(os.path.join(corpus_dir, '*.jsonl')):
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                try:
                    data = json.loads(line)
                    metadata = data.get('metadata', {})
                    
                    # 必須フラグの確認
                    if not metadata.get('anonymized', False):
                        errors.append(
                            f"{jsonl_file}:{line_no}: Missing or false 'anonymized' flag"
                        )
                    
                    if not metadata.get('verified_by_human', False):
                        warnings.append(
                            f"{jsonl_file}:{line_no}: 'verified_by_human' is false or missing"
                        )
                    
                    # GiNZAバージョン確認
                    if 'anonymizer_version' not in metadata:
                        warnings.append(
                            f"{jsonl_file}:{line_no}: Missing 'anonymizer_version'"
                        )
                    
                except json.JSONDecodeError as e:
                    errors.append(f"{jsonl_file}:{line_no}: Invalid JSON - {e}")
        
        processed_files.append(jsonl_file)
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info={'processed_files': processed_files}
    )

def scan_unmasked_patterns(corpus_dir: str) -> ValidationResult:
    """未マスクの個人情報パターンを検出"""
    patterns = {
        'phone': r'\d{2,4}-\d{2,4}-\d{4}',
        'email': r'[\w\.-]+@[\w\.-]+\.\w+',
        'id_number': r'[A-Z]{2,3}\d{6,10}',
        'japanese_name': r'(山田|田中|佐藤|鈴木|高橋|伊藤|渡辺|中村|小林|加藤)[\s]*(太郎|花子|一郎|二郎|三郎)',
        'credit_card': r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',
        'postal_code': r'〒?\d{3}-\d{4}'
    }
    
    warnings = []
    detected_patterns = []
    
    for jsonl_file in glob.glob(os.path.join(corpus_dir, '*.jsonl')):
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                try:
                    data = json.loads(line)
                    text_fields = [
                        data.get('user', ''),
                        data.get('response', ''),
                        data.get('text', '')
                    ]
                    
                    for field_text in text_fields:
                        if not field_text:
                            continue
                            
                        for pattern_name, pattern in patterns.items():
                            matches = re.findall(pattern, field_text)
                            if matches:
                                for match in matches:
                                    warnings.append(
                                        f"{jsonl_file}:{line_no}: "
                                        f"Potential {pattern_name} found: '{match}'"
                                    )
                                    detected_patterns.append({
                                        'file': jsonl_file,
                                        'line': line_no,
                                        'type': pattern_name,
                                        'content': match
                                    })
                
                except json.JSONDecodeError:
                    continue  # JSONエラーは別の検証で処理
    
    return ValidationResult(
        passed=True,  # 警告のみ、エラーとしない
        errors=[],
        warnings=warnings,
        info={'detected_patterns': detected_patterns}
    )
```

##### B.1.5 統合匿名化検証スクリプト

```python
# ci/check_anonymization.py
import argparse
import json
import sys
from typing import Dict, Any

def main():
    parser = argparse.ArgumentParser(description='Check anonymization in JSONL files')
    parser.add_argument('--corpus-dir', required=True, help='Directory containing JSONL files')
    parser.add_argument('--output-format', choices=['json', 'text'], default='text')
    args = parser.parse_args()
    
    # フラグ検証
    flag_result = check_anonymization_flags(args.corpus_dir)
    
    # パターン検出
    pattern_result = scan_unmasked_patterns(args.corpus_dir)
    
    # 結果の統合
    overall_passed = flag_result.passed and len(pattern_result.warnings) == 0
    
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'corpus_dir': args.corpus_dir,
        'overall_passed': overall_passed,
        'flag_check': {
            'passed': flag_result.passed,
            'errors': flag_result.errors,
            'warnings': flag_result.warnings
        },
        'pattern_scan': {
            'warnings': pattern_result.warnings,
            'detected_patterns': pattern_result.info.get('detected_patterns', [])
        }
    }
    
    if args.output_format == 'json':
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Anonymization Check Report - {report['timestamp']}")
        print(f"Corpus Directory: {report['corpus_dir']}")
        print(f"Overall Result: {'PASSED' if overall_passed else 'FAILED'}")
        
        if flag_result.errors:
            print("\nFlag Check Errors:")
            for error in flag_result.errors:
                print(f"  - {error}")
        
        if pattern_result.warnings:
            print(f"\nPotential Unmasked Information ({len(pattern_result.warnings)} found):")
            for warning in pattern_result.warnings[:10]:  # 最初の10件のみ表示
                print(f"  - {warning}")
            if len(pattern_result.warnings) > 10:
                print(f"  ... and {len(pattern_result.warnings) - 10} more")
    
    # CI終了コード
    sys.exit(0 if flag_result.passed else 1)

if __name__ == '__main__':
    main()
```

##### B.1.6 辞書ハッシュ整合性検査

```python
def check_lexicon_hash_consistency() -> ValidationResult:
    """辞書ファイルとchangelogのハッシュ整合性を検証"""
    errors = []
    warnings = []
    
    changelog_path = 'lexicons/versions/changelog.json'
    if not os.path.exists(changelog_path):
        return ValidationResult(
            passed=False,
            errors=[f"Changelog not found: {changelog_path}"],
            warnings=[],
            info={}
        )
    
    with open(changelog_path, 'r', encoding='utf-8') as f:
        changelog = json.load(f)
    
    for version in changelog.get('versions', []):
        timestamp = version['timestamp']
        expected_hash = version.get('file_hash')
        
        if not expected_hash:
            warnings.append(f"Version {timestamp}: Missing file_hash in changelog")
            continue
        
        # 対応する辞書ファイルを探す
        lexicon_file = f'lexicons/versions/jaiml_lexicons_{timestamp}.yaml'
        if os.path.exists(lexicon_file):
            # 実際のファイルハッシュを計算
            with open(lexicon_file, 'rb') as f:
                actual_hash = 'sha256:' + hashlib.sha256(f.read()).hexdigest()
            
            if actual_hash != expected_hash:
                errors.append(
                    f"Hash mismatch for {lexicon_file}: "
                    f"expected={expected_hash}, actual={actual_hash}"
                )
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info={'versions_checked': len(changelog.get('versions', []))}
    )
```

##### B.1.7 クラスタリング品質検証

```python
def check_clustering_quality(metrics_file: str) -> ValidationResult:
    """クラスタリング評価指標の検証"""
    errors = []
    warnings = []
    
    if not os.path.exists(metrics_file):
        return ValidationResult(
            passed=False,
            errors=[f"Metrics file not found: {metrics_file}"],
            warnings=[],
            info={}
        )
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    
    silhouette_score = metrics.get('silhouette_score')
    if silhouette_score is None:
        errors.append("Missing silhouette_score in metrics")
    elif silhouette_score < 0.25:
        warnings.append(
            f"Low silhouette score: {silhouette_score:.3f} (threshold: 0.25). "
            "This indicates poor clustering quality."
        )
    
    # JSONスキーマ検証
    required_fields = ['algorithm', 'n_clusters', 'silhouette_score', 'timestamp']
    missing_fields = [field for field in required_fields if field not in metrics]
    if missing_fields:
        errors.append(f"Missing required fields: {', '.join(missing_fields)}")
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info=metrics
    )
```

##### B.1.8 TF-IDF再現性テスト

```python
def test_tfidf_reproducibility() -> ValidationResult:
    """TF-IDF noveltyスコアの再現性を検証"""
    # テストデータ
    test_cases = [
            # 省略された実装をここに追加
    ]
```
##### B.1.9 アノテーション品質監視

```python
# ci/check_annotation_metrics.py
import json
import os
import numpy as np
from sklearn.metrics import cohen_kappa_score, f1_score
from typing import Dict, List, Tuple
import warnings

def calculate_weighted_kappa(y1: List[int], y2: List[int]) -> float:
    """Calculate quadratic weighted kappa"""
    return cohen_kappa_score(y1, y2, weights='quadratic')

def calculate_macro_f1(y_true: List[int], y_pred: List[int], n_classes: int = 5) -> float:
    """Calculate macro F1 score for ordinal labels"""
    return f1_score(y_true, y_pred, labels=list(range(1, n_classes+1)), average='macro')

def check_annotation_quality(annotation_file: str) -> ValidationResult:
    """Check annotation quality metrics"""
    errors = []
    warnings = []
    metrics = {}
    
    if not os.path.exists(annotation_file):
        return ValidationResult(
            passed=False,
            errors=[f"Annotation file not found: {annotation_file}"],
            warnings=[],
            info={}
        )
    
    # Load annotations
    with open(annotation_file, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    # Calculate metrics for each axis
    axes = ['social', 'avoidant', 'mechanical', 'self']
    
    for axis in axes:
        # Extract annotations for this axis
        annotator1_scores = []
        annotator2_scores = []
        
        for item in annotations.get('items', []):
            if axis in item.get('annotations', {}):
                scores = item['annotations'][axis]
                if len(scores) >= 2:
                    annotator1_scores.append(scores[0])
                    annotator2_scores.append(scores[1])
        
        if len(annotator1_scores) < 10:
            warnings.append(f"{axis}: Insufficient annotations ({len(annotator1_scores)} samples)")
            continue
        
        # Calculate metrics
        kappa = calculate_weighted_kappa(annotator1_scores, annotator2_scores)
        
        # For F1, we need predicted vs true labels
        # Here we use annotator consensus as "true" label
        consensus_scores = [
            round(np.mean([s1, s2])) 
            for s1, s2 in zip(annotator1_scores, annotator2_scores)
        ]
        
        # Simulate predictions for F1 calculation (in real scenario, use model predictions)
        # For CI check, we calculate inter-annotator F1
        f1 = calculate_macro_f1(consensus_scores, annotator1_scores)
        
        metrics[axis] = {
            'weighted_kappa': kappa,
            'macro_f1': f1,
            'n_samples': len(annotator1_scores)
        }
        
        # Check thresholds
        if kappa < 0.60:
            warnings.append(
                f"{axis}: Low inter-annotator agreement (κ={kappa:.3f} < 0.60)"
            )
        
        if f1 < 0.60:
            warnings.append(
                f"{axis}: Low F1 score (F1={f1:.3f} < 0.60)"
            )
    
    # Overall metrics
    overall_kappa = np.mean([m['weighted_kappa'] for m in metrics.values()])
    overall_f1 = np.mean([m['macro_f1'] for m in metrics.values()])
    
    metrics['overall'] = {
        'mean_weighted_kappa': overall_kappa,
        'mean_macro_f1': overall_f1
    }
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info={'metrics': metrics}
    )

def main():
    """Main entry point for CI"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Check annotation quality metrics')
    parser.add_argument('--annotation-file', default='corpus/annotations/pilot_annotations.json')
    parser.add_argument('--output-format', choices=['json', 'text'], default='text')
    args = parser.parse_args()
    
    result = check_annotation_quality(args.annotation_file)
    
    if args.output_format == 'json':
        report = {
            'passed': result.passed,
            'errors': result.errors,
            'warnings': result.warnings,
            'metrics': result.info.get('metrics', {})
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("Annotation Quality Check")
        print("=" * 50)
        
        if result.errors:
            print("\nERRORS:")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.warnings:
            print("\nWARNINGS:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        metrics = result.info.get('metrics', {})
        if metrics:
            print("\nMETRICS:")
            for axis, values in metrics.items():
                if axis != 'overall':
                    print(f"\n  {axis.upper()}:")
                    print(f"    Weighted κ: {values['weighted_kappa']:.3f}")
                    print(f"    Macro F1:   {values['macro_f1']:.3f}")
                    print(f"    Samples:    {values['n_samples']}")
            
            if 'overall' in metrics:
                print(f"\n  OVERALL:")
                print(f"    Mean κ:  {metrics['overall']['mean_weighted_kappa']:.3f}")
                print(f"    Mean F1: {metrics['overall']['mean_macro_f1']:.3f}")
    
    sys.exit(0 if result.passed and not result.warnings else 1)

if __name__ == '__main__':
    main()
```

#### B.1.10 CI検証項目テーブル

| 検証項目 | 実行スクリプト | 検証内容 | 失敗条件 |
|----------|---------------|----------|----------|
| アノテーション品質 | `check_annotation_metrics.py` | 評価者間一致率とF1スコア | κ<0.60 or Macro-F1<0.60 |
| アノテーション完全性 | `check_annotation_metrics.py` | 必須軸の評価存在 | 4軸いずれかの欠損 |
| 評価者数 | `check_annotation_metrics.py` | 最小評価者数確認 | <3人/対話 |
| 時系列一貫性 | `check_annotation_metrics.py` | 評価時期の妥当性 | 未来日付の検出 |
| ログスキーマ準拠性 | `validate_annotation_logs.py` | JSONスキーマ検証 | スキーマ違反 |
| ログ時刻論理性 | `validate_annotation_logs.py` | タイムスタンプ整合性 | 差分>0.1秒 |
| UI定義整合性 | `check_ui_consistency.py` | ラベル・スケール一致 | 不一致検出 |

##### B.1.11 Nightly Annotation Quality Job

```yaml
# .github/workflows/annotation_quality.yml
name: Annotation Quality Check

on:
  schedule:
    - cron: '0 2 * * *'  # 毎日午前2時（UTC）
  workflow_dispatch:  # 手動実行も可能

jobs:
  check-quality:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install numpy scikit-learn
    
    - name: Check annotation metrics
      run: |
        python ci/check_annotation_metrics.py \
          --annotation-file corpus/annotations/pilot_annotations.json \
          --output-format json > annotation_metrics.json
    
     - name: Validate annotation logs
      run: python src/ci/validate_annotation_logs.py --log-dir annotation/logs/current/
    
    - name: Check UI consistency
      run: python src/ci/check_ui_consistency.py --snapshot-file ci/snapshots/ui_spec.json   
    
    - name: Upload metrics report
      uses: actions/upload-artifact@v3
      with:
        name: annotation-metrics
        path: annotation_metrics.json
    
    - name: Post to Slack on warnings
      if: failure()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'Annotation quality check detected issues. Please review the metrics.'
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

##### B.1.12 アノテーションログ検証

```python
def validate_annotation_logs(log_dir: str) -> ValidationResult:
    """アノテーションログのJSONスキーマ準拠性を検証"""
    errors = []
    warnings = []
    
    schema = {
        "type": "object",
        "required": [
            "annotator_id", "target_id", "scores", 
            "timestamp_start", "timestamp_end", "annotation_duration",
            "is_modified", "browser_meta", "confidence_flag"
        ],
        "properties": {
            "annotator_id": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "target_id": {"type": "string", "format": "uuid"},
            "scores": {
                "type": "object",
                "required": ["social", "avoidant", "mechanical", "self"],
                "properties": {
                    "social": {"type": "integer", "minimum": 0, "maximum": 4},
                    "avoidant": {"type": "integer", "minimum": 0, "maximum": 4},
                    "mechanical": {"type": "integer", "minimum": 0, "maximum": 4},
                    "self": {"type": "integer", "minimum": 0, "maximum": 4}
                }
            }
        }
    }
    
    for log_file in glob.glob(os.path.join(log_dir, "*.jsonl")):
        with open(log_file, 'r') as f:
            for line_no, line in enumerate(f, 1):
                try:
                    record = json.loads(line)
                    jsonschema.validate(record, schema)
                    
                    # タイムスタンプ論理性チェック
                    start = datetime.fromisoformat(record['timestamp_start'])
                    end = datetime.fromisoformat(record['timestamp_end'])
                    duration = record['annotation_duration']
                    
                    calculated = (end - start).total_seconds()
                    if abs(calculated - duration) > 0.1:
                        warnings.append(
                            f"{log_file}:{line_no}: Duration mismatch "
                            f"(calculated: {calculated}, recorded: {duration})"
                        )
                        
                except json.JSONDecodeError as e:
                    errors.append(f"{log_file}:{line_no}: Invalid JSON - {e}")
                except jsonschema.ValidationError as e:
                    errors.append(f"{log_file}:{line_no}: Schema violation - {e}")
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info={'files_checked': len(list(glob.glob(os.path.join(log_dir, "*.jsonl"))))}
    )
```

##### B.1.13 UI整合性チェック

```python
def check_ui_consistency(snapshot_file: str = "ci/snapshots/ui_spec.json") -> ValidationResult:
    """UI要素とアノテーション定義の整合性を検証"""
    errors = []
    
    # UIスナップショット読み込み
    if not os.path.exists(snapshot_file):
        return ValidationResult(
            passed=False,
            errors=[f"UI snapshot not found: {snapshot_file}"],
            warnings=[],
            info={}
        )
    
    with open(snapshot_file, 'r') as f:
        ui_spec = json.load(f)
    
    # 期待される要素
    expected_axes = ['social', 'avoidant', 'mechanical', 'self']
    expected_labels = {
        'social': '社会的迎合',
        'avoidant': '回避的迎合',
        'mechanical': '機械的迎合',
        'self': '自己迎合'
    }
    expected_scale = {
        0: 'なし',
        1: 'わずか',
        2: '中程度',
        3: '強い',
        4: '極度'
    }
    
    # UIスナップショットとの照合
    ui_axes = ui_spec.get('score_inputs', {})
    for axis in expected_axes:
        if axis not in ui_axes:
            errors.append(f"Missing UI element for axis: {axis}")
        else:
            # ラベルチェック
            if ui_axes[axis].get('label') != expected_labels[axis]:
                errors.append(
                    f"Label mismatch for {axis}: "
                    f"expected '{expected_labels[axis]}', "
                    f"got '{ui_axes[axis].get('label')}'"
                )
            
            # スケールチェック
            ui_options = ui_axes[axis].get('options', {})
            for value, label in expected_scale.items():
                if str(value) not in ui_options or ui_options[str(value)] != label:
                    errors.append(
                        f"Scale mismatch for {axis}[{value}]: "
                        f"expected '{label}', got '{ui_options.get(str(value))}'"
                    )
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=[],
        info={'snapshot_timestamp': ui_spec.get('timestamp')}
    )
```

#### B.2 セキュリティ検査

##### B.2.1 Pickle使用検出

```python
def scan_pickle_usage() -> ValidationResult:
    """セキュリティリスクのあるPickle使用を検出"""
    errors = []
    warnings = []
    pickle_usage = []
    
    for root, dirs, files in os.walk('src'):
        # __pycache__をスキップ
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath) as f:
                    content = f.read()
                
                # pickle使用の検出
                if 'import pickle' in content or 'from pickle' in content:
                    # 警告コメントの確認
                    if 'trusted source only' not in content.lower():
                        errors.append(
                            f"{filepath}: Pickle usage without security warning"
                        )
                    else:
                        warnings.append(
                            f"{filepath}: Pickle usage with warning (consider joblib)"
                        )
                    
                    pickle_usage.append(filepath)
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info={'pickle_files': pickle_usage}
    )
```

##### B.2.2 依存関係脆弱性検査

```python
def check_dependency_vulnerabilities() -> ValidationResult:
    """既知の脆弱性を持つ依存関係を検出"""
    import subprocess
    
    try:
        # safetyによる脆弱性検査
        result = subprocess.run(
            ['safety', 'check', '--json'],
            capture_output=True,
            text=True
        )
        
        vulnerabilities = json.loads(result.stdout)
        
        if vulnerabilities:
            errors = [
                f"{v['package']}: {v['vulnerability']}" 
                for v in vulnerabilities
            ]
            return ValidationResult(
                passed=False,
                errors=errors,
                warnings=[],
                info={'vulnerabilities': vulnerabilities}
            )
        
        return ValidationResult(
            passed=True,
            errors=[],
            warnings=[],
            info={'message': 'No vulnerabilities found'}
        )
        
    except Exception as e:
        return ValidationResult(
            passed=False,
            errors=[f"Failed to run safety check: {e}"],
            warnings=[],
            info={}
        )
```

#### B.3 GitHub Actions設定

##### B.3.1 validate.yml

```yaml
name: Validate Configuration

on:
  push:
    paths:
      - 'config/*.yaml'
      - 'src/ci/**'
  pull_request:
    paths:
      - 'config/*.yaml'
      - 'src/ci/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r src/requirements.txt
        pip install jsonschema pyyaml
    
    - name: Validate YAML configs
      run: python src/ci/schema_validate.py
    
    - name: Check tokenizer consistency
      run: python src/ci/check_tokenizer.py
    
    - name: Check version consistency
      run: python src/ci/check_versions.py

    - name: Check anonymization
      run: python src/ci/check_anonymization.py --corpus-dir corpus/jsonl/

    - name: Check annotation metrics
      run: python src/ci/check_annotation_metrics.py --annotation-file corpus/annotations/pilot_annotations.json
    
    - name: Generate report
      if: always()
      run: |
        python src/ci/run_all_checks.py --output-format markdown > validation_report.md
    
    - name: Upload report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: validation-report
        path: validation_report.md
```

##### B.3.2 security.yml

```yaml
name: Security Audit

on:
  schedule:
    - cron: '0 0 * * 1'  # 毎週月曜日
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install security tools
      run: |
        pip install bandit safety
    
    - name: Run bandit
      run: bandit -r src/ -f json -o bandit_report.json
    
    - name: Run safety check
      run: safety check --json > safety_report.json
    
    - name: Check for pickle usage
      run: python src/ci/check_security.py
    
    - name: Upload security reports
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit_report.json
          safety_report.json
```

#### B.4 cluster_metrics.json スキーマ

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Cluster Metrics Report",
  "type": "object",
  "required": ["timestamp", "algorithm", "n_clusters", "silhouette_score", "clusters"],
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of report generation"
    },
    "algorithm": {
      "type": "string",
      "enum": ["k-means", "dbscan", "hierarchical"],
      "description": "Clustering algorithm used"
    },
    "n_clusters": {
      "type": "integer",
      "minimum": 2,
      "description": "Number of clusters identified"
    },
    "silhouette_score": {
      "type": "number",
      "minimum": -1,
      "maximum": 1,
      "description": "Overall silhouette coefficient"
    },
    "clusters": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "size", "silhouette_score", "representative_terms"],
        "properties": {
          "id": {
            "type": "integer",
            "minimum": 0
          },
          "size": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of terms in cluster"
          },
          "silhouette_score": {
            "type": "number",
            "minimum": -1,
            "maximum": 1,
            "description": "Cluster-specific silhouette score"
          },
          "representative_terms": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "minItems": 1,
            "maxItems": 10,
            "description": "Most representative terms in cluster"
          },
          "annotation_difficulty": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "description": "Estimated annotation difficulty based on silhouette score"
          }
        }
      }
    }
  }
}
```

#### B.5 changelog.json ハッシュ必須化

```python
def validate_changelog_hash(changelog_path: str) -> ValidationResult:
    """Validate that all changelog entries have file_hash"""
    errors = []
    warnings = []
    
    with open(changelog_path, 'r', encoding='utf-8') as f:
        changelog = json.load(f)
    
    for idx, version in enumerate(changelog.get('versions', [])):
        if 'file_hash' not in version:
            errors.append(
                f"Version entry {idx} (timestamp: {version.get('timestamp', 'unknown')}): "
                f"Missing required 'file_hash' field"
            )
        elif not version['file_hash'].startswith('sha256:'):
            warnings.append(
                f"Version entry {idx}: file_hash should start with 'sha256:' prefix"
            )
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info={'total_versions': len(changelog.get('versions', []))}
    )
```

#### B.6 UIスナップショット仕様

```json
// ci/snapshots/ui_spec.json
{
  "timestamp": "2025-01-15T10:00:00Z",
  "version": "1.0",
  "score_inputs": {
    "social": {
      "label": "社会的迎合",
      "options": {
        "0": "なし",
        "1": "わずか",
        "2": "中程度",
        "3": "強い",
        "4": "極度"
      }
    },
    "avoidant": { ... },
    "mechanical": { ... },
    "self": { ... }
  },
  "confidence_options": {
    "certain": "確信",
    "uncertain": "不確信"
  },
  "required_elements": ["dialogue_history", "current_pair", "timer_display"]
}
```