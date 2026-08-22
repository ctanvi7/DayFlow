# Database Runbook

Run these commands from the `DayFlow` directory in PowerShell.

## Sync and apply migrations

```powershell
git status --short
git stash push --include-untracked -m "attendance database work"
git pull --rebase origin main
git stash pop
python -m flask --app run.py db upgrade
python -m pytest -q
```

If `git stash pop` reports a conflict, resolve it, run `git add <resolved-files>`, and rerun the tests before applying the migration. Never use `git reset --hard` to resolve a stash conflict.

## Create the local MySQL database

```sql
CREATE DATABASE IF NOT EXISTS dayflow_hrms
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'dayflow_app'@'localhost' IDENTIFIED BY 'DayflowLocal_2026!';
GRANT ALL PRIVILEGES ON dayflow_hrms.* TO 'dayflow_app'@'localhost';
FLUSH PRIVILEGES;
```

Set `DATABASE_URL=mysql+pymysql://dayflow_app:DayflowLocal_2026!@localhost/dayflow_hrms` in `.env`, then run `python -m flask --app run.py db upgrade`.

## Reset data without dropping schema

Run `scripts/reset_local.sql` against `dayflow_hrms`:

```powershell
mysql -u dayflow_app -p dayflow_hrms < scripts/reset_local.sql
```

This deletes local rows only. It does not drop tables, indexes, migrations, or the database.

## Seed demo data

Set a local password before running the idempotent seed:

```powershell
$env:DEMO_ADMIN_PASSWORD = 'DayflowAdmin_2026!'
$env:DEMO_HR_PASSWORD = 'DayflowHr_2026!'
python scripts/seed_demo.py
```