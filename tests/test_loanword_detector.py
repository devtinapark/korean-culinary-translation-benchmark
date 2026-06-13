"""
Unit tests for loanword detection
"""
import unittest
from src.loanword_detector import KonglishDetector, LoanwordSubsetAnalyzer


class TestKonglishDetector(unittest.TestCase):
    """Test Konglish detector"""

    def setUp(self):
        self.detector = KonglishDetector()

    def test_detect_loanwords_simple(self):
        """Test simple loanword detection"""
        text = "오늘은 pizza를 먹었어요"
        loanwords = self.detector.detect_loanwords(text)

        self.assertIn("pizza", loanwords)

    def test_detect_multiple_loanwords(self):
        """Test multiple loanword detection"""
        text = "오늘 oven에서 pizza와 pasta를 만들었어요"
        loanwords = self.detector.detect_loanwords(text)

        self.assertIn("oven", loanwords)
        self.assertIn("pizza", loanwords)
        self.assertIn("pasta", loanwords)

    def test_no_loanwords(self):
        """Test text with no loanwords"""
        text = "안녕하세요 여러분"
        loanwords = self.detector.detect_loanwords(text)

        self.assertEqual(len(loanwords), 0)

    def test_contains_kitchen_loanwords(self):
        """Test kitchen loanword detection"""
        text = "oven을 사용해서 요리했어요"
        result = self.detector.contains_kitchen_loanwords(text)

        self.assertTrue(result)

    def test_filter_loanword_samples(self):
        """Test filtering samples with loanwords"""
        samples = [
            ("1", "pizza를 먹었어요"),
            ("2", "안녕하세요"),
            ("3", "oven을 사용했어요")
        ]

        loanword_samples = self.detector.filter_loanword_samples(samples)

        self.assertEqual(len(loanword_samples), 2)
        self.assertEqual(loanword_samples[0].id, "1")
        self.assertEqual(loanword_samples[1].id, "3")

    def test_analyze_loanword_distribution(self):
        """Test loanword distribution analysis"""
        samples = [
            ("1", "pizza를 먹었어요"),
            ("2", "안녕하세요"),
            ("3", "pizza와 pasta를 먹었어요"),
            ("4", "oven을 사용했어요")
        ]

        analysis = self.detector.analyze_loanword_distribution(samples)

        self.assertEqual(analysis['total_samples'], 4)
        self.assertEqual(analysis['samples_with_loanwords'], 3)
        self.assertGreater(analysis['unique_loanwords'], 0)


class TestLoanwordSubsetAnalyzer(unittest.TestCase):
    """Test loanword subset analyzer"""

    def setUp(self):
        self.analyzer = LoanwordSubsetAnalyzer()

    def test_create_loanword_subset(self):
        """Test creating subset with loanwords"""
        references = [
            "pizza를 먹었어요",
            "안녕하세요",
            "pasta를 만들었어요"
        ]
        hypotheses = [
            "pizza를 먹었어요",
            "안녕하세요",
            "pasta를 만들었어요"
        ]
        ids = ["1", "2", "3"]

        filtered_refs, filtered_hyps, filtered_ids = \
            self.analyzer.create_loanword_subset(references, hypotheses, ids)

        self.assertEqual(len(filtered_refs), 2)
        self.assertIn("1", filtered_ids)
        self.assertIn("3", filtered_ids)
        self.assertNotIn("2", filtered_ids)


if __name__ == '__main__':
    unittest.main()
