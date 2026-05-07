# AI→DevOps 파이프라인 MVP 발표 가이드

## 🎯 한 줄 요약

**"Gemma4 기반으로 사용자 자연어 요청을 GitLab CI YAML 초안으로 변환하는 단순하고 안정적인 생성기를 만든다. 검증과 실행은 DevOps 파트가 담당한다."**

---

## 📊 시스템 아키텍처

```
┌─────────────────────────────────────────────────┐
│         사용자 (자연어 요청)                      │
│   "Node.js CI 파이프라인 만들어줘"              │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │  Flask API     │
        └────────────────┘
                 │
         ┌───────┴───────┐
         ▼               ▼
    ┌────────┐      ┌──────────┐
    │ Gemma  │      │ Template │
    │  LLM   │      │ Fallback │
    └────────┘      └──────────┘
                 │
                 ▼
        ┌────────────────┐
        │ YAML 생성      │
        │ (초안)         │
        └────────────────┘
                 │
         ┌───────┴──────────┐
         ▼                  ▼
    ┌──────────┐      ┌──────────────┐
    │ 문법검증 │      │ Sandbox 검증 │
    │ (YAML)   │      │ (--network)  │
    └──────────┘      └──────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ 결과 반환       │
        │ Pass/Fail/Log   │
        └─────────────────┘
```

---

## 🎬 발표 시나리오

### 1️⃣ 도입 (1분)
```
"현재 DevOps 자동화 플랫폼을 구축 중입니다.
 핵심은 '자동 생성'이 아니라 '검증'입니다.
 
 사용자가 요청하면 → LLM이 초안을 생성하고 → DevOps가 검증한다."
```

### 2️⃣ 데모 (3~5분)

#### Demo 1: YAML 생성
```bash
$ python demo_e2e.py
```
자연어 입력 → Gemma YAML 생성 보여주기

#### Demo 2: 검증 파이프라인
```
사용자 요청 → YAML 생성 → 문법 검증 → Sandbox 실행 → 결과
```

#### Demo 3: 결과 확인
```json
{
  "status": "ok",
  "generation": {
    "yaml": "...생성된 YAML...",
    "generated_by": "gemma"
  },
  "validation": {
    "is_valid": true,
    "errors": []
  },
  "sandbox": {
    "success": true,
    "output": "node v20.x.x"
  }
}
```

### 3️⃣ 핵심 메시지 (1분)
```
"LLM의 역할은 명확합니다:
 - ✅ YAML 초안 생성
 - ✅ 기본 구조 제시
 - ❌ 프로젝트 분석 안 함
 - ❌ 복잡한 배포 파이프라인 안 만듦
 
 DevOps의 역할도 명확합니다:
 - ✅ YAML 문법 검증
 - ✅ 위험 명령어 탐지
 - ✅ Docker Sandbox에서 실행 검증
 - ✅ Pass/Fail 판단"
```

---

## 🔑 MVP 완성도

### ✅ 구현된 것
- [x] Gemma 2B LLM 설치 (로컬)
- [x] Flask API 엔드포인트 3개
  - `/api/generate-yaml` - YAML 생성
  - `/api/validate-yaml` - 문법 검증
  - `/api/generate-and-validate` - 통합 (E2E)
- [x] YAML 검증 로직
- [x] Docker Sandbox 검증
- [x] E2E 데모 스크립트

### ⏳ 향후 확장 (Phase 2)
- [ ] 프로젝트 폴더 자동 분석 (package.json, requirements.txt)
- [ ] 복잡한 파이프라인 생성
- [ ] 사용자 피드백 반영 (재생성)
- [ ] GitHub Actions 지원

---

## 📁 핵심 파일

```
DevOps/
├── src/
│   ├── app.py                 # Flask API
│   ├── llm_service.py         # Gemma 통합
│   ├── validators.py          # YAML 검증
│   └── sandbox_service.py     # Sandbox 래퍼
├── sandbox.sh                 # Docker --network none
└── requirements.txt           # 의존성
prompt_to_yaml.py              # CLI 도구
demo_e2e.py                    # 발표 데모
```

---

## 🚀 실행 방법

### 1. 환경 설정
```bash
cd DevOps
pip install -r requirements.txt
```

### 2. 서비스 시작
```bash
# Terminal 1: Flask API
cd DevOps
python -m flask run --port=5000

# Terminal 2: Ollama (이미 실행 중이면 생략)
ollama serve
```

### 3. 데모 실행
```bash
python demo_e2e.py
```

### 4. 또는 개별 테스트
```bash
# YAML 생성만
python prompt_to_yaml.py

# API 직접 호출
curl -X POST http://localhost:5000/api/generate-yaml \
  -H "Content-Type: application/json" \
  -d '{"requirements":"Node.js CI","use_llm":true}'
```

---

## 💡 설명 포인트

### Q: "왜 LLM을 간단하게 만들었나?"
```
A: 복잡한 분석보다 검증이 더 중요합니다.
   LLM은 초안 생성에 집중하고,
   DevOps는 안정성 검증에 집중합니다.
   
   5일 MVP에서 범위를 명확히 했습니다.
```

### Q: "Sandbox는 왜 필수인가?"
```
A: 생성된 YAML이 실제로 실행 가능한지 확인해야 합니다.
   --network none으로 실행하면:
   - 네트워크 접근 시도 탐지
   - 위험한 명령어 식별
   - 실제 환경과 격리 검증
```

### Q: "GitHub Actions는?"
```
A: 현재 MVP는 GitLab CI 전용입니다.
   GitHub Actions는 개발/레포 관리용이고,
   이 시스템의 생성 대상은 .gitlab-ci.yml입니다.
   
   향후 요청이 있으면 Phase 2에서 추가 가능합니다.
```

---

## 📊 데모 실행 결과 예시

```
🤖 Demo 1️⃣  YAML 생성 (Gemma 기반)
======================================================================

📝 사용자 요청:
   "Node.js 프로젝트용 GitLab CI 파이프라인 만들어줘"

⏳ Gemma에서 YAML 생성 중...

✅ 생성 완료 (생성기: gemma)

📄 생성된 YAML:
---
stages:
  - validate
  - test

image: node:20

validate:
  stage: validate
  script:
    - node -v

test:
  stage: test
  script:
    - npm test || echo "No tests configured"
---

🚀 Demo 2️⃣  완전한 파이프라인 (생성→검증→Sandbox)
======================================================================

📝 사용자 요청:
   "Python 프로젝트용 CI 파이프라인"

⏳ 처리 중...
   1️⃣  YAML 생성 (Gemma)
   2️⃣  문법 검증
   3️⃣  Sandbox 실행 (--network none)

✅ 처리 완료

📊 결과:
   전체 상태: ok

   1️⃣  생성:
      생성기: gemma
      stages:
        - validate
      ...

   2️⃣  검증:
      유효: True
      오류: []

   3️⃣  Sandbox:
      상태: ✅ 성공
      반환 코드: 0
      출력: Python 3.10.x
```

---

## ✨ 발표 마무리

```
"이 MVP는 기초입니다.
 핵심은 자동 생성이 아니라 검증 파이프라인입니다.
 
 다음 단계:
 1. 사용자 피드백 수집
 2. 검증 로직 강화
 3. 프로젝트 분석 추가 (Phase 2)
 
 감사합니다!"
```
