import os
import time
import logging
import uuid
import json
import boto3
from prefect import flow, task, get_run_logger

# --- Configuration ---
# NOTE: Assume these environment variables are set in your Docker Compose
INPUT_DIR = "/app/input"
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi')
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_MEDIA_PATH = os.getenv("S3_MEDIA_PATH", "raw_media")

# Initialize S3 Client (can be done globally or in a task)
try:
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )
except Exception as e:
    logging.error(f"Failed to initialize S3 client: {e}")
    # We will let Prefect handle logging and failure if this object is used inside a task

# Initialize a Prefect-specific logger
LOGGER = get_run_logger()

# --- Prefect Tasks ---

@task(name="Find New Videos")
def find_new_videos(directory: str, extensions: tuple) -> list[str]:
    """
    Scans the input directory for video files.
    NOTE: In a real system, you'd track processed files (e.g., using a manifest or DB).
    """
    new_files = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(extensions):
            full_path = os.path.join(directory, filename)
            new_files.append(full_path)
    LOGGER.info(f"Found {len(new_files)} new videos to process.")
    return new_files

@task(name="Upload Raw Video to S3")
def upload_raw_video(local_path: str, bucket_name: str, s3_client) -> dict:
    """
    Uploads a local file to S3 and returns the structured job metadata.
    """
    job_id = str(uuid.uuid4())
    file = os.path.basename(local_path)
    file_name, file_ext = os.path.splitext(file)

    # Define the S3 key structure using the job ID as a prefix
    s3_prefix = f"jobs/{job_id}"
    s3_video_key = f"{s3_prefix}/{file}"

    LOGGER.info(f"Assigned Job ID: {job_id}. Uploading raw video...")

    # --- S3 Upload ---
    s3_client.upload_file(local_path, bucket_name, s3_video_key)
    LOGGER.info(f"S3 upload successful. Key: s3://{bucket_name}/{s3_video_key}")

    # Clean up the local file after successful upload
    try:
        os.remove(local_path)
        LOGGER.info(f"Local file cleaned up: {file}")
    except Exception as e:
        LOGGER.warning(f"Could not delete local file {local_path}: {e}")

    # Return the metadata needed for the next steps
    return {
        "job_id": job_id,
        "s3_raw_video_key": s3_video_key,
        "s3_bucket": bucket_name,
        "s3_prefix": s3_prefix,
        "file_name": file_name,
        "file_ext": file_ext
    }

@flow(name="Video Dataloader Flow")
def video_dataloader_flow(input_dir: str = INPUT_DIR):
    """
    Scans the input folder and triggers the next stage for each new video found.
    """
    videos_to_process = find_new_videos(input_dir, VIDEO_EXTENSIONS)

    # Use Prefect's Task Mapping to process all found videos in parallel
    job_metadata_list = upload_raw_video.map(
        videos_to_process,
        bucket_name=S3_BUCKET_NAME,
        s3_client=s3_client
    )

    # For a unified pipeline, we immediately call the next flow (Main Processing)
    # The output of this flow (a list of job metadata) is passed to the next flow.
    # We use submit() for asynchronous execution of the downstream flow.

    # NOTE: To complete the full pipeline, we need the next flow defined.
    # This line below assumes the 'video_main_processing_flow' is defined and imported.
    LOGGER.info(f"Queueing {len(videos_to_process)} jobs for Main Processing.")
    # video_main_processing_flow.submit(job_metadata_list)

# --- Deployment ---

if __name__ == "__main__":
    from prefect.deployments import Deployment

    deployment = Deployment.build_from_flow(
        flow=video_dataloader_flow,
        name="Scheduled Video Loader",
        schedule={"interval": 300}, # Runs every 5 minutes
        tags=["media", "loader"],
        work_pool_name="default-agent-pool"
    )
    deployment.apply()
