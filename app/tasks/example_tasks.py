import time
from app.celery_app import celery_app


@celery_app.task
def long_running_task(duration: int) -> str:
    time.sleep(duration)
    return f"Task completed after {duration} seconds"
