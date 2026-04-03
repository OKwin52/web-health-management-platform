"""add archive tables

Revision ID: 0002_add_archive_tables
Revises: 0001_create_core_tables
Create Date: 2026-04-04 00:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_archive_tables"
down_revision = "0001_create_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("external_id", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_patients_external_id"), "patients", ["external_id"], unique=True)

    op.create_table(
        "encounters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("encounter_class", sa.String(length=50), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("reason_code", sa.String(length=50), nullable=True),
        sa.Column("reason_description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name=op.f("fk_encounters_patient_id_patients")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_encounters")),
        sa.UniqueConstraint("external_id", name=op.f("uq_encounters_external_id")),
    )
    op.create_index(op.f("ix_encounters_patient_id"), "encounters", ["patient_id"], unique=False)

    op.create_table(
        "conditions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("encounter_id", sa.Integer(), nullable=True),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["encounter_id"], ["encounters.id"], name=op.f("fk_conditions_encounter_id_encounters")),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name=op.f("fk_conditions_patient_id_patients")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conditions")),
        sa.UniqueConstraint("source_key", name=op.f("uq_conditions_source_key")),
    )
    op.create_index(op.f("ix_conditions_encounter_id"), "conditions", ["encounter_id"], unique=False)
    op.create_index(op.f("ix_conditions_patient_id"), "conditions", ["patient_id"], unique=False)

    op.create_table(
        "medications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("encounter_id", sa.Integer(), nullable=True),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("reason_code", sa.String(length=50), nullable=True),
        sa.Column("reason_description", sa.String(length=255), nullable=True),
        sa.Column("base_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("payer_coverage", sa.Numeric(10, 2), nullable=True),
        sa.Column("dispenses", sa.Integer(), nullable=True),
        sa.Column("total_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["encounter_id"], ["encounters.id"], name=op.f("fk_medications_encounter_id_encounters")),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name=op.f("fk_medications_patient_id_patients")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_medications")),
        sa.UniqueConstraint("source_key", name=op.f("uq_medications_source_key")),
    )
    op.create_index(op.f("ix_medications_encounter_id"), "medications", ["encounter_id"], unique=False)
    op.create_index(op.f("ix_medications_patient_id"), "medications", ["patient_id"], unique=False)

    op.create_table(
        "observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("encounter_id", sa.Integer(), nullable=True),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("units", sa.String(length=50), nullable=True),
        sa.Column("value_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["encounter_id"], ["encounters.id"], name=op.f("fk_observations_encounter_id_encounters")),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name=op.f("fk_observations_patient_id_patients")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_observations")),
        sa.UniqueConstraint("source_key", name=op.f("uq_observations_source_key")),
    )
    op.create_index(op.f("ix_observations_encounter_id"), "observations", ["encounter_id"], unique=False)
    op.create_index(op.f("ix_observations_patient_id"), "observations", ["patient_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_observations_patient_id"), table_name="observations")
    op.drop_index(op.f("ix_observations_encounter_id"), table_name="observations")
    op.drop_table("observations")

    op.drop_index(op.f("ix_medications_patient_id"), table_name="medications")
    op.drop_index(op.f("ix_medications_encounter_id"), table_name="medications")
    op.drop_table("medications")

    op.drop_index(op.f("ix_conditions_patient_id"), table_name="conditions")
    op.drop_index(op.f("ix_conditions_encounter_id"), table_name="conditions")
    op.drop_table("conditions")

    op.drop_index(op.f("ix_encounters_patient_id"), table_name="encounters")
    op.drop_table("encounters")

    op.drop_index(op.f("ix_patients_external_id"), table_name="patients")
    op.drop_column("patients", "external_id")
