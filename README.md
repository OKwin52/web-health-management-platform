# Phase 2 Backend

This repository currently implements **Phase 1 and Phase 2 backend work** for the personal health management system.

Implemented scope:

- FastAPI backend
- SQLAlchemy models for users, patients, doctors, doctor authorization, and medical archive records
- JWT login
- role-based access control
- Alembic migration setup
- demo seed script
- Synthea-style CSV import for medical archive content
- archive read APIs for encounters, conditions, medications, and observations

Not implemented yet:

- daily health monitoring
- reports
- prediction or warning modules
- frontend feature work beyond API availability

## Project Structure

```text
backend/
  api/
  core/
  models/
  schemas/
  scripts/
alembic/
requirements.txt
```

## Environment

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables as needed. Defaults are already suitable for local SQLite usage.

PowerShell example:

```powershell
$env:DATABASE_URL = "sqlite:///./health_management.db"
$env:JWT_SECRET_KEY = "dev-secret"
```

Optional variables are listed in `.env.example`.

## Run Instructions

1. Run the database migration:

```bash
alembic upgrade head
```

2. Seed demo users:

```bash
python -m backend.scripts.seed_demo
```

3. Start the backend:

```bash
uvicorn backend.main:app --reload
```

4. Import Synthea CSV files after placing them in a directory such as `data/synthea/`.

Expected files:

- `patients.csv`
- `encounters.csv`
- `conditions.csv`
- `medications.csv`
- `observations.csv`

Import command:

```bash
python -m backend.scripts.import_synthea_csv data/synthea
```

The importer is designed to be idempotent. Re-running the same import updates matching records instead of creating uncontrolled duplicates.

5. Verify health check:

```text
GET http://127.0.0.1:8000/health
```

## Demo Accounts

- `admin` / `admin123`
- `alice` / `alice123`
- `bob` / `bob123`
- `drsmith` / `doctor123`

The seed script creates one active authorization from patient `alice` to doctor `drsmith`. `bob` remains unauthorized, which is useful for access-control checks.

## Key API Endpoints

- `POST /auth/login`
- `GET /auth/me`
- `GET /health`
- `GET /doctors`
- `GET /patients`
- `POST /patients`
- `GET /patients/{patient_id}`
- `PUT /patients/{patient_id}`
- `DELETE /patients/{patient_id}`
- `GET /patients/{patient_id}/encounters`
- `GET /patients/{patient_id}/conditions`
- `GET /patients/{patient_id}/medications`
- `GET /patients/{patient_id}/observations`
- `GET /authorizations`
- `POST /authorizations`
- `DELETE /authorizations/{authorization_id}`

## Example Login Request

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## Acceptance Check Hints

- backend starts: `uvicorn backend.main:app --reload`
- migration succeeds: `alembic upgrade head`
- login works: call `POST /auth/login`
- patient CRUD works: use `admin` token on `/patients`
- import Synthea CSV files: `python -m backend.scripts.import_synthea_csv data/synthea`
- query imported records: call `/patients/{patient_id}/encounters` and related archive endpoints
- unauthorized doctor blocked: login as `drsmith`, then request archive endpoints for an unauthorized patient
