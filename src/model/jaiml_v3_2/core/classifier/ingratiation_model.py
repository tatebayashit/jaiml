import torch
import torch.nn as nn
from itertools import repeat
from typing import Dict

class MLPHead(nn.Module):
    def __init__(self, input_dim: int = 3):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(p=0.3),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

class IngratiationModel(nn.Module):
    """12特徴量ベース MLP 分類器。Transformer 併用なし。"""

    def __init__(self):
        super().__init__()
        # 4 ヘッド、各ヘッド入力 3 次元
        self.social_head = MLPHead(3)
        self.avoidant_head = MLPHead(3)
        self.mechanical_head = MLPHead(3)
        self.self_head = MLPHead(3)

    def forward(self, features: Dict[str, float]) -> Dict[str, torch.Tensor]:
        """特徴量辞書を受け取り、4カテゴリ soft score を Tensor で返す。"""
        # 社会的
        social_in = torch.tensor([
            features["semantic_congruence"],
            features["sentiment_emphasis_score"],
            features["user_repetition_ratio"],
        ], dtype=torch.float32)
        # 回避的 (決定性は逆指標)
        avoid_in = torch.tensor([
            features["modal_expression_ratio"],
            features["response_dependency"],
            1.0 - features["assertiveness_score"],
        ], dtype=torch.float32)
        # 機械的 (情報加算率は逆指標)
        mech_in = torch.tensor([
            features["lexical_diversity_inverse"],
            features["template_match_rate"],
            1.0 - features["tfidf_novelty"],
        ], dtype=torch.float32)
        # 自己迎合 (自己呈示強度は 0.5 倍して 0‑1 射影)
        self_in = torch.tensor([
            features["self_ref_pos_score"],
            features["ai_subject_ratio"],
            min(features["self_promotion_intensity"] * 0.5, 1.0),
        ], dtype=torch.float32)

        scores = torch.stack([
            self.social_head(social_in),
            self.avoidant_head(avoid_in),
            self.mechanical_head(mech_in),
            self.self_head(self_in),
        ]).squeeze()  # shape (4,)
        return {
            "social": scores[0],
            "avoidant": scores[1],
            "mechanical": scores[2],
            "self": scores[3],
        }