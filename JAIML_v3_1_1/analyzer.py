
import torch
import numpy as np
import MeCab
import CaboCha
from transformers import AutoTokenizer, AutoModel
import logging

logger = logging.getLogger(__name__)

class LinguisticAnalyzer:
    def __init__(self, model_name: str = 'pkshatech/simcse-ja-bert-base-clcmlp'):
        try:
            self.mecab = MeCab.Tagger('-Owakati')
            self.cabocha = CaboCha.Parser()
            self.bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.bert_model = AutoModel.from_pretrained(model_name)
        except Exception as e:
            logger.error(f"言語解析器の初期化失敗: {e}")
            raise

    def tokenize(self, text: str):
        try:
            parsed = self.mecab.parse(text).strip()
            return parsed.split()
        except Exception as e:
            logger.warning(f"トークン化失敗: {e}")
            return text.split()

    def get_sentence_embedding(self, text: str) -> np.ndarray:
        try:
            inputs = self.bert_tokenizer(text, return_tensors='pt',
                                         truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
            cls_vector = outputs.last_hidden_state[0][0].numpy()
            return cls_vector
        except Exception as e:
            logger.warning(f"文脈ベクトル取得失敗: {e}")
            return np.zeros(768)

    def parse_syntax_tree(self, text: str) -> str:
        try:
            tree = self.cabocha.parse(text)
            return tree.toString(CaboCha.FORMAT_TREE)
        except Exception as e:
            logger.warning(f"構文解析失敗: {e}")
            return ""
