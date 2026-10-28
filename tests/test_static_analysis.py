from backend.services.static_analysis import StaticAnalysisService


def test_detects_aws_key():
    diff = """
diff --git a/aws_config.py b/aws_config.py
--- a/aws_config.py
+++ b/aws_config.py
@@ -1,2 +1,2 @@
-AWS_KEY = os.environ.get("AWS_KEY")
+AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
"""
    result = StaticAnalysisService.scan_diff(diff)
    assert not result.is_safe
    assert result.critical_count >= 1
    assert any(f.rule_id == "SEC-001" for f in result.findings)
    assert "AKIA" in result.findings[0].snippet_redacted
    assert "EXAMPLE" not in result.findings[0].snippet_redacted or "*" in result.findings[0].snippet_redacted


def test_detects_dangerous_eval():
    diff = """
--- a/calculator.py
+++ b/calculator.py
@@ -10,3 +10,3 @@
 def parse_expr(user_input):
+    return eval(user_input)
"""
    result = StaticAnalysisService.scan_diff(diff)
    assert not result.is_safe
    assert any(f.rule_id == "BUG-001" for f in result.findings)


def test_detects_sql_injection():
    diff = """
--- a/db.py
+++ b/db.py
@@ -5,2 +5,2 @@
-cursor.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})
+cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
"""
    result = StaticAnalysisService.scan_diff(diff)
    assert result.high_count >= 1
    assert any(f.rule_id == "BUG-002" for f in result.findings)


def test_safe_diff_passes():
    diff = """
--- a/utils.py
+++ b/utils.py
@@ -1,3 +1,5 @@
+import os
+
 def get_timeout():
+    return int(os.getenv("TIMEOUT_SECONDS", "30"))
"""
    result = StaticAnalysisService.scan_diff(diff)
    assert result.is_safe
    assert result.findings_count == 0
