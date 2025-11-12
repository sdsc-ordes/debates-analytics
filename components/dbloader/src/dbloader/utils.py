import json
import logging
from datetime import datetime, timezone
import pytz

def get_media_role_format(s3_path):
    parts = s3_path.split("/")
    filename = parts[-1]
    logging.info(f"filename: {filename}")
    filename_parts = filename.split(".")
    logging.info(f"filename parts: {filename_parts}")
    return filename_parts


def format_current_datetime():
    current_datetime = datetime.now(
        timezone.utc
    )
    return _format_date(current_datetime)


def _format_date(dt):
    return dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
