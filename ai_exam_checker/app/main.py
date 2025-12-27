"""
FastAPI main application.
Provides REST API endpoints for the exam evaluation system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from datetime import datetime

from app.models import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationHistory,
    RetrievalResult
)
from app.rag import get_retriever
from app.evaluation import get_evaluator
from app.scoring import get_scoring_engine
from app.feedback import get_feedback_generator
from app.db import get_database
from app.settings import settings, ensure_directories

# Initialize FastAPI app
app = FastAPI(
    title="AI Exam Checker",
    description="RAG-based automated exam answer evaluation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("Starting AI Exam Checker API...")
    ensure_directories()
    print("System ready!")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Exam Checker API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    retriever = get_retriever()
    doc_count = retriever.collection.count()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "vector_db_count": doc_count,
        "ollama_model": settings.ollama_model,
        "embedding_model": settings.embedding_model
    }


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_answer(request: EvaluationRequest) -> EvaluationResponse:
    """
    Evaluate a student answer using RAG pipeline.

    This is the main endpoint that orchestrates the entire evaluation process:
    1. Retrieve relevant marking criteria
    2. Evaluate answer using LLM
    3. Calculate scores
    4. Generate feedback
    5. Save to database
    """
    try:
        print(f"\n{'=' * 60}")
        print(f"New evaluation request: {request.subject} - {request.question_id}")
        print(f"{'=' * 60}\n")

        # Step 1: Retrieve relevant marking criteria
        retriever = get_retriever()
        retrieved_context = retriever.retrieve(
            query=request.student_answer,
            filter_metadata={
                'subject': request.subject,
                'question_id': request.question_id
            }
        )

        if not retrieved_context:
            raise HTTPException(
                status_code=404,
                detail=f"No marking criteria found for {request.subject} - {request.question_id}"
            )

        print(f"Retrieved {len(retrieved_context)} relevant criteria chunks")

        # Step 2: Evaluate using LLM
        evaluator = get_evaluator()
        evaluation_result = evaluator.evaluate(
            student_answer=request.student_answer,
            retrieved_context=retrieved_context
        )

        # Parse to CriterionScore objects
        criteria_scores = evaluator.parse_to_criterion_scores(evaluation_result)

        if not criteria_scores:
            raise HTTPException(
                status_code=500,
                detail="Evaluation failed to produce criterion scores"
            )

        # Step 3: Calculate total score
        scoring_engine = get_scoring_engine()
        total_awarded, total_possible = scoring_engine.calculate_total_score(criteria_scores)

        # Validate scores
        warnings = scoring_engine.validate_scores(criteria_scores)
        if warnings:
            print("Validation warnings:")
            for warning in warnings:
                print(f"  - {warning}")

        # Step 4: Generate feedback
        feedback_generator = get_feedback_generator()
        feedback_data = feedback_generator.generate_feedback(
            criteria_scores,
            confidence=evaluation_result.get('confidence', 'medium')
        )

        # Step 5: Create response object
        evaluation_response = EvaluationResponse(
            subject=request.subject,
            question_id=request.question_id,
            student_answer=request.student_answer,
            retrieved_context=retrieved_context,
            criteria_scores=criteria_scores,
            total_marks_awarded=total_awarded,
            total_marks_possible=total_possible,
            feedback=feedback_data['summary'],
            strengths=feedback_data['strengths'],
            weaknesses=feedback_data['weaknesses'],
            improvement_suggestions=feedback_data['improvement_suggestions'],
            timestamp=datetime.now()
        )

        # Step 6: Save to database
        db = get_database()
        evaluation_id = db.save_evaluation(evaluation_response)
        print(f"\nEvaluation saved with ID: {evaluation_id}")

        print(f"\n{'=' * 60}")
        print(f"Evaluation complete: {total_awarded}/{total_possible} marks")
        print(f"{'=' * 60}\n")

        return evaluation_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history", response_model=List[EvaluationHistory])
async def get_evaluation_history(limit: int = 50):
    """
    Get evaluation history.

    Args:
        limit: Maximum number of records to return
    """
    try:
        db = get_database()
        history = db.get_all_evaluations(limit=limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{evaluation_id}")
async def get_evaluation_detail(evaluation_id: int):
    """
    Get detailed evaluation by ID.

    Args:
        evaluation_id: ID of the evaluation
    """
    try:
        db = get_database()
        evaluation = db.get_evaluation_by_id(evaluation_id)

        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        return evaluation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/subjects")
async def get_subjects() -> Dict[str, List[str]]:
    """
    Get available subjects and questions from vector database.

    Returns:
        Dictionary mapping subjects to question IDs
    """
    try:
        retriever = get_retriever()

        # Get all documents from ChromaDB
        all_docs = retriever.collection.get()

        subjects_questions = {}

        if all_docs['metadatas']:
            for metadata in all_docs['metadatas']:
                subject = metadata.get('subject', 'Unknown')
                question_id = metadata.get('question_id', 'Unknown')

                if subject not in subjects_questions:
                    subjects_questions[subject] = set()

                subjects_questions[subject].add(question_id)

        # Convert sets to sorted lists
        result = {
            subject: sorted(list(questions))
            for subject, questions in subjects_questions.items()
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        retriever = get_retriever()
        db = get_database()

        total_docs = retriever.collection.count()
        total_evaluations = len(db.get_all_evaluations(limit=10000))

        return {
            "total_marking_schemes": total_docs,
            "total_evaluations": total_evaluations,
            "ollama_model": settings.ollama_model,
            "embedding_model": settings.embedding_model,
            "vector_db_path": settings.chroma_persist_dir,
            "database_path": settings.sqlite_db_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
