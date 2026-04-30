# Redis Configuration & Tuning Guide

## Current Configuration

### Session Storage (BFF)
| Parameter | Default | Env Var | Purpose |
|-----------|---------|---------|---------|
| Session TTL | 3600s (1h) | `SESSION_TTL_SECONDS` | How long sessions persist before auto-expiration |
| Max Sessions | 1000 | `MAX_SESSIONS` | Memory bound when using in-memory fallback |
| Redis URL | `redis://redis:6379/0` | `REDIS_URL` | Connection string to Redis instance |

### Connection Handling (Python redis library)
| Parameter | Default | Env Var | Purpose |
|-----------|---------|---------|---------|
| **NEW** Connection Timeout | 5.0s | `REDIS_SOCKET_CONNECT_TIMEOUT` | How long to wait for initial connection |
| **NEW** Socket Timeout | 5.0s | `REDIS_SOCKET_TIMEOUT` | How long to wait for responses |
| **NEW** Socket Keepalive | true | `REDIS_SOCKET_KEEPALIVE` | Enable TCP keepalive on Redis connection |
| **NEW** Max Retries | 3 | `REDIS_MAX_RETRIES` | Retry attempts on transient errors |
| **NEW** Retry Backoff | 0.1s | `REDIS_RETRY_BACKOFF_MS` | Initial backoff between retries (ms) |

### Redis Server Configuration (docker-compose)
| Parameter | Current | Purpose |
|-----------|---------|---------|
| Save Policy | `--save ""` | Disable RDB snapshots (in-memory only) |
| Append Only | `--appendonly no` | Disable AOF persistence |
| **NEW** Eviction Policy | (default) | Behavior when memory limit reached |
| **NEW** Max Memory | (unlimited) | Memory limit before eviction |
| **NEW** Databases | (default 16) | Number of logical databases (0-15) |

---

## Tuning Scenarios

### Development (Current Default)
```bash
# BFF environment
SESSION_TTL_SECONDS=3600
MAX_SESSIONS=1000
REDIS_URL=redis://redis:6379/0

# docker-compose: in-memory, no persistence
redis-server --save "" --appendonly no
```
**Profile**: Low memory, single-database, forgiving timeouts
**Use when**: Local testing, temporary sessions, development

### Staging (Balanced)
```bash
# BFF environment
SESSION_TTL_SECONDS=1800          # 30 min sessions
MAX_SESSIONS=5000                 # More concurrent sessions
REDIS_URL=redis://redis:6379/0
REDIS_SOCKET_CONNECT_TIMEOUT=10   # Slightly more generous
REDIS_SOCKET_TIMEOUT=10
REDIS_MAX_RETRIES=5
REDIS_RETRY_BACKOFF_MS=100

# docker-compose
redis-server --save "" --appendonly no --maxmemory 256mb --maxmemory-policy allkeys-lru
```
**Profile**: Moderate memory (256MB), auto-eviction on overflow, more resilient
**Use when**: Testing load, pre-production validation

### Production (High Availability)
```bash
# BFF environment
SESSION_TTL_SECONDS=900           # 15 min sessions (frequent refresh)
MAX_SESSIONS=10000                # Many concurrent sessions
REDIS_URL=redis://redis:6379/0
REDIS_SOCKET_CONNECT_TIMEOUT=15
REDIS_SOCKET_TIMEOUT=15
REDIS_MAX_RETRIES=10
REDIS_RETRY_BACKOFF_MS=200

# docker-compose
redis-server --save "" --appendonly no --maxmemory 512mb --maxmemory-policy allkeys-lru --databases 2
```
**Profile**: Higher resilience, memory-bounded, session churn expected
**Use when**: Production deployment, multi-tenant workloads

---

## Tuning Parameters Explained

### 1. Session TTL (`SESSION_TTL_SECONDS`)
- **Lower (300-900s)**: Frequent session renewal, less state per session, more Redis requests
  - **Best for**: High-security scenarios, strict data minimization
  - **Trade-off**: More server load
- **Higher (3600-7200s)**: Longer sessions, fewer renewals, better UX
  - **Best for**: Internal tools, low-sensitivity workloads
  - **Trade-off**: Longer exposure if session compromised

**Recommendation**: 
- Dev: 3600s (1h)
- Staging: 1800s (30m)
- Production: 900s (15m)

### 2. Connection Timeout (`REDIS_SOCKET_CONNECT_TIMEOUT`)
- **Lower (1-5s)**: Fail fast, suitable for co-located Redis
- **Higher (10-30s)**: Tolerate network latency, cloud deployments

**Recommendation**: 
- Co-located (same container network): 5s
- Same VPC/region: 10s
- Cross-region: 15-30s

### 3. Socket Timeout (`REDIS_SOCKET_TIMEOUT`)
- **Lower (1-5s)**: Low tolerance for slow operations
- **Higher (10-30s)**: Tolerate occasional slowness, RDB saves

**Recommendation**:
- Session reads/writes only: 5s
- Mixed workloads: 10s
- Bursty workloads: 15-30s

### 4. Max Retries (`REDIS_MAX_RETRIES`)
- **Number of retry attempts** on transient failures (connection reset, timeout, BUSY, etc.)
- Each retry waits: `REDIS_RETRY_BACKOFF_MS` × exponential backoff

**Recommendation**:
- Low criticality: 2-3 retries
- Standard: 5 retries
- High criticality: 10 retries

### 5. Redis Eviction Policy (`--maxmemory-policy`)
- **None (default)**: Error when memory full
- **volatile-lru**: Evict least-recently-used keys with TTL
- **allkeys-lru**: Evict any least-recently-used keys
- **volatile-ttl**: Evict keys with TTL closest to expiry

**Recommendation**:
- Sessions only: `allkeys-lru` (simplest)
- Mixed data: `volatile-lru` (preserve non-session data)
- Test environments: `allkeys-lru`

---

## Performance Tuning Checklist

- [ ] **Monitor Redis memory**: `docker compose exec redis redis-cli INFO memory`
- [ ] **Monitor session churn**: Grep BFF logs for `redis_connected`, `session_expired`
- [ ] **Tune TTL based on activity**: Short TTL if many sessions, long if few
- [ ] **Set maxmemory**: Prevent unbounded growth; use eviction policy
- [ ] **Enable keepalive**: TCP keepalive helps detect dead connections faster
- [ ] **Test timeout values**: Match your network latency profile
- [ ] **Monitor retry rate**: If high, increase TTL or connection timeouts
- [ ] **Use multiple databases**: Only if mixing session + cache layers (advanced)

---

## Monitoring Commands

```bash
docker compose exec redis redis-cli INFO server
docker compose exec redis redis-cli INFO memory
docker compose exec redis redis-cli DBSIZE
docker compose exec redis redis-cli KEYS 'session:*' | wc -l

# View BFF logs for Redis events:
docker compose logs bff | grep redis
```

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Sessions lost frequently | TTL too short | Increase `SESSION_TTL_SECONDS` |
| "redis unavailable" fallback errors | Network latency | Increase `REDIS_SOCKET_CONNECT_TIMEOUT` |
| Slow session reads | Memory exhaustion | Set `--maxmemory` and eviction policy |
| High memory usage | Max sessions too high | Reduce `MAX_SESSIONS` or lower TTL |
| Connection timeouts under load | Insufficient pool/retries | Increase `REDIS_MAX_RETRIES` |
| Stale sessions persisting | TTL not honored | Verify Redis is running, check logs |

---

## Next Steps

1. **Apply staging defaults** if you want more resilience:
   ```bash
   docker compose down
   SESSION_TTL_SECONDS=1800 REDIS_SOCKET_CONNECT_TIMEOUT=10 REDIS_MAX_RETRIES=5 docker compose up -d
   ```

2. **Enable new env vars** in BFF (requires code update, see instructions below)

3. **Monitor and adjust** based on your actual workload

4. **For production**, add Redis persistence:
   ```yaml
   # docker-compose.yml
   command: ["redis-server", "--appendonly", "yes", "--maxmemory", "512mb", "--maxmemory-policy", "allkeys-lru"]
   volumes:
     - redis-data:/data
   volumes:
     redis-data:
   ```
