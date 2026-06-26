"""
Document Comparison Agent — compares two documents and highlights differences.
Uses LLM to generate a structured comparison analysis.
"""

from services.llm_client import call_llm
from database.db import get_db
from bson import ObjectId


async def compare_documents(doc_id_1: str, doc_id_2: str) -> dict:
    """
    Compare two documents and generate a detailed analysis of differences.

    Returns:
        {
            "doc_1": { "id", "name", "classification" },
            "doc_2": { "id", "name", "classification" },
            "comparison": str,
            "similarities": list[str],
            "differences": list[str],
            "recommendation": str
        }
    """
    db = get_db()

    doc1 = await db.documents.find_one({"_id": ObjectId(doc_id_1)})
    doc2 = await db.documents.find_one({"_id": ObjectId(doc_id_2)})

    if not doc1:
        raise ValueError(f"Document 1 not found: {doc_id_1}")
    if not doc2:
        raise ValueError(f"Document 2 not found: {doc_id_2}")

    text1 = doc1.get("text_content", "")[:4000]
    text2 = doc2.get("text_content", "")[:4000]

    if not text1 or not text2:
        raise ValueError("Both documents must have text content for comparison.")

    system_msg = """You are an expert document comparison analyst. Your job is to compare two documents 
and identify key similarities, differences, and provide actionable insights.
Be thorough, specific, and well-organized in your analysis."""

    prompt = f"""Compare these two documents in detail:

═══ DOCUMENT 1: {doc1.get('original_name', 'Document 1')} ═══
Type: {doc1.get('classification', 'unknown')}
Content:
{text1}

═══ DOCUMENT 2: {doc2.get('original_name', 'Document 2')} ═══
Type: {doc2.get('classification', 'unknown')}
Content:
{text2}

Provide your analysis in this exact format:

OVERALL COMPARISON:
[2-3 sentence overview of how these documents relate to each other]

SIMILARITIES:
• [similarity 1]
• [similarity 2]
• [similarity 3]

KEY DIFFERENCES:
• [difference 1]
• [difference 2]
• [difference 3]

RECOMMENDATION:
[1-2 sentences of actionable insight based on the comparison]"""

    response = await call_llm(prompt, system_msg=system_msg)

    # Parse the response into structured sections
    similarities = []
    differences = []
    comparison = ""
    recommendation = ""

    current_section = None
    for line in response.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "OVERALL COMPARISON" in line.upper():
            current_section = "comparison"
            continue
        elif "SIMILARITIES" in line.upper():
            current_section = "similarities"
            continue
        elif "KEY DIFFERENCES" in line.upper() or "DIFFERENCES" in line.upper():
            current_section = "differences"
            continue
        elif "RECOMMENDATION" in line.upper():
            current_section = "recommendation"
            continue

        clean = line.lstrip("•-*").strip()
        if not clean:
            continue

        if current_section == "comparison":
            comparison += clean + " "
        elif current_section == "similarities":
            similarities.append(clean)
        elif current_section == "differences":
            differences.append(clean)
        elif current_section == "recommendation":
            recommendation += clean + " "

    return {
        "doc_1": {
            "id": doc_id_1,
            "name": doc1.get("original_name", ""),
            "classification": doc1.get("classification"),
        },
        "doc_2": {
            "id": doc_id_2,
            "name": doc2.get("original_name", ""),
            "classification": doc2.get("classification"),
        },
        "comparison": comparison.strip() or response,
        "similarities": similarities,
        "differences": differences,
        "recommendation": recommendation.strip(),
    }
