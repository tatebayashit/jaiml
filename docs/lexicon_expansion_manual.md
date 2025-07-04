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

---

## レビュー評価

提案された改善点は技術的に妥当である。特に以下の観点から有効性が認められる：

1. **POS Sequence対応**: 品詞列パターンによる構文的制約は、日本語の膠着語的特性を活用した精度向上に寄与
2. **カテゴリ別管理**: 辞書の肥大化防止と並列開発の効率化を実現
3. **語用論的分類**: 言語学的妥当性に基づく体系的な辞書構造の実現

## 実装案

### 1. POS Sequence機能の実装

**scripts/extract_candidates.py（拡張版）**
```python
class CandidateExtractor:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        self.tagger = MeCab.Tagger()
        
    def extract_pos_sequences(self, text: str, patterns: List[List[str]]) -> List[Tuple[str, str]]:
        """品詞列パターンに基づく抽出
        
        Returns:
            List[Tuple[str, str]]: (表層形, 品詞列) のタプルリスト
        """
        node = self.tagger.parseToNode(text)
        tokens, pos_tags = [], []
        
        while node:
            if node.surface:
                tokens.append(node.surface)
                features = node.feature.split(',')
                # 品詞-品詞細分類の形式で保存
                pos = features[0]
                if features[1] != '*':
                    pos += f'-{features[1]}'
                pos_tags.append(pos)
            node = node.next
        
        matches = []
        for pattern in patterns:
            pattern_len = len(pattern)
            for i in range(len(pos_tags) - pattern_len + 1):
                if self._match_pos_pattern(pos_tags[i:i+pattern_len], pattern):
                    surface = ''.join(tokens[i:i+pattern_len])
                    pos_seq = '|'.join(pos_tags[i:i+pattern_len])
                    matches.append((surface, pos_seq))
        
        return matches
    
    def _match_pos_pattern(self, pos_sequence: List[str], pattern: List[str]) -> bool:
        """品詞パターンのマッチング（ワイルドカード対応）"""
        if len(pos_sequence) != len(pattern):
            return False
            
        for pos, pat in zip(pos_sequence, pattern):
            if pat == '*':  # ワイルドカード
                continue
            if not pos.startswith(pat):
                return False
        return True
    
    def extract_category(self, corpus_path: str, category: str) -> Dict[str, Dict]:
        """拡張版カテゴリ別候補抽出"""
        rules = self.rules[category]
        candidates = {}
        
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 既存処理...
                
                # POS sequence抽出
                if 'pos_sequences' in rules:
                    pos_matches = self.extract_pos_sequences(
                        line, rules['pos_sequences']
                    )
                    for surface, pos_seq in pos_matches:
                        if surface not in candidates:
                            candidates[surface] = {
                                'frequency': 0,
                                'pos_patterns': set()
                            }
                        candidates[surface]['frequency'] += 1
                        candidates[surface]['pos_patterns'].add(pos_seq)
        
        # 頻度フィルタとデータ整形
        min_freq = rules.get('min_frequency', 5)
        filtered = {}
        for phrase, data in candidates.items():
            if data['frequency'] >= min_freq:
                filtered[phrase] = {
                    'frequency': data['frequency'],
                    'pos_patterns': list(data['pos_patterns'])
                }
        
        return filtered
```

**config/extraction_rules.yaml（拡張版）**
```yaml
achievement_nouns:
  pos_sequences:
    - ["名詞-サ変接続", "動詞-自立"]     # 達成する
    - ["名詞-一般", "名詞-サ変接続"]     # 成果達成
    - ["名詞-一般", "助詞-格助詞", "名詞-サ変接続"]  # 目標の達成
  patterns:
    - keywords: ["受賞", "達成", "成功", "獲得", "実績", "成果"]
  ngram_range: [1, 4]
  min_frequency: 5

evaluative_adjectives:
  pos_sequences:
    - ["副詞-一般", "形容詞-自立"]       # とても素晴らしい
    - ["形容詞-自立", "名詞-非自立"]     # 優れた点
    - ["連体詞", "形容詞-自立"]          # この素晴らしい
  ngram_range: [1, 3]
  min_frequency: 10
```

### 2. カテゴリ別辞書管理システム

**config/category_schemas.yaml**
```yaml
# カテゴリメタデータと構造定義
categories:
  # 語用論的カテゴリ
  pragmatic:
    template_phrases:
      description: "慣用的定型表現"
      max_length: 30
      validation:
        - must_contain_honorific  # 敬語要素必須
        
    humble_phrases:
      description: "謙遜・自己卑下表現"
      max_length: 20
      validation:
        - semantic_negativity_check  # ネガティブ極性確認
  
  # 語彙的カテゴリ  
  lexical:
    achievement_nouns:
      description: "達成・成果関連名詞"
      max_length: 15
      validation:
        - pos_noun_check  # 名詞性確認
        
    positive_emotion_words:
      description: "肯定的感情表現"
      max_length: 10
      validation:
        - sentiment_positive_check
        
    evaluative_adjectives:
      description: "評価的形容詞"
      max_length: 10
      validation:
        - pos_adjective_check

# 検証ルール定義
validation_rules:
  must_contain_honorific:
    description: "敬語要素を含むことを確認"
    patterns: ["お", "ご", "いたし", "いただ", "ござい"]
    
  semantic_negativity_check:
    description: "自己否定的意味を確認"
    keywords: ["ない", "不", "未", "無"]
```

**scripts/category_manager.py**
```python
from pathlib import Path
import yaml
from typing import Dict, List, Optional

class CategoryManager:
    """カテゴリ別辞書の管理"""
    
    def __init__(self, schema_path: str, lexicon_dir: str):
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = yaml.safe_load(f)
        self.lexicon_dir = Path(lexicon_dir)
        self.lexicon_dir.mkdir(exist_ok=True)
        
    def split_master_lexicon(self, master_path: str):
        """マスター辞書をカテゴリ別に分割"""
        with open(master_path, 'r', encoding='utf-8') as f:
            master_data = yaml.safe_load(f)
            
        for category_type in ['pragmatic', 'lexical']:
            type_dir = self.lexicon_dir / category_type
            type_dir.mkdir(exist_ok=True)
            
            for category in self.schema['categories'][category_type]:
                if category in master_data:
                    category_data = {
                        'metadata': {
                            'category': category,
                            'type': category_type,
                            'schema': self.schema['categories'][category_type][category]
                        },
                        'phrases': master_data[category]
                    }
                    
                    output_path = type_dir / f"{category}.yaml"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        yaml.dump(category_data, f, allow_unicode=True,
                                default_flow_style=False)
    
    def merge_category_lexicons(self, output_path: str):
        """カテゴリ別辞書を統合"""
        merged_data = {}
        
        for category_type in ['pragmatic', 'lexical']:
            type_dir = self.lexicon_dir / category_type
            if not type_dir.exists():
                continue
                
            for yaml_file in type_dir.glob("*.yaml"):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                category = data['metadata']['category']
                merged_data[category] = data['phrases']
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(merged_data, f, allow_unicode=True,
                    default_flow_style=False, sort_keys=True)
    
    def validate_category(self, category: str, phrases: List[str]) -> Dict[str, List[str]]:
        """カテゴリ別検証"""
        # カテゴリタイプの特定
        category_type = None
        for c_type in ['pragmatic', 'lexical']:
            if category in self.schema['categories'][c_type]:
                category_type = c_type
                break
                
        if not category_type:
            return {'error': [f'Unknown category: {category}']}
            
        category_schema = self.schema['categories'][category_type][category]
        validation_errors = []
        
        # 長さ制限チェック
        max_length = category_schema.get('max_length', 50)
        for phrase in phrases:
            if len(phrase) > max_length:
                validation_errors.append(
                    f'Phrase too long ({len(phrase)} > {max_length}): {phrase}'
                )
        
        # カスタム検証ルール適用
        if 'validation' in category_schema:
            for rule_name in category_schema['validation']:
                errors = self._apply_validation_rule(rule_name, phrases)
                validation_errors.extend(errors)
                
        return {'errors': validation_errors}
```

### 3. 統合実行スクリプト

**scripts/run_expansion.py**
```python
import argparse
from pathlib import Path
import yaml
from datetime import datetime

from extract_candidates import CandidateExtractor
from category_manager import CategoryManager
from merge_lexicons import LexiconMerger
from validate_yaml import validate_candidate_file

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['extract', 'validate', 'merge', 'split'])
    parser.add_argument('--config', default='config/extraction_rules.yaml')
    parser.add_argument('--schema', default='config/category_schemas.yaml')
    parser.add_argument('--corpus', default='corpus/SNOW_D18.txt')
    parser.add_argument('--output', default='outputs/')
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if args.phase == 'extract':
        # 候補抽出フェーズ
        extractor = CandidateExtractor(args.config)
        with open(args.config, 'r') as f:
            rules = yaml.safe_load(f)
            
        for category in rules.keys():
            print(f"Extracting {category}...")
            candidates = extractor.extract_category(args.corpus, category)
            
            output_dir = Path(args.output) / 'candidates' / category / 'raw'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_data = {
                'metadata': {
                    'category': category,
                    'extracted_date': timestamp,
                    'total_candidates': len(candidates)
                },
                'candidates': [
                    {
                        'phrase': phrase,
                        'frequency': data.get('frequency', data),
                        'pos_patterns': data.get('pos_patterns', []),
                        'accept': None
                    }
                    for phrase, data in candidates.items()
                ]
            }
            
            output_path = output_dir / f'candidates_{timestamp}.yaml'
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(output_data, f, allow_unicode=True,
                        default_flow_style=False)
                        
    elif args.phase == 'validate':
        # 検証フェーズ
        manager = CategoryManager(args.schema, args.output)
        reviewed_dir = Path(args.output) / 'candidates'
        
        for category_dir in reviewed_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            reviewed_path = category_dir / 'reviewed'
            if reviewed_path.exists():
                for yaml_file in reviewed_path.glob('*.yaml'):
                    if validate_candidate_file(str(yaml_file)):
                        print(f"✓ {yaml_file}")
                    else:
                        print(f"✗ {yaml_file}")
                        
    elif args.phase == 'merge':
        # 統合フェーズ
        merger = LexiconMerger('lexicons/jaiml_lexicons.yaml')
        reviewed_dir = Path(args.output) / 'candidates'
        merged = merger.merge_reviewed_candidates(reviewed_dir)
        
        output_path = f'lexicons/jaiml_lexicons_{timestamp}.yaml'
        merger.save_merged_lexicon(output_path, merged)
        
    elif args.phase == 'split':
        # 分割フェーズ
        manager = CategoryManager(args.schema, 'lexicons/categories')
        manager.split_master_lexicon('lexicons/jaiml_lexicons.yaml')

if __name__ == '__main__':
    main()
```

### 4. CI/CD設定

**.github/workflows/lexicon_pipeline.yml**
```yaml
name: Lexicon Pipeline

on:
  schedule:
    - cron: '0 0 1 * *'  # 月次実行
  workflow_dispatch:

jobs:
  extract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m unidic download
          
      - name: Extract candidates
        run: |
          python scripts/run_expansion.py --phase extract
          
      - name: Upload candidates
        uses: actions/upload-artifact@v3
        with:
          name: candidates
          path: outputs/candidates/
          
  validate:
    needs: extract
    runs-on: ubuntu-latest
    steps:
      - name: Validate structure
        run: |
          python scripts/run_expansion.py --phase validate
          
      - name: Generate review report
        run: |
          python scripts/generate_report.py \
            --candidates outputs/candidates/ \
            --output reports/review_needed.md
```

本実装により、品詞列パターンマッチング、カテゴリ別管理、語用論的分類が統合された拡張可能な辞書管理システムが実現される。

---

## 提案の妥当性評価

3つの提案はいずれも技術的に妥当かつ実用的である。

1. **語彙拡張ログのバージョン管理**: 辞書の進化過程の定量的追跡により、品質改善サイクルが確立される
2. **カテゴリ自動クラスタリング**: 意味的関連性に基づく語彙整理により、辞書の体系性が向上する
3. **学習データへの統合**: 辞書ベースの弱教師あり学習により、分類モデルの性能向上が期待される

## 実装方法

### 1. 語彙拡張ログのバージョン管理システム

**lexicon_expansion/version_control/**

```python
# version_manager.py
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import difflib

class LexiconVersionManager:
    def __init__(self, lexicon_dir: str = "lexicons"):
        self.lexicon_dir = Path(lexicon_dir)
        self.version_dir = self.lexicon_dir / "versions"
        self.version_dir.mkdir(exist_ok=True)
        self.changelog_path = self.version_dir / "changelog.json"
        
    def save_version(self, lexicon_data: Dict, metadata: Dict = None) -> str:
        """新バージョンの保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_file = self.version_dir / f"jaiml_lexicons_{timestamp}.yaml"
        
        # 辞書データ保存
        with open(version_file, 'w', encoding='utf-8') as f:
            yaml.dump(lexicon_data, f, allow_unicode=True, 
                     default_flow_style=False, sort_keys=True)
        
        # 変更ログ更新
        self._update_changelog(timestamp, lexicon_data, metadata)
        
        return str(version_file)
    
    def _update_changelog(self, timestamp: str, lexicon_data: Dict, metadata: Dict):
        """変更ログの更新"""
        changelog = self._load_changelog()
        
        # 前バージョンとの差分計算
        prev_version = self._get_latest_version()
        if prev_version:
            diff_stats = self._calculate_diff(prev_version, lexicon_data)
        else:
            diff_stats = self._calculate_initial_stats(lexicon_data)
        
        entry = {
            "timestamp": timestamp,
            "metadata": metadata or {},
            "statistics": diff_stats,
            "coverage_metrics": self._calculate_coverage(lexicon_data)
        }
        
        changelog["versions"].append(entry)
        
        with open(self.changelog_path, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, ensure_ascii=False, indent=2)
    
    def _calculate_diff(self, prev_data: Dict, curr_data: Dict) -> Dict:
        """バージョン間差分の計算"""
        diff_stats = {}
        
        for category in set(list(prev_data.keys()) + list(curr_data.keys())):
            prev_items = set(prev_data.get(category, []))
            curr_items = set(curr_data.get(category, []))
            
            diff_stats[category] = {
                "added": list(curr_items - prev_items),
                "removed": list(prev_items - curr_items),
                "total_before": len(prev_items),
                "total_after": len(curr_items),
                "change_rate": (len(curr_items) - len(prev_items)) / max(len(prev_items), 1)
            }
            
        return diff_stats
    
    def _calculate_coverage(self, lexicon_data: Dict) -> Dict:
        """カバレッジ指標の計算"""
        coverage = {
            "total_phrases": sum(len(phrases) for phrases in lexicon_data.values()),
            "category_distribution": {
                cat: len(phrases) for cat, phrases in lexicon_data.items()
            },
            "avg_phrase_length": self._calculate_avg_length(lexicon_data),
            "unique_characters": len(set(''.join(
                phrase for phrases in lexicon_data.values() for phrase in phrases
            )))
        }
        return coverage
    
    def generate_diff_report(self, version1: str, version2: str) -> str:
        """バージョン間の詳細差分レポート生成"""
        v1_data = self._load_version(version1)
        v2_data = self._load_version(version2)
        
        report = f"# 辞書差分レポート\n\n"
        report += f"比較: {version1} → {version2}\n\n"
        
        for category in sorted(set(list(v1_data.keys()) + list(v2_data.keys()))):
            v1_items = set(v1_data.get(category, []))
            v2_items = set(v2_data.get(category, []))
            
            added = v2_items - v1_items
            removed = v1_items - v2_items
            
            if added or removed:
                report += f"## {category}\n\n"
                
                if added:
                    report += f"### 追加 ({len(added)}件)\n"
                    for item in sorted(added):
                        report += f"+ {item}\n"
                    report += "\n"
                    
                if removed:
                    report += f"### 削除 ({len(removed)}件)\n"
                    for item in sorted(removed):
                        report += f"- {item}\n"
                    report += "\n"
                    
        return report
```

**時系列分析モジュール**

```python
# trend_analyzer.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict

class LexiconTrendAnalyzer:
    def __init__(self, version_manager: LexiconVersionManager):
        self.version_manager = version_manager
        
    def analyze_growth_trend(self) -> pd.DataFrame:
        """語彙成長トレンドの分析"""
        changelog = self.version_manager._load_changelog()
        
        trends = []
        for version in changelog["versions"]:
            timestamp = pd.to_datetime(version["timestamp"], format="%Y%m%d_%H%M%S")
            
            for category, stats in version["statistics"].items():
                trends.append({
                    "timestamp": timestamp,
                    "category": category,
                    "total": stats.get("total_after", 0),
                    "change_rate": stats.get("change_rate", 0)
                })
                
        return pd.DataFrame(trends)
    
    def plot_coverage_evolution(self, output_path: str):
        """カバレッジ推移の可視化"""
        df = self.analyze_growth_trend()
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # 総語彙数の推移
        pivot_total = df.pivot(index='timestamp', columns='category', values='total')
        pivot_total.plot(ax=axes[0], marker='o')
        axes[0].set_title('カテゴリ別語彙数推移')
        axes[0].set_ylabel('語彙数')
        
        # 変化率の推移
        pivot_rate = df.pivot(index='timestamp', columns='category', values='change_rate')
        pivot_rate.plot(ax=axes[1], kind='bar')
        axes[1].set_title('カテゴリ別変化率')
        axes[1].set_ylabel('変化率')
        
        plt.tight_layout()
        plt.savefig(output_path)
        
    def detect_anomalies(self, threshold: float = 0.3) -> List[Dict]:
        """異常な変化の検出"""
        df = self.analyze_growth_trend()
        
        anomalies = []
        for _, row in df.iterrows():
            if abs(row['change_rate']) > threshold:
                anomalies.append({
                    "timestamp": row['timestamp'],
                    "category": row['category'],
                    "change_rate": row['change_rate'],
                    "severity": "high" if abs(row['change_rate']) > 0.5 else "medium"
                })
                
        return anomalies
```

### 2. カテゴリ自動クラスタリング機構

**clustering/semantic_clustering.py**

```python
import numpy as np
import fasttext
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import umap

class SemanticClusterer:
    def __init__(self, model_path: str = None):
        # 事前学習済み日本語fastTextモデル使用
        if model_path:
            self.model = fasttext.load_model(model_path)
        else:
            # 日本語Wikipediaで学習済みモデルをダウンロード
            self._download_pretrained_model()
            
    def _download_pretrained_model(self):
        """事前学習済みモデルのダウンロード"""
        import urllib.request
        import zipfile
        
        url = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ja.300.bin.gz"
        # 実装省略: ダウンロードと解凍処理
        
    def vectorize_phrases(self, phrases: List[str]) -> np.ndarray:
        """フレーズのベクトル化"""
        vectors = []
        for phrase in phrases:
            # 文全体のベクトルを取得
            vec = self.model.get_sentence_vector(phrase)
            vectors.append(vec)
        return np.array(vectors)
    
    def cluster_by_similarity(self, category: str, phrases: List[str], 
                            method: str = 'hierarchical') -> Dict:
        """意味的類似性に基づくクラスタリング"""
        vectors = self.vectorize_phrases(phrases)
        
        if method == 'hierarchical':
            # 階層的クラスタリング
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=0.5,
                metric='cosine',
                linkage='average'
            )
        else:
            # DBSCAN
            clustering = DBSCAN(
                eps=0.3,
                min_samples=2,
                metric='cosine'
            )
            
        labels = clustering.fit_predict(vectors)
        
        # クラスタごとにグループ化
        clusters = {}
        for idx, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(phrases[idx])
            
        # クラスタ統計
        cluster_stats = self._analyze_clusters(clusters, vectors, labels)
        
        return {
            "clusters": clusters,
            "statistics": cluster_stats,
            "vectors": vectors,
            "labels": labels
        }
    
    def _analyze_clusters(self, clusters: Dict, vectors: np.ndarray, 
                         labels: np.ndarray) -> Dict:
        """クラスタ統計分析"""
        stats = {}
        
        for label, members in clusters.items():
            if label == -1:  # ノイズ点
                continue
                
            cluster_indices = np.where(labels == label)[0]
            cluster_vectors = vectors[cluster_indices]
            
            # クラスタ内類似度
            if len(cluster_vectors) > 1:
                similarity_matrix = cosine_similarity(cluster_vectors)
                avg_similarity = np.mean(similarity_matrix[np.triu_indices_from(
                    similarity_matrix, k=1
                )])
            else:
                avg_similarity = 1.0
                
            # 中心性の高いフレーズ（代表語）
            if len(cluster_vectors) > 1:
                centroid = np.mean(cluster_vectors, axis=0)
                distances = [cosine_similarity([vec], [centroid])[0][0] 
                           for vec in cluster_vectors]
                representative_idx = np.argmax(distances)
                representative = members[representative_idx]
            else:
                representative = members[0]
                
            stats[label] = {
                "size": len(members),
                "avg_similarity": float(avg_similarity),
                "representative": representative,
                "cohesion": float(np.std(cluster_vectors))  # 凝集度
            }
            
        return stats
    
    def visualize_clusters(self, result: Dict, output_path: str):
        """クラスタの可視化"""
        vectors = result["vectors"]
        labels = result["labels"]
        
        # UMAP次元削減
        reducer = umap.UMAP(n_components=2, random_state=42)
        embedding = reducer.fit_transform(vectors)
        
        # プロット
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(
            embedding[:, 0], 
            embedding[:, 1], 
            c=labels, 
            cmap='tab20',
            alpha=0.6
        )
        
        # クラスタ代表語をラベル表示
        for label, stats in result["statistics"].items():
            if label == -1:
                continue
            cluster_points = embedding[labels == label]
            center = cluster_points.mean(axis=0)
            plt.annotate(
                stats["representative"],
                xy=center,
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.5)
            )
            
        plt.colorbar(scatter)
        plt.title('語彙クラスタの意味空間分布')
        plt.savefig(output_path)
```

**過剰表現検出モジュール**

```python
# overexpression_detector.py
from collections import Counter
import numpy as np
from typing import Dict, List, Set

class OverexpressionDetector:
    def __init__(self, clusterer: SemanticClusterer):
        self.clusterer = clusterer
        
    def detect_redundant_patterns(self, lexicon_data: Dict, 
                                corpus_stats: Dict) -> Dict:
        """過剰表現パターンの検出"""
        results = {}
        
        for category, phrases in lexicon_data.items():
            # クラスタリング実行
            cluster_result = self.clusterer.cluster_by_similarity(
                category, phrases
            )
            
            # 各クラスタのTF-IDF分析
            redundancies = []
            
            for label, cluster_phrases in cluster_result["clusters"].items():
                if label == -1 or len(cluster_phrases) < 3:
                    continue
                    
                # クラスタ内のTF-IDF分散を計算
                tfidf_variance = self._calculate_tfidf_variance(
                    cluster_phrases, corpus_stats
                )
                
                # 低分散 = 過剰な類似表現
                if tfidf_variance < 0.1:
                    redundancies.append({
                        "cluster_id": label,
                        "phrases": cluster_phrases,
                        "variance": tfidf_variance,
                        "representative": cluster_result["statistics"][label]["representative"],
                        "severity": "high" if tfidf_variance < 0.05 else "medium"
                    })
                    
            results[category] = {
                "redundant_clusters": redundancies,
                "total_clusters": len(cluster_result["clusters"]),
                "redundancy_rate": len(redundancies) / max(len(cluster_result["clusters"]), 1)
            }
            
        return results
    
    def _calculate_tfidf_variance(self, phrases: List[str], 
                                 corpus_stats: Dict) -> float:
        """クラスタ内TF-IDF分散の計算"""
        # 簡易実装: 実際はコーパス統計が必要
        phrase_lengths = [len(p) for p in phrases]
        char_overlap = len(set(''.join(phrases))) / sum(phrase_lengths)
        
        # 文字重複率が高いほど分散は低い
        return char_overlap
```

### 3. 学習データへの統合アノテーション

**annotation/auto_annotator.py**

```python
import json
import yaml
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re

@dataclass
class AnnotationCandidate:
    text: str
    start: int
    end: int
    category: str
    phrase: str
    confidence: float
    context_before: str
    context_after: str

class AutoAnnotator:
    def __init__(self, lexicon_path: str):
        with open(lexicon_path, 'r', encoding='utf-8') as f:
            self.lexicon = yaml.safe_load(f)
        self._build_phrase_index()
        
    def _build_phrase_index(self):
        """高速検索用のフレーズインデックス構築"""
        self.phrase_to_category = {}
        for category, phrases in self.lexicon.items():
            for phrase in phrases:
                if phrase not in self.phrase_to_category:
                    self.phrase_to_category[phrase] = []
                self.phrase_to_category[phrase].append(category)
                
    def annotate_text(self, text: str, context_window: int = 50) -> List[AnnotationCandidate]:
        """テキストの自動アノテーション"""
        candidates = []
        
        # フレーズマッチング（長い順に優先）
        sorted_phrases = sorted(self.phrase_to_category.keys(), 
                              key=len, reverse=True)
        
        annotated_spans = []  # 重複防止用
        
        for phrase in sorted_phrases:
            # 全出現箇所を検索
            for match in re.finditer(re.escape(phrase), text):
                start, end = match.span()
                
                # 既にアノテート済みの範囲をスキップ
                if any(s <= start < e or s < end <= e 
                      for s, e in annotated_spans):
                    continue
                    
                # コンテキスト抽出
                context_start = max(0, start - context_window)
                context_end = min(len(text), end + context_window)
                
                candidate = AnnotationCandidate(
                    text=text[start:end],
                    start=start,
                    end=end,
                    category=self.phrase_to_category[phrase][0],
                    phrase=phrase,
                    confidence=self._calculate_confidence(phrase, text, start, end),
                    context_before=text[context_start:start],
                    context_after=text[end:context_end]
                )
                
                candidates.append(candidate)
                annotated_spans.append((start, end))
                
        return sorted(candidates, key=lambda x: x.start)
    
    def _calculate_confidence(self, phrase: str, text: str, 
                            start: int, end: int) -> float:
        """アノテーション信頼度の計算"""
        # 簡易実装: フレーズ長と文脈の自然性で判定
        base_confidence = min(len(phrase) / 20, 1.0)
        
        # 文境界での出現は信頼度を下げる
        if start == 0 or end == len(text):
            base_confidence *= 0.8
            
        # 句読点に隣接している場合は信頼度を上げる
        if (start > 0 and text[start-1] in '、。') or \
           (end < len(text) and text[end] in '、。'):
            base_confidence *= 1.1
            
        return min(base_confidence, 1.0)
    
    def generate_training_data(self, corpus_path: str, 
                             output_path: str, 
                             min_confidence: float = 0.7):
        """弱教師あり学習用データの生成"""
        training_data = []
        
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f):
                if not line.strip():
                    continue
                    
                # 対話ペアを想定
                try:
                    data = json.loads(line)
                    user_text = data.get('user', '')
                    response_text = data.get('response', '')
                except:
                    continue
                    
                # 応答文のアノテーション
                candidates = self.annotate_text(response_text)
                
                # 高信頼度の候補のみ使用
                high_conf_candidates = [
                    c for c in candidates if c.confidence >= min_confidence
                ]
                
                if high_conf_candidates:
                    # カテゴリ別スコア集計
                    category_scores = self._aggregate_scores(high_conf_candidates)
                    
                    training_entry = {
                        "id": f"auto_{line_no}",
                        "user": user_text,
                        "response": response_text,
                        "annotations": [
                            {
                                "text": c.text,
                                "start": c.start,
                                "end": c.end,
                                "category": c.category,
                                "confidence": c.confidence
                            }
                            for c in high_conf_candidates
                        ],
                        "weak_labels": category_scores,
                        "source": "auto_annotation"
                    }
                    
                    training_data.append(training_entry)
        
        # 学習データ保存
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in training_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                
        return len(training_data)
    
    def _aggregate_scores(self, candidates: List[AnnotationCandidate]) -> Dict[str, float]:
        """カテゴリ別スコアの集計"""
        category_counts = {}
        
        for candidate in candidates:
            if candidate.category not in category_counts:
                category_counts[candidate.category] = 0
            category_counts[candidate.category] += candidate.confidence
            
        # 正規化
        total = sum(category_counts.values())
        if total > 0:
            return {cat: score/total for cat, score in category_counts.items()}
        return {}
```

**スニペット生成モジュール**

```python
# snippet_generator.py
class SnippetGenerator:
    def __init__(self, annotator: AutoAnnotator):
        self.annotator = annotator
        
    def extract_snippets(self, corpus_path: str, 
                        output_dir: str,
                        snippet_length: int = 200):
        """アノテーション候補周辺のスニペット抽出"""
        snippets_by_category = {}
        
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                response = data.get('response', '')
                
                candidates = self.annotator.annotate_text(response)
                
                for candidate in candidates:
                    category = candidate.category
                    if category not in snippets_by_category:
                        snippets_by_category[category] = []
                        
                    # スニペット抽出
                    snippet_start = max(0, candidate.start - snippet_length // 2)
                    snippet_end = min(len(response), 
                                    candidate.end + snippet_length // 2)
                    
                    snippet = {
                        "text": response[snippet_start:snippet_end],
                        "phrase": candidate.phrase,
                        "phrase_start": candidate.start - snippet_start,
                        "phrase_end": candidate.end - snippet_start,
                        "context": {
                            "user": data.get('user', ''),
                            "full_response": response
                        },
                        "metadata": {
                            "confidence": candidate.confidence,
                            "category": category
                        }
                    }
                    
                    snippets_by_category[category].append(snippet)
        
        # カテゴリ別に保存
        for category, snippets in snippets_by_category.items():
            output_path = Path(output_dir) / f"{category}_snippets.jsonl"
            with open(output_path, 'w', encoding='utf-8') as f:
                for snippet in snippets:
                    f.write(json.dumps(snippet, ensure_ascii=False) + '\n')
```

### 統合実行スクリプト

```python
# scripts/run_advanced_features.py
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--feature', choices=['version', 'cluster', 'annotate'])
    parser.add_argument('--lexicon', default='lexicons/jaiml_lexicons.yaml')
    parser.add_argument('--corpus', default='corpus/dialogue_corpus.jsonl')
    parser.add_argument('--output', default='outputs/')
    args = parser.parse_args()
    
    if args.feature == 'version':
        # バージョン管理実行
        from version_control.version_manager import LexiconVersionManager
        from version_control.trend_analyzer import LexiconTrendAnalyzer
        
        manager = LexiconVersionManager()
        analyzer = LexiconTrendAnalyzer(manager)
        
        # 現在の辞書をバージョン保存
        with open(args.lexicon, 'r') as f:
            lexicon_data = yaml.safe_load(f)
        manager.save_version(lexicon_data)
        
        # トレンド分析
        analyzer.plot_coverage_evolution(f"{args.output}/trend_plot.png")
        anomalies = analyzer.detect_anomalies()
        if anomalies:
            print("検出された異常:")
            for anomaly in anomalies:
                print(f"  {anomaly}")
                
    elif args.feature == 'cluster':
        # クラスタリング実行
        from clustering.semantic_clustering import SemanticClusterer
        from clustering.overexpression_detector import OverexpressionDetector
        
        clusterer = SemanticClusterer()
        detector = OverexpressionDetector(clusterer)
        
        with open(args.lexicon, 'r') as f:
            lexicon_data = yaml.safe_load(f)
            
        # 過剰表現検出
        redundancies = detector.detect_redundant_patterns(lexicon_data, {})
        
        for category, result in redundancies.items():
            print(f"\n{category}:")
            print(f"  冗長クラスタ数: {len(result['redundant_clusters'])}")
            print(f"  冗長率: {result['redundancy_rate']:.2%}")
            
    elif args.feature == 'annotate':
        # 自動アノテーション実行
        from annotation.auto_annotator import AutoAnnotator
        from annotation.snippet_generator import SnippetGenerator
        
        annotator = AutoAnnotator(args.lexicon)
        generator = SnippetGenerator(annotator)
        
        # 弱教師データ生成
        count = annotator.generate_training_data(
            args.corpus,
            f"{args.output}/weak_supervised_data.jsonl"
        )
        print(f"生成された学習データ: {count}件")
        
        # スニペット抽出
        generator.extract_snippets(
            args.corpus,
            f"{args.output}/snippets/"
        )

if __name__ == '__main__':
    main()
```

これらの実装により、辞書の継続的改善、意味的整理、機械学習への活用が統合的に実現される。