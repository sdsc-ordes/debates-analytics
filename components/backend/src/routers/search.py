import logging
from fastapi import APIRouter, Depends,Query
from services.solr import get_solr_manager, SolrManager
from models.search import SearchQuery, SearchResponse, FacetField, FacetValue
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search-solr", response_model=SearchResponse)
async def search_solr(
    #  Individual Query Parameters
    q: Optional[str] = Query(None, alias="queryTerm", description="The main search string"),

    # Accepts multiple values: ?facetFilters=speaker:Alice&facetFilters=type:Original
    raw_filters: List[str] = Query([], alias="facetFilters", description="List of filters in 'field:value' format"),

    # Accepts multiple values: ?facetFields=speaker&facetFields=type
    facet_fields: List[str] = Query(
        ["debate_schedule", "statement_type", "debate_session", "speaker_name", "speaker_role_tag"],
        alias="facetFields"
    ),

    sort_by: Optional[str] = Query(None, alias="sortBy"),
    rows: int = Query(10, ge=1, le=100),
    start: int = Query(0, ge=0),

    solr: SolrManager = Depends(get_solr_manager)
):
    # Parse the "field:value" strings back into the FacetFilter dictionaries
    parsed_filters = []
    for f in raw_filters:
        if ":" in f:
            # Split only on the first colon to handle values that might contain colons (like timestamps)
            field, value = f.split(":", 1)
            parsed_filters.append({"facetField": field, "facetValue": value})

    # Map to the SearchQuery Object for the SolrManager
    internal_query_model = SearchQuery(
        queryTerm=q,
        facetFilters=parsed_filters,
        facetFields=facet_fields,
        sortBy=sort_by,
        rows=rows,
        start=start,
    )

    # Query Solr (get raw results)
    results = solr.search(internal_query_model)
    logger.info(f"Solr returned: {results}")
    raw = results.raw_response

    # Extract Basic Data
    docs = raw.get("response", {}).get("docs", [])
    num_found = raw.get("response", {}).get("numFound", 0)
    highlighting = raw.get("highlighting", {})

    # Transform Facets
    clean_facets = []
    raw_facet_fields = raw.get("facet_counts", {}).get("facet_fields", {})

    for field, flat_values in raw_facet_fields.items():
        facet_values_list = []

        # Iterate Solr's flat list in steps of 2 [Label, Count, Label, Count...]
        for i in range(0, len(flat_values), 2):
            label = flat_values[i]
            count = flat_values[i+1]

            if count > 0:
                facet_values_list.append(FacetValue(
                    label=str(label),
                    count=count
                ))

        if facet_values_list:
            clean_facets.append(FacetField(
                field_name=field,
                values=facet_values_list
            ))

    # Return the Clean Object
    return SearchResponse(
        docs=docs,
        total=num_found,
        facets=clean_facets,
        highlighting=highlighting
    )
