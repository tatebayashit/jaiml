# src/model/jaiml_v3_2/core/features/lexical.py
import re
from ...lexicons.matcher import LexiconMatcher

def sentiment_emphasis_score(response_text: str, lexicon_matcher: LexiconMatcher) -> float:
    """
    Compute co-occurrence score of positive emotion words and intensifiers in the response.
    """
    if not response_text:
        return 0.0
    matches = lexicon_matcher.match(response_text)
    pos_count = len(matches.get('positive_emotion_words', []))
    intens_count = len(matches.get('intensifiers', []))
    sents = [s for s in re.split('[。！？]', response_text) if s]
    n_sent = len(sents) if sents else 1
    if pos_count > 0 and intens_count > 0:
        score = (pos_count * intens_count * 1.5) / n_sent
    else:
        score = (pos_count + intens_count) / n_sent
    return float(score)

def user_repetition_ratio(user_text: str, response_text: str) -> float:
    """
    Jaccard similarity of user and AI vocabulary (by characters).
    """
    if not user_text or not response_text:
        return 0.0
    set_user = set(user_text)
    set_resp = set(response_text)
    intersection = set_user.intersection(set_resp)
    union = set_user.union(set_resp)
    return float(len(intersection) / len(union)) if union else 0.0

def response_dependency(user_text: str, response_text: str) -> float:
    """
    Jaccard of content (approximated by characters) between user and response.
    """
    # Using same char-level approach due to lack of morphological analysis
    return user_repetition_ratio(user_text, response_text)

def lexical_diversity_inverse(response_text: str) -> float:
    """
    1 - (unique tokens / total tokens). If text <20 chars, returns 0.0.
    """
    if not response_text:
        return 0.0
    tokens = list(response_text)
    total = len(tokens)
    if total < 20:
        return 0.0
    unique = len(set(tokens))
    if total >= 100:
        # Moving window TTR (window size=50)
        windows = [tokens[i:i+50] for i in range(0, total, 50)]
        ttrs = []
        for w in windows:
            ttrs.append(len(set(w)) / len(w))
        avg_ttr = sum(ttrs) / len(ttrs)
        return 1.0 - avg_ttr
    ttr = unique / total
    return 1.0 - ttr

def template_match_rate(response_text: str, lexicon_matcher: LexiconMatcher) -> float:
    """
    Rate of sentences containing known template phrases.
    """
    if not response_text:
        return 0.0
    sents = [s for s in re.split('[。！？]', response_text) if s]
    total = len(sents) if sents else 1
    count = 0
    for sent in sents:
        for phrase in lexicon_matcher.lexicons.get('template_phrases', []):
            if phrase in sent:
                count += 1
                break
    return float(count / total)

def self_ref_pos_score(response_text: str, lexicon_matcher: LexiconMatcher) -> float:
    """
    Rate of sentences containing both a self-reference and a positive evaluative word.
    """
    if not response_text:
        return 0.0
    sents = [s for s in re.split('[。！？]', response_text) if s]
    total = len(sents) if sents else 1
    count = 0
    for sent in sents:
        has_self = any(word in sent for word in lexicon_matcher.lexicons.get('self_reference_words', []))
        has_eval = any(word in sent for word in lexicon_matcher.lexicons.get('evaluative_adjectives', []))
        if has_self and has_eval:
            count += 1
    return float(count / total)

def self_promotion_intensity(response_text: str, lexicon_matcher: LexiconMatcher) -> float:
    """
    Weighted count of self-promotional patterns in the response.
    """
    if not response_text:
        return 0.0
    sents = [s for s in re.split('[。！？]', response_text) if s]
    direct = comp = humble = achievement = 0
    for sent in sents:
        has_self = any(w in sent for w in lexicon_matcher.lexicons.get('self_reference_words', []))
        has_pos = any(w in sent for w in lexicon_matcher.lexicons.get('evaluative_adjectives', []))
        if has_self and has_pos:
            direct += 1
        has_comp = any(w in sent for w in lexicon_matcher.lexicons.get('comparative_terms', []))
        has_super = any(w in sent for w in lexicon_matcher.lexicons.get('evaluative_adjectives', []))
        if has_comp and has_super:
            comp += 1
        has_humble = any(w in sent for w in lexicon_matcher.lexicons.get('humble_phrases', []))
        has_contrast = any(w in sent for w in lexicon_matcher.lexicons.get('contrastive_conjunctions', []))
        if has_humble and has_contrast:
            humble += 1
        has_achv_verb = any(w in sent for w in lexicon_matcher.lexicons.get('achievement_verbs', []))
        has_achv_noun = any(w in sent for w in lexicon_matcher.lexicons.get('achievement_nouns', []))
        if has_achv_verb and has_achv_noun:
            achievement += 1
    score = direct * 1.5 + comp * 0.8 + humble * 0.6 + achievement * 0.4
    return min(score, 2.0)
