import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rq.job import Job
    from services.mongo import MongoManager

class JobReporter:
    def __init__(self, media_id: str, mongo: "MongoManager", logger: logging.Logger, job: "Job" = None):
        self.media_id = media_id
        self.mongo = mongo
        self.logger = logger
        self.job = job

    def report_job_start(self, status: str, metadata: dict = None, job_id: str = None):
        """
        Updates MongoDB and Redis. Use for State Transitions.
        """
        self.logger.info(f"media_id={self.media_id} - Status changed to: '{status}'")

        # Update Redis/Job Meta
        self.job.meta['status'] = status
        self.job.save_meta()

        # Update MongoDB
        self.mongo.update_status_with_history(
            media_id=self.media_id,
            status=status,
            job_id=self.job.get_id(),
        )

    def report_status_change(self, status: str, metadata: dict = None):
        """
        Updates MongoDB and Redis. Use for State Transitions.
        """
        self.logger.info(f"media_id={self.media_id} - Status changed to: '{status}'")

        # Update Redis/Job Meta
        if self.job:
            self.job.meta['status'] = status
            self.job.save_meta()

        # Update MongoDB
        self.mongo.update_status_with_history(
            media_id=self.media_id,
            status=status,
            metadata=metadata,
        )

    def mark_failed(self, error: Exception):
        """
        Final failure state.
        """
        error_msg = str(error)

        self.logger.error(f"Job {self.media_id} FAILED: {error_msg}")

        if self.job:
            self.job.meta['progress'] = 'failed'
            self.job.meta['error'] = error_msg
            self.job.save_meta()

        self.mongo.update_status_with_history(
            media_id=self.media_id,
            status="failed",
            metadata={"error_message": error_msg}
        )
        self.logger.exception(f"media_id={self.media_id} - CRITICAL: Job failed.")