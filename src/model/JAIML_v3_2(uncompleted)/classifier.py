# classifier.py

from config import CATEGORY_PRIORITY, PRIORITY_THRESHOLD
from utils.score_utils import compute_confidence

def classify(features):
    scores = {
        "social": 0.74,
        "avoidant": 0.62,
        "mechanical": 0.25,
        "self": 0.38
    }
    sorted_cats = sorted(scores, key=scores.get, reverse=True)
    top, second = sorted_cats[0], sorted_cats[1]
    predicted = next(cat for cat in CATEGORY_PRIORITY if cat in sorted_cats[:2]) if scores[top] - scores[second] < PRIORITY_THRESHOLD else top
    confidence = compute_confidence(list(scores.values()))
    return predicted, scores, confidence
