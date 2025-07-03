# src/model/jaiml_v3_2/core/features/corpus_based.py
from typing import List, Callable
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from core.utils.tokenize import mecab_tokenize

__all__ = [
    "TFIDFNoveltyCalculator",
]

class TFIDFNoveltyCalculator:
    """TF-IDF に基づく情報加算率 (tfidf_novelty) を計算する簡易実装。

    - 上位 20% TF-IDF 単語を "新規情報" とみなす。
    - ユーザー発話と AI 応答のペアをコーパスとし、その TF-IDF を用いる（外部大規模コーパスがない前提）。
    - 実運用では対話コーパスで vectorizer を事前学習させ、transform のみ行う想定。
    """

    def __init__(self):
        # MeCabトークナイザを使用
        self.vectorizer = TfidfVectorizer(
            tokenizer=self._mecab_tokenize,
            token_pattern=None,  # tokenizerを使用する場合は無効化
            min_df=1,
            max_df=0.9
        )
    
    def _mecab_tokenize(self, text: str) -> List[str]:
        """TfidfVectorizer用のトークナイザ関数。
        
        Args:
            text: 入力テキスト
            
        Returns:
            List[str]: 形態素のリスト
        """
        return mecab_tokenize(text)

    def compute(self, user_text: str, response_text: str) -> float:
        """情報加算率を算出する。

        Returns:
            float: 値域 [0,1]。高値 = 新規情報が多い。
        """
        # コーパスを構築
        corpus: List[str] = [user_text, response_text]
        tfidf_matrix = self.vectorizer.fit_transform(corpus)
        # 行0: user, 行1: response
        response_vec = tfidf_matrix[1].toarray()[0]
        user_vec = tfidf_matrix[0].toarray()[0]
        # 上位20%インデックス
        non_zero_idx = response_vec.nonzero()[0]
        if len(non_zero_idx) == 0:
            return 0.0
        top_k = max(1, int(len(non_zero_idx) * 0.2))
        top_indices = response_vec.argsort()[::-1][:top_k]
        # top 単語のうち user に存在しない単語割合
        novel_mask = (user_vec[top_indices] == 0).astype(float)
        novelty_ratio = float(novel_mask.sum() / top_k)
        return novelty_ratio