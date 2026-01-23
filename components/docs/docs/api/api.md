# API Documentation

The API can be seen as a second interface to processing and data along to the
[UI](../ui/ui.md)

## Ingestion

--8<-- "includes/diagrams/ingest.md"

- `ingest/get_presinged-post`: gets a presigned post url, that can be used to
  upload the media file on S3
- `ingest/process`: triggers the first job on redis queue: either a `convert` or
  a `trnascribe` task, depending on the type of the media.

See [Frontend](../ui/ingest.md)

## Metadata

--8<-- "includes/diagrams/metadata-display.md" --8<--
"includes/diagrams/metadata-update.md"

- `ingest/get_presinged-post`: gets a presigned post url, that can be used to
  upload the media file on S3
- `ingest/process`: triggers the first job on redis queue: either a `convert` or
  a `trnascribe` task, depending on the type of the media.

See Frontend

## Search

<div style="width: 40%; margin: 0 auto;">
--8<-- "includes/diagrams/search.md"
</div>

- `ingest/get_presinged-post`: gets a presigned post url, that can be used to
  upload the media file on S3
- `ingest/process`: triggers the first job on redis queue: either a `convert` or
  a `trnascribe` task, depending on the type of the media.

See Frontend

## Admin

--8<-- "includes/diagrams/admin.md"

- `ingest/get_presinged-post`: gets a presigned post url, that can be used to
  upload the media file on S3
- `ingest/process`: triggers the first job on redis queue: either a `convert` or
  a `trnascribe` task, depending on the type of the media.

See Frontend

## API Spec

<swagger-ui src="./openapi.json"/>
