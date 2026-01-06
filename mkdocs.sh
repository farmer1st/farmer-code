#!/bin/bash
# Serve MkDocs documentation locally
# Docs dependencies are installed via optional [docs] group
uv run --extra docs mkdocs serve -a localhost:8080
