# src/model/jaiml_v3_2/tests/test_features.py
import unittest
from lexicons.matcher import LexiconMatcher
from core.features.lexical import sentiment_emphasis_score, user_repetition_ratio, lexical_diversity_inverse, template_match_rate, self_ref_pos_score, self_promotion_intensity, response_dependency
from core.features.syntactic import modal_expression_ratio, assertiveness_score, ai_subject_ratio
from core.utils.tokenize import mecab_tokenize, extract_content_words

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.matcher = LexiconMatcher("lexicons/jaiml_lexicons.yaml")

    def test_lexicon_matcher(self):
        text = "私はすばらしい実績を達成した。"
        matches = self.matcher.match(text)
        # '達成する' is an achievement verb; 'すばらしい' is in evaluative adjectives
        self.assertIn("達成する", matches.get("achievement_verbs", []))
        self.assertIn("すばらしい", matches.get("evaluative_adjectives", []))

    def test_mecab_tokenize(self):
        """MeCabトークナイザの動作確認"""
        text = "今日は良い天気です。"
        tokens = mecab_tokenize(text)
        # 形態素に分割されていることを確認
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        # '今日', 'は', '良い', '天気', 'です', '。' などが含まれる
        self.assertIn("今日", tokens)
        self.assertIn("天気", tokens)

    def test_extract_content_words(self):
        """内容語抽出の動作確認"""
        text = "今日は良い天気です。"
        content_words = extract_content_words(text)
        # 名詞・形容詞が抽出される
        self.assertIn("今日", content_words)
        self.assertIn("天気", content_words)
        self.assertIn("良い", content_words)
        # 助詞・助動詞は含まれない
        self.assertNotIn("は", content_words)
        self.assertNotIn("です", content_words)

    def test_user_repetition_ratio_morpheme_based(self):
        """形態素ベースのJaccard係数テスト"""
        user = "今日は良い天気ですね"
        resp = "はい、今日は本当に良い天気です"
        ratio = user_repetition_ratio(user, resp)
        # 共通語彙：今日、は、良い、天気、です
        self.assertGreater(ratio, 0.5)
        self.assertLess(ratio, 1.0)

    def test_response_dependency_content_words(self):
        """内容語ベースの応答依存度テスト"""
        user = "最新のAI技術について教えて"
        resp = "AI技術は急速に発展しています"
        dep = response_dependency(user, resp)
        # 共通内容語：AI、技術
        self.assertGreater(dep, 0.0)
        self.assertLess(dep, 1.0)

    def test_lexical_diversity_morpheme_based(self):
        """形態素ベースの語彙多様性テスト"""
        resp = "素晴らしい素晴らしい本当に素晴らしい成果です"
        diversity_inv = lexical_diversity_inverse(resp)
        # 重複が多いため多様性逆数は高い
        self.assertGreater(diversity_inv, 0.5)

    def test_template_match(self):
        resp = "はい、ご質問ありがとうございます。"
        rate = template_match_rate(resp, self.matcher)
        self.assertGreater(rate, 0.0)

    def test_sentiment_emphasis(self):
        resp = "本当に素晴らしい。心から感謝します。"
        score = sentiment_emphasis_score(resp, self.matcher)
        self.assertTrue(score > 0)

    def test_sentiment_emphasis_normalization(self):
        """sentiment_emphasis_scoreの正規化確認"""
        resp = "本当に素晴らしい。非常に優秀で、とても感動しました。"
        score = sentiment_emphasis_score(resp, self.matcher)
        # スコアは0-3の範囲内
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 3.0)

    def test_modal_assertiveness(self):
        resp = "それはそうかもしれません。わかりませんが…。"
        mod = modal_expression_ratio(resp, self.matcher)
        ass = assertiveness_score(resp, self.matcher)
        self.assertTrue(mod > 0)
        self.assertTrue(ass < 1.0)

    def test_ai_subject(self):
        resp = "私は頑張ります。"
        ratio = ai_subject_ratio(resp, self.matcher)
        self.assertEqual(ratio, 1.0)

if __name__ == "__main__":
    unittest.main()