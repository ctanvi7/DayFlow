# Dayflow HRMS

## Member 4 slice

This repository contains the shared Flask/SQLAlchemy foundation, salary structure calculations, migration dependencies, demo seed entrypoint, and shared CSS tokens.

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Create MySQL database `dayflow_hrms`, then update `DATABASE_URL` and `SECRET_KEY` in `.env`. Run migrations with `flask --app run.py db upgrade` after migrations are generated. For the current empty scaffold, `db.create_all()` may be used only for local smoke testing.

Set `DEMO_ADMIN_PASSWORD` in the environment and run `python scripts/seed_demo.py`. Start Flask with `python run.py`; verify `GET /api/health` returns `{"status":"ok"}`. Run tests with `python -m pytest`.
