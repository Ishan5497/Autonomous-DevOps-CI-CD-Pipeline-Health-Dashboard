from datetime import datetime, timezone, timedelta
import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import PipelineRun, PullRequest, SecurityFinding, WebhookEvent
from backend.models.schemas import DashboardSummaryResponse
from backend.services.pipeline_health import PipelineHealthService
from backend.services.static_analysis import StaticAnalysisService

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard Summary"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get Consolidated Dashboard Summary",
    description="Returns aggregate health metrics, recent pipeline executions, active PRs, and security findings.",
)
def get_dashboard_summary(db: Session = Depends(get_db)):
    health = PipelineHealthService.calculate_health(db)
    recent_runs = db.query(PipelineRun).order_by(PipelineRun.created_at.desc()).limit(10).all()
    recent_prs = db.query(PullRequest).order_by(PullRequest.updated_at.desc()).limit(10).all()
    recent_findings = db.query(SecurityFinding).order_by(SecurityFinding.created_at.desc()).limit(10).all()

    system_status = {
        "engine": "Autonomous CI/CD Health Monitor",
        "version": "1.0.0",
        "database": "SQLite (models/database.py)",
        "active_rules_count": len(StaticAnalysisService.SECRET_RULES) + len(StaticAnalysisService.BUG_RULES),
        "status": "OPERATIONAL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return DashboardSummaryResponse(
        health=health,
        recent_runs=recent_runs,
        recent_pull_requests=recent_prs,
        recent_findings=recent_findings,
        system_status=system_status,
    )


@router.post(
    "/seed-demo-data",
    summary="Seed Demo Data for Interactive Testing",
    description="Seeds realistic pipeline runs, PRs, and webhook events for immediate visual telemetry.",
)
def seed_demo_data(db: Session = Depends(get_db)):
    repo_name = "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard"

    # Only seed if fewer than 5 pipeline runs exist
    existing_count = db.query(PipelineRun).count()
    if existing_count >= 5:
        return {"status": "ok", "message": f"Database already has {existing_count} runs. Skipping seed."}

    now = datetime.now(timezone.utc)
    stages = ["lint", "test", "build", "deploy", "security_scan"]
    branches = ["main", "feature/autonomous-healing", "fix/docker-cache", "refactor/services"]
    authors = ["ishan-dev", "alex-ops", "github-actions[bot]", "ci-runner"]

    runs = [
        PipelineRun(
            pipeline_id=f"run-seed-{100 + i}",
            repository=repo_name,
            branch=branches[i % len(branches)],
            commit_sha=f"c7f8a{i}9e2b10",
            commit_message=f"ci(pipeline): stage run {i + 1} validation and automated tests",
            author=authors[i % len(authors)],
            status="success" if i != 2 else "failed",
            stage=stages[i % len(stages)],
            duration_seconds=round(random.uniform(22.0, 78.0), 1),
            failure_reason="Integration test timeout on postgres connection" if i == 2 else None,
            created_at=now - timedelta(minutes=(5 - i) * 15),
            completed_at=now - timedelta(minutes=(5 - i) * 15) + timedelta(seconds=45),
        )
        for i in range(5)
    ]
    db.add_all(runs)

    # Add sample PRs
    prs = [
        PullRequest(
            repository=repo_name,
            pr_number=101,
            title="feat: autonomous pipeline anomaly detection & remediation",
            state="open",
            action="opened",
            author="ishan-dev",
            head_branch="feature/autonomous-healing",
            base_branch="main",
            head_sha="a1b2c3d4e5f6",
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(minutes=30),
        ),
        PullRequest(
            repository=repo_name,
            pr_number=102,
            title="fix(ci): optimize docker build cache and runner matrix",
            state="merged",
            action="closed",
            author="alex-ops",
            head_branch="fix/docker-cache",
            base_branch="main",
            head_sha="f6e5d4c3b2a1",
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(hours=5),
        ),
    ]
    db.add_all(prs)

    # Add sample mock security finding
    finding = SecurityFinding(
        repository=repo_name,
        commit_sha="c7f8a29e2b10",
        file_path="backend/services/mock_auth.py",
        line_number=14,
        rule_id="SEC-001",
        rule_name="AWS Access Key ID",
        issue_type="HARDCODED_SECRET",
        severity="CRITICAL",
        description="Hardcoded AWS Access Key ID detected in pull request diff.",
        snippet_redacted='AWS_ACCESS_KEY = "AKIA****************LE"',
        recommendation="Revoke credential and use AWS IAM Secrets Manager.",
        created_at=now - timedelta(hours=1),
    )
    db.add(finding)

    db.commit()
    return {"status": "success", "message": "Demo data seeded successfully"}
