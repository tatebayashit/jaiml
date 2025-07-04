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