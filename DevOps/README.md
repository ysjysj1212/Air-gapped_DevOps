# CI/CD 파이프라인 자동 생성 시스템

자연어 요구사항을 받아 **GitHub Actions / GitLab CI YAML을 생성하고 검증하는 Flask 기반 서비스**입니다.
로컬 PoC 기준으로는 **Docker Compose로 앱 + GitLab CE + GitLab Runner**를 함께 올려 시연할 수 있습니다.

## 핵심 기능

- 자연어 기반 YAML 생성
- GitHub Actions / GitLab CI 검증
- YAML diff 비교
- 템플릿 커스터마이징
- 다중 파이프라인 관리
- 로컬 GitLab Runner 기반 PoC 검증

## 권장 실행 방식

### 1. 기본 데모 스택 (앱 + GitLab + Runner)

```bash
cd DevOps
cp .env.example .env
docker compose up -d app gitlab gitlab-runner
```

기본 앱 주소:

```text
http://localhost:${APP_PORT:-5000}
```

GitLab 주소:

```text
http://localhost:8080
```

기본 구성에서는 Ollama를 **호스트에서 실행**한다고 가정합니다:

```text
OLLAMA_URL=http://host.docker.internal:11434
```

### 2. Ollama까지 컨테이너로 띄우는 전체 스택

`.env`에서 Ollama URL을 아래처럼 바꾼 뒤:

```text
OLLAMA_URL=http://ollama:11434
```

다음 명령으로 전체 스택을 올립니다:

```bash
docker compose --profile ollama up -d app ollama gitlab gitlab-runner
```

## 빠른 확인 명령

```bash
curl -s http://localhost:${APP_PORT:-5000}/health | jq .
curl -I http://localhost:8080/users/sign_in
docker compose ps
```

## 주요 API

### YAML 생성

```http
POST /api/generate-yaml
```

예시:

```json
{
  "requirements": "Python Flask API with pytest and GitLab CI",
  "ci_type": "gitlab_ci",
  "use_llm": false
}
```

### YAML 검증

```http
POST /api/validate-yaml
```

예시:

```json
{
  "yaml": "stages:\n  - build\nbuild:\n  stage: build\n  script:\n    - echo hi\n",
  "ci_type": "gitlab_ci"
}
```

### 헬스 체크

```http
GET /health
```

## 프로젝트 구조

```text
DevOps/
├── src/                 # Flask 앱과 생성/검증 로직
├── tests/               # 테스트
├── docker/              # 컨테이너 이미지 정의
├── templates/           # 기본 YAML 템플릿
├── ci-samples/          # GitLab PoC 샘플
├── docs/                # 운영/검증 문서
├── docker-compose.yml   # 데모 스택
├── run.py               # 앱 엔트리포인트
└── requirements.txt     # Python 의존성
```

## 참고 문서

- [QUICKSTART.md](./QUICKSTART.md)
- [docs/SANDBOX.md](./docs/SANDBOX.md)
- [docs/register-runner.md](./docs/register-runner.md)
