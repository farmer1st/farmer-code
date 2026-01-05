"""Unit tests for Baron dispatch models.

Tests validation of request models and parsing of result models.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestrator.baron_models import (
    PlanRequest,
    PlanResult,
    SpecifyRequest,
    SpecifyResult,
    TasksRequest,
    TasksResult,
)


class TestSpecifyRequest:
    """Tests for SpecifyRequest validation."""

    def test_valid_request_minimal(self):
        """Test valid request with only required fields."""
        request = SpecifyRequest(feature_description="Add user authentication with OAuth2 support")
        assert request.feature_description == "Add user authentication with OAuth2 support"
        assert request.feature_number is None
        assert request.short_name is None

    def test_valid_request_full(self):
        """Test valid request with all fields."""
        request = SpecifyRequest(
            feature_description="Add user authentication with OAuth2 support",
            feature_number=8,
            short_name="oauth2-auth",
        )
        assert request.feature_number == 8
        assert request.short_name == "oauth2-auth"

    def test_description_too_short(self):
        """Test that short descriptions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SpecifyRequest(feature_description="Add auth")
        assert "String should have at least 10 characters" in str(exc_info.value)

    def test_feature_number_must_be_positive(self):
        """Test that feature number must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            SpecifyRequest(
                feature_description="Add user authentication",
                feature_number=0,
            )
        assert "greater than 0" in str(exc_info.value)

    def test_short_name_valid_pattern(self):
        """Test valid short name patterns."""
        valid_names = ["auth", "oauth2-auth", "user-123", "my-feature"]
        for name in valid_names:
            request = SpecifyRequest(
                feature_description="Add user authentication",
                short_name=name,
            )
            assert request.short_name == name

    def test_short_name_invalid_pattern(self):
        """Test that invalid short names are rejected."""
        invalid_names = ["Auth", "oauth_auth", "user auth", "MY-FEATURE", "auth!"]
        for name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                SpecifyRequest(
                    feature_description="Add user authentication",
                    short_name=name,
                )
            assert "short_name must match pattern" in str(exc_info.value)


class TestSpecifyResult:
    """Tests for SpecifyResult parsing."""

    def test_success_result(self):
        """Test parsing successful result."""
        result = SpecifyResult(
            success=True,
            spec_path=Path("specs/008-oauth2-auth/spec.md"),
            feature_id="008-oauth2-auth",
            branch_name="008-oauth2-auth",
            duration_seconds=45.2,
        )
        assert result.success is True
        assert result.spec_path == Path("specs/008-oauth2-auth/spec.md")
        assert result.feature_id == "008-oauth2-auth"
        assert result.error is None

    def test_failure_result(self):
        """Test parsing failed result."""
        result = SpecifyResult(
            success=False,
            error="Template not found: spec-template.md",
            duration_seconds=1.5,
        )
        assert result.success is False
        assert result.error == "Template not found: spec-template.md"
        assert result.spec_path is None

    def test_duration_must_be_positive(self):
        """Test that duration cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            SpecifyResult(success=True, duration_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)


class TestPlanRequest:
    """Tests for PlanRequest validation."""

    def test_valid_request(self):
        """Test valid plan request."""
        request = PlanRequest(spec_path=Path("specs/008-oauth2-auth/spec.md"))
        assert request.spec_path == Path("specs/008-oauth2-auth/spec.md")
        assert request.force_research is False

    def test_force_research_flag(self):
        """Test force_research flag."""
        request = PlanRequest(
            spec_path=Path("specs/008-oauth2-auth/spec.md"),
            force_research=True,
        )
        assert request.force_research is True

    def test_spec_path_accepts_string(self):
        """Test that spec_path can be created from string."""
        request = PlanRequest(spec_path="specs/008-oauth2-auth/spec.md")
        assert request.spec_path == Path("specs/008-oauth2-auth/spec.md")

    def test_spec_path_preserves_relative_path(self):
        """Test that relative paths are preserved."""
        request = PlanRequest(spec_path=Path("./specs/feature/spec.md"))
        assert str(request.spec_path) == "specs/feature/spec.md"


class TestPlanResult:
    """Tests for PlanResult parsing."""

    def test_success_result(self):
        """Test parsing successful result with all artifacts."""
        result = PlanResult(
            success=True,
            plan_path=Path("specs/008-oauth2-auth/plan.md"),
            research_path=Path("specs/008-oauth2-auth/research.md"),
            data_model_path=Path("specs/008-oauth2-auth/data-model.md"),
            contracts_dir=Path("specs/008-oauth2-auth/contracts"),
            quickstart_path=Path("specs/008-oauth2-auth/quickstart.md"),
            duration_seconds=120.5,
        )
        assert result.success is True
        assert result.blocked_on_escalation is False

    def test_blocked_result(self):
        """Test result when blocked on escalation."""
        result = PlanResult(
            success=False,
            blocked_on_escalation=True,
            duration_seconds=30.0,
        )
        assert result.success is False
        assert result.blocked_on_escalation is True

    def test_partial_success_result(self):
        """Test result with only some artifacts."""
        result = PlanResult(
            success=True,
            plan_path=Path("specs/008-oauth2-auth/plan.md"),
            research_path=Path("specs/008-oauth2-auth/research.md"),
            duration_seconds=60.0,
        )
        assert result.success is True
        assert result.plan_path is not None
        assert result.data_model_path is None
        assert result.contracts_dir is None

    def test_failure_with_error(self):
        """Test failed result with error message."""
        result = PlanResult(
            success=False,
            error="Spec file not found",
            duration_seconds=5.0,
        )
        assert result.success is False
        assert result.error == "Spec file not found"

    def test_duration_must_be_non_negative(self):
        """Test that duration cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            PlanResult(success=True, duration_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)


class TestTasksRequest:
    """Tests for TasksRequest validation."""

    def test_valid_request(self):
        """Test valid tasks request."""
        request = TasksRequest(plan_path=Path("specs/008-oauth2-auth/plan.md"))
        assert request.plan_path == Path("specs/008-oauth2-auth/plan.md")

    def test_plan_path_accepts_string(self):
        """Test that plan_path can be created from string."""
        request = TasksRequest(plan_path="specs/008-oauth2-auth/plan.md")
        assert request.plan_path == Path("specs/008-oauth2-auth/plan.md")

    def test_plan_path_preserves_relative_path(self):
        """Test that relative paths are preserved."""
        request = TasksRequest(plan_path=Path("./specs/feature/plan.md"))
        assert str(request.plan_path) == "specs/feature/plan.md"


class TestTasksResult:
    """Tests for TasksResult parsing."""

    def test_success_result(self):
        """Test parsing successful result."""
        result = TasksResult(
            success=True,
            tasks_path=Path("specs/008-oauth2-auth/tasks.md"),
            task_count=25,
            test_count=12,
            duration_seconds=60.3,
        )
        assert result.success is True
        assert result.task_count == 25
        assert result.test_count == 12

    def test_counts_must_be_non_negative(self):
        """Test that counts cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            TasksResult(success=True, task_count=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_test_count_must_be_non_negative(self):
        """Test that test_count cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            TasksResult(success=True, test_count=-5)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_failure_with_error(self):
        """Test failed result with error message."""
        result = TasksResult(
            success=False,
            error="Plan file not found",
            duration_seconds=3.0,
        )
        assert result.success is False
        assert result.error == "Plan file not found"
        assert result.tasks_path is None

    def test_duration_must_be_non_negative(self):
        """Test that duration cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            TasksResult(success=True, duration_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_default_counts_are_zero(self):
        """Test that task and test counts default to zero."""
        result = TasksResult(success=True, duration_seconds=10.0)
        assert result.task_count == 0
        assert result.test_count == 0
