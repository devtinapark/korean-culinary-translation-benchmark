"""
Unit tests for model ranking
"""
import unittest
from src.ranking import ModelRanker, RankingCriteria


class TestRankingCriteria(unittest.TestCase):
    """Test ranking criteria"""

    def test_default_weights_sum_to_one(self):
        """Test that default weights sum to 1.0"""
        criteria = RankingCriteria()

        total = (
            criteria.cer_weight +
            criteria.wer_weight +
            criteria.loanword_weight +
            criteria.speed_weight +
            criteria.ratio_weight
        )

        self.assertAlmostEqual(total, 1.0, places=5)


class TestModelRanker(unittest.TestCase):
    """Test model ranker"""

    def setUp(self):
        self.ranker = ModelRanker()

    def test_normalize_metric_lower_is_better(self):
        """Test metric normalization with lower is better"""
        values = [0.1, 0.2, 0.3, 0.4]
        normalized = self.ranker.normalize_metric(values, lower_is_better=True)

        # Lowest value should have highest normalized score
        self.assertGreater(normalized[0], normalized[-1])

    def test_normalize_metric_higher_is_better(self):
        """Test metric normalization with higher is better"""
        values = [0.1, 0.2, 0.3, 0.4]
        normalized = self.ranker.normalize_metric(values, lower_is_better=False)

        # Highest value should have highest normalized score
        self.assertGreater(normalized[-1], normalized[0])

    def test_rank_models(self):
        """Test model ranking"""
        results = {
            "model_a": {
                "cer": 0.1,
                "wer": 0.2,
                "loanword_accuracy": 0.9,
                "samples_per_second": 10.0,
                "cer_wer_ratio": 2.5,
                "error": None
            },
            "model_b": {
                "cer": 0.2,
                "wer": 0.3,
                "loanword_accuracy": 0.8,
                "samples_per_second": 5.0,
                "cer_wer_ratio": 2.0,
                "error": None
            },
            "model_c": {
                "cer": 0.15,
                "wer": 0.25,
                "loanword_accuracy": 0.85,
                "samples_per_second": 8.0,
                "cer_wer_ratio": 2.2,
                "error": None
            }
        }

        ranked_df = self.ranker.rank_models(results)

        # Check that we have 3 models
        self.assertEqual(len(ranked_df), 3)

        # Check that ranks are assigned
        self.assertTrue('rank' in ranked_df.columns)
        self.assertTrue('composite_score' in ranked_df.columns)

        # Check that model_a (best CER) is ranked first
        self.assertEqual(ranked_df.iloc[0]['model'], 'model_a')

    def test_get_top_n(self):
        """Test getting top N models"""
        results = {
            f"model_{i}": {
                "cer": 0.1 + i * 0.05,
                "wer": 0.2 + i * 0.05,
                "loanword_accuracy": 0.9 - i * 0.05,
                "samples_per_second": 10.0 - i,
                "cer_wer_ratio": 2.5 - i * 0.1,
                "error": None
            }
            for i in range(10)
        }

        top_df, top_models = self.ranker.get_top_n(results, n=2)

        # Check we get 2 models (Whisper vs Deepgram)
        self.assertEqual(len(top_models), 2)
        self.assertEqual(len(top_df), 2)

        # Check that model_0 (best metrics) is in the comparison
        self.assertIn("model_0", top_models)

    def test_skip_models_with_errors(self):
        """Test that models with errors are skipped"""
        results = {
            "model_a": {
                "cer": 0.1,
                "wer": 0.2,
                "loanword_accuracy": 0.9,
                "samples_per_second": 10.0,
                "cer_wer_ratio": 2.5,
                "error": None
            },
            "model_b": {
                "cer": None,
                "wer": None,
                "loanword_accuracy": None,
                "samples_per_second": None,
                "cer_wer_ratio": None,
                "error": "Failed to load"
            }
        }

        ranked_df = self.ranker.rank_models(results)

        # Only model_a should be ranked
        self.assertEqual(len(ranked_df), 1)
        self.assertEqual(ranked_df.iloc[0]['model'], 'model_a')


if __name__ == '__main__':
    unittest.main()
