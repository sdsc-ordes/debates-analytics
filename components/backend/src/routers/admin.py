import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends
from common.s3 import get_s3_manager, S3Manager
from common.queue import get_queue_manager, QueueManager
from common.mongo import get_mongo_manager, MongoManager
from common.models.storage import S3PostRequest, S3PostResponse, ProcessRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/delete-media")
async def get_presigned_post(
    request_data: DeleteMediaRequest,
    s3_client: S3Manager = Depends(get_s3_manager),
    mongo_client: MongoManager = Depends(get_mongo_manager),
    solr_client: SolrManager = Depends(get_solr_manager),
):
    """
    [POST] Returns a presigned URL and creates the initial Mongodb record.
    Status -> 'preparing'
    """
    media_id = request_data.media_id
    solr_client.delete()
    s3_key = f"{media_id}/source.mp4"

    logging.info(f"Generating presigned POST for media_id: {media_id}")

    try:
        post_data = s3_client.get_presigned_post(s3_key)
    except Exception:
        logger.exception(f"Failed to generate presigned URL for {media_id}")
        raise HTTPException(status_code=500, detail="Storage service unavailable.")

    try:
        mongo_client.insert_initial_media_document(
            media_id=media_id,
            s3_key=s3_key,
            filename=request_data.filename,
        )
    except Exception as e:
        logger.exception(f"Database insertion failed: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    return S3PostResponse(
        postUrl=post_data["url"],
        fields=post_data["fields"],
        mediaId=media_id,
        s3Key=s3_key
    )

def delete_all_documents_in_solr():
    solr = Solr(SOLR_URL, always_commit=True)
    solr.delete(q='*:*')
