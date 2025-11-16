import sys
import logging
import boto3
from typing import List
from botocore.exceptions import ClientError
from mediaworkers.config import (S3_SERVER, S3_ACCESS_KEY, S3_SECRET_KEY,
   S3_BUCKET_NAME, MARKER_FILENAME, STATE_FILENAME)

logger = logging.getLogger(__name__)

# --- S3 Client Initialization ---

class s3Manager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=S3_SERVER,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )
        self.bucket_name = S3_BUCKET_NAME
        logger.info("S3 client initialized successfully.")

    def download_file(self, s3_key: str, local_path: str):
        """Downloads a file from S3 to a local path."""
        logger.info(f"Downloading file from S3: {s3_key}...")
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Download of {s3_key} successful to {local_path}.")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"S3 Object not found: {s3_key}")
                raise FileNotFoundError(f"Object not found at {s3_key}")
            raise

    def upload_file(self, local_path: str, s3_key: str):
        """Uploads a local file to S3."""
        logger.info(f"Uploading file to S3: {s3_key}...")
        self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
        logger.info(f"Upload of {s3_key} successful.")

    def delete_object(self, object_key):
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)

    def find_new_jobs(self) -> List[str]:
        """Lists all top-level prefixes that contain the job marker file."""
        marker_keys = []
        try:
            # List top-level prefixes (CommonPrefixes are returned when Delimiter is used)
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='',
                Delimiter='/'
            )

            if 'CommonPrefixes' in response:
                logger.debug(f"Found {len(response['CommonPrefixes'])} top-level prefixes to check.")

                for prefix_data in response['CommonPrefixes']:
                    job_prefix = prefix_data['Prefix'] # e.g., '12345-job-id/'

                    # Construct the full marker key path: {job_id}/media/{MARKER_FILENAME}
                    marker_key = f"{job_prefix}media/{MARKER_FILENAME}"

                    # Check for the existence of the specific marker file using head_object
                    try:
                        self.s3_client.head_object(Bucket=self.bucket_name, Key=marker_key)
                        marker_keys.append(marker_key)
                        logger.info(f"SUCCESS: Marker found at {marker_key}")

                    except ClientError as e:
                        # 404 is expected if the marker isn't there; ignore it.
                        if e.response['Error']['Code'] != '404':
                            logger.error(f"S3 Head Object Error ({job_prefix}): {e}")
            else:
                logger.debug("No top-level prefixes (potential job folders) found.")

        except Exception as e:
            logger.error(f"Error listing S3 prefixes: {e}")

        return marker_keys

    def get_state_key(self, job_id: str) -> str:
        """Returns the S3 key path for the job state file."""
        # State file lives at the job's root: {job_id}/status.json
        return f"{job_id}/{STATE_FILENAME}"

    def load_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the job state JSON file from S3.
        Returns None if the file does not exist.
        """
        key = get_state_key(job_id)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = response['Body'].read().decode('utf-8')
            state = json.loads(data)
            logger.debug(f" [STATE] Loaded state for {job_id}: {state['status']}")
            return state
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f" [STATE] Error loading state for {job_id}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f" [STATE] Error decoding JSON for {job_id}: {e}")
            raise

    def save_job_state(self,, job_id: str, new_state: Dict[str, Any]):
        """
        Saves the updated job state JSON back to S3.
        """
        key = self.get_state_key(job_id)
        json_data = json.dumps(new_state, indent=2)

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data,
                ContentType='application/json'
            )
            logger.info(f" [STATE] Saved state for {job_id}. Status: {new_state['status']}")
        except Exception as e:
            logger.error(f" [STATE] Error saving state for {job_id}: {e}")
