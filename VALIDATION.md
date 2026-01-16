# Validation Setup - Complete

## What's Configured

### 1. GitHub Actions CI (`.github/workflows/ci.yml`)
- Runs automatically on push/PR to `main` or `develop`
- Tests both backend and frontend
- Shows ✅ or ❌ on GitHub commits

### 2. Pre-Commit Hooks
- Runs automatically before every `git commit`
- Fast checks only (ruff, mypy, eslint, type-check)
- Blocks commit if checks fail

### 3. Validation Scripts
- `backend/scripts/validate.sh` - Run all backend checks
- `frontend/scripts/validate.sh` - Run all frontend checks
- `scripts/validate-all.sh` - Run everything from project root

## Quick Reference

```bash
# Run validations manually
cd backend && ./scripts/validate.sh
cd frontend && ./scripts/validate.sh
# OR from project root
./scripts/validate-all.sh

# Test pre-commit hooks manually
cd backend && pre-commit run --all-files
cd frontend && pre-commit run --all-files

# Skip hooks for one commit (use sparingly!)
git commit --no-verify -m "message"
```

## Current Status

All validations passing:

| Check | Backend | Frontend |
|-------|---------|----------|
| Lint (ruff/eslint) | ✓ | ✓ |
| Type Check (mypy/tsc) | ✓ | ✓ |
| Tests (pytest/vitest) | ✓ (10/10) | ✓ (4/4) |
| Build | - | ✓ |

## Fix Applied for Recurring E402 Errors

Added `E402` to global ruff ignores in `pyproject.toml` since `sys.path.insert()` before imports is intentional in this project structure.
