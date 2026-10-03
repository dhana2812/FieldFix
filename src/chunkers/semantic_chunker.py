import re
import math
from collections import Counter
from typing import List, Dict, Any

class SemanticChunker:
    """
    Semantic chunker based on sentence-level lexical/term similarity.
    Calculates cosine similarity between adjacent sentences and creates boundaries
    when topic similarity drops below threshold, with min/max word constraints.
    Flushes leftover bucket at document completion.
    """
    def __init__(self, similarity_threshold: float = 0.20, max_words: int = 180, min_words: int = 35):
        self.similarity_threshold = similarity_threshold
        self.max_words = max_words
        self.min_words = min_words
        self.strategy_name = f"semantic_thresh{similarity_threshold}_max{max_words}"

    def _sentence_vector(self, sentence: str) -> Counter:
        words = re.findall(r'\b[a-zA-Z0-9_\-]+\b', sentence.lower())
        # Filter common ultra-low information words
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were"}
        filtered = [w for w in words if w not in stopwords]
        return Counter(filtered or words)

    def _cosine_similarity(self, vec1: Counter, vec2: Counter) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum(vec1[x] * vec2[x] for x in intersection)
        sum1 = sum(val**2 for val in vec1.values())
        sum2 = sum(val**2 for val in vec2.values())
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = doc["text"]
        doc_id = doc["doc_id"]
        doc_title = doc.get("title", doc_id)

        # Split into sentences
        raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?\n])\s+', text) if s.strip()]
        if not raw_sentences:
            return []

        chunks = []
        chunk_idx = 0

        current_sentences = [raw_sentences[0]]
        current_words = len(raw_sentences[0].split())
        current_vector = self._sentence_vector(raw_sentences[0])

        for i in range(1, len(raw_sentences)):
            sent = raw_sentences[i]
            sent_words = len(sent.split())
            sent_vec = self._sentence_vector(sent)

            sim = self._cosine_similarity(current_vector, sent_vec)

            # Check boundary conditions
            is_max_exceeded = (current_words + sent_words) > self.max_words
            is_topic_shift = (sim < self.similarity_threshold) and (current_words >= self.min_words)

            if is_max_exceeded or is_topic_shift:
                # Emit current bucket
                chunk_text = " ".join(current_sentences)
                chunk_id = f"{doc_id}#sem_{self.max_words}w_c{chunk_idx:03d}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "title": doc_title,
                    "heading": "Semantic Unit",
                    "strategy": f"Semantic (Thresh={self.similarity_threshold}, Max={self.max_words}w)",
                    "word_count": len(chunk_text.split()),
                    "text": chunk_text
                })
                chunk_idx += 1
                
                # Start new bucket
                current_sentences = [sent]
                current_words = sent_words
                current_vector = sent_vec
            else:
                current_sentences.append(sent)
                current_words += sent_words
                # Update rolling vector
                for k, v in sent_vec.items():
                    current_vector[k] += v

        # CRITICAL: Always flush the trailing leftover bucket!
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunk_id = f"{doc_id}#sem_{self.max_words}w_c{chunk_idx:03d}"
            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "title": doc_title,
                "heading": "Semantic Unit",
                "strategy": f"Semantic (Thresh={self.similarity_threshold}, Max={self.max_words}w)",
                "word_count": len(chunk_text.split()),
                "text": chunk_text
            })
            chunk_idx += 1

        return chunks
