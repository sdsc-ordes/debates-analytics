# About HELLO vjhvjvj

Political Debates is a projects that aims to facilitate analysis of video or
audio content in the following ways:

- transcripts and translations are AI generated and split content per speakers
- a user interface is offered to add annotations for the speakers and to correct
  the AI generated transcriptions and translations
- a search engine that is updated with the modified content helps to find
  relevant statements of speakers

## Context

The project was developed in the context of analyzing political debate by the
UNHCR. But it can be generalized to other video and audio content, where the
focus is on speakers that take turns discussing a topic. The input are just
video and audio files, with no specific assumptions. The goal is to make the
content available per speaker and to be able to search into who said what when.

## User Interface with two roles

The project comes with a user interface and assumes two roles:

- `Editor`: can process and admister the data and metadata
- `Reader`: has access to the processed videos and their metadata, but cannot
  edit any data or metadata

Both roles have access to the user interface, but the reader is restricted to
certain pages.

## Parts

### Dashboard

![Searchpage](static/content/dashboard.png "Dashboard to upload and administer media files"){
width="800" }

- only the `Editor` has access
- new videos and audio files can be uploaded to start processing
- all videos and audio files are listed and can be deleted
- indexing for processed videos and audios can be repeated

### Searchpage

![Searchpage](static/content/searchpage.png "Search interface to make speaker statements searchable"){
width="800" }

- both roles have access
- the search page can be used to search in speaker statements for a term or
  filter the statements by certain criteria that have been added as tags to the
  segments by the `Editor`.

### Mediaplayer

![Mediaplayer](static/content/mediaplayer.png "Mediaplayer to compare media with transcripts and translations"){
width="800" }

- both roles have access
- the `Editor` can edit and add metadata on speakers and videos and correct
  transcripts and translations
- the `Reader` can view and jump around in the media replay via pointing to text
  in transcripts and translations

## PoC

The project has been done as a Proof of Concept: it is not production ready in
the following ways:

- the data is stored on docker volumes. The volumes are limited by the diskspace
  on the server and their are no data recovery strategies in place
- the authentication uses nginx basic auth to distinguish between just two
  roles. There is no real user authentication in place besides these teo roles.
