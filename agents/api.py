"""
FastAPI REST API Server for Federated Clustering Kmeans Agent.
"""
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fed_kmeans.clustering import federated_kmeans
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Federated Clustering Kmeans Agent API",
    description="Local threshold-based telemetry auditing and k-means simulation. No secure aggregation, differential privacy, or compliance guarantee.",
    version="3.0.0-ENTERPRISE",
)


console_dir = Path(__file__).resolve().parent.parent / "web"
if console_dir.is_dir():
    app.mount("/console", StaticFiles(directory=str(console_dir), html=True), name="console")


class ClusteringRequest(BaseModel):
    sites: List[List[List[float]]]
    initial_centroids: List[List[float]]
    max_iterations: int = Field(default=50, ge=1, le=50)
    tolerance: float = Field(default=1e-6, ge=0, allow_inf_nan=False)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "federated-clustering-kmeans-agent", "domain": "Privacy-Preserving Federated Healthcare & FHE", "standard": "HIPAA Safe Harbor §164.514 / Google SecAgg Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
        return dossier.to_dict()
    except SecurityException as e:
        raise HTTPException(status_code=422, detail=f"Security violation: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal processing error")


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException as e:
        raise HTTPException(status_code=422, detail=f"Security violation: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


@app.post("/api/cluster")
def api_cluster(req: ClusteringRequest):
    """Simulate site-local aggregation. Raw data arrives at this API: not private transport."""
    try:
        return federated_kmeans(
            req.sites, req.initial_centroids,
            max_iterations=req.max_iterations, tolerance=req.tolerance,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
