#!/usr/bin/env python3
"""
Autonomous DevOps & CI/CD Telemetry Live Simulator
---------------------------------------------------
Fires mock webhook payloads (pushes, pull requests, build statuses, security leaks)
into the FastAPI backend every few seconds to visually verify the live activity
stream and dynamic metric counters over WebSocket.

Usage:
    python simulate_live.py
    python simulate_live.py --interval 2.5 --count 10
    python simulate_live.py --mode failures
    python simulate_live.py --mode secrets
"""

import sys
import time
import random
import argparse
from datetime import datetime
from typing import Dict, Any, List

try:
    import requests
except ImportError:
    print("Error: 'requests' package not found. Install via 'pip install requests'")
    sys.exit(1)

# Color terminal helpers
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"


def timestamp_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def generate_sha(length: int = 8) -> str:
    return "".join(random.choices("0123456789abcdef", k=length))


# ==========================================
# Payload Generators
# ==========================================

REPO_NAME = "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard"
AUTHORS = ["ishan-dev", "alex-ops", "sarah-qa", "ci-runner", "dependabot[bot]"]
BRANCHES = ["main", "feature/auth-remediation", "fix/docker-cache", "hotfix/api-gateway", "feature/live-ws"]

SAFE_MESSAGES = [
    "feat(telemetry): enable streaming event logs",
    "perf(db): optimize sqlite connection pooling",
    "refactor(services): streamline pipeline health aggregator",
    "docs(readme): add real-time websocket architecture guide",
    "ci(actions): cache python wheels in matrix runner",
    "test(e2e): verify live metric counters incrementation",
]

SECRET_DIFFS = [
    (
        "AWS Secret Access Key leak",
        "diff --git a/backend/config/aws.py b/backend/config/aws.py\n"
        "--- a/backend/config/aws.py\n"
        "+++ b/backend/config/aws.py\n"
        "@@ -5,2 +5,3 @@\n"
        "+# Hardcoded credentials for quick debugging\n"
        "+AWS_ACCESS_KEY_ID = 'AKIA" + "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=16)) + "'\n"
        "+AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'\n",
    ),
    (
        "Slack Bot Webhook URL leak",
        "diff --git a/backend/notifications/slack.py b/backend/notifications/slack.py\n"
        "--- a/backend/notifications/slack.py\n"
        "+++ b/backend/notifications/slack.py\n"
        "@@ -10,1 +10,2 @@\n"
        "+SLACK_WEBHOOK = 'https://hooks.slack.com/services/YOUR/DUMMY/WEBHOOK'\n",
    ),
    (
        "Dangerous eval() & SQL injection",
        "diff --git a/backend/routers/query.py b/backend/routers/query.py\n"
        "--- a/backend/routers/query.py\n"
        "+++ b/backend/routers/query.py\n"
        "@@ -12,2 +12,4 @@\n"
        "+def run_custom_filter(user_input):\n"
        "+    result = eval(user_input)\n"
        "+    db.execute(f'SELECT * FROM audit WHERE id = {user_input}')\n",
    ),
]

FAILURE_REASONS = [
    "TestMatrixFailure: Unit test 'test_token_expiry' timed out after 30s",
    "DockerBuildError: Exit code 137 (OOM killed during layer compilation)",
    "DatabaseConnectionError: Connection to postgres://pg:5432 refused",
    "LintCheckError: 12 formatting violations detected by ruff/flake8",
    "E2ESuiteError: Playwright chromium browser crash in headless runner",
]


def make_safe_push() -> Dict[str, Any]:
    sha = generate_sha(10)
    branch = random.choice(BRANCHES)
    return {
        "url_suffix": "/api/v1/webhooks/simulate/push",
        "name": "Safe Git Push",
        "color": GREEN,
        "payload": {
            "repository": REPO_NAME,
            "ref": f"refs/heads/{branch}",
            "commit_sha": sha,
            "commit_message": random.choice(SAFE_MESSAGES),
            "author": random.choice(AUTHORS),
            "diff": "--- a/metrics.py\n+++ b/metrics.py\n@@ -1,1 +1,2 @@\n+# healthy refactor\n",
        },
    }


def make_secret_leak_push() -> Dict[str, Any]:
    sha = generate_sha(10)
    title, diff_text = random.choice(SECRET_DIFFS)
    return {
        "url_suffix": "/api/v1/webhooks/simulate/push",
        "name": f"Security Alert Push ({title})",
        "color": RED,
        "payload": {
            "repository": REPO_NAME,
            "ref": "refs/heads/feature/critical-fix",
            "commit_sha": sha,
            "commit_message": f"fix(security): urgent patch [{title[:20]}]",
            "author": random.choice(AUTHORS),
            "diff": diff_text,
        },
    }


def make_pull_request() -> Dict[str, Any]:
    pr_num = random.randint(105, 999)
    head_sha = generate_sha(10)
    branch = f"feature/auto-heal-{pr_num}"
    action = random.choice(["opened", "synchronize", "reopened"])
    return {
        "url_suffix": "/api/v1/webhooks/simulate/pull-request",
        "name": f"Pull Request #{pr_num} ({action})",
        "color": MAGENTA,
        "payload": {
            "repository": REPO_NAME,
            "pr_number": pr_num,
            "title": f"feat: autonomous self-healing controller for node-cluster-{random.randint(1, 9)}",
            "action": action,
            "author": random.choice(AUTHORS),
            "head_branch": branch,
            "base_branch": "main",
            "head_sha": head_sha,
            "diff": None,
        },
    }


def make_passing_build() -> Dict[str, Any]:
    pipe_id = f"pipe-ci-{random.randint(2000, 9999)}"
    stage = random.choice(["lint", "test", "build", "deploy"])
    duration = round(random.uniform(18.5, 62.0), 1)
    return {
        "url_suffix": "/api/v1/webhooks/simulate/build-status",
        "name": f"CI Build SUCCESS ({stage})",
        "color": CYAN,
        "payload": {
            "repository": REPO_NAME,
            "pipeline_id": pipe_id,
            "branch": "main",
            "commit_sha": generate_sha(8),
            "commit_message": "ci(matrix): cross-platform integration tests passed",
            "author": "github-actions[bot]",
            "status": "success",
            "stage": stage,
            "duration_seconds": duration,
            "failure_reason": None,
        },
    }


def make_failing_build() -> Dict[str, Any]:
    pipe_id = f"pipe-fail-{random.randint(1000, 9999)}"
    stage = random.choice(["test", "lint", "build"])
    reason = random.choice(FAILURE_REASONS)
    return {
        "url_suffix": "/api/v1/webhooks/simulate/build-status",
        "name": f"Build FAILURE ({stage})",
        "color": YELLOW,
        "payload": {
            "repository": REPO_NAME,
            "pipeline_id": pipe_id,
            "branch": random.choice(BRANCHES),
            "commit_sha": generate_sha(8),
            "commit_message": "test: regression test suite",
            "author": "ci-runner",
            "status": "failed",
            "stage": stage,
            "duration_seconds": round(random.uniform(8.0, 24.0), 1),
            "failure_reason": reason,
        },
    }


def make_github_native_push() -> Dict[str, Any]:
    sha = generate_sha(12)
    return {
        "url_suffix": "/api/v1/webhooks/github",
        "name": "Native GitHub Push Hook",
        "color": BLUE,
        "headers": {"X-GitHub-Event": "push", "X-GitHub-Delivery": f"guid-{generate_sha(8)}"},
        "payload": {
            "repository": {"full_name": REPO_NAME, "name": "Autonomous-DevOps"},
            "ref": "refs/heads/main",
            "sender": {"login": "octocat"},
            "head_commit": {
                "id": sha,
                "message": "chore(deps): bump dependencies and apply security hotfixes",
                "author": {"name": "octocat"},
            },
            "commits": [],
        },
    }


# ==========================================
# Main Runner Loop
# ==========================================

ALL_GENERATORS = [
    make_safe_push,
    make_passing_build,
    make_pull_request,
    make_failing_build,
    make_secret_leak_push,
    make_safe_push,
    make_passing_build,
    make_github_native_push,
]


def run_simulator(base_url: str, interval: float, count: int, mode: str):
    base_url = base_url.rstrip("/")
    print(f"\n{BOLD}{CYAN}================================================================={RESET}")
    print(f"{BOLD}{CYAN}   AUTONOMOUS DEVOPS & CI/CD REAL-TIME WEBHOOK SIMULATOR         {RESET}")
    print(f"{BOLD}{CYAN}================================================================={RESET}")
    print(f"Target Server : {BOLD}{base_url}{RESET}")
    print(f"Interval      : {BOLD}{interval}s{RESET}")
    print(f"Total Count   : {BOLD}{'Infinite (Ctrl+C to stop)' if count == 0 else count}{RESET}")
    print(f"Mode          : {BOLD}{mode}{RESET}")
    print(f"WebSocket URL : {BOLD}{base_url.replace('http', 'ws')}/api/v1/ws{RESET}\n")

    # Pre-flight check
    try:
        ping = requests.get(f"{base_url}/api/v1/ws/status", timeout=3)
        if ping.status_code == 200:
            status_data = ping.json()
            active = status_data.get("active_clients", 0)
            print(f"{GREEN}[OK] Telemetry server online! Connected WebSocket clients: {active}{RESET}\n")
        else:
            print(f"{YELLOW}[WARN] Server responded with HTTP {ping.status_code}{RESET}\n")
    except Exception as e:
        print(f"{RED}[FAIL] Could not reach {base_url}: {e}{RESET}")
        print(f"{YELLOW}Hint: Start the FastAPI backend first via:{RESET}")
        print(f"  python -m uvicorn backend.main:app --reload --port 8000\n")
        sys.exit(1)

    print(f"{DIM}Timestamp  Status  Event Type                       Detail{RESET}")
    print(f"{DIM}---------  ------  -------------------------------  -----------------------------------{RESET}")

    sent_count = 0
    success_count = 0
    error_count = 0
    idx = 0

    try:
        while True:
            sent_count += 1

            # Select payload generator based on mode
            if mode == "failures":
                gen = make_failing_build
            elif mode == "secrets":
                gen = make_secret_leak_push
            elif mode == "clean":
                gen = random.choice([make_safe_push, make_passing_build])
            elif mode == "cycle":
                gen = ALL_GENERATORS[idx % len(ALL_GENERATORS)]
                idx += 1
            else:  # random
                gen = random.choice(ALL_GENERATORS)

            item = gen()
            target_url = f"{base_url}{item['url_suffix']}"
            headers = item.get("headers", {})

            t_start = time.time()
            try:
                res = requests.post(target_url, json=item["payload"], headers=headers, timeout=5)
                duration_ms = int((time.time() - t_start) * 1000)

                if res.status_code == 200:
                    success_count += 1
                    status_badge = f"{GREEN}{res.status_code} OK{RESET}"
                else:
                    error_count += 1
                    status_badge = f"{RED}{res.status_code} ERR{RESET}"

                name_styled = f"{item['color']}{item['name']:<31}{RESET}"
                detail_summary = (
                    item["payload"].get("commit_message")
                    or item["payload"].get("title")
                    or item["payload"].get("failure_reason")
                    or str(res.json().get("status", ""))
                )
                if len(detail_summary) > 42:
                    detail_summary = detail_summary[:39] + "..."

                print(f"[{timestamp_str()}] {status_badge}  {name_styled}  {DIM}{detail_summary} ({duration_ms}ms){RESET}")

            except Exception as exc:
                error_count += 1
                print(f"[{timestamp_str()}] {RED}ERROR   {RESET} {item['name']:<31}  {RED}{str(exc)[:40]}{RESET}")

            if count > 0 and sent_count >= count:
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Simulation interrupted by user.{RESET}")

    print(f"\n{BOLD}Simulation Summary:{RESET}")
    print(f"  Total Dispatched : {sent_count}")
    print(f"  Success (HTTP 200): {GREEN}{success_count}{RESET}")
    print(f"  Errors           : {RED if error_count > 0 else GREEN}{error_count}{RESET}")
    print(f"  All dispatched events broadcasted to connected WebSocket clients in real-time!\n")


def main():
    parser = argparse.ArgumentParser(
        description="Fires realistic mock webhook payloads into Autonomous DevOps backend for live stream verification."
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="FastAPI backend base URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="Seconds between each simulated payload (default: 3.0)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of payloads to dispatch (0 for continuous loop until Ctrl+C, default: 0)",
    )
    parser.add_argument(
        "--mode",
        choices=["random", "cycle", "failures", "secrets", "clean"],
        default="cycle",
        help="Simulation scenario mode: 'cycle', 'random', 'failures', 'secrets', or 'clean' (default: cycle)",
    )

    args = parser.parse_args()
    run_simulator(
        base_url=args.url,
        interval=args.interval,
        count=args.count,
        mode=args.mode,
    )


if __name__ == "__main__":
    main()

