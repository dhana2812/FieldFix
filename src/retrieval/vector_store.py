import os
import json
import numpy as np
from typing import List, Dict, Any, Optional

class VectorStore:
    """
    Local Vector Database Collection.
    
    Fields per record:
    - id: Unique record ID
    - chunk_id: Target chunk identifier
    - doc_id: Source document ID
    - corpus_id: SHA-256 fingerprint watermark of the corpus
    - title: Document or section title
    - content: Raw chunk content
    - metadata: Structural metadata (heading, word_count, strategy, timestamp)
    - vector: Dense float embedding vector
    """
    def __init__(self, collection_name: str = "amperia_chunks"):
        self.collection_name = collection_name
        self.records: List[Dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None
        self.corpus_id: Optional[str] = None
        self.version_history: List[Dict[str, Any]] = []

    def _rebuild_vectors(self):
        """Rebuilds L2-normalized numpy vectors from current records."""
        if not self.records:
            self.vectors = None
            return
        vec_list = [r["vector"] for r in self.records]
        self.vectors = np.array(vec_list, dtype=np.float32)
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.vectors = self.vectors / norms

    def upsert_batch(self, records: List[Dict[str, Any]]):
        """Upserts a batch of records, replacing current records."""
        self.records = records
        self._rebuild_vectors()
        if records and "corpus_id" in records[0]:
            self.corpus_id = records[0]["corpus_id"]
            self._update_version_history(self.corpus_id, len(records))

    def append_version(self, new_records: List[Dict[str, Any]], new_corpus_id: str):
        """
        Retains previous versions and appends a new corpus version.
        Points active corpus_id to the new version.
        """
        self.records.extend(new_records)
        self._rebuild_vectors()
        self.corpus_id = new_corpus_id
        self._update_version_history(new_corpus_id, len(new_records))

    def _update_version_history(self, corpus_id: str, count: int):
        existing = next((v for v in self.version_history if v["corpus_id"] == corpus_id), None)
        if existing:
            existing["record_count"] = count
        else:
            import time
            self.version_history.append({
                "corpus_id": corpus_id,
                "record_count": count,
                "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })

    def list_versions(self) -> List[Dict[str, Any]]:
        """Returns metadata for all retained corpus versions."""
        from collections import Counter
        counts = Counter(r.get("corpus_id") for r in self.records)
        versions = []
        for cid, count in counts.items():
            versions.append({
                "corpus_id": cid,
                "record_count": count,
                "is_active": (cid == self.corpus_id)
            })
        return versions

    def rollback_to(self, target_corpus_id: str) -> bool:
        """
        Rolls back the active retrieval pointer to a previously retained corpus version.
        Zero downtime and zero re-embedding required.
        """
        matching = [r for r in self.records if r.get("corpus_id") == target_corpus_id]
        if not matching:
            return False
        self.corpus_id = target_corpus_id
        return True

    def search(self, query_vector: List[float], top_k: int = 5, corpus_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Performs Cosine Similarity search with active corpus_id filtering.
        Defaults to active self.corpus_id when corpus_id is None.
        Formula: sim(q, d) = (q . d) / (||q|| * ||d||)
        """
        if self.vectors is None or len(self.records) == 0:
            return []

        target_corpus_id = corpus_id if corpus_id is not None else self.corpus_id

        # Filter indices by target corpus_id
        valid_indices = []
        for i, rec in enumerate(self.records):
            if target_corpus_id is None or rec.get("corpus_id") == target_corpus_id:
                valid_indices.append(i)

        if not valid_indices:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        sub_vectors = self.vectors[valid_indices]
        scores = np.dot(sub_vectors, q_vec)
        top_sub_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, sub_idx in enumerate(top_sub_indices, 1):
            orig_idx = valid_indices[sub_idx]
            rec = self.records[orig_idx].copy()
            rec_clean = {k: v for k, v in rec.items() if k != "vector"}
            rec_clean["cosine_score"] = round(float(scores[sub_idx]), 4)
            rec_clean["vector_rank"] = rank
            results.append(rec_clean)

        return results

    def save(self, filepath: str):
        """Persists the vector store to disk with version metadata."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        payload = {
            "collection_name": self.collection_name,
            "active_corpus_id": self.corpus_id,
            "corpus_id": self.corpus_id,
            "version_history": self.list_versions(),
            "record_count": len(self.records),
            "dimension": int(self.vectors.shape[1]) if self.vectors is not None else 0,
            "records": self.records
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load(self, filepath: str) -> "VectorStore":
        """Loads a persisted vector store from disk."""
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)
        
        self.collection_name = payload.get("collection_name", "amperia_chunks")
        self.corpus_id = payload.get("active_corpus_id", payload.get("corpus_id"))
        self.records = payload.get("records", [])
        self.version_history = payload.get("version_history", [])
        if self.records:
            self._rebuild_vectors()
        return self
