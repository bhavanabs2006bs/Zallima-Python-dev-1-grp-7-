import os
import json
import time
from datetime import datetime
from ..core.celery_app import celery_app
from ..processors.image_processor import ImageProcessor
from ..core.config import settings
from sqlalchemy import create_engine, text


engine = create_engine(settings.DATABASE_URL)


@celery_app.task(bind=True, name="process_media")
def process_media_task(self, job_id: str, input_path: str, operation: str):
    try:
        _update_status(job_id, "processing")

        start_time = time.time()
        output_files = []

        if input_path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")):
            processor = ImageProcessor()
            os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

            if operation == "resize":
                output_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_resized.jpg")
                processor.resize(input_path, output_path, width=800, height=600)
                output_files.append(output_path)
            elif operation == "compress":
                output_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_compressed.jpg")
                processor.compress(input_path, output_path, quality=70)
                output_files.append(output_path)
            elif operation == "thumbnail":
                output_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_thumb.jpg")
                processor.create_thumbnail(input_path, output_path, size=(200, 200))
                output_files.append(output_path)
            elif operation == "watermark":
                output_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_watermarked.jpg")
                processor.add_watermark(input_path, output_path, text="PROCESSED")
                output_files.append(output_path)
            else:
                output_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_processed.jpg")
                processor.resize(input_path, output_path, width=800, height=600)
                output_files.append(output_path)
        else:
            output_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_copy{os.path.splitext(input_path)[1]}")
            os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
            import shutil
            shutil.copy2(input_path, output_path)
            output_files.append(output_path)

        elapsed = int((time.time() - start_time) * 1000)
        _update_status(job_id, "completed", output_files=json.dumps(output_files))
        return {"job_id": job_id, "status": "completed", "files": output_files, "time_ms": elapsed}

    except Exception as e:
        _update_status(job_id, "failed", error=str(e))
        return {"job_id": job_id, "status": "failed", "error": str(e)}


def _update_status(job_id: str, status: str, output_files: str = None, error: str = None):
    with engine.connect() as conn:
        updates = {"status": status, "jid": job_id}
        sql = "UPDATE media_jobs SET status=:status"
        if output_files:
            sql += ", output_files=:of"
            updates["of"] = output_files
        if status in ("completed", "failed"):
            sql += ", completed_at=:ca"
            updates["ca"] = datetime.now()
        if error:
            sql += ", error_message=:em"
            updates["em"] = error
        sql += " WHERE job_id=:jid"
        conn.execute(text(sql), updates)
        conn.commit()
