import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.models.entities import WebhookEvent, PipelineRun, PullRequest, SecurityFinding
from backend.models.schemas import (
    SimulatedPushPayload,
    SimulatedPullRequestPayload,
    SimulatedBuildStatusPayload,
    DiffScanResponse,
)
from backend.services.static_analysis import StaticAnalysisService
from backend.services.websocket_manager import ws_manager
from backend.services.pipeline_health import PipelineHealthService
from backend.models.database import SessionLocal


def _get_current_metrics_dict() -> Optional[Dict[str, Any]]:
    """Safely compute current health metrics for WebSocket broadcast payloads."""
    try:
        with SessionLocal() as db:
            metrics = PipelineHealthService.calculate_health(db)
            return metrics.model_dump()
    except Exception:
        return None


class WebhookService:
    """
    Service responsible for parsing and routing GitHub and GitLab webhook events,
    recording pipeline runs, pull requests, and triggering static analysis.
    All mutations broadcast real-time updates via the WebSocket manager.
    """

    @classmethod
    def record_raw_event(
        cls,
        db: Session,
        source: str,
        event_type: str,
        payload: Dict[str, Any],
        delivery_id: Optional[str] = None,
        repository: Optional[str] = None,
        sender: Optional[str] = None,
        status: str = "processed",
    ) -> WebhookEvent:
        event = WebhookEvent(
            source=source,
            event_type=event_type,
            delivery_id=delivery_id,
            repository=repository,
            sender=sender,
            payload=json.dumps(payload),
            status=status,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @classmethod
    def handle_github_webhook(
        cls,
        db: Session,
        event_type: str,
        payload: Dict[str, Any],
        delivery_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Processes native GitHub webhook payloads."""
        repo_data = payload.get("repository", {})
        repo_name = repo_data.get("full_name") or repo_data.get("name") or "unknown/repo"
        sender = payload.get("sender", {}).get("login", "unknown")

        # Save raw event
        cls.record_raw_event(
            db=db,
            source="github",
            event_type=event_type,
            payload=payload,
            delivery_id=delivery_id,
            repository=repo_name,
            sender=sender,
        )

        scan_result: Optional[DiffScanResponse] = None

        if event_type == "push":
            commits = payload.get("commits", [])
            ref = payload.get("ref", "refs/heads/main")
            branch = ref.replace("refs/heads/", "")
            head_commit = payload.get("head_commit", {})
            commit_sha = head_commit.get("id") or (commits[-1].get("id") if commits else "0000000")
            commit_msg = head_commit.get("message") or (commits[-1].get("message") if commits else "Push event")
            author = head_commit.get("author", {}).get("name") or sender

            # Scan any diff or commit patch embedded in payload
            diff_text = payload.get("diff") or head_commit.get("diff")
            if diff_text:
                scan_result = cls._run_and_save_static_analysis(
                    db=db,
                    diff_text=diff_text,
                    repo_name=repo_name,
                    commit_sha=commit_sha,
                )

            # Auto-register an initial build/pipeline run for this push
            run = PipelineRun(
                pipeline_id=f"gh-push-{commit_sha[:7]}",
                repository=repo_name,
                branch=branch,
                commit_sha=commit_sha,
                commit_message=commit_msg,
                author=author,
                status="running",
                stage="build",
                duration_seconds=0.0,
                started_at=datetime.now(timezone.utc),
            )
            db.add(run)
            db.commit()

            # Broadcast via WebSocket
            metrics = _get_current_metrics_dict()
            run_broadcast = {
                "pipeline_id": run.pipeline_id,
                "repository": repo_name,
                "branch": branch,
                "commit_sha": commit_sha,
                "commit_message": commit_msg,
                "author": author,
                "status": "running",
                "stage": "build",
                "duration_seconds": 0.0,
            }
            ws_manager.broadcast_pipeline_update(run_broadcast, metrics)

            if scan_result and not scan_result.is_safe:
                ws_manager.broadcast_security_alert(
                    findings=[f.model_dump() for f in scan_result.findings],
                    repository=repo_name,
                    commit_sha=commit_sha,
                    metrics=metrics,
                )

            return {
                "status": "success",
                "message": f"Push event processed for branch {branch}",
                "commit_sha": commit_sha,
                "static_analysis": scan_result.model_dump() if scan_result else None,
            }

        elif event_type == "pull_request":
            pr_data = payload.get("pull_request", {})
            action = payload.get("action", "opened")
            pr_number = pr_data.get("number") or payload.get("number", 0)
            title = pr_data.get("title", "Untitled PR")
            author = pr_data.get("user", {}).get("login", sender)
            head_branch = pr_data.get("head", {}).get("ref", "feature")
            base_branch = pr_data.get("base", {}).get("ref", "main")
            head_sha = pr_data.get("head", {}).get("sha", "")

            # Check if PR already exists in DB
            pr = db.query(PullRequest).filter_by(repository=repo_name, pr_number=pr_number).first()
            if not pr:
                pr = PullRequest(
                    repository=repo_name,
                    pr_number=pr_number,
                    title=title,
                    state="open" if action in ("opened", "reopened", "synchronize") else action,
                    action=action,
                    author=author,
                    head_branch=head_branch,
                    base_branch=base_branch,
                    head_sha=head_sha,
                )
                db.add(pr)
            else:
                pr.title = title
                pr.action = action
                pr.state = "open" if action in ("opened", "reopened", "synchronize") else action
                pr.head_sha = head_sha
                pr.updated_at = datetime.now(timezone.utc)

            # Scan diff if supplied
            diff_text = payload.get("diff") or pr_data.get("diff")
            if diff_text:
                scan_result = cls._run_and_save_static_analysis(
                    db=db,
                    diff_text=diff_text,
                    repo_name=repo_name,
                    commit_sha=head_sha,
                )

            db.commit()

            return {
                "status": "success",
                "message": f"Pull request #{pr_number} ({action}) processed",
                "pr_number": pr_number,
                "static_analysis": scan_result.model_dump() if scan_result else None,
            }

        elif event_type in ("workflow_run", "check_run"):
            # GitHub Actions build run
            run_data = payload.get("workflow_run") or payload.get("check_run", {})
            run_id = str(run_data.get("id", "gh-run"))
            conclusion = run_data.get("conclusion") or run_data.get("status", "running")
            branch = run_data.get("head_branch", "main")
            commit_sha = run_data.get("head_sha", "")

            status_map = {
                "success": "success",
                "failure": "failed",
                "timed_out": "failed",
                "cancelled": "cancelled",
                "in_progress": "running",
                "queued": "running",
            }
            normalized_status = status_map.get(conclusion, "running")

            run = db.query(PipelineRun).filter_by(pipeline_id=run_id).first()
            if not run:
                run = PipelineRun(
                    pipeline_id=run_id,
                    repository=repo_name,
                    branch=branch,
                    commit_sha=commit_sha,
                    commit_message=run_data.get("display_title", "GitHub Action run"),
                    author=sender,
                    status=normalized_status,
                    stage="workflow",
                    duration_seconds=run_data.get("run_duration_ms", 30000) / 1000.0,
                )
                db.add(run)
            else:
                run.status = normalized_status
                if normalized_status in ("success", "failed", "cancelled"):
                    run.completed_at = datetime.now(timezone.utc)

            db.commit()

            # Broadcast via WebSocket
            metrics = _get_current_metrics_dict()
            run_broadcast = {
                "pipeline_id": run_id,
                "repository": repo_name,
                "branch": branch,
                "commit_sha": commit_sha,
                "commit_message": run_data.get("display_title", "GitHub Action run"),
                "author": sender,
                "status": normalized_status,
                "stage": "workflow",
                "duration_seconds": run_data.get("run_duration_ms", 30000) / 1000.0,
            }
            if normalized_status == "failed":
                ws_manager.broadcast_build_failure(run_broadcast, metrics=metrics)
            else:
                ws_manager.broadcast_pipeline_update(run_broadcast, metrics)

            return {"status": "success", "pipeline_id": run_id, "build_status": normalized_status}

        return {"status": "acknowledged", "event_type": event_type}

    @classmethod
    def handle_gitlab_webhook(
        cls,
        db: Session,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Processes native GitLab webhook payloads."""
        project = payload.get("project", {})
        repo_name = project.get("path_with_namespace") or project.get("name") or "unknown/gitlab-repo"
        user_name = payload.get("user_name") or payload.get("user_username") or "gitlab-user"

        cls.record_raw_event(
            db=db,
            source="gitlab",
            event_type=event_type,
            payload=payload,
            repository=repo_name,
            sender=user_name,
        )

        scan_result = None

        if "Push" in event_type or payload.get("object_kind") == "push":
            ref = payload.get("ref", "refs/heads/main")
            branch = ref.replace("refs/heads/", "")
            commits = payload.get("commits", [])
            commit_sha = payload.get("after") or (commits[-1].get("id") if commits else "0000000")
            commit_msg = commits[-1].get("message") if commits else "GitLab Push Hook"

            diff_text = payload.get("diff")
            if diff_text:
                scan_result = cls._run_and_save_static_analysis(
                    db=db,
                    diff_text=diff_text,
                    repo_name=repo_name,
                    commit_sha=commit_sha,
                )

            run = PipelineRun(
                pipeline_id=f"gl-push-{commit_sha[:7]}",
                repository=repo_name,
                branch=branch,
                commit_sha=commit_sha,
                commit_message=commit_msg,
                author=user_name,
                status="running",
                stage="build",
            )
            db.add(run)
            db.commit()

            # Broadcast via WebSocket
            metrics = _get_current_metrics_dict()
            run_broadcast = {
                "pipeline_id": run.pipeline_id,
                "repository": repo_name,
                "branch": branch,
                "commit_sha": commit_sha,
                "commit_message": commit_msg,
                "author": user_name,
                "status": "running",
                "stage": "build",
                "duration_seconds": 0.0,
            }
            ws_manager.broadcast_pipeline_update(run_broadcast, metrics)

            if scan_result and not scan_result.is_safe:
                ws_manager.broadcast_security_alert(
                    findings=[f.model_dump() for f in scan_result.findings],
                    repository=repo_name,
                    commit_sha=commit_sha,
                    metrics=metrics,
                )

            return {
                "status": "success",
                "message": f"GitLab Push Hook processed for {branch}",
                "commit_sha": commit_sha,
                "static_analysis": scan_result.model_dump() if scan_result else None,
            }

        elif "Pipeline" in event_type or payload.get("object_kind") == "pipeline":
            obj_attrs = payload.get("object_attributes", {})
            pipeline_id = f"gl-pipe-{obj_attrs.get('id', '0')}"
            status = obj_attrs.get("status", "running")
            duration = float(obj_attrs.get("duration") or 0.0)
            branch = obj_attrs.get("ref", "main")
            sha = obj_attrs.get("sha", "")

            status_map = {
                "success": "success",
                "failed": "failed",
                "canceled": "cancelled",
                "running": "running",
                "pending": "running",
            }
            normalized_status = status_map.get(status, "running")

            run = db.query(PipelineRun).filter_by(pipeline_id=pipeline_id).first()
            if not run:
                run = PipelineRun(
                    pipeline_id=pipeline_id,
                    repository=repo_name,
                    branch=branch,
                    commit_sha=sha,
                    commit_message="GitLab CI Pipeline",
                    author=user_name,
                    status=normalized_status,
                    stage="pipeline",
                    duration_seconds=duration,
                )
                db.add(run)
            else:
                run.status = normalized_status
                run.duration_seconds = duration
                if normalized_status in ("success", "failed"):
                    run.completed_at = datetime.now(timezone.utc)

            db.commit()

            # Broadcast via WebSocket
            metrics = _get_current_metrics_dict()
            run_broadcast = {
                "pipeline_id": pipeline_id,
                "repository": repo_name,
                "branch": branch,
                "commit_sha": sha,
                "commit_message": "GitLab CI Pipeline",
                "author": user_name,
                "status": normalized_status,
                "stage": "pipeline",
                "duration_seconds": duration,
            }
            if normalized_status == "failed":
                ws_manager.broadcast_build_failure(run_broadcast, metrics=metrics)
            else:
                ws_manager.broadcast_pipeline_update(run_broadcast, metrics)

            return {"status": "success", "pipeline_id": pipeline_id, "build_status": normalized_status}

        return {"status": "acknowledged", "event_type": event_type}

    # ==========================================
    # Simulated Webhook Helpers
    # ==========================================

    @classmethod
    def process_simulated_push(cls, db: Session, payload: SimulatedPushPayload) -> Dict[str, Any]:
        """Handles simulated push event."""
        branch = payload.ref.replace("refs/heads/", "")
        scan_result = None

        if payload.diff:
            scan_result = cls._run_and_save_static_analysis(
                db=db,
                diff_text=payload.diff,
                repo_name=payload.repository,
                commit_sha=payload.commit_sha,
            )

        # Record webhook event
        cls.record_raw_event(
            db=db,
            source="simulated",
            event_type="push",
            payload=payload.model_dump(),
            repository=payload.repository,
            sender=payload.author,
        )

        # Record Pipeline Run triggered by push
        pipeline_status = "failed" if (scan_result and not scan_result.is_safe) else "success"
        failure_reason = "Blocked by Autonomous Static Analysis: High-severity finding detected in diff." if pipeline_status == "failed" else None

        run = PipelineRun(
            pipeline_id=f"sim-run-{payload.commit_sha[:7]}",
            repository=payload.repository,
            branch=branch,
            commit_sha=payload.commit_sha,
            commit_message=payload.commit_message,
            author=payload.author,
            status=pipeline_status,
            stage="lint_and_build",
            duration_seconds=12.4,
            failure_reason=failure_reason,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(run)
        db.commit()

        # Broadcast real-time updates via WebSocket
        metrics = _get_current_metrics_dict()
        run_data = {
            "pipeline_id": run.pipeline_id,
            "repository": run.repository,
            "branch": run.branch,
            "commit_sha": run.commit_sha,
            "commit_message": run.commit_message,
            "author": run.author,
            "status": run.status,
            "stage": run.stage,
            "duration_seconds": run.duration_seconds,
            "failure_reason": run.failure_reason,
        }

        if pipeline_status == "failed":
            ws_manager.broadcast_build_failure(run_data, failure_reason, metrics)
        else:
            ws_manager.broadcast_pipeline_update(run_data, metrics)

        if scan_result and not scan_result.is_safe:
            ws_manager.broadcast_security_alert(
                findings=[f.model_dump() for f in scan_result.findings],
                repository=payload.repository,
                commit_sha=payload.commit_sha,
                metrics=metrics,
            )

        return {
            "status": "success",
            "message": f"Simulated push processed for branch '{branch}'",
            "pipeline_status": pipeline_status,
            "static_analysis": scan_result.model_dump() if scan_result else None,
        }

    @classmethod
    def process_simulated_pull_request(cls, db: Session, payload: SimulatedPullRequestPayload) -> Dict[str, Any]:
        """Handles simulated pull request event."""
        scan_result = None
        if payload.diff:
            scan_result = cls._run_and_save_static_analysis(
                db=db,
                diff_text=payload.diff,
                repo_name=payload.repository,
                commit_sha=payload.head_sha,
            )

        # Record webhook event
        cls.record_raw_event(
            db=db,
            source="simulated",
            event_type="pull_request",
            payload=payload.model_dump(),
            repository=payload.repository,
            sender=payload.author,
        )

        # Upsert PR
        pr = db.query(PullRequest).filter_by(
            repository=payload.repository, pr_number=payload.pr_number
        ).first()

        if not pr:
            pr = PullRequest(
                repository=payload.repository,
                pr_number=payload.pr_number,
                title=payload.title,
                state="open" if payload.action in ("opened", "reopened", "synchronize") else payload.action,
                action=payload.action,
                author=payload.author,
                head_branch=payload.head_branch,
                base_branch=payload.base_branch,
                head_sha=payload.head_sha,
            )
            db.add(pr)
        else:
            pr.title = payload.title
            pr.action = payload.action
            pr.state = "open" if payload.action in ("opened", "reopened", "synchronize") else payload.action
            pr.head_sha = payload.head_sha
            pr.updated_at = datetime.now(timezone.utc)

        db.commit()

        # Broadcast PR update via WebSocket
        metrics = _get_current_metrics_dict()
        pr_data = {
            "pipeline_id": f"pr-{payload.pr_number}",
            "repository": payload.repository,
            "branch": payload.head_branch,
            "commit_sha": payload.head_sha,
            "commit_message": payload.title,
            "author": payload.author,
            "status": payload.action,
            "stage": "pull_request",
            "duration_seconds": 0,
        }
        ws_manager.broadcast_pipeline_update(pr_data, metrics)

        if scan_result and not scan_result.is_safe:
            ws_manager.broadcast_security_alert(
                findings=[f.model_dump() for f in scan_result.findings],
                repository=payload.repository,
                commit_sha=payload.head_sha,
                metrics=metrics,
            )

        return {
            "status": "success",
            "message": f"Simulated PR #{payload.pr_number} processed",
            "pr_number": payload.pr_number,
            "static_analysis": scan_result.model_dump() if scan_result else None,
        }

    @classmethod
    def process_simulated_build_status(cls, db: Session, payload: SimulatedBuildStatusPayload) -> Dict[str, Any]:
        """Handles simulated build/pipeline status update."""
        cls.record_raw_event(
            db=db,
            source="simulated",
            event_type="build_status",
            payload=payload.model_dump(),
            repository=payload.repository,
            sender=payload.author or "simulated-ci",
        )

        run = db.query(PipelineRun).filter_by(pipeline_id=payload.pipeline_id).first()
        if not run:
            run = PipelineRun(
                pipeline_id=payload.pipeline_id,
                repository=payload.repository,
                branch=payload.branch,
                commit_sha=payload.commit_sha,
                commit_message=payload.commit_message,
                author=payload.author,
                status=payload.status.lower(),
                stage=payload.stage,
                duration_seconds=payload.duration_seconds,
                failure_reason=payload.failure_reason,
                completed_at=datetime.now(timezone.utc) if payload.status.lower() in ("success", "failed", "cancelled") else None,
            )
            db.add(run)
        else:
            run.status = payload.status.lower()
            run.stage = payload.stage
            run.duration_seconds = payload.duration_seconds
            run.failure_reason = payload.failure_reason
            if payload.status.lower() in ("success", "failed", "cancelled"):
                run.completed_at = datetime.now(timezone.utc)

        db.commit()

        # Broadcast build status update via WebSocket
        metrics = _get_current_metrics_dict()
        run_data = {
            "pipeline_id": payload.pipeline_id,
            "repository": payload.repository,
            "branch": payload.branch,
            "commit_sha": payload.commit_sha,
            "commit_message": payload.commit_message,
            "author": payload.author,
            "status": payload.status.lower(),
            "stage": payload.stage,
            "duration_seconds": payload.duration_seconds,
            "failure_reason": payload.failure_reason,
        }

        if payload.status.lower() == "failed":
            ws_manager.broadcast_build_failure(run_data, payload.failure_reason, metrics)
        else:
            ws_manager.broadcast_pipeline_update(run_data, metrics)

        return {
            "status": "success",
            "message": f"Pipeline run '{payload.pipeline_id}' updated to status '{payload.status}'",
            "pipeline_id": payload.pipeline_id,
        }

    @classmethod
    def _run_and_save_static_analysis(
        cls,
        db: Session,
        diff_text: str,
        repo_name: str,
        commit_sha: str,
    ) -> DiffScanResponse:
        """Helper to scan diff and store findings to database."""
        result = StaticAnalysisService.scan_diff(diff_text)
        for finding in result.findings:
            db_finding = SecurityFinding(
                repository=repo_name,
                commit_sha=commit_sha,
                file_path=finding.file_path,
                line_number=finding.line_number,
                rule_id=finding.rule_id,
                rule_name=finding.rule_name,
                issue_type=finding.issue_type,
                severity=finding.severity,
                description=finding.description,
                snippet_redacted=finding.snippet_redacted,
                recommendation=finding.recommendation,
                created_at=datetime.now(timezone.utc),
            )
            db.add(db_finding)
        db.commit()
        return result
