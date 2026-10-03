#!/usr/bin/env python3
"""
FieldFix - Step 5: Corpus Ingestion, Fingerprint Watermarking & Vector Database Upsert
"""
import os
import sys
import json
import hashlib
import time
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.loader import DocumentLoader
from src.chunkers.structure_chunker import StructureChunker
from src.retrieval.embeddings import EmbeddingClient
from src.retrieval.vector_store import VectorStore

def compute_corpus_watermark(documents: List[Dict[str, Any]]) -> str:
    """
    Computes a deterministic SHA-256 fingerprint of the entire corpus content.
    Used as an immutable watermark on all ingested chunk records.
    """
    hasher = hashlib.sha256()
    # Sort by doc_id to ensure deterministic hash regardless of directory ordering
    sorted_docs = sorted(documents, key=lambda x: x["doc_id"])
    for doc in sorted_docs:
        hasher.update(doc["doc_id"].encode("utf-8"))
        hasher.update(doc["text"].encode("utf-8"))
    return hasher.hexdigest()

def ingest_corpus():
    print("=" * 80)
    print("[*] FieldFix - Step 5: Corpus Ingestion & Vector Indexing")
    print("=" * 80)
    
    # 1. Load Raw Documents
    loader = DocumentLoader()
    documents = loader.load_all_documents()
    print(f"Loaded {len(documents)} raw documents from corpus.")
    
    # 2. Compute SHA-256 Watermark
    corpus_id = compute_corpus_watermark(documents)
    print(f"\n[Watermark] Corpus SHA-256 Fingerprint: {corpus_id}")
    
    # 3. Apply Production Chunking Strategy (Structure-Aware Max 200w)
    chunker = StructureChunker(max_words=200, min_words=25)
    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)
        
    print(f"[Chunking] Generated {len(all_chunks)} structure-aware chunks.")
    
    # 4. Generate Embeddings in Single Batch
    embedder = EmbeddingClient()
    print(f"[Embedding] Embedding model: '{embedder.model_name}' (Target Dimension: {embedder.dimension})")
    
    chunk_texts = [c["text"] for c in all_chunks]
    start_embed_time = time.time()
    vectors = embedder.embed_texts(chunk_texts)
    embed_duration = time.time() - start_embed_time
    
    actual_dim = len(vectors[0]) if vectors else 0
    print(f"[Embedding] Successfully generated {len(vectors)} vectors in {embed_duration:.2f}s. (Dim: {actual_dim})")
    
    # 5. Build Records for Vector Store
    records = []
    for i, (chunk, vec) in enumerate(zip(all_chunks, vectors)):
        rec_id = f"rec_{i+1:03d}_{chunk['doc_id']}"
        record = {
            "id": rec_id,
            "chunk_id": chunk["chunk_id"],
            "doc_id": chunk["doc_id"],
            "corpus_id": corpus_id,
            "title": chunk.get("title", chunk["doc_id"]),
            "content": chunk["text"],
            "metadata": {
                "heading": chunk.get("heading", "General"),
                "strategy": chunk.get("strategy", "Recursive Structure"),
                "word_count": chunk.get("word_count", len(chunk["text"].split())),
                "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            "vector": vec
        }
        records.append(record)
        
    # 6. Upsert Batch into Vector Database & Persist
    vector_store = VectorStore(collection_name="amperia_chunks_v1")
    vector_store.upsert_batch(records)
    
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vector_store.json")
    vector_store.save(data_path)
    print(f"[VectorStore] Upserted {len(records)} records. Persisted to: {data_path}")
    
    # 7. Display Stored Record Sample Printouts
    print("\n" + "=" * 80)
    print("[*] SAMPLE STORED VECTOR DATABASE RECORDS (Record Printout)")
    print("=" * 80)
    
    samples_to_show = [0, 8, 20] if len(records) > 20 else [0, 1]
    for idx in samples_to_show:
        r = records[idx]
        vec_preview = [round(x, 4) for x in r["vector"][:5]] + ["..."]
        print(f"\n--- [Record #{idx+1}: {r['id']}] ---")
        print(f"  - chunk_id   : {r['chunk_id']}")
        print(f"  - doc_id     : {r['doc_id']}")
        print(f"  - corpus_id  : {r['corpus_id']}")
        print(f"  - heading    : {r['metadata']['heading']}")
        print(f"  - word_count : {r['metadata']['word_count']} words")
        print(f"  - vector[{len(r['vector'])}d]: {vec_preview}")
        snippet = r['content'].replace('\n', ' ')[:120]
        print(f"  - content    : \"{snippet}...\"")
        
    print("\n" + "=" * 80)
    print(f"[Done] Ingestion Complete! Vector DB ready with {len(records)} records.")
    print("=" * 80)

if __name__ == "__main__":
    ingest_corpus()
