"""
Recursive text chunking with configurable size and overlap.
"""

from config import settings


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[str]:
    """
    Split text into overlapping chunks using paragraph/sentence boundaries.

    Args:
        text:          The full document text.
        chunk_size:    Max characters per chunk (default from config).
        chunk_overlap: Overlap between chunks (default from config).

    Returns:
        List of text chunks.
    """
    chunk_size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

    if not text or not text.strip():
        return []

    # Try splitting by paragraphs first, then sentences, then words
    separators = ["\n\n", "\n", ". ", " "]
    return _recursive_split(text, separators, chunk_size, chunk_overlap)


def _recursive_split(
    text: str,
    separators: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Recursively split text using progressively finer separators."""
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    # Pick the best separator
    separator = separators[-1]
    for sep in separators:
        if sep in text:
            separator = sep
            break

    parts = text.split(separator)
    chunks: list[str] = []
    current_chunk = ""

    for part in parts:
        candidate = (current_chunk + separator + part).strip() if current_chunk else part.strip()

        if len(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            # Save what we have
            if current_chunk:
                chunks.append(current_chunk)
            # If single part is larger than chunk_size, recurse with finer separator
            if len(part) > chunk_size and len(separators) > 1:
                sub_chunks = _recursive_split(
                    part,
                    separators[1:],
                    chunk_size,
                    chunk_overlap,
                )
                chunks.extend(sub_chunks)
                current_chunk = ""
            else:
                current_chunk = part.strip()

    if current_chunk:
        chunks.append(current_chunk)

    # Re-add overlap between consecutive chunks
    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped: list[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-chunk_overlap:]
            merged = prev_tail + " " + chunks[i]
            overlapped.append(merged[:chunk_size])
        return overlapped

    return chunks
