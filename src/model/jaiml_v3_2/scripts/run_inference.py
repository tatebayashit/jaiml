import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, List

import torch

from core.features.semantic import semantic_congruence
from core.features.lexical import (
    sentiment_emphasis_score,
    user_repetition_ratio,
    response_dependency,
    lexical_diversity_inverse,
    template_match_rate,
    self_ref_pos_score,
    self_promotion_intensity,
)
from core.features.syntactic import (
    modal_expression_ratio,
    assertiveness_score,
    ai_subject_ratio,
)
from core.features.corpus_based import TFIDFNoveltyCalculator
from core.classifier.ingratiation_model import IngratiationModel
from core.utils.metrics import compute_confidence
from lexicons.matcher import LexiconMatcher

# --- 入力検証 -------------------------------------------------------------

def validate(text: str) -> None:
    if text == "":
        raise ValueError("Empty input text")
    if len(text) < 5:
        raise ValueError("Input too short (min 5 chars)")
    if len(text) > 10000:
        raise ValueError("Input too long (max 10000 chars)")

# --- 特徴量抽出 -----------------------------------------------------------

def extract_features(user: str, resp: str, matcher: LexiconMatcher, tfidf_calc: TFIDFNoveltyCalculator) -> Dict[str, float]:
    feats: Dict[str, float] = {
        "semantic_congruence": semantic_congruence(user, resp),
        "sentiment_emphasis_score": sentiment_emphasis_score(resp, matcher),
        "user_repetition_ratio": user_repetition_ratio(user, resp),
        "modal_expression_ratio": modal_expression_ratio(resp, matcher),
        "response_dependency": response_dependency(user, resp),
        "assertiveness_score": assertiveness_score(resp, matcher),
        "lexical_diversity_inverse": lexical_diversity_inverse(resp),
        "template_match_rate": template_match_rate(resp, matcher),
        "tfidf_novelty": tfidf_calc.compute(user, resp),
        "self_ref_pos_score": self_ref_pos_score(resp, matcher),
        "ai_subject_ratio": ai_subject_ratio(resp, matcher),
        "self_promotion_intensity": self_promotion_intensity(resp, matcher),
    }
    return feats

# --- 主カテゴリ決定 -------------------------------------------------------

_PRIORITIES: List[str] = ["self", "social", "avoidant", "mechanical"]

def decide_category(scores: Dict[str, float]) -> str:
    top, second = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:2]
    if abs(top[1] - second[1]) < 0.1:
        # 差が小さい場合は優先順位ルール
        ordered = sorted(scores.items(), key=lambda x: (_PRIORITIES.index(x[0]), -x[1]))
        return ordered[0][0]
    return top[0]

# --- 推論処理 -------------------------------------------------------------

def inference_pair(user: str, resp: str, matcher: LexiconMatcher, model: IngratiationModel, tfidf_calc: TFIDFNoveltyCalculator) -> Dict[str, Any]:
    validate(user)
    validate(resp)
    start = time.perf_counter()

    # 特徴量
    feats = extract_features(user, resp, matcher, tfidf_calc)

    # MCDropout 20回
    model.train()  # Dropout 有効
    samples = []
    for _ in range(20):
        out = model(feats)
        samples.append(torch.tensor([out["social"], out["avoidant"], out["mechanical"], out["self"]]))
    score_samples = torch.stack(samples)  # shape (20,4)
    confidence = compute_confidence(score_samples)
    # 平均を最終スコアとする
    mean_scores = torch.mean(score_samples, dim=0)
    scores = {
        "social": float(mean_scores[0]),
        "avoidant": float(mean_scores[1]),
        "mechanical": float(mean_scores[2]),
        "self": float(mean_scores[3]),
    }
    idx = sum(scores.values()) / 4.0
    cat = decide_category(scores)

    elapsed = (time.perf_counter() - start) * 1000.0
    meta = {
        "token_length": len(resp),  # 文字数を簡易トークン長とする。
        "confidence": confidence,
        "processing_time_ms": int(elapsed),
    }

    return {
        "input": {"user": user, "response": resp},
        "scores": scores,
        "index": idx,
        "predicted_category": cat,
        "features": feats,
        "meta": meta,
    }

# --- バッチ処理 -----------------------------------------------------------

def process_file(input_path: Path, output_path: Path, matcher: LexiconMatcher, model: IngratiationModel, tfidf_calc: TFIDFNoveltyCalculator) -> None:
    with input_path.open("r", encoding="utf-8") as fin, output_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            record = json.loads(line)
            result = inference_pair(record["user"], record["response"], matcher, model, tfidf_calc)
            fout.write(json.dumps(result, ensure_ascii=False) + "\n")

# --- エントリポイント -----------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="JAIML v3.2 inference (SRS compliant)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input", type=str, help="Input JSONL path")
    mode.add_argument("--user", type=str, help="Single user utterance")
    parser.add_argument("--response", type=str, help="Single AI response (needed with --user)")
    parser.add_argument("--output", type=str, help="Output JSON path (batch mode)")
    parser.add_argument("--lexicon", type=str, default="lexicons/jaiml_lexicons.yaml")
    args = parser.parse_args()

    matcher = LexiconMatcher(args.lexicon)
    model = IngratiationModel()
    tfidf_calc = TFIDFNoveltyCalculator()

    if args.input:
        if not args.output:
            parser.error("--output is required when --input is specified")
        process_file(Path(args.input), Path(args.output), matcher, model, tfidf_calc)
    else:
        if args.response is None:
            parser.error("--response is required when --user is specified")
        result = inference_pair(args.user, args.response, matcher, model, tfidf_calc)
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()