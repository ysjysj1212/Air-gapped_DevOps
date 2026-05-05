# System Architecture

## Overview

This system generates CI/CD pipeline configurations on-demand using a local LLM (Ollama). It exposes a REST API built with Flask and runs entirely inside Docker containers, making it suitable for air-gapped environments.

## Component Diagram

```
Client
  │
  ▼ HTTP
Flask API (src/app.py)
  ├── LLM Service (src/llm_service.py) ──► Ollama :11434
  ├── Template Generator (src/template_generator.py)
  ├── Validators (src/validators.py)
  └── Sandbox Service (src/sandbox_service.py) ──► Docker daemon
```

## Components

### Flask API (`src/app.py`)

Entry point for all HTTP requests. Orchestrates the pipeline between the LLM service, template generator, and validators.

### LLM Service (`src/llm_service.py`)

Wraps the Ollama `/api/generate` endpoint. Handles connection errors gracefully so the API can fall back to static templates when Ollama is unavailable.

### Template Generator (`src/template_generator.py`)

Produces GitHub Actions and GitLab CI YAML from Jinja2 templates. Supports Python, Node.js, Java, and Go out of the box.

### Validators (`src/validators.py`)

Validates arbitrary YAML strings and checks GitHub Actions pipeline structure (required fields: `name`, `on`, `jobs`).

### Sandbox Service (`src/sandbox_service.py`)

Optional Docker-based sandbox for safe pipeline validation. Degrades gracefully when Docker is unavailable.

## Data Flow

1. Client POSTs `project_description` + `language` to `/api/generate-ci`.
2. App builds a prompt and calls Ollama.
3. LLM response is validated; if invalid, a static template is used instead.
4. The final YAML is returned to the client.

## Deployment

Run all services with Docker Compose:

```bash
docker-compose up -d
```

Services:
- `app` – Flask API on port 5000
- `ollama` – Ollama LLM on port 11434
