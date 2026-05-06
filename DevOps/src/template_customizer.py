"""
Template Customization Module
Allows users to customize CI/CD templates with custom jobs, variables, and configurations
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class CustomJob:
    """Represents a custom CI/CD job"""
    name: str
    script: List[str]
    stage: str = "custom"
    artifacts: Optional[Dict[str, Any]] = None
    needs: Optional[List[str]] = None
    cache: Optional[Dict[str, Any]] = None
    environment: Optional[str] = None
    only: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        job = {
            'script': self.script,
            'stage': self.stage
        }
        if self.artifacts:
            job['artifacts'] = self.artifacts
        if self.needs:
            job['needs'] = self.needs
        if self.cache:
            job['cache'] = self.cache
        if self.environment:
            job['environment'] = self.environment
        if self.only:
            job['only'] = self.only
        return job


class TemplateCustomizer:
    """Customizes CI/CD templates with user-defined jobs and configurations"""

    def __init__(self):
        self.custom_jobs: Dict[str, CustomJob] = {}
        self.custom_vars: Dict[str, str] = {}
        self.custom_stages: List[str] = []

    def add_custom_job(self, job: CustomJob) -> None:
        """Add a custom job to the template"""
        self.custom_jobs[job.name] = job

    def add_custom_variable(self, key: str, value: str) -> None:
        """Add a custom environment variable"""
        self.custom_vars[key] = value

    def add_custom_stage(self, stage: str) -> None:
        """Add a custom stage"""
        if stage not in self.custom_stages:
            self.custom_stages.append(stage)

    def customize_github_actions(self, template: str) -> str:
        """Customize GitHub Actions template"""
        lines = template.split('\n')
        
        # Add custom variables as env section
        if self.custom_vars:
            env_section = "env:\n"
            for key, value in self.custom_vars.items():
                env_section += f"  {key}: {value}\n"
            lines.insert(0, env_section)
        
        return '\n'.join(lines)

    def customize_gitlab_ci(self, template: str) -> str:
        """Customize GitLab CI template"""
        lines = template.split('\n')
        
        # Add custom variables
        if self.custom_vars:
            var_section = "variables:\n"
            for key, value in self.custom_vars.items():
                var_section += f"  {key}: {value}\n"
            lines.insert(0, var_section)
        
        # Add custom stages
        if self.custom_stages:
            stages_line = f"stages:\n"
            for stage in self.custom_stages:
                stages_line += f"  - {stage}\n"
            lines.insert(0, stages_line)
        
        # Add custom jobs
        if self.custom_jobs:
            jobs_section = ""
            for job_name, job in self.custom_jobs.items():
                jobs_section += f"\n{job_name}:\n"
                jobs_section += f"  stage: {job.stage}\n"
                jobs_section += "  script:\n"
                for script_line in job.script:
                    jobs_section += f"    - {script_line}\n"
                
                job_dict = job.to_dict()
                for key, value in job_dict.items():
                    if key != 'script' and key != 'stage':
                        jobs_section += f"  {key}: {value}\n"
            
            lines.append(jobs_section)
        
        return '\n'.join(lines)

    def export_customization(self) -> Dict[str, Any]:
        """Export customization as JSON"""
        return {
            'custom_jobs': {
                name: job.to_dict() for name, job in self.custom_jobs.items()
            },
            'custom_vars': self.custom_vars,
            'custom_stages': self.custom_stages
        }

    def import_customization(self, data: Dict[str, Any]) -> None:
        """Import customization from JSON"""
        for key, value in data.get('custom_vars', {}).items():
            self.add_custom_variable(key, value)
        
        for stage in data.get('custom_stages', []):
            self.add_custom_stage(stage)
        
        for job_name, job_data in data.get('custom_jobs', {}).items():
            job = CustomJob(
                name=job_name,
                script=job_data.get('script', []),
                stage=job_data.get('stage', 'custom'),
                artifacts=job_data.get('artifacts'),
                needs=job_data.get('needs'),
                cache=job_data.get('cache'),
                environment=job_data.get('environment'),
                only=job_data.get('only')
            )
            self.add_custom_job(job)


class PresetTemplates:
    """Predefined template presets"""

    @staticmethod
    def get_security_scan_preset() -> CustomJob:
        """Security scanning preset"""
        return CustomJob(
            name="security_scan",
            stage="scan",
            script=[
                "pip install bandit safety",
                "bandit -r DevOps/src -f json -o bandit-report.json",
                "safety check --json"
            ]
        )

    @staticmethod
    def get_performance_test_preset() -> CustomJob:
        """Performance testing preset"""
        return CustomJob(
            name="performance_test",
            stage="test",
            script=[
                "pip install pytest-benchmark",
                "pytest DevOps/tests/test_performance.py --benchmark-only"
            ]
        )

    @staticmethod
    def get_docker_push_preset(registry: str) -> CustomJob:
        """Docker push preset"""
        return CustomJob(
            name="docker_push",
            stage="build",
            script=[
                f"docker login -u $REGISTRY_USER -p $REGISTRY_PASSWORD {registry}",
                f"docker build -t {registry}/air-gapped-devops:$CI_COMMIT_SHA .",
                f"docker push {registry}/air-gapped-devops:$CI_COMMIT_SHA"
            ]
        )

    @staticmethod
    def get_notification_preset() -> CustomJob:
        """Notification preset"""
        return CustomJob(
            name="notify_slack",
            stage="deploy",
            script=[
                "curl -X POST $SLACK_WEBHOOK -H 'Content-type: application/json' -d '{\"text\":\"Pipeline completed\"}'"
            ]
        )
