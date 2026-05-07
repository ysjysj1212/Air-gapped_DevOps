"""YAML generation helpers for GitHub Actions and GitLab CI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from .llm_service import OllamaService


@dataclass(frozen=True)
class LanguageConfig:
    setup_action: str
    setup_block: str
    version_command: str
    install_command: str
    build_command: str
    test_command: str
    gitlab_image: str


LANGUAGE_CONFIGS: Dict[str, LanguageConfig] = {
    "python": LanguageConfig(
        setup_action="actions/setup-python@v5",
        setup_block='uses: actions/setup-python@v5\n        with:\n          python-version: "3.10"',
        version_command="python --version",
        install_command="python -m pip install --upgrade pip && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi",
        build_command="python -m compileall . || true",
        test_command='if [ -d tests ]; then pytest || echo "No tests configured"; else echo "No tests directory"; fi',
        gitlab_image="python:3.10",
    ),
    "javascript": LanguageConfig(
        setup_action="actions/setup-node@v4",
        setup_block='uses: actions/setup-node@v4\n        with:\n          node-version: "20"',
        version_command="node --version",
        install_command='if [ -f package-lock.json ] || [ -f npm-shrinkwrap.json ]; then npm ci; elif [ -f package.json ]; then npm install; else echo "No package.json found"; fi',
        build_command='if [ -f package.json ]; then npm run build || echo "No build script configured"; else echo "Skipping build"; fi',
        test_command='if [ -f package.json ]; then npm test || echo "No test script configured"; else echo "Skipping tests"; fi',
        gitlab_image="node:20",
    ),
    "nodejs": LanguageConfig(
        setup_action="actions/setup-node@v4",
        setup_block='uses: actions/setup-node@v4\n        with:\n          node-version: "20"',
        version_command="node --version",
        install_command='if [ -f package-lock.json ] || [ -f npm-shrinkwrap.json ]; then npm ci; elif [ -f package.json ]; then npm install; else echo "No package.json found"; fi',
        build_command='if [ -f package.json ]; then npm run build || echo "No build script configured"; else echo "Skipping build"; fi',
        test_command='if [ -f package.json ]; then npm test || echo "No test script configured"; else echo "Skipping tests"; fi',
        gitlab_image="node:20",
    ),
    "java": LanguageConfig(
        setup_action="actions/setup-java@v4",
        setup_block='uses: actions/setup-java@v4\n        with:\n          distribution: "temurin"\n          java-version: "17"',
        version_command="java -version",
        install_command='echo "Java projects typically resolve dependencies during build"',
        build_command='./gradlew build || mvn -B package || echo "No Gradle or Maven project detected"',
        test_command='./gradlew test || mvn -B test || echo "No Gradle or Maven tests detected"',
        gitlab_image="eclipse-temurin:17",
    ),
    "go": LanguageConfig(
        setup_action="actions/setup-go@v5",
        setup_block='uses: actions/setup-go@v5\n        with:\n          go-version: "1.22"',
        version_command="go version",
        install_command='if [ -f go.mod ]; then go mod download; else echo "No go.mod found"; fi',
        build_command='go build ./... || echo "No Go packages detected"',
        test_command='go test ./... || echo "No Go tests detected"',
        gitlab_image="golang:1.22",
    ),
}


def _normalize_language(language: Optional[str]) -> str:
    normalized = (language or "").strip().lower()
    if normalized in LANGUAGE_CONFIGS:
        return normalized
    return "python"


def _infer_language(requirements: str) -> str:
    lowered = requirements.lower()
    if any(keyword in lowered for keyword in ("node", "npm", "express", "javascript", "react", "next.js", "nextjs")):
        return "javascript"
    if any(keyword in lowered for keyword in ("java", "maven", "gradle", "spring", "spring boot")):
        return "java"
    if any(keyword in lowered for keyword in ("golang", "go ", "go.mod")):
        return "go"
    if any(keyword in lowered for keyword in ("python", "flask", "django", "fastapi", "pytest")):
        return "python"
    return "python"


def _include_deploy(requirements: str) -> bool:
    lowered = requirements.lower()
    return any(keyword in lowered for keyword in ("deploy", "release", "publish"))


def _mvp_test_command(language: str, project_name: str) -> str:
    normalized = _normalize_language(language)
    if normalized in {"javascript", "nodejs"}:
        return f'echo "Node.js sandbox verified for {project_name}"'
    if normalized == "python":
        return f'echo "Python sandbox verified for {project_name}"'
    if normalized == "java":
        return f'echo "Java pipeline draft ready for {project_name}"'
    if normalized == "go":
        return f'echo "Go pipeline draft ready for {project_name}"'
    return f'echo "Pipeline draft ready for {project_name}"'


def generate_github_actions(language: str, project_name: str, requirements: str = "") -> str:
    """Generate a simple but valid GitHub Actions workflow."""
    config = LANGUAGE_CONFIGS[_normalize_language(language)]
    deploy_job = ""
    if _include_deploy(requirements):
        deploy_job = """
  deploy:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Deploy placeholder
        run: echo "Deploy stage ready for customization"
"""

    return f"""name: {project_name}
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up runtime
        {config.setup_block}
      - name: Install dependencies
        run: {config.install_command}
      - name: Build / smoke check
        run: {config.build_command}

  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - name: Set up runtime
        {config.setup_block}
      - name: Runtime version
        run: {config.version_command}
      - name: Run tests
        run: {config.test_command}
{deploy_job}"""


def generate_gitlab_ci(language: str, project_name: str, requirements: str = "") -> str:
    """Generate a simple but valid GitLab CI pipeline."""
    config = LANGUAGE_CONFIGS[_normalize_language(language)]
    stages = ["build", "test"]
    deploy_job = ""
    if _include_deploy(requirements):
        stages.append("deploy")
        deploy_job = """
deploy:
  stage: deploy
  script:
    - echo "Deploy stage ready for customization"
"""

    stage_lines = "\n".join(f"  - {stage}" for stage in stages)
    return f"""stages:
{stage_lines}

image: {config.gitlab_image}

before_script:
  - {config.version_command}

build:
  stage: build
  script:
    - {config.install_command}
    - {config.build_command}

test:
  stage: test
  script:
    - {config.test_command}
{deploy_job}"""


def generate_gitlab_ci_mvp(language: str, project_name: str, requirements: str = "") -> str:
    """Generate a GitLab CI draft optimized for the DevOps MVP flow."""
    config = LANGUAGE_CONFIGS[_normalize_language(language)]
    deploy_job = ""
    stage_lines = ["  - validate", "  - test"]
    if _include_deploy(requirements):
        stage_lines.append("  - deploy")
        deploy_job = """
deploy:
  stage: deploy
  script:
    - echo "Deploy stage placeholder"
"""

    return f"""stages:
{chr(10).join(stage_lines)}

image: {config.gitlab_image}

validate:
  stage: validate
  script:
    - {config.version_command}

test:
  stage: test
  script:
    - {_mvp_test_command(language, project_name)}
{deploy_job}"""


def generate_yaml_from_requirements(
    requirements: str,
    language: str = "python",
    project_name: str = "generated-pipeline",
    ci_type: str = "github_actions",
    use_llm: bool = False,
) -> str:
    """Generate YAML for a requested CI system."""
    normalized_language = _normalize_language(language or _infer_language(requirements))
    normalized_ci_type = (ci_type or "github_actions").strip().lower()

    if normalized_ci_type == "auto":
        normalized_ci_type = "gitlab_ci" if "gitlab" in requirements.lower() else "github_actions"

    if use_llm:
        service = OllamaService()
        llm_summary = service.generate_pipeline_description(requirements)
        if llm_summary:
            requirements = f"{requirements}\n{llm_summary}"

    if normalized_ci_type == "gitlab_ci":
        return generate_gitlab_ci(normalized_language, project_name, requirements=requirements)

    return generate_github_actions(normalized_language, project_name, requirements=requirements)


class TemplateGenerator:
    """Application-friendly wrapper around the module helpers."""

    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama_service = ollama_service or OllamaService()

    def generate_yaml(self, requirements: str, ci_type: str = "auto") -> str:
        language = _infer_language(requirements)
        project_name = self._infer_project_name(requirements)
        return generate_yaml_from_requirements(
            requirements=requirements,
            language=language,
            project_name=project_name,
            ci_type=ci_type,
            use_llm=False,
        )

    def generate_with_llm(self, requirements: str, ci_type: str = "auto") -> str:
        language = _infer_language(requirements)
        project_name = self._infer_project_name(requirements)
        llm_summary = self.ollama_service.generate_pipeline_description(requirements)
        final_requirements = requirements if not llm_summary else f"{requirements}\n{llm_summary}"
        return generate_yaml_from_requirements(
            requirements=final_requirements,
            language=language,
            project_name=project_name,
            ci_type=ci_type,
            use_llm=False,
        )

    def generate_gitlab_mvp(self, requirements: str, use_llm: bool = False) -> str:
        language = _infer_language(requirements)
        project_name = self._infer_project_name(requirements)
        final_requirements = requirements
        if use_llm:
            llm_summary = self.ollama_service.generate_pipeline_description(requirements)
            if llm_summary:
                final_requirements = f"{requirements}\n{llm_summary}"
        return generate_gitlab_ci_mvp(language, project_name, requirements=final_requirements)

    @staticmethod
    def _infer_project_name(requirements: str) -> str:
        tokens = re.findall(r"[a-zA-Z0-9]+", requirements.lower())
        if not tokens:
            return "generated-pipeline"
        return "-".join(tokens[:3])
