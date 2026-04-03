from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.deps import ensure_patient_access, get_current_user
from backend.db import get_db
from backend.models import Condition, Encounter, Medication, Observation, Patient, User
from backend.schemas.archive import (
    ConditionResponse,
    EncounterResponse,
    MedicationResponse,
    ObservationResponse,
)


router = APIRouter(prefix="/patients", tags=["medical-archive"])


def get_accessible_patient(db: Session, current_user: User, patient_id: int) -> Patient:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    ensure_patient_access(db, current_user, patient)
    return patient


@router.get("/{patient_id}/encounters", response_model=list[EncounterResponse])
def list_patient_encounters(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Encounter]:
    patient = get_accessible_patient(db, current_user, patient_id)
    return db.scalars(
        select(Encounter)
        .where(Encounter.patient_id == patient.id)
        .order_by(Encounter.started_at.desc(), Encounter.id.desc())
    ).all()


@router.get("/{patient_id}/conditions", response_model=list[ConditionResponse])
def list_patient_conditions(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Condition]:
    patient = get_accessible_patient(db, current_user, patient_id)
    return db.scalars(
        select(Condition)
        .where(Condition.patient_id == patient.id)
        .order_by(Condition.started_at.desc(), Condition.id.desc())
    ).all()


@router.get("/{patient_id}/medications", response_model=list[MedicationResponse])
def list_patient_medications(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Medication]:
    patient = get_accessible_patient(db, current_user, patient_id)
    return db.scalars(
        select(Medication)
        .where(Medication.patient_id == patient.id)
        .order_by(Medication.started_at.desc(), Medication.id.desc())
    ).all()


@router.get("/{patient_id}/observations", response_model=list[ObservationResponse])
def list_patient_observations(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Observation]:
    patient = get_accessible_patient(db, current_user, patient_id)
    return db.scalars(
        select(Observation)
        .where(Observation.patient_id == patient.id)
        .order_by(Observation.observed_at.desc(), Observation.id.desc())
    ).all()
