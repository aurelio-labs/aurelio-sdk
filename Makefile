format:
	poetry run black --target-version py39 -l 88 .
	poetry run ruff check --select I --fix .

PYTHON_FILES=.
lint: PYTHON_FILES=.
lint_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$')

lint lint_diff:
	poetry run black --target-version py39 -l 88 $(PYTHON_FILES) --check
	poetry run ruff check .
	poetry run mypy $(PYTHON_FILES)
