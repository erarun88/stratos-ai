# API Documentation

## API Overview

The StratOS AI REST API provides programmatic access to project portfolio management data. The API is built with FastAPI and exposes endpoints for managing projects, engineers, and future AI-powered analytics.

### API Information
- **Name**: StratOS AI API
- **Version**: 1.0.0
- **Framework**: FastAPI (Python)
- **Status**: Development/Beta
- **Uptime**: 99.5% (production target)

---

## Base URL

```
Development: http://localhost:8000
Production: https://api.stratos-ai.example.com (planned)
```

---

## Authentication

### Current State
⚠️ **No authentication implemented** - All endpoints are currently public

### Planned Authentication (Roadmap)

#### JWT Token Authentication
```
Authorization: Bearer <token>
```

#### API Key Authentication
```
X-API-Key: <api_key>
```

#### OAuth 2.0 (Future)
```
Authorization: Bearer <oauth_token>
```

---

## Rate Limiting

### Current State
- No rate limiting implemented

### Planned Rate Limiting (Roadmap)

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1629792000
```

**Limits** (Planned):
- **Anonymous**: 100 requests/hour
- **Authenticated**: 1000 requests/hour
- **Premium**: Unlimited

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400
}
```

### Error Codes

| Status Code | HTTP Status | Description | Example |
|------------|-------------|-------------|---------|
| `200` | OK | Successful request | Project retrieved successfully |
| `201` | Created | Resource created successfully | Project created |
| `400` | Bad Request | Invalid request parameters | Missing required field |
| `401` | Unauthorized | Missing/invalid authentication | Invalid token |
| `403` | Forbidden | Insufficient permissions | Not authorized for resource |
| `404` | Not Found | Resource not found | Project ID doesn't exist |
| `409` | Conflict | Resource already exists | Duplicate email |
| `422` | Unprocessable Entity | Validation error | Invalid data format |
| `429` | Too Many Requests | Rate limit exceeded | Too many requests |
| `500` | Internal Server Error | Server error | Database connection failed |
| `503` | Service Unavailable | Service temporarily unavailable | Maintenance |

### Example Error Response

```json
{
  "detail": "Project with id 999 not found",
  "status_code": 404
}
```

---

## API Versioning

### Current Approach
- Single version (v1) implicit in API endpoints
- No version prefix in URLs

### Future Versioning Strategy (Planned)

```
/api/v1/projects
/api/v2/projects
```

**Versioning Policy**:
- Backward-compatible changes: No version bump
- Breaking changes: Major version bump
- Deprecation notice: 6 months before removal

---

## Endpoints

### Base Structure

All endpoints follow RESTful conventions:
- **GET**: Retrieve data (read-only)
- **POST**: Create new data (idempotent)
- **PUT**: Update existing data (full replacement)
- **PATCH**: Partially update data (not yet implemented)
- **DELETE**: Remove data (destructive)

---

### Home Endpoint

#### GET /

**Description**: Home message - verify API is running

**Authentication**: None

**Request**:
```bash
curl http://localhost:8000/
```

**Response** (200 OK):
```json
{
  "message": "Welcome to StratOS AI"
}
```

**Use Case**: Health check, verify API availability

---

### Projects Endpoints

A project has the following fields. `status` is one of `planning`, `active`,
`on_hold`, `completed`, `cancelled`. `budget` is a legacy/optional field retained
from the original schema — it is included in responses but is **not** accepted or
required by the create/update endpoints.

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | Auto-assigned |
| `name` | string | Required, non-blank |
| `customer` | string | Required, non-blank |
| `project_manager` | string | Required, non-blank |
| `status` | string enum | `planning` / `active` / `on_hold` / `completed` / `cancelled` |
| `start_date` | date (`YYYY-MM-DD`) | Optional |
| `end_date` | date (`YYYY-MM-DD`) | Optional; must be ≥ `start_date` when both are set |
| `description` | string | Optional |
| `created_at` | datetime | Auto-set on creation |
| `updated_at` | datetime | Auto-updated on modification |

#### GET /projects

**Description**: Retrieve all projects (ordered by `id`)

**Authentication**: None (planned: Required)

**Request**:
```bash
curl http://localhost:8000/projects
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "name": "CloudSync Platform",
    "customer": "TechCorp Inc.",
    "project_manager": "Sarah Mitchell",
    "status": "active",
    "start_date": "2026-01-15",
    "end_date": "2026-12-15",
    "description": "Enterprise file synchronization and collaboration platform.",
    "created_at": "2026-07-24T21:03:15.247614Z",
    "updated_at": "2026-07-24T21:03:15.247614Z"
  }
]
```

**Status Codes**:
- `200`: Success
- `500`: Server error

---

#### GET /projects/{id}

**Description**: Retrieve a specific project by ID

**Request**:
```bash
curl http://localhost:8000/projects/1
```

**Response** (200 OK): a single project object (same shape as above).

**Status Codes**:
- `200`: Success
- `404`: Project not found

---

#### POST /projects

**Description**: Create a new project

**Validation**:
- `name`, `customer`, `project_manager` required and non-blank
- `status` must be a valid enum value (defaults to `planning` if omitted)
- `end_date` must not be earlier than `start_date` when both are provided

**Request Body**:
```json
{
  "name": "AI Insights Engine",
  "customer": "Innovate Labs",
  "project_manager": "Marcus Reid",
  "status": "planning",
  "start_date": "2026-08-01",
  "end_date": "2027-01-31",
  "description": "LLM-powered analytics assistant."
}
```

**Response** (201 Created): the created project, including `id`, `created_at`, `updated_at`.

**Request Example**:
```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI Insights Engine",
    "customer": "Innovate Labs",
    "project_manager": "Marcus Reid",
    "status": "planning"
  }'
```

**Status Codes**:
- `201`: Created
- `422`: Validation error (blank required field, invalid status, `end_date` before `start_date`)

---

#### PUT /projects/{id}

**Description**: Full update of a project (all fields replaced)

**Validation**: same as `POST /projects`; project must exist.

**Request Body**:
```json
{
  "name": "AI Insights Engine v2",
  "customer": "Innovate Labs",
  "project_manager": "Marcus Reid",
  "status": "active",
  "start_date": "2026-08-01",
  "end_date": "2027-03-31",
  "description": "Expanded scope."
}
```

**Response** (200 OK): the updated project (`updated_at` is bumped).

**Status Codes**:
- `200`: Success
- `404`: Project not found
- `422`: Validation error

---

#### PATCH /projects/{id}/status

**Description**: Change only a project's status.

**Request Body**:
```json
{
  "status": "on_hold"
}
```

Allowed values: `planning`, `active`, `on_hold`, `completed`, `cancelled`

**Response** (200 OK): the updated project.

**Request Example**:
```bash
curl -X PATCH http://localhost:8000/projects/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "on_hold"}'
```

**Status Codes**:
- `200`: Success
- `404`: Project not found
- `422`: Invalid status value

---

#### DELETE /projects/{id}

**Status**: ❌ Not implemented (by design)

Consistent with engineers, projects are not hard-deleted. Use
`PATCH /projects/{id}/status` to mark a project `cancelled` or `completed`,
preserving historical portfolio data.

---

### Engineers Endpoints

#### GET /engineers

**Description**: Retrieve all engineers

**Authentication**: None (planned: Required)

**Parameters**: None

**Request**:
```bash
curl http://localhost:8000/engineers
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "name": "Alice Johnson",
    "email": "alice.johnson@stratos.ai",
    "role": "Senior Engineer",
    "status": "active",
    "project_id": 1
  },
  {
    "id": 2,
    "name": "Bob Chen",
    "email": "bob.chen@stratos.ai",
    "role": "Backend Engineer",
    "status": "active",
    "project_id": 1
  },
  ...
]
```

**Query Parameters** (Future):
```
GET /engineers?project_id=1&status=active&role=Backend%20Engineer&skip=0&limit=20
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | integer | No | Filter by project assignment |
| `status` | string | No | Filter by status (active, on_leave, inactive) |
| `role` | string | No | Filter by role/title |
| `skip` | integer | No | Number of records to skip |
| `limit` | integer | No | Maximum records to return |

---

#### POST /engineers

**Description**: Create a new engineer

**Authentication**: None (planned: Required)

**Validation**:
- `project_id` must reference an existing project
- `email` must be a valid, unique address
- `name` is required and cannot be blank
- `status` must be one of: `active`, `inactive`, `on_leave`

**Request Body**:
```json
{
  "name": "John Smith",
  "email": "john.smith@stratos.ai",
  "role": "Backend Engineer",
  "status": "active",
  "project_id": 1
}
```

**Response** (201 Created):
```json
{
  "id": 21,
  "name": "John Smith",
  "email": "john.smith@stratos.ai",
  "role": "Backend Engineer",
  "status": "active",
  "project_id": 1
}
```

**Request Example**:
```bash
curl -X POST http://localhost:8000/engineers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "email": "john.smith@stratos.ai",
    "role": "Backend Engineer",
    "status": "active",
    "project_id": 1
  }'
```

**Status Codes**:
- `201`: Created
- `400`: `project_id` does not exist
- `409`: Email already exists
- `422`: Validation error (blank name, invalid email, invalid status, missing field)

---

#### GET /engineers/{id}

**Description**: Retrieve specific engineer by ID

**Authentication**: None (planned: Required)

**Request**:
```bash
curl http://localhost:8000/engineers/1
```

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "Alice Johnson",
  "email": "alice.johnson@stratos.ai",
  "role": "Senior Engineer",
  "status": "active",
  "project_id": 1
}
```

**Status Codes**:
- `200`: Success
- `404`: Engineer not found

---

#### PUT /engineers/{id}

**Description**: Update engineer information (full replacement of all fields)

**Authentication**: None (planned: Required)

**Validation**:
- Engineer must exist
- `project_id` must reference an existing project
- `email` must be unique (excluding the engineer being updated)

**Request Body**:
```json
{
  "name": "Alice Johnson",
  "email": "alice.johnson@stratos.ai",
  "role": "Tech Lead",
  "status": "active",
  "project_id": 2
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "Alice Johnson",
  "email": "alice.johnson@stratos.ai",
  "role": "Tech Lead",
  "status": "active",
  "project_id": 2
}
```

**Request Example**:
```bash
curl -X PUT http://localhost:8000/engineers/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice.johnson@stratos.ai",
    "role": "Tech Lead",
    "status": "active",
    "project_id": 2
  }'
```

**Status Codes**:
- `200`: Success
- `400`: `project_id` does not exist
- `404`: Engineer not found
- `409`: Email already exists on another engineer
- `422`: Validation error

---

#### PATCH /engineers/{id}/status

**Description**: Change an engineer's status. Engineers are never physically deleted — this is the intended way to retire an engineer from active duty while preserving historical staffing data.

**Authentication**: None (planned: Required)

**Request Body**:
```json
{
  "status": "on_leave"
}
```

Allowed values: `active`, `inactive`, `on_leave`

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "Alice Johnson",
  "email": "alice.johnson@stratos.ai",
  "role": "Tech Lead",
  "status": "on_leave",
  "project_id": 2
}
```

**Request Example**:
```bash
curl -X PATCH http://localhost:8000/engineers/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "on_leave"}'
```

**Status Codes**:
- `200`: Success
- `404`: Engineer not found
- `422`: Invalid status value

---

#### DELETE /engineers/{id}

**Status**: ❌ Not implemented (by design)

**Description**: Intentionally not offered. Deleting engineer records would destroy historical staffing data. Use `PATCH /engineers/{id}/status` to mark an engineer `inactive` instead.

---

#### GET /projects/{project_id}/engineers

**Description**: Retrieve all engineers assigned to a given project

**Authentication**: None (planned: Required)

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | integer | Yes | Project ID |

**Request**:
```bash
curl http://localhost:8000/projects/1/engineers
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "name": "Alice Johnson",
    "email": "alice.johnson@stratos.ai",
    "role": "Senior Engineer",
    "status": "active",
    "project_id": 1
  },
  {
    "id": 2,
    "name": "Bob Chen",
    "email": "bob.chen@stratos.ai",
    "role": "Backend Engineer",
    "status": "active",
    "project_id": 1
  }
]
```

**Status Codes**:
- `200`: Success
- `404`: Project not found

---

### Dashboard Endpoints

Executive dashboard aggregations computed live from the database (no cached or
hardcoded values). All are read-only and require no path/query parameters.

#### GET /dashboard/summary

**Description**: Portfolio and team headline counts.

**Request**:
```bash
curl http://localhost:8000/dashboard/summary
```

**Response** (200 OK):
```json
{
  "total_projects": 3,
  "active_projects": 1,
  "planning_projects": 1,
  "on_hold_projects": 1,
  "completed_projects": 0,
  "cancelled_projects": 0,
  "total_engineers": 20,
  "active_engineers": 17,
  "inactive_engineers": 1
}
```

---

#### GET /dashboard/project-status

**Description**: Project counts grouped by status, for the status chart. Always
returns all five statuses in a stable order, including zero counts.

**Response** (200 OK):
```json
[
  { "status": "planning",  "label": "Planning",  "count": 1 },
  { "status": "active",    "label": "Active",    "count": 1 },
  { "status": "on_hold",   "label": "On Hold",   "count": 1 },
  { "status": "completed", "label": "Completed", "count": 0 },
  { "status": "cancelled", "label": "Cancelled", "count": 0 }
]
```

---

#### GET /dashboard/recent-projects

**Description**: The 5 most recently created projects (ordered by `created_at`
descending, then `id`). Returns full project objects (same shape as
`GET /projects`).

---

#### GET /dashboard/recent-engineers

**Description**: The 5 most recently added engineers. Because the engineers table
has no timestamp column, `id` descending is used as the proxy for recency. Returns
full engineer objects (same shape as `GET /engineers`).

**Status Codes** (all dashboard endpoints):
- `200`: Success
- `500`: Server error

---

### Analytics Endpoints (Future)

#### GET /analytics/portfolio

**Status**: 📋 Planned

**Description**: Get portfolio-level analytics

**Response**:
```json
{
  "total_projects": 3,
  "active_projects": 2,
  "total_budget": 2450000.0,
  "spent": 1200000.0,
  "remaining": 1250000.0,
  "engineers_count": 20,
  "utilization": 0.85,
  "on_time_delivery": 0.92
}
```

---

#### GET /analytics/project/{id}

**Status**: 📋 Planned

**Description**: Get project-specific analytics

---

#### POST /analytics/recommendations

**Status**: 📋 Planned

**Description**: Get AI-powered recommendations for project

---

#### GET /analytics/risks

**Status**: 📋 Planned

**Description**: Get identified project risks with AI assessment

---

### Database Testing

#### GET /db-test

**Description**: Test database connectivity

**Authentication**: None

**Request**:
```bash
curl http://localhost:8000/db-test
```

**Response** (200 OK):
```json
{
  "database": "PostgreSQL 15.1 on x86_64-pc-linux-gnu, ..."
}
```

**Use Case**: Debugging, deployment verification, health monitoring

---

## Request/Response Formats

### Request Headers

**Common Headers**:
```
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token>        (future)
X-API-Key: <key>                     (future)
User-Agent: YourApp/1.0
```

### Response Headers

**Standard Response Headers**:
```
Content-Type: application/json
Content-Length: 1234
Date: Wed, 22 Jul 2026 10:30:00 GMT
X-RateLimit-Limit: 1000              (future)
X-RateLimit-Remaining: 999           (future)
X-RateLimit-Reset: 1629792000        (future)
```

### Request Body Schema

**Project Create**:
```json
{
  "name": "string (required, non-blank)",
  "customer": "string (required, non-blank)",
  "project_manager": "string (required, non-blank)",
  "status": "string (planning|active|on_hold|completed|cancelled; default planning)",
  "start_date": "date YYYY-MM-DD (optional)",
  "end_date": "date YYYY-MM-DD (optional, >= start_date)",
  "description": "string (optional)"
}
```

**Engineer Create**:
```json
{
  "name": "string (required, 1-255 chars)",
  "email": "string (required, valid email)",
  "role": "string (required)",
  "status": "string (required: active|on_leave|inactive)",
  "project_id": "integer (required)"
}
```

### Response Body Schema

**Paginated Response** (Future):
```json
{
  "data": [
    {
      "id": 1,
      ...
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 10,
    "total": 100,
    "has_more": true
  }
}
```

---

## Status Codes

### 2xx Success

| Code | Meaning | Usage |
|------|---------|-------|
| `200` | OK | Successful GET, PUT request |
| `201` | Created | Successful POST request |
| `204` | No Content | Successful DELETE request |

### 4xx Client Error

| Code | Meaning | Usage |
|------|---------|-------|
| `400` | Bad Request | Invalid parameters or body |
| `401` | Unauthorized | Missing/invalid credentials |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Resource already exists |
| `422` | Validation Error | Invalid data format |
| `429` | Rate Limited | Too many requests |

### 5xx Server Error

| Code | Meaning | Usage |
|------|---------|-------|
| `500` | Internal Error | Unexpected server error |
| `503` | Unavailable | Service temporarily down |

---

## Webhooks (Future)

**Status**: 📋 Planned

Webhooks allow receiving notifications when events occur:

```json
{
  "event": "project.created",
  "timestamp": "2026-07-22T10:30:00Z",
  "data": {
    "id": 4,
    "name": "New Project"
  }
}
```

---

## Rate Limiting & Quotas (Future)

### Rate Limit Tiers

| Tier | Requests/Hour | Concurrent |
|------|---------------|-----------|
| Free | 100 | 5 |
| Pro | 1,000 | 25 |
| Enterprise | Unlimited | Unlimited |

---

## Best Practices

### 1. Use Pagination for Large Datasets
```bash
# Instead of fetching all 1000 engineers
curl http://localhost:8000/engineers?skip=0&limit=10
curl http://localhost:8000/engineers?skip=10&limit=10
```

### 2. Handle Errors Gracefully
```python
response = requests.get('http://localhost:8000/projects/999')
if response.status_code == 404:
    print("Project not found")
elif response.status_code >= 500:
    print("Server error, retry later")
```

### 3. Cache Results When Appropriate
```python
# Cache project list for 5 minutes
cache = {}
if 'projects' not in cache or cache['projects_time'] < time.time() - 300:
    cache['projects'] = requests.get('http://localhost:8000/projects').json()
    cache['projects_time'] = time.time()
```

### 4. Use Appropriate HTTP Methods
```bash
GET     /projects          # Retrieve
POST    /projects          # Create
PUT     /projects/1        # Update entire resource
PATCH   /projects/1        # Partial update (not implemented)
DELETE  /projects/1        # Delete
```

### 5. Filter and Sort on Server
```bash
# Let server handle filtering/sorting
GET /engineers?project_id=1&status=active&sort_by=name

# Not: Fetch all engineers and filter in client
GET /engineers  # ❌ Inefficient
```

---

## Integration Examples

### Python (requests)
```python
import requests

# Get all projects
response = requests.get('http://localhost:8000/projects')
projects = response.json()

# Create new engineer (future)
new_engineer = {
    "name": "Jane Doe",
    "email": "jane.doe@stratos.ai",
    "role": "Full Stack Engineer",
    "status": "active",
    "project_id": 1
}
response = requests.post(
    'http://localhost:8000/engineers',
    json=new_engineer
)
```

### JavaScript/Node.js
```javascript
// Get projects
fetch('http://localhost:8000/projects')
  .then(res => res.json())
  .then(projects => console.log(projects));

// Create engineer (future)
fetch('http://localhost:8000/engineers', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Jane Doe',
    email: 'jane.doe@stratos.ai',
    role: 'Frontend Engineer',
    status: 'active',
    project_id: 1
  })
})
```

### cURL
```bash
# Get projects
curl http://localhost:8000/projects

# Get engineers
curl http://localhost:8000/engineers

# Test database
curl http://localhost:8000/db-test
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and breaking changes.

---

## Support & Contact

**Documentation**: [API Docs](http://localhost:8000/docs)
**Interactive Docs**: [Swagger UI](http://localhost:8000/docs)
**Alternative Docs**: [ReDoc](http://localhost:8000/redoc)

**Issues**: Report via GitHub Issues
**Email**: support@stratos-ai.com (future)

---

## API Roadmap

- ✅ GET /projects - Implemented
- ✅ GET /engineers - Implemented
- ✅ GET /engineers/{id} - Implemented
- ✅ POST /engineers - Implemented
- ✅ PUT /engineers/{id} - Implemented
- ✅ PATCH /engineers/{id}/status - Implemented
- ❌ DELETE /engineers/{id} - Not planned (soft status management instead)
- ✅ GET /projects/{project_id}/engineers - Implemented
- ✅ GET / - Implemented
- ✅ GET /db-test - Implemented
- ✅ GET /projects/{id} - Implemented
- ✅ POST /projects - Implemented
- ✅ PUT /projects/{id} - Implemented
- ✅ PATCH /projects/{id}/status - Implemented
- ❌ DELETE /projects/{id} - Not planned (soft status management instead)
- ✅ GET /dashboard/summary - Implemented
- ✅ GET /dashboard/project-status - Implemented
- ✅ GET /dashboard/recent-projects - Implemented
- ✅ GET /dashboard/recent-engineers - Implemented
- 📋 Analytics endpoints - Planned
- 📋 WebSocket real-time updates - Planned
- 📋 GraphQL API - Planned
- 📋 Webhook system - Planned
