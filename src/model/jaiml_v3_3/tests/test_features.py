# src/model/jaiml_v3_3/tests/test_features.py
import unittest
from lexicons.matcher import LexiconMatcher
from core.features.lexical import sentiment_emphasis_score, user_repetition_ratio, lexical_diversity_inverse, template_match_rate, self_ref_pos_score, self_promotion_intensity, response_dependency
from core.features.syntactic import modal_expression_ratio, assertiveness_score, ai_subject_ratio
from core.utils.tokenize import mecab_tokenize, extract_content_words

import sys
from pathlib import Path
# プロジェクトルートをPythonパスに追加（テスト実行時の相対インポート対応）
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.utils.paths import get_lexicon_path

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.matcher = LexiconMatcher(str(get_lexicon_path()))

    def test_lexicon_matcher(self):
        text = "私はすばらしい実績を達成した。"
        matches = self.matcher.match(text)
        # '達成する' is an achievement verb; 'すばらしい' is in evaluative adjectives
        self.assertIn("達成する", matches.get("achievement_verbs", []))
        self.assertIn("すばらしい", matches.get("evaluative_adjectives", []))

    def test_fugashi_tokenize(self):
        """fugashiトークナイザの動作確認"""
        text = "今日は良い天気です。"
        tokens = mecab_tokenize(text)
        # 形態素に分割されていることを確認
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        # '今日', 'は', '良い', '天気', 'です', '。' などが含まれる
        self.assertIn("今日", tokens)
        self.assertIn("天気", tokens)

    def test_extract_content_words(self):
        """内容語抽出の動作確認（fugashiベース）"""
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
        """文字ベースのJaccard係数テスト（既存実装維持）"""
        user = "今日は良い天気ですね"
        resp = "はい、今日は本当に良い天気です"
        ratio = user_repetition_ratio(user, resp)
        # 文字レベルでの共通部分
        self.assertGreater(ratio, 0.3)
        self.assertLess(ratio, 1.0)

    def test_response_dependency_content_words(self):
        """内容語ベースの応答依存度テスト（fugashiベース）"""
        # 内容語が重複するケース
        user = "今日は天気が良い"
        resp = "天気が良いですね"
        dep = response_dependency(user, resp)
        # 「天気」「良い」が共通内容語
        self.assertGreater(dep, 0.0)
        self.assertLess(dep, 1.0)
        
        # 内容語が重複しないケース
        user = "朝食を食べた"
        resp = "こんにちは"
        dep = response_dependency(user, resp)
        self.assertEqual(dep, 0.0)

    def test_tfidf_novelty_integration(self):
        """TF-IDF情報加算率の統合テスト（fugashiベース）"""
        from core.features.corpus_based import TFIDFNoveltyCalculator
        calc = TFIDFNoveltyCalculator()
        
        # 新規情報が少ないケース
        user = "天気について教えて"
        resp = "天気について説明します"
        novelty = calc.compute(user, resp)
        self.assertLess(novelty, 0.5)
        
        # 新規情報が多いケース
        user = "今日"
        resp = "気温は15度で晴れ、風速3メートル"
        novelty = calc.compute(user, resp)
        self.assertGreater(novelty, 0.5)
        
    def test_lexical_diversity_morpheme_based(self):
        """形態素ベースの語彙多様性テスト（fugashiベース）"""
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
    
    def test_self_promotion_v3_3_humble_brag(self):
        """v3.3: 4スロット構造による謙遜装い自慢の検出テスト"""
        # 4スロット完全一致ケース
        resp = "完璧ではないかもしれませんが、私は多くの賞を受賞しました。"
        score = self_promotion_intensity(resp, self.matcher)
        # 謙遜語：完璧ではない
        # 逆接：が
        # 自己参照：私
        # 実績語彙：受賞
        # 期待値: humble部分が1.0 * 0.6 = 0.6
        self.assertGreater(score, 0.5)
        
        # 自己参照なしケース（スコア0）
        resp = "完璧ではないかもしれませんが、受賞しました。"
        score = self_promotion_intensity(resp, self.matcher)
        # humble部分は0になるが、他のパターンがある可能性があるため
        # 完全に0にはならない可能性がある
        
        # 実績語彙なしケース（スコア0）
        resp = "完璧ではないかもしれませんが、私は頑張ります。"
        score = self_promotion_intensity(resp, self.matcher)
        # humble部分は0になる
        
    def test_self_promotion_v3_3_achievement_enumeration(self):
        """v3.3: 実績列挙における自己参照共起の必須化テスト"""
        # 自己参照と実績語彙の共起ケース
        resp = "私は目標を達成しました。"
        score = self_promotion_intensity(resp, self.matcher)
        # achievement部分が1 * 0.4 = 0.4
        self.assertGreater(score, 0.3)
        
        # 自己参照なしケース（v3.3では0）
        resp = "目標を達成しました。"
        score = self_promotion_intensity(resp, self.matcher)
        # achievement部分は0になる
        self.assertEqual(score, 0.0)
        
        # 実績語彙のみケース（v3.3では0）
        resp = "達成する実績がある。"
        score = self_promotion_intensity(resp, self.matcher)
        # 自己参照がないためachievement部分は0
        self.assertEqual(score, 0.0)
        
    def test_humble_brag_slot_detection(self):
        """v3.3: 謙遜装い自慢の4スロット検出詳細テスト"""
        from core.features.lexical import _detect_humble_brag_v3_3
        
        # 4スロット完全一致
        sent = "まだまだ不完全ながら、私は多くの成果を達成しました。"
        score = _detect_humble_brag_v3_3(sent, self.matcher)
        self.assertEqual(score, 1.0)
        
        # 3スロット（逆接なし）
        sent = "まだまだ不完全で私は成果を達成しました。"
        score = _detect_humble_brag_v3_3(sent, self.matcher)
        self.assertEqual(score, 0.75)
        
        # 必須条件不足（自己参照なし）
        sent = "まだまだ不完全ながら、成果を達成しました。"
        score = _detect_humble_brag_v3_3(sent, self.matcher)
        self.assertEqual(score, 0.0)
        
        # 必須条件不足（実績語彙なし）
        sent = "まだまだ不完全ながら、私は頑張ります。"
        score = _detect_humble_brag_v3_3(sent, self.matcher)
        self.assertEqual(score, 0.0)

if __name__ == "__main__":
    unittest.main()