# DataPrepToolkit v1.0.0 — GitHub Release Execution Guide

**Date:** 2026-07-19  
**Remote:** https://github.com/Arasoul/DataPrepToolkit.git  
**Branch:** main  
**Tag:** v1.0.0

---

## 1. Pre-Release Verification Checklist

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Branch is `main` | PASS | `git branch` shows `main` |
| 2 | Branch up to date with `origin/main` | PASS | `git status` confirms |
| 3 | Version is 1.0.0 | PASS | `pyproject.toml:7`, `__init__.py:19`, `README.md:10`, `CHANGELOG.md:8` |
| 4 | Tests pass | PASS | 171/171 passed (0.91s) |
| 5 | CHANGELOG updated | PASS | v1.0.0 section rewritten with full overview |
| 6 | RELEASE_NOTES.md exists | PASS | Created, complete |
| 7 | README final | PASS | Badges accurate (171 tests, 92% coverage) |
| 8 | No TODOs/placeholder text | PASS | Grep found zero matches in docs |
| 9 | No temporary files tracked | PASS | `.coverage`, `.pytest_cache/`, etc. are gitignored |
| 10 | No tags exist yet | PASS | `git tag -l` returns empty |
| 11 | Development Status | PASS | `Production/Stable` classifier set |
| 12 | PEP 561 | PASS | `py.typed` present |
| 13 | Dependencies clean | PASS | Only pandas, numpy |

---

## 2. Release Commit

### Files to Stage

**Source code (engineering improvements + release prep):**

```
src/datapreptoolkit/__init__.py
src/datapreptoolkit/analyzer.py
src/datapreptoolkit/cleaner.py
src/datapreptoolkit/config.py
src/datapreptoolkit/exceptions.py
src/datapreptoolkit/loader.py
src/datapreptoolkit/optimizer.py
src/datapreptoolkit/outliers.py
src/datapreptoolkit/reporter.py
src/datapreptoolkit/utils.py
src/datapreptoolkit/validator.py
src/datapreptoolkit/py.typed
```

**Tests:**

```
tests/conftest.py
tests/test_analyzer.py
tests/test_cleaner.py
tests/test_config.py
tests/test_exceptions.py
tests/test_integration.py
tests/test_loader.py
tests/test_optimizer.py
tests/test_utils.py
tests/test_validator.py
```

**Configuration & docs:**

```
pyproject.toml
README.md
CHANGELOG.md
RELEASE_NOTES.md
requirements.txt
.gitignore
.github/workflows/ci.yml
```

**Examples:**

```
examples/full_workflow.ipynb
examples/full_workflow.py
```

**Screenshots:**

```
screenshots/Slide_1.png
screenshots/Slide_2.png
screenshots/Slide_3.png
```

### Files to EXCLUDE (internal, not for public release)

```
AUDIT_REPORT.md          # Internal audit document
ENGINEERING_READINESS.md # Internal engineering doc
RELEASE_PREPARATION.md   # Internal release prep doc
.coverage                # Test coverage data
.mypy_cache/             # mypy cache
.pytest_cache/           # pytest cache
.ruff_cache/             # ruff cache
reports/*.html           # Generated reports
reports/*.csv            # Generated reports
```

### Exact Git Commands

```bash
# Stage all release files
git add \
  src/datapreptoolkit/__init__.py \
  src/datapreptoolkit/analyzer.py \
  src/datapreptoolkit/cleaner.py \
  src/datapreptoolkit/config.py \
  src/datapreptoolkit/exceptions.py \
  src/datapreptoolkit/loader.py \
  src/datapreptoolkit/optimizer.py \
  src/datapreptoolkit/outliers.py \
  src/datapreptoolkit/reporter.py \
  src/datapreptoolkit/utils.py \
  src/datapreptoolkit/validator.py \
  src/datapreptoolkit/py.typed \
  tests/conftest.py \
  tests/test_analyzer.py \
  tests/test_cleaner.py \
  tests/test_config.py \
  tests/test_exceptions.py \
  tests/test_integration.py \
  tests/test_loader.py \
  tests/test_optimizer.py \
  tests/test_utils.py \
  tests/test_validator.py \
  pyproject.toml \
  README.md \
  CHANGELOG.md \
  RELEASE_NOTES.md \
  requirements.txt \
  .gitignore \
  .github/workflows/ci.yml \
  examples/full_workflow.ipynb \
  examples/full_workflow.py \
  screenshots/Slide_1.png \
  screenshots/Slide_2.png \
  screenshots/Slide_3.png

# Verify staged files
git diff --cached --stat

# Commit
git commit -m "release: v1.0.0 — first stable release

Production-quality Python toolkit for automated data preprocessing,
profiling, and quality reporting.

Changes:
- Remove unused dependencies (scikit-learn, tabulate)
- Add py.typed PEP 561 marker
- Fix spelling consistency (optimise_memory)
- Fix dead code branch in generate_feature_summaries()
- Remove unused _STRATEGY_DISPATCH dict
- Fix exception hierarchy (load_csv raises LoadError)
- Make quality_weights immutable via MappingProxyType
- Narrow exception handling in detect_invalid_values()
- Add 5 integration tests for full pipeline validation
- Harden CI/CD (format check, coverage floor, caching, codecov v5)
- Update classifiers to Production/Stable
- Add Python 3.13 to CI matrix and classifiers
- Update CHANGELOG and README for v1.0.0 release
- Add RELEASE_NOTES.md for GitHub Release

Quality gates:
- 171 tests passing, 92% coverage
- ruff lint clean, ruff format clean, mypy clean
- PEP 561 compliant
- Only pandas and numpy as runtime dependencies"
```

### What This Commit Represents

This is the **release commit** — a single, atomic commit that contains every change from development through engineering review, remediation, verification, and release preparation. It is the exact state of the codebase that will be tagged as v1.0.0.

Using a single release commit (rather than many small commits) is standard practice for projects that develop on a separate branch and merge to `main` for release. It keeps the release history clean and makes `git bisect` and `git revert` straightforward.

---

## 3. Git Tag

### Why Annotated Tags

Annotated tags are preferred over lightweight tags for official releases because they:

- Store the tagger name, date, and tag message
- Can be signed with GPG for authenticity verification
- Are the standard for releases in the Python ecosystem
- Appear in `git tag -n` output with descriptive messages
- Are what PyPI and GitHub expect for release tags

### Exact Git Commands

```bash
# Create annotated tag
git tag -a v1.0.0 -m "DataPrepToolkit v1.0.0 — First Stable Release

Production-quality Python toolkit for automated data preprocessing,
profiling, and quality reporting.

171 tests, 92% coverage, PEP 561 compliant.
Only depends on pandas and numpy.

See RELEASE_NOTES.md for full details."
```

### Verify Tag

```bash
# Show tag details
git tag -n v1.0.0

# Show tag with commit
git show v1.0.0
```

---

## 4. Push to GitHub

### Exact Git Commands

```bash
# Push the release commit to origin/main
git push origin main

# Push the annotated tag to origin
git push origin v1.0.0
```

### What Each Command Does

| Command | Effect |
|---------|--------|
| `git push origin main` | Uploads the release commit to the `main` branch on GitHub. All files become visible in the repository. |
| `git push origin v1.0.0` | Uploads the annotated tag. GitHub will recognize this as a release candidate. The tag is permanent and immutable. |

### Note on Push Order

The commit must be pushed **before** the tag. GitHub creates the tag reference on the remote only after the commit exists there. Pushing the tag first would create a dangling reference.

---

## 5. GitHub Release Creation Guide

### Via GitHub Web Interface

1. Navigate to: `https://github.com/Arasoul/DataPrepToolkit/releases/new`

2. **Choose a tag:** Select `v1.0.0` from the dropdown (it will appear after `git push origin v1.0.0`)

3. **Release title:** `DataPrepToolkit v1.0.0`

4. **Description:** Paste the contents of `RELEASE_NOTES.md`

5. **Options:**
   - [x] **Set as the latest release** — checked (this is the most recent stable release)
   - [ ] **Pre-release** — unchecked (this is a stable release)
   - [ ] **Create a discussion for this release** — optional

6. Click **Publish release**

### Via GitHub CLI (Alternative)

```bash
gh release create v1.0.0 \
  --title "DataPrepToolkit v1.0.0" \
  --notes-file RELEASE_NOTES.md \
  --latest
```

### Option Explanations

| Option | Value | Reason |
|--------|-------|--------|
| Tag | `v1.0.0` | Semantic versioning tag |
| Title | `DataPrepToolkit v1.0.0` | Professional, scannable |
| Latest | Yes | First and only stable release |
| Pre-release | No | This is a stable production release |
| Draft | No | Release is ready for immediate publication |

---

## 6. GitHub Release Title

```
DataPrepToolkit v1.0.0 — First Stable Release
```

---

## 7. GitHub Release Description

The full release description is in `RELEASE_NOTES.md`. Here is the content formatted for GitHub Releases:

---

### DataPrepToolkit v1.0.0

First stable release of DataPrepToolkit — a production-quality Python toolkit for automated data preprocessing, profiling, and quality reporting.

#### Overview

DataPrepToolkit automates the repetitive data preparation tasks that precede every analysis project: loading, validation, cleaning, optimization, outlier detection, and quality reporting. Instead of rewriting the same preprocessing code for every project, use DataPrepToolkit as a reusable foundation.

#### Major Features

- **Load & Profile** — CSV/DataFrame loading with automatic dataset profiling
- **Validate** — Rule-based validation with six rule types
- **Clean** — 10 imputation strategies, deduplication, datetime parsing, invalid value detection
- **Optimize** — Automatic type downcasting with measurable memory savings
- **Detect** — IQR and Z-score outlier detection
- **Report** — Professional HTML/CSV quality reports with configurable scoring

#### Engineering Improvements

- 171 unit and integration tests with 92% code coverage
- Type hints on all public APIs with mypy enforcement
- PEP 561 compliant (`py.typed` marker)
- Hardened CI/CD: ruff lint, ruff format, mypy, coverage floor, multi-Python matrix
- Clean dependency footprint: only `pandas` and `numpy`
- Immutable configuration via `MappingProxyType`
- Consistent exception hierarchy rooted at `DataPrepError`

#### Breaking Changes

No breaking changes. This is the first stable public release.

#### Known Limitations

- In-memory processing (Pandas DataFrames only)
- Configuration via Python objects (no YAML/CLI)
- No streaming support

#### Installation

```bash
pip install datapreptoolkit
```

#### Future Roadmap

DataPrepToolkit is the foundation of a planned automation ecosystem: AutoEDA, AutoAnalytics, AutoBI.

#### License

MIT License

---

## 8. Post-Release Verification Checklist

After publishing the GitHub Release, verify:

| # | Check | How to Verify | Status |
|---|-------|---------------|--------|
| 1 | Release appears under Releases | `https://github.com/Arasoul/DataPrepToolkit/releases` | |
| 2 | Tag `v1.0.0` exists | `https://github.com/Arasoul/DataPrepToolkit/tags` | |
| 3 | README displays correctly | `https://github.com/Arasoul/DataPrepToolkit` | |
| 4 | Release notes render correctly | Click the release, verify formatting | |
| 5 | Badges are correct | Build status, test count (171), coverage (92%) | |
| 6 | Source archive downloadable | Click "Source code (zip)" on release page | |
| 7 | Repository is public | Verify from incognito/private window | |
| 8 | Installation works | `pip install datapreptoolkit` on a clean environment | |
| 9 | Import works | `python -c "from datapreptoolkit import __version__; print(__version__)"` → `1.0.0` | |
| 10 | Example notebook accessible | `examples/full_workflow.ipynb` renders on GitHub | |

---

## 9. Project Status After Release

```
Project:    DataPrepToolkit
Status:     Released
Version:    1.0.0
License:    MIT
PyPI:       datapreptoolkit
Repository: https://github.com/Arasoul/DataPrepToolkit

Maintenance Mode:  Active (Bug Fixes & Minor Improvements)
Next Version:      1.1.0

Future Work:
- Bug fixes and stability improvements
- Performance optimizations
- Ecosystem integration (AutoEDA, AutoAnalytics, AutoBI)
- New features in future minor/patch versions

Support:
- Issues: https://github.com/Arasoul/DataPrepToolkit/issues
- Contributing: CONTRIBUTING.md
```

---

## 10. Final Release Confirmation

### Release Decision: APPROVED

| Criterion | Evidence | Verdict |
|-----------|----------|---------|
| Code is complete | All 171 tests pass, 92% coverage | PASS |
| Documentation is complete | README, CHANGELOG, RELEASE_NOTES.md | PASS |
| Version is consistent | 1.0.0 in all 4 locations | PASS |
| No internal docs tracked | AUDIT_REPORT.md, ENGINEERING_READINESS.md are untracked | PASS |
| Clean release commit | All changes staged in single commit | PASS |
| Tag is annotated | `git tag -a v1.0.0` | PASS |
| Push commands ready | Origin confirmed, commands documented | PASS |
| GitHub Release ready | Title, description, options documented | PASS |
| Post-release checklist | 10 verification steps documented | PASS |

**DataPrepToolkit v1.0.0 is ready for official release.**

Execute the commands in Sections 2, 3, and 4 in order, then complete Section 5 via the GitHub web interface or CLI.
