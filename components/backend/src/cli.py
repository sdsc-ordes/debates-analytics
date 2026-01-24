import typer
import logging
from tasks.reindex import reindex_solr
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

import typer
import logging
import uuid
import os
from pathlib import Path
from config.logging import configure_logging

# Services
from tasks.reindex import reindex_solr
from services.s3 import get_s3_manager
from services.mongo import get_mongo_manager

configure_logging()
logger = logging.getLogger(__name__)

app = typer.Typer()

# ... existing reindex command ...

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

    for file_path in files:
        filename = file_path.name
        ext = file_path.suffix.lower()

        # 1. Determine Type
        media_type = ""
        s3_suffix = ""
        if ext == ".mp4":
            media_type = "video"
            s3_suffix = "source.mp4"
        elif ext == ".wav":
            media_type = "audio"
            s3_suffix = "source.wav"
        else:
            print(f"⚠️ Skipping unsupported file: {filename}")
            continue

        # 2. Generate Identity
        media_id = str(uuid.uuid4())
        s3_key = f"{media_id}/{s3_suffix}"

        print(f"▶️ Processing: {filename}")
        print(f"   └── ID: {media_id}")

        try:
            # 3. Upload to S3
            # We use the internal method or client directly
            print(f"   └── Uploading to S3 ({s3_key})...")
            s3.upload_file(str(file_path), s3_key)

            # 4. Register in MongoDB
            print(f"   └── Registering in MongoDB...")
            mongo.insert_initial_media_document(
                media_id=media_id,
                s3_key=s3_key,
                filename=filename,
                media_type=media_type,
            )
            print(f"   ✅ Success")

        except Exception as e:
            logger.exception(f"Failed to process {filename}")
            print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    app()
