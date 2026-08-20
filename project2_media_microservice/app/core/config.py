import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///media_jobs.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "media-uploads-bucket")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")

settings = Settings()
