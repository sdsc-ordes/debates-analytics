import logging
from fastapi import APIRouter, Depends,Query, HTTPException
from services.solr import get_solr_manager, SolrManager
from models.search import SearchQuery, SearchResponse, FacetField, FacetValue
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search-solr", response_model=SearchResponse)
async def search_solr(
    q: Optional[str] = Query(None, alias="queryTerm", description="The main search string"),
    raw_filters: List[str] = Query([], alias="facetFilters", description="List of filters in 'field:value' format"),
    facet_fields: List[str] = Query(
        ["debate_date", "debate_timeslot", "statement_type", "debate_session", "speaker_name", "speaker_role_tag", "speaker_country"],
        alias="facetFields"
    ),
    sort_by: Optional[str] = Query(None, alias="sortBy"),
    rows: int = Query(10, ge=1, le=100),
    start: int = Query(0, ge=0),
    solr: SolrManager = Depends(get_solr_manager)
):
    parsed_filters = []
    for f in raw_filters:
        if ":" in f:
            field, value = f.split(":", 1)
            parsed_filters.append({"facetField": field, "facetValue": value})

    logger.info(f"Search Query: q='{q}' | filters={len(parsed_filters)} | sort='{sort_by}' | range={start}-{start+rows}")

    internal_query_model = SearchQuery(
        queryTerm=q,
        facetFilters=parsed_filters,
        facetFields=facet_fields,
        sortBy=sort_by,
        rows=rows,
        start=start,
    )

    try:
        results = solr.search(internal_query_model)
    except Exception as e:
        logger.error(f"Solr Query Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search service unavailable")

    raw = results.raw_response

    docs = raw.get("response", {}).get("docs", [])
    num_found = raw.get("response", {}).get("numFound", 0)
    highlighting = raw.get("highlighting", {})

    if num_found == 0:
        logger.info("Search completed. 0 hits found.")
    else:
        logger.info(f"Search completed. Found {num_found} hits. Returning {len(docs)} docs.")

    clean_facets = []
    raw_facet_fields = raw.get("facet_counts", {}).get("facet_fields", {})

    for field, flat_values in raw_facet_fields.items():
        facet_values_list = []
        for i in range(0, len(flat_values), 2):
            label = flat_values[i]
            count = flat_values[i+1]
            if count > 0:
                facet_values_list.append(FacetValue(label=str(label), count=count))

        if facet_values_list:
            clean_facets.append(FacetField(field_name=field, values=facet_values_list))

    return SearchResponse(
        docs=docs,
        total=num_found,
        facets=clean_facets,
        highlighting=highlighting
    )
