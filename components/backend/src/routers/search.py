import logging
from fastapi import APIRouter, HTTPException, Depends

from services.solr import get_solr_manager, SolrManager
from models import SolrRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search-solr")
async def search_solr(
    request: SolrRequest,
    solr_client: SolrManager = Depends(get_solr_manager),
):
    """Fetch search results from Solr"""
    logger.info(f"request: {request}")
    try:
        solr_response = solr_client.search(
            request
        )
        logger.info(f"Solr search request: {request}")
        logger.debug(f"Solr response: {solr_response}")
        return solr_response
    except Exception as e:
        logger.exception(f"Error occurred for Solr search {request}")
        raise HTTPException(
            status_code=500,
            detail=f"Solr Search failed: {str(e)}"
        )
