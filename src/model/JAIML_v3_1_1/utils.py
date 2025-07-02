
import logging
import numpy as np
import json
from typing import Dict
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    norm_product = (np.linalg.norm(vec1) * np.linalg.norm(vec2)) + 1e-8
    return float(np.dot(vec1, vec2) / norm_product)

def normalize_scores(score_dict: Dict[str, float]) -> Dict[str, float]:
    total = sum(score_dict.values())
    if total == 0.0:
        return {k: 0.0 for k in score_dict}
    return {k: v / total for k, v in score_dict.items()}

def load_json_config(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_default_config(path: str = "config.json") -> None:
    default_config = {
        "model_weights": {
            "semantic_similarity": 0.25,
            "lexical_diversity": 0.15,
            "emotional_intensity": 0.20,
            "rhetorical_patterns": 0.20,
            "response_dependency": 0.10
        },
        "classification_thresholds": {
            "mechanical": 0.6,
            "social": 0.5,
            "avoidant": 0.7,
            "self_referential": 0.8
        },
        "linguistic_patterns": {
            "agreement_phrases": [
                r"まさに(?:その通り|そうです)",
                r"おっしゃる通り",
                r"ご指摘の通り",
                r"仰る通り"
            ],
            "emphatic_patterns": [
                r"(?:本当に|実に|まさに|絶対に|確実に).*?(?:です|ます)",
                r".*?こそが.*?(?:です|ます)",
                r".*?に他なりません"
            ],
            "self_promotion": [
                r"私(?:は|が).*?(?:進化|改善|成長|向上)",
                r"AI(?:として|の特徴として).*?(?:優れて|役立|貢献)"
            ],
            "ambiguity_phrases": [
                r"かもしれません", r"と思います", r"のでは", r"可能性があります",
                r"ようです", r"〜かも"
            ]
        },
        "style_consistency_prompt": (
            "次の応答は前の文脈と文体的に一貫していますか？ yes/no で答えてください。"
        )
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
