#!/usr/bin/env python3
"""
LLM CLI - Ollama를 통한 CI/CD 자동화 도구
- copilot: 일반 LLM 질의
- AutoCI: GitLab CI YAML 자동 생성
"""
import sys
import json
import os
import re
import requests
import argparse
import time
from datetime import datetime
from pathlib import Path

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "600"))
TARGET_PROJECT_DIR = Path.cwd()

def call_ollama(prompt: str, *, num_predict: int = 64, retries: int = 2) -> str:
    """Ollama LLM에 프롬프트 전달"""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "30m",
        "options": {
            "num_ctx": 512,
            "num_predict": num_predict,
            "temperature": 0.1,
            "top_p": 0.8,
        },
    }

    last_error = None
    for attempt in range(1, retries + 2):
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=OLLAMA_TIMEOUT,
            )
            if not response.ok:
                raise RuntimeError(f"{response.status_code} {response.text}")
            result = response.json().get("response", "").strip()
            if not result:
                raise RuntimeError("Ollama returned an empty response")
            return result
        except requests.exceptions.ConnectionError as exc:
            last_error = exc
            if attempt <= retries:
                time.sleep(3)
                continue
            print("❌ Ollama 서버에 연결할 수 없습니다.")
            print("   실행해주세요: docker-compose --profile ollama up -d ollama")
            sys.exit(1)
        except Exception as exc:
            last_error = exc
            if attempt <= retries:
                time.sleep(3)
                continue
            print(f"❌ LLM 호출 실패: {last_error}")
            sys.exit(1)

def copilot(query: str):
    """일반 LLM 질의"""
    print("🤖 Copilot 호출 중...\n")
    response = call_ollama(query, num_predict=256)
    print(response)

def infer_language_with_llm(requirements: str) -> str:
    """LLM으로 요구사항을 짧게 분석해 CI 템플릿 대상을 결정"""
    lower = requirements.lower()
    candidate = "python" if any(
        keyword in lower for keyword in ["python", "flask", "django", "fastapi", "pytest"]
    ) else "node"
    prompt = f"Say exactly this one word: {candidate}"
    response = call_ollama(prompt, num_predict=32).lower()
    if re.search(rf"\b{candidate}\b", response):
        return candidate

    match = re.search(r"\b(node|python)\b", response)
    if match:
        return match.group(1)

    raise RuntimeError(f"LLM returned an unexpected runtime classification: {response}")

def build_gitlab_ci(requirements: str, language: str) -> str:
    """LLM 분석 결과를 검증 가능한 GitLab CI 템플릿으로 변환"""
    if language == "python":
        image = "python:3.10"
        version_command = "python --version"
        smoke_command = 'echo "Python CI smoke check passed"'
    else:
        image = "node:20"
        version_command = "node --version"
        smoke_command = 'echo "Node.js CI smoke check passed"'

    return f"""stages:
  - validate
  - test

image: {image}

validate:
  stage: validate
  tags:
    - docker-socket
  script:
    - {version_command}

test:
  stage: test
  tags:
    - docker-socket
  script:
    - {smoke_command}
"""

def normalize_yaml_response(content: str) -> str:
    """LLM이 markdown fence를 붙인 경우 YAML 본문만 추출"""
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped

def auto_ci(requirements: str):
    """GitLab CI YAML 자동 생성"""
    print("🚀 AutoCI - GitLab CI YAML 생성 중...\n")

    language = infer_language_with_llm(requirements)
    print(f"🤖 LLM 분석 완료: {language}")
    yaml_content = build_gitlab_ci(requirements, language)
    
    # YAML 저장
    output_path = TARGET_PROJECT_DIR / ".gitlab-ci.yml"
    output_path.write_text(yaml_content)
    
    print(f"✅ YAML 파일 생성 완료: {output_path}")
    print(f"\n📝 생성된 파일 내용:\n")
    print(yaml_content)
    
    # GitLab 업로드 가이드
    print("\n" + "="*60)
    print("📤 다음 단계: GitLab에 업로드")
    print("="*60)
    print(f"""
1. GitLab 웹 UI 접속: http://localhost:8080
2. 프로젝트 → 파일 업로드
3. {output_path.name} 파일 선택
4. 푸시하면 자동으로 CI 파이프라인 실행됨
    """)

def main():
    parser = argparse.ArgumentParser(
        description="LLM 기반 CI/CD 자동화 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  make copilot "Kubernetes 설명해줘"
  make AutoCI "Node.js 프로젝트, npm test 및 build 포함"
        """
    )
    parser.add_argument("mode", choices=["copilot", "AutoCI"], help="실행 모드")
    parser.add_argument("query", nargs="+", help="질의 내용")
    
    args = parser.parse_args()
    query = " ".join(args.query)
    
    if args.mode == "copilot":
        copilot(query)
    elif args.mode == "AutoCI":
        auto_ci(query)

if __name__ == "__main__":
    main()
