import torch
import torch.nn.functional as F

__all__ = [
    "compute_confidence",
]

def compute_confidence(score_samples: torch.Tensor) -> float:
    """MCDropout サンプリング結果 (N×4) から信頼度を算出する。

    Args:
        score_samples: torch.Tensor, shape (N, 4), 各列は social, avoidant, mechanical, self の soft score。

    Returns:
        float: Confidence ∈ [0,1]  (1 − 平均分散)。
    """
    # 分散 (列ごと) → 平均
    variance = torch.var(score_samples, dim=0, unbiased=False)
    mean_var = torch.mean(variance).item()
    confidence = max(0.0, 1.0 - mean_var)
    return confidence