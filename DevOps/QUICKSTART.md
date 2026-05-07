# Quick Start

이 문서는 **컨테이너 기반 데모 실행**을 가장 빠르게 재현하는 절차를 정리합니다.

## 1. 기본 데모 스택 실행 (루트 디렉토리)

```bash
cd /Users/gyubeom/Desktop/Air-gapped_DevOps

# 최신 코드 받기
git pull origin main

# 통합된 docker-compose로 시작 (Dev 환경)
docker-compose up -d

# 확인
docker-compose ps
curl -s http://localhost:5000/health | jq .
curl -I http://localhost:8080/users/sign_in
```

포트 5000이 이미 사용 중이면 `.env`에서 `APP_PORT`를 변경합니다.

접속 주소:
```text
Flask API:    http://localhost:5000
GitLab:       http://localhost:8080
```

## 2. Ollama + Gemma4 포함 시작 (폐쇄망 최적)

Gemma4 LLM을 포함한 이미지로 시작합니다:

```bash
# 첫 번째 빌드 (Gemma4 다운로드 포함, 시간 소요)
docker-compose --profile ollama up -d

# 또는 백그라운드 빌드
docker-compose --profile ollama build ollama
docker-compose --profile ollama up -d
```

확인:
```bash
docker-compose ps | grep ollama

# Gemma4 확인
curl http://localhost:11434/api/tags
```

## 3. DevOps MVP 흐름 실행

자연어 입력으로 GitLab CI 초안을 만들고, 구조 검증과 sandbox 검증을 확인합니다.

### LLM 없이 (Fallback 템플릿)
```bash
curl -s http://localhost:5000/api/devops/gitlab/verify \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Node.js 프로젝트용 GitLab CI",
    "use_llm": false
  }' | jq .
```

### LLM 포함 (Gemma4)
```bash
curl -s http://localhost:5000/api/devops/gitlab/verify \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Node.js 프로젝트용 GitLab CI YAML을 만들어줘. Docker sandbox에서 검증 가능한 단순 단계로 구성해줘.",
    "use_llm": true
  }' | jq .
```

응답에서 확인할 필드:
- `yaml`
- `validation.is_valid`
- `safety.is_safe`
- `sandbox.passed`
- `sandbox.jobs[].stdout`

## 4. YAML 생성 예시

```bash
curl -s http://localhost:5000/api/generate-yaml \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Python Flask API with pytest and GitLab CI",
    "ci_type": "gitlab_ci",
    "use_llm": false
  }' | jq .
```

## 5. YAML 검증 예시

```bash
curl -s http://localhost:5000/api/validate-yaml \
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

## 7. 폐쇄망 배포 (Air-gapped)

Gemma4가 사전 빌드된 Docker 이미지를 사용:

```bash
# 이미지 준비 (이미 포함됨)
docker-compose --profile ollama build ollama

# 이미지 저장 (USB/네트워크 전달용)
docker save poc-ollama-with-gemma4:latest > ollama-gemma4.tar.gz

# 폐쇄망 환경에서:
docker load < ollama-gemma4.tar.gz
docker-compose --profile ollama up -d
```

## 8. 종료

```bash
docker-compose down
```
