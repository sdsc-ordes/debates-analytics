# political debates ui: frontend

## About

This is the frontend for [debates-app](https://github.com/sdsc-ordes/debates-app).
The frontend is made in SvelteKit. It has two pages:
- A search page to search in video transcripts on a Solr Instance
- A media player page where a video or audio file can be played along with transcript, translation and speaker information: these can also be edited. The metadata of the media is retrieved from a mongo db.
- There is an edit route: `/edit`: going on that route allows to switch into edit mode and edit the video transcript, translation and speaker information


## Technology

- The frontend uses SvelteKit.

## Setup

Dependencies:
- the frontend assumes a backend to be up and running: checkout the documentation at [debates-app](https://github.com/sdsc-ordes/debates-app)

## Setup

There is a `env.dist` file provided to show the environment variables that the frontend needs. In case the dependencies are all accessible it can be setup on its own with the following commands:

```
npm install
pnpm dev
```
