"""Reusable document retrieval module.

Retrieves relevant chunks for a user query and returns citation-ready
results with document name, ID, page number, chunk ID and excerpt.
"""

from typing import List, Optional

from backend.services.vector_store import VectorStore


class RetrievalService:
    """Retrieves relevant document chunks for RAG."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        n_results: int = 5,
    ) -> List[dict]:
        """Retrieve relevant chunks for a query.

        Returns a list of citation-ready dicts with:
        document_id, filename, page_number, chunk_id, text (excerpt),
        relevance_score.
        """
        return self.vector_store.query(
            query_text=query,
            document_ids=document_ids,
            n_results=n_results,
        )
