#!/usr/bin/env python3
"""
FieldFix - Step 6: Semantic Vector Search & BM25 vs Vector Head-to-Head Comparison
"""
import os
import sys
import argparse
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.retrieval.vector_store import VectorStore
from src.retrieval.embeddings import EmbeddingClient
from src.retrieval.bm25 import BM25Index

def run_comparison(vector_store: VectorStore, embedder: EmbeddingClient, bm25: BM25Index):
    """Runs the benchmark head-to-head comparison scenarios."""
    scenarios = [
        {
            "scenario_num": 1,
            "title": "Scenario 1: Semantic Intent & Vocabulary Mismatch (Vector Search Wins)",
            "query": "how long is the power module covered if it dies?",
            "analysis": (
                "The engineer uses colloquial language ('dies', 'covered') not found literally in the text. "
                "The technical manual uses formal phrasing: 'Hardware Warranty and Coverage Schedule', "
                "'dielectric breakdown', and 'thermal fatigue'. Vector search captures the latent semantic "
                "geometry and ranks the 5-year power module warranty table at Rank #1. In contrast, BM25 "
                "suffers from vocabulary mismatch and returns irrelevant error codes."
            ),
            "top_k": 3
        },
        {
            "scenario_num": 2,
            "title": "Scenario 2: Exact Alphanumeric Identifier & Error Code (BM25 Wins)",
            "query": "E-217",
            "analysis": (
                "The technician searches for a specific alphanumeric fault code. BM25 leverages high "
                "Inverse Document Frequency (IDF) for the rare token 'e-217', pinning the exact firmware "
                "advisory and troubleshooting table at Rank #1. Dense embeddings distribute representation "
                "across general communication and electrical fault spaces."
            ),
            "top_k": 3
        },
        {
            "scenario_num": 3,
            "title": "Scenario 3: Specific Firmware Version & Bug Release (BM25 Wins)",
            "query": "fw 4.3",
            "analysis": (
                "Short version specifier 'fw 4.3'. BM25's exact token matching zeroes directly into "
                "the firmware release notes changelog, whereas dense embeddings match general firmware "
                "procedures across multiple documents."
            ),
            "top_k": 3
        }
    ]

    print("=" * 90)
    print(" " * 20 + "STEP 6: HEAD-TO-HEAD RETRIEVAL BENCHMARK")
    print("=" * 90)

    for sc in scenarios:
        q = sc["query"]
        top_k = sc["top_k"]
        print("\n" + "#" * 90)
        print(f"[*] {sc['title']}")
        print(f"Query: \"{q}\"")
        print(f"Core Mechanism: {sc['analysis']}")
        print("-" * 90)

        # 1. Vector Search (Semantic)
        q_vec = embedder.embed_query(q)
        vec_hits = vector_store.search(q_vec, top_k=top_k, corpus_id=vector_store.corpus_id)

        # 2. BM25 Search (Sparse Keyword)
        bm25_hits = bm25.search(q, top_k=top_k)

        # Side-by-Side Display
        print("\n--- [ Dense Vector Retrieval (text-embedding-3-small, Cosine Similarity) ] ---")
        print(f"{'Rank':<5} | {'Score':<8} | {'Doc ID':<24} | {'Chunk ID':<36} | {'Heading / Preview'}")
        print("-" * 90)
        for h in vec_hits:
            heading = h['metadata']['heading'].encode('ascii', 'replace').decode('ascii')
            preview = h['content'].replace('\n', ' ')[:50].encode('ascii', 'replace').decode('ascii')
            chunk_id = h['chunk_id'][:34]
            print(f"#{h['vector_rank']:<4} | {h['cosine_score']:>7.4f} | {h['doc_id']:<24} | {chunk_id:<36} | [{heading}] {preview}...")

        print("\n--- [ Sparse Keyword Retrieval (Okapi BM25, k1=1.5, b=0.75) ] ---")
        print(f"{'Rank':<5} | {'Score':<8} | {'Doc ID':<24} | {'Chunk ID':<36} | {'Heading / Preview'}")
        print("-" * 90)
        for h in bm25_hits:
            heading = h['heading'].encode('ascii', 'replace').decode('ascii')
            preview = h['text'].replace('\n', ' ')[:50].encode('ascii', 'replace').decode('ascii')
            chunk_id = h['chunk_id'][:34]
            print(f"#{h['bm25_rank']:<4} | {h['bm25_score']:>7.4f} | {h['doc_id']:<24} | {chunk_id:<36} | [{heading}] {preview}...")

def run_single_query(query: str, vector_store: VectorStore, embedder: EmbeddingClient, top_k: int = 5):
    """Executes a single vector search query and prints ranked results."""
    print("=" * 90)
    print(f"[*] Executing Semantic Vector Search for Query: \"{query}\"")
    print(f"Corpus Filter Watermark: {vector_store.corpus_id}")
    print(f"Embedding Model: {embedder.model_name} ({embedder.dimension}d)")
    print("=" * 90)

    q_vec = embedder.embed_query(query)
    results = vector_store.search(q_vec, top_k=top_k, corpus_id=vector_store.corpus_id)

    if not results:
        print("[!] No matching chunks found for the given corpus ID.")
        return

    print(f"\n{'Rank':<5} | {'Score (Cos)':<12} | {'Doc ID':<24} | {'Chunk ID':<36} | {'Heading / Content Preview'}")
    print("-" * 90)
    for h in results:
        heading = h['metadata']['heading'].encode('ascii', 'replace').decode('ascii')
        preview = h['content'].replace('\n', ' ')[:55].encode('ascii', 'replace').decode('ascii')
        chunk_id = h['chunk_id'][:34]
        print(f"#{h['vector_rank']:<4} | {h['cosine_score']:>10.4f}   | {h['doc_id']:<24} | {chunk_id:<36} | [{heading}] {preview}...")

def main():
    parser = argparse.ArgumentParser(description="FieldFix - Step 6: Semantic Vector Search")
    parser.add_argument("query", nargs="?", type=str, help="Optional search query string")
    parser.add_argument("--top_k", type=int, default=5, help="Number of nearest chunks to retrieve")
    parser.add_argument("--compare", action="store_true", help="Run head-to-head comparison benchmark against BM25")
    args = parser.parse_args()

    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vector_store.json")
    if not os.path.exists(data_path):
        print(f"[Error] Vector store not found at {data_path}. Please run 'python ingest.py' first.")
        sys.exit(1)

    vector_store = VectorStore().load(data_path)
    embedder = EmbeddingClient()

    # Build BM25 index for comparison
    chunks_for_bm25 = []
    for r in vector_store.records:
        chunks_for_bm25.append({
            "chunk_id": r["chunk_id"],
            "doc_id": r["doc_id"],
            "heading": r["metadata"]["heading"],
            "text": r["content"]
        })
    bm25 = BM25Index(k1=1.5, b=0.75).fit(chunks_for_bm25)

    if args.query and not args.compare:
        run_single_query(args.query, vector_store, embedder, top_k=args.top_k)
    else:
        run_comparison(vector_store, embedder, bm25)

if __name__ == "__main__":
    main()
