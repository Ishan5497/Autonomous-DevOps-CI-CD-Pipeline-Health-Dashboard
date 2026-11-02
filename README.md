# Autonomous DevOps & CI/CD Pipeline Health Dashboard

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![WebSocket](https://img.shields.io/badge/WebSocket-Real--Time-blueviolet.svg)](https://websockets.readthedocs.io/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/React-19.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![SQLite](https://img.shields.io/badge/SQLite3-Database-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/pytest-20%20passed-brightgreen.svg?logo=pytest&logoColor=white)](#running-tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end full-stack platform for monitoring CI/CD pipeline reliability, processing simulated & native GitHub/GitLab webhooks, calculating Mean Time To Recovery (MTTR) and health grades, and autonomously scanning commit diffs for hardcoded secrets and critical code bugs with instant WebSocket real-time telemetry streaming.

---

## Architecture Overview

```
                          ┌────────────────────────────────┐
                          │   GitHub / GitLab / Webhook    │
                          │   Simulators (Push, PR, Build) │
                          └───────────────┬────────────────┘
                                          │ JSON Payloads
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Telemetry & Webhook Engine                    │
│                                                                             │
│   ┌────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐   │
│   │  /webhooks Router  │   │  /pipeline Router   │   │ /security Router │   │
│   │  - GitHub Handler  │   │  - MTTR Engine      │   │ - Static Scanner │   │
│   │  - GitLab Handler  │   │  - Runs & Health    │   │ - Secret Redact  │   │
│   │  - Simulation APIs │   │  - AI Actions       │   │ - Vuln Detector  │   │
│   └─────────┬──────────┘   └──────────┬──────────┘   └─────────┬────────┘   │
│             │                         │                        │            │
│             ▼                         ▼                        ▼            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                  SQLAlchemy ORM (SQLite / PostgreSQL)               │   │
│   │   (WebhookEvents, PipelineRuns, PullRequests, SecurityFindings)     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Real-time Telemetry
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Modern Glassmorphic Telemetry UI                         │
│  - Health Grade Badge (A+, A, B, C, F) & Risk Level Meter                   │
│  - MTTR & Build Success Rate Visualizer                                     │
│  - Interactive One-Click Webhook Simulator Console                          │
│  - Live Unified Diff Static Scanner with Automatic Secret Redaction        │
│  - Real-time Pipeline Execution & Security Findings Feed                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard/
├── backend/
│   ├── main.py                     # FastAPI entrypoint, lifespan db init, CORS, routes
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Configuration template
│   ├── Dockerfile                  # Container definition for backend
│   ├── models/
│   │   ├── __init__.py             # Exports ORM models and schemas
│   │   ├── database.py             # SQLite engine, sessionmaker, init_db()
│   │   ├── entities.py             # SQLAlchemy models (PipelineRun, WebhookEvent, etc.)
│   │   └── schemas.py              # Pydantic v2 schemas and validation models
│   ├── routers/
│   │   ├── __init__.py             # Router exports
│   │   ├── webhooks.py             # GitHub, GitLab, and simulation webhook endpoints
│   │   ├── pipeline.py             # Pipeline runs, health metrics, and recommendations
│   │   ├── security.py             # Static analysis diff scanner & findings
│   │   └── dashboard.py            # Summary telemetry and demo data seeder
│   └── services/
│       ├── __init__.py             # Services exports
│       ├── static_analysis.py      # Secret scanner (AWS, Tokens) & bug detector (eval, SQLi)
│       ├── webhook_service.py      # Webhook ingestion and diff analysis pipeline
│       └── pipeline_health.py      # Health score, MTTR, flakiness, & auto-recommendations
├── frontend/
│   ├── index.html                  # Responsive modern telemetry dashboard
│   ├── css/
│   │   └── styles.css              # Cyberpunk dark mode & glassmorphic styling
│   └── js/
│       └── app.js                  # Live UI controller, API caller, and simulator
├── sample_payloads/
│   ├── github_push.json            # Realistic GitHub push webhook event
│   ├── github_pull_request.json     # GitHub PR opened webhook event
│   ├── github_workflow_run.json    # GitHub Actions completed build event
│   ├── gitlab_push.json            # GitLab Push Hook event
│   ├── gitlab_pipeline.json        # GitLab Pipeline Hook event
│   ├── simulated_push_with_secret.json # Push with AWS secret payload
│   └── vulnerable_diff.diff        # Sample diff with secret leak, eval(), and SQLi
├── tests/
│   ├── __init__.py
│   ├── test_webhooks.py            # Integration tests for webhooks & simulations
│   ├── test_static_analysis.py     # Tests for secrets, eval, and SQLi detection
│   └── test_pipeline_health.py     # Tests for MTTR and health metrics
├── docker-compose.yml              # Local container deployment
├── requirements.txt                # Root convenience requirements
├── .gitignore                      # Git ignore rules for Python, Node, and SQLite
└── README.md                       # Documentation & usage guide
```

---

## Features

### 1. Simulated & Native Webhook Ingestion
- **GitHub Receiver (`POST /api/v1/webhooks/github`)**: Handles `X-GitHub-Event` headers for `push`, `pull_request`, and `workflow_run`.
- **GitLab Receiver (`POST /api/v1/webhooks/gitlab`)**: Handles `X-Gitlab-Event` headers for `Push Hook`, `Merge Request Hook`, and `Pipeline Hook`.
- **Simulation Endpoints**:
  - `POST /api/v1/webhooks/simulate/push`: Simulate commits, branch pushes, and optional diff patches.
  - `POST /api/v1/webhooks/simulate/pull-request`: Simulate PR lifecycle events (`opened`, `synchronize`, `closed`).
  - `POST /api/v1/webhooks/simulate/build-status`: Simulate build status changes (`success`, `failed`, `running`, `cancelled`).

### 2. Static Analysis Mock Engine
Scans incoming diffs or source code patches for high-impact security risks and common anti-patterns:
- **Hardcoded Secrets**:
  - AWS Access Key ID (`AKIA...`) and Secret Keys
  - GitHub (`ghp_...`, `github_pat_...`) and GitLab (`glpat-...`) Personal Access Tokens
  - Slack Webhook URLs & Bot Tokens (`xoxb-...`)
  - Private Cryptographic Keys (`-----BEGIN RSA PRIVATE KEY-----`)
  - Generic High-Entropy API tokens (`api_key = "..."`)
  - Database connection strings containing credentials (`postgres://user:pass@host`)
  - JWT Tokens
- **Dangerous Bugs & DevOps Anti-Patterns**:
  - Dangerous code evaluation (`eval()`, `exec()`)
  - String concatenation/interpolation SQL injection patterns
  - Disabled SSL/TLS verification (`verify=False`, `NODE_TLS_REJECT_UNAUTHORIZED=0`)
  - Insecure random generators for sensitive values (`random.random()`)
  - Silent exception swallowing (`except: pass`)
- **Automatic Secret Redaction**: Replaces raw secrets with masked strings (e.g. `AKIA****************LE`) to prevent exposure in logs or UI.

### 3. Real-Time Telemetry & WebSocket Streaming
- **WebSocket Manager (`ws_manager`)**: Centralized broadcast hub tracking connected clients with heartbeat keep-alives and automatic reconnection.
- **Instant Event Broadcasts**:
  - `PIPELINE_UPDATE`: Broadcasts every commit push, pull request, or stage transition with embedded metrics.
  - `BUILD_FAILURE`: Instant notification when a build fails or is blocked by static analysis gates.
  - `SECURITY_ALERT`: Real-time alarm triggered upon detecting hardcoded secrets or critical vulnerabilities in diffs.
- **React WebSocket Hook (`useWebSocket`)**: Auto-reconnecting frontend hook that streams live events directly into the telemetry activity feed and dynamically updates dashboard KPI cards without page reload.

### 4. Autonomous Pipeline Health & MTTR Metrics
- **Health Grade (A+, A, B, C, F)**: Derived from real-time build success rate and vulnerability threshold.
- **Mean Time To Recovery (MTTR)**: Analyzes time elapsed between build failures and subsequent successful recoveries.
- **Autonomous Remediation Recommendations**: Generates contextual remediation actions (e.g., quarantine pipeline on critical leak, retry flaky build stages, or optimize build duration).

---

## Live Webhook Traffic Simulator

To visually verify the real-time activity stream and dynamic metric counters during local development, use the included CLI simulator utility:

```bash
# Run continuous live simulation (dispatches every 3 seconds)
python simulate_live.py

# Or run with custom interval and count
python simulate_live.py --interval 2.0 --count 15

# Target specific event scenario types:
python simulate_live.py --mode failures    # Focus on failing builds and timeouts
python simulate_live.py --mode secrets     # Trigger static analysis secret leaks
python simulate_live.py --mode clean       # Safe commits and successful builds
```

---

## Getting Started Locally

### Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 1. Clone the Repository
```bash
git clone https://github.com/Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard.git
cd Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard
```

### 2. Create and Activate Virtual Environment
```bash
# On Windows:
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Run the Backend
```bash
# Run with uvicorn directly from workspace root:
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Or run via Python:
```bash
python -m backend.main
```

### 5. Open the Interfaces
- **Interactive Telemetry Dashboard**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Docs**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running with Docker & Docker Compose

Deploy the containerized dashboard with a single command:

```bash
docker compose up --build -d
```

The container starts with an embedded SQLite database and exposes port `8000`. Stop the container using:
```bash
docker compose down
```

---

## Running Tests

Run the complete 20-test test suite with `pytest`:

```bash
pytest -v
```

Output:
```text
tests/test_pipeline_health.py::test_pipeline_health_endpoint PASSED
tests/test_pipeline_health.py::test_dashboard_summary_endpoint PASSED
tests/test_pipeline_health.py::test_dashboard_ui_endpoint PASSED
tests/test_pipeline_health.py::test_seed_demo_data PASSED
tests/test_static_analysis.py::test_detects_aws_key PASSED
tests/test_static_analysis.py::test_detects_dangerous_eval PASSED
tests/test_static_analysis.py::test_detects_sql_injection PASSED
tests/test_static_analysis.py::test_safe_diff_passes PASSED
tests/test_webhooks.py::test_root_endpoint PASSED
tests/test_webhooks.py::test_simulate_push_clean PASSED
tests/test_webhooks.py::test_simulate_push_with_secret_fails_pipeline PASSED
tests/test_webhooks.py::test_simulate_pull_request PASSED
tests/test_webhooks.py::test_simulate_build_status PASSED
tests/test_webhooks.py::test_github_webhook_receiver PASSED
tests/test_webhooks.py::test_gitlab_webhook_receiver PASSED
tests/test_websocket.py::test_websocket_status_endpoint PASSED
tests/test_websocket.py::test_websocket_handshake_and_ping PASSED
tests/test_websocket.py::test_websocket_broadcasts_pipeline_update PASSED
tests/test_websocket.py::test_websocket_broadcasts_security_alert_and_build_failure PASSED
tests/test_websocket.py::test_websocket_broadcasts_simulated_build_status PASSED
============================== 20 passed in 1.15s ==============================
```

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root API status and available endpoint index |
| `GET` | `/dashboard` | Interactive frontend telemetry dashboard |
| `WS` | `/api/v1/ws` | Real-time WebSocket telemetry event stream |
| `GET` | `/api/v1/ws/status` | WebSocket broadcaster status and active client count |
| `GET` | `/docs` | OpenAPI Swagger interactive documentation |
| `POST` | `/api/v1/webhooks/github` | Ingest native GitHub webhook events |
| `POST` | `/api/v1/webhooks/gitlab` | Ingest native GitLab webhook events |
| `POST` | `/api/v1/webhooks/simulate/push` | Simulate commit push event (with optional diff) |
| `POST` | `/api/v1/webhooks/simulate/pull-request` | Simulate pull request lifecycle event |
| `POST` | `/api/v1/webhooks/simulate/build-status` | Simulate CI/CD build status update |
| `GET` | `/api/v1/webhooks/events` | List historical webhook payloads |
| `POST` | `/api/v1/security/scan-diff` | Run static analysis scan on arbitrary diff |
| `GET` | `/api/v1/security/findings` | List detected vulnerabilities and leaked secrets |
| `GET` | `/api/v1/security/rules` | List all active security and bug detector rules |
| `GET` | `/api/v1/pipeline/health` | Calculate reliability, MTTR, and health grade |
| `GET` | `/api/v1/pipeline/runs` | List tracked pipeline runs and statuses |
| `GET` | `/api/v1/pipeline/pull-requests` | List tracked pull requests |
| `GET` | `/api/v1/dashboard/summary` | Consolidated metrics for the frontend |
| `POST` | `/api/v1/dashboard/seed-demo-data` | Seed sample runs and findings for quick testing |

---

## Example cURL Requests

### 1. Simulate a Push Event with Hardcoded AWS Secret
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/webhooks/simulate/push" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
    "ref": "refs/heads/feature/s3-upload",
    "commit_sha": "d41d8cd98f00b204",
    "commit_message": "feat: connect s3 client",
    "author": "developer@example.com",
    "diff": "+++ b/config.py\n+AWS_KEY = \"AKIAIOSFODNN7EXAMPLE\""
  }'
```

### 2. Simulate a Pull Request
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/webhooks/simulate/pull-request" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
    "pr_number": 42,
    "title": "feat: autonomous healing engine",
    "action": "opened",
    "author": "ishan-dev",
    "head_branch": "feature/healing",
    "base_branch": "main",
    "head_sha": "8a7b6c5d4e3f"
  }'
```

### 3. Simulate Build Status Update
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/webhooks/simulate/build-status" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
    "pipeline_id": "gh-run-5501",
    "branch": "main",
    "commit_sha": "8a7b6c5d4e3f",
    "status": "success",
    "stage": "deploy",
    "duration_seconds": 38.5
  }'
```

### 4. Scan a Raw Diff via Static Analysis Service
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/security/scan-diff?persist=true" \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "+++ b/handler.py\n+result = eval(user_command)\n+cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")",
    "file_path": "backend/handler.py"
  }'
```

---

## Contributing
1. Fork this repository.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'feat: add amazing feature'`).
4. Push to branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## License
Distributed under the MIT License. See `LICENSE` for details.
