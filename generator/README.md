# Central F10 Schedule Generator

Downloads ICS calendars from Profixio and generates schedule data files for the web frontend.

## Quick Start

```bash
uv sync                  # Install dependencies
uv run app.py            # Run generator
```

## Output

Writes to `../data/`:
- `games.json` — Schedule data for the web app
- `games.tsv` — Tab-separated format for Excel/Sheets import
- `calendar.ics` — Calendar format for Google Calendar import

## Configuration

Edit `config.toml` to add or update team calendars. Each entry requires:
- `url` — Profixio ICS calendar URL (found in Profixio → Team → Calendar → Subscribe)
- `filename` — Local cache filename (must end with `.ics`)
- `team_name` — Full team name for display
- `team_slug` — URL-safe identifier (unique)
- `team_display` — Short name for UI badges
- `team_color` — Hex color for UI elements (e.g. `#550f38`)

## Commands

```bash
uv run pytest            # Run tests
uv run ruff check .      # Lint
uv run ruff format .     # Format
uv run ty check src/     # Type check
```