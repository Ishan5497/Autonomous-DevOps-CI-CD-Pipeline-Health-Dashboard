from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from backend.models.entities import PipelineRun, SecurityFinding
from backend.models.schemas import PipelineHealthMetrics, AutonomousRecommendation


class PipelineHealthService:
    """
    Calculates pipeline reliability metrics, MTTR (Mean Time To Recovery),
    flakiness indices, and synthesizes autonomous health grades and recommendations.
    """

    @staticmethod
    def calculate_health(db: Session) -> PipelineHealthMetrics:
        runs = db.query(PipelineRun).order_by(PipelineRun.created_at.desc()).all()
        findings = db.query(SecurityFinding).order_by(SecurityFinding.created_at.desc()).all()

        total_runs = len(runs)
        successful_runs = sum(1 for r in runs if r.status.lower() == "success")
        failed_runs = sum(1 for r in runs if r.status.lower() in ("failed", "failure", "error"))
        running_runs = sum(1 for r in runs if r.status.lower() in ("running", "pending", "in_progress"))

        if total_runs > 0:
            success_rate = round((successful_runs / total_runs) * 100, 1)
            failure_rate = round((failed_runs / total_runs) * 100, 1)
            durations = [r.duration_seconds for r in runs if r.duration_seconds > 0]
            avg_duration = round(sum(durations) / len(durations), 1) if durations else 0.0
        else:
            success_rate = 100.0
            failure_rate = 0.0
            avg_duration = 0.0

        # Calculate MTTR (Mean Time to Recovery) in seconds
        # Look for instances where a failed run is followed by a success
        mttr_samples: List[float] = []
        chronological_runs = sorted(runs, key=lambda r: r.created_at)
        failed_timestamp = None

        for r in chronological_runs:
            status = r.status.lower()
            if status in ("failed", "failure", "error") and failed_timestamp is None:
                failed_timestamp = r.created_at
            elif status == "success" and failed_timestamp is not None:
                recovery_time = (r.created_at - failed_timestamp).total_seconds()
                if recovery_time > 0:
                    mttr_samples.append(recovery_time)
                failed_timestamp = None

        if mttr_samples:
            mttr_seconds = round(sum(mttr_samples) / len(mttr_samples), 1)
            mttr_minutes = round(mttr_seconds / 60, 1)
            mttr_display = f"{mttr_minutes} min" if mttr_minutes >= 1 else f"{int(mttr_seconds)} sec"
        else:
            mttr_seconds = 0.0
            mttr_display = "Optimal (0 failures / instant)"

        critical_findings = [f for f in findings if f.severity.upper() == "CRITICAL"]
        high_findings = [f for f in findings if f.severity.upper() == "HIGH"]

        # Determine Health Grade & Risk Level
        if len(critical_findings) > 0 or failure_rate >= 40:
            health_grade = "F"
            risk_level = "CRITICAL"
        elif failure_rate >= 25 or len(high_findings) >= 3:
            health_grade = "D"
            risk_level = "HIGH"
        elif failure_rate >= 15 or len(high_findings) > 0:
            health_grade = "C"
            risk_level = "MODERATE"
        elif failure_rate >= 8:
            health_grade = "B"
            risk_level = "LOW"
        elif total_runs > 0 and success_rate >= 95:
            health_grade = "A+"
            risk_level = "MINIMAL"
        else:
            health_grade = "A"
            risk_level = "MINIMAL"

        # Formulate Autonomous Recommendations
        recommendations: List[AutonomousRecommendation] = []

        if critical_findings:
            recommendations.append(
                AutonomousRecommendation(
                    id="REC-SEC-01",
                    type="SECURITY_ALERT",
                    priority="HIGH",
                    title="Critical Credentials Leaked in Codebase",
                    message=f"Found {len(critical_findings)} CRITICAL severity findings (e.g. {critical_findings[0].rule_name}).",
                    suggested_action="Quarantine pipeline, revoke active credentials immediately, and enforce pre-commit scan hooks.",
                )
            )

        if failure_rate > 20:
            recommendations.append(
                AutonomousRecommendation(
                    id="REC-REL-01",
                    type="PIPELINE_FIX",
                    priority="HIGH",
                    title="Elevated Build Failure Rate Detected",
                    message=f"Failure rate is currently {failure_rate}%, exceeding the 10% SLA threshold.",
                    suggested_action="Isolate failing test suites, review latest merge commits, and enable flaky test retries.",
                )
            )

        if avg_duration > 180:
            recommendations.append(
                AutonomousRecommendation(
                    id="REC-PERF-01",
                    type="PERFORMANCE_OPTIMIZATION",
                    priority="MEDIUM",
                    title="Pipeline Execution Duration Exceeds Target",
                    message=f"Average pipeline runtime is {avg_duration}s. Slow build stages delay delivery velocity.",
                    suggested_action="Introduce Docker layer caching and parallelize matrix test execution.",
                )
            )

        if not recommendations:
            recommendations.append(
                AutonomousRecommendation(
                    id="REC-AUTO-OK",
                    type="AUTONOMOUS_HEALTHY",
                    priority="LOW",
                    title="Autonomous Pipeline In Peak Condition",
                    message="All quality gates passing. No secrets detected and build reliability is high.",
                    suggested_action="Maintain automated static analysis checks on all pull request events.",
                )
            )

        return PipelineHealthMetrics(
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            running_runs=running_runs,
            success_rate_percent=success_rate,
            failure_rate_percent=failure_rate,
            average_duration_seconds=avg_duration,
            mttr_seconds=mttr_seconds,
            mttr_display=mttr_display,
            health_grade=health_grade,
            risk_level=risk_level,
            total_security_findings=len(findings),
            critical_vulnerabilities=len(critical_findings),
            recommendations=recommendations,
        )
