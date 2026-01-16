#!/bin/bash
# Run all validations for the backend

set -e

# Activate virtual environment
source venv/bin/activate

echo "Running backend validations..."
echo

echo "1. Ruff linting..."
ruff check app/ tests/
echo "   Ruff passed ✓"

echo
echo "2. Mypy type checking..."
mypy app/
echo "   Mypy passed ✓"

echo
echo "3. Pytest..."
pytest tests/ -q
echo "   Pytest passed ✓"

echo
echo "All validations passed! ✓"
