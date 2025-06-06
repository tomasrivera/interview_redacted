.PHONY: format
format:
	uv run ruff check src
	uv run ruff format src --check

.PHONY: format!
format!:
	uv run ruff check src --fix
	uv run ruff format src

.PHONY: dev
dev:
	uv run fastapi dev src/main.py

.PHONY: test
test:
	uv run pytest src

.PHONY: typecheck
typecheck:
	uv run mypy src
