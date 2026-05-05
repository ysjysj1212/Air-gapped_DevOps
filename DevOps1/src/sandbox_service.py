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
        _client = docker.DockerClient()
        _client.ping()
        _available = True
        logger.info("Docker is available")
    except Exception as exc:  # pylint: disable=broad-except
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
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Sandbox run failed: %s", exc)
        return {"exit_code": 1, "output": "", "error": str(exc)}
