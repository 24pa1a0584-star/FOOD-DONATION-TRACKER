# Project analysis and Render deployment

## Assessment

This is one Flask application: Jinja HTML templates, Bootstrap and vanilla JavaScript,
Flask-Login authentication, Flask-WTF validation/CSRF, and SQLAlchemy models for users
and donations. It needs a Python **Web Service** and PostgreSQL, not a Static Site.
There is no Node build, separate frontend server, file-upload storage, or job queue.
Expiry is updated when routes are visited; no scheduled job is required for the current design.

Implemented flows include donor/receiver registration, posting, filtering, claiming,
delivery, cancellation, activity dashboards, and impact statistics. Passwords are
hashed; pickup address and phone are restricted to the donor and claiming receiver.
Claims use a conditional SQL UPDATE to prevent a second successful claim.

Deployment preparation added:

- Gunicorn and the psycopg PostgreSQL driver.
- PostgreSQL URL normalization, connection health checks, and `/healthz`.
- Strong-secret and PostgreSQL requirements when running on Render, secure HTTPS cookies.
- A Python version file and `render.yaml` Blueprint.
- Demo credentials hidden unless explicitly enabled; destructive demo seeding blocked on Render.
- Rejection of external login redirect targets and host-independent IST test data.

Remaining product limitations before a larger public launch:

- Receiver accounts are self-registered, not identity-verified, despite the README's wording.
- There is no email verification, password reset, login rate limiting, or moderation system.
- Logout is a GET request; change it to a CSRF-protected POST for further hardening.
- Cancellation reads then writes status, so a concurrent cancellation and claim can race.
  Convert cancellation to a conditional update before high-concurrency use.
- Forms interpret expiry as IST, while the browser default uses the browser's timezone.
  Users outside India can submit an unintended expiry time.
- Lists are unpaginated. Add pagination and suitable database indexes as data grows.
- `db.create_all()` creates missing tables at startup but does not migrate existing schemas.
  Introduce Alembic/Flask-Migrate before changing deployed model columns. Keep one worker
  for this initial deployment; plan schema initialization separately before scaling.
- Bootstrap/icons/fonts require external CDN access.

## 1. Put the correct folder on GitHub

Your actual application directory is:

```text
D:\FOOD TRACKER\food-donation-tracker-main\food-donation-tracker-main
```

This downloaded folder currently has no Git repository or remote configured.
Create an empty GitHub repository, then run the following from PowerShell,
replacing YOUR_USERNAME and YOUR_REPOSITORY:

```powershell
cd 'D:\FOOD TRACKER\food-donation-tracker-main\food-donation-tracker-main'
git init
git add .
git status
git commit -m "Prepare Flask app for Render"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Check `git status` before committing. `.env`, `instance/`, and `.venv/` are ignored.
Do not upload credentials, your local database, or the virtual environment manually.
At the GitHub repository root you should see `app.py`, `requirements.txt`,
`.python-version`, and `render.yaml` directly.

## 2. Recommended quick demo: Blueprint

1. Sign in at https://dashboard.render.com and connect your GitHub account.
2. Select **New > Blueprint**, choose the repository and branch, and use `render.yaml`.
3. Review the two resources: `food-donation-tracker` and `food-donation-db`, in Singapore.
4. The supplied YAML uses free plans. Review availability and any charges in Render
   before creating resources. If your workspace already has a free database, reuse it
   through the manual setup below or select a paid database.
5. Deploy the Blueprint. It generates `SECRET_KEY` and connects `DATABASE_URL` automatically.
6. Open the web service's assigned HTTPS `onrender.com` address after deployment succeeds.

Render automatically sets `RENDER=true`; the application uses this to enforce production
configuration. Tables are created at startup. New deployments start with empty data;
register your own donor and receiver accounts. Never run `python seed.py` in deployment:
it drops all tables and is now explicitly blocked on Render.

If you upload the OUTER folder instead, set the Blueprint path to
`food-donation-tracker-main/render.yaml` and add
`rootDir: food-donation-tracker-main` under the web service in the YAML.
The simplest layout is the application files directly at repository root.

## 3. Alternative: manual Dashboard setup

Use this instead of a Blueprint; do not create duplicate resources.

First select **New > Postgres**, choose Singapore, select the database plan, and copy
its **Internal Database URL**. Keep the web service and database in the same region.

Next select **New > Web Service**, connect the GitHub repository, and enter:

| Setting | Value |
| --- | --- |
| Language/runtime | Python 3 |
| Branch | main |
| Root Directory | Leave blank when `app.py` is at repository root |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --access-logfile - --error-logfile -` |
| Health Check Path | `/healthz` |
| Region | Singapore, matching the database |

If GitHub shows an extra folder before `app.py`, set Root Directory to that folder
(`food-donation-tracker-main` in this download). The included `.python-version` selects
Python 3.13; avoid overriding it with a conflicting `PYTHON_VERSION` setting.

Set these environment variables in Render:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Your database's Internal Database URL |
| `SECRET_KEY` | A generated random secret, at least 32 characters |
| `SHOW_DEMO_ACCOUNTS` | `false` |

Generate a secret locally, paste it into Render, and keep it private:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Do not set `FLASK_DEBUG=1`, use `flask run`, or run `python app.py` as the production command.

## 4. Validate after deployment

Local validation on 27 October 2026: `python -m pytest -q` passed all 19 tests
on Windows / Python 3.14.5. Four WTForms choice-format deprecation warnings remain.
The Render target is Python 3.13; that runtime and a live PostgreSQL server were not
available for local integration testing. No Render resources have been deployed.

1. Open `/healthz`; expect HTTP 200 and `{"status":"ok"}`.
2. Open `/`, `/register`, and `/login`; confirm CSS loads and no demo password is shown.
3. Register a donor and post a donation expiring several hours ahead in IST.
4. In another browser/private window, register a receiver. Check address privacy before
   claiming, claim once, and mark delivered. Verify dashboard and `/api/stats` totals.
5. Try claiming the same donation from another receiver; it should fail.
6. Redeploy and confirm accounts/donations remain in PostgreSQL.

The local pytest suite uses isolated SQLite databases. PostgreSQL configuration is
tested with database creation mocked; this does not replace a live PostgreSQL smoke test.
Gunicorn runs on Linux on Render and cannot be exercised natively on Windows.
`tests/test_e2e_live.py` is a manually run demo script, not a collected pytest test,
and expects seeded data; do not point it at production.

## 5. Hosting limits and operations

Free web services sleep after 15 idle minutes and can take about a minute to wake.
Their local files are lost on restart/redeploy, which is why this setup uses PostgreSQL.
Free Render PostgreSQL expires 30 days after creation and has no backups. It is suitable
only for a temporary demo. Upgrade the database before expiration to keep the app usable.
For ongoing community use, select a paid database with backups and an always-on paid
web service. Review current prices in the Dashboard; no paid resource has been created here.

The Blueprint restricts external database connections (`ipAllowList: []`); the web service
uses Render's internal connection. If you later need external access for maintenance,
allow only the required IP and use the external connection URL privately.

Changing from local SQLite to PostgreSQL does not copy existing data. This setup creates
a new empty database. Plan a separate export/import if local data must be preserved.
Before later schema changes, add migrations and take a backup. A code rollback alone
does not reverse database schema changes.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `requirements.txt` / `app` not found | Root Directory and repository folder layout |
| `gunicorn` or `psycopg` missing | Updated requirements were committed and the build completed |
| `SECRET_KEY` startup error | Set a generated secret of at least 32 characters |
| `DATABASE_URL` startup error | Use the Postgres URL, not a SQLite URL |
| Database connection error / health 503 | Database is running, not expired, and internal URL/region match |
| New model column missing | Apply a migration; `create_all()` does not alter tables |
| Slow first request | Free web service may be waking from idle |
| Demo credentials do not work | They are intentionally not created on Render; register new accounts |

Official references:
- https://render.com/docs/deploy-flask
- https://render.com/docs/blueprint-spec
- https://render.com/docs/python-version
- https://render.com/docs/free
