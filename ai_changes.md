COMMIT_MESSAGE: Add monthly order status totals report

## Features Added
- Added `GET /api/v1/reports/monthly`, aggregating orders created in the last 30 days by status.
- Each status total includes `order_count` and the summed `total_amount`.

## Files Modified
- `app/api/v1/router.py` — registered the reports router.
- `app/core/config.py` — loads the job-specific environment file and reads the database URL from the environment.
- `app/core/database.py` — normalizes the resolved async MySQL URL for the existing synchronous SQLAlchemy engine.
- `.env.example` — updated the configured database URL.
- `docker-compose.yml` — updated configured database URLs.
- `requirements.txt` — added aiomysql and pytest dependencies.
- `.gitignore` — excludes the job-specific secrets file and local tool artifacts.

## Files Added
- `app/api/v1/reports.py` — monthly report HTTP endpoint.
- `app/services/report_service.py` — grouped 30-day order aggregation query.
- `app/schemas/report.py` — monthly status total response schema.
- `tests/test_reports.py` — endpoint aggregation coverage.

## Secrets Extracted
- `DATABASE_URL` -> written to `.env_0afcde1f6be381c2`.
- `MYSQL_ROOT_PASSWORD` -> written to `.env_0afcde1f6be381c2`.
- `MYSQL_DATABASE` -> written to `.env_0afcde1f6be381c2`.
- `MYSQL_USER` -> written to `.env_0afcde1f6be381c2`.
- `MYSQL_PASSWORD` -> written to `.env_0afcde1f6be381c2`.

## DB URLs Resolved
- `mysql+pymysql://orders_user:orders_password@localhost:3306/orders_db` -> `mysql+aiomysql://myuser:mypassword@localhost:3306/gen_7bc532ef5bfd`.
- `mysql+pymysql://orders_user:orders_password@mysql:3306/orders_db` -> `mysql+aiomysql://myuser:mypassword@localhost:3306/gen_7bc532ef5bfd_1`.
- `sqlite:///:memory:` -> `sqlite:///:memory:`.

## Test Results Summary
- 11 PASSED, 0 FAILED, 0 SKIPPED.
- Real Uvicorn boot verified at `http://localhost:26046/health`.
