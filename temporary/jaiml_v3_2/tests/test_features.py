# src/model/jaiml_v3_2/tests/test_features.py
import unittest
from lexicons.matcher import LexiconMatcher
from core.features.lexical import sentiment_emphasis_score, user_repetition_ratio, lexical_diversity_inverse, template_match_rate, self_ref_pos_score, self_promotion_intensity
from core.features.syntactic import modal_expression_ratio, assertiveness_score, ai_subject_ratio

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.matcher = LexiconMatcher("lexicons/jaiml_lexicons.yaml")

    def test_lexicon_matcher(self):
        text = "私はすばらしい実績を達成した。"
        matches = self.matcher.match(text)
        # '達成する' is an achievement verb; 'すばらしい' is in evaluative adjectives
        self.assertIn("達成する", matches.get("achievement_verbs", []))
        self.assertIn("すばらしい", matches.get("evaluative_adjectives", []))

    def test_user_repetition_ratio(self):
        user = "こんにちは"
        resp = "こんにちは"
        self.assertAlmostEqual(user_repetition_ratio(user, resp), 1.0)

    def test_template_match(self):
        resp = "はい、ご質問ありがとうございます。"
        rate = template_match_rate(resp, self.matcher)
        self.assertGreater(rate, 0.0)

    def test_sentiment_emphasis(self):
        resp = "本当に素晴らしい。心から感謝します。"
        score = sentiment_emphasis_score(resp, self.matcher)
        self.assertTrue(score > 0)

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
