"""Command-line interface for ESPN Fantasy Football weekly pot calculator."""

import argparse
import sys

from espn_fantasy.scores import (
    calculate_payouts,
    fetch_all_weeks,
    load_config,
    load_credentials,
    output_all_scores_human,
    output_high_scores_human,
    output_payouts_human,
    write_csv_to_file,
    write_high_scores_csv,
    write_payouts_csv,
    filter_participants,
)


def parse_args(command_name, description):
    """Parse command-line arguments."""
    # Load config - league_id and season_id must come from config
    config = load_config()
    
    if not config:
        print(
            "Error: Configuration file 'config.yaml' not found.",
            file=sys.stderr,
        )
        print(
            "\nPlease create this file with your league configuration. See README.md for details.",
            file=sys.stderr,
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(
        prog=command_name,
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "start_week",
        nargs="?",
        type=int,
        default=1,
        help="First week to fetch (default: 1)",
    )
    parser.add_argument(
        "end_week",
        nargs="?",
        type=int,
        default=18,
        help="Last week to fetch (default: 18)",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Additionally write results to a CSV file",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all league members, not just weekly pot participants (applies to list-high-scores and list-payouts)",
    )

    args = parser.parse_args()
    
    # Add league_id and season_id from config to args
    args.league_id = config.league_id
    args.season_id = config.season_id
    args.config = config  # Pass full config for participant filtering

    return args


def list_scores_main():
    """Main CLI entry point for listing all scores."""
    args = parse_args(
        "list-scores",
        "List all scores for teams in your league for a range of weeks.",
    )

    # Load credentials from environment variables
    espn_s2, swid = load_credentials()

    # Fetch all weeks
    results = fetch_all_weeks(
        args.league_id, args.season_id, args.start_week, args.end_week, espn_s2, swid
    )

    if not results:
        print("Error: Failed to fetch any data", file=sys.stderr)
        sys.exit(1)

    # Output human-friendly format to stdout
    output_all_scores_human(results)

    # Optionally write CSV file
    if args.csv:
        filename = f"scores_weeks_{args.start_week}_{args.end_week}.csv"
        write_csv_to_file(results, filename)
        print(f"\nCSV file written to: {filename}", file=sys.stderr)


def list_high_scores_main():
    """Main CLI entry point for listing weekly high scores."""
    args = parse_args(
        "list-high-scores",
        "List the highest scoring team owner for each week in a range.",
    )

    # Load credentials from environment variables
    espn_s2, swid = load_credentials()

    # Fetch all weeks
    results = fetch_all_weeks(
        args.league_id, args.season_id, args.start_week, args.end_week, espn_s2, swid
    )

    if not results:
        print("Error: Failed to fetch any data", file=sys.stderr)
        sys.exit(1)

    # Filter to only show weekly pot participants (unless --include-all is set)
    if not args.include_all:
        results = filter_participants(results, args.config.weekly_pot.participants)

    # Output human-friendly format to stdout
    output_high_scores_human(results)

    # Optionally write CSV file (results already filtered)
    if args.csv:
        filename = f"high_scores_weeks_{args.start_week}_{args.end_week}.csv"
        write_high_scores_csv(results, filename)
        print(f"\nCSV file written to: {filename}", file=sys.stderr)


def list_payouts_main():
    """Main CLI entry point for listing payout totals."""
    args = parse_args(
        "list-payouts",
        "Calculate total payouts for each person based on weekly wins.",
    )

    # Load credentials from environment variables
    espn_s2, swid = load_credentials()

    # Fetch all weeks
    results = fetch_all_weeks(
        args.league_id, args.season_id, args.start_week, args.end_week, espn_s2, swid
    )

    if not results:
        print("Error: Failed to fetch any data", file=sys.stderr)
        sys.exit(1)

    # Filter to only show weekly pot participants (unless --include-all is set)
    if not args.include_all:
        results = filter_participants(results, args.config.weekly_pot.participants)

    # Calculate payouts
    payout_amount = args.config.weekly_pot.payout
    payouts = calculate_payouts(results, payout_amount)

    # Output human-friendly format to stdout
    output_payouts_human(payouts, payout_amount)

    # Optionally write CSV file
    if args.csv:
        filename = f"payouts_weeks_{args.start_week}_{args.end_week}.csv"
        write_payouts_csv(payouts, filename, payout_amount)
        print(f"\nCSV file written to: {filename}", file=sys.stderr)


if __name__ == "__main__":
    # For backward compatibility, default to list-scores
    if len(sys.argv) > 1 and sys.argv[1] in ["list-scores", "list-high-scores", "list-payouts"]:
        command = sys.argv.pop(1)
        if command == "list-scores":
            list_scores_main()
        elif command == "list-high-scores":
            list_high_scores_main()
        else:
            list_payouts_main()
    else:
        list_scores_main()
