# Feature Specification: Farmer Code Rebrand

**Feature Branch**: `007-farmer-code-rebrand`
**Created**: 2026-01-05
**Status**: Draft
**Input**: User description: "Rebrand app from farmcode/farm code to Farmer Code"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent Brand in Documentation (Priority: P1)

When developers or users read any documentation, they see a consistent brand name "Farmer Code" throughout all README files, module docs, and architecture documents.

**Why this priority**: Documentation is the primary touchpoint for understanding the project. Inconsistent branding creates confusion about the product identity.

**Independent Test**: Open any documentation file and verify "Farmer Code" appears consistently, with no instances of "farmcode" or "farm code" in prose text.

**Acceptance Scenarios**:

1. **Given** a user opens the root README, **When** they read the project description, **Then** they see "Farmer Code" as the product name
2. **Given** a developer reads module documentation, **When** they see brand references, **Then** all display text uses "Farmer Code" capitalization
3. **Given** a user searches documentation for "farmcode", **When** results appear, **Then** only technical identifiers (paths, package names) are found, not brand text

---

### User Story 2 - Correct Project Metadata (Priority: P1)

Project configuration files display the correct brand name in metadata fields while maintaining valid technical identifiers.

**Why this priority**: Project metadata appears in package managers, build outputs, and developer tools - incorrect branding here propagates confusion.

**Independent Test**: Run package info commands and verify display name shows "Farmer Code" while package identifier uses appropriate format.

**Acceptance Scenarios**:

1. **Given** a developer checks pyproject.toml, **When** they view project metadata, **Then** the display name field shows "Farmer Code"
2. **Given** the project is installed as a package, **When** package info is displayed, **Then** the human-readable name shows "Farmer Code"

---

### User Story 3 - Developer Context Files Updated (Priority: P2)

AI assistant context files (CLAUDE.md) and developer guides use the correct brand name so that AI-assisted development reflects the proper product identity.

**Why this priority**: AI assistants read these files to understand the project - correct branding ensures accurate AI responses about the product.

**Independent Test**: Read CLAUDE.md files and verify all references use "Farmer Code" for the product name.

**Acceptance Scenarios**:

1. **Given** an AI assistant reads CLAUDE.md, **When** it describes the project, **Then** it uses "Farmer Code" as the product name
2. **Given** a developer reads the development guidelines, **When** they see project references, **Then** "Farmer Code" is used consistently

---

### Edge Cases

- Technical paths and package names (e.g., `farmer_code`, `farmer-code`) should remain as valid identifiers
- Git repository name on GitHub remains unchanged (organizational decision outside this scope)
- Historical commit messages are not modified
- Import statements and module paths follow Python conventions (snake_case)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All README files MUST display "Farmer Code" as the product name in headings and prose
- **FR-002**: pyproject.toml MUST use "Farmer Code" in the project description/display name field
- **FR-003**: All module docstrings MUST reference "Farmer Code" when describing the product
- **FR-004**: CLAUDE.md files MUST use "Farmer Code" as the product name
- **FR-005**: Documentation titles MUST use "Farmer Code" (e.g., "Farmer Code Development Guidelines")
- **FR-006**: User-facing text in code comments MUST use "Farmer Code" for brand references
- **FR-007**: Technical identifiers MUST use appropriate formats: `farmer-code` (kebab-case) or `farmer_code` (snake_case)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero instances of "farmcode" (single word) appear in prose text across all documentation
- **SC-002**: Zero instances of "farm code" (two lowercase words) appear anywhere in the codebase
- **SC-003**: 100% of README files use "Farmer Code" in their title or first paragraph
- **SC-004**: All CLAUDE.md files reference the project as "Farmer Code"
- **SC-005**: pyproject.toml contains "Farmer Code" in project metadata

## Assumptions

- The GitHub repository name (`farmcode`) will not be renamed as part of this feature
- Python package/module directory names may remain as-is if renaming would break imports
- This is a cosmetic/branding change only - no functional code changes required
- Historical git history is preserved as-is
