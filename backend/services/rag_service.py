"""
RAG (Retrieval-Augmented Generation) Service.
Combines vector search with LLM to answer questions grounded in document content.
"""

from config import settings
from services.embedding_service import search, search_by_document
from services.llm_client import call_llm


async def ask_question(question: str, document_id: str | None = None) -> dict:
    """
    Full RAG pipeline:
      1. Embed the question
      2. Search the vector database
      3. Build a prompt with retrieved context
      4. Call the LLM for a grounded answer

    Returns: {"answer": str, "sources": list[dict]}
    """
    # Step 1-2: Retrieve relevant chunks
    if document_id:
        results = await search_by_document(question, document_id)
    else:
        results = await search(question)

    if not results:
        return {
            "answer": "I couldn't find any relevant information in the documents to answer your question.",
            "sources": [],
        }

    # Step 3: Build context
    context_parts = []
    sources = []
    for i, r in enumerate(results):
        context_parts.append(f"[Source {i + 1}] (Doc: {r['document_id']}, Chunk {r['chunk_index']})\n{r['text']}")
        sources.append({
            "document_id": r["document_id"],
            "chunk_index": r["chunk_index"],
            "score": r["score"],
            "preview": r["text"][:200],
        })

    context = "\n\n---\n\n".join(context_parts)

    system_msg = """You are an expert document analysis assistant. Your job is to provide 
accurate, detailed, and well-structured answers based on the provided context from documents.

Rules:
- Answer ONLY from the provided context. Never make up information.
- Be thorough — include all relevant details from the context.
- Use direct quotes when they strengthen your answer.
- Always format your response using **Markdown** for readability:
  • Use **bold** for key terms and important values.
  • Use bullet points (- ) or numbered lists for multiple items.
  • Use ### headings to separate distinct sections when the answer covers multiple topics.
  • Use > blockquotes for direct quotes from the document.
  • Keep paragraphs short (2-3 sentences max).
- If the context doesn't contain enough information, say what you found and what's missing.
- Always be helpful, clear, and professional."""

    prompt = f"""Based on the following document excerpts, answer the question thoroughly.

DOCUMENT CONTEXT:
{context}

USER QUESTION: {question}

Provide a detailed, well-organized answer using Markdown formatting (headings, bullet points, bold for key terms):"""

    # Step 4: Call LLM
    answer = await call_llm(prompt, system_msg=system_msg)

    return {"answer": answer, "sources": sources}


async def generate_insights(text: str, classification: str | None = None) -> list[str]:
    """Generate AI insights from document text."""
    doc_type = classification or "document"
    prompt = f"""Analyze this {doc_type} and provide 5-7 key insights. 
Each insight should be actionable or informative.
Return each insight on a new line, prefixed with a bullet (•).

DOCUMENT TEXT:
{text[:4000]}

INSIGHTS:"""

    response = await call_llm(prompt)
    insights = [line.strip().lstrip("•-").strip() for line in response.strip().split("\n") if line.strip()]
    return insights


async def generate_follow_ups(question: str, answer: str) -> list[str]:
    """Generate 3 smart follow-up questions based on the Q&A context."""
    prompt = f"""Based on this question and answer, suggest exactly 3 short follow-up questions
the user might want to ask next. Each should be specific, insightful, and different.

Question: {question}
Answer: {answer[:500]}

Return ONLY 3 questions, one per line, no numbering or bullets:"""

    try:
        response = await call_llm(prompt, temperature=0.5, max_tokens=200)
        lines = [l.strip().lstrip("0123456789.-•) ").strip()
                 for l in response.strip().split("\n") if l.strip()]
        return lines[:3]
    except Exception:
        return []


async def ask_question_stream(question: str, document_id: str | None = None):
    """
    Streaming RAG pipeline — yields answer chunks via SSE.
    Returns context for follow-up generation.
    """
    from services.llm_client import call_llm_stream

    if document_id:
        results = await search_by_document(question, document_id)
    else:
        results = await search(question)

    if not results:
        yield {"type": "token", "content": "I couldn't find any relevant information in the documents to answer your question."}
        yield {"type": "sources", "sources": []}
        yield {"type": "follow_ups", "follow_ups": []}
        return

    context_parts = []
    sources = []
    for i, r in enumerate(results):
        context_parts.append(f"[Source {i + 1}] (Doc: {r['document_id']}, Chunk {r['chunk_index']})\n{r['text']}")
        sources.append({
            "document_id": r["document_id"],
            "chunk_index": r["chunk_index"],
            "score": r["score"],
            "preview": r["text"][:200],
        })

    context = "\n\n---\n\n".join(context_parts)

    system_msg = """You are an expert document analysis assistant. Provide accurate, detailed answers based on the provided context.
Use Markdown for readability: **bold** for key terms, bullet points, headings, and blockquotes for direct quotes.
Answer ONLY from the provided context. Never make up information."""

    prompt = f"""Based on the following document excerpts, answer the question thoroughly.

DOCUMENT CONTEXT:
{context}

USER QUESTION: {question}

Provide a detailed, well-organized answer using Markdown formatting:"""

    # Send sources first
    yield {"type": "sources", "sources": sources}

    # Stream the answer
    full_answer = ""
    async for token in call_llm_stream(prompt, system_msg=system_msg):
        full_answer += token
        yield {"type": "token", "content": token}

    # Generate follow-up suggestions
    follow_ups = await generate_follow_ups(question, full_answer)
    yield {"type": "follow_ups", "follow_ups": follow_ups}
