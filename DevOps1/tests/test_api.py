"""API ?붾뱶?ъ씤???뚯뒪??""
import pytest
import json
from src.app import app
from src.template_generator import (
    generate_github_actions,
    generate_gitlab_ci,
    generate_pipeline_yaml
)

@pytest.fixture
def client():
    """?뚯뒪???대씪?댁뼵???앹꽦"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    """???붾뱶?ъ씤???뚯뒪??""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_health(client):
    """?ъ뒪 泥댄겕 ?붾뱶?ъ씤???뚯뒪??""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'services' in data

def test_generate_ci_missing_description(client):
    """?꾩닔 ?뚮씪誘명꽣 ?꾨씫 ?뚯뒪??""
    response = client.post('/api/generate-ci', 
        json={'language': 'python'})
    assert response.status_code == 400

def test_generate_ci_success(client):
    """CI/CD ?앹꽦 ?깃났 ?뚯뒪??""
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

def test_generate_github_actions():
    """GitHub Actions ?쒗뵆由??앹꽦 ?뚯뒪??""
    result = generate_github_actions('python', 'test-project')
    assert 'name: test-project CI/CD Pipeline' in result
    assert 'runs-on: ubuntu-latest' in result
    assert 'python-version' in result

def test_generate_github_actions_with_options():
    """GitHub Actions 而ㅼ뒪? ?듭뀡 ?뚯뒪??""
    options = {
        'runner_os': 'ubuntu-22.04',
        'python_versions': ['3.9', '3.10', '3.11']
    }
    result = generate_github_actions('python', 'test-project', options)
    assert 'ubuntu-22.04' in result
    assert 'python-version' in result

def test_generate_gitlab_ci():
    """GitLab CI ?쒗뵆由??앹꽦 ?뚯뒪??""
    result = generate_gitlab_ci('python', 'test-project')
    assert 'stages:' in result
    assert 'build:' in result
    assert 'test:' in result
    assert 'python:3.10' in result

def test_generate_gitlab_ci_with_options():
    """GitLab CI 而ㅼ뒪? ?듭뀡 ?뚯뒪??""
    options = {'python_version': '3.11'}
    result = generate_gitlab_ci('python', 'test-project', options)
    assert 'python:3.11' in result

def test_generate_pipeline_yaml_github_actions():
    """generate_pipeline_yaml - GitHub Actions ?щ㎎ ?뚯뒪??""
    result = generate_pipeline_yaml('github_actions', 'python', 'test-project')
    assert 'name: test-project CI/CD Pipeline' in result
    assert 'github.com/actions' not in result or 'checkout' in result

def test_generate_pipeline_yaml_gitlab_ci():
    """generate_pipeline_yaml - GitLab CI ?щ㎎ ?뚯뒪??""
    result = generate_pipeline_yaml('gitlab_ci', 'python', 'test-project')
    assert 'stages:' in result
    assert 'build:' in result

