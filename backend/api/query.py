"""
Query API — question-answering and summarization endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from database.models import QueryRequest, AnswerResponse, SummarizeRequest, SummaryResponse
from agents.qa_agent import answer_question
from agents.summarization_agent import get_summary
from services.auth_middleware import get_current_user

router = APIRouter(tags=["Query"])


@router.post("/ask-question", response_model=AnswerResponse)
async def ask_question_endpoint(request: QueryRequest, current_user: dict = Depends(get_current_user)):
    """
    Ask a question about uploaded documents.
    Uses RAG (Retrieval-Augmented Generation) for grounded answers.
    """
    try:
        result = await answer_question(request.question, request.document_id)
        return AnswerResponse(
            answer=result["answer"],
            sources=result["sources"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA failed: {str(e)}")


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_endpoint(request: SummarizeRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate a summary of a specific document.
    Results are cached for subsequent requests.
    """
    try:
        result = await get_summary(request.document_id, request.num_points)
        return SummaryResponse(
            document_id=result["document_id"],
            summary=result["summary"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")
