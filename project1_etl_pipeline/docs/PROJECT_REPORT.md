# Project Report: Enterprise ETL Pipeline & Data Warehouse Synchronizer

**Author (reported by):** Code review agent
**Date:** 2026-08-29
**Scope:** `project1_etl_pipeline`

---

## 1. Executive Summary

The project is a layered, mock-driven ETL pipeline that extracts business records from
two sources (**Salesforce** and **Stripe**), validates and normalizes them via
**Pydantic v2**, and upserts them into a central data warehouse (SQLite default,
PostgreSQL support via SQLAlchemy). The codebase is cleanly separated into
`extractors/`, `transformers/`, `loaders/`, `models/`, and `utils/`, ships with a CLI
and an Airflow DAG, and includes a small pytest suite.

**Verdict:** A well-organized learning/reference implementation of a production-style
ETL pipeline. The core structure, validation, upsert, retry, logging, and job-tracking
patterns are solid. The main gaps are the **mock data sources**, **lack of real
credentials/config management**, and **schema-vs-runtime unit mismatches** (details in
§6).

---

## 2. Repository Overview

| Metric | Value |
|---|---|
| Language | Python 3.9+ |
| Dependencies | pandas, pydantic, python-dotenv, sqlalchemy, psycopg2-binary, tenacity, boto3, pytest, httpx |
| Source files (`.py`) | 23 (across 6 packages + `main.py` + `dags/` + `tests/`) |
| Tests | 9 (extractors 6, transformers 2, loaders 1) |
| Database | SQLite (default) / PostgreSQL |
| Orchestration | Apache Airflow DAG (standalone) |

---

## 3. Architecture & Design Assessment

**Strengths:**

- **Clean separation of concerns** — extract/transform/load modules are independent and
  individually testable.
- **Abstract base extractor** (`BaseExtractor`) centralizes pagination, retry
  (`tenacity`), and rate-limit throttling — new sources only implement
  `authenticate()` and `extract_page()`.
- **Schema-driven validation** — Pydantic models protect the warehouse from malformed
  input and centralize the contract between sources and storage.
- **Idempotent loading** — `UNIQUE(source, source_id)` + `ON CONFLICT DO UPDATE` makes
  re-runs safe (upsert).
- **Auditability** — every run writes an `etl_jobs` audit row with status and record
  counts, queryable via CLI `history`.

**Weaknesses / Risks:**

- Mock extractors give the **illusion of completeness**; production wiring requires
  real OAuth (Salesforce) and key-based (Stripe) API clients.
- The Airflow DAG is **not yet a real DAG object** — it is a plain function and needs
  `DAG`/`PythonOperator`/`schedule_interval` scaffolding.
- No configuration layer — credentials and page counts are hardcoded (with `dotenv`
  already available but unused).

---

## 4. Detailed Component Findings

### 4.1 Models (`models/schemas.py`)

| Check | Status | Notes |
|---|---|---|
| Pydantic v2 models | ✅ | `BaseModel`, `Field` constraints used |
| `amount` validation | ✅ | `ge=0` enforces non-negative cents |
| `currency` validation | ✅ | `min_length=3, max_length=3` |
| Zendesk schema present | ✅ | Ready for future source |
| Defaults on mutable field | ⚠️ | `TransformResult.errors: List[str] = []` and `UnifiedRecord.metadata: dict = {}` use mutable defaults — legal in Pydantic v2 (deep-copied), but flagged by some linters |

### 4.2 Extractors

| Check | Status | Notes |
|---|---|---|
| Pagination loop | ✅ | Handles `next_cursor`, empty pages, `max_pages` |
| Retry | ✅ | 3 attempts, exponential backoff 1–5 s |
| Rate limit | ✅ | Configurable delay per page |
| Real auth | ❌ | Mock tokens only |
| Real API calls | ❌ | Randomized mock record generation |
| `since` param | ⚠️ | `extract_contacts/extract_transactions` accept `since` but ignore it |

### 4.3 Transformer (`transformers/data_transformer.py`)

| Check | Status | Notes |
|---|---|---|
| Validation before load | ✅ | Pydantic per record |
| Error isolation | ✅ | Per-record try/except; counts and errors tracked |
| Normalization | ✅ | Unified record structure with source-specific metadata |
| Amount units | ⚠️ | Kept as cents in DB, converted to dollars only in DataFrame helper — document and stay consistent |
| Stats consistency | ⚠️ | In `transform_stripe`, failures increment `stats["failed"]` but not `stats["errors"]` (inconsistent with `transform_salesforce`) |

### 4.4 Loader (`loaders/warehouse_loader.py`)

| Check | Status | Notes |
|---|---|---|
| Table creation | ✅ | `CREATE TABLE IF NOT EXISTS` for both tables |
| Upsert | ✅ | Platform-specific `ON CONFLICT` (SQLite/PG) |
| Job lifecycle | ✅ | create → update with status/completed_at |
| Transaction safety | ✅ | Per-connection commit after batch |
| FK constraint | ⚠️ | `etl_job_id` is a plain column — no actual FOREIGN KEY constraint |
| MySQL compatibility | ❌ | `ON CONFLICT` not supported (needs `ON DUPLICATE KEY UPDATE`) |

### 4.5 Utils

| Check | Status | Notes |
|---|---|---|
| Logger | ✅ | Console + optional file, auto-creates dirs |
| S3 handler | ✅ | JSON upload/download under `raw/<source>/<date>/` |
| S3 credentials | ⚠️ | Relies on Boto3 default chain or explicit args (fine) |
| `httpx` dep | ⚠️ | Declared in requirements but unused — likely planned for real API calls |

### 4.6 CLI (`main.py`)

- Two commands: `run` and `history`, both with configurable `--db-url`.
- One inconsistency: the mock job is created with `DataSource.SALESFORCE` even though
  the data contains both Salesforce **and** Stripe records — the audit attribution is
  wrong/stale (same issue in the DAG).

---

## 5. Test Coverage Report

```
tests/test_extractors.py      6 tests  (Salesforce auth/page/all, Stripe auth/page/all)
tests/test_transformers.py    2 tests  (SF transform, Stripe transform)
tests/test_loaders.py         1 test   (job create + upsert)

Total: 9 tests
```

| Area | Covered? | Gaps |
|---|---|---|
| Extract pages pagination | ✅ | No test for `max_pages` cap, empty-page stop |
| Retry behavior | ❌ | `tenacity` retry path untested |
| Upsert idempotency | ❌ | No test that re-inserting same `(source, source_id)` updates instead of duplicating |
| Job finalization | ❌ | `update_job_status` untested |
| History/count queries | ❌ | Untested |
| S3 handler | ❌ | No tests (needs moto/mock) |

**Recommendation:** add tests for upsert idempotency, `update_job_status`, pagination
stop conditions, and job-history queries. Estimated current coverage ≈ **60–70%** of
statements.

---

## 6. Key Issues & Recommendations

### Critical / must-fix for production
1. **Real API integration** — replace mock generators with actual HTTP clients
   (Salesforce REST OAuth2 + SOQL; Stripe REST paging via `starting_after`). `httpx` is
   already in requirements, suggesting that was the plan.
2. **Secrets management** — move all credentials to environment variables or a `.env`
   file (load via `python-dotenv`, already included). Never hardcode keys.
3. **Correct job/cause attribution** — `create_etl_job(DataSource.SALESFORCE)` labels a
   mixed SF+Stripe run as Salesforce-only. Use a per-source job or a distinct
   "combined"/batch source value.

### Important / should-fix
4. **Make the DAG a real DAG** — wrap `run_etl_pipeline` in `DAG` + `PythonOperator`
   with a `schedule_interval`, `catchup=False`, and retries.
5. **Config module** — centralize `MAX_PAGES`, default DB URL, and per-source settings.
6. **Unit consistency** — standardize amounts (store cents everywhere or convert at the
   boundary once) and document it.
7. **Transformer stats parity** — append to `stats["errors"]` in `transform_stripe` too.

### Minor / nice-to-have
8. Add a `FOREIGN KEY (etl_job_id)` constraint and indexes on `(source, source_id)`.
9. DB-portable upsert helper (dialect-aware) for MySQL compatibility.
10. Wire `S3Handler` as a raw-landing layer between extract and transform.
11. Implement `since`/watermark incremental extraction.
12. Add a `.gitignore` for `venv/`, `__pycache__/`, `*.db`, and `logs/`.

---

## 7. Data Flow Verification (Manual Run Trace)

1. `WarehouseLoader.create_tables()` creates `etl_jobs` + `unified_records`.
2. Salesforce extractor produces mock contacts (2 pages); Stripe produces mock
   transactions (2 pages).
3. `DataTransformer` validates each raw record and emits `UnifiedRecord` dicts.
4. `upsert_records` inserts rows; on re-run, matching `(source, source_id)` rows are
   **updated** rather than duplicated.
5. Job row status → `completed`, with `records_extracted` and `records_loaded` set.

---

## 8. Conclusion

This is a strong foundation — the project demonstrates the correct mental model for
ETL engineering: typed contracts, defensive retry/throttle, idempotent load, audit
jobs, and unit tests. It is immediately runnable in "demo mode" because of the mock
extractors, which makes it an excellent learning artifact or template.

The next professional milestone is replacing the mocks with real integrations,
introducing environment-based configuration, and hardening the DAG + test suite
(§5–§6). No blocker prevents that evolution — the seams are already in the right
places.