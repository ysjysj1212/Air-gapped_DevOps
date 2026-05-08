import importlib.util
from pathlib import Path


def load_llm_cli():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "llm-cli.py"
    spec = importlib.util.spec_from_file_location("llm_cli", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_infer_language_from_requirements_for_node():
    module = load_llm_cli()

    language = module.infer_language_from_requirements(
        "Node.js 프로젝트인데 npm test와 build가 필요한 GitLab CI를 만들어줘"
    )

    assert language == "node"


def test_infer_language_from_requirements_for_python():
    module = load_llm_cli()

    language = module.infer_language_from_requirements(
        "Python Flask 프로젝트고 pytest를 실행하는 GitLab CI를 만들어줘"
    )

    assert language == "python"


def test_infer_requested_version_for_node():
    module = load_llm_cli()

    version = module.infer_requested_version(
        "Node.js 프로젝트 중이고 node 버전은 18로 쓰고 있어", "node"
    )

    assert version == "18"


def test_infer_requested_version_for_python():
    module = load_llm_cli()

    version = module.infer_requested_version(
        "python 프로젝트 중이고 python 버전을 3.11로 하고 있어", "python"
    )

    assert version == "3.11"


def test_build_gitlab_ci_for_node_projects():
    module = load_llm_cli()

    yaml_content = module.build_gitlab_ci("Node.js 프로젝트", "node")

    assert "image: node:20" in yaml_content
    assert yaml_content.count("- docker-socket") == 4
    assert "node --version" in yaml_content
    assert "npm --version" in yaml_content
    assert "merge_request_event" in yaml_content


def test_build_gitlab_ci_respects_requested_node_version():
    module = load_llm_cli()

    yaml_content = module.build_gitlab_ci(
        "Node.js 프로젝트고 node 버전은 18을 사용 중이야", "node"
    )

    assert "image: node:18" in yaml_content


def test_build_gitlab_ci_for_python_projects():
    module = load_llm_cli()

    yaml_content = module.build_gitlab_ci("Python 프로젝트", "python")

    assert "image: python:3.10" in yaml_content
    assert yaml_content.count("- docker-socket") == 4
    assert "python --version" in yaml_content
    assert "pip --version" in yaml_content
    assert "Merge-ready pipeline checks passed" in yaml_content


def test_build_gitlab_ci_respects_requested_python_version():
    module = load_llm_cli()

    yaml_content = module.build_gitlab_ci(
        "python 프로젝트 중이고 python 버전 3.11로 맞춰줘", "python"
    )

    assert "image: python:3.11" in yaml_content
