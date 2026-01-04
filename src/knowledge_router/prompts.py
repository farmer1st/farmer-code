"""Prompt templates for Knowledge Router agents.

This module defines the prompt templates used when dispatching
questions to knowledge agents and tasks to execution agents.
"""

# Template for knowledge agent questions
KNOWLEDGE_AGENT_PROMPT = """You are {agent_name}, the {agent_role} Agent.

Answer the following question. Your response MUST be valid JSON with this structure:
{{
  "answer": "your answer here",
  "rationale": "why you believe this is correct (at least 20 characters)",
  "confidence": 85,
  "uncertainty_reasons": ["reason 1", "reason 2"]
}}

Base your confidence on:
- 90-100: You have specific knowledge/documentation about this
- 70-89: You're making an informed inference based on patterns
- 50-69: You have general knowledge but significant uncertainty
- 0-49: You're guessing, recommend human input

If confidence < 100, include uncertainty_reasons explaining what you don't know.

Question: {question}

{context_section}
{options_section}
"""

# Template for execution agent tasks (to be implemented in Phase 7)
EXECUTION_AGENT_PROMPT = """You are {agent_name}, the {agent_role} Agent.

You have been assigned the following task:

## Task: {task_title}

{task_description}

## Acceptance Criteria
{acceptance_criteria}

## File Scope
You may ONLY modify files in these directories:
{file_scope}

## Instructions
1. Implement the task according to the acceptance criteria
2. Only modify files within your allowed scope
3. Follow existing code patterns and conventions
4. Write clean, well-documented code

Begin implementation.
"""


def format_knowledge_prompt(
    agent_name: str,
    agent_role: str,
    question: str,
    context: str = "",
    options: list[str] | None = None,
) -> str:
    """Format a knowledge agent prompt.

    Args:
        agent_name: Display name (e.g., '@duc').
        agent_role: Role name (e.g., 'Architect').
        question: The question text.
        context: Optional context for the question.
        options: Optional answer choices.

    Returns:
        Formatted prompt string.
    """
    context_section = ""
    if context:
        context_section = f"Context: {context}"

    options_section = ""
    if options:
        options_section = "Options:\n" + "\n".join(f"  - {opt}" for opt in options)

    return KNOWLEDGE_AGENT_PROMPT.format(
        agent_name=agent_name,
        agent_role=agent_role,
        question=question,
        context_section=context_section,
        options_section=options_section,
    )


def format_execution_prompt(
    agent_name: str,
    agent_role: str,
    task_title: str,
    task_description: str,
    acceptance_criteria: list[str],
    file_scope: list[str],
) -> str:
    """Format an execution agent prompt.

    Args:
        agent_name: Display name (e.g., '@marie').
        agent_role: Role name (e.g., 'QA').
        task_title: Task title.
        task_description: Task description.
        acceptance_criteria: List of acceptance criteria.
        file_scope: Directories agent can modify.

    Returns:
        Formatted prompt string.
    """
    criteria_text = "\n".join(f"- {c}" for c in acceptance_criteria)
    scope_text = "\n".join(f"- {s}" for s in file_scope)

    return EXECUTION_AGENT_PROMPT.format(
        agent_name=agent_name,
        agent_role=agent_role,
        task_title=task_title,
        task_description=task_description,
        acceptance_criteria=criteria_text,
        file_scope=scope_text,
    )
