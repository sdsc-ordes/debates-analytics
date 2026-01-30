# Commandline interface

Currently the commandline should just be used for admin purposes by developers:

It offers two commands:

```bash title="reindex a media item from the commandline"
just reindex <media_id>
```

Upload a media with analysis results:

```bash title="reindex a media item from the commandline"
just upload <folder>
```

The second command was just used to upload previously analysed video material. After uploading it needs to be reindexed either from the commandline or interactively in the dashboard.

The upload is in the moment not very forgiving:

The directory should have the following files:

```bash hl_lines="2 9 10 12" title="expected file names for a video upload"
/mymedia
├── audio.wav
├── segments-original.json
├── segments-original.md
├── segments-original.pdf
├── segments-translation.json
├── segments-translation.md
├── segments-translation.pdf
├── source.mp4
├── subtitles-original.json
├── subtitles-original.srt
├── subtitles-translation.json
└── subtitles-translation.srt
```

In case of an audio upload: the `source.mp4` file can be missing and the audio file should be called `source.wav`

!!! hint
    It would be nice to make that more flexible in the future, so that WhisperX output can be uploaded without any further intervention
