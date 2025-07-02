
from dataclasses import dataclass
from typing import Dict

@dataclass
class IngrationResult:
    total_score: float
    function_scores: Dict[str, float]
    confidence: float
    feature_weights: Dict[str, float]
    style_consistency: float = 0.5
