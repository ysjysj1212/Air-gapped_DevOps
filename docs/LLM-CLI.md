# LLM CLI 사용법 가이드

## 설정 요구사항

모든 서비스가 실행 중이어야 합니다:

```bash
# 1단계: 기본 서비스 시작 (GitLab, Runner, App)
make docker-up

# 2단계: Ollama 서비스 시작
make docker-ollama
```

## 사용법

### 1. Copilot - 일반 LLM 질의

일반적인 DevOps/CI CD 질문을 LLM에 물어봅니다:

```bash
make copilot "Kubernetes가 뭐야?"
make copilot "Docker 보안 Best Practice"
make copilot "CI/CD 파이프라인 설계 원칙"
```

**예상 동작:**
- LLM이 프롬프트를 처리합니다
- 터미널에 답변이 출력됩니다

### 2. AutoCI - GitLab CI YAML 자동 생성

프로젝트 요구사항을 설명하면 실행 가능한 `.gitlab-ci.yml`이 자동 생성됩니다:

```bash
make AutoCI "Node.js 프로젝트, npm install, npm test, npm build 필요"
make AutoCI "Python 프로젝트, pytest, pylint, 도커 빌드 포함"
make AutoCI "멀티 언어 프로젝트: Node.js와 Python 모두 테스트"
```

**예상 동작:**
1. LLM이 프롬프트를 분석합니다
2. 완전한 `.gitlab-ci.yml` 파일을 생성합니다
3. 파일이 프로젝트 루트에 저장됩니다: `./gitlab-ci.yml`
4. 파일 경로와 내용이 터미널에 출력됩니다
5. GitLab에 푸시하면 자동 실행됩니다

## 예제 시나리오

### 시나리오 1: Node.js 프로젝트 CI/CD 생성

```bash
cd /Users/gyubeom/Desktop/Air-gapped_DevOps

# 서비스 시작
make docker-up
make docker-ollama

# CI YAML 생성
make AutoCI "Node.js Express 백엔드 프로젝트
- npm install로 의존성 설치
- npm run lint로 코드 품질 검사
- npm test로 단위 테스트
- npm run build로 프로덕션 빌드
- Docker 이미지 빌드 (선택사항)
- develop 브랜치 merge시에만 배포 stage 실행"
```

### 시나리오 2: Python 프로젝트 CI/CD 생성

```bash
make AutoCI "Python Django 프로젝트
- pip install -r requirements.txt
- python manage.py test로 테스트
- pylint로 코드 검사
- Docker 이미지 빌드
- 모든 브랜치에서 자동 실행"
```

### 시나리오 3: 일반 질의

```bash
make copilot "GitLab CI/CD에서 secret 변수를 어떻게 안전하게 관리하나요?"
```

## 파일 위치

- **생성된 CI YAML**: `프로젝트_루트/.gitlab-ci.yml`
- **스크립트**: `프로젝트_루트/scripts/llm-cli.py`
- **Makefile**: `프로젝트_루트/Makefile`

## 문제 해결

### "Ollama 서버에 연결할 수 없습니다"

```bash
# Ollama 서비스 확인
docker-compose --profile ollama ps

# Ollama 재시작
docker-compose --profile ollama down ollama
docker-compose --profile ollama up -d ollama
```

### LLM 응답 시간이 오래 걸림

Gemma4 모델은 약 30-60초가 필요합니다. 인내심을 가지세요! 🐱

### 생성된 YAML이 이상한 경우

프롬프트를 더 명확하게 작성하세요:

```bash
# 좋은 예
make AutoCI "React 프론트엔드
- Node.js 18 사용
- npm install로 의존성 설치
- npm run lint로 ESLint 검사
- npm run test로 Jest 테스트
- npm run build로 프로덕션 빌드
- 빌드 결과를 artifacts에 저장"

# 나쁜 예
make AutoCI "웹사이트"
```

## 다음 단계

생성된 YAML 파일을 GitLab에 푸시하면:
1. CI 파이프라인이 자동으로 트리거됩니다
2. GitLab Runner가 정의된 stage들을 순서대로 실행합니다
3. 빌드/테스트 결과를 GitLab UI에서 확인할 수 있습니다
