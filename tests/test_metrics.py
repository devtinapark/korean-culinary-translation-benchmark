"""
Unit tests for metrics calculation
"""
import unittest
from src.metrics import (
    KoreanMetricsCalculator,
    LoanwordAccuracyCalculator,
    InferenceSpeedCalculator
)


class TestKoreanMetricsCalculator(unittest.TestCase):
    """Test Korean metrics calculator"""

    def setUp(self):
        self.calculator = KoreanMetricsCalculator()

    def test_normalize_korean_text(self):
        """Test Korean text normalization"""
        text = "  안녕하세요,  세계!  "
        normalized = self.calculator.normalize_korean_text(text)

        self.assertEqual(normalized, "안녕하세요 세계")

    def test_calculate_cer_perfect_match(self):
        """Test CER calculation with perfect match"""
        references = ["안녕하세요"]
        hypotheses = ["안녕하세요"]

        cer = self.calculator.calculate_cer(references, hypotheses)
        self.assertEqual(cer, 0.0)

    def test_calculate_cer_complete_mismatch(self):
        """Test CER calculation with complete mismatch"""
        references = ["안녕"]
        hypotheses = ["하세요"]

        cer = self.calculator.calculate_cer(references, hypotheses)
        self.assertGreater(cer, 0.0)

    def test_calculate_wer_perfect_match(self):
        """Test WER calculation with perfect match"""
        references = ["안녕하세요 반갑습니다"]
        hypotheses = ["안녕하세요 반갑습니다"]

        wer = self.calculator.calculate_wer(references, hypotheses)
        self.assertEqual(wer, 0.0)

    def test_cer_wer_ratio(self):
        """Test CER/WER ratio calculation"""
        references = ["안녕하세요 여러분"]
        hypotheses = ["안녕하세요 여러분"]

        metrics = self.calculator.calculate_all_metrics(references, hypotheses)

        # For perfect match, ratio should be 0 (both are 0)
        self.assertEqual(metrics.cer, 0.0)
        self.assertEqual(metrics.wer, 0.0)


class TestLoanwordAccuracyCalculator(unittest.TestCase):
    """Test loanword accuracy calculator"""

    def setUp(self):
        self.calculator = LoanwordAccuracyCalculator()

    def test_extract_loanwords(self):
        """Test loanword extraction"""
        text = "오늘은 pizza와 pasta를 먹었어요"
        loanwords = self.calculator.extract_loanwords(text)

        self.assertIn("pizza", loanwords)
        self.assertIn("pasta", loanwords)

    def test_loanword_accuracy_perfect(self):
        """Test loanword accuracy with perfect match"""
        references = ["pizza를 먹었어요"]
        hypotheses = ["pizza를 먹었어요"]

        metrics = self.calculator.calculate_loanword_accuracy(references, hypotheses)

        self.assertEqual(metrics['loanword_accuracy'], 1.0)
        self.assertEqual(metrics['correct_loanwords'], 1)

    def test_loanword_accuracy_no_loanwords(self):
        """Test loanword accuracy with no loanwords"""
        references = ["안녕하세요"]
        hypotheses = ["안녕하세요"]

        metrics = self.calculator.calculate_loanword_accuracy(references, hypotheses)

        # No loanwords, accuracy should be 0
        self.assertEqual(metrics['total_loanwords'], 0)


class TestInferenceSpeedCalculator(unittest.TestCase):
    """Test inference speed calculator"""

    def test_calculate_speed(self):
        """Test speed calculation"""
        metrics = InferenceSpeedCalculator.calculate_speed(
            num_samples=100,
            total_time=10.0
        )

        self.assertEqual(metrics['samples_per_second'], 10.0)
        self.assertEqual(metrics['avg_time_per_sample'], 0.1)

    def test_calculate_speed_with_rtf(self):
        """Test speed calculation with real-time factor"""
        metrics = InferenceSpeedCalculator.calculate_speed(
            num_samples=100,
            total_time=10.0,
            total_audio_duration=100.0
        )

        self.assertEqual(metrics['real_time_factor'], 0.1)


if __name__ == '__main__':
    unittest.main()
