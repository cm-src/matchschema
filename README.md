# Central F10/F11 – Matchschema

**Live site:** https://basket.mtln.se/

Matchschema för Central F10/F11, automatiskt uppdaterat från Profixio.

## Project Structure

This repository has a clear separation between frontend and generator:

- **Root (`/`)** — Static frontend (HTML/CSS/JS) served by GitHub Pages
- **`generator/`** — Python tooling that fetches schedules and generates data files
- **`data/`** — Generated JSON/TSV/ICS files (committed by GitHub Actions)

The generator runs on a schedule (06:00 and 18:00 CET / 05:00 and 17:00 UTC) and on pushes to `generator/`.

## Features

- Dynamiskt schema — Uppdateras automatiskt dagligen
- Team-filter — Välj mellan Alla eller lag
- Datum-filter — Visa kommande eller alla matcher
- Sök — Sök på lag, motståndare eller hall
- Nedladdning — TSV för Excel/Sheets, ICS för kalender
- Mörkt/ljust läge — Växla tema
- PWA — Installera som app

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

## Links

- **YouTube Streams:** https://www.youtube.com/@CentralBasketF10-t2w/streams
- **Profixio:** https://www.profixio.com

## License

© 2026 C. Mathlin
