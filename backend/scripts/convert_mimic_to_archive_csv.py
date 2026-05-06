from __future__ import annotations

import argparse
import csv
import gzip
from datetime import date
from pathlib import Path
from typing import Iterable, TextIO


ARCHIVE_HEADERS = {
    "patients.csv": ["Id", "BIRTHDATE", "FIRST", "LAST", "GENDER", "PHONE", "ADDRESS", "CITY", "STATE"],
    "encounters.csv": [
        "Id",
        "PATIENT",
        "START",
        "STOP",
        "ENCOUNTERCLASS",
        "CODE",
        "DESCRIPTION",
        "REASONCODE",
        "REASONDESCRIPTION",
    ],
    "conditions.csv": ["START", "STOP", "PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION"],
    "medications.csv": [
        "START",
        "STOP",
        "PATIENT",
        "ENCOUNTER",
        "CODE",
        "DESCRIPTION",
        "REASONCODE",
        "REASONDESCRIPTION",
        "BASE_COST",
        "PAYER_COVERAGE",
        "DISPENSES",
        "TOTALCOST",
    ],
    "observations.csv": [
        "DATE",
        "PATIENT",
        "ENCOUNTER",
        "CATEGORY",
        "CODE",
        "DESCRIPTION",
        "VALUE",
        "UNITS",
        "TYPE",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert MIMIC-IV Demo/Full hospital CSV files into the archive CSV layout."
    )
    parser.add_argument(
        "mimic_dir",
        help="MIMIC-IV root directory or the hosp directory containing patients.csv(.gz).",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="data/mimic_archive",
        help="Directory for generated patients/encounters/conditions/medications/observations CSV files.",
    )
    return parser.parse_args()


def resolve_hosp_dir(mimic_dir: Path) -> Path:
    if (mimic_dir / "patients.csv").exists() or (mimic_dir / "patients.csv.gz").exists():
        return mimic_dir
    hosp_dir = mimic_dir / "hosp"
    if (hosp_dir / "patients.csv").exists() or (hosp_dir / "patients.csv.gz").exists():
        return hosp_dir
    raise FileNotFoundError("Could not find MIMIC hosp CSV files. Expected patients.csv or patients.csv.gz.")


def csv_path(hosp_dir: Path, filename: str) -> Path:
    plain_path = hosp_dir / filename
    gzip_path = hosp_dir / f"{filename}.gz"
    if plain_path.exists():
        return plain_path
    if gzip_path.exists():
        return gzip_path
    raise FileNotFoundError(f"Missing MIMIC file: {filename} or {filename}.gz")


def open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8-sig", newline="")
    return path.open("r", encoding="utf-8-sig", newline="")


def read_rows(path: Path) -> Iterable[dict[str, str]]:
    with open_text(path) as file_obj:
        yield from csv.DictReader(file_obj)


def row_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and value.strip() != "":
            return value.strip()
    return ""


def clean_text(*parts: str) -> str:
    return " | ".join(part.strip() for part in parts if part and part.strip())


def approximate_birthdate(anchor_age: str, anchor_year: str) -> str:
    try:
        age = int(float(anchor_age))
        year = int(float(anchor_year)) - age
    except ValueError:
        return ""
    return date(max(year, 1900), 1, 1).isoformat()


def write_csv(output_dir: Path, filename: str, rows: Iterable[dict[str, str]]) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    headers = ARCHIVE_HEADERS[filename]
    count = 0
    with output_path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})
            count += 1
    return count


def load_icd_titles(hosp_dir: Path) -> dict[tuple[str, str], str]:
    path = csv_path(hosp_dir, "d_icd_diagnoses.csv")
    titles: dict[tuple[str, str], str] = {}
    for row in read_rows(path):
        code = row_value(row, "icd_code")
        version = row_value(row, "icd_version")
        title = row_value(row, "long_title")
        if code and version:
            titles[(code, version)] = title
    return titles


def load_lab_items(hosp_dir: Path) -> dict[str, dict[str, str]]:
    path = csv_path(hosp_dir, "d_labitems.csv")
    items: dict[str, dict[str, str]] = {}
    for row in read_rows(path):
        itemid = row_value(row, "itemid")
        if itemid:
            items[itemid] = {
                "label": row_value(row, "label"),
                "fluid": row_value(row, "fluid"),
                "category": row_value(row, "category"),
            }
    return items


def patient_rows(hosp_dir: Path) -> Iterable[dict[str, str]]:
    for row in read_rows(csv_path(hosp_dir, "patients.csv")):
        subject_id = row_value(row, "subject_id")
        if not subject_id:
            continue
        yield {
            "Id": subject_id,
            "BIRTHDATE": approximate_birthdate(row_value(row, "anchor_age"), row_value(row, "anchor_year")),
            "FIRST": "MIMIC",
            "LAST": f"Patient {subject_id}",
            "GENDER": row_value(row, "gender"),
        }


def encounter_rows(hosp_dir: Path) -> Iterable[dict[str, str]]:
    for row in read_rows(csv_path(hosp_dir, "admissions.csv")):
        subject_id = row_value(row, "subject_id")
        hadm_id = row_value(row, "hadm_id")
        if not subject_id or not hadm_id:
            continue
        admission_type = row_value(row, "admission_type")
        admission_location = row_value(row, "admission_location")
        discharge_location = row_value(row, "discharge_location")
        description = clean_text(admission_type, admission_location, discharge_location)
        yield {
            "Id": hadm_id,
            "PATIENT": subject_id,
            "START": row_value(row, "admittime"),
            "STOP": row_value(row, "dischtime"),
            "ENCOUNTERCLASS": admission_type,
            "CODE": admission_type,
            "DESCRIPTION": description or "Hospital admission",
            "REASONCODE": row_value(row, "admission_location"),
            "REASONDESCRIPTION": admission_location,
        }


def condition_rows(hosp_dir: Path, icd_titles: dict[tuple[str, str], str]) -> Iterable[dict[str, str]]:
    for row in read_rows(csv_path(hosp_dir, "diagnoses_icd.csv")):
        subject_id = row_value(row, "subject_id")
        hadm_id = row_value(row, "hadm_id")
        code = row_value(row, "icd_code")
        version = row_value(row, "icd_version")
        if not subject_id or not code:
            continue
        title = icd_titles.get((code, version), code)
        seq_num = row_value(row, "seq_num")
        yield {
            "PATIENT": subject_id,
            "ENCOUNTER": hadm_id,
            "CODE": f"ICD-{version}:{code}" if version else code,
            "DESCRIPTION": clean_text(title, f"seq {seq_num}" if seq_num else ""),
        }


def medication_rows(hosp_dir: Path) -> Iterable[dict[str, str]]:
    for row in read_rows(csv_path(hosp_dir, "prescriptions.csv")):
        subject_id = row_value(row, "subject_id")
        hadm_id = row_value(row, "hadm_id")
        drug = row_value(row, "drug")
        if not subject_id or not drug:
            continue
        code = row_value(row, "ndc", "formulary_drug_cd", "gsn")
        dose = clean_text(row_value(row, "dose_val_rx"), row_value(row, "dose_unit_rx"))
        description = clean_text(drug, dose, row_value(row, "route"))
        yield {
            "START": row_value(row, "starttime"),
            "STOP": row_value(row, "stoptime"),
            "PATIENT": subject_id,
            "ENCOUNTER": hadm_id,
            "CODE": code or drug,
            "DESCRIPTION": description or drug,
            "REASONCODE": row_value(row, "drug_type"),
            "REASONDESCRIPTION": row_value(row, "drug_type"),
            "DISPENSES": row_value(row, "doses_per_24_hrs"),
        }


def observation_rows(hosp_dir: Path, lab_items: dict[str, dict[str, str]]) -> Iterable[dict[str, str]]:
    for row in read_rows(csv_path(hosp_dir, "labevents.csv")):
        subject_id = row_value(row, "subject_id")
        itemid = row_value(row, "itemid")
        if not subject_id or not itemid:
            continue
        item = lab_items.get(itemid, {})
        event_id = row_value(row, "labevent_id")
        value = row_value(row, "valuenum", "value")
        value_type = "numeric" if row_value(row, "valuenum") else "text"
        yield {
            "DATE": row_value(row, "charttime", "storetime"),
            "PATIENT": subject_id,
            "ENCOUNTER": row_value(row, "hadm_id"),
            "CATEGORY": clean_text(item.get("category", ""), item.get("fluid", "")),
            "CODE": itemid,
            "DESCRIPTION": clean_text(item.get("label", itemid), f"event {event_id}" if event_id else ""),
            "VALUE": value,
            "UNITS": row_value(row, "valueuom"),
            "TYPE": value_type,
        }


def main() -> None:
    args = parse_args()
    hosp_dir = resolve_hosp_dir(Path(args.mimic_dir).resolve())
    output_dir = Path(args.output_dir).resolve()

    icd_titles = load_icd_titles(hosp_dir)
    lab_items = load_lab_items(hosp_dir)

    summary = {
        "patients": write_csv(output_dir, "patients.csv", patient_rows(hosp_dir)),
        "encounters": write_csv(output_dir, "encounters.csv", encounter_rows(hosp_dir)),
        "conditions": write_csv(output_dir, "conditions.csv", condition_rows(hosp_dir, icd_titles)),
        "medications": write_csv(output_dir, "medications.csv", medication_rows(hosp_dir)),
        "observations": write_csv(output_dir, "observations.csv", observation_rows(hosp_dir, lab_items)),
    }

    print("MIMIC archive CSV conversion summary:")
    print(f"- source: {hosp_dir}")
    print(f"- output: {output_dir}")
    for key, value in summary.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
