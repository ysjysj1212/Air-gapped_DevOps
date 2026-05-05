import logging
import os

from flask import Flask, jsonify, request

_DEBUG = os.getenv("FLASK_ENV", "production") == "development"

from src.llm_service import ask_ollama
from src.sandbox_service import is_available as docker_available
from src.template_generator import generate_github_actions
from src.validators import validate_pipeline, validate_yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.get("/")
def home():
    return jsonify({"message": "CI/CD Pipeline Generator API", "version": "1.0.0"})


@app.get("/health")
def health():
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    return jsonify(
        {
            "status": "healthy",
            "services": {
                "flask": "running",
                "docker": "connected" if docker_available() else "unavailable",
                "ollama": ollama_url,
            },
        }
    )


@app.post("/api/generate-ci")
def generate_ci():
    body = request.get_json(silent=True) or {}

    project_description = body.get("project_description", "").strip()
    if not project_description:
        return jsonify({"status": "error", "message": "project_description is required"}), 400

    language = body.get("language", "python").strip().lower()
    requirements = body.get("requirements", [])

    # Build an LLM prompt and attempt to get a customised pipeline
    prompt = (
        f"Generate a GitHub Actions CI/CD pipeline YAML for a {language} project.\n"
        f"Project description: {project_description}\n"
        f"Requirements: {', '.join(requirements) if requirements else 'standard CI'}\n"
        "Return only the YAML content without any explanation."
    )

    pipeline_yaml = None
    try:
        llm_response = ask_ollama(prompt)
        result = validate_yaml(llm_response)
        if result["valid"]:
            pipeline_result = validate_pipeline(result["data"])
            if pipeline_result["valid"]:
                pipeline_yaml = llm_response
    except RuntimeError as exc:
        logger.warning("LLM unavailable, using template: %s", exc)

    # Fall back to a static template when LLM is unavailable or returns invalid YAML
    if pipeline_yaml is None:
        pipeline_yaml = generate_github_actions(language=language)

    return jsonify(
        {
            "status": "success",
            "pipeline": pipeline_yaml,
            "format": "github_actions",
        }
    )


@app.errorhandler(404)
def not_found(exc):  # pylint: disable=unused-argument
    return jsonify({"status": "error", "message": "Not found"}), 404


@app.errorhandler(405)
def method_not_allowed(exc):  # pylint: disable=unused-argument
    return jsonify({"status": "error", "message": "Method not allowed"}), 405


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=_DEBUG)
