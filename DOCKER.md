# Docker Deployment Guide

## Overview
The CI/CD Pipeline Generator can be deployed using Docker for easy containerization and deployment.

## Components

### 1. Dockerfile
Multi-stage build Dockerfile that:
- Uses Python 3.11 slim base image
- Installs dependencies in builder stage
- Copies built packages to final image
- Runs as non-root user (appuser)
- Includes health checks
- Exposes port 5000

### 2. docker-compose.yml
Defines two services:
- **api**: The Flask CI/CD Pipeline Generator
  - Port: 5000
  - Volume mounts for src and tests
  - Health checks enabled
  - Auto-restart on failure

- **ollama** (optional): LLM service for enhanced YAML generation
  - Port: 11434
  - Persistent volume for models
  - Requires manual model pulling

### 3. .dockerignore
Optimizes build context by excluding unnecessary files

## Building the Image

### Prerequisites
- Docker installed and running
- Docker Desktop (recommended for Windows/Mac)

### Build Command
```bash
docker build -t ci-pipeline-generator:1.0 -f Dockerfile .
```

### Build Output
```
Step 1/X : FROM python:3.11-slim as builder
...
Successfully built <image_id>
Successfully tagged ci-pipeline-generator:1.0
```

## Running the Container

### Single Container (API Only)
```bash
docker run -d -p 5000:5000 ci-pipeline-generator:1.0
```

### Docker Compose (API + Optional Ollama)
```bash
docker-compose up -d
```

### Verify Container is Running
```bash
docker ps
```

## Testing the Container

### Health Check
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "CI/CD Pipeline Generator",
  "timestamp": "..."
}
```

### Generate YAML Endpoint
```bash
curl -X POST http://localhost:5000/api/generate-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "build, test, deploy",
    "language": "python",
    "ci_type": "github_actions"
  }'
```

### Validate YAML Endpoint
```bash
curl -X POST http://localhost:5000/api/validate-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "yaml": "name: Test\non: push\njobs: ...",
    "ci_type": "github_actions"
  }'
```

## Using docker-compose with Ollama

### Pull Ollama Model
After starting the service:
```bash
docker exec ollama-service ollama pull llama2
```

### Use LLM Features
```bash
curl -X POST http://localhost:5000/api/generate-yaml \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "build, test, deploy",
    "language": "python",
    "ci_type": "github_actions",
    "use_llm": true
  }'
```

## Environment Variables

### API Container
- `FLASK_ENV=production` - Production environment
- `FLASK_APP=src/app.py` - Flask app entry point
- `PYTHONUNBUFFERED=1` - Unbuffered Python output

### Ollama Container
- `OLLAMA_HOST=0.0.0.0:11434` - Listen on all interfaces

## Container Logs

### View API Logs
```bash
docker logs ci-pipeline-generator
```

### Stream Logs
```bash
docker logs -f ci-pipeline-generator
```

### View Ollama Logs
```bash
docker logs ollama-service
```

## Stopping Containers

### Stop Single Container
```bash
docker stop ci-pipeline-generator
```

### Stop All Services (docker-compose)
```bash
docker-compose down
```

### Remove Images
```bash
docker rmi ci-pipeline-generator:1.0
```

## Performance Considerations

### Image Size
- Builder stage reduces final image size
- Multi-stage build removes build dependencies
- Python slim base image (~150MB)
- Final image: ~200-250MB (without models)

### Health Checks
- Interval: 30 seconds
- Timeout: 10 seconds
- Start period: 5 seconds
- Retries: 3

### Volume Mounts
- `src` mounted read-only for production
- `tests` mounted for development/testing

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs ci-pipeline-generator

# Verify image exists
docker images | grep ci-pipeline-generator

# Rebuild image
docker build -t ci-pipeline-generator:1.0 .
```

### Port Already in Use
```bash
# Use different port
docker run -d -p 5001:5000 ci-pipeline-generator:1.0

# Or find and kill process on port 5000
lsof -i :5000
```

### Can't Connect to API
```bash
# Check if container is running
docker ps

# Check health status
docker inspect ci-pipeline-generator | grep -A 5 Health

# Try accessing from container
docker exec ci-pipeline-generator curl http://localhost:5000/health
```

## Production Deployment

### Recommended Settings
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    image: ci-pipeline-generator:1.0
    restart: always
    environment:
      - FLASK_ENV=production
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
      reservations:
        cpus: '0.25'
        memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t ci-pipeline-generator:${{ github.sha }} .
      
      - name: Run tests
        run: docker run --rm ci-pipeline-generator:${{ github.sha }} pytest
      
      - name: Push to registry
        run: |
          docker tag ci-pipeline-generator:${{ github.sha }} your-registry/ci-pipeline-generator:latest
          docker push your-registry/ci-pipeline-generator:latest
```

## Security Best Practices

1. **Non-root User**: Container runs as non-root user (appuser)
2. **Minimal Base Image**: Uses python:3.11-slim
3. **Read-only Volumes**: Production mounts are read-only
4. **Health Checks**: Enabled for container monitoring
5. **Resource Limits**: Set limits in production compose file
6. **Environment Isolation**: Use .env files for secrets

## Next Steps

1. Start Docker Desktop (if not already running)
2. Run `docker build -t ci-pipeline-generator:1.0 .`
3. Run `docker-compose up -d` to start services
4. Test endpoints with curl
5. Monitor logs with `docker logs -f`

## Support

For issues or questions, refer to:
- Docker Documentation: https://docs.docker.com
- Flask Documentation: https://flask.palletsprojects.com
- Ollama Documentation: https://ollama.ai
