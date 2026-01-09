import typer
import logging
from config.settings import get_settings
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

if __name__ == "__main__":
    app()
