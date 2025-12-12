import json
import logging

from typing import List, Dict, Set, Union
from models.search import SearchDocument

logger = logging.getLogger(__name__)


class JsonTranscriptParser:

    def enrich_subtitles(self, json_input: Union[str, bytes, List, Dict]) -> List[Dict]:
        """
        Parses JSON input, normalizes it to a list, and enriches segment data.
        """
        data = json_input

        # 1. Decode bytes/string if needed
        if isinstance(data, bytes):
            data = json.loads(data.decode('utf-8'))
        elif isinstance(data, str):
            data = json.loads(data)

        # 2. Normalize to List
        if isinstance(data, dict) and "segments" in data:
            subtitle_list = data["segments"]
        elif isinstance(data, list):
            subtitle_list = data
        else:
            subtitle_list = []

        # 3. Check for empty list (Fix: use 'if not' instead of '!')
        if not subtitle_list:
            return subtitle_list

        # 4. Initialize the first segment
        subtitle_list[0]["segment_nr"] = 1
        subtitle_list[0]["speaker_id"] = subtitle_list[0].pop("speaker", None)

        # 5. Loop through list starting from index 1 to compare with previous
        # We use range(1, len(...)) so we can easily access i and i-1
        for i in range(1, len(subtitle_list)):
            current_seg = subtitle_list[i]
            prev_seg = subtitle_list[i-1]

            # Map 'speaker' to 'speaker_id' for the current segment
            current_seg["speaker_id"] = current_seg.pop("speaker", None)

            # Segment Numbering: Check if speaker changed
            # (Assuming 'speaker_id' is the key based on your input JSON)
            if current_seg.get("speaker_id") != prev_seg.get("speaker_id"):
                current_seg["segment_nr"] = prev_seg["segment_nr"] + 1
            else:
                current_seg["segment_nr"] = prev_seg["segment_nr"]
        logger.info(subtitle_list)
        return subtitle_list

    def extract_speakers(self, segments: List[Dict]) -> Set[str]:
        return {s.get("speaker_id") for s in segments if s.get("speaker_id")}

    def extract_segments(self, subtitle_list: List[Dict]) -> List[Dict]:
        """
        Groups individual subtitle items into segments based on 'segment_nr'.
        Each resulting dictionary contains the segment metadata and a list of its subtitles.
        """
        if not subtitle_list:
            return []

        grouped_segments = []

        current_group = {
            "segment_nr": subtitle_list[0]["segment_nr"],
            "language": subtitle_list[0]["language"],
            "speaker_id": subtitle_list[0].get("speaker_id"),
            "subtitles": [subtitle_list[0]["text"]],
            "start": subtitle_list[0]["start"],
            "end": subtitle_list[0]["end"],
        }

        for i in range(1, len(subtitle_list)):
            sub = subtitle_list[i]

            if sub["segment_nr"] == current_group["segment_nr"]:
                current_group["subtitles"].append(sub["text"])
                current_group["end"] = sub["end"]

            else:
                grouped_segments.append(current_group)

                current_group = {
                    "segment_nr": sub["segment_nr"],
                    "language": sub["language"],
                    "speaker_id": sub.get("speaker_id"),
                    "start": sub["start"],
                    "subtitles": [sub["text"]]
                }
                logger.info(current_group)

        grouped_segments.append(current_group)

        logger.info("grupped segments")
        logger.info(grouped_segments)

        return grouped_segments

    def parse(self, segments: Union[str, List[Dict]], media_id: str, subtitle_type: str) -> List[SearchDocument]:
        """
        Parses content into Solr SearchDocuments.
        Accepts raw JSON string OR the already-enriched list.
        """
        logger.info(segments)
        solr_docs = []
        for seg in segments:
            logger.info("Solr docs")
            logger.info(f"seg: {seg}")
            index = seg.get('segment_nr', 1) - 1
            unique_id = f"{media_id}_{index}_{subtitle_type}"

            doc = SearchDocument(
                id=unique_id,
                media_id=media_id,
                segment_nr=seg.get('segment_nr', index + 1),
                speaker_id=seg.get("speaker_id", "UNKNOWN"),
                statement_language=seg.get("language", "en"),

                # Wrap text in list for Solr multi-valued field
                statement=seg.get("subtitles"),

                statement_type=subtitle_type,

                # Data is already float thanks to enrich_segments running first
                start=seg.get("start", 0.0),
                end=seg.get("end", 0.0),
            )
            solr_docs.append(doc)

        return solr_docs