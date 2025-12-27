"""
Smoke test for AI Exam Checker system.
Tests the complete RAG pipeline end-to-end.
"""

import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.settings import ensure_directories
from app.rag import get_retriever
from app.evaluation import get_evaluator
from app.scoring import get_scoring_engine
from app.feedback import get_feedback_generator
from app.models import EvaluationRequest


def test_retrieval():
    """Test vector retrieval"""
    print("\n" + "=" * 60)
    print("TEST 1: Vector Retrieval")
    print("=" * 60)

    retriever = get_retriever()

    # Check if data is loaded
    doc_count = retriever.collection.count()
    print(f"Documents in vector DB: {doc_count}")

    if doc_count == 0:
        print("❌ FAILED: No documents in vector database")
        print("Please run: python ingest.py")
        return False

    # Test retrieval
    test_query = "Explain the process of photosynthesis"

    print(f"\nTest Query: {test_query}")
    print("Retrieving relevant criteria...")

    results = retriever.retrieve(
        query=test_query,
        filter_metadata={'subject': 'Biology', 'question_id': 'Q1'}
    )

    print(f"Retrieved {len(results)} results")

    if results:
        print("\nTop result:")
        print(f"  Similarity: {results[0].similarity_score:.4f}")
        print(f"  Content: {results[0].content[:100]}...")
        print("✅ PASSED: Retrieval working")
        return True
    else:
        print("❌ FAILED: No results retrieved")
        return False


def test_evaluation():
    """Test LLM evaluation"""
    print("\n" + "=" * 60)
    print("TEST 2: LLM Evaluation")
    print("=" * 60)

    try:
        evaluator = get_evaluator()
        retriever = get_retriever()

        # Sample student answer
        student_answer = """
        Photosynthesis is the process by which plants convert light energy into chemical energy.
        It occurs in the chloroplasts. The process has two main stages: light-dependent reactions
        and light-independent reactions (Calvin cycle). In the light reactions, light energy is
        captured and used to produce ATP and NADPH. In the Calvin cycle, CO2 is fixed to produce
        glucose. The overall equation is: 6CO2 + 6H2O + light → C6H12O6 + 6O2.
        """

        print("Sample Answer:")
        print(student_answer[:150] + "...")

        # Retrieve context
        print("\nRetrieving context...")
        retrieved_context = retriever.retrieve(
            query=student_answer,
            filter_metadata={'subject': 'Biology', 'question_id': 'Q1'}
        )

        if not retrieved_context:
            print("❌ FAILED: Could not retrieve context")
            return False

        print(f"Retrieved {len(retrieved_context)} context chunks")

        # Evaluate
        print("\nEvaluating with LLM...")
        print("(This may take 10-30 seconds)")

        evaluation_result = evaluator.evaluate(
            student_answer=student_answer,
            retrieved_context=retrieved_context
        )

        # Check result
        if evaluation_result and evaluation_result.get('criteria_evaluations'):
            print(f"\n✅ PASSED: Evaluation completed")
            print(f"Confidence: {evaluation_result.get('confidence', 'unknown')}")
            print(f"Criteria evaluated: {len(evaluation_result['criteria_evaluations'])}")

            # Parse scores
            criteria_scores = evaluator.parse_to_criterion_scores(evaluation_result)

            scoring_engine = get_scoring_engine()
            total_awarded, total_possible = scoring_engine.calculate_total_score(criteria_scores)

            print(f"Score: {total_awarded}/{total_possible}")

            return True
        else:
            print("❌ FAILED: Evaluation returned no results")
            return False

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_feedback_generation():
    """Test feedback generation"""
    print("\n" + "=" * 60)
    print("TEST 3: Feedback Generation")
    print("=" * 60)

    try:
        from app.models import CriterionScore

        # Create sample criterion scores
        sample_scores = [
            CriterionScore(
                criterion="Definition of photosynthesis",
                max_marks=2,
                awarded_marks=2,
                justification="Correctly defined photosynthesis with all key elements",
                missing_points=[]
            ),
            CriterionScore(
                criterion="Light-dependent reactions",
                max_marks=3,
                awarded_marks=2,
                justification="Mentioned ATP/NADPH production but missing details on thylakoid",
                missing_points=["Location in thylakoid membrane"]
            )
        ]

        feedback_generator = get_feedback_generator()
        feedback = feedback_generator.generate_feedback(sample_scores)

        print("Feedback generated successfully")
        print(f"  Strengths: {len(feedback['strengths'])}")
        print(f"  Weaknesses: {len(feedback['weaknesses'])}")
        print(f"  Suggestions: {len(feedback['improvement_suggestions'])}")

        print("\n✅ PASSED: Feedback generation working")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_database():
    """Test database operations"""
    print("\n" + "=" * 60)
    print("TEST 4: Database Operations")
    print("=" * 60)

    try:
        from app.db import get_database
        from datetime import datetime

        db = get_database()

        # Get history
        history = db.get_all_evaluations(limit=5)
        print(f"Found {len(history)} historical evaluations")

        print("✅ PASSED: Database working")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    """Run all smoke tests"""
    print("\n" + "=" * 60)
    print("AI EXAM CHECKER - SMOKE TEST")
    print("=" * 60)

    # Ensure directories exist
    ensure_directories()

    # Run tests
    results = {
        'Vector Retrieval': test_retrieval(),
        'LLM Evaluation': test_evaluation(),
        'Feedback Generation': test_feedback_generation(),
        'Database': test_database()
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All tests passed! System is ready.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
