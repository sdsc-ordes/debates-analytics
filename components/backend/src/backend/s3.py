import boto3
import os
from botocore.exceptions import NoCredentialsError, DataNotFoundError

from dotenv import load_dotenv

load_dotenv()

PROD_S3_ACCESS_KEY = os.getenv("PROD_S3_ACCESS_KEY")
PROD_S3_SECRET_KEY = os.getenv("PROD_S3_SECRET_KEY")
PROD_S3_BUCKET_NAME = os.getenv("PROD_S3_BUCKET_NAME")
PROD_S3_REGION_NAME = os.getenv("PROD_S3_REGION_NAME")
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
        if prod:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=PROD_S3_ACCESS_KEY,
                aws_secret_access_key=PROD_S3_SECRET_KEY,
                region_name=PROD_S3_REGION_NAME
            )
            self.bucket_name = PROD_S3_BUCKET_NAME
        else:
            self.s3 = boto3.client(
                's3',
                endpoint_url=S3_SERVER,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
            )
            self.bucket_name = "debates"

    def get_presigned_url(self, prefix, key, expiration=3600):
        """
        Generate a presigned URL for an S3 object.
        """
        try:
            object_key = f"{prefix}/{key}"
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
