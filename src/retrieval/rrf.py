"""
FieldFix - Step 7: Hand-Implemented Reciprocal Rank Fusion (RRF)
Module: src.retrieval.rrf

Mathematical Formulation:
RRF_Score(d) = sum_{m in Models} [ 1 / (k + rank_m(d)) ]

Where:
- d is a retrieved chunk / document
- m is a retrieval model (e.g., BM25, Dense Vector)
- rank_m(d) is the 1-based ordinal rank of document d in model m's output
- k is the rank smoothing constant (default: k = 60, per Cormack, Clarke & Buettcher 2009)
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict


def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    k: int = 60,
    top_n: int = 5,
    id_key: str = "chunk_id"
) -> List[Dict[str, Any]]:
    """
    Pure Python Reciprocal Rank Fusion implementation for N arbitrary ranked result lists.
    
    score(d) = sum_{i=1}^M [ 1 / (k + rank_i(d)) ]
    """
    rrf_scores = defaultdict(float)
    item_map = {}
    rank_history = defaultdict(dict)
    score_history = defaultdict(dict)

    for list_idx, result_list in enumerate(ranked_lists):
        list_name = f"list_{list_idx + 1}"
        for rank, item in enumerate(result_list, 1):
            doc_id = item.get(id_key, str(item))
            rrf_scores[doc_id] += 1.0 / (k + rank)
            
            if doc_id not in item_map:
                item_map[doc_id] = item
                
            rank_history[doc_id][list_name] = rank
            
            # Record individual scores if available
            if "bm25_score" in item:
                score_history[doc_id]["bm25_score"] = item["bm25_score"]
            if "cosine_score" in item:
                score_history[doc_id]["cosine_score"] = item["cosine_score"]

    # Sort descending by RRF score
    sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda d: rrf_scores[d], reverse=True)

    fused = []
    for final_rank, doc_id in enumerate(sorted_doc_ids[:top_n], 1):
        record = item_map[doc_id].copy()
        record["rrf_score"] = round(rrf_scores[doc_id], 6)
        record["rrf_rank"] = final_rank
        record["ranks"] = rank_history[doc_id]
        record.update(score_history[doc_id])
        fused.append(record)

    return fused


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion (RRF) for combining multi-modal rankings (BM25 + Vector Search).
    
    Formula:
    RRF_Score(d) = sum_{m in Models} [ 1 / (k + rank_m(d)) ]
    
    Default smoothing constant k = 60 (Cormack et al., 2009).
    """
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fuses BM25 and Vector rankings into a single unified ranked list.
        """
        rrf_scores = defaultdict(float)
        chunk_map = {}
        bm25_ranks = {}
        vector_ranks = {}
        bm25_raw_scores = {}
        vector_raw_scores = {}

        # 1. Process BM25 rankings
        for rank, item in enumerate(bm25_results, 1):
            c_id = item["chunk_id"]
            rrf_scores[c_id] += 1.0 / (self.k + rank)
            chunk_map[c_id] = item
            bm25_ranks[c_id] = rank
            bm25_raw_scores[c_id] = item.get("bm25_score", 0.0)

        # 2. Process Vector rankings
        for rank, item in enumerate(vector_results, 1):
            c_id = item["chunk_id"]
            rrf_scores[c_id] += 1.0 / (self.k + rank)
            if c_id not in chunk_map:
                chunk_map[c_id] = item
            vector_ranks[c_id] = rank
            vector_raw_scores[c_id] = item.get("cosine_score", 0.0)

        # 3. Sort by fused RRF score descending
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        fused_results = []
        for fused_rank, c_id in enumerate(sorted_chunk_ids[:top_n], 1):
            base_item = chunk_map[c_id].copy()
            base_item["rrf_score"] = round(rrf_scores[c_id], 6)
            base_item["rrf_rank"] = fused_rank
            base_item["bm25_rank"] = bm25_ranks.get(c_id, None)
            base_item["vector_rank"] = vector_ranks.get(c_id, None)
            base_item["bm25_score"] = bm25_raw_scores.get(c_id, None)
            base_item["cosine_score"] = vector_raw_scores.get(c_id, None)
            fused_results.append(base_item)

        return fused_results
