# src/model/jaiml_v3_2/core/features/lexical.py
import re
from typing import Set
import fugashi
from lexicons.matcher import LexiconMatcher
from core.utils.tokenize import mecab_tokenize

# 形態素解析器の初期化（モジュールレベルで一度だけ）
_tagger = fugashi.Tagger()

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
    文字レベルのJaccard類似度を算出する（既存実装を維持）。
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
    内容語（名詞・動詞・形容詞）に限定したJaccard類似度を算出する。
    
    Args:
        user_text: ユーザー発話テキスト
        response_text: AI応答テキスト
    
    Returns:
        float: 内容語ベースのJaccard係数 [0.0, 1.0]
    """
    if not user_text or not response_text:
        return 0.0
    
    def extract_content_words(text: str) -> Set[str]:
        """内容語（名詞・動詞・形容詞）を抽出する。"""
        content_words = set()
        # fugashiによる形態素解析
        for word in _tagger(text):
            pos = word.pos.split(',')[0]  # 品詞の大分類
            # 名詞・動詞・形容詞を内容語とする
            if pos in ['名詞', '動詞', '形容詞']:
                # 表層形を使用（基本形でも可）
                content_words.add(word.surface)
        return content_words
    
    # 内容語集合の抽出
    user_content = extract_content_words(user_text)
    resp_content = extract_content_words(response_text)
    
    # 空集合の場合の処理
    if not user_content and not resp_content:
        return 0.0
    
    # Jaccard係数の算出
    intersection = user_content.intersection(resp_content)
    union = user_content.union(resp_content)
    
    return float(len(intersection) / len(union)) if union else 0.0

def lexical_diversity_inverse(response_text: str) -> float:
    """
    1 - (unique tokens / total tokens). If text <20 chars, returns 0.0.
    形態素解析による語彙多様性の逆数を計算する。
    """
    if not response_text:
        return 0.0
    
    # 文字数での前処理は維持
    if len(response_text) < 20:
        return 0.0
    
    # MeCabによる形態素解析
    tokens = mecab_tokenize(response_text)
    total = len(tokens)
    
    if total == 0:
        return 0.0
    
    unique = len(set(tokens))
    
    if total >= 100:
        # Moving window TTR (window size=50)
        windows = [tokens[i:i+50] for i in range(0, total, 50)]
        ttrs = []
        for w in windows:
            if len(w) > 0:
                ttrs.append(len(set(w)) / len(w))
        if ttrs:
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