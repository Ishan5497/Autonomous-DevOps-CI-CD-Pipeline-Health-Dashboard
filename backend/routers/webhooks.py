from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import WebhookEvent
from backend.models.schemas import (
    SimulatedPushPayload,
    SimulatedPullRequestPayload,
    SimulatedBuildStatusPayload,
    WebhookEventResponse,
)
from backend.services.webhook_service import WebhookService

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@router.post("/github", summary="GitHub Webhook Receiver Endpoint")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
    db: Session = Depends(get_db),
):
    """
    Accepts native GitHub webhook JSON payloads for push events,
    pull requests, workflow runs, and check runs.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = x_github_event or payload.get("event") or "push"
    result = WebhookService.handle_github_webhook(
        db=db,
        event_type=event_type,
        payload=payload,
        delivery_id=x_github_delivery,
    )
    return result


@router.post("/gitlab", summary="GitLab Webhook Receiver Endpoint")
async def gitlab_webhook(
    request: Request,
    x_gitlab_event: Optional[str] = Header(None, alias="X-Gitlab-Event"),
    db: Session = Depends(get_db),
):
    """
    Accepts native GitLab webhook JSON payloads for Push Hook,
    Merge Request Hook, and Pipeline Hook events.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = x_gitlab_event or payload.get("object_kind") or "Push Hook"
    result = WebhookService.handle_gitlab_webhook(
        db=db,
        event_type=event_type,
        payload=payload,
    )
    return result


@router.post(
    "/simulate/push",
    summary="Simulate Push Event",
    description="Simulate a Git push event with commit details and optional diff for static analysis.",
)
def simulate_push(payload: SimulatedPushPayload, db: Session = Depends(get_db)):
    return WebhookService.process_simulated_push(db=db, payload=payload)


@router.post(
    "/simulate/pull-request",
    summary="Simulate Pull Request Event",
    description="Simulate a pull request lifecycle event (opened, synchronize, closed).",
)
def simulate_pull_request(payload: SimulatedPullRequestPayload, db: Session = Depends(get_db)):
    return WebhookService.process_simulated_pull_request(db=db, payload=payload)


@router.post(
    "/simulate/build-status",
    summary="Simulate CI/CD Build Status Update",
    description="Simulate a CI/CD build status transition (success, failed, running, cancelled).",
)
def simulate_build_status(payload: SimulatedBuildStatusPayload, db: Session = Depends(get_db)):
    return WebhookService.process_simulated_build_status(db=db, payload=payload)


@router.get(
    "/events",
    response_model=List[WebhookEventResponse],
    summary="List Received Webhook Events",
)
def list_events(
    source: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(WebhookEvent)
    if source:
        query = query.filter(WebhookEvent.source == source)
    return query.order_by(WebhookEvent.created_at.desc()).limit(limit).all()
