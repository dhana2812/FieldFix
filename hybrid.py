#!/usr/bin/env python3
"""
FieldFix - Step 7: Hybrid Search with Hand-Implemented Reciprocal Rank Fusion (RRF)

Goal:
Combine keyword (sparse BM25) and semantic (dense vector) retrieval strengths without
mixing incompatible, uncalibrated raw score distributions.

Formula:
RRF_Score(d) = sum_{m in {BM25, Vector}} [ 1 / (k + rank_m(d)) ]
where k = 60 (rank-smoothing constant).
"""

import os
import sys
import argparse
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.retrieval.vector_store import VectorStore
from src.retrieval.embeddings import EmbeddingClient
from src.retrieval.bm25 import BM25Index


# -------------------------------------------------------------------------------------
# HAND-IMPLEMENTED RECIPROCAL RANK FUSION (RRF)
# -------------------------------------------------------------------------------------
def rrf_fuse(
    bm25_results: List[Dict[str, Any]],
    vector_results: List[Dict[str, Any]],
    k: int = 60,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Combines sparse (BM25) and dense (Vector) ranked result lists using
    hand-implemented Reciprocal Rank Fusion.
    
    Formula:
        score(d) = sum_{m in Models} 1 / (k + rank_m(d))
    
    Args:
        bm25_results: List of dicts returned by BM25Index.search()
        vector_results: List of dicts returned by VectorStore.search()
        k: Smoothing constant (default: 60)
        top_n: Number of fused results to return
        
    Returns:
        List of fused chunk dicts sorted descending by RRF score.
    """
    rrf_scores = defaultdict(float)
    chunk_map: Dict[str, Dict[str, Any]] = {}
    bm25_ranks: Dict[str, int] = {}
    vector_ranks: Dict[str, int] = {}
    bm25_scores: Dict[str, float] = {}
    vector_scores: Dict[str, float] = {}

    # 1. Accumulate reciprocal ranks from BM25 list
    for rank, item in enumerate(bm25_results, 1):
        c_id = item["chunk_id"]
        rrf_scores[c_id] += 1.0 / (k + rank)
        chunk_map[c_id] = item
        bm25_ranks[c_id] = rank
        bm25_scores[c_id] = item.get("bm25_score", 0.0)

    # 2. Accumulate reciprocal ranks from Vector list
    for rank, item in enumerate(vector_results, 1):
        c_id = item["chunk_id"]
        rrf_scores[c_id] += 1.0 / (k + rank)
        if c_id not in chunk_map:
            chunk_map[c_id] = item
        vector_ranks[c_id] = rank
        vector_scores[c_id] = item.get("cosine_score", 0.0)

    # 3. Sort all candidate chunk IDs descending by fused RRF score
    sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

    # 4. Construct final fused result objects
    fused_results = []
    for fused_rank, c_id in enumerate(sorted_ids[:top_n], 1):
        base_item = chunk_map[c_id].copy()
        base_item["rrf_score"] = round(rrf_scores[c_id], 6)
        base_item["rrf_rank"] = fused_rank
        base_item["bm25_rank"] = bm25_ranks.get(c_id, None)
        base_item["vector_rank"] = vector_ranks.get(c_id, None)
        base_item["bm25_score"] = bm25_scores.get(c_id, 0.0)
        base_item["cosine_score"] = vector_scores.get(c_id, 0.0)
        
        # Calculate naive raw addition score for direct comparison
        raw_b = base_item["bm25_score"] if base_item["bm25_score"] is not None else 0.0
        raw_v = base_item["cosine_score"] if base_item["cosine_score"] is not None else 0.0
        base_item["naive_raw_sum"] = round(raw_b + raw_v, 4)
        
        fused_results.append(base_item)

    return fused_results


def naive_sum_fuse(
    bm25_results: List[Dict[str, Any]],
    vector_results: List[Dict[str, Any]],
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Combines results via naive raw addition: score = bm25_score + cosine_score.
    Provided for pedagogical and empirical comparison against RRF.
    """
    chunk_map = {}
    combined_scores = defaultdict(float)

    for item in bm25_results:
        cid = item["chunk_id"]
        combined_scores[cid] += item.get("bm25_score", 0.0)
        chunk_map[cid] = item

    for item in vector_results:
        cid = item["chunk_id"]
        combined_scores[cid] += item.get("cosine_score", 0.0)
        if cid not in chunk_map:
            chunk_map[cid] = item

    sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
    results = []
    for rank, cid in enumerate(sorted_ids[:top_n], 1):
        item = chunk_map[cid].copy()
        item["naive_rank"] = rank
        item["naive_score"] = round(combined_scores[cid], 4)
        results.append(item)
    return results


def run_hybrid_retrieval(single_query: Optional[str] = None, k_param: int = 60, top_n: int = 5):
    print("=" * 90)
    print(f"[*] FieldFix - Step 7: Hybrid Search with Reciprocal Rank Fusion (RRF, k={k_param})")
    print("=" * 90)
    
    # ---------------------------------------------------------------------------------
    # Three-sentence explanation of why simply adding raw BM25 score to cosine score is wrong
    # ---------------------------------------------------------------------------------
    print("\n" + "-" * 90)
    print("[*] WHY SIMPLY ADDING RAW BM25 TO COSINE SIMILARITY IS WRONG (Theoretical Rationale):")
    print("-" * 90)
    explanation = (
        "1. Incompatible Scales & Bounds: BM25 produces unbounded positive scores (typically 0 to 25+)\n"
        "   scaling with query length and term frequency, whereas Cosine Similarity is strictly bounded\n"
        "   between [-1.0, 1.0] (often 0.20 to 0.85 for dense embeddings).\n"
        "2. Score Dominance: Simply adding raw scores allows BM25's large numerical magnitude to overwhelm\n"
        "   the cosine signal by 10x to 30x, effectively nullifying semantic understanding whenever any\n"
        "   lexical match exists.\n"
        "3. Incomparable Distributions: BM25 reflects discrete token term rarity (IDF) and saturation, while\n"
        "   cosine similarity reflects geometric vector angles in continuous latent space; RRF solves this\n"
        "   by fusing ordinal rank positions (1 / (k + rank_i)) rather than uncalibrated raw scores."
    )
    print(explanation)
    print("-" * 90 + "\n")

    # Load Vector Store
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vector_store.json")
    if not os.path.exists(data_path):
        print(f"[Error] Vector store not found at {data_path}. Please run 'python ingest.py' first.")
        return

    vector_store = VectorStore().load(data_path)
    embedder = EmbeddingClient()
    
    print(f"Loaded Vector Store: {len(vector_store.records)} records | Watermark: {vector_store.corpus_id}")
    print(f"Embedding Provider:  {embedder.model_name} ({embedder.dimension}d)\n")

    # Initialize BM25 Index over the same corpus chunks
    chunks_for_bm25 = []
    for r in vector_store.records:
        chunks_for_bm25.append({
            "chunk_id": r["chunk_id"],
            "doc_id": r["doc_id"],
            "heading": r["metadata"].get("heading", ""),
            "text": r["content"]
        })
    bm25 = BM25Index(k1=1.5, b=0.75).fit(chunks_for_bm25)

    if single_query:
        test_scenarios = [{
            "scenario": "Ad-Hoc Technician Query",
            "query": single_query
        }]
    else:
        test_scenarios = [
            {
                "scenario": "Hero Question: Multi-Document Fault Diagnostic",
                "query": "Three DC-150s at the Pune Expressway site are throwing E-217 since last night. Is this a hardware fault or the known firmware issue, and what fixed it last time?"
            },
            {
                "scenario": "Colloquial Query vs Technical Specification: Warranty & Power Module",
                "query": "how long is the power module covered if it dies?"
            },
            {
                "scenario": "Alphanumeric Fault Code & Troubleshooting",
                "query": "E-217 CAN bus timeout resolution"
            }
        ]

    for item in test_scenarios:
        q = item["query"]
        print("=" * 90)
        print(f"[*] Scenario: {item['scenario']}")
        print(f"    Query:    \"{q}\"")
        print("=" * 90)
        
        # 1. Retrieve BM25 candidates (top-10)
        bm25_hits = bm25.search(q, top_k=10)
        
        # 2. Retrieve Dense Vector candidates (top-10)
        q_vec = embedder.embed_query(q)
        vec_hits = vector_store.search(q_vec, top_k=10, corpus_id=vector_store.corpus_id)
        
        # 3. Apply Hand-Implemented RRF (k=k_param, top_n=top_n)
        fused_hits = rrf_fuse(bm25_hits, vec_hits, k=k_param, top_n=top_n)
        
        # 4. Apply Naive Raw Sum for comparison
        naive_hits = naive_sum_fuse(bm25_hits, vec_hits, top_n=top_n)
        naive_rank_map = {h["chunk_id"]: h["naive_rank"] for h in naive_hits}

        # Display fused ranking breakdown table
        print(f"\n{'RRF Rank':<9} | {'RRF Score':<10} | {'BM25 Rank (Score)':<18} | {'Vector Rank (Score)':<20} | {'Doc ID':<22} | {'Heading'}")
        print("-" * 90)
        
        for h in fused_hits:
            bm_str = f"#{h['bm25_rank']} ({h['bm25_score']:.2f})" if h['bm25_rank'] is not None else "Unranked"
            vc_str = f"#{h['vector_rank']} ({h['cosine_score']:.2f})" if h['vector_rank'] is not None else "Unranked"
            doc_str = h['doc_id'][:21]
            head_str = h.get('heading', h.get('metadata', {}).get('heading', 'General'))
            head_clean = head_str.encode('ascii', 'replace').decode('ascii')[:25]
            
            print(f"#{h['rrf_rank']:<8} | {h['rrf_score']:>9.6f} | {bm_str:<18} | {vc_str:<20} | {doc_str:<22} | {head_clean}")
            
        print("\n[Top-1 Fused Evidence Chunk Preview]:")
        top_chunk = fused_hits[0]
        preview_text = top_chunk.get('text', top_chunk.get('content', '')).replace('\n', ' ')[:130]
        preview_clean = preview_text.encode('ascii', 'replace').decode('ascii')
        print(f"  Chunk ID: {top_chunk['chunk_id']}")
        print(f"  Snippet:  \"{preview_clean}...\"\n")


def main():
    parser = argparse.ArgumentParser(description="FieldFix - Step 7: Hybrid Retrieval with Reciprocal Rank Fusion (RRF)")
    parser.add_argument("query", nargs="?", type=str, help="Optional custom query string")
    parser.add_argument("--k", type=int, default=60, help="RRF rank smoothing constant (default: 60)")
    parser.add_argument("--top_n", type=int, default=5, help="Number of fused results to return (default: 5)")
    args = parser.parse_args()

    run_hybrid_retrieval(single_query=args.query, k_param=args.k, top_n=args.top_n)


if __name__ == "__main__":
    main()
