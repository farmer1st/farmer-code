#!/usr/bin/env bash
# Run all tests across services, avoiding conftest collisions
set -e

echo "Running tests for all services..."
echo ""

# Track overall exit code
exit_code=0

# Run shared tests
echo "=== services/shared ==="
if uv run pytest services/shared/tests -q --tb=short 2>&1; then
    echo "✓ shared tests passed"
else
    echo "✗ shared tests failed"
    exit_code=1
fi
echo ""

# Run orchestrator tests
echo "=== services/orchestrator ==="
if uv run pytest services/orchestrator/tests -q --tb=short 2>&1; then
    echo "✓ orchestrator tests passed"
else
    echo "✗ orchestrator tests failed"
    exit_code=1
fi
echo ""

# Run agent-hub tests
echo "=== services/agent-hub ==="
if uv run pytest services/agent-hub/tests -q --tb=short 2>&1; then
    echo "✓ agent-hub tests passed"
else
    echo "✗ agent-hub tests failed"
    exit_code=1
fi
echo ""

if [ $exit_code -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed."
fi

exit $exit_code
