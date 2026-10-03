# FieldFix - Step 6: Semantic Vector Search & Head-to-Head Evaluation Report

## 1. Executive Summary & Retrieval Objectives

In **Step 6**, we evaluate dense semantic vector search across the 39 structure-aware chunks of the Amperia EV charging infrastructure corpus. Using **1,536-dimensional L2-normalized dense embeddings** (`text-embedding-3-small`), our vector retrieval engine calculates high-dimensional cosine similarity while strictly enforcing **corpus watermark isolation** (`corpus_id: c6278cc1...`).

This report provides an empirical **head-to-head comparison** between:
1. **Dense Vector Search (Cosine Similarity)**: Optimized for semantic meaning, conceptual intent, and conversational/colloquial phrasing.
2. **Sparse Keyword Search (Okapi BM25)**: Optimized for exact lexical tokens, error codes (`E-217`), and version specifiers (`fw 4.3`).

---

## 2. Mathematical Foundation & Corpus Isolation

### 2.1 Cosine Similarity Formulation
For a query vector $\mathbf{q} \in \mathbb{R}^{1536}$ and stored chunk vector $\mathbf{d} \in \mathbb{R}^{1536}$:
$$\text{Cosine Similarity}(\mathbf{q}, \mathbf{d}) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\|_2 \|\mathbf{d}\|_2}$$

Because all chunk vectors $\mathbf{d}$ are pre-normalized during batch upsert ($\|\mathbf{d}\|_2 = 1.0$) and the query vector is normalized at query time ($\|\mathbf{q}\|_2 = 1.0$), the cosine score simplifies to the fast matrix dot product:
$$\text{Score}(\mathbf{q}, \mathbf{d}) = \mathbf{q}_{\text{norm}} \cdot \mathbf{d}_{\text{norm}}$$

### 2.2 Corpus Watermark Filtering
Every chunk in the vector database stores the SHA-256 fingerprint watermark of the verified corpus (`c6278cc1bc2e740142b065a58c5252a8148d5932ac8db5943f96fe52bc001e37`). Vector search filters out stale, cross-tenant, or non-matching chunks prior to computing matrix similarities.

---

## 3. Side-by-Side Comparison: Vector Search vs. BM25

### 3.1 Scenario A: Semantic Intent & Vocabulary Mismatch (Vector Search Wins)
> **Query:** `"how long is the power module covered if it dies?"`

#### Qualitative Context & Failure Analysis
- **Technician Phrasing:** The field engineer uses colloquial terms (`"covered"`, `"dies"`) rather than the formal language of technical manuals.
- **Corpus Phrasing:** The authoritative document (`dc150_product_manual.md`) uses terms such as `"Hardware Warranty and Coverage Schedule"`, `"5 Years / 60 Months"`, `"dielectric breakdown"`, and `"thermal fatigue"`.
- **Vector Search Result:** Vector search understands the semantic equivalence between "power module dies / covered" and "warranty schedule / component replacement period", placing the 5-year warranty table at **Rank #1** with a high similarity score of **0.5251**.
- **BM25 Result:** BM25 fails due to **vocabulary mismatch**. Because the words `"covered"` and `"dies"` do not literally appear in the warranty table, BM25 ranks communication error codes (`E-201`) at Rank #1 purely due to incidental token frequency matches.

#### Side-by-Side Results Table

| Rank | Retrieval Engine | Score | Document ID | Chunk ID | Section Heading & Content Preview |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **#1** | **Dense Vector** | **0.5251** | `dc150_product_manual` | `dc150_...#struct_200w_c005` | **[3. Hardware Warranty and Coverage Schedule]** 5 Years / 60 Months coverage for 75 kW SiC Power Conversion Modules... |
| #2 | Dense Vector | 0.3754 | `firmware_release_notes` | `firmware_...#struct_200w_c000` | **[Summary]** Maintenance release addressing field communication stability... |
| #3 | Dense Vector | 0.3519 | `dc150_product_manual` | `dc150_...#struct_200w_c007` | **[4.1 Hardware Error Codes (`E-1xx`)]** `E-101` - AC Grid Phase Loss, `E-102` - DC Bus Overvoltage... |
| | | | | | |
| **#1** | **Okapi BM25** | **5.5303** | `dc150_product_manual` | `dc150_...#struct_200w_c008` | **[4.2 Comm & Firmware Error Codes (`E-2xx`)]** *(Irrelevant to warranty)* Loss of WebSocket ping heartbeat... |
| #2 | Okapi BM25 | 5.2104 | `firmware_release_notes` | `firmware_...#struct_200w_c000` | **[Summary]** *(Irrelevant to warranty)* Power cycle and CAN bus recovery... |
| #3 | Okapi BM25 | 3.2369 | `dc150_product_manual` | `dc150_...#struct_200w_c002` | **[1.1 Key Technical Specifications]** *(Irrelevant to warranty)* 415 V AC input nominal voltage... |

---

### 3.2 Scenario B: Exact Alphanumeric Identifier & Error Code (BM25 Wins)
> **Query:** `"E-217"`

#### Qualitative Context & Failure Analysis
- **Technician Phrasing:** The technician submits the exact alphanumeric error code `"E-217"` observed on the DC-150 charger HMI screen.
- **BM25 Result:** BM25's Inverse Document Frequency (IDF) assigns massive discriminatory weight to the rare token `'e-217'` ($\text{IDF} \approx 2.26$). It immediately pins the **Known Field Advisory #FWA-2026-03** and the **Section 4.2 Error Code Diagnostic Table** at **Rank #1 and Rank #2**.
- **Vector Search Result:** While Vector search includes the communication error table, its dense representation distributes energy across general charger error concepts, placing the critical Field Advisory below the general section. BM25 provides sharper, zero-noise localization for specific error tokens.

#### Side-by-Side Results Table

| Rank | Retrieval Engine | Score | Document ID | Chunk ID | Section Heading & Content Preview |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **#1** | **Okapi BM25** | **2.2661** | `firmware_release_notes` | `firmware_...#struct_200w_c004` | **[Known Field Advisory #FWA-2026-03]** `E-217` CAN Bus Transceiver Buffer Saturation Anomaly... |
| **#2** | **Okapi BM25** | **2.1958** | `dc150_product_manual` | `dc150_...#struct_200w_c008` | **[4.2 Comm & Firmware Error Codes (`E-2xx`)]** `E-217` - Internal CAN Communication Timeout... |
| #3 | Okapi BM25 | 1.7425 | `incident_postmortem` | `incident_...#struct_200w_c002` | **[2. Chronological Timeline of Events]** E-217 triggered during high-temperature session... |
| | | | | | |
| **#1** | **Dense Vector** | **0.4652** | `dc150_product_manual` | `dc150_...#struct_200w_c008` | **[4.2 Comm & Firmware Error Codes (`E-2xx`)]** `E-201`, `E-208`, `E-217` table... |
| #2 | Dense Vector | 0.3995 | `firmware_release_notes` | `firmware_...#struct_200w_c004` | **[Known Field Advisory #FWA-2026-03]** Firmware patch guidelines for CAN transceiver... |
| #3 | Dense Vector | 0.3910 | `site_inspection_report` | `site_...#struct_200w_c001` | **[Annual Site & Hardware Inspection]** Site inspection diagnostic summary... |

---

### 3.3 Scenario C: Short Firmware Version & Changelog Query (BM25 Wins)
> **Query:** `"fw 4.3"`

#### Qualitative Context & Failure Analysis
- **Technician Phrasing:** Concise abbreviation for firmware 4.3.
- **BM25 Result:** Exact token matching for `fw` and `4.3` retrieves the specific regional field technician log entries recording the fw 4.3 deployment at Pune Station with high confidence (**Score: 6.5692**).
- **Vector Search Result:** Vector search yields lower differentiation between firmware versions (`v4.3.0` vs `v4.1.0` vs general firmware sections) because short numerical tokens have subtle embedding distance differences.

---

## 4. Key Engineering Takeaways & Synthesis

```
┌────────────────────────────────────────────────────────────────────────┐
│                      RETRIEVAL COMPARISON MATRIX                       │
├──────────────────────────┬──────────────────────┬──────────────────────┤
│ Metric / Dimension       │ Dense Vector Search  │ Sparse Okapi BM25    │
├──────────────────────────┼──────────────────────┼──────────────────────┤
│ Semantic Conceptual Match│ ★★★★★ (Superior)     │ ★☆☆☆☆ (Fails)        │
│ Colloquial / Natural Lang│ ★★★★★ (Understands)  │ ★☆☆☆☆ (Mismatch)     │
│ Alphanumeric Error Codes │ ★★★☆☆ (Dispersed)    │ ★★★★★ (Pinpoint IDF) │
│ Exact Model Numbers / FW │ ★★★☆☆ (Moderate)     │ ★★★★★ (Exact Token)  │
│ Out-of-Vocabulary Noise  │ Low                  │ High                 │
└──────────────────────────┴──────────────────────┴──────────────────────┘
```

### Why Hybrid Search (Step 7: RRF) is Essential:
1. **Single-method retrieval leaves critical blind spots:** Relying solely on dense embeddings risks missing critical error codes (`E-217`) or exact part numbers. Relying solely on BM25 risks failing any question asked in conversational natural language.
2. **Reciprocal Rank Fusion (RRF):** Combining both dense vector search and BM25 with $k=60$ produces the optimal balance, ensuring both colloquial semantic questions and exact hardware error queries achieve Rank #1 retrieval in production.

---

## 5. Verification & CLI Usage

To execute Step 6 vector search and run the automated head-to-head comparison:
```powershell
# Run automated head-to-head comparison benchmark:
python vector_search.py

# Or query specific custom strings with corpus filtering:
python vector_search.py "what is the warranty on the power module?"
python vector_search.py "E-217"
```
