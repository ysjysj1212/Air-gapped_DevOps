"""YAML 템플릿 생성 모듈"""
import yaml
from jinja2 import Template

GITHUB_ACTIONS_TEMPLATE = """name: CI/CD Pipeline
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup {{ language }}
        uses: actions/setup-{{ language }}@v4
      - name: Install dependencies
        run: |
          {% if language == 'python' %}
          pip install -r requirements.txt
          {% elif language == 'nodejs' %}
          npm install
          {% endif %}
      - name: Run tests
        run: |
          {% if language == 'python' %}
          pytest
          {% elif language == 'nodejs' %}
          npm test
          {% endif %}
      - name: Build
        run: |
          {% if language == 'python' %}
          python setup.py build
          {% elif language == 'nodejs' %}
          npm run build
          {% endif %}
"""

def generate_github_actions(language: str, project_name: str) -> str:
    """GitHub Actions 템플릿 생성"""
    template = Template(GITHUB_ACTIONS_TEMPLATE)
    return template.render(language=language, project_name=project_name)

def generate_pipeline_yaml(format_type: str, language: str, project_name: str) -> str:
    """CI/CD 파이프라인 YAML 생성"""
    if format_type == "github_actions":
        return generate_github_actions(language, project_name)
    else:
        return f"format: {format_type}, language: {language}"
