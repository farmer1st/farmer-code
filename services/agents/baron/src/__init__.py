"""Baron Agent Service - SpecKit PM Agent.

Baron is a stateless agent service that handles SpecKit workflows:
- specify: Generate feature specifications
- plan: Create implementation plans
- tasks: Generate task breakdowns
- implement: Execute implementation tasks

All context is passed in the request; no server-side state is maintained.
"""

__version__ = "0.1.0"
__agent_name__ = "baron"
