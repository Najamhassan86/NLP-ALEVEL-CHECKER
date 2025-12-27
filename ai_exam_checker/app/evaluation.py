"""
Answer evaluation module using local LLM (Ollama).
Implements grounded evaluation based on retrieved marking criteria.
"""

import json
from typing import List, Dict
import ollama
from app.settings import settings
from app.models import RetrievalResult, CriterionScore


class AnswerEvaluator:
    """
    Evaluates student answers using a local LLM with retrieved context.
    Ensures evaluation is grounded in marking scheme criteria only.
    """

    def __init__(self, model_name: str = None, base_url: str = None):
        """
        Initialize the evaluator with Ollama client.

        Args:
            model_name: Name of the Ollama model to use
            base_url: Ollama server URL
        """
        self.model_name = model_name or settings.ollama_model
        self.base_url = base_url or settings.ollama_base_url

        # Configure Ollama client
        self.client = ollama.Client(host=self.base_url)

        # Verify model is available
        self._verify_model()

    def _verify_model(self):
        """Check if the specified model is available"""
        try:
            models = self.client.list()
            available_models = [m['name'] for m in models.get('models', [])]

            if not any(self.model_name in model for model in available_models):
                print(f"Warning: Model {self.model_name} not found in Ollama.")
                print(f"Available models: {available_models}")
                print(f"Please pull the model using: ollama pull {self.model_name}")
            else:
                print(f"Ollama model {self.model_name} is ready")

        except Exception as e:
            print(f"Warning: Could not verify Ollama model: {e}")
            print(f"Make sure Ollama is running at {self.base_url}")

    def _build_evaluation_prompt(
        self,
        student_answer: str,
        retrieved_context: List[RetrievalResult]
    ) -> str:
        """
        Build a structured prompt for the LLM that enforces grounded evaluation.

        Args:
            student_answer: The student's answer text
            retrieved_context: Retrieved marking scheme criteria

        Returns:
            Formatted prompt string
        """
        # Format retrieved context
        context_text = "\n\n".join([
            f"CRITERION {idx + 1} (Relevance: {ctx.similarity_score:.2f}):\n{ctx.content}"
            for idx, ctx in enumerate(retrieved_context)
        ])

        prompt = f"""You are an exam grader. Your task is to evaluate a student's answer STRICTLY based on the provided marking criteria.

IMPORTANT RULES:
1. ONLY use the criteria provided below - DO NOT invent or assume additional criteria
2. Award marks ONLY for points explicitly mentioned in the criteria
3. If the retrieved criteria seem incomplete or irrelevant, indicate low confidence
4. Be objective and consistent

MARKING CRITERIA (Retrieved from marking scheme):
{context_text}

STUDENT ANSWER:
{student_answer}

TASK:
Evaluate the student answer against EACH criterion above. For each criterion, provide:
1. The criterion description
2. Maximum marks for this criterion (estimate from context, typically 1-3 marks per criterion)
3. Marks awarded (0 to max)
4. Clear justification
5. Missing points (if any)

OUTPUT FORMAT (strict JSON):
{{
  "criteria_evaluations": [
    {{
      "criterion": "description of what is being evaluated",
      "max_marks": <number>,
      "awarded_marks": <number>,
      "justification": "explanation of why marks were awarded or deducted",
      "missing_points": ["point 1", "point 2"]
    }}
  ],
  "confidence": "high|medium|low",
  "confidence_reason": "explanation of confidence level"
}}

Respond with ONLY valid JSON, no additional text."""

        return prompt

    def evaluate(
        self,
        student_answer: str,
        retrieved_context: List[RetrievalResult]
    ) -> Dict:
        """
        Evaluate student answer using LLM with retrieved context.

        Args:
            student_answer: Student's answer text
            retrieved_context: Retrieved marking criteria

        Returns:
            Dictionary containing evaluation results
        """
        if not retrieved_context:
            return {
                "criteria_evaluations": [],
                "confidence": "low",
                "confidence_reason": "No relevant marking criteria could be retrieved"
            }

        # Build prompt
        prompt = self._build_evaluation_prompt(student_answer, retrieved_context)

        print(f"Sending evaluation request to Ollama ({self.model_name})...")

        try:
            # Call Ollama
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.1,  # Low temperature for consistent grading
                    'top_p': 0.9,
                }
            )

            # Extract response content
            response_text = response['message']['content'].strip()

            # Parse JSON response
            # Sometimes LLM adds markdown code blocks, remove them
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            evaluation_result = json.loads(response_text)

            print(f"Evaluation complete. Confidence: {evaluation_result.get('confidence', 'unknown')}")

            return evaluation_result

        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Response was: {response_text[:200]}...")
            return {
                "criteria_evaluations": [],
                "confidence": "low",
                "confidence_reason": f"Failed to parse LLM response: {str(e)}"
            }

        except Exception as e:
            print(f"Error during evaluation: {e}")
            return {
                "criteria_evaluations": [],
                "confidence": "low",
                "confidence_reason": f"Evaluation error: {str(e)}"
            }

    def parse_to_criterion_scores(self, evaluation_result: Dict) -> List[CriterionScore]:
        """
        Parse LLM evaluation result into CriterionScore objects.

        Args:
            evaluation_result: Raw evaluation result from LLM

        Returns:
            List of CriterionScore objects
        """
        criteria_scores = []

        for criterion_eval in evaluation_result.get('criteria_evaluations', []):
            score = CriterionScore(
                criterion=criterion_eval.get('criterion', 'Unknown criterion'),
                max_marks=criterion_eval.get('max_marks', 1),
                awarded_marks=criterion_eval.get('awarded_marks', 0),
                justification=criterion_eval.get('justification', ''),
                missing_points=criterion_eval.get('missing_points', [])
            )
            criteria_scores.append(score)

        return criteria_scores


# Global evaluator instance
_evaluator = None


def get_evaluator() -> AnswerEvaluator:
    """
    Get or create the global evaluator instance.

    Returns:
        AnswerEvaluator instance
    """
    global _evaluator
    if _evaluator is None:
        _evaluator = AnswerEvaluator()
    return _evaluator
