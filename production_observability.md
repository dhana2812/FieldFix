# FieldFix — Step 12: Production Observability, Cost & Re-Ingestion

## 1. Overview & Architectural Goals
In an enterprise-grade field engineering copilot, changes to the knowledge corpus must be **auditable, non-destructive, and immediately reversible**, and every user request must be traced across its lifecycle with **precise latency, token consumption, and cost attribution**.

---

## 2. Immutable Corpus Versioning & Zero-Downtime Rollback

### 2.1 Dual-Version Retention Mechanism
FieldFix utilizes a **Blue-Green / Immutable Versioning Architecture** in `data/vector_store.json`:
- **Corpus Fingerprinting:** Ingestion computes an immutable SHA-256 fingerprint watermark over all corpus documents.
  - Previous Version: `c6278cc1bc2e740142b065a58c5252a8148d5932ac8db5943f96fe52bc001e37` (Firmware v4.3 baseline)
  - Updated Version:  `b586b73ea30754ebb0e633ba10dd0178b0539cf9fcd57e62abc1973619732152` (Firmware v4.4.0 adaptive pre-charge hotfix)
- **Non-Destructive Ingestion:** When new documents are ingested via `vector_store.append_version()`, previous records are **retained** in the database rather than purged.
- **Active Version Filtering:** Queries automatically filter vectors where `rec.corpus_id == active_corpus_id`.

### 2.2 Operational Rollback Runbook
If a newly published firmware note contains an operational defect or incorrect specification, operators can execute an instant rollback:
```python
vector_store = VectorStore().load("data/vector_store.json")
vector_store.rollback_to("c6278cc1bc2e740142b065a58c5252a8148d5932ac8db5943f96fe52bc001e37")
vector_store.save("data/vector_store.json")
```
- **Zero Re-Embedding:** All prior embedding vectors and metadata remain in memory/disk; no external API calls required.
- **Switch Latency:** `< 1 millisecond` pointer update.
- **Verification:** As demonstrated in the test execution, querying the rolled-back corpus for v4.4.0 causes the model to strictly state *"I don't have enough information"*, proving isolation.

---

## 3. Request Observability & Telemetry

### 3.1 End-to-End Request Tracing with Correlation IDs
Every request entering `FieldFixRAG.answer()` is assigned a unique `correlation_id` (e.g. `req_20261003_5d1c9907`) and logged to `logs/telemetry.jsonl`.

### 3.2 Granular Stage Latency Tracking
The pipeline measures wall-clock execution time for every discrete sub-system:
- **`embed`**: Time to generate dense 1,536d query embedding vector.
- **`retrieve`**: Time to execute sparse Okapi BM25 and dense cosine vector search, fused via Reciprocal Rank Fusion ($k=60$).
- **`rerank`**: Time for Cross-Encoder re-ranking to prioritize actionable root causes.
- **`generate`**: Time for LLM grounded answer generation with citation enforcement.

### 3.3 Token Accounting & Cost Estimation
FieldFix tracks token consumption across prompt and completion phases, computing cost using standard enterprise pricing:
- **Embedding:** $0.02 per 1,000,000 tokens
- **LLM Input:** $0.15 per 1,000,000 tokens
- **LLM Output:** $0.60 per 1,000,000 tokens

---

## 4. Sample Telemetry Audit Record

### 4.1 Production One-Line Summary (Printed at End of Answer)
```text
[REQ req_20261003_5d1c9907] | Latency: 27665.9ms (embed: 645.4ms, retrieve: 43.8ms, rerank: 15243.8ms, gen: 11732.8ms) | Tokens: 1,206 in / 1,442 out | Cost: $0.001222 | Corpus: b586b73ea3...
```

### 4.2 Structured JSON Telemetry Log (`logs/telemetry.jsonl`)
```json
{
  "timestamp": "2026-10-03T05:22:38Z",
  "correlation_id": "req_20261003_5d1c9907",
  "corpus_id": "b586b73ea30754ebb0e633ba10dd0178b0539cf9fcd57e62abc1973619732152",
  "query": "What is the maximum pre-charge evaluation window allowed in firmware v4.4.0 to resolve the E-217 error on long cables?",
  "stages": {
    "embed_ms": 645.42,
    "retrieve_ms": 43.79,
    "rerank_ms": 15243.84,
    "generate_ms": 11732.83,
    "total_ms": 27665.88
  },
  "tokens": {
    "prompt": 1206,
    "completion": 1442,
    "total": 2648
  },
  "cost_usd": 0.001222,
  "model": "openai/gpt-5-mini",
  "provider": "openrouter",
  "status": "SUCCESS"
}
```

### 4.3 Stage Latency & Token Breakdown Table

| Stage / Metric | Value | Description |
| :--- | :---: | :--- |
| **Correlation ID** | `req_20261003_5d1c9907` | Globally unique trace identifier |
| **Active Corpus Version** | `b586b73ea30754eb...` | Deterministic SHA-256 corpus watermark |
| **Query Embedding Latency** | `645.42 ms` | Vector embedding generation |
| **Hybrid Retrieval Latency** | `43.79 ms` | Okapi BM25 + Cosine Vector + RRF ($k=60$) |
| **Re-Ranking Latency** | `15243.84 ms` | Cross-encoder contextual scoring |
| **Grounded Generation Latency** | `11732.83 ms` | Strict citation synthesis |
| **Total Request Latency** | `27665.88 ms` | Complete end-to-end user wait time |
| **Prompt (Input) Tokens** | `1,206` tokens | Context chunks + system prompt |
| **Completion (Output) Tokens** | `1,442` tokens | Synthesized answer + citations |
| **Total Token Volume** | `2,648` tokens | Full API token exchange |
| **Estimated Request Cost** | `$0.001222 USD` | Billed cost for request |
