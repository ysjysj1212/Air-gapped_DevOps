"""Parser for extracting pipeline metadata from YAML configuration."""

import yaml


def parse_pipeline(content: str) -> dict:
    """Parse a CI pipeline YAML string and return a normalised metadata dict.

    Keys in the returned dict:
        - language: detected language hint (str | None)
        - stages: list of stage names
        - jobs: list of job name strings
        - image: top-level Docker image (str | None)
    """
    try:
        config = yaml.safe_load(content)
    except yaml.YAMLError:
        return {"language": None, "stages": [], "jobs": [], "image": None}

    if not isinstance(config, dict):
        return {"language": None, "stages": [], "jobs": [], "image": None}

    image = config.get("image")
    stages = config.get("stages", [])
    if not isinstance(stages, list):
        stages = []

    # Detect language from the top-level image tag
    language = None
    if isinstance(image, str):
        for lang in ("python", "node", "java", "go", "ruby"):
            if lang in image.lower():
                language = lang
                break

    # Collect job names (keys that are not reserved GitLab CI keywords)
    reserved = {"image", "stages", "variables", "include", "workflow", "default"}
    jobs = [k for k in config if k not in reserved]

    return {
        "language": language,
        "stages": stages,
        "jobs": jobs,
        "image": image,
    }
