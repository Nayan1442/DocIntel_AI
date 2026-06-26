"""
QA Agent — handles question-answering using the RAG service.
Manages conversation context and provides sourced answers.
"""

from services.rag_service import ask_question


async def answer_question(question: str, document_id: str | None = None) -> dict:
    """
    Process a user question and return a grounded answer.

    Args:
        question:     The user's question.
        document_id:  Optional — scope answer to a specific document.

    Returns:
        {"answer": str, "sources": list[dict]}
    """
    if not question or not question.strip():
        return {
            "answer": "Please provide a valid question.",
            "sources": [],
        }

    result = await ask_question(question, document_id)
    return result
