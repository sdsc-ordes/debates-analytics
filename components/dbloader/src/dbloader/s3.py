import boto3
import os
from botocore.exceptions import NoCredentialsError, DataNotFoundError
from typing import List, Dict, Union
import logging

from dotenv import load_dotenv

load_dotenv()

S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_SERVER = os.getenv("S3_SERVER")
S3_FRONTEND_BASE_URL = os.getenv("S3_FRONTEND_BASE_URL")

S3_BUCKET_NAME=os.getenv("S3_BUCKET_NAME")
SUFFIX_SRT_ORIG="transcription_original.srt"
SUFFIX_SRT_EN="translation_original_english.srt"
SUFFIX_METADATA="metadata.yml"

print("bucket", S3_BUCKET_NAME)


class s3Manager:
    def __init__(self, prod=False):
        self.s3 = boto3.client(
            's3',
            endpoint_url=S3_SERVER,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )
        self.bucket_name = "debates"

    def get_s3_data(self, s3_path):
        response = self.s3.get_object(Bucket=self.bucket_name, Key=s3_path)
        data = response['Body'].read().decode('utf-8')
        return data

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

    def get_all_prefixed_files_data(self, prefix: str) -> Dict[str, Union[str, Exception]]:
        """
        The requested feature: Retrieves the content of all objects under a given prefix.

        Args:
            prefix: The S3 key prefix (e.g., 'videos/debate-001/').

        Returns:
            A dictionary where keys are the S3 object keys and values are the file content (string)
            or an Exception object if retrieval failed for a specific file.
        """
        all_data = {}
        object_keys = self.list_objects_by_prefix(prefix)

        for key in object_keys:
            try:
                # OPTIONAL: Skip if the key is just the 'directory' prefix itself
                if key == prefix and not key.endswith('/'):
                    continue

                content = self.get_s3_data(key)
                all_data[key] = content
            except ClientError as e:
                # Catch errors for individual files but continue processing others
                logging.error(f"Failed to fetch content for key: {key}. Error: {e.response['Error']['Code']}")
                all_data[key] = e  # Store the exception instead of content

        return all_data