# ESPN Fantasy Football Weekly Pot Calculator - Just Commands

# Install dependencies
install:
    uv sync

# Format code
fmt:
    uv run --dev ruff format .

# Lint code
lint:
    uv run --dev ruff check .

# Type check
typing:
    uv run --dev python -m mypy src/espn_fantasy

# Alias for typing (backward compatibility)
typecheck:
    just typing

# Run all checks
check:
    just fmt
    just lint
    just typing

# CI checks (what runs in CI)
ci:
    just check

