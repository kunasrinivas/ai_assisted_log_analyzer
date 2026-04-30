# Token Usage & Cost Tracking Guide

## Overview

The application now tracks LLM token usage (input/output tokens) and calculates costs in real-time, displaying them in the GUI with efficiency metrics.

---

## Architecture

### Token Tracking Flow

```
User Question
    ↓
BFF (/api/chat)
    ↓
Chat Service (/ask)
    ↓
LLM (Azure OpenAI/Foundry)
    ↓ Response with usage stats
Token Tracker extracts:
  - prompt_tokens
  - completion_tokens
    ↓
Cost Calculator (based on model pricing)
    ↓
Efficiency Metrics (tokens per char, etc)
    ↓
Response to UI with:
  {
    "answer": "...",
    "tokens": {
      "tokens": { "prompt": X, "completion": Y, "total": Z },
      "cost": { "input_cost_usd": A, "output_cost_usd": B, "total_cost_usd": C },
      "efficiency": { "tokens_per_answer_char": E, "input_output_ratio": R, ... },
      "model": "gpt-4o"
    }
  }
    ↓
UI displays Metrics Badge with:
  - Token counts (prompt/completion/total)
  - Cost in human-readable format (microUSD, milliUSD, USD)
  - Efficiency grade (A-F) based on token/character ratio
```

### Key Components

#### 1. **src/token_cost_tracker.py** - Token Extraction & Cost Calculation
- `TokenUsageMetrics` class: Encapsulates token counts, model, and character lengths
- `extract_token_usage(response, model)`: Extracts usage from OpenAI/Azure responses
- `format_cost_human_readable(usd)`: Formats costs (e.g., "2.3µ$", "1.5m$", "$0.05")
- `format_efficiency_grade(metrics)`: Grades efficiency A-F
- Supports all Azure OpenAI models with configurable pricing

#### 2. **src/rag_chatbot.py** - LLM Integration
- `ask_assurance_question_with_metrics()`: New function returns `(answer, TokenUsageMetrics)`
- `ask_assurance_question()`: Backwards-compatible, returns answer only
- Token extraction happens at LLM query time (in `_query_chat()`, `_query_responses()`)

#### 3. **services/chat_service/main.py** - Chat Endpoint
- `/ask` endpoint now returns:
  ```json
  {
    "answer": "Assistant response text...",
    "tokens": {
      "tokens": {...},
      "cost": {...},
      "efficiency": {...},
      "model": "gpt-4o"
    }
  }
  ```
- Falls back gracefully if token data unavailable (maintains fallback mode)

#### 4. **services/ui/index.html** - GUI Display
- Metrics badge shows after each chat response:
  - **Tokens**: Breakdown of prompt/completion/total
  - **Cost**: Total + per-direction costs in human-readable format
  - **Efficiency**: A-F grade + tokens-per-character ratio
- Responsive design works on mobile
- Green styling indicates efficiency metrics

---

## Pricing Model

### Supported Models (2024 rates)

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o | $5/1M | $15/1M |
| gpt-4o-mini | $0.15/1M | $0.60/1M |
| gpt-4-turbo | $10/1M | $30/1M |
| gpt-4 | $30/1M | $60/1M |
| gpt-35-turbo | $0.50/1M | $1.50/1M |

### Cost Calculation Formula

```
Input Cost = (prompt_tokens / 1,000,000) × input_price_per_million
Output Cost = (completion_tokens / 1,000,000) × output_price_per_million
Total Cost = Input Cost + Output Cost
```

### Human-Readable Cost Format

- **< $0.000001** (1µ$): Microunits (µ$) — e.g., "0.5µ$"
- **$0.000001 - $0.001**: Milliunits (m$) — e.g., "1.2m$"
- **≥ $0.001**: USD — e.g., "$0.05"

### Updating Pricing

Edit `src/token_cost_tracker.py`:
```python
PRICING_MODELS = {
    "your-model": {"input": X.XX, "output": Y.YY},  # $/1M tokens
}
```

---

## Efficiency Metrics

### Tokens Per Answer Character (Most Important)

**Lower is better** — fewer tokens wasted on verbose answers.

```
Efficiency = completion_tokens / answer_length_in_chars
```

**Grading Scale:**
- **A (Excellent)**: < 0.05 tokens/char — Concise, efficient answers
- **B (Good)**: 0.05 - 0.10 — Reasonable verbosity
- **C (Fair)**: 0.10 - 0.15 — Acceptable but could be more concise
- **D (Poor)**: 0.15 - 0.25 — Verbose, potential room for optimization
- **F (Very Poor)**: > 0.25 — Very verbose answers

### Input/Output Ratio

**Ideal range: 1.0 - 2.0** — Indicates balanced context-to-answer ratio.

```
Context Balance = prompt_tokens / completion_tokens
```

**Interpretation:**
- **< 1.0**: Answer-heavy (lot of output from little context)
- **1.0 - 2.0**: Optimal (context supports proportional output)
- **> 2.0**: Context-heavy (too much input, shorter answers)

### Answer to Question Ratio

**Interpretive** — Shows how much the system elaborated.

```
Elaboration = answer_length_chars / question_length_chars
```

**Example:**
- Question: "What is this?" (14 chars)
- Answer: "This is a..." (500 chars)
- Ratio: 500/14 = 35.7× elaboration (high but expected)

---

## How to Measure Efficiency Improvements

### 1. **Track Metrics Over Time**

Enable logging and store token metrics:

```bash
wsl docker compose logs chat-service | grep token_usage
```

Log output example:
```json
{
  "event": "token_usage",
  "metrics": {
    "tokens": {"prompt": 450, "completion": 85, "total": 535},
    "cost": {"input_cost_usd": 0.00225, "output_cost_usd": 0.001275, "total_cost_usd": 0.003525},
    "efficiency": {"tokens_per_answer_char": 0.089, "input_output_ratio": 5.29}
  }
}
```

### 2. **Optimize System Prompt**

**Test different prompts and compare:**

```python
# src/rag_chatbot.py - SYSTEM_PROMPT
SYSTEM_PROMPT = """You are an assurance assistant. Answer with concise, practical guidance."""
```

**Metrics to compare:**
- `tokens_per_answer_char` (lower = more efficient)
- `total_cost_usd` (obvious cost savings)
- `input_output_ratio` (should stay 1-2 range)

### 3. **Context Pruning**

Remove unnecessary data from context before querying:

```python
# Only pass relevant signals to LLM, not entire JSON
context = {
    "key_signals": signals[:5],  # Top 5 instead of all
    "critical_assurance": assurance
}
```

**Impact:**
- Lower `prompt_tokens` → Lower input cost
- May increase `completion_tokens` if model elaborates more
- Overall cost usually decreases

### 4. **Compare Models**

**Test prompt with different models:**

```python
# In rag_chatbot.py, swap model name
model = "gpt-4o-mini"  # vs "gpt-4o"
```

**Metrics to track:**
- Same answer quality, compare total cost
- `tokens_per_answer_char` (efficiency)
- Response time

**Example comparison:**
| Model | Input Cost | Output Cost | Total | Efficiency |
|-------|-----------|-----------|--------|-----------|
| gpt-4o | $0.0023 | $0.0013 | $0.0036 | 0.089 |
| gpt-4o-mini | $0.00003 | $0.00005 | $0.00008 | 0.112 |

---

## Communicating Costs to Users

### Strategy 1: Real-Time Display (Current Implementation)

Show metrics badge after each response:
- ✅ Transparent about costs
- ✅ Educates users about efficiency
- ✅ No hidden surprises

### Strategy 2: Usage Dashboard

Create `/api/usage-summary` endpoint:
```json
{
  "session_id": "...",
  "questions_asked": 3,
  "total_tokens": 1050,
  "total_cost_usd": 0.015,
  "average_cost_per_question": 0.005,
  "most_efficient_question": {...},
  "cost_trend": "stable"
}
```

### Strategy 3: Budget Alerts

Add cost threshold warnings:

```python
# services/bff/main.py
MAX_SESSION_COST_USD = float(os.getenv("MAX_SESSION_COST_USD", "1.0"))

if session_cost > MAX_SESSION_COST_USD:
    # Warn user before processing
    raise HTTPException(status_code=429, detail="Session cost limit exceeded")
```

UI displays:
```
⚠️ Warning: This session is approaching cost limit ($1.00/max)
Current: $0.87 | Remaining: $0.13
```

### Strategy 4: Cost Factorization

Break down cost by component:

```json
{
  "answer": "...",
  "tokens": {
    "cost_breakdown": {
      "system_prompt": "$0.00001",     // Fixed overhead
      "user_question": "$0.00002",     // Variable on Q length
      "context_signals": "$0.00100",   // Main cost driver
      "answer_generation": "$0.00127"  // Model output
    }
  }
}
```

Helps users understand what drives costs → optimize context size.

---

## Implementation Checklist

✅ Token extraction from OpenAI/Azure responses
✅ Cost calculation based on model pricing
✅ Efficiency metrics (tokens per char, ratios)
✅ Real-time GUI display in metrics badge
✅ Human-readable cost formatting (µ$, m$, USD)
✅ Fallback handling (graceful degradation if no token data)
✅ Structured logging of token events

### Optional Enhancements

- [ ] Usage dashboard endpoint (`/api/usage-summary`)
- [ ] Budget alerts per session/user
- [ ] Cost trends visualization
- [ ] Model comparison tool
- [ ] System prompt optimization recommendations
- [ ] Batch cost estimates (before processing)
- [ ] User activity report (weekly/monthly costs)
- [ ] Cost-aware rate limiting

---

## Troubleshooting

### Tokens not appearing in GUI

1. Check browser console for errors: `F12 → Console tab`
2. Verify chat service is returning `tokens` field:
   ```bash
   wsl curl -X POST http://localhost:8010/api/chat \
     -H "Content-Type: application/json" \
     -d '{"session_id":"test","question":"Hi"}' | jq .tokens
   ```
3. Check LLM response includes `usage` object (Azure OpenAI always does)

### Cost seems wrong

1. Verify model name in response matches `PRICING_MODELS` keys
2. Check token counts are reasonable (prompt should be > completion usually)
3. Review pricing rates in `src/token_cost_tracker.py` — rates change over time

### Efficiency grade is poor (D/F)

1. Review system prompt — is it overly verbose?
2. Check context size — reduce unnecessary signals
3. Try shorter answers in system prompt: "Be concise."
4. Test with `gpt-4o-mini` for comparison

---

## Example: Full Session with Token Tracking

```
User: "What abnormal behavior do you see?"

Response:
  Answer: "The system shows elevated error rates in BILLING_SYSTEM..."
  
  Tokens:
    - Prompt: 450 tokens
    - Completion: 85 tokens
    - Total: 535 tokens
  
  Cost:
    - Input: $0.00225 (450 × $5/1M)
    - Output: $0.001275 (85 × $15/1M)
    - Total: $0.003525 (~3.5m$)
  
  Efficiency:
    - Grade: B ✓ (0.089 tokens/char)
    - Context Balance: Optimal (5.3:1)
    - Elaboration: 35.7× (question was short)
```

**Interpretation:** Good efficiency, reasonable cost, well-balanced response.

---

## References

- [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)
- [Token Estimation Tool](https://platform.openai.com/tokenizer)
- [LLM Token Efficiency Best Practices](https://cookbook.openai.com/articles/what_every_llm_developer_should_know)
