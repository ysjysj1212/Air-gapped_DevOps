"""CI pipeline runner - executes a pipeline YAML in a subprocess."""

import subprocess
import logging

logger = logging.getLogger(__name__)


def run(pipeline_yaml: str, workdir: str = ".") -> dict:
    """Simulate running a CI pipeline described in *pipeline_yaml*.

    This is a simplified runner that executes the first script entry found
    in a GitLab-CI style YAML.  Returns a dict with 'exit_code' and 'output'.
    """
    import yaml  # local import keeps startup light

    try:
        config = yaml.safe_load(pipeline_yaml)
    except yaml.YAMLError as exc:
        return {"exit_code": 1, "output": f"Invalid YAML: {exc}"}

    if not isinstance(config, dict):
        return {"exit_code": 1, "output": "Pipeline config is not a mapping"}

    outputs = []
    for job_name, job in config.items():
        if not isinstance(job, dict):
            continue
        scripts = job.get("script", [])
        if isinstance(scripts, str):
            scripts = [scripts]
        for cmd in scripts:
            logger.info("Running [%s]: %s", job_name, cmd)
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=workdir,
                    timeout=60,
                )
                outputs.append(result.stdout + result.stderr)
                if result.returncode != 0:
                    return {
                        "exit_code": result.returncode,
                        "output": "\n".join(outputs),
                    }
            except subprocess.TimeoutExpired:
                return {"exit_code": 1, "output": f"Command timed out: {cmd}"}

    return {"exit_code": 0, "output": "\n".join(outputs)}
