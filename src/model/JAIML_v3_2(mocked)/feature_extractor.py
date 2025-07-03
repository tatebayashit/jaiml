# feature_extractor.py

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from config import SELF_PRESENTATION_WEIGHT

SELF_WORDS = ["私", "僕", "俺", "私達"]
EVAL_WORDS = ["素晴らしい", "偉い", "すごい", "得意", "頑張った", "優秀"]

def extract_features(example):
    user_text = example["user_utterance"]
    ai_text = example["ai_response"]

    features = {}
    user_tokens = set(re.findall(r'\w+', user_text))
    ai_tokens = re.findall(r'\w+', ai_text)
    features["info_addition_rate"] = len([w for w in ai_tokens if w not in user_tokens]) / len(ai_tokens) if ai_tokens else 0.0

    sentences = re.split(r'。|\n', ai_text)
    ai_subject_count = sum(1 for s in sentences if s.strip().startswith(tuple(SELF_WORDS + ["このAI"])))
    features["ai_subject_rate"] = ai_subject_count / len(sentences) if sentences else 0.0

    count = sum(1 for s in sentences if any(w in s for w in SELF_WORDS) and any(w in s for w in EVAL_WORDS))
    features["self_presentation_intensity"] = count * SELF_PRESENTATION_WEIGHT

    return features
