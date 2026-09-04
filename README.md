# Federated Clustering Kmeans Agent

> **Domain:** Privacy-Preserving Healthcare & Federated Computing
> **Reference Guidelines & Standards:** `HIPAA Safe Harbor §164.514 & Differential Privacy RDP`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Federated Clustering Kmeans Agent** is an analytical platform implementing privacy-preserving federated Lloyd's k-means clustering with differential privacy perturbation. It provides a multi-agent evaluation system with specialized workers for quality control, safety escalation, and protocol conformance.

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Multi-Agent Evaluation System**: Specialized workers (InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker) evaluate tasks independently
- **Zero-PHI Outbound Interceptor**: Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail**: Chained, cryptographically signed logs for every evaluation
- **FastAPI REST API**: OpenAPI 3.1 REST endpoints with Prometheus-compatible metrics
- **Batch Processing**: CSV-based batch evaluation with result export
- **Enrichment Suite**: 8 domain-specific engines for secure aggregation, differential privacy, Byzantine resilience, and compliance reporting

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/federated-clustering-kmeans-agent.git
cd federated-clustering-kmeans-agent

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Optional: Set audit secret key for persistent audit integrity
export AUDIT_SECRET_KEY="your-secure-random-key-here"
```

---

## 💻 CLI Quickstart & Usage

### 1. Run Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Interactive Chat Query
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task identifier (required)
- `--target`: Target entity identifier (required)
- `--primary`: Primary metric value (float, required)
- `--secondary`: Secondary metric value (float, optional)
- `--critical`: Flag for critical/emergency status (boolean)
- `--status`: Status descriptor (e.g., NOMINAL, DISCORDANT, ANOMALY)

### Input Data Schema (CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task identifier | Required |
| `target_identifier` | Target entity identifier | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary measurement value | Optional |
| `is_critical_flag` | Critical flag (true/false) | Optional |
| `status_descriptor` | Status descriptor | Optional |

---

## 🛡️ Security Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOB, and patient names.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Input Validation:** Pydantic models with bounds checking and path traversal prevention.
* **Configurable Audit Key:** Set `AUDIT_SECRET_KEY` environment variable for persistent audit integrity.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t federated-clustering-kmeans-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" federated-clustering-kmeans-agent
```

Or using Docker Compose:

```bash
docker-compose up -d
```

---

## 📁 Project Structure

```
federated-clustering-kmeans-agent/
├── agents/                  # Multi-agent evaluation system
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Master orchestrator
│   ├── workers.py          # Specialized evaluation workers
│   ├── llm_factory.py      # LLM provider factory
│   ├── learning.py         # Bayesian calibration engine
│   ├── metrics.py          # Prometheus metrics collector
│   └── streamer.py         # WebSocket telemetry broadcaster
├── fed_kmeans/             # Federated K-means clustering module
│   ├── agents.py           # Sub-agent coordination
│   ├── engine.py           # Core algorithmic engine
│   ├── models.py           # Data models
│   ├── cli.py              # CLI interface
│   └── server.py           # FastAPI server factory
├── tests/                  # Test suite
├── web/                    # Operations console (HTML)
├── cli.py                  # Main CLI entry point
├── enrichment.py           # Domain-specific enrichment engines
├── simulator.py            # High-throughput simulation
├── pyproject.toml          # Project configuration
├── Dockerfile              # Container build
└── docker-compose.yml      # Container orchestration
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
