# CI/CD 파이프라인 자동 생성 시스템

자연어 요구사항을 받아 **GitLab CI YAML 초안을 생성하고 검증하는 Flask 기반 서비스**입니다.
시연 핵심은 **자연어 입력 → YAML 생성 → YAML 검증 → 위험 명령 검사 → Docker sandbox 검증 → 결과 반환** 흐름이며, 로컬 PoC 기준으로는 **Docker Compose로 앱 + GitLab CE + GitLab Runner**를 함께 올려 재현할 수 있습니다.

## 핵심 기능

- 자연어 기반 YAML 생성
- GitLab CI 구조 검증
- GitLab CI 위험 명령 검사
- Docker sandbox smoke 검증
- YAML diff 비교
- 템플릿 커스터마이징
- 다중 파이프라인 관리
- 로컬 GitLab Runner 기반 PoC 검증

> GitHub Actions 관련 기능은 레포 운영과 개발 자동화를 위해 유지하며, **MVP 시연 대상은 GitLab CI**입니다.

## 권장 실행 방식

### 1. 기본 데모 스택

```bash
cd DevOps
cp .env.example .env
docker pull node:20 python:3.10
docker compose up -d app gitlab gitlab-runner
```

앱과 GitLab 접속:

```text
http://localhost:5000
http://localhost:8080
```

> `app` 서비스는 DevOps MVP의 Docker sandbox 검증을 위해 **호스트 Docker socket**을 사용합니다. 이 설정은 **PoC 전용**입니다.

### 2. Ollama 포함 스택

`.env`에서 Ollama URL을 컨테이너 서비스명으로 바꾼 뒤 실행합니다.

```bash
OLLAMA_URL=http://ollama:11434
docker compose --profile ollama up -d app ollama gitlab gitlab-runner
```

## 주요 API

### DevOps MVP 검증 흐름

```http
POST /api/devops/gitlab/verify
```

예시:

```json
{
  "requirements": "Node.js 프로젝트용 GitLab CI YAML을 만들어줘. Docker sandbox에서 검증 가능한 단순 단계로 구성해줘.",
  "use_llm": true
}
```

응답에는 아래 정보가 함께 반환됩니다.

- 생성된 GitLab CI YAML
- YAML 구조 검증 결과
- 위험 명령 검사 결과
- Docker sandbox 실행 결과와 로그

MVP sandbox smoke 검증은 `node:20`, `python:3.10` 이미지만 자동 실행합니다. Spring Boot/Java 같은 요청은 GitLab CI 초안 생성과 구조/위험 명령 검사는 가능하지만, sandbox 실행 결과는 MVP 범위 밖으로 표시됩니다.

자연어 입력은 비교적 자유롭게 받을 수 있습니다. 예를 들면:

- "Node.js 프로젝트용 GitLab CI YAML을 만들어줘"
- "Python 앱인데 외부 네트워크 없이 검증 가능한 CI 초안이 필요해"
- "테스트는 단순하게 하고 deploy는 빼고 싶어"

### YAML 생성

```http
POST /api/generate-yaml
```

예시:

```json
{
  "requirements": "Python Flask API with pytest and GitLab CI",
  "ci_type": "gitlab_ci"
}
```

### YAML 검증

```http
POST /api/validate-yaml
```

예시:

```json
{
  "yaml": "stages:\n  - validate\nvalidate:\n  stage: validate\n  script:\n    - python --version\n",
  "ci_type": "gitlab_ci"
}
```

## 문서

- `DevOps/QUICKSTART.md`
- `DevOps/docs/SANDBOX.md`
- `DevOps/docs/register-runner.md`
- `DevOps/docs/VERIFICATION_SUMMARY.md`
