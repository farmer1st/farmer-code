"""Contract tests for RoutingConfig JSON schema."""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate

# Load the JSON schema
SCHEMA_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "specs"
    / "004-knowledge-router"
    / "contracts"
    / "routing-config.json"
)


@pytest.fixture
def routing_config_schema() -> dict:
    """Load the RoutingConfig JSON schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


class TestRoutingConfigSchemaContract:
    """Contract tests for routing configuration schema."""

    def test_minimal_config_matches_schema(self, routing_config_schema: dict) -> None:
        """Test minimal valid config matches schema."""
        config = {
            "defaults": {
                "confidence_threshold": 80,
            },
            "agents": {},
        }
        validate(instance=config, schema=routing_config_schema)

    def test_full_config_matches_schema(self, routing_config_schema: dict) -> None:
        """Test full config with all options matches schema."""
        config = {
            "defaults": {
                "confidence_threshold": 80,
                "timeout_seconds": 120,
                "model": "sonnet",
            },
            "agents": {
                "architect": {
                    "name": "@duc",
                    "topics": ["authentication", "database", "architecture"],
                    "model": "opus",
                },
                "product": {
                    "name": "@veuve",
                    "topics": ["scope", "priority"],
                },
            },
            "overrides": {
                "security": {
                    "agent": "architect",
                    "confidence_threshold": 95,
                },
                "budget": {
                    "agent": "human",
                },
            },
            "execution_agents": {
                "qa": {
                    "name": "@marie",
                    "scope": ["tests/"],
                    "model": "sonnet",
                },
                "dev": {
                    "name": "@dede",
                    "scope": ["src/"],
                },
            },
        }
        validate(instance=config, schema=routing_config_schema)

    def test_missing_defaults_rejected_by_schema(self, routing_config_schema: dict) -> None:
        """Test that schema rejects config without defaults."""
        invalid_config = {
            "agents": {},
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_config, schema=routing_config_schema)

    def test_missing_agents_rejected_by_schema(self, routing_config_schema: dict) -> None:
        """Test that schema rejects config without agents."""
        invalid_config = {
            "defaults": {
                "confidence_threshold": 80,
            },
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_config, schema=routing_config_schema)

    def test_invalid_confidence_threshold_rejected(self, routing_config_schema: dict) -> None:
        """Test that schema rejects invalid confidence threshold."""
        invalid_config = {
            "defaults": {
                "confidence_threshold": 150,  # Invalid: > 100
            },
            "agents": {},
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_config, schema=routing_config_schema)

    def test_invalid_model_rejected(self, routing_config_schema: dict) -> None:
        """Test that schema rejects invalid model names."""
        invalid_config = {
            "defaults": {
                "confidence_threshold": 80,
                "model": "invalid_model",  # Not opus/sonnet/haiku
            },
            "agents": {},
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_config, schema=routing_config_schema)

    def test_invalid_agent_name_pattern_rejected(self, routing_config_schema: dict) -> None:
        """Test that schema rejects invalid agent name patterns."""
        invalid_config = {
            "defaults": {
                "confidence_threshold": 80,
            },
            "agents": {
                "architect": {
                    "name": "duc",  # Missing @ prefix
                    "topics": ["authentication"],
                },
            },
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_config, schema=routing_config_schema)

    def test_agent_without_topics_rejected(self, routing_config_schema: dict) -> None:
        """Test that schema rejects agent without topics."""
        invalid_config = {
            "defaults": {
                "confidence_threshold": 80,
            },
            "agents": {
                "architect": {
                    "name": "@duc",
                    # Missing topics
                },
            },
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_config, schema=routing_config_schema)

    def test_execution_agent_matches_schema(self, routing_config_schema: dict) -> None:
        """Test execution agent definition matches schema."""
        config = {
            "defaults": {
                "confidence_threshold": 80,
            },
            "agents": {},
            "execution_agents": {
                "devops": {
                    "name": "@gustave",
                    "scope": ["k8s/", "argocd/", "helm/"],
                    "model": "sonnet",
                },
            },
        }
        validate(instance=config, schema=routing_config_schema)

    def test_override_with_threshold_matches_schema(self, routing_config_schema: dict) -> None:
        """Test override rule with threshold matches schema."""
        config = {
            "defaults": {
                "confidence_threshold": 80,
            },
            "agents": {},
            "overrides": {
                "compliance": {
                    "agent": "human",
                    "confidence_threshold": 100,
                },
            },
        }
        validate(instance=config, schema=routing_config_schema)
