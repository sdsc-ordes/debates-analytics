import typer
import logging
import uuid
from pathlib import Path
from tasks.reindex import reindex_solr
from services.s3 import get_s3_manager
from services.mongo import get_mongo_manager
from config.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def reindex(media_id: str):
    """
    Manually triggers the S3 -> Solr loading process for a media ID.
    """
    print(f"Manual trigger: Re-indexing {media_id}...")
    try:
        reindex_solr(media_id)
        print("✅ Success")
    except Exception as e:
        print(f"❌ Failed: {e}")


@app.command()
def upload_folder(folder_path: str):
    """
    [Bulk Import] Uploads all .mp4 and .wav files in a folder to S3
    and registers them in MongoDB.
    """
    path = Path(folder_path)
    if not path.exists():
        print(f"❌ Error: Path '{folder_path}' not found inside container.")
        return

    s3 = get_s3_manager()
    mongo = get_mongo_manager()

    # Get all files
    files = [f for f in path.iterdir() if f.is_file()]
    print(f"📂 Found {len(files)} files in {folder_path}...")
    media_id = str(uuid.uuid4())
    logger.info(f"Bulk upload initiated for folder='{folder_path}' with Media ID='{media_id}'")
    media_type = None
    media_filename = None
    media_s3_key = None
    s3_suffix = None

    for file_path in files:
        filename = file_path.name
        ext = file_path.suffix.lower()

        if ext == ".mp4":
            media_type = "video"
            s3_suffix = "source.mp4"
            media_filename = filename
            media_s3_key = f"{media_id}/{s3_suffix}"
            s3_key = media_s3_key
        elif ext == ".wav" and not media_type:
            media_type = "audio"
            s3_suffix = "source.wav"
            media_filename = filename
            media_s3_key = f"{media_id}/{s3_suffix}"
            s3_key = media_s3_key
        elif ext == ".wav":
            s3_suffix = "audio.wav"
            s3_key = f"{media_id}/{s3_suffix}"
        else:
            s3_suffix = filename.lower()
            s3_key = f"{media_id}/transcripts/{s3_suffix}"

        print(f"▶️ Processing: {filename}")
        print(f"   └── ID: {media_id}")

        try:
            # 3. Upload to S3
            # We use the internal method or client directly
            print(f"   └── Uploading to S3 ({s3_key})")
            s3.upload_file(str(file_path), s3_key)

        except Exception as e:
            logger.exception(f"Failed to process {filename}")
            print(f"   ❌ Failed: {e}")

    # 3. Verify upload
    print(f"   └── Verifying upload in S3...")
    try:
        for key in s3.list_objects_by_prefix(media_id):
            print(f"   ✅ Uploaded: {key}")
    except Exception as e:
        logger.exception(f"Failed to verify upload for {path}")
        print(f"   ❌ Verification failed: {e}")

    # 4. Register in MongoDB
    try:
        print("   └── Registering in MongoDB...")
        mongo.insert_initial_media_document(
            media_id=media_id,
            s3_key=media_s3_key,
            filename=media_filename,
            media_type=media_type,
            status="manually uploaded with results"
        )
        print("   ✅ Success")
    except Exception as e:
        logger.exception(f"Failed to register in mongodb upload for {path}")
        print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    app()
