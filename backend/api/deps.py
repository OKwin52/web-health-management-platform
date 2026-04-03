from __future__ import annotations

from typing import Iterable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.db import get_db
from backend.models import AuthorizationStatus, Doctor, Patient, PatientDoctorAuthorization, User, UserRole


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.scalar(select(User).where(User.username == username))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user")
    return user


def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


def get_current_patient(db: Session, user: User) -> Patient | None:
    return db.scalar(select(Patient).where(Patient.user_id == user.id))


def get_current_doctor(db: Session, user: User) -> Doctor | None:
    return db.scalar(select(Doctor).where(Doctor.user_id == user.id))


def ensure_patient_access(db: Session, current_user: User, patient: Patient) -> None:
    if current_user.role == UserRole.ADMIN:
        return

    if current_user.role == UserRole.PATIENT:
        current_patient = get_current_patient(db, current_user)
        if current_patient and current_patient.id == patient.id:
            return

    if current_user.role == UserRole.DOCTOR:
        doctor = get_current_doctor(db, current_user)
        if doctor is not None:
            authorization = db.scalar(
                select(PatientDoctorAuthorization).where(
                    PatientDoctorAuthorization.patient_id == patient.id,
                    PatientDoctorAuthorization.doctor_id == doctor.id,
                    PatientDoctorAuthorization.status == AuthorizationStatus.ACTIVE,
                )
            )
            if authorization is not None:
                return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient access denied")


def patient_list_scope(db: Session, current_user: User) -> Iterable[Patient]:
    if current_user.role == UserRole.ADMIN:
        return db.scalars(select(Patient).order_by(Patient.id)).all()

    if current_user.role == UserRole.PATIENT:
        patient = get_current_patient(db, current_user)
        return [patient] if patient is not None else []

    doctor = get_current_doctor(db, current_user)
    if doctor is None:
        return []

    return db.scalars(
        select(Patient)
        .join(PatientDoctorAuthorization, PatientDoctorAuthorization.patient_id == Patient.id)
        .where(
            PatientDoctorAuthorization.doctor_id == doctor.id,
            PatientDoctorAuthorization.status == AuthorizationStatus.ACTIVE,
        )
        .order_by(Patient.id)
    ).all()
