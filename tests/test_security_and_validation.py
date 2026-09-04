"""
Focused tests for security improvements and input validation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, AuditTrail
from agents.models import SystemTaskPayload, UrgencyLevel
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from cli import _parse_bool


class TestParseBool:
    """Tests for the _parse_bool utility function."""

    def test_true_values(self):
        assert _parse_bool("true") is True
        assert _parse_bool("True") is True
        assert _parse_bool("TRUE") is True
        assert _parse_bool("1") is True
        assert _parse_bool("yes") is True
        assert _parse_bool("Y") is True
        assert _parse_bool("on") is True

    def test_false_values(self):
        assert _parse_bool("false") is False
        assert _parse_bool("False") is False
        assert _parse_bool("FALSE") is False
        assert _parse_bool("0") is False
        assert _parse_bool("no") is False
        assert _parse_bool("N") is False
        assert _parse_bool("off") is False
        assert _parse_bool("") is False

    def test_boolean_passthrough(self):
        assert _parse_bool(True) is True
        assert _parse_bool(False) is False

    def test_whitespace_handling(self):
        assert _parse_bool(" true ") is True
        assert _parse_bool(" false ") is False


class TestInputValidation:
    """Tests for input validation in SystemTaskPayload."""

    def test_valid_payload(self):
        payload = SystemTaskPayload(
            task_id="TASK-001",
            target_identifier="TARGET-01",
            primary_metric=15.0,
            secondary_metric=5.0,
        )
        assert payload.task_id == "TASK-001"
        assert payload.target_identifier == "TARGET-01"

    def test_path_traversal_prevention_task_id(self):
        with pytest.raises(ValueError, match="invalid characters"):
            SystemTaskPayload(
                task_id="../etc/passwd",
                target_identifier="TARGET-01",
                primary_metric=15.0,
            )

    def test_path_traversal_prevention_target(self):
        with pytest.raises(ValueError, match="invalid characters"):
            SystemTaskPayload(
                task_id="TASK-001",
                target_identifier="..\\windows\\system32",
                primary_metric=15.0,
            )

    def test_null_byte_prevention(self):
        with pytest.raises(ValueError, match="invalid characters"):
            SystemTaskPayload(
                task_id="TASK\x00INJECT",
                target_identifier="TARGET-01",
                primary_metric=15.0,
            )

    def test_empty_task_id_rejected(self):
        with pytest.raises(ValueError):
            SystemTaskPayload(
                task_id="",
                target_identifier="TARGET-01",
                primary_metric=15.0,
            )

    def test_max_length_enforcement(self):
        with pytest.raises(ValueError):
            SystemTaskPayload(
                task_id="T" * 200,
                target_identifier="TARGET-01",
                primary_metric=15.0,
            )

    def test_whitespace_stripped(self):
        payload = SystemTaskPayload(
            task_id="  TASK-001  ",
            target_identifier="  TARGET-01  ",
            primary_metric=15.0,
        )
        assert payload.task_id == "TASK-001"
        assert payload.target_identifier == "TARGET-01"


class TestPHIGuard:
    """Tests for PHI detection and redaction."""

    def test_ssn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")

    def test_mrn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("MRN-12345678")

    def test_phone_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_email_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("TARGET-BIO-01 primary metric 28.5")

    def test_redact_phi(self):
        result = PHIGuard.redact_phi("Patient MRN-12345678 is stable")
        assert "REDACTED_IDENTIFIER" in result
        assert "MRN-12345678" not in result

    def test_empty_string_handled(self):
        PHIGuard.assert_no_phi("")


class TestAuditTrail:
    """Tests for HMAC-SHA256 audit trail integrity."""

    def test_audit_trail_integrity(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("test_actor", "test_tier", "TEST_EVENT", {"detail": "value1"})
        trail.log("test_actor", "test_tier", "TEST_EVENT", {"detail": "value2"})
        assert trail.verify_integrity() is True

    def test_audit_trail_tamper_detection(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("test_actor", "test_tier", "TEST_EVENT", {"detail": "value1"})
        trail.log("test_actor", "test_tier", "TEST_EVENT", {"detail": "value2"})
        # Tamper with the trail
        trail.logs[0]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False

    def test_audit_trail_empty(self):
        trail = AuditTrail(secret_key="test-key-123")
        assert trail.verify_integrity() is True
        assert trail.get_trail() == []


class TestWorkerEdgeCases:
    """Tests for worker edge cases."""

    def test_qc_worker_boundary_value(self):
        # Exactly at threshold should not trigger
        payload = SystemTaskPayload(
            task_id="T1", target_identifier="KEY-01", primary_metric=25.0
        )
        alerts = InvariantQCWorker.evaluate(payload)
        assert len(alerts) == 0

    def test_qc_worker_just_above_threshold(self):
        payload = SystemTaskPayload(
            task_id="T1", target_identifier="KEY-01", primary_metric=25.01
        )
        alerts = InvariantQCWorker.evaluate(payload)
        assert len(alerts) == 1
        assert alerts[0].urgency == UrgencyLevel.ELEVATED

    def test_safety_worker_critical_flag_only(self):
        payload = SystemTaskPayload(
            task_id="T1", target_identifier="KEY-01",
            primary_metric=10.0, secondary_metric=5.0,
            is_critical_flag=True
        )
        alerts = SafetyEscalationWorker.evaluate(payload)
        assert len(alerts) == 1
        assert alerts[0].urgency == UrgencyLevel.CRITICAL_STAT

    def test_conformance_worker_clean_descriptor(self):
        payload = SystemTaskPayload(
            task_id="T1", target_identifier="KEY-01",
            primary_metric=10.0, status_descriptor="NOMINAL"
        )
        alerts = ProtocolConformanceWorker.evaluate(payload)
        assert len(alerts) == 0

    def test_conformance_worker_multiple_flags(self):
        for flag in ["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"]:
            payload = SystemTaskPayload(
                task_id="T1", target_identifier="KEY-01",
                primary_metric=10.0, status_descriptor=flag
            )
            alerts = ProtocolConformanceWorker.evaluate(payload)
            assert len(alerts) == 1, f"Flag '{flag}' should trigger alert"
