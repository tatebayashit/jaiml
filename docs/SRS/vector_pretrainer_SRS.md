## 📊 vector_pretrainer v1.1 システム要求仕様書 - 改訂版

### A. 統一記述セクション

#### A.1 概要

**モジュール名**: vector_pretrainer v1.1

**目的**: 外部対話コーパス（SNOW D18・BCCWJ等）を用いてTF-IDFベクトライザーを事前学習し、JAIML v3.3および lexicon_expansion v2.0の`tfidf_novelty`特徴量計算に供給する。再現性・安全性・拡張性を確保するため、全プロジェクト共通の設定体系に準拠する。

#### A.2 モジュール構成と責務

```
src/vector_pretrainer/
├── corpus/
│   ├── raw/                 # 外部配布コーパス（txt, xml等）
│   └── jsonl/               # 正規化済みJSONL形式
├── config/
│   └── tfidf_config.yaml    # TF-IDF専用設定
├── outputs/
│   ├── models/              # 一時出力ディレクトリ
│   │   ├── tfidf_vectorizer.joblib  # → model/vectorizers/へ手動コピー
│   │   └── metadata.json             # → model/vectorizers/へ手動コピー
│   └── logs/
├── scripts/
│   ├── to_jsonl.py          # コーパス形式変換
│   └── train_tfidf.py       # TF-IDF学習
└── README.md
```

**責務**:
- 大規模コーパスの前処理とJSONL形式への統一
- TF-IDFベクトライザーの学習と永続化
- メタデータによるバージョン管理と整合性保証

#### A.3 入出力仕様

**入力形式（JSONL）**:
```json
{
  "user": "発話者ID（匿名化済み）",
  "response": "発話テキスト（正規化済み）",
  "metadata": {
    "source": "コーパス名",
    "topic": "話題カテゴリ（オプション）",
    "timestamp": "発話時刻（オプション）"
  }
}
```

**出力形式**:
1. `tfidf_vectorizer.joblib`: scikit-learn TfidfVectorizerオブジェクト
2. `metadata.json`:
```json
{
  "model_version": "1.1",
  "sklearn_version": "1.7.0",
  "creation_date": "2025-07-05T12:00:00Z",
  "corpus_stats": {
    "total_documents": 100000,
    "vocabulary_size": 50000
  },
  "config_hash": "sha256:...",
  "vectorizer_hash": "sha256:..."
}
```

#### A.4 パラメータ定義

**共通パラメータ（config/global.yamlから継承）**:
- `tokenizer`: "fugashi"
- `min_df`: 1
- `max_df`: 0.95
- `ngram_range`: [1, 1]

**TF-IDF専用パラメータ（config/tfidf_config.yaml）**:
- `token_normalization`: "NFKC"
- `sublinear_tf`: true
- `use_idf`: true
- `smooth_idf`: true
- `norm`: "l2"

#### A.5 関連ファイル構成

```
config/
├── global.yaml              # プロジェクト共通設定
└── tfidf_config.yaml        # 本モジュール専用設定

model/vectorizers/           # 学習済みモデルの最終配置先
├── tfidf_vectorizer.joblib
└── metadata.json

corpus/                      # 入力コーパス
├── raw/
│   └── SNOW_D18.txt
└── jsonl/
    └── combined.jsonl
```

#### A.6 使用例とコマンドライン

**コーパス形式変換**:
```bash
python scripts/to_jsonl.py \
  --input corpus/raw/SNOW_D18.txt \
  --output corpus/jsonl/snow_d18.jsonl \
  --format plaintext \
  --anonymize true
```

**TF-IDF学習**:
```bash
python scripts/train_tfidf.py \
  --corpus corpus/jsonl/combined.jsonl \
  --config config/tfidf_config.yaml \
  --output model/vectorizers/  # 最終配置先に直接出力
```

#### A.7 CI検証項目

1. **設定ファイル整合性**: `tfidf_config.yaml`と`global.yaml`のパラメータ一致
2. **tokenizerの統一**: 必ず"fugashi"が使用されていること
3. **出力ファイル検証**: `.joblib`と`metadata.json`の両方が生成されること
4. **バージョン情報**: `sklearn_version`が実行環境と一致すること
5. **再現性テスト**: 同一入力から同一ベクトルが生成されること
6. **テストカバレッジ**: 80%以上（CI共通閾値）

#### A.8 インターフェース定義（型注釈付き）

```python
from typing import Dict, List, Optional
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

class TFIDFTrainer:
    def __init__(self, config_path: str):
        """
        Args:
            config_path: tfidf_config.yamlのパス
        """
        self.config = self._load_config(config_path)
        self.vectorizer = None
    
    def train(self, corpus_path: str) -> None:
        """
        コーパスからTF-IDFベクトライザーを学習
        
        Args:
            corpus_path: JSONL形式のコーパスファイルパス
        """
    
    def save(self, output_dir: str) -> Dict[str, str]:
        """
        学習済みモデルを保存
        
        Returns:
            Dict[str, str]: 保存されたファイルのパス
                - "model": joblib形式のモデルファイル
                - "metadata": JSON形式のメタデータファイル
        """

class CorpusConverter:
    def convert_to_jsonl(self, input_path: str, output_path: str, 
                        format: str = "plaintext") -> int:
        """
        各種形式のコーパスをJSONL形式に変換
        
        Args:
            input_path: 入力ファイルパス
            output_path: 出力JSONLファイルパス
            format: 入力形式（"plaintext", "xml", "csv"）
            
        Returns:
            int: 変換された文書数
        """
```

#### A.9 既知の制約と注意事項

1. **メモリ制約**: 大規模コーパス（>1GB）の処理時は最大4GBのメモリが必要
2. **処理性能**: 最低1MB/分（50MB/時間）の処理速度を保証
3. **ファイルサイズ**: 出力される`.joblib`ファイルは最大200MB
4. **セキュリティ**: Pickle形式は完全禁止、joblib形式を必須とする
5. **匿名化要件**: 固有名詞は`<PERSON>`, `<LOCATION>`等に置換必須

### B. 詳細仕様セクション

#### B.1 コーパス前処理仕様

##### B.1.1 テキスト正規化

```python
def normalize_text(text: str) -> str:
    """テキストの正規化処理"""
    # 1. Unicode正規化（NFKC）
    text = unicodedata.normalize('NFKC', text)
    
    # 2. 全角英数字→半角変換
    text = mojimoji.zen_to_han(text, kana=False)
    
    # 3. HTMLエンティティのデコード
    text = html.unescape(text)
    
    # 4. 制御文字の除去
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # 5. 連続空白の正規化
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
```

##### B.1.2 匿名化処理

本モジュールの匿名化処理は、プライバシー保護の確実性を高めるため、自動処理と人手補完の2段階構成とする。

**自動処理フェーズ（NERベース）**:
- spaCy + GiNZA（標準モデル: `ja_ginza_electra`）による固有表現認識を実施
- 検出されたエンティティを以下のプレースホルダでマスキング：
  - `PERSON` → `<PERSON>`
  - `ORG` → `<ORG>`
  - `LOC` → `<LOCATION>`
  - `DATE` → `<DATE>`
  - `TIME` → `<TIME>`
  - `MONEY` → `<MONEY>`
  - `PERCENT` → `<PERCENT>`
- 正規表現による追加マスキング：
  - メールアドレス: `[\w\.-]+@[\w\.-]+\.\w+` → `<EMAIL>`
  - 電話番号: `\d{2,4}-\d{2,4}-\d{4}` → `<PHONE>`
  - 各種ID番号: `[A-Z]{2,3}\d{6,10}` → `<ID>`

**人手補完フェーズ**:
- 自動処理結果をCSV形式で出力し、SpreadsheetまたはWebベースの専用UIで人間がレビュー
- マスキング漏れや過剰マスキングを修正
- 修正履歴は `.annotated_difflog.jsonl` に記録：
  ```json
  {
    "document_id": "doc_001",
    "position": {"start": 45, "end": 50},
    "original": "山田太郎",
    "masked": "<PERSON>",
    "annotator": "reviewer_01",
    "timestamp": "2025-07-05T14:30:00Z"
  }
  ```

**設定管理**:
- GiNZAモデル名とバージョンは `config/global.yaml` の `common.ginza_model` で指定
- 全モジュールで同一設定を参照し、一貫性を保証

**実装例**:
```python
import spacy
from typing import List, Tuple

class GiNZAAnonymizer:
    def __init__(self, model_name: str = "ja_ginza_electra"):
        self.nlp = spacy.load(model_name)
        self.entity_mapping = {
            "PERSON": "<PERSON>",
            "ORG": "<ORG>",
            "LOC": "<LOCATION>",
            "DATE": "<DATE>",
            "TIME": "<TIME>",
            "MONEY": "<MONEY>",
            "PERCENT": "<PERCENT>"
        }
    
    def anonymize(self, text: str) -> Tuple[str, List[dict]]:
        """
        テキストの匿名化と変更ログの生成
        
        Returns:
            Tuple[str, List[dict]]: (匿名化済みテキスト, 変更ログ)
        """
        doc = self.nlp(text)
        anonymized_text = text
        changes = []
        
        # エンティティを逆順で処理（位置ずれ防止）
        for ent in reversed(doc.ents):
            if ent.label_ in self.entity_mapping:
                placeholder = self.entity_mapping[ent.label_]
                anonymized_text = (
                    anonymized_text[:ent.start_char] + 
                    placeholder + 
                    anonymized_text[ent.end_char:]
                )
                changes.append({
                    "position": {"start": ent.start_char, "end": ent.end_char},
                    "original": ent.text,
                    "masked": placeholder,
                    "entity_type": ent.label_
                })
        
        # 正規表現による追加マスキング
        anonymized_text = self._apply_regex_rules(anonymized_text, changes)
        
        return anonymized_text, changes
```

#### B.2 TF-IDF学習仕様

##### B.2.1 Tokenizerの実装

```python
from fugashi import Tagger

class FugashiTokenizer:
    def __init__(self):
        self.tagger = Tagger()
    
    def __call__(self, text: str) -> List[str]:
        """fugashiによる形態素解析"""
        tokens = []
        for word in self.tagger(text):
            if word.surface:
                tokens.append(word.surface)
        return tokens
```

##### B.2.2 TF-IDFベクトライザーの設定

```python
def create_vectorizer(config: Dict) -> TfidfVectorizer:
    """設定に基づくTF-IDFベクトライザーの生成"""
    return TfidfVectorizer(
        tokenizer=FugashiTokenizer(),
        min_df=config['min_df'],
        max_df=config['max_df'],
        ngram_range=tuple(config['ngram_range']),
        sublinear_tf=config.get('sublinear_tf', True),
        use_idf=config.get('use_idf', True),
        smooth_idf=config.get('smooth_idf', True),
        norm=config.get('norm', 'l2')
    )
```

##### B.2.3 モデル保存形式

```python
def save_model(vectorizer: TfidfVectorizer, output_dir: str) -> Dict[str, str]:
    """モデルとメタデータの保存"""
    # 1. モデル本体の保存（joblib形式）
    model_path = os.path.join(output_dir, 'tfidf_vectorizer.joblib')
    joblib.dump(vectorizer, model_path, compress=3)
    
    # 2. メタデータの生成と保存
    metadata = {
        'model_version': '1.1',
        'sklearn_version': sklearn.__version__,
        'creation_date': datetime.utcnow().isoformat() + 'Z',
        'corpus_stats': {
            'total_documents': vectorizer.n_features_in_,
            'vocabulary_size': len(vectorizer.vocabulary_)
        },
        'config_hash': hashlib.sha256(
            json.dumps(config, sort_keys=True).encode()
        ).hexdigest(),
        'vectorizer_hash': hashlib.sha256(
            open(model_path, 'rb').read()
        ).hexdigest()
    }
    
    metadata_path = os.path.join(output_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return {
        'model': model_path,
        'metadata': metadata_path
    }
```

#### B.3 セキュリティと再現性

##### B.3.1 Pickle使用の禁止

```python
def load_model_safe(model_path: str) -> TfidfVectorizer:
    """安全なモデル読み込み（Pickle警告付き）"""
    if model_path.endswith('.pkl') or model_path.endswith('.pickle'):
        raise ValueError(
            "Pickle format is prohibited due to security risks. "
            "Use joblib format instead."
        )
    
    # joblibでの読み込み
    try:
        model = joblib.load(model_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}")
    
    # バージョン検証
    metadata_path = model_path.replace('.joblib', '_metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        if metadata['sklearn_version'] != sklearn.__version__:
            warnings.warn(
                f"Model was trained with sklearn {metadata['sklearn_version']}, "
                f"but current version is {sklearn.__version__}. "
                "This may cause compatibility issues.",
                RuntimeWarning
            )
    
    return model
```

##### B.3.2 再現性の保証

```python
def ensure_reproducibility():
    """再現性を保証するための環境設定"""
    # 1. 乱数シード固定
    random.seed(42)
    np.random.seed(42)
    
    # 2. ハッシュシード固定
    os.environ['PYTHONHASHSEED'] = '0'
    
    # 3. 並列処理の無効化（決定論的処理のため）
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
```