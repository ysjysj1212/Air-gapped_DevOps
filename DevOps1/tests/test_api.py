"""API 엔드포인트 테스트"""
import pytest
import json
from src.app import app

@pytest.fixture
def client():
    """테스트 클라이언트 생성"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    """홈 엔드포인트 테스트"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_health(client):
    """헬스 체크 엔드포인트 테스트"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'services' in data

def test_generate_ci_missing_description(client):
    """필수 파라미터 누락 테스트"""
    response = client.post('/api/generate-ci', 
        json={'language': 'python'})
    assert response.status_code == 400

def test_generate_ci_success(client):
    """CI/CD 생성 성공 테스트"""
    response = client.post('/api/generate-ci',
        json={
            'project_description': 'Node.js Express API',
            'language': 'nodejs',
            'requirements': ['test', 'build']
        })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'pipeline' in data
