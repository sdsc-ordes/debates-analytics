import os
import json
from pysolr import Solr
from dotenv import load_dotenv
from typing import List
from dbloader import merge
from dbloader import utils
from pprint import pprint
import logging

load_dotenv()


SOLR_URL = os.getenv("SOLR_URL")
SOLR_SELECT_URL = f"{SOLR_URL}select"


class DataloaderSolrException(Exception):
    pass


def delete_all_documents_in_solr():
    solr = Solr(SOLR_URL, always_commit=True)
    solr.delete(q='*:*')


def update_solr(
    job_id,
    subtitles_orig,
    subtitles_en,
    metadata,
    segments,
    speakers
):
    solr = Solr(SOLR_URL, always_commit=True)
    logging.info(f"Metadata: {metadata} for {job_id}")
    documents = []
    for segment in segments:
        document_orig = _map_segment(
            segment=segment,
            subtitles=subtitles_orig,
            debate_extras=metadata,
            segment_type=merge.SUBTITLE_TYPE_TRANSCRIPT
        )
        if document_orig:
            documents.append(document_orig)

        document_en = _map_segment(
            segment=segment,
            subtitles=subtitles_en,
            debate_extras=metadata,
            segment_type=merge.SUBTITLE_TYPE_TRANSLATION
        )
        if document_en:
            documents.append(document_en)

    pprint(documents)
    solr.add(documents)
    logging.info(f"Successfully inserted {len(documents)} documents into solr for {job_id}")


def _map_segment(segment, subtitles, debate_extras, segment_type):
    document = {}
    document["statement"] = [
        subtitle["content"]
        for subtitle in subtitles if subtitle["segment_nr"] == segment["segment_nr"]]
    if not document["statement"]:
        return None
    document ["statement_type"] = segment_type
    if segment_type == merge.SUBTITLE_TYPE_TRANSLATION:
        document["statement_language"] = "en"
    else:
        document["statement_language"] = ""
    for key in segment.keys():
        document[key] = segment[key]
    for key in debate_extras.keys():
        document[key] = debate_extras[key]
    return document


def _map_to_solr_date(debate_date):
    isodate_utc = debate_date
    return isodate_utc
