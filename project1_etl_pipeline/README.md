# Enterprise ETL Pipeline & Data Warehouse Synchronizer

## Overview
A resilient, automated Data Engineering pipeline that extracts business data from multiple APIs, transforms and cleans the data, and loads it into a centralized Data Warehouse.

## Features
- Multi-Source Extraction (Salesforce, Stripe)
- Pydantic data validation
- Upsert logic for incremental loads
- Comprehensive error handling & logging
- Unit tests with Pytest

## Quick Start
```bash
pip install -r requirements.txt
python -m project1_etl_pipeline run
```

## Testing
```bash
pytest tests/ -v
```
