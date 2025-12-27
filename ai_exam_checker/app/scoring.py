"""
Scoring engine module.
Aggregates criterion-level scores into final marks and validates scoring logic.
"""

from typing import List, Dict, Tuple
from app.models import CriterionScore


class ScoringEngine:
    """
    Handles score aggregation and validation.
    Ensures scoring logic is consistent and explainable.
    """

    def __init__(self):
        """Initialize the scoring engine"""
        pass

    def calculate_total_score(self, criteria_scores: List[CriterionScore]) -> Tuple[int, int]:
        """
        Calculate total marks from criterion scores.

        Args:
            criteria_scores: List of CriterionScore objects

        Returns:
            Tuple of (awarded_marks, total_possible_marks)
        """
        total_awarded = sum(score.awarded_marks for score in criteria_scores)
        total_possible = sum(score.max_marks for score in criteria_scores)

        return total_awarded, total_possible

    def validate_scores(self, criteria_scores: List[CriterionScore]) -> List[str]:
        """
        Validate scoring consistency and return any warnings.

        Args:
            criteria_scores: List of CriterionScore objects

        Returns:
            List of validation warning strings
        """
        warnings = []

        for idx, score in enumerate(criteria_scores):
            # Check if awarded marks exceed maximum
            if score.awarded_marks > score.max_marks:
                warnings.append(
                    f"Criterion {idx + 1}: Awarded marks ({score.awarded_marks}) "
                    f"exceed maximum ({score.max_marks})"
                )

            # Check for negative marks
            if score.awarded_marks < 0:
                warnings.append(
                    f"Criterion {idx + 1}: Negative marks awarded ({score.awarded_marks})"
                )

            # Check if justification is provided
            if not score.justification or len(score.justification.strip()) < 10:
                warnings.append(
                    f"Criterion {idx + 1}: Insufficient justification provided"
                )

        return warnings

    def get_score_breakdown(self, criteria_scores: List[CriterionScore]) -> Dict[str, any]:
        """
        Generate detailed score breakdown for reporting.

        Args:
            criteria_scores: List of CriterionScore objects

        Returns:
            Dictionary with score breakdown details
        """
        total_awarded, total_possible = self.calculate_total_score(criteria_scores)

        percentage = (total_awarded / total_possible * 100) if total_possible > 0 else 0

        breakdown = {
            'total_awarded': total_awarded,
            'total_possible': total_possible,
            'percentage': round(percentage, 2),
            'grade': self._calculate_grade(percentage),
            'criteria_count': len(criteria_scores),
            'fully_met_criteria': sum(1 for s in criteria_scores if s.awarded_marks == s.max_marks),
            'partially_met_criteria': sum(
                1 for s in criteria_scores
                if 0 < s.awarded_marks < s.max_marks
            ),
            'unmet_criteria': sum(1 for s in criteria_scores if s.awarded_marks == 0)
        }

        return breakdown

    def _calculate_grade(self, percentage: float) -> str:
        """
        Convert percentage to letter grade.

        Args:
            percentage: Score percentage

        Returns:
            Letter grade
        """
        if percentage >= 90:
            return 'A+'
        elif percentage >= 85:
            return 'A'
        elif percentage >= 80:
            return 'A-'
        elif percentage >= 75:
            return 'B+'
        elif percentage >= 70:
            return 'B'
        elif percentage >= 65:
            return 'B-'
        elif percentage >= 60:
            return 'C+'
        elif percentage >= 55:
            return 'C'
        elif percentage >= 50:
            return 'C-'
        elif percentage >= 45:
            return 'D'
        else:
            return 'F'

    def identify_strengths_and_weaknesses(
        self,
        criteria_scores: List[CriterionScore]
    ) -> Tuple[List[str], List[str]]:
        """
        Identify strengths and weaknesses from scoring.

        Args:
            criteria_scores: List of CriterionScore objects

        Returns:
            Tuple of (strengths, weaknesses) as lists of strings
        """
        strengths = []
        weaknesses = []

        for score in criteria_scores:
            score_ratio = score.awarded_marks / score.max_marks if score.max_marks > 0 else 0

            if score_ratio >= 0.8:  # 80% or more
                strengths.append(
                    f"{score.criterion}: {score.justification}"
                )
            elif score_ratio < 0.5:  # Less than 50%
                weaknesses.append(
                    f"{score.criterion}: {score.justification}"
                )

        return strengths, weaknesses


# Global scoring engine instance
_scoring_engine = None


def get_scoring_engine() -> ScoringEngine:
    """
    Get or create the global scoring engine instance.

    Returns:
        ScoringEngine instance
    """
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = ScoringEngine()
    return _scoring_engine
