# FieldFix — Step 11: PDF Ingestion & OCR Grounded Q&A Transcript

## 1. Overview & Parsing Architecture

Real-world enterprise field engineering repositories contain unstructured PDF reports, scanned audit sheets, and multi-column tabular data.
Step 11 converts `site_inspection_report.pdf` into structured Markdown via Document Intelligence / OCR layout parsing, chunks it with the recursive `StructureChunker`, and proves end-to-end grounded generation on **questions whose answers exist ONLY in the PDF**.

### Parsing Comparison: Raw Text Dump vs. Document Intelligence Markdown

| Feature | Raw PDF Text Extraction (`pypdf`) | Document Intelligence / OCR Parsing ([pdf_ingest.py](file:///c:/Users/dhana/FieldFix/pdf_ingest.py)) |
| :--- | :--- | :--- |
| **Table Layout** | ❌ Multi-column tables flattened into single vertical lines. Headers and row cells decoupled. |  Clean GitHub-Flavored Markdown tables with explicit column headers and cell alignment. |
| **Section Hierarchy** | ❌ Section titles treated as plain body text; lost heading hierarchy. |  Preserves `## 1. Environmental`, `## 2. High-Voltage Insulation`, `## 3. Cable Physical Wear`. |
| **Metadata Key-Values** | ❌ Arbitrary text flow without structural context. |  Organized into structured key-value summary blocks. |
| **Chunking Alignment** | ❌ Chunks break mid-sentence or mid-table row. |  `StructureChunker` segments along semantic section boundaries, preserving table integrity. |

---

## 2. End-to-End Q&A Transcript: PDF-Exclusive Questions

### Question 1: Environmental & Earthing Measurements (PDF-Only)

**Query:** `"What were the exact ambient temperature, three-phase AC line voltage, and earthing pit loop impedance recorded during the Pune Expressway annual site inspection?"`

**Why PDF-Only:** *Recorded solely by field inspector Vikram Shinde on the physical test sheet; not present in firmware notes or product manuals.*

**Model / Provider:** `openai/gpt-5-mini` (`openrouter`) | **Latency:** `27365.68 ms` | **Tokens:** `2394`

**Grounded Response:**
Summary — recorded measurements (Pune Expressway annual inspection)
- Field Ambient Temperature: 38.5 °C measured at 14:00 hours under direct sun exposure [site_inspection_report#struct_200w_c001].
- Three‑phase AC line voltage: 418.2 V AC RMS (line‑to‑line); measured phase imbalance 1.2% [site_inspection_report#struct_200w_c001].
- Earthing pit loop impedance: 2.14 Ω (3‑point fall‑of‑potential test) — recorded as fully compliant with the < 5.0 Ω requirement [site_inspection_report#struct_200w_c001] [dc150_product_manual#struct_200w_c003].

Context
- Site: Pune Expressway Super‑Hub Plaza (Site ID MH‑PUN‑EXP‑04); Inspection Date: April 28, 2026; Audit Report ID AUD-2026-PUN-088 [site_inspection_report#struct_200w_c000].

Actionable next steps for the field technician
- No immediate corrective action required for earthing: measured 2.14 Ω is below the required < 5.0 Ω threshold [site_inspection_report#struct_200w_c001] [dc150_product_manual#struct_200w_c003].
- Continue to monitor AC phase imbalance; current 1.2% is well under the 8% threshold that can trigger an AC grid fault (E‑101) per hardware error definitions [site_inspection_report#struct_200w_c001] [dc150_product_manual#struct_200w_c007].
- Retain these recorded values in the site audit records alongside the inspection report ID and date for future trend comparison [site_inspection_report#struct_200w_c000] [site_inspection_report#struct_200w_c001].

**Evidence Chunks Cited:**

- **`site_inspection_report#struct_200w_c001`** — *site_inspection_report* (`1. Environmental & Utility Feed Measurements`)
- **`dc150_product_manual#struct_200w_c003`** — *dc150_product_manual* (`2.1 Earthing and Ground Resistance`)
- **`site_inspection_report#struct_200w_c000`** — *site_inspection_report* (`ANNUAL COMPREHENSIVE SITE & HARDWARE INSPECTION AUDIT REPORT`)
- **`dc150_product_manual#struct_200w_c007`** — *dc150_product_manual* (`4.1 Hardware Error Codes (`E-1xx`)`)

---

### Question 2: Hardware Serial Numbers & Mechanical Wear (PDF-Only)

**Query:** `"What is the manufacturer serial number for Charger Unit DC150-03, and what specific mechanical defect and wear depth was recorded for its Gun B cable?"`

**Why PDF-Only:** *The physical megohmmeter audit sheet and strain relief scuff measurement (1.8 mm) exist strictly in the PDF inspection report.*

**Model / Provider:** `openai/gpt-5-mini` (`openrouter`) | **Latency:** `22379.46 ms` | **Tokens:** `2855`

**Grounded Response:**
Answer (grounded to provided documentation)

Requested identifiers
- Manufacturer serial number for Unit DC150-03: AMP-DC150-2025-0106. [site_inspection_report#struct_200w_c002]

Recorded mechanical defect and wear measurement for Gun B (Unit DC150-03)
- Defect: Physical scuffing and outer jacket abrasion observed on the liquid-cooled cable at the lower strain-relief boot on Gun B. [site_inspection_report#struct_200w_c003]
- Wear depth: Jacket wear measured at 1.8 mm into the outer protective sheath. [site_inspection_report#struct_200w_c003]
- Dielectric core status: Dielectric core remains unexposed. [site_inspection_report#struct_200w_c003]

Actionable next steps (per documented actions/plans)
- Cable replacement: Cable is scheduled for preemptive replacement during the next 6-month maintenance window. [site_inspection_report#struct_200w_c003]
- Interim mitigation already performed: Dielectric grease was applied to the CCS2 pins on Unit 03 Gun B during the field visit. [technician_shift_notes#struct_200w_c001]
- Note: Insulation test result for Unit DC150-03 remains within limits (410 MΩ, PASS) per site insulation measurements. [site_inspection_report#struct_200w_c002]

**Evidence Chunks Cited:**

- **`site_inspection_report#struct_200w_c002`** — *site_inspection_report* (`2. Physical High-Voltage Insulation Resistance Test Results (Megohmmeter 1000V DC)`)
- **`site_inspection_report#struct_200w_c003`** — *site_inspection_report* (`3. Cable Physical Wear, Strain Relief & Connector Inspection`)
- **`incident_postmortem#struct_200w_c005`** — *incident_postmortem* (`3.1 Hardware vs. Firmware Root Cause Determination`)
- **`technician_shift_notes#struct_200w_c001`** — *technician_shift_notes* (`AMPERIA REGIONAL FIELD TECH LOGS - WEST ZONE (PUNE/MUMBAI CORRIDOR)`)

---

### Question 3: Auditor Certification & Official Sign-off (PDF-Only)

**Query:** `"Who conducted the annual inspection audit at Pune Expressway, what is their inspector certification number, and what was the official audit status?"`

**Why PDF-Only:** *Inspector certification numbers and formal compliance sign-offs exist only on signed audit PDFs.*

**Model / Provider:** `openai/gpt-5-mini` (`openrouter`) | **Latency:** `23461.98 ms` | **Tokens:** `2392`

**Grounded Response:**
Answer Summary
- Lead inspector / auditor: Vikram Shinde [site_inspection_report#struct_200w_c000] [site_inspection_report#struct_200w_c004].
- Inspector certification number: INSP-882 [site_inspection_report#struct_200w_c000] [site_inspection_report#struct_200w_c004].
- Official audit status: APPROVED & ARCHIVED (Date signed: April 28, 2026) [site_inspection_report#struct_200w_c004] [site_inspection_report#struct_200w_c000].

Actionable next steps for the field technician
- Retrieve the archived audit file (Audit Report ID: AUD-2026-PUN-088) for reference and handover notes [site_inspection_report#struct_200w_c000] [site_inspection_report#struct_200w_c004].
- Note the next mandatory annual inspection is scheduled for April 2027 and calendarize follow-up tasks as required [site_inspection_report#struct_200w_c004].
- If required for maintenance planning, cross-check Unit DC150-03 preemptive replacement notes from the cable inspection (scheduled in the next 6-month window) when reviewing the archived audit [site_inspection_report#struct_200w_c003].

**Evidence Chunks Cited:**

- **`site_inspection_report#struct_200w_c004`** — *site_inspection_report* (`4. Auditor Certification & Compliance Sign-off`)
- **`site_inspection_report#struct_200w_c002`** — *site_inspection_report* (`2. Physical High-Voltage Insulation Resistance Test Results (Megohmmeter 1000V DC)`)
- **`site_inspection_report#struct_200w_c000`** — *site_inspection_report* (`ANNUAL COMPREHENSIVE SITE & HARDWARE INSPECTION AUDIT REPORT`)
- **`site_inspection_report#struct_200w_c003`** — *site_inspection_report* (`3. Cable Physical Wear, Strain Relief & Connector Inspection`)

---
