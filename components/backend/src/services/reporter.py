import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rq.job import Job
    from services.mongo import MongoManager

class JobReporter:
    def __init__(
        self,
        media_id: str,
        mongo: "MongoManager",
        job: "Job",
        logger: logging.Logger
    ):
        self.media_id = media_id
        self.mongo = mongo
        self.job = job
        self.logger = logger

    def update(self, status: str, progress: str = None, metadata: dict = None):
        """
        Updates ALL 3 systems at once.
        """
        self.logger.info(f"Job {self.media_id}: {status}...")

        if progress:
            self.job.meta['progress'] = progress
            self.job.save_meta()

        self.mongo.update_processing_status(
            media_id=self.media_id,
            status=status,
            metadata=metadata,
        )

    def mark_failed(self, error: Exception):
        """
        Standard failure handler.
        """
        error_msg = str(error)

        self.logger.error(f"Job {self.media_id} FAILED: {error_msg}")

        self.job.meta['progress'] = 'failed'
        self.job.meta['error'] = error_msg
        self.job.save_meta()

        self.mongo.update_processing_status(
            media_id=self.media_id,
            status="failed",
            metadata={"error_message": error_msg}
        )
