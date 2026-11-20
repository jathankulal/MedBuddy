"""ChromaDB vector store wrapper with persistent local storage.

Persists vectors under DATA_DIR/chroma. Supports adding chunks, querying
similar chunks, filtering by document_id, and deleting documents.
"""

import os
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings


class VectorStore:
    """Persistent ChromaDB wrapper for document chunks."""

    COLLECTION_NAME = "medbuddy_documents"

    def __init__(self, data_dir: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.data_dir = Path(data_dir)
        self.persist_dir = self.data_dir / "chroma"
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Lazy-initialized embedding service
        from backend.services.embedding_service import EmbeddingService

        self.embedding_service = EmbeddingService(model_name=embedding_model)

        self._collection = None

    @property
    def collection(self):
        """Get or create the ChromaDB collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_chunks(self, chunks: List[dict]) -> None:
        """Add document chunks to the vector store.

        Each chunk dict must have: chunk_id, document_id, filename,
        page_number, text.
        """
        if not chunks:
            return

        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [
            {
                "document_id": c["document_id"],
                "filename": c["filename"],
                "page_number": c["page_number"],
            }
            for c in chunks
        ]

        embeddings = self.embedding_service.embed_texts(texts)

        # Delete any existing chunks with these IDs first (avoid duplicates on re-index)
        try:
            self.collection.delete(ids=ids)
        except Exception:
            pass

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def query(
        self,
        query_text: str,
        document_ids: Optional[List[str]] = None,
        n_results: int = 5,
    ) -> List[dict]:
        """Retrieve relevant chunks for a query.

        Returns a list of dicts with: chunk_id, document_id, filename,
        page_number, text, relevance_score.
        """
        query_embedding = self.embedding_service.embed_text(query_text)

        where_filter = None
        if document_ids:
            where_filter = {"document_id": {"$in": document_ids}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        chunks: List[dict] = []
        if not results["ids"] or not results["ids"][0]:
            return chunks

        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            # Convert cosine distance to a 0-1 relevance score
            relevance_score = max(0.0, 1.0 - distance)
            chunks.append(
                {
                    "chunk_id": results["ids"][0][i],
                    "document_id": results["metadatas"][0][i]["document_id"],
                    "filename": results["metadatas"][0][i]["filename"],
                    "page_number": results["metadatas"][0][i]["page_number"],
                    "text": results["documents"][0][i],
                    "relevance_score": relevance_score,
                }
            )

        return chunks

    def delete_document(self, document_id: str) -> None:
        """Delete all chunks belonging to a document."""
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as exc:
            raise RuntimeError(f"Failed to delete document chunks from vector store: {exc}") from exc

    def count(self) -> int:
        """Return total number of chunks in the store."""
        return self.collection.count()
