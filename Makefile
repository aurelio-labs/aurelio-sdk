format:
	poetry run ruff format .

PYTHON_FILES=.
lint: PYTHON_FILES=.
lint_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$')

lint lint_diff:
	poetry run ruff check .
	poetry run mypy $(PYTHON_FILES)
