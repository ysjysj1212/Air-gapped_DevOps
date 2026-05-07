"""
Flask application for CI/CD Pipeline Generator
Includes YAML generation, validation, and advanced features
"""

from flask import Flask, request, jsonify
from datetime import datetime
from typing import Tuple
import uuid
import os
from pathlib import Path

from .llm_service import OllamaService
from .template_generator import TemplateGenerator
from .sandbox_service import SandboxService, SandboxValidationResult
from .validators import inspect_gitlab_safety, validate_ci_yaml
from .yaml_diff import YAMLDiffer
from .template_customizer import TemplateCustomizer, CustomJob
from .pipeline_manager import PipelineManager, Pipeline, PipelineJob, PipelineStatus

app = Flask(__name__)

# Initialize services
ollama_service = OllamaService()
template_generator = TemplateGenerator()
yaml_differ = YAMLDiffer()
template_customizer = TemplateCustomizer()
pipeline_manager = PipelineManager()
sandbox_service = SandboxService()

# YAML 저장 디렉토리 설정
GENERATED_YAMLS_DIR = Path(__file__).parent.parent.parent / "generated_yamls"
GENERATED_YAMLS_DIR.mkdir(exist_ok=True)


def save_generated_yaml(yaml_content: str, prefix: str = "auto") -> str:
    """
    생성된 YAML을 generated_yamls 디렉토리에 자동 저장
    
    Args:
        yaml_content: 저장할 YAML 내용
        prefix: 파일명 prefix (llm, auto, validate 등)
    
    Returns:
        저장된 파일 경로
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{prefix}-{timestamp}.yml"
    filepath = GENERATED_YAMLS_DIR / filename
    
    with open(filepath, 'w') as f:
        f.write(yaml_content)
    
    return str(filepath)


# ===== Basic Endpoints =====

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'status': 'ok',
        'app': 'CI/CD Pipeline Generator',
        'version': '2.0.0',
        'features': [
            'YAML Generation',
            'YAML Validation',
            'GitLab Sandbox Verification',
            'YAML Diff & Comparison',
            'Template Customization',
            'Multi-Pipeline Management',
            'Ollama LLM Integration'
        ]
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


def _skip_sandbox_result(reason: str) -> SandboxValidationResult:
    return SandboxValidationResult(
        available=True,
        executed=False,
        passed=False,
        errors=[reason],
    )


def _build_gitlab_mvp_yaml(requirements: str, use_llm: bool) -> Tuple[str, str]:
    if use_llm and ollama_service.is_healthy():
        return template_generator.generate_gitlab_mvp(requirements, use_llm=True), 'llm'
    source = 'fallback'
    if use_llm:
        source = 'fallback_without_ollama'
    return template_generator.generate_gitlab_mvp(requirements, use_llm=False), source


# ===== Ollama Integration Endpoints =====

@app.route('/api/ollama/health', methods=['GET'])
def ollama_health():
    """Check Ollama service health"""
    try:
        is_healthy = ollama_service.is_healthy()
        return jsonify({
            'status': 'ok' if is_healthy else 'error',
            'ollama_healthy': is_healthy
        }), 200 if is_healthy else 503
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ollama/models', methods=['GET'])
def ollama_models():
    """List available Ollama models"""
    try:
        models = ollama_service.list_models()
        return jsonify({
            'status': 'ok',
            'models': models
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ollama/ask', methods=['POST'])
def ollama_ask():
    """Ask Ollama LLM a question"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        model = data.get('model', 'llama2')
        
        if not prompt:
            return jsonify({'status': 'error', 'message': 'Prompt is required'}), 400
        
        response = ollama_service.ask(prompt, model)
        return jsonify({
            'status': 'ok',
            'prompt': prompt,
            'model': model,
            'response': response
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== YAML Generation Endpoints =====

@app.route('/api/generate-yaml', methods=['POST'])
def generate_yaml():
    """Generate YAML from requirements"""
    try:
        data = request.get_json()
        requirements = data.get('requirements', '')
        ci_type = data.get('ci_type', 'auto')  # github_actions, gitlab_ci, auto
        use_llm = data.get('use_llm', False)
        
        if not requirements:
            return jsonify({'status': 'error', 'message': 'Requirements are required'}), 400
        
        if use_llm and ollama_service.is_healthy():
            yaml_content = template_generator.generate_with_llm(requirements, ci_type)
            prefix = 'llm'
        else:
            yaml_content = template_generator.generate_yaml(requirements, ci_type)
            prefix = 'auto'
        
        # 자동 저장
        saved_file = save_generated_yaml(yaml_content, prefix=prefix)
        
        return jsonify({
            'status': 'ok',
            'yaml': yaml_content,
            'ci_type': ci_type,
            'saved_file': saved_file  # ← 저장된 파일 경로
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== YAML Validation Endpoints =====

@app.route('/api/validate-yaml', methods=['POST'])
def validate_yaml():
    """Validate CI/CD YAML"""
    try:
        data = request.get_json()
        yaml_content = data.get('yaml', '')
        ci_type = data.get('ci_type', 'auto')
        
        if not yaml_content:
            return jsonify({'status': 'error', 'message': 'YAML content is required'}), 400
        
        result = validate_ci_yaml(yaml_content, ci_type)
        return jsonify(result.to_dict()), 200 if result.is_valid else 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/devops/gitlab/verify', methods=['POST'])
def devops_gitlab_verify():
    """Run the DevOps MVP flow for GitLab CI generation, validation, and sandbox checks."""
    try:
        data = request.get_json() or {}
        requirements = (data.get('requirements') or '').strip()
        yaml_content = (data.get('yaml') or '').strip()
        use_llm = bool(data.get('use_llm', False))

        if not requirements and not yaml_content:
            return jsonify({'status': 'error', 'message': 'Requirements or YAML content is required'}), 400

        generation_source = 'provided_yaml'
        if not yaml_content:
            yaml_content, generation_source = _build_gitlab_mvp_yaml(requirements, use_llm)

        validation = validate_ci_yaml(yaml_content, 'gitlab_ci')
        safety = inspect_gitlab_safety(yaml_content)

        skip_reason = 'Sandbox validation was skipped because YAML validation or safety checks failed.'
        if validation.is_valid and safety.is_safe and not safety.sandbox_compatible:
            skip_reason = (
                'Sandbox validation was skipped because one or more jobs use images outside '
                'the DevOps MVP sandbox scope. Supported images: node:20, python:3.10.'
            )

        sandbox_result = _skip_sandbox_result(skip_reason)
        if validation.is_valid and safety.is_safe and safety.sandbox_compatible:
            sandbox_result = sandbox_service.validate_gitlab_yaml(yaml_content)

        overall_status = 'passed' if validation.is_valid and safety.is_safe and sandbox_result.passed else 'failed'

        # 자동 저장: YAML을 generated_yamls 디렉토리에 저장
        prefix = 'llm' if (generation_source == 'llm' and use_llm) else 'auto'
        saved_file = save_generated_yaml(yaml_content, prefix=prefix)

        return jsonify({
            'status': 'ok',
            'overall_status': overall_status,
            'generation': {
                'source': generation_source,
                'llm_requested': use_llm,
            },
            'yaml': yaml_content,
            'saved_file': saved_file,  # ← 저장된 파일 경로
            'validation': validation.to_dict(),
            'safety': safety.to_dict(),
            'sandbox': sandbox_result.to_dict(),
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== YAML Diff Endpoints =====

@app.route('/api/yaml/diff', methods=['POST'])
def yaml_diff():
    """Compare two YAML files"""
    try:
        data = request.get_json()
        old_yaml = data.get('old_yaml', '')
        new_yaml = data.get('new_yaml', '')
        format_type = data.get('format', 'json')  # json or html
        
        if not old_yaml or not new_yaml:
            return jsonify({'status': 'error', 'message': 'Both YAML contents are required'}), 400
        
        diffs = yaml_differ.compare_yaml(old_yaml, new_yaml)
        summary = yaml_differ.generate_diff_summary(diffs)
        
        if format_type == 'html':
            return jsonify({
                'status': 'ok',
                'summary': summary,
                'diff_html': yaml_differ.format_diff_html(diffs)
            }), 200
        else:
            return jsonify({
                'status': 'ok',
                'summary': summary,
                'diff_json': yaml_differ.format_diff_json(diffs)
            }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== Template Customization Endpoints =====

@app.route('/api/template/customize', methods=['POST'])
def customize_template():
    """Customize CI/CD template"""
    try:
        data = request.get_json()
        base_yaml = data.get('base_yaml', '')
        ci_type = data.get('ci_type', 'gitlab_ci')
        customizations = data.get('customizations', {})
        
        if not base_yaml:
            return jsonify({'status': 'error', 'message': 'Base YAML is required'}), 400
        
        # Import customizations
        template_customizer.import_customization(customizations)
        
        # Customize template
        if ci_type == 'gitlab_ci':
            customized = template_customizer.customize_gitlab_ci(base_yaml)
        else:
            customized = template_customizer.customize_github_actions(base_yaml)
        
        return jsonify({
            'status': 'ok',
            'customized_yaml': customized,
            'customization_summary': template_customizer.export_customization()
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/template/presets', methods=['GET'])
def get_template_presets():
    """Get available template presets"""
    return jsonify({
        'status': 'ok',
        'presets': [
            {
                'name': 'security_scan',
                'description': 'Add security scanning (Bandit, Safety)',
                'stage': 'scan'
            },
            {
                'name': 'performance_test',
                'description': 'Add performance testing benchmarks',
                'stage': 'test'
            },
            {
                'name': 'docker_push',
                'description': 'Add Docker image push to registry',
                'stage': 'build'
            },
            {
                'name': 'slack_notification',
                'description': 'Add Slack notifications',
                'stage': 'deploy'
            }
        ]
    }), 200


# ===== Pipeline Management Endpoints =====

@app.route('/api/pipelines', methods=['GET'])
def list_pipelines():
    """List all pipelines"""
    branch = request.args.get('branch')
    status = request.args.get('status')
    
    pipelines = pipeline_manager.list_pipelines(branch=branch)
    
    return jsonify({
        'status': 'ok',
        'pipelines': [p.to_dict() for p in pipelines]
    }), 200


@app.route('/api/pipelines', methods=['POST'])
def create_pipeline():
    """Create a new pipeline"""
    try:
        data = request.get_json()
        name = data.get('name', 'Pipeline')
        branch = data.get('branch', 'main')
        
        pipeline_id = str(uuid.uuid4())[:8]
        pipeline = pipeline_manager.create_pipeline(pipeline_id, name, branch)
        
        return jsonify({
            'status': 'ok',
            'pipeline': pipeline.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/pipelines/<pipeline_id>', methods=['GET'])
def get_pipeline(pipeline_id):
    """Get pipeline details"""
    pipeline = pipeline_manager.get_pipeline(pipeline_id)
    
    if not pipeline:
        return jsonify({'status': 'error', 'message': 'Pipeline not found'}), 404
    
    return jsonify({
        'status': 'ok',
        'pipeline': pipeline.to_dict()
    }), 200


@app.route('/api/pipelines/<pipeline_id>/status', methods=['PUT'])
def update_pipeline_status(pipeline_id):
    """Update pipeline status"""
    try:
        data = request.get_json()
        new_status = data.get('status', 'pending')
        
        success = pipeline_manager.update_pipeline_status(pipeline_id, PipelineStatus(new_status))
        
        if not success:
            return jsonify({'status': 'error', 'message': 'Pipeline not found'}), 404
        
        pipeline = pipeline_manager.get_pipeline(pipeline_id)
        return jsonify({
            'status': 'ok',
            'pipeline': pipeline.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/pipelines/<pipeline_id>/jobs', methods=['POST'])
def add_pipeline_job(pipeline_id):
    """Add a job to a pipeline"""
    try:
        data = request.get_json()
        job_name = data.get('name', 'job')
        
        job = PipelineJob(name=job_name)
        success = pipeline_manager.add_job_to_pipeline(pipeline_id, job)
        
        if not success:
            return jsonify({'status': 'error', 'message': 'Pipeline not found'}), 404
        
        return jsonify({
            'status': 'ok',
            'message': f'Job {job_name} added to pipeline'
        }), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/pipelines/statistics', methods=['GET'])
def pipeline_statistics():
    """Get pipeline statistics"""
    branch = request.args.get('branch')
    stats = pipeline_manager.get_pipeline_statistics(branch=branch)
    
    return jsonify({
        'status': 'ok',
        'statistics': stats
    }), 200


@app.route('/api/pipelines/trends', methods=['GET'])
def pipeline_trends():
    """Get pipeline trends"""
    branch = request.args.get('branch')
    trends = pipeline_manager.calculate_pipeline_trends(branch=branch)
    
    return jsonify({
        'status': 'ok',
        'trends': trends
    }), 200


# ===== Error Handlers =====

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
