"""LLM 서비스 모듈 - Ollama API와 통신하여 자연어 처리를 담당"""
import requests
import json
from typing import Optional, Dict

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama2"


def ask_ollama(prompt: str) -> Optional[str]:
    """Ollama LLM에 질문을 보내고 답변을 받는 함수"""
    try:
        request_data = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=request_data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "No response")
    except requests.exceptions.RequestException as error:
        print(f"Ollama 연결 오류: {error}")
        return None


def generate_pipeline_description(project_desc: str, language: str, requirements: list) -> Optional[str]:
    """프로젝트 설명을 기반으로 CI/CD 파이프라인 설명 생성"""
    prompt = f"""프로젝트: {project_desc}
언어: {language}
요구사항: {', '.join(requirements)}

위 프로젝트를 위한 CI/CD 파이프라인을 설계해주세요."""
    
    return ask_ollama(prompt)
