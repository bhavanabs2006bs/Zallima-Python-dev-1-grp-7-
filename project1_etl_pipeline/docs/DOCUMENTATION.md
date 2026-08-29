# Enterprise ETL Pipeline & Data Warehouse Synchronizer

Technical documentation for the `project1_etl_pipeline` package.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Components](#components)
   - [Models / Schemas](#models--schemas)
   - [Extractors](#extractors)
   - [Transformers](#transformers)
   - [Loaders](#loaders)
   - [Utils](#utils)
7. [Data Flow](#data-flow)
8. [Database Schema](#database-schema)
9. [Scheduling with Airflow](#scheduling-with-airflow)
10. [Testing](#testing)
11. [Configuration & Environment](#configuration--environment)
12. [Extending the Pipeline](#extending-the-pipeline)

---

## Overview

A resilient, automated data engineering pipeline that:

- Extracts business data from multiple API sources (**Salesforce**, **Stripe**)
- Validates and normalizes data with **Pydantic v2** schemas
- Transforms raw records into a unified warehouse format
- Loads transformed records into a centralized data warehouse using **upsert** logic (insert-or-update)
- Tracks every run as an **ETL job** for auditability and monitoring
- Provides an **Apache Airflow DAG** for scheduled orchestration

### Key Features

| Feature | Description |
|---|---|
| Multi-source extraction | Salesforce contacts + Stripe transactions |
| Data validation | Pydantic `BaseModel` schemas with field constraints |
| Incremental loads | `UNIQUE(source, source_id)` upsert via `ON CONFLICT DO UPDATE` |
| Resilience | `tenacity` retry with exponential backoff on extraction |
| Rate limiting | Configurable delay between API page requests |
| Observability | Structured logging to console and file |
| Testing | Unit tests for extractors, transformers, and loaders (pytest) |
| Orchestration | Standalone Airflow DAG (`run_etl_pipeline`) |

> **Note:** Current extractors use **mock data generators**. No real API credentials are
> required to run the pipeline end-to-end.

---

## Architecture

The pipeline follows the classic **ELT/ETL** three-stage pattern:

```
                    +-------------------+
                    |  API SOURCES      |
                    |  (Salesforce,     |
                    |   Stripe)         |
                    +---------+---------+
                              |
                              v
   +-------------------------------------------------+
   |  EXTRACT  (extractors/)                         |
   |  - BaseExtractor: pagination + retry + throttle |
   |  - SalesforceExtractor / StripeExtractor        |
   +-------------------------------------------------+
                              |
                              v
   +-------------------------------------------------+
   |  TRANSFORM (transformers/)                      |
   |  - Pydantic validation                         |
   |  - Normalize to UnifiedRecord                  |
   |  - pandas helpers for analysis                 |
   +-------------------------------------------------+
                              |
                              v
   +-------------------------------------------------+
   |  LOAD (loaders/)                               |
   |  - WarehouseLoader: create tables, upsert,     |
   |    job tracking                                 |
   +-------------------------------------------------+
                              |
                              v
   +-------------------------------------------------+
   |  DATA WAREHOUSE                                 |
   |  (SQLite by default, PostgreSQL supported)      |
   |  tables: etl_jobs, unified_records              |
   +-------------------------------------------------+
```

---

## Project Structure

```
project1_etl_pipeline/
├── __init__.py                # Package metadata (version, author)
├── __main__.py                # Enables `python -m project1_etl_pipeline`
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── README.md                  # Quick-start readme
├── docs/
│   ├── DOCUMENTATION.md        # This file
│   └── PROJECT_REPORT.md       # Analysis & assessment report
├── dags/
│   └── etl_dag.py             # Apache Airflow DAG (standalone)
├── extractors/
│   ├── base_extractor.py      # Abstract base class w/ pagination, retry, throttle
│   ├── salesforce_extractor.py# Salesforce contact mock extractor
│   └── stripe_extractor.py    # Stripe transaction mock extractor
├── transformers/
│   └── data_transformer.py    # Validates + normalizes raw → UnifiedRecord
├── loaders/
│   └── warehouse_loader.py    # SQLAlchemy persistence, upsert, job tracking
├── models/
│   └── schemas.py             # Pydantic models & enums
├── utils/
│   ├── logger.py              # Console + file logging setup
│   └── aws_utils.py           # S3 upload/download helper
└── tests/
    ├── test_extractors.py
    ├── test_transformers.py
    └── test_loaders.py
```

---

## Installation

### Prerequisites

- Python 3.9+
- `pip`

### Setup

```bash
# 1. Navigate to the project root
cd project1_etl_pipeline

# 2. (Recommended) Create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

> If the package folder is inside a git repo root, install it in development mode:
> ```bash
> pip install -e .
> ```

---

## Usage

### CLI

Run the full ETL pipeline:

```bash
python -m project1_etl_pipeline run
```

Run with a custom database (e.g. PostgreSQL):

```bash
python -m project1_etl_pipeline run --db-url "postgresql+psycopg2://user:pass@localhost:5432/warehouse"
```

Show job history (last 10 jobs):

```bash
python -m project1_etl_pipeline history
```

Show help:

```bash
python -m project1_etl_pipeline --help
```

### Programmatic use

```python
from extractors import SalesforceExtractor, StripeExtractor
from transformers import DataTransformer
from loaders import WarehouseLoader
from models.schemas import DataSource, JobStatus

# Extract
sf = SalesforceExtractor("client_id", "client_secret")
sf.authenticate()
sf_records = sf.extract_all(max_pages=2)

stripe = StripeExtractor("sk_test_xxx")
stripe.authenticate()
stripe_records = stripe.extract_all(max_pages=2)

# Transform
transformer = DataTransformer()
unified = transformer.transform_salesforce(sf_records).data + \
          transformer.transform_stripe(stripe_records).data

# Load
loader = WarehouseLoader("sqlite:///etl_database.db")
loader.create_tables()
job_id = loader.create_etl_job(DataSource.SALESFORCE)
loaded = loader.upsert_records(unified, job_id)
loader.update_job_status(job_id, JobStatus.COMPLETED, len(unified), loaded)
```

---

## Components

### Models / Schemas

Defined in `models/schemas.py` using **Pydantic v2**.

#### Enums

| Enum | Members | Values |
|---|---|---|
| `JobStatus` | PENDING, RUNNING, COMPLETED, FAILED | `"pending"`, `"running"`, `"completed"`, `"failed"` |
| `DataSource` | SALESFORCE, STRIPE, ZENDESK | `"salesforce"`, `"stripe"`, `"zendesk"` |

#### Source-specific models

| Model | Purpose | Key fields |
|---|---|---|
| `SalesforceContact` | Validated contact record | `id`, `email`, `first_name`, `last_name`, `company`, `phone`, `created_at`, `updated_at` |
| `StripeTransaction` | Validated payment record | `id`, `customer_id`, `amount` (cents, `>= 0`), `currency` (3 chars), `status`, `description`, `created_at` |
| `ZendeskTicket` | Ticket model (schema available, extractor not yet implemented) | `id`, `subject`, `description`, `status`, `priority`, `requester_id`, `created_at`, `updated_at` |

#### Warehouse models

| Model | Purpose |
|---|---|
| `UnifiedRecord` | Canonical warehouse row combining all sources |
| `ETLJob` | Run/audit record for one pipeline execution |
| `TransformResult` | Result object returned by transformers (success, counts, errors, data) |

### Extractors

#### `BaseExtractor` (`extractors/base_extractor.py`)

Abstract base class with:

- `authenticate()` — abstract; source-specific auth.
- `extract_page(cursor, page_size)` — abstract; returns `{"records": [...], "next_cursor": str|None}`.
- `extract_all(max_pages=10)` — concrete pagination loop:
  - Enforces `rate_limit_delay` (seconds) between pages.
  - Decorated with `@retry(stop=after 3 attempts, wait_exponential(min=1s, max=5s))`.
  - Stops when `max_pages` reached, `next_cursor` is `None`, or an empty page is returned.

#### `SalesforceExtractor` (`extractors/salesforce_extractor.py`)

- Mocks OAuth-style authentication (sets a fake `access_token`).
- Generates random mock contact records (`Id`, `Email`, `FirstName`, `LastName`, `Company`, `Phone`, `CreatedDate`, `LastModifiedDate`).
- Provides `extract_contacts(since=None)` convenience wrapper.

#### `StripeExtractor` (`extractors/stripe_extractor.py`)

- Mock authentication only.
- Generates random mock transaction records (`id`, `customer`, `amount`, `currency`, `status`, `description`, `created`).
- Provides `extract_transactions(since=None)` convenience wrapper.

### Transformers

#### `DataTransformer` (`transformers/data_transformer.py`)

- `transform_salesforce(raw)` → validates each record into `SalesforceContact`, then normalizes to `UnifiedRecord`. Returns `TransformResult`.
- `transform_stripe(raw)` → validates into `StripeTransaction`, then normalizes to `UnifiedRecord`. Returns `TransformResult`.
- `transform_to_dataframe(records)` → converts unified records to a `pandas.DataFrame`; coerces `created_at`/`updated_at` to datetimes and converts `amount` from **cents to dollars**.
- `get_stats()` → running `{"processed", "failed", "errors"}` counters.

Field mapping / standardization:

| Source field | Unified field |
|---|---|
| Salesforce `Id` | `source_id`, `source=salesforce` |
| Salesforce `Email` | `email` |
| Salesforce `FirstName + LastName` | `name` ("first last") |
| Salesforce `Company` | `company` |
| Stripe `id` | `source_id`, `source=stripe` |
| Stripe `description` | `name` |
| Stripe `amount` (cents) | `amount` (kept in cents for persistence) |
| Stripe `customer` | `metadata.customer_id` |
| Salesforce `Phone` | `metadata.phone` |

### Loaders

#### `WarehouseLoader` (`loaders/warehouse_loader.py`)

Handles all persistence via **SQLAlchemy Core** (raw SQL `text()` statements).

Methods:

| Method | Description |
|---|---|
| `create_tables()` | Creates `etl_jobs` and `unified_records` tables if they don't exist. |
| `create_etl_job(source)` | Inserts a running job, returns its `id`. |
| `upsert_records(records, etl_job_id)` | Batch inserts/updates each record; returns count loaded. Uses `ON CONFLICT(source, source_id) DO UPDATE`. |
| `update_job_status(job_id, status, ...)` | Finalizes a job (sets `completed_at` for COMPLETED/FAILED, optional `error_message`). |
| `get_job_history(limit=10)` | Returns recent jobs as dicts. |
| `get_record_count(source=None)` | Counts rows in `unified_records`, optionally filtered by source. |

> **Note:** `ON CONFLICT` is PostgreSQL/SQLite syntax. For MySQL/MariaDB, it would need
> to be swapped for `INSERT ... ON DUPLICATE KEY UPDATE`.

### Utils

#### `logger.py`

- `setup_logger(name, log_file=None, level=INFO)` — prepares a logger with a simple console formatter and an optional detailed file handler (creates parent directories automatically).
- `get_logger(name)` — returns a named logger (used by other modules).

#### `aws_utils.py`

Optional AWS S3 integration:

- `S3Handler.upload_json(data, source, extraction_date)` — uploads raw data to
  `s3://<bucket>/raw/<source>/<YYYY-MM-DD>/data.json`, returns the object key.
- `S3Handler.download_json(key)` — downloads and decodes a JSON object.

Credentials can be passed explicitly or resolved via the default Boto3 chain
(env vars like `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`, AWS profile, IAM role).

---

## Data Flow

1. **CLI / DAG invokes** `run_full_pipeline(db_url)` or `run_etl_pipeline()`.
2. **Extraction** — Salesforce and Stripe extractors authenticate and pull pages of
   raw records (2 pages in the default run).
3. **Transformation** — raw records are validated with Pydantic and normalized into
   `UnifiedRecord` dicts.
4. **Load** — an ETL job row is created; each unified record is upserted into
   `unified_records`; the job is marked `completed`.
5. **Audit** — job history is queryable via CLI `history` or `get_job_history()`.

---

## Database Schema

### `etl_jobs`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `source` | VARCHAR(50) NOT NULL | Data source name |
| `status` | VARCHAR(20) DEFAULT 'pending' | pending/running/completed/failed |
| `records_extracted` | INTEGER DEFAULT 0 | |
| `records_loaded` | INTEGER DEFAULT 0 | |
| `started_at` | TIMESTAMP | default now |
| `completed_at` | TIMESTAMP | set on completion/failure |
| `error_message` | TEXT | failure reason |

### `unified_records`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `source` | VARCHAR(50) NOT NULL | part of unique key |
| `source_id` | VARCHAR(100) NOT NULL | part of unique key |
| `email` | VARCHAR(255) | nullable |
| `name` | VARCHAR(200) | nullable |
| `company` | VARCHAR(200) | nullable |
| `amount` | REAL | nullable |
| `currency` | VARCHAR(10) | nullable |
| `status` | VARCHAR(50) | nullable |
| `created_at` | TIMESTAMP | nullable |
| `updated_at` | TIMESTAMP | nullable |
| `metadata` | TEXT | JSON-encoded dict |
| `etl_job_id` | INTEGER | FK-like to `etl_jobs.id` |
| `loaded_at` | TIMESTAMP | default now |
| **UNIQUE** | | `(source, source_id)` |

---

## Scheduling with Airflow

`dags/etl_dag.py` exposes `run_etl_pipeline(database_url="sqlite:///etl_database.db")`.

To wire it into Airflow as a real DAG you would wrap it with `DAG`, `PythonOperator`,
a `schedule_interval`, and retries, e.g.:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG(
    "project1_etl_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    run_task = PythonOperator(
        task_id="run_etl",
        python_callable=run_etl_pipeline,
        op_kwargs={"database_url": "sqlite:///etl_database.db", "dal": 1},
    )
```

Currently the file is **standalone** (runnable via `python -m dags.etl_dag`) and
references the package through relative imports; place it in your Airflow `dags/`
folder together with the package installed in the Airflow environment.

---

## Testing

Run the full suite:

```bash
pytest tests/ -v
```

| File | Covers |
|---|---|
| `test_extractors.py` | Salesforce/Stripe `authenticate`, `extract_page`, `extract_all` |
| `test_transformers.py` | Salesforce/Stripe transform → success + record counts |
| `test_loaders.py` | Job creation, upsert of records (in-memory SQLite) |

---

## Configuration & Environment

The pipeline currently has **no runtime configuration file**; values are hardcoded
in `main.py` and `dags/etl_dag.py`:

- Mock credentials: `"mock_id"`, `"mock_secret"`, `"sk_test_mock"`
- Max pages: `2`
- Default DB: `sqlite:///etl_database.db`

Environmental configs to add for production:

```
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
STRIPE_SECRET_KEY=...
DATABASE_URL=postgresql+psycopg2://...
```

The `python-dotenv` dependency is already included, ready for a `.env`-based config.

---

## Extending the Pipeline

To add a new source (e.g., **Zendesk** — schema already exists):

1. Create `extractors/zendesk_extractor.py` subclassing `BaseExtractor`.
2. Implement `authenticate()` and `extract_page()`.
3. Add a transformer method (e.g., `transform_zendesk`) in `DataTransformer`.
4. Add the source to `DataSource` enum if not present (Zendesk already is).
5. Register the new extractor in `run_full_pipeline` in `main.py`.

Optionally integrate AWS S3 raw-data landing via `S3Handler` between extract and transform.

---

## Known Limitations

- Extractors return **mock data**; replace with real API calls for production.
- Stored amounts are in **cents** (`REAL`), but the DataFrame helper converts to
  dollars — keep units consistent.
- `ON CONFLICT` upsert works on SQLite/PostgreSQL only.
- The Airflow DAG is standalone and not yet fully wired with a `DAG`/`schedule_interval`.
- Real secrets should be injected via environment variables, never hardcoded.