#!/bin/bash
# Run all validations for the frontend

set -e

echo "Running frontend validations..."
echo

echo "1. ESLint..."
npm run lint
echo "   ESLint passed ✓"

echo
echo "2. TypeScript type check..."
npm run type-check
echo "   Type check passed ✓"

echo
echo "3. Vitest tests..."
npm run test
echo "   Tests passed ✓"

echo
echo "4. Vite build..."
npm run build
echo "   Build passed ✓"

echo
echo "All validations passed! ✓"
