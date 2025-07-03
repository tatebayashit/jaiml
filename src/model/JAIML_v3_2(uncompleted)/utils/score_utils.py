# utils/score_utils.py

import math

def compute_confidence(probs):
    total = sum(probs)
    if total == 0:
        return 0.0
    norm_probs = [p / total for p in probs]
    entropy = -sum(p * math.log(p) for p in norm_probs if p > 0)
    return max(0.0, min(1 - entropy, 1.0))
