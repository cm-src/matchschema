# Central F10/F11 – Game Schedule

**Live site:** https://basket.mtln.se/

Basketball game schedule for Central F10/F11 teams, automatically synced from Profixio.

## Project Structure

This repository separates the static frontend from the Python data generator:

- **`/`** — Static frontend (HTML/CSS/JS) served by GitHub Pages
- **`generator/`** — Python tool that fetches ICS feeds and outputs JSON/TSV/ICS
- **`data/`** — Generated schedule files (committed by GitHub Actions)

The generator runs twice daily (06:00 and 18:00 CET / 05:00 and 17:00 UTC) and on every push to `generator/`.

## Features

- **Auto-updating schedule** — Refreshed twice daily from Profixio
- **Team filter** — View all teams or filter by a specific team
- **Date filter** — Show upcoming games only, or all games
- **Search** — Find games by team, opponent, or venue
- **Downloads** — TSV for Excel/Sheets, ICS for calendar import
- **Dark/light mode** — Toggle between themes
- **PWA support** — Install as a standalone app

## Local Development

```bash
# Frontend (from repo root)
./serve.sh
# Open http://localhost:8000

# Generator (from generator/ directory)
cd generator
uv sync
uv run app.py
uv run pytest
```

## License

© 2026 C. Mathlin
