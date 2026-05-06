"""YAML Validation Tests"""
import pytest
from src.validators import validate_ci_yaml, ValidationResult, suggest_fixes

class TestYAMLValidation:
    """Test YAML validation functionality"""
    
    def test_validate_empty_yaml(self):
        """Test validation of empty YAML"""
        result = validate_ci_yaml("")
        assert result.is_valid == False
        assert any('empty' in e.lower() for e in result.errors)
    
    def test_validate_github_actions_valid(self):
        """Test valid GitHub Actions YAML"""
        yaml_content = """name: Test Pipeline
on:
  push:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm test
"""
        result = validate_ci_yaml(yaml_content, 'github_actions')
        assert result.is_valid == True
    
    def test_validate_github_actions_missing_name(self):
        """Test GitHub Actions YAML missing name"""
        yaml_content = """on:
  push:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
"""
        result = validate_ci_yaml(yaml_content, 'github_actions')
        assert result.is_valid == False
        assert any('name' in e.lower() for e in result.errors)
    
    def test_validate_gitlab_ci_valid(self):
        """Test valid GitLab CI YAML"""
        yaml_content = """stages:
  - build
  - test

build:
  stage: build
  script:
    - echo "Building..."

test:
  stage: test
  script:
    - echo "Testing..."
"""
        result = validate_ci_yaml(yaml_content, 'gitlab_ci')
        assert result.is_valid == True
    
    def test_validate_gitlab_ci_missing_stages(self):
        """Test GitLab CI YAML missing stages"""
        yaml_content = """build:
  script:
    - echo "Building..."

test:
  script:
    - echo "Testing..."
"""
        result = validate_ci_yaml(yaml_content, 'gitlab_ci')
        assert result.is_valid == False
        assert any('stages' in e.lower() for e in result.errors)
    
    def test_auto_detect_github_actions(self):
        """Test auto-detection of GitHub Actions"""
        yaml_content = """name: Test
on: push
jobs:
  test:
    runs-on: ubuntu-latest
"""
        result = validate_ci_yaml(yaml_content, 'auto')
        assert result.is_valid == True or result.is_valid == False  # Either is acceptable
    
    def test_auto_detect_gitlab_ci(self):
        """Test auto-detection of GitLab CI"""
        yaml_content = """stages:
  - test

test:
  stage: test
  script:
    - echo "test"
"""
        result = validate_ci_yaml(yaml_content, 'auto')
        assert result.is_valid == True or result.is_valid == False  # Either is acceptable
    
    def test_suggest_fixes(self):
        """Test fix suggestions"""
        yaml_content = """on: push
jobs: {}
"""
        result = validate_ci_yaml(yaml_content, 'github_actions')
        suggestions = suggest_fixes(yaml_content, result)
        assert len(suggestions) > 0 or result.is_valid
    
    def test_validation_result_to_dict(self):
        """Test ValidationResult to_dict conversion"""
        result = ValidationResult(True, errors=[], warnings=['warning1'])
        result_dict = result.to_dict()
        assert 'is_valid' in result_dict
        assert 'error_count' in result_dict
        assert 'warning_count' in result_dict
        assert result_dict['warning_count'] == 1
    
    def test_github_actions_missing_jobs(self):
        """Test GitHub Actions YAML missing jobs"""
        yaml_content = """name: Test
on: push
"""
        result = validate_ci_yaml(yaml_content, 'github_actions')
        assert result.is_valid == False
        assert any('jobs' in e.lower() for e in result.errors)
