"""LLM 서비스 테스트"""
import pytest
from unittest.mock import patch, MagicMock
from src.llm_service import ask_ollama, generate_pipeline_description


class TestAskOllama:
    """Ollama 질의 테스트"""
    
    @patch('src.llm_service.requests.post')
    def test_ask_ollama_success(self, mock_post):
        """Ollama 질의 성공 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Test response"}
        mock_post.return_value = mock_response
        
        response = ask_ollama("Test prompt")
        assert response == "Test response"
    
    @patch('src.llm_service.requests.post')
    def test_ask_ollama_failure(self, mock_post):
        """Ollama 질의 실패 테스트"""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        response = ask_ollama("Test prompt")
        assert response is None


class TestGeneratePipelineDescription:
    """파이프라인 설명 생성 테스트"""
    
    @patch('src.llm_service.ask_ollama')
    def test_generate_pipeline_description_success(self, mock_ask):
        """파이프라인 설명 생성 성공 테스트"""
        mock_ask.return_value = "Generated description"
        
        response = generate_pipeline_description(
            "Web API",
            "python",
            ["test", "build", "deploy"]
        )
        
        assert response == "Generated description"
        assert mock_ask.called
    
    @patch('src.llm_service.ask_ollama')
    def test_generate_pipeline_description_failure(self, mock_ask):
        """파이프라인 설명 생성 실패 테스트"""
        mock_ask.return_value = None
        
        response = generate_pipeline_description(
            "Web API",
            "python",
            ["test"]
        )
        
        assert response is None

