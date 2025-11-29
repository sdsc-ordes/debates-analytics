import os
import shutil
import uuid
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

TEMP_BASE = "/tmp/processing"

@contextmanager
def temp_workspace():
    """
    Creates a unique temporary directory for a specific job.
    Automatically cleans it up when the 'with' block exits,
    even if an error occurs.
    """
    job_uid = str(uuid.uuid4())
    work_dir = os.path.join(TEMP_BASE, job_uid)

    os.makedirs(work_dir, exist_ok=True)
    logger.info(f"Created temp workspace: {work_dir}")

    try:
        yield work_dir
    finally:
        # This runs no matter what happens inside the 'with' block
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
            logger.info(f"Cleaned up workspace: {work_dir}")
