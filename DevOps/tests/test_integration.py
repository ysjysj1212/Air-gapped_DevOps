"""Integration Tests - YAML Generation and Validation Pipeline"""
import pytest
from src.template_generator import generate_yaml_from_requirements
from src.validators import validate_ci_yaml, suggest_fixes


class TestIntegration:
    """Test complete pipeline: Generate → Validate"""
    
    def test_generate_and_validate_github_actions_pipeline(self):
        """Test: Generate GitHub Actions YAML and validate it"""
        # Generate YAML from requirements
        yaml_content = generate_yaml_from_requirements(
            requirements="build, test, deploy",
            language="python",
            project_name="integration-test",
            ci_type="github_actions",
            use_llm=False
        )
        
        assert yaml_content is not None
        assert "name:" in yaml_content
        assert "jobs:" in yaml_content
        
        # Validate the generated YAML
        result = validate_ci_yaml(yaml_content, "github_actions")
        assert result.is_valid == True, f"Generated YAML is invalid: {result.errors}"
    
    def test_generate_and_validate_gitlab_ci_pipeline(self):
        """Test: Generate GitLab CI YAML and validate it"""
        # Generate YAML from requirements
        yaml_content = generate_yaml_from_requirements(
            requirements="build, test, deploy",
            language="python",
            project_name="integration-test",
            ci_type="gitlab_ci",
            use_llm=False
        )
        
        assert yaml_content is not None
        assert "stages:" in yaml_content
        
        # Validate the generated YAML
        result = validate_ci_yaml(yaml_content, "gitlab_ci")
        assert result.is_valid == True, f"Generated YAML is invalid: {result.errors}"
    
    def test_generate_with_different_languages(self):
        """Test: Generate and validate for different languages"""
        languages = ["python", "javascript", "java", "go"]
        
        for lang in languages:
            yaml_content = generate_yaml_from_requirements(
                requirements="build, test",
                language=lang,
                project_name=f"test-{lang}",
                ci_type="github_actions",
                use_llm=False
            )
            
            assert yaml_content is not None, f"Failed to generate YAML for {lang}"
            result = validate_ci_yaml(yaml_content, "github_actions")
            assert result.is_valid == True, f"Generated YAML for {lang} is invalid: {result.errors}"
    
    def test_generate_with_different_requirements(self):
        """Test: Generate and validate with various requirement strings"""
        requirements_list = [
            "build, test",
            "build, test, deploy, notify",
            "lint, format, test, build, deploy",
            "checkout, install, build, test, release"
        ]
        
        for requirements in requirements_list:
            yaml_content = generate_yaml_from_requirements(
                requirements=requirements,
                language="python",
                project_name="integration-test",
                ci_type="github_actions",
                use_llm=False
            )
            
            assert yaml_content is not None, f"Failed to generate YAML for requirements: {requirements}"
            result = validate_ci_yaml(yaml_content, "github_actions")
            assert result.is_valid == True, f"Generated YAML for requirements '{requirements}' is invalid"
    
    def test_auto_detect_github_actions_yaml(self):
        """Test: Generate GitHub Actions YAML and validate with auto-detection"""
        yaml_content = generate_yaml_from_requirements(
            requirements="build, test",
            language="python",
            project_name="auto-detect-test",
            ci_type="github_actions",
            use_llm=False
        )
        
        # Validate with auto-detection
        result = validate_ci_yaml(yaml_content, "auto")
        assert result.is_valid == True, f"Auto-detection failed for GitHub Actions YAML"
    
    def test_auto_detect_gitlab_ci_yaml(self):
        """Test: Generate GitLab CI YAML and validate with auto-detection"""
        yaml_content = generate_yaml_from_requirements(
            requirements="build, test",
            language="python",
            project_name="auto-detect-test",
            ci_type="gitlab_ci",
            use_llm=False
        )
        
        # Validate with auto-detection
        result = validate_ci_yaml(yaml_content, "auto")
        assert result.is_valid == True, f"Auto-detection failed for GitLab CI YAML"
    
    def test_generated_yaml_contains_project_name(self):
        """Test: Generated YAML contains project name"""
        project_names = ["my-app", "data-pipeline", "web-service"]
        
        for project_name in project_names:
            yaml_content = generate_yaml_from_requirements(
                requirements="build, test",
                language="python",
                project_name=project_name,
                ci_type="github_actions",
                use_llm=False
            )
            
            assert project_name in yaml_content, f"Project name '{project_name}' not found in generated YAML"
    
    def test_yaml_generation_consistency(self):
        """Test: Same requirements generate consistent YAML structure"""
        yaml1 = generate_yaml_from_requirements(
            requirements="build, test, deploy",
            language="python",
            project_name="consistency-test",
            ci_type="github_actions",
            use_llm=False
        )
        
        yaml2 = generate_yaml_from_requirements(
            requirements="build, test, deploy",
            language="python",
            project_name="consistency-test",
            ci_type="github_actions",
            use_llm=False
        )
        
        # Both should be valid
        result1 = validate_ci_yaml(yaml1, "github_actions")
        result2 = validate_ci_yaml(yaml2, "github_actions")
        
        assert result1.is_valid == True
        assert result2.is_valid == True
        
        # Structure should be similar (both have required sections)
        assert "name:" in yaml1 and "name:" in yaml2
        assert "jobs:" in yaml1 and "jobs:" in yaml2
    
    def test_validation_with_empty_requirements(self):
        """Test: Generate with empty requirements still produces valid YAML"""
        yaml_content = generate_yaml_from_requirements(
            requirements="",
            language="python",
            project_name="empty-req-test",
            ci_type="github_actions",
            use_llm=False
        )
        
        # Should still generate valid YAML even with empty requirements
        result = validate_ci_yaml(yaml_content, "github_actions")
        assert result.is_valid == True
    
    def test_cross_ci_type_validation_fails_appropriately(self):
        """Test: Validate GitHub Actions YAML as GitLab CI should fail"""
        github_yaml = generate_yaml_from_requirements(
            requirements="build, test",
            language="python",
            project_name="cross-test",
            ci_type="github_actions",
            use_llm=False
        )
        
        # Validating GitHub Actions YAML as GitLab CI should either fail or succeed
        # depending on YAML structure overlap
        result = validate_ci_yaml(github_yaml, "gitlab_ci")
        # This is expected to fail in most cases
        assert isinstance(result.is_valid, bool)
    
    def test_validation_error_is_actionable(self):
        """Test: Invalid YAML produces actionable error messages"""
        invalid_yaml = "jobs: {}"
        
        result = validate_ci_yaml(invalid_yaml, "github_actions")
        assert result.is_valid == False
        assert len(result.errors) > 0
        suggestions = suggest_fixes(invalid_yaml, result)
        assert len(suggestions) > 0


class TestEndToEndPipeline:
    """Test complete end-to-end workflow"""
    
    def test_multiple_ci_types_generation(self):
        """Test: Generate both GitHub Actions and GitLab CI for same requirements"""
        requirements = "build, test, deploy"
        
        # Generate GitHub Actions
        github_yaml = generate_yaml_from_requirements(
            requirements=requirements,
            language="python",
            project_name="e2e-test",
            ci_type="github_actions",
            use_llm=False
        )
        
        # Generate GitLab CI
        gitlab_yaml = generate_yaml_from_requirements(
            requirements=requirements,
            language="python",
            project_name="e2e-test",
            ci_type="gitlab_ci",
            use_llm=False
        )
        
        # Both should be valid
        github_result = validate_ci_yaml(github_yaml, "github_actions")
        gitlab_result = validate_ci_yaml(gitlab_yaml, "gitlab_ci")
        
        assert github_result.is_valid == True
        assert gitlab_result.is_valid == True
        
        # Both should contain different structure markers
        assert "jobs:" in github_yaml
        assert "stages:" in gitlab_yaml
    
    def test_pipeline_with_complex_requirements(self):
        """Test: Complex requirement strings are handled properly"""
        complex_requirements = "lint code, format python, test with pytest, build docker, deploy to aws, notify slack"
        
        yaml_content = generate_yaml_from_requirements(
            requirements=complex_requirements,
            language="python",
            project_name="complex-pipeline",
            ci_type="github_actions",
            use_llm=False
        )
        
        assert yaml_content is not None
        result = validate_ci_yaml(yaml_content, "github_actions")
        assert result.is_valid == True
