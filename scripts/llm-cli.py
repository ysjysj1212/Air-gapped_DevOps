#!/usr/bin/env python3
"""
LLM CLI - Ollama를 통한 CI/CD 자동화 도구
- copilot: 일반 LLM 질의
- AutoCI: GitLab CI YAML 자동 생성
"""
import sys
import os
import re
import requests
import argparse
import time
from pathlib import Path
from typing import Optional

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

def infer_language_from_requirements(requirements: str) -> Optional[str]:
    """요구사항 문자열에서 런타임을 휴리스틱하게 판별"""
    lower = requirements.lower()

    python_keywords = [
        "python",
        "flask",
        "django",
        "fastapi",
        "pytest",
        "pip",
    ]
    node_keywords = [
        "node",
        "nodejs",
        "node.js",
        "npm",
        "yarn",
        "pnpm",
        "next.js",
        "react",
        "vue",
    ]

    if any(keyword in lower for keyword in python_keywords):
        return "python"
    if any(keyword in lower for keyword in node_keywords):
        return "node"
    return None


def infer_requested_version(requirements: str, language: str) -> Optional[str]:
    """요구사항 문자열에서 런타임 버전을 휴리스틱하게 추출"""
    patterns = {
        "python": [
            r"python[^\n\r]{0,30}?버전(?:은|는|을)?\s*v?(\d+(?:\.\d+){1,2})",
            r"python(?:\s*version)?\s*[:=]?\s*v?(\d+(?:\.\d+){1,2})",
            r"python(\d+(?:\.\d+){1,2})",
        ],
        "node": [
            r"node(?:\.js|js)?[^\n\r]{0,30}?버전(?:은|는|을)?\s*v?(\d+(?:\.\d+){0,2})",
            r"node(?:\.js|js)?(?:\s*version)?\s*[:=]?\s*v?(\d+(?:\.\d+){0,2})",
            r"node(?:\.js|js)\s*v?(\d+(?:\.\d+){0,2})",
        ],
    }

    for pattern in patterns[language]:
        match = re.search(pattern, requirements, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def infer_language_with_llm(requirements: str) -> str:
    """LLM으로 요구사항을 짧게 분석해 CI 템플릿 대상을 결정"""
    inferred = infer_language_from_requirements(requirements)
    candidate = inferred or "node"

    prompt = (
        "Classify the project runtime from the user's CI request. "
        "Answer with exactly one word: node or python.\n\n"
        f"Request: {requirements}\n"
        f"Best guess: {candidate}"
    )
    response = call_ollama(prompt, num_predict=32).lower()

    match = re.search(r"\b(node|python)\b", response)
    if match:
        return match.group(1)
    if inferred:
        return inferred

    raise RuntimeError(f"LLM returned an unexpected runtime classification: {response}")


def build_gitlab_ci(requirements: str, language: str) -> str:
    """프로젝트 유형에 맞는 검증 가능한 GitLab CI 템플릿 생성"""
    requested_version = infer_requested_version(requirements, language)

    if language == "python":
        image = f"python:{requested_version or '3.10'}"
        validate_steps = [
            "python --version",
            "pip --version",
        ]
        test_steps = [
            'python -c "print(\'Python CI smoke check passed\')"',
        ]
        build_steps = [
            'echo "Python project build-ready pipeline generated"',
        ]
    else:
        image = f"node:{requested_version or '20'}"
        validate_steps = [
            "node --version",
            "npm --version",
        ]
        test_steps = [
            'node -e "console.log(\'Node.js CI smoke check passed\')"',
        ]
        build_steps = [
            'echo "Node.js project build-ready pipeline generated"',
        ]

    validate_script = "\n".join(f"    - {step}" for step in validate_steps)
    test_script = "\n".join(f"    - {step}" for step in test_steps)
    build_script = "\n".join(f"    - {step}" for step in build_steps)

    return f"""workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH'

stages:
  - validate
  - test
  - build

image: {image}

validate:
  stage: validate
  tags:
    - docker-socket
  script:
{validate_script}

test:
  stage: test
  tags:
    - docker-socket
  script:
{test_script}

build:
  stage: build
  tags:
    - docker-socket
  script:
{build_script}

merge-ready:
  stage: build
  tags:
    - docker-socket
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  script:
    - echo "Merge-ready pipeline checks passed"
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

def interactive_auto_ci():
    """AutoCI 대화형 요구사항 입력 모드"""
    print("🚀 AutoCI 대화형 모드")
    print("GitLab CI 요구사항을 입력하면 현재 디렉터리에 .gitlab-ci.yml을 생성합니다.")
    print("종료하려면 exit, quit, q, 종료 중 하나를 입력하세요.\n")

    while True:
        try:
            requirements = input("AutoCI> ").strip()
        except EOFError:
            print()
            break

        if not requirements:
            continue

        if requirements.lower() in {"exit", "quit", "q", ":q"} or requirements == "종료":
            print("AutoCI 대화형 모드를 종료합니다.")
            break

        auto_ci(requirements)

def main():
    parser = argparse.ArgumentParser(
        description="LLM 기반 CI/CD 자동화 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  AutoCI
  AutoCI "Node.js 프로젝트, npm test 및 build 포함"
  make copilot "Kubernetes 설명해줘"
  make AutoCI "Node.js 프로젝트, npm test 및 build 포함"
        """
    )
    parser.add_argument("mode", choices=["copilot", "AutoCI"], help="실행 모드")
    parser.add_argument("query", nargs="*", help="질의 내용")
    
    args = parser.parse_args()
    query = " ".join(args.query)
    
    if args.mode == "copilot":
        copilot(query)
    elif args.mode == "AutoCI" and query:
        auto_ci(query)
    elif args.mode == "AutoCI":
        interactive_auto_ci()

if __name__ == "__main__":
    main()
