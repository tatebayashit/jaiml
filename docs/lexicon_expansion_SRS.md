# JAIML v3.3 辞書拡張・自動アノテーション支援基盤 実装準拠仕様書

## 1. 概要（System Overview）

### 1.1 目的
本システムは、JAIML v3.3における語彙辞書の継続的改善と機械学習データの自動生成を支援する統合基盤である。語彙管理の自動化、意味的整理、学習データ生成の3機能を提供する。

### 1.2 システム構成
```
辞書拡張基盤
├── バージョン管理層：辞書の履歴追跡と品質監視
├── 意味解析層：語彙の意味的整理と冗長性検出
└── データ生成層：弱教師付き学習データの自動生成
```

### 1.3 主要特性
- **追跡可能性**: 全ての辞書変更を時系列で記録
- **定量的品質管理**: カバレッジ指標による客観的評価
- **意味的整合性**: 類義語クラスタの自動検出
- **学習データ自動化**: 辞書ベースの弱教師付きアノテーション

## 2. 対象スクリプト一覧

| モジュール | ファイル名 | 機能概要 |
|-----------|----------|----------|
| **バージョン管理** | version_manager.py | 辞書スナップショット管理 |
| | trend_analyzer.py | 時系列分析・異常検出 |
| **意味解析** | semantic_clustering.py | 語彙クラスタリング |
| | overexpression_detector.py | 冗長表現検出 |
| **データ生成** | auto_annotator.py | 自動アノテーション |
| | snippet_generator.py | コンテキスト付きスニペット生成 |
| **統合実行** | run_advanced_features.py | 機能統合実行インターフェース |

## 3. モジュール別仕様

### 3.1 Lexicon Version Management

#### 3.1.1 version_manager.py

**機能**: 辞書のバージョン管理と差分追跡

**主要メソッド**:
- `save_version()`: 現在の辞書状態をタイムスタンプ付きで保存
- `calculate_diff()`: バージョン間の追加・削除語彙を算出
- `generate_diff_report()`: 人間可読な差分レポート生成

**入力**:
- 辞書データ（YAML形式）
- メタデータ（任意）

**出力**:
- バージョンファイル: `jaiml_lexicons_YYYYMMDD_HHMMSS.yaml`
- 変更ログ: `changelog.json`

**データ構造（changelog.json）**:
```json
{
  "versions": [
    {
      "timestamp": "20240115_143052",
      "metadata": {},
      "statistics": {
        "template_phrases": {
          "added": ["新規フレーズ1", "新規フレーズ2"],
          "removed": ["削除フレーズ1"],
          "total_before": 156,
          "total_after": 157,
          "change_rate": 0.0064
        }
      },
      "coverage_metrics": {
        "total_phrases": 2483,
        "category_distribution": {},
        "avg_phrase_length": 12.3,
        "unique_characters": 1052
      }
    }
  ]
}
```

#### 3.1.2 trend_analyzer.py

**機能**: 辞書成長の時系列分析と異常検出

**主要メソッド**:
- `analyze_growth_trend()`: カテゴリ別成長率をDataFrame化
- `plot_coverage_evolution()`: カバレッジ推移の可視化
- `detect_anomalies()`: 閾値ベースの異常変化検出

**入力**:
- 変更ログ（changelog.json）

**出力**:
- トレンドデータ（pandas DataFrame）
- 可視化グラフ（PNG）
- 異常検出リスト

**異常判定基準**:
- 変化率 > 30%: medium severity
- 変化率 > 50%: high severity

### 3.2 Semantic Clustering & Redundancy Detection

#### 3.2.1 semantic_clustering.py

**機能**: fastTextベクトルによる語彙の意味的クラスタリング

**主要メソッド**:
- `vectorize_phrases()`: フレーズを300次元ベクトルに変換
- `cluster_by_similarity()`: 階層的クラスタリングまたはDBSCAN
- `visualize_clusters()`: UMAP次元削減による2D可視化

**入力**:
- カテゴリ名
- フレーズリスト

**出力**:
```python
{
  "clusters": {
    0: ["素晴らしい", "優れている", "秀逸"],
    1: ["ありがとうございます", "感謝します"],
    -1: ["外れ値フレーズ"]  # ノイズ点
  },
  "statistics": {
    0: {
      "size": 3,
      "avg_similarity": 0.85,
      "representative": "素晴らしい",
      "cohesion": 0.12
    }
  }
}
```

**パラメータ**:
- 階層的クラスタリング: `distance_threshold=0.5`
- DBSCAN: `eps=0.3, min_samples=2`

#### 3.2.2 overexpression_detector.py

**機能**: クラスタ内のTF-IDF分散による冗長表現検出

**主要メソッド**:
- `detect_redundant_patterns()`: カテゴリ全体の冗長性分析
- `calculate_tfidf_variance()`: クラスタ内分散計算

**入力**:
- 辞書データ（全カテゴリ）
- コーパス統計（オプション）

**出力**:
```python
{
  "template_phrases": {
    "redundant_clusters": [
      {
        "cluster_id": 0,
        "phrases": ["ご質問ありがとうございます", 
                   "お問い合わせありがとうございます"],
        "variance": 0.08,
        "representative": "ご質問ありがとうございます",
        "severity": "high"
      }
    ],
    "total_clusters": 15,
    "redundancy_rate": 0.133
  }
}
```

**冗長判定基準**:
- TF-IDF分散 < 0.05: high severity
- TF-IDF分散 < 0.10: medium severity

### 3.3 Auto Annotation & Snippet Extraction

#### 3.3.1 auto_annotator.py

**機能**: 辞書ベースの弱教師付き自動アノテーション

**主要メソッド**:
- `annotate_text()`: テキスト内の辞書フレーズを検出
- `calculate_confidence()`: アノテーション信頼度算出
- `generate_training_data()`: 学習用データ生成

**入力**:
- 対話コーパス（JSONL形式）
- 辞書データ

**出力（弱教師データ）**:
```json
{
  "id": "auto_0",
  "user": "君の分析、なかなか鋭いね",
  "response": "ありがとうございます。ご指摘に共感します。",
  "annotations": [
    {
      "text": "ありがとうございます",
      "start": 0,
      "end": 11,
      "category": "template_phrases",
      "confidence": 0.95
    }
  ],
  "weak_labels": {
    "template_phrases": 0.7,
    "positive_emotion_words": 0.3
  },
  "source": "auto_annotation"
}
```

**信頼度計算ロジック**:
- 基本信頼度 = min(フレーズ長/20, 1.0)
- 文頭/文末: ×0.8
- 句読点隣接: ×1.1

#### 3.3.2 snippet_generator.py

**機能**: アノテーション候補周辺のコンテキスト抽出

**主要メソッド**:
- `extract_snippets()`: 指定長のスニペット生成

**入力**:
- 対話コーパス
- スニペット長（デフォルト200文字）

**出力（スニペットデータ）**:
```json
{
  "text": "...前文脈...ありがとうございます...後文脈...",
  "phrase": "ありがとうございます",
  "phrase_start": 50,
  "phrase_end": 61,
  "context": {
    "user": "完全なユーザー発話",
    "full_response": "完全な応答文"
  },
  "metadata": {
    "confidence": 0.95,
    "category": "template_phrases"
  }
}
```

## 4. 設定ファイルスキーマ

### 4.1 extraction_rules.yaml
```yaml
カテゴリ名:
  patterns:              # 正規表現パターン
    - regex: string
      min_frequency: int
  pos_sequences:         # 品詞列パターン
    - [品詞1, 品詞2, ...]
  ngram_range: [min, max]
  min_frequency: int
```

### 4.2 category_schemas.yaml
```yaml
categories:
  語用論的/語彙的:
    カテゴリ名:
      description: string
      max_length: int
      validation: [ルール名のリスト]

validation_rules:
  ルール名:
    description: string
    patterns: [文字列パターン]
    keywords: [キーワードリスト]
```

## 5. データ構造例

### 5.1 差分ログエントリ
```
{
  timestamp: ISO形式日時
  category: カテゴリ名
  action: "added" | "removed"
  phrases: [変更されたフレーズリスト]
  count: 変更数
}
```

### 5.2 クラスタ統計
```
{
  cluster_id: 整数（-1はノイズ）
  member_count: クラスタサイズ
  centroid_phrase: 代表フレーズ
  coherence_score: 凝集度（0-1）
  similarity_matrix: 内部類似度行列
}
```

### 5.3 アノテーション統計
```
{
  total_documents: 処理文書数
  annotated_documents: アノテーション付与文書数
  category_distribution: {カテゴリ: 出現数}
  avg_confidence: 平均信頼度
  low_confidence_ratio: 低信頼度率
}
```

## 6. 今後の拡張ポイント

### 6.1 機能拡張候補
- **多言語対応**: 英語・中国語辞書への展開
- **能動学習**: 低信頼度アノテーションの優先的人手確認
- **動的閾値調整**: コーパス特性に基づく閾値最適化

### 6.2 性能改善候補
- **ベクトルキャッシュ**: fastText埋め込みの事前計算
- **並列処理**: 大規模コーパスでのマルチプロセス化
- **インクリメンタル更新**: 差分のみの再計算

### 6.3 統合候補
- **MLOpsパイプライン**: 学習・評価の自動化
- **ダッシュボード**: リアルタイム品質監視
- **APIサービス化**: マイクロサービスアーキテクチャへの移行

---

本仕様書は、JAIML v3.3辞書拡張基盤の実装内容を文書化したものである。各モジュールは独立性を保ちつつ、統合実行スクリプトにより協調動作する設計となっている。