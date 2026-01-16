import os
import boto3
import time
from botocore.client import Config

# These env vars will be passed from docker-compose
ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
SECRET_KEY = os.environ.get("S3_SECRET_KEY")
ENDPOINT = "http://localhost:3900"
BUCKET = "debates"

def wait_and_configure():
    print("🐍 Python: Waiting for S3 API...")
    s3 = boto3.client('s3', endpoint_url=ENDPOINT,
                      aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY,
                      region_name='garage',
                      config=Config(signature_version='s3v4'))

    # Retry loop until Garage is ready
    for _ in range(30):
        try:
            s3.head_bucket(Bucket=BUCKET)
            break
        except Exception:
            time.sleep(1)

    print(f"🐍 Python: Applying CORS to {BUCKET}...")
    s3.put_bucket_cors(
        Bucket=BUCKET,
        CORSConfiguration={
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedOrigins': ['*'],
                'ExposeHeaders': ['ETag', 'x-amz-request-id']
            }]
        }
    )
    print("🐍 Python: CORS configured successfully.")

if __name__ == "__main__":
    wait_and_configure()
