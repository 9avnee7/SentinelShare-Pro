from app.tasks.worker import celery_app

@celery_app.task
def test_scan_task(filename: str):
    print(f"Scanning file: {filename}")
    return f"Scanned {filename} successfully"
