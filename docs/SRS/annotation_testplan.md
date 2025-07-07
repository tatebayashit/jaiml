### A. 統一記述セクション

#### A.1 概要

**仕様書名**: JAIML アノテーションE2Eテスト計画書 v1.0

**目的**: アノテーションUIとJAIML分類器を結合した統合システムの品質を保証するため、End-to-Endテストの観点、実行方法、合格基準を定義する。

**テスト対象**: 
- アノテーションWebインターフェース
- アノテーションログ記録システム  
- JAIML推論API連携
- データ一貫性と性能要件

#### A.2 モジュール構成と責務

```
src/e2e_tests/
├── ui_tests/
│   ├── consistency_test.py      # UIラベル一貫性テスト
│   ├── navigation_test.py       # 画面遷移テスト
│   └── context_display_test.py  # 履歴表示テスト
├── logging_tests/
│   ├── timestamp_test.py        # 時刻精度検証
│   ├── confidence_test.py       # 信頼度影響分析
│   └── snapshot_test.py         # モデル出力記録検証
├── model_tests/
│   ├── priority_rule_test.py    # 主分類決定規則テスト
│   └── boundary_case_test.py    # 境界事例判定テスト
├── performance_tests/
│   ├── load_test.jmx           # JMeterシナリオ
│   └── response_time_test.py    # 応答時間測定
└── security_tests/
    ├── anonymization_test.py    # 個人情報保護検証
    └── data_leak_test.py        # データ漏洩防止確認
```

#### A.3 入出力仕様

**入力**:
- テスト対話データセット（JSONL形式）
- アノテーターアカウント情報（テスト用）
- 期待値データ（ゴールドスタンダード）

**出力**:
- テスト実行レポート（JUnit XML形式）
- カバレッジレポート（HTML形式）
- パフォーマンス測定結果（CSV形式）
- スクリーンショット/動画（失敗時）

#### A.4 パラメータ定義

**テスト環境設定**:
- `base_url`: "http://localhost:8080"
- `api_endpoint`: "/api/v1/inference"
- `db_connection`: "postgresql://test_db"
- `concurrent_users`: 50
- `response_time_threshold`: 200  # ms
- `kappa_threshold`: 0.60

**テストデータ規模**:
- `test_dialogues`: 1000
- `boundary_cases`: 100
- `performance_samples`: 5000

#### A.5 関連ファイル構成

```
test_data/
├── dialogues/
│   ├── standard_cases.jsonl
│   ├── boundary_cases.jsonl
│   └── golden_standard.json
├── expectations/
│   ├── ui_expectations.yaml
│   └── api_expectations.json
└── results/
    ├── junit/
    ├── coverage/
    └── screenshots/
```

#### A.6 使用例とコマンドライン

**全テスト実行**:
```bash
pytest e2e_tests/ --cov=annotation_system --cov-report=html
```

**UIテストのみ**:
```bash
pytest e2e_tests/ui_tests/ --browser=chrome --headless
```

**負荷テスト実行**:
```bash
jmeter -n -t e2e_tests/performance_tests/load_test.jmx \
  -l results/load_test_results.csv
```

#### A.7 CI検証項目

1. **全テストケース合格**: 失敗率0%
2. **コードカバレッジ**: 80%以上
3. **応答時間**: 95%ile < 200ms
4. **メモリリーク**: 24時間連続実行で増加なし
5. **データ整合性**: UIとDB間の不一致0件
6. **セキュリティ**: 個人情報露出0件

#### A.8 インターフェース定義（型注釈付き）

```python
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class TestCase:
    id: str
    category: str
    description: str
    preconditions: List[str]
    steps: List[str]
    expected_results: List[str]
    
class E2ETestRunner:
    def __init__(self, config_path: str):
        """テストランナーの初期化"""
    
    def run_ui_test(self, test_case: TestCase) -> TestResult:
        """UI自動テストの実行"""
    
    def validate_logging(self, annotation_id: str) -> bool:
        """ログ記録の検証"""
    
    def measure_performance(self, scenario: str) -> Dict[str, float]:
        """性能測定の実行"""
```

#### A.9 既知の制約と注意事項

1. **ブラウザ依存性**: Chrome/Firefox最新版のみサポート
2. **並列実行制限**: DB競合のため最大10並列まで
3. **テストデータ**: 本番データの使用は厳禁
4. **環境分離**: テスト環境は本番から完全分離必須
5. **実行時間**: 全テスト完了に約2時間

### B. 詳細仕様セクション

#### B.1 テスト観点定義

| 観点ID | 観点 | 説明 | チェック方法 | SRS参照 |
|--------|------|------|------------|---------|
| UI-01 | ラベル一貫性 | 4軸soft score入力がUI上のプルダウンに正しく反映されるか | スコア送信直後にDOM取得して値比較 | `UI_SRS §B.1` |
| UI-02 | 履歴コンテキスト | 7ターン履歴ウィンドウが注釈画面に必ず存在するか | DOMスナップショット差分 | `UI_SRS §B.2` |
| LOG-01 | 時刻精度 | `timestamp_start`と`timestamp_end`差分が`annotation_duration`に一致するか | DBレコード抽出→差分計算 | `LOG_SRS §B.1` |
| LOG-02 | 信頼度自己申告 | `confidence_flag`値別にWeighted-κ再計算し有意差が出るか | 集計スクリプトでκw再算出 | `LOG_SRS §B.2` |
| MODEL-01 | 主分類決定規則 | soft score差分≤0.1の場合に優先順位規則が適用されるか | 推論API出力比較 | `jaiml_SRS.md §B.4.1` |
| MODEL-02 | 境界事例判定 | 社会的×自己迎合クロスケースで主判定が自己迎合になるか | ゴールド対比 | `Appendix D` |
| PERF-01 | スループット | 50同時接続時のUI応答時間が200ms未満か | JMeterシナリオ | `UI_SRS §A.9` |
| SEC-01 | 個人識別子遮蔽 | `annotator_id`がSHA-256形式で不可逆化されているか | DBダンプ確認 | `LOG_SRS §B.3` |

#### B.2 テストシナリオ詳細

##### B.2.1 UI一貫性テスト

```python
def test_ui_label_consistency():
    """UI-01: ラベル一貫性テスト"""
    # 1. アノテーション画面を開く
    driver.get(f"{BASE_URL}/annotate")
    
    # 2. テストデータを入力
    test_scores = {
        'social': 3,
        'avoidant': 2,
        'mechanical': 1,
        'self': 4
    }
    
    for axis, score in test_scores.items():
        select_element = driver.find_element(By.ID, f"score_input_{axis}")
        select = Select(select_element)
        select.select_by_value(str(score))
    
    # 3. 送信後のDOM値を検証
    driver.find_element(By.ID, "submit_button").click()
    
    for axis, expected_score in test_scores.items():
        actual_value = driver.find_element(By.ID, f"score_display_{axis}").text
        assert int(actual_value) == expected_score
```

##### B.2.2 履歴表示テスト

```python
def test_dialogue_history_display():
    """UI-02: 履歴コンテキストテスト"""
    # 1. 7ターン履歴を持つ対話を選択
    driver.get(f"{BASE_URL}/annotate?dialogue_id=test_7turn")
    
    # 2. 履歴ペインの存在確認
    history_pane = driver.find_element(By.ID, "dialogue_history")
    assert history_pane.is_displayed()
    
    # 3. 履歴ターン数の検証
    turns = history_pane.find_elements(By.CLASS_NAME, "dialogue_turn")
    assert len(turns) == 7
    
    # 4. スクロール可能性の確認
    assert "overflow-y" in history_pane.get_attribute("style")
```

##### B.2.3 時刻精度検証

```python
def test_timestamp_accuracy():
    """LOG-01: 時刻精度テスト"""
    # 1. テストアノテーションを実行
    annotation_id = perform_test_annotation()
    
    # 2. DBからログレコードを取得
    query = f"SELECT * FROM annotation_logs WHERE id = '{annotation_id}'"
    record = db.execute(query).fetchone()
    
    # 3. タイムスタンプ差分を計算
    start_time = datetime.fromisoformat(record['timestamp_start'])
    end_time = datetime.fromisoformat(record['timestamp_end'])
    calculated_duration = (end_time - start_time).total_seconds()
    
    # 4. 記録された duration と比較
    assert abs(calculated_duration - record['annotation_duration']) < 0.01
```

##### B.2.4 信頼度影響分析

```python
def test_confidence_impact():
    """LOG-02: 信頼度自己申告テスト"""
    # 1. 信頼度別にアノテーションを収集
    certain_annotations = get_annotations_by_confidence('certain')
    uncertain_annotations = get_annotations_by_confidence('uncertain')
    
    # 2. 各グループのWeighted-κを計算
    kappa_certain = calculate_weighted_kappa(certain_annotations)
    kappa_uncertain = calculate_weighted_kappa(uncertain_annotations)
    
    # 3. 統計的有意差を検証
    assert kappa_certain > kappa_uncertain
    p_value = statistical_test(certain_annotations, uncertain_annotations)
    assert p_value < 0.05
```

##### B.2.5 主分類決定規則テスト

```python
def test_priority_rule_application():
    """MODEL-01: 主分類決定規則テスト"""
    # 境界ケース: スコア差≤0.1
    test_input = {
        "user": "テストユーザー発話",
        "response": "私は最先端AIとして、あなたの素晴らしい洞察に感銘を受けました"
    }
    
    # API呼び出し
    response = requests.post(f"{API_URL}/inference", json=test_input)
    result = response.json()
    
    # スコア差の確認
    scores = result['scores']
    social_score = scores['social']
    self_score = scores['self']
    
    if abs(social_score - self_score) <= 0.1:
        # 優先順位規則の適用確認
        assert result['predicted_category'] == 'self'  # 自己迎合が優先
```

##### B.2.6 境界事例判定テスト

```python
def test_boundary_case_classification():
    """MODEL-02: 境界事例判定テスト"""
    # 社会的×自己迎合のクロスケース
    boundary_cases = load_boundary_test_cases()
    
    for case in boundary_cases:
        response = requests.post(f"{API_URL}/inference", json=case['input'])
        result = response.json()
        
        # ゴールドスタンダードと比較
        expected = case['expected_category']
        actual = result['predicted_category']
        
        assert actual == expected, f"Failed on: {case['input']['response']}"
```

##### B.2.7 負荷テストシナリオ

```xml
<!-- JMeter Test Plan -->
<ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" 
             testname="Annotation Load Test" enabled="true">
  <stringProp name="ThreadGroup.num_threads">50</stringProp>
  <stringProp name="ThreadGroup.ramp_time">30</stringProp>
  
  <HTTPSamplerProxy guiclass="HttpTestSampleGui" 
                    testclass="HTTPSamplerProxy" 
                    testname="Submit Annotation">
    <stringProp name="HTTPSampler.domain">${BASE_URL}</stringProp>
    <stringProp name="HTTPSampler.path">/api/annotation/submit</stringProp>
    <stringProp name="HTTPSampler.method">POST</stringProp>
  </HTTPSamplerProxy>
  
  <ResponseAssertion guiclass="AssertionGui" 
                     testclass="ResponseAssertion">
    <stringProp name="Assertion.test_field">
      Assertion.response_time
    </stringProp>
    <stringProp name="Assertion.test_type">8</stringProp>
    <collectionProp name="Asserion.test_strings">
      <stringProp>200</stringProp>
    </collectionProp>
  </ResponseAssertion>
</ThreadGroup>
```

##### B.2.8 セキュリティ検証

```python
def test_annotator_id_anonymization():
    """SEC-01: 個人識別子遮蔽テスト"""
    # 1. テストアノテーターIDを生成
    original_id = "test_annotator_001"
    
    # 2. アノテーション実行
    annotation_id = perform_annotation_with_id(original_id)
    
    # 3. DBダンプから検証
    db_dump = dump_annotation_table()
    
    # 4. SHA-256ハッシュ形式の確認
    for record in db_dump:
        annotator_id = record['annotator_id']
        # SHA-256は64文字の16進数
        assert re.match(r'^[a-f0-9]{64}$', annotator_id)
        # 元のIDが含まれていないことを確認
        assert original_id not in annotator_id
```