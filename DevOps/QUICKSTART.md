# Quick Start

이 문서는 **컨테이너 기반 데모 실행**을 가장 빠르게 재현하는 절차를 정리합니다.

## 1. 기본 데모 스택 실행

호스트 Ollama를 사용하는 기본 구성입니다.

```bash
cd DevOps
cp .env.example .env
docker compose up -d app gitlab gitlab-runner
```

포트 5000이 이미 사용 중이면 `.env`에서 `APP_PORT`만 바꾸면 됩니다.

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

## 3. YAML 생성 예시

```bash
curl -s http://localhost:${APP_PORT:-5000}/api/generate-yaml \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Python Flask API with pytest and GitLab CI",
    "ci_type": "gitlab_ci",
    "use_llm": false
  }' | jq .
```

## 4. YAML 검증 예시

```bash
curl -s http://localhost:${APP_PORT:-5000}/api/validate-yaml \
  -H 'Content-Type: application/json' \
  -d '{
    "yaml": "stages:\n  - build\nbuild:\n  stage: build\n  script:\n    - echo hi\n",
    "ci_type": "gitlab_ci"
  }' | jq .
```

## 5. GitLab PoC 검증

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

## 6. 종료

```bash
docker compose down
```
