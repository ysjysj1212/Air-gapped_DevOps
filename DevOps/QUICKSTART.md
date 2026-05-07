# Quick Start

이 문서는 **컨테이너 기반 데모 실행**을 가장 빠르게 재현하는 절차를 정리합니다.

## 1. 기본 데모 스택 실행

호스트 Ollama를 사용하는 기본 구성입니다.

```bash
cd DevOps
cp .env.example .env
docker pull node:20 python:3.10
docker compose up -d app gitlab gitlab-runner
```

포트 5000이 이미 사용 중이면 `.env`에서 `APP_PORT`만 바꾸면 됩니다.
DevOps MVP의 sandbox 검증은 호스트 Docker daemon을 사용하므로, `app` 서비스에 Docker socket이 마운트됩니다. 이 구성은 **PoC 전용**입니다.

확인:

```bash
docker compose ps
curl -s http://localhost:${APP_PORT:-5000}/health | jq .
curl -I http://localhost:8080/users/sign_in
```

접속 주소:

```text
Flask app: http://localhost:${APP_PORT:-5000}
GitLab:    http://localhost:8080
```

## 2. Ollama까지 컨테이너로 올리기

`.env`에서 Ollama URL을 내부 서비스명으로 바꿉니다:

```text
OLLAMA_URL=http://ollama:11434
```

그 다음:

```bash
docker compose --profile ollama up -d app ollama gitlab gitlab-runner
```

## 3. DevOps MVP 흐름 실행

가장 중요한 데모 경로입니다. 자연어 입력으로 GitLab CI 초안을 만들고, 구조 검증과 sandbox 검증을 한 번에 확인합니다.

```bash
curl -s http://localhost:${APP_PORT:-5000}/api/devops/gitlab/verify \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Node.js 프로젝트용 GitLab CI YAML을 만들어줘. Docker sandbox에서 검증 가능한 단순 단계로 구성해줘.",
    "use_llm": false
  }' | jq .
```

응답에서 확인할 필드:

- `yaml`
- `validation.is_valid`
- `safety.is_safe`
- `sandbox.passed`
- `sandbox.jobs[].stdout`

입력 문장은 꼭 한 가지 형식일 필요는 없습니다. 아래처럼 달라도 같은 검증 흐름으로 들어갑니다.

```text
Node.js 프로젝트용 GitLab CI YAML을 만들어줘.
Python 앱인데 네트워크 없이 검증 가능한 초안이 필요해.
테스트만 있는 간단한 GitLab CI를 만들어줘.
```

Spring Boot/Java처럼 `node:20`, `python:3.10` 밖의 이미지를 요구하는 입력은 YAML 초안과 구조/위험 명령 검사까지 수행하고, sandbox 실행은 MVP 범위 밖으로 표시합니다.

## 4. YAML 생성 예시

```bash
curl -s http://localhost:${APP_PORT:-5000}/api/generate-yaml \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Python Flask API with pytest and GitLab CI",
    "ci_type": "gitlab_ci",
    "use_llm": false
  }' | jq .
```

## 5. YAML 검증 예시

```bash
curl -s http://localhost:${APP_PORT:-5000}/api/validate-yaml \
  -H 'Content-Type: application/json' \
  -d '{
    "yaml": "stages:\n  - build\nbuild:\n  stage: build\n  script:\n    - echo hi\n",
    "ci_type": "gitlab_ci"
  }' | jq .
```

## 6. GitLab PoC 검증

Runner 등록과 clone URL/network_mode 보정은 아래 문서를 따릅니다:

```text
docs/register-runner.md
```

이미 등록된 환경이라면 샘플 CI 파일을 프로젝트에 반영해 바로 시연할 수 있습니다:

```text
ci-samples/basic-success.gitlab-ci.yml
ci-samples/.gitlab-ci.yml
ci-samples/failure-network-blocked.gitlab-ci.yml
```

## 7. 종료

```bash
docker compose down
```
