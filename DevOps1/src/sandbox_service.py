import logging

logger = logging.getLogger(__name__)

_client = None
_available = None


def _get_client():
    global _client, _available
    if _available is not None:
        return _client
    try:
        import docker
        import docker.errors
        _client = docker.DockerClient()
        _client.ping()
        _available = True
        logger.info("Docker is available")
    except ImportError:
        logger.warning("docker package is not installed")
        _client = None
        _available = False
    except Exception as exc:  # docker.errors.DockerException and subclasses
        logger.warning("Docker is not available: %s", exc)
        _client = None
        _available = False
    return _client


def is_available() -> bool:
    """Return True if the Docker daemon is reachable."""
    _get_client()
    return bool(_available)


def run_sandbox(image: str, command: str, timeout: int = 30) -> dict:
    """Run a command in a disposable Docker container.

    Returns a dict with keys 'exit_code', 'output', and 'error'.
    """
    client = _get_client()
    if not client:
        return {
            "exit_code": -1,
            "output": "",
            "error": "Docker is not available",
        }

    try:
        import docker.errors
        result = client.containers.run(
            image,
            command=command,
            remove=True,
            stdout=True,
            stderr=True,
            timeout=timeout,
        )
        output = result.decode("utf-8") if isinstance(result, bytes) else str(result)
        return {"exit_code": 0, "output": output, "error": ""}
    except docker.errors.ContainerError as exc:
        logger.error("Container exited with non-zero status: %s", exc)
        return {"exit_code": exc.exit_status, "output": "", "error": str(exc)}
    except docker.errors.ImageNotFound as exc:
        logger.error("Docker image not found: %s", exc)
        return {"exit_code": 1, "output": "", "error": str(exc)}
    except docker.errors.APIError as exc:
        logger.error("Docker API error: %s", exc)
        return {"exit_code": 1, "output": "", "error": str(exc)}
