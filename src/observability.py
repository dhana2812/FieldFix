import os
import sys
import json
import time
import uuid
from typing import Dict, Any, Optional

class TelemetryLogger:
    """
    Production Observability & Cost Tracking Logger for FieldFix RAG.
    Tracks Correlation IDs, per-stage latencies, token consumption, and cost estimates.
    """
    # Standard enterprise pricing per 1M tokens (USD)
    PRICING = {
        "embedding": 0.02,        # text-embedding-3-small: $0.02 / 1M tokens
        "llm_prompt": 0.15,       # gpt-4o-mini / gemini-1.5-flash: $0.15 / 1M tokens
        "llm_completion": 0.60,   # gpt-4o-mini / gemini-1.5-flash: $0.60 / 1M tokens
        "rerank": 0.15            # cross-encoder / LLM rerank input: $0.15 / 1M tokens
    }

    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "telemetry.jsonl")

    @staticmethod
    def generate_correlation_id() -> str:
        """Generates a unique request correlation ID."""
        date_str = time.strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:8]
        return f"req_{date_str}_{unique_suffix}"

    @classmethod
    def estimate_cost(
        cls,
        prompt_tokens: int,
        completion_tokens: int,
        embedding_tokens: int = 0,
        rerank_tokens: int = 0
    ) -> float:
        """Computes estimated request cost in USD."""
        cost_embed = (embedding_tokens * cls.PRICING["embedding"]) / 1_000_000.0
        cost_prompt = (prompt_tokens * cls.PRICING["llm_prompt"]) / 1_000_000.0
        cost_comp = (completion_tokens * cls.PRICING["llm_completion"]) / 1_000_000.0
        cost_rerank = (rerank_tokens * cls.PRICING["rerank"]) / 1_000_000.0
        return round(cost_embed + cost_prompt + cost_comp + cost_rerank, 6)

    def log_request(self, payload: Dict[str, Any]):
        """Persists structured telemetry log to JSONL."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            print(f"[Warning] Failed to write telemetry log: {e}", file=sys.stderr)

    @classmethod
    def format_one_line_summary(cls, payload: Dict[str, Any]) -> str:
        """
        Formats a clean, one-line production summary printed at the end of each answer.
        Format: [REQ <id>] | Latency: <total>ms (<stages>) | Tokens: <in> in / <out> out | Cost: $<cost> | Corpus: <hash>
        """
        cid = payload.get("correlation_id", "req_unknown")
        stages = payload.get("stages", {})
        tokens = payload.get("tokens", {})
        cost = payload.get("cost_usd", 0.0)
        corpus = payload.get("corpus_id", "unknown")[:10]

        total_ms = stages.get("total_ms", 0)
        embed_ms = stages.get("embed_ms", 0)
        ret_ms = stages.get("retrieve_ms", 0)
        rerank_ms = stages.get("rerank_ms", 0)
        gen_ms = stages.get("generate_ms", 0)

        prompt_tok = tokens.get("prompt", 0)
        comp_tok = tokens.get("completion", 0)

        return (
            f"[REQ {cid}] | "
            f"Latency: {total_ms:.1f}ms (embed: {embed_ms:.1f}ms, retrieve: {ret_ms:.1f}ms, rerank: {rerank_ms:.1f}ms, gen: {gen_ms:.1f}ms) | "
            f"Tokens: {prompt_tok:,} in / {comp_tok:,} out | "
            f"Cost: ${cost:.6f} | "
            f"Corpus: {corpus}..."
        )

    @classmethod
    def format_detailed_log(cls, payload: Dict[str, Any]) -> str:
        """Formats a human-readable multi-line audit log for observability inspection."""
        stages = payload.get("stages", {})
        tokens = payload.get("tokens", {})
        lines = [
            f"================== TELEMETRY AUDIT RECORD ==================",
            f"Correlation ID:   {payload.get('correlation_id')}",
            f"Timestamp:        {payload.get('timestamp')}",
            f"Active Corpus ID: {payload.get('corpus_id')}",
            f"Model / Provider: {payload.get('model')} ({payload.get('provider')})",
            f"------------------------------------------------------------",
            f"Stage Latencies:",
            f" • Embed Query:   {stages.get('embed_ms', 0):>8.2f} ms",
            f" • Hybrid Ret:    {stages.get('retrieve_ms', 0):>8.2f} ms",
            f" • Re-Ranking:    {stages.get('rerank_ms', 0):>8.2f} ms",
            f" • Generation:    {stages.get('generate_ms', 0):>8.2f} ms",
            f" • Total Latency: {stages.get('total_ms', 0):>8.2f} ms",
            f"------------------------------------------------------------",
            f"Token Consumption & Cost:",
            f" • Prompt Tokens:     {tokens.get('prompt', 0):>6,}",
            f" • Completion Tokens: {tokens.get('completion', 0):>6,}",
            f" • Total Tokens:      {tokens.get('total', 0):>6,}",
            f" • Estimated Cost:    ${payload.get('cost_usd', 0.0):.6f} USD",
            f"============================================================"
        ]
        return "\n".join(lines)
