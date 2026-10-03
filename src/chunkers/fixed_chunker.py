from typing import List, Dict, Any

class FixedChunker:
    """
    Fixed-size sliding window chunker.
    Splits text every N words with an overlap of M words.
    """
    def __init__(self, chunk_size: int = 60, overlap: int = 10):
        if overlap >= chunk_size:
            raise ValueError("Overlap must be strictly smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy_name = f"fixed_{chunk_size}_{overlap}"

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        words = doc["text"].split()
        if not words:
            return []

        chunks = []
        step = max(1, self.chunk_size - self.overlap)
        chunk_idx = 0

        for i in range(0, len(words), step):
            chunk_words = words[i : i + self.chunk_size]
            if not chunk_words:
                break
            
            chunk_text = " ".join(chunk_words)
            chunk_id = f"{doc['doc_id']}#fix_{self.chunk_size}w_c{chunk_idx:03d}"
            
            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc["doc_id"],
                "title": doc.get("title", doc["doc_id"]),
                "heading": "General",
                "strategy": f"Fixed (N={self.chunk_size}, M={self.overlap})",
                "word_count": len(chunk_words),
                "text": chunk_text
            })
            chunk_idx += 1
            
            if i + self.chunk_size >= len(words):
                break

        return chunks
