# Air-gapped AutoCI PoC

폐쇄망(air-gapped) 환경을 가정하고, **자연어 요구사항에서 GitLab CI/CD YAML을 자동 생성하고 Docker sandbox로 검증하는 DevOps PoC**입니다.

이 프로젝트는 단순히 YAML 한 장을 만드는 데서 끝나지 않습니다. **생성 → 저장 → 구조 검증 → 안전성 검사 → sandbox 검증 → GitLab 반영**까지 이어지는 흐름을 한 번에 재현할 수 있도록 만들었습니다.

## 왜 만들었나

GitLab CI를 수작업으로 만들 때는 보통 이런 문제가 반복됩니다.

- 프로젝트마다 YAML을 새로 작성해야 함
- 문법은 맞아도 실제 실행이 안 되는 경우가 많음
- 위험 명령이나 불필요한 네트워크 접근이 뒤늦게 발견됨
- 폐쇄망 환경에서는 패키지 다운로드와 외부 의존성 때문에 재현성이 떨어짐

그래서 이 PoC는 **"폐쇄망에서도 바로 재현 가능한 자동화된 CI 초안 생성/검증 흐름"**을 목표로 만들었습니다.

## 누구에게 도움이 되나

- 사내 폐쇄망에서 GitLab CI 표준안을 빠르게 만들어야 하는 DevOps 엔지니어
- 신규 프로젝트 온보딩 시 CI 초안 작성 시간을 줄이고 싶은 팀
- YAML을 생성만 하지 않고 **실행 가능한지까지** 확인하고 싶은 조직
- GitLab Runner, Docker sandbox, LLM 기반 YAML 생성 흐름을 한 번에 시연해야 하는 PoC 담당자

## 어떤 점이 빨라지나

아래 수치는 현재 로컬 PoC 환경에서 직접 확인한 값입니다.

| 항목 | 기존 수작업 방식 | 이 시스템 사용 시 |
| --- | --- | --- |
| CI 초안 작성 | 요구사항 해석, YAML 작성, 저장까지 보통 수 분~수십 분 | `AutoCI "요구사항"` 한 번으로 현재 디렉터리에 파일 생성 |
| 구조/안전성 확인 | 문법 검사, 위험 명령 확인을 별도 수행 | API 한 번으로 함께 수행 |
| 검증 응답 시간 | 단계별 수동 확인 필요 | `/api/devops/gitlab/verify` 실측 **0.56초** |
| 스택 재현 | 도구별 개별 설치 필요 | Docker Compose로 통합 기동 |

> 참고: `gemma4:e2b` 경로는 이 호스트에서 약 **9.7~9.8 GiB** 메모리를 요구했습니다. Docker 메모리 한도를 약 12.5 GiB 이상으로 올린 뒤 단독 LLM 추론은 성공했으며, 첫 모델 로딩에는 약 **4분 11초**가 걸렸습니다. 실사용 `AutoCI` 명령은 LLM으로 런타임을 짧게 분석한 뒤 검증 가능한 GitLab CI 템플릿을 생성합니다.

## 핵심 흐름

1. 자연어로 CI 요구사항 입력
2. `AutoCI` 또는 API가 프로젝트 유형에 맞는 GitLab CI YAML 생성
3. 생성된 파일을 현재 작업 디렉터리에 저장
4. API가 YAML 구조/위험 명령/sandbox 검증 수행
5. 결과를 보고 GitLab 프로젝트에 반영

## 빠른 시작

### 1. 스택 실행

```bash
cd /path/to/Air-gapped_DevOps
docker-compose up -d
docker-compose --profile ollama up -d
```

접속 주소:

```text
App API   http://localhost:8000
GitLab    http://localhost:8080
Ollama    http://localhost:11434
```

### 2. `AutoCI` 명령 설치

다른 사용자도 레포를 받은 뒤 **한 번만** 아래 명령을 실행하면 새 터미널에서 `AutoCI`를 바로 쓸 수 있습니다.

```bash
cd /path/to/Air-gapped_DevOps
./scripts/install-autoci.sh
```

설치 후에는 현재 프로젝트 위치에서 바로:

```bash
AutoCI
AutoCI "Node.js 프로젝트, npm ci / npm test / npm run build가 필요한 GitLab CI"
```

`AutoCI`만 실행하면 대화형 모드로 진입합니다. 요구사항을 입력하면 LLM이 프로젝트 유형을 판별하고, **현재 디렉터리**에 `.gitlab-ci.yml`을 생성합니다.

- Node.js 요청이면 `node:20` 기반 job 생성
- Python 요청이면 `python:3.10` 기반 job 생성
- 요청문에 버전을 적으면 그 버전(`node:18`, `python:3.11` 등)을 우선 반영
- 생성되는 job에는 `docker-socket` 태그와 merge-ready 검증 단계가 포함됩니다
CPU 기반 `gemma4:e2b` 환경에서 긴 YAML 전체를 직접 생성시키면 불안정하므로, LLM은 짧은 런타임 분석을 담당하고 YAML은 검증 가능한 템플릿으로 생성합니다.

### 3. API로 생성 + 검증

LLM 없이 템플릿 기반으로 바로 검증:

```bash
curl -s http://localhost:8000/api/devops/gitlab/verify \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Node.js 프로젝트용 GitLab CI",
    "use_llm": false
  }' | jq .
```

LLM 경로 사용:

```bash
curl -s http://localhost:8000/api/devops/gitlab/verify \
  -H 'Content-Type: application/json' \
  -d '{
    "requirements": "Node.js 프로젝트용 GitLab CI YAML을 만들어줘",
    "use_llm": true
  }' | jq .
```

## 대표 명령어

```bash
# 전체 서비스 시작
docker-compose up -d

# Ollama 포함 시작
docker-compose --profile ollama up -d

# AutoCI 설치
./scripts/install-autoci.sh

# YAML 자동 생성
AutoCI
AutoCI "Python 프로젝트, pytest와 build 단계 필요"
AutoCI "Node.js 프로젝트, npm test와 build 단계 필요"

# 스택 상태 확인
docker-compose ps

# GitLab 접속 확인
curl -I http://localhost:8080/users/sign_in
```

## 문서

- `DevOps/QUICKSTART.md`
- `DevOps/README.md`
- `DevOps/docs/SANDBOX.md`
- `DevOps/docs/register-runner.md`

## 현재 PoC 범위

- GitLab CE + GitLab Runner 기반 CI 시연
- Docker sandbox 기반 검증
- 폐쇄망 배포를 위한 사전 빌드 Ollama 이미지
- `AutoCI` 전역 명령 스타일 사용

Kubernetes, ArgoCD, 복잡한 인프라 오케스트레이션은 의도적으로 제외했습니다.
