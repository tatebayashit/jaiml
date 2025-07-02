
import json
from pathlib import Path
from typing import Dict

class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)

    def _load_config(self, path: str) -> Dict:
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
            ),
            "pretrained_classifier": ""
        }
        if Path(path).exists():
            with open(path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        return default_config
