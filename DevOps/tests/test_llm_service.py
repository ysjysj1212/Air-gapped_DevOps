"""Ollama LLM Service Tests"""
import pytest
from src.llm_service import OllamaService, is_ollama_available

class TestOllamaService:
    """Test Ollama service integration"""
    
    def test_ollama_service_init(self):
        """Test OllamaService initialization"""
        service = OllamaService()
        assert service.base_url == "http://localhost:11434"
        assert service.api_endpoint == "http://localhost:11434/api"
    
    def test_is_ollama_available(self):
        """Test Ollama availability check"""
        available = is_ollama_available()
        assert isinstance(available, bool)
        # This test passes regardless of actual Ollama availability
    
    def test_ollama_service_custom_url(self):
        """Test OllamaService with custom URL"""
        service = OllamaService("http://custom:9999")
        assert service.base_url == "http://custom:9999"
        assert service.api_endpoint == "http://custom:9999/api"
    
    def test_ollama_get_available_models_when_unavailable(self):
        """Test getting models when Ollama is unavailable"""
        service = OllamaService("http://invalid:9999")
        models = service.get_available_models()
        assert isinstance(models, list)
        # Should return empty list when service unavailable
    
    def test_ollama_ask_ollama_when_unavailable(self):
        """Test asking Ollama when service is unavailable"""
        service = OllamaService("http://invalid:9999")
        response = service.ask_ollama("test prompt")
        assert response is None
    
    def test_ollama_generate_pipeline_description_when_unavailable(self):
        """Test generating pipeline description when Ollama unavailable"""
        service = OllamaService("http://invalid:9999")
        result = service.generate_pipeline_description("test requirements")
        assert result is None
