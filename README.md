# AI-WAF — Artificial Intelligence Web Application Firewall

> A multi-engine, production-grade WAF built with FastAPI, Next.js, PostgreSQL, and Redis. Combines rule-based detection, SecBERT transformer inference, autoencoder anomaly detection, and a meta-learner ensemble — all orchestrated by Docker Compose.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Service URLs](#service-urls)
5. [API Endpoints](#api-endpoints)
6. [Local Development](#local-development)
7. [Environment Variables](#environment-variables)
8. [Database Schema](#database-schema)
9. [Testing](#testing)
10. [Architecture Decisions](#architecture-decisions)
11. [License](#license)

---

## Architecture

```
                          ┌──────────────────────────────────────────────┐
                          │              Docker Network: waf-network      │
                          │                                               │
   Browser / Client       │  ┌──────────┐      ┌──────────────────────┐  │
   ─────────────────► :80 │  │          │ /api/ │                      │  │
                          │  │  NGINX   │──────►│  FastAPI Backend     │  │
                          │  │ (Reverse │       │  :8000               │  │
                          │  │  Proxy)  │──────►│                      │  │
                          │  │          │  /    │  ┌──────────────┐    │  │
                          │  │          │       │  │ Rule Engine  │    │  │
                          │  └────┬─────┘       │  │ SecBERT      │    │  │
                          │       │             │  │ Autoencoder  │    │  │
                          │       │ /juice-shop │  │ Meta-Learner │    │  │
                          │       ▼             │  └──────┬───────┘    │  │
                          │  ┌──────────┐       └─────────┼────────────┘  │
                          │  │Juice Shop│                 │               │
                          │  │ :3000    │        ┌────────┴────────┐      │
                          │  └──────────┘        │                 │      │
                          │       │ /dvwa    ┌───▼──────┐   ┌──────▼───┐  │
                          │       ▼          │PostgreSQL│   │  Redis   │  │
                          │  ┌──────────┐    │  :5432   │   │  :6379   │  │
                          │  │  DVWA    │    └──────────┘   └──────────┘  │
                          │  │ :8080    │                                  │
                          │  └──────────┘   ┌────────────────────────┐    │
                          │                 │  Next.js Frontend       │    │
                          │                 │  :3001 → :3000 (intern) │    │
                          │                 └────────────────────────┘    │
                          └──────────────────────────────────────────────┘
```

### Detection Pipeline

```
Inbound Request
      │
      ▼
┌─────────────┐
│ Rule Engine │ ──── fast regex / OWASP ModSecurity rules
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SecBERT   │ ──── transformer fine-tuned on web attack corpus
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ Autoencoder  │ ──── anomaly score on request embedding
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Meta-Learner │ ──── XGBoost ensemble of all engine outputs
└──────┬───────┘
       │
  ┌────┴─────┐
  │          │
ALLOW      BLOCK
  │          │
  ▼          ▼
Target    403 + log
```

---

## Prerequisites

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| Docker | 24.0+ | [Install Docker](https://docs.docker.com/get-docker/) |
| Docker Compose | 2.20+ (plugin) | Bundled with Docker Desktop |
| Node.js | 20 LTS | For local frontend development only |
| Python | 3.12 | For local backend development only |
| Git | 2.40+ | |
| Make (optional) | Any | For Makefile shortcuts |

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/ai-waf.git
cd ai-waf

# 2. Copy and configure environment variables
cp .env.example .env
# Edit .env — at minimum change SECRET_KEY for any non-local environment

# 3. Build and start all services
docker compose up --build

# 4. (Optional) Run in detached mode
docker compose up --build -d

# 5. View logs
docker compose logs -f backend

# 6. Stop everything
docker compose down

# 7. Tear down including volumes (⚠ destroys all data)
docker compose down -v
```

> **First Boot**: PostgreSQL will automatically run `database/init.sql` on first startup and seed the default WAF rules. This takes ~15–30 seconds. The backend will retry until the database is healthy.

---

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Dashboard | http://localhost | Next.js WAF management UI |
| API (Swagger) | http://localhost/api/v1/docs | Interactive OpenAPI docs |
| API (ReDoc) | http://localhost/api/v1/redoc | Alternative API reference |
| Juice Shop | http://localhost/juice-shop/ | OWASP Juice Shop (target) |
| DVWA | http://localhost/dvwa/ | Damn Vulnerable Web App (target) |
| Backend (direct) | http://localhost:8000 | FastAPI direct access (dev only) |
| Frontend (direct) | http://localhost:3001 | Next.js direct access (dev only) |
| Juice Shop (direct) | http://localhost:3000 | Juice Shop direct access |
| DVWA (direct) | http://localhost:8080 | DVWA direct access |
| PostgreSQL | localhost:5432 | Use `psql` or PgAdmin |
| Redis | localhost:6379 | Use `redis-cli` |

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Core WAF

| Method | Path | Description | Request Body |
|--------|------|-------------|--------------|
| `POST` | `/api/v1/inspect` | Inspect and classify a request | `InspectRequest` |
| `GET` | `/api/v1/health` | Service health check | — |
| `GET` | `/api/v1/metrics` | Prometheus-compatible metrics | — |

### Logs & Analytics

| Method | Path | Description | Query Params |
|--------|------|-------------|--------------|
| `GET` | `/api/v1/logs` | Paginated request logs | `page`, `limit`, `decision`, `attack_type`, `from_ts`, `to_ts` |
| `GET` | `/api/v1/logs/{id}` | Single log entry with detection results | — |
| `GET` | `/api/v1/stats` | Aggregated WAF statistics (cached 5s) | `period` (`1h`, `24h`, `7d`, `30d`) |

### Rules

| Method | Path | Description | Request Body |
|--------|------|-------------|--------------|
| `GET` | `/api/v1/rules` | List all WAF rules with hit counts | `category`, `severity` |
| `GET` | `/api/v1/rules/{rule_id}` | Single rule detail | — |
| `PUT` | `/api/v1/rules/{rule_id}` | Update rule enabled/severity | `RuleUpdateRequest` |

### Replay

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/replay` | Queue a request for replay against a target |
| `GET` | `/api/v1/replay/{id}` | Check replay status |

### Example: Inspect a Request

```bash
curl -X POST http://localhost/api/v1/inspect \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "path": "/products?id=1 UNION SELECT username,password FROM users--",
    "headers": {"User-Agent": "Mozilla/5.0"},
    "body": null,
    "ip": "192.168.1.100"
  }'
```

**Response:**

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "decision": "blocked",
  "attack_type": "SQLI",
  "severity": "CRITICAL",
  "confidence": 0.997,
  "triggered_rules": ["SQLI-001"],
  "engines": {
    "rule_engine": "blocked",
    "secbert": "blocked",
    "autoencoder": "blocked",
    "meta_learner": "blocked"
  },
  "latency_ms": 18.4
}
```

---

## Local Development

### Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
.venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Start dependent services only
docker compose up postgres redis -d

# Copy environment
cp ../.env.example ../.env

# Run with hot-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Start development server (with HMR)
npm run dev
# → http://localhost:3001

# Build for production
npm run build
npm start
```

### Running a Specific Service Stack

```bash
# Only infrastructure (DB + cache)
docker compose up postgres redis -d

# Infrastructure + backend only
docker compose up postgres redis backend -d

# Everything except target apps
docker compose up postgres redis backend frontend nginx -d
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment: `development`, `staging`, `production` |
| `DEBUG` | `true` | Enable debug logging and reload |
| `SECRET_KEY` | *(change me)* | HMAC signing key — use `openssl rand -hex 32` |
| `BACKEND_PORT` | `8000` | Port the FastAPI app listens on |
| `BACKEND_WORKERS` | `4` | Number of Uvicorn worker processes |
| `MAX_REQUEST_SIZE_MB` | `10` | Maximum accepted request body size |
| `RATE_LIMIT_PER_MINUTE` | `100` | Per-IP rate limit for `/api/` routes |
| `POSTGRES_HOST` | `postgres` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `wafdb` | Database name |
| `POSTGRES_USER` | `wafuser` | Database user |
| `POSTGRES_PASSWORD` | `wafpassword` | Database password *(change in production)* |
| `DATABASE_URL` | *(constructed)* | Full async SQLAlchemy connection string |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis logical database index |
| `REDIS_URL` | *(constructed)* | Full Redis connection URL |
| `STATS_CACHE_TTL` | `5` | Stats endpoint cache TTL in seconds |
| `JUICE_SHOP_URL` | `http://juice-shop:3000` | Internal Juice Shop base URL |
| `DVWA_URL` | `http://dvwa:80` | Internal DVWA base URL |
| `NEXT_PUBLIC_API_URL` | `http://localhost/api/v1` | Public API URL seen by the browser |

---

## Database Schema

```
raw_request_logs          processed_request_logs
─────────────────         ──────────────────────────
id (PK, UUID)             id (PK, UUID)
timestamp                 raw_log_id (FK → raw_request_logs)
ip_address (INET)         normalized_path
method                    normalized_body
path                      fingerprint (SHA-256, 64 chars)
original_headers (JSONB)  decision (decision_enum)
original_body             attack_type (attack_category_enum)
user_agent                rule_version
request_size              response_status
                          latency_ms
                          created_at

detection_results          request_replays
─────────────────          ───────────────────────────
id (PK, UUID)              id (PK, UUID)
request_id (FK → raw_…)   request_log_id (FK → raw_…)
engine (engine_enum)       payload
rule_id                    headers (JSONB)
severity (severity_enum)   method
confidence [0.0–1.0]       path
decision (decision_enum)   timestamp
metadata (JSONB)           status (replay_status_enum)
created_at                 replayed_at

rule_stats
──────────────────────
id (PK, UUID)
rule_id (UNIQUE)
rule_name
category (attack_category_enum)
severity (severity_enum)
hit_count (BIGINT)
last_triggered
created_at
updated_at
```

### ENUMs

| Type | Values |
|------|--------|
| `decision_enum` | `allowed`, `blocked` |
| `severity_enum` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `engine_enum` | `rule_engine`, `secbert`, `autoencoder`, `meta_learner` |
| `replay_status_enum` | `pending`, `replayed`, `failed` |
| `attack_category_enum` | `SQLI`, `XSS`, `PATH_TRAVERSAL`, `COMMAND_INJECTION` |

---

## Testing and Validation

Testing and validation are executed locally on development machines. Continuous Integration (CI) systems like GitHub Actions, Jenkins, or GitLab CI are deliberately excluded to minimize maintenance overhead and keep the project's focus squarely on security and ML engineering.

### Local Unit & Integration Tests

All backend unit and integration tests are executed via `pytest` inside the backend container to ensure direct access to containerized dependencies (Redis, PostgreSQL).

```bash
# Run pytest with term-missing coverage report inside the backend container
docker compose exec backend pytest tests/ --cov=app --cov-report=term-missing
```

### Manual Release Verification

To run a full manual verification suite of the application before release:

```bash
# Run the automated release check script
python scripts/release_check.py
```

This script automates:
1. **Connectivity Checks**: Validating that WAF API, Juice Shop, DVWA, and Dashboard are reachable and return healthy HTTP statuses.
2. **Backend Tests & Coverage**: Running the Pytest test suite inside the container and validating that code coverage meets or exceeds **80%**.
3. **Traffic Simulation**: Blasting benign and malicious traffic to verify that rules match and attacks are blocked properly.

### Traffic Simulator

To simulate a mix of randomized benign and malicious traffic:

```bash
# Run the traffic simulator locally
python scripts/traffic_simulator.py
```

### Manual Attack Simulation (End-to-End)

You can manually inspect WAF responses using `curl`:

```bash
# SQL Injection
curl "http://localhost/api/v1/inspect" \
  -X POST -H "Content-Type: application/json" \
  -d '{"method":"GET","path":"/login?user=admin'\''--","ip":"10.0.0.1"}'

# XSS
curl "http://localhost/api/v1/inspect" \
  -X POST -H "Content-Type: application/json" \
  -d '{"method":"POST","path":"/comment","body":"<script>alert(1)</script>","ip":"10.0.0.2"}'

# Path Traversal
curl "http://localhost/api/v1/inspect" \
  -X POST -H "Content-Type: application/json" \
  -d '{"method":"GET","path":"/../../../etc/passwd","ip":"10.0.0.3"}'

# Command Injection
curl "http://localhost/api/v1/inspect" \
  -X POST -H "Content-Type: application/json" \
  -d '{"method":"POST","path":"/ping","body":"host=localhost;cat /etc/shadow","ip":"10.0.0.4"}'
```

### Load Testing

Smoke and stress load testing are executed locally using `k6`:

```bash
k6 run tests/load/smoke.js
k6 run tests/load/stress.js --vus 100 --duration 60s
```

### Health Check

```bash
curl -sf http://localhost/api/v1/health | python -m json.tool
```

---

## Architecture Decisions

This project implements **6 Level 2 extensibility choices** that allow each detection layer to be swapped, scaled, or enhanced independently.

### 1. Multi-Engine Detection Pipeline (Strategy Pattern)

Each detection engine (`rule_engine`, `secbert`, `autoencoder`, `meta_learner`) implements a common `DetectionEngine` abstract base class. Engines are loaded via a registry and can be enabled/disabled at runtime without restarting the service. This means a new engine (e.g., a graph neural network) can be integrated by implementing the interface and registering it — zero changes to the pipeline orchestrator.

### 2. Async-First Backend (FastAPI + asyncpg)

All I/O — PostgreSQL queries via `asyncpg`, Redis operations via `aioredis`, and outbound HTTP for replays via `httpx` — is fully asynchronous. A single Uvicorn worker can handle hundreds of concurrent inspection requests without thread-pool starvation, making the system linearly scalable via `BACKEND_WORKERS`.

### 3. Immutable Request Log + Derived Tables

`raw_request_logs` is append-only and never modified. All WAF analysis is written to `processed_request_logs` and `detection_results` as derived data. This separation means: (a) the raw capture survives engine changes/upgrades, (b) you can re-run any engine on historical data, and (c) the replay system has a stable source of truth to replay from.

### 4. Redis-Backed Stats Cache (TTL = 5s)

The `/api/v1/stats` endpoint is queried frequently by the dashboard. Rather than hitting PostgreSQL on every poll, results are cached in Redis with a 5-second TTL (configurable via `STATS_CACHE_TTL`). Under high dashboard load (many browser tabs), the database query rate is bounded to 1 query / 5 seconds regardless of dashboard users.

### 5. NGINX as the Single Ingress (Upstream Abstraction)

NGINX sits in front of every service and is the only component that binds to host port 80. Upstreams are named (`backend`, `frontend`, `juice_shop`, `dvwa`) — allowing any upstream's internal address to change (e.g., when horizontally scaling the backend to multiple containers behind a Docker internal load balancer) without touching application code.

### 6. Target App Isolation via Docker Network

Juice Shop and DVWA run inside `waf-network` but are also accessible directly on their host ports (`:3000`, `:8080`). This dual-access design means: (a) traffic routed through NGINX at `/juice-shop/` and `/dvwa/` is subject to WAF inspection and logging, and (b) direct-port access is available for baseline comparisons and pen-testing tooling that doesn't support path prefixes, all without modifying the target applications.

---

## Project Structure

```
ai-waf/
├── .env.example            # Environment variable template
├── docker-compose.yml      # Full service orchestration
├── README.md               # This file
│
├── backend/                # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── api/            # Route handlers
│       ├── engines/        # Detection engine implementations
│       ├── models/         # SQLAlchemy ORM models
│       └── services/       # Business logic
│
├── frontend/               # Next.js 14 dashboard
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── app/            # App Router pages
│       └── components/     # UI components
│
├── nginx/
│   ├── nginx.conf          # Main NGINX config
│   └── default.conf        # Virtual host / location blocks
│
├── database/
│   └── init.sql            # PostgreSQL schema + seed data
│
└── logs/                   # Shared log volume (nginx + backend)
    └── .gitkeep
```

## Project Roadmap

### Level 1: Core Proxy & Rules
* **FastAPI**: Core async proxy gateway and WAF API.
* **NGINX**: Reverse proxy acting as the single ingress point.
* **PostgreSQL**: Hardened backend database for raw/processed logs.
* **Redis**: Stats cache and atomic metrics store.
* **Docker Compose**: Primary local and development deployment orchestrator.
* **OWASP Juice Shop & DVWA**: Isolated target web applications for testing.
* **Dashboard**: Next.js 14-based real-time security dashboard.
* **Traffic Simulator**: Multi-threaded attack and benign traffic simulation tool.

### Level 2: Deep Learning Detection
* **SecBERT**: Transformer model fine-tuned on payload corpus for semantic classification.
* **ONNX Runtime**: High-performance model inference integration.
* **MLflow**: ML lifecycle management and model registry.
* **Dataset Pipeline**: Automated pipeline for preparing training datasets from replays.
* **Explainability Layer**: Integrated feature importance and explanation visualization.

### Level 3: Advanced Ensemble & Behavioral Analysis
* **Autoencoder**: Anomaly detection engine for zero-day attack identification.
* **Session Engine**: Session-level behavioral modeling.
* **Meta Learner**: XGBoost ensemble classifier to combine rule engine, SecBERT, and anomaly scores.
* **Redis Streams**: High-throughput message bus for logs and stream processing.
* **Drift Detection**: Automatic alerts for model feature/concept drift.
* **Feedback Loop**: Active learning workflow for continuous model retraining.
* **Kubernetes**: Scalable, containerized production orchestration.

---

## License

MIT License

Copyright (c) 2024 AI-WAF Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
