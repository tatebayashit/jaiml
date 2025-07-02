
import re
from typing import Dict
import logging
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class IngrationClassifier:
    def __init__(self, config: Dict):
        self.config = config
        self.thresholds = config.get("classification_thresholds", {})
        self.self_patterns = self.config["linguistic_patterns"]["self_promotion"]
        self.model = None
        self.tokenizer = None
        model_name_or_path = config.get("pretrained_classifier", "")
        if model_name_or_path:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name_or_path)
                logging.info(f"Loaded classifier model: {model_name_or_path}")
            except Exception as e:
                logging.error(f"Failed to load classifier model: {e}")
                self.model = None
                self.tokenizer = None

    def classify_functions(self, features: Dict[str, float], user_input: str, ai_response: str) -> Dict[str, float]:
        scores = {}
        if self.model and self.tokenizer:
            try:
                inputs = self.tokenizer(user_input, ai_response, truncation=True,
                                        padding=True, max_length=256, return_tensors='pt')
                outputs = self.model(**inputs)
                logits = outputs.logits.detach().numpy().flatten()
                exp_scores = np.exp(logits - np.max(logits))
                probs = exp_scores / exp_scores.sum()
                categories = ["mechanical", "social", "avoidant", "self_referential"]
                scores = {cat: float(prob) for cat, prob in zip(categories, probs)}
                return scores
            except Exception as e:
                logging.error(f"Model prediction failed: {e}")
        scores["mechanical"] = min(1.0, features.get("rhetorical_patterns", 0.0) * 0.7 +
                                        features.get("lexical_diversity", 0.0) * 0.3)
        scores["social"] = min(1.0, features.get("semantic_similarity", 0.0) * 0.4 +
                                    features.get("emotional_intensity", 0.0) * 0.6)
        scores["avoidant"] = min(1.0, features.get("ambiguity_score", 0.0) * 0.5 +
                                      features.get("response_dependency", 0.0) * 0.5)
        matches = sum(len(re.findall(p, ai_response)) for p in self.self_patterns)
        tokens = ai_response.split()
        scores["self_referential"] = min(1.0, matches / max(1, len(tokens)))
        return scores
