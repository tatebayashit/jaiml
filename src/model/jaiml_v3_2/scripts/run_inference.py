import argparse
import json
from pathlib import Path

from lexicons.matcher import LexiconMatcher
from core.features.semantic import semantic_congruence, tfidf_novelty
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
from core.classifier.ingratiation_model import IngratiationModel, compute_main_category


def build_features(user: str, response: str, matcher: LexiconMatcher) -> dict:
    """Extract 12 JAIML features from user/response pair."""
    feats = {
        "semantic_congruence": semantic_congruence(user, response),
        "sentiment_emphasis_score": sentiment_emphasis_score(response, matcher),
        "user_repetition_ratio": user_repetition_ratio(user, response),
        "modal_expression_ratio": modal_expression_ratio(response, matcher),
        "response_dependency": response_dependency(user, response),
        "assertiveness_score": assertiveness_score(response, matcher),
        "lexical_diversity_inverse": lexical_diversity_inverse(response),
        "template_match_rate": template_match_rate(response, matcher),
        "tfidf_novelty": tfidf_novelty(response),
        "self_ref_pos_score": self_ref_pos_score(response, matcher),
        "ai_subject_ratio": ai_subject_ratio(response, matcher),
        "self_promotion_intensity": self_promotion_intensity(response, matcher),
    }
    return feats


def compute_ingratiation(user: str, response: str, matcher: LexiconMatcher, model: IngratiationModel) -> dict:
    """Return ingratiation scores and index for a single utterance pair."""
    features = build_features(user, response, matcher)
    scores = model.forward(user, response, features)
    main_cat = compute_main_category(scores)
    ingr_index = sum(scores.values()) / 4.0
    return {
        "user": user,
        "response": response,
        "scores": scores,
        "main_category": main_cat,
        "ingratiation_index": ingr_index,
    }


def process_file(input_path: Path, output_path: Path, matcher: LexiconMatcher, model: IngratiationModel) -> None:
    """Read JSONL input, write JSONL output with one result per line."""
    with input_path.open("r", encoding="utf-8") as f_in, output_path.open(
        "w", encoding="utf-8"
    ) as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            user = record.get("user", "")
            response = record.get("response", "")
            result = compute_ingratiation(user, response, matcher, model)
            f_out.write(json.dumps(result, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="JAIML Ingratiation Detection (batch mode)")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--input", type=str, help="Path to input JSONL file")
    mode_group.add_argument("--user", type=str, help="Single user utterance")
    parser.add_argument("--response", type=str, help="Single AI response (required if --user)")
    parser.add_argument("--output", type=str, help="Path to output JSON file (batch mode)")
    parser.add_argument(
        "--lexicon",
        type=str,
        default="lexicons/jaiml_lexicons.yaml",
        help="Path to lexicon YAML",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="cl-tohoku/bert-base-japanese",
        help="Transformer model name",
    )
    args = parser.parse_args()

    # Instantiate shared objects
    matcher = LexiconMatcher(args.lexicon)
    model = IngratiationModel(args.model)

    if args.input:
        if not args.output:
            parser.error("--output is required when --input is specified")
        input_path = Path(args.input)
        output_path = Path(args.output)
        process_file(input_path, output_path, matcher, model)
    else:
        if args.response is None:
            parser.error("--response is required when --user is specified")
        result = compute_ingratiation(args.user, args.response, matcher, model)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
