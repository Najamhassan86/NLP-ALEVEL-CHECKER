"""
Pydantic models for data validation and serialization.
These models define the structure of data throughout the RAG pipeline.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class MarkingSchemeMetadata(BaseModel):
    """Metadata for marking scheme documents"""
    subject: str
    question_id: str
    total_marks: int
    file_path: str


class DocumentChunk(BaseModel):
    """Represents a chunk of a marking scheme document"""
    content: str
    metadata: Dict[str, str]
    chunk_id: Optional[str] = None


class RetrievalResult(BaseModel):
    """Result from vector similarity search"""
    content: str
    metadata: Dict[str, str]
    similarity_score: float

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Award 2 marks for explaining photosynthesis...",
                "metadata": {"subject": "Biology", "question_id": "Q1"},
                "similarity_score": 0.87
            }
        }


class CriterionScore(BaseModel):
    """Scoring for a single marking criterion"""
    criterion: str = Field(..., description="The marking criterion being evaluated")
    max_marks: int = Field(..., description="Maximum marks available for this criterion")
    awarded_marks: int = Field(..., description="Marks awarded to the student")
    justification: str = Field(..., description="Explanation for the awarded marks")
    missing_points: List[str] = Field(default_factory=list, description="Points the student missed")


class EvaluationRequest(BaseModel):
    """Request for evaluating a student answer"""
    subject: str
    question_id: str
    student_answer: str

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Biology",
                "question_id": "Q1",
                "student_answer": "Photosynthesis is the process where plants convert light energy into chemical energy..."
            }
        }


class EvaluationResponse(BaseModel):
    """Complete evaluation response"""
    subject: str
    question_id: str
    student_answer: str
    retrieved_context: List[RetrievalResult]
    criteria_scores: List[CriterionScore]
    total_marks_awarded: int
    total_marks_possible: int
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Biology",
                "question_id": "Q1",
                "total_marks_awarded": 7,
                "total_marks_possible": 10,
                "criteria_scores": [
                    {
                        "criterion": "Definition of photosynthesis",
                        "max_marks": 3,
                        "awarded_marks": 2,
                        "justification": "Correct process but missing light wavelength details",
                        "missing_points": ["Specific wavelengths absorbed"]
                    }
                ]
            }
        }


class EvaluationHistory(BaseModel):
    """Historical evaluation record"""
    id: int
    subject: str
    question_id: str
    student_answer: str
    total_marks_awarded: int
    total_marks_possible: int
    timestamp: datetime

    class Config:
        from_attributes = True
