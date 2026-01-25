# Release Checklist

This document outlines the process for releasing new versions of Fluid Rower Monitor.

## Pre-Release Checklist

### 1. Code Quality
- [ ] All tests pass: `uv run pytest`
- [ ] Full tox suite passes: `uv run tox`
- [ ] Code is formatted: `uv run black fluid_rower_monitor tests`
- [ ] Lint checks pass: `uv run flake8 fluid_rower_monitor tests --max-line-length=120 --ignore=E203,W503`
- [ ] Coverage meets threshold (>80%): Check in tox output or `uv run pytest --cov=fluid_rower_monitor --cov-fail-under=80`

### 2. Version Numbers
- [ ] Update `__version__` in `fluid_rower_monitor/__init__.py`
- [ ] Update `version` in `pyproject.toml` to match
- [ ] Ensure test_version.py passes (validates version sync)

### 3. Documentation
- [ ] Update ROADMAP.md to reflect completed features
- [ ] Add entry to CHANGELOG.md (if exists, or create one)
- [ ] Update README.md if new features warrant it
- [ ] Check that docs/ are up to date with new features

### 4. Schema Changes (if applicable)
- [ ] If data format changed, update SCHEMA_VERSION in rowing_data.py
- [ ] Document migration path in docs/DEVELOPER.md
- [ ] Add migration function to migrations.py (if it exists)

## Release Process

### For Minor/Patch Releases (0.x.y)

```bash
# 1. Ensure working directory is clean
git status

# 2. Run full test suite
uv run tox

# 3. Commit any final changes
git add -A
git commit -m "Prepare release v0.x.y"

# 4. Tag the release
git tag -a v0.x.y -m "Release version 0.x.y"

# 5. Push changes and tags
git push origin main
git push origin v0.x.y
```

### For Major Releases (x.0.0)

Same as above, plus:
- [ ] Review ROADMAP.md for next phase priorities
- [ ] Consider creating GitHub release with release notes
- [ ] Notify users of breaking changes (if any)

## Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (x.0.0): Breaking changes, incompatible API changes, schema changes requiring migration
- **MINOR** (0.x.0): New features, backward-compatible functionality
- **PATCH** (0.0.x): Bug fixes, backward-compatible fixes

### Examples

- Adding `--version` flag: **0.1.0 → 0.2.0** (new feature)
- Fixing reconnection bug: **0.2.0 → 0.2.1** (bug fix)
- Changing parquet schema: **0.2.1 → 1.0.0** (breaking change)

## Quick Pre-Commit Commands

Before any push:

```bash
# Quick validation (runs in ~3 seconds)
uv run pytest && uv run black fluid_rower_monitor tests && \
  uv run flake8 fluid_rower_monitor tests --max-line-length=120 --ignore=E203,W503
```

For thorough validation before releases:

```bash
# Full validation with tox (runs in ~20 seconds)
uv run tox
```

## Rollback Process

If a release has issues:

```bash
# 1. Revert to previous tag
git checkout v0.x.y

# 2. Create fix branch
git checkout -b hotfix/issue-description

# 3. Fix, test, and merge
# ... make fixes ...
uv run tox
git checkout main
git merge hotfix/issue-description

# 4. Release patch version
git tag -a v0.x.z -m "Hotfix for issue"
git push origin main v0.x.z
```

## Notes

- Always run `uv run tox` before releasing
- Version numbers must match between `__init__.py` and `pyproject.toml`
- Keep ROADMAP.md updated to track progress
- Git tags should always use format `vX.Y.Z` (with 'v' prefix)
