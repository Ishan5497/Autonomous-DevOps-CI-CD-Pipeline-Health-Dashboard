from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==========================================
# Webhook Input Schemas (Simulated & Direct)
# ==========================================

class SimulatedPushPayload(BaseModel):
    repository: str = Field(..., description="Target repository name, e.g. Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard")
    ref: str = Field(default="refs/heads/main", description="Git ref (e.g. refs/heads/main)")
    commit_sha: str = Field(..., description="Commit hash")
    commit_message: str = Field(..., description="Commit message")
    author: str = Field(default="developer@example.com", description="Author email or username")
    diff: Optional[str] = Field(
        default=None,
        description="Optional Git diff text to trigger static analysis scan on push",
    )


class SimulatedPullRequestPayload(BaseModel):
    repository: str = Field(..., description="Target repository name")
    pr_number: int = Field(..., description="Pull request number")
    title: str = Field(..., description="Pull request title")
    action: str = Field(default="opened", description="PR action: opened, synchronize, closed, merged")
    author: str = Field(default="ishan-dev", description="PR author username")
    head_branch: str = Field(default="feature/health-dashboard")
    base_branch: str = Field(default="main")
    head_sha: str = Field(..., description="Head commit SHA")
    diff: Optional[str] = Field(
        default=None,
        description="Optional PR diff to scan for secrets or vulnerabilities",
    )


class SimulatedBuildStatusPayload(BaseModel):
    repository: str = Field(..., description="Target repository name")
    pipeline_id: str = Field(..., description="Unique pipeline/build identifier")
    branch: str = Field(default="main")
    commit_sha: str = Field(..., description="Commit SHA associated with build")
    commit_message: Optional[str] = Field(default="feat: deploy pipeline engine")
    author: Optional[str] = Field(default="ci-bot")
    status: str = Field(..., description="Build status: success, failed, running, cancelled")
    stage: str = Field(default="build", description="Pipeline stage: lint, build, test, deploy")
    duration_seconds: float = Field(default=38.5)
    failure_reason: Optional[str] = Field(default=None)


# ==========================================
# Static Analysis Schemas
# ==========================================

class DiffScanRequest(BaseModel):
    diff: str = Field(..., description="Raw unified diff or source code patch to analyze")
    file_path: Optional[str] = Field(default="patch.diff")
    commit_sha: Optional[str] = Field(default="manual-scan")
    repository: Optional[str] = Field(default="local-workspace")


class StaticFinding(BaseModel):
    rule_id: str
    rule_name: str
    issue_type: str  # HARDCODED_SECRET, CODE_SMELL, SECURITY_VULNERABILITY
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    snippet_redacted: str
    recommendation: Optional[str] = None


class DiffScanResponse(BaseModel):
    scanned_lines: int
    findings_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    is_safe: bool
    findings: List[StaticFinding]


# ==========================================
# Output & Analytics Schemas
# ==========================================

class WebhookEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    event_type: str
    delivery_id: Optional[str] = None
    repository: Optional[str] = None
    sender: Optional[str] = None
    status: str
    created_at: datetime


class PipelineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pipeline_id: Optional[str] = None
    repository: str
    branch: str
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    author: Optional[str] = None
    status: str
    stage: str
    duration_seconds: float
    failure_reason: Optional[str] = None
    created_at: datetime


class PullRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository: str
    pr_number: int
    title: str
    state: str
    action: str
    author: Optional[str] = None
    head_branch: Optional[str] = None
    base_branch: Optional[str] = None
    head_sha: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SecurityFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository: Optional[str] = None
    commit_sha: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    rule_id: str
    rule_name: str
    issue_type: str
    severity: str
    description: str
    snippet_redacted: str
    recommendation: Optional[str] = None
    created_at: datetime


class AutonomousRecommendation(BaseModel):
    id: str
    type: str  # "SECURITY_ALERT", "PIPELINE_FIX", "PERFORMANCE_OPTIMIZATION", "RECOVERY_ALERT"
    priority: str  # "HIGH", "MEDIUM", "LOW"
    title: str
    message: str
    suggested_action: str


class PipelineHealthMetrics(BaseModel):
    total_runs: int
    successful_runs: int
    failed_runs: int
    running_runs: int
    success_rate_percent: float
    failure_rate_percent: float
    average_duration_seconds: float
    mttr_seconds: float  # Mean Time To Recovery
    mttr_display: str
    health_grade: str  # A+, A, B, C, F
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    total_security_findings: int
    critical_vulnerabilities: int
    recommendations: List[AutonomousRecommendation]


class DashboardSummaryResponse(BaseModel):
    health: PipelineHealthMetrics
    recent_runs: List[PipelineRunResponse]
    recent_pull_requests: List[PullRequestResponse]
    recent_findings: List[SecurityFindingResponse]
    system_status: Dict[str, Any]
