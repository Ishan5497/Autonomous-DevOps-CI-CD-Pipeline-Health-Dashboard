from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import PipelineRun, PullRequest
from backend.models.schemas import (
    PipelineRunResponse,
    PullRequestResponse,
    PipelineHealthMetrics,
    AutonomousRecommendation,
    SimulatedBuildStatusPayload,
)
from backend.services.pipeline_health import PipelineHealthService
from backend.services.webhook_service import WebhookService

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline & Health"])


@router.get(
    "/health",
    response_model=PipelineHealthMetrics,
    summary="Get Pipeline Health & Reliability Metrics",
    description="Computes MTTR, success/failure rate, health grade (A+, A, B, C, F), and autonomous recommendations.",
)
def get_pipeline_health(db: Session = Depends(get_db)):
    return PipelineHealthService.calculate_health(db)


@router.get(
    "/recommendations",
    response_model=List[AutonomousRecommendation],
    summary="Get Autonomous Actionable Recommendations",
)
def get_recommendations(db: Session = Depends(get_db)):
    health = PipelineHealthService.calculate_health(db)
    return health.recommendations


@router.get(
    "/runs",
    response_model=List[PipelineRunResponse],
    summary="List Pipeline Runs",
)
def list_pipeline_runs(
    status: Optional[str] = None,
    branch: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(PipelineRun)
    if status:
        query = query.filter(PipelineRun.status == status.lower())
    if branch:
        query = query.filter(PipelineRun.branch == branch)
    return query.order_by(PipelineRun.created_at.desc()).limit(limit).all()


@router.get(
    "/runs/{pipeline_id}",
    response_model=PipelineRunResponse,
    summary="Get Pipeline Run Detail",
)
def get_pipeline_run(pipeline_id: str, db: Session = Depends(get_db)):
    run = db.query(PipelineRun).filter(PipelineRun.pipeline_id == pipeline_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")
    return run


@router.post(
    "/runs",
    summary="Trigger / Register Pipeline Run",
)
def create_pipeline_run(payload: SimulatedBuildStatusPayload, db: Session = Depends(get_db)):
    return WebhookService.process_simulated_build_status(db=db, payload=payload)


@router.get(
    "/pull-requests",
    response_model=List[PullRequestResponse],
    summary="List Tracked Pull Requests",
)
def list_pull_requests(
    state: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(PullRequest)
    if state:
        query = query.filter(PullRequest.state == state.lower())
    return query.order_by(PullRequest.updated_at.desc()).limit(limit).all()
