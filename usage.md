# How to Use the OSS Assurance Insight Bot

This document provides a **single, end‑to‑end explanation** of how to use the OSS Assurance Insight Bot. It describes the full lifecycle from raw telco OSS logs to AI‑assisted Service Assurance insights, without fragmentation, so the reader can understand the system holistically.

---

## Overview

The OSS Assurance Insight Bot follows a layered, signal‑first architecture designed for Tier‑1 telecom environments. The goal is to ensure that **raw logs are never passed directly to an LLM**. Instead, logs are transformed into **service‑relevant signals** before AI reasoning is applied.

The overall flow is:

```
Raw OSS Logs
→ Log Parsing & Normalization
→ Signal Extraction
→ Service Assurance Interpretation
→ RAG Indexing (Azure AI Search)
→ Azure AI Foundry Reasoning
→ Service Assurance Insights
```

---

## Step 1: Provide OSS Log Input

**Location**:

```
logs/sample_telco_oss_logs.txt
```

The input file contains telco OSS telemetry such as:

- Core switch events
- Billing and CDR processing events
- SMS gateway logs
- Network performance warnings

Each log entry follows a simple CSV structure:

```
<timestamp>,<severity>,<system>,<message>
```

At this stage, logs are **high‑volume, noisy, and unstructured from a Service Assurance perspective**.

---

## Step 2: Log Parsing and Normalization

**Module**: `src/log_reader.py`

The system reads the raw log file and converts each line into a structured event object containing:

- Timestamp
- Severity level (INFO, WARN, ERROR)
- Originating OSS or network component
- Message text

**Why this step matters**:

- Removes parsing ambiguity
- Produces uniform input for downstream logic
- Mirrors real OSS ingestion pipelines

After this step, logs are structured but still represent **telemetry**, not actionable knowledge.

---

## Step 3: Signal Extraction (Telemetry → Knowledge)

**Module**: `src/signal_engine.py`

This is the most critical architectural step. The signal engine scans normalized log events and extracts **high‑signal assurance facts**, such as:

- Repeated error bursts from the same system
- Call drops and service interruptions
- Network latency or packet loss indicators

Example transformation:

Raw log events (many):

```
ERROR,BILLING_SYSTEM,Database connection timeout
ERROR,BILLING_SYSTEM,Failed to update CDR
WARN,NETWORK_MONITOR,Packet loss detected
```

Derived signals (few):

```json
{
  "type": "ERROR_BURST",
  "system": "BILLING_SYSTEM",
  "confidence": "HIGH"
}
```

**Why this step exists**:

- Reduces noise and cost
- Improves explainability
- Makes AI reasoning scalable for Tier‑1 telcos

From this point onward, the system works with **knowledge**, not raw logs.

---

## Step 4: Service Assurance Interpretation

**Module**: `src/assurance_model.py`

Derived signals are mapped to **Service Assurance concepts**, including:

- Assurance domain (Performance, Service Quality)
- Potential customer impact
- Likely root‑cause patterns (capacity, dependency, or fault)

This aligns technical observations with how **NOC and Assurance teams reason**, rather than how infrastructure components log errors.

---

## Step 5: Index Signals for RAG

**Module**: `src/rag_indexer.py`

Only service‑relevant signals are indexed into **Azure AI Search**. Raw logs are explicitly excluded.

Key characteristics:

- Uses Azure Managed Identity (`DefaultAzureCredential`)
- No API keys or secrets
- RBAC‑controlled access

This creates a **clean, high‑signal retrieval layer** for AI reasoning.

---

## Step 6: Ask Questions via Azure AI Foundry (RAG)

**Module**: `src/rag_chatbot.py`

Users can ask natural‑language Service Assurance questions such as:

- "Is there any customer service impact?"
- "Is this a fault or a performance issue?"
- "What should the assurance team investigate next?"

The RAG flow:

1. Question is submitted
2. Relevant signals are retrieved from Azure AI Search
3. Azure AI Foundry applies domain‑specific reasoning
4. A service‑oriented response is generated

The system prompt ensures the LLM:

- Analyzes signals, not logs
- Avoids vendor‑specific guessing
- Produces explainable output

---

## Step 7: Generate Service Assurance Insights

**Output**:

The final response is a human‑readable Service Assurance summary explaining:

- What abnormal behaviour was detected
- Which assurance domain is involved
- Whether customer‑facing services may be impacted
- Recommended next investigation steps

This output is suitable for:

- NOC dashboards
- Incident triage
- Management summaries

---

## Step 8: View Token Usage & Cost Metrics

**Module**: `src/token_cost_tracker.py`

After the LLM generates a response, token usage metrics are automatically captured and displayed, including:

- **Tokens**: Number of input tokens (prompt) and output tokens (completion) consumed
- **Cost**: Automatic USD calculation based on the model's pricing tier
- **Efficiency**: Grade A-F based on how concisely the model answered
- **Context Balance**: Ratio of input to output tokens (ideal: 1-2 range)

In the **web GUI**, metrics appear in a badge below each answer:

```
┌─ TOKENS ───────────┬─ COST ──────────┬─ EFFICIENCY ────┐
│ 275 total          │ 2.1m$           │ C (0.173)        │
│ 203 in, 72 out     │ Input: 1.0µ$    │ Optimal context  │
│                    │ Output: 1.1µ$   │ (2.82:1 ratio)   │
└────────────────────┴─────────────────┴──────────────────┘
```

**Cost Format Reference**:
- `µ$` = Microunits ($0.0001) — single responses
- `m$` = Milliunits ($0.001) — typical responses
- `$` = Dollars ($1.00) — high-volume usage

**Efficiency Grades**:
- **A 🌟** (< 0.05 tokens/char): Excellent, very concise
- **B ✓** (0.05-0.10): Good, balanced
- **C** (0.10-0.15): Fair, acceptable
- **D** (0.15-0.25): Poor, verbose
- **F** (> 0.25): Very poor, wasting tokens

Use these metrics to:
- Understand LLM costs in real-time
- Identify which questions are most efficient
- Optimize system prompts to reduce verbosity
- Compare model costs (e.g., gpt-4o vs gpt-4o-mini)

For detailed guidance, see [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md).

---

## Step 9: Run the Full Pipeline (CLI Mode)

Execute the end‑to‑end flow using:

```
python src/main.py
```

You will see:

- Logs processed
- Signals extracted and indexed
- An interactive prompt for Service Assurance questions

Type `exit` to end the session.

---

## Key Architectural Principle

**Logs are telemetry. Signals are knowledge.**

The OSS Assurance Insight Bot enforces this separation to ensure scalability, cost control, and explainability in AI‑assisted Service Assurance.
