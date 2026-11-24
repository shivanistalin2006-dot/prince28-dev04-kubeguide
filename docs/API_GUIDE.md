# KubeGuide API Reference & Usage Guide

KubeGuide provides a RESTful API for querying Kubernetes troubleshooting documents, system liveness, and database readiness.

---

## 1. Endpoints

### `GET /health` (Liveness Probe)
Verifies the application process is running and accepting HTTP requests.

* **Response (200 OK):**
  ```json
  {
    "status": "ok",
    "app": "kubeguide",
    "env": "production",
    "version": "e269eef"
  }
  ```

---

### `GET /ready` (Readiness Probe)
Performs an active database connection check against PostgreSQL.

* **Response (200 OK - Healthy):**
  ```json
  {
    "status": "ready",
    "checks": {
      "database": true
    }
  }
  ```
* **Response (503 Service Unavailable - Database Down):**
  ```json
  {
    "status": "unavailable",
    "checks": {
      "database": false
    }
  }
  ```

---

### `GET /v1/documents` (List Documents)
Retrieves a paginated list of Kubernetes documentation records.

* **Query Parameters:**
  * `limit` *(int, default: 20, max: 100)*: Maximum documents to return.
  * `offset` *(int, default: 0)*: Pagination offset.
  * `page` *(string, optional)*: Filter by exact metadata page identifier.
* **Example Request:**
  ```bash
  curl -s "https://kubeguide.onrender.com/v1/documents?limit=5"
  ```
* **Example Response (200 OK):**
  ```json
  [
    {
      "id": 1,
      "source": "k8s-docs",
      "url": "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/",
      "title": "Deployments",
      "licence": "CC BY 4.0",
      "metadata": {
        "page": "deployment",
        "kind": "concept"
      }
    }
  ]
  ```

---

## 2. Standard Response Headers

Every API response contains observability headers:
* `X-Request-ID`: Correlation identifier for distributed tracing (propagated if sent in request).
* `X-Process-Time`: Server-side request processing duration (e.g., `1.45ms`).
