import logging
from typing import List, Dict, Any
from functools import lru_cache
from pysolr import Solr
from config.settings import get_settings

from models.search import SearchQuery

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
            params["fq"] = [
                f'{filter.facetField}:"{filter.facetValue}"' for filter in query.facetFilters
            ]

        if query.sortBy:
            params["sort"] = query.sortBy

        return self.client.search(query.queryTerm if query.queryTerm else "*:*", **params)

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


@lru_cache()
def get_solr_manager() -> SolrManager:
    return SolrManager()
