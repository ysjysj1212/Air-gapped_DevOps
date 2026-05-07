"""CI YAML validation helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


GITHUB_RESERVED_SECTIONS = {"name", "on", "jobs", "env", "permissions", "defaults", "concurrency"}
GITLAB_RESERVED_SECTIONS = {
    "stages",
    "image",
    "services",
    "before_script",
    "after_script",
    "variables",
    "workflow",
    "default",
    "include",
    "cache",
}
MVP_SANDBOX_IMAGES = {"node:20", "python:3.10"}
DANGEROUS_GITLAB_PATTERNS = (
    (re.compile(r"\bcurl\b"), "External HTTP downloads are not allowed in the DevOps MVP."),
    (re.compile(r"\bwget\b"), "External downloads are not allowed in the DevOps MVP."),
    (re.compile(r"\bapt(-get)?\b"), "Package manager installs are not allowed in the DevOps MVP."),
    (re.compile(r"\b(apk|yum|dnf)\b"), "Package manager installs are not allowed in the DevOps MVP."),
    (re.compile(r"\bpip\s+install\b"), "Dependency installation is out of scope for the DevOps MVP."),
    (re.compile(r"\bnpm\s+(install|ci)\b"), "Dependency installation is out of scope for the DevOps MVP."),
    (re.compile(r"\bgit\s+clone\b"), "Repository cloning is not allowed in the DevOps MVP jobs."),
    (re.compile(r"\bssh\b"), "Remote shell access is not allowed in the DevOps MVP."),
    (re.compile(r"\bscp\b"), "Remote copy is not allowed in the DevOps MVP."),
    (re.compile(r"\bdocker\s+(build|push|compose|login)\b"), "Docker orchestration is not part of the DevOps MVP jobs."),
    (re.compile(r"\b(kubectl|helm)\b"), "Cluster deployment commands are out of scope for the DevOps MVP."),
)


@dataclass
class ValidationResult:
    """Structured validation result."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    detected_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "detected_type": self.detected_type,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


@dataclass
class GitLabSafetyResult:
    """Structured safety and sandbox compatibility result for GitLab CI YAML."""

    is_safe: bool
    sandbox_compatible: bool
    blocked_commands: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "sandbox_compatible": self.sandbox_compatible,
            "blocked_commands": self.blocked_commands,
            "warnings": self.warnings,
            "blocked_count": len(self.blocked_commands),
            "warning_count": len(self.warnings),
        }


def _load_yaml(yaml_content: str) -> Dict[str, Any]:
    if not yaml_content or not yaml_content.strip():
        raise ValueError("YAML content is empty")

    data = yaml.safe_load(yaml_content)
    if data is None:
        raise ValueError("YAML content is empty")
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    return _normalize_mapping(data)


def _normalize_mapping(data: Any) -> Any:
    if isinstance(data, list):
        return [_normalize_mapping(item) for item in data]
    if not isinstance(data, dict):
        return data

    normalized: Dict[str, Any] = {}
    has_on_key = "on" in data
    for key, value in data.items():
        if key is True and not has_on_key:
            normalized_key = "on"
        elif isinstance(key, str):
            normalized_key = key
        else:
            normalized_key = str(key)
        normalized[normalized_key] = _normalize_mapping(value)
    return normalized


def _detect_ci_type(data: Dict[str, Any]) -> str:
    if "jobs" in data or "on" in data:
        return "github_actions"
    if "stages" in data:
        return "gitlab_ci"
    return "github_actions"


def extract_gitlab_jobs(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return GitLab job mappings from a parsed YAML document."""
    return {
        key: value
        for key, value in data.items()
        if key not in GITLAB_RESERVED_SECTIONS and isinstance(value, dict)
    }


def extract_script_lines(job: Dict[str, Any]) -> List[str]:
    """Normalize GitLab script fields into a list of shell commands."""
    script = job.get("script")
    if isinstance(script, str):
        return [script]
    if isinstance(script, list):
        return [line for line in script if isinstance(line, str)]
    return []


def _validate_github_actions(data: Dict[str, Any]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not data.get("name"):
        errors.append("Missing required top-level field: name")
    if "on" not in data:
        errors.append("Missing required top-level field: on")

    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        errors.append("Missing required jobs definition")
    else:
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                errors.append(f"Job '{job_name}' must be a mapping")
                continue
            if "runs-on" not in job:
                errors.append(f"Job '{job_name}' is missing runs-on")
            if "steps" not in job:
                errors.append(f"Job '{job_name}' is missing steps")

    unknown_top_level = set(data.keys()) - GITHUB_RESERVED_SECTIONS
    if unknown_top_level:
        warnings.append(
            "Unknown top-level sections for GitHub Actions: "
            + ", ".join(sorted((str(section) for section in unknown_top_level), key=str))
        )

    return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings, detected_type="github_actions")


def _validate_gitlab_ci(data: Dict[str, Any]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    stages = data.get("stages")
    if not isinstance(stages, list) or not stages:
        errors.append("Missing required stages definition")

    jobs = {key: value for key, value in data.items() if key not in GITLAB_RESERVED_SECTIONS}
    if not jobs:
        errors.append("No GitLab CI jobs were found")
    else:
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                errors.append(f"Job '{job_name}' must be a mapping")
                continue
            if "script" not in job:
                errors.append(f"Job '{job_name}' is missing script")

    if "image" not in data:
        warnings.append("No default image defined; jobs may need job-level images")

    return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings, detected_type="gitlab_ci")


def validate_ci_yaml(yaml_content: str, ci_type: str = "auto") -> ValidationResult:
    """Validate GitHub Actions or GitLab CI YAML."""
    try:
        data = _load_yaml(yaml_content)
    except (yaml.YAMLError, ValueError) as exc:
        return ValidationResult(is_valid=False, errors=[str(exc)], detected_type=None)

    requested_type = (ci_type or "auto").strip().lower()
    detected_type = _detect_ci_type(data)
    effective_type = detected_type if requested_type == "auto" else requested_type

    if effective_type == "gitlab_ci":
        result = _validate_gitlab_ci(data)
    else:
        result = _validate_github_actions(data)

    result.detected_type = detected_type
    return result


def inspect_gitlab_safety(yaml_content: str) -> GitLabSafetyResult:
    """Inspect GitLab CI YAML for blocked MVP commands and sandbox compatibility."""
    try:
        data = _load_yaml(yaml_content)
    except ValueError as exc:
        return GitLabSafetyResult(
            is_safe=False,
            sandbox_compatible=False,
            blocked_commands=[{"job": "pipeline", "command": "<invalid-yaml>", "reason": str(exc)}],
            warnings=[],
        )

    pipeline_image = data.get("image") if isinstance(data.get("image"), str) else None
    blocked_commands: List[Dict[str, str]] = []
    warnings: List[str] = []
    sandbox_compatible = True

    for job_name, job in extract_gitlab_jobs(data).items():
        image = job.get("image") if isinstance(job.get("image"), str) else pipeline_image
        if image not in MVP_SANDBOX_IMAGES:
            sandbox_compatible = False
            warnings.append(
                f"Job '{job_name}' uses sandbox-unsupported image '{image or 'none'}'. "
                "Supported images: node:20, python:3.10"
            )

        for command in extract_script_lines(job):
            for pattern, reason in DANGEROUS_GITLAB_PATTERNS:
                if pattern.search(command):
                    blocked_commands.append(
                        {
                            "job": job_name,
                            "command": command,
                            "reason": reason,
                        }
                    )
                    break

    return GitLabSafetyResult(
        is_safe=not blocked_commands,
        sandbox_compatible=sandbox_compatible,
        blocked_commands=blocked_commands,
        warnings=warnings,
    )


def suggest_fixes(yaml_content: str, result: ValidationResult) -> List[str]:
    """Provide simple actionable fix suggestions."""
    suggestions: List[str] = []

    if any("empty" in error.lower() for error in result.errors):
        suggestions.append("Provide non-empty YAML content before validation.")
    if any("name" in error.lower() for error in result.errors):
        suggestions.append("Add a top-level 'name' field for GitHub Actions workflows.")
    if any("jobs" in error.lower() for error in result.errors):
        suggestions.append("Define at least one job under the top-level 'jobs' section.")
    if any("stages" in error.lower() for error in result.errors):
        suggestions.append("Define a top-level 'stages' list for GitLab CI pipelines.")
    if any("script" in error.lower() for error in result.errors):
        suggestions.append("Ensure every GitLab CI job contains a 'script' section.")
    if any("runs-on" in error.lower() for error in result.errors):
        suggestions.append("Ensure every GitHub Actions job defines 'runs-on'.")
    if not suggestions and not result.is_valid:
        suggestions.append("Review the YAML structure and compare it with a known-good CI template.")

    return suggestions
