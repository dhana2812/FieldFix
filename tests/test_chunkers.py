import pytest
from src.chunkers import FixedChunker, StructureChunker, SemanticChunker

def test_fixed_chunker_basic():
    """Tests FixedChunker splits by N words with M overlap."""
    doc = {
        "doc_id": "test_doc",
        "title": "Test Title",
        "text": "word " * 100
    }
    chunker = FixedChunker(chunk_size=40, overlap=10)
    chunks = chunker.chunk_document(doc)
    
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk["word_count"] <= 40
        assert chunk["chunk_id"].startswith("test_doc#fix_40w_")

def test_structure_chunker_preserves_headings():
    """Tests StructureChunker parses Markdown headings into chunk metadata."""
    md_text = (
        "# Main Heading\n\n"
        "Introduction paragraph text here.\n\n"
        "## Sub Heading 1\n\n"
        "Detailed sub section content here.\n\n"
        "## Sub Heading 2\n\n"
        "Second sub section content here."
    )
    doc = {
        "doc_id": "struct_doc",
        "title": "Structure Test",
        "text": md_text
    }
    chunker = StructureChunker(max_words=200, min_words=5)
    chunks = chunker.chunk_document(doc)
    
    headings = [c.get("heading", "") for c in chunks]
    assert any("Sub Heading 1" in h for h in headings)
    assert any("Sub Heading 2" in h for h in headings)

def test_semantic_chunker_flushes_last_bucket():
    """
    CRITICAL TEST (Step 3 & Common Pitfalls):
    Verifies that SemanticChunker never drops the trailing leftover sentences.
    """
    sentences = (
        "Electric vehicle fast chargers operate at 400 volts direct current. "
        "The power modules convert alternating current into high voltage direct current. "
        "Liquid cooling keeps the silicone carbide switches within safe operating margins. "
        "This is the final trailing sentence that must not be forgotten or dropped."
    )
    doc = {
        "doc_id": "sem_doc",
        "title": "Semantic Test",
        "text": sentences
    }
    chunker = SemanticChunker(max_words=100, similarity_threshold=0.3)
    chunks = chunker.chunk_document(doc)
    
    assert len(chunks) >= 1
    # Check that the final sentence is present in the chunks
    combined_text = " ".join(c["text"] for c in chunks)
    assert "final trailing sentence that must not be forgotten or dropped" in combined_text
