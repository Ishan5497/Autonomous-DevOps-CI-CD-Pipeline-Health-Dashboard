from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from backend.models.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # github, gitlab, simulated
    event_type = Column(String(50), nullable=False)  # push, pull_request, pipeline, etc.
    delivery_id = Column(String(100), nullable=True)
    repository = Column(String(200), nullable=True, index=True)
    sender = Column(String(100), nullable=True)
    payload = Column(Text, nullable=False)
    status = Column(String(50), default="processed")  # processed, failed, ignored
    created_at = Column(DateTime, default=utc_now)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(String(100), index=True)
    repository = Column(String(200), index=True, nullable=False)
    branch = Column(String(100), default="main")
    commit_sha = Column(String(100), index=True)
    commit_message = Column(String(500), nullable=True)
    author = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False)  # success, failed, running, cancelled
    stage = Column(String(50), default="build")  # build, test, deploy, lint
    duration_seconds = Column(Float, default=0.0)
    failure_reason = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    repository = Column(String(200), index=True, nullable=False)
    pr_number = Column(Integer, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    state = Column(String(50), default="open")  # open, closed, merged
    action = Column(String(50), default="opened")
    author = Column(String(100), nullable=True)
    head_branch = Column(String(100), nullable=True)
    base_branch = Column(String(100), nullable=True)
    head_sha = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id = Column(Integer, primary_key=True, index=True)
    repository = Column(String(200), index=True, nullable=True)
    commit_sha = Column(String(100), index=True, nullable=True)
    file_path = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)
    rule_id = Column(String(50), nullable=False)
    rule_name = Column(String(100), nullable=False)
    issue_type = Column(String(50), nullable=False)  # HARDCODED_SECRET, CODE_SMELL, SECURITY_VULNERABILITY
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    description = Column(Text, nullable=False)
    snippet_redacted = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
