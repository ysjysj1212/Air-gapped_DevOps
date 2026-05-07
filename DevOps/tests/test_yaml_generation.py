"""YAML Generation Tests"""
import pytest
from src.template_generator import (
    TemplateGenerator,
    generate_yaml_from_requirements,
    generate_github_actions,
    generate_gitlab_ci
)

class TestYAMLGeneration:
    """Test YAML generation functionality"""
    
    def test_generate_yaml_from_requirements_github_actions(self):
        """Test YAML generation for GitHub Actions"""
        requirements = "Python Flask API with pytest"
        yaml = generate_yaml_from_requirements(
            requirements,
            language='python',
            project_name='test-project',
            ci_type='github_actions',
            use_llm=False
        )
        
        assert yaml is not None
        assert 'name: test-project' in yaml
        assert 'github' not in yaml.lower() or 'actions' in yaml.lower()
        assert 'pytest' not in yaml or 'python' in yaml.lower()
    
    def test_generate_yaml_from_requirements_gitlab_ci(self):
        """Test YAML generation for GitLab CI"""
        requirements = "Node.js Express with npm"
        yaml = generate_yaml_from_requirements(
            requirements,
            language='nodejs',
            project_name='node-app',
            ci_type='gitlab_ci',
            use_llm=False
        )
        
        assert yaml is not None
        assert 'stages:' in yaml
        assert 'build:' in yaml or 'test:' in yaml
        assert 'script:' in yaml
    
    def test_github_actions_contains_jobs(self):
        """Test GitHub Actions template has jobs"""
        yaml = generate_github_actions('python', 'test')
        assert 'jobs:' in yaml
        assert 'test:' in yaml or 'build:' in yaml
    
    def test_gitlab_ci_contains_stages(self):
        """Test GitLab CI template has stages"""
        yaml = generate_gitlab_ci('python', 'test')
        assert 'stages:' in yaml
        assert 'image:' in yaml
    
    def test_yaml_valid_structure_github_actions(self):
        """Test generated GitHub Actions YAML has valid structure"""
        yaml = generate_yaml_from_requirements(
            'Test project',
            'python',
            'myapp',
            'github_actions',
            use_llm=False
        )
        
        assert yaml.startswith('name:')
        assert 'on:' in yaml
        assert 'jobs:' in yaml
    
    def test_yaml_valid_structure_gitlab_ci(self):
        """Test generated GitLab CI YAML has valid structure"""
        yaml = generate_yaml_from_requirements(
            'Test project',
            'python',
            'myapp',
            'gitlab_ci',
            use_llm=False
        )
        
        assert yaml.startswith('stages:')
        assert 'image:' in yaml
    
    def test_yaml_contains_project_name(self):
        """Test YAML contains project name"""
        yaml = generate_yaml_from_requirements(
            'Test',
            'python',
            'my-special-project',
            'github_actions',
            use_llm=False
        )
        
        assert 'my-special-project' in yaml
    
    def test_requirements_with_build_stage(self):
        """Test requirements with build stage"""
        requirements = "Build stage for Docker"
        yaml = generate_yaml_from_requirements(
            requirements,
            'python',
            'project',
            'github_actions',
            use_llm=False
        )
        
        assert yaml is not None
        assert len(yaml) > 100  # Should generate substantial YAML

    def test_mvp_generator_handles_broad_natural_language(self):
        """Test broad natural language prompts still map to a GitLab draft"""
        generator = TemplateGenerator()

        spring_yaml = generator.generate_gitlab_mvp(
            "Spring Boot 앱을 빌드하고 테스트하는 GitLab CI 초안을 만들어줘"
        )
        react_yaml = generator.generate_gitlab_mvp(
            "React 프론트엔드 프로젝트용 간단한 GitLab CI YAML을 만들어줘"
        )

        assert "image: eclipse-temurin:17" in spring_yaml
        assert "image: node:20" in react_yaml
        assert "stages:" in spring_yaml
        assert "stages:" in react_yaml
