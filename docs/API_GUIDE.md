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
  curl -s "https://kubeguide.onrender.com/v1/documents?limit=2"
  ```
* **Example Response (200 OK):**
  ```json
  {
    "items": [
      {
        "id": "data/raw/k8s-docs/content/en/docs/concepts/architecture/cgroups.md",
        "title": "What is cgroup v2?",
        "doc_type": "text",
        "source_url": "https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/cgroups.md",
        "licence": "Kubernetes docs CC BY 4.0."
      }
    ],
    "total": 422,
    "offset": 0,
    "limit": 2
  }
  ```

---

### `GET /v1/documents/{doc_id}` (Get Single Document)
Retrieves metadata and properties of a specific document by its ID (supports URL paths).

* **Example Request:**
  ```bash
  curl -s "https://kubeguide.onrender.com/v1/documents/data/raw/k8s-docs/content/en/docs/concepts/architecture/cgroups.md"
  ```
* **Example Response (200 OK):**
  ```json
  {
    "id": "data/raw/k8s-docs/content/en/docs/concepts/architecture/cgroups.md",
    "title": "What is cgroup v2?",
    "doc_type": "text",
    "source_url": "https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/cgroups.md",
    "licence": "Kubernetes docs CC BY 4.0."
  }
  ```

---

### `GET /v1/documents/{doc_id}/pages` (Get Document Pages)
Retrieves extracted page content and heading hierarchies for a document.

* **Query Parameters:**
  * `page_no` *(int, optional)*: When provided, returns only the specified page object. When omitted, returns all pages for the document.
* **Example Request (Single Page):**
  ```bash
  curl -s "https://kubeguide.onrender.com/v1/documents/data/raw/k8s-docs/content/en/docs/concepts/architecture/cgroups.md/pages?page_no=1"
  ```
* **Example Response (200 OK):**
  ```json
  {
    "document_id": "data/raw/k8s-docs/content/en/docs/concepts/architecture/cgroups.md",
    "page_no": 1,
    "text": "Control groups are a Linux kernel feature that limits...",
    "headings": ["What is cgroup v2?"]
  }
  ```
* **Error Response (404 Not Found - RFC 7807):**
  ```json
  {
    "type": "https://example.com/probs/not-found",
    "title": "Not Found",
    "status": 404,
    "detail": "Page 99 not found for document 'data/raw/...'.",
    "instance": "/v1/documents/.../pages"
  }
  ```

---

## 2. Standard Response Headers

Every API response contains observability headers:
* `X-Request-ID`: Correlation identifier for distributed tracing (propagated if sent in request).
* `X-Process-Time`: Server-side request processing duration (e.g., `1.45ms`).
