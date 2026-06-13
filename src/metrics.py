"""
ASR Evaluation Metrics
Computes CER, WER, and Korean-specific metrics
"""
from typing import List, Dict, Tuple
import jiwer
from jiwer import wer, cer
import re
from dataclasses import dataclass


@dataclass
class MetricResults:
    """Container for evaluation metrics"""
    cer: float
    wer: float
    cer_wer_ratio: float
    char_precision: float
    char_recall: float
    word_precision: float
    word_recall: float
    num_samples: int


class KoreanMetricsCalculator:
    """
    Calculates ASR metrics with Korean language considerations
    """

    def __init__(self):
        """Initialize metrics calculator"""
        self.transformation = jiwer.Compose([
            jiwer.ToLowerCase(),
            jiwer.RemoveMultipleSpaces(),
            jiwer.Strip(),
        ])

    def normalize_korean_text(self, text: str, strip_spaces: bool = False) -> str:
        # Lowercase (covers English loanwords in mixed clips)
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[.,!?;:()\[\]{}「」『』·…~\-—\[\]]', '', text)
        # Remove content in brackets like [gesture] [한 줌 표시]
        text = re.sub(r'\[.*?\]', '', text)
        if strip_spaces:
            # For CER: remove all spaces — Korean spacing is inconsistent across models
            text = re.sub(r'\s+', '', text)
        else:
            # For WER: collapse multiple spaces only
            text = re.sub(r'\s+', ' ', text).strip()
        return text

    def calculate_cer(
        self,
        references: List[str],
        hypotheses: List[str],
        normalize: bool = True
    ) -> float:
        """
        Calculate Character Error Rate

        Args:
            references: Reference transcriptions
            hypotheses: Predicted transcriptions
            normalize: Whether to normalize text

        Returns:
            CER value (0-1, lower is better)
        """
        if normalize:
            references = [self.normalize_korean_text(ref, strip_spaces=True) for ref in references]
            hypotheses = [self.normalize_korean_text(hyp, strip_spaces=True) for hyp in hypotheses]

        return cer(references, hypotheses)

    def calculate_wer(
        self,
        references: List[str],
        hypotheses: List[str],
        normalize: bool = True
    ) -> float:
        """
        Calculate Word Error Rate

        Args:
            references: Reference transcriptions
            hypotheses: Predicted transcriptions
            normalize: Whether to normalize text

        Returns:
            WER value (0-1, lower is better)
        """
        if normalize:
            references = [self.normalize_korean_text(ref) for ref in references]
            hypotheses = [self.normalize_korean_text(hyp) for hyp in hypotheses]

        return wer(references, hypotheses)

    def calculate_precision_recall(
        self,
        references: List[str],
        hypotheses: List[str],
        level: str = "char"
    ) -> Tuple[float, float]:
        """
        Calculate precision and recall at character or word level

        Args:
            references: Reference transcriptions
            hypotheses: Predicted transcriptions
            level: "char" or "word"

        Returns:
            Tuple of (precision, recall)
        """
        total_ref_units = 0
        total_hyp_units = 0
        total_matches = 0

        for ref, hyp in zip(references, hypotheses):
            ref = self.normalize_korean_text(ref)
            hyp = self.normalize_korean_text(hyp)

            if level == "char":
                ref_units = set(enumerate(ref))
                hyp_units = set(enumerate(hyp))
            else:  # word
                ref_units = set(enumerate(ref.split()))
                hyp_units = set(enumerate(hyp.split()))

            # Count units
            total_ref_units += len(ref_units)
            total_hyp_units += len(hyp_units)

            # Count matches (units present in both at same position)
            matches = len(ref_units.intersection(hyp_units))
            total_matches += matches

        # Calculate precision and recall
        precision = total_matches / total_hyp_units if total_hyp_units > 0 else 0.0
        recall = total_matches / total_ref_units if total_ref_units > 0 else 0.0

        return precision, recall

    def calculate_all_metrics(
        self,
        references: List[str],
        hypotheses: List[str]
    ) -> MetricResults:
        """
        Calculate all evaluation metrics

        Args:
            references: Reference transcriptions
            hypotheses: Predicted transcriptions

        Returns:
            MetricResults object with all metrics
        """
        # Calculate CER and WER
        cer_score = self.calculate_cer(references, hypotheses)
        wer_score = self.calculate_wer(references, hypotheses)

        # Calculate CER/WER ratio
        # For Korean, this should be >2x due to agglutinative nature
        cer_wer_ratio = wer_score / cer_score if cer_score > 0 else 0.0

        # Calculate precision/recall
        char_precision, char_recall = self.calculate_precision_recall(
            references, hypotheses, level="char"
        )
        word_precision, word_recall = self.calculate_precision_recall(
            references, hypotheses, level="word"
        )

        return MetricResults(
            cer=cer_score,
            wer=wer_score,
            cer_wer_ratio=cer_wer_ratio,
            char_precision=char_precision,
            char_recall=char_recall,
            word_precision=word_precision,
            word_recall=word_recall,
            num_samples=len(references)
        )


class LoanwordAccuracyCalculator:
    """
    Calculates accuracy for English loanwords (Konglish) in Korean text
    """

    def __init__(self):
        """Initialize loanword accuracy calculator"""
        # Common English loanword patterns in Korean
        self.english_pattern = re.compile(r'[a-zA-Z]+')

    def extract_loanwords(self, text: str) -> List[str]:
        """
        Extract English loanwords from Korean text

        Args:
            text: Korean text potentially containing loanwords

        Returns:
            List of extracted loanwords
        """
        # Find all English words
        loanwords = self.english_pattern.findall(text)

        # Normalize to lowercase
        loanwords = [w.lower() for w in loanwords]

        return loanwords

    def calculate_loanword_accuracy(
        self,
        references: List[str],
        hypotheses: List[str]
    ) -> Dict[str, float]:
        """
        Calculate loanword transcription accuracy

        Args:
            references: Reference transcriptions
            hypotheses: Predicted transcriptions

        Returns:
            Dictionary with loanword metrics
        """
        total_loanwords = 0
        correct_loanwords = 0
        loanword_cer = []

        for ref, hyp in zip(references, hypotheses):
            ref_loanwords = self.extract_loanwords(ref)
            hyp_loanwords = self.extract_loanwords(hyp)

            if not ref_loanwords:
                continue

            total_loanwords += len(ref_loanwords)

            # Match loanwords
            for ref_word in ref_loanwords:
                if ref_word in hyp_loanwords:
                    correct_loanwords += 1
                else:
                    # Calculate CER for this loanword
                    best_match_cer = min(
                        [cer([ref_word], [hyp_word]) for hyp_word in hyp_loanwords],
                        default=1.0
                    )
                    loanword_cer.append(best_match_cer)

        # Calculate metrics
        accuracy = correct_loanwords / total_loanwords if total_loanwords > 0 else 0.0
        avg_cer = sum(loanword_cer) / len(loanword_cer) if loanword_cer else 0.0

        return {
            "loanword_accuracy": accuracy,
            "loanword_cer": avg_cer,
            "total_loanwords": total_loanwords,
            "correct_loanwords": correct_loanwords
        }


class InferenceSpeedCalculator:
    """
    Calculates inference speed metrics
    """

    @staticmethod
    def calculate_speed(
        num_samples: int,
        total_time: float,
        total_audio_duration: float = None
    ) -> Dict[str, float]:
        """
        Calculate inference speed metrics

        Args:
            num_samples: Number of samples processed
            total_time: Total processing time in seconds
            total_audio_duration: Total audio duration in seconds (optional)

        Returns:
            Dictionary with speed metrics
        """
        samples_per_second = num_samples / total_time if total_time > 0 else 0.0

        result = {
            "samples_per_second": samples_per_second,
            "avg_time_per_sample": total_time / num_samples if num_samples > 0 else 0.0,
            "total_time": total_time
        }

        if total_audio_duration is not None:
            rtf = total_time / total_audio_duration if total_audio_duration > 0 else 0.0
            result["real_time_factor"] = rtf

        return result
