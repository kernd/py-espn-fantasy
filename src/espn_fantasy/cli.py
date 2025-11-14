"""Command-line interface for ESPN Fantasy Football weekly pot calculator."""

import typer

from espn_fantasy.scores import (
    calculate_payouts,
    fetch_all_weeks,
    filter_participants,
    load_config,
    load_credentials,
    output_all_scores_human,
    output_high_scores_human,
    output_payouts_human,
    validate_participants,
    write_csv_to_file,
    write_high_scores_csv,
    write_payouts_csv,
)

app = typer.Typer()


def get_config():
    """Load and validate config."""
    config = load_config()
    if not config:
        typer.echo(
            "Error: Configuration file 'config.yaml' not found.",
            err=True,
        )
        typer.echo(
            "\nPlease create this file with your league configuration. See README.md for details.",
            err=True,
        )
        raise typer.Exit(1)
    return config


@app.command()
def list_scores(
    start_week: int = typer.Option(1, "--start-week", "-s", help="First week to fetch"),
    end_week: int = typer.Option(18, "--end-week", "-e", help="Last week to fetch"),
    csv: bool = typer.Option(False, "--csv", help="Additionally write results to a CSV file"),
    safe: bool = typer.Option(
        False, "--safe", help="Only show first letter of last name in output"
    ),
):
    """List all scores for teams in your league for a range of weeks."""
    config = get_config()
    espn_s2, swid = load_credentials()

    results = fetch_all_weeks(
        config.league_id, config.season_id, start_week, end_week, espn_s2, swid
    )

    if not results:
        typer.echo("Error: Failed to fetch any data", err=True)
        raise typer.Exit(1)

    if not results:
        typer.echo("No played weeks found in the specified range.", err=True)
        raise typer.Exit(1)

    output_all_scores_human(results, safe=safe)

    if csv:
        filename = f"scores_weeks_{start_week}_{end_week}.csv"
        write_csv_to_file(results, filename, safe=safe)
        typer.echo(f"\nCSV file written to: {filename}", err=True)


@app.command()
def list_high_scores(
    start_week: int = typer.Option(1, "--start-week", "-s", help="First week to fetch"),
    end_week: int = typer.Option(18, "--end-week", "-e", help="Last week to fetch"),
    csv: bool = typer.Option(False, "--csv", help="Additionally write results to a CSV file"),
    include_all: bool = typer.Option(
        False,
        "--include-all",
        help="Include all league members, not just weekly pot participants",
    ),
    safe: bool = typer.Option(
        False, "--safe", help="Only show first letter of last name in output"
    ),
):
    """List the highest scoring team owner for each week in a range."""
    config = get_config()
    espn_s2, swid = load_credentials()

    # Validate participants before fetching data
    if not include_all:
        if not validate_participants(config, config.league_id, config.season_id, espn_s2, swid):
            raise typer.Exit(1)

    results = fetch_all_weeks(
        config.league_id, config.season_id, start_week, end_week, espn_s2, swid
    )

    if not results:
        typer.echo("Error: Failed to fetch any data", err=True)
        raise typer.Exit(1)

    if not results:
        typer.echo("No played weeks found in the specified range.", err=True)
        raise typer.Exit(1)

    if not include_all:
        results = filter_participants(results, config.weekly_pot.participants)

    output_high_scores_human(results, safe=safe)

    if csv:
        filename = f"high_scores_weeks_{start_week}_{end_week}.csv"
        write_high_scores_csv(results, filename, safe=safe)
        typer.echo(f"\nCSV file written to: {filename}", err=True)


@app.command()
def list_payouts(
    start_week: int = typer.Option(1, "--start-week", "-s", help="First week to fetch"),
    end_week: int = typer.Option(18, "--end-week", "-e", help="Last week to fetch"),
    csv: bool = typer.Option(False, "--csv", help="Additionally write results to a CSV file"),
    include_all: bool = typer.Option(
        False,
        "--include-all",
        help="Include all league members, not just weekly pot participants",
    ),
    safe: bool = typer.Option(
        False, "--safe", help="Only show first letter of last name in output"
    ),
):
    """Calculate total payouts for each person based on weekly wins."""
    config = get_config()
    espn_s2, swid = load_credentials()

    # Validate participants before fetching data
    if not include_all:
        if not validate_participants(config, config.league_id, config.season_id, espn_s2, swid):
            raise typer.Exit(1)

    results = fetch_all_weeks(
        config.league_id, config.season_id, start_week, end_week, espn_s2, swid
    )

    if not results:
        typer.echo("Error: Failed to fetch any data", err=True)
        raise typer.Exit(1)

    if not results:
        typer.echo("No played weeks found in the specified range.", err=True)
        raise typer.Exit(1)

    if not include_all:
        results = filter_participants(results, config.weekly_pot.participants)

    payout_amount = config.weekly_pot.payout
    payouts = calculate_payouts(results, payout_amount)

    output_payouts_human(payouts, payout_amount, safe=safe)

    if csv:
        filename = f"payouts_weeks_{start_week}_{end_week}.csv"
        write_payouts_csv(payouts, filename, payout_amount, safe=safe)
        typer.echo(f"\nCSV file written to: {filename}", err=True)


def list_scores_cmd():
    """CLI entry point for list-scores command."""
    typer.run(list_scores)


def list_high_scores_cmd():
    """CLI entry point for list-high-scores command."""
    typer.run(list_high_scores)


def list_payouts_cmd():
    """CLI entry point for list-payouts command."""
    typer.run(list_payouts)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
