# src/model/jaiml_v3_2/scripts/run_inference.py
import argparse
import json
from lexicons.matcher import LexiconMatcher
from core.features.semantic import semantic_congruence, tfidf_novelty
from core.features.lexical import sentiment_emphasis_score, user_repetition_ratio, response_dependency
from core.features.lexical import lexical_diversity_inverse, template_match_rate, self_ref_pos_score, self_promotion_intensity
from core.features.syntactic import modal_expression_ratio, assertiveness_score, ai_subject_ratio
from core.classifier.ingratiation_model import IngratiationModel, compute_main_category

def main():
    parser = argparse.ArgumentParser(description="JAIML Ingratiation Detection")
    parser.add_argument("--user", type=str, required=True, help="User utterance")
    parser.add_argument("--response", type=str, required=True, help="AI response")
    parser.add_argument("--lexicon", type=str, default="lexicons/jaiml_lexicons.yaml", help="Path to lexicon YAML")
    parser.add_argument("--model", type=str, default="cl-tohoku/bert-base-japanese", help="Transformer model name")
    args = parser.parse_args()

    # Initialize lexicon matcher
    matcher = LexiconMatcher(args.lexicon)

    # Extract features
    features = {}
    features['semantic_congruence'] = semantic_congruence(args.user, args.response)
    features['sentiment_emphasis_score'] = sentiment_emphasis_score(args.response, matcher)
    features['user_repetition_ratio'] = user_repetition_ratio(args.user, args.response)
    features['modal_expression_ratio'] = modal_expression_ratio(args.response, matcher)
    features['response_dependency'] = response_dependency(args.user, args.response)
    features['assertiveness_score'] = assertiveness_score(args.response, matcher)
    features['lexical_diversity_inverse'] = lexical_diversity_inverse(args.response)
    features['template_match_rate'] = template_match_rate(args.response, matcher)
    features['tfidf_novelty'] = tfidf_novelty(args.response)
    features['self_ref_pos_score'] = self_ref_pos_score(args.response, matcher)
    features['ai_subject_ratio'] = ai_subject_ratio(args.response, matcher)
    features['self_promotion_intensity'] = self_promotion_intensity(args.response, matcher)

    # Initialize classifier
    model = IngratiationModel(args.model)
    scores = model.forward(args.user, args.response, features)
    main = compute_main_category(scores)
    ingr_index = (scores['social'] + scores['avoidant'] + scores['mechanical'] + scores['self']) / 4.0
    output = {
        'scores': scores,
        'main_category': main,
        'ingratiation_index': ingr_index
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
