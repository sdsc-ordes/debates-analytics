#!/bin/bash

python3 /odtp/odtp-app/app.py \
    --start_date $START_DATE \
    --end_date $END_DATE \
    --output_file $OUTPUT_FILE \
    --output_folder "/odtp/odtp-output/" \
    ${ORGANIZATION:+--organization $ORGANIZATION} \
    ${MEETING_TYPE:+--meeting_type $MEETING_TYPE} \
    ${KEYWORDS:+--keywords $KEYWORDS} \
    --download

#cp -r $OUTPUT_FILE /odtp/odtp-output/$OUTPUT_FILE

