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
curl -s http://localhost:8000/health | jq .
curl -I http://localhost:8080/users/sign_in
```

포트 8000이 이미 사용 중이면 `.env`에서 `APP_PORT`를 변경합니다.

접속 주소:
```text
Flask API:    http://localhost:8000
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

`AutoCI`를 새 터미널에서 바로 쓰려면 한 번만 아래를 실행합니다.

```bash
./scripts/install-autoci.sh
AutoCI
AutoCI "Node.js 프로젝트, npm ci / npm test / npm run build가 필요한 GitLab CI"
```

`AutoCI`만 입력하면 대화형 모드로 들어갑니다. `gemma4:e2b`는 큰 모델이라 첫 로딩이 수 분 걸릴 수 있습니다. `AutoCI`는 LLM으로 프로젝트 유형을 분석한 뒤 **현재 디렉터리**에 실행 가능한 GitLab CI 템플릿을 생성합니다.

- Node.js 요청 → `node:20` 이미지와 `docker-socket` 태그 job 생성
- Python 요청 → `python:3.10` 이미지와 `docker-socket` 태그 job 생성
- 요청문에 버전을 적으면 해당 버전을 우선 반영
- merge-ready 검증 단계가 함께 포함됩니다
- 요청에 런타임이 명확하면 휴리스틱으로 바로 처리하고, 애매할 때만 Ollama를 사용합니다

예를 들어 새 프로젝트에 바로 만들려면:

```bash
mkdir -p ~/Desktop/practice
cd ~/Desktop/practice
AutoCI "Node.js 프로젝트고 node 버전은 20이야. GitLab CI YAML 생성해줘."
ls -la .gitlab-ci.yml
```

## 3. DevOps MVP 흐름 실행

자연어 입력으로 GitLab CI 초안을 만들고, 구조 검증과 sandbox 검증을 확인합니다.

### LLM 없이 (템플릿 검증)
```bash
curl -s http://localhost:8000/api/devops/gitlab/verify \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Node.js 프로젝트용 GitLab CI",
    "use_llm": false
  }' | jq .
```

### LLM 포함 (Gemma4)
```bash
curl -s http://localhost:8000/api/devops/gitlab/verify \
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
curl -s http://localhost:8000/api/generate-yaml \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Python Flask API with pytest and GitLab CI",
    "ci_type": "gitlab_ci",
    "use_llm": false
  }' | jq .
```

## 5. YAML 검증 예시

```bash
curl -s http://localhost:8000/api/validate-yaml \
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

주소 구분:

```text
브라우저/로컬 push: http://localhost:8080/...
Runner 내부 clone: http://gitlab/...
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
docker save poc-ollama-with-gemma4:latest > ollama-gemma4-e2b.tar.gz

# 폐쇄망 환경에서:
docker load < ollama-gemma4-e2b.tar.gz
docker-compose --profile ollama up -d
```

## 8. 종료

```bash
docker-compose down
```
