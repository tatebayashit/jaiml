### A. 統一記述セクション

#### A.1 概要

**仕様書名**: JAIML アノテーションログ記録仕様書 v1.0

**目的**: アノテーション作業の詳細なログを記録し、品質分析、作業効率評価、モデル比較のためのデータ基盤を提供する。

**記録方針**:
- 全アノテーション活動の完全な監査証跡
- プライバシーに配慮した個人情報の匿名化
- モデル出力との比較分析を可能にする構造

#### A.2 モジュール構成と責務

```
src/annotation_logging/
├── collectors/
│   ├── ui_event_collector.py     # UI操作イベント収集
│   ├── api_collector.py          # API呼び出し記録
│   └── browser_collector.js      # ブラウザメタデータ収集
├── processors/
│   ├── anonymizer.py             # 個人情報匿名化
│   ├── duration_calculator.py    # 作業時間計算
│   └── model_snapshot.py         # モデル出力記録
├── storage/
│   ├── db_writer.py              # データベース書き込み
│   ├── archive_manager.py        # アーカイブ管理
│   └── version_controller.py     # バージョン管理
└── analyzers/
    ├── confidence_analyzer.py     # 信頼度影響分析
    ├── efficiency_analyzer.py     # 作業効率分析
    └── quality_metrics.py         # 品質指標算出
```

#### A.3 入出力仕様

**入力**:
- UIイベントストリーム
- アノテーション送信データ
- モデル推論API応答
- ブラウザ環境情報

**出力**:
- 構造化ログレコード（JSON）
- 集計レポート
- 分析用データセット

#### A.4 パラメータ定義

**ログ設定パラメータ**:
- `retention_days`: 365  # ログ保持期間
- `batch_size`: 100  # バッチ書き込みサイズ
- `compression`: "gzip"  # アーカイブ圧縮形式
- `hash_algorithm`: "sha256"  # 匿名化ハッシュ
- `snapshot_enabled`: true  # モデル出力記録

#### A.5 関連ファイル構成

```
logs/
├── current/
│   └── annotations_YYYYMMDD.jsonl
├── archive/
│   └── annotations_YYYYMM.jsonl.gz
└── analysis/
    ├── daily_summary.json
    └── quality_report.json

database/
├── annotation_latest  # 最新版テーブル
└── annotation_history # 履歴テーブル
```

#### A.6 使用例とコマンドライン

**ログ収集開始**:
```bash
python -m annotation_logging.start --config config/logging.yaml
```

**分析レポート生成**:
```bash
python -m annotation_logging.analyze \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --output reports/monthly_analysis.json
```

**アーカイブ実行**:
```bash
python -m annotation_logging.archive --older-than 30
```

#### A.7 CI検証項目

1. **スキーマ検証**: 全ログレコードのJSONスキーマ準拠
2. **匿名化検証**: 個人情報の完全マスキング
3. **時刻整合性**: タイムスタンプの論理的一貫性
4. **データ完全性**: 欠損フィールドなし
5. **圧縮効率**: 70%以上の圧縮率
6. **クエリ性能**: 1ヶ月分の集計を10秒以内

#### A.8 インターフェース定義（型注釈付き）

```python
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass

@dataclass
class AnnotationLog:
    annotator_id: str  # SHA-256ハッシュ
    target_id: str     # 対話ID
    scores: Dict[str, int]
    timestamp_start: datetime
    timestamp_end: datetime
    annotation_duration: float
    is_modified: bool
    browser_meta: Dict[str, str]
    confidence_flag: str
    model_snapshot: Optional[Dict[str, Any]]

class LogCollector:
    def collect_ui_event(self, event: Dict[str, Any]) -> None:
        """UIイベントの収集"""
    
    def capture_submission(self, data: AnnotationLog) -> str:
        """アノテーション送信の記録"""
    
    def add_model_snapshot(self, annotation_id: str, 
                          model_output: Dict) -> None:
        """モデル出力の追加"""
```

#### A.9 既知の制約と注意事項

1. **ストレージ容量**: 1日あたり約100MB増加
2. **GDPR準拠**: 個人データの削除要求対応必須
3. **時刻同期**: NTPによるサーバー時刻同期必須
4. **並行性**: 同時書き込みでのデッドロック注意
5. **バックアップ**: 日次バックアップ必須

### B. 詳細仕様セクション

#### B.1 JSONスキーマ定義

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "annotator_id", "target_id", "scores", 
    "timestamp_start", "timestamp_end", "annotation_duration",
    "is_modified", "browser_meta", "confidence_flag"
  ],
  "properties": {
    "annotator_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "SHA-256ハッシュ化されたアノテーターID"
    },
    "target_id": {
      "type": "string",
      "format": "uuid",
      "description": "対話ペアの一意識別子"
    },
    "scores": {
      "type": "object",
      "required": ["social", "avoidant", "mechanical", "self"],
      "properties": {
        "social": {"type": "integer", "minimum": 0, "maximum": 4},
        "avoidant": {"type": "integer", "minimum": 0, "maximum": 4},
        "mechanical": {"type": "integer", "minimum": 0, "maximum": 4},
        "self": {"type": "integer", "minimum": 0, "maximum": 4}
      }
    },
    "timestamp_start": {
      "type": "string",
      "format": "date-time",
      "description": "アノテーション開始時刻（ISO-8601）"
    },
    "timestamp_end": {
      "type": "string",
      "format": "date-time",
      "description": "アノテーション終了時刻（ISO-8601）"
    },
    "annotation_duration": {
      "type": "number",
      "minimum": 0,
      "description": "作業時間（秒）"
    },
    "is_modified": {
      "type": "boolean",
      "description": "再アノテーションフラグ"
    },
    "browser_meta": {
      "type": "object",
      "properties": {
        "user_agent": {"type": "string"},
        "os": {"type": "string"},
        "viewport": {"type": "string"}
      }
    },
    "confidence_flag": {
      "type": "string",
      "enum": ["certain", "uncertain"],
      "description": "アノテーター自己申告の確信度"
    },
    "model_snapshot": {
      "type": "object",
      "properties": {
        "scores": {
          "type": "object",
          "properties": {
            "social": {"type": "number"},
            "avoidant": {"type": "number"},
            "mechanical": {"type": "number"},
            "self": {"type": "number"}
          }
        },
        "predicted_category": {
          "type": "string",
          "enum": ["social", "avoidant", "mechanical", "self"]
        }
      },
      "description": "推論API応答のスナップショット"
    }
  }
}
```

#### B.2 データ収集実装

##### B.2.1 UIイベント収集

```javascript
class UIEventCollector {
  constructor(apiEndpoint) {
    this.apiEndpoint = apiEndpoint;
    this.eventBuffer = [];
    this.sessionId = this.generateSessionId();
  }
  
  trackScoreChange(axis, oldValue, newValue) {
    this.eventBuffer.push({
      type: 'score_change',
      axis: axis,
      old_value: oldValue,
      new_value: newValue,
      timestamp: new Date().toISOString()
    });
  }
  
  trackConfidenceChange(value) {
    this.eventBuffer.push({
      type: 'confidence_change',
      value: value,
      timestamp: new Date().toISOString()
    });
  }
  
  trackSubmission(scores, confidence, startTime) {
    const endTime = new Date();
    const duration = (endTime - startTime) / 1000;
    
    const logData = {
      annotator_id: this.getHashedAnnotatorId(),
      target_id: this.getCurrentTaskId(),
      scores: scores,
      timestamp_start: startTime.toISOString(),
      timestamp_end: endTime.toISOString(),
      annotation_duration: duration,
      is_modified: this.isModification(),
      browser_meta: this.getBrowserMeta(),
      confidence_flag: confidence,
      ui_events: this.eventBuffer
    };
    
    return fetch(`${this.apiEndpoint}/log`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(logData)
    });
  }
  
  getBrowserMeta() {
    return {
      user_agent: navigator.userAgent,
      os: this.detectOS(),
      viewport: `${window.innerWidth}x${window.innerHeight}`
    };
  }
}
```

##### B.2.2 匿名化処理

```python
import hashlib
from datetime import datetime

class AnnotatorAnonymizer:
    def __init__(self, salt: str):
        self.salt = salt.encode()
    
    def anonymize_id(self, original_id: str) -> str:
        """SHA-256による不可逆ハッシュ化"""
        data = (original_id + self.salt.decode()).encode()
        return hashlib.sha256(data).hexdigest()
    
    def process_log_entry(self, log_entry: dict) -> dict:
        """ログエントリの匿名化処理"""
        # アノテーターIDをハッシュ化
        if 'annotator_id' in log_entry:
            log_entry['annotator_id'] = self.anonymize_id(
                log_entry['annotator_id']
            )
        
        # その他の個人情報を除去
        sensitive_fields = ['ip_address', 'session_id', 'email']
        for field in sensitive_fields:
            log_entry.pop(field, None)
        
        return log_entry
```

##### B.2.3 モデルスナップショット記録

```python
class ModelSnapshotCollector:
    def __init__(self, inference_api_url: str):
        self.api_url = inference_api_url
    
    async def capture_snapshot(self, user_text: str, 
                              response_text: str) -> dict:
        """推論APIを呼び出してモデル出力を記録"""
        payload = {
            "user": user_text,
            "response": response_text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload) as resp:
                result = await resp.json()
        
        # 必要な情報のみ抽出
        snapshot = {
            "scores": result["scores"],
            "predicted_category": result["predicted_category"],
            "inference_timestamp": datetime.utcnow().isoformat()
        }
        
        return snapshot
```

#### B.3 バージョン管理実装

##### B.3.1 履歴管理

```python
class AnnotationVersionController:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def save_annotation(self, log_entry: AnnotationLog) -> str:
        """最新版の保存と履歴の管理"""
        # 既存レコードの確認
        existing = self.db.query(
            "SELECT * FROM annotation_latest WHERE target_id = ?",
            (log_entry.target_id,)
        ).fetchone()
        
        if existing:
            # 既存レコードを履歴テーブルに移動
            self.db.execute(
                "INSERT INTO annotation_history SELECT * FROM annotation_latest WHERE target_id = ?",
                (log_entry.target_id,)
            )
            
            # 変更フラグを設定
            log_entry.is_modified = True
            
            # 差分を計算
            delta = self.calculate_delta(existing, log_entry)
            log_entry.delta_json = json.dumps(delta)
        
        # 最新版を更新
        self.db.execute(
            "REPLACE INTO annotation_latest (...) VALUES (...)",
            log_entry.to_tuple()
        )
        
        return log_entry.target_id
    
    def calculate_delta(self, old: dict, new: AnnotationLog) -> dict:
        """新旧アノテーションの差分計算"""
        delta = {
            "changed_fields": [],
            "score_changes": {}
        }
        
        # スコアの変更を記録
        for axis in ['social', 'avoidant', 'mechanical', 'self']:
            if old['scores'][axis] != new.scores[axis]:
                delta["score_changes"][axis] = {
                    "old": old['scores'][axis],
                    "new": new.scores[axis]
                }
                delta["changed_fields"].append(f"scores.{axis}")
        
        # 信頼度の変更
        if old.get('confidence_flag') != new.confidence_flag:
            delta["confidence_change"] = {
                "old": old.get('confidence_flag'),
                "new": new.confidence_flag
            }
            delta["changed_fields"].append("confidence_flag")
        
        return delta
```

##### B.3.2 アーカイブ処理

```python
import gzip
import shutil
from datetime import datetime, timedelta

class LogArchiveManager:
    def __init__(self, log_dir: str, archive_dir: str):
        self.log_dir = Path(log_dir)
        self.archive_dir = Path(archive_dir)
    
    def archive_old_logs(self, days_old: int = 30):
        """指定日数以前のログをアーカイブ"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        for log_file in self.log_dir.glob("annotations_*.jsonl"):
            # ファイル名から日付を抽出
            file_date = self.extract_date_from_filename(log_file.name)
            
            if file_date < cutoff_date:
                # gzip圧縮
                compressed_path = self.archive_dir / f"{log_file.stem}.jsonl.gz"
                
                with open(log_file, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # 元ファイルを削除
                log_file.unlink()
                
                print(f"Archived: {log_file.name} -> {compressed_path.name}")
    
    def extract_date_from_filename(self, filename: str) -> datetime:
        """ファイル名から日付を抽出（annotations_YYYYMMDD.jsonl）"""
        date_str = filename.split('_')[1].split('.')[0]
        return datetime.strptime(date_str, '%Y%m%d')
```

#### B.4 分析機能実装

##### B.4.1 信頼度影響分析

```python
class ConfidenceAnalyzer:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def analyze_confidence_impact(self) -> dict:
        """信頼度フラグ別の品質指標を分析"""
        # 信頼度別にデータを取得
        certain_data = self.get_annotations_by_confidence('certain')
        uncertain_data = self.get_annotations_by_confidence('uncertain')
        
        # Weighted-κの計算
        kappa_certain = self.calculate_group_kappa(certain_data)
        kappa_uncertain = self.calculate_group_kappa(uncertain_data)
        
        # 統計的検定
        from scipy import stats
        statistic, p_value = stats.mannwhitneyu(
            [a['agreement_score'] for a in certain_data],
            [a['agreement_score'] for a in uncertain_data],
            alternative='greater'
        )
        
        return {
            "certain_group": {
                "n": len(certain_data),
                "weighted_kappa": kappa_certain,
                "avg_duration": np.mean([a['annotation_duration'] 
                                       for a in certain_data])
            },
            "uncertain_group": {
                "n": len(uncertain_data),
                "weighted_kappa": kappa_uncertain,
                "avg_duration": np.mean([a['annotation_duration'] 
                                       for a in uncertain_data])
            },
            "statistical_test": {
                "method": "Mann-Whitney U",
                "statistic": statistic,
                "p_value": p_value,
                "significant": p_value < 0.05
            }
        }
    
    def calculate_group_kappa(self, annotations: List[dict]) -> float:
        """グループ内のWeighted-κを計算"""
        from sklearn.metrics import cohen_kappa_score
        
        # ペアワイズκの平均を計算
        kappa_scores = []
        
        # 同じtarget_idを持つアノテーションをグループ化
        grouped = defaultdict(list)
        for ann in annotations:
            grouped[ann['target_id']].append(ann)
        
        # 2人以上のアノテーターがいるケースでκを計算
        for target_id, group in grouped.items():
            if len(group) >= 2:
                for i in range(len(group) - 1):
                    for j in range(i + 1, len(group)):
                        # 各軸でκを計算して平均
                        axis_kappas = []
                        for axis in ['social', 'avoidant', 'mechanical', 'self']:
                            k = cohen_kappa_score(
                                [group[i]['scores'][axis]],
                                [group[j]['scores'][axis]],
                                weights='quadratic'
                            )
                            axis_kappas.append(k)
                        kappa_scores.append(np.mean(axis_kappas))
        
        return np.mean(kappa_scores) if kappa_scores else 0.0
```

##### B.4.2 作業効率分析

```python
class EfficiencyAnalyzer:
    def analyze_annotator_efficiency(self, start_date: datetime, 
                                   end_date: datetime) -> dict:
        """アノテーター別の作業効率を分析"""
        query = """
        SELECT 
            annotator_id,
            COUNT(*) as total_annotations,
            AVG(annotation_duration) as avg_duration,
            MIN(annotation_duration) as min_duration,
            MAX(annotation_duration) as max_duration,
            SUM(CASE WHEN is_modified THEN 1 ELSE 0 END) as modifications
        FROM annotation_latest
        WHERE timestamp_start BETWEEN ? AND ?
        GROUP BY annotator_id
        """
        
        results = self.db.execute(query, (start_date, end_date)).fetchall()
        
        # 効率指標の計算
        efficiency_metrics = []
        for row in results:
            metric = {
                "annotator_id": row["annotator_id"],
                "total_annotations": row["total_annotations"],
                "avg_duration_seconds": row["avg_duration"],
                "throughput_per_hour": 3600 / row["avg_duration"],
                "modification_rate": row["modifications"] / row["total_annotations"],
                "consistency_score": 1.0 - row["modification_rate"]
            }
            efficiency_metrics.append(metric)
        
        # 全体統計
        overall_stats = {
            "total_annotators": len(efficiency_metrics),
            "total_annotations": sum(m["total_annotations"] for m in efficiency_metrics),
            "avg_throughput": np.mean([m["throughput_per_hour"] for m in efficiency_metrics]),
            "avg_consistency": np.mean([m["consistency_score"] for m in efficiency_metrics])
        }
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "annotator_metrics": efficiency_metrics,
            "overall_statistics": overall_stats
        }
```