"""Core module for Marie agent."""

from src.core.agent import MarieAgent
from src.core.prompts import get_supported_topics, get_system_prompt

__all__ = ["MarieAgent", "get_system_prompt", "get_supported_topics"]
