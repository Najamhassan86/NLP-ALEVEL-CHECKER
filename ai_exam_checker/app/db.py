"""
SQLite database module for persisting evaluation results.
Stores evaluation history for analysis and review.
"""

import os
import sqlite3
from typing import List, Optional
from datetime import datetime
from contextlib import contextmanager
from app.settings import settings, get_absolute_path
from app.models import EvaluationResponse, EvaluationHistory
import json


class Database:
    """SQLite database handler for evaluation results"""

    def __init__(self, db_path: str = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = get_absolute_path(db_path or settings.sqlite_db_path)
        self._initialize_database()

    def _initialize_database(self):
        """Create database tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create evaluations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    student_answer TEXT NOT NULL,
                    total_marks_awarded INTEGER NOT NULL,
                    total_marks_possible INTEGER NOT NULL,
                    criteria_scores TEXT NOT NULL,
                    feedback TEXT,
                    strengths TEXT,
                    weaknesses TEXT,
                    improvement_suggestions TEXT,
                    retrieved_context TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_subject_question
                ON evaluations(subject, question_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON evaluations(timestamp DESC)
            """)

            conn.commit()
            print(f"Database initialized at: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_evaluation(self, evaluation: EvaluationResponse) -> int:
        """
        Save an evaluation result to the database.

        Args:
            evaluation: EvaluationResponse object

        Returns:
            ID of the inserted record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO evaluations (
                    subject, question_id, student_answer,
                    total_marks_awarded, total_marks_possible,
                    criteria_scores, feedback, strengths, weaknesses,
                    improvement_suggestions, retrieved_context, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evaluation.subject,
                evaluation.question_id,
                evaluation.student_answer,
                evaluation.total_marks_awarded,
                evaluation.total_marks_possible,
                json.dumps([score.model_dump() for score in evaluation.criteria_scores]),
                evaluation.feedback,
                json.dumps(evaluation.strengths),
                json.dumps(evaluation.weaknesses),
                json.dumps(evaluation.improvement_suggestions),
                json.dumps([ctx.model_dump() for ctx in evaluation.retrieved_context]),
                evaluation.timestamp.isoformat()
            ))

            conn.commit()
            return cursor.lastrowid

    def get_evaluation_by_id(self, evaluation_id: int) -> Optional[dict]:
        """
        Retrieve a specific evaluation by ID.

        Args:
            evaluation_id: ID of the evaluation

        Returns:
            Dictionary containing evaluation data or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM evaluations WHERE id = ?",
                (evaluation_id,)
            )
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_all_evaluations(self, limit: int = 100) -> List[EvaluationHistory]:
        """
        Get all evaluations ordered by timestamp (most recent first).

        Args:
            limit: Maximum number of records to return

        Returns:
            List of EvaluationHistory objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, question_id, student_answer,
                       total_marks_awarded, total_marks_possible, timestamp
                FROM evaluations
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [
                EvaluationHistory(
                    id=row['id'],
                    subject=row['subject'],
                    question_id=row['question_id'],
                    student_answer=row['student_answer'],
                    total_marks_awarded=row['total_marks_awarded'],
                    total_marks_possible=row['total_marks_possible'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                )
                for row in rows
            ]

    def get_evaluations_by_subject(self, subject: str) -> List[EvaluationHistory]:
        """
        Get all evaluations for a specific subject.

        Args:
            subject: Subject name

        Returns:
            List of EvaluationHistory objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, question_id, student_answer,
                       total_marks_awarded, total_marks_possible, timestamp
                FROM evaluations
                WHERE subject = ?
                ORDER BY timestamp DESC
            """, (subject,))

            rows = cursor.fetchall()
            return [
                EvaluationHistory(
                    id=row['id'],
                    subject=row['subject'],
                    question_id=row['question_id'],
                    student_answer=row['student_answer'],
                    total_marks_awarded=row['total_marks_awarded'],
                    total_marks_possible=row['total_marks_possible'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                )
                for row in rows
            ]


# Global database instance
_database = None


def get_database() -> Database:
    """
    Get or create the global database instance.

    Returns:
        Database instance
    """
    global _database
    if _database is None:
        _database = Database()
    return _database
