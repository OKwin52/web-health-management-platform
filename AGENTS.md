# AGENTS.md

## 1. Project Overview

This project is a graduation design for a **personal health management system with trend prediction and early warning**.

The system aims to address the following practical problems:

- fragmented personal health information
- discontinuous medical records
- untimely doctor-patient communication
- lack of continuous home health monitoring
- lack of intelligent trend analysis for blood pressure and weight

The final system should integrate:

1. personal health record management
2. medical encounter and medication management
3. daily home health data recording
4. doctor-patient authorized sharing and interaction
5. automatic health report generation
6. blood pressure and weight trend prediction
7. abnormal trend warning and reminder

This is **primarily a system project**, with machine learning as an embedded module.

## Current Delivery Status

- Phase 1 is complete: backend skeleton, JWT auth, RBAC, user/patient/doctor/authorization models, patient CRUD, migrations, and demo seed data are in place.
- Current implementation target is Phase 2 only: medical archive content tables, Synthea-style CSV import, and archive read APIs.
- Do not start daily monitoring, reports, or prediction work unless explicitly requested in a later phase.

---

## 2. Core Design Principle

When making architectural or coding decisions, always follow this priority:

### Priority order
1. **system usability and data consistency**
2. **clear database design**
3. **modular backend implementation**
4. **predictive analytics integration**
5. **UI refinement**

Do **not** treat this project as a pure machine learning project.

Do **not** over-engineer the prediction module at the cost of core system functions.

The system should be designed as:

- **medical record and health archive management as the main body**
- **trend prediction and warning as an intelligent extension**

---

## 3. Data Strategy

### 3.1 Synthea data usage
Synthea is used as the **base EHR source** for synthetic patient records.

It should be used to initialize and simulate:

- patient basic information
- encounters
- conditions / diagnoses
- medications
- observations
- procedures
- allergies

Synthea data is mainly used for:

- system database initialization
- patient profile pages
- encounter history pages
- medication management pages
- doctor-side patient review functions

### 3.2 Home daily monitoring dataset
The system must define an additional dataset for **daily home monitoring**, because the prediction task is based on continuous home records rather than hospital-only EHR data.

This dataset should include at least:

- daily systolic blood pressure
- daily diastolic blood pressure
- daily weight
- medication adherence
- exercise duration
- sleep duration
- salt intake level
- stress level
- warning labels if needed

This dataset can be:
- manually constructed
- rule-augmented from Synthea patient background
- stored in the project database

This daily dataset is the main source for model training and inference.

---

## 4. System Scope

The coding agent must keep the system within the following scope.

### 4.1 Required modules
The system should include the following modules:

#### A. User and patient management
- patient registration / import
- patient profile
- role distinction: patient / doctor / admin
- secure login and identity management

#### B. Health archive management
- patient demographic profile
- diagnosis history
- encounter history
- medication history
- observation history
- allergies / chronic disease summary

#### C. Daily health monitoring
- daily blood pressure input
- daily weight input
- lifestyle behavior input
- trend charts
- historical query

#### D. Doctor-patient interaction
- doctor can view authorized patient records
- patient can authorize or revoke access
- online messaging or simple consultation records
- review of warnings and suggestions

#### E. Health report generation
- summarize recent blood pressure and weight changes
- summarize medication adherence
- generate structured health report text
- optionally export report as PDF later

#### F. Prediction and warning
- predict future blood pressure / weight trend
- detect abnormal rising trends
- provide reminder messages
- display prediction results inside the system

### 4.2 Out of scope
Unless explicitly requested later, avoid implementing:
- full hospital-grade HIS/EMR complexity
- complex billing systems
- sophisticated real-time chat infrastructure
- large-scale distributed microservices
- advanced deep learning serving pipelines
- medical-grade diagnosis generation

This is a graduation project, so simplicity, clarity, and completeness matter more than enterprise-scale complexity.

---

## 5. Recommended Technical Architecture

The coding agent should prefer a simple, maintainable full-stack structure.

### Recommended stack
- **Frontend**: React / Vue (prefer React if no constraint)
- **Backend**: FastAPI / Flask (prefer FastAPI)
- **Database**: MySQL or PostgreSQL
- **Model service**: integrated Python module inside backend
- **ORM**: SQLAlchemy
- **Charts**: ECharts / Recharts
- **Auth**: JWT-based simple authentication

### Suggested architecture
- `frontend/` for UI
- `backend/` for API and business logic
- `backend/models/` for ORM entities
- `backend/schemas/` for request/response models
- `backend/services/` for business services
- `backend/ml/` for prediction pipeline
- `backend/scripts/` for Synthea import and daily data generation
- `data/` for raw or processed synthetic datasets
- `docs/` for design notes

---

## 6. Database Design Guidance

The database should be designed around two layers:

### Layer 1: Medical archive layer
This stores long-term health records initialized from Synthea.

Suggested core tables:
- `users`
- `patients`
- `doctors`
- `patient_doctor_authorizations`
- `encounters`
- `conditions`
- `medications`
- `observations`
- `allergies`
- `procedures`

### Layer 2: Home monitoring layer
This stores daily home health records and model-related data.

Suggested core tables:
- `daily_health_records`
- `daily_lifestyle_records`
- `prediction_results`
- `warning_logs`
- `health_reports`
- `consultation_messages`

### Example for daily health records
Each row should represent **one patient on one day**.

Fields may include:
- `id`
- `patient_id`
- `record_date`
- `systolic_bp`
- `diastolic_bp`
- `weight`
- `heart_rate` (optional)
- `medicine_taken`
- `exercise_minutes`
- `sleep_hours`
- `salt_intake_level`
- `stress_level`
- `remark`
- `created_at`
- `updated_at`

### Design rules
- keep schemas normalized enough for clarity
- avoid unnecessary excessive decomposition
- use foreign keys consistently
- preserve auditability and traceability
- make patient-to-daily-record relationship explicit

---

## 7. Machine Learning Module Guidance

The ML module is a submodule of the system.

### 7.1 Primary goal
Provide simple, interpretable prediction for:
- next-day systolic blood pressure
- next-day diastolic blood pressure
- next-day weight
- optional warning classification

### 7.2 Recommended models
Preferred order:

1. **XGBoost / LightGBM**
2. Linear Regression
3. ARIMA
4. GRU (optional extension only)

Default recommendation:
- use **XGBoost or LightGBM** as the main model
- use **Linear Regression** and/or **ARIMA** as baseline models

Do not default to complex deep learning unless specifically needed.

### 7.3 Feature engineering
The ML module should use time-window features such as:
- previous day blood pressure
- 3-day moving average
- 7-day moving average
- 7-day slope
- previous day weight
- recent medication adherence count
- recent sleep average
- recent exercise total
- recent salt intake pattern
- weekday effects if useful

### 7.4 Output expectations
Prediction module should output:
- predicted value(s)
- predicted trend direction
- warning label if threshold exceeded
- human-readable explanation summary if possible

### 7.5 Integration rule
The prediction result must be stored back into the system and shown in:
- patient dashboard
- doctor review page
- health report

The ML module must not exist as an isolated notebook-only artifact.

---

## 8. Functional Priorities for Development

The coding agent should implement the project in this order:

### Phase 1: core backend and database
- define schema
- implement ORM models
- build CRUD APIs
- support Synthea import
- support daily record insertion

### Phase 2: core frontend pages
- login
- patient dashboard
- doctor dashboard
- patient archive page
- daily health record page
- authorization page

### Phase 3: analytics and reports
- trend visualization
- report generation
- warning panel

### Phase 4: prediction module
- dataset preparation
- training pipeline
- inference API
- result storage
- frontend display

### Phase 5: refinement
- permission hardening
- usability improvements
- documentation
- deployment scripts

Do not begin with model training before basic CRUD and data flow are working.

---

## 9. Doctor-Patient Authorization Logic

Authorization is an important functional point of this system.

The coding agent should implement a clear permission mechanism:

- patients own their personal records
- doctors can only view records when authorization exists
- patients can grant and revoke access
- authorization actions should be logged
- prediction results follow the same visibility rule as health records

If simplified, implement:
- one patient can authorize one or more doctors
- each authorization has status and timestamps

---

## 10. Health Report Logic

The system should generate health reports based on:
- recent daily blood pressure records
- recent weight records
- medication adherence
- warning history
- prediction outputs

Reports should be:
- structured
- readable
- concise
- traceable to stored data

A report may include:
- summary of recent blood pressure trend
- summary of recent weight trend
- adherence summary
- risk reminder
- personalized suggestion template

Keep report generation deterministic and data-driven.

---

## 11. UI/UX Guidance

The UI should prioritize clarity and healthcare context.

### Recommended UI principles
- simple dashboard layout
- chart-first presentation for trends
- readable forms for daily input
- clear separation between archive records and daily monitoring
- obvious warning highlights
- obvious authorization status

Pages should not be overloaded.

For the graduation project, it is better to have:
- fewer pages
- clearer flows
- stronger coherence

than too many partially finished features.

---

## 12. Code Quality Expectations

The coding agent should maintain:

- clear module boundaries
- readable naming
- minimal duplication
- separate data access from business logic
- separate prediction logic from API layer
- configuration via environment variables
- migration-friendly database design
- comments only where useful

Avoid:
- hard-coded paths everywhere
- mixing training code into route handlers
- giant monolithic files
- frontend calling raw database logic

---

## 13. Documentation Expectations

The coding agent should produce developer-friendly documentation, including:

- project structure overview
- setup instructions
- database schema summary
- Synthea import instructions
- daily dataset generation logic
- model training instructions
- inference API usage
- deployment basics

The project should remain explainable to:
- supervisors
- teammates
- future maintainers
- examiners during defense

---

## 14. Research and Thesis Alignment

All implementation decisions should support the thesis narrative below:

This project builds a personal health management system for continuous health archive integration and doctor-patient collaboration. Using Synthea-generated synthetic EHR data as the foundational medical record source, the system realizes unified management of patient profiles, encounter history, medication records, and health observations. On top of this foundation, a daily home monitoring dataset for blood pressure and weight is constructed to support trend prediction and warning. A machine learning module is integrated into the system to provide next-day trend estimation and abnormal risk reminders, thereby enhancing continuity and intelligence in personal health management.

The coding agent should ensure the codebase reflects this narrative.

---

## 15. Decision Heuristics

When uncertain, follow these rules:

- choose simplicity over sophistication
- choose completeness over excessive novelty
- choose modularity over clever shortcuts
- choose explainability over black-box complexity
- choose system coherence over isolated model performance

If two options are both valid, prefer the one that:
- is easier to explain in a graduation defense
- better supports the thesis structure
- reduces implementation risk

---

## 16. Final Reminder for Agent Behavior

Always remember:

- this is a **health management system with an embedded prediction module**
- **Synthea is the base medical archive source**
- **home daily records are the prediction data source**
- **the database and system workflow come first**
- **the model is a value-added module, not the entire project**

Do not drift into building a pure ML benchmark project.

Do not drift into building a hospital-scale enterprise system.

Build a coherent, usable, explainable graduation design system.
