#!/bin/bash
# Setup pre-commit hooks for the project

set -e

echo "Setting up pre-commit hooks..."
echo

# Install pre-commit in backend
echo "1. Installing pre-commit in backend..."
cd backend
source venv/bin/activate
pip install pre-commit
pre-commit install

cd ..

# Install pre-commit in frontend
echo
echo "2. Installing pre-commit in frontend..."
cd frontend
npm install --save-dev pre-commit
pre-commit install

cd ..

echo
echo "✓ Pre-commit hooks installed!"
echo
echo "Now when you run 'git commit', the hooks will automatically:"
echo "  - Backend: Run ruff and mypy"
echo "  - Frontend: Run eslint and type-check"
echo
echo "To skip hooks temporarily, use: git commit --no-verify"
