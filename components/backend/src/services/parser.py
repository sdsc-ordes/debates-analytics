import json
import logging

from typing import List, Dict, Set, Union
from models.search import SearchDocument

logger = logging.getLogger(__name__)


class JsonTranscriptParser:
    # ... enrich_subtitles remains exactly the same ...
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

        # 3. Check for empty list
        if not subtitle_list:
            return subtitle_list

        # 4. Initialize the first segment
        subtitle_list[0]["segment_nr"] = 1
        subtitle_list[0]["speaker_id"] = subtitle_list[0].pop("speaker", None)

        # 5. Loop through list starting from index 1 to compare with previous
        for i in range(1, len(subtitle_list)):
            current_seg = subtitle_list[i]
            prev_seg = subtitle_list[i-1]

            # Map 'speaker' to 'speaker_id'
            current_seg["speaker_id"] = current_seg.pop("speaker", None)

            # Check if speaker changed to determine segment_nr
            if current_seg.get("speaker_id") != prev_seg.get("speaker_id"):
                current_seg["segment_nr"] = prev_seg["segment_nr"] + 1
            else:
                current_seg["segment_nr"] = prev_seg["segment_nr"]
        logger.info(subtitle_list)
        return subtitle_list

    def extract_segments(self, subtitle_list: List[Dict]) -> List[Dict]:
        """
        Groups individual subtitles into Segments.
        NOW INCLUDES FULL SUBTITLE DATA (Timestamps) inside the group.
        """
        if not subtitle_list:
            return []

        grouped_segments = []

        # Helper to create a clean subtitle object
        def clean_sub(s):
            return {"start": s["start"], "end": s["end"], "text": s["text"]}

        # Initialize first group
        first = subtitle_list[0]
        current_group = {
            "segment_nr": first["segment_nr"],
            "language": first.get("language", "en"),
            "speaker_id": first.get("speaker_id"),
            "start": first["start"],
            "end": first["end"],
            # CHANGE: Store full objects, not just text strings
            "subtitles": [clean_sub(first)]
        }

        for i in range(1, len(subtitle_list)):
            sub = subtitle_list[i]

            if sub["segment_nr"] == current_group["segment_nr"]:
                # Add to current group
                current_group["subtitles"].append(clean_sub(sub))
                current_group["end"] = sub["end"] # Update segment end time
            else:
                # Finish current group
                grouped_segments.append(current_group)

                # Start new group
                current_group = {
                    "segment_nr": sub["segment_nr"],
                    "language": sub.get("language", "en"),
                    "speaker_id": sub.get("speaker_id"),
                    "start": sub["start"],
                    "end": sub["end"],
                    "subtitles": [clean_sub(sub)]
                }

        grouped_segments.append(current_group)
        return grouped_segments

    def parse(self, segments: List[Dict], media_id: str, subtitle_type: str) -> List[SearchDocument]:
        """
        Parses Segments into Solr SearchDocuments.
        """
        solr_docs = []

        for seg in segments:
            index = seg.get('segment_nr', 1) - 1
            unique_id = f"{media_id}_{index}_{subtitle_type}"

            # CHANGE: Extract just the text list for Solr indexing
            # Solr wants: ["Hello world", "How are you"]
            text_list = [s["text"] for s in seg.get("subtitles", [])]

            doc = SearchDocument(
                id=unique_id,
                media_id=media_id,
                segment_nr=seg.get('segment_nr', index + 1),
                speaker_id=seg.get("speaker_id", "UNKNOWN"),
                statement_language=seg.get("language", "en"),
                statement=text_list, # <--- Solr gets plain text list
                statement_type=subtitle_type,
                start=seg.get("start", 0.0),
                end=seg.get("end", 0.0),
            )
            solr_docs.append(doc)

        return solr_docs

    def extract_speakers(self, segments: List[Dict]) -> List:
         # Helper to extract unique speakers for the separate speakers collection
         seen = set()
         for s in segments:
             sid = s.get("speaker_id")
             if sid and sid not in seen:
                 seen.add(sid)
         return list(seen)
