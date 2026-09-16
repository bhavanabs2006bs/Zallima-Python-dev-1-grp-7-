FROM python:3.11-slim

WORKDIR /app

COPY project1_etl_pipeline/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY project1_etl_pipeline ./project1_etl_pipeline

CMD ["python", "-m", "project1_etl_pipeline.main", "run"]