import pytest
import math
from src.retrieval.bm25 import BM25Index

def test_bm25_toy_math_proof():
    """
    Verifies the hand-checked mathematical proof on the 2-chunk toy corpus:
    Chunk 1 (D1): 'DC-150 warranty warranty'
    Chunk 2 (D2): 'standard warranty policy'
    """
    toy_chunks = [
        {"chunk_id": "toy_001", "doc_id": "toy", "text": "DC-150 warranty warranty"},
        {"chunk_id": "toy_002", "doc_id": "toy", "text": "standard warranty policy"}
    ]
    
    bm25 = BM25Index(k1=1.5, b=0.75)
    bm25.fit(toy_chunks)
    
    assert bm25.num_docs == 2
    assert bm25.doc_frequencies["dc-150"] == 1
    assert bm25.doc_frequencies["warranty"] == 2
    
    # Mathematical RSJ IDF verification:
    # IDF(q) = ln( (N - df + 0.5)/(df + 0.5) + 1 )
    # IDF('dc-150') = ln( (2 - 1 + 0.5)/(1 + 0.5) + 1 ) = ln(1.0 + 1) = ln(2.0) approx 0.693147
    # IDF('warranty') = ln( (2 - 2 + 0.5)/(2 + 0.5) + 1 ) = ln(0.2 + 1) = ln(1.2) approx 0.182322
    expected_idf_dc150 = math.log(((2 - 1 + 0.5) / (1 + 0.5)) + 1.0)
    expected_idf_warranty = math.log(((2 - 2 + 0.5) / (2 + 0.5)) + 1.0)
    
    assert pytest.approx(bm25.idf["dc-150"], abs=1e-4) == expected_idf_dc150
    assert pytest.approx(bm25.idf["warranty"], abs=1e-4) == expected_idf_warranty
    
    # Assert rarer term has higher IDF
    assert bm25.idf["dc-150"] > bm25.idf["warranty"]
    assert pytest.approx(bm25.idf["dc-150"] / bm25.idf["warranty"], abs=0.05) == 3.80

    # Query scoring verification for 'DC-150 warranty'
    results = bm25.search("DC-150 warranty", top_k=2)
    assert len(results) == 2
    assert results[0]["chunk_id"] == "toy_001"
    assert results[1]["chunk_id"] == "toy_002"
    assert pytest.approx(results[0]["bm25_score"], abs=1e-3) == 0.9536
    assert pytest.approx(results[1]["bm25_score"], abs=1e-3) == 0.1823

def test_bm25_tokenization_preserves_error_codes():
    """Verifies tokenizer preserves technical codes like 'E-217', 'v4.3.0', 'DC-150'."""
    text = "The DC-150 charger threw error E-217 in firmware v4.3.0 at site PNE-01."
    tokens = BM25Index.tokenize(text)
    assert "dc-150" in tokens
    assert "e-217" in tokens
    assert "v4.3.0" in tokens
    assert "pne-01" in tokens
