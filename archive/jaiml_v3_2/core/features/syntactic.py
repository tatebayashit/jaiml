# src/model/jaiml_v3_2/core/features/syntactic.py
import re

def modal_expression_ratio(response_text: str, lexicon_matcher) -> float:
    """
    Rate of sentences containing modal/hesitation expressions.
    """
    if not response_text:
        return 0.0
    sents = [s for s in re.split('[。！？]', response_text) if s]
    total = len(sents) if sents else 1
    count = 0
    for sent in sents:
        for modal in lexicon_matcher.lexicons.get('modal_expressions', []):
            if modal in sent:
                count += 1
                break
    return float(count / total)

def assertiveness_score(response_text: str, lexicon_matcher) -> float:
    """
    Ratio of assertive sentences (no modal expressions).
    """
    if not response_text:
        return 0.0
    sents = [s for s in re.split('[。！？]', response_text) if s]
    total = len(sents) if sents else 1
    count = 0
    for sent in sents:
        # If no modal expression found in sentence
        found = False
        for modal in lexicon_matcher.lexicons.get('modal_expressions', []):
            if modal in sent:
                found = True
                break
        if not found:
            count += 1
    return float(count / total)

def ai_subject_ratio(response_text: str, lexicon_matcher) -> float:
    """
    Ratio of sentences where the subject refers to the AI (self).
    """
    if not response_text:
        return 0.0
    sents = [s for s in re.split('[。！？]', response_text) if s]
    total = len(sents) if sents else 1
    count = 0
    for sent in sents:
        if any(w in sent for w in lexicon_matcher.lexicons.get('self_reference_words', [])):
            count += 1
    return float(count / total)
