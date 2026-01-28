# About

![Logo](static/logo/political_debates_logo.png "Logo of debates-analytics"){ align=left width="200" }

**Political Debates** is a project designed to facilitate the comprehensive analysis of video and audio content.

It streamlines the workflow from raw media to searchable analytics through three core capabilities:

* :material-waveform: **AI-Powered Processing:** Transcripts and translations are automatically generated and diarized (split by speaker).
* :material-human-edit: **Human-in-the-Loop:** A dedicated user interface allows editors to annotate speakers and correct AI-generated text.
* :material-magnify: **Dynamic Search:** A specialized search engine updates in real-time with modified content to help locate specific speaker statements.

<br clear="left"/>

---

## Context

This work was originally funded by the SNSF Spark Grant **“Debating Human Rights”**.

!!! quote ""
    **Grant Number:** 221139
    **Source:** [SNSF Data Portal](https://data.snf.ch/grants/grant/221139)

The goal was to create specialized components for analyzing **United Nations Human Rights Council (UNHRC)** debates, focusing on:

1.  **Sophisticated Transcription:** Integrating cutting-edge models (e.g., Whisper 3.0) for accurate, multilingual transcription.
2.  **Multimodal Handling:** Processing video/audio for scene extraction and speaker diarization.
3.  **Specialized Database:** Storing metadata and extracted features efficiently.

This repository consolidates the results of that project to make the processing tools available in a generalizable form.

## Guides

Get started with the platform:

[ :material-download: Installation Options ](installation/overview.md){ .md-button .md-button--primary }
[ :material-school: User Guide ](userguide/roles.md){ .md-button }

---

## Status & Limitations

!!! warning "Proof of Concept (PoC)"
    This project is currently a **Proof of Concept** and is **not production-ready**. Please be aware of the following limitations:

    * **Data Storage:** Data is stored on Docker volumes limited by server disk space. There are currently no automated data recovery strategies in place.
    * **Authentication:** The system uses basic Nginx authentication to distinguish between two roles (`Editor` and `Reader`). There is no granular user management beyond these two roles.
