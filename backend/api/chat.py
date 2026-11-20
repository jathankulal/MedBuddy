"""Chat / RAG API route (POST /chat).

Flow:
1. Validate the request.
2. Load profile, medications and relevant episodes.
3. Run safety assessment BEFORE any Gemini call.
4. If emergency detected, return emergency guidance without calling Gemini.
5. If safety engine fails/invalid, return ERR_SAFETY_ENGINE.
6. Retrieve relevant PDF chunks.
7. Assemble grounded context.
8. Call Gemini.
9. Return answer, citations, safety info, context info, missing info, disclaimer, response_mode.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.database import ensure_data_dir, read_json, write_json
from backend.schemas import ChatRequest, ChatResponse, Citation
from backend.services.context_engine import ContextEngine
from backend.services.gemini_client import GeminiClient
from backend.services.retrieval_service import RetrievalService
from backend.services.safety_integration import run_safety_assessment
from backend.services.vector_store import VectorStore

router = APIRouter(prefix="", tags=["chat"])

DOCUMENTS_FILENAME = "documents_metadata.json"


def _load_documents() -> List[dict]:
    return read_json(settings.data_dir, DOCUMENTS_FILENAME, default=[]) or []


# Module-level singletons (initialized lazily)
_gemini_client: Optional[GeminiClient] = None
_vector_store: Optional[VectorStore] = None
_retrieval_service: Optional[RetrievalService] = None


def _get_gemini_client() -> Optional[GeminiClient]:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def _get_retrieval_service() -> RetrievalService:
    global _vector_store, _retrieval_service
    if _retrieval_service is None:
        _vector_store = VectorStore(data_dir=settings.data_dir)
        _retrieval_service = RetrievalService(vector_store=_vector_store)
    return _retrieval_service


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Handle a chat message with RAG and safety checks."""

    # --- Step 1: Safety assessment BEFORE any Gemini call ---
    try:
        safety_result = run_safety_assessment(
            data_dir=settings.data_dir,
            user_message=request.message,
        )
    except RuntimeError as exc:
        # Fail closed: safety engine unavailable or invalid
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ERR_SAFETY_ENGINE",
                    "message": str(exc),
                    "details": None,
                }
            },
        )

    safety_dict = safety_result.model_dump()

    # --- Step 2: Emergency short-circuit (no Gemini call) ---
    if safety_result.emergency:
        return ChatResponse(
            answer=(
                "Based on your message, this may be a medical emergency. "
                "Please seek immediate medical attention or call emergency "
                "services right away. This system is not a diagnostic tool."
            ),
            citations=[],
            safety=safety_dict,
            context_used=False,
            context_sources=[],
            missing_information=[],
            disclaimer=ContextEngine.get_disclaimer(),
            response_mode="emergency",
        )

    # --- Step 3: Load profile, medications, episodes ---
    profile = read_json(settings.data_dir, "profile.json", default=None) or {}
    medications = read_json(settings.data_dir, "medications.json", default=[]) or []
    episodes = read_json(settings.data_dir, "episodes.json", default=[]) or []

    # If a specific episode is requested, filter to it
    if request.episode_id:
        episodes = [ep for ep in episodes if ep.get("id") == request.episode_id]

    # --- Step 4: Retrieve relevant document chunks ---
    retrieval = _get_retrieval_service()
    document_chunks = retrieval.retrieve(
        query=request.message,
        document_ids=request.document_ids,
        n_results=5,
    )

    citations: List[Citation] = []
    for chunk in document_chunks:
        citations.append(
            Citation(
                document_id=chunk["document_id"],
                filename=chunk["filename"],
                page_number=chunk["page_number"],
                excerpt=chunk["text"][:500],
                chunk_id=chunk["chunk_id"],
                relevance_score=chunk.get("relevance_score"),
            )
        )

    context_used = len(document_chunks) > 0

    # --- Step 5: Assemble grounded context ---
    context_str = ContextEngine.build_context(
        profile=profile,
        medications=medications,
        episodes=episodes,
        document_chunks=document_chunks,
    )

    missing_info = ContextEngine.identify_missing_information(
        profile=profile,
        medications=medications,
        episodes=episodes,
        document_chunks=document_chunks,
        user_message=request.message,
    )

    # --- Step 6: Call Gemini ---
    context_sources: List[str] = []
    if profile and profile.get("id"):
        context_sources.append("profile")
    if medications:
        context_sources.append("medications")
    if episodes:
        context_sources.append("episodes")
    if document_chunks:
        context_sources.append("documents")

    gemini_client = _get_gemini_client()

    if not gemini_client.is_configured():
        # No API key: cannot generate. Return a helpful message.
        answer = (
            "I cannot generate an answer because the Gemini API key is not "
            "configured on the backend. Please set GEMINI_API_KEY and try again."
        )
    else:
        prompt = (
            f"{context_str}\n\n"
            f"USER QUESTION: {request.message}\n\n"
            f"Please answer based on the context above."
        )
        try:
            answer = gemini_client.generate(prompt)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "code": "ERR_GEMINI",
                        "message": str(exc),
                        "details": None,
                    }
                },
            )

    return ChatResponse(
        answer=answer,
        citations=citations,
        safety=safety_dict,
        context_used=context_used,
        context_sources=context_sources,
        missing_information=missing_info if missing_info else None,
        disclaimer=ContextEngine.get_disclaimer(),
        response_mode="normal",
    )
