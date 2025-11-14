"""ESPN Fantasy Football score fetching functionality."""

import os
import sys
from pathlib import Path

import yaml
from espn_api.football import League
from pydantic import BaseModel, Field, ValidationError


class WeeklyPotConfig(BaseModel):
    """Configuration for weekly pot."""

    payout: float = Field(..., description="Weekly pot payout amount in dollars")
    participants: list[str] = Field(..., description="List of participant names (first and last)")

    def model_post_init(self, __context):
        """Normalize participant names to lowercase and strip whitespace."""
        self.participants = [name.strip().lower() for name in self.participants]


class Config(BaseModel):
    """Main configuration model."""

    league_id: int = Field(..., description="ESPN Fantasy Football league ID")
    season_id: int = Field(..., description="Season year (e.g., 2025)")
    weekly_pot: WeeklyPotConfig = Field(..., description="Weekly pot configuration")


def load_config():
    """Load and validate configuration from config.yaml file."""
    config_file = Path("config.yaml")
    if not config_file.exists():
        return None

    try:
        with open(config_file) as f:
            config_data = yaml.safe_load(f)
        config = Config.model_validate(config_data)
        return config
    except ValidationError as e:
        print(f"Error: Invalid configuration file: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Warning: Could not load config file: {e}", file=sys.stderr)
        return None


def load_credentials():
    """Load credentials from environment variables."""
    espn_s2 = os.getenv("ESPN_S2")
    swid = os.getenv("SWID")

    # Remove curly braces from SWID if present
    if swid and swid.startswith("{") and swid.endswith("}"):
        swid = swid[1:-1]

    return espn_s2, swid


def fetch_week_scores(league, week):
    """Fetch scores for a specific week using the ESPN API"""
    try:
        # Get matchups for the week
        matchups = league.scoreboard(week=week)

        # Extract team names, scores, and owners
        results = []
        for matchup in matchups:
            home_team = matchup.home_team
            away_team = matchup.away_team

            # Check if matchup has been played
            # Try different attributes that might indicate completion
            matchup_played = False
            if hasattr(matchup, "complete"):
                matchup_played = matchup.complete
            elif hasattr(matchup, "winner"):
                # If winner is set, the matchup has been played
                matchup_played = matchup.winner is not None
            elif hasattr(matchup, "played"):
                matchup_played = matchup.played
            else:
                # Fallback: check if scores are non-zero
                home_score_check = (
                    home_team.scores[week - 1] if week <= len(home_team.scores) else 0
                )
                away_score_check = (
                    away_team.scores[week - 1] if week <= len(away_team.scores) else 0
                )
                matchup_played = home_score_check > 0 or away_score_check > 0

            if not matchup_played:
                continue

            # Get score for this week
            home_score = home_team.scores[week - 1] if week <= len(home_team.scores) else 0
            away_score = away_team.scores[week - 1] if week <= len(away_team.scores) else 0

            # Get owner name from owners list (first owner if multiple)
            # Store both displayName (for CSV) and full name (for summary)
            home_owner_display = (
                home_team.owners[0]["displayName"]
                if home_team.owners and len(home_team.owners) > 0
                else home_team.team_name
            )
            home_owner_full = (
                (
                    f"{home_team.owners[0]['firstName'].strip()} "
                    f"{home_team.owners[0]['lastName'].strip()}"
                ).strip()
                if home_team.owners
                and len(home_team.owners) > 0
                and "firstName" in home_team.owners[0]
                and "lastName" in home_team.owners[0]
                else home_owner_display
            )
            away_owner_display = (
                away_team.owners[0]["displayName"]
                if away_team.owners and len(away_team.owners) > 0
                else away_team.team_name
            )
            away_owner_full = (
                (
                    f"{away_team.owners[0]['firstName'].strip()} "
                    f"{away_team.owners[0]['lastName'].strip()}"
                ).strip()
                if away_team.owners
                and len(away_team.owners) > 0
                and "firstName" in away_team.owners[0]
                and "lastName" in away_team.owners[0]
                else away_owner_display
            )

            results.append(
                {
                    "team": home_team.team_name,
                    "score": home_score,
                    "week": week,
                    "owner": home_owner_display,
                    "owner_full": home_owner_full,
                }
            )
            results.append(
                {
                    "team": away_team.team_name,
                    "score": away_score,
                    "week": week,
                    "owner": away_owner_display,
                    "owner_full": away_owner_full,
                }
            )

        return results

    except Exception as e:
        print(f"Error fetching week {week}: {e}", file=sys.stderr)
        return None


def get_league_owners(league_id, season_id, espn_s2=None, swid=None):
    """Get all team owners from the league for validation."""
    try:
        # Initialize league
        if espn_s2 and swid:
            league = League(league_id=league_id, year=season_id, espn_s2=espn_s2, swid=swid)
        else:
            league = League(league_id=league_id, year=season_id)

        # Get all teams and extract owner names
        owners = set()
        for team in league.teams:
            if team.owners and len(team.owners) > 0:
                # Get full name (first + last)
                if "firstName" in team.owners[0] and "lastName" in team.owners[0]:
                    full_name = (
                        (
                            f"{team.owners[0]['firstName'].strip()} "
                            f"{team.owners[0]['lastName'].strip()}"
                        )
                        .strip()
                        .lower()
                    )
                    owners.add(full_name)
                # Also add display name
                if "displayName" in team.owners[0]:
                    owners.add(team.owners[0]["displayName"].strip().lower())

        return owners
    except Exception as e:
        print(f"Error getting league owners: {e}", file=sys.stderr)
        return None


def validate_participants(config, league_id, season_id, espn_s2=None, swid=None):
    """Validate that all participants in config exist as team owners in the league."""
    owners = get_league_owners(league_id, season_id, espn_s2, swid)
    if owners is None:
        print(
            "Warning: Could not validate participants against league owners.",
            file=sys.stderr,
        )
        return True  # Don't block if we can't validate

    participants = set(config.weekly_pot.participants)
    missing = participants - owners

    if missing:
        print(
            "Error: The following participants are not found as team owners in the league:",
            file=sys.stderr,
        )
        for name in sorted(missing):
            print(f"  - {name}", file=sys.stderr)
        print(
            "\nPlease check your config.yaml file and ensure participant names match "
            "team owner names (first and last name).",
            file=sys.stderr,
        )
        return False

    return True


def fetch_all_weeks(league_id, season_id, start_week=1, end_week=18, espn_s2=None, swid=None):
    """Fetch scores for multiple weeks"""
    try:
        # Initialize league
        if espn_s2 and swid:
            league = League(league_id=league_id, year=season_id, espn_s2=espn_s2, swid=swid)
        else:
            # Try without authentication (works for public leagues)
            print(
                "No cookies provided. Attempting to access as public league...",
                file=sys.stderr,
            )
            league = League(league_id=league_id, year=season_id)

        all_results = []

        for week in range(start_week, end_week + 1):
            print(f"Fetching week {week}...", file=sys.stderr)
            results = fetch_week_scores(league, week)
            if results:
                all_results.extend(results)
            else:
                print(f"Warning: Failed to fetch week {week}", file=sys.stderr)

        return all_results

    except Exception as e:
        print(f"Error initializing league: {e}", file=sys.stderr)
        if "authentication" in str(e).lower() or "private" in str(e).lower():
            print(
                "\nThis appears to be a private league. You need to provide credentials.",
                file=sys.stderr,
            )
            print(
                "Set ESPN_S2 and SWID environment variables.",
                file=sys.stderr,
            )
        return None


def write_csv_to_file(results, filename, safe=False):
    """Write results as CSV to a file"""
    with open(filename, "w") as f:
        f.write("owner,score,week,index\n")

        # Group by week and add index
        week_data = {}
        for result in results:
            week = result["week"]
            if week not in week_data:
                week_data[week] = []
            week_data[week].append(result)

        # Sort by week, then by score (descending)
        for week in sorted(week_data.keys()):
            week_results = sorted(week_data[week], key=lambda x: x["score"], reverse=True)
            for idx, result in enumerate(week_results, 1):
                # Use full name (first + last) for CSV, fallback to display name, then team name
                owner = result.get("owner_full", result.get("owner", result["team"]))
                owner = owner.lower()  # Normalize to lowercase
                owner = mask_name(owner, safe=safe)
                f.write(f"{owner},{result['score']},{week},{idx}\n")


def mask_name(name, safe=False):
    """Mask last name to show only first letter if safe mode is enabled."""
    if not safe:
        return name

    parts = name.split()
    if len(parts) >= 2:
        # Keep first name, show only first letter of last name
        first_name = parts[0]
        last_initial = parts[-1][0] if parts[-1] else ""
        return f"{first_name} {last_initial}."
    return name


def output_all_scores_human(results, safe=False):
    """Output all scores in a human-friendly format"""
    # Group by week
    week_data = {}
    for result in results:
        week = result["week"]
        if week not in week_data:
            week_data[week] = []
        week_data[week].append(result)

    # Sort by week, then by score (descending)
    for week in sorted(week_data.keys()):
        week_results = sorted(week_data[week], key=lambda x: x["score"], reverse=True)
        print(f"\n=== Week {week} ===")
        for idx, result in enumerate(week_results, 1):
            # Use full name (first + last) for display, fallback to display name, then team name
            owner = result.get("owner_full", result.get("owner", result["team"]))
            owner = owner.lower()  # Normalize to lowercase
            owner = mask_name(owner, safe=safe)
            score = result["score"]
            print(f"  {idx}. {owner}: {score:.1f} points")


def output_high_scores_human(results, safe=False):
    """Output summary of highest scoring team owner for each week in human-friendly format"""
    # Group by week
    week_data = {}
    for result in results:
        week = result["week"]
        if week not in week_data:
            week_data[week] = []
        week_data[week].append(result)

    # Find highest scorer for each week
    print("\n=== Weekly High Scores ===")
    for week in sorted(week_data.keys()):
        week_results = week_data[week]
        highest = max(week_results, key=lambda x: x["score"])
        # Use full name (first + last) for the summary, fallback to display name
        owner = highest.get("owner_full", highest.get("owner", highest["team"]))
        owner = owner.lower()  # Normalize to lowercase
        owner = mask_name(owner, safe=safe)
        print(f"Week {week}: {owner} - {highest['score']:.1f} points")


def filter_participants(results, participant_names):
    """Filter results to only include weekly pot participants."""
    # Participant names are already normalized to lowercase in the Pydantic model
    # Just strip whitespace for comparison
    normalized_participants = {name.strip() for name in participant_names}

    filtered = []
    for result in results:
        # Check both full name and display name
        owner_full = result.get("owner_full", "").strip().lower()
        owner_display = result.get("owner", "").strip().lower()

        # Match if either full name or display name exactly matches or contains a participant name
        # We check both directions: participant in owner name, and owner name in participant
        matches = False
        for participant in normalized_participants:
            # Exact match or participant name is contained in owner name
            if (
                participant == owner_full
                or participant == owner_display
                or participant in owner_full
                or participant in owner_display
            ):
                matches = True
                break

        if matches:
            filtered.append(result)

    return filtered


def write_high_scores_csv(results, filename, safe=False):
    """Write weekly high scores as CSV to a file"""
    # Group by week
    week_data = {}
    for result in results:
        week = result["week"]
        if week not in week_data:
            week_data[week] = []
        week_data[week].append(result)

    with open(filename, "w") as f:
        f.write("week,owner,score\n")
        for week in sorted(week_data.keys()):
            week_results = week_data[week]
            highest = max(week_results, key=lambda x: x["score"])
            owner = highest.get("owner_full", highest.get("owner", highest["team"]))
            owner = owner.lower()  # Normalize to lowercase
            owner = mask_name(owner, safe=safe)
            f.write(f"{week},{owner},{highest['score']:.1f}\n")


def calculate_payouts(results, payout_amount):
    """Calculate total payouts for each person based on weekly wins."""
    # Group by week
    week_data = {}
    for result in results:
        week = result["week"]
        if week not in week_data:
            week_data[week] = []
        week_data[week].append(result)

    # Track wins per person
    payouts = {}
    for week in sorted(week_data.keys()):
        week_results = week_data[week]
        highest = max(week_results, key=lambda x: x["score"])
        owner = highest.get("owner_full", highest.get("owner", highest["team"]))
        owner = owner.lower()  # Normalize to lowercase

        if owner not in payouts:
            payouts[owner] = {"wins": 0, "total": 0.0}
        payouts[owner]["wins"] += 1
        payouts[owner]["total"] += payout_amount

    return payouts


def output_payouts_human(payouts, payout_amount, safe=False):
    """Output payout summary in human-friendly format."""
    print(f"\n=== Payout Summary (${payout_amount:.2f} per win) ===")

    if not payouts:
        print("No winners found.")
        return

    # Sort by total payout (descending), then by name
    sorted_payouts = sorted(
        payouts.items(),
        key=lambda x: (x[1]["total"], x[0]),
        reverse=True,
    )

    for owner, data in sorted_payouts:
        wins = data["wins"]
        total = data["total"]
        owner_display = mask_name(owner, safe=safe)
        print(f"{owner_display}: {wins} win{'s' if wins != 1 else ''} = ${total:.2f}")


def write_payouts_csv(payouts, filename, payout_amount, safe=False):
    """Write payout summary as CSV to a file"""
    with open(filename, "w") as f:
        f.write("owner,wins,total_payout\n")
        # Sort by total payout (descending), then by name
        sorted_payouts = sorted(
            payouts.items(),
            key=lambda x: (x[1]["total"], x[0]),
            reverse=True,
        )
        for owner, data in sorted_payouts:
            owner_display = mask_name(owner, safe=safe)
            f.write(f"{owner_display},{data['wins']},{data['total']:.2f}\n")
