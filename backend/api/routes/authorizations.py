from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.api.deps import get_current_patient, get_current_user, require_roles
from backend.db import get_db
from backend.models import (
    AuthorizationStatus,
    Doctor,
    Patient,
    PatientDoctorAuthorization,
    User,
    UserRole,
)
from backend.schemas.authorization import AuthorizationCreate, AuthorizationResponse


router = APIRouter(prefix="/authorizations", tags=["authorizations"])


@router.get("", response_model=list[AuthorizationResponse])
def list_authorizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PatientDoctorAuthorization]:
    query = select(PatientDoctorAuthorization).order_by(PatientDoctorAuthorization.id)

    if current_user.role == UserRole.ADMIN:
        return db.scalars(query).all()

    if current_user.role == UserRole.PATIENT:
        patient = get_current_patient(db, current_user)
        if patient is None:
            return []
        return db.scalars(query.where(PatientDoctorAuthorization.patient_id == patient.id)).all()

    doctor = db.scalar(select(Doctor).where(Doctor.user_id == current_user.id))
    if doctor is None:
        return []
    return db.scalars(query.where(PatientDoctorAuthorization.doctor_id == doctor.id)).all()


@router.post("", response_model=AuthorizationResponse, status_code=status.HTTP_201_CREATED)
def create_authorization(
    payload: AuthorizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PatientDoctorAuthorization:
    patient = db.scalar(select(Patient).where(Patient.id == payload.patient_id))
    doctor = db.scalar(select(Doctor).where(Doctor.id == payload.doctor_id))
    if patient is None or doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient or doctor not found")

    if current_user.role == UserRole.PATIENT and current_user.id != patient.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot authorize for another patient")

    if current_user.role not in {UserRole.ADMIN, UserRole.PATIENT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authorization change denied")

    authorization = db.scalar(
        select(PatientDoctorAuthorization).where(
            PatientDoctorAuthorization.patient_id == payload.patient_id,
            PatientDoctorAuthorization.doctor_id == payload.doctor_id,
        )
    )

    if authorization is None:
        authorization = PatientDoctorAuthorization(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            status=AuthorizationStatus.ACTIVE,
            revoked_at=None,
        )
        db.add(authorization)
    else:
        authorization.status = AuthorizationStatus.ACTIVE
        authorization.revoked_at = None

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization could not be saved") from exc

    db.refresh(authorization)
    return authorization


@router.delete("/{authorization_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_authorization(
    authorization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    authorization = db.scalar(
        select(PatientDoctorAuthorization).where(PatientDoctorAuthorization.id == authorization_id)
    )
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Authorization not found")

    if current_user.role == UserRole.PATIENT:
        patient = get_current_patient(db, current_user)
        if patient is None or patient.id != authorization.patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authorization revoke denied")
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authorization revoke denied")

    authorization.status = AuthorizationStatus.REVOKED
    authorization.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
