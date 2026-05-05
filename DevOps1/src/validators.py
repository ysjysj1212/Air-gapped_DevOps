"""CI/CD 파이프라인 검증 모듈"""
import yaml
from typing import Tuple, List

def validate_yaml(yaml_content: str) -> Tuple[bool, str]:
    """YAML 문법 검증"""
    try:
        yaml.safe_load(yaml_content)
        return True, "YAML 문법 검증 완료"
    except yaml.YAMLError as e:
        return False, f"YAML 오류: {str(e)}"

def validate_pipeline(pipeline_dict: dict) -> Tuple[bool, List[str]]:
    """CI/CD 파이프라인 구조 검증"""
    errors = []
    
    if not isinstance(pipeline_dict, dict):
        errors.append("파이프라인은 딕셔너리 형태여야 합니다")
        return False, errors
    
    if "name" not in pipeline_dict:
        errors.append("파이프라인에 'name' 필드가 필요합니다")
    
    if "on" not in pipeline_dict:
        errors.append("파이프라인에 'on' 필드 (트리거)가 필요합니다")
    
    if "jobs" not in pipeline_dict:
        errors.append("파이프라인에 'jobs' 필드가 필요합니다")
    
    return len(errors) == 0, errors
