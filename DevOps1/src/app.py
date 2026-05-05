"""Flask 메인 애플리케이션"""
from flask import Flask, request, jsonify
from src.llm_service import generate_pipeline_description
from src.template_generator import generate_pipeline_yaml
from src.validators import validate_yaml, validate_pipeline
from src.sandbox_service import SandboxService
import yaml

app = Flask(__name__)
sandbox = SandboxService()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "healthy", "message": "DevOps1 API Server Running!"})

@app.route("/health", methods=["GET"])
def health():
    """헬스 체크 엔드포인트"""
    return jsonify({
        "status": "healthy",
        "services": {
            "flask": "running",
            "docker": "connected" if sandbox.is_available() else "unavailable",
            "ollama": "checking..."
        }
    })

@app.route("/api/generate-ci", methods=["POST"])
def generate_ci():
    """CI/CD 파이프라인 생성 엔드포인트"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "요청 본문이 비어있습니다"}), 400
        
        project_description = data.get("project_description")
        language = data.get("language", "python")
        requirements = data.get("requirements", [])
        format_type = data.get("format", "github_actions")
        
        if not project_description:
            return jsonify({"status": "error", "message": "project_description이 필요합니다"}), 400
        
        # YAML 생성
        pipeline_yaml = generate_pipeline_yaml(format_type, language, project_description)
        
        # YAML 검증
        is_valid, validation_msg = validate_yaml(pipeline_yaml)
        if not is_valid:
            return jsonify({
                "status": "error",
                "message": validation_msg
            }), 400
        
        # 샌드박스에서 검증 실행
        validation_result = sandbox.run_validation(pipeline_yaml)
        
        return jsonify({
            "status": "success",
            "pipeline": pipeline_yaml,
            "format": format_type,
            "language": language,
            "validation": validation_result
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "엔드포인트를 찾을 수 없습니다"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "내부 서버 오류"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
