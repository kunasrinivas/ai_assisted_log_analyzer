# AI‑Assisted Service Assurance Log Insight Bot
*(Azure AI Foundry POC)*

## Overview

This repository contains a **small, explainable Proof‑of‑Concept (POC)** chatbot designed to demonstrate how **Azure AI Foundry** can be used to assist **Service Assurance** teams in a telecom OSS environment.

The solution analyzes OSS log files and converts them into **service‑level insights** rather than raw technical alerts.  
The focus of this POC is **architectural clarity, domain reasoning, and explainability**, not scale or full automation.

This project is intentionally minimal and realistic, suitable for discussion in **Solution Architect interviews** or technical design reviews.

---

## Problem Statement

Traditional OSS monitoring tools generate large volumes of logs and alarms, but Service Assurance engineers still need to:
- Correlate symptoms manually
- Infer service impact from infrastructure‑level signals
- Spend significant time reading logs instead of reasoning about services

Rule‑based or threshold‑based systems can detect anomalies, but they **do not explain** what the issue means from a **service assurance perspective**.

---

## Solution Approach

This POC demonstrates how an **LLM‑powered chatbot**, grounded using **Azure AI Foundry + Retrieval‑Augmented Generation (RAG)**, can:

- Analyze OSS logs semantically
- Identify abnormal behavior
- Classify the issue in Service Assurance terms
- Explain potential service impact
- Suggest next investigation steps

The chatbot **assists engineers** rather than replacing them and always produces **explainable, domain‑aware output**.

---

## Architecture

### High‑Level Architecture Diagram

<img width="4032" height="591" alt="image" src="https://github.com/user-attachments/assets/bcfe3ffe-543f-4d91-bedf-06a4a49bd75a" />


# Key Design Decisions

## Why Azure AI Foundry?

- Provides governance, prompt orchestration, and grounding
- Reduces hallucinations through controlled retrieval
- Aligns with enterprise cloud and compliance expectations

---

## Why Retrieval‑Augmented Generation (RAG)?

- Logs are treated as **knowledge**, not just events
- Prevents the model from guessing or inventing causes
- Improves trust and explainability in Service Assurance environments

---

## Why Keep This POC Small?

- Large AIOps platforms hide architectural decisions
- A minimal system makes reasoning, trade‑offs, and intent visible
- This mirrors how early‑stage innovation typically starts in telco environments

---

# Functional Scope

## What This POC Does

- Parses and chunks OSS log files
- Performs semantic search over logs
- Answers service‑oriented questions using an LLM
- Produces explainable Service Assurance insights

---

## What This POC Deliberately Does **NOT** Do

- Real‑time streaming ingestion
- Automated remediation
- Full alarm correlation
- Vendor‑specific behavior modeling

These exclusions are intentional to keep the design transparent, explainable, and interview‑appropriate.

---

# Example Questions Supported

- “What abnormal behavior do you see in these logs?”
- “Is this a fault or a performance issue?”
- “Which service layer could be impacted?”
- “Is this likely a symptom or a root cause?”
- “What should a Service Assurance engineer investigate next?”

---

# Example Output

> “The logs indicate repeated downstream timeouts leading to delayed SLA monitoring updates. This suggests a performance degradation rather than a hard fault. From a Service Assurance perspective, this issue is likely to impact customer‑facing services if sustained. Further investigation should focus on dependency latency and service topology relationships.”

This style of output is aligned with **OSS Service Assurance workflows**, not generic IT monitoring.

---

# Project Structure

```text
.
├── logs/
│   └── sample_oss_logs.txt
├── src/
│   ├── log_parser.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── vector_index.py
│   └── chatbot.py
├── architecture/
│   └── architecture.png
├── README.md
```
# Fact Check
Using raw logs directly in RAG does not scale for Tier‑1 telcos due to volume, cost, and noise.
In my design, logs are pre‑processed into service‑relevant signals, and only those insights are used in RAG.
Raw logs remain accessible as evidence, not primary knowledge.
