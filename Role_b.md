# Role B — API 구현 단계별 가이드

> **프로젝트**: CI/CD 파이프라인 자동 생성 시스템  
> **역할**: Role B (백엔드 API 개발자)  
> **경로**: `DevOps1/`

---

## 목차

1. [환경 설정](#1-환경-설정)
2. [Flask 애플리케이션 진입점 구현 (app.py)](#2-flask-애플리케이션-진입점-구현-apppy)
3. [LLM 서비스 구현 (llm_service.py)](#3-llm-서비스-구현-llm_servicepy)
4. [템플릿 생성기 구현 (template_generator.py)](#4-템플릿-생성기-구현-template_generatorpy)
5. [YAML 검증기 구현 (validators.py)](#5-yaml-검증기-구현-validatorspy)
6. [샌드박스 서비스 구현 (sandbox_service.py)](#6-샌드박스-서비스-구현-sandbox_servicepy)
7. [CI/CD 템플릿 파일 작성](#7-cicd-템플릿-파일-작성)
8. [Docker 설정 파일 작성](#8-docker-설정-파일-작성)
9. [테스트 작성 (test_api.py)](#9-테스트-작성-test_apipy)
10. [통합 실행 및 검증](#10-통합-실행-및-검증)

---

## 1. 환경 설정

### 1-1. Python 의존성 설치

```bash
cd DevOps1
pip install -r requirements.txt
```

`requirements.txt` 에 이미 선언된 라이브러리:

| 라이브러리 | 용도 |
|---|---|
| Flask | 웹 API 서버 |
| Werkzeug | WSGI 유틸리티 |
| PyYAML | YAML 파싱/생성 |
| python-dotenv | 환경 변수 관리 |
| docker | Docker SDK |
| requests | HTTP 클라이언트 (Ollama 호출) |
| yamllint | YAML 린트 검증 |
| Jinja2 | 템플릿 렌더링 |
| pytest / pytest-cov | 테스트 |

### 1-2. 환경 변수 파일 생성

프로젝트 루트(`DevOps1/`)에 `.env` 파일을 생성합니다.

```dotenv
FLASK_APP=src/app.py
FLASK_ENV=development
FLASK_DEBUG=1
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
DOCKER_HOST=unix:///var/run/docker.sock
```

> **참고**: `.gitignore` 에 `.env`가 이미 포함되어 있는지 확인하세요.

### 1-3. Ollama 설치 및 모델 다운로드 (로컬 실행 시)

```bash
# Ollama 설치 (Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# 모델 다운로드 (예: llama3)
ollama pull llama3

# Ollama 서버 실행
ollama serve
```

---

## 2. Flask 애플리케이션 진입점 구현 (app.py)

**파일 경로**: `DevOps1/src/app.py`

### 구현 목표

- Flask 앱 초기화
- 환경 변수 로드 (python-dotenv)
- 블루프린트 또는 직접 라우트 등록
- 3개의 엔드포인트 노출:
  - `GET /` — 서버 상태 확인
  - `GET /health` — 서비스 헬스 체크
  - `POST /api/generate-ci` — CI/CD YAML 파이프라인 생성

### 구현 코드

```python
# DevOps1/src/app.py

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from llm_service import LLMService
from template_generator import TemplateGenerator
from validators import PipelineValidator
from sandbox_service import SandboxService

load_dotenv()

app = Flask(__name__)

llm_service = LLMService(
    ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
    model=os.getenv("OLLAMA_MODEL", "llama3"),
)
template_generator = TemplateGenerator(templates_dir=os.path.join(os.path.dirname(__file__), '..', 'templates'))
validator = PipelineValidator()
sandbox = SandboxService()


@app.route("/")
def index():
    return jsonify({"message": "Server Running!"}), 200


@app.route("/health")
def health():
    docker_ok = sandbox.is_available()
    ollama_ok = llm_service.is_available()
    return jsonify({
        "status": "healthy" if docker_ok and ollama_ok else "degraded",
        "services": {
            "flask": "running",
            "docker": "connected" if docker_ok else "unavailable",
            "ollama": "available" if ollama_ok else "unavailable",
        }
    }), 200


@app.route("/api/generate-ci", methods=["POST"])
def generate_ci():
    data = request.get_json(force=True)

    project_description = data.get("project_description", "")
    language = data.get("language", "python")
    requirements = data.get("requirements", [])
    pipeline_format = data.get("format", "github_actions")  # github_actions | gitlab_ci

    if not project_description:
        return jsonify({"status": "error", "message": "project_description is required"}), 400

    # 1. LLM으로 파이프라인 스펙 생성
    spec = llm_service.generate_pipeline_spec(
        project_description=project_description,
        language=language,
        requirements=requirements,
    )

    # 2. 스펙을 YAML 템플릿에 채워 넣기
    pipeline_yaml = template_generator.render(spec=spec, pipeline_format=pipeline_format)

    # 3. YAML 유효성 검증
    errors = validator.validate(pipeline_yaml)
    if errors:
        return jsonify({"status": "error", "message": "Validation failed", "errors": errors}), 422

    return jsonify({
        "status": "success",
        "pipeline": pipeline_yaml,
        "format": pipeline_format,
    }), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
```

### 검증 방법

```bash
cd DevOps1/src
python app.py
# 브라우저 또는 curl로 확인
curl http://localhost:5000/
curl http://localhost:5000/health
```

---

## 3. LLM 서비스 구현 (llm_service.py)

**파일 경로**: `DevOps1/src/llm_service.py`

### 구현 목표

- Ollama REST API(`/api/generate`)를 통해 자연어 → CI/CD 스펙 딕셔너리로 변환
- 응답 파싱 및 구조화
- Ollama 연결 가용성 확인 메서드 제공

### Ollama API 호출 규격

```
POST http://localhost:11434/api/generate
Content-Type: application/json

{
  "model": "llama3",
  "prompt": "<프롬프트>",
  "stream": false
}
```

응답:
```json
{
  "response": "<LLM 생성 텍스트>"
}
```

### 구현 코드

```python
# DevOps1/src/llm_service.py

import json
import requests


PROMPT_TEMPLATE = """
You are a DevOps expert. Given the following project information, generate a CI/CD pipeline specification as a JSON object.

Project Description: {project_description}
Programming Language: {language}
Requirements: {requirements}

Return ONLY a valid JSON object with the following keys:
- "language": string
- "steps": list of strings (e.g. ["install", "test", "build", "deploy"])
- "env_vars": dict of required environment variables (name -> description)
- "docker_image": string (base Docker image to use)
- "artifacts": list of output artifact paths

Respond with JSON only, no explanation.
"""


class LLMService:
    def __init__(self, ollama_url: str, model: str):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def generate_pipeline_spec(self, project_description: str, language: str, requirements: list) -> dict:
        prompt = PROMPT_TEMPLATE.format(
            project_description=project_description,
            language=language,
            requirements=", ".join(requirements) if requirements else "없음",
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        resp = requests.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()

        raw_text = resp.json().get("response", "")
        return self._parse_json_response(raw_text)

    def _parse_json_response(self, text: str) -> dict:
        # JSON 블록 추출 (```json ... ``` 형식도 처리)
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 파싱 실패 시 기본값 반환
            return {
                "language": "python",
                "steps": ["install", "test", "build"],
                "env_vars": {},
                "docker_image": "python:3.11-slim",
                "artifacts": [],
            }
```

### 검증 방법

```python
from llm_service import LLMService
svc = LLMService("http://localhost:11434", "llama3")
print(svc.is_available())
spec = svc.generate_pipeline_spec("FastAPI 프로젝트", "python", ["테스트", "빌드"])
print(spec)
```

---

## 4. 템플릿 생성기 구현 (template_generator.py)

**파일 경로**: `DevOps1/src/template_generator.py`

### 구현 목표

- `templates/github_actions.yaml` 또는 `templates/gitlab_ci.yaml` Jinja2 템플릿 로드
- LLM이 반환한 스펙 딕셔너리를 템플릿에 삽입하여 최종 YAML 문자열 반환

### 구현 코드

```python
# DevOps1/src/template_generator.py

import os
from jinja2 import Environment, FileSystemLoader


FORMAT_TO_TEMPLATE = {
    "github_actions": "github_actions.yaml",
    "gitlab_ci": "gitlab_ci.yaml",
}


class TemplateGenerator:
    def __init__(self, templates_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(os.path.abspath(templates_dir)),
            autoescape=False,
        )

    def render(self, spec: dict, pipeline_format: str) -> str:
        template_file = FORMAT_TO_TEMPLATE.get(pipeline_format)
        if not template_file:
            raise ValueError(f"Unsupported pipeline format: {pipeline_format}")

        template = self.env.get_template(template_file)
        return template.render(**spec)
```

---

## 5. YAML 검증기 구현 (validators.py)

**파일 경로**: `DevOps1/src/validators.py`

### 구현 목표

- `yamllint` 라이브러리로 YAML 문법 오류 탐지
- `PyYAML`로 필수 키 존재 여부 확인 (형식별 필수 필드 검증)
- 오류 목록 반환 (없으면 빈 리스트)

### 구현 코드

```python
# DevOps1/src/validators.py

import yaml
from yamllint import linter
from yamllint.config import YamlLintConfig


YAMLLINT_CONFIG = YamlLintConfig("""
extends: default
rules:
  line-length:
    max: 200
  truthy:
    allowed-values: ['true', 'false', 'on', 'off']
""")


class PipelineValidator:
    def validate(self, pipeline_yaml: str) -> list:
        errors = []

        # 1. yamllint 문법 검사
        lint_errors = list(linter.run(pipeline_yaml, YAMLLINT_CONFIG))
        for problem in lint_errors:
            if problem.level == "error":
                errors.append(f"Line {problem.line}: {problem.message}")

        # 2. PyYAML 파싱 확인
        try:
            parsed = yaml.safe_load(pipeline_yaml)
        except yaml.YAMLError as e:
            errors.append(f"YAML parse error: {e}")
            return errors

        # 3. 기본 구조 확인
        if not isinstance(parsed, dict):
            errors.append("Pipeline YAML must be a mapping (dict) at the top level")

        return errors
```

---

## 6. 샌드박스 서비스 구현 (sandbox_service.py)

**파일 경로**: `DevOps1/src/sandbox_service.py`

### 구현 목표

- Docker Python SDK로 Docker 데몬 연결
- `is_available()` — Docker 연결 상태 확인
- `run_pipeline(yaml_content)` — 격리 컨테이너에서 파이프라인 드라이런(dry-run) 실행 (선택 구현)

### 구현 코드

```python
# DevOps1/src/sandbox_service.py

import docker


class SandboxService:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception:
            self.client = None

    def is_available(self) -> bool:
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def run_pipeline(self, image: str, command: str, timeout: int = 60) -> dict:
        """
        격리된 Docker 컨테이너에서 명령 실행 후 결과 반환.
        Returns: {"exit_code": int, "logs": str}
        """
        if not self.is_available():
            return {"exit_code": -1, "logs": "Docker is not available"}

        try:
            container = self.client.containers.run(
                image=image,
                command=command,
                remove=True,
                stdout=True,
                stderr=True,
                detach=False,
                network_disabled=True,
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=50000,
            )
            logs = container.decode("utf-8") if isinstance(container, bytes) else str(container)
            return {"exit_code": 0, "logs": logs}
        except docker.errors.ContainerError as e:
            return {"exit_code": e.exit_status, "logs": e.stderr.decode("utf-8")}
        except Exception as e:
            return {"exit_code": -1, "logs": str(e)}
```

---

## 7. CI/CD 템플릿 파일 작성

### 7-1. GitHub Actions 템플릿

**파일 경로**: `DevOps1/templates/github_actions.yaml`

```yaml
name: CI Pipeline

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  ci:
    runs-on: ubuntu-latest
    container:
      image: {{ docker_image | default('python:3.11-slim') }}

    steps:
      - uses: actions/checkout@v4

      {% for step in steps %}
      - name: {{ step }}
        run: |
          echo "Running step: {{ step }}"
      {% endfor %}

      {% if artifacts %}
      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: |
            {% for artifact in artifacts %}
            {{ artifact }}
            {% endfor %}
      {% endif %}
```

### 7-2. GitLab CI 템플릿

**파일 경로**: `DevOps1/templates/gitlab_ci.yaml`

```yaml
image: {{ docker_image | default('python:3.11-slim') }}

stages:
  {% for step in steps %}
  - {{ step }}
  {% endfor %}

{% for step in steps %}
{{ step }}:
  stage: {{ step }}
  script:
    - echo "Running stage: {{ step }}"
{% endfor %}

{% if artifacts %}
artifacts:
  paths:
    {% for artifact in artifacts %}
    - {{ artifact }}
    {% endfor %}
{% endif %}
```

---

## 8. Docker 설정 파일 작성

### 8-1. 메인 애플리케이션 Dockerfile

**파일 경로**: `DevOps1/docker/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY templates/ ./templates/

ENV FLASK_APP=src/app.py
ENV PYTHONPATH=/app/src

EXPOSE 5000

CMD ["python", "src/app.py"]
```

### 8-2. 검증 전용 Dockerfile

**파일 경로**: `DevOps1/docker/Dockerfile.validator`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir yamllint PyYAML

COPY src/validators.py ./validators.py

ENTRYPOINT ["python", "validators.py"]
```

### 8-3. Docker Compose 파일

**파일 경로**: `DevOps1/docker-compose.yml`

```yaml
version: "3.9"

services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "5000:5000"
    environment:
      - OLLAMA_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3
    depends_on:
      - ollama
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

---

## 9. 테스트 작성 (test_api.py)

**파일 경로**: `DevOps1/tests/test_api.py`

### 구현 목표

- Flask 테스트 클라이언트를 사용한 API 엔드포인트 단위 테스트
- LLM 서비스와 샌드박스 서비스는 mock 처리
- `pytest` 실행 시 커버리지 측정

### 구현 코드

```python
# DevOps1/tests/test_api.py

import json
import pytest
from unittest.mock import MagicMock, patch

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------- GET / ----------

def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Server Running!"


# ---------- GET /health ----------

def test_health_healthy(client):
    with patch("app.sandbox") as mock_sb, patch("app.llm_service") as mock_llm:
        mock_sb.is_available.return_value = True
        mock_llm.is_available.return_value = True
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["services"]["docker"] == "connected"
        assert data["services"]["ollama"] == "available"


def test_health_degraded(client):
    with patch("app.sandbox") as mock_sb, patch("app.llm_service") as mock_llm:
        mock_sb.is_available.return_value = False
        mock_llm.is_available.return_value = False
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "degraded"


# ---------- POST /api/generate-ci ----------

SAMPLE_SPEC = {
    "language": "python",
    "steps": ["install", "test", "build"],
    "env_vars": {},
    "docker_image": "python:3.11-slim",
    "artifacts": ["dist/"],
}

SAMPLE_YAML = """
name: CI Pipeline
on:
  push:
    branches: ["main"]
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""


def test_generate_ci_success(client):
    with patch("app.llm_service") as mock_llm, \
         patch("app.template_generator") as mock_tg, \
         patch("app.validator") as mock_val:

        mock_llm.generate_pipeline_spec.return_value = SAMPLE_SPEC
        mock_tg.render.return_value = SAMPLE_YAML
        mock_val.validate.return_value = []

        payload = {
            "project_description": "Python Flask 프로젝트",
            "language": "python",
            "requirements": ["테스트 자동화"],
            "format": "github_actions",
        }
        resp = client.post(
            "/api/generate-ci",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert "pipeline" in data
        assert data["format"] == "github_actions"


def test_generate_ci_missing_description(client):
    resp = client.post(
        "/api/generate-ci",
        data=json.dumps({"language": "python"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["status"] == "error"


def test_generate_ci_validation_failure(client):
    with patch("app.llm_service") as mock_llm, \
         patch("app.template_generator") as mock_tg, \
         patch("app.validator") as mock_val:

        mock_llm.generate_pipeline_spec.return_value = SAMPLE_SPEC
        mock_tg.render.return_value = "invalid: yaml: ["
        mock_val.validate.return_value = ["Line 1: syntax error"]

        payload = {
            "project_description": "테스트 프로젝트",
            "language": "python",
        }
        resp = client.post(
            "/api/generate-ci",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 422
        data = resp.get_json()
        assert data["status"] == "error"
        assert "errors" in data
```

### 테스트 실행

```bash
cd DevOps1
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## 10. 통합 실행 및 검증

### 10-1. 로컬 직접 실행 (개발 모드)

```bash
# 터미널 1: Ollama 실행
ollama serve

# 터미널 2: Flask 실행
cd DevOps1/src
python app.py
```

### 10-2. Docker Compose 실행 (권장)

```bash
cd DevOps1

# 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f app
```

### 10-3. API 동작 확인

```bash
# 서버 상태 확인
curl http://localhost:5000/

# 헬스 체크
curl http://localhost:5000/health

# CI/CD 파이프라인 생성 (GitHub Actions)
curl -X POST http://localhost:5000/api/generate-ci \
  -H "Content-Type: application/json" \
  -d '{
    "project_description": "Node.js Express API 프로젝트",
    "language": "nodejs",
    "requirements": ["테스트 자동화", "빌드 자동화", "Docker 이미지 배포"],
    "format": "github_actions"
  }'

# CI/CD 파이프라인 생성 (GitLab CI)
curl -X POST http://localhost:5000/api/generate-ci \
  -H "Content-Type: application/json" \
  -d '{
    "project_description": "Python FastAPI 백엔드",
    "language": "python",
    "requirements": ["유닛 테스트", "린트 검사"],
    "format": "gitlab_ci"
  }'
```

### 10-4. 전체 테스트 + 커버리지

```bash
cd DevOps1
pytest tests/ -v --cov=src --cov-report=html
# 결과: htmlcov/index.html 에서 커버리지 확인
```

---

## 구현 순서 요약 (체크리스트)

```
[ ] 1. 환경 설정 (.env 파일, pip install)
[ ] 2. templates/github_actions.yaml 작성
[ ] 3. templates/gitlab_ci.yaml 작성
[ ] 4. src/validators.py 구현 (YAML 검증)
[ ] 5. src/llm_service.py 구현 (Ollama 연동)
[ ] 6. src/template_generator.py 구현 (Jinja2 렌더링)
[ ] 7. src/sandbox_service.py 구현 (Docker SDK)
[ ] 8. src/app.py 구현 (Flask API 3개 엔드포인트)
[ ] 9. docker/Dockerfile 작성
[ ] 10. docker/Dockerfile.validator 작성
[ ] 11. docker-compose.yml 작성
[ ] 12. tests/test_api.py 작성 및 통과 확인
[ ] 13. docker-compose up --build 로 통합 동작 확인
[ ] 14. curl 로 /api/generate-ci 엔드포인트 최종 검증
```

> **권장 구현 순서**: 의존성이 낮은 것부터 구현합니다.  
> `validators` → `llm_service` → `template_generator` → `sandbox_service` → `app` → 테스트 → Docker

---

## 참고 자료

- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [Ollama API 레퍼런스](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Docker Python SDK 문서](https://docker-py.readthedocs.io/)
- [yamllint 문서](https://yamllint.readthedocs.io/)
- [Jinja2 템플릿 문서](https://jinja.palletsprojects.com/)
- [pytest 공식 문서](https://docs.pytest.org/)
