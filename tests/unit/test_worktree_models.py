"""
Unit tests for worktree_manager models.

Tests Pydantic models for validation, properties, and computed fields.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

# =============================================================================
# US1: Worktree, Branch, CreateWorktreeRequest models
# =============================================================================


class TestWorktreeModel:
    """Tests for Worktree model (US1)."""

    def test_worktree_creation_valid(self) -> None:
        """Worktree should accept valid data."""
        from worktree_manager.models import Worktree

        wt = Worktree(
            issue_number=123,
            feature_name="add-auth",
            path=Path("/path/to/worktree"),
            main_repo_path=Path("/path/to/main"),
            branch_name="123-add-auth",
            is_clean=True,
            created_at=datetime.now(UTC),
        )
        assert wt.issue_number == 123
        assert wt.feature_name == "add-auth"
        assert wt.branch_name == "123-add-auth"

    def test_worktree_issue_number_must_be_positive(self) -> None:
        """Worktree should reject non-positive issue numbers."""
        from worktree_manager.models import Worktree

        with pytest.raises(ValidationError) as exc_info:
            Worktree(
                issue_number=0,
                feature_name="test",
                path=Path("/path"),
                main_repo_path=Path("/main"),
                branch_name="0-test",
                is_clean=True,
                created_at=datetime.now(UTC),
            )
        assert "issue_number" in str(exc_info.value)

    def test_worktree_feature_name_validation(self) -> None:
        """Worktree should validate feature_name length."""
        from worktree_manager.models import Worktree

        # Empty feature name should fail
        with pytest.raises(ValidationError):
            Worktree(
                issue_number=1,
                feature_name="",
                path=Path("/path"),
                main_repo_path=Path("/main"),
                branch_name="1-",
                is_clean=True,
                created_at=datetime.now(UTC),
            )

    def test_worktree_plans_path_property(self) -> None:
        """Worktree.plans_path should return correct path."""
        from worktree_manager.models import Worktree

        wt = Worktree(
            issue_number=123,
            feature_name="add-auth",
            path=Path("/path/to/worktree"),
            main_repo_path=Path("/path/to/main"),
            branch_name="123-add-auth",
            is_clean=True,
            created_at=datetime.now(UTC),
        )
        expected = Path("/path/to/worktree/.plans/123")
        assert wt.plans_path == expected

    def test_worktree_is_immutable(self) -> None:
        """Worktree should be immutable (frozen)."""
        from worktree_manager.models import Worktree

        wt = Worktree(
            issue_number=123,
            feature_name="add-auth",
            path=Path("/path/to/worktree"),
            main_repo_path=Path("/path/to/main"),
            branch_name="123-add-auth",
            is_clean=True,
            created_at=datetime.now(UTC),
        )
        with pytest.raises(ValidationError):
            wt.is_clean = False  # type: ignore


class TestBranchModel:
    """Tests for Branch model (US1)."""

    def test_branch_creation_valid(self) -> None:
        """Branch should accept valid data."""
        from worktree_manager.models import Branch

        branch = Branch(
            name="123-add-auth",
            remote="origin",
            remote_branch="123-add-auth",
            is_local=True,
            is_remote=True,
            is_merged=False,
            ahead=2,
            behind=0,
        )
        assert branch.name == "123-add-auth"
        assert branch.remote == "origin"

    def test_branch_name_required(self) -> None:
        """Branch should require name."""
        from worktree_manager.models import Branch

        with pytest.raises(ValidationError):
            Branch(
                name="",
                is_local=True,
            )

    def test_branch_is_tracking_property(self) -> None:
        """Branch.is_tracking should return True when tracking remote."""
        from worktree_manager.models import Branch

        # Tracking branch
        tracking = Branch(
            name="123-add-auth",
            remote="origin",
            remote_branch="123-add-auth",
            is_local=True,
            is_remote=True,
        )
        assert tracking.is_tracking is True

        # Non-tracking branch
        local_only = Branch(
            name="local-branch",
            is_local=True,
        )
        assert local_only.is_tracking is False

    def test_branch_is_synced_property(self) -> None:
        """Branch.is_synced should return True when ahead=0 and behind=0."""
        from worktree_manager.models import Branch

        # Synced
        synced = Branch(name="synced", is_local=True, ahead=0, behind=0)
        assert synced.is_synced is True

        # Ahead
        ahead = Branch(name="ahead", is_local=True, ahead=2, behind=0)
        assert ahead.is_synced is False

        # Behind
        behind = Branch(name="behind", is_local=True, ahead=0, behind=3)
        assert behind.is_synced is False

    def test_branch_ahead_behind_non_negative(self) -> None:
        """Branch.ahead and behind must be non-negative."""
        from worktree_manager.models import Branch

        with pytest.raises(ValidationError):
            Branch(name="test", is_local=True, ahead=-1)

        with pytest.raises(ValidationError):
            Branch(name="test", is_local=True, behind=-1)


class TestCreateWorktreeRequestModel:
    """Tests for CreateWorktreeRequest model (US1)."""

    def test_create_request_valid(self) -> None:
        """CreateWorktreeRequest should accept valid data."""
        from worktree_manager.models import CreateWorktreeRequest

        req = CreateWorktreeRequest(
            issue_number=123,
            feature_name="add-auth",
        )
        assert req.issue_number == 123
        assert req.feature_name == "add-auth"

    def test_create_request_branch_name_property(self) -> None:
        """CreateWorktreeRequest.branch_name should combine issue and feature."""
        from worktree_manager.models import CreateWorktreeRequest

        req = CreateWorktreeRequest(issue_number=123, feature_name="add-auth")
        assert req.branch_name == "123-add-auth"

    def test_create_request_issue_number_positive(self) -> None:
        """CreateWorktreeRequest should require positive issue number."""
        from worktree_manager.models import CreateWorktreeRequest

        with pytest.raises(ValidationError):
            CreateWorktreeRequest(issue_number=0, feature_name="test")

        with pytest.raises(ValidationError):
            CreateWorktreeRequest(issue_number=-1, feature_name="test")

    def test_create_request_feature_name_pattern(self) -> None:
        """CreateWorktreeRequest should validate feature_name pattern."""
        from worktree_manager.models import CreateWorktreeRequest

        # Valid names
        CreateWorktreeRequest(issue_number=1, feature_name="a")
        CreateWorktreeRequest(issue_number=1, feature_name="add-auth")
        CreateWorktreeRequest(issue_number=1, feature_name="feature-123")

        # Invalid: empty
        with pytest.raises(ValidationError):
            CreateWorktreeRequest(issue_number=1, feature_name="")

        # Invalid: starts with hyphen
        with pytest.raises(ValidationError):
            CreateWorktreeRequest(issue_number=1, feature_name="-invalid")

        # Invalid: ends with hyphen
        with pytest.raises(ValidationError):
            CreateWorktreeRequest(issue_number=1, feature_name="invalid-")

        # Invalid: uppercase (should be lowercase)
        with pytest.raises(ValidationError):
            CreateWorktreeRequest(issue_number=1, feature_name="InvalidName")


# =============================================================================
# US2: PlansFolder model
# =============================================================================


class TestPlansFolderModel:
    """Tests for PlansFolder model (US2)."""

    def test_plans_folder_creation_valid(self) -> None:
        """PlansFolder should accept valid data."""
        from worktree_manager.models import PlansFolder

        pf = PlansFolder(
            issue_number=123,
            worktree_path=Path("/path/to/worktree"),
            has_specs=True,
            has_plans=True,
            has_reviews=True,
            has_readme=True,
        )
        assert pf.issue_number == 123
        assert pf.has_specs is True

    def test_plans_folder_issue_number_positive(self) -> None:
        """PlansFolder should require positive issue number."""
        from worktree_manager.models import PlansFolder

        with pytest.raises(ValidationError):
            PlansFolder(
                issue_number=0,
                worktree_path=Path("/path"),
            )

    def test_plans_folder_path_property(self) -> None:
        """PlansFolder.path should return correct path."""
        from worktree_manager.models import PlansFolder

        pf = PlansFolder(
            issue_number=123,
            worktree_path=Path("/path/to/worktree"),
        )
        expected = Path("/path/to/worktree/.plans/123")
        assert pf.path == expected

    def test_plans_folder_is_complete_property(self) -> None:
        """PlansFolder.is_complete should return True when all subdirs exist."""
        from worktree_manager.models import PlansFolder

        # Incomplete
        incomplete = PlansFolder(
            issue_number=123,
            worktree_path=Path("/path"),
            has_specs=True,
            has_plans=True,
            has_reviews=False,
            has_readme=True,
        )
        assert incomplete.is_complete is False

        # Complete
        complete = PlansFolder(
            issue_number=123,
            worktree_path=Path("/path"),
            has_specs=True,
            has_plans=True,
            has_reviews=True,
            has_readme=True,
        )
        assert complete.is_complete is True

    def test_plans_folder_defaults(self) -> None:
        """PlansFolder should default has_* fields to False."""
        from worktree_manager.models import PlansFolder

        pf = PlansFolder(
            issue_number=123,
            worktree_path=Path("/path"),
        )
        assert pf.has_specs is False
        assert pf.has_plans is False
        assert pf.has_reviews is False
        assert pf.has_readme is False
        assert pf.is_complete is False


# =============================================================================
# US3: CommitRequest and CommitResult models
# =============================================================================


class TestCommitRequestModel:
    """Tests for CommitRequest model (US3)."""

    def test_commit_request_valid(self) -> None:
        """CommitRequest should accept valid data."""
        from worktree_manager.models import CommitRequest

        req = CommitRequest(message="Add feature X")
        assert req.message == "Add feature X"
        assert req.push is True  # default

    def test_commit_request_push_optional(self) -> None:
        """CommitRequest.push should default to True."""
        from worktree_manager.models import CommitRequest

        req = CommitRequest(message="test", push=False)
        assert req.push is False

    def test_commit_request_message_required(self) -> None:
        """CommitRequest should require message."""
        from worktree_manager.models import CommitRequest

        with pytest.raises(ValidationError):
            CommitRequest(message="")

    def test_commit_request_message_max_length(self) -> None:
        """CommitRequest should enforce message max length."""
        from worktree_manager.models import CommitRequest

        # 500 chars should work
        CommitRequest(message="x" * 500)

        # 501 chars should fail
        with pytest.raises(ValidationError):
            CommitRequest(message="x" * 501)


class TestCommitResultModel:
    """Tests for CommitResult model (US3)."""

    def test_commit_result_success(self) -> None:
        """CommitResult should represent successful commit."""
        from worktree_manager.models import CommitResult

        result = CommitResult(
            commit_sha="abc123",
            pushed=True,
        )
        assert result.commit_sha == "abc123"
        assert result.pushed is True
        assert result.nothing_to_commit is False

    def test_commit_result_nothing_to_commit(self) -> None:
        """CommitResult should represent nothing to commit."""
        from worktree_manager.models import CommitResult

        result = CommitResult(nothing_to_commit=True)
        assert result.nothing_to_commit is True
        assert result.commit_sha is None

    def test_commit_result_push_failed(self) -> None:
        """CommitResult should capture push failure."""
        from worktree_manager.models import CommitResult

        result = CommitResult(
            commit_sha="abc123",
            pushed=False,
            push_error="Network unreachable",
        )
        assert result.commit_sha == "abc123"
        assert result.pushed is False
        assert result.push_error == "Network unreachable"

    def test_commit_result_defaults(self) -> None:
        """CommitResult should have sensible defaults."""
        from worktree_manager.models import CommitResult

        result = CommitResult()
        assert result.commit_sha is None
        assert result.pushed is False
        assert result.nothing_to_commit is False
        assert result.push_error is None


# =============================================================================
# US4: OperationStatus, OperationResult, RemoveWorktreeRequest models
# =============================================================================


class TestOperationStatusEnum:
    """Tests for OperationStatus enum (US4)."""

    def test_operation_status_values(self) -> None:
        """OperationStatus should have expected values."""
        from worktree_manager.models import OperationStatus

        assert OperationStatus.SUCCESS == "success"
        assert OperationStatus.PARTIAL == "partial"
        assert OperationStatus.FAILED == "failed"

    def test_operation_status_is_str_enum(self) -> None:
        """OperationStatus should be a string enum."""
        from worktree_manager.models import OperationStatus

        assert isinstance(OperationStatus.SUCCESS, str)
        # StrEnum value can be accessed directly
        assert OperationStatus.SUCCESS.value == "success"


class TestOperationResultModel:
    """Tests for OperationResult model (US4)."""

    def test_operation_result_success(self) -> None:
        """OperationResult should represent success."""
        from worktree_manager.models import OperationResult, OperationStatus

        result = OperationResult(
            status=OperationStatus.SUCCESS,
            message="Worktree removed",
        )
        assert result.status == OperationStatus.SUCCESS
        assert result.message == "Worktree removed"

    def test_operation_result_partial(self) -> None:
        """OperationResult should represent partial success."""
        from worktree_manager.models import OperationResult, OperationStatus

        result = OperationResult(
            status=OperationStatus.PARTIAL,
            message="Worktree removed but branch delete failed",
            retry_possible=True,
        )
        assert result.status == OperationStatus.PARTIAL
        assert result.retry_possible is True

    def test_operation_result_with_worktree(self) -> None:
        """OperationResult should optionally include worktree."""
        from datetime import datetime

        from worktree_manager.models import OperationResult, OperationStatus, Worktree

        wt = Worktree(
            issue_number=123,
            feature_name="test",
            path=Path("/path"),
            main_repo_path=Path("/main"),
            branch_name="123-test",
            is_clean=True,
            created_at=datetime.now(UTC),
        )
        result = OperationResult(
            status=OperationStatus.SUCCESS,
            message="Created",
            worktree=wt,
        )
        assert result.worktree is not None
        assert result.worktree.issue_number == 123


class TestRemoveWorktreeRequestModel:
    """Tests for RemoveWorktreeRequest model (US4)."""

    def test_remove_request_defaults(self) -> None:
        """RemoveWorktreeRequest should have sensible defaults."""
        from worktree_manager.models import RemoveWorktreeRequest

        req = RemoveWorktreeRequest(issue_number=123)
        assert req.issue_number == 123
        assert req.delete_branch is False
        assert req.delete_remote_branch is False
        assert req.force is False

    def test_remove_request_with_flags(self) -> None:
        """RemoveWorktreeRequest should accept all flags."""
        from worktree_manager.models import RemoveWorktreeRequest

        req = RemoveWorktreeRequest(
            issue_number=123,
            delete_branch=True,
            delete_remote_branch=True,
            force=True,
        )
        assert req.delete_branch is True
        assert req.delete_remote_branch is True
        assert req.force is True

    def test_remove_request_issue_number_positive(self) -> None:
        """RemoveWorktreeRequest should require positive issue number."""
        from worktree_manager.models import RemoveWorktreeRequest

        with pytest.raises(ValidationError):
            RemoveWorktreeRequest(issue_number=0)
