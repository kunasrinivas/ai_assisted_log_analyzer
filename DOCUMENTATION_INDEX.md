# Documentation Index & Quick Links

## 📚 Core Documentation (Start Here)

| Document | Purpose | Best For |
|----------|---------|----------|
| [README.md](README.md) | Project overview, problem statement, architecture overview | Understanding the project goals & vision |
| [usage.md](usage.md) | Complete step-by-step walkthrough of the full system | Learning how data flows through the system |
| [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) | How to run the web GUI locally with Docker | Getting started with the web interface |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Detailed microservice architecture, service boundaries | Understanding technical design & components |

---

## 💰 Token Tracking & Cost Visibility (NEW)

| Document | Purpose | Best For |
|----------|---------|----------|
| [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md) | Cost format, efficiency grades, quick interpretation guide | Quick answers about metrics you see in GUI |
| [TOKEN_TRACKING_GUIDE.md](TOKEN_TRACKING_GUIDE.md) | Complete technical guide, pricing by model, optimization techniques | Deep understanding of token tracking system |
| [TOKEN_IMPLEMENTATION_SUMMARY.md](TOKEN_IMPLEMENTATION_SUMMARY.md) | What was built, code changes, testing results | Understanding implementation details |

---

## 🔧 Infrastructure & Tuning

| Document | Purpose | Best For |
|----------|---------|----------|
| [REDIS_TUNING.md](REDIS_TUNING.md) | Session storage tuning, connection settings, monitoring | Optimizing Redis for your environment |

---

## 🚀 Quick Start Paths

### I want to...

**...run the web GUI locally**
1. Start: [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) (2 min setup)
2. Run: `wsl bash scripts/run.sh`
3. Open: http://localhost:8080
4. Learn: [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md) (what those metrics mean)

**...understand the system architecture**
1. Read: [README.md](README.md) (overview)
2. Read: [usage.md](usage.md) (step-by-step flow)
3. Read: [ARCHITECTURE.md](ARCHITECTURE.md) (technical details)

**...optimize costs and efficiency**
1. Read: [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md) (quick reference)
2. Read: [TOKEN_TRACKING_GUIDE.md](TOKEN_TRACKING_GUIDE.md) (detailed tuning)
3. Try: `python token_tracking_demo.py` (see scenarios)

**...configure Redis and session storage**
1. Read: [REDIS_TUNING.md](REDIS_TUNING.md)
2. Update `.env` or `docker-compose.yml`
3. Restart: `wsl bash scripts/run.sh down; wsl bash scripts/run.sh`

**...deploy to production**
1. Read: [ARCHITECTURE.md](ARCHITECTURE.md) → "Production Hardening" section
2. Configure: Redis, JWT auth, API keys
3. Set environment variables (see [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) Prerequisites)
4. Monitor: Token metrics logging, correlations IDs

---

## 📊 Token Metrics Reference

**Seen a metrics badge in the GUI?** Here's what each part means:

```
┌─ TOKENS ────────┬─ COST ──────────┬─ EFFICIENCY ────┐
│ 275 total       │ 2.1m$           │ C (0.173)        │
│ 203 in, 72 out  │ Model: gpt-4o   │ Optimal context  │
└─────────────────┴─────────────────┴──────────────────┘
```

- **Tokens**: Total tokens used (lower = cheaper). Breakdown: input (prompt) + output (completion)
- **Cost**: USD in human-readable format (µ$ = microunits, m$ = milliunits, $ = dollars)
- **Efficiency**: Grade A-F based on tokens per character (lower = better)
- **Model**: Which OpenAI model was used

**Want to understand more?** → [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md)

---

## 🔗 Cross-References

### By Feature

**Web GUI & UI**
- [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) — How to run locally
- [ARCHITECTURE.md](ARCHITECTURE.md) → Presentation Layer

**Log Analysis & Signals**
- [usage.md](usage.md) → Steps 1-4 (parsing, normalization, signal extraction)
- [ARCHITECTURE.md](ARCHITECTURE.md) → Application Layer

**Token Metrics & Cost**
- [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md) — Quick answers
- [TOKEN_TRACKING_GUIDE.md](TOKEN_TRACKING_GUIDE.md) — Deep dive
- [TOKEN_IMPLEMENTATION_SUMMARY.md](TOKEN_IMPLEMENTATION_SUMMARY.md) — What was built
- [ARCHITECTURE.md](ARCHITECTURE.md) → Token Usage & Cost Tracking Layer

**Session & Storage**
- [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) → Session & Storage section
- [REDIS_TUNING.md](REDIS_TUNING.md) — Detailed tuning guide
- [ARCHITECTURE.md](ARCHITECTURE.md) → Production Hardening

**Security & Auth**
- [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) → Redis & Connection Tuning
- [ARCHITECTURE.md](ARCHITECTURE.md) → Production Hardening

### By Audience

**Solution Architects**
1. [README.md](README.md)
2. [ARCHITECTURE.md](ARCHITECTURE.md)
3. [TOKEN_IMPLEMENTATION_SUMMARY.md](TOKEN_IMPLEMENTATION_SUMMARY.md)

**DevOps / Infrastructure**
1. [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md)
2. [REDIS_TUNING.md](REDIS_TUNING.md)
3. [ARCHITECTURE.md](ARCHITECTURE.md) → Production Hardening

**Data Scientists / ML Engineers**
1. [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md)
2. [TOKEN_TRACKING_GUIDE.md](TOKEN_TRACKING_GUIDE.md)
3. `python token_tracking_demo.py`

**End Users / NOC Analysts**
1. [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) → Usage section
2. [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md)

---

## 📈 Example Workflows

### Workflow 1: Analyzing Logs with Cost Visibility

```
1. Open http://localhost:8080
2. Paste or upload logs
3. Click "Analyze and Index"
4. Ask question: "What abnormal behavior do you see?"
5. SEE → Answer + Metrics Badge
   - Tokens used
   - Cost in m$
   - Efficiency grade
6. Optimize by:
   - Switching model (gpt-4o → gpt-4o-mini for 30× savings)
   - Refining system prompt for conciseness
```

### Workflow 2: Cost Optimization

```
1. Run demo: python token_tracking_demo.py
2. See: Cost comparison across models
3. See: Monthly cost projection (1000 questions/day)
4. Decision: Switch to gpt-4o-mini? (saves ~$116/month)
5. Verify: Run end-to-end test to confirm quality
6. Deploy: Update AZURE_OPENAI_MODEL in .env
```

### Workflow 3: Production Deployment

```
1. Read ARCHITECTURE.md → Production Hardening
2. Configure:
   - Redis (persistent or in-memory fallback)
   - JWT auth (JWT_REQUIRED=true)
   - API key (BFF_API_KEY)
   - Session TTL (SESSION_TTL_SECONDS)
3. Run: wsl bash scripts/run.sh
4. Test: Health check, analyze, chat
5. Monitor: Token metrics logged in docker compose logs
```

---

## 🆘 Troubleshooting

### Metrics not showing in GUI?
→ See [TOKEN_TRACKING_GUIDE.md](TOKEN_TRACKING_GUIDE.md) → Troubleshooting

### High costs on a model?
→ See [TOKEN_TRACKING_GUIDE.md](TOKEN_TRACKING_GUIDE.md) → Performance Tuning Checklist

### Redis connection failing?
→ See [REDIS_TUNING.md](REDIS_TUNING.md) → Common Issues & Fixes

### Need to understand efficiency grades?
→ See [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md) → Efficiency Grades Explained

---

## 📋 Summary of Features

| Feature | Status | Documentation |
|---------|--------|-----------------|
| Web GUI with Nginx | ✅ | [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) |
| Microservice architecture | ✅ | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Log analysis & signals | ✅ | [usage.md](usage.md) |
| Redis session storage | ✅ | [REDIS_TUNING.md](REDIS_TUNING.md) |
| Optional JWT auth | ✅ | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Correlation ID tracing | ✅ | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Token usage tracking (NEW)** | ✅ | [TOKEN_TRACKING_GUIDE.md](TOKEN_TRACKING_GUIDE.md) |
| **Cost visibility (NEW)** | ✅ | [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md) |
| **Efficiency metrics (NEW)** | ✅ | [TOKEN_IMPLEMENTATION_SUMMARY.md](TOKEN_IMPLEMENTATION_SUMMARY.md) |
| **Real-time GUI display (NEW)** | ✅ | [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) |

---

## 🎯 Recommended Reading Order

**For First-Time Users** (30 min total):
1. [README.md](README.md) (5 min) — Get the big picture
2. [WEB_GUI_SETUP.md](WEB_GUI_SETUP.md) (5 min) — Set up locally
3. [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md) (5 min) — Understand metrics
4. Try it: `wsl bash scripts/run.sh` → http://localhost:8080
5. Experiment: Ask questions, see metrics badges

**For Deep Dive** (2 hours total):
1. [README.md](README.md) (5 min)
2. [usage.md](usage.md) (15 min)
3. [ARCHITECTURE.md](ARCHITECTURE.md) (20 min)
4. [TOKEN_TRACKING_GUIDE.md](TOKEN_TRACKING_GUIDE.md) (30 min)
5. [REDIS_TUNING.md](REDIS_TUNING.md) (15 min)
6. Run demo: `python token_tracking_demo.py` (10 min)
7. Experiment: Try different models, prompts, contexts

---

**Last Updated**: April 30, 2026 | **Status**: All docs updated with token tracking v2.0
