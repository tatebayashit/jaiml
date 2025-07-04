# src/model/jaiml_v3_2/core/features/semantic.py
from sentence_transformers import SentenceTransformer, util

# Sentence-BERTモデルの初期化
_model = SentenceTransformer('pkshatech/simcse-ja-bert-base-clcmlp')

def semantic_congruence(user_text: str, response_text: str) -> float:
    """
    ユーザー発話とAI応答の意味的類似度を算出する。
    SimCSE埋め込みのコサイン類似度を[0.0, 1.0]に正規化して返す。
    """
    if not user_text or not response_text:
        return 0.0
    # 文埋め込みの取得
    user_emb = _model.encode(user_text, convert_to_tensor=True)
    resp_emb = _model.encode(response_text, convert_to_tensor=True)
    score = util.cos_sim(user_emb, resp_emb).item()
    # [-1,1]から[0,1]への正規化
    score = max(score, -1.0)
    norm_score = (score + 1.0) / 2.0
    return float(norm_score)

# tfidf_novelty は意味的特徴ではなく語彙的特徴であるため、
# semantic.py からは削除し、run_inference.py で直接 corpus_based.py を使用する構成とする