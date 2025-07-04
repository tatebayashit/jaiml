# src/model/jaiml_v3_3/core/utils/tokenize.py
from fugashi import Tagger
import re
from typing import List

# fugashiタガーのグローバルインスタンス
_tagger = None

def get_fugashi_tagger() -> Tagger:
    """fugashiタガーのシングルトンインスタンスを返す。
    
    Returns:
        Tagger: 形態素解析器インスタンス
    """
    global _tagger
    if _tagger is None:
        _tagger = Tagger()
    return _tagger

def mecab_tokenize(text: str) -> List[str]:
    """fugashiによる日本語形態素解析を行い、表層形のリストを返す。
    
    Args:
        text: 入力テキスト
        
    Returns:
        List[str]: 形態素のリスト
    """
    if not text:
        return []
    
    tagger = get_fugashi_tagger()
    tokens = []
    
    for word in tagger(text):
        if word.surface:  # 空文字をスキップ
            tokens.append(word.surface)
    
    return tokens

def mecab_tokenize_with_pos(text: str) -> List[tuple]:
    """品詞情報付きで形態素解析を行う。
    
    Args:
        text: 入力テキスト
        
    Returns:
        List[tuple]: (表層形, 品詞)のタプルリスト
    """
    if not text:
        return []
    
    tagger = get_fugashi_tagger()
    tokens_with_pos = []
    
    for word in tagger(text):
        if word.surface:  # 空文字をスキップ
            features = word.pos.split(',')
            pos = features[0]  # 品詞（第1要素）
            tokens_with_pos.append((word.surface, pos))
    
    return tokens_with_pos

def extract_content_words(text: str) -> List[str]:
    """内容語（名詞・動詞・形容詞）のみを抽出する。
    
    Args:
        text: 入力テキスト
        
    Returns:
        List[str]: 内容語のリスト
    """
    tokens_with_pos = mecab_tokenize_with_pos(text)
    content_pos = {'名詞', '動詞', '形容詞'}
    
    content_words = []
    for surface, pos in tokens_with_pos:
        if pos in content_pos:
            content_words.append(surface)
    
    return content_words

def split_sentences(text: str) -> List[str]:
    """日本語テキストを句点で文に分割する。
    
    Args:
        text: 入力テキスト
        
    Returns:
        List[str]: 文のリスト
    """
    return [s for s in re.split('[。！？]', text) if s]

# 既存関数との互換性維持
def tokenize(text: str) -> List[str]:
    """fugashiによる形態素解析を行う（既存インターフェース互換）。
    
    Args:
        text: 入力テキスト
        
    Returns:
        List[str]: 形態素のリスト
    """
    return mecab_tokenize(text)