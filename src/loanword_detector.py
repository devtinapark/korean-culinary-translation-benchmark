"""
Loanword Detection and Analysis
Identifies and analyzes English loanwords (Konglish) in Korean text
"""
from typing import List, Dict, Set, Tuple
import re
from dataclasses import dataclass


@dataclass
class LoanwordSample:
    """Sample containing loanwords"""
    id: str
    text: str
    loanwords: List[str]
    num_loanwords: int


class KonglishDetector:
    """
    Detects English loanwords (Konglish) in Korean text
    """

    # Common English loanwords used in Korean kitchen contexts
    KITCHEN_LOANWORDS = {
        # Appliances
        'oven', 'toaster', 'blender', 'mixer', 'grill', 'microwave',

        # Cooking terms
        'recipe', 'pasta', 'pizza', 'salad', 'steak', 'sauce',
        'cream', 'butter', 'cheese', 'bacon', 'ham', 'cake',
        'cookie', 'bread', 'toast', 'sandwich', 'burger',

        # Measurements
        'cup', 'spoon', 'timer', 'scale',

        # Ingredients
        'tomato', 'potato', 'onion', 'garlic', 'pepper',
        'sugar', 'salt', 'oil', 'milk', 'chocolate',

        # Cooking methods
        'grill', 'roast', 'fry', 'mix', 'blend', 'beat',

        # Kitchen items
        'pan', 'pot', 'fork', 'knife', 'spoon', 'plate',
        'bowl', 'glass', 'cup', 'napkin', 'table',

        # Others
        'menu', 'cooking', 'kitchen', 'dining', 'food'
    }

    def __init__(self, custom_loanwords: Set[str] = None):
        """
        Initialize loanword detector

        Args:
            custom_loanwords: Additional loanwords to detect
        """
        self.loanwords = self.KITCHEN_LOANWORDS.copy()
        if custom_loanwords:
            self.loanwords.update(custom_loanwords)

        # Pattern to detect English words
        self.english_pattern = re.compile(r'\b[a-zA-Z]+\b')

        # Pattern to detect romanized Korean (rough heuristic)
        # This helps avoid false positives from romanization
        self.romanized_korean_pattern = re.compile(
            r'\b(gim|kim|park|lee|choi|jeong|kang|han|'
            r'bulgogi|kimchi|bibimbap|tteokbokki|gochujang|'
            r'samgyeopsal|galbi|jjigae|banchan|jeon|'
            r'guk|tang|bap|namul|jorim)\b',
            re.IGNORECASE
        )

    def detect_loanwords(self, text: str) -> List[str]:
        """
        Detect English loanwords in text

        Args:
            text: Korean text potentially containing loanwords

        Returns:
            List of detected loanwords
        """
        # Extract all English words
        english_words = self.english_pattern.findall(text.lower())

        # Filter out romanized Korean
        loanwords = [
            word for word in english_words
            if not self.romanized_korean_pattern.match(word)
        ]

        return loanwords

    def contains_kitchen_loanwords(self, text: str) -> bool:
        """
        Check if text contains kitchen-related loanwords

        Args:
            text: Text to check

        Returns:
            True if contains kitchen loanwords
        """
        detected = self.detect_loanwords(text)
        return any(word in self.loanwords for word in detected)

    def filter_loanword_samples(
        self,
        samples: List[Tuple[str, str]]
    ) -> List[LoanwordSample]:
        """
        Filter samples containing loanwords

        Args:
            samples: List of (id, text) tuples

        Returns:
            List of LoanwordSample objects
        """
        loanword_samples = []

        for sample_id, text in samples:
            loanwords = self.detect_loanwords(text)

            if loanwords:
                loanword_samples.append(LoanwordSample(
                    id=sample_id,
                    text=text,
                    loanwords=loanwords,
                    num_loanwords=len(loanwords)
                ))

        return loanword_samples

    def analyze_loanword_distribution(
        self,
        samples: List[Tuple[str, str]]
    ) -> Dict:
        """
        Analyze distribution of loanwords in samples

        Args:
            samples: List of (id, text) tuples

        Returns:
            Dictionary with distribution statistics
        """
        all_loanwords = []
        samples_with_loanwords = 0

        for _, text in samples:
            loanwords = self.detect_loanwords(text)
            if loanwords:
                samples_with_loanwords += 1
                all_loanwords.extend(loanwords)

        # Count frequency
        from collections import Counter
        loanword_freq = Counter(all_loanwords)

        return {
            "total_samples": len(samples),
            "samples_with_loanwords": samples_with_loanwords,
            "loanword_percentage": samples_with_loanwords / len(samples) * 100 if samples else 0,
            "total_loanwords": len(all_loanwords),
            "unique_loanwords": len(set(all_loanwords)),
            "most_common": loanword_freq.most_common(10),
            "loanword_frequency": dict(loanword_freq)
        }


class LoanwordSubsetAnalyzer:
    """
    Analyzes model performance on loanword-containing samples
    """

    def __init__(self, detector: KonglishDetector = None):
        """
        Initialize analyzer

        Args:
            detector: KonglishDetector instance
        """
        self.detector = detector or KonglishDetector()

    def create_loanword_subset(
        self,
        references: List[str],
        hypotheses: List[str],
        ids: List[str] = None
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Create subset of samples containing loanwords

        Args:
            references: Reference transcriptions
            hypotheses: Model predictions
            ids: Sample IDs (optional)

        Returns:
            Tuple of (filtered_refs, filtered_hyps, filtered_ids)
        """
        filtered_refs = []
        filtered_hyps = []
        filtered_ids = []

        if ids is None:
            ids = [str(i) for i in range(len(references))]

        for ref, hyp, sample_id in zip(references, hypotheses, ids):
            if self.detector.detect_loanwords(ref):
                filtered_refs.append(ref)
                filtered_hyps.append(hyp)
                filtered_ids.append(sample_id)

        return filtered_refs, filtered_hyps, filtered_ids

    def compare_loanword_performance(
        self,
        all_refs: List[str],
        all_hyps: List[str],
        metrics_calculator
    ) -> Dict:
        """
        Compare performance on loanword vs non-loanword samples

        Args:
            all_refs: All reference transcriptions
            all_hyps: All predictions
            metrics_calculator: KoreanMetricsCalculator instance

        Returns:
            Dictionary comparing performance
        """
        # Separate loanword and non-loanword samples
        loanword_refs = []
        loanword_hyps = []
        non_loanword_refs = []
        non_loanword_hyps = []

        for ref, hyp in zip(all_refs, all_hyps):
            if self.detector.detect_loanwords(ref):
                loanword_refs.append(ref)
                loanword_hyps.append(hyp)
            else:
                non_loanword_refs.append(ref)
                non_loanword_hyps.append(hyp)

        # Calculate metrics for each subset
        results = {
            "total_samples": len(all_refs),
            "loanword_samples": len(loanword_refs),
            "non_loanword_samples": len(non_loanword_refs)
        }

        if loanword_refs:
            loanword_metrics = metrics_calculator.calculate_all_metrics(
                loanword_refs, loanword_hyps
            )
            results["loanword_cer"] = loanword_metrics.cer
            results["loanword_wer"] = loanword_metrics.wer

        if non_loanword_refs:
            non_loanword_metrics = metrics_calculator.calculate_all_metrics(
                non_loanword_refs, non_loanword_hyps
            )
            results["non_loanword_cer"] = non_loanword_metrics.cer
            results["non_loanword_wer"] = non_loanword_metrics.wer

        return results
