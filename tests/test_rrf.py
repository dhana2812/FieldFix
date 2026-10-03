import pytest
from src.retrieval.rrf import reciprocal_rank_fusion
from hybrid import rrf_fuse

def test_rrf_scoring_math():
    """
    Tests reciprocal rank fusion calculation:
    score(d) = sum 1 / (60 + rank)
    """
    list_bm25 = [
        {"chunk_id": "c_A", "title": "Doc A"},
        {"chunk_id": "c_B", "title": "Doc B"},
        {"chunk_id": "c_C", "title": "Doc C"}
    ]
    list_vector = [
        {"chunk_id": "c_B", "title": "Doc B"},
        {"chunk_id": "c_A", "title": "Doc A"},
        {"chunk_id": "c_D", "title": "Doc D"}
    ]
    
    # Run fusion
    fused = reciprocal_rank_fusion([list_bm25, list_vector], k=60, top_n=4)
    
    # Expected scores:
    # c_A: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.0163934 + 0.0161290 = 0.032522
    # c_B: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.032522
    # c_C: 1/(60+3) = 1/63 = 0.015873
    # c_D: 1/(60+3) = 1/63 = 0.015873
    
    score_A = (1.0 / 61) + (1.0 / 62)
    score_C = 1.0 / 63
    
    # First two must be c_A and c_B (tied for top rank)
    top_2_ids = {fused[0]["chunk_id"], fused[1]["chunk_id"]}
    assert top_2_ids == {"c_A", "c_B"}
    assert pytest.approx(fused[0]["rrf_score"], abs=1e-5) == round(score_A, 6)
    
    # Items appearing in both lists must strictly outrank items appearing only in one
    assert fused[0]["rrf_score"] > fused[2]["rrf_score"]
    assert pytest.approx(fused[2]["rrf_score"], abs=1e-5) == round(score_C, 6)

def test_rrf_top_n_cutoff():
    """Verifies RRF respects the top_n candidate cutoff."""
    list_a = [{"chunk_id": f"c_{i}"} for i in range(10)]
    list_b = [{"chunk_id": f"c_{i}"} for i in range(10, 20)]
    
    fused = reciprocal_rank_fusion([list_a, list_b], k=60, top_n=5)
    assert len(fused) == 5
