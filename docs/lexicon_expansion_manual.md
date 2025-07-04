# JAIML v3.3 語彙辞書拡張手順書

## 1. システム概要

### 1.1 目的
JAIML v3.3における語彙辞書の系統的拡張により、迎合分類の精度向上を実現する。

### 1.2 対象カテゴリ
- `template_phrases`: 定型句・慣用表現
- `humble_phrases`: 謙遜表現
- `achievement_nouns`: 実績名詞
- `positive_emotion_words`: 肯定的感情語
- `evaluative_adjectives`: 評価形容詞

### 1.3 処理フロー
```
コーパス → 自動抽出 → 候補生成 → 人手選別 → 検証 → 辞書統合
```

## 2. ディレクトリ構造

```
jaiml_v3_3/
├── lexicon_expansion/
│   ├── config/
│   │   ├── extraction_rules.yaml    # 抽出ルール定義
│   │   └── category_schemas.yaml    # カテゴリ別スキーマ
│   ├── scripts/
│   │   ├── extract_candidates.py    # 候補抽出スクリプト
│   │   ├── merge_lexicons.py        # 辞書統合スクリプト
│   │   ├── validate_yaml.py         # YAML検証スクリプト
│   │   └── generate_report.py       # 統計レポート生成
│   ├── candidates/                   # 候補語彙（カテゴリ別）
│   │   ├── template_phrases/
│   │   │   ├── raw/                 # 自動抽出結果
│   │   │   └── reviewed/            # 選別済み
│   │   └── [他カテゴリ同様]
│   └── corpus/                      # コーパスデータ（.gitignore対象）
└── lexicons/
    └── jaiml_lexicons.yaml          # 統合済み本辞書
```

## 3. 実装手順

### 3.1 環境構築

```bash
# 依存パッケージインストール
pip install mecab-python3==1.0.4
pip install unidic-lite==1.0.8
pip install pyyaml==6.0
pip install pydantic==2.5.0
pip install pandas==2.1.0
```

### 3.2 抽出ルール定義

**config/extraction_rules.yaml**
```yaml
template_phrases:
  patterns:
    - regex: "ご.*ありがとうございます"
      min_frequency: 10
    - regex: "お.*いたします"
      min_frequency: 15
    - regex: ".*させていただ.*"
      min_frequency: 20
  ngram_range: [3, 7]
  pos_filter: ["名詞", "動詞", "助動詞"]

humble_phrases:
  patterns:
    - regex: "(まだまだ|不完全|未熟)"
      min_frequency: 5
    - regex: ".*ながら"
      min_frequency: 10
  ngram_range: [2, 5]
  
achievement_nouns:
  patterns:
    - pos_sequence: ["名詞-サ変接続", "動詞-自立"]
    - keywords: ["受賞", "達成", "成功", "獲得"]
  ngram_range: [1, 3]
```

### 3.3 候補抽出スクリプト

**scripts/extract_candidates.py**
```python
import yaml
import MeCab
import re
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple

class CandidateExtractor:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        self.tagger = MeCab.Tagger()
        
    def extract_ngrams(self, text: str, n_range: Tuple[int, int]) -> List[str]:
        """指定範囲のN-gramを抽出"""
        tokens = self._tokenize(text)
        ngrams = []
        for n in range(n_range[0], n_range[1] + 1):
            for i in range(len(tokens) - n + 1):
                ngrams.append(''.join(tokens[i:i+n]))
        return ngrams
    
    def _tokenize(self, text: str) -> List[str]:
        """MeCabによる形態素解析"""
        node = self.tagger.parseToNode(text)
        tokens = []
        while node:
            if node.surface:
                tokens.append(node.surface)
            node = node.next
        return tokens
    
    def apply_patterns(self, text: str, patterns: List[Dict]) -> List[str]:
        """正規表現パターンによる抽出"""
        candidates = []
        for pattern in patterns:
            if 'regex' in pattern:
                matches = re.findall(pattern['regex'], text)
                candidates.extend(matches)
        return candidates
    
    def extract_category(self, corpus_path: str, category: str) -> Dict[str, int]:
        """カテゴリ別候補抽出"""
        rules = self.rules[category]
        candidates = Counter()
        
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line in f:
                # N-gram抽出
                if 'ngram_range' in rules:
                    ngrams = self.extract_ngrams(line, rules['ngram_range'])
                    candidates.update(ngrams)
                
                # パターンマッチング
                if 'patterns' in rules:
                    matches = self.apply_patterns(line, rules['patterns'])
                    candidates.update(matches)
        
        # 頻度フィルタ適用
        min_freq = rules.get('min_frequency', 5)
        return {k: v for k, v in candidates.items() if v >= min_freq}
```

### 3.4 候補ファイル形式

**candidates/template_phrases/raw/candidates_20240115.yaml**
```yaml
metadata:
  category: template_phrases
  extracted_date: "2024-01-15"
  corpus: "SNOW_D18"
  total_candidates: 156

candidates:
  - phrase: "ご質問ありがとうございます"
    frequency: 234
    accept: null  # 未レビュー
    
  - phrase: "お役に立てて光栄です"
    frequency: 45
    accept: null
    
  - phrase: "ご指摘の通りです"
    frequency: 89
    accept: null
```

### 3.5 人手選別プロセス

**candidates/template_phrases/reviewed/candidates_20240115.yaml**
```yaml
metadata:
  category: template_phrases
  reviewed_date: "2024-01-16"
  reviewer: "annotator_01"

candidates:
  - phrase: "ご質問ありがとうございます"
    frequency: 234
    accept: true
    note: "典型的な定型句"
    
  - phrase: "お役に立てて光栄です"
    frequency: 45
    accept: true
    note: "過度な丁寧表現"
    
  - phrase: "ご指摘の通りです"
    frequency: 89
    accept: false
    note: "通常の敬語範囲"
```

### 3.6 辞書統合スクリプト

**scripts/merge_lexicons.py**
```python
import yaml
from pathlib import Path
from typing import Dict, List

class LexiconMerger:
    def __init__(self, base_lexicon_path: str):
        with open(base_lexicon_path, 'r', encoding='utf-8') as f:
            self.base_lexicon = yaml.safe_load(f)
            
    def merge_reviewed_candidates(self, reviewed_dir: Path) -> Dict[str, List[str]]:
        """選別済み候補を統合"""
        merged = {}
        
        for category_dir in reviewed_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            category = category_dir.name
            merged[category] = list(self.base_lexicon.get(category, []))
            
            # 各レビュー済みファイルを処理
            for yaml_file in category_dir.glob("*.yaml"):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                for candidate in data['candidates']:
                    if candidate.get('accept', False):
                        phrase = candidate['phrase']
                        if phrase not in merged[category]:
                            merged[category].append(phrase)
        
        return merged
    
    def save_merged_lexicon(self, output_path: str, merged_data: Dict):
        """統合辞書を保存"""
        # 既存辞書に統合
        for category, phrases in merged_data.items():
            self.base_lexicon[category] = sorted(list(set(phrases)))
            
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.base_lexicon, f, allow_unicode=True, 
                     default_flow_style=False, sort_keys=True)
```

### 3.7 検証スクリプト

**scripts/validate_yaml.py**
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import yaml

class CandidateItem(BaseModel):
    phrase: str
    frequency: int = Field(ge=1)
    accept: Optional[bool] = None
    note: Optional[str] = None
    
    @validator('phrase')
    def phrase_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('phrase cannot be empty')
        return v.strip()

class CandidateFile(BaseModel):
    metadata: dict
    candidates: List[CandidateItem]
    
    @validator('candidates')
    def check_duplicates(cls, v):
        phrases = [item.phrase for item in v]
        if len(phrases) != len(set(phrases)):
            raise ValueError('Duplicate phrases found')
        return v

def validate_candidate_file(file_path: str) -> bool:
    """候補ファイルの検証"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    try:
        CandidateFile(**data)
        return True
    except Exception as e:
        print(f"Validation error in {file_path}: {e}")
        return False
```

## 4. 運用フロー

### 4.1 定期実行スケジュール

```bash
# 月次実行スクリプト
#!/bin/bash
DATE=$(date +%Y%m%d)

# 1. 候補抽出
python scripts/extract_candidates.py \
  --config config/extraction_rules.yaml \
  --corpus corpus/SNOW_D18.txt \
  --output candidates/raw_$DATE/

# 2. レビュー待機（人手作業）
echo "Review candidates in candidates/raw_$DATE/"

# 3. 検証と統合（レビュー完了後）
python scripts/validate_yaml.py candidates/reviewed_$DATE/
python scripts/merge_lexicons.py \
  --base lexicons/jaiml_lexicons.yaml \
  --reviewed candidates/reviewed_$DATE/ \
  --output lexicons/jaiml_lexicons_$DATE.yaml

# 4. 統計レポート生成
python scripts/generate_report.py \
  --old lexicons/jaiml_lexicons.yaml \
  --new lexicons/jaiml_lexicons_$DATE.yaml \
  --output reports/expansion_report_$DATE.md
```

### 4.2 CI統合（GitHub Actions例）

**.github/workflows/lexicon_validation.yml**
```yaml
name: Lexicon Validation

on:
  pull_request:
    paths:
      - 'lexicons/*.yaml'
      - 'lexicon_expansion/candidates/**/*.yaml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          pip install pyyaml pydantic
          
      - name: Validate YAML files
        run: |
          python scripts/validate_yaml.py lexicons/
          python scripts/validate_yaml.py lexicon_expansion/candidates/
```

## 5. 品質管理指標

### 5.1 カバレッジ指標
- カテゴリ別語彙数
- コーパスカバー率
- 重複率

### 5.2 品質指標
- レビュー承認率
- カテゴリ間重複
- 文字数分布

### 5.3 レポート形式

**reports/expansion_report_20240115.md**
```markdown
# 辞書拡張レポート 2024-01-15

## 概要
- 追加語彙数: 342
- 削除語彙数: 15
- 総語彙数: 2,156 → 2,483

## カテゴリ別統計
| カテゴリ | 既存 | 追加 | 削除 | 最終 |
|---------|------|------|------|------|
| template_phrases | 156 | 45 | 3 | 198 |
| humble_phrases | 89 | 23 | 0 | 112 |

## 品質指標
- 平均文字数: 12.3
- 最大文字数: 28
- カテゴリ間重複: 2.1%
```

本手順書により、系統的かつ再現可能な語彙辞書拡張が実現される。各プロセスは独立性を保ち、将来的な自動化にも対応可能な設計となっている。