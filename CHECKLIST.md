# CHECKLIST.md

## Phase 1 Completed
- [x] app starts without error
- [x] database migration setup added
- [x] /health endpoint implemented
- [x] login returns jwt
- [x] patient CRUD implemented

## Phase 1 Authorization Completed
- [x] patient can authorize doctor
- [x] doctor cannot access unauthorized patient
- [x] doctor can access authorized patient

## Phase 2 Medical Archive
- [ ] alembic upgrade head succeeds with archive tables
- [ ] Synthea import script runs successfully
- [ ] repeated import does not create uncontrolled duplicates
- [x] MIMIC-IV Demo conversion script added
- [x] MIMIC-IV data replacement documentation added
- [ ] imported encounters API works
- [ ] imported conditions API works
- [ ] imported medications API works
- [ ] imported observations API works
- [ ] unauthorized doctor cannot access imported patient archive
- [ ] README contains import instructions

## Code quality
- [ ] no hard-coded local paths
- [ ] config comes from environment variables
- [x] training code not mixed into route handlers
