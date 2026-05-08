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
cd /path/to/Air-gapped_DevOps
docker-compose up -d
```

앱과 GitLab 접속:

```text
http://localhost:8000
http://localhost:8080
```

> `app` 서비스는 DevOps MVP의 Docker sandbox 검증을 위해 **호스트 Docker socket**을 사용합니다. 이 설정은 **PoC 전용**입니다.

### 2. Ollama 포함 스택

`.env`에서 Ollama URL을 컨테이너 서비스명으로 바꾼 뒤 실행합니다.

```bash
docker-compose --profile ollama up -d
./scripts/install-autoci.sh
AutoCI
AutoCI "Node.js 프로젝트, npm ci / npm test / npm run build가 필요한 GitLab CI"
```

`AutoCI`만 입력하면 대화형 모드로 진입합니다. `gemma4:e2b` 첫 로딩은 수 분 걸릴 수 있습니다. `AutoCI`는 LLM으로 프로젝트 유형을 분석한 뒤 실행 가능한 GitLab CI 템플릿을 생성합니다.

중요한 점은 **`AutoCI`를 실행한 현재 디렉터리**에 `.gitlab-ci.yml`이 생성된다는 것입니다. 즉 새 프로젝트 루트에서 실행해야 그 프로젝트에 바로 생성됩니다.

```bash
mkdir -p ~/Desktop/practice
cd ~/Desktop/practice
AutoCI "Node.js 프로젝트고 node 버전은 20이야. GitLab CI YAML 생성해줘."
ls -la .gitlab-ci.yml
```

- Node.js 요청 → `node:20` 기반 job
- Python 요청 → `python:3.10` 기반 job
- 요청문에 버전을 적으면 해당 버전을 우선 반영
- 모든 기본 job에는 `docker-socket` 태그와 merge-ready 검증 단계 포함
- 요청에 런타임이 명확하면 휴리스틱으로 바로 처리하고, 애매할 때만 Ollama를 사용

GitLab 연결 시 주소 구분:

| 용도 | 주소 |
| --- | --- |
| 브라우저/로컬 push | `http://localhost:8080/...` |
| Runner 내부 clone | `http://gitlab/...` |

새 project runner를 등록했다면 아래 값도 함께 맞춰야 합니다.

```text
custom_http_clone_url_root = http://gitlab
clone_url = "http://gitlab"
network_mode = "air-gapped_devops_air-gapped-network"
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
