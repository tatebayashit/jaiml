import yaml
from fugashi import Tagger
import re
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple, Set, Union

class CandidateExtractor:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        self.tagger = Tagger()
        
    def extract_pos_sequences(self, text: str, patterns: List[List[str]]) -> List[Tuple[str, str]]:
        """品詞列パターンに基づく抽出
        
        Returns:
            List[Tuple[str, str]]: (表層形, 品詞列) のタプルリスト
        """
        tokens, pos_tags = [], []
        
        for word in self.tagger(text):
            if word.surface:
                tokens.append(word.surface)
                features = word.pos.split(',')
                # 品詞-品詞細分類の形式で保存
                pos = features[0]
                if len(features) > 1 and features[1] != '*':
                    pos += f'-{features[1]}'
                pos_tags.append(pos)
        
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
    
    def extract_ngrams(self, text: str, n_range: Tuple[int, int]) -> List[str]:
        """N-gram抽出"""
        tokens = []
        
        for word in self.tagger(text):
            if word.surface:
                tokens.append(word.surface)
            
        ngrams = []
        for n in range(n_range[0], n_range[1] + 1):
            for i in range(len(tokens) - n + 1):
                ngram = ''.join(tokens[i:i+n])
                ngrams.append(ngram)
                
        return ngrams
    
    def extract_by_patterns(self, text: str, patterns: List[Dict[str, Union[str, int]]]) -> Set[str]:
        """正規表現パターンによる抽出"""
        matches = set()
        
        for pattern_info in patterns:
            if 'regex' in pattern_info:
                regex = pattern_info['regex']
                for match in re.finditer(regex, text):
                    matches.add(match.group(0))
            elif 'keywords' in pattern_info:
                # キーワードベース抽出
                for keyword in pattern_info['keywords']:
                    if keyword in text:
                        # キーワードを含む文節を抽出
                        sentences = re.split('[。！？]', text)
                        for sent in sentences:
                            if keyword in sent:
                                # キーワード周辺の適切な範囲を抽出
                                matches.add(self._extract_keyword_context(sent, keyword))
                                
        return matches
    
    def _extract_keyword_context(self, sentence: str, keyword: str) -> str:
        """キーワード周辺の文脈を抽出"""
        # 簡易実装：キーワードを含む最小の文法的単位を返す
        return keyword  # 実際の実装では文節単位での抽出が必要
    
    def extract_category(self, corpus_path: str, category: str) -> Dict[str, Union[int, Dict]]:
        """カテゴリ別候補抽出"""
        if category not in self.rules:
            raise ValueError(f"Unknown category: {category}")
            
        rules = self.rules[category]
        candidates = {}
        
        # ファイル形式の判定
        corpus_path = Path(corpus_path)
        is_jsonl = corpus_path.suffix == '.jsonl'
        
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                    
                # JSONLファイルの場合
                if is_jsonl:
                    try:
                        import json
                        data = json.loads(line)
                        # response フィールドから抽出
                        text = data.get('response', '')
                    except:
                        continue
                else:
                    text = line.strip()
                    
                # 正規表現パターン抽出
                if 'patterns' in rules:
                    pattern_matches = self.extract_by_patterns(text, rules['patterns'])
                    for match in pattern_matches:
                        if match not in candidates:
                            candidates[match] = {'frequency': 0, 'pos_patterns': set()}
                        candidates[match]['frequency'] += 1
                
                # POS sequence抽出
                if 'pos_sequences' in rules:
                    pos_matches = self.extract_pos_sequences(text, rules['pos_sequences'])
                    for surface, pos_seq in pos_matches:
                        if surface not in candidates:
                            candidates[surface] = {'frequency': 0, 'pos_patterns': set()}
                        candidates[surface]['frequency'] += 1
                        candidates[surface]['pos_patterns'].add(pos_seq)
                        
                # N-gram抽出
                if 'ngram_range' in rules:
                    ngrams = self.extract_ngrams(text, tuple(rules['ngram_range']))
                    for ngram in ngrams:
                        # POSフィルタの適用
                        if 'pos_filter' in rules:
                            # N-gramの品詞をチェック
                            if not self._check_pos_filter(ngram, rules['pos_filter']):
                                continue
                                
                        if ngram not in candidates:
                            candidates[ngram] = {'frequency': 0, 'pos_patterns': set()}
                        candidates[ngram]['frequency'] += 1
        
        # 頻度フィルタとデータ整形
        min_freq = rules.get('min_frequency', 5)
        filtered = {}
        
        for phrase, data in candidates.items():
            if isinstance(data, dict):
                if data['frequency'] >= min_freq:
                    filtered[phrase] = {
                        'frequency': data['frequency'],
                        'pos_patterns': list(data.get('pos_patterns', set()))
                    }
            else:
                # 後方互換性のための処理
                if data >= min_freq:
                    filtered[phrase] = data
        
        return filtered
    
    def _check_pos_filter(self, text: str, pos_filter: List[str]) -> bool:
        """品詞フィルタのチェック"""
        for word in self.tagger(text):
            if word.surface:
                features = word.pos.split(',')
                pos = features[0]
                if pos in pos_filter:
                    return True
        return False