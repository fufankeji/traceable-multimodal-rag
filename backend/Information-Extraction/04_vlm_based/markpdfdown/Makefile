.PHONY: install format lint test check update

install:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff check .

fix:
	uv run ruff check . --fix

test:
	uv run pytest

check:
	uv run pre-commit run --all-files

update:
	uv lock --upgrade
	uv run pre-commit autoupdate
