# Research: Farmer Code Rebrand

**Feature**: 007-farmer-code-rebrand
**Date**: 2026-01-05

## Overview

This feature requires no research phase - it is a straightforward text replacement task with no technical unknowns.

## Decisions

### Brand Name Format

**Decision**: Use "Farmer Code" (capitalized, two words) for all display text

**Rationale**:
- Consistent with professional branding conventions
- Easy to read and understand
- Distinct from technical identifiers

**Alternatives Considered**:
- "FarmerCode" (CamelCase) - rejected: harder to read
- "FARMER CODE" (all caps) - rejected: too aggressive
- "farmer code" (lowercase) - rejected: not professional

### Technical Identifier Format

**Decision**: Use `farmer-code` (kebab-case) or `farmer_code` (snake_case) based on context

**Rationale**:
- Kebab-case for URLs, CLI commands, file names
- Snake_case for Python module names, variables
- Follows existing codebase conventions

### Scope Boundaries

**Decision**: Do NOT rename the following:
- GitHub repository name (`farmcode`)
- Existing directory paths in src/
- Python package imports
- Git history

**Rationale**: These changes would require extensive refactoring and break existing references. The visual branding change achieves the goal without technical disruption.

## No Further Research Required

All aspects of this feature are well-defined. Proceed to task generation.
