"""
Advanced Features Test Suite
Tests for YAML diff, template customization, and pipeline management
"""

import pytest
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from yaml_diff import YAMLDiffer
from template_customizer import TemplateCustomizer, CustomJob
from pipeline_manager import PipelineManager, PipelineStatus, PipelineJob


class TestYAMLDiffer:
    """Test YAML Diff functionality"""

    def test_compare_identical_yaml(self):
        """Test comparing identical YAML files"""
        yaml1 = """
name: Test
jobs:
  build:
    runs-on: ubuntu-latest
"""
        differ = YAMLDiffer()
        diffs = differ.compare_yaml(yaml1, yaml1)
        assert len(diffs) == 0

    def test_compare_added_fields(self):
        """Test detecting added fields"""
        yaml1 = "name: Test\n"
        yaml2 = "name: Test\nversion: 1.0\n"
        
        differ = YAMLDiffer()
        diffs = differ.compare_yaml(yaml1, yaml2)
        
        assert len(diffs) > 0
        assert any(d.type == 'added' for d in diffs)

    def test_compare_removed_fields(self):
        """Test detecting removed fields"""
        yaml1 = "name: Test\nversion: 1.0\n"
        yaml2 = "name: Test\n"
        
        differ = YAMLDiffer()
        diffs = differ.compare_yaml(yaml1, yaml2)
        
        assert len(diffs) > 0
        assert any(d.type == 'removed' for d in diffs)

    def test_compare_modified_values(self):
        """Test detecting modified values"""
        yaml1 = "timeout: 300\n"
        yaml2 = "timeout: 600\n"
        
        differ = YAMLDiffer()
        diffs = differ.compare_yaml(yaml1, yaml2)
        
        assert len(diffs) > 0
        assert any(d.type == 'modified' for d in diffs)

    def test_generate_diff_summary(self):
        """Test generating diff summary"""
        yaml1 = "name: Test\nversion: 1.0\n"
        yaml2 = "name: Test\nversion: 2.0\nauthor: John\n"
        
        differ = YAMLDiffer()
        diffs = differ.compare_yaml(yaml1, yaml2)
        summary = differ.generate_diff_summary(diffs)
        
        assert summary['total_changes'] > 0
        assert 'added' in summary
        assert 'modified' in summary

    def test_format_diff_html(self):
        """Test formatting diff as HTML"""
        yaml1 = "name: Test\n"
        yaml2 = "name: Test\nversion: 1.0\n"
        
        differ = YAMLDiffer()
        diffs = differ.compare_yaml(yaml1, yaml2)
        html = differ.format_diff_html(diffs)
        
        assert '<table' in html
        assert 'diff-table' in html
        assert 'added' in html

    def test_format_diff_json(self):
        """Test formatting diff as JSON"""
        yaml1 = "name: Test\n"
        yaml2 = "name: Test\nversion: 1.0\n"
        
        differ = YAMLDiffer()
        diffs = differ.compare_yaml(yaml1, yaml2)
        json_str = differ.format_diff_json(diffs)
        
        assert '[' in json_str
        assert 'type' in json_str
        assert 'path' in json_str


class TestTemplateCustomizer:
    """Test Template Customization functionality"""

    def test_add_custom_job(self):
        """Test adding custom job"""
        customizer = TemplateCustomizer()
        job = CustomJob(
            name="test_job",
            script=["echo 'test'"],
            stage="test"
        )
        customizer.add_custom_job(job)
        
        assert "test_job" in customizer.custom_jobs
        assert customizer.custom_jobs["test_job"].stage == "test"

    def test_add_custom_variable(self):
        """Test adding custom variable"""
        customizer = TemplateCustomizer()
        customizer.add_custom_variable("MY_VAR", "my_value")
        
        assert "MY_VAR" in customizer.custom_vars
        assert customizer.custom_vars["MY_VAR"] == "my_value"

    def test_add_custom_stage(self):
        """Test adding custom stage"""
        customizer = TemplateCustomizer()
        customizer.add_custom_stage("security")
        
        assert "security" in customizer.custom_stages

    def test_customize_gitlab_ci(self):
        """Test customizing GitLab CI template"""
        customizer = TemplateCustomizer()
        customizer.add_custom_variable("CI_DEBUG", "true")
        customizer.add_custom_stage("security")
        
        template = "test:\n  script: pytest\n"
        result = customizer.customize_gitlab_ci(template)
        
        assert "CI_DEBUG" in result
        assert "security" in result

    def test_customize_github_actions(self):
        """Test customizing GitHub Actions template"""
        customizer = TemplateCustomizer()
        customizer.add_custom_variable("DEBUG", "true")
        
        template = "name: Test\njobs:\n  build:\n    runs-on: ubuntu-latest\n"
        result = customizer.customize_github_actions(template)
        
        assert "DEBUG" in result

    def test_export_customization(self):
        """Test exporting customization"""
        customizer = TemplateCustomizer()
        customizer.add_custom_variable("VAR", "value")
        customizer.add_custom_stage("custom")
        
        export = customizer.export_customization()
        
        assert "VAR" in export['custom_vars']
        assert "custom" in export['custom_stages']

    def test_import_customization(self):
        """Test importing customization"""
        customizer = TemplateCustomizer()
        data = {
            'custom_vars': {'VAR1': 'value1'},
            'custom_stages': ['stage1'],
            'custom_jobs': {}
        }
        customizer.import_customization(data)
        
        assert "VAR1" in customizer.custom_vars
        assert "stage1" in customizer.custom_stages


class TestPipelineManager:
    """Test Pipeline Management functionality"""

    def test_create_pipeline(self):
        """Test creating a pipeline"""
        manager = PipelineManager()
        pipeline = manager.create_pipeline("pipe1", "Test Pipeline", "main")
        
        assert pipeline.id == "pipe1"
        assert pipeline.name == "Test Pipeline"
        assert pipeline.branch == "main"

    def test_get_pipeline(self):
        """Test getting a pipeline"""
        manager = PipelineManager()
        manager.create_pipeline("pipe1", "Test", "main")
        
        pipeline = manager.get_pipeline("pipe1")
        assert pipeline is not None
        assert pipeline.id == "pipe1"

    def test_list_pipelines(self):
        """Test listing pipelines"""
        manager = PipelineManager()
        manager.create_pipeline("pipe1", "Test1", "main")
        manager.create_pipeline("pipe2", "Test2", "dev")
        
        all_pipes = manager.list_pipelines()
        assert len(all_pipes) == 2

    def test_list_pipelines_by_branch(self):
        """Test listing pipelines by branch"""
        manager = PipelineManager()
        manager.create_pipeline("pipe1", "Test1", "main")
        manager.create_pipeline("pipe2", "Test2", "dev")
        
        main_pipes = manager.list_pipelines(branch="main")
        assert len(main_pipes) == 1
        assert main_pipes[0].branch == "main"

    def test_update_pipeline_status(self):
        """Test updating pipeline status"""
        manager = PipelineManager()
        manager.create_pipeline("pipe1", "Test", "main")
        
        success = manager.update_pipeline_status("pipe1", PipelineStatus.RUNNING)
        assert success is True
        
        pipeline = manager.get_pipeline("pipe1")
        assert pipeline.status == PipelineStatus.RUNNING

    def test_add_job_to_pipeline(self):
        """Test adding job to pipeline"""
        manager = PipelineManager()
        manager.create_pipeline("pipe1", "Test", "main")
        
        job = PipelineJob(name="test_job")
        success = manager.add_job_to_pipeline("pipe1", job)
        
        assert success is True
        pipeline = manager.get_pipeline("pipe1")
        assert "test_job" in pipeline.jobs

    def test_get_pipeline_statistics(self):
        """Test getting pipeline statistics"""
        manager = PipelineManager()
        p1 = manager.create_pipeline("pipe1", "Test1", "main")
        p2 = manager.create_pipeline("pipe2", "Test2", "main")
        
        p1.update_status(PipelineStatus.SUCCESS)
        p2.update_status(PipelineStatus.FAILED)
        
        stats = manager.get_pipeline_statistics()
        
        assert stats['total_pipelines'] == 2
        assert stats['successful'] == 1
        assert stats['failed'] == 1

    def test_get_job_statistics(self):
        """Test getting job statistics"""
        manager = PipelineManager()
        pipeline = manager.create_pipeline("pipe1", "Test", "main")
        
        job1 = PipelineJob(name="job1")
        job1.status = PipelineStatus.SUCCESS
        job2 = PipelineJob(name="job2")
        job2.status = PipelineStatus.FAILED
        
        pipeline.add_job(job1)
        pipeline.add_job(job2)
        
        stats = manager.get_job_statistics("pipe1")
        
        assert stats['total_jobs'] == 2
        assert stats['successful_jobs'] == 1
        assert stats['failed_jobs'] == 1

    def test_export_pipelines(self):
        """Test exporting pipelines"""
        manager = PipelineManager()
        manager.create_pipeline("pipe1", "Test", "main")
        
        export = manager.export_pipelines()
        
        assert 'pipe1' in export
        assert 'Test' in export

    def test_get_failed_pipelines(self):
        """Test getting failed pipelines"""
        manager = PipelineManager()
        p1 = manager.create_pipeline("pipe1", "Test1", "main")
        p2 = manager.create_pipeline("pipe2", "Test2", "main")
        
        p1.update_status(PipelineStatus.SUCCESS)
        p2.update_status(PipelineStatus.FAILED)
        
        failed = manager.get_failed_pipelines()
        
        assert len(failed) == 1
        assert failed[0].id == "pipe2"

    def test_calculate_pipeline_trends(self):
        """Test calculating pipeline trends"""
        manager = PipelineManager()
        
        for i in range(10):
            p = manager.create_pipeline(f"pipe{i}", f"Test{i}", "main")
            if i < 8:
                p.update_status(PipelineStatus.SUCCESS)
            else:
                p.update_status(PipelineStatus.FAILED)
        
        trends = manager.calculate_pipeline_trends()
        
        assert 'trend' in trends
        assert 'recent_success_rate' in trends
        assert trends['trend'] == 'improving'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
