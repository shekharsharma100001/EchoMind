from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import PROCESSED_DIR, RAG_TOP_K
from app.services.rag_service import retrieve_relevant_chunks
from app.services.llm_service import answer_question_with_rag_context

router = APIRouter(prefix="/api", tags=["Q&A"])


class QuestionRequest(BaseModel):
    question: str


@router.post("/qa/{file_id}")
async def ask_question(file_id: str, payload: QuestionRequest):
    try:
        question = (payload.question or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question is required.")

        processed_dir = PROCESSED_DIR / file_id
        if not processed_dir.exists():
            raise HTTPException(status_code=404, detail="Processed file not found.")

        retrieved_chunks = retrieve_relevant_chunks(
            question=question,
            processed_dir=str(processed_dir),
            top_k=RAG_TOP_K,
        )

        answer = answer_question_with_rag_context(
            question=question,
            retrieved_chunks=retrieved_chunks,
        )

        return {
            "file_id": file_id,
            "question": question,
            "answer": answer,
            "retrieved_chunks": retrieved_chunks,
            "retrieved_count": len(retrieved_chunks),
        }

    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(exc)}") from exc