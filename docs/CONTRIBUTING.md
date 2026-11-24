# Contributing to KubeGuide

Welcome! This guide outlines development practices, testing standards, and pull request procedures for KubeGuide.

---

## 1. Local Environment Setup

KubeGuide uses `uv` for fast, deterministic Python environment management.

```bash
# 1. Clone repository and install dependencies
git clone https://github.com/shivanistalin2006-dot/prince28-dev04-kubeguide.git
cd prince28-dev04-kubeguide
uv sync

# 2. Install pre-commit hooks
uv run pre-commit install
```

---

## 2. Code Quality & Formatting

All code must pass pre-commit checks before being committed:
* **Linting:** `uv run ruff check .`
* **Formatting:** `uv run ruff format .`
* **Pre-commit full suite:** `uv run pre-commit run --all-files`

---

## 3. Testing Standards

Every new feature or bug fix must include corresponding unit tests in `tests/unit/`:

```bash
# Run unit test suite
uv run pytest tests/unit

# Run full test suite with coverage
uv run poe test
```

Unit tests must execute without requiring external databases or live network endpoints. Use mocks or dependency overrides where necessary.

---

## 4. Branching & Pull Request Process

1. Create a feature branch from the latest `main`:
   ```bash
   git switch main
   git pull origin main
   git switch -c feat/my-new-feature
   ```
2. Make granular, logically grouped commits with clear commit messages following Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
3. Push to your branch and open a Pull Request.
4. Ensure all CI status checks (`lint and test` and `build image`) pass before merging into `main`.
