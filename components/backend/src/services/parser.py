import json
import logging
from typing import List
from models.search import SolrSegmentDocument

logger = logging.getLogger(__name__)


class JsonTranscriptParser:
    def parse(self, json_content: str, media_id: str, subtitle_type: str) -> List[SolrSegmentDocument]:
        """
        Parses the JSON output from Whisper/Transcription service.
        Input format: [{"start": "00:00:00", "end": "00:00:09", "text": "...", "speaker": "SPEAKER_01", "language": "en"}, ...]
        """
        # 1. Load raw JSON string
        segments = json.loads(json_content)

        solr_docs = []

        for index, seg in enumerate(segments):
            # 2. Convert Time format ("HH:MM:SS" -> Seconds Float)
            start_sec = self._time_str_to_seconds(seg.get("start", "00:00:00"))
            end_sec = self._time_str_to_seconds(seg.get("end", "00:00:00"))

            # 3. Create Unique ID (Collision proof)
            # Format: {media_id}_{index}_{type}
            unique_id = f"{media_id}_{index}_{subtitle_type}"

            doc = SolrSegmentDocument(
                id=unique_id,
                media_id=media_id,
                segment_nr=index + 1, # 1-based index for humans

                # Field Mapping
                speaker_id=seg.get("speaker", "UNKNOWN"),
                statement=seg.get("text", "").strip(),
                statement_language=seg.get("language", "en"), # Map language
                statement_type=subtitle_type,

                # Time Calculations
                start=start_sec,
                end=end_sec,
            )
            solr_docs.append(doc)

        return solr_docs

    def _time_str_to_seconds(self, time_str: str) -> float:
        """
        Converts '00:00:28' or '00:00:28.500' to float 28.5
        """
        if isinstance(time_str, (float, int)):
            return float(time_str)

        try:
            # Handle HH:MM:SS.mmm
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
            elif len(parts) == 2:
                m, s = parts
                return int(m) * 60 + float(s)
            return 0.0
        except ValueError:
            return 0.0