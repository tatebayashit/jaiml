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