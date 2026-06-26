import logging
from services.llm_client import call_llm

logger = logging.getLogger(__name__)


async def summarize_document(text: str, num_points: int = 5) -> str:
    """
    Generate a bullet-point summary of the document text.

    Args:
        text:       Full document text.
        num_points: Number of bullet points in the summary.

    Returns:
        Summary string.
    """
    # Truncate very long documents
    text_sample = text[:6000]

    prompt = f"""Summarize the following document in a clear, well-structured format using Markdown.

Instructions:
1. Start with a **one-sentence overview** of what this document is about.
2. Then provide exactly {num_points} key points as bullet points using "- " prefix.
3. Each bullet should start with a **bold key phrase** followed by a brief explanation.
4. End with a one-line "**Bottom line:**" takeaway.

Example format:
This document is a [type] about [topic].

- **Key Point One** — Brief explanation of this point.
- **Key Point Two** — Brief explanation of this point.

**Bottom line:** One sentence summary takeaway.

DOCUMENT TEXT:
{text_sample}

SUMMARY:"""

    try:
        return await call_llm(prompt, temperature=0.2, max_tokens=1024)

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return f"Summarization failed: {str(e)}"

