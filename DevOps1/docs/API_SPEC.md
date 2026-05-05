# API Specification

## Base URL

```
http://localhost:5000
```

---

## Endpoints

### GET /

Returns basic API metadata.

**Response 200**

```json
{
  "message": "CI/CD Pipeline Generator API",
  "version": "1.0.0"
}
```

---

### GET /health

Returns the health status of the API and its dependent services.

**Response 200**

```json
{
  "status": "healthy",
  "services": {
    "flask": "running",
    "docker": "connected",
    "ollama": "http://localhost:11434"
  }
}
```

---

### POST /api/generate-ci

Generate a CI/CD pipeline YAML from a natural language project description.

**Request body (JSON)**

| Field                 | Type     | Required | Description                          |
| --------------------- | -------- | -------- | ------------------------------------ |
| `project_description` | `string` | Yes      | Free-text description of the project |
| `language`            | `string` | No       | `python` (default), `nodejs`, `java`, `go` |
| `requirements`        | `array`  | No       | List of CI requirement strings       |

**Example request**

```json
{
  "project_description": "Node.js Express REST API",
  "language": "nodejs",
  "requirements": ["unit tests", "lint"]
}
```

**Response 200**

```json
{
  "status": "success",
  "pipeline": "name: CI\n...",
  "format": "github_actions"
}
```

**Response 400** – missing `project_description`

```json
{
  "status": "error",
  "message": "project_description is required"
}
```
