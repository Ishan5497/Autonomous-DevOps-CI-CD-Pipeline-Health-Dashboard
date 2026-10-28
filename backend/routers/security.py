from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import SecurityFinding
from backend.models.schemas import (
    DiffScanRequest,
    DiffScanResponse,
    SecurityFindingResponse,
)
from backend.services.static_analysis import StaticAnalysisService

router = APIRouter(prefix="/api/v1/security", tags=["Security & Static Analysis"])


@router.post(
    "/scan-diff",
    response_model=DiffScanResponse,
    summary="Scan Code Diff for Secrets & Common Bugs",
    description="Analyzes a Git patch or diff for hardcoded secrets, dangerous functions, and DevOps security flaws.",
)
def scan_diff(request: DiffScanRequest, persist: bool = Query(False, description="Persist findings to database"), db: Session = Depends(get_db)):
    result = StaticAnalysisService.scan_diff(
        diff_text=request.diff,
        default_file_path=request.file_path or "patch.diff",
    )

    if persist and result.findings:
        for f in result.findings:
            db_finding = SecurityFinding(
                repository=request.repository,
                commit_sha=request.commit_sha,
                file_path=f.file_path,
                line_number=f.line_number,
                rule_id=f.rule_id,
                rule_name=f.rule_name,
                issue_type=f.issue_type,
                severity=f.severity,
                description=f.description,
                snippet_redacted=f.snippet_redacted,
                recommendation=f.recommendation,
            )
            db.add(db_finding)
        db.commit()

    return result


@router.get(
    "/findings",
    response_model=List[SecurityFindingResponse],
    summary="List Security Findings",
    description="Retrieve detected hardcoded secrets and code vulnerabilities with severity filters.",
)
def list_findings(
    severity: Optional[str] = None,
    repository: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(SecurityFinding)
    if severity:
        query = query.filter(SecurityFinding.severity == severity.upper())
    if repository:
        query = query.filter(SecurityFinding.repository == repository)
    return query.order_by(SecurityFinding.created_at.desc()).limit(limit).all()


@router.delete(
    "/findings/{finding_id}",
    summary="Resolve / Dismiss Security Finding",
)
def resolve_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(SecurityFinding).filter(SecurityFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    db.delete(finding)
    db.commit()
    return {"status": "success", "message": f"Finding #{finding_id} resolved"}


@router.get("/rules", summary="List Active Static Analysis Rules")
def list_rules():
    return {
        "secret_rules_count": len(StaticAnalysisService.SECRET_RULES),
        "bug_rules_count": len(StaticAnalysisService.BUG_RULES),
        "secret_rules": StaticAnalysisService.SECRET_RULES,
        "bug_rules": StaticAnalysisService.BUG_RULES,
    }
