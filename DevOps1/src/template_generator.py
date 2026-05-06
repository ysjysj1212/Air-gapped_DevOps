"""YAML ?쒗뵆由??앹꽦 紐⑤뱢"""
import yaml
from jinja2 import Template
from typing import Dict, Any, Optional

GITHUB_ACTIONS_TEMPLATE = """name: {{ project_name }} CI/CD Pipeline
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: {{ runner_os }}
    strategy:
      matrix:
        python-version: {{ python_versions | tojson }}
    steps:
      - uses: actions/checkout@v3
      - name: Setup {{ language }}
        uses: actions/setup-{{ language }}@v4
        {% if language == 'python' %}
        with:
          python-version: {% raw %}${{ matrix.python-version }}{% endraw %}
        {% endif %}
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: {% if language == 'python' %}~/.cache/pip{% elif language == 'nodejs' %}~/.npm{% endif %}
          key: {% raw %}${{ runner.os }}-{{ language }}-${{ hashFiles('**/requirements.txt', '**/package.json') }}{% endraw %}
      - name: Install dependencies
        run: |
          {% if language == 'python' %}
          pip install -r requirements.txt
          {% elif language == 'nodejs' %}
          npm install
          {% endif %}
      - name: Run linting
        run: |
          {% if language == 'python' %}
          pip install pylint
          pylint src/
          {% elif language == 'nodejs' %}
          npm run lint
          {% endif %}
      - name: Run tests
        run: |
          {% if language == 'python' %}
          pytest tests/ -v --cov
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

GITLAB_CI_TEMPLATE = r"""stages:
  - build
  - test
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

build:
  stage: build
  image: python:{{ python_version }}
  script:
    - pip install -r requirements.txt
  cache:
    paths:
      - .cache/pip
  artifacts:
    paths:
      - build/

test:
  stage: test
  image: python:{{ python_version }}
  script:
    - pip install -r requirements.txt
    - pytest tests/ -v --cov
  coverage: '/TOTAL.*\s+(\d+%)$/'

deploy:
  stage: deploy
  image: python:{{ python_version }}
  script:
    - pip install -r requirements.txt
    - python setup.py install
  only:
    - main
"""

def generate_github_actions(language: str, project_name: str, options: Optional[Dict[str, Any]] = None) -> str:
    """GitHub Actions ?쒗뵆由??앹꽦"""
    if options is None:
        options = {}
    
    context = {
        'language': language,
        'project_name': project_name,
        'runner_os': options.get('runner_os', 'ubuntu-latest'),
        'python_versions': options.get('python_versions', ['3.10', '3.11']),
    }
    template = Template(GITHUB_ACTIONS_TEMPLATE)
    return template.render(**context)

def generate_gitlab_ci(language: str, project_name: str, options: Optional[Dict[str, Any]] = None) -> str:
    """GitLab CI ?쒗뵆由??앹꽦"""
    if options is None:
        options = {}
    
    context = {
        'language': language,
        'project_name': project_name,
        'python_version': options.get('python_version', '3.10'),
    }
    template = Template(GITLAB_CI_TEMPLATE)
    return template.render(**context)

def generate_pipeline_yaml(format_type: str, language: str, project_name: str, options: Optional[Dict[str, Any]] = None) -> str:
    """CI/CD ?뚯씠?꾨씪??YAML ?앹꽦"""
    if format_type == "github_actions":
        return generate_github_actions(language, project_name, options)
    elif format_type == "gitlab_ci":
        return generate_gitlab_ci(language, project_name, options)
    else:
        return f"format: {format_type}, language: {language}"
