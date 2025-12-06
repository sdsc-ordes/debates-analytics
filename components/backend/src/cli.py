import typer
import logging
import sys
import os

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tasks.reindex import reindex_solr

# Configure logging to see output in terminal
logging.basicConfig(level=logging.INFO)

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

if __name__ == "__main__":
    app()
