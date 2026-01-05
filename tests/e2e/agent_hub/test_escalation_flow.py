"""End-to-end tests for escalation flow (KR-003, AH-003)."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from agent_hub.config import ConfigLoader
from agent_hub.models import (
    Answer,
    HumanAction,
    HumanResponse,
    Question,
    QuestionTarget,
    ResponseStatus,
    ValidationOutcome,
)


@pytest.mark.journey("KR-003")
class TestEscalationFlowE2E:
    """E2E tests for the full escalation flow."""

    def test_low_confidence_triggers_escalation_e2e(self) -> None:
        """Test end-to-end: low confidence answer triggers escalation."""
        from agent_hub.escalation import EscalationHandler
        from agent_hub.validator import ConfidenceValidator

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["security"],
                    },
                },
            }
        )

        validator = ConfidenceValidator(config)
        escalation_handler = EscalationHandler(config)

        # Step 1: Create question
        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What encryption algorithm should we use?",
            feature_id="005-user-auth",
        )

        # Step 2: Simulate low-confidence answer
        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use AES-256 for encryption.",
            rationale="Standard choice but uncertain about key management.",
            confidence=65,
            uncertainty_reasons=["Key management approach unclear"],
            model_used="sonnet",
            duration_seconds=2.5,
        )

        # Step 3: Validate and trigger escalation
        validation = validator.validate(answer, topic=question.topic)
        assert validation.outcome == ValidationOutcome.ESCALATE

        # Step 4: Create escalation request
        escalation = escalation_handler.create_escalation(question, validation)
        assert escalation.status == "pending"
        assert escalation.tentative_answer == answer
        assert escalation.threshold_used == 80

    def test_human_confirms_answer_e2e(self) -> None:
        """Test end-to-end: human confirms a low-confidence answer."""
        from agent_hub.escalation import EscalationHandler
        from agent_hub.models import EscalationRequest

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["authentication"],
                    },
                },
            }
        )

        escalation_handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="Which OAuth2 flow should we use for our mobile app?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use Authorization Code with PKCE flow.",
            rationale="Recommended for mobile apps as it's more secure than implicit flow.",
            confidence=75,
            model_used="opus",
            duration_seconds=3.0,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        # Human confirms the answer
        human_response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.CONFIRM,
            responder="farmer1st",
            github_comment_id=12345,
        )

        result = escalation_handler.process_response(escalation, human_response)

        assert result.escalation_resolved is True
        assert result.action_taken == HumanAction.CONFIRM
        assert result.final_answer == answer

    def test_human_corrects_answer_e2e(self) -> None:
        """Test end-to-end: human provides a corrected answer."""
        from agent_hub.escalation import EscalationHandler
        from agent_hub.models import EscalationRequest

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["database"],
                    },
                },
            }
        )

        escalation_handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="database",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What database migration strategy should we use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use raw SQL migrations.",
            rationale="Simple and direct approach to database changes.",
            confidence=60,
            uncertainty_reasons=["Not sure about rollback support"],
            model_used="sonnet",
            duration_seconds=1.8,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        # Human corrects the answer
        human_response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.CORRECT,
            corrected_answer=(
                "Use Alembic for database migrations with version control and rollback support."
            ),
            responder="farmer1st",
            github_comment_id=12346,
        )

        result = escalation_handler.process_response(escalation, human_response)

        assert result.escalation_resolved is True
        assert result.action_taken == HumanAction.CORRECT
        assert result.final_answer.confidence == 100
        assert "Alembic" in result.final_answer.answer

    def test_human_adds_context_triggers_reroute_e2e(self) -> None:
        """Test end-to-end: human adds context and triggers re-routing."""
        from agent_hub.escalation import EscalationHandler
        from agent_hub.models import EscalationRequest

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["caching"],
                    },
                },
            }
        )

        escalation_handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="caching",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What caching strategy should we use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use Redis for caching.",
            rationale="Popular choice but need more context about usage patterns.",
            confidence=55,
            uncertainty_reasons=["Unknown cache size requirements", "Unclear data access patterns"],
            model_used="sonnet",
            duration_seconds=2.0,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        # Human adds context
        human_response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.ADD_CONTEXT,
            additional_context=(
                "We expect 10K concurrent users. Cache needs to handle "
                "session data and user preferences. Must survive pod restarts."
            ),
            responder="farmer1st",
            github_comment_id=12347,
        )

        result = escalation_handler.process_response(escalation, human_response)

        assert result.escalation_resolved is False
        assert result.action_taken == HumanAction.ADD_CONTEXT
        assert result.needs_reroute is True
        assert result.updated_question is not None
        assert "10K concurrent users" in result.updated_question.context
        assert "session data" in result.updated_question.context

    def test_topic_override_affects_escalation_threshold_e2e(self) -> None:
        """Test end-to-end: security topic with higher threshold triggers escalation."""
        from agent_hub.escalation import EscalationHandler
        from agent_hub.validator import ConfidenceValidator

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["security"],
                    },
                },
                "overrides": {
                    "security": {
                        "agent": "architect",
                        "confidence_threshold": 95,  # Higher threshold for security
                    },
                },
            }
        )

        validator = ConfidenceValidator(config)
        escalation_handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="How should we implement password reset?",
            feature_id="005-user-auth",
        )

        # 90% confidence - passes default 80% but fails security 95%
        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use time-limited tokens sent via email.",
            rationale="Standard approach with good security properties for password reset.",
            confidence=90,
            model_used="opus",
            duration_seconds=2.5,
        )

        validation = validator.validate(answer, topic="security")

        assert validation.outcome == ValidationOutcome.ESCALATE
        assert validation.threshold_used == 95

        escalation = escalation_handler.create_escalation(question, validation)
        assert escalation.threshold_used == 95


@pytest.mark.journey("AH-003")
class TestConfidenceEscalationE2E:
    """E2E tests for confidence validation and escalation via ask_expert (T051 - US3).

    User Story 3: Validate Confidence and Escalate
    - Low-confidence answers trigger human escalation with pending status
    - Escalation includes escalation_id for tracking
    - Topic-specific thresholds can trigger escalation
    """

    @patch("agent_hub.router.subprocess.run")
    def test_ask_expert_low_confidence_creates_escalation_e2e(self, mock_run: MagicMock) -> None:
        """Test that low confidence answer creates escalation with proper fields."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Consider using AES encryption", '
                '"rationale": "Standard choice but need to verify key management", '
                '"confidence": 65, '
                '"uncertainty_reasons": ["Key management unclear", "Compliance unclear"]}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["security"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="security",
            question="What encryption should we use for user data?",
            context="HIPAA compliance required",
            feature_id="005-encryption",
        )

        # Verify escalation was created
        assert response.status == ResponseStatus.PENDING_HUMAN
        assert response.confidence == 65
        assert response.escalation_id is not None
        assert len(response.escalation_id) > 0

        # Verify answer details still present
        assert "AES" in response.answer
        assert response.rationale is not None

    @patch("agent_hub.router.subprocess.run")
    def test_ask_expert_topic_override_triggers_escalation_e2e(self, mock_run: MagicMock) -> None:
        """Test that topic override threshold can trigger escalation."""
        from agent_hub.hub import AgentHub

        # 88% confidence - passes default 80% but fails compliance 95%
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Store data in encrypted S3 buckets", '
                '"rationale": "AWS best practice for data storage with encryption at rest", '
                '"confidence": 88}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["compliance", "storage"],
                    },
                },
                "overrides": {
                    "compliance": {
                        "agent": "architect",
                        "confidence_threshold": 95,  # Higher threshold for compliance
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="compliance",
            question="How should we store PII for GDPR compliance?",
            feature_id="005-compliance",
        )

        # 88% < 95% topic threshold, should escalate
        assert response.status == ResponseStatus.PENDING_HUMAN
        assert response.confidence == 88
        assert response.escalation_id is not None

    @patch("agent_hub.router.subprocess.run")
    def test_ask_expert_high_confidence_no_escalation_e2e(self, mock_run: MagicMock) -> None:
        """Test that high confidence answers don't create escalation."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use PostgreSQL with connection pooling", '
                '"rationale": "Reliable choice with query optimization", '
                '"confidence": 95}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["database"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="database",
            question="What database should we use for transaction processing?",
            feature_id="005-database",
        )

        # High confidence - no escalation
        assert response.status == ResponseStatus.RESOLVED
        assert response.confidence == 95
        assert response.escalation_id is None

    @patch("agent_hub.router.subprocess.run")
    def test_ask_expert_escalation_preserves_uncertainty_reasons_e2e(
        self, mock_run: MagicMock
    ) -> None:
        """Test that escalation response includes uncertainty reasons."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Maybe use Redis", '
                '"rationale": "Common choice but depends on scale requirements", '
                '"confidence": 50, '
                '"uncertainty_reasons": '
                '["Unknown traffic volume", "Unclear persistence", "Scale unclear"]}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["caching"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="caching",
            question="What caching solution should we implement?",
            feature_id="005-caching",
        )

        assert response.status == ResponseStatus.PENDING_HUMAN
        assert response.uncertainty_reasons is not None
        assert len(response.uncertainty_reasons) == 3
        assert "Unknown traffic volume" in response.uncertainty_reasons

    @patch("agent_hub.router.subprocess.run")
    def test_ask_expert_escalation_with_session_context_e2e(self, mock_run: MagicMock) -> None:
        """Test that escalation works correctly within a session context."""
        from agent_hub.hub import AgentHub

        mock_run.side_effect = [
            # First call - high confidence
            MagicMock(
                returncode=0,
                stdout=(
                    '{"answer": "Use JWT tokens for authentication", '
                    '"rationale": "Stateless authentication perfect for distributed systems", '
                    '"confidence": 92}'
                ),
                stderr="",
            ),
            # Second call - low confidence, should escalate
            MagicMock(
                returncode=0,
                stdout=(
                    '{"answer": "Maybe 1 hour expiry", '
                    '"rationale": "Depends on security requirements and UX trade-offs", '
                    '"confidence": 55, '
                    '"uncertainty_reasons": ["Security policy undefined"]}'
                ),
                stderr="",
            ),
        ]

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["authentication", "tokens"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        # First question - high confidence
        response1 = hub.ask_expert(
            topic="authentication",
            question="What token type should we use?",
            feature_id="005-auth",
        )
        session_id = response1.session_id

        assert response1.status == ResponseStatus.RESOLVED
        assert response1.escalation_id is None

        # Second question in same session - low confidence
        response2 = hub.ask_expert(
            topic="tokens",
            question="What should be the token expiry time?",
            feature_id="005-auth",
            session_id=session_id,
        )

        assert response2.session_id == session_id  # Same session
        assert response2.status == ResponseStatus.PENDING_HUMAN
        assert response2.escalation_id is not None

        # Session should have both exchanges
        session = hub.get_session(session_id)
        assert len(session.messages) >= 4  # 2 Q&A pairs


@pytest.mark.journey("AH-004")
class TestPendingEscalationE2E:
    """E2E tests for tracking pending escalations (T058 - US4).

    User Story 4: Track Pending Escalations
    - Agents can check escalation status via check_escalation()
    - Agents can add human responses via add_human_response()
    - Human responses are fed back to session
    - NEEDS_REROUTE triggers re-query with updated context
    """

    @patch("agent_hub.router.subprocess.run")
    def test_check_escalation_returns_status_e2e(self, mock_run: MagicMock) -> None:
        """Test that check_escalation returns escalation with correct status."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Consider using OAuth2", '
                '"rationale": "Standard but need to confirm security requirements", '
                '"confidence": 55, '
                '"uncertainty_reasons": ["Security requirements unclear"]}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["authentication"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        # Create escalation via ask_expert
        response = hub.ask_expert(
            topic="authentication",
            question="What auth method for mobile app?",
            feature_id="005-auth",
        )

        assert response.status == ResponseStatus.PENDING_HUMAN
        assert response.escalation_id is not None

        # Check escalation status
        escalation = hub.check_escalation(response.escalation_id)

        assert escalation.id == response.escalation_id
        assert escalation.status == "pending"
        assert escalation.question is not None
        assert escalation.tentative_answer is not None

    @patch("agent_hub.router.subprocess.run")
    def test_add_human_response_confirms_and_resolves_e2e(self, mock_run: MagicMock) -> None:
        """Test that human confirmation resolves the escalation."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use JWT with refresh tokens", '
                '"rationale": "Good for stateless authentication", '
                '"confidence": 70}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["tokens"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="tokens",
            question="How to handle token refresh?",
            feature_id="005-tokens",
        )

        # Human confirms the answer
        result = hub.add_human_response(
            escalation_id=response.escalation_id,
            action=HumanAction.CONFIRM,
            responder="@farmer1st",
        )

        assert result.escalation_resolved is True
        assert result.action_taken == HumanAction.CONFIRM
        assert result.final_answer is not None

        # Verify escalation is now resolved
        escalation = hub.check_escalation(response.escalation_id)
        assert escalation.status == "resolved"

    @patch("agent_hub.router.subprocess.run")
    def test_add_human_response_corrects_answer_e2e(self, mock_run: MagicMock) -> None:
        """Test that human correction provides new answer with 100% confidence."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use bcrypt", '
                '"rationale": "Common choice for password hashing", '
                '"confidence": 60}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["security"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="security",
            question="How should we hash passwords?",
            feature_id="005-security",
        )

        # Human corrects the answer
        result = hub.add_human_response(
            escalation_id=response.escalation_id,
            action=HumanAction.CORRECT,
            corrected_answer="Use Argon2id - it's the current best practice for password hashing",
            responder="@farmer1st",
        )

        assert result.escalation_resolved is True
        assert result.action_taken == HumanAction.CORRECT
        assert "Argon2id" in result.final_answer.answer
        assert result.final_answer.confidence == 100

    @patch("agent_hub.router.subprocess.run")
    def test_add_human_response_adds_context_for_reroute_e2e(self, mock_run: MagicMock) -> None:
        """Test that ADD_CONTEXT triggers NEEDS_REROUTE with updated question."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use microservices", '
                '"rationale": "Depends on scale requirements", '
                '"confidence": 40, '
                '"uncertainty_reasons": ["Unknown traffic volume", "Team size unclear"]}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["architecture"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="architecture",
            question="What architecture pattern should we use?",
            feature_id="005-arch",
        )

        # Human adds context
        context = "5 developers, 50K daily users, 3 month timeline"
        result = hub.add_human_response(
            escalation_id=response.escalation_id,
            action=HumanAction.ADD_CONTEXT,
            additional_context=context,
            responder="@farmer1st",
        )

        assert result.escalation_resolved is False
        assert result.needs_reroute is True
        assert result.updated_question is not None
        assert "50K daily users" in result.updated_question.context
        assert "5 developers" in result.updated_question.context

    @patch("agent_hub.router.subprocess.run")
    def test_human_response_fed_back_to_session_e2e(self, mock_run: MagicMock) -> None:
        """Test that human response is added to session message history."""
        from agent_hub.hub import AgentHub
        from agent_hub.models import MessageRole

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use Redis for caching", '
                '"rationale": "Good for high-throughput scenarios", '
                '"confidence": 65}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["caching"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="caching",
            question="What caching solution?",
            feature_id="005-cache",
        )

        session_id = response.session_id

        # Human confirms
        hub.add_human_response(
            escalation_id=response.escalation_id,
            action=HumanAction.CONFIRM,
            responder="@farmer1st",
        )

        # Check session has human message
        session = hub.get_session(session_id)
        human_messages = [m for m in session.messages if m.role == MessageRole.HUMAN]

        assert len(human_messages) >= 1
        last_human_msg = human_messages[-1]
        assert last_human_msg.metadata is not None
        assert last_human_msg.metadata.get("action") == "confirm"
        assert last_human_msg.metadata.get("responder") == "@farmer1st"

    @patch("agent_hub.router.subprocess.run")
    def test_full_escalation_workflow_e2e(self, mock_run: MagicMock) -> None:
        """Test complete escalation workflow: create, check, resolve."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use PostgreSQL with read replicas", '
                '"rationale": "Good for read-heavy workloads", '
                '"confidence": 55}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["database"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        # Step 1: Create escalation via low-confidence answer
        response = hub.ask_expert(
            topic="database",
            question="What database scaling strategy?",
            feature_id="005-db",
        )
        assert response.status == ResponseStatus.PENDING_HUMAN
        escalation_id = response.escalation_id

        # Step 2: Check escalation status (polling simulation)
        escalation = hub.check_escalation(escalation_id)
        assert escalation.status == "pending"

        # Step 3: Human provides correction
        result = hub.add_human_response(
            escalation_id=escalation_id,
            action=HumanAction.CORRECT,
            corrected_answer="Use CockroachDB for automatic horizontal scaling",
            responder="@farmer1st",
        )

        # Step 4: Verify resolution
        assert result.escalation_resolved is True
        assert "CockroachDB" in result.final_answer.answer
        assert result.final_answer.confidence == 100

        # Step 5: Verify escalation is resolved
        resolved_escalation = hub.check_escalation(escalation_id)
        assert resolved_escalation.status == "resolved"
