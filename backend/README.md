# Backend (ClimbBot) — README

This folder contains the backend helper script and API server for ClimbBot.

Contents
- `api_server.py` — FastAPI server that exposes endpoints the frontend uses (e.g. `/api/training`, `/api/workouts`, `/analyze`).
- `No_Langchain.py` — Claude/Anthropic-based orchestration and helper functions used by the backend.

Quick setup
1. Create and activate a Python virtual environment (bash):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies (from project root):

```bash
pip install --upgrade pip setuptools wheel
pip install -r ../exported_requirements.txt
```

Environment variables
The backend requires several environment variables. Copy the repo's `.env` template or create your own and set these at minimum:

- `DATABASE_URL` — connection string for the app (pooler) used at runtime
- `DIRECT_URL` — direct connection used for migrations
- `ANTHROPIC_API_KEY` — your Anthropic API key for Claude calls
- `CLAUDE_MODEL` — (optional) Claude model to use (defaults to `claude-sonnet-4-5`)
- `KAGGLE_GYM_PATH` — path to gym exercise CSV (default `data/gym_data.csv`)
- `KAGGLE_CLIMB_PATH` — path to climb CSV (default `data/climb_data.csv`)
- `GOOGLE_SHEETS_URL` — optional CSV export URL for sheet data

Security: do NOT commit `.env` with secrets to version control.

Running locally
Start the backend API server (inside the activated venv):

```bash
python api_server.py
# or
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

The server listens by default on port 8000 (configured in `api_server.py`). The frontend expects the SvelteKit dev server on port 5173 and may call the backend on `http://localhost:8000` or `http://localhost:5173` depending on your setup — confirm `api_base_url` when instantiating `ClimbingCoachSystem`.

Troubleshooting
- If you see a Prisma / database connection error, check `DATABASE_URL` and network access to the DB.
- If Anthropics / Claude calls fail, make sure `ANTHROPIC_API_KEY` is set and `CLAUDE_MODEL` is a valid model name.
- To export your current environment packages for reproducibility:

```bash
pip freeze > requirements.txt
```

Contact
If you want, I can add a simple script to validate environment variables at startup or add more examples for invoking the tools.
