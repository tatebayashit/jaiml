# src/model/jaiml_v3_2/core/utils/tokenizer.py
def tokenize(text: str):
    """
    Naive tokenizer: split on whitespace. Replace with proper Japanese tokenizer if available.
    """
    return text.split()

def split_sentences(text: str):
    """
    Split Japanese text into sentences by punctuation.
    """
    import re
    return [s for s in re.split('[。！？]', text) if s]
