
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY airflow ./airflow
COPY tests ./tests
COPY pytest.ini .

ENV PYTHONPATH=/app

CMD ["pytest", "-q"]

