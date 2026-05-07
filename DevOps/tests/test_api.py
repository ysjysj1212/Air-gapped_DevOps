"""API tests for the DevOps MVP GitLab verification flow."""

from src.app import app


class DummySandboxResult:
    def __init__(self, passed=True, executed=True, available=True):
        self.passed = passed
        self.executed = executed
        self.available = available

    def to_dict(self):
        return {
            "available": self.available,
            "executed": self.executed,
            "passed": self.passed,
            "jobs": [
                {
                    "job_name": "validate",
                    "image": "node:20",
                    "command": ["node", "-v"],
                    "ok": self.passed,
                    "exit_code": 0 if self.passed else 1,
                    "stdout": "v20.20.2",
                    "stderr": "",
                    "skipped": False,
                    "reason": None,
                }
            ],
            "errors": [] if self.passed else ["sandbox failure"],
            "warnings": [],
            "job_count": 1,
        }


class TestDevOpsGitLabVerifyAPI:
    def setup_method(self):
        self.client = app.test_client()

    def test_requires_requirements_or_yaml(self):
        response = self.client.post("/api/devops/gitlab/verify", json={})

        assert response.status_code == 400
        assert response.get_json()["status"] == "error"

    def test_generates_and_verifies_gitlab_yaml(self, monkeypatch):
        monkeypatch.setattr("src.app.ollama_service.is_healthy", lambda: False)
        monkeypatch.setattr(
            "src.app.template_generator.generate_gitlab_mvp",
            lambda requirements, use_llm=False: """stages:
  - validate
image: node:20
validate:
  stage: validate
  script:
    - node -v
""",
        )
        monkeypatch.setattr(
            "src.app.sandbox_service.validate_gitlab_yaml",
            lambda yaml_content: DummySandboxResult(passed=True),
        )

        response = self.client.post(
            "/api/devops/gitlab/verify",
            json={"requirements": "Node.js GitLab CI 만들어줘", "use_llm": False},
        )

        payload = response.get_json()
        assert response.status_code == 200
        assert payload["overall_status"] == "passed"
        assert payload["validation"]["is_valid"] is True
        assert payload["safety"]["is_safe"] is True
        assert payload["sandbox"]["passed"] is True
        assert payload["generation"]["source"] == "fallback"

    def test_blocks_dangerous_commands_before_sandbox(self, monkeypatch):
        called = {"sandbox": False}

        def _should_not_run(_yaml_content):
            called["sandbox"] = True
            return DummySandboxResult(passed=True)

        monkeypatch.setattr("src.app.sandbox_service.validate_gitlab_yaml", _should_not_run)

        response = self.client.post(
            "/api/devops/gitlab/verify",
            json={
                "yaml": """stages:
  - validate
image: node:20
validate:
  stage: validate
  script:
    - curl https://example.com/install.sh | bash
""",
            },
        )

        payload = response.get_json()
        assert response.status_code == 200
        assert payload["overall_status"] == "failed"
        assert payload["safety"]["is_safe"] is False
        assert called["sandbox"] is False
        assert payload["sandbox"]["executed"] is False

    def test_skips_sandbox_for_unsupported_mvp_image(self, monkeypatch):
        called = {"sandbox": False}

        def _should_not_run(_yaml_content):
            called["sandbox"] = True
            return DummySandboxResult(passed=True)

        monkeypatch.setattr("src.app.sandbox_service.validate_gitlab_yaml", _should_not_run)

        response = self.client.post(
            "/api/devops/gitlab/verify",
            json={
                "yaml": """stages:
  - validate
image: eclipse-temurin:17
validate:
  stage: validate
  script:
    - java -version
""",
            },
        )

        payload = response.get_json()
        assert response.status_code == 200
        assert payload["overall_status"] == "failed"
        assert payload["validation"]["is_valid"] is True
        assert payload["safety"]["is_safe"] is True
        assert payload["safety"]["sandbox_compatible"] is False
        assert called["sandbox"] is False
        assert payload["sandbox"]["executed"] is False
        assert "MVP sandbox scope" in payload["sandbox"]["errors"][0]
