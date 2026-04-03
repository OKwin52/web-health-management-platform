from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select

from backend.core.security import hash_password
from backend.db import SessionLocal
from backend.models import Condition, Encounter, Medication, Observation, Patient, User, UserRole


SUPPORTED_FILES = {
    "patients": "patients.csv",
    "encounters": "encounters.csv",
    "conditions": "conditions.csv",
    "medications": "medications.csv",
    "observations": "observations.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Synthea CSV files into the local database.")
    parser.add_argument(
        "data_dir",
        nargs="?",
        default="data/synthea",
        help="Directory containing Synthea CSV files.",
    )
    return parser.parse_args()


def row_value(row: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return None


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    text = value.strip()
    if "T" in text:
        parsed = parse_datetime(text)
        return parsed.date() if parsed else None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def parse_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def parse_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def build_username(external_id: str) -> str:
    return f"synthea_{external_id.replace('-', '').lower()[:32]}"


def build_source_key(prefix: str, *parts: str | None) -> str:
    normalized = [part.strip() if part else "" for part in parts]
    return f"{prefix}:" + "|".join(normalized)


def ensure_file(path: Path) -> Path:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Missing required CSV file: {path}")
    return path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def ensure_import_patient(db, external_id: str, row: dict[str, str], summary: dict[str, int]) -> Patient:
    patient = db.scalar(select(Patient).where(Patient.external_id == external_id))
    first_name = row_value(row, "FIRST", "first") or "Imported"
    last_name = row_value(row, "LAST", "last") or "Patient"
    full_name = f"{first_name} {last_name}".strip()
    address_parts = [
        row_value(row, "ADDRESS", "address"),
        row_value(row, "CITY", "city"),
        row_value(row, "STATE", "state"),
    ]
    address = ", ".join(part for part in address_parts if part)

    if patient is None:
        username = build_username(external_id)
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            user = User(
                username=username,
                password_hash=hash_password(f"imported-{external_id}"),
                role=UserRole.PATIENT,
                is_active=False,
            )
            db.add(user)
            db.flush()

        patient = Patient(
            user_id=user.id,
            external_id=external_id,
            full_name=full_name,
            date_of_birth=parse_date(row_value(row, "BIRTHDATE", "birthdate")),
            gender=row_value(row, "GENDER", "gender"),
            phone=row_value(row, "PHONE", "phone"),
            address=address or None,
        )
        db.add(patient)
        summary["patients_created"] += 1
        return patient

    patient.full_name = full_name
    patient.date_of_birth = parse_date(row_value(row, "BIRTHDATE", "birthdate"))
    patient.gender = row_value(row, "GENDER", "gender")
    patient.phone = row_value(row, "PHONE", "phone")
    patient.address = address or patient.address
    summary["patients_updated"] += 1
    return patient


def import_patients(db, csv_path: Path, summary: dict[str, int]) -> None:
    for row in read_rows(csv_path):
        external_id = row_value(row, "Id", "ID", "id")
        if not external_id:
            summary["patients_skipped"] += 1
            continue
        ensure_import_patient(db, external_id, row, summary)
    db.flush()


def import_encounters(db, csv_path: Path, summary: dict[str, int]) -> None:
    for row in read_rows(csv_path):
        external_id = row_value(row, "Id", "ID", "id")
        patient_external_id = row_value(row, "PATIENT", "patient")
        if not external_id or not patient_external_id:
            summary["encounters_skipped"] += 1
            continue

        patient = db.scalar(select(Patient).where(Patient.external_id == patient_external_id))
        if patient is None:
            summary["encounters_skipped"] += 1
            continue

        encounter = db.scalar(select(Encounter).where(Encounter.external_id == external_id))
        if encounter is None:
            encounter = Encounter(patient_id=patient.id, external_id=external_id)
            db.add(encounter)
            summary["encounters_created"] += 1
        else:
            summary["encounters_updated"] += 1

        encounter.patient_id = patient.id
        encounter.started_at = parse_datetime(row_value(row, "START", "start"))
        encounter.ended_at = parse_datetime(row_value(row, "STOP", "stop"))
        encounter.encounter_class = row_value(row, "ENCOUNTERCLASS", "encounterclass")
        encounter.code = row_value(row, "CODE", "code")
        encounter.description = row_value(row, "DESCRIPTION", "description")
        encounter.reason_code = row_value(row, "REASONCODE", "reasoncode")
        encounter.reason_description = row_value(row, "REASONDESCRIPTION", "reasondescription")

    db.flush()


def import_conditions(db, csv_path: Path, summary: dict[str, int]) -> None:
    for row in read_rows(csv_path):
        patient_external_id = row_value(row, "PATIENT", "patient")
        if not patient_external_id:
            summary["conditions_skipped"] += 1
            continue

        patient = db.scalar(select(Patient).where(Patient.external_id == patient_external_id))
        if patient is None:
            summary["conditions_skipped"] += 1
            continue

        encounter_external_id = row_value(row, "ENCOUNTER", "encounter")
        source_key = build_source_key(
            "condition",
            patient_external_id,
            encounter_external_id,
            row_value(row, "START", "start"),
            row_value(row, "STOP", "stop"),
            row_value(row, "CODE", "code"),
            row_value(row, "DESCRIPTION", "description"),
        )
        condition = db.scalar(select(Condition).where(Condition.source_key == source_key))
        if condition is None:
            condition = Condition(patient_id=patient.id, source_key=source_key)
            db.add(condition)
            summary["conditions_created"] += 1
        else:
            summary["conditions_updated"] += 1

        encounter = None
        if encounter_external_id:
            encounter = db.scalar(select(Encounter).where(Encounter.external_id == encounter_external_id))

        condition.patient_id = patient.id
        condition.encounter_id = encounter.id if encounter else None
        condition.started_at = parse_datetime(row_value(row, "START", "start"))
        condition.ended_at = parse_datetime(row_value(row, "STOP", "stop"))
        condition.code = row_value(row, "CODE", "code")
        condition.description = row_value(row, "DESCRIPTION", "description")

    db.flush()


def import_medications(db, csv_path: Path, summary: dict[str, int]) -> None:
    for row in read_rows(csv_path):
        patient_external_id = row_value(row, "PATIENT", "patient")
        if not patient_external_id:
            summary["medications_skipped"] += 1
            continue

        patient = db.scalar(select(Patient).where(Patient.external_id == patient_external_id))
        if patient is None:
            summary["medications_skipped"] += 1
            continue

        encounter_external_id = row_value(row, "ENCOUNTER", "encounter")
        source_key = build_source_key(
            "medication",
            patient_external_id,
            encounter_external_id,
            row_value(row, "START", "start"),
            row_value(row, "STOP", "stop"),
            row_value(row, "CODE", "code"),
            row_value(row, "DESCRIPTION", "description"),
        )
        medication = db.scalar(select(Medication).where(Medication.source_key == source_key))
        if medication is None:
            medication = Medication(patient_id=patient.id, source_key=source_key)
            db.add(medication)
            summary["medications_created"] += 1
        else:
            summary["medications_updated"] += 1

        encounter = None
        if encounter_external_id:
            encounter = db.scalar(select(Encounter).where(Encounter.external_id == encounter_external_id))

        medication.patient_id = patient.id
        medication.encounter_id = encounter.id if encounter else None
        medication.started_at = parse_datetime(row_value(row, "START", "start"))
        medication.ended_at = parse_datetime(row_value(row, "STOP", "stop"))
        medication.code = row_value(row, "CODE", "code")
        medication.description = row_value(row, "DESCRIPTION", "description")
        medication.reason_code = row_value(row, "REASONCODE", "reasoncode")
        medication.reason_description = row_value(row, "REASONDESCRIPTION", "reasondescription")
        medication.base_cost = parse_decimal(row_value(row, "BASE_COST", "base_cost"))
        medication.payer_coverage = parse_decimal(
            row_value(row, "PAYER_COVERAGE", "payer_coverage")
        )
        medication.dispenses = parse_int(row_value(row, "DISPENSES", "dispenses"))
        medication.total_cost = parse_decimal(row_value(row, "TOTALCOST", "TOTAL_COST", "total_cost"))

    db.flush()


def import_observations(db, csv_path: Path, summary: dict[str, int]) -> None:
    for row in read_rows(csv_path):
        patient_external_id = row_value(row, "PATIENT", "patient")
        if not patient_external_id:
            summary["observations_skipped"] += 1
            continue

        patient = db.scalar(select(Patient).where(Patient.external_id == patient_external_id))
        if patient is None:
            summary["observations_skipped"] += 1
            continue

        encounter_external_id = row_value(row, "ENCOUNTER", "encounter")
        source_key = build_source_key(
            "observation",
            patient_external_id,
            encounter_external_id,
            row_value(row, "DATE", "date"),
            row_value(row, "CODE", "code"),
            row_value(row, "DESCRIPTION", "description"),
            row_value(row, "VALUE", "value"),
            row_value(row, "UNITS", "units"),
        )
        observation = db.scalar(select(Observation).where(Observation.source_key == source_key))
        if observation is None:
            observation = Observation(patient_id=patient.id, source_key=source_key)
            db.add(observation)
            summary["observations_created"] += 1
        else:
            summary["observations_updated"] += 1

        encounter = None
        if encounter_external_id:
            encounter = db.scalar(select(Encounter).where(Encounter.external_id == encounter_external_id))

        observation.patient_id = patient.id
        observation.encounter_id = encounter.id if encounter else None
        observation.observed_at = parse_datetime(row_value(row, "DATE", "date"))
        observation.category = row_value(row, "CATEGORY", "category")
        observation.code = row_value(row, "CODE", "code")
        observation.description = row_value(row, "DESCRIPTION", "description")
        observation.value_text = row_value(row, "VALUE", "value")
        observation.units = row_value(row, "UNITS", "units")
        observation.value_type = row_value(row, "TYPE", "type")

    db.flush()


def print_summary(summary: dict[str, int]) -> None:
    print("Synthea import summary:")
    for key in sorted(summary):
        print(f"- {key}: {summary[key]}")


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    summary = {key: 0 for key in [
        "patients_created",
        "patients_updated",
        "patients_skipped",
        "encounters_created",
        "encounters_updated",
        "encounters_skipped",
        "conditions_created",
        "conditions_updated",
        "conditions_skipped",
        "medications_created",
        "medications_updated",
        "medications_skipped",
        "observations_created",
        "observations_updated",
        "observations_skipped",
    ]}

    file_map = {name: ensure_file(data_dir / filename) for name, filename in SUPPORTED_FILES.items()}

    db = SessionLocal()
    try:
        import_patients(db, file_map["patients"], summary)
        import_encounters(db, file_map["encounters"], summary)
        import_conditions(db, file_map["conditions"], summary)
        import_medications(db, file_map["medications"], summary)
        import_observations(db, file_map["observations"], summary)
        db.commit()
        print_summary(summary)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
