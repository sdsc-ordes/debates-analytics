import logging
from fastapi import APIRouter, HTTPException, Depends

from services.solr import get_solr_manager, SolrManager
from models.search import SearchQuery, SearchResponse, FacetField, FacetValue

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search-solr", response_model=SearchResponse)
async def search_solr(
    query: SearchQuery,
    solr: SolrManager = Depends(get_solr_manager)
):
    # 1. Query Solr (get raw results)
    results = solr.search(query)
    raw = results.raw_response

    # 2. Extract Basic Data
    docs = raw.get("response", {}).get("docs", [])
    num_found = raw.get("response", {}).get("numFound", 0)
    highlighting = raw.get("highlighting", {})

    # 3. Transform Facets
    # FROM: {"speaker": ["Alice", 10, "Bob", 5]}
    # TO:   [{"field_name": "speaker", "values": [{"label": "Alice", "count": 10}, ...]}]
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

        # Only add the field if it actually has results
        if facet_values_list:
            clean_facets.append(FacetField(
                field_name=field,
                values=facet_values_list
            ))

    # 4. Return the Clean Object
    return SearchResponse(
        items=docs,
        total=num_found,
        facets=clean_facets,
        highlighting=highlighting
    )
