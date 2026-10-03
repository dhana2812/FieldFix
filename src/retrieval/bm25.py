import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple

class BM25Index:
    """
    Pure Python implementation of Okapi BM25 ranking algorithm from scratch.
    
    Formula:
    BM25(D, Q) = sum_{q in Q} IDF(q) * [ (f(q, D) * (k1 + 1)) / (f(q, D) + k1 * (1 - b + b * (|D| / avgdl))) ]
    
    where:
    IDF(q) = ln( (N - df(q) + 0.5) / (df(q) + 0.5) + 1 )
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avgdl: float = 0.0
        self.num_docs: int = 0
        
        # Inverted Index: term -> list of (doc_index, term_frequency)
        self.inverted_index: Dict[str, Dict[int, int]] = defaultdict(dict)
        # Document frequencies: term -> count of docs containing term
        self.doc_frequencies: Dict[str, int] = defaultdict(int)
        # Precomputed IDFs
        self.idf: Dict[str, float] = {}

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenizes text into terms while preserving technical identifiers,
        hyphenated codes (e.g. 'dc-150', 'e-217', 'v4.3'), and alphanumeric words.
        """
        # Lowercase and split on punctuation while keeping compound terms
        raw_tokens = re.findall(r'[a-zA-Z0-9]+(?:[-_.][a-zA-Z0-9]+)*', text.lower())
        stopwords = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "is", "are", "was", "were", "it", "this", "that"
        }
        return [t for t in raw_tokens if t not in stopwords]

    def fit(self, chunks: List[Dict[str, Any]]) -> "BM25Index":
        """
        Builds the inverted index and computes IDF values across all chunks.
        """
        self.chunks = chunks
        self.num_docs = len(chunks)
        self.doc_lengths = []
        self.inverted_index = defaultdict(dict)
        self.doc_frequencies = defaultdict(int)
        
        total_length = 0

        for idx, chunk in enumerate(chunks):
            tokens = self.tokenize(chunk["text"])
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_length += doc_len
            
            tf_counts = Counter(tokens)
            for term, count in tf_counts.items():
                self.inverted_index[term][idx] = count
                self.doc_frequencies[term] += 1

        self.avgdl = (total_length / self.num_docs) if self.num_docs > 0 else 0.0

        # Compute Robertson-Spärck Jones IDF with +1 smoothing
        self.idf = {}
        for term, df in self.doc_frequencies.items():
            idf_val = math.log(((self.num_docs - df + 0.5) / (df + 0.5)) + 1.0)
            self.idf[term] = max(0.0, idf_val)

        return self

    def compute_idf(self, term: str) -> float:
        """Returns the precalculated IDF for a term, or calculates for an unseen term."""
        term_clean = term.lower()
        if term_clean in self.idf:
            return self.idf[term_clean]
        df = self.doc_frequencies.get(term_clean, 0)
        return math.log(((self.num_docs - df + 0.5) / (df + 0.5)) + 1.0)

    def score_document(self, query_tokens: List[str], doc_idx: int) -> float:
        """Computes the BM25 score of a single document for the given query tokens."""
        score = 0.0
        doc_len = self.doc_lengths[doc_idx]
        
        # Denominator length normalization factor
        len_norm = self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl)) if self.avgdl > 0 else self.k1

        for term in query_tokens:
            if term not in self.inverted_index or doc_idx not in self.inverted_index[term]:
                continue
            
            tf = self.inverted_index[term][doc_idx]
            idf = self.idf.get(term, 0.0)
            
            # Term frequency saturation component
            tf_component = (tf * (self.k1 + 1.0)) / (tf + len_norm)
            score += idf * tf_component

        return score

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Ranks all chunks by BM25 score against the query and returns top-k.
        """
        query_tokens = self.tokenize(query)
        if not query_tokens or self.num_docs == 0:
            return []

        # Find candidate documents that contain at least one query term
        candidate_doc_indices = set()
        for term in query_tokens:
            if term in self.inverted_index:
                candidate_doc_indices.update(self.inverted_index[term].keys())

        scored_docs: List[Tuple[int, float]] = []
        for doc_idx in candidate_doc_indices:
            score = self.score_document(query_tokens, doc_idx)
            if score > 0:
                scored_docs.append((doc_idx, score))

        # Sort descending by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank, (doc_idx, score) in enumerate(scored_docs[:top_k], 1):
            chunk = self.chunks[doc_idx].copy()
            chunk["bm25_score"] = round(score, 4)
            chunk["bm25_rank"] = rank
            results.append(chunk)

        return results
