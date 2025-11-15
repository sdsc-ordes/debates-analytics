import boto3
import os
import logging
from botocore.exceptions import NoCredentialsError, DataNotFoundError
from typing import List, Dict, Union

from dotenv import load_dotenv

load_dotenv()

S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_SERVER = os.getenv("S3_SERVER")
S3_FRONTEND_BASE_URL = os.getenv("S3_FRONTEND_BASE_URL")

S3_BUCKET_NAME="debates"
SUFFIX_SRT_ORIG="transcription_original.srt"
SUFFIX_SRT_EN="translation_original_english.srt"
SUFFIX_METADATA="metadata.yml"


class s3Manager:
    def __init__(self, prod=False):
        self.s3 = boto3.client(
            's3',
            endpoint_url=S3_SERVER,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )
        self.bucket_name = "debates"

    def get_presigned_url(self, object_key, expiration=3600):
        """
        Generate a presigned URL for an S3 object.
        """
        try:
            print(f"uploading data for s3 key {object_key}")
            response = self.s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_key,
                    "ResponseContentDisposition": f"attachment; filename={object_key}"
                },
                ExpiresIn=expiration,
            )
            frontend_url = response.replace(S3_SERVER, S3_FRONTEND_BASE_URL)
            return frontend_url
        except DataNotFoundError:
            print(f"s3 key not found: {object_key}")
        except NoCredentialsError:
            print("Credentials not available.")
            return None

    def list_objects_by_prefix(self, prefix: str) -> List[str]:
        """
        Lists object keys starting with the given prefix.
        Optimized for small results (< 1000 keys) by avoiding the paginator.

        Args:
            prefix: The S3 key prefix (e.g., 'path/to/directory/').

        Returns:
            A list of full object keys (paths).
        """
        keys = []
        # Use list_objects_v2 directly without the paginator
        response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

        if response.get('IsTruncated'):
             logging.warning(
                 f"S3 returned more than 1000 results for prefix '{prefix}'. "
                 "The current function is optimized for small lists and may be incomplete. "
                 "Consider switching back to the paginator."
             )

        if 'Contents' in response:
            # Filter out the 'directory' entry if it exists (which has a size of 0)
            for obj in response['Contents']:
                # Optional: You can add further checks here if needed, like obj['Size'] > 0
                keys.append(obj['Key'])

        logging.info(f"Found {len(keys)} objects with prefix '{prefix}' in bucket '{self.bucket_name}': {keys}")
        return keys

    def list_top_level_prefixes(self) -> List[str]:
        """
        Lists all top-level prefixes (job_ids) in the S3 bucket using the delimiter '/'.
        This returns what looks like folders at the root level.

        Returns:
            A list of top-level prefixes (e.g., 'job_id_1/', 'job_id_2/').
        """
        job_ids = []
        paginator = self.s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name, Delimiter='/')

        for page in pages:
            if 'CommonPrefixes' in page:
                for prefix_data in page['CommonPrefixes']:
                    # CommonPrefixes contains dictionaries like {'Prefix': 'job_id_1/'}
                    job_ids.append(prefix_data['Prefix'])

        logging.info(f"Found {len(job_ids)} top-level prefixes (job_ids) in bucket '{self.bucket_name}'.")
        return job_ids

    def get_presigned_upload_url(self, object_key: str, expiration: int = 3600) -> Union[str, None]:
        """
        Generate a presigned URL for uploading a file (PUT/UPLOAD).
        The client uses an HTTP PUT request with the file data to upload.
        """
        try:
            print(f"getting presigned upload URL for s3 key {object_key}")
            response = self.s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_key
                    # Note: No 'ResponseContentDisposition' is needed for uploads
                },
                ExpiresIn=expiration,
            )
            # Replace the S3 server URL with the frontend-accessible base URL if necessary
            frontend_url = response.replace(S3_SERVER, S3_FRONTEND_BASE_URL)
            return frontend_url
        except NoCredentialsError:
            print("Credentials not available for upload.")
            return None
        except Exception as e:
            print(f"Error generating presigned upload URL: {e}")
            return None
