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