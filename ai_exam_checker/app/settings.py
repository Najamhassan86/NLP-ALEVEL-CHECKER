"""
Configuration settings for the AI Exam Checker system.
Uses pydantic-settings for environment variable management.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file"""

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Embedding Model
    embedding_model: str = "all-MiniLM-L6-v2"

    # Vector Database
    chroma_persist_dir: str = "./chroma_db"

    # SQLite Database
    sqlite_db_path: str = "./exam_results.db"

    # Retrieval Settings
    top_k_retrieval: int = 5
    similarity_threshold: float = 0.3

    # Chunking Settings
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Data Directory
    markschemes_dir: str = "./data/markschemes"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_absolute_path(relative_path: str) -> str:
    """
    Convert relative path to absolute path, Windows-safe.

    Args:
        relative_path: Relative path string

    Returns:
        Absolute path string
    """
    if os.path.isabs(relative_path):
        return relative_path

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.normpath(os.path.join(base_dir, relative_path))


def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        settings.chroma_persist_dir,
        settings.markschemes_dir,
        os.path.dirname(settings.sqlite_db_path)
    ]

    for directory in directories:
        abs_dir = get_absolute_path(directory)
        if abs_dir and not os.path.exists(abs_dir):
            os.makedirs(abs_dir, exist_ok=True)
            print(f"Created directory: {abs_dir}")
