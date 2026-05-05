import logging

import yaml
from jinja2 import Template

logger = logging.getLogger(__name__)

GITHUB_ACTIONS_TEMPLATE = """\
name: CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up {{ language_display }}
        uses: {{ setup_action }}
        with:
          {{ version_key }}: "{{ version }}"

      - name: Install dependencies
        run: {{ install_command }}

      - name: Run tests
        run: {{ test_command }}
"""

GITLAB_CI_TEMPLATE = """\
image: {{ docker_image }}

stages:
  - test

test:
  stage: test
  script:
    - {{ install_command }}
    - {{ test_command }}
"""

_LANGUAGE_DEFAULTS = {
    "python": {
        "language_display": "Python",
        "setup_action": "actions/setup-python@v5",
        "version_key": "python-version",
        "version": "3.10",
        "install_command": "pip install -r requirements.txt",
        "test_command": "pytest",
        "docker_image": "python:3.10",
    },
    "nodejs": {
        "language_display": "Node.js",
        "setup_action": "actions/setup-node@v4",
        "version_key": "node-version",
        "version": "18",
        "install_command": "npm install",
        "test_command": "npm test",
        "docker_image": "node:18",
    },
    "java": {
        "language_display": "Java",
        "setup_action": "actions/setup-java@v4",
        "version_key": "java-version",
        "version": "17",
        "install_command": "mvn install -DskipTests",
        "test_command": "mvn test",
        "docker_image": "maven:3.9-eclipse-temurin-17",
    },
    "go": {
        "language_display": "Go",
        "setup_action": "actions/setup-go@v5",
        "version_key": "go-version",
        "version": "1.21",
        "install_command": "go mod download",
        "test_command": "go test ./...",
        "docker_image": "golang:1.21",
    },
}

_DEFAULT_LANGUAGE = "python"


def generate_github_actions(language: str = "python", **overrides) -> str:
    """Render a GitHub Actions workflow YAML for the given language.

    Extra keyword arguments override the default template variables.
    """
    lang_key = language.lower()
    context = dict(_LANGUAGE_DEFAULTS.get(lang_key, _LANGUAGE_DEFAULTS[_DEFAULT_LANGUAGE]))
    context.update(overrides)

    rendered = Template(GITHUB_ACTIONS_TEMPLATE).render(**context)
    # Validate the rendered YAML is parseable
    yaml.safe_load(rendered)
    return rendered


def generate_gitlab_ci(language: str = "python", **overrides) -> str:
    """Render a GitLab CI pipeline YAML for the given language."""
    lang_key = language.lower()
    context = dict(_LANGUAGE_DEFAULTS.get(lang_key, _LANGUAGE_DEFAULTS[_DEFAULT_LANGUAGE]))
    context.update(overrides)

    rendered = Template(GITLAB_CI_TEMPLATE).render(**context)
    yaml.safe_load(rendered)
    return rendered
