# JAIML v3.3 語彙辞書拡張パイプライン 実行手順書

## 1. はじめに

### 1.1 本手順書の目的
本書は、JAIML v3.3の語彙辞書を拡張・管理するための実践的な操作マニュアルです。コーパスからの語彙抽出から、レビュー、統合、学習データ生成まで、一連の作業を段階的に説明します。

### 1.2 想定読者
- JAIMLプロジェクトの辞書管理担当者
- 外部協力研究者
- 語彙拡張作業の初学者

### 1.3 作業フローの概要
```
1. 語彙候補抽出 → 2. レビュー・検証 → 3. 統合・バージョン管理
                                              ↓
5. 自動アノテーション ← 4. カテゴリ別管理
```

## 2. 環境準備

### 2.1 必要なソフトウェア
```bash
# Python 3.10以上の確認
python --version

# MeCabのインストール（Ubuntu/Debian）
sudo apt-get install mecab libmecab-dev mecab-ipadic-utf8

# MeCabのインストール（macOS）
brew install mecab mecab-ipadic
```

### 2.2 Pythonパッケージのインストール
```bash
# プロジェクトディレクトリで実行
cd jaiml_v3_3/
pip install -r requirements.txt

# UniDic辞書のダウンロード
python -m unidic download
```

### 2.3 ディレクトリ構造の確認
```bash
# 主要ディレクトリが存在することを確認
ls -la lexicon_expansion/
ls -la lexicons/
```

## 3. 各フェーズの操作手順

### フェーズ1: 語彙候補の抽出

#### 目的
対話コーパスから迎合表現の候補となる語彙を自動抽出する。

#### 典型的な使用ケース
- 月次の定期的な辞書更新
- 新規ドメインのコーパス追加時

#### 実行手順

1. **抽出ルールの確認・編集**
```bash
# 抽出ルールを確認
cat lexicon_expansion/config/extraction_rules.yaml

# 必要に応じて編集（例：最小頻度の調整）
nano lexicon_expansion/config/extraction_rules.yaml
```

2. **候補抽出の実行**
```bash
# 基本的な実行
python lexicon_expansion/scripts/run_expansion.py \
  --phase extract \
  --corpus lexicon_expansion/corpus/SNOW_D18.txt \
  --output lexicon_expansion/outputs/

# 特定カテゴリのみ抽出したい場合
python lexicon_expansion/scripts/run_expansion.py \
  --phase extract \
  --corpus lexicon_expansion/corpus/dialogue_corpus.jsonl \
  --output lexicon_expansion/outputs/ \
  --categories template_phrases,humble_phrases
```

3. **出力確認**
```bash
# 抽出結果の確認
ls -la lexicon_expansion/outputs/candidates/template_phrases/raw/

# 候補数の確認
grep "total_candidates" lexicon_expansion/outputs/candidates/template_phrases/raw/candidates_*.yaml
```

#### 出力ファイル
- `candidates/[カテゴリ名]/raw/candidates_YYYYMMDD_HHMMSS.yaml`
- 各ファイルには抽出された候補と頻度情報が含まれる

### フェーズ2: 語彙候補のレビューと検証

#### 目的
自動抽出された候補を人手でレビューし、採用/却下を決定する。

#### 典型的な使用ケース
- 週次のレビュー会議
- 品質保証チェック

#### 実行手順

1. **レビュー用ファイルの準備**
```bash
# rawディレクトリからreviewedディレクトリへコピー
cp lexicon_expansion/outputs/candidates/template_phrases/raw/candidates_*.yaml \
   lexicon_expansion/outputs/candidates/template_phrases/reviewed/

# レビュー用エディタで開く
nano lexicon_expansion/outputs/candidates/template_phrases/reviewed/candidates_*.yaml
```

2. **レビューの実施**
```yaml
# YAMLファイル内で accept フィールドを編集
candidates:
  - phrase: "ご質問ありがとうございます"
    frequency: 234
    accept: true  # ← null から true/false に変更
    note: "典型的な定型句"  # ← 任意でコメント追加
```

3. **スキーマ検証の実行**
```bash
# レビュー済みファイルの検証
python lexicon_expansion/scripts/run_expansion.py \
  --phase validate \
  --output lexicon_expansion/outputs/

# カテゴリ別検証レポートの確認
cat lexicon_expansion/outputs/reports/validation_report.txt
```

#### 検証項目
- YAML構文の正しさ
- 必須フィールドの存在
- 値の型と範囲
- 重複チェック

### フェーズ3: 語彙の統合とバージョン管理

#### 目的
レビュー済み候補を既存辞書に統合し、変更履歴を記録する。

#### 典型的な使用ケース
- 月次辞書更新のリリース
- 緊急修正の適用

#### 実行手順

1. **現在の辞書のバックアップ**
```bash
# 手動バックアップ（推奨）
cp lexicons/jaiml_lexicons.yaml lexicons/jaiml_lexicons_backup_$(date +%Y%m%d).yaml
```

2. **辞書の統合**
```bash
# レビュー済み候補を統合
python lexicon_expansion/scripts/run_expansion.py \
  --phase merge \
  --output lexicon_expansion/outputs/

# 統合結果の確認
ls -la lexicons/jaiml_lexicons_*.yaml
```

3. **差分レポートの生成**
```bash
# バージョン管理機能の実行
python lexicon_expansion/scripts/run_advanced_features.py \
  --feature version \
  --lexicon lexicons/jaiml_lexicons.yaml \
  --output lexicon_expansion/outputs/

# 差分レポートの確認
cat lexicon_expansion/outputs/reports/expansion_report_*.md
```

4. **トレンド分析の実行**
```bash
# カバレッジ推移グラフの生成
python lexicon_expansion/scripts/run_advanced_features.py \
  --feature version \
  --action plot \
  --output lexicon_expansion/outputs/reports/

# 生成されたグラフを確認
open lexicon_expansion/outputs/reports/trend_plot.png
```

#### 出力ファイル
- `lexicons/jaiml_lexicons_YYYYMMDD_HHMMSS.yaml`: 新バージョン
- `lexicons/versions/changelog.json`: 変更履歴
- `outputs/reports/expansion_report_*.md`: 差分レポート

### フェーズ4: 語彙のカテゴリ別管理と分割

#### 目的
統合辞書をカテゴリ別に分割し、語用論的・語彙的分類で整理する。

#### 典型的な使用ケース
- カテゴリ単位での専門家レビュー
- 特定カテゴリのみの更新

#### 実行手順

1. **カテゴリスキーマの確認**
```bash
# スキーマ定義を確認
cat lexicon_expansion/config/category_schemas.yaml
```

2. **辞書の分割**
```bash
# マスター辞書をカテゴリ別に分割
python lexicon_expansion/scripts/run_expansion.py \
  --phase split \
  --lexicon lexicons/jaiml_lexicons.yaml \
  --output lexicons/categories/

# 分割結果の確認
tree lexicons/categories/
```

3. **カテゴリ別編集**
```bash
# 特定カテゴリのみ編集
nano lexicons/categories/pragmatic/template_phrases.yaml
```

4. **再統合**
```bash
# カテゴリ別ファイルを統合
python lexicon_expansion/scripts/category_manager.py \
  --action merge \
  --input lexicons/categories/ \
  --output lexicons/jaiml_lexicons_merged.yaml
```

#### 分割構造
```
lexicons/categories/
├── pragmatic/          # 語用論的カテゴリ
│   ├── template_phrases.yaml
│   └── humble_phrases.yaml
└── lexical/            # 語彙的カテゴリ
    ├── achievement_nouns.yaml
    └── positive_emotion_words.yaml
```

### フェーズ5: 自動アノテーションとスニペット抽出

#### 目的
辞書を用いて対話コーパスに弱教師付きラベルを付与し、学習データを生成する。

#### 典型的な使用ケース
- 新規学習データの準備
- アノテーション品質の事前確認

#### 実行手順

1. **対話コーパスの準備**
```bash
# コーパスフォーマットの確認（JSONL形式）
head -n 3 lexicon_expansion/corpus/dialogue_corpus.jsonl
```

2. **自動アノテーションの実行**
```bash
# 弱教師データの生成
python lexicon_expansion/scripts/run_advanced_features.py \
  --feature annotate \
  --lexicon lexicons/jaiml_lexicons.yaml \
  --corpus lexicon_expansion/corpus/dialogue_corpus.jsonl \
  --output lexicon_expansion/outputs/

# 生成件数の確認
wc -l lexicon_expansion/outputs/weak_supervised_data.jsonl
```

3. **スニペット抽出**
```bash
# カテゴリ別スニペットの生成
python lexicon_expansion/scripts/run_advanced_features.py \
  --feature annotate \
  --action snippets \
  --corpus lexicon_expansion/corpus/dialogue_corpus.jsonl \
  --output lexicon_expansion/outputs/snippets/

# スニペット数の確認
ls -la lexicon_expansion/outputs/snippets/
```

#### 出力ファイル
- `outputs/weak_supervised_data.jsonl`: 弱教師付き学習データ
- `outputs/snippets/[カテゴリ]_snippets.jsonl`: コンテキスト付きスニペット

## 4. 実行結果の確認方法

### 4.1 YAML形式の確認
```bash
# YAMLの整形表示
python -m yaml lexicon_expansion/outputs/candidates/template_phrases/raw/candidates_*.yaml | less

# 特定フィールドの抽出
grep -A 2 "phrase:" candidates_*.yaml | grep -E "(phrase:|frequency:)"
```

### 4.2 統計情報の読み方

**差分レポート（expansion_report_*.md）の見方**：
```markdown
## カテゴリ別統計
| カテゴリ | 既存 | 追加 | 削除 | 最終 |
|---------|------|------|------|------|
| template_phrases | 156 | 45 | 3 | 198 |

解釈：
- 追加 > 削除：辞書が成長している
- 削除 > 0：品質改善が行われている
```

**変更ログ（changelog.json）の見方**：
```json
"change_rate": 0.288  // 28.8%の変化率 → 要確認
"change_rate": 0.064  // 6.4%の変化率 → 通常範囲
```

### 4.3 可視化グラフの解釈
- **右肩上がり**: 順調な辞書成長
- **急激な変化**: 大規模更新または異常（要確認）
- **停滞**: 新規候補の枯渇（コーパス追加を検討）

## 5. よくあるエラーと対処

### 5.1 MeCab関連エラー
```
エラー: MeCab.Tagger() failed
対処: 
1. MeCabが正しくインストールされているか確認
   which mecab
2. 辞書パスを明示的に指定
   export MECAB_PATH=/usr/local/lib/mecab/dic/mecab-ipadic-neologd
```

### 5.2 ファイルパスエラー
```
エラー: FileNotFoundError: [Errno 2] No such file or directory
対処:
1. 作業ディレクトリを確認
   pwd
2. 相対パスを絶対パスに変更
   --corpus /absolute/path/to/corpus.txt
```

### 5.3 YAML検証エラー
```
エラー: Duplicate phrases found
対処:
1. 重複フレーズを検索
   sort candidates.yaml | uniq -d
2. 重複を手動で削除
```

### 5.4 メモリ不足
```
エラー: MemoryError
対処:
1. バッチサイズを調整
   --batch-size 1000
2. カテゴリ単位で処理
   --categories template_phrases
```

## 6. 付録：ディレクトリ構成の説明

```
現在整理中
```

### 主要ファイルの役割
- `run_expansion.py`: 基本的な辞書操作（抽出・検証・統合・分割）
- `run_advanced_features.py`: 高度な分析（バージョン管理・クラスタリング・アノテーション）
- `jaiml_lexicons.yaml`: 全カテゴリを含む統合辞書
- `changelog.json`: すべての変更履歴を記録

---

本手順書は定期的に更新されます。最新版は `docs/lexicon_expansion_USAGE.md` を参照してください。