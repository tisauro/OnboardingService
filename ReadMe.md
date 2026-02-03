# OnboardingService — IoT Device Onboarding & Provisioning Service

OnboardingService is a FastAPI-based backend that manages secure first-boot onboarding for IoT devices and provides an admin API to operate the provisioning lifecycle in AWS IoT Core.

At a glance, the service:
- Exposes a public device registration endpoint where a device presents a factory-installed bootstrap API key to obtain its own X.509 certificate and private key.
- Creates/attaches an AWS IoT Thing and policy, returning credentials to the device on first registration.
- Offers private admin endpoints to manage bootstrap keys and to view/revoke provisioned devices.
- Uses PostgreSQL for persistence and Alembic for database migrations.

## Objectives
- Ensure secure, one-time device onboarding using time-bound, revocable bootstrap keys.
- Centralize key lifecycle management (create, list, activate/deactivate, delete) for manufacturing batches or groups.
- Automate AWS IoT provisioning steps (Thing creation, certificate issuance/attachment, policy attachment).
- Provide operators with visibility and controls (list devices, revoke certificates) without direct AWS console access.
- Support repeatable deployments via configuration (`.env`) and migrations (Alembic).

## High-level Architecture
- API Layer: FastAPI application with separate public and private routers.
  - Public: device self-registration using a bootstrap key (`/public/v1/register`).
  - Private: admin management of bootstrap keys and devices (`/private/v1/admin/...`).
- Persistence: PostgreSQL accessed asynchronously; schema managed with Alembic.
- Cloud Integration: AWS IoT Core for device identity, certificates, and policies.
- Configuration: Pydantic `Settings` loaded from `.env` (see `app/core/settings.py`).


## Alembic commands

Full documentation can be found [here](https://alembic.sqlalchemy.org/en/latest/):

- Init (run once): `alembic init alembic` and in `alembic.ini` set `file_template = %%(epoch)s_%%(slug)s`.
- Create a migration: `alembic revision --autogenerate -m "create account table"`
- Apply latest: `alembic upgrade head`
- Partial revision identifier: `alembic upgrade ae1` (sufficiently unique prefix)
- Relative migration identifiers: `alembic upgrade +2`
- Info: `alembic current` and `alembic history --verbose`
- Downgrade: `alembic downgrade base` or `alembic downgrade <revision>`