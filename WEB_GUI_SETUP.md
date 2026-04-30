# Web GUI + Microservice Setup

## Prerequisites
- WSL2 with Ubuntu 24.04 (no Docker Desktop required)
- Existing .env in repository root with Azure settings already used by the CLI app

Required env vars:
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_MODEL
- AZURE_SEARCH_ENDPOINT
- AZURE_SEARCH_INDEX

## One-time Docker Engine setup inside WSL2
Run this once from PowerShell — it installs Docker Engine (no Docker Desktop) in your Ubuntu 24.04 distro:

```powershell
wsl bash scripts/wsl2_docker_setup.sh
```

## Build and Run
From PowerShell (calls into WSL2):

```powershell
wsl bash scripts/run.sh        # build images and start all services
wsl bash scripts/run.sh down   # stop everything
wsl bash scripts/run.sh logs   # tail logs
```

Or directly inside a WSL2 shell:

```bash
bash scripts/run.sh
```

WSL2 automatically forwards ports to Windows localhost, so no extra configuration is needed.

## Open the UI
- http://localhost:8080

## Health Checks
- BFF: http://localhost:8010/api/health
- Signal, Index, and Chat services are internal-only and are not host-exposed.

## Usage
1. Paste logs in CSV format or upload a text file.
2. Click **Analyze and Index**.
3. Ask assurance questions in the chat section.
4. **View token metrics** — A badge appears below each answer showing:
   - Token counts (input + output + total)
   - Cost in USD (µ$, m$, or $)
   - Efficiency grade (A-F)
   - Context balance ratio

## Token Metrics Display

After each question, the UI displays a **metrics badge** with:

```
┌─────────────────────────────────────────────────────┐
│ Tokens: 275 | Cost: 2.1m$ | Efficiency: C (0.173) │
│ Prompt: 203 | Completion: 72 | Model: gpt-4o       │
└─────────────────────────────────────────────────────┘
```

**What each metric means**:
- **Tokens**: Lower is cheaper. 275 typical for average response.
- **Cost**: Display format (µ$ = micro, m$ = milli, $ = dollars)
- **Efficiency**: Grade A-F. A = concise, F = verbose.
- **Model**: Which OpenAI model was used for this response.

Use metrics to optimize:
- Switch models (gpt-4o-mini is ~30× cheaper)
- Refine system prompt for conciseness
- Filter context to only relevant signals

See [TOKEN_QUICK_REFERENCE.md](TOKEN_QUICK_REFERENCE.md) for quick guidance.

## Session & Storage
- Redis-backed session storage is enabled by default in Docker Compose.
- Optional API key auth is supported at the BFF layer via `BFF_API_KEY`.
- Optional JWT auth can be enabled via `JWT_REQUIRED=true` with matching JWT settings.
- Token metrics are computed server-side and included in every chat response.
- Compose defaults are suitable for local development; tune limits and auth for production.

## Redis & Connection Tuning

For custom Redis or connection settings, see [REDIS_TUNING.md](REDIS_TUNING.md):
- Session TTL (default 3600s)
- Connection timeout (default 5.0s)
- Max retries (default 3)
- Eviction policy for memory management
