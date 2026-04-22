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

<img width="4032" height="403" alt="image" src="https://github.com/user-attachments/assets/62c10dbd-2386-4ea4-9e62-df31f9fdba98" />
