import logging
from typing import List, Dict, Any
from functools import lru_cache
from pysolr import Solr
from config.settings import get_settings

from models.search import SearchQuery


DEBATE_DETAILS_MAPPING = {
    "session": "debate_session",
    "type": "debate_type",
    "schedule": "debate_schedule",
}

logger = logging.getLogger(__name__)

class SolrManager:
    def __init__(self):
        settings = get_settings()
        self.solr_url = settings.solr_url
        self.client = Solr(self.solr_url, timeout=10)
        logger.info(f"SolrManager initialized with URL: {self.solr_url}")

    def update_speakers(self, media_id: str, speakers: List[Dict[str, Any]]):
        """
        Updates speaker information in Solr documents.
        """
        for speaker in speakers:
            speaker_id = speaker["speaker_id"]
            speaker_name = speaker.get("name", None)
            speaker_role_tag = speaker.get("role_tag", None)

            query = f'speaker_id:{speaker_id} AND media_id:{media_id}'

            results = self.client.search(query)

            if results.hits > 0:
                docs_to_update = []
                for doc in results:
                    updated_doc = {
                        "id": doc["id"],
                        "speaker_name": {"set": speaker_name},
                        "speaker_role_tag": {"set": speaker_role_tag}
                    }
                    docs_to_update.append(updated_doc)

                if docs_to_update:
                    self.client.add(docs_to_update, commit=True)

    def update_segment(self, media_id: str, segment_nr: int, subtitles: List[dict], subtitle_type: str):
        statement = [s.get("text", "") for s in subtitles]

        query = f'statement_type:{subtitle_type} AND media_id:{media_id} AND segment_nr:{segment_nr}'
        results = self.client.search(query)

        if results.hits > 0:
            docs_to_update = []
            for doc in results:
                updated_doc = {
                    "id": doc["id"],
                    "statement": {"set": statement},
                }
                docs_to_update.append(updated_doc)

            if docs_to_update:
                self.client.add(docs_to_update, commit=True)

    def search(
        self,
        query: SearchQuery
    ):
        """Fetch search results from Solr"""
        params = {
            "wt": "json",
            "indent": "true",
            "df": "statement",
            "hl": "true" if query.queryTerm else "false",
            "hl.fragsize": 0,
            "rows": 500,
            "start": 0,
        }

        if query.facetFields:
            params["facet"] = "true"
            params["facet.field"] = query.facetFields

        if query.facetFilters:
            params["fq"] = self.build_filters(query.facetFilters)

        if query.sortBy:
            params["sort"] = query.sortBy

        return self.client.search(query.queryTerm if query.queryTerm else "*:*", **params)

    def build_filters(self, facet_filters: Dict[str, str]) -> List[str]:
        filter_queries = []
        for f in facet_filters:
            field = f.facetField
            value = f.facetValue

            # Special handling for debate_schedule (Date Range)
            if field == "debate_schedule":
                # Assume value is "YYYY-MM-DD" or "YYYY-MM-DDTHH..."
                # We strip it to the date part and create a 24-hour range
                if len(value) >= 10:
                    date_str = value[:10]  # Take "2025-12-13"
                    # Create range covering the full day in UTC
                    fq = f'{field}:[{date_str}T00:00:00Z TO {date_str}T23:59:59Z]'
                    filter_queries.append(fq)
                else:
                    # Fallback if format is weird
                    filter_queries.append(f'{field}:"{value}"')

            else:
                # Standard handling for text/string fields (Speakers, Language, etc.)
                filter_queries.append(f'{field}:"{value}"')

        return filter_queries

    def delete_by_media_id(self, media_id: str):
        """
        Deletes all segments associated with a specific media_id.
        """
        query = f'media_id:"{media_id}"'

        logger.info(f"Deleting Solr documents for query: {query}")

        try:
            self.client.delete(q=query, commit=True)
        except Exception as e:
            logger.error(f"Failed to delete documents for {media_id} from Solr: {e}")
            raise e

    def update_debate_details(self, media_id: str, details: Dict[str, Any]):
        """
        Generic method to update debate metadata on ALL segments for a given media_id.
        Driven by DEBATE_DETAILS_MAPPING configuration.
        """
        # 1. Build the Atomic Update Payload dynamically
        #    We only include fields that are actually present in the 'details' dict
        solr_updates = {}
        for api_field, solr_field in DEBATE_DETAILS_MAPPING.items():
            if api_field in details and details[api_field] is not None:
                # Solr atomic update syntax: {"set": "New Value"}
                solr_updates[solr_field] = {"set": details[api_field]}

        if not solr_updates:
            logger.info("No mapped fields found to update in Solr.")
            return

        logger.info(f"Updating Solr metadata for {media_id}: {solr_updates}")

        # 2. Fetch all Segment IDs for this Media
        #    (Solr requires the unique 'id' to perform atomic updates)
        query = f"media_id:{media_id}"
        results = self.client.search(query, fl="id", rows=10000)

        if len(results) == 0:
            logger.warning(f"No Solr documents found for media_id: {media_id}")
            return

        # 3. Apply the updates to every segment
        batch_update = []
        for doc in results:
            update_doc = {"id": doc["id"]}
            update_doc.update(solr_updates) # Merge our dynamic updates
            batch_update.append(update_doc)

        # 4. Commit
        if batch_update:
            self.client.add(batch_update, commit=True)
            logger.info(f"Updated {len(batch_update)} documents in Solr.")


@lru_cache()
def get_solr_manager() -> SolrManager:
    return SolrManager()
