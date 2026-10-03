import os
import time
import hashlib
import numpy as np
from typing import List, Dict, Any, Union
from src.config import Config

class EmbeddingClient:
    """
    Unified Embedding Client supporting:
    1. OpenAI / OpenRouter 'text-embedding-3-small' (1536 dimensions)
    2. Deterministic Local Semantic Dense Embeddings (384 dimensions) as resilient offline fallback.
    """
    def __init__(self, model_name: str = None, dimension: int = None):
        self.model_name = model_name or Config.EMBEDDING_MODEL
        self.dimension = dimension or Config.EMBEDDING_DIM
        self.provider = Config.LLM_PROVIDER
        self.api_key = Config.OPENROUTER_API_KEY if self.provider == "openrouter" else Config.OPENAI_API_KEY

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of strings."""
        if not texts:
            return []

        # 1. Try OpenAI / OpenRouter API if key is present
        if self.api_key and self.provider in ["openai", "openrouter"]:
            try:
                from openai import OpenAI
                base_url = "https://openrouter.ai/api/v1" if self.provider == "openrouter" else None
                client = OpenAI(api_key=self.api_key, base_url=base_url)
                
                # Batch request
                response = client.embeddings.create(
                    model=self.model_name,
                    input=texts
                )
                embeddings = [item.embedding for item in response.data]
                self.dimension = len(embeddings[0])
                return embeddings
            except Exception as e:
                print(f"[Warning] Remote embedding API error ({str(e)}). Using local semantic dense fallback.")

        # 2. Local Deterministic Semantic Dense Embeddings (Consistent between chunks and queries)
        return self._local_dense_embeddings(texts)

    def embed_query(self, query: str) -> List[float]:
        """Embeds a single query string using the exact same model."""
        return self.embed_texts([query])[0]

    def _local_dense_embeddings(self, texts: List[str], dim: int = 384) -> List[List[float]]:
        """
        Deterministic, L2-normalized dense feature hashing embedding for offline/local use.
        Ensures consistent high-dimensional geometry and cosine distance properties.
        """
        self.dimension = dim
        self.model_name = f"local-dense-hash-{dim}d"
        embeddings = []

        for text in texts:
            tokens = text.lower().split()
            vec = np.zeros(dim, dtype=np.float32)
            
            for i, token in enumerate(tokens):
                # Hash token to multiple dimensions for distributed representation
                h1 = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
                h2 = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
                
                idx1 = h1 % dim
                idx2 = h2 % dim
                sign1 = 1.0 if ((h1 >> 8) & 1) else -1.0
                sign2 = 1.0 if ((h2 >> 8) & 1) else -1.0
                
                weight = 1.0 / (1.0 + 0.05 * i)  # Position discounting
                vec[idx1] += sign1 * weight
                vec[idx2] += sign2 * weight

            # L2 Normalization
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            else:
                vec[0] = 1.0
                
            embeddings.append(vec.tolist())

        return embeddings
