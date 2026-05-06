# API Documentation

## Base URL
- Local: `http://localhost:5000`
- Production: `https://api.example.com`

## Authentication
Currently, no authentication is required. In production, consider adding JWT or API key authentication.

---

## Health Endpoints

### GET /
**Status**: `200 OK`

Returns basic service information.

**Example:**
```bash
curl http://localhost:5000/
```

**Response:**
```json
{
  "status": "healthy",
  "service": "CI/CD Pipeline Generator",
  "version": "1.0.0"
}
```

### GET /health
**Status**: `200 OK`

Returns detailed health information including timestamp.

**Example:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "CI/CD Pipeline Generator",
  "timestamp": "2024-05-06T14:00:00Z"
}
```

---

## YAML Generation Endpoints

### POST /api/generate-yaml

Generate CI/CD YAML configuration from requirements.

**Request Body:**
```json
{
  "requirements": "build, test, deploy",
  "language": "python",
  "project_name": "my-project",
  "ci_type": "github_actions",
  "use_llm": false
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| requirements | string | Yes | - | Pipeline requirements (e.g., "build, test, deploy") |
| language | string | No | python | Programming language (python, javascript, java, go, ruby) |
| project_name | string | No | my-project | Name of the project |
| ci_type | string | No | github_actions | CI/CD type (github_actions, gitlab_ci) |
| use_llm | boolean | No | false | Use LLM for enhanced generation |

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/generate-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "build, test, deploy",
    "language": "python",
    "project_name": "data-pipeline",
    "ci_type": "github_actions"
  }'
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "yaml": "name: data-pipeline\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: echo 'Building...'",
  "ci_type": "github_actions",
  "language": "python",
  "project_name": "data-pipeline",
  "use_llm": false
}
```

**Response (Error - 400):**
```json
{
  "status": "error",
  "error": "requirements is required"
}
```

**Response (Error - 500):**
```json
{
  "status": "error",
  "error": "Failed to generate YAML"
}
```

---

## YAML Validation Endpoints

### POST /api/validate-yaml

Validate CI/CD YAML configuration.

**Request Body:**
```json
{
  "yaml": "name: Test\non: push\njobs: {...}",
  "ci_type": "github_actions"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| yaml | string | Yes | - | YAML content to validate |
| ci_type | string | No | auto | CI type (auto, github_actions, gitlab_ci) |

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/validate-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "yaml": "name: Test Pipeline\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo test",
    "ci_type": "github_actions"
  }'
```

**Response (Valid - 200):**
```json
{
  "status": "success",
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "error_count": 0,
  "warning_count": 0,
  "suggestions": []
}
```

**Response (Invalid - 400):**
```json
{
  "status": "invalid",
  "is_valid": false,
  "errors": [
    "Missing required section: 'name:'",
    "Workflow must have a name"
  ],
  "warnings": [],
  "error_count": 2,
  "warning_count": 0,
  "suggestions": [
    "Add 'name: <workflow-name>' at the top of the file"
  ]
}
```

**Response (Error - 400):**
```json
{
  "error": "yaml is required"
}
```

---

## Ollama Integration Endpoints

### GET /api/ollama/health

Check Ollama service availability.

**Example:**
```bash
curl http://localhost:5000/api/ollama/health
```

**Response (Available):**
```json
{
  "status": "available",
  "message": "Ollama service is healthy",
  "url": "http://localhost:11434"
}
```

**Response (Unavailable):**
```json
{
  "status": "unavailable",
  "message": "Ollama service is not responding",
  "url": "http://localhost:11434"
}
```

### GET /api/ollama/models

List available Ollama models.

**Example:**
```bash
curl http://localhost:5000/api/ollama/models
```

**Response (Success):**
```json
{
  "status": "success",
  "models": [
    "llama2",
    "mistral",
    "neural-chat"
  ],
  "count": 3
}
```

**Response (Service Unavailable - 503):**
```json
{
  "status": "error",
  "error": "Ollama service is not available"
}
```

### POST /api/ollama/ask

Send a prompt to Ollama and get a response.

**Request Body:**
```json
{
  "prompt": "Generate a CI/CD pipeline for Python project",
  "model": "llama2"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| prompt | string | Yes | - | Prompt to send to LLM |
| model | string | No | llama2 | Model name to use |

**Example:**
```bash
curl -X POST http://localhost:5000/api/ollama/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a build pipeline",
    "model": "llama2"
  }'
```

**Response (Success):**
```json
{
  "status": "success",
  "response": "Here's a comprehensive build pipeline...",
  "model": "llama2",
  "processing_time": 2.345
}
```

**Response (Error - 503):**
```json
{
  "status": "error",
  "error": "Ollama service is not available"
}
```

---

## Error Responses

### 400 Bad Request
Returned when:
- Required parameters are missing
- Invalid parameter values
- Malformed JSON

Example:
```json
{
  "error": "Invalid request",
  "details": "Parameter 'requirements' is required"
}
```

### 404 Not Found
Returned when endpoint doesn't exist.

Example:
```json
{
  "error": "Endpoint not found",
  "path": "/api/unknown"
}
```

### 500 Internal Server Error
Returned when server encounters an error.

Example:
```json
{
  "status": "error",
  "error": "Internal server error occurred"
}
```

### 503 Service Unavailable
Returned when Ollama service is not available.

Example:
```json
{
  "status": "error",
  "error": "Ollama service is not available"
}
```

---

## Response Format

All responses are in JSON format with the following structure:

**Success Response:**
```json
{
  "status": "success",
  "data": {}
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Error message",
  "details": "Additional details (optional)"
}
```

**Validation Response:**
```json
{
  "is_valid": true/false,
  "errors": [],
  "warnings": [],
  "suggestions": []
}
```

---

## Rate Limiting

Currently, there are no rate limits. In production, consider implementing:
- Per-IP rate limiting
- Per-user rate limiting
- Concurrent request limits

---

## Pagination

Currently, no endpoints support pagination. If needed in the future:
- Use `page` and `limit` query parameters
- Return `total_count` and `page_count` in response

---

## Examples

### Example 1: Generate GitHub Actions YAML

**Request:**
```bash
curl -X POST http://localhost:5000/api/generate-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "lint, build, test",
    "language": "python",
    "project_name": "web-app",
    "ci_type": "github_actions"
  }'
```

**Response:**
```json
{
  "status": "success",
  "yaml": "name: web-app\non:\n  push:\n    branches: [main]\njobs:\n  lint:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: pip install flake8\n      - run: flake8 .\n  build:\n    runs-on: ubuntu-latest\n    needs: lint\n    steps:\n      - uses: actions/checkout@v3\n      - run: pip install -r requirements.txt\n  test:\n    runs-on: ubuntu-latest\n    needs: build\n    steps:\n      - uses: actions/checkout@v3\n      - run: pip install pytest\n      - run: pytest",
  "ci_type": "github_actions",
  "language": "python",
  "project_name": "web-app",
  "use_llm": false
}
```

### Example 2: Validate Generated YAML

**Request:**
```bash
curl -X POST http://localhost:5000/api/validate-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "yaml": "name: web-app\non:\n  push:\n    branches: [main]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: pytest",
    "ci_type": "auto"
  }'
```

**Response:**
```json
{
  "status": "success",
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "error_count": 0,
  "warning_count": 0,
  "suggestions": []
}
```

### Example 3: Use LLM for Enhanced Generation

**Request:**
```bash
curl -X POST http://localhost:5000/api/generate-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "linting, testing, security scan, docker build, push to registry",
    "language": "python",
    "project_name": "microservice",
    "ci_type": "gitlab_ci",
    "use_llm": true
  }'
```

**Response:**
```json
{
  "status": "success",
  "yaml": "... (LLM-enhanced YAML with more sophisticated pipeline)",
  "ci_type": "gitlab_ci",
  "language": "python",
  "project_name": "microservice",
  "use_llm": true
}
```

---

## Performance Metrics

### Response Times (Approximate)

| Endpoint | Time | Notes |
|----------|------|-------|
| GET / | < 10ms | Lightweight response |
| GET /health | < 10ms | Lightweight response |
| POST /api/generate-yaml | 50-200ms | Template-based |
| POST /api/generate-yaml (LLM) | 2-10s | Depends on Ollama |
| POST /api/validate-yaml | 20-100ms | Regex-based validation |
| GET /api/ollama/health | 200-500ms | Depends on network |
| POST /api/ollama/ask | 2-30s | Depends on model |

---

## Best Practices

1. **Error Handling**: Always check the `status` field in responses
2. **Validation**: Validate YAML after generation before using
3. **Caching**: Cache generated YAML for identical requirements
4. **Timeouts**: Set appropriate timeouts for LLM requests (30s recommended)
5. **Monitoring**: Log all requests in production for debugging

---

## Support & Feedback

For issues, questions, or feedback:
- Open an issue on GitHub: https://github.com/ysjysj1212/Air-gapped_DevOps/issues
- Check existing documentation: https://github.com/ysjysj1212/Air-gapped_DevOps/wiki

---

**Last Updated**: 2024-05-06  
**Version**: 1.0.0
