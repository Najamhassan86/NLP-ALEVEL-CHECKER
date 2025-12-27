"""
Data ingestion script for loading marking schemes into ChromaDB.
Reads markdown files from data/markschemes and indexes them for retrieval.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
import re

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.settings import settings, get_absolute_path, ensure_directories
from app.rag import get_retriever, Chunker
from app.models import DocumentChunk, MarkingSchemeMetadata


def parse_filename(filename: str) -> Dict[str, str]:
    """
    Parse marking scheme filename to extract metadata.

    Expected format: {subject}_{question_id}.md
    Example: biology_q1.md -> subject="Biology", question_id="Q1"

    Args:
        filename: Name of the file (without path)

    Returns:
        Dictionary with subject and question_id
    """
    # Remove extension
    name = filename.replace('.md', '').replace('.txt', '')

    # Split by underscore
    parts = name.split('_')

    if len(parts) >= 2:
        subject = parts[0].capitalize()
        question_id = parts[1].upper()
    else:
        subject = "Unknown"
        question_id = name.upper()

    return {
        'subject': subject,
        'question_id': question_id
    }


def extract_total_marks(content: str) -> int:
    """
    Extract total marks from marking scheme content.

    Looks for patterns like "Total Marks: 10" or "**Total Marks: 10**"

    Args:
        content: Marking scheme text content

    Returns:
        Total marks (default: 10 if not found)
    """
    # Pattern to match "Total Marks: XX"
    pattern = r'\*\*Total Marks:\s*(\d+)\*\*|Total Marks:\s*(\d+)'
    match = re.search(pattern, content, re.IGNORECASE)

    if match:
        # Return whichever group matched
        return int(match.group(1) or match.group(2))

    return 10  # Default


def load_marking_scheme(file_path: str) -> tuple[str, MarkingSchemeMetadata]:
    """
    Load a single marking scheme file.

    Args:
        file_path: Path to the marking scheme file

    Returns:
        Tuple of (content, metadata)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = os.path.basename(file_path)
    file_metadata = parse_filename(filename)
    total_marks = extract_total_marks(content)

    metadata = MarkingSchemeMetadata(
        subject=file_metadata['subject'],
        question_id=file_metadata['question_id'],
        total_marks=total_marks,
        file_path=file_path
    )

    return content, metadata


def ingest_marking_schemes(reset: bool = False):
    """
    Main ingestion function.
    Loads all marking schemes and indexes them in ChromaDB.

    Args:
        reset: If True, clear existing data before ingesting
    """
    print("=" * 60)
    print("MARKING SCHEME INGESTION")
    print("=" * 60)

    # Ensure directories exist
    ensure_directories()

    # Get retriever
    retriever = get_retriever()

    # Reset if requested
    if reset:
        print("\nResetting vector database...")
        retriever.reset_collection()

    # Get chunker
    chunker = Chunker()

    # Get marking scheme directory
    markschemes_dir = get_absolute_path(settings.markschemes_dir)

    if not os.path.exists(markschemes_dir):
        print(f"\nError: Marking schemes directory not found: {markschemes_dir}")
        print("Please create the directory and add marking scheme files.")
        return

    # Find all markdown and text files
    files = []
    for ext in ['*.md', '*.txt']:
        files.extend(Path(markschemes_dir).glob(ext))

    if not files:
        print(f"\nNo marking scheme files found in: {markschemes_dir}")
        print("Please add .md or .txt files with marking schemes.")
        return

    print(f"\nFound {len(files)} marking scheme file(s)")

    # Process each file
    all_chunks = []

    for file_path in files:
        print(f"\nProcessing: {file_path.name}")

        try:
            # Load file
            content, metadata = load_marking_scheme(str(file_path))

            print(f"  Subject: {metadata.subject}")
            print(f"  Question: {metadata.question_id}")
            print(f"  Total Marks: {metadata.total_marks}")

            # Create chunks
            metadata_dict = {
                'subject': metadata.subject,
                'question_id': metadata.question_id,
                'total_marks': str(metadata.total_marks),
                'file_path': metadata.file_path
            }

            chunks = chunker.chunk_by_criteria(content, metadata_dict)
            print(f"  Created {len(chunks)} chunks")

            all_chunks.extend(chunks)

        except Exception as e:
            print(f"  Error processing file: {e}")
            continue

    # Add all chunks to vector database
    if all_chunks:
        print(f"\n{'=' * 60}")
        print(f"Indexing {len(all_chunks)} total chunks into vector database...")
        print(f"{'=' * 60}\n")

        retriever.add_documents(all_chunks)

        print("\n" + "=" * 60)
        print("INGESTION COMPLETE")
        print("=" * 60)
        print(f"Total documents in vector DB: {retriever.collection.count()}")
        print(f"Vector DB location: {settings.chroma_persist_dir}")
    else:
        print("\nNo chunks created. Ingestion failed.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest marking schemes into vector database")
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset vector database before ingestion'
    )

    args = parser.parse_args()

    ingest_marking_schemes(reset=args.reset)
