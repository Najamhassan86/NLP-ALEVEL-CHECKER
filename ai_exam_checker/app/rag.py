"""
RAG (Retrieval-Augmented Generation) module.
Handles document chunking, indexing, and semantic retrieval using ChromaDB.
"""

import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
from app.settings import settings, get_absolute_path
from app.models import DocumentChunk, RetrievalResult, MarkingSchemeMetadata
from app.embeddings import get_embedding_generator
import re


class Chunker:
    """
    Chunks marking scheme documents into semantically meaningful pieces.
    Implements criterion-based chunking for exam marking schemes.
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize chunker with size and overlap parameters.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_by_criteria(self, text: str, metadata: Dict[str, str]) -> List[DocumentChunk]:
        """
        Chunk marking scheme by criteria (bullet points, numbered items).
        This is more semantically meaningful than fixed-size chunking.

        Args:
            text: Marking scheme text
            metadata: Document metadata

        Returns:
            List of DocumentChunk objects
        """
        chunks = []

        # Split by common marking scheme patterns
        # Pattern 1: Numbered criteria (1., 2., etc.)
        # Pattern 2: Bullet points (-, *, •)
        # Pattern 3: Double newlines (paragraphs)

        # First, try to split by numbered or bulleted criteria
        criteria_pattern = r'(?:^|\n)(?:\d+\.|[-*•])\s+'
        sections = re.split(criteria_pattern, text)

        # Remove empty sections
        sections = [s.strip() for s in sections if s.strip()]

        if len(sections) > 1:
            # Successfully split by criteria
            for idx, section in enumerate(sections):
                if section:
                    chunk = DocumentChunk(
                        content=section,
                        metadata={
                            **metadata,
                            'chunk_index': str(idx),
                            'chunk_type': 'criterion'
                        }
                    )
                    chunks.append(chunk)
        else:
            # Fallback to paragraph-based chunking
            paragraphs = text.split('\n\n')
            for idx, para in enumerate(paragraphs):
                if para.strip():
                    chunk = DocumentChunk(
                        content=para.strip(),
                        metadata={
                            **metadata,
                            'chunk_index': str(idx),
                            'chunk_type': 'paragraph'
                        }
                    )
                    chunks.append(chunk)

        # If still no chunks (very short document), use the whole text
        if not chunks:
            chunks.append(DocumentChunk(
                content=text,
                metadata={**metadata, 'chunk_index': '0', 'chunk_type': 'full'}
            ))

        return chunks

    def chunk_fixed_size(self, text: str, metadata: Dict[str, str]) -> List[DocumentChunk]:
        """
        Fallback chunking strategy using fixed size with overlap.

        Args:
            text: Text to chunk
            metadata: Document metadata

        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunk = DocumentChunk(
                content=chunk_text,
                metadata={
                    **metadata,
                    'chunk_index': str(len(chunks)),
                    'chunk_type': 'fixed_size'
                }
            )
            chunks.append(chunk)

            start = end - self.chunk_overlap

        return chunks


class VectorRetriever:
    """
    Handles vector storage and retrieval using ChromaDB.
    Core component of the RAG pipeline.
    """

    def __init__(self, persist_directory: str = None, collection_name: str = "marking_schemes"):
        """
        Initialize ChromaDB client and collection.

        Args:
            persist_directory: Directory to persist the vector database
            collection_name: Name of the ChromaDB collection
        """
        self.persist_dir = get_absolute_path(persist_directory or settings.chroma_persist_dir)
        self.collection_name = collection_name
        self.embedding_generator = get_embedding_generator()

        # Ensure directory exists
        os.makedirs(self.persist_dir, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Exam marking schemes for RAG retrieval"}
        )

        print(f"ChromaDB initialized at: {self.persist_dir}")
        print(f"Collection: {self.collection_name} (count: {self.collection.count()})")

    def add_documents(self, chunks: List[DocumentChunk]):
        """
        Add document chunks to the vector store.

        Args:
            chunks: List of DocumentChunk objects
        """
        if not chunks:
            return

        print(f"Adding {len(chunks)} chunks to vector store...")

        # Prepare data for ChromaDB
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        ids = [f"{chunk.metadata.get('subject', 'unknown')}_{chunk.metadata.get('question_id', 'unknown')}_{chunk.metadata.get('chunk_index', i)}"
               for i, chunk in enumerate(chunks)]

        # Generate embeddings
        embeddings = self.embedding_generator.encode_batch(documents)

        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        print(f"Successfully added {len(chunks)} chunks. Total count: {self.collection.count()}")

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Optional[Dict[str, str]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve most relevant chunks for a query using semantic search.

        Args:
            query: Query text (student answer)
            top_k: Number of results to retrieve
            filter_metadata: Optional metadata filters (e.g., subject, question_id)

        Returns:
            List of RetrievalResult objects with similarity scores
        """
        top_k = top_k or settings.top_k_retrieval

        # Generate query embedding
        query_embedding = self.embedding_generator.encode_single(query)

        # Build where clause for filtering
        where = None
        if filter_metadata:
            where = filter_metadata

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )

        # Parse results into RetrievalResult objects
        retrieval_results = []

        if results['documents'] and results['documents'][0]:
            for idx in range(len(results['documents'][0])):
                # ChromaDB returns distances, convert to similarity (1 - distance)
                distance = results['distances'][0][idx]
                similarity = 1 - distance

                # Only include results above threshold
                if similarity >= settings.similarity_threshold:
                    result = RetrievalResult(
                        content=results['documents'][0][idx],
                        metadata=results['metadatas'][0][idx],
                        similarity_score=round(similarity, 4)
                    )
                    retrieval_results.append(result)

        print(f"Retrieved {len(retrieval_results)} relevant chunks (threshold: {settings.similarity_threshold})")

        return retrieval_results

    def reset_collection(self):
        """Delete all documents from the collection"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Exam marking schemes for RAG retrieval"}
        )
        print(f"Collection {self.collection_name} reset")


# Global retriever instance
_retriever = None


def get_retriever() -> VectorRetriever:
    """
    Get or create the global retriever instance.

    Returns:
        VectorRetriever instance
    """
    global _retriever
    if _retriever is None:
        _retriever = VectorRetriever()
    return _retriever
