# CI/CD 파이프라인 자동 생성 시스템

## 프로젝트 개요

이 프로젝트는 사용자의 자연어 입력을 기반으로 **자동으로 CI/CD 파이프라인 YAML 파일을 생성**하는 시스템입니다.

### 처리 흐름

```
사용자 입력 → LLM 처리 → YAML 생성 → 검증 → 결과 반환
```

### 주요 기술

- **Flask**: 경량 웹 프레임워크로 RESTful API 제공
- **Ollama LLM**: 로컬 기반 대형 언어 모델로 자연어 처리
- **Docker Sandbox**: 안전한 격리 환경에서 CI/CD 파이프라인 실행 및 검증

---

## 설치 및 실행 방법

### 사전 요구사항
- Python 3.10+
- Docker & Docker Compose
- Ollama (LLM 런타임)

### 설치 단계

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd DevOps1
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **환경 변수 설정** (.env 파일 생성)
   ```bash
   FLASK_APP=src/app.py
   OLLAMA_URL=http://localhost:11434
   ```

4. **Docker Compose로 서비스 실행**
   ```bash
   docker-compose up
   ```

서비스가 정상 실행되면 http://localhost:5000 에서 API에 접근 가능합니다.

---

## API 엔드포인트

### 1. CI/CD 파이프라인 생성
**POST** `/api/generate-ci`

요청 예시:
```json
{
  "project_description": "Node.js Express 프로젝트",
  "language": "nodejs",
  "requirements": ["테스트 자동화", "빌드 자동화"]
}
```

응답 예시:
```json
{
  "status": "success",
  "pipeline": "...",
  "format": "github_actions"
}
```

### 2. 헬스 체크
**GET** `/health`

응답 예시:
```json
{
  "status": "healthy",
  "services": {
    "flask": "running",
    "docker": "connected",
    "ollama": "available"
  }
}
```

---

## 프로젝트 구조

```
DevOps1/
├── src/                           # 핵심 로직
│   ├── app.py                     # Flask 애플리케이션 진입점
│   ├── llm_service.py             # LLM 통합 및 자연어 처리
│   ├── sandbox_service.py         # Docker 샌드박스 관리
│   ├── template_generator.py      # YAML 템플릿 생성 로직
│   └── validators.py              # CI/CD 파이프라인 검증
│
├── tests/                         # 테스트 코드
│   ├── test_api.py                # API 엔드포인트 테스트
│   └── __init__.py
│
├── docker/                        # Docker 이미지 설정
│   ├── Dockerfile                 # 메인 애플리케이션 컨테이너
│   └── Dockerfile.validator       # 검증 전용 컨테이너
│
├── templates/                     # CI/CD 템플릿
│   ├── github_actions.yaml        # GitHub Actions 템플릿
│   └── gitlab_ci.yaml             # GitLab CI/CD 템플릿
│
├── docs/                          # 문서
│   ├── API_SPEC.md                # API 명세서
│   └── ARCHITECTURE.md            # 시스템 아키텍처 설명서
│
├── requirements.txt               # Python 의존성
├── docker-compose.yml             # Docker Compose 설정
├── .gitignore                     # Git 제외 파일 목록
└── README.md                      # 프로젝트 문서 (이 파일)
```

---

## 빠른 시작 (Quick Start)

자세한 설정 및 예제는 [QUICKSTART.md](./QUICKSTART.md)를 참고하세요.

```bash
# 1. 프로젝트 클론 및 설정
git clone <repository-url>
cd DevOps1
pip install -r requirements.txt

# 2. 서비스 시작
docker-compose up -d

# 3. 테스트 (선택사항)
pytest tests/ --cov=src
```

---

## 참고 자료

- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [Ollama 공식 사이트](https://ollama.ai/)
- [Docker 공식 문서](https://docs.docker.com/)
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [GitLab CI/CD 문서](https://docs.gitlab.com/ee/ci/)

---

## 라이선스

이 프로젝트는 **MIT 라이선스** 하에서 배포됩니다. 자세한 사항은 LICENSE 파일을 참고하세요.

```
Copyright (c) 2026 DevOps1 Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

**기여도 있으신 분들은 Pull Request를 보내주세요!** 📝
