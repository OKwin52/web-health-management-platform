# MIMIC-IV Demo Real EHR Data Replacement

This project keeps the existing medical archive schema and imports MIMIC-IV data through a conversion step. The goal is to replace synthetic Synthea archive data with a public, citable, deidentified real EHR source without expanding the current Phase 2 scope.

## Data Source

Recommended source:

- MIMIC-IV Clinical Database Demo v2.2
- URL: https://physionet.org/content/mimic-iv-demo/2.2/
- DOI: https://doi.org/10.13026/dp1f-ex47
- Access: open access under the dataset license
- Scale: 100 deidentified patients

Expansion source:

- MIMIC-IV v3.1
- URL: https://physionet.org/content/mimiciv/3.1/
- DOI: https://doi.org/10.13026/kpb9-mt58
- Access: credentialed PhysioNet access required

Do not commit full real EHR exports into this repository. Keep downloaded MIMIC files in a local data directory and commit only code, documentation, and small permitted examples.

## Mapping Strategy

The converter reads MIMIC `hosp` CSV files and writes the five archive CSV files already supported by the current importer.

| Current archive CSV | MIMIC source table | Mapping intent |
| --- | --- | --- |
| `patients.csv` | `hosp/patients` | Patient identity placeholder, gender, approximate birth year from anchor age/year |
| `encounters.csv` | `hosp/admissions` | Hospital admissions as encounter records |
| `conditions.csv` | `hosp/diagnoses_icd` + `hosp/d_icd_diagnoses` | ICD diagnosis history |
| `medications.csv` | `hosp/prescriptions` | Medication order/prescription history |
| `observations.csv` | `hosp/labevents` + `hosp/d_labitems` | Laboratory observations |

MIMIC dates and identifiers are deidentified. The converter preserves the shifted timestamps as provided by MIMIC and uses MIMIC identifiers only as external archive keys.

## Conversion and Import

Download and unzip the MIMIC-IV Demo files locally. The converter accepts either the dataset root or the `hosp` directory.

```powershell
python -m backend.scripts.convert_mimic_to_archive_csv data\mimic-iv-demo data\mimic_archive
python -m backend.scripts.import_synthea_csv data\mimic_archive
```

The generated directory contains:

- `patients.csv`
- `encounters.csv`
- `conditions.csv`
- `medications.csv`
- `observations.csv`

The existing importer remains idempotent for these generated files. Re-running conversion replaces the generated CSV files, and re-running import updates matching archive records instead of creating uncontrolled duplicates.

## Frontend Presentation

The frontend presents system labels in Chinese and uses a small display dictionary for common medical terms. Low-frequency or ambiguous medical terms remain in the original English wording to avoid inaccurate translation and preserve traceability to the source data.

## Prediction Data Boundary

MIMIC-IV replaces the medical archive layer only. The prediction module should not claim that home blood pressure or weight prediction data comes from MIMIC unless a later phase explicitly derives and validates such a time series.

Recommended thesis wording:

> The system uses MIMIC-IV Demo as a real deidentified EHR source for medical archive management. The trend prediction module is planned as a separate extension based on longitudinal blood pressure and weight records; if lifestyle fields are rule-augmented, they are explicitly marked as derived auxiliary features.
