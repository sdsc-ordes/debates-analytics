import boto3
import os
import logging
from botocore.exceptions import ClientError
from functools import lru_cache

# Setup Logging
logger = logging.getLogger(__name__)


class S3Manager:
    def __init__(self):
        self.access_key = os.getenv("S3_ACCESS_KEY")
        self.secret_key = os.getenv("S3_SECRET_KEY")
        self.server_url = os.getenv("S3_SERVER")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")

        if not all([self.access_key, self.secret_key, self.server_url]):
            logger.error("Missing S3 environment variables!")

        self.s3 = boto3.client(
            's3',
            endpoint_url=self.server_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def download_file(self, s3_key: str, local_path: str):
        """Used by Workers to download source files"""
        try:
            logger.info(f"Downloading {s3_key} -> {local_path}")
            self.s3.download_file(self.bucket_name, s3_key, local_path)
        except ClientError as e:
            logger.error(f"Failed to download {s3_key}: {e}")
            raise e

    def upload_file(self, local_path: str, s3_key: str):
        """Used by Workers to upload results"""
        try:
            logger.info(f"Uploading {local_path} -> {s3_key}")
            self.s3.upload_file(local_path, self.bucket_name, s3_key)
        except ClientError as e:
            logger.error(f"Failed to upload {s3_key}: {e}")
            raise e


@lru_cache()
def get_s3_manager() -> S3Manager:
    """
    Creates the manager once and caches it in memory.
    Acting like a Singleton, but that can be overridden in tests.
    """
    return S3Manager()
