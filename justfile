# ESPN Fantasy Football Weekly Pot Calculator - Just Commands

# Install dependencies
install:
    uv sync

# List all scores for a range of weeks
# For private leagues, set ESPN_S2 and SWID environment variables first:
#   export ESPN_S2='your_value'
#   export SWID='your_value'
# League ID and season ID are read from config.yaml
# Examples:
#   just list-scores
#   just list-scores 1 10
#   just list-scores 1 18 csv
list-scores start_week="1" end_week="18" csv="":
    @if [ -n "{{csv}}" ]; then \
        uv run list-scores {{start_week}} {{end_week}} --csv; \
    else \
        uv run list-scores {{start_week}} {{end_week}}; \
    fi

# List weekly high scores for a range of weeks
# League ID and season ID are read from config.yaml
# Examples:
#   just list-high-scores
#   just list-high-scores 1 10
#   just list-high-scores 1 18 csv
list-high-scores start_week="1" end_week="18" csv="":
    @if [ -n "{{csv}}" ]; then \
        uv run list-high-scores {{start_week}} {{end_week}} --csv; \
    else \
        uv run list-high-scores {{start_week}} {{end_week}}; \
    fi

# List payout totals for a range of weeks
# League ID and season ID are read from config.yaml
# Examples:
#   just list-payouts
#   just list-payouts 1 10
#   just list-payouts 1 18 csv
#   just list-payouts 1 18 csv include-all
list-payouts start_week="1" end_week="18" csv="" include_all="":
    @if [ -n "{{include_all}}" ]; then \
        @if [ -n "{{csv}}" ]; then \
            uv run list-payouts {{start_week}} {{end_week}} --csv --include-all; \
        else \
            uv run list-payouts {{start_week}} {{end_week}} --include-all; \
        fi \
    else \
        @if [ -n "{{csv}}" ]; then \
            uv run list-payouts {{start_week}} {{end_week}} --csv; \
        else \
            uv run list-payouts {{start_week}} {{end_week}}; \
        fi \
    fi

# Format code
fmt:
    uv run ruff format .

# Lint code
lint:
    uv run ruff check .

# Type check
typecheck:
    uv run mypy src/espn_fantasy

# Run all checks
check:
    just fmt
    just lint
    just typecheck

# CI checks (what runs in CI)
ci:
    just check

