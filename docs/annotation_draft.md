# 基本コーパス仕様(例)
- 言語：日本語
- 会話：ユーザー発話/AI応答（前後3ターン含む計7発話を文脈窓とする）
- ジャンル：雑談、QA、感情応答、意見交換
- Weighted-κ ≥ 0.60 を運用開始基準(Substantial)とし，0.80 を優れた一致(Almost perfect)と定義し継続的改善目標とする。

# 評価指標(例)
・分類精度
  - Weighted-κ (quadratic, per-axis)
  - Macro-F1 (5-class, per-axis)  
  - MAE (ordinal regression, per-axis)
・回帰精度　Spearman 相関係数
・汎化性　　Zero-shot転移性能、再注釈一致率
※詳細な算式はAppendix AのA.5参照

## 実装(例)
・データ数：15,000対
・社会的・回避的・機械的・自己の4軸について、
    1(Absent) 2(Slight) 3(Moderate) 4(Strong) 5(Extreme)
　の5段階評価
・アノテーション実施者：言語学者N名＋専門アノテーターM名

## パイロット(論文用、例)
・データ数：1,000対
・社会的・回避的・機械的・自己の4軸について、
    1(Absent) 2(Moderate) 3(Extreme)
　の3段階評価
・アノテーション実施者：クラウドワーカー3名

## 語彙クラスタ毎の注釈難度分析

lexicon_expansionモジュールが出力する`outputs/reports/cluster_metrics.json`に基づき、
各語彙クラスタの注釈難度を分析する。

・高Silhouetteスコア（>0.7）クラスタ：明確な迎合パターンを持ち、注釈一致率が高い
・低Silhouetteスコア（<0.3）クラスタ：曖昧な表現が多く、注釈者間の判断が分かれやすい
・クラスタ別κ値の算出により、注釈困難な語彙群を特定し、追加ガイドライン策定に活用

---

## 📄 1. `annotation_guideline_SRS.md`（アノテーション仕様書）

### Aセクション（統一記述セクション）

| セクション          | 内容概要                                              |
| -------------- | ------------------------------------------------- |
| A1. 概要         | 対話ペアに対する迎合性アノテーションの仕様（4軸：社会的・回避的・機械的・自己）          |
| A2. モジュール構成    | アノテーション収集（クラウド）＋集計＋信頼度計算（Cohen’s κ）               |
| A3. 入出力仕様      | 入力：JSONL（user, response）／出力：CSVまたはJSONL（各軸0〜1スコア） |
| A4. パラメータ定義    | ラベルスキーム、閾値、κ閾値など                         |
| A5. 関連ファイル構成   | `data/annotations/*.csv`, `guideline/labels.md`   |
| A6. 使用例        | Google Spreadsheet または Webフォームでの操作例               |
| A7. CI検証項目     | アノテーション漏れ／形式検査／一致率チェック                            |
| A8. インターフェース定義 | `load_annotation(file:str) -> Dict[str, float]` 等 |
| A9. 既知の制約      | 認知バイアス、文脈依存性、評価者間差異の存在                            |

### Bセクション（詳細仕様セクション）

* 各軸の定義と境界事例
* クラウドワーカー教育用チュートリアルと誤例分析
* Cohen’s κ と再注釈ロジックの記述

---

## 📄 2. `annotation_filtering_SRS.md`（品質検査／信頼度フィルタ仕様書）

### Aセクション（統一記述セクション）

| セクション          | 内容概要                                                            |
| -------------- | --------------------------------------------------------------- |
| A1. 概要         | アノテーション結果から信頼できるデータのみを抽出するフィルタ処理仕様                              |
| A2. モジュール構成    | κベースのアノテーション集計／評価者間一致率計算／マージ処理                                  |
| A3. 入出力仕様      | 入：raw annotation CSV／出：filtered annotation JSONL                |
| A4. パラメータ定義    | κ閾値（例：0.80）、最小一致率、軸ごとのスコア平均方式など                                 |
| A5. 関連ファイル構成   | `filtered/*.jsonl`, `logs/discarded.log`                        |
| A6. 使用例        | `filter_annotations.py --input raw.csv --output filtered.jsonl` |
| A7. CI検証項目     | κ < 閾値のレコード除外確認、一貫性検査                                           |
| A8. インターフェース定義 | `filter_annotations(df:pd.DataFrame) -> List[Dict]`             |
| A9. 既知の制約      | 評価者母集団偏り、少数ラベル除外リスク、欠損処理の限界                                     |

### Bセクション（詳細仕様セクション）

* Cohen’s κ の計算手法（ラベル vs スコアベース）
* 捨てたレコードの再注釈フロー

---

## 📄 3. `feature_extraction_SRS.md`（特徴量抽出（再）仕様書）

### Aセクション（統一記述セクション）

| セクション          | 内容概要                                                                |
| -------------- | ------------------------------------------------------------------- |
| A1. 概要         | filtered annotation に対し、JAIML v3.3 構造に準拠した特徴量を抽出                    |
| A2. モジュール構成    | `corpus_based`, `lexical`, `semantic`, `syntactic` の4系統             |
| A3. 入出力仕様      | 入：annotatedペア ／ 出：feature vector + ラベル（CSV or JSON）                 |
| A4. パラメータ定義    | 使用辞書、閾値、正規化方式（0–1スケーリング）等                                           |
| A5. 関連ファイル構成   | `features/annotated_features.csv`, `feature_map.yaml`               |
| A6. 使用例        | `extract_features.py --input annotated.jsonl --output features.csv` |
| A7. CI検証項目     | 欠損値チェック、一貫性検査、型整合性                                                  |
| A8. インターフェース定義 | `extract_features(jsonl:str) -> pd.DataFrame`                       |
| A9. 既知の制約      | 文構造依存性／辞書不足／未知語問題                                                   |

### Bセクション（詳細仕様セクション）

* 各特徴量の算出式（JAIML v3.3 から再利用）
* 特徴量設計ポリシー（解釈性、対迎合性）

---

## 📄 4. `model_retraining_SRS.md`（分類器再学習仕様書）

### Aセクション（統一記述セクション）

| セクション          | 内容概要                                                     |
| -------------- | -------------------------------------------------------- |
| A1. 概要         | 抽出済み特徴量と迎合ラベル（教師信号）を用いて分類器（XGBoost等）を再学習                 |
| A2. モジュール構成    | モデル読み込み／再学習／予測／評価モジュール                                   |
| A3. 入出力仕様      | 入：features.csv + labels ／ 出：新モデル、評価指標ログ                  |
| A4. パラメータ定義    | 学習率、木の深さ、early stopping 等                                |
| A5. 関連ファイル構成   | `models/retrained_xgb.model`, `logs/train.log`           |
| A6. 使用例        | `train_model.py --input features.csv --label labels.csv` |
| A7. CI検証項目     | 精度上昇チェック（旧モデルとの比較）／再現性（seed）                             |
| A8. インターフェース定義 | `train_model(X:pd.DataFrame, y:pd.Series) -> Model`      |
| A9. 既知の制約      | ラベル分布の偏り／過学習／再学習による旧構造破壊の懸念                              |

### Bセクション（詳細仕様セクション）

* 使用アルゴリズムの概要（XGBoost 他）
* マルチラベル vs マルチクラスの選択理由
* 推薦評価指標（Macro-F1, κ）