# Orchestrator Service Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for package management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system -e .

# Copy source code
COPY src/ ./src/

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///./data/orchestrator.db

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
