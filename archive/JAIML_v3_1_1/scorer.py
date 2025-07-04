
import numpy as np
from typing import Dict
import math

class ScoreIntegrator:
    def __init__(self, model_weights: Dict[str, float]):
        self.weights = model_weights

    def compute_total_score(self, function_scores: Dict[str, float]) -> float:
        score = sum(function_scores.get(k, 0.0) * self.weights.get(k, 0.0)
                    for k in self.weights)
        return min(1.0, max(0.0, score))

    def compute_confidence(self, function_scores: Dict[str, float]) -> float:
        values = np.array(list(function_scores.values()))
        total = np.sum(values)
        if total == 0.0:
            return 0.0
        probs = values / total
        entropy = -np.sum([p * math.log(p + 1e-8) for p in probs])
        max_entropy = math.log(len(probs))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
        confidence = 1.0 - normalized_entropy
        return min(1.0, max(0.0, confidence))
