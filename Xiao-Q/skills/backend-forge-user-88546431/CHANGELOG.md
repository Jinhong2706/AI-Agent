# Changelog

## v0.1.0

Productized Backend Forge as a runnable forge skill baseline.

### Runtime Surface

- Added `VERSION` and release metadata.
- Added project root detection for empty, Spring Boot, FastAPI, Django, generic backend, and non-backend workspaces.
- Added deterministic task route golden tests.
- Added minimal session, gate, output, and release validation scripts.

### Governance

- Connected backend tracks to the shared forge controller discipline: requirements, architecture/data/security confirmation, implementation gates, and test closure.
- Added release validation as the required local acceptance command.
- Kept backend-specific architecture leadership A0-A7 and data/security/testing rules as adapter behavior.
