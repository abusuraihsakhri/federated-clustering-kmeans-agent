"""Regression tests for signed audit records and input handling."""
import pytest
from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from fed_kmeans.clustering import federated_kmeans
from fed_kmeans.cli import main as package_cli
from cli import main as root_cli


@pytest.mark.parametrize("field", ["current_hash", "payload_hash", "timestamp", "actor", "event_type"])
def test_audit_tamper_rejected(field):
    trail = AuditTrail("a-fixed-test-key")
    trail.log("actor", "tier", "event", {"value": "first"})
    trail.log("actor", "tier", "event", {"value": "second"})
    trail.logs[-1][field] = "tampered"
    assert trail.verify_integrity() is False


def test_audit_trail_returns_copies():
    trail = AuditTrail("a-fixed-test-key")
    trail.log("actor", "tier", "event", {"value": 1})
    external = trail.get_trail()
    external[0]["current_hash"] = "tampered"
    assert trail.verify_integrity() is True


def test_phi_in_nested_metadata_is_rejected():
    supervisor = SystemSupervisor()
    data = SystemTaskPayload(task_id="TASK-1", target_identifier="KEY-1", primary_metric=1,
                             attributes={"details": {"email": "patient@example.com"}})
    with pytest.raises(SecurityException):
        supervisor.process_task(data)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_telemetry_rejects_nonfinite(value):
    with pytest.raises(ValueError):
        SystemTaskPayload(task_id="TASK", target_identifier="KEY", primary_metric=value)


def test_blank_identifier_rejected():
    with pytest.raises(ValueError):
        SystemTaskPayload(task_id="    ", target_identifier="KEY", primary_metric=1)


def test_cli_cluster_round_trip(tmp_path, capsys):
    import json
    payload = {"sites": [[[0, 0], [0, 2]], [[10, 10], [10, 12]]],
               "initial_centroids": [[0, 0], [10, 10]]}
    source = tmp_path / "sites.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    assert root_cli(["cluster", "-i", str(source)]) == 0
    assert json.loads(capsys.readouterr().out)["centroids"] == [[0, 1], [10, 11]]
    result = tmp_path / "results.json"
    assert package_cli(["cluster", "-i", str(source), "-o", str(result)]) == 0
    assert json.loads(result.read_text(encoding="utf-8"))["inertia"] == pytest.approx(4)
