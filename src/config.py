import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
    
    TOP_K = int(os.getenv("TOP_K", "5"))
    BM25_K1 = float(os.getenv("BM25_K1", "1.5"))
    BM25_B = float(os.getenv("BM25_B", "0.75"))
    RRF_K = int(os.getenv("RRF_K", "60"))
    
    CORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "corpus")
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
