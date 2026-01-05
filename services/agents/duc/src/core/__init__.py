"""Core module for Duc agent."""

from src.core.agent import DucAgent
from src.core.prompts import get_supported_topics, get_system_prompt

__all__ = ["DucAgent", "get_system_prompt", "get_supported_topics"]
