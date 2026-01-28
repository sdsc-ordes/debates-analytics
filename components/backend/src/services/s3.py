import boto3
import os
from botocore.client import Config
from dotenv import load_dotenv
import logging
from functools import lru_cache
from config.settings import get_settings
from typing import List, Union, Dict, Any
from botocore.exceptions import (
    NoCredentialsError, DataNotFoundError, ClientError
)

logger = logging.getLogger(__name__)

load_dotenv()

class S3Manager:
    def __init__(self):
        settings = get_settings()
        self.access_key = settings.s3_access_key
        self.secret_key = settings.s3_secret_key
        self.bucket_name = settings.s3_bucket_name

        # 1. Internal Connection (Backend <-> Garage)
        self.server_url = settings.s3_server

        # 2. Signing URL (What the final receiver expects the Host header to be)
        # In Prod: This is 'garage:3900' (because Nginx rewrites headers)
        # In Local: This is 'localhost:3900' (because Browser sends headers)
        self.signing_url = settings.s3_signing_url

        # 3. Public URL (What the user clicks)
        self.public_url = settings.s3_public_url

        # ... checks ...

        # Internal Client (Uses S3_SERVER_URL)
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.server_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='garage',
            config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4'),
        )

        # Signer Client (Uses S3_SIGNING_URL)
        self.s3_signer = boto3.client(
            's3',
            endpoint_url=self.signing_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='garage',
            config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4')
        )

    def get_presigned_url(self, object_key, as_attachment=False, expiration=3600):
        """
        Generates a presigned URL for accessing an S3 object.

        This method employs a "Split-Horizon" signing strategy to handle Docker networking:
        1. Signs the URL using the internal Docker hostname (e.g., 'http://garage:3900').
           This matches the 'Host' header Nginx will spoof when proxying the request to S3.
        2. Swaps the internal hostname for the public-facing domain (e.g., 'https://debates...').
           This ensures the link is clickable by the user's browser.

        Args:
            object_key (str): The S3 key of the object.
            as_attachment (bool): If True, adds Content-Disposition header to force file download.
            expiration (int): Time in seconds before the link expires.

        Returns:
            str: A public-facing HTTPS URL with a valid internal signature.
        """
        # Generate URL using the SIGNING endpoint
        # The signature is now calculated for the correct expected Host
        try:
            params = {
                "Bucket": self.bucket_name,
                "Key": object_key,
            }
            if as_attachment:
                clean_filename = os.path.basename(object_key)
                params["ResponseContentDisposition"] = f'attachment; filename="{clean_filename}"'
            url = self.s3_signer.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )
            # Replace the Signing URL with the Public URL
            # This makes the link clickable for the user
            final_url = url.replace(self.signing_url, self.public_url)

            return final_url
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

        logging.debug(f"Found {len(keys)} objects with prefix '{prefix}' in bucket '{self.bucket_name}': {keys}")
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

        logging.debug(f"Found {len(media_ids)} top-level prefixes (media_ids) in bucket '{self.bucket_name}'.")
        return media_ids

    def get_presigned_post(self, object_key: str, expiration: int = 3600) -> Union[Dict[str, Any], None]:
        """
        Generates a presigned URL and fields for a client-side HTTP POST upload.
        The URL returned is adjusted to use the S3_PUBLIC_URL hostname.
        """
        try:
            logging.info(f"Generating presigned POST for key: {object_key}, bucket {self.bucket_name}")

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
                    "success_action_status": "201",
                    "bucket": self.bucket_name,
                },
                Conditions=conditions,
                ExpiresIn=expiration
            )

            response["url"] = response["url"].replace(self.server_url, self.public_url)

            logging.info("Returning external POST URL")

            return response

        except Exception as e:
            logging.error(f"Error generating presigned POST: {e}")
            raise e

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

    def delete_media_folder(self, media_id: str):
        """
        Deletes the entire folder for a media_id (video + transcripts).
        """
        prefix = f"{media_id}/"
        try:
            # List all objects in the folder
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

            if 'Contents' in response:
                objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]

                # Delete in batch
                self.s3.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                logger.info(f"Deleted {len(objects_to_delete)} objects from S3 for {media_id}")
        except Exception as e:
            logger.error(f"Failed to delete S3 folder {media_id}: {e}")
            # Don't raise, we want to continue deleting other resources

    def get_file_content(self, s3_path):
        response = self.s3.get_object(Bucket=self.bucket_name, Key=s3_path)
        data = response['Body'].read().decode('utf-8')
        return data


@lru_cache()
def get_s3_manager() -> S3Manager:
    """
    Creates the manager once and caches it in memory.
    Acting like a Singleton, but that can be overridden in tests.
    """
    return S3Manager()
