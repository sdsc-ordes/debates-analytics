import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rq.job import Job
    from services.mongo import MongoManager

class JobReporter:
    def __init__(self, media_id: str, mongo: "MongoManager", job: "Job", logger: logging.Logger):
        self.media_id = media_id
        self.mongo = mongo
        self.job = job
        self.logger = logger

    def report_status_change(self, status: str, step_name: str = None):
        """
        [Heavyweight] Updates MongoDB and Redis. Use for State Transitions.
        """
        self.logger.info(f"media_id={self.media_id} - Status changed to: '{status}'")

        # 1. Update Redis (for immediate UI polling)
        self.job.meta['status'] = status
        self.job.save_meta()

        # 2. Update Mongo (for persistence)
        update_payload = {"status": status}

        # Suggestion: Track the timeline of steps in Mongo
        if step_name:
            # Pushes a record into a 'history' array in Mongo
            # This answers "How long did transcription take?" later.
            self.mongo.add_processing_step(self.media_id, step_name)

        self.mongo.update_processing_status(
            media_id=self.media_id,
            status=status
        )

    def mark_failed(self, error: Exception):
        """
        Final failure state.
        """
        self.logger.exception(f"media_id={self.media_id} - CRITICAL: Job failed.")
        # ... existing failure logic ...
