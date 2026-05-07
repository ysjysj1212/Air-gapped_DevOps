"""Helpers for running GitLab CI smoke checks in the local Docker sandbox."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .validators import _load_yaml, extract_gitlab_jobs


SANDBOX_SMOKE_COMMANDS = {
    "node:20": ["node", "-v"],
    "python:3.10": ["python", "--version"],
}


@dataclass
class SandboxJobResult:
    """Sandbox execution result for a single GitLab CI job."""

    job_name: str
    image: str
    command: List[str]
    ok: bool
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    skipped: bool = False
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_name": self.job_name,
            "image": self.image,
            "command": self.command,
            "ok": self.ok,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "skipped": self.skipped,
            "reason": self.reason,
        }


@dataclass
class SandboxValidationResult:
    """Overall sandbox validation result."""

    available: bool
    executed: bool
    passed: bool
    jobs: List[SandboxJobResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "executed": self.executed,
            "passed": self.passed,
            "jobs": [job.to_dict() for job in self.jobs],
            "errors": self.errors,
            "warnings": self.warnings,
            "job_count": len(self.jobs),
        }


class SandboxService:
    """Run smoke validations for GitLab CI jobs through sandbox.sh."""

    def __init__(self, sandbox_script_path: Optional[str] = None, timeout_seconds: int = 30):
        default_path = Path(__file__).resolve().parents[1] / "sandbox.sh"
        self.sandbox_script_path = Path(sandbox_script_path) if sandbox_script_path else default_path
        self.timeout_seconds = timeout_seconds

    def validate_gitlab_yaml(self, yaml_content: str) -> SandboxValidationResult:
        """Execute sandbox smoke checks for GitLab CI jobs with supported images."""
        availability_error = self._availability_error()
        if availability_error:
            return SandboxValidationResult(
                available=False,
                executed=False,
                passed=False,
                errors=[availability_error],
            )

        try:
            data = _load_yaml(yaml_content)
        except ValueError as exc:
            return SandboxValidationResult(
                available=True,
                executed=False,
                passed=False,
                errors=[str(exc)],
            )

        pipeline_image = data.get("image") if isinstance(data.get("image"), str) else None
        jobs: List[SandboxJobResult] = []
        errors: List[str] = []
        warnings: List[str] = []
        executed = False

        for job_name, job in extract_gitlab_jobs(data).items():
            if "script" not in job:
                continue

            image = job.get("image") if isinstance(job.get("image"), str) else pipeline_image
            smoke_command = SANDBOX_SMOKE_COMMANDS.get(image or "")
            if not image or smoke_command is None:
                reason = (
                    f"Job '{job_name}' cannot be smoke-validated automatically. "
                    "Supported images: node:20, python:3.10"
                )
                jobs.append(
                    SandboxJobResult(
                        job_name=job_name,
                        image=image or "",
                        command=[],
                        ok=False,
                        skipped=True,
                        reason=reason,
                    )
                )
                errors.append(reason)
                continue

            executed = True
            completed = subprocess.run(
                [
                    "bash",
                    str(self.sandbox_script_path),
                    "--network",
                    "none",
                    "--timeout",
                    str(self.timeout_seconds),
                    image,
                    *smoke_command,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            ok = completed.returncode == 0
            jobs.append(
                SandboxJobResult(
                    job_name=job_name,
                    image=image,
                    command=smoke_command,
                    ok=ok,
                    exit_code=completed.returncode,
                    stdout=completed.stdout.strip(),
                    stderr=completed.stderr.strip(),
                    reason=None if ok else f"Sandbox command failed for job '{job_name}'",
                )
            )
            if not ok:
                errors.append(f"Sandbox command failed for job '{job_name}'")

        if not jobs:
            warnings.append("No GitLab jobs with script sections were found for sandbox validation.")

        return SandboxValidationResult(
            available=True,
            executed=executed,
            passed=executed and not errors,
            jobs=jobs,
            errors=errors,
            warnings=warnings,
        )

    def _availability_error(self) -> Optional[str]:
        if not self.sandbox_script_path.exists():
            return f"sandbox script not found: {self.sandbox_script_path}"
        if shutil.which("docker") is None:
            return "docker is not installed or not in PATH"
        return None
