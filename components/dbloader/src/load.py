import typer
import traceback
import uvicorn
import os
from pprint import pprint
import dataloader.srt_parser as dl_parse_srt
import dataloader.yml_parser as dl_parse_yml
import dataloader.mongodb as dl_mongo
import dataloader.file as dl_file
import dataloader.solr as dl_solr
from typing_extensions import Annotated
from dataloader.s3 import s3Manager, SUFFIX_METADATA, SUFFIX_SRT_EN, SUFFIX_SRT_ORIG
from dataloader.api import api
from dataloader.merge import (
    merge_and_segment, get_speakers_from_segments,
    assign_segments_to_subtitles)
from dotenv import load_dotenv

load_dotenv()

API_HOST = os.getenv("API_HOST")


cli = typer.Typer()


@cli.command()
def s3_to_mongo_solr(
    s3_prefix: Annotated[str, typer.Argument(help="s3 prefix")],
    debug: Annotated[bool, typer.Option(help="Print traceback on exception")] = False,
):
    """Get data and metadata for s3_path from S3 and add it to the Mongo DB"""
    try:
        # get data from s3
        s3 = s3Manager()
        s3_srt_path_orig = f"{s3_prefix}/{s3_prefix}-{SUFFIX_SRT_ORIG}"
        s3_srt_path_en = f"{s3_prefix}/{s3_prefix}-{SUFFIX_SRT_EN}"
        s3_metadata_path = f"{s3_prefix}/{s3_prefix}-{SUFFIX_METADATA}"
        print(s3_metadata_path)
        print(s3_srt_path_en)
        print(s3_srt_path_orig)

        # get srt files
        raw_srt_en = s3.get_s3_data(s3_srt_path_en)
        raw_srt_orig = s3.get_s3_data(s3_srt_path_orig)

        # get yml metadata
        raw_metadata = s3.get_s3_data(s3_metadata_path)

        # parse srt into json
        subtitles_orig = dl_parse_srt.parse_subtitles(raw_srt_orig)
        subtitles_en = dl_parse_srt.parse_subtitles(raw_srt_en)

        # parse metadata from yml into json
        parsed_metadata = dl_parse_yml.parse_metadata(raw_metadata)

        # merge subtitles to derive segments
        segments = merge_and_segment(subtitles_en, subtitles_orig)

        # get speakers list from segments
        speakers = get_speakers_from_segments(segments)

        # enrich subtitles be segment_nr
        subtitles_orig = assign_segments_to_subtitles(subtitles_orig, segments)
        subtitles_en = assign_segments_to_subtitles(subtitles_en, segments)

        # update mongodb
        dl_file.write_parsed_data_to_file(speakers, "speakers.json")
        debate_data = dl_mongo.mongodb_insert_debate(
            metadata=parsed_metadata,
            subtitles_orig=subtitles_orig,
            subtitles_en=subtitles_en,
            segments=segments,
            speakers=speakers
        )
        dl_solr.update_solr(debate_data)
    except Exception as e:
        print(f"S3 data could not be loaded into secondary databases. An exception occurred: {e}")
        _print_traceback(debug)


def _print_traceback(debug):
    if debug:
        traceback.print_exc()


if __name__ == "__main__":
    s3_to_mongo_solr()
