# src/model/jaiml_v3_2/core/features/semantic.py
from sentence_transformers import SentenceTransformer, util

# Load Japanese SimCSE model (Sentence-BERT) for semantic similarity
_model = SentenceTransformer('pkshatech/simcse-ja-bert-base-clcmlp')

def semantic_congruence(user_text: str, response_text: str) -> float:
    """
    Compute semantic congruence between user utterance and AI response using SimCSE embeddings.
    Returns cosine similarity normalized to [0.0, 1.0].
    """
    if not user_text or not response_text:
        return 0.0
    # Encode sentences
    user_emb = _model.encode(user_text, convert_to_tensor=True)
    resp_emb = _model.encode(response_text, convert_to_tensor=True)
    score = util.cos_sim(user_emb, resp_emb).item()
    # Normalize cosine [-1,1] to [0,1]
    score = max(score, -1.0)
    norm_score = (score + 1.0) / 2.0
    return float(norm_score)

def tfidf_novelty(response_text: str) -> float:
    """
    Compute information novelty of response using TF-IDF.
    Returns proportion of high-IDF words (top 20%) in the response.
    Placeholder implementation returning 0.0.
    """
    # TODO: Implement with a corpus IDF. For now, return 0.0.
    return 0.0
