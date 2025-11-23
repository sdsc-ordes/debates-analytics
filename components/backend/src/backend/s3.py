import boto3
import os
import logging
from botocore.exceptions import NoCredentialsError, DataNotFoundError
from typing import List, Dict, Union, Any

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

MARKER_FILENAME=os.getenv("MARKER_FILENAME")


class s3Manager:
    def __init__(self, prod=False):
        self.s3 = boto3.client(
            's3',
            endpoint_url=S3_SERVER,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )
        self.bucket_name = S3_BUCKET_NAME

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
        Lists all top-level prefixes (media_ids) in the S3 bucket using the delimiter '/'.
        This returns what looks like folders at the root level.

        Returns:
            A list of top-level prefixes (e.g., 'media_id_1/', 'media_id_2/').
        """
        media_ids = []
        paginator = self.s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name, Delimiter='/')

        for page in pages:
            if 'CommonPrefixes' in page:
                for prefix_data in page['CommonPrefixes']:
                    # CommonPrefixes contains dictionaries like {'Prefix': 'media_id_1/'}
                    media_ids.append(prefix_data['Prefix'])

        logging.info(f"Found {len(media_ids)} top-level prefixes (media_ids) in bucket '{self.bucket_name}'.")
        return media_ids

    def get_presigned_post(self, object_key: str, expiration: int = 3600) -> Union[Dict[str, Any], None]:
        """
        Generates a presigned URL and fields for a client-side HTTP POST upload.
        The URL returned is adjusted to use the S3_FRONTEND_BASE_URL hostname.
        """
        try:
            logging.info(f"Generating presigned POST for key: {object_key}")

            conditions = [
                {"acl": "public-read"},
                {"bucket": self.bucket_name},
                ["starts-with", "$key", object_key],
                ["content-length-range", 1, 500 * 1024 * 1024],
                {"success_action_status": "201"},
            ]

            response = self.s3.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=object_key,
                Fields={
                    "acl": "public-read",
                    "success_action_status": "201"
                },
                Conditions=conditions,
                ExpiresIn=expiration
            )

            # CRITICAL ADJUSTMENT: Apply the same hostname substitution logic as get_presigned_url
            if S3_FRONTEND_BASE_URL and S3_SERVER:
                # The 'url' field contains the internal Docker hostname (S3_SERVER)
                # We replace it with the public hostname (S3_FRONTEND_BASE_URL)
                response["url"] = response["url"].replace(S3_SERVER, S3_FRONTEND_BASE_URL)

            logging.info(f"Returning external POST URL: {response['url']}")

            return response

        except NoCredentialsError:
            logging.error("Credentials not available for S3 POST.")
            return None
        except Exception as e:
            logging.error(f"Error generating presigned POST: {e}")
            return None

    def create_marker_file(self, media_id: str) -> bool:
        """
        Creates an empty marker file to signal a complete upload for the watcher service.
        Key: {media_id}/media/job_registered.txt
        """
        try:
            marker_key = f"{media_id}/media/{MARKER_FILENAME}"
            logging.info(f"Creating marker file at: {marker_key}")
            
            # Put a minimal (empty) object to act as the marker
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=marker_key,
                Body=b'', # Empty body is fine for a marker
                ContentType='text/plain',
            )
            return True
        except NoCredentialsError:
            logging.error("Credentials not available to create marker.")
            return False
        except Exception as e:
            logging.error(f"Error creating marker file for job {media_id}: {e}")
            return False
