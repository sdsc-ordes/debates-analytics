import boto3
from dotenv import load_dotenv
import logging
from functools import lru_cache
from common.config import get_settings
from typing import List, Union, Dict, Any
from botocore.exceptions import NoCredentialsError, DataNotFoundError

# Setup Logging
logger = logging.getLogger(__name__)

load_dotenv()


class S3Manager:
    def __init__(self):
        settings = get_settings()

        self.access_key = settings.s3_access_key
        self.secret_key = settings.s3_secret_key
        self.server_url = settings.s3_server
        self.bucket_name = settings.s3_bucket_name
        self.s3_frontend_base_url = settings.s3_frontend_base_url

        if not all([self.access_key, self.secret_key, self.server_url]):
            logger.error("Missing S3 environment variables!")

        self.s3 = boto3.client(
            's3',
            endpoint_url=self.server_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

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
            frontend_url = response.replace(self.server_url, self.s3_frontend_base_url)
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
            for obj in response['Contents']:
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

            response["url"] = response["url"].replace(self.server_url, self.s3_frontend_base_url)

            logging.info(f"Returning external POST URL: {response['url']}")

            return response

        except NoCredentialsError:
            logging.error("Credentials not available for S3 POST.")
            return None
        except Exception as e:
            logging.error(f"Error generating presigned POST: {e}")
            return None


@lru_cache()
def get_s3_manager() -> S3Manager:
    """
    Creates the manager once and caches it in memory.
    Acting like a Singleton, but that can be overridden in tests.
    """
    return S3Manager()
