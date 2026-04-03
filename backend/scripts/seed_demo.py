from __future__ import annotations

from datetime import date

from sqlalchemy import select

from backend.core.security import hash_password
from backend.db import SessionLocal
from backend.models import (
    AuthorizationStatus,
    Doctor,
    Patient,
    PatientDoctorAuthorization,
    User,
    UserRole,
)


def ensure_user(db, username: str, password: str, role: UserRole) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is not None:
        return user

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def main() -> None:
    db = SessionLocal()
    try:
        admin = ensure_user(db, "admin", "admin123", UserRole.ADMIN)
        alice_user = ensure_user(db, "alice", "alice123", UserRole.PATIENT)
        bob_user = ensure_user(db, "bob", "bob123", UserRole.PATIENT)
        doctor_user = ensure_user(db, "drsmith", "doctor123", UserRole.DOCTOR)

        alice_patient = db.scalar(select(Patient).where(Patient.user_id == alice_user.id))
        if alice_patient is None:
            alice_patient = Patient(
                user_id=alice_user.id,
                full_name="Alice Carter",
                date_of_birth=date(1993, 5, 17),
                gender="female",
                phone="13800000001",
                address="Demo Street 1",
            )
            db.add(alice_patient)

        bob_patient = db.scalar(select(Patient).where(Patient.user_id == bob_user.id))
        if bob_patient is None:
            bob_patient = Patient(
                user_id=bob_user.id,
                full_name="Bob Lin",
                date_of_birth=date(1989, 9, 8),
                gender="male",
                phone="13800000002",
                address="Demo Street 2",
            )
            db.add(bob_patient)

        doctor = db.scalar(select(Doctor).where(Doctor.user_id == doctor_user.id))
        if doctor is None:
            doctor = Doctor(
                user_id=doctor_user.id,
                full_name="Dr. Smith",
                department="Cardiology",
                title="Attending Physician",
            )
            db.add(doctor)

        db.flush()

        authorization = db.scalar(
            select(PatientDoctorAuthorization).where(
                PatientDoctorAuthorization.patient_id == alice_patient.id,
                PatientDoctorAuthorization.doctor_id == doctor.id,
            )
        )
        if authorization is None:
            db.add(
                PatientDoctorAuthorization(
                    patient_id=alice_patient.id,
                    doctor_id=doctor.id,
                    status=AuthorizationStatus.ACTIVE,
                )
            )

        db.commit()
        print("Demo data seeded: admin/admin123, alice/alice123, bob/bob123, drsmith/doctor123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
