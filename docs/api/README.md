# API Documentation

This directory contains API documentation for the Farmer Code project.

## REST APIs

When REST API services are added (FastAPI), their OpenAPI specifications will be exported here:

- `openapi.yaml` - OpenAPI 3.0 specification (auto-generated from FastAPI)

Access interactive documentation at runtime:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc` (recommended for reading)

## Python Libraries

For Python library documentation, see:

| Module | README | Contracts |
|--------|--------|-----------|
| `worktree_manager` | [`src/worktree_manager/README.md`](../../src/worktree_manager/README.md) | [`specs/002-git-worktree-manager/contracts/`](../../specs/002-git-worktree-manager/contracts/) |
| `github_integration` | [`src/github_integration/README.md`](../../src/github_integration/README.md) | [`specs/001-github-integration-core/contracts/`](../../specs/001-github-integration-core/contracts/) |

## Documentation Standards

All APIs follow the documentation standards defined in the [Constitution v1.6.3](../../.specify/memory/constitution.md):

- REST APIs: OpenAPI spec with Swagger UI and ReDoc
- Python libraries: Google-style docstrings with module README
- All public interfaces documented with examples and error conditions
