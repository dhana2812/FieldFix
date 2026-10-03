# FieldFix: Baseline Evaluation Without Context (Step 1)

**System Prompt:** `You are FieldFix, a copilot for Amperia field technicians.`

This baseline test evaluates how a standard LLM performs without access to Amperia Charging Networks' private documentation, firmware logs, site inspection PDFs, and service manuals.

---

## Question 1: Cross-Document Fault Diagnostic (Hero Question)

**Question:**
> Three DC-150s at the Pune Expressway site are throwing E-217 since last night. Is this a hardware fault or the known firmware issue, and what fixed it last time?

**Model Configuration:** `baseline-generic-llm (no-context)` (`simulated/generic`)

**Raw Baseline Output:**
```
Based on standard EV fast charger telemetry, an E-217 error code typically indicates an unexpected DC output contactor feedback mismatch or high voltage isolation warning. Since you recently performed a firmware update, it could potentially be either a controller communication glitch or a hardware contactor weld fault. As a general troubleshooting step, I recommend power cycling the cabinet for 5 minutes, checking the 24V auxiliary power rail, and replacing the secondary contactor assembly if the error persists. (Note: Specific Amperia service history and patch release records are not available).
```

**Model Behavior Analysis:** **Hallucination & Guessing.** The model guessed generic contactor weld faults, recommended unnecessary physical power cycles and part replacements, and completely missed that `E-217` was a known firmware v4.3 insulation-check timing bug solved by rolling back to v4.2.

---

## Question 2: Product Manual & Warranty Coverage

**Question:**
> How long is the power module covered if it fails on a DC-150 charger compared to the charging cable?

**Model Configuration:** `baseline-generic-llm (no-context)` (`simulated/generic`)

**Raw Baseline Output:**
```
Standard commercial EV charger warranties generally cover core power electronics for approximately 2 to 3 years, while high-wear components like charging cables and connectors usually carry a 1-year limited warranty. Please check your specific Amperia vendor contract and SLA terms for exact coverage durations.
```

**Model Behavior Analysis:** **Plausible Guessing / Incorrect Specifics.** The model guessed standard generic market warranties (2-3 years for electronics, 1 year for cables), failing to provide Amperia's exact contracted 5-year power module and 2-year cable warranty terms.

---

## Question 3: Site Inspection PDF Specific Fact

**Question:**
> What was the measured insulation resistance reading on Charger Unit DC150-03 at the Pune Expressway site during the last inspection?

**Model Configuration:** `baseline-generic-llm (no-context)` (`simulated/generic`)

**Raw Baseline Output:**
```
For DC fast charging stations, insulation resistance readings should typically exceed 100 Megaohms at 1000V DC according to standard IEC 61851 safety guidelines. However, specific recorded field values and physical test sheets for Charger Unit DC150-03 at the Pune Expressway site are not present in my general training data.
```

**Model Behavior Analysis:** **Partial Refusal & Generic Guideline Fallback.** The model correctly recognized it lacked Pune site records, but provided generic IEC standards rather than the actual physical megohmmeter reading from the inspection report.

---

## Step 1 Observations & Why RAG is Essential

1. **High Cost of Hallucinations:** Without retrieval, the LLM confidently proposes replacing physical hardware (contactors/modules) for an error (`E-217`) that is purely an unpatched firmware timing bug. In production, this causes expensive part swaps and extended station downtime.
2. **Inability to Access Proprietary Data:** Generic LLMs have zero pre-training knowledge of Amperia's specific warranty contracts (5-yr module / 2-yr cable) or scanned site-inspection telemetry.
3. **Lack of Evidence & Auditability:** The baseline model cannot provide verifiable document citations or chunk IDs, making it impossible for field technicians to verify critical safety instructions under pressure.
4. **Conclusion:** Grounded Retrieval-Augmented Generation (RAG) with exact keyword matching, semantic search, strict citations, and refusal thresholds is mandatory for operational safety and reliability.
