# 🎬 LLM YAML Generator - 실시간 시연 가이드

## 📋 시연 개요
사용자의 **자연어 프롬프트** → **Gemma 2B LLM** → **GitLab CI YAML 자동 생성**

---

## 🚀 시연 3단계 프로세스

### 1️⃣ **Flask 서버 시작** (터미널 1)

```bash
cd DevOps/src
python app.py
```

**예상 출력:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

✅ **서버가 준비됨** → 다음 단계로 진행

---

### 2️⃣ **시연 스크립트 실행** (터미널 2)

```powershell
.\run_demo.ps1
```

또는 수동으로 API 호출:

```powershell
$prompt = "Node.js 프로젝트용 GitLab CI YAML을 만들어줘"

$body = @{ requirements = $prompt } | ConvertTo-Json

Invoke-WebRequest `
  -Uri "http://localhost:5000/api/generate-yaml" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json
```

---

### 3️⃣ **결과 확인**

**YAML이 생성되면:**
```yaml
stages:
  - validate
  - test
  - build
  - deploy

variables:
  NODE_VERSION: "20"

# ... 전체 GitLab CI YAML
```

**저장 위치:**
```
generated_yamls/llm-20250507-151200.yml
```

---

## 📊 전체 흐름도

```
사용자 프롬프트
    ↓
┌───────────────────────────────────────┐
│ Flask API: /api/generate-yaml         │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ Gemma 2B (Ollama)                     │
│ • 자연어 이해                          │
│ • GitLab CI 구조 생성                  │
│ • 최적화된 파이프라인 설정             │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ YAML 검증 & 정제                      │
│ • 문법 확인                            │
│ • 마크다운 제거                        │
│ • 최종 파일 생성                       │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 결과 저장                              │
│ generated_yamls/llm-*.yml              │
└───────────────────────────────────────┘
```

---

## 🎯 예제 프롬프트

### 예제 1️⃣ - Node.js
```
Node.js 프로젝트용 GitLab CI YAML을 만들어줘. 
npm 의존성 캐싱, 테스트, 빌드, 배포 단계를 포함해.
```

### 예제 2️⃣ - Python FastAPI
```
Python FastAPI 프로젝트의 CI/CD YAML을 생성해줘. 
pytest 테스트, Docker 빌드, 레지스트리 푸시를 포함해.
```

### 예제 3️⃣ - 샌드박스
```
외부 네트워크 접근이 없는 Docker 샌드박스에서 
실행 가능한 단순한 검증 YAML을 만들어줘.
```

### 예제 4️⃣ - Java Spring Boot
```
Java Spring Boot 프로젝트용 CI YAML. 
Maven 빌드, JUnit 테스트, JAR 배포를 포함해.
```

---

## 💡 API 엔드포인트

### `/api/generate-yaml` (POST)
**역할:** 자연어 프롬프트 → YAML 생성

**요청:**
```json
{
  "requirements": "Node.js 프로젝트용 CI YAML"
}
```

**응답:**
```json
{
  "status": "ok",
  "yaml": "stages:\n  - validate\n  - test\n...",
  "generated_by": "gemma",
  "timestamp": "2025-05-07T15:20:00"
}
```

---

### `/api/validate-yaml` (POST)
**역할:** YAML 문법 검증

**요청:**
```json
{
  "yaml": "stages:\n  - test\n..."
}
```

**응답:**
```json
{
  "is_valid": true,
  "errors": []
}
```

---

### `/api/generate-and-validate` (POST)
**역할:** YAML 생성 → 검증 → 샌드박스 테스트 (완전 파이프라인)

---

## 📁 파일 구조

```
dev-project/
├── DevOps/
│   └── src/
│       ├── app.py                  ← Flask 앱 (API 엔드포인트)
│       ├── llm_service.py           ← Gemma LLM 통합
│       ├── template_generator.py    ← YAML 템플릿
│       ├── sandbox_service.py       ← Docker 샌드박스
│       └── templates/
│           └── index.html          ← (웹 UI는 없음)
├── generated_yamls/
│   ├── .gitlab-ci.yml
│   ├── .gitlab-ci-nodejs.yml
│   └── llm-*.yml                   ← LLM 생성 파일
├── run_demo.ps1                     ← 시연 스크립트 (이 파일!)
└── DEMO_GUIDE.md                    ← 이전 가이드

```

---

## 🔧 시연 중 문제 해결

### 문제 1: "Connection refused"
```
❌ http://localhost:5000 에 연결할 수 없음
```
**해결:**
1. Flask 서버가 실행 중인지 확인
2. 포트 5000이 다른 앱에서 사용 중이 아닌지 확인
```powershell
Get-NetTCPConnection -LocalPort 5000
```

---

### 문제 2: "Ollama not running"
```
❌ Gemma를 찾을 수 없음 (템플릿 폴백 사용)
```
**해결:**
```bash
ollama serve    # Ollama 시작
ollama pull gemma  # Gemma 다운로드
```

---

### 문제 3: "Generated YAML이 이상함"
```
❌ stages가 모두 "test"로 나옴
```
**해결:**
1. `generated_by` 확인: "gemma" or "template_fallback"?
2. Gemma 메모리 부족 → 템플릿으로 대체
3. 프롬프트 더 상세히 입력

---

## 🎓 LLM이 하는 역할

### ✅ Gemma가 생성하는 것
- GitLab CI 구조 (stages, jobs)
- 언어별 최적화 (Node.js, Python, Java, Go)
- 캐싱, 아티팩트, 테스트 설정
- 보안 고려 사항

### ❌ Gemma가 하지 않는 것
- 프로젝트 폴더 자동 분석 (MVP 범위 외)
- 복잡한 DevOps 전략 설정
- 실제 배포 구성 (샌드박스만 제공)

---

## 📊 MVP 아키텍처

```
Air-gapped DevOps 환경 (네트워크 격리)
    ↓
Gemma 2B (1.7GB, 로컬 LLM)
    ↓
Flask API (포트 5000)
    ↓
사용자 프롬프트 입력 → YAML 생성
    ↓
YAML 검증 + Docker 샌드박스 테스트
    ↓
최종 결과 저장
```

---

## 🎬 시연 시나리오

### 시나리오 1: 빠른 시연 (2분)
1. Flask 시작
2. `run_demo.ps1` 실행
3. 프롬프트 1 선택
4. YAML 결과 확인
5. 저장된 파일 확인

### 시나리오 2: 상세 시연 (5분)
1. Flask 시작
2. 여러 프롬프트 순차 실행
3. 각 YAML 비교
4. 검증 결과 확인
5. 생성된 파일 구조 설명

### 시나리오 3: 라이브 데모 (10분)
1. Flask 서버 표시
2. 실시간 API 호출 (cURL/PowerShell)
3. 처리 과정 설명
4. 결과 즉시 파일 확인
5. Q&A

---

## 📝 발표 시 핵심 메시지

1. **자동화**: "자연어로 말하면 LLM이 CI YAML을 자동 생성합니다"
2. **검증**: "생성된 YAML은 자동으로 검증되고 Docker에서 테스트됩니다"
3. **보안**: "Air-gapped 환경에서 실행 - 외부 의존성 없음"
4. **확장성**: "Gemma 모델 교체로 더 나은 생성 가능"

---

## ✨ 다음 단계

- [ ] 웹 UI 추가 (시연 이후)
- [ ] 더 큰 LLM 모델 (메모리 확보 시)
- [ ] 프로젝트 폴더 자동 분석
- [ ] GitLab API 통합 (직접 CI 생성)

---

**시연 준비 완료! 🚀**
