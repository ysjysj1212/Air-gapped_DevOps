import yaml


def validate_yaml(content: str) -> dict:
    """Parse and validate a YAML string. Returns a dict with 'valid', 'data', and 'errors'."""
    errors = []
    data = None
    try:
        data = yaml.safe_load(content)
        if data is None:
            errors.append("YAML content is empty")
    except yaml.YAMLError as exc:
        errors.append(f"YAML parse error: {exc}")
    return {"valid": len(errors) == 0, "data": data, "errors": errors}


def validate_pipeline(pipeline_data: dict) -> dict:
    """Validate a CI/CD pipeline configuration dict. Returns a dict with 'valid' and 'errors'."""
    errors = []

    if not isinstance(pipeline_data, dict):
        return {"valid": False, "errors": ["Pipeline configuration must be a YAML mapping"]}

    required_keys = ["name", "on", "jobs"]
    for key in required_keys:
        if key not in pipeline_data:
            errors.append(f"Missing required field: '{key}'")

    jobs = pipeline_data.get("jobs")
    if isinstance(jobs, dict):
        for job_name, job_def in jobs.items():
            if not isinstance(job_def, dict):
                errors.append(f"Job '{job_name}' must be a mapping")
                continue
            if "runs-on" not in job_def:
                errors.append(f"Job '{job_name}' is missing 'runs-on'")
            if "steps" not in job_def:
                errors.append(f"Job '{job_name}' is missing 'steps'")

    return {"valid": len(errors) == 0, "errors": errors}
