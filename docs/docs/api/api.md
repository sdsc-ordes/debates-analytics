# API Documentation

The API can be seen as a second interface to processing and data along to the [UI](../ui/ui.md)

## Ingestion

--8<-- "includes/diagrams/ingest.md"

- `ingest/get_presinged-post`: gets a presigned post url, that can be used to upload the media file on S3
- `ingest/process`: triggers the first job on redis queue: either a `convert` or a `trnascribe` task, depending on the type of the media.

See [Frontend](../ui/ingest.md)

hello.  uhgjgjhgjhg

<swagger-ui src="./openapi.json"/>
