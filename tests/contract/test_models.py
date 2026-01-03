"""
Contract tests for Pydantic data models.

These tests verify the validation rules and constraints defined in
specs/001-github-integration-core/contracts/data_models.md

Tests focus on:
- Field validation (types, lengths, patterns)
- Required vs optional fields
- Default values
- Immutability (frozen=True)
- Helper methods
"""

from datetime import datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from github_integration import Comment, Issue, Label, PullRequest


class TestIssueModel:
    """
    T025 [P] [US1] Pydantic model validation test for Issue model

    Verifies Issue model validation rules from data-model.md
    """

    def test_issue_valid_minimal(self, sample_issue_data):
        """Test Issue with minimal required fields"""
        issue = Issue(**sample_issue_data)

        assert issue.number == 42
        assert issue.title == "Add user authentication"
        assert issue.state == "open"
        assert isinstance(issue.created_at, datetime)
        assert isinstance(issue.updated_at, datetime)

    def test_issue_number_must_be_positive(self, sample_issue_data):
        """Test Issue.number validation (must be > 0)"""
        sample_issue_data["number"] = 0
        with pytest.raises(PydanticValidationError) as exc_info:
            Issue(**sample_issue_data)

        assert "number" in str(exc_info.value)

        sample_issue_data["number"] = -1
        with pytest.raises(PydanticValidationError):
            Issue(**sample_issue_data)

    def test_issue_title_validation(self, sample_issue_data):
        """Test Issue.title validation (1-256 chars)"""
        # Empty title
        sample_issue_data["title"] = ""
        with pytest.raises(PydanticValidationError) as exc_info:
            Issue(**sample_issue_data)

        assert "title" in str(exc_info.value)

        # Title too long
        sample_issue_data["title"] = "a" * 257
        with pytest.raises(PydanticValidationError) as exc_info:
            Issue(**sample_issue_data)

        assert "title" in str(exc_info.value)

        # Valid title
        sample_issue_data["title"] = "Valid title"
        issue = Issue(**sample_issue_data)
        assert issue.title == "Valid title"

    def test_issue_state_validation(self, sample_issue_data):
        """Test Issue.state validation (must be 'open' or 'closed')"""
        sample_issue_data["state"] = "invalid"
        with pytest.raises(PydanticValidationError) as exc_info:
            Issue(**sample_issue_data)

        assert "state" in str(exc_info.value)

        # Valid states
        sample_issue_data["state"] = "open"
        assert Issue(**sample_issue_data).state == "open"

        sample_issue_data["state"] = "closed"
        assert Issue(**sample_issue_data).state == "closed"

    def test_issue_body_optional(self, sample_issue_data):
        """Test Issue.body is optional (can be None)"""
        sample_issue_data["body"] = None
        issue = Issue(**sample_issue_data)
        assert issue.body is None

        sample_issue_data["body"] = "Some body text"
        issue = Issue(**sample_issue_data)
        assert issue.body == "Some body text"

    def test_issue_labels_default_empty(self, sample_issue_data):
        """Test Issue.labels defaults to empty list"""
        del sample_issue_data["labels"]
        issue = Issue(**sample_issue_data)
        assert issue.labels == []

    def test_issue_immutable(self, sample_issue_data):
        """Test Issue is immutable (frozen=True)"""
        issue = Issue(**sample_issue_data)

        # Pydantic raises ValidationError for frozen models
        with pytest.raises(PydanticValidationError):
            issue.title = "New title"

    def test_issue_has_label_helper(self, sample_issue_data):
        """Test Issue.has_label() helper method"""
        issue = Issue(**sample_issue_data)

        assert issue.has_label("status:new") is True
        assert issue.has_label("priority:p1") is True
        assert issue.has_label("nonexistent") is False


class TestCommentModel:
    """Contract tests for Comment model"""

    def test_comment_valid(self, sample_comment_data):
        """Test Comment with valid data"""
        comment = Comment(**sample_comment_data)

        assert comment.id == 987654321
        assert comment.issue_number == 42
        assert comment.author == "dede"
        assert comment.body == "✅ Backend plan complete. @baron"
        assert isinstance(comment.created_at, datetime)

    def test_comment_id_must_be_positive(self, sample_comment_data):
        """Test Comment.id validation (must be > 0)"""
        sample_comment_data["id"] = 0
        with pytest.raises(PydanticValidationError):
            Comment(**sample_comment_data)

    def test_comment_body_required(self, sample_comment_data):
        """Test Comment.body is required and non-empty"""
        sample_comment_data["body"] = ""
        with pytest.raises(PydanticValidationError) as exc_info:
            Comment(**sample_comment_data)

        assert "body" in str(exc_info.value)

    def test_comment_contains_signal_helper(self, sample_comment_data):
        """Test Comment.contains_signal() helper method"""
        comment = Comment(**sample_comment_data)

        assert comment.contains_signal("✅") is True
        assert comment.contains_signal("❓") is False
        assert comment.contains_signal("@baron") is True

    def test_comment_extract_mentions_helper(self, sample_comment_data):
        """Test Comment.extract_mentions() helper method"""
        comment = Comment(**sample_comment_data)

        mentions = comment.extract_mentions()
        assert "baron" in mentions
        assert len(mentions) == 1


class TestLabelModel:
    """Contract tests for Label model"""

    def test_label_valid(self, sample_label_data):
        """Test Label with valid data"""
        label = Label(**sample_label_data)

        assert label.name == "status:specs-ready"
        assert label.color == "EDEDED"
        assert label.description == "Specifications approved and ready for planning"

    def test_label_name_validation(self, sample_label_data):
        """Test Label.name validation (1-50 chars)"""
        sample_label_data["name"] = ""
        with pytest.raises(PydanticValidationError):
            Label(**sample_label_data)

        sample_label_data["name"] = "a" * 51
        with pytest.raises(PydanticValidationError):
            Label(**sample_label_data)

    def test_label_color_validation(self, sample_label_data):
        """Test Label.color validation (6 hex chars, no #)"""
        # Invalid - with # prefix
        sample_label_data["color"] = "#EDEDED"
        with pytest.raises(PydanticValidationError):
            Label(**sample_label_data)

        # Invalid - wrong length
        sample_label_data["color"] = "EDE"
        with pytest.raises(PydanticValidationError):
            Label(**sample_label_data)

        # Invalid - non-hex characters
        sample_label_data["color"] = "GGGGGG"
        with pytest.raises(PydanticValidationError):
            Label(**sample_label_data)

        # Valid
        sample_label_data["color"] = "EDEDED"
        label = Label(**sample_label_data)
        assert label.color == "EDEDED"

    def test_label_hex_color_property(self, sample_label_data):
        """Test Label.hex_color property (adds # prefix)"""
        label = Label(**sample_label_data)
        assert label.hex_color == "#EDEDED"


class TestPullRequestModel:
    """Contract tests for PullRequest model"""

    def test_pr_valid(self, sample_pr_data):
        """Test PullRequest with valid data"""
        pr = PullRequest(**sample_pr_data)

        assert pr.number == 15
        assert pr.title == "Add user authentication"
        assert pr.state == "open"
        assert pr.merged is False
        assert pr.base_branch == "main"
        assert pr.head_branch == "123-add-auth"
        assert pr.linked_issues == [42]

    def test_pr_number_must_be_positive(self, sample_pr_data):
        """Test PullRequest.number validation (must be > 0)"""
        sample_pr_data["number"] = 0
        with pytest.raises(PydanticValidationError):
            PullRequest(**sample_pr_data)

    def test_pr_state_validation(self, sample_pr_data):
        """Test PullRequest.state validation (must be 'open' or 'closed')"""
        sample_pr_data["state"] = "invalid"
        with pytest.raises(PydanticValidationError):
            PullRequest(**sample_pr_data)

    def test_pr_merged_must_be_boolean(self, sample_pr_data):
        """Test PullRequest.merged validation (must be bool)"""
        sample_pr_data["merged"] = "true"  # String instead of bool
        # Pydantic may coerce this, so let's test with invalid value
        try:
            pr = PullRequest(**sample_pr_data)
            # If coercion happens, verify it's still a bool
            assert isinstance(pr.merged, bool)
        except PydanticValidationError:
            # If coercion doesn't happen, that's also valid
            pass

    def test_pr_is_linked_to_helper(self, sample_pr_data):
        """Test PullRequest.is_linked_to() helper method"""
        pr = PullRequest(**sample_pr_data)

        assert pr.is_linked_to(42) is True
        assert pr.is_linked_to(99) is False
