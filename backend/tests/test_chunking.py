from utils.chunking import chunk_text


def test_chunk_text_empty():
    """Verify that empty text returns an empty list of chunks."""
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_short():
    """Verify that text shorter than chunk size returns a single chunk."""
    text = "Hello world. This is a short text."
    chunks = chunk_text(text, chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_split():
    """Verify that text is split correctly when exceeding chunk size."""
    text = "Paragraph one is short.\n\nParagraph two is also short.\n\nParagraph three is the final paragraph."
    # Set chunk_size to fit about one paragraph
    chunks = chunk_text(text, chunk_size=40, chunk_overlap=0)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 40


def test_chunk_text_overlap():
    """Verify that overlap text is appended to subsequent chunks."""
    text = "WordOne WordTwo WordThree WordFour WordFive"
    chunks = chunk_text(text, chunk_size=20, chunk_overlap=8)
    assert len(chunks) > 1
    # Check that subsequent chunks share content from the tail of the previous chunk
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-8:]
        # At least one word from the overlap tail should appear in the next chunk
        tail_words = prev_tail.split()
        assert any(word in chunks[i] for word in tail_words if word)
