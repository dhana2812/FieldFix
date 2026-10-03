#!/usr/bin/env python3
"""
FieldFix - Step 4: Custom BM25 Implementation & Toy Mathematical Proof
"""
import os
import sys
import math
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.retrieval.bm25 import BM25Index
from src.loader import DocumentLoader
from src.chunkers.structure_chunker import StructureChunker

def run_toy_example_proof():
    print("=" * 80)
    print("[*] BM25 STEP-BY-STEP MATHEMATICAL HAND-CHECK ON TOY CORPUS")
    print("=" * 80)
    
    toy_chunks = [
        {"chunk_id": "toy_doc_1", "text": "DC-150 warranty warranty"},
        {"chunk_id": "toy_doc_2", "text": "standard warranty policy"}
    ]
    
    print("\n1. Toy Documents:")
    print("   Chunk 1 (D1): 'DC-150 warranty warranty'  (Length |D1| = 3 words)")
    print("   Chunk 2 (D2): 'standard warranty policy'   (Length |D2| = 3 words)")
    print(f"   Total Documents (N) = 2, Average Document Length (avgdl) = (3 + 3)/2 = 3.0")
    print(f"   Parameters: k1 = 1.5, b = 0.75\n")
    
    bm25 = BM25Index(k1=1.5, b=0.75)
    bm25.fit(toy_chunks)
    
    print("2. Document Frequencies (df) and Inverted Index:")
    for term, docs in sorted(bm25.inverted_index.items()):
        df = bm25.doc_frequencies[term]
        print(f"   - Term '{term:<10}': df = {df}, occurrences in docs = {dict(docs)}")
        
    print("\n3. Robertson-Sparck Jones IDF Calculation:")
    print("   Formula: IDF(q) = ln( ((N - df + 0.5) / (df + 0.5)) + 1 )")
    
    # Rare term: dc-150
    df_rare = 1
    idf_rare_calc = math.log(((2 - 1 + 0.5) / (1 + 0.5)) + 1.0)
    print(f"\n   - Rare Term 'dc-150' (df = 1):")
    print(f"     IDF('dc-150') = ln( ((2 - 1 + 0.5)/(1 + 0.5)) + 1 ) = ln( (1.5 / 1.5) + 1 ) = ln(1.0 + 1) = ln(2.0) approx {idf_rare_calc:.6f}")
    
    # Common term: warranty
    df_common = 2
    idf_common_calc = math.log(((2 - 2 + 0.5) / (2 + 0.5)) + 1.0)
    print(f"\n   - Common Term 'warranty' (df = 2):")
    print(f"     IDF('warranty') = ln( ((2 - 2 + 0.5)/(2 + 0.5)) + 1 ) = ln( (0.5 / 2.5) + 1 ) = ln(0.2 + 1) = ln(1.2) approx {idf_common_calc:.6f}")
    
    ratio = idf_rare_calc / idf_common_calc
    print(f"\n   => MATHEMATICAL PROOF: IDF('dc-150') [{idf_rare_calc:.4f}] is {ratio:.2f}x HIGHER than IDF('warranty') [{idf_common_calc:.4f}].")
    print("      The rarer term receives much higher discriminatory weight.")
    
    print("\n4. BM25 Query Scoring Verification:")
    query = "DC-150 warranty"
    print(f"   Query: '{query}'")
    
    results = bm25.search(query, top_k=2)
    print("\n   [BM25 Ranking Results]:")
    for r in results:
        print(f"   - Rank {r['bm25_rank']}: [{r['chunk_id']}] Score = {r['bm25_score']} | Content: \"{r['text']}\"")
        
    print("=" * 80)

def run_corpus_bm25_search():
    print("\n" + "=" * 80)
    print("[*] STEP 4: BM25 SEARCH ON PRODUCTION AMPERIA CORPUS")
    print("=" * 80)
    
    loader = DocumentLoader()
    docs = loader.load_all_documents()
    
    chunker = StructureChunker(max_words=200, min_words=25)
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunker.chunk_document(doc))
        
    print(f"Indexed {len(all_chunks)} structure-aware chunks into Custom BM25 Inverted Index.\n")
    
    bm25 = BM25Index(k1=1.5, b=0.75)
    bm25.fit(all_chunks)
    
    test_queries = [
        "DC-150 throwing E-217 error at Pune Expressway",
        "power module warranty coverage duration",
        "measured insulation resistance reading DC150-03 inspection"
    ]
    
    for q in test_queries:
        print(f"\n[Search] Query: \"{q}\"")
        hits = bm25.search(q, top_k=3)
        for h in hits:
            print(f"   [Rank {h['bm25_rank']} | Score: {h['bm25_score']:>7.4f}] ({h['doc_id']}) {h['heading']}")
            snippet = h['text'].replace('\n', ' ')[:110]
            print(f"     \"{snippet}...\"")
            
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_toy_example_proof()
    run_corpus_bm25_search()
