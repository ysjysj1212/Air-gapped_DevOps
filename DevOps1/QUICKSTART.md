# Quick Start

## Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Ollama (optional for LLM-powered generation)

## Run locally without Docker

```bash
cd DevOps1
pip install -r requirements.txt

# Start the Flask development server
FLASK_APP=src/app.py flask run
```

Open `http://localhost:5000/health` to verify the server is running.

## Run with Docker Compose

```bash
cd DevOps1
docker-compose up -d
```

This starts:
- The Flask API on **port 5000**
- The Ollama LLM service on **port 11434**

## Generate a pipeline

```bash
curl -s -X POST http://localhost:5000/api/generate-ci \
  -H "Content-Type: application/json" \
  -d '{"project_description": "Python Flask API", "language": "python"}' \
  | python3 -m json.tool
```

## Run tests

```bash
cd DevOps1
pytest tests/
```
