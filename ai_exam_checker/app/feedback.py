"""
Feedback generation module.
Generates structured, actionable feedback for students.
"""

from typing import List, Dict
from app.models import CriterionScore
from app.scoring import get_scoring_engine


class FeedbackGenerator:
    """
    Generates comprehensive feedback based on evaluation results.
    Focuses on constructive, actionable advice.
    """

    def __init__(self):
        """Initialize the feedback generator"""
        self.scoring_engine = get_scoring_engine()

    def generate_feedback(
        self,
        criteria_scores: List[CriterionScore],
        confidence: str = "medium"
    ) -> Dict[str, any]:
        """
        Generate complete feedback package.

        Args:
            criteria_scores: List of CriterionScore objects
            confidence: Evaluation confidence level

        Returns:
            Dictionary containing feedback components
        """
        # Get score breakdown
        breakdown = self.scoring_engine.get_score_breakdown(criteria_scores)

        # Identify strengths and weaknesses
        strengths, weaknesses = self.scoring_engine.identify_strengths_and_weaknesses(
            criteria_scores
        )

        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            criteria_scores,
            breakdown
        )

        # Generate overall feedback summary
        summary = self._generate_summary(breakdown, confidence)

        return {
            'summary': summary,
            'strengths': strengths if strengths else ["N/A - No strong areas identified"],
            'weaknesses': weaknesses if weaknesses else ["N/A - No major weaknesses identified"],
            'improvement_suggestions': improvement_suggestions,
            'breakdown': breakdown
        }

    def _generate_summary(self, breakdown: Dict, confidence: str) -> str:
        """
        Generate overall feedback summary.

        Args:
            breakdown: Score breakdown dictionary
            confidence: Evaluation confidence level

        Returns:
            Summary text
        """
        total_awarded = breakdown['total_awarded']
        total_possible = breakdown['total_possible']
        percentage = breakdown['percentage']
        grade = breakdown['grade']

        summary = f"Score: {total_awarded}/{total_possible} ({percentage:.1f}%) - Grade: {grade}\n\n"

        # Performance assessment
        if percentage >= 80:
            summary += "Excellent work! Your answer demonstrates strong understanding of the topic. "
        elif percentage >= 70:
            summary += "Good answer with solid understanding. "
        elif percentage >= 60:
            summary += "Satisfactory answer, but there's room for improvement. "
        elif percentage >= 50:
            summary += "Adequate answer, but several key points were missed. "
        else:
            summary += "Your answer needs significant improvement. "

        # Criteria breakdown
        fully_met = breakdown['fully_met_criteria']
        partially_met = breakdown['partially_met_criteria']
        unmet = breakdown['unmet_criteria']

        summary += f"\n\nCriteria met: {fully_met} fully, {partially_met} partially, {unmet} not met."

        # Confidence note
        if confidence == "low":
            summary += "\n\nNote: This evaluation has low confidence due to limited or irrelevant marking criteria retrieval. Manual review recommended."

        return summary

    def _generate_improvement_suggestions(
        self,
        criteria_scores: List[CriterionScore],
        breakdown: Dict
    ) -> List[str]:
        """
        Generate specific improvement suggestions.

        Args:
            criteria_scores: List of CriterionScore objects
            breakdown: Score breakdown

        Returns:
            List of improvement suggestion strings
        """
        suggestions = []

        # Analyze missing points
        all_missing_points = []
        for score in criteria_scores:
            if score.missing_points:
                all_missing_points.extend(score.missing_points)

        if all_missing_points:
            suggestions.append(
                f"Address the following missing points: {', '.join(all_missing_points[:3])}"
                + ("..." if len(all_missing_points) > 3 else "")
            )

        # Suggest based on unmet criteria
        unmet_criteria = [
            score for score in criteria_scores
            if score.awarded_marks < score.max_marks * 0.5
        ]

        if unmet_criteria:
            for criterion in unmet_criteria[:2]:  # Top 2 weakest areas
                suggestions.append(
                    f"Strengthen your response on: {criterion.criterion}"
                )

        # General suggestions based on performance
        percentage = breakdown['percentage']

        if percentage < 60:
            suggestions.append(
                "Review the core concepts and ensure your answer directly addresses the question"
            )
            suggestions.append(
                "Include more specific details and examples to support your points"
            )

        if percentage >= 60 and percentage < 80:
            suggestions.append(
                "Expand on your main points with more detail and explanation"
            )

        if not suggestions:
            suggestions.append(
                "Continue demonstrating thorough understanding in your answers"
            )

        return suggestions

    def format_feedback_for_display(self, feedback: Dict) -> str:
        """
        Format feedback dictionary into readable text.

        Args:
            feedback: Feedback dictionary

        Returns:
            Formatted feedback string
        """
        output = []

        output.append("=" * 60)
        output.append("EVALUATION FEEDBACK")
        output.append("=" * 60)
        output.append("")

        output.append(feedback['summary'])
        output.append("")

        output.append("STRENGTHS:")
        for idx, strength in enumerate(feedback['strengths'], 1):
            output.append(f"  {idx}. {strength}")
        output.append("")

        output.append("AREAS FOR IMPROVEMENT:")
        for idx, weakness in enumerate(feedback['weaknesses'], 1):
            output.append(f"  {idx}. {weakness}")
        output.append("")

        output.append("SUGGESTIONS:")
        for idx, suggestion in enumerate(feedback['improvement_suggestions'], 1):
            output.append(f"  {idx}. {suggestion}")
        output.append("")

        output.append("=" * 60)

        return "\n".join(output)


# Global feedback generator instance
_feedback_generator = None


def get_feedback_generator() -> FeedbackGenerator:
    """
    Get or create the global feedback generator instance.

    Returns:
        FeedbackGenerator instance
    """
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = FeedbackGenerator()
    return _feedback_generator
