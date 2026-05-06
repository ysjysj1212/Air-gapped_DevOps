"""
Multi-Pipeline Management Module
Manages and orchestrates multiple CI/CD pipelines
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class PipelineStatus(Enum):
    """Pipeline execution statuses"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class PipelineJob:
    """Represents a job in a pipeline"""
    name: str
    status: PipelineStatus = PipelineStatus.PENDING
    duration_ms: int = 0
    log_url: Optional[str] = None
    error_message: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)


@dataclass
class Pipeline:
    """Represents a complete CI/CD pipeline"""
    id: str
    name: str
    branch: str
    status: PipelineStatus = PipelineStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    jobs: Dict[str, PipelineJob] = field(default_factory=dict)
    duration_ms: int = 0
    coverage_percent: Optional[float] = None
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None

    def add_job(self, job: PipelineJob) -> None:
        """Add a job to the pipeline"""
        self.jobs[job.name] = job

    def update_status(self, new_status: PipelineStatus) -> None:
        """Update pipeline status"""
        self.status = new_status
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'branch': self.branch,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'duration_ms': self.duration_ms,
            'coverage_percent': self.coverage_percent,
            'commit_sha': self.commit_sha,
            'commit_message': self.commit_message,
            'jobs': {
                name: {
                    'status': job.status.value,
                    'duration_ms': job.duration_ms,
                    'error_message': job.error_message,
                    'artifacts': job.artifacts
                }
                for name, job in self.jobs.items()
            }
        }


class PipelineManager:
    """Manages multiple pipelines"""

    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self.pipeline_history: List[Pipeline] = []

    def create_pipeline(self, pipeline_id: str, name: str, branch: str) -> Pipeline:
        """Create a new pipeline"""
        pipeline = Pipeline(
            id=pipeline_id,
            name=name,
            branch=branch
        )
        self.pipelines[pipeline_id] = pipeline
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get a pipeline by ID"""
        return self.pipelines.get(pipeline_id)

    def list_pipelines(self, branch: Optional[str] = None, status: Optional[PipelineStatus] = None) -> List[Pipeline]:
        """List pipelines with optional filters"""
        pipelines = list(self.pipelines.values())
        
        if branch:
            pipelines = [p for p in pipelines if p.branch == branch]
        
        if status:
            pipelines = [p for p in pipelines if p.status == status]
        
        return sorted(pipelines, key=lambda p: p.created_at, reverse=True)

    def update_pipeline_status(self, pipeline_id: str, new_status: PipelineStatus) -> bool:
        """Update pipeline status"""
        pipeline = self.get_pipeline(pipeline_id)
        if pipeline:
            pipeline.update_status(new_status)
            return True
        return False

    def add_job_to_pipeline(self, pipeline_id: str, job: PipelineJob) -> bool:
        """Add a job to a pipeline"""
        pipeline = self.get_pipeline(pipeline_id)
        if pipeline:
            pipeline.add_job(job)
            return True
        return False

    def get_pipeline_statistics(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about pipelines"""
        pipelines = self.list_pipelines(branch=branch)
        
        total = len(pipelines)
        successful = len([p for p in pipelines if p.status == PipelineStatus.SUCCESS])
        failed = len([p for p in pipelines if p.status == PipelineStatus.FAILED])
        avg_duration = sum(p.duration_ms for p in pipelines) / total if total > 0 else 0
        avg_coverage = sum(p.coverage_percent or 0 for p in pipelines) / len([p for p in pipelines if p.coverage_percent]) if any(p.coverage_percent for p in pipelines) else None
        
        return {
            'total_pipelines': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'avg_duration_ms': avg_duration,
            'avg_coverage_percent': avg_coverage
        }

    def get_job_statistics(self, pipeline_id: str) -> Dict[str, Any]:
        """Get statistics about jobs in a pipeline"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return {}
        
        jobs = pipeline.jobs.values()
        total = len(jobs)
        successful = len([j for j in jobs if j.status == PipelineStatus.SUCCESS])
        failed = len([j for j in jobs if j.status == PipelineStatus.FAILED])
        avg_duration = sum(j.duration_ms for j in jobs) / total if total > 0 else 0
        
        return {
            'total_jobs': total,
            'successful_jobs': successful,
            'failed_jobs': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'avg_duration_ms': avg_duration
        }

    def export_pipelines(self) -> str:
        """Export all pipelines as JSON"""
        return json.dumps(
            [p.to_dict() for p in self.pipelines.values()],
            indent=2,
            default=str
        )

    def get_failed_pipelines(self, branch: Optional[str] = None) -> List[Pipeline]:
        """Get all failed pipelines"""
        return self.list_pipelines(branch=branch, status=PipelineStatus.FAILED)

    def get_recent_pipelines(self, limit: int = 10, branch: Optional[str] = None) -> List[Pipeline]:
        """Get recent pipelines"""
        pipelines = self.list_pipelines(branch=branch)
        return pipelines[:limit]

    def calculate_pipeline_trends(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Calculate pipeline trends (success rate over time)"""
        pipelines = self.list_pipelines(branch=branch)
        
        if not pipelines:
            return {'trend': 'no_data'}
        
        recent = pipelines[:10]
        success_count = len([p for p in recent if p.status == PipelineStatus.SUCCESS])
        
        if success_count >= 8:
            trend = 'improving'
        elif success_count <= 2:
            trend = 'degrading'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'recent_success_rate': (success_count / len(recent) * 100) if recent else 0,
            'recommendation': self._get_recommendation(trend)
        }

    @staticmethod
    def _get_recommendation(trend: str) -> str:
        """Get recommendation based on trend"""
        recommendations = {
            'improving': 'Pipeline quality is improving. Keep up the good work!',
            'degrading': 'Pipeline quality is degrading. Review recent changes for issues.',
            'stable': 'Pipeline quality is stable. Consider optimization opportunities.'
        }
        return recommendations.get(trend, '')
