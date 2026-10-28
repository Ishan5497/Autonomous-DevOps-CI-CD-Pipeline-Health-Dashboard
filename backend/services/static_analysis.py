import re
from typing import List, Dict, Any, Tuple
from backend.models.schemas import StaticFinding, DiffScanResponse


class StaticAnalysisService:
    """
    Mock Static Analysis Service that inspects incoming commit diffs
    and source patches for hardcoded secrets, dangerous functions,
    and common DevOps/security anti-patterns.
    """

    SECRET_RULES = [
        {
            "id": "SEC-001",
            "name": "AWS Access Key ID",
            "pattern": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "severity": "CRITICAL",
            "type": "HARDCODED_SECRET",
            "description": "Hardcoded AWS Access Key ID detected. Exposes cloud infrastructure to unauthorized access.",
            "recommendation": "Use environment variables or AWS IAM roles/Secrets Manager instead of hardcoded keys.",
        },
        {
            "id": "SEC-002",
            "name": "AWS Secret Access Key",
            "pattern": r"(?i)(?:aws_secret_access_key|aws_secret|secret_key)\s*[:=]\s*['\"]([a-zA-Z0-9/+=]{40})['\"]",
            "severity": "CRITICAL",
            "type": "HARDCODED_SECRET",
            "description": "Hardcoded AWS Secret Access Key detected.",
            "recommendation": "Rotate compromised AWS secrets immediately and use AWS Secrets Manager or vault.",
        },
        {
            "id": "SEC-003",
            "name": "GitHub Personal Access Token",
            "pattern": r"(?:ghp_[0-9a-zA-Z]{36}|gho_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82})",
            "severity": "CRITICAL",
            "type": "HARDCODED_SECRET",
            "description": "GitHub Personal Access Token leaked in code diff.",
            "recommendation": "Revoke the token in GitHub Settings and inject it via GitHub Actions Secrets.",
        },
        {
            "id": "SEC-004",
            "name": "GitLab Personal Access Token",
            "pattern": r"glpat-[0-9a-zA-Z\-_]{20,}",
            "severity": "CRITICAL",
            "type": "HARDCODED_SECRET",
            "description": "GitLab Personal Access Token detected.",
            "recommendation": "Revoke GitLab PAT and configure CI/CD masked variables.",
        },
        {
            "id": "SEC-005",
            "name": "Slack Webhook / Bot Token",
            "pattern": r"(?:https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+|xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24})",
            "severity": "HIGH",
            "type": "HARDCODED_SECRET",
            "description": "Slack webhook URL or bot token committed to repository.",
            "recommendation": "Store Slack webhook URLs in pipeline environment variables.",
        },
        {
            "id": "SEC-006",
            "name": "Private Cryptographic Key",
            "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "severity": "CRITICAL",
            "type": "HARDCODED_SECRET",
            "description": "Unencrypted Private Key block detected in diff.",
            "recommendation": "Remove private keys from version control. Use SSH agent or encrypted key stores.",
        },
        {
            "id": "SEC-007",
            "name": "Generic Hardcoded Secret / API Token",
            "pattern": r"(?i)(?:api_key|apikey|secret_token|auth_token|client_secret|db_password)\s*[:=]\s*['\"]([a-zA-Z0-9_\-\.]{16,})['\"]",
            "severity": "HIGH",
            "type": "HARDCODED_SECRET",
            "description": "High-entropy API key or authentication secret detected in source assignment.",
            "recommendation": "Load credentials from secure environment config or .env excluded from Git.",
        },
        {
            "id": "SEC-008",
            "name": "Database Connection String with Password",
            "pattern": r"(?:postgres|mysql|mongodb|redis)://[a-zA-Z0-9_\-]+:[^@\s]+@[a-zA-Z0-9_\-\.]+",
            "severity": "CRITICAL",
            "type": "HARDCODED_SECRET",
            "description": "Database connection URI with plain-text credentials found in diff.",
            "recommendation": "Externalize DB connection strings and use vault/secrets manager.",
        },
        {
            "id": "SEC-009",
            "name": "Hardcoded JSON Web Token (JWT)",
            "pattern": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
            "severity": "MEDIUM",
            "type": "HARDCODED_SECRET",
            "description": "Embedded JWT token found in source code.",
            "recommendation": "Do not hardcode authorization tokens; obtain them dynamically during runtime.",
        },
    ]

    BUG_RULES = [
        {
            "id": "BUG-001",
            "name": "Dangerous Dynamic Code Execution (eval/exec)",
            "pattern": r"(?<![a-zA-Z0-9_])(?:eval|exec)\s*\(",
            "severity": "CRITICAL",
            "type": "SECURITY_VULNERABILITY",
            "description": "Use of eval() or exec() permits arbitrary remote code execution (RCE).",
            "recommendation": "Refactor logic to use safe parsers, ast.literal_eval(), or structured JSON.",
        },
        {
            "id": "BUG-002",
            "name": "Potential SQL Injection Pattern",
            "pattern": r"(?i)(?:f[\"'].*(?:SELECT|INSERT|UPDATE|DELETE).*\{|(?:SELECT|INSERT|UPDATE|DELETE).*(?:%s|%d|\.format\(|f[\"'].*\{|\+\s*[a-zA-Z_]))",
            "severity": "HIGH",
            "type": "SECURITY_VULNERABILITY",
            "description": "String interpolation in SQL query statement introduces SQL Injection risks.",
            "recommendation": "Use parameterized queries or SQLAlchemy ORM bind parameters.",
        },
        {
            "id": "BUG-003",
            "name": "Disabled SSL/TLS Certificate Validation",
            "pattern": r"(?i)(?:verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0['\"]?|InsecureRequestWarning)",
            "severity": "HIGH",
            "type": "SECURITY_VULNERABILITY",
            "description": "TLS certificate validation disabled. Allows Man-In-The-Middle (MITM) attacks.",
            "recommendation": "Enable TLS verification and configure trusted CA certificate bundles.",
        },
        {
            "id": "BUG-004",
            "name": "Weak Cryptographic PRNG",
            "pattern": r"\brandom\.(?:random|randint|choice|randrange)\(",
            "severity": "MEDIUM",
            "type": "CODE_SMELL",
            "description": "Standard pseudo-random generator used in potentially sensitive context.",
            "recommendation": "Use Python's `secrets` module for security-sensitive tokens and random values.",
        },
        {
            "id": "BUG-005",
            "name": "Silent Exception Swallowing",
            "pattern": r"except\s*:\s*pass|except\s+Exception\s*:\s*pass",
            "severity": "MEDIUM",
            "type": "CODE_SMELL",
            "description": "Bare 'except: pass' silently suppresses all errors including system interrupts.",
            "recommendation": "Catch specific exception types and log warnings or re-raise.",
        },
        {
            "id": "BUG-006",
            "name": "Hardcoded Sensitive Debug / Unrestricted Host",
            "pattern": r"(?i)(?:DEBUG\s*=\s*True|host\s*=\s*['\"]0\.0\.0\.0['\"])",
            "severity": "LOW",
            "type": "CODE_SMELL",
            "description": "Debug mode enabled or server binding to all network interfaces.",
            "recommendation": "Drive DEBUG and bind host through environment variables for production readiness.",
        },
    ]

    @classmethod
    def redact_secret(cls, value: str) -> str:
        """Redacts sensitive strings to protect credentials while keeping context."""
        if not value:
            return "***"
        length = len(value)
        if length <= 6:
            return "*" * length
        visible = 3 if length < 20 else 4
        return f"{value[:visible]}{'*' * (length - (visible * 2))}{value[-visible:]}"

    @classmethod
    def scan_diff(cls, diff_text: str, default_file_path: str = "patch.diff") -> DiffScanResponse:
        """
        Scans unified git diff or source patch.
        Only inspects added lines (starting with '+', excluding '+++') to focus on new changes.
        """
        if not diff_text:
            return DiffScanResponse(
                scanned_lines=0,
                findings_count=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                is_safe=True,
                findings=[],
            )

        findings: List[StaticFinding] = []
        lines = diff_text.splitlines()
        current_file = default_file_path
        line_num = 0

        all_rules = cls.SECRET_RULES + cls.BUG_RULES

        for idx, line in enumerate(lines, 1):
            # Check for git diff file header
            if line.startswith("+++ b/"):
                current_file = line.replace("+++ b/", "").strip()
                line_num = 0
                continue
            elif line.startswith("--- a/") or line.startswith("diff --git"):
                continue
            elif line.startswith("@@"):
                # Unified diff chunk header @@ -x,y +start,len @@
                chunk_match = re.search(r"\+(\d+)", line)
                if chunk_match:
                    line_num = int(chunk_match.group(1)) - 1
                continue

            # In diffs, lines starting with '+' (but not '+++') are new additions
            # If the text is raw code (not a git diff), scan all non-empty lines
            is_diff_addition = line.startswith("+") and not line.startswith("+++")
            is_raw_code = not any(l.startswith("diff --git") or l.startswith("@@") for l in lines[:10])

            if not (is_diff_addition or is_raw_code):
                continue

            content = line[1:] if is_diff_addition else line
            line_num += 1

            for rule in all_rules:
                match = re.search(rule["pattern"], content)
                if match:
                    raw_snippet = content.strip()
                    matched_text = match.group(0)

                    # Redact matched sensitive segment if secret rule
                    if rule["type"] == "HARDCODED_SECRET":
                        redacted = cls.redact_secret(matched_text)
                        snippet_display = raw_snippet.replace(matched_text, redacted)
                    else:
                        snippet_display = raw_snippet

                    finding = StaticFinding(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        issue_type=rule["type"],
                        severity=rule["severity"],
                        description=rule["description"],
                        file_path=current_file,
                        line_number=line_num if line_num > 0 else idx,
                        snippet_redacted=snippet_display,
                        recommendation=rule["recommendation"],
                    )
                    findings.append(finding)

        critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in findings if f.severity == "HIGH")
        medium_count = sum(1 for f in findings if f.severity == "MEDIUM")
        low_count = sum(1 for f in findings if f.severity == "LOW")

        return DiffScanResponse(
            scanned_lines=len(lines),
            findings_count=len(findings),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            is_safe=(critical_count == 0 and high_count == 0),
            findings=findings,
        )
