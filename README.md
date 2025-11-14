# ESPN Fantasy Football Weekly Pot Calculator

Calculate weekly high scores and track payouts for your ESPN Fantasy Football league's weekly pot.

This project is the Python approach to the former [espn-fantasy](https://github.com/ryantuck/espn-fantasy) project that used Make and HTML scraping. This version uses the ESPN API directly via Python, providing a more reliable and maintainable solution for tracking weekly high scores and calculating pot payouts. As league commissioner, this tool automates fetching scores from ESPN's Fantasy Football API and identifies weekly winners, making it easy to calculate and distribute payouts.

**Features:**
- ✅ Fetches weekly scores directly from ESPN's API
- ✅ Shows owner names (first + last) in weekly high score summary
- ✅ Outputs CSV with owner, score, week, and ranking
- ✅ Tracks weekly high score winners for pot payouts
- ✅ Uses environment variables for secure authentication

## Quick Start

### Install Dependencies

```sh
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
just install
```

### Create Configuration File

Create a `config.yaml` file in the project root directory with your league configuration:

```yaml
league_id: 123456
season_id: 2025

weekly_pot:
  payout: 10
  participants:
    - John Doe
    - Jane Smith
    - Bob Johnson
    - Alice Williams
    - Charlie Brown
```

**Finding your League ID and Season ID:**

1. **League ID**: Found in your ESPN Fantasy Football league URL
   - Go to your league page: `https://fantasy.espn.com/football/league?leagueId=123456`
   - The number after `leagueId=` is your league ID (e.g., `123456`)

2. **Season ID**: The year of the season (e.g., `2025` for the 2025 season)

3. **Weekly Pot Payout**: The dollar amount for each week's pot (e.g., `10` for $10), nested under `weekly_pot.payout`

4. **Participants**: List of names (first and last) of people who bought into the weekly pot, nested under `weekly_pot.participants`

**Note:** This file is gitignored and won't be committed to the repository, so you can safely store your league-specific configuration here.

### Authentication (for private leagues)

For private leagues, you need to set `ESPN_S2` and `SWID` environment variables. See [Authentication](#authentication-for-private-leagues) section below for detailed instructions on how to find these values.

```sh
export ESPN_S2='your_espn_s2_value'
export SWID='your_swid_value'
```

For persistent setup, add to your `~/.zshrc` or `~/.bashrc`:
```sh
export ESPN_S2='your_value_here'
export SWID='your_value_here'
```

## Usage

### List All Scores

List all team scores for a range of weeks in a human-friendly format:

```sh
just list-scores              # Weeks 1-18 (default)
just list-scores 1 10         # Weeks 1-10
just list-scores 1 18 csv     # Also write CSV file
```

### List Weekly High Scores

List only the highest scoring team owner for each week:

```sh
just list-high-scores              # Weeks 1-18 (default)
just list-high-scores 1 10         # Weeks 1-10
just list-high-scores 1 18 csv     # Also write CSV file
just list-high-scores 1 18 csv include-all  # Include all league members
```

### List Payout Totals

Calculate and display total payouts for each person based on weekly wins:

```sh
just list-payouts              # Weeks 1-18 (default)
just list-payouts 1 10         # Weeks 1-10
just list-payouts 1 18 csv     # Also write CSV file
just list-payouts 1 18 csv include-all  # Include all league members
```

## Authentication (for private leagues)

According to the [espn-api wiki](https://github.com/cwendt94/espn-api/wiki), you need two cookies: `espn_s2` and `swid`.

1. **Log into ESPN Fantasy Football:**
   - Go to https://fantasy.espn.com/football
   - Make sure you're logged into your account

2. **Open Developer Tools:**
   - **Chrome/Edge:** Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - **Firefox:** Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)

3. **Navigate to Cookies:**
   - **Chrome/Edge:** Go to the `Application` tab → `Cookies` → `https://fantasy.espn.com`
   - **Firefox:** Go to the `Storage` tab → `Cookies` → `https://fantasy.espn.com`

4. **Find and Copy Cookie Values:**
   - Look for the `espn_s2` cookie (it's a long string)
   - Look for the `SWID` cookie (usually in format `{12345678-1234-1234-1234-123456789ABC}`)
   - Copy the **Value** (not the name) of each cookie

5. **Set Environment Variables:**
   ```sh
   export ESPN_S2='YOUR_ESPN_S2_VALUE_HERE'
   export SWID='YOUR_SWID_VALUE_HERE'
   ```
   
   **For persistent setup**, add to your `~/.zshrc` or `~/.bashrc`:
   ```sh
   export ESPN_S2='your_value_here'
   export SWID='your_value_here'
   ```

**Cookie Expiration:**
- **SWID**: Typically persistent (can last months or until you clear browser cookies)
- **espn_s2**: Session-based token that may expire after periods of inactivity, logging out, or ESPN policy changes
- If you get authentication errors, refresh both cookies by logging back into ESPN and extracting new values

## Dev

Development commands for code quality:

```sh
just fmt               # Format code
just lint              # Lint code
just typecheck         # Type check code
just check             # Run all checks (fmt, lint, typecheck)
just ci                # Run CI checks (same as check)
```

This project uses:
- **uv** for dependency management and virtual environments
- **just** for running common tasks
- **ruff** for linting and formatting
- **mypy** for type checking
