# About

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
- `Reader`: has access to the processed videos and their metadata, but cannot edit any data or metadata

Both roles have access to the user interface, but the reader is restricted to certain pages.

## Parts

### Dashboard

![Search interface](static/content/dashboard.png){ width="800",
caption="hello" } /// caption Search interface to make speaker statements
searchable ///

- only the `Editor` has access
- new videos and audio files can be uploaded to start processing
- all videos and audio files are listed and can be deleted
- indexing for processed videos and audios can be repeated

### Searchpage

- both roles have access
- the search page can be used to search in speaker statements for a term or filter the statements by certain criteria that have been added as tags to the segments by the `Editor`.

### Mediaplayer page

: A dashboard for administering the video and audio data and metadata, that also allows to start processing for newly uploaded video and audio files
- `Reader` and `Editor`: Search page to search in transcripts
- `

, that allows to:

- start processing of media files: videos as `mp4` and audios as `wav``
- 


shows maybe best what has been achieved:

- There is a search interface, where the videos and audios are searchable by
  speaker statements in both original language and english translation

- You can jump into the media player page for each statement and hear/watch the
  statement while at the same time being able to compare against transcript and
  translation. You can also edit the speaker, transcript and translation of the
  statement.

![Search interface](static/content/search-interface.png){ width="800",
caption="hello" } /// caption Search interface to make speaker statements
searchable ///

![Search interface](static/content/mediaplayer-interface.png){ width="800" } ///
caption Media player to compare and edit speaker information, transcripts and
translations ///

## PoC

The project has been done as a Proof of Concept: it is not production ready and
some steps that can be automated are still manual. Also some settings that could
be custom are currently hard coded. In Roadmap we describe the next steps to
generalize the project.
