---
name: api-development
description: "Implement FastAPI route handlers, Pydantic schemas, and API tests."
metadata:
  trigger-keywords: "api, endpoint, route, fastap, schema"
  trigger-patterns: "^api, ^endpoint"
---

# API Development Skill

Use this skill when introducing or modifying REST API endpoints.

---

## 🏃 Implementation Workflow

### 1. Define Pydantic Schemas
* Add request validation schemas and public response schemas inside the module's `schemas.py` or the API file.
* Use explicit type annotations and field constraints (e.g. `min_length`, `ge`).

### 2. Implement Route Handler
* Place endpoints inside the appropriate router file under `api/` (e.g. `api/accounts.py`).
* Expose endpoints using appropriate REST verbs (`GET`, `POST`, `PUT`, `DELETE`) and status codes (e.g. 201 for Created).
* Map internal exceptions (like `NotFoundError` or `ConflictError`) to corresponding HTTP status codes (404, 409).

### 3. Write Unit & Integration Tests
* Implement test cases under `tests/api/`.
* Mock dependencies or use test sessions as appropriate.
* Verify coverage meets the >80% threshold using:
  ```bash
  uv run pytest --cov=edgebook
  ```
