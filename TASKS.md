# TASKS.md

## Current Phase
Phase 2: Medical archive content layer with Synthea-style import

## Goal
Add the medical archive content layer using Synthea-style imported records.

## Required deliverables
- Add database models and migrations for:
- encounters
- conditions
- medications
- observations
- allergies (optional if time allows)
- procedures (optional if time allows)
- Implement a Synthea CSV import script:
- `backend/scripts/import_synthea_csv.py`
- support importing at least:
- `patients.csv`
- `encounters.csv`
- `conditions.csv`
- `medications.csv`
- `observations.csv`
- map imported records into our own database schema
- support idempotent import behavior to avoid duplicate records on repeated runs
- provide basic logging / summary output after import
- Implement backend read APIs for medical archive content:
- `GET /patients/{patient_id}/encounters`
- `GET /patients/{patient_id}/conditions`
- `GET /patients/{patient_id}/medications`
- `GET /patients/{patient_id}/observations`
- Enforce authorization rules for imported archive data
- Update `README.md` with import and verification instructions

## Constraints
- do not implement ML yet
- do not implement daily home monitoring records yet
- do not refactor unrelated authentication code unless necessary
- keep code modular

## Acceptance checks
- alembic upgrade head runs successfully
- import script runs successfully on sample Synthea CSV files
- repeated import does not create uncontrolled duplicates
- imported patient archive data can be queried through API
- unauthorized doctor access returns 403
- README includes import instructions
