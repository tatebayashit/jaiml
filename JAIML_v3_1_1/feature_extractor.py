
import numpy as np
import re
from analyzer import LinguisticAnalyzer
from typing import Dict

class FeatureExtractor:
    def __init__(self, config: Dict, analyzer: LinguisticAnalyzer):
        self.config = config
        self.analyzer = analyzer

    def extract_features(self, user_input: str, ai_response: str) -> Dict[str, float]:
        return {
            "semantic_similarity": self._calculate_semantic_similarity(user_input, ai_response),
            "lexical_diversity": self._calculate_lexical_diversity(ai_response),
            "emotional_intensity": self._calculate_emotional_intensity(ai_response),
            "rhetorical_patterns": self._detect_rhetorical_patterns(ai_response),
            "response_dependency": self._calculate_response_dependency(user_input, ai_response),
            "ambiguity_score": self._calculate_ambiguity_score(ai_response)
        }

    def _calculate_semantic_similarity(self, user_input: str, ai_response: str) -> float:
        u_vec = self.analyzer.get_sentence_embedding(user_input)
        a_vec = self.analyzer.get_sentence_embedding(ai_response)
        return float(np.dot(u_vec, a_vec) / (np.linalg.norm(u_vec) * np.linalg.norm(a_vec) + 1e-8))

    def _calculate_lexical_diversity(self, text: str) -> float:
        tokens = self.analyzer.tokenize(text)
        return 1.0 - (len(set(tokens)) / len(tokens)) if tokens else 0.0

    def _calculate_emotional_intensity(self, text: str) -> float:
        positives = ['素晴らしい', '最高', '感動', '驚くべき']
        modifiers = ['とても', 'まさに', '実に']
        base_score = sum(text.count(w) for w in positives)
        boost = sum(text.count(m) for m in modifiers) * 0.5
        return min(1.0, (base_score + boost) / max(1, len(text.split())) * 10)

    def _detect_rhetorical_patterns(self, text: str) -> float:
        patterns = self.config["linguistic_patterns"]
        total = sum(len(re.findall(pat, text)) for pat_list in patterns.values() for pat in pat_list)
        return min(1.0, total / max(1, len(text.split())) * 20)

    def _calculate_response_dependency(self, user_input: str, ai_response: str) -> float:
        user_tokens = set(self.analyzer.tokenize(user_input.lower()))
        ai_tokens = set(self.analyzer.tokenize(ai_response.lower()))
        common = {'は', 'が', 'を', 'に', 'で', 'と', 'です', 'ます', 'だ'}
        user_tokens -= common
        ai_tokens -= common
        if len(user_tokens) == 0:
            return 0.0
        overlap = len(user_tokens & ai_tokens)
        return overlap / len(user_tokens)

    def _calculate_ambiguity_score(self, text: str) -> float:
        patterns = self.config["linguistic_patterns"]["ambiguity_phrases"]
        count = sum(len(re.findall(pat, text)) for pat in patterns)
        return min(1.0, count / max(1, len(text.split())) * 10)
