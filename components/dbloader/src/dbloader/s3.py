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

S3_BUCKET_NAME=os.getenv("S3_BUCKET_NAME")
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

    def get_s3_data(self, s3_path):
        response = self.s3.get_object(Bucket=self.bucket_name, Key=s3_path)
        data = response['Body'].read().decode('utf-8')
        return data
