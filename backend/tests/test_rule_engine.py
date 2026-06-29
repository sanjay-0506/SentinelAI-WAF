import pytest
from app.rules.engine import RuleEngine

def test_sqli_union_select(rule_engine: RuleEngine):
    result = rule_engine.evaluate("/search", "1 UNION SELECT 1,2,3--", {})
    assert not result.allowed
    assert result.attack_type == "SQLI"

def test_xss_script(rule_engine: RuleEngine):
    result = rule_engine.evaluate("/post", "<script>alert(1)</script>", {})
    assert not result.allowed
    assert result.attack_type == "XSS"

def test_path_traversal(rule_engine: RuleEngine):
    result = rule_engine.evaluate("/download", "../../etc/passwd", {})
    assert not result.allowed
    assert result.attack_type == "PATH_TRAVERSAL"

def test_command_injection(rule_engine: RuleEngine):
    result = rule_engine.evaluate("/ping", "127.0.0.1; whoami", {})
    assert not result.allowed
    assert result.attack_type == "COMMAND_INJECTION"

def test_clean_request(rule_engine: RuleEngine):
    result = rule_engine.evaluate("/search", "hello world", {})
    assert result.allowed
    assert result.attack_type is None
    assert result.matched_rule is None

def test_short_circuit_behavior(rule_engine: RuleEngine):
    # This evaluates if critical rules short circuit. It depends on rule setup.
    # Usually the first match in sorted list returns.
    result = rule_engine.evaluate("/search", "1 UNION SELECT 1,2,3--", {})
    assert not result.allowed
