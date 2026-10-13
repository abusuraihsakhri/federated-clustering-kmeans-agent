# Federated Clustering K-means Agent

### [Open the Live Application →](https://abusuraihsakhri.github.io/federated-clustering-kmeans-agent/)

An executable, dependency-light **multi-site Lloyd k-means simulator**, with the repository's existing task-audit CLI, FastAPI endpoints, and validation utilities.

The clustering implementation computes cluster sums and counts at each site, aggregates those statistics, and updates centroids. It is a **single-process simulation**, not an encrypted federated-learning deployment, secure aggregation protocol, differential privacy mechanism, or validated clinical system.

## Browser application

Open [`index.html`](index.html) in a modern browser, or run `python -m http.server 8080` and visit `http://localhost:8080/`.

The browser simulator uses vanilla JavaScript and works without a Python runtime, CDN, backend, or build step. Enter or import JSON describing sites and initial centroids, inspect centroid coordinates, assignments by site, convergence and inertia, then export JSON results. All computations remain in the local browser tab; the application does not transmit data.

The GitHub Pages workflow deploys the static files and checks published HTML and JavaScript over HTTPS after each release.

## Python quick start

Python 3.9+:

```bash
python -m pip install -e ".[api,test]"
python cli.py cluster -i sample_clustering.json -o clustering_results.json
python -m fed_kmeans.cli cluster -i sample_clustering.json
python -m pytest -q
```

The two-site sample has initial centroids `[0,0]` and `[10,10]`, converging to `[0,1]` and `[10,11]` with final squared-distance inertia `4`.

### Input format

```json
{
  "sites": [
    [[0, 0], [0, 2]],
    [[10, 10], [10, 12]]
  ],
  "initial_centroids": [[0, 0], [10, 10]],
  "max_iterations": 50,
  "tolerance": 0.000001
}
```

Sites are nonempty lists of feature vectors. Initial centroids are supplied explicitly; cluster IDs follow their input order. Ties are assigned to the first centroid, and empty clusters retain their previous centroid. The simulation limits input to 64 sites, 20,000 observations, 32 features, 20 clusters, and 200 iterations (the API limits iterations to 50). Use synthetic or appropriately de-identified non-sensitive data only.

## Existing audit tools and API

The separate task-audit subsystems are retained. Their threshold-based worker alerts are **not k-means clustering calculations**:

```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

With the server running, visit `http://127.0.0.1:8000/console/index.html` to use the backend-dependent audit console; `/docs` contains the generated API schema. Endpoints include `/health`, `/metrics`, `/api/audit`, `/api/chat`, `/api/audit/logs`, and `/api/cluster`. The last accepts the JSON format above:

```bash
curl -s -X POST http://127.0.0.1:8000/api/cluster \
  -H "Content-Type: application/json" \
  --data-binary @sample_clustering.json
```

The REST clustering endpoint receives **raw site observations**. Do not send patient data or expose this service to the public internet without implementing a separate threat model, authentication, authorization, transport security and privacy architecture. The built-in audit logging is process-local; the audit key must remain private, and records are not persisted across restarts. The optional PHI regex screen is heuristic and cannot establish HIPAA/GDPR compliance or comprehensive de-identification.

For container operation, set a strong key in the shell before launching:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

Compose binds port 8000 to loopback by default. The repository retains illustrative enrichment modules; those produce generic threshold-based assessments rather than implementations of secure multiparty aggregation, Rényi-DP accounting, Byzantine-resilient clustering, or homomorphic encryption.

## Development and verification

Run `python -m pytest -q` and `node --check cluster.js && node --test tests/cluster.test.cjs`. GitHub Actions tests Python 3.10–3.12 and Node.js 22. The codebase has no browser Python dependency or production JavaScript dependencies.

Review [`agents/`](agents/) for legacy audit and telemetry workers, [`fed_kmeans/`](fed_kmeans/) for the k-means simulation and its original threshold agents, [`tests/`](tests/) for regression tests, and [`web/`](web/) for the local FastAPI audit console.

## License

MIT; see [LICENSE](LICENSE).
