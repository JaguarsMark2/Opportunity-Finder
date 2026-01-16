#!/bin/bash
# Run all validations for the entire project

set -e

echo "=========================================="
echo "Running ALL validations"
echo "=========================================="
echo

echo "=========================================="
echo "BACKEND VALIDATIONS"
echo "=========================================="
cd backend
./scripts/validate.sh

echo
echo "=========================================="
echo "FRONTEND VALIDATIONS"
echo "=========================================="
cd ../frontend
./scripts/validate.sh

echo
echo "=========================================="
echo "ALL VALIDATIONS PASSED! ✓✓✓"
echo "=========================================="
