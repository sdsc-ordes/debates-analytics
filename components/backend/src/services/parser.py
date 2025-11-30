import re
import srt
from typing import List, Tuple
from .models import DebateSegment, SubtitleItem, SolrSegmentDocument

class SrtParser:
    def parse(
        self, srt_content: str, media_id: str, subtitle_type: str = "transcript"
    ) -> List[SolrSegmentDocument]:
        """
        Orchestrates: Raw String -> Subtitles -> Grouped Segments -> Solr Docs
        """
        # 1. Parse raw SRT
        raw_subs = list(srt.parse(srt_content))

        # 2. Group into Segments (Speaker Blocks)
        segments = self._group_by_speaker(raw_subs, media_id)

        # 3. Map to Solr Documents
        solr_docs = []
        for seg in segments:
            doc = SolrSegmentDocument(
                id=f"{media_id}_{seg.segment_nr}",
                media_id_s=seg.media_id,
                segment_nr_i=seg.segment_nr,
                speaker_id_s=seg.speaker_id,
                statement_t=seg.text_content, # Computed field
                statement_type_s=subtitle_type,
                start_f=seg.start_time,
                end_f=seg.end_time,
                duration_f=seg.end_time - seg.start_time
            )
            solr_docs.append(doc)

        return solr_docs

    def _group_by_speaker(self, subtitles: List[srt.Subtitle], media_id: str) -> List[DebateSegment]:
        segments = []
        current_segment = None
        segment_counter = 0

        for sub in subtitles:
            # Extract Speaker & Content
            speaker_id, clean_content = self._extract_speaker(sub.content)

            # Create Internal Subtitle Object
            sub_item = SubtitleItem(
                index=sub.index,
                start=sub.start.total_seconds(),
                end=sub.end.total_seconds(),
                content=clean_content
            )

            # Logic: If speaker changes, start new segment
            if current_segment is None or current_segment.speaker_id != speaker_id:
                # Save previous if exists
                if current_segment:
                    segments.append(current_segment)

                # Start new
                segment_counter += 1
                current_segment = DebateSegment(
                    segment_nr=segment_counter,
                    speaker_id=speaker_id,
                    media_id=media_id,
                    subtitles=[]
                )

            current_segment.subtitles.append(sub_item)

        # Append last segment
        if current_segment:
            segments.append(current_segment)

        return segments

    def _extract_speaker(self, content: str) -> Tuple[str, str]:
        """
        Parses '[SPEAKER_01]: Hello world' -> ('SPEAKER_01', 'Hello world')
        Fallback: If no tag, uses 'UNKNOWN'
        """
        match = re.match(r"\[(SPEAKER_\d+)\]:\s*(.*)", content, re.DOTALL)
        if match:
            return match.group(1), match.group(2).strip()
        # Fallback if transcription has lines without speaker tags
        # We assume same speaker or "UNKNOWN"
        return "UNKNOWN", content.strip()
