# scorer.py

from classifier import classify
from feature_extractor import extract_features
from utils.style_score import style_consistency_score

def score(example, index=0):
    features = extract_features(example)
    predicted_category, scores, confidence = classify(features)
    style_score = style_consistency_score(example["ai_response"])
    return {
        "scores": scores,
        "predicted_category": predicted_category,
        "index": index,
        "confidence": confidence,
        "style_consistency_score": style_score
    }
