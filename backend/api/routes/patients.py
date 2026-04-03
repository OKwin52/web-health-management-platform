from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend.api.deps import ensure_patient_access, get_current_user, patient_list_scope, require_roles
from backend.core.security import hash_password
from backend.db import get_db
from backend.models import (
    Condition,
    Encounter,
    Medication,
    Observation,
    Patient,
    PatientDoctorAuthorization,
    User,
    UserRole,
)
from backend.schemas.patient import PatientCreate, PatientResponse, PatientUpdate


router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientResponse])
def list_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Patient]:
    scoped_patients = patient_list_scope(db, current_user)
    patient_ids = [patient.id for patient in scoped_patients]
    if not patient_ids:
        return []
    return db.scalars(
        select(Patient)
        .options(joinedload(Patient.user))
        .where(Patient.id.in_(patient_ids))
        .order_by(Patient.id)
    ).unique().all()


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Patient:
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=UserRole.PATIENT,
        is_active=True,
    )
    patient = Patient(
        user=user,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        phone=payload.phone,
        address=payload.address,
    )
    db.add(patient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists") from exc

    db.refresh(patient)
    return db.scalar(
        select(Patient).options(joinedload(Patient.user)).where(Patient.id == patient.id)
    )


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Patient:
    patient = db.scalar(
        select(Patient).options(joinedload(Patient.user)).where(Patient.id == patient_id)
    )
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    ensure_patient_access(db, current_user, patient)
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Patient:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if current_user.role not in {UserRole.ADMIN, UserRole.PATIENT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient update denied")

    if current_user.role == UserRole.PATIENT and patient.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient update denied")

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field_name, value)

    db.commit()
    db.refresh(patient)
    return db.scalar(
        select(Patient).options(joinedload(Patient.user)).where(Patient.id == patient.id)
    )


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: int,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Response:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    user = db.scalar(select(User).where(User.id == patient.user_id))
    observations = db.scalars(
        select(Observation).where(Observation.patient_id == patient.id)
    ).all()
    medications = db.scalars(
        select(Medication).where(Medication.patient_id == patient.id)
    ).all()
    conditions = db.scalars(
        select(Condition).where(Condition.patient_id == patient.id)
    ).all()
    encounters = db.scalars(
        select(Encounter).where(Encounter.patient_id == patient.id)
    ).all()
    authorizations = db.scalars(
        select(PatientDoctorAuthorization).where(
            PatientDoctorAuthorization.patient_id == patient.id
        )
    ).all()
    for observation in observations:
        db.delete(observation)
    for medication in medications:
        db.delete(medication)
    for condition in conditions:
        db.delete(condition)
    for encounter in encounters:
        db.delete(encounter)
    for authorization in authorizations:
        db.delete(authorization)
    db.delete(patient)
    if user is not None:
        db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
